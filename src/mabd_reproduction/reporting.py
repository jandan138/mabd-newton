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


def validate_claim_report_mapping(data: dict[str, Any]) -> ClaimReport:
    missing = sorted(REQUIRED_REPORT_KEYS - set(data))
    if missing:
        raise ValueError("claim report missing required keys: " + ", ".join(missing))
    try:
        status = EvidenceStatus(str(data["status"]))
    except ValueError as exc:
        allowed = sorted(status.value for status in EvidenceStatus)
        raise ValueError(f"status must be one of {allowed}") from exc
    return ClaimReport(
        claim_id=_require_str(data, "claim_id"),
        scene_id=_require_str(data, "scene_id"),
        asset_hashes=_require_str_mapping(data, "asset_hashes"),
        solver_mode=_require_str(data, "solver_mode"),
        backend=_require_str(data, "backend"),
        baseline_lane=_require_str(data, "baseline_lane"),
        expected=_require_mapping(data, "expected"),
        observed=_require_mapping(data, "observed"),
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
    report_path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(report.to_mapping(), indent=2, sort_keys=True) + "\n"
    report_path.write_text(payload, encoding="utf-8")


def load_claim_report(path: str | Path) -> ClaimReport:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("claim report JSON must contain an object")
    return validate_claim_report_mapping(data)
