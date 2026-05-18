"""Report writers for the T-handle diagnostic lanes."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from .experiment_configs import THandleRunConfig
from .reporting import ClaimReport, EvidenceStatus, write_claim_report
from .t_handle_mabd import THandleMABDRollout, roll_out_t_handle_mabd_model_derived
from .t_handle_reference import THandleReferenceTrajectory, roll_out_t_handle_rk4_reference


T_HANDLE_REPORT_BLOCKERS = (
    "exact_t_handle_geometry_unknown",
    "raw_t_handle_reference_curve_data_missing",
    "mabd_newton_report_incomplete",
    "t_handle_comparison_report_incomplete",
    "t_handle_timing_evidence_missing",
)
T_HANDLE_MABD_REPORT_BLOCKERS = (
    "exact_t_handle_geometry_unknown",
    "raw_t_handle_reference_curve_data_missing",
    "mabd_newton_report_incomplete",
    "t_handle_comparison_report_incomplete",
    "t_handle_timing_evidence_missing",
)


def _clean_report_float(value: float) -> float:
    result = float(value)
    return 0.0 if abs(result) < 1.0e-14 else result


def _sample_rows(trajectory: THandleReferenceTrajectory) -> list[dict[str, float | int]]:
    return [
        {
            "sample_index": int(index),
            "time_s": _clean_report_float(row[0]),
            "omega_x_rad_s": _clean_report_float(row[1]),
            "omega_y_rad_s": _clean_report_float(row[2]),
            "omega_z_rad_s": _clean_report_float(row[3]),
        }
        for index, row in enumerate(trajectory.samples)
    ]


def _mabd_sample_rows(rollout: THandleMABDRollout) -> list[dict[str, float | int]]:
    return [
        {
            "sample_index": sample.sample_index,
            "step": sample.step,
            "time_s": _clean_report_float(sample.time_s),
            "omega_x_rad_s": _clean_report_float(sample.angular_velocity_rad_s[0]),
            "omega_y_rad_s": _clean_report_float(sample.angular_velocity_rad_s[1]),
            "omega_z_rad_s": _clean_report_float(sample.angular_velocity_rad_s[2]),
            "energy": _clean_report_float(sample.energy),
            "angular_momentum_norm": _clean_report_float(sample.angular_momentum_norm),
            "affine_shape_spread_m": _clean_report_float(sample.affine_shape_spread_m),
        }
        for sample in rollout.samples
    ]


def write_t_handle_rk4_reference_report(
    path: str | Path,
    *,
    config: THandleRunConfig,
    source_commit: str,
    vendored_newton_commit: str,
    paper_source_version: str = "2603.08079v2",
) -> ClaimReport:
    trajectory = roll_out_t_handle_rk4_reference(config)
    thresholds = config.reference.thresholds
    threshold_violations: list[str] = []
    if abs(trajectory.relative_energy_drift) > thresholds["max_relative_energy_drift"]:
        threshold_violations.append("max_relative_energy_drift")
    if (
        abs(trajectory.angular_momentum_norm_drift)
        > thresholds["max_angular_momentum_norm_drift"]
    ):
        threshold_violations.append("max_angular_momentum_norm_drift")
    if (
        trajectory.intermediate_axis_sign_flips
        < thresholds["min_intermediate_axis_sign_flips"]
    ):
        threshold_violations.append("min_intermediate_axis_sign_flips")

    observed = {
        "lane_status": "diagnostic_generated" if not threshold_violations else "diagnostic_failed",
        "full_experiment_claim_passed": False,
        "reference_not_paper_geometry": True,
        "reference_scope": "torque_free_principal_axis_rk4_diagnostic",
        "time_step_s": config.reference.time_step_s,
        "duration_s": config.reference.duration_s,
        "sample_count": config.reference.sample_count,
        "principal_inertia_kg_m2": config.reference.principal_inertia_kg_m2.tolist(),
        "intermediate_axis_index": config.reference.intermediate_axis_index,
        "initial_angular_velocity_rad_s": (
            config.reference.initial_angular_velocity_rad_s.tolist()
        ),
        "gravity_m_s2": config.reference.gravity_m_s2.tolist(),
        "energy_initial": trajectory.energy_initial,
        "energy_final": trajectory.energy_final,
        "relative_energy_drift": trajectory.relative_energy_drift,
        "angular_momentum_norm_initial": trajectory.angular_momentum_norm_initial,
        "angular_momentum_norm_final": trajectory.angular_momentum_norm_final,
        "angular_momentum_norm_drift": trajectory.angular_momentum_norm_drift,
        "intermediate_axis_sign_flips": trajectory.intermediate_axis_sign_flips,
        "angular_velocity_samples": _sample_rows(trajectory),
        "threshold_violations": threshold_violations,
        "blocking_reasons": list(T_HANDLE_REPORT_BLOCKERS),
        "required_missing_lanes": list(config.required_missing_lanes),
    }
    report = ClaimReport(
        claim_id=config.claim_id,
        scene_id=config.scene_id,
        asset_hashes={"t_handle_procedural": "not_applicable_procedural"},
        solver_mode="t_handle_torque_free_rk4_reference",
        backend="cpu_numpy",
        baseline_lane=config.baseline_lane,
        expected={
            "paper_claim_status": "RK4 reference diagnostic lane only; full experiment incomplete",
            "source_lines": list(config.source_lines),
            "paper_values": config.paper_values,
            "figure_pdf_sha256": config.reference.figure_pdf_sha256,
            "figure_text_source": config.reference.figure_text_source,
            "matrix_claim_report": "reports/experiment_matrix/single_body_t_handle.json",
            "lane_report": config.reference.output_report,
            "known_source_gaps": [
                "exact_t_handle_geometry_unknown",
                "principal_inertias_unknown",
                "subtle_asymmetry_magnitude_unknown",
                "raw_t_handle_reference_curve_data_missing",
            ],
            "blocking_reasons": list(T_HANDLE_REPORT_BLOCKERS),
            "full_experiment_claim_passed": False,
        },
        observed=observed,
        threshold=dict(thresholds),
        unit="dimensionless",
        status=EvidenceStatus.INCOMPLETE,
        failure_reason=config.failure_reason,
        timing_distribution={"status": "not_measured", "paper_comparable": False},
        raw_outputs={},
        plot_paths={},
        source_commit=source_commit,
        vendored_newton_commit=vendored_newton_commit,
        paper_source_version=paper_source_version,
    )
    write_claim_report(report, path)
    return report


def write_t_handle_mabd_newton_report(
    path: str | Path,
    *,
    config: THandleRunConfig,
    source_commit: str,
    vendored_newton_commit: str,
    paper_source_version: str = "2603.08079v2",
) -> ClaimReport:
    rollout = roll_out_t_handle_mabd_model_derived(config)
    finite_values = (
        rollout.energy_initial,
        rollout.energy_final,
        rollout.relative_energy_drift,
        rollout.angular_momentum_norm_initial,
        rollout.angular_momentum_norm_final,
        rollout.angular_momentum_norm_drift,
        rollout.max_proxy_inertia_relative_error,
        rollout.max_affine_shape_spread_m,
    )
    if (
        not rollout.finite
        or not all(np.isfinite(value) for value in finite_values)
        or not np.all(np.isfinite(rollout.proxy_inertia_kg_m2))
        or not np.all(np.isfinite(rollout.reference_inertia_kg_m2))
    ):
        raise ValueError("T-handle MABD Newton rollout must be finite before writing a report")
    thresholds = config.mabd_newton.thresholds
    threshold_violations: list[str] = []
    if abs(rollout.relative_energy_drift) > thresholds["max_relative_energy_drift"]:
        threshold_violations.append("max_relative_energy_drift")
    if (
        abs(rollout.angular_momentum_norm_drift)
        > thresholds["max_angular_momentum_norm_drift"]
    ):
        threshold_violations.append("max_angular_momentum_norm_drift")
    if rollout.max_affine_shape_spread_m > thresholds["max_affine_shape_spread_m"]:
        threshold_violations.append("max_affine_shape_spread_m")
    if (
        rollout.max_proxy_inertia_relative_error
        > thresholds["max_proxy_inertia_relative_error"]
    ):
        threshold_violations.append("max_proxy_inertia_relative_error")

    observed = {
        "lane_status": (
            "incomplete_diagnostic_generated"
            if not threshold_violations and rollout.finite
            else "incomplete_diagnostic_failed"
        ),
        "full_experiment_claim_passed": False,
        "reference_not_paper_geometry": True,
        "mabd_diagnostic_scope": "t_handle_model_derived_proxy",
        "solver_model_config_source": rollout.solver_model_config_source,
        "newton_model_derived_custom_frequencies": list(
            rollout.newton_model_derived_custom_frequencies
        ),
        "time_step_s": rollout.time_step_s,
        "step_count": rollout.step_count,
        "sample_count": rollout.sample_count,
        "duration_s": rollout.step_count * rollout.time_step_s,
        "rotation_mode": rollout.rotation_mode,
        "finite": rollout.finite,
        "rest_points_m": config.mabd_newton.rest_points_m.tolist(),
        "point_masses_kg": config.mabd_newton.point_masses_kg.tolist(),
        "volume_m3": config.mabd_newton.volume_m3,
        "gravity_m_s2": config.mabd_newton.gravity_m_s2.tolist(),
        "initial_angular_velocity_rad_s": (
            config.mabd_newton.initial_angular_velocity_rad_s.tolist()
        ),
        "reference_principal_inertia_kg_m2": rollout.reference_inertia_kg_m2.tolist(),
        "proxy_principal_inertia_kg_m2": rollout.proxy_inertia_kg_m2.tolist(),
        "max_proxy_inertia_relative_error": rollout.max_proxy_inertia_relative_error,
        "energy_initial": rollout.energy_initial,
        "energy_final": rollout.energy_final,
        "relative_energy_drift": rollout.relative_energy_drift,
        "angular_momentum_norm_initial": rollout.angular_momentum_norm_initial,
        "angular_momentum_norm_final": rollout.angular_momentum_norm_final,
        "angular_momentum_norm_drift": rollout.angular_momentum_norm_drift,
        "max_affine_shape_spread_m": rollout.max_affine_shape_spread_m,
        "angular_velocity_samples": _mabd_sample_rows(rollout),
        "threshold_violations": threshold_violations,
        "blocking_reasons": list(T_HANDLE_MABD_REPORT_BLOCKERS),
        "required_missing_lanes": [],
    }
    report = ClaimReport(
        claim_id=config.claim_id,
        scene_id=config.scene_id,
        asset_hashes={"t_handle_procedural": "not_applicable_procedural"},
        solver_mode="mabd_cpu_oracle_t_handle_newton_lane",
        backend="cpu_numpy_newton_only",
        baseline_lane="mabd_newton",
        expected={
            "paper_claim_status": "Newton MABD diagnostic lane only; full experiment incomplete",
            "source_lines": list(config.source_lines),
            "paper_values": config.paper_values,
            "figure_pdf_sha256": config.reference.figure_pdf_sha256,
            "figure_text_source": config.reference.figure_text_source,
            "matrix_claim_report": "reports/experiment_matrix/single_body_t_handle.json",
            "lane_report": config.mabd_newton.output_report,
            "known_source_gaps": [
                "exact_t_handle_geometry_unknown",
                "principal_inertias_only_proxy",
                "subtle_asymmetry_magnitude_unknown",
                "raw_t_handle_reference_curve_data_missing",
            ],
            "blocking_reasons": list(T_HANDLE_MABD_REPORT_BLOCKERS),
            "full_experiment_claim_passed": False,
        },
        observed=observed,
        threshold=dict(thresholds),
        unit="dimensionless",
        status=EvidenceStatus.INCOMPLETE,
        failure_reason=(
            "t_handle mabd_newton diagnostic lane remains incomplete because "
            "paper-faithful geometry, raw waveform agreement, comparison, and timing "
            "evidence are unavailable"
        ),
        timing_distribution={"status": "not_measured", "paper_comparable": False},
        raw_outputs={},
        plot_paths={},
        source_commit=source_commit,
        vendored_newton_commit=vendored_newton_commit,
        paper_source_version=paper_source_version,
    )
    write_claim_report(report, path)
    return report


__all__ = [
    "T_HANDLE_MABD_REPORT_BLOCKERS",
    "T_HANDLE_REPORT_BLOCKERS",
    "write_t_handle_mabd_newton_report",
    "write_t_handle_rk4_reference_report",
]
