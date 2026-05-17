"""Per-scene run configs for M-ABD reproduction reports."""

from __future__ import annotations

from dataclasses import dataclass
from math import asin, isfinite, pi
from numbers import Integral, Real
from pathlib import Path
from typing import Any

import numpy as np
import yaml

from .experiment_contracts import ExperimentMatrix
from .reporting import EvidenceStatus


class ExperimentRunConfigError(ValueError):
    """Raised when a per-scene run config is incomplete or unsafe."""


@dataclass(frozen=True)
class SpinningBoxPaperHorizonConfig:
    duration_s: float
    time_step_grid_s: tuple[float, ...]
    sample_count: int
    output_report: str
    figure_pdf_sha256: str
    figure_text_source: str
    thresholds: dict[str, float]


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
    contact_surface: dict[str, Any]
    report_status: EvidenceStatus
    failure_reason: str
    output_report: str
    thresholds: dict[str, float]
    paper_horizon: SpinningBoxPaperHorizonConfig


@dataclass(frozen=True)
class PhysicalPendulumReferenceConfig:
    release_angle_rad: float
    initial_angle_rad: float
    kappa: float
    omega_lin_rad_s: float
    period_count: int
    sample_count: int


@dataclass(frozen=True)
class PhysicalPendulumMABDDevelopmentConfig:
    time_step_s: float
    step_count: int
    sample_count: int
    rest_points_m: np.ndarray
    masses_kg: np.ndarray
    pivot_rest_point_m: np.ndarray
    pivot_world_point_m: np.ndarray
    angle_probe_rest_point_m: np.ndarray
    gravity_m_s2: np.ndarray
    initial_q: np.ndarray
    initial_qd: np.ndarray
    output_report: str
    thresholds: dict[str, float]


@dataclass(frozen=True)
class PhysicalPendulumRBDBaselineConfig:
    time_step_s: float
    step_count: int
    sample_count: int
    length_m: float
    mass_kg: float
    gravity_m_s2: np.ndarray
    initial_angle_rad: float
    initial_angular_velocity_rad_s: float
    newton_iteration_limit: int
    newton_residual_tolerance: float
    output_report: str
    thresholds: dict[str, float]


@dataclass(frozen=True)
class PhysicalPendulumRunConfig:
    schema_version: int
    claim_id: str
    scene_id: str
    source_lines: tuple[str, ...]
    asset_ids: tuple[str, ...]
    baseline_lane: str
    required_missing_lanes: tuple[str, ...]
    paper_values: dict[str, Any]
    reference: PhysicalPendulumReferenceConfig
    mabd_development: PhysicalPendulumMABDDevelopmentConfig
    rbd_baseline: PhysicalPendulumRBDBaselineConfig
    report_status: EvidenceStatus
    failure_reason: str
    output_report: str
    thresholds: dict[str, float]


PAPER_HORIZON_THRESHOLD_KEYS = frozenset(
    {
        "max_linear_momentum_error",
        "max_angular_momentum_error",
        "max_relative_kinetic_energy_drift",
        "max_relative_total_energy_drift",
        "max_abs_det_minus_one",
        "min_singular_value",
        "max_singular_value",
        "max_affine_orthogonality_error",
        "max_residual_norm",
    }
)

PHYSICAL_PENDULUM_THRESHOLD_KEYS = frozenset(
    {
        "max_abs_reference_identity_error",
    }
)
PHYSICAL_PENDULUM_MABD_DEVELOPMENT_THRESHOLD_KEYS = frozenset(
    {
        "max_abs_angle_error_rad",
        "max_constraint_residual_norm",
        "max_pivot_residual_m",
    }
)
PHYSICAL_PENDULUM_RBD_BASELINE_THRESHOLD_KEYS = frozenset(
    {
        "max_abs_angle_error_rad",
        "max_implicit_residual",
        "max_length_constraint_error_m",
        "max_phase_drift_rad",
    }
)
PHYSICAL_PENDULUM_REQUIRED_MISSING_LANES = ("mabd_newton",)


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


def _require_str_tuple(
    data: dict[str, Any], key: str, *, allow_empty: bool = False
) -> tuple[str, ...]:
    value = data.get(key)
    if (
        not isinstance(value, list)
        or (not allow_empty and not value)
        or not all(isinstance(item, str) and item for item in value)
    ):
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
        if not isinstance(item_value, Real) or isinstance(item_value, bool):
            raise ExperimentRunConfigError(f"{key} values must be finite numeric values")
        value = float(item_value)
        if not isfinite(value):
            raise ExperimentRunConfigError(f"{key} values must be finite numeric values")
        result[item_key] = value
    return result


def _require_vector(data: dict[str, Any], key: str) -> np.ndarray:
    value = data.get(key)
    if not isinstance(value, list) or len(value) != 12:
        raise ExperimentRunConfigError(f"{key} must contain 12 numeric values")
    result: list[float] = []
    for item in value:
        if not isinstance(item, Real) or isinstance(item, bool):
            raise ExperimentRunConfigError(f"{key} must contain 12 numeric values")
        item_float = float(item)
        if not isfinite(item_float):
            raise ExperimentRunConfigError(f"{key} must contain 12 finite numeric values")
        result.append(item_float)
    return np.asarray(result, dtype=float)


def _require_positive_float(data: dict[str, Any], key: str) -> float:
    value = data.get(key)
    if not isinstance(value, Real) or isinstance(value, bool):
        raise ExperimentRunConfigError(f"{key} must be a finite positive number")
    result = float(value)
    if not isfinite(result) or result <= 0.0:
        raise ExperimentRunConfigError(f"{key} must be a finite positive number")
    return result


def _require_positive_int(data: dict[str, Any], key: str) -> int:
    value = data.get(key)
    if not isinstance(value, Integral) or isinstance(value, bool):
        raise ExperimentRunConfigError(f"{key} must be a positive integer")
    result = int(value)
    if result <= 0:
        raise ExperimentRunConfigError(f"{key} must be a positive integer")
    return result


def _require_positive_float_tuple(
    data: dict[str, Any],
    key: str,
) -> tuple[float, ...]:
    value = data.get(key)
    if not isinstance(value, list) or not value:
        raise ExperimentRunConfigError(f"{key} must be a non-empty list of finite positive numbers")
    result: list[float] = []
    for item in value:
        if not isinstance(item, Real) or isinstance(item, bool):
            raise ExperimentRunConfigError(f"{key} must contain finite positive numbers")
        item_float = float(item)
        if not isfinite(item_float) or item_float <= 0.0:
            raise ExperimentRunConfigError(f"{key} must contain finite positive numbers")
        result.append(item_float)
    return tuple(result)


def _require_finite_number(data: dict[str, Any], key: str) -> float:
    value = data.get(key)
    if not isinstance(value, Real) or isinstance(value, bool):
        raise ExperimentRunConfigError(f"{key} must be a finite number")
    result = float(value)
    if not isfinite(result):
        raise ExperimentRunConfigError(f"{key} must be a finite number")
    return result


def _require_unit_interval_float(data: dict[str, Any], key: str) -> float:
    result = _require_finite_number(data, key)
    if result <= 0.0 or result >= 1.0:
        raise ExperimentRunConfigError(f"{key} must be in the open interval (0, 1)")
    return result


def _require_vec3_tuple(data: dict[str, Any], key: str) -> tuple[float, float, float]:
    value = data.get(key)
    if not isinstance(value, list) or len(value) != 3:
        raise ExperimentRunConfigError(f"{key} must contain 3 numeric values")
    result: list[float] = []
    for item in value:
        if not isinstance(item, Real) or isinstance(item, bool):
            raise ExperimentRunConfigError(f"{key} must contain 3 numeric values")
        item_float = float(item)
        if not isfinite(item_float):
            raise ExperimentRunConfigError(f"{key} must contain 3 finite numeric values")
        result.append(item_float)
    if np.linalg.norm(result) == 0.0:
        raise ExperimentRunConfigError(f"{key} must be nonzero")
    return (result[0], result[1], result[2])


def _require_vec3_array(data: dict[str, Any], key: str) -> np.ndarray:
    value = data.get(key)
    if not isinstance(value, list) or len(value) != 3:
        raise ExperimentRunConfigError(f"{key} must contain 3 numeric values")
    result: list[float] = []
    for item in value:
        if not isinstance(item, Real) or isinstance(item, bool):
            raise ExperimentRunConfigError(f"{key} must contain 3 numeric values")
        item_float = float(item)
        if not isfinite(item_float):
            raise ExperimentRunConfigError(f"{key} must contain 3 finite numeric values")
        result.append(item_float)
    return np.asarray(result, dtype=float)


def _require_points(data: dict[str, Any], key: str) -> np.ndarray:
    value = data.get(key)
    if not isinstance(value, list) or len(value) < 4:
        raise ExperimentRunConfigError(f"{key} must contain at least 4 3D points")
    rows: list[list[float]] = []
    for row in value:
        if not isinstance(row, list) or len(row) != 3:
            raise ExperimentRunConfigError(f"{key} must contain 3D points")
        parsed: list[float] = []
        for item in row:
            if not isinstance(item, Real) or isinstance(item, bool):
                raise ExperimentRunConfigError(f"{key} must contain finite numeric 3D points")
            item_float = float(item)
            if not isfinite(item_float):
                raise ExperimentRunConfigError(f"{key} must contain finite numeric 3D points")
            parsed.append(item_float)
        rows.append(parsed)
    return np.asarray(rows, dtype=float)


def _require_positive_mass_vector(data: dict[str, Any], key: str, count: int) -> np.ndarray:
    value = data.get(key)
    if not isinstance(value, list) or len(value) != count:
        raise ExperimentRunConfigError(f"{key} must contain {count} positive masses")
    result: list[float] = []
    for item in value:
        if not isinstance(item, Real) or isinstance(item, bool):
            raise ExperimentRunConfigError(f"{key} must contain finite positive masses")
        item_float = float(item)
        if not isfinite(item_float) or item_float <= 0.0:
            raise ExperimentRunConfigError(f"{key} must contain finite positive masses")
        result.append(item_float)
    return np.asarray(result, dtype=float)


def _require_contact_surface(data: dict[str, Any]) -> dict[str, Any]:
    surface = _require_mapping(data, "contact_surface")
    if _require_str(surface, "type") != "plane":
        raise ExperimentRunConfigError("contact_surface.type must be plane")
    stiffness = _require_positive_float(surface, "stiffness")
    damping = _require_finite_number(surface, "damping")
    if damping < 0.0:
        raise ExperimentRunConfigError("damping must be nonnegative")
    return {
        "type": "plane",
        "plane_normal": _require_vec3_tuple(surface, "plane_normal"),
        "plane_offset": _require_finite_number(surface, "plane_offset"),
        "stiffness": stiffness,
        "damping": damping,
    }


def _require_paper_horizon(data: dict[str, Any]) -> SpinningBoxPaperHorizonConfig:
    horizon = _require_mapping(data, "paper_horizon")
    thresholds = _require_float_mapping(horizon, "thresholds")
    missing = sorted(PAPER_HORIZON_THRESHOLD_KEYS - set(thresholds))
    if missing:
        raise ExperimentRunConfigError(
            "paper_horizon.thresholds missing required keys: " + ", ".join(missing)
        )
    return SpinningBoxPaperHorizonConfig(
        duration_s=_require_positive_float(horizon, "duration_s"),
        time_step_grid_s=_require_positive_float_tuple(horizon, "time_step_grid_s"),
        sample_count=_require_positive_int(horizon, "sample_count"),
        output_report=_require_str(horizon, "output_report"),
        figure_pdf_sha256=_require_str(horizon, "figure_pdf_sha256"),
        figure_text_source=_require_str(horizon, "figure_text_source"),
        thresholds=thresholds,
    )


def _require_physical_pendulum_reference(
    data: dict[str, Any],
) -> PhysicalPendulumReferenceConfig:
    reference = _require_mapping(data, "reference")
    sample_count = _require_positive_int(reference, "sample_count")
    if sample_count < 3:
        raise ExperimentRunConfigError("reference.sample_count must be at least 3")
    return PhysicalPendulumReferenceConfig(
        release_angle_rad=_require_positive_float(reference, "release_angle_rad"),
        initial_angle_rad=_require_finite_number(reference, "initial_angle_rad"),
        kappa=_require_unit_interval_float(reference, "kappa"),
        omega_lin_rad_s=_require_positive_float(reference, "omega_lin_rad_s"),
        period_count=_require_positive_int(reference, "period_count"),
        sample_count=sample_count,
    )


def _require_physical_pendulum_mabd_development(
    data: dict[str, Any],
) -> PhysicalPendulumMABDDevelopmentConfig:
    mabd_development = _require_mapping(data, "mabd_development")
    rest_points = _require_points(mabd_development, "rest_points_m")
    masses = _require_positive_mass_vector(
        mabd_development,
        "masses_kg",
        rest_points.shape[0],
    )
    rank = np.linalg.matrix_rank(rest_points[1:] - rest_points[0], tol=1.0e-12)
    if rank != 3:
        raise ExperimentRunConfigError("mabd_development.rest_points_m must be nondegenerate")

    step_count = _require_positive_int(mabd_development, "step_count")
    sample_count = _require_positive_int(mabd_development, "sample_count")
    if sample_count < 2:
        raise ExperimentRunConfigError("mabd_development.sample_count must be at least 2")
    if sample_count > step_count + 1:
        raise ExperimentRunConfigError("mabd_development.sample_count must be at most step_count + 1")
    thresholds = _require_float_mapping(mabd_development, "thresholds")
    missing = sorted(PHYSICAL_PENDULUM_MABD_DEVELOPMENT_THRESHOLD_KEYS - set(thresholds))
    if missing:
        raise ExperimentRunConfigError(
            "mabd_development.thresholds missing required keys: " + ", ".join(missing)
        )
    pivot_rest = _require_vec3_array(mabd_development, "pivot_rest_point_m")
    angle_probe = _require_vec3_array(mabd_development, "angle_probe_rest_point_m")
    if np.linalg.norm(angle_probe - pivot_rest) <= 1.0e-12:
        raise ExperimentRunConfigError("mabd_development angle probe must be distinct from pivot")
    return PhysicalPendulumMABDDevelopmentConfig(
        time_step_s=_require_positive_float(mabd_development, "time_step_s"),
        step_count=step_count,
        sample_count=sample_count,
        rest_points_m=rest_points,
        masses_kg=masses,
        pivot_rest_point_m=pivot_rest,
        pivot_world_point_m=_require_vec3_array(mabd_development, "pivot_world_point_m"),
        angle_probe_rest_point_m=angle_probe,
        gravity_m_s2=_require_vec3_array(mabd_development, "gravity_m_s2"),
        initial_q=_require_vector(mabd_development, "initial_q"),
        initial_qd=_require_vector(mabd_development, "initial_qd"),
        output_report=_require_str(mabd_development, "output_report"),
        thresholds=thresholds,
    )


def _require_physical_pendulum_rbd_baseline(
    data: dict[str, Any],
) -> PhysicalPendulumRBDBaselineConfig:
    rbd_baseline = _require_mapping(data, "rbd_baseline")
    step_count = _require_positive_int(rbd_baseline, "step_count")
    sample_count = _require_positive_int(rbd_baseline, "sample_count")
    if sample_count < 2:
        raise ExperimentRunConfigError("rbd_baseline.sample_count must be at least 2")
    if sample_count > step_count + 1:
        raise ExperimentRunConfigError("rbd_baseline.sample_count must be at most step_count + 1")
    thresholds = _require_float_mapping(rbd_baseline, "thresholds")
    missing = sorted(PHYSICAL_PENDULUM_RBD_BASELINE_THRESHOLD_KEYS - set(thresholds))
    if missing:
        raise ExperimentRunConfigError(
            "rbd_baseline.thresholds missing required keys: " + ", ".join(missing)
        )
    return PhysicalPendulumRBDBaselineConfig(
        time_step_s=_require_positive_float(rbd_baseline, "time_step_s"),
        step_count=step_count,
        sample_count=sample_count,
        length_m=_require_positive_float(rbd_baseline, "length_m"),
        mass_kg=_require_positive_float(rbd_baseline, "mass_kg"),
        gravity_m_s2=_require_vec3_array(rbd_baseline, "gravity_m_s2"),
        initial_angle_rad=_require_finite_number(rbd_baseline, "initial_angle_rad"),
        initial_angular_velocity_rad_s=_require_finite_number(
            rbd_baseline,
            "initial_angular_velocity_rad_s",
        ),
        newton_iteration_limit=_require_positive_int(rbd_baseline, "newton_iteration_limit"),
        newton_residual_tolerance=_require_positive_float(
            rbd_baseline,
            "newton_residual_tolerance",
        ),
        output_report=_require_str(rbd_baseline, "output_report"),
        thresholds=thresholds,
    )


def load_spinning_box_config(path: str | Path) -> SpinningBoxRunConfig:
    config_path = Path(path)
    data = _read_mapping(config_path)
    if not isinstance(data.get("schema_version"), int) or isinstance(data.get("schema_version"), bool):
        raise ExperimentRunConfigError("schema_version must be 1")
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

    time_step_s = _require_positive_float(simulation, "time_step_s")
    step_count = _require_positive_int(simulation, "step_count")

    return SpinningBoxRunConfig(
        schema_version=1,
        claim_id=claim_id,
        scene_id=_require_str(data, "scene_id"),
        source_lines=_require_str_tuple(data, "source_lines"),
        asset_ids=_require_str_tuple(data, "asset_ids"),
        baseline_lane=_require_str(data, "baseline_lane"),
        required_missing_lanes=_require_str_tuple(
            data,
            "required_missing_lanes",
            allow_empty=True,
        ),
        paper_values=_require_mapping(data, "paper_values"),
        time_step_s=time_step_s,
        step_count=step_count,
        initial_q=_require_vector(simulation, "initial_q"),
        initial_qd=_require_vector(simulation, "initial_qd"),
        mass_diagonal=_require_vector(simulation, "mass_diagonal"),
        contact_surface=_require_contact_surface(data),
        report_status=status,
        failure_reason=_require_str(report, "failure_reason"),
        output_report=_require_str(report, "output_report"),
        thresholds=_require_float_mapping(report, "thresholds"),
        paper_horizon=_require_paper_horizon(data),
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
    if config.paper_values != entry.paper_values:
        raise ExperimentRunConfigError("paper_values must match experiment matrix")
    if config.output_report != entry.output_report:
        raise ExperimentRunConfigError("output_report must match experiment matrix")
    if config.baseline_lane not in entry.required_lanes:
        raise ExperimentRunConfigError("baseline_lane must be listed in required_lanes")
    missing = set(config.required_missing_lanes) - set(entry.required_lanes)
    if missing:
        raise ExperimentRunConfigError("required_missing_lanes must be listed in required_lanes")
    for lane in config.required_missing_lanes:
        if (
            f"{lane}_adapter_missing" not in entry.blocking_reasons
            and f"{lane}_report_incomplete" not in entry.blocking_reasons
        ):
            raise ExperimentRunConfigError("required_missing_lanes must match matrix blocking_reasons")
    if entry.reproduction_status != "blocked_by_baselines":
        raise ExperimentRunConfigError("matrix reproduction_status must remain blocked_by_baselines")
    if "energy_drift" not in entry.metrics or "energy_drift" not in config.thresholds:
        raise ExperimentRunConfigError("energy_drift metric must be present in matrix and thresholds")


def load_physical_pendulum_config(path: str | Path) -> PhysicalPendulumRunConfig:
    config_path = Path(path)
    data = _read_mapping(config_path)
    if not isinstance(data.get("schema_version"), int) or isinstance(data.get("schema_version"), bool):
        raise ExperimentRunConfigError("schema_version must be 1")
    if data.get("schema_version") != 1:
        raise ExperimentRunConfigError("schema_version must be 1")
    claim_id = _require_str(data, "claim_id")
    if claim_id != "experiment.single_body.physical_pendulum":
        raise ExperimentRunConfigError(
            "physical-pendulum config must target experiment.single_body.physical_pendulum"
        )

    report = _require_mapping(data, "report")
    try:
        status = EvidenceStatus(_require_str(report, "status"))
    except ValueError as exc:
        raise ExperimentRunConfigError("report.status is not a known EvidenceStatus") from exc
    if status == EvidenceStatus.PASSED:
        raise ExperimentRunConfigError("passed experiment configs require a dedicated evidence gate")

    thresholds = _require_float_mapping(report, "thresholds")
    missing = sorted(PHYSICAL_PENDULUM_THRESHOLD_KEYS - set(thresholds))
    if missing:
        raise ExperimentRunConfigError(
            "report.thresholds missing required keys: " + ", ".join(missing)
        )

    return PhysicalPendulumRunConfig(
        schema_version=1,
        claim_id=claim_id,
        scene_id=_require_str(data, "scene_id"),
        source_lines=_require_str_tuple(data, "source_lines"),
        asset_ids=_require_str_tuple(data, "asset_ids"),
        baseline_lane=_require_str(data, "baseline_lane"),
        required_missing_lanes=_require_str_tuple(
            data,
            "required_missing_lanes",
            allow_empty=True,
        ),
        paper_values=_require_mapping(data, "paper_values"),
        reference=_require_physical_pendulum_reference(data),
        mabd_development=_require_physical_pendulum_mabd_development(data),
        rbd_baseline=_require_physical_pendulum_rbd_baseline(data),
        report_status=status,
        failure_reason=_require_str(report, "failure_reason"),
        output_report=_require_str(report, "output_report"),
        thresholds=thresholds,
    )


def validate_physical_pendulum_config_against_matrix(
    config: PhysicalPendulumRunConfig,
    matrix: ExperimentMatrix,
) -> None:
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
    if config.paper_values != entry.paper_values:
        raise ExperimentRunConfigError("paper_values must match experiment matrix")
    if config.baseline_lane not in entry.required_lanes:
        raise ExperimentRunConfigError("baseline_lane must be listed in required_lanes")
    missing = set(config.required_missing_lanes) - set(entry.required_lanes)
    if missing:
        raise ExperimentRunConfigError("required_missing_lanes must be listed in required_lanes")
    if config.baseline_lane in config.required_missing_lanes:
        raise ExperimentRunConfigError("baseline_lane cannot be listed as missing")
    if config.required_missing_lanes != PHYSICAL_PENDULUM_REQUIRED_MISSING_LANES:
        raise ExperimentRunConfigError(
            "required_missing_lanes must be mabd_newton and rbd_implicit_baseline"
        )
    if "pendulum_geometry_unknown" not in entry.blocking_reasons:
        raise ExperimentRunConfigError("matrix must retain pendulum_geometry_unknown blocker")
    if entry.reproduction_status != "planned":
        raise ExperimentRunConfigError("matrix reproduction_status must remain planned")
    for metric in ("pendulum_angle_error", "joint_force_error", "phase_drift"):
        if metric not in entry.metrics:
            raise ExperimentRunConfigError("physical pendulum metrics must match the paper matrix")
    reference_initial = pi / 2.0 - 2.0 * asin(config.reference.kappa)
    if not np.isclose(config.reference.release_angle_rad, pi / 2.0, rtol=0.0, atol=1.0e-15):
        raise ExperimentRunConfigError("reference release_angle_rad must match horizontal release")
    if not np.isclose(config.reference.initial_angle_rad, 0.0, rtol=0.0, atol=1.0e-15):
        raise ExperimentRunConfigError("reference initial_angle_rad must match paper zero angle")
    if not np.isclose(reference_initial, config.reference.initial_angle_rad, rtol=0.0, atol=1.0e-15):
        raise ExperimentRunConfigError("reference kappa must match the configured initial angle")
    expected_prefix = Path(entry.output_report).with_suffix("").as_posix() + "_"
    if not config.output_report.startswith(expected_prefix) or not config.output_report.endswith(".json"):
        raise ExperimentRunConfigError("output_report must be a lane-specific report under the matrix stem")
    if (
        not config.mabd_development.output_report.startswith(expected_prefix)
        or not config.mabd_development.output_report.endswith(".json")
    ):
        raise ExperimentRunConfigError(
            "mabd_development.output_report must be a lane-specific report under the matrix stem"
        )
    if config.mabd_development.output_report == config.output_report:
        raise ExperimentRunConfigError("mabd_development.output_report must be separate from analytic output_report")
    if (
        not config.rbd_baseline.output_report.startswith(expected_prefix)
        or not config.rbd_baseline.output_report.endswith(".json")
    ):
        raise ExperimentRunConfigError(
            "rbd_baseline.output_report must be a lane-specific report under the matrix stem"
        )
    if config.rbd_baseline.output_report in (
        config.output_report,
        config.mabd_development.output_report,
    ):
        raise ExperimentRunConfigError("rbd_baseline.output_report must be separate from other lane reports")


__all__ = [
    "ExperimentRunConfigError",
    "PAPER_HORIZON_THRESHOLD_KEYS",
    "PHYSICAL_PENDULUM_REQUIRED_MISSING_LANES",
    "PHYSICAL_PENDULUM_MABD_DEVELOPMENT_THRESHOLD_KEYS",
    "PHYSICAL_PENDULUM_RBD_BASELINE_THRESHOLD_KEYS",
    "PHYSICAL_PENDULUM_THRESHOLD_KEYS",
    "PhysicalPendulumMABDDevelopmentConfig",
    "PhysicalPendulumRBDBaselineConfig",
    "PhysicalPendulumReferenceConfig",
    "PhysicalPendulumRunConfig",
    "SpinningBoxPaperHorizonConfig",
    "SpinningBoxRunConfig",
    "load_physical_pendulum_config",
    "load_spinning_box_config",
    "validate_physical_pendulum_config_against_matrix",
    "validate_spinning_box_config_against_matrix",
]
