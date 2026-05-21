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
    contacts_input_output_report: str
    affine_static_plane_contacts_output_report: str
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
class RollingSpinningPerformanceConfig:
    body: str
    time_step_s: float
    step_count: int
    paper_hardware_context: str
    protocol_status: str
    paper_total_simulation_time_ms: dict[str, float]


@dataclass(frozen=True)
class RollingSpinningRBDBaselineConfig:
    output_report: str
    radius_m: float
    half_height_m: float
    density_kg_m3: float
    time_step_s: float
    step_count: int
    sample_count: int
    initial_position_m: np.ndarray
    initial_linear_velocity_m_s: np.ndarray
    initial_angular_velocity_rad_s: np.ndarray
    gravity_m_s2: np.ndarray
    contact: dict[str, float]
    thresholds: dict[str, float]


@dataclass(frozen=True)
class RollingSpinningMABDNewtonConfig:
    output_report: str
    radius_m: float
    half_height_m: float
    density_kg_m3: float
    young_modulus_pa: float
    poisson_ratio: float
    zero_stiffness_diagnostic: bool
    time_step_s: float
    step_count: int
    sample_count: int
    rest_points_m: np.ndarray
    point_masses_kg: np.ndarray
    volume_m3: float
    rotation_mode: str
    initial_position_m: np.ndarray
    initial_linear_velocity_m_s: np.ndarray
    initial_angular_velocity_rad_s: np.ndarray
    gravity_m_s2: np.ndarray
    contact_constraint_mode: str
    thresholds: dict[str, float]


@dataclass(frozen=True)
class RollingSpinningTimingProtocolConfig:
    output_report: str
    input_reports: tuple[str, ...]
    paper_comparable: bool


@dataclass(frozen=True)
class RollingSpinningPaperFaithfulGateLedgerConfig:
    output_report: str
    required_gates: tuple[str, ...]
    current_evidence_reports: dict[str, str]


@dataclass(frozen=True)
class RollingSpinningRunConfig:
    schema_version: int
    claim_id: str
    scene_id: str
    source_lines: tuple[str, ...]
    asset_ids: tuple[str, ...]
    baseline_lane: str
    required_missing_lanes: tuple[str, ...]
    paper_values: dict[str, Any]
    performance: RollingSpinningPerformanceConfig
    rbd_implicit_baseline: RollingSpinningRBDBaselineConfig
    rbd_explicit_baseline: RollingSpinningRBDBaselineConfig
    rbd_no_slip_reference: RollingSpinningRBDBaselineConfig
    rbd_explicit_no_slip_candidate: RollingSpinningRBDBaselineConfig
    mabd_newton: RollingSpinningMABDNewtonConfig
    mabd_material_preflight: RollingSpinningMABDNewtonConfig
    mabd_rolling_contact_candidate: RollingSpinningMABDNewtonConfig
    paper_timing_protocol: RollingSpinningTimingProtocolConfig
    paper_faithful_gate_ledger: RollingSpinningPaperFaithfulGateLedgerConfig
    report_status: EvidenceStatus
    failure_reason: str
    output_report: str
    thresholds: dict[str, float]


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
ROLLING_SPINNING_TIMING_KEYS = frozenset(
    {
        "vanilla_implicit_abd",
        "implicit_rbd",
        "explicit_rbd",
        "corotated_abd_with_polar",
        "corotated_abd_without_polar",
    }
)
ROLLING_SPINNING_REQUIRED_MISSING_LANES = (
    "rbd_implicit_baseline",
    "rbd_explicit_baseline",
)
ROLLING_SPINNING_RBD_IMPLICIT_BASELINE_OUTPUT_REPORT = (
    "reports/experiment_matrix/single_body_rolling_spinning_rbd_implicit_baseline.json"
)
ROLLING_SPINNING_RBD_EXPLICIT_BASELINE_OUTPUT_REPORT = (
    "reports/experiment_matrix/single_body_rolling_spinning_rbd_explicit_baseline.json"
)
ROLLING_SPINNING_RBD_NO_SLIP_REFERENCE_OUTPUT_REPORT = (
    "reports/experiment_matrix/single_body_rolling_spinning_rbd_no_slip_reference.json"
)
ROLLING_SPINNING_RBD_EXPLICIT_NO_SLIP_CANDIDATE_OUTPUT_REPORT = (
    "reports/experiment_matrix/"
    "single_body_rolling_spinning_rbd_explicit_no_slip_candidate.json"
)
ROLLING_SPINNING_MABD_NEWTON_OUTPUT_REPORT = (
    "reports/experiment_matrix/single_body_rolling_spinning_mabd_newton.json"
)
ROLLING_SPINNING_MABD_MATERIAL_PREFLIGHT_OUTPUT_REPORT = (
    "reports/experiment_matrix/single_body_rolling_spinning_mabd_material_preflight.json"
)
ROLLING_SPINNING_MABD_ROLLING_CONTACT_CANDIDATE_OUTPUT_REPORT = (
    "reports/experiment_matrix/"
    "single_body_rolling_spinning_mabd_rolling_contact_candidate.json"
)
ROLLING_SPINNING_TIMING_PROTOCOL_OUTPUT_REPORT = (
    "reports/experiment_matrix/single_body_rolling_spinning_timing_protocol.json"
)
ROLLING_SPINNING_PAPER_FAITHFUL_GATE_LEDGER_OUTPUT_REPORT = (
    "reports/experiment_matrix/"
    "single_body_rolling_spinning_paper_faithful_gate_ledger.json"
)
ROLLING_SPINNING_TIMING_PROTOCOL_INPUT_REPORTS = (
    "reports/experiment_matrix/single_body_rolling_spinning.json",
    ROLLING_SPINNING_RBD_IMPLICIT_BASELINE_OUTPUT_REPORT,
    ROLLING_SPINNING_RBD_EXPLICIT_BASELINE_OUTPUT_REPORT,
    ROLLING_SPINNING_MABD_NEWTON_OUTPUT_REPORT,
    ROLLING_SPINNING_MABD_MATERIAL_PREFLIGHT_OUTPUT_REPORT,
)
ROLLING_SPINNING_PAPER_FAITHFUL_GATE_LEDGER_REQUIRED_GATES = (
    "paper_faithful_explicit_rbd_baseline",
    "paper_faithful_implicit_rbd_baseline",
    "paper_faithful_mabd_rolling_cylinder",
    "paper_comparable_timing",
)
ROLLING_SPINNING_PAPER_FAITHFUL_GATE_LEDGER_CURRENT_EVIDENCE_REPORTS = {
    "rbd_explicit_no_slip_candidate": (
        ROLLING_SPINNING_RBD_EXPLICIT_NO_SLIP_CANDIDATE_OUTPUT_REPORT
    ),
    "rbd_implicit_development": ROLLING_SPINNING_RBD_IMPLICIT_BASELINE_OUTPUT_REPORT,
    "mabd_rolling_contact_candidate": (
        ROLLING_SPINNING_MABD_ROLLING_CONTACT_CANDIDATE_OUTPUT_REPORT
    ),
    "timing_protocol": ROLLING_SPINNING_TIMING_PROTOCOL_OUTPUT_REPORT,
}
ROLLING_SPINNING_RBD_CONTACT_KEYS = frozenset({"ke", "kd", "kf", "mu", "gap"})
ROLLING_SPINNING_RBD_THRESHOLD_KEYS = frozenset(
    {
        "max_no_slip_residual_m_s",
        "max_relative_energy_drift",
        "min_contact_count",
        "max_runtime_wall_time_ms",
    }
)
ROLLING_SPINNING_MABD_NEWTON_THRESHOLD_KEYS = frozenset(
    {
        "max_no_slip_residual_m_s",
        "max_relative_energy_drift",
        "min_contact_count",
        "max_affine_shape_spread_m",
        "max_constraint_residual_norm",
        "max_runtime_wall_time_ms",
    }
)
ROLLING_SPINNING_MABD_CONTACT_CONSTRAINT_MODES = frozenset({"plane", "world"})

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


def _require_str_mapping(data: dict[str, Any], key: str) -> dict[str, str]:
    mapping = _require_mapping(data, key)
    result: dict[str, str] = {}
    for item_key, item_value in mapping.items():
        if not isinstance(item_key, str) or not item_key:
            raise ExperimentRunConfigError(f"{key} keys must be non-empty strings")
        if not isinstance(item_value, str) or not item_value:
            raise ExperimentRunConfigError(f"{key} values must be non-empty strings")
        result[item_key] = item_value
    return result


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


def _require_bool(data: dict[str, Any], key: str) -> bool:
    value = data.get(key)
    if not isinstance(value, bool):
        raise ExperimentRunConfigError(f"{key} must be a boolean")
    return value


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
        contacts_input_output_report=_require_str(horizon, "contacts_input_output_report"),
        affine_static_plane_contacts_output_report=_require_str(
            horizon,
            "affine_static_plane_contacts_output_report",
        ),
        decoupled_twist_output_report=_require_str(horizon, "decoupled_twist_output_report"),
        figure_curve_output_report=_require_str(horizon, "figure_curve_output_report"),
        figure_pdf_sha256=_require_str(horizon, "figure_pdf_sha256"),
        figure_text_source=_require_str(horizon, "figure_text_source"),
        thresholds=thresholds,
    )


def _require_rolling_spinning_performance(
    data: dict[str, Any],
) -> RollingSpinningPerformanceConfig:
    performance = _require_mapping(data, "performance")
    paper_timing = _require_float_mapping(performance, "paper_total_simulation_time_ms")
    if set(paper_timing) != ROLLING_SPINNING_TIMING_KEYS:
        raise ExperimentRunConfigError(
            "paper_total_simulation_time_ms keys must match paper timing modes"
        )
    if _require_str(performance, "body") != "rolling_cylinder":
        raise ExperimentRunConfigError("performance.body must be rolling_cylinder")
    if (
        _require_str(performance, "protocol_status")
        != "paper_text_timing_only_no_local_runtime_measurement"
    ):
        raise ExperimentRunConfigError(
            "performance.protocol_status must record no local runtime measurement"
        )
    if _require_str(performance, "paper_hardware_context") != "i7 CPU, single thread":
        raise ExperimentRunConfigError(
            "performance.paper_hardware_context must match the paper timing context"
        )
    return RollingSpinningPerformanceConfig(
        body="rolling_cylinder",
        time_step_s=_require_positive_float(performance, "time_step_s"),
        step_count=_require_positive_int(performance, "step_count"),
        paper_hardware_context="i7 CPU, single thread",
        protocol_status="paper_text_timing_only_no_local_runtime_measurement",
        paper_total_simulation_time_ms=paper_timing,
    )


def _require_rolling_spinning_rbd_baseline(
    data: dict[str, Any],
    key: str,
) -> RollingSpinningRBDBaselineConfig:
    section_key = key
    baseline = _require_mapping(data, key)
    contact = _require_float_mapping(baseline, "contact")
    if set(contact) != ROLLING_SPINNING_RBD_CONTACT_KEYS:
        raise ExperimentRunConfigError(
            f"{section_key}.contact keys must match Newton shape material fields"
        )
    for contact_key, value in contact.items():
        if value < 0.0:
            raise ExperimentRunConfigError(
                f"{section_key}.contact.{contact_key} must be non-negative"
            )
    thresholds = _require_float_mapping(baseline, "thresholds")
    if set(thresholds) != ROLLING_SPINNING_RBD_THRESHOLD_KEYS:
        raise ExperimentRunConfigError(
            f"{section_key}.thresholds keys must match rolling-cylinder RBD metrics"
        )
    for threshold_key, value in thresholds.items():
        if value < 0.0:
            raise ExperimentRunConfigError(
                f"{section_key}.thresholds.{threshold_key} must be non-negative"
            )
    return RollingSpinningRBDBaselineConfig(
        output_report=_require_str(baseline, "output_report"),
        radius_m=_require_positive_float(baseline, "radius_m"),
        half_height_m=_require_positive_float(baseline, "half_height_m"),
        density_kg_m3=_require_positive_float(baseline, "density_kg_m3"),
        time_step_s=_require_positive_float(baseline, "time_step_s"),
        step_count=_require_positive_int(baseline, "step_count"),
        sample_count=_require_positive_int(baseline, "sample_count"),
        initial_position_m=_require_vec3_array(baseline, "initial_position_m"),
        initial_linear_velocity_m_s=_require_vec3_array(
            baseline,
            "initial_linear_velocity_m_s",
        ),
        initial_angular_velocity_rad_s=_require_vec3_array(
            baseline,
            "initial_angular_velocity_rad_s",
        ),
        gravity_m_s2=_require_negative_y_gravity_array(baseline, "gravity_m_s2"),
        contact=contact,
        thresholds=thresholds,
    )


def _require_rolling_spinning_mabd_newton(
    data: dict[str, Any],
    key: str,
    *,
    default_young_modulus_pa: float,
    default_poisson_ratio: float,
    default_zero_stiffness_diagnostic: bool,
) -> RollingSpinningMABDNewtonConfig:
    section = _require_mapping(data, key)
    thresholds = _require_float_mapping(section, "thresholds")
    if set(thresholds) != ROLLING_SPINNING_MABD_NEWTON_THRESHOLD_KEYS:
        raise ExperimentRunConfigError(
            f"{key}.thresholds keys must match rolling-cylinder M-ABD metrics"
        )
    for threshold_key, value in thresholds.items():
        if value < 0.0:
            raise ExperimentRunConfigError(
                f"{key}.thresholds.{threshold_key} must be non-negative"
            )
    rest_points = _require_points(section, "rest_points_m")
    if rest_points.shape != (4, 3):
        raise ExperimentRunConfigError(
            f"{key}.rest_points_m must contain exactly 4 diagnostic points"
        )
    point_masses = _require_positive_mass_vector(
        section,
        "point_masses_kg",
        rest_points.shape[0],
    )
    rotation_mode = _require_str(section, "rotation_mode")
    if rotation_mode != "polar":
        raise ExperimentRunConfigError(f"{key}.rotation_mode must be polar")
    step_count = _require_positive_int(section, "step_count")
    sample_count = _require_positive_int(section, "sample_count")
    if sample_count > step_count + 1:
        raise ExperimentRunConfigError(f"{key}.sample_count must be at most step_count + 1")
    young_modulus_pa = (
        _require_finite_number(section, "young_modulus_pa")
        if "young_modulus_pa" in section
        else default_young_modulus_pa
    )
    if young_modulus_pa < 0.0 or not isfinite(young_modulus_pa):
        raise ExperimentRunConfigError(f"{key}.young_modulus_pa must be finite and non-negative")
    poisson_ratio = (
        _require_finite_number(section, "poisson_ratio")
        if "poisson_ratio" in section
        else default_poisson_ratio
    )
    if poisson_ratio <= -1.0 or poisson_ratio >= 0.5:
        raise ExperimentRunConfigError(f"{key}.poisson_ratio must be in (-1, 0.5)")
    zero_stiffness_diagnostic = (
        _require_bool(section, "zero_stiffness_diagnostic")
        if "zero_stiffness_diagnostic" in section
        else default_zero_stiffness_diagnostic
    )
    contact_constraint_mode = (
        _require_str(section, "contact_constraint_mode")
        if "contact_constraint_mode" in section
        else "plane"
    )
    if contact_constraint_mode not in ROLLING_SPINNING_MABD_CONTACT_CONSTRAINT_MODES:
        raise ExperimentRunConfigError(
            f"{key}.contact_constraint_mode must be plane or world"
        )
    return RollingSpinningMABDNewtonConfig(
        output_report=_require_str(section, "output_report"),
        radius_m=_require_positive_float(section, "radius_m"),
        half_height_m=_require_positive_float(section, "half_height_m"),
        density_kg_m3=_require_positive_float(section, "density_kg_m3"),
        young_modulus_pa=young_modulus_pa,
        poisson_ratio=poisson_ratio,
        zero_stiffness_diagnostic=zero_stiffness_diagnostic,
        time_step_s=_require_positive_float(section, "time_step_s"),
        step_count=step_count,
        sample_count=sample_count,
        rest_points_m=rest_points,
        point_masses_kg=point_masses,
        volume_m3=_require_positive_float(section, "volume_m3"),
        rotation_mode=rotation_mode,
        initial_position_m=_require_vec3_array(section, "initial_position_m"),
        initial_linear_velocity_m_s=_require_vec3_array(
            section,
            "initial_linear_velocity_m_s",
        ),
        initial_angular_velocity_rad_s=_require_vec3_array(
            section,
            "initial_angular_velocity_rad_s",
        ),
        gravity_m_s2=_require_negative_y_gravity_array(section, "gravity_m_s2"),
        contact_constraint_mode=contact_constraint_mode,
        thresholds=thresholds,
    )


def _require_rolling_spinning_timing_protocol(
    data: dict[str, Any],
) -> RollingSpinningTimingProtocolConfig:
    section = _require_mapping(data, "paper_timing_protocol")
    return RollingSpinningTimingProtocolConfig(
        output_report=_require_str(section, "output_report"),
        input_reports=_require_str_tuple(section, "input_reports"),
        paper_comparable=_require_bool(section, "paper_comparable"),
    )


def _require_rolling_spinning_paper_faithful_gate_ledger(
    data: dict[str, Any],
) -> RollingSpinningPaperFaithfulGateLedgerConfig:
    section = _require_mapping(data, "paper_faithful_gate_ledger")
    return RollingSpinningPaperFaithfulGateLedgerConfig(
        output_report=_require_str(section, "output_report"),
        required_gates=_require_str_tuple(section, "required_gates"),
        current_evidence_reports=_require_str_mapping(section, "current_evidence_reports"),
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


def load_rolling_spinning_config(path: str | Path) -> RollingSpinningRunConfig:
    data = _read_mapping(Path(path))
    if not isinstance(data.get("schema_version"), int) or isinstance(
        data.get("schema_version"), bool
    ):
        raise ExperimentRunConfigError("schema_version must be 1")
    if data.get("schema_version") != 1:
        raise ExperimentRunConfigError("schema_version must be 1")
    claim_id = _require_str(data, "claim_id")
    if claim_id != "experiment.single_body.rolling_spinning":
        raise ExperimentRunConfigError(
            "rolling-spinning config must target experiment.single_body.rolling_spinning"
        )
    report = _require_mapping(data, "report")
    try:
        status = EvidenceStatus(_require_str(report, "status"))
    except ValueError as exc:
        raise ExperimentRunConfigError("report.status is not a known EvidenceStatus") from exc
    if status == EvidenceStatus.PASSED:
        raise ExperimentRunConfigError("passed experiment configs require a dedicated evidence gate")
    return RollingSpinningRunConfig(
        schema_version=1,
        claim_id=claim_id,
        scene_id=_require_str(data, "scene_id"),
        source_lines=_require_str_tuple(data, "source_lines"),
        asset_ids=_require_str_tuple(data, "asset_ids"),
        baseline_lane=_require_str(data, "baseline_lane"),
        required_missing_lanes=_require_str_tuple(data, "required_missing_lanes"),
        paper_values=_require_mapping(data, "paper_values"),
        performance=_require_rolling_spinning_performance(data),
        rbd_implicit_baseline=_require_rolling_spinning_rbd_baseline(
            data,
            "rbd_implicit_baseline",
        ),
        rbd_explicit_baseline=_require_rolling_spinning_rbd_baseline(
            data,
            "rbd_explicit_baseline",
        ),
        rbd_no_slip_reference=_require_rolling_spinning_rbd_baseline(
            data,
            "rbd_no_slip_reference",
        ),
        rbd_explicit_no_slip_candidate=_require_rolling_spinning_rbd_baseline(
            data,
            "rbd_explicit_no_slip_candidate",
        ),
        mabd_newton=_require_rolling_spinning_mabd_newton(
            data,
            "mabd_newton",
            default_young_modulus_pa=0.0,
            default_poisson_ratio=0.25,
            default_zero_stiffness_diagnostic=True,
        ),
        mabd_material_preflight=_require_rolling_spinning_mabd_newton(
            data,
            "mabd_material_preflight",
            default_young_modulus_pa=1.0e9,
            default_poisson_ratio=0.3,
            default_zero_stiffness_diagnostic=False,
        ),
        mabd_rolling_contact_candidate=_require_rolling_spinning_mabd_newton(
            data,
            "mabd_rolling_contact_candidate",
            default_young_modulus_pa=1.0e9,
            default_poisson_ratio=0.3,
            default_zero_stiffness_diagnostic=False,
        ),
        paper_timing_protocol=_require_rolling_spinning_timing_protocol(data),
        paper_faithful_gate_ledger=(
            _require_rolling_spinning_paper_faithful_gate_ledger(data)
        ),
        report_status=status,
        failure_reason=_require_str(report, "failure_reason"),
        output_report=_require_str(report, "output_report"),
        thresholds=_require_float_mapping(report, "thresholds"),
    )


def validate_rolling_spinning_config_against_matrix(
    config: RollingSpinningRunConfig,
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
    if config.output_report != entry.output_report:
        raise ExperimentRunConfigError("output_report must match experiment matrix")
    if config.baseline_lane not in entry.required_lanes:
        raise ExperimentRunConfigError("baseline_lane must be listed in required_lanes")
    if config.required_missing_lanes != ROLLING_SPINNING_REQUIRED_MISSING_LANES:
        raise ExperimentRunConfigError(
            "required_missing_lanes must match rolling/spinning baseline blockers"
        )
    for lane in config.required_missing_lanes:
        if lane not in entry.required_lanes:
            raise ExperimentRunConfigError("required_missing_lanes must be listed in required_lanes")
    for reason in ("rbd_baseline_adapter_missing", "benchmark_protocol_not_recorded"):
        if reason not in entry.blocking_reasons:
            raise ExperimentRunConfigError(
                "matrix blocking_reasons must keep rolling/spinning blockers"
            )
    if entry.reproduction_status != "blocked_by_baselines":
        raise ExperimentRunConfigError("matrix reproduction_status must remain blocked_by_baselines")
    for metric in entry.metrics:
        if metric not in config.thresholds:
            raise ExperimentRunConfigError(
                "matrix metrics must be present in report.thresholds"
            )
    if config.performance.time_step_s != 0.01:
        raise ExperimentRunConfigError(
            "performance.time_step_s must match paper h = 0.01 sec"
        )
    if config.performance.step_count != 10000:
        raise ExperimentRunConfigError("performance.step_count must match paper 10K steps")
    def validate_rbd_baseline(
        baseline: RollingSpinningRBDBaselineConfig,
        *,
        field_name: str,
        expected_output_report: str,
        disallowed_reports: tuple[str, ...],
    ) -> None:
        rbd_report = baseline.output_report
        rbd_report_path = Path(rbd_report)
        if (
            rbd_report_path.is_absolute()
            or ".." in rbd_report_path.parts
            or rbd_report_path.parent.as_posix() != "reports/experiment_matrix"
            or rbd_report_path.suffix != ".json"
            or rbd_report != expected_output_report
            or rbd_report in disallowed_reports
        ):
            raise ExperimentRunConfigError(
                f"{field_name}.output_report must be the lane-specific "
                "relative JSON report under reports/experiment_matrix"
            )
        if baseline.time_step_s != config.performance.time_step_s:
            raise ExperimentRunConfigError(
                f"{field_name}.time_step_s must match performance.time_step_s"
            )
        if baseline.step_count > config.performance.step_count:
            raise ExperimentRunConfigError(
                f"{field_name}.step_count must not exceed performance.step_count"
            )
        if baseline.sample_count < 2:
            raise ExperimentRunConfigError(
                f"{field_name}.sample_count must include initial and final samples"
            )
        if not np.isclose(
            baseline.initial_position_m[1],
            baseline.radius_m,
            rtol=0.0,
            atol=1.0e-12,
        ):
            raise ExperimentRunConfigError(
                f"{field_name}.initial_position_m must place the cylinder on the plane"
            )
        expected_no_slip = (
            baseline.initial_linear_velocity_m_s[0]
            + baseline.initial_angular_velocity_rad_s[2] * baseline.radius_m
        )
        if not np.isclose(expected_no_slip, 0.0, rtol=0.0, atol=1.0e-12):
            raise ExperimentRunConfigError(
                f"{field_name} initial velocities must satisfy the no-slip diagnostic"
            )

    validate_rbd_baseline(
        config.rbd_implicit_baseline,
        field_name="rbd_implicit_baseline",
        expected_output_report=ROLLING_SPINNING_RBD_IMPLICIT_BASELINE_OUTPUT_REPORT,
        disallowed_reports=(config.output_report,),
    )
    validate_rbd_baseline(
        config.rbd_explicit_baseline,
        field_name="rbd_explicit_baseline",
        expected_output_report=ROLLING_SPINNING_RBD_EXPLICIT_BASELINE_OUTPUT_REPORT,
        disallowed_reports=(
            config.output_report,
            config.rbd_implicit_baseline.output_report,
        ),
    )
    validate_rbd_baseline(
        config.rbd_no_slip_reference,
        field_name="rbd_no_slip_reference",
        expected_output_report=ROLLING_SPINNING_RBD_NO_SLIP_REFERENCE_OUTPUT_REPORT,
        disallowed_reports=(
            config.output_report,
            config.rbd_implicit_baseline.output_report,
            config.rbd_explicit_baseline.output_report,
        ),
    )
    validate_rbd_baseline(
        config.rbd_explicit_no_slip_candidate,
        field_name="rbd_explicit_no_slip_candidate",
        expected_output_report=ROLLING_SPINNING_RBD_EXPLICIT_NO_SLIP_CANDIDATE_OUTPUT_REPORT,
        disallowed_reports=(
            config.output_report,
            config.rbd_implicit_baseline.output_report,
            config.rbd_explicit_baseline.output_report,
            config.rbd_no_slip_reference.output_report,
        ),
    )
    reference = config.rbd_no_slip_reference
    candidate = config.rbd_explicit_no_slip_candidate
    implicit = config.rbd_implicit_baseline
    if not np.isclose(reference.time_step_s, 0.01, rtol=0.0, atol=1.0e-15):
        raise ExperimentRunConfigError("rbd_no_slip_reference.time_step_s must be 0.01")
    if reference.step_count != 10000:
        raise ExperimentRunConfigError("rbd_no_slip_reference.step_count must be 10000")
    if reference.sample_count < 3:
        raise ExperimentRunConfigError("rbd_no_slip_reference.sample_count must be at least 3")
    if not np.isclose(reference.initial_position_m[1], reference.radius_m, rtol=0.0, atol=1.0e-12):
        raise ExperimentRunConfigError(
            "rbd_no_slip_reference.initial_position_m must place the cylinder center at radius height"
        )
    if not np.allclose(reference.initial_linear_velocity_m_s[1:], [0.0, 0.0], rtol=0.0, atol=1.0e-12):
        raise ExperimentRunConfigError(
            "rbd_no_slip_reference.initial_linear_velocity_m_s must have zero vertical and lateral velocity"
        )
    if not np.allclose(reference.initial_angular_velocity_rad_s[:2], [0.0, 0.0], rtol=0.0, atol=1.0e-12):
        raise ExperimentRunConfigError(
            "rbd_no_slip_reference.initial_angular_velocity_rad_s must have zero off-axis angular velocity"
        )
    if not np.isclose(
        reference.initial_linear_velocity_m_s[0]
        + reference.initial_angular_velocity_rad_s[2] * reference.radius_m,
        0.0,
        rtol=0.0,
        atol=1.0e-12,
    ):
        raise ExperimentRunConfigError(
            "rbd_no_slip_reference velocities must satisfy the no-slip condition"
        )
    if not np.isclose(reference.radius_m, implicit.radius_m, rtol=0.0, atol=1.0e-15):
        raise ExperimentRunConfigError("rbd_no_slip_reference.radius_m must match rbd_implicit_baseline")
    if not np.isclose(
        reference.half_height_m,
        implicit.half_height_m,
        rtol=0.0,
        atol=1.0e-15,
    ):
        raise ExperimentRunConfigError(
            "rbd_no_slip_reference.half_height_m must match rbd_implicit_baseline"
        )
    if not np.isclose(
        reference.density_kg_m3,
        implicit.density_kg_m3,
        rtol=0.0,
        atol=1.0e-15,
    ):
        raise ExperimentRunConfigError(
            "rbd_no_slip_reference.density_kg_m3 must match rbd_implicit_baseline"
        )
    if not np.isclose(candidate.time_step_s, 0.01, rtol=0.0, atol=1.0e-15):
        raise ExperimentRunConfigError(
            "rbd_explicit_no_slip_candidate.time_step_s must be 0.01"
        )
    if candidate.step_count != 10000:
        raise ExperimentRunConfigError(
            "rbd_explicit_no_slip_candidate.step_count must be 10000"
        )
    if candidate.sample_count < 3:
        raise ExperimentRunConfigError(
            "rbd_explicit_no_slip_candidate.sample_count must be at least 3"
        )
    if not np.allclose(
        candidate.initial_position_m,
        reference.initial_position_m,
        rtol=0.0,
        atol=1.0e-15,
    ):
        raise ExperimentRunConfigError(
            "rbd_explicit_no_slip_candidate.initial_position_m must match the no-slip reference"
        )
    if not np.allclose(
        candidate.initial_linear_velocity_m_s,
        reference.initial_linear_velocity_m_s,
        rtol=0.0,
        atol=1.0e-15,
    ):
        raise ExperimentRunConfigError(
            "rbd_explicit_no_slip_candidate.initial_linear_velocity_m_s must match the no-slip reference"
        )
    if not np.allclose(
        candidate.initial_angular_velocity_rad_s,
        reference.initial_angular_velocity_rad_s,
        rtol=0.0,
        atol=1.0e-15,
    ):
        raise ExperimentRunConfigError(
            "rbd_explicit_no_slip_candidate.initial_angular_velocity_rad_s must match the no-slip reference"
        )
    if not np.isclose(candidate.radius_m, reference.radius_m, rtol=0.0, atol=1.0e-15):
        raise ExperimentRunConfigError(
            "rbd_explicit_no_slip_candidate.radius_m must match the no-slip reference"
        )
    if not np.isclose(
        candidate.half_height_m,
        reference.half_height_m,
        rtol=0.0,
        atol=1.0e-15,
    ):
        raise ExperimentRunConfigError(
            "rbd_explicit_no_slip_candidate.half_height_m must match the no-slip reference"
        )
    if not np.isclose(
        candidate.density_kg_m3,
        reference.density_kg_m3,
        rtol=0.0,
        atol=1.0e-15,
    ):
        raise ExperimentRunConfigError(
            "rbd_explicit_no_slip_candidate.density_kg_m3 must match the no-slip reference"
        )
    if candidate.contact != config.rbd_explicit_baseline.contact:
        raise ExperimentRunConfigError(
            "rbd_explicit_no_slip_candidate.contact must match rbd_explicit_baseline"
        )
    if candidate.thresholds != reference.thresholds:
        raise ExperimentRunConfigError(
            "rbd_explicit_no_slip_candidate.thresholds must match the no-slip reference"
        )

    mabd_report = config.mabd_newton.output_report
    mabd_report_path = Path(mabd_report)
    if (
        mabd_report_path.is_absolute()
        or ".." in mabd_report_path.parts
        or mabd_report_path.parent.as_posix() != "reports/experiment_matrix"
        or mabd_report_path.suffix != ".json"
        or mabd_report != ROLLING_SPINNING_MABD_NEWTON_OUTPUT_REPORT
        or mabd_report
        in (
            config.output_report,
            config.rbd_implicit_baseline.output_report,
            config.rbd_explicit_baseline.output_report,
            config.rbd_no_slip_reference.output_report,
            config.rbd_explicit_no_slip_candidate.output_report,
        )
    ):
        raise ExperimentRunConfigError(
            "mabd_newton.output_report must be the lane-specific relative JSON "
            "report under reports/experiment_matrix"
        )
    if config.mabd_newton.time_step_s != config.performance.time_step_s:
        raise ExperimentRunConfigError(
            "mabd_newton.time_step_s must match performance.time_step_s"
        )
    if config.mabd_newton.step_count > config.performance.step_count:
        raise ExperimentRunConfigError(
            "mabd_newton.step_count must not exceed performance.step_count"
        )
    if config.mabd_newton.sample_count < 2:
        raise ExperimentRunConfigError(
            "mabd_newton.sample_count must include initial and final samples"
        )
    expected_volume = (
        np.pi
        * config.mabd_newton.radius_m**2
        * (2.0 * config.mabd_newton.half_height_m)
    )
    if not np.isclose(config.mabd_newton.volume_m3, expected_volume, rtol=0.0, atol=1.0e-12):
        raise ExperimentRunConfigError(
            "mabd_newton.volume_m3 must match the configured cylinder volume"
        )
    expected_mass = config.mabd_newton.density_kg_m3 * config.mabd_newton.volume_m3
    if not np.isclose(
        float(np.sum(config.mabd_newton.point_masses_kg)),
        expected_mass,
        rtol=0.0,
        atol=1.0e-9,
    ):
        raise ExperimentRunConfigError(
            "mabd_newton.point_masses_kg must sum to cylinder mass"
        )
    if not np.isclose(
        config.mabd_newton.initial_position_m[1],
        config.mabd_newton.radius_m,
        rtol=0.0,
        atol=1.0e-12,
    ):
        raise ExperimentRunConfigError(
            "mabd_newton.initial_position_m must place the cylinder on the plane"
        )
    expected_no_slip = (
        config.mabd_newton.initial_linear_velocity_m_s[0]
        + config.mabd_newton.initial_angular_velocity_rad_s[2]
        * config.mabd_newton.radius_m
    )
    if not np.isclose(expected_no_slip, 0.0, rtol=0.0, atol=1.0e-12):
        raise ExperimentRunConfigError(
            "mabd_newton initial velocities must satisfy the no-slip diagnostic"
        )

    material = config.mabd_material_preflight
    material_report = material.output_report
    material_report_path = Path(material_report)
    if (
        material_report_path.is_absolute()
        or ".." in material_report_path.parts
        or material_report_path.parent.as_posix() != "reports/experiment_matrix"
        or material_report_path.suffix != ".json"
        or material_report != ROLLING_SPINNING_MABD_MATERIAL_PREFLIGHT_OUTPUT_REPORT
        or material_report
        in (
            config.output_report,
            config.rbd_implicit_baseline.output_report,
            config.rbd_explicit_baseline.output_report,
            config.rbd_no_slip_reference.output_report,
            config.rbd_explicit_no_slip_candidate.output_report,
            config.mabd_newton.output_report,
        )
    ):
        raise ExperimentRunConfigError(
            "mabd_material_preflight.output_report must be the lane-specific "
            "relative JSON report under reports/experiment_matrix"
        )
    if material.time_step_s != config.performance.time_step_s:
        raise ExperimentRunConfigError(
            "mabd_material_preflight.time_step_s must match performance.time_step_s"
        )
    if material.step_count > config.performance.step_count:
        raise ExperimentRunConfigError(
            "mabd_material_preflight.step_count must not exceed performance.step_count"
        )
    if material.sample_count < 2:
        raise ExperimentRunConfigError(
            "mabd_material_preflight.sample_count must include initial and final samples"
        )
    expected_volume = np.pi * material.radius_m**2 * (2.0 * material.half_height_m)
    if not np.isclose(material.volume_m3, expected_volume, rtol=0.0, atol=1.0e-12):
        raise ExperimentRunConfigError(
            "mabd_material_preflight.volume_m3 must match the configured cylinder volume"
        )
    expected_mass = material.density_kg_m3 * material.volume_m3
    if not np.isclose(
        float(np.sum(material.point_masses_kg)),
        expected_mass,
        rtol=0.0,
        atol=1.0e-9,
    ):
        raise ExperimentRunConfigError(
            "mabd_material_preflight.point_masses_kg must sum to cylinder mass"
        )
    if not np.isclose(material.initial_position_m[1], material.radius_m, rtol=0.0, atol=1.0e-12):
        raise ExperimentRunConfigError(
            "mabd_material_preflight.initial_position_m must place the cylinder on the plane"
        )
    expected_no_slip = (
        material.initial_linear_velocity_m_s[0]
        + material.initial_angular_velocity_rad_s[2] * material.radius_m
    )
    if not np.isclose(expected_no_slip, 0.0, rtol=0.0, atol=1.0e-12):
        raise ExperimentRunConfigError(
            "mabd_material_preflight initial velocities must satisfy the no-slip diagnostic"
        )
    if material.young_modulus_pa <= 0.0:
        raise ExperimentRunConfigError(
            "mabd_material_preflight.young_modulus_pa must be positive"
        )
    if material.poisson_ratio <= -1.0 or material.poisson_ratio >= 0.5:
        raise ExperimentRunConfigError(
            "mabd_material_preflight.poisson_ratio must be in (-1, 0.5)"
        )
    if material.zero_stiffness_diagnostic:
        raise ExperimentRunConfigError(
            "mabd_material_preflight.zero_stiffness_diagnostic must be false"
        )

    rolling_contact = config.mabd_rolling_contact_candidate
    rolling_contact_report = rolling_contact.output_report
    rolling_contact_report_path = Path(rolling_contact_report)
    if (
        rolling_contact_report_path.is_absolute()
        or ".." in rolling_contact_report_path.parts
        or rolling_contact_report_path.parent.as_posix() != "reports/experiment_matrix"
        or rolling_contact_report_path.suffix != ".json"
        or rolling_contact_report
        != ROLLING_SPINNING_MABD_ROLLING_CONTACT_CANDIDATE_OUTPUT_REPORT
        or rolling_contact_report
        in (
            config.output_report,
            config.rbd_implicit_baseline.output_report,
            config.rbd_explicit_baseline.output_report,
            config.rbd_no_slip_reference.output_report,
            config.rbd_explicit_no_slip_candidate.output_report,
            config.mabd_newton.output_report,
            config.mabd_material_preflight.output_report,
        )
    ):
        raise ExperimentRunConfigError(
            "mabd_rolling_contact_candidate.output_report must be the lane-specific "
            "relative JSON report under reports/experiment_matrix"
        )
    if rolling_contact.time_step_s != config.performance.time_step_s:
        raise ExperimentRunConfigError(
            "mabd_rolling_contact_candidate.time_step_s must match performance.time_step_s"
        )
    if rolling_contact.step_count > config.performance.step_count:
        raise ExperimentRunConfigError(
            "mabd_rolling_contact_candidate.step_count must not exceed performance.step_count"
        )
    if rolling_contact.sample_count < 2:
        raise ExperimentRunConfigError(
            "mabd_rolling_contact_candidate.sample_count must include initial and final samples"
        )
    expected_volume = (
        np.pi * rolling_contact.radius_m**2 * (2.0 * rolling_contact.half_height_m)
    )
    if not np.isclose(rolling_contact.volume_m3, expected_volume, rtol=0.0, atol=1.0e-12):
        raise ExperimentRunConfigError(
            "mabd_rolling_contact_candidate.volume_m3 must match the configured cylinder volume"
        )
    expected_mass = rolling_contact.density_kg_m3 * rolling_contact.volume_m3
    if not np.isclose(
        float(np.sum(rolling_contact.point_masses_kg)),
        expected_mass,
        rtol=0.0,
        atol=1.0e-9,
    ):
        raise ExperimentRunConfigError(
            "mabd_rolling_contact_candidate.point_masses_kg must sum to cylinder mass"
        )
    if not np.isclose(
        rolling_contact.initial_position_m[1],
        rolling_contact.radius_m,
        rtol=0.0,
        atol=1.0e-12,
    ):
        raise ExperimentRunConfigError(
            "mabd_rolling_contact_candidate.initial_position_m must place the cylinder on the plane"
        )
    expected_no_slip = (
        rolling_contact.initial_linear_velocity_m_s[0]
        + rolling_contact.initial_angular_velocity_rad_s[2] * rolling_contact.radius_m
    )
    if not np.isclose(expected_no_slip, 0.0, rtol=0.0, atol=1.0e-12):
        raise ExperimentRunConfigError(
            "mabd_rolling_contact_candidate initial velocities must satisfy the no-slip diagnostic"
        )
    if rolling_contact.young_modulus_pa <= 0.0:
        raise ExperimentRunConfigError(
            "mabd_rolling_contact_candidate.young_modulus_pa must be positive"
        )
    if rolling_contact.poisson_ratio <= -1.0 or rolling_contact.poisson_ratio >= 0.5:
        raise ExperimentRunConfigError(
            "mabd_rolling_contact_candidate.poisson_ratio must be in (-1, 0.5)"
        )
    if rolling_contact.zero_stiffness_diagnostic:
        raise ExperimentRunConfigError(
            "mabd_rolling_contact_candidate.zero_stiffness_diagnostic must be false"
        )
    if rolling_contact.contact_constraint_mode != "world":
        raise ExperimentRunConfigError(
            "mabd_rolling_contact_candidate.contact_constraint_mode must be world"
        )
    if not np.isclose(rolling_contact.radius_m, material.radius_m, rtol=0.0, atol=1.0e-15):
        raise ExperimentRunConfigError(
            "mabd_rolling_contact_candidate.radius_m must match mabd_material_preflight"
        )
    if not np.isclose(
        rolling_contact.half_height_m,
        material.half_height_m,
        rtol=0.0,
        atol=1.0e-15,
    ):
        raise ExperimentRunConfigError(
            "mabd_rolling_contact_candidate.half_height_m must match mabd_material_preflight"
        )
    if not np.isclose(
        rolling_contact.density_kg_m3,
        material.density_kg_m3,
        rtol=0.0,
        atol=1.0e-15,
    ):
        raise ExperimentRunConfigError(
            "mabd_rolling_contact_candidate.density_kg_m3 must match mabd_material_preflight"
        )
    if not np.allclose(
        rolling_contact.initial_linear_velocity_m_s,
        material.initial_linear_velocity_m_s,
        rtol=0.0,
        atol=1.0e-15,
    ):
        raise ExperimentRunConfigError(
            "mabd_rolling_contact_candidate.initial_linear_velocity_m_s must match mabd_material_preflight"
        )
    if not np.allclose(
        rolling_contact.initial_angular_velocity_rad_s,
        material.initial_angular_velocity_rad_s,
        rtol=0.0,
        atol=1.0e-15,
    ):
        raise ExperimentRunConfigError(
            "mabd_rolling_contact_candidate.initial_angular_velocity_rad_s must match mabd_material_preflight"
        )

    timing = config.paper_timing_protocol
    timing_report = timing.output_report
    timing_report_path = Path(timing_report)
    if (
        timing_report_path.is_absolute()
        or ".." in timing_report_path.parts
        or timing_report_path.parent.as_posix() != "reports/experiment_matrix"
        or timing_report_path.suffix != ".json"
        or timing_report != ROLLING_SPINNING_TIMING_PROTOCOL_OUTPUT_REPORT
        or timing_report
        in (
            config.output_report,
            config.rbd_implicit_baseline.output_report,
            config.rbd_explicit_baseline.output_report,
            config.rbd_no_slip_reference.output_report,
            config.rbd_explicit_no_slip_candidate.output_report,
            config.mabd_newton.output_report,
            config.mabd_material_preflight.output_report,
            config.mabd_rolling_contact_candidate.output_report,
        )
    ):
        raise ExperimentRunConfigError(
            "paper_timing_protocol.output_report must be the lane-specific "
            "relative JSON report under reports/experiment_matrix"
        )
    if timing.input_reports != ROLLING_SPINNING_TIMING_PROTOCOL_INPUT_REPORTS:
        raise ExperimentRunConfigError(
            "paper_timing_protocol.input_reports must list the rolling/spinning evidence reports"
        )
    if timing.paper_comparable:
        raise ExperimentRunConfigError("paper_timing_protocol.paper_comparable must be false")

    gate_ledger = config.paper_faithful_gate_ledger
    gate_ledger_report = gate_ledger.output_report
    gate_ledger_report_path = Path(gate_ledger_report)
    if (
        gate_ledger_report_path.is_absolute()
        or ".." in gate_ledger_report_path.parts
        or gate_ledger_report_path.parent.as_posix() != "reports/experiment_matrix"
        or gate_ledger_report_path.suffix != ".json"
        or gate_ledger_report
        != ROLLING_SPINNING_PAPER_FAITHFUL_GATE_LEDGER_OUTPUT_REPORT
        or gate_ledger_report
        in (
            config.output_report,
            config.rbd_implicit_baseline.output_report,
            config.rbd_explicit_baseline.output_report,
            config.rbd_no_slip_reference.output_report,
            config.rbd_explicit_no_slip_candidate.output_report,
            config.mabd_newton.output_report,
            config.mabd_material_preflight.output_report,
            config.mabd_rolling_contact_candidate.output_report,
            config.paper_timing_protocol.output_report,
        )
    ):
        raise ExperimentRunConfigError(
            "paper_faithful_gate_ledger.output_report must be the lane-specific "
            "relative JSON report under reports/experiment_matrix"
        )
    if (
        gate_ledger.required_gates
        != ROLLING_SPINNING_PAPER_FAITHFUL_GATE_LEDGER_REQUIRED_GATES
    ):
        raise ExperimentRunConfigError(
            "paper_faithful_gate_ledger.required_gates must list the required "
            "rolling/spinning paper-faithful evidence gates"
        )
    if (
        gate_ledger.current_evidence_reports
        != ROLLING_SPINNING_PAPER_FAITHFUL_GATE_LEDGER_CURRENT_EVIDENCE_REPORTS
    ):
        raise ExperimentRunConfigError(
            "paper_faithful_gate_ledger.current_evidence_reports must reference "
            "the current rolling/spinning incomplete evidence reports"
        )
    for evidence_path in gate_ledger.current_evidence_reports.values():
        report_path = Path(evidence_path)
        if (
            report_path.is_absolute()
            or ".." in report_path.parts
            or report_path.parent.as_posix() != "reports/experiment_matrix"
            or report_path.suffix != ".json"
        ):
            raise ExperimentRunConfigError(
                "paper_faithful_gate_ledger.current_evidence_reports must be "
                "relative JSON reports under reports/experiment_matrix"
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
        not config.paper_horizon.contacts_input_output_report.startswith(expected_prefix)
        or not config.paper_horizon.contacts_input_output_report.endswith(".json")
    ):
        raise ExperimentRunConfigError(
            "paper_horizon.contacts_input_output_report must be a lane-specific report under the matrix stem"
        )
    if config.paper_horizon.contacts_input_output_report in (
        config.output_report,
        config.paper_horizon.output_report,
        config.paper_horizon.contact_response_output_report,
        config.paper_horizon.normal_constraint_output_report,
        config.paper_horizon.model_plane_constraint_output_report,
        config.paper_horizon.affine_static_plane_contacts_output_report,
        config.paper_horizon.decoupled_twist_output_report,
        config.paper_horizon.figure_curve_output_report,
    ):
        raise ExperimentRunConfigError(
            "paper_horizon.contacts_input_output_report and "
            "paper_horizon.affine_static_plane_contacts_output_report must be separate "
            "from lane reports"
        )
    if (
        not config.paper_horizon.affine_static_plane_contacts_output_report.startswith(expected_prefix)
        or not config.paper_horizon.affine_static_plane_contacts_output_report.endswith(".json")
    ):
        raise ExperimentRunConfigError(
            "paper_horizon.affine_static_plane_contacts_output_report must be a lane-specific report under the matrix stem"
        )
    if config.paper_horizon.affine_static_plane_contacts_output_report in (
        config.output_report,
        config.paper_horizon.output_report,
        config.paper_horizon.contact_response_output_report,
        config.paper_horizon.normal_constraint_output_report,
        config.paper_horizon.model_plane_constraint_output_report,
        config.paper_horizon.contacts_input_output_report,
        config.paper_horizon.decoupled_twist_output_report,
        config.paper_horizon.figure_curve_output_report,
    ):
        raise ExperimentRunConfigError(
            "paper_horizon.affine_static_plane_contacts_output_report and "
            "paper_horizon.contacts_input_output_report must be separate from lane reports"
        )
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
        config.paper_horizon.contacts_input_output_report,
        config.paper_horizon.affine_static_plane_contacts_output_report,
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
        config.paper_horizon.contacts_input_output_report,
        config.paper_horizon.affine_static_plane_contacts_output_report,
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
    "ROLLING_SPINNING_RBD_CONTACT_KEYS",
    "ROLLING_SPINNING_RBD_EXPLICIT_BASELINE_OUTPUT_REPORT",
    "ROLLING_SPINNING_RBD_IMPLICIT_BASELINE_OUTPUT_REPORT",
    "ROLLING_SPINNING_RBD_THRESHOLD_KEYS",
    "ROLLING_SPINNING_MABD_MATERIAL_PREFLIGHT_OUTPUT_REPORT",
    "ROLLING_SPINNING_MABD_NEWTON_OUTPUT_REPORT",
    "ROLLING_SPINNING_MABD_NEWTON_THRESHOLD_KEYS",
    "ROLLING_SPINNING_REQUIRED_MISSING_LANES",
    "ROLLING_SPINNING_TIMING_KEYS",
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
    "RollingSpinningMABDNewtonConfig",
    "RollingSpinningPerformanceConfig",
    "RollingSpinningRBDBaselineConfig",
    "RollingSpinningRunConfig",
    "SpinningBoxPaperHorizonConfig",
    "SpinningBoxRunConfig",
    "THandleComparisonConfig",
    "THandleFigureCurvesConfig",
    "THandleMABDNewtonConfig",
    "THandleReferenceConfig",
    "THandleRunConfig",
    "load_physical_pendulum_config",
    "load_rolling_spinning_config",
    "load_spinning_box_config",
    "load_t_handle_config",
    "load_heavy_top_config",
    "validate_heavy_top_config_against_matrix",
    "validate_physical_pendulum_config_against_matrix",
    "validate_rolling_spinning_config_against_matrix",
    "validate_spinning_box_config_against_matrix",
    "validate_t_handle_config_against_matrix",
]
