"""Report writer for the T-handle RK4 diagnostic lane."""

from __future__ import annotations

from pathlib import Path

from .experiment_configs import THandleRunConfig
from .reporting import ClaimReport, EvidenceStatus, write_claim_report
from .t_handle_reference import THandleReferenceTrajectory, roll_out_t_handle_rk4_reference


T_HANDLE_REPORT_BLOCKERS = (
    "exact_t_handle_geometry_unknown",
    "raw_t_handle_reference_curve_data_missing",
    "mabd_newton_report_missing",
    "t_handle_comparison_report_missing",
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
        asset_hashes={"t_handle_procedural": "not_applicable_procedural_diagnostic"},
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


__all__ = [
    "T_HANDLE_REPORT_BLOCKERS",
    "write_t_handle_rk4_reference_report",
]
