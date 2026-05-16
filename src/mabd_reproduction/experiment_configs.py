"""Per-scene run configs for M-ABD reproduction reports."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import yaml

from .experiment_contracts import ExperimentMatrix
from .reporting import EvidenceStatus


class ExperimentRunConfigError(ValueError):
    """Raised when a per-scene run config is incomplete or unsafe."""


@dataclass(frozen=True)
class SpinningBoxRunConfig:
    schema_version: int
    claim_id: str
    scene_id: str
    source_lines: tuple[str, ...]
    asset_ids: tuple[str, ...]
    baseline_lane: str
    required_missing_lanes: tuple[str, ...]
    paper_values: dict[str, Any]
    time_step_s: float
    step_count: int
    initial_q: np.ndarray
    initial_qd: np.ndarray
    mass_diagonal: np.ndarray
    report_status: EvidenceStatus
    failure_reason: str
    output_report: str
    thresholds: dict[str, float]


def _read_mapping(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ExperimentRunConfigError(f"{path} must contain a YAML mapping")
    return data


def _require_str(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value:
        raise ExperimentRunConfigError(f"{key} must be a non-empty string")
    return value


def _require_str_tuple(data: dict[str, Any], key: str) -> tuple[str, ...]:
    value = data.get(key)
    if not isinstance(value, list) or not value or not all(isinstance(item, str) and item for item in value):
        raise ExperimentRunConfigError(f"{key} must be a non-empty list of strings")
    return tuple(value)


def _require_mapping(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = data.get(key)
    if not isinstance(value, dict) or not value:
        raise ExperimentRunConfigError(f"{key} must be a non-empty mapping")
    return dict(value)


def _require_float_mapping(data: dict[str, Any], key: str) -> dict[str, float]:
    mapping = _require_mapping(data, key)
    result: dict[str, float] = {}
    for item_key, item_value in mapping.items():
        if not isinstance(item_key, str):
            raise ExperimentRunConfigError(f"{key} keys must be strings")
        result[item_key] = float(item_value)
    return result


def _require_vector(data: dict[str, Any], key: str) -> np.ndarray:
    value = data.get(key)
    vector = np.asarray(value, dtype=float)
    if vector.shape != (12,):
        raise ExperimentRunConfigError(f"{key} must contain 12 numeric values")
    return vector


def load_spinning_box_config(path: str | Path) -> SpinningBoxRunConfig:
    config_path = Path(path)
    data = _read_mapping(config_path)
    if data.get("schema_version") != 1:
        raise ExperimentRunConfigError("schema_version must be 1")
    claim_id = _require_str(data, "claim_id")
    if claim_id != "experiment.single_body.spinning_box":
        raise ExperimentRunConfigError("spinning-box config must target experiment.single_body.spinning_box")

    simulation = _require_mapping(data, "simulation")
    report = _require_mapping(data, "report")
    try:
        status = EvidenceStatus(_require_str(report, "status"))
    except ValueError as exc:
        raise ExperimentRunConfigError("report.status is not a known EvidenceStatus") from exc
    if status == EvidenceStatus.PASSED:
        raise ExperimentRunConfigError("passed experiment configs require a dedicated evidence gate")

    time_step_s = float(simulation.get("time_step_s"))
    step_count = int(simulation.get("step_count"))
    if time_step_s <= 0.0:
        raise ExperimentRunConfigError("time_step_s must be positive")
    if step_count <= 0:
        raise ExperimentRunConfigError("step_count must be positive")

    return SpinningBoxRunConfig(
        schema_version=1,
        claim_id=claim_id,
        scene_id=_require_str(data, "scene_id"),
        source_lines=_require_str_tuple(data, "source_lines"),
        asset_ids=_require_str_tuple(data, "asset_ids"),
        baseline_lane=_require_str(data, "baseline_lane"),
        required_missing_lanes=_require_str_tuple(data, "required_missing_lanes"),
        paper_values=_require_mapping(data, "paper_values"),
        time_step_s=time_step_s,
        step_count=step_count,
        initial_q=_require_vector(simulation, "initial_q"),
        initial_qd=_require_vector(simulation, "initial_qd"),
        mass_diagonal=_require_vector(simulation, "mass_diagonal"),
        report_status=status,
        failure_reason=_require_str(report, "failure_reason"),
        output_report=_require_str(report, "output_report"),
        thresholds=_require_float_mapping(report, "thresholds"),
    )


def validate_spinning_box_config_against_matrix(config: SpinningBoxRunConfig, matrix: ExperimentMatrix) -> None:
    matches = [entry for entry in matrix.experiments if entry.claim_id == config.claim_id]
    if len(matches) != 1:
        raise ExperimentRunConfigError(f"{config.claim_id} must have exactly one matrix entry")
    entry = matches[0]
    if config.scene_id != entry.scene_id:
        raise ExperimentRunConfigError("scene_id must match experiment matrix")
    if config.source_lines != entry.source_lines:
        raise ExperimentRunConfigError("source_lines must match experiment matrix")
    if config.asset_ids != entry.asset_ids:
        raise ExperimentRunConfigError("asset_ids must match experiment matrix")
    if config.output_report != entry.output_report:
        raise ExperimentRunConfigError("output_report must match experiment matrix")
    if config.baseline_lane not in entry.required_lanes:
        raise ExperimentRunConfigError("baseline_lane must be listed in required_lanes")
    missing = set(config.required_missing_lanes) - set(entry.required_lanes)
    if missing:
        raise ExperimentRunConfigError("required_missing_lanes must be listed in required_lanes")


__all__ = [
    "ExperimentRunConfigError",
    "SpinningBoxRunConfig",
    "load_spinning_box_config",
    "validate_spinning_box_config_against_matrix",
]
