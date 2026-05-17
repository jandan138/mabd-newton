"""Report writer for the physical-pendulum analytic reference lane."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from .experiment_configs import PhysicalPendulumRunConfig
from .physical_pendulum_reference import (
    physical_pendulum_angle_reference,
    physical_pendulum_complete_elliptic_k,
    physical_pendulum_period_s,
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


__all__ = [
    "write_physical_pendulum_analytic_reference_report",
]
