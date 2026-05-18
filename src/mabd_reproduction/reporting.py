"""Shared report status contracts for M-ABD reproduction evidence."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any


class EvidenceStatus(str, Enum):
    """Allowed machine-readable reproduction statuses."""

    PASSED = "passed"
    FAILED = "failed"
    INCOMPLETE = "incomplete"
    NOT_VERIFIED = "not_verified"
    UNSUPPORTED = "unsupported"
    QUALITATIVE_RECONSTRUCTION = "qualitative_reconstruction"


@dataclass(frozen=True)
class ClaimReport:
    """Minimal report record shared by future runners and validators."""

    claim_id: str
    scene_id: str
    asset_hashes: dict[str, str]
    solver_mode: str
    backend: str
    baseline_lane: str
    expected: dict[str, Any]
    observed: dict[str, Any]
    threshold: dict[str, Any]
    unit: str
    status: EvidenceStatus
    failure_reason: str
    timing_distribution: dict[str, Any]
    raw_outputs: dict[str, str]
    plot_paths: dict[str, str]
    source_commit: str
    vendored_newton_commit: str
    paper_source_version: str

    def to_mapping(self) -> dict[str, Any]:
        return claim_report_to_mapping(self)


REQUIRED_REPORT_KEYS = frozenset(ClaimReport.__dataclass_fields__)
LANE_PASS_GATE_KEY = "lane_pass_gate"
LANE_PASS_GATE_VERSION = "required_lane_v1"
LANE_PASS_GATE_SCOPE = "required_lane_only"
LANE_PASS_GATE_CLAIM_ID = "experiment.single_body.spinning_box"
LANE_PASS_GATE_BASELINE = "rbd_implicit_baseline"
LANE_PASS_GATE_SOLVER_MODE = "paper_faithful_implicit_rbd"
LANE_PASS_GATE_BACKEND = "cpu_numpy_newton_only"


def _require_mapping(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = data.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"{key} must be a mapping")
    return dict(value)


def _require_str_mapping(data: dict[str, Any], key: str) -> dict[str, str]:
    value = _require_mapping(data, key)
    if not all(isinstance(k, str) and isinstance(v, str) for k, v in value.items()):
        raise ValueError(f"{key} must map strings to strings")
    return {str(k): str(v) for k, v in value.items()}


def _require_str(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{key} must be a non-empty string")
    return value


def _contains_lane_pass_gate(expected: dict[str, Any], observed: dict[str, Any]) -> bool:
    return (
        LANE_PASS_GATE_KEY in expected
        or LANE_PASS_GATE_KEY in observed
        or "lane_gate_status" in observed
    )


def _require_lane_pass_gate(
    data: dict[str, Any], container_name: str
) -> dict[str, Any]:
    gate = data.get(LANE_PASS_GATE_KEY)
    if not isinstance(gate, dict):
        raise ValueError(f"{container_name}.{LANE_PASS_GATE_KEY} must be a mapping")
    return dict(gate)


def _require_gate_value(
    gate: dict[str, Any], gate_name: str, key: str, expected: Any
) -> None:
    if gate.get(key) != expected:
        raise ValueError(f"{gate_name}.{key} must be {expected!r}")


def _validate_gate_payload(
    gate: dict[str, Any],
    gate_name: str,
    *,
    claim_id: str,
    baseline_lane: str,
    solver_mode: str,
    backend: str,
) -> None:
    expected_values = {
        "gate_version": LANE_PASS_GATE_VERSION,
        "claim_id": claim_id,
        "baseline_lane": baseline_lane,
        "solver_mode": solver_mode,
        "backend": backend,
        "scope": LANE_PASS_GATE_SCOPE,
        "full_experiment_claim_passed": False,
    }
    for key, expected in expected_values.items():
        _require_gate_value(gate, gate_name, key, expected)


def _validate_lane_pass_gate(
    *,
    claim_id: str,
    baseline_lane: str,
    solver_mode: str,
    backend: str,
    status: EvidenceStatus,
    expected: dict[str, Any],
    observed: dict[str, Any],
) -> None:
    if not _contains_lane_pass_gate(expected, observed):
        return
    if status != EvidenceStatus.INCOMPLETE:
        raise ValueError("lane_pass_gate requires incomplete top-level status")
    allowlist_values = {
        "claim_id": LANE_PASS_GATE_CLAIM_ID,
        "baseline_lane": LANE_PASS_GATE_BASELINE,
        "solver_mode": LANE_PASS_GATE_SOLVER_MODE,
        "backend": LANE_PASS_GATE_BACKEND,
    }
    actual_values = {
        "claim_id": claim_id,
        "baseline_lane": baseline_lane,
        "solver_mode": solver_mode,
        "backend": backend,
    }
    for key, allowed in allowlist_values.items():
        if actual_values[key] != allowed:
            raise ValueError(f"lane_pass_gate {key} must be {allowed!r}")
    if observed.get("lane_gate_status") != "passed":
        raise ValueError("lane_gate_status must be 'passed'")
    expected_gate = _require_lane_pass_gate(expected, "expected")
    observed_gate = _require_lane_pass_gate(observed, "observed")
    _validate_gate_payload(
        expected_gate,
        "expected.lane_pass_gate",
        claim_id=claim_id,
        baseline_lane=baseline_lane,
        solver_mode=solver_mode,
        backend=backend,
    )
    _validate_gate_payload(
        observed_gate,
        "observed.lane_pass_gate",
        claim_id=claim_id,
        baseline_lane=baseline_lane,
        solver_mode=solver_mode,
        backend=backend,
    )
    if observed_gate.get("thresholds_met") is not True:
        raise ValueError("observed.lane_pass_gate.thresholds_met must be true")


def validate_claim_report_mapping(data: dict[str, Any]) -> ClaimReport:
    missing = sorted(REQUIRED_REPORT_KEYS - set(data))
    if missing:
        raise ValueError("claim report missing required keys: " + ", ".join(missing))
    try:
        status = EvidenceStatus(str(data["status"]))
    except ValueError as exc:
        allowed = sorted(status.value for status in EvidenceStatus)
        raise ValueError(f"status must be one of {allowed}") from exc
    claim_id = _require_str(data, "claim_id")
    if status == EvidenceStatus.PASSED and claim_id.startswith("experiment."):
        raise ValueError("passed experiment reports require a dedicated evidence gate")
    solver_mode = _require_str(data, "solver_mode")
    backend = _require_str(data, "backend")
    baseline_lane = _require_str(data, "baseline_lane")
    expected = _require_mapping(data, "expected")
    observed = _require_mapping(data, "observed")
    _validate_lane_pass_gate(
        claim_id=claim_id,
        baseline_lane=baseline_lane,
        solver_mode=solver_mode,
        backend=backend,
        status=status,
        expected=expected,
        observed=observed,
    )
    return ClaimReport(
        claim_id=claim_id,
        scene_id=_require_str(data, "scene_id"),
        asset_hashes=_require_str_mapping(data, "asset_hashes"),
        solver_mode=solver_mode,
        backend=backend,
        baseline_lane=baseline_lane,
        expected=expected,
        observed=observed,
        threshold=_require_mapping(data, "threshold"),
        unit=_require_str(data, "unit"),
        status=status,
        failure_reason=_require_str(data, "failure_reason"),
        timing_distribution=_require_mapping(data, "timing_distribution"),
        raw_outputs=_require_str_mapping(data, "raw_outputs"),
        plot_paths=_require_str_mapping(data, "plot_paths"),
        source_commit=_require_str(data, "source_commit"),
        vendored_newton_commit=_require_str(data, "vendored_newton_commit"),
        paper_source_version=_require_str(data, "paper_source_version"),
    )


def claim_report_to_mapping(report: ClaimReport) -> dict[str, Any]:
    data = asdict(report)
    data["status"] = report.status.value
    return data


def write_claim_report(report: ClaimReport, path: str | Path) -> None:
    report_path = Path(path)
    mapping = report.to_mapping()
    validate_claim_report_mapping(mapping)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(mapping, allow_nan=False, indent=2, sort_keys=True) + "\n"
    report_path.write_text(payload, encoding="utf-8")


def load_claim_report(path: str | Path) -> ClaimReport:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("claim report JSON must contain an object")
    return validate_claim_report_mapping(data)
