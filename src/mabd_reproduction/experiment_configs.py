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
    contact_response_output_report: str
    normal_constraint_output_report: str
    model_plane_constraint_output_report: str
    decoupled_twist_output_report: str
    figure_curve_output_report: str
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
class PhysicalPendulumMABDNewtonConfig:
    rotation_mode: str
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
class PhysicalPendulumComparisonConfig:
    output_report: str
    required_lanes: tuple[str, ...]
    diagnostic_lanes: tuple[str, ...]
    required_metrics: tuple[str, ...]
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
    mabd_newton: PhysicalPendulumMABDNewtonConfig
    rbd_baseline: PhysicalPendulumRBDBaselineConfig
    comparison: PhysicalPendulumComparisonConfig
    report_status: EvidenceStatus
    failure_reason: str
    output_report: str
    thresholds: dict[str, float]


@dataclass(frozen=True)
class THandleReferenceConfig:
    time_step_s: float
    duration_s: float
    sample_count: int
    principal_inertia_kg_m2: np.ndarray
    intermediate_axis_index: int
    initial_angular_velocity_rad_s: np.ndarray
    gravity_m_s2: np.ndarray
    figure_pdf_sha256: str
    figure_text_source: str
    output_report: str
    thresholds: dict[str, float]


@dataclass(frozen=True)
class THandleMABDNewtonConfig:
    time_step_s: float
    step_count: int
    sample_count: int
    rest_points_m: np.ndarray
    point_masses_kg: np.ndarray
    volume_m3: float
    rotation_mode: str
    initial_angular_velocity_rad_s: np.ndarray
    gravity_m_s2: np.ndarray
    output_report: str
    thresholds: dict[str, float]


@dataclass(frozen=True)
class THandleComparisonConfig:
    output_report: str
    required_lanes: tuple[str, ...]
    required_metrics: tuple[str, ...]
    thresholds: dict[str, float]


@dataclass(frozen=True)
class THandleFigureCurvesConfig:
    output_report: str


@dataclass(frozen=True)
class THandleRunConfig:
    schema_version: int
    claim_id: str
    scene_id: str
    source_lines: tuple[str, ...]
    asset_ids: tuple[str, ...]
    baseline_lane: str
    required_missing_lanes: tuple[str, ...]
    paper_values: dict[str, Any]
    reference: THandleReferenceConfig
    mabd_newton: THandleMABDNewtonConfig
    comparison: THandleComparisonConfig
    figure_curves: THandleFigureCurvesConfig
    report_status: EvidenceStatus
    failure_reason: str
    output_report: str
    thresholds: dict[str, float]


@dataclass(frozen=True)
class HeavyTopReferenceConfig:
    time_step_s: float
    duration_s: float
    sample_count: int
    principal_inertia_kg_m2: np.ndarray
    mass_kg: float
    pivot_to_com_m: np.ndarray
    gravity_m_s2: np.ndarray
    initial_tilt_deg: float
    initial_spin_rad_s: float
    figure_pdf_sha256: str
    figure_text_source: str
    output_report: str
    thresholds: dict[str, float]


@dataclass(frozen=True)
class HeavyTopMABDNewtonConfig:
    time_step_s: float
    step_count: int
    sample_count: int
    rest_points_m: np.ndarray
    point_masses_kg: np.ndarray
    pivot_rest_point_m: np.ndarray
    pivot_world_point_m: np.ndarray
    angle_probe_rest_point_m: np.ndarray
    gravity_m_s2: np.ndarray
    rotation_mode: str
    output_report: str
    thresholds: dict[str, float]


@dataclass(frozen=True)
class HeavyTopComparisonConfig:
    output_report: str
    required_lanes: tuple[str, ...]
    required_metrics: tuple[str, ...]
    thresholds: dict[str, float]


@dataclass(frozen=True)
class HeavyTopFigureCurvesConfig:
    output_report: str


@dataclass(frozen=True)
class HeavyTopRunConfig:
    schema_version: int
    claim_id: str
    scene_id: str
    source_lines: tuple[str, ...]
    asset_ids: tuple[str, ...]
    baseline_lane: str
    required_missing_lanes: tuple[str, ...]
    paper_values: dict[str, Any]
    reference: HeavyTopReferenceConfig
    mabd_newton: HeavyTopMABDNewtonConfig
    mabd_paper_horizon: HeavyTopMABDNewtonConfig
    comparison: HeavyTopComparisonConfig
    figure_curves: HeavyTopFigureCurvesConfig
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
PHYSICAL_PENDULUM_MABD_NEWTON_THRESHOLD_KEYS = frozenset(
    {
        "max_abs_angle_error_rad",
        "max_constraint_residual_norm",
        "max_phase_drift_rad",
        "max_pivot_residual_m",
        "max_world_anchor_reaction_magnitude_n",
    }
)
PHYSICAL_PENDULUM_MABD_NEWTON_ROTATION_MODES = frozenset({"polar"})
PHYSICAL_PENDULUM_RBD_BASELINE_THRESHOLD_KEYS = frozenset(
    {
        "max_abs_angle_error_rad",
        "max_implicit_residual",
        "max_length_constraint_error_m",
        "max_phase_drift_rad",
    }
)
PHYSICAL_PENDULUM_COMPARISON_THRESHOLD_KEYS = frozenset(
    {
        "max_mabd_rbd_abs_angle_delta_rad",
    }
)
PHYSICAL_PENDULUM_REQUIRED_MISSING_LANES = ("mabd_newton",)
PHYSICAL_PENDULUM_COMPARISON_REQUIRED_LANES = (
    "mabd_newton",
    "analytic_reference",
    "rbd_implicit_baseline",
)
PHYSICAL_PENDULUM_COMPARISON_DIAGNOSTIC_LANES = (
    "physical_pendulum_mabd_development_diagnostic",
)
PHYSICAL_PENDULUM_COMPARISON_REQUIRED_METRICS = (
    "pendulum_angle_error",
    "joint_force_error",
    "phase_drift",
)
T_HANDLE_THRESHOLD_KEYS = frozenset(
    {
        "max_relative_energy_drift",
        "max_angular_momentum_norm_drift",
        "min_intermediate_axis_sign_flips",
    }
)
T_HANDLE_MABD_NEWTON_THRESHOLD_KEYS = frozenset(
    {
        "max_relative_energy_drift",
        "max_angular_momentum_norm_drift",
        "max_affine_shape_spread_m",
        "max_proxy_inertia_relative_error",
    }
)
T_HANDLE_MABD_NEWTON_ROTATION_MODES = frozenset({"polar"})
T_HANDLE_REQUIRED_MISSING_LANES: tuple[str, ...] = ()
T_HANDLE_COMPARISON_REQUIRED_LANES = ("mabd_newton", "rbd_rk4_reference")
T_HANDLE_COMPARISON_REQUIRED_METRICS = (
    "flip_timing_error",
    "intermediate_axis_angular_velocity_waveform",
    "energy_loss",
)
T_HANDLE_COMPARISON_THRESHOLD_KEYS = frozenset({"max_sample_time_delta_s"})
T_HANDLE_EXPECTED_FIGURE_PDF_SHA256 = (
    "5ae6464fd7e7e6fd471ad56e67cdbead6014736cb731a232ce29d80630a72c1c"
)
T_HANDLE_EXPECTED_FIGURE_TEXT_SOURCE = (
    "pdftotext /tmp/mabd-paper/source/images/T-handle/T-handle.pdf -"
)
T_HANDLE_REQUIRED_BLOCKERS = frozenset(
    {
        "exact_t_handle_geometry_unknown",
        "raw_t_handle_reference_curve_data_missing",
        "mabd_newton_report_incomplete",
        "t_handle_comparison_report_incomplete",
    }
)
HEAVY_TOP_THRESHOLD_KEYS = frozenset(
    {
        "max_relative_energy_drift",
        "min_nutation_angle_range_deg",
        "min_abs_precession_velocity_rad_s",
    }
)
HEAVY_TOP_MABD_NEWTON_THRESHOLD_KEYS = frozenset(
    {
        "max_pivot_residual_m",
        "max_constraint_residual_norm",
        "min_nutation_angle_range_deg",
        "max_affine_shape_spread_m",
    }
)
HEAVY_TOP_MABD_NEWTON_ROTATION_MODES = frozenset({"polar"})
HEAVY_TOP_REQUIRED_MISSING_LANES: tuple[str, ...] = ()
HEAVY_TOP_COMPARISON_REQUIRED_LANES = ("mabd_newton", "rbd_rk4_reference")
HEAVY_TOP_COMPARISON_REQUIRED_METRICS = (
    "precession_velocity_error",
    "nutation_angle_error",
    "energy_drift",
)
HEAVY_TOP_COMPARISON_THRESHOLD_KEYS = frozenset({"max_sample_time_delta_s"})
HEAVY_TOP_EXPECTED_FIGURE_PDF_SHA256 = (
    "c8f5e206415b9feb3578ee32aa3b7284e2695bdd84eeb0200f3b4aa01cf3422d"
)
HEAVY_TOP_EXPECTED_FIGURE_TEXT_SOURCE = (
    "pdftotext /tmp/mabd-paper/source/images/spinning_top/spinning_top.pdf -"
)
HEAVY_TOP_REQUIRED_BLOCKERS = frozenset(
    {
        "exact_heavy_top_inertia_unknown",
        "exact_heavy_top_geometry_unknown",
        "raw_heavy_top_reference_curve_data_missing",
        "mabd_newton_report_incomplete",
        "heavy_top_comparison_report_incomplete",
    }
)


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


def _require_positive_vec3_array(data: dict[str, Any], key: str) -> np.ndarray:
    vector = _require_vec3_array(data, key)
    if np.any(vector <= 0.0):
        raise ExperimentRunConfigError(f"{key} must contain 3 finite positive values")
    return vector


def _require_zero_vec3_array(data: dict[str, Any], key: str) -> np.ndarray:
    vector = _require_vec3_array(data, key)
    if not np.allclose(vector, np.zeros(3), rtol=0.0, atol=1.0e-15):
        raise ExperimentRunConfigError(f"{key} must be zero gravity")
    return vector


def _require_axis_index(data: dict[str, Any], key: str) -> int:
    value = data.get(key)
    if not isinstance(value, Integral) or isinstance(value, bool):
        raise ExperimentRunConfigError(f"{key} must be 0, 1, or 2")
    result = int(value)
    if result not in (0, 1, 2):
        raise ExperimentRunConfigError(f"{key} must be 0, 1, or 2")
    return result


def _require_negative_y_gravity_array(data: dict[str, Any], key: str) -> np.ndarray:
    gravity = _require_vec3_array(data, key)
    if not (
        np.isclose(gravity[0], 0.0, rtol=0.0, atol=1.0e-15)
        and gravity[1] < 0.0
        and np.isclose(gravity[2], 0.0, rtol=0.0, atol=1.0e-15)
    ):
        raise ExperimentRunConfigError(f"{key} must point along the negative y axis")
    return gravity


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
        contact_response_output_report=_require_str(horizon, "contact_response_output_report"),
        normal_constraint_output_report=_require_str(horizon, "normal_constraint_output_report"),
        model_plane_constraint_output_report=_require_str(
            horizon,
            "model_plane_constraint_output_report",
        ),
        decoupled_twist_output_report=_require_str(horizon, "decoupled_twist_output_report"),
        figure_curve_output_report=_require_str(horizon, "figure_curve_output_report"),
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


def _require_physical_pendulum_mabd_newton(
    data: dict[str, Any],
) -> PhysicalPendulumMABDNewtonConfig:
    mabd_newton = _require_mapping(data, "mabd_newton")
    rotation_mode = _require_str(mabd_newton, "rotation_mode")
    if rotation_mode not in PHYSICAL_PENDULUM_MABD_NEWTON_ROTATION_MODES:
        raise ExperimentRunConfigError("mabd_newton.rotation_mode must be polar")
    thresholds = _require_float_mapping(mabd_newton, "thresholds")
    missing = sorted(PHYSICAL_PENDULUM_MABD_NEWTON_THRESHOLD_KEYS - set(thresholds))
    if missing:
        raise ExperimentRunConfigError(
            "mabd_newton.thresholds missing required keys: " + ", ".join(missing)
        )
    return PhysicalPendulumMABDNewtonConfig(
        rotation_mode=rotation_mode,
        output_report=_require_str(mabd_newton, "output_report"),
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
        gravity_m_s2=_require_negative_y_gravity_array(rbd_baseline, "gravity_m_s2"),
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


def _require_physical_pendulum_comparison(
    data: dict[str, Any],
) -> PhysicalPendulumComparisonConfig:
    comparison = _require_mapping(data, "comparison")
    required_lanes = _require_str_tuple(comparison, "required_lanes")
    if required_lanes != PHYSICAL_PENDULUM_COMPARISON_REQUIRED_LANES:
        raise ExperimentRunConfigError("comparison.required_lanes must match physical-pendulum paper lanes")
    diagnostic_lanes = _require_str_tuple(comparison, "diagnostic_lanes")
    if diagnostic_lanes != PHYSICAL_PENDULUM_COMPARISON_DIAGNOSTIC_LANES:
        raise ExperimentRunConfigError(
            "comparison.diagnostic_lanes must match current physical-pendulum diagnostics"
        )
    required_metrics = _require_str_tuple(comparison, "required_metrics")
    if required_metrics != PHYSICAL_PENDULUM_COMPARISON_REQUIRED_METRICS:
        raise ExperimentRunConfigError(
            "comparison.required_metrics must match physical-pendulum matrix metrics"
        )
    if not isinstance(comparison.get("thresholds"), dict) or not comparison["thresholds"]:
        raise ExperimentRunConfigError("comparison.thresholds must be a non-empty mapping")
    thresholds = _require_float_mapping(comparison, "thresholds")
    missing = sorted(PHYSICAL_PENDULUM_COMPARISON_THRESHOLD_KEYS - set(thresholds))
    if missing:
        raise ExperimentRunConfigError(
            "comparison.thresholds missing required keys: " + ", ".join(missing)
        )
    return PhysicalPendulumComparisonConfig(
        output_report=_require_str(comparison, "output_report"),
        required_lanes=required_lanes,
        diagnostic_lanes=diagnostic_lanes,
        required_metrics=required_metrics,
        thresholds=thresholds,
    )


def _require_t_handle_reference(data: dict[str, Any]) -> THandleReferenceConfig:
    reference = _require_mapping(data, "reference")
    thresholds = _require_float_mapping(reference, "thresholds")
    missing = sorted(T_HANDLE_THRESHOLD_KEYS - set(thresholds))
    if missing:
        raise ExperimentRunConfigError(
            "reference.thresholds missing required keys: " + ", ".join(missing)
        )
    sample_count = _require_positive_int(reference, "sample_count")
    if sample_count < 2:
        raise ExperimentRunConfigError("reference.sample_count must be at least 2")
    time_step_s = _require_positive_float(reference, "time_step_s")
    duration_s = _require_positive_float(reference, "duration_s")
    step_count_float = duration_s / time_step_s
    step_count = round(step_count_float)
    if not np.isclose(step_count_float, float(step_count), rtol=0.0, atol=1.0e-10):
        raise ExperimentRunConfigError("reference duration_s must be an integer multiple of time_step_s")
    if sample_count > step_count + 1:
        raise ExperimentRunConfigError("reference.sample_count must be at most step_count + 1")
    return THandleReferenceConfig(
        time_step_s=time_step_s,
        duration_s=duration_s,
        sample_count=sample_count,
        principal_inertia_kg_m2=_require_positive_vec3_array(
            reference,
            "principal_inertia_kg_m2",
        ),
        intermediate_axis_index=_require_axis_index(reference, "intermediate_axis_index"),
        initial_angular_velocity_rad_s=_require_vec3_array(
            reference,
            "initial_angular_velocity_rad_s",
        ),
        gravity_m_s2=_require_zero_vec3_array(reference, "gravity_m_s2"),
        figure_pdf_sha256=_require_str(reference, "figure_pdf_sha256"),
        figure_text_source=_require_str(reference, "figure_text_source"),
        output_report=_require_str(reference, "output_report"),
        thresholds=thresholds,
    )


def _require_t_handle_mabd_newton(data: dict[str, Any]) -> THandleMABDNewtonConfig:
    mabd_newton = _require_mapping(data, "mabd_newton")
    rest_points = _require_points(mabd_newton, "rest_points_m")
    if rest_points.shape != (4, 3):
        raise ExperimentRunConfigError("mabd_newton.rest_points_m must contain exactly 4 3D points")
    rank = np.linalg.matrix_rank(rest_points[1:] - rest_points[0], tol=1.0e-12)
    if rank != 3:
        raise ExperimentRunConfigError("mabd_newton.rest_points_m must be nondegenerate")
    masses = _require_positive_mass_vector(mabd_newton, "point_masses_kg", 4)
    step_count = _require_positive_int(mabd_newton, "step_count")
    sample_count = _require_positive_int(mabd_newton, "sample_count")
    if sample_count < 2:
        raise ExperimentRunConfigError("mabd_newton.sample_count must be at least 2")
    if sample_count > step_count + 1:
        raise ExperimentRunConfigError("mabd_newton.sample_count must be at most step_count + 1")
    rotation_mode = _require_str(mabd_newton, "rotation_mode")
    if rotation_mode not in T_HANDLE_MABD_NEWTON_ROTATION_MODES:
        raise ExperimentRunConfigError("mabd_newton.rotation_mode must be polar")
    thresholds = _require_float_mapping(mabd_newton, "thresholds")
    missing = sorted(T_HANDLE_MABD_NEWTON_THRESHOLD_KEYS - set(thresholds))
    if missing:
        raise ExperimentRunConfigError(
            "mabd_newton.thresholds missing required keys: " + ", ".join(missing)
        )
    try:
        gravity_m_s2 = _require_zero_vec3_array(mabd_newton, "gravity_m_s2")
    except ExperimentRunConfigError as exc:
        raise ExperimentRunConfigError("mabd_newton.gravity_m_s2 must be zero gravity") from exc
    initial_angular_velocity = _require_vec3_array(
        mabd_newton,
        "initial_angular_velocity_rad_s",
    )
    if np.linalg.norm(initial_angular_velocity) <= 1.0e-15:
        raise ExperimentRunConfigError("mabd_newton.initial_angular_velocity_rad_s must be nonzero")
    return THandleMABDNewtonConfig(
        time_step_s=_require_positive_float(mabd_newton, "time_step_s"),
        step_count=step_count,
        sample_count=sample_count,
        rest_points_m=rest_points,
        point_masses_kg=masses,
        volume_m3=_require_positive_float(mabd_newton, "volume_m3"),
        rotation_mode=rotation_mode,
        initial_angular_velocity_rad_s=initial_angular_velocity,
        gravity_m_s2=gravity_m_s2,
        output_report=_require_str(mabd_newton, "output_report"),
        thresholds=thresholds,
    )


def _require_t_handle_comparison(data: dict[str, Any]) -> THandleComparisonConfig:
    comparison = _require_mapping(data, "comparison")
    required_lanes = _require_str_tuple(comparison, "required_lanes")
    if required_lanes != T_HANDLE_COMPARISON_REQUIRED_LANES:
        raise ExperimentRunConfigError("comparison.required_lanes must match T-handle paper lanes")
    required_metrics = _require_str_tuple(comparison, "required_metrics")
    if required_metrics != T_HANDLE_COMPARISON_REQUIRED_METRICS:
        raise ExperimentRunConfigError("comparison.required_metrics must match T-handle matrix metrics")
    if not isinstance(comparison.get("thresholds"), dict) or not comparison["thresholds"]:
        raise ExperimentRunConfigError("comparison.thresholds must be a non-empty mapping")
    thresholds = _require_float_mapping(comparison, "thresholds")
    missing = sorted(T_HANDLE_COMPARISON_THRESHOLD_KEYS - set(thresholds))
    if missing:
        raise ExperimentRunConfigError(
            "comparison.thresholds missing required keys: " + ", ".join(missing)
        )
    if thresholds["max_sample_time_delta_s"] < 0.0:
        raise ExperimentRunConfigError("comparison.thresholds.max_sample_time_delta_s must be nonnegative")
    return THandleComparisonConfig(
        output_report=_require_str(comparison, "output_report"),
        required_lanes=required_lanes,
        required_metrics=required_metrics,
        thresholds=thresholds,
    )


def _require_t_handle_figure_curves(data: dict[str, Any]) -> THandleFigureCurvesConfig:
    figure_curves = _require_mapping(data, "figure_curves")
    return THandleFigureCurvesConfig(
        output_report=_require_str(figure_curves, "output_report"),
    )


def _require_heavy_top_reference(data: dict[str, Any]) -> HeavyTopReferenceConfig:
    reference = _require_mapping(data, "reference")
    thresholds = _require_float_mapping(reference, "thresholds")
    missing = sorted(HEAVY_TOP_THRESHOLD_KEYS - set(thresholds))
    if missing:
        raise ExperimentRunConfigError(
            "reference.thresholds missing required keys: " + ", ".join(missing)
        )
    sample_count = _require_positive_int(reference, "sample_count")
    if sample_count < 2:
        raise ExperimentRunConfigError("reference.sample_count must be at least 2")
    time_step_s = _require_positive_float(reference, "time_step_s")
    duration_s = _require_positive_float(reference, "duration_s")
    step_count_float = duration_s / time_step_s
    step_count = round(step_count_float)
    if not np.isclose(step_count_float, float(step_count), rtol=0.0, atol=1.0e-10):
        raise ExperimentRunConfigError("reference duration_s must be an integer multiple of time_step_s")
    if sample_count > step_count + 1:
        raise ExperimentRunConfigError("reference.sample_count must be at most step_count + 1")
    pivot_to_com = _require_vec3_array(reference, "pivot_to_com_m")
    if np.linalg.norm(pivot_to_com) <= 0.0:
        raise ExperimentRunConfigError("reference.pivot_to_com_m must be nonzero")
    return HeavyTopReferenceConfig(
        time_step_s=time_step_s,
        duration_s=duration_s,
        sample_count=sample_count,
        principal_inertia_kg_m2=_require_positive_vec3_array(
            reference,
            "principal_inertia_kg_m2",
        ),
        mass_kg=_require_positive_float(reference, "mass_kg"),
        pivot_to_com_m=pivot_to_com,
        gravity_m_s2=_require_negative_y_gravity_array(reference, "gravity_m_s2"),
        initial_tilt_deg=_require_positive_float(reference, "initial_tilt_deg"),
        initial_spin_rad_s=_require_positive_float(reference, "initial_spin_rad_s"),
        figure_pdf_sha256=_require_str(reference, "figure_pdf_sha256"),
        figure_text_source=_require_str(reference, "figure_text_source"),
        output_report=_require_str(reference, "output_report"),
        thresholds=thresholds,
    )


def _require_heavy_top_mabd_lane(
    data: dict[str, Any],
    key: str,
) -> HeavyTopMABDNewtonConfig:
    mabd_newton = _require_mapping(data, key)
    rest_points = _require_points(mabd_newton, "rest_points_m")
    if rest_points.shape != (4, 3):
        raise ExperimentRunConfigError(f"{key}.rest_points_m must contain exactly 4 3D points")
    basis = np.column_stack(
        (
            rest_points[1] - rest_points[0],
            rest_points[2] - rest_points[0],
            rest_points[3] - rest_points[0],
        )
    )
    if abs(float(np.linalg.det(basis))) <= 1.0e-12:
        raise ExperimentRunConfigError(f"{key}.rest_points_m must be nondegenerate")

    step_count = _require_positive_int(mabd_newton, "step_count")
    sample_count = _require_positive_int(mabd_newton, "sample_count")
    if sample_count < 2:
        raise ExperimentRunConfigError(f"{key}.sample_count must be at least 2")
    if sample_count > step_count + 1:
        raise ExperimentRunConfigError(f"{key}.sample_count must be at most step_count + 1")

    thresholds = _require_float_mapping(mabd_newton, "thresholds")
    missing = sorted(HEAVY_TOP_MABD_NEWTON_THRESHOLD_KEYS - set(thresholds))
    if missing:
        raise ExperimentRunConfigError(
            f"{key}.thresholds missing required keys: " + ", ".join(missing)
        )

    pivot_rest = _require_vec3_array(mabd_newton, "pivot_rest_point_m")
    angle_probe = _require_vec3_array(mabd_newton, "angle_probe_rest_point_m")
    if np.linalg.norm(angle_probe - pivot_rest) <= 1.0e-12:
        raise ExperimentRunConfigError(f"{key} angle probe must be distinct from pivot")

    rotation_mode = _require_str(mabd_newton, "rotation_mode")
    if rotation_mode not in HEAVY_TOP_MABD_NEWTON_ROTATION_MODES:
        raise ExperimentRunConfigError(f"{key}.rotation_mode must be polar")

    return HeavyTopMABDNewtonConfig(
        time_step_s=_require_positive_float(mabd_newton, "time_step_s"),
        step_count=step_count,
        sample_count=sample_count,
        rest_points_m=rest_points,
        point_masses_kg=_require_positive_mass_vector(
            mabd_newton,
            "point_masses_kg",
            rest_points.shape[0],
        ),
        pivot_rest_point_m=pivot_rest,
        pivot_world_point_m=_require_vec3_array(mabd_newton, "pivot_world_point_m"),
        angle_probe_rest_point_m=angle_probe,
        gravity_m_s2=_require_negative_y_gravity_array(mabd_newton, "gravity_m_s2"),
        rotation_mode=rotation_mode,
        output_report=_require_str(mabd_newton, "output_report"),
        thresholds=thresholds,
    )


def _require_heavy_top_mabd_newton(data: dict[str, Any]) -> HeavyTopMABDNewtonConfig:
    return _require_heavy_top_mabd_lane(data, "mabd_newton")


def _require_heavy_top_mabd_paper_horizon(
    data: dict[str, Any],
) -> HeavyTopMABDNewtonConfig:
    return _require_heavy_top_mabd_lane(data, "mabd_paper_horizon")


def _require_heavy_top_paper_horizon_alignment(config: HeavyTopRunConfig) -> None:
    lane = config.mabd_paper_horizon
    reference = config.reference
    short_lane = config.mabd_newton
    duration = lane.step_count * lane.time_step_s
    if not np.isclose(duration, reference.duration_s, rtol=0.0, atol=1.0e-12):
        raise ExperimentRunConfigError(
            "mabd_paper_horizon step_count*time_step_s must match reference.duration_s"
        )
    if lane.sample_count != reference.sample_count:
        raise ExperimentRunConfigError(
            "mabd_paper_horizon.sample_count must match reference.sample_count"
        )
    if lane.step_count % (lane.sample_count - 1) != 0:
        raise ExperimentRunConfigError(
            "mabd_paper_horizon sample grid must divide step_count evenly"
        )
    if lane.output_report == short_lane.output_report:
        raise ExperimentRunConfigError(
            "mabd_paper_horizon.output_report must be separate from mabd_newton.output_report"
        )
    if not np.allclose(lane.rest_points_m, short_lane.rest_points_m, rtol=0.0, atol=1.0e-15):
        raise ExperimentRunConfigError(
            "mabd_paper_horizon.rest_points_m must match mabd_newton.rest_points_m"
        )
    if not np.allclose(
        lane.point_masses_kg,
        short_lane.point_masses_kg,
        rtol=0.0,
        atol=1.0e-15,
    ):
        raise ExperimentRunConfigError(
            "mabd_paper_horizon.point_masses_kg must match mabd_newton.point_masses_kg"
        )
    if not np.allclose(
        lane.pivot_rest_point_m,
        short_lane.pivot_rest_point_m,
        rtol=0.0,
        atol=1.0e-15,
    ):
        raise ExperimentRunConfigError(
            "mabd_paper_horizon.pivot_rest_point_m must match mabd_newton.pivot_rest_point_m"
        )
    if not np.allclose(
        lane.pivot_world_point_m,
        short_lane.pivot_world_point_m,
        rtol=0.0,
        atol=1.0e-15,
    ):
        raise ExperimentRunConfigError(
            "mabd_paper_horizon.pivot_world_point_m must match mabd_newton.pivot_world_point_m"
        )
    if not np.allclose(
        lane.angle_probe_rest_point_m,
        short_lane.angle_probe_rest_point_m,
        rtol=0.0,
        atol=1.0e-15,
    ):
        raise ExperimentRunConfigError(
            "mabd_paper_horizon.angle_probe_rest_point_m must match mabd_newton.angle_probe_rest_point_m"
        )
    if lane.rotation_mode != short_lane.rotation_mode:
        raise ExperimentRunConfigError(
            "mabd_paper_horizon.rotation_mode must match mabd_newton.rotation_mode"
        )
    if lane.thresholds != short_lane.thresholds:
        raise ExperimentRunConfigError(
            "mabd_paper_horizon.thresholds must match mabd_newton.thresholds"
        )


def _require_heavy_top_comparison(data: dict[str, Any]) -> HeavyTopComparisonConfig:
    comparison = _require_mapping(data, "comparison")
    required_lanes = _require_str_tuple(comparison, "required_lanes")
    if required_lanes != HEAVY_TOP_COMPARISON_REQUIRED_LANES:
        raise ExperimentRunConfigError("comparison.required_lanes must match heavy-top paper lanes")
    required_metrics = _require_str_tuple(comparison, "required_metrics")
    if required_metrics != HEAVY_TOP_COMPARISON_REQUIRED_METRICS:
        raise ExperimentRunConfigError("comparison.required_metrics must match heavy-top matrix metrics")
    if not isinstance(comparison.get("thresholds"), dict) or not comparison["thresholds"]:
        raise ExperimentRunConfigError("comparison.thresholds must be a non-empty mapping")
    thresholds = _require_float_mapping(comparison, "thresholds")
    missing = sorted(HEAVY_TOP_COMPARISON_THRESHOLD_KEYS - set(thresholds))
    if missing:
        raise ExperimentRunConfigError(
            "comparison.thresholds missing required keys: " + ", ".join(missing)
        )
    return HeavyTopComparisonConfig(
        output_report=_require_str(comparison, "output_report"),
        required_lanes=required_lanes,
        required_metrics=required_metrics,
        thresholds=thresholds,
    )


def _require_heavy_top_figure_curves(data: dict[str, Any]) -> HeavyTopFigureCurvesConfig:
    figure_curves = _require_mapping(data, "figure_curves")
    return HeavyTopFigureCurvesConfig(
        output_report=_require_str(figure_curves, "output_report"),
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
    expected_prefix = Path(entry.output_report).with_suffix("").as_posix() + "_"
    if (
        not config.paper_horizon.figure_curve_output_report.startswith(expected_prefix)
        or not config.paper_horizon.figure_curve_output_report.endswith(".json")
    ):
        raise ExperimentRunConfigError(
            "paper_horizon.figure_curve_output_report must be a lane-specific report under the matrix stem"
        )
    if config.paper_horizon.figure_curve_output_report in (
        config.output_report,
        config.paper_horizon.output_report,
        config.paper_horizon.contact_response_output_report,
        config.paper_horizon.normal_constraint_output_report,
        config.paper_horizon.decoupled_twist_output_report,
    ):
        raise ExperimentRunConfigError(
            "paper_horizon.figure_curve_output_report must be separate from lane reports"
        )
    if (
        not config.paper_horizon.model_plane_constraint_output_report.startswith(expected_prefix)
        or not config.paper_horizon.model_plane_constraint_output_report.endswith(".json")
    ):
        raise ExperimentRunConfigError(
            "paper_horizon.model_plane_constraint_output_report must be a lane-specific report under the matrix stem"
        )
    if config.paper_horizon.model_plane_constraint_output_report in (
        config.output_report,
        config.paper_horizon.output_report,
        config.paper_horizon.contact_response_output_report,
        config.paper_horizon.normal_constraint_output_report,
        config.paper_horizon.decoupled_twist_output_report,
        config.paper_horizon.figure_curve_output_report,
    ):
        raise ExperimentRunConfigError(
            "paper_horizon.model_plane_constraint_output_report must be separate from lane reports"
        )


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
        mabd_newton=_require_physical_pendulum_mabd_newton(data),
        rbd_baseline=_require_physical_pendulum_rbd_baseline(data),
        comparison=_require_physical_pendulum_comparison(data),
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
        raise ExperimentRunConfigError("required_missing_lanes must be mabd_newton only")
    if "pendulum_geometry_unknown" not in entry.blocking_reasons:
        raise ExperimentRunConfigError("matrix must retain pendulum_geometry_unknown blocker")
    if entry.reproduction_status != "planned":
        raise ExperimentRunConfigError("matrix reproduction_status must remain planned")
    for metric in ("pendulum_angle_error", "joint_force_error", "phase_drift"):
        if metric not in entry.metrics:
            raise ExperimentRunConfigError("physical pendulum metrics must match the paper matrix")
    if set(config.comparison.required_lanes) != set(entry.required_lanes):
        raise ExperimentRunConfigError("comparison.required_lanes must match experiment matrix")
    if config.comparison.required_metrics != entry.metrics:
        raise ExperimentRunConfigError("comparison.required_metrics must match experiment matrix")
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
        not config.mabd_newton.output_report.startswith(expected_prefix)
        or not config.mabd_newton.output_report.endswith(".json")
    ):
        raise ExperimentRunConfigError(
            "mabd_newton.output_report must be a lane-specific report under the matrix stem"
        )
    if config.mabd_newton.output_report in (
        config.output_report,
        config.mabd_development.output_report,
    ):
        raise ExperimentRunConfigError("mabd_newton.output_report must be separate from other lane reports")
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
        config.mabd_newton.output_report,
    ):
        raise ExperimentRunConfigError("rbd_baseline.output_report must be separate from other lane reports")
    if (
        not config.comparison.output_report.startswith(expected_prefix)
        or not config.comparison.output_report.endswith(".json")
    ):
        raise ExperimentRunConfigError(
            "comparison.output_report must be a lane-specific report under the matrix stem"
        )
    if config.comparison.output_report in (
        config.output_report,
        config.mabd_development.output_report,
        config.mabd_newton.output_report,
        config.rbd_baseline.output_report,
    ):
        raise ExperimentRunConfigError("comparison.output_report must be separate from other lane reports")


def load_t_handle_config(path: str | Path) -> THandleRunConfig:
    config_path = Path(path)
    data = _read_mapping(config_path)
    if not isinstance(data.get("schema_version"), int) or isinstance(data.get("schema_version"), bool):
        raise ExperimentRunConfigError("schema_version must be 1")
    if data.get("schema_version") != 1:
        raise ExperimentRunConfigError("schema_version must be 1")
    claim_id = _require_str(data, "claim_id")
    if claim_id != "experiment.single_body.t_handle":
        raise ExperimentRunConfigError("T-handle config must target experiment.single_body.t_handle")

    report = _require_mapping(data, "report")
    try:
        status = EvidenceStatus(_require_str(report, "status"))
    except ValueError as exc:
        raise ExperimentRunConfigError("report.status is not a known EvidenceStatus") from exc
    if status == EvidenceStatus.PASSED:
        raise ExperimentRunConfigError("passed experiment configs require a dedicated evidence gate")

    thresholds = _require_float_mapping(report, "thresholds")
    missing = sorted(T_HANDLE_THRESHOLD_KEYS - set(thresholds))
    if missing:
        raise ExperimentRunConfigError(
            "report.thresholds missing required keys: " + ", ".join(missing)
        )

    config = THandleRunConfig(
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
        reference=_require_t_handle_reference(data),
        mabd_newton=_require_t_handle_mabd_newton(data),
        comparison=_require_t_handle_comparison(data),
        figure_curves=_require_t_handle_figure_curves(data),
        report_status=status,
        failure_reason=_require_str(report, "failure_reason"),
        output_report=_require_str(report, "output_report"),
        thresholds=thresholds,
    )
    mabd_duration = config.mabd_newton.step_count * config.mabd_newton.time_step_s
    if not np.isclose(mabd_duration, config.reference.duration_s, rtol=0.0, atol=1.0e-12):
        raise ExperimentRunConfigError("mabd_newton step_count*time_step_s must match reference.duration_s")
    if config.mabd_newton.sample_count != config.reference.sample_count:
        raise ExperimentRunConfigError("mabd_newton.sample_count must match reference.sample_count")
    if not np.allclose(
        config.mabd_newton.initial_angular_velocity_rad_s,
        config.reference.initial_angular_velocity_rad_s,
        rtol=0.0,
        atol=1.0e-15,
    ):
        raise ExperimentRunConfigError(
            "mabd_newton.initial_angular_velocity_rad_s must match reference"
        )
    return config


def validate_t_handle_config_against_matrix(
    config: THandleRunConfig,
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
    if config.baseline_lane != "rbd_rk4_reference":
        raise ExperimentRunConfigError("baseline_lane must be rbd_rk4_reference")
    if config.baseline_lane not in entry.required_lanes:
        raise ExperimentRunConfigError("baseline_lane must be listed in required_lanes")
    if config.required_missing_lanes != T_HANDLE_REQUIRED_MISSING_LANES:
        raise ExperimentRunConfigError("required_missing_lanes must be empty after Phase 57")
    missing_lanes = set(config.required_missing_lanes) - set(entry.required_lanes)
    if missing_lanes:
        raise ExperimentRunConfigError("required_missing_lanes must be listed in required_lanes")
    if config.baseline_lane in config.required_missing_lanes:
        raise ExperimentRunConfigError("baseline_lane cannot be listed as missing")
    blockers = set(entry.blocking_reasons)
    missing_blockers = sorted(T_HANDLE_REQUIRED_BLOCKERS - blockers)
    if missing_blockers:
        raise ExperimentRunConfigError(
            "T-handle matrix blockers missing: " + ", ".join(missing_blockers)
        )
    if "mabd_newton_report_missing" in blockers:
        raise ExperimentRunConfigError("T-handle matrix must use mabd_newton_report_incomplete")
    if "t_handle_comparison_report_missing" in blockers:
        raise ExperimentRunConfigError(
            "T-handle matrix must use t_handle_comparison_report_incomplete"
        )
    if entry.reproduction_status != "planned":
        raise ExperimentRunConfigError("matrix reproduction_status must remain planned")
    for metric in (
        "flip_timing_error",
        "intermediate_axis_angular_velocity_waveform",
        "energy_loss",
    ):
        if metric not in entry.metrics:
            raise ExperimentRunConfigError("T-handle metrics must match the paper matrix")
    if config.comparison.required_lanes != T_HANDLE_COMPARISON_REQUIRED_LANES:
        raise ExperimentRunConfigError("comparison.required_lanes must match T-handle paper lanes")
    if set(config.comparison.required_lanes) != set(entry.required_lanes):
        raise ExperimentRunConfigError("comparison.required_lanes must match experiment matrix")
    if config.comparison.required_metrics != entry.metrics:
        raise ExperimentRunConfigError("comparison.required_metrics must match experiment matrix")
    if config.reference.figure_pdf_sha256 != T_HANDLE_EXPECTED_FIGURE_PDF_SHA256:
        raise ExperimentRunConfigError("reference.figure_pdf_sha256 changed")
    if config.reference.figure_text_source != T_HANDLE_EXPECTED_FIGURE_TEXT_SOURCE:
        raise ExperimentRunConfigError("reference.figure_text_source changed")
    if not np.allclose(config.reference.gravity_m_s2, np.zeros(3), rtol=0.0, atol=1.0e-15):
        raise ExperimentRunConfigError("reference.gravity_m_s2 must be zero gravity")
    expected_prefix = Path(entry.output_report).with_suffix("").as_posix() + "_"
    if (
        not config.reference.output_report.startswith(expected_prefix)
        or not config.reference.output_report.endswith(".json")
    ):
        raise ExperimentRunConfigError(
            "reference.output_report must be a lane-specific report under the matrix stem"
        )
    if config.output_report != config.reference.output_report:
        raise ExperimentRunConfigError("output_report must match reference.output_report")
    if (
        not config.mabd_newton.output_report.startswith(expected_prefix)
        or not config.mabd_newton.output_report.endswith(".json")
    ):
        raise ExperimentRunConfigError(
            "mabd_newton.output_report must be a lane-specific report under the matrix stem"
        )
    if config.mabd_newton.output_report == config.reference.output_report:
        raise ExperimentRunConfigError("mabd_newton.output_report must be separate from reference output_report")
    if (
        not config.comparison.output_report.startswith(expected_prefix)
        or not config.comparison.output_report.endswith(".json")
    ):
        raise ExperimentRunConfigError(
            "comparison.output_report must be a lane-specific report under the matrix stem"
        )
    if config.comparison.output_report in (
        config.reference.output_report,
        config.mabd_newton.output_report,
    ):
        raise ExperimentRunConfigError("comparison.output_report must be separate from other lane reports")
    if (
        not config.figure_curves.output_report.startswith(expected_prefix)
        or not config.figure_curves.output_report.endswith(".json")
    ):
        raise ExperimentRunConfigError(
            "figure_curves.output_report must be a lane-specific report under the matrix stem"
        )
    if config.figure_curves.output_report in (
        config.reference.output_report,
        config.mabd_newton.output_report,
        config.comparison.output_report,
    ):
        raise ExperimentRunConfigError("figure_curves.output_report must be separate from lane reports")
    mabd_duration = config.mabd_newton.step_count * config.mabd_newton.time_step_s
    if not np.isclose(mabd_duration, config.reference.duration_s, rtol=0.0, atol=1.0e-12):
        raise ExperimentRunConfigError("mabd_newton step_count*time_step_s must match reference.duration_s")
    if config.mabd_newton.sample_count != config.reference.sample_count:
        raise ExperimentRunConfigError("mabd_newton.sample_count must match reference.sample_count")
    if not np.allclose(
        config.mabd_newton.initial_angular_velocity_rad_s,
        config.reference.initial_angular_velocity_rad_s,
        rtol=0.0,
        atol=1.0e-15,
    ):
        raise ExperimentRunConfigError(
            "mabd_newton.initial_angular_velocity_rad_s must match reference"
        )
    if not np.allclose(config.mabd_newton.gravity_m_s2, np.zeros(3), rtol=0.0, atol=1.0e-15):
        raise ExperimentRunConfigError("mabd_newton.gravity_m_s2 must remain zero")
    for blocker in T_HANDLE_REQUIRED_BLOCKERS:
        if blocker not in config.failure_reason:
            raise ExperimentRunConfigError(f"report.failure_reason missing {blocker}")


def load_heavy_top_config(path: str | Path) -> HeavyTopRunConfig:
    config_path = Path(path)
    data = _read_mapping(config_path)
    if not isinstance(data.get("schema_version"), int) or isinstance(data.get("schema_version"), bool):
        raise ExperimentRunConfigError("schema_version must be 1")
    if data.get("schema_version") != 1:
        raise ExperimentRunConfigError("schema_version must be 1")
    claim_id = _require_str(data, "claim_id")
    if claim_id != "experiment.single_body.heavy_top":
        raise ExperimentRunConfigError("heavy-top config must target experiment.single_body.heavy_top")

    report = _require_mapping(data, "report")
    try:
        status = EvidenceStatus(_require_str(report, "status"))
    except ValueError as exc:
        raise ExperimentRunConfigError("report.status is not a known EvidenceStatus") from exc
    if status == EvidenceStatus.PASSED:
        raise ExperimentRunConfigError("passed experiment configs require a dedicated evidence gate")

    thresholds = _require_float_mapping(report, "thresholds")
    missing = sorted(HEAVY_TOP_THRESHOLD_KEYS - set(thresholds))
    if missing:
        raise ExperimentRunConfigError(
            "report.thresholds missing required keys: " + ", ".join(missing)
        )

    config = HeavyTopRunConfig(
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
        reference=_require_heavy_top_reference(data),
        mabd_newton=_require_heavy_top_mabd_newton(data),
        mabd_paper_horizon=_require_heavy_top_mabd_paper_horizon(data),
        comparison=_require_heavy_top_comparison(data),
        figure_curves=_require_heavy_top_figure_curves(data),
        report_status=status,
        failure_reason=_require_str(report, "failure_reason"),
        output_report=_require_str(report, "output_report"),
        thresholds=thresholds,
    )
    _require_heavy_top_paper_horizon_alignment(config)
    return config


def validate_heavy_top_config_against_matrix(
    config: HeavyTopRunConfig,
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
    paper_reference_pairs = (
        ("tilt_deg", config.reference.initial_tilt_deg),
        ("angular_speed_rad_s", config.reference.initial_spin_rad_s),
        ("reference_h_s", config.reference.time_step_s),
    )
    for key, expected in paper_reference_pairs:
        value = config.paper_values.get(key)
        if not isinstance(value, Real) or isinstance(value, bool):
            raise ExperimentRunConfigError(f"paper_values.{key} must be numeric")
        numeric = float(value)
        if not isfinite(numeric) or not np.isclose(numeric, expected, rtol=0.0, atol=1.0e-15):
            raise ExperimentRunConfigError(
                f"paper_values.{key} must match the configured heavy-top reference"
            )
    if config.baseline_lane != "rbd_rk4_reference":
        raise ExperimentRunConfigError("baseline_lane must be rbd_rk4_reference")
    if config.baseline_lane not in entry.required_lanes:
        raise ExperimentRunConfigError("baseline_lane must be listed in required_lanes")
    if config.required_missing_lanes != HEAVY_TOP_REQUIRED_MISSING_LANES:
        raise ExperimentRunConfigError("required_missing_lanes must be empty after Phase 50")
    missing_lanes = set(config.required_missing_lanes) - set(entry.required_lanes)
    if missing_lanes:
        raise ExperimentRunConfigError("required_missing_lanes must be listed in required_lanes")
    if config.baseline_lane in config.required_missing_lanes:
        raise ExperimentRunConfigError("baseline_lane cannot be listed as missing")
    blockers = set(entry.blocking_reasons)
    missing_blockers = sorted(HEAVY_TOP_REQUIRED_BLOCKERS - blockers)
    if missing_blockers:
        raise ExperimentRunConfigError(
            "heavy-top matrix blockers missing: " + ", ".join(missing_blockers)
        )
    if "mabd_newton_report_missing" in blockers:
        raise ExperimentRunConfigError("heavy-top matrix must use mabd_newton_report_incomplete")
    if entry.reproduction_status != "planned":
        raise ExperimentRunConfigError("matrix reproduction_status must remain planned")
    for metric in ("precession_velocity_error", "nutation_angle_error", "energy_drift"):
        if metric not in entry.metrics:
            raise ExperimentRunConfigError("heavy-top metrics must match the paper matrix")
    if set(config.comparison.required_lanes) != set(entry.required_lanes):
        raise ExperimentRunConfigError("comparison.required_lanes must match experiment matrix")
    if config.comparison.required_metrics != entry.metrics:
        raise ExperimentRunConfigError("comparison.required_metrics must match experiment matrix")
    if config.reference.figure_pdf_sha256 != HEAVY_TOP_EXPECTED_FIGURE_PDF_SHA256:
        raise ExperimentRunConfigError("reference.figure_pdf_sha256 changed")
    if config.reference.figure_text_source != HEAVY_TOP_EXPECTED_FIGURE_TEXT_SOURCE:
        raise ExperimentRunConfigError("reference.figure_text_source changed")
    if not (
        np.isclose(config.reference.gravity_m_s2[0], 0.0, rtol=0.0, atol=1.0e-15)
        and config.reference.gravity_m_s2[1] < 0.0
        and np.isclose(config.reference.gravity_m_s2[2], 0.0, rtol=0.0, atol=1.0e-15)
    ):
        raise ExperimentRunConfigError("reference.gravity_m_s2 must point along negative y")
    expected_prefix = Path(entry.output_report).with_suffix("").as_posix() + "_"
    if (
        not config.reference.output_report.startswith(expected_prefix)
        or not config.reference.output_report.endswith(".json")
    ):
        raise ExperimentRunConfigError(
            "reference.output_report must be a lane-specific report under the matrix stem"
        )
    if config.output_report != config.reference.output_report:
        raise ExperimentRunConfigError("output_report must match reference.output_report")
    if (
        not config.mabd_newton.output_report.startswith(expected_prefix)
        or not config.mabd_newton.output_report.endswith(".json")
    ):
        raise ExperimentRunConfigError(
            "mabd_newton.output_report must be a lane-specific report under the matrix stem"
        )
    if config.mabd_newton.output_report == config.reference.output_report:
        raise ExperimentRunConfigError("mabd_newton.output_report must be separate from reference output_report")
    if (
        not config.mabd_paper_horizon.output_report.startswith(expected_prefix)
        or not config.mabd_paper_horizon.output_report.endswith(".json")
    ):
        raise ExperimentRunConfigError(
            "mabd_paper_horizon.output_report must be a lane-specific report under the matrix stem"
        )
    if config.mabd_paper_horizon.output_report in (
        config.reference.output_report,
        config.mabd_newton.output_report,
    ):
        raise ExperimentRunConfigError(
            "mabd_paper_horizon.output_report must be separate from other lane reports"
        )
    if (
        not config.comparison.output_report.startswith(expected_prefix)
        or not config.comparison.output_report.endswith(".json")
    ):
        raise ExperimentRunConfigError(
            "comparison.output_report must be a lane-specific report under the matrix stem"
        )
    if config.comparison.output_report in (
        config.reference.output_report,
        config.mabd_newton.output_report,
        config.mabd_paper_horizon.output_report,
    ):
        raise ExperimentRunConfigError("comparison.output_report must be separate from lane reports")
    if (
        not config.figure_curves.output_report.startswith(expected_prefix)
        or not config.figure_curves.output_report.endswith(".json")
    ):
        raise ExperimentRunConfigError(
            "figure_curves.output_report must be a lane-specific report under the matrix stem"
        )
    if config.figure_curves.output_report in (
        config.reference.output_report,
        config.mabd_newton.output_report,
        config.mabd_paper_horizon.output_report,
        config.comparison.output_report,
    ):
        raise ExperimentRunConfigError("figure_curves.output_report must be separate from lane reports")
    _require_heavy_top_paper_horizon_alignment(config)
    if not np.isclose(
        float(np.sum(config.mabd_newton.point_masses_kg)),
        config.reference.mass_kg,
        rtol=0.0,
        atol=1.0e-12,
    ):
        raise ExperimentRunConfigError("mabd_newton.point_masses_kg must sum to reference.mass_kg")
    if not np.allclose(
        config.mabd_newton.gravity_m_s2,
        config.reference.gravity_m_s2,
        rtol=0.0,
        atol=1.0e-15,
    ):
        raise ExperimentRunConfigError("mabd_newton.gravity_m_s2 must match reference.gravity_m_s2")
    if not np.isclose(
        float(np.sum(config.mabd_paper_horizon.point_masses_kg)),
        config.reference.mass_kg,
        rtol=0.0,
        atol=1.0e-12,
    ):
        raise ExperimentRunConfigError("mabd_paper_horizon.point_masses_kg must sum to reference.mass_kg")
    if not np.allclose(
        config.mabd_paper_horizon.gravity_m_s2,
        config.reference.gravity_m_s2,
        rtol=0.0,
        atol=1.0e-15,
    ):
        raise ExperimentRunConfigError(
            "mabd_paper_horizon.gravity_m_s2 must match reference.gravity_m_s2"
        )
    for blocker in HEAVY_TOP_REQUIRED_BLOCKERS:
        if blocker not in config.failure_reason:
            raise ExperimentRunConfigError(f"report.failure_reason missing {blocker}")


__all__ = [
    "ExperimentRunConfigError",
    "HEAVY_TOP_EXPECTED_FIGURE_PDF_SHA256",
    "HEAVY_TOP_EXPECTED_FIGURE_TEXT_SOURCE",
    "HEAVY_TOP_COMPARISON_REQUIRED_LANES",
    "HEAVY_TOP_COMPARISON_REQUIRED_METRICS",
    "HEAVY_TOP_COMPARISON_THRESHOLD_KEYS",
    "HEAVY_TOP_MABD_NEWTON_ROTATION_MODES",
    "HEAVY_TOP_MABD_NEWTON_THRESHOLD_KEYS",
    "HEAVY_TOP_REQUIRED_BLOCKERS",
    "HEAVY_TOP_REQUIRED_MISSING_LANES",
    "HEAVY_TOP_THRESHOLD_KEYS",
    "PAPER_HORIZON_THRESHOLD_KEYS",
    "PHYSICAL_PENDULUM_REQUIRED_MISSING_LANES",
    "PHYSICAL_PENDULUM_COMPARISON_DIAGNOSTIC_LANES",
    "PHYSICAL_PENDULUM_COMPARISON_REQUIRED_LANES",
    "PHYSICAL_PENDULUM_COMPARISON_REQUIRED_METRICS",
    "PHYSICAL_PENDULUM_COMPARISON_THRESHOLD_KEYS",
    "PHYSICAL_PENDULUM_MABD_DEVELOPMENT_THRESHOLD_KEYS",
    "PHYSICAL_PENDULUM_MABD_NEWTON_THRESHOLD_KEYS",
    "PHYSICAL_PENDULUM_RBD_BASELINE_THRESHOLD_KEYS",
    "PHYSICAL_PENDULUM_THRESHOLD_KEYS",
    "T_HANDLE_EXPECTED_FIGURE_PDF_SHA256",
    "T_HANDLE_EXPECTED_FIGURE_TEXT_SOURCE",
    "T_HANDLE_COMPARISON_REQUIRED_LANES",
    "T_HANDLE_COMPARISON_REQUIRED_METRICS",
    "T_HANDLE_COMPARISON_THRESHOLD_KEYS",
    "T_HANDLE_REQUIRED_BLOCKERS",
    "T_HANDLE_REQUIRED_MISSING_LANES",
    "T_HANDLE_MABD_NEWTON_ROTATION_MODES",
    "T_HANDLE_MABD_NEWTON_THRESHOLD_KEYS",
    "T_HANDLE_THRESHOLD_KEYS",
    "HeavyTopComparisonConfig",
    "HeavyTopMABDNewtonConfig",
    "HeavyTopReferenceConfig",
    "HeavyTopRunConfig",
    "PhysicalPendulumComparisonConfig",
    "PhysicalPendulumMABDDevelopmentConfig",
    "PhysicalPendulumMABDNewtonConfig",
    "PhysicalPendulumRBDBaselineConfig",
    "PhysicalPendulumReferenceConfig",
    "PhysicalPendulumRunConfig",
    "SpinningBoxPaperHorizonConfig",
    "SpinningBoxRunConfig",
    "THandleComparisonConfig",
    "THandleFigureCurvesConfig",
    "THandleMABDNewtonConfig",
    "THandleReferenceConfig",
    "THandleRunConfig",
    "load_physical_pendulum_config",
    "load_spinning_box_config",
    "load_t_handle_config",
    "load_heavy_top_config",
    "validate_heavy_top_config_against_matrix",
    "validate_physical_pendulum_config_against_matrix",
    "validate_spinning_box_config_against_matrix",
    "validate_t_handle_config_against_matrix",
]
