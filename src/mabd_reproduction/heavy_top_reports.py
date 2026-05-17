"""Report writer for the heavy-top RK4 diagnostic lane."""

from __future__ import annotations

from pathlib import Path

from .experiment_configs import HeavyTopRunConfig
from .heavy_top_mabd import (
    NEWTON_MODEL_DERIVED_CONFIG_SOURCE,
    NEWTON_MODEL_DERIVED_CUSTOM_FREQUENCIES,
    HeavyTopMABDRollout,
    roll_out_heavy_top_mabd_model_derived,
)
from .heavy_top_reference import (
    HeavyTopReferenceTrajectory,
    roll_out_heavy_top_rk4_reference,
)
from .reporting import ClaimReport, EvidenceStatus, write_claim_report


HEAVY_TOP_REPORT_BLOCKERS = (
    "exact_heavy_top_inertia_unknown",
    "exact_heavy_top_geometry_unknown",
    "raw_heavy_top_reference_curve_data_missing",
    "mabd_newton_report_incomplete",
    "heavy_top_comparison_report_incomplete",
    "heavy_top_timing_evidence_missing",
)
HEAVY_TOP_MABD_REPORT_BLOCKERS = (
    "exact_heavy_top_inertia_unknown",
    "exact_heavy_top_geometry_unknown",
    "raw_heavy_top_reference_curve_data_missing",
    "mabd_newton_report_incomplete",
    "heavy_top_comparison_report_incomplete",
    "heavy_top_timing_evidence_missing",
)


def _clean_report_float(value: float) -> float:
    result = float(value)
    return 0.0 if abs(result) < 1.0e-14 else result


def _sample_rows(trajectory: HeavyTopReferenceTrajectory) -> list[dict[str, float | int]]:
    return [
        {
            "sample_index": int(index),
            "time_s": _clean_report_float(row[0]),
            "nutation_angle_deg": _clean_report_float(row[1]),
            "precession_angle_rad": _clean_report_float(row[2]),
            "precession_velocity_rad_s": _clean_report_float(row[3]),
        }
        for index, row in enumerate(trajectory.samples)
    ]


def _mabd_sample_rows(rollout: HeavyTopMABDRollout) -> list[dict[str, float | int | list[float]]]:
    return [
        {
            "sample_index": sample.sample_index,
            "step": sample.step,
            "time_s": _clean_report_float(sample.time_s),
            "nutation_angle_deg": _clean_report_float(sample.nutation_angle_deg),
            "precession_angle_rad": _clean_report_float(sample.precession_angle_rad),
            "precession_velocity_rad_s": _clean_report_float(
                sample.precession_velocity_rad_s
            ),
            "pivot_residual_m": _clean_report_float(sample.pivot_residual_m),
            "constraint_residual_norm": _clean_report_float(sample.constraint_residual_norm),
            "affine_shape_spread_m": _clean_report_float(sample.affine_shape_spread_m),
            "world_anchor_reaction_vector_n": [
                _clean_report_float(component)
                for component in sample.world_anchor_reaction_vector_n.tolist()
            ],
            "world_anchor_reaction_magnitude_n": _clean_report_float(
                sample.world_anchor_reaction_magnitude_n
            ),
        }
        for sample in rollout.samples
    ]


def write_heavy_top_rk4_reference_report(
    path: str | Path,
    *,
    config: HeavyTopRunConfig,
    source_commit: str,
    vendored_newton_commit: str,
    paper_source_version: str = "2603.08079v2",
) -> ClaimReport:
    trajectory = roll_out_heavy_top_rk4_reference(config)
    thresholds = config.reference.thresholds
    threshold_violations: list[str] = []
    if abs(trajectory.relative_energy_drift) > thresholds["max_relative_energy_drift"]:
        threshold_violations.append("max_relative_energy_drift")
    if (
        trajectory.max_nutation_angle_deg - trajectory.min_nutation_angle_deg
        < thresholds["min_nutation_angle_range_deg"]
    ):
        threshold_violations.append("min_nutation_angle_range_deg")
    if (
        trajectory.max_abs_precession_velocity_rad_s
        < thresholds["min_abs_precession_velocity_rad_s"]
    ):
        threshold_violations.append("min_abs_precession_velocity_rad_s")

    observed = {
        "lane_status": "diagnostic_generated" if not threshold_violations else "diagnostic_failed",
        "full_experiment_claim_passed": False,
        "reference_not_paper_inertia": True,
        "reference_not_paper_geometry": True,
        "reference_scope": "fixed_pivot_rbd_rk4_heavy_top_diagnostic",
        "time_step_s": config.reference.time_step_s,
        "duration_s": config.reference.duration_s,
        "sample_count": config.reference.sample_count,
        "principal_inertia_kg_m2": config.reference.principal_inertia_kg_m2.tolist(),
        "mass_kg": config.reference.mass_kg,
        "pivot_to_com_m": config.reference.pivot_to_com_m.tolist(),
        "gravity_m_s2": config.reference.gravity_m_s2.tolist(),
        "initial_tilt_deg": config.reference.initial_tilt_deg,
        "initial_spin_rad_s": config.reference.initial_spin_rad_s,
        "energy_initial": trajectory.energy_initial,
        "energy_final": trajectory.energy_final,
        "relative_energy_drift": trajectory.relative_energy_drift,
        "angular_momentum_norm_initial": trajectory.angular_momentum_norm_initial,
        "angular_momentum_norm_final": trajectory.angular_momentum_norm_final,
        "angular_momentum_norm_drift": trajectory.angular_momentum_norm_drift,
        "min_nutation_angle_deg": trajectory.min_nutation_angle_deg,
        "max_nutation_angle_deg": trajectory.max_nutation_angle_deg,
        "max_abs_precession_velocity_rad_s": trajectory.max_abs_precession_velocity_rad_s,
        "precession_nutation_samples": _sample_rows(trajectory),
        "threshold_violations": threshold_violations,
        "blocking_reasons": list(HEAVY_TOP_REPORT_BLOCKERS),
        "required_missing_lanes": list(config.required_missing_lanes),
    }
    report = ClaimReport(
        claim_id=config.claim_id,
        scene_id=config.scene_id,
        asset_hashes={"heavy_top_procedural": "not_applicable_procedural"},
        solver_mode="heavy_top_rk4_reference_diagnostic",
        backend="cpu_numpy",
        baseline_lane=config.baseline_lane,
        expected={
            "paper_claim_status": "RK4 reference diagnostic lane only; full experiment incomplete",
            "source_lines": list(config.source_lines),
            "paper_values": config.paper_values,
            "figure_pdf_sha256": config.reference.figure_pdf_sha256,
            "figure_text_source": config.reference.figure_text_source,
            "matrix_claim_report": "reports/experiment_matrix/single_body_heavy_top.json",
            "lane_report": config.reference.output_report,
            "known_source_gaps": [
                "exact_heavy_top_inertia_unknown",
                "exact_heavy_top_geometry_unknown",
                "raw_heavy_top_reference_curve_data_missing",
            ],
            "blocking_reasons": list(HEAVY_TOP_REPORT_BLOCKERS),
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


def write_heavy_top_mabd_newton_report(
    path: str | Path,
    *,
    config: HeavyTopRunConfig,
    source_commit: str,
    vendored_newton_commit: str,
    paper_source_version: str = "2603.08079v2",
) -> ClaimReport:
    rollout = roll_out_heavy_top_mabd_model_derived(config)
    thresholds = config.mabd_newton.thresholds
    threshold_violations: list[str] = []
    if rollout.max_pivot_residual_m > thresholds["max_pivot_residual_m"]:
        threshold_violations.append("max_pivot_residual_m")
    if rollout.max_constraint_residual_norm > thresholds["max_constraint_residual_norm"]:
        threshold_violations.append("max_constraint_residual_norm")
    if (
        rollout.max_nutation_angle_deg - rollout.min_nutation_angle_deg
        < thresholds["min_nutation_angle_range_deg"]
    ):
        threshold_violations.append("min_nutation_angle_range_deg")
    if rollout.max_affine_shape_spread_m > thresholds["max_affine_shape_spread_m"]:
        threshold_violations.append("max_affine_shape_spread_m")
    if not rollout.finite:
        threshold_violations.append("finite_rollout")

    lane_status = (
        "incomplete_diagnostic_generated"
        if not threshold_violations
        else "incomplete_diagnostic_failed"
    )
    observed = {
        "lane_status": lane_status,
        "full_experiment_claim_passed": False,
        "step_count": rollout.step_count,
        "sample_count": rollout.sample_count,
        "time_step_s": rollout.time_step_s,
        "mabd_rotation_mode": rollout.rotation_mode,
        "solver_model_config_source": rollout.solver_model_config_source,
        "newton_model_derived_custom_frequencies": list(NEWTON_MODEL_DERIVED_CUSTOM_FREQUENCIES),
        "rest_points_m": config.mabd_newton.rest_points_m.tolist(),
        "point_masses_kg": config.mabd_newton.point_masses_kg.tolist(),
        "pivot_rest_point_m": config.mabd_newton.pivot_rest_point_m.tolist(),
        "pivot_world_point_m": config.mabd_newton.pivot_world_point_m.tolist(),
        "angle_probe_rest_point_m": config.mabd_newton.angle_probe_rest_point_m.tolist(),
        "gravity_m_s2": config.mabd_newton.gravity_m_s2.tolist(),
        "energy_initial": rollout.energy_initial,
        "energy_final": rollout.energy_final,
        "relative_energy_drift": rollout.relative_energy_drift,
        "min_nutation_angle_deg": rollout.min_nutation_angle_deg,
        "max_nutation_angle_deg": rollout.max_nutation_angle_deg,
        "max_abs_precession_velocity_rad_s": rollout.max_abs_precession_velocity_rad_s,
        "max_pivot_residual_m": rollout.max_pivot_residual_m,
        "max_constraint_residual_norm": rollout.max_constraint_residual_norm,
        "max_affine_shape_spread_m": rollout.max_affine_shape_spread_m,
        "max_world_anchor_reaction_magnitude_n": rollout.max_world_anchor_reaction_magnitude_n,
        "threshold_violations": threshold_violations,
        "required_missing_lanes": list(config.required_missing_lanes),
        "blocking_reasons": list(HEAVY_TOP_MABD_REPORT_BLOCKERS),
        "precession_nutation_samples": _mabd_sample_rows(rollout),
    }
    report = ClaimReport(
        claim_id=config.claim_id,
        scene_id=config.scene_id,
        asset_hashes={"heavy_top_procedural": "not_applicable_procedural"},
        solver_mode="mabd_cpu_oracle_heavy_top_newton_lane",
        backend="cpu_numpy_newton_only",
        baseline_lane="mabd_newton",
        expected={
            "paper_claim_status": "formal M-ABD lane generated; full heavy-top experiment incomplete",
            "source_lines": list(config.source_lines),
            "paper_values": config.paper_values,
            "figure_pdf_sha256": config.reference.figure_pdf_sha256,
            "figure_text_source": config.reference.figure_text_source,
            "matrix_claim_report": "reports/experiment_matrix/single_body_heavy_top.json",
            "lane_report": config.mabd_newton.output_report,
            "solver_model_config_source": NEWTON_MODEL_DERIVED_CONFIG_SOURCE,
            "newton_model_derived_custom_frequencies": list(NEWTON_MODEL_DERIVED_CUSTOM_FREQUENCIES),
            "world_anchor_constraint": {
                "pivot_rest_point_m": config.mabd_newton.pivot_rest_point_m.tolist(),
                "pivot_world_point_m": config.mabd_newton.pivot_world_point_m.tolist(),
            },
            "known_source_gaps": [
                "exact_heavy_top_inertia_unknown",
                "exact_heavy_top_geometry_unknown",
                "raw_heavy_top_reference_curve_data_missing",
            ],
            "nonclaim_limitations": [
                "procedural point-mass tetrahedron is not the paper's undisclosed heavy-top geometry",
                "configured inertia is not matched to the paper's undisclosed heavy-top inertia",
                "no raw paper curve digitization or curve agreement gate is generated",
                "no ABD-vs-RBD comparison pass gate is generated",
                "no rendered figure or timing distribution is generated",
            ],
            "blocking_reasons": list(HEAVY_TOP_MABD_REPORT_BLOCKERS),
            "full_experiment_claim_passed": False,
        },
        observed=observed,
        threshold=dict(thresholds),
        unit="angle_deg",
        status=EvidenceStatus.INCOMPLETE,
        failure_reason=(
            "heavy_top mabd_newton diagnostic lane remains incomplete because "
            "exact_heavy_top_inertia_unknown, exact_heavy_top_geometry_unknown, "
            "raw_heavy_top_reference_curve_data_missing, heavy_top_comparison_report_incomplete, "
            "and heavy_top_timing_evidence_missing remain unresolved"
        ),
        timing_distribution={"status": "not_measured", "paper_comparable": False},
        raw_outputs={"time_series": "compact_samples_only"},
        plot_paths={},
        source_commit=source_commit,
        vendored_newton_commit=vendored_newton_commit,
        paper_source_version=paper_source_version,
    )
    write_claim_report(report, path)
    return report


__all__ = [
    "HEAVY_TOP_MABD_REPORT_BLOCKERS",
    "HEAVY_TOP_REPORT_BLOCKERS",
    "write_heavy_top_mabd_newton_report",
    "write_heavy_top_rk4_reference_report",
]
