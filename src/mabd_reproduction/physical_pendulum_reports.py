"""Report writers for physical-pendulum reproduction lanes."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from .experiment_configs import PhysicalPendulumRunConfig
from .physical_pendulum_reference import (
    physical_pendulum_angle_reference,
    physical_pendulum_complete_elliptic_k,
    physical_pendulum_period_s,
)
from .physical_pendulum_mabd import (
    PhysicalPendulumMABDRollout,
    roll_out_physical_pendulum_mabd_development,
)
from .reporting import ClaimReport, write_claim_report


def _clean_report_float(value: float) -> float:
    result = float(value)
    return 0.0 if abs(result) < 1.0e-15 else result


def _angle_samples(
    *,
    config: PhysicalPendulumRunConfig,
    period_s: float,
) -> list[dict[str, float]]:
    duration = config.reference.period_count * period_s
    times = np.linspace(0.0, duration, config.reference.sample_count)
    angles = physical_pendulum_angle_reference(
        times,
        kappa=config.reference.kappa,
        omega_lin=config.reference.omega_lin_rad_s,
    )
    return [
        {
            "sample_index": int(index),
            "time_s": _clean_report_float(time_s),
            "angle_rad": _clean_report_float(angle_rad),
        }
        for index, (time_s, angle_rad) in enumerate(zip(times, angles, strict=True))
    ]


def _identity_error(config: PhysicalPendulumRunConfig) -> float:
    complete = physical_pendulum_complete_elliptic_k(config.reference.kappa)
    times = np.asarray(
        [
            0.0,
            complete / config.reference.omega_lin_rad_s,
            2.0 * complete / config.reference.omega_lin_rad_s,
        ],
        dtype=float,
    )
    expected = np.asarray([0.0, np.pi / 2.0, np.pi], dtype=float)
    observed = physical_pendulum_angle_reference(
        times,
        kappa=config.reference.kappa,
        omega_lin=config.reference.omega_lin_rad_s,
    )
    return float(np.max(np.abs(observed - expected)))


def _development_sample_rows(rollout: PhysicalPendulumMABDRollout) -> list[dict[str, float | int]]:
    return [
        {
            "sample_index": sample.sample_index,
            "step": sample.step,
            "time_s": _clean_report_float(sample.time_s),
            "angle_rad": _clean_report_float(sample.angle_rad),
            "reference_angle_rad": _clean_report_float(sample.reference_angle_rad),
            "abs_angle_error_rad": _clean_report_float(sample.abs_angle_error_rad),
            "pivot_residual_m": _clean_report_float(sample.pivot_residual_m),
            "constraint_residual_norm": _clean_report_float(sample.constraint_residual_norm),
        }
        for sample in rollout.samples
    ]


def write_physical_pendulum_analytic_reference_report(
    path: str | Path,
    *,
    config: PhysicalPendulumRunConfig,
    source_commit: str,
    vendored_newton_commit: str,
    paper_source_version: str = "2603.08079v2",
) -> ClaimReport:
    period_s = physical_pendulum_period_s(
        kappa=config.reference.kappa,
        omega_lin=config.reference.omega_lin_rad_s,
    )
    max_abs_identity_error = _identity_error(config)
    threshold_violations = (
        []
        if max_abs_identity_error <= config.thresholds["max_abs_reference_identity_error"]
        else ["max_abs_reference_identity_error"]
    )
    observed = {
        "lane_status": "passed" if not threshold_violations else "failed",
        "full_experiment_claim_passed": False,
        "sample_count": config.reference.sample_count,
        "period_count": config.reference.period_count,
        "period_s": period_s,
        "duration_s": config.reference.period_count * period_s,
        "release_angle_rad": config.reference.release_angle_rad,
        "initial_angle_rad": config.reference.initial_angle_rad,
        "kappa": config.reference.kappa,
        "omega_lin_rad_s": config.reference.omega_lin_rad_s,
        "max_abs_reference_identity_error": max_abs_identity_error,
        "threshold_violations": threshold_violations,
        "required_missing_lanes": list(config.required_missing_lanes),
        "blocking_reasons": ["pendulum_geometry_unknown"],
        "angle_samples_rad": _angle_samples(config=config, period_s=period_s),
    }
    report = ClaimReport(
        claim_id=config.claim_id,
        scene_id=config.scene_id,
        asset_hashes={"physical_pendulum_procedural": "not_applicable_procedural"},
        solver_mode="analytic_elliptic_reference",
        backend="cpu_scipy_reference",
        baseline_lane=config.baseline_lane,
        expected={
            "paper_claim_status": "analytic reference lane only; full experiment incomplete",
            "source_lines": list(config.source_lines),
            "paper_values": config.paper_values,
            "formula": (
                "theta(t)=pi/2 - 2 asin(kappa * "
                "sn(K(kappa) - omega_lin * t, kappa))"
            ),
            "scipy_parameterization": "ellipk/ellipj use m=kappa**2",
            "full_experiment_claim_passed": False,
        },
        observed=observed,
        threshold=config.thresholds,
        unit="angle_rad",
        status=config.report_status,
        failure_reason=config.failure_reason,
        timing_distribution={"scope": "not_timed", "lane": "analytic_reference"},
        raw_outputs={"time_series": "compact_samples_only"},
        plot_paths={},
        source_commit=source_commit,
        vendored_newton_commit=vendored_newton_commit,
        paper_source_version=paper_source_version,
    )
    write_claim_report(report, path)
    return report


def write_physical_pendulum_mabd_development_report(
    path: str | Path,
    *,
    config: PhysicalPendulumRunConfig,
    source_commit: str,
    vendored_newton_commit: str,
    paper_source_version: str = "2603.08079v2",
) -> ClaimReport:
    rollout = roll_out_physical_pendulum_mabd_development(config)
    thresholds = config.mabd_development.thresholds
    threshold_violations: list[str] = []
    if rollout.max_pivot_residual_m > thresholds["max_pivot_residual_m"]:
        threshold_violations.append("max_pivot_residual_m")
    if rollout.max_constraint_residual_norm > thresholds["max_constraint_residual_norm"]:
        threshold_violations.append("max_constraint_residual_norm")
    if rollout.max_abs_angle_error_rad > thresholds["max_abs_angle_error_rad"]:
        threshold_violations.append("max_abs_angle_error_rad")
    if not rollout.finite:
        threshold_violations.append("finite_rollout")

    lane_status = (
        "development_diagnostic_generated"
        if not threshold_violations
        else "development_diagnostic_failed"
    )
    observed = {
        "lane_status": lane_status,
        "full_experiment_claim_passed": False,
        "step_count": rollout.step_count,
        "sample_count": rollout.sample_count,
        "time_step_s": rollout.time_step_s,
        "max_pivot_residual_m": rollout.max_pivot_residual_m,
        "max_constraint_residual_norm": rollout.max_constraint_residual_norm,
        "max_abs_angle_error_rad": rollout.max_abs_angle_error_rad,
        "threshold_violations": threshold_violations,
        "required_missing_lanes": list(config.required_missing_lanes),
        "blocking_reasons": [
            "pendulum_geometry_unknown",
            "rbd_implicit_baseline",
            "joint_force_comparison_missing",
            "paper_geometry_and_timing_missing",
        ],
        "angle_samples_rad": _development_sample_rows(rollout),
    }
    report = ClaimReport(
        claim_id=config.claim_id,
        scene_id=config.scene_id,
        asset_hashes={"physical_pendulum_procedural": "not_applicable_procedural"},
        solver_mode="mabd_cpu_oracle_physical_pendulum_development",
        backend="cpu_numpy_newton_only",
        baseline_lane="physical_pendulum_mabd_development_diagnostic",
        expected={
            "paper_claim_status": "development diagnostic only; full experiment incomplete",
            "source_lines": list(config.source_lines),
            "paper_values": config.paper_values,
            "world_anchor_constraint": {
                "pivot_rest_point_m": config.mabd_development.pivot_rest_point_m.tolist(),
                "pivot_world_point_m": config.mabd_development.pivot_world_point_m.tolist(),
            },
            "nonclaim_limitations": [
                "procedural point set is not the paper's undisclosed physical-pendulum geometry",
                "no joint-force waveform comparison is generated",
                "no implicit RBD baseline comparison is generated",
                "no rendered figure or timing distribution is generated",
            ],
            "full_experiment_claim_passed": False,
        },
        observed=observed,
        threshold=thresholds,
        unit="angle_rad",
        status=config.report_status,
        failure_reason=(
            "physical_pendulum_mabd_development diagnostic only; required mabd_newton lane, "
            "rbd_implicit_baseline, joint-force comparison, and pendulum_geometry_unknown "
            "remain incomplete"
        ),
        timing_distribution={"scope": "not_timed", "lane": "mabd_development"},
        raw_outputs={"time_series": "compact_samples_only"},
        plot_paths={},
        source_commit=source_commit,
        vendored_newton_commit=vendored_newton_commit,
        paper_source_version=paper_source_version,
    )
    write_claim_report(report, path)
    return report


__all__ = [
    "write_physical_pendulum_analytic_reference_report",
    "write_physical_pendulum_mabd_development_report",
]
