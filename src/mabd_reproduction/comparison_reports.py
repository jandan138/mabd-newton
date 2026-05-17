"""Multi-lane comparison reports for paper experiment claims."""

from __future__ import annotations

import hashlib
from math import isfinite
from pathlib import Path
from typing import Any

from .experiment_configs import PhysicalPendulumRunConfig, SpinningBoxRunConfig
from .reporting import ClaimReport, EvidenceStatus, load_claim_report, write_claim_report


SPINNING_BOX_REQUIRED_METRICS = (
    "linear_momentum_error",
    "angular_momentum_error",
    "energy_drift",
)
SPINNING_BOX_REQUIRED_VECTOR_METRICS = (
    "initial_position_m",
    "final_position_m",
)
PHYSICAL_PENDULUM_REQUIRED_METRICS = (
    "pendulum_angle_error",
    "joint_force_error",
    "phase_drift",
)
PHYSICAL_PENDULUM_INPUT_LANES = {
    "analytic_reference": {
        "solver_mode": "analytic_elliptic_reference",
        "backend": "cpu_scipy_reference",
    },
    "physical_pendulum_mabd_development_diagnostic": {
        "solver_mode": "mabd_cpu_oracle_physical_pendulum_development",
        "backend": "cpu_numpy_newton_only",
    },
    "rbd_implicit_baseline": {
        "solver_mode": "physical_pendulum_scalar_implicit_rbd_development",
        "backend": "cpu_numpy_newton_only",
    },
}


def _require_lane_report(
    path: str | Path,
    *,
    config: SpinningBoxRunConfig,
    lane: str,
) -> ClaimReport:
    report = load_claim_report(path)
    if report.claim_id != config.claim_id:
        raise ValueError(f"{lane} report claim_id must be {config.claim_id}")
    if report.scene_id != config.scene_id:
        raise ValueError(f"{lane} report scene_id must be {config.scene_id}")
    if report.baseline_lane != lane:
        raise ValueError(f"{lane} report must have baseline_lane={lane}")
    return report


def _sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _require_physical_pendulum_lane_report(
    path: str | Path,
    *,
    config: PhysicalPendulumRunConfig,
    lane: str,
) -> ClaimReport:
    report = load_claim_report(path)
    if report.claim_id != config.claim_id:
        raise ValueError(f"{lane} report claim_id must be {config.claim_id}")
    if report.scene_id != config.scene_id:
        raise ValueError(f"{lane} report scene_id must be {config.scene_id}")
    if report.baseline_lane != lane:
        raise ValueError(f"{lane} report must have baseline_lane={lane}")
    expected_identity = PHYSICAL_PENDULUM_INPUT_LANES[lane]
    expected_solver_mode = expected_identity["solver_mode"]
    if report.solver_mode != expected_solver_mode:
        raise ValueError(f"{lane} report solver_mode must be {expected_solver_mode}")
    expected_backend = expected_identity["backend"]
    if report.backend != expected_backend:
        raise ValueError(f"{lane} report backend must be {expected_backend}")
    if report.status != EvidenceStatus.INCOMPLETE:
        raise ValueError(f"{lane} report status must be incomplete")
    if report.asset_hashes.get("physical_pendulum_procedural") != "not_applicable_procedural":
        raise ValueError(f"{lane} report must use physical_pendulum_procedural")
    if report.observed.get("full_experiment_claim_passed") is not False:
        raise ValueError(f"{lane} report must not claim full experiment pass")
    return report


def _finite_scalar(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    result = float(value)
    return result if isfinite(result) else None


def _finite_vector3(value: Any) -> list[float] | None:
    if not isinstance(value, list | tuple) or len(value) != 3:
        return None
    result: list[float] = []
    for component in value:
        scalar = _finite_scalar(component)
        if scalar is None:
            return None
        result.append(scalar)
    return result


def _finite_difference(lhs: float, rhs: float) -> float | None:
    difference = lhs - rhs
    return difference if isfinite(difference) else None


def _physical_lane_provenance(path: str | Path, report: ClaimReport) -> dict[str, str]:
    return {
        "path": Path(path).as_posix(),
        "sha256": _sha256_file(path),
        "source_commit": report.source_commit,
        "vendored_newton_commit": report.vendored_newton_commit,
        "solver_mode": report.solver_mode,
        "backend": report.backend,
        "baseline_lane": report.baseline_lane,
        "status": report.status.value,
    }


def _physical_pendulum_metric_snapshot(report: ClaimReport, metrics: tuple[str, ...]) -> dict[str, float | None]:
    return {
        metric: _finite_scalar(report.observed.get(metric))
        for metric in metrics
    }


def _physical_angle_rows(report: ClaimReport) -> list[dict[str, Any]]:
    rows = report.observed.get("angle_samples_rad")
    if not isinstance(rows, list):
        return []
    return [dict(row) for row in rows if isinstance(row, dict)]


def _physical_sample_key(row: dict[str, Any]) -> tuple[int, float] | None:
    step = _finite_scalar(row.get("step"))
    time_s = _finite_scalar(row.get("time_s"))
    if step is None or time_s is None:
        return None
    step_int = int(step)
    if float(step_int) != step:
        return None
    return (step_int, round(time_s, 12))


def _physical_sample_identity(row: dict[str, Any]) -> dict[str, float | int | None]:
    sample_index = _finite_scalar(row.get("sample_index"))
    step = _finite_scalar(row.get("step"))
    time_s = _finite_scalar(row.get("time_s"))
    return {
        "sample_index": int(sample_index) if sample_index is not None else None,
        "step": int(step) if step is not None and float(int(step)) == step else None,
        "time_s": time_s,
    }


def _physical_angle_sample_differences(
    mabd_report: ClaimReport,
    rbd_report: ClaimReport,
) -> dict[str, Any]:
    mabd_rows = _physical_angle_rows(mabd_report)
    rbd_rows = _physical_angle_rows(rbd_report)
    mabd_by_key = {
        key: row for row in mabd_rows if (key := _physical_sample_key(row)) is not None
    }
    rbd_by_key = {
        key: row for row in rbd_rows if (key := _physical_sample_key(row)) is not None
    }
    matched_keys = sorted(set(mabd_by_key) & set(rbd_by_key))
    unmatched_mabd = [
        _physical_sample_identity(row)
        for row in mabd_rows
        if (key := _physical_sample_key(row)) is None or key not in rbd_by_key
    ]
    unmatched_rbd = [
        _physical_sample_identity(row)
        for row in rbd_rows
        if (key := _physical_sample_key(row)) is None or key not in mabd_by_key
    ]
    differences: list[dict[str, float | int]] = []
    nonfinite = False
    for key in matched_keys:
        mabd_row = mabd_by_key[key]
        rbd_row = rbd_by_key[key]
        mabd_angle = _finite_scalar(mabd_row.get("angle_rad"))
        rbd_angle = _finite_scalar(rbd_row.get("angle_rad"))
        if mabd_angle is None or rbd_angle is None:
            nonfinite = True
            continue
        delta = _finite_difference(mabd_angle, rbd_angle)
        if delta is None:
            nonfinite = True
            continue
        sample_index = _finite_scalar(mabd_row.get("sample_index"))
        differences.append(
            {
                "sample_index": int(sample_index) if sample_index is not None else len(differences),
                "step": key[0],
                "time_s": key[1],
                "mabd_angle_rad": mabd_angle,
                "rbd_angle_rad": rbd_angle,
                "mabd_minus_rbd_angle_rad": delta,
                "abs_angle_delta_rad": abs(delta),
            }
        )
    max_delta = (
        max(row["abs_angle_delta_rad"] for row in differences)
        if differences
        else None
    )
    return {
        "mabd_sample_count": len(mabd_rows),
        "rbd_sample_count": len(rbd_rows),
        "matched_sample_count": len(matched_keys),
        "unmatched_mabd_samples": unmatched_mabd,
        "unmatched_rbd_samples": unmatched_rbd,
        "angle_sample_differences_rad": differences,
        "max_mabd_rbd_abs_angle_delta_rad": max_delta,
        "nonfinite": nonfinite,
    }


def _physical_pendulum_paper_metric_statuses() -> dict[str, dict[str, str | None]]:
    return {
        "pendulum_angle_error": {
            "status": "diagnostic_available",
            "mabd_field": "max_abs_angle_error_rad",
            "rbd_field": "max_abs_angle_error_rad",
        },
        "phase_drift": {
            "status": "rbd_diagnostic_only",
            "mabd_field": None,
            "rbd_field": "max_phase_drift_rad",
        },
        "joint_force_error": {
            "status": "missing_waveform_not_max_magnitude",
            "mabd_field": None,
            "rbd_diagnostic_field": "max_joint_force_magnitude_n",
        },
    }


def _lane_metric_snapshot(report: ClaimReport) -> dict[str, float | None]:
    return {
        metric: _finite_scalar(report.observed[metric]) if metric in report.observed else None
        for metric in SPINNING_BOX_REQUIRED_METRICS
    }


def _lane_vector_metric_snapshot(report: ClaimReport) -> dict[str, list[float] | None]:
    return {
        metric: _finite_vector3(report.observed[metric]) if metric in report.observed else None
        for metric in SPINNING_BOX_REQUIRED_VECTOR_METRICS
    }


def _lane_gate_status(report: ClaimReport) -> str:
    value = report.observed.get("lane_gate_status")
    return value if isinstance(value, str) and value else report.status.value


def _missing_metrics(lane: str, report: ClaimReport) -> list[str]:
    return [
        f"{lane}:{metric}" for metric in SPINNING_BOX_REQUIRED_METRICS if metric not in report.observed
    ]


def _missing_vector_metrics(lane: str, report: ClaimReport) -> list[str]:
    return [
        f"{lane}:{metric}"
        for metric in SPINNING_BOX_REQUIRED_VECTOR_METRICS
        if metric not in report.observed
    ]


def _invalid_metrics(lane: str, report: ClaimReport) -> list[str]:
    return [
        f"{lane}:{metric}"
        for metric in SPINNING_BOX_REQUIRED_METRICS
        if metric in report.observed and _finite_scalar(report.observed[metric]) is None
    ]


def _invalid_vector_metrics(lane: str, report: ClaimReport) -> list[str]:
    return [
        f"{lane}:{metric}"
        for metric in SPINNING_BOX_REQUIRED_VECTOR_METRICS
        if metric in report.observed and _finite_vector3(report.observed[metric]) is None
    ]


def _lane_metric_differences(
    mabd_report: ClaimReport,
    rbd_report: ClaimReport,
) -> dict[str, dict[str, float]]:
    differences: dict[str, float] = {}
    for metric in SPINNING_BOX_REQUIRED_METRICS:
        mabd_value = _finite_scalar(mabd_report.observed.get(metric))
        rbd_value = _finite_scalar(rbd_report.observed.get(metric))
        if mabd_value is not None and rbd_value is not None:
            difference = _finite_difference(mabd_value, rbd_value)
            if difference is not None:
                differences[metric] = difference
    return {"mabd_newton_minus_rbd_implicit_baseline": differences}


def _lane_vector_metric_differences(
    mabd_report: ClaimReport,
    rbd_report: ClaimReport,
) -> dict[str, dict[str, list[float]]]:
    differences: dict[str, list[float]] = {}
    for metric in SPINNING_BOX_REQUIRED_VECTOR_METRICS:
        mabd_value = _finite_vector3(mabd_report.observed.get(metric))
        rbd_value = _finite_vector3(rbd_report.observed.get(metric))
        if mabd_value is not None and rbd_value is not None:
            difference: list[float] = []
            for mabd_component, rbd_component in zip(mabd_value, rbd_value, strict=True):
                component_difference = _finite_difference(mabd_component, rbd_component)
                if component_difference is None:
                    break
                difference.append(component_difference)
            if len(difference) == 3:
                differences[metric] = difference
    return {"mabd_newton_minus_rbd_implicit_baseline": differences}


def write_spinning_box_comparison_report(
    path: str | Path,
    *,
    config: SpinningBoxRunConfig,
    mabd_report_path: str | Path,
    rbd_report_path: str | Path,
    source_commit: str,
    vendored_newton_commit: str,
    paper_source_version: str = "2603.08079v2",
) -> ClaimReport:
    mabd_report = _require_lane_report(mabd_report_path, config=config, lane="mabd_newton")
    rbd_report = _require_lane_report(rbd_report_path, config=config, lane="rbd_implicit_baseline")
    lane_statuses = {
        "mabd_newton": mabd_report.status.value,
        "rbd_implicit_baseline": rbd_report.status.value,
    }
    lane_gate_statuses = {
        "mabd_newton": _lane_gate_status(mabd_report),
        "rbd_implicit_baseline": _lane_gate_status(rbd_report),
    }
    missing_required_metrics = _missing_metrics("mabd_newton", mabd_report) + _missing_metrics(
        "rbd_implicit_baseline",
        rbd_report,
    )
    invalid_required_metrics = _invalid_metrics("mabd_newton", mabd_report) + _invalid_metrics(
        "rbd_implicit_baseline",
        rbd_report,
    )
    missing_required_vector_metrics = _missing_vector_metrics(
        "mabd_newton",
        mabd_report,
    ) + _missing_vector_metrics("rbd_implicit_baseline", rbd_report)
    invalid_required_vector_metrics = _invalid_vector_metrics(
        "mabd_newton",
        mabd_report,
    ) + _invalid_vector_metrics("rbd_implicit_baseline", rbd_report)
    metric_differences = _lane_metric_differences(mabd_report, rbd_report)
    vector_metric_differences = _lane_vector_metric_differences(mabd_report, rbd_report)
    incomplete_lanes = [
        lane
        for lane, status in lane_gate_statuses.items()
        if status != EvidenceStatus.PASSED.value
    ]
    blocking_reasons = [
        *(f"{lane}_report_{lane_statuses[lane]}" for lane in incomplete_lanes),
        *(f"{metric}_missing" for metric in missing_required_metrics),
        *(f"{metric}_invalid" for metric in invalid_required_metrics),
        *(f"{metric}_missing" for metric in missing_required_vector_metrics),
        *(f"{metric}_invalid" for metric in invalid_required_vector_metrics),
    ]
    if rbd_report.solver_mode != "paper_faithful_implicit_rbd":
        blocking_reasons.append("rbd_implicit_baseline_not_paper_faithful")
    blocking_reasons.append("spinning_box_comparison_pass_gate_not_enabled")

    report = ClaimReport(
        claim_id=config.claim_id,
        scene_id=config.scene_id,
        asset_hashes={"primitive_cube": "not_applicable_procedural"},
        solver_mode="spinning_box_multilane_comparison_development",
        backend="report_protocol",
        baseline_lane="spinning_box_comparison_protocol",
        expected={
            "paper_claim_status": "requires passed M-ABD and paper-faithful implicit RBD lane gates",
            "required_lanes": ["mabd_newton", "rbd_implicit_baseline"],
            "required_metrics": list(SPINNING_BOX_REQUIRED_METRICS),
            "required_vector_metrics": list(SPINNING_BOX_REQUIRED_VECTOR_METRICS),
            "source_lines": list(config.source_lines),
        },
        observed={
            "lane_statuses": lane_statuses,
            "lane_gate_statuses": lane_gate_statuses,
            "lane_solver_modes": {
                "mabd_newton": mabd_report.solver_mode,
                "rbd_implicit_baseline": rbd_report.solver_mode,
            },
            "lane_metrics": {
                "mabd_newton": _lane_metric_snapshot(mabd_report),
                "rbd_implicit_baseline": _lane_metric_snapshot(rbd_report),
            },
            "lane_vector_metrics": {
                "mabd_newton": _lane_vector_metric_snapshot(mabd_report),
                "rbd_implicit_baseline": _lane_vector_metric_snapshot(rbd_report),
            },
            "missing_required_metrics": missing_required_metrics,
            "invalid_required_metrics": invalid_required_metrics,
            "missing_required_vector_metrics": missing_required_vector_metrics,
            "invalid_required_vector_metrics": invalid_required_vector_metrics,
            "lane_metric_differences": metric_differences,
            "lane_vector_metric_differences": vector_metric_differences,
            "blocking_reasons": blocking_reasons,
        },
        threshold={
            "required_lane_status": EvidenceStatus.PASSED.value,
            "required_lane_gate_status": EvidenceStatus.PASSED.value,
            "required_metrics": list(SPINNING_BOX_REQUIRED_METRICS),
            "required_vector_metrics": list(SPINNING_BOX_REQUIRED_VECTOR_METRICS),
            "paper_faithful_rbd_solver_mode": "paper_faithful_implicit_rbd",
        },
        unit="json_report",
        status=EvidenceStatus.INCOMPLETE,
        failure_reason="required lane gate statuses or comparison pass gate remain incomplete",
        timing_distribution={"scope": "not_timed"},
        raw_outputs={
            "mabd_report": Path(mabd_report_path).as_posix(),
            "rbd_report": Path(rbd_report_path).as_posix(),
        },
        plot_paths={},
        source_commit=source_commit,
        vendored_newton_commit=vendored_newton_commit,
        paper_source_version=paper_source_version,
    )
    write_claim_report(report, path)
    return report


def write_physical_pendulum_comparison_report(
    path: str | Path,
    *,
    config: PhysicalPendulumRunConfig,
    analytic_report_path: str | Path,
    mabd_report_path: str | Path,
    rbd_report_path: str | Path,
    source_commit: str,
    vendored_newton_commit: str,
    paper_source_version: str = "2603.08079v2",
) -> ClaimReport:
    analytic_report = _require_physical_pendulum_lane_report(
        analytic_report_path,
        config=config,
        lane="analytic_reference",
    )
    mabd_report = _require_physical_pendulum_lane_report(
        mabd_report_path,
        config=config,
        lane="physical_pendulum_mabd_development_diagnostic",
    )
    rbd_report = _require_physical_pendulum_lane_report(
        rbd_report_path,
        config=config,
        lane="rbd_implicit_baseline",
    )
    sample_diagnostics = _physical_angle_sample_differences(mabd_report, rbd_report)
    blocking_reasons = [
        "mabd_newton_missing",
        "joint_force_waveform_agreement_missing",
        "pendulum_geometry_unknown",
        "paper_timing_missing",
        "physical_pendulum_comparison_pass_gate_not_enabled",
    ]
    if sample_diagnostics["matched_sample_count"] == 0:
        blocking_reasons.append("angle_sample_alignment_missing")
    if sample_diagnostics["nonfinite"]:
        blocking_reasons.append("angle_sample_nonfinite")

    observed = {
        "full_experiment_claim_passed": False,
        "lane_statuses": {
            "analytic_reference": analytic_report.status.value,
            "physical_pendulum_mabd_development_diagnostic": mabd_report.status.value,
            "rbd_implicit_baseline": rbd_report.status.value,
        },
        "lane_observed_statuses": {
            "analytic_reference": analytic_report.observed.get("lane_status"),
            "physical_pendulum_mabd_development_diagnostic": mabd_report.observed.get(
                "lane_status"
            ),
            "rbd_implicit_baseline": rbd_report.observed.get("lane_status"),
        },
        "lane_solver_modes": {
            "analytic_reference": analytic_report.solver_mode,
            "physical_pendulum_mabd_development_diagnostic": mabd_report.solver_mode,
            "rbd_implicit_baseline": rbd_report.solver_mode,
        },
        "input_report_provenance": {
            "analytic_reference": _physical_lane_provenance(
                analytic_report_path,
                analytic_report,
            ),
            "physical_pendulum_mabd_development_diagnostic": _physical_lane_provenance(
                mabd_report_path,
                mabd_report,
            ),
            "rbd_implicit_baseline": _physical_lane_provenance(
                rbd_report_path,
                rbd_report,
            ),
        },
        "lane_metrics": {
            "analytic_reference": _physical_pendulum_metric_snapshot(
                analytic_report,
                ("max_abs_reference_identity_error",),
            ),
            "physical_pendulum_mabd_development_diagnostic": _physical_pendulum_metric_snapshot(
                mabd_report,
                (
                    "max_abs_angle_error_rad",
                    "max_pivot_residual_m",
                    "max_constraint_residual_norm",
                ),
            ),
            "rbd_implicit_baseline": _physical_pendulum_metric_snapshot(
                rbd_report,
                (
                    "max_abs_angle_error_rad",
                    "max_phase_drift_rad",
                    "max_implicit_residual",
                    "max_length_constraint_error_m",
                    "max_joint_force_magnitude_n",
                ),
            ),
        },
        "paper_metric_statuses": _physical_pendulum_paper_metric_statuses(),
        "missing_required_lanes": list(config.required_missing_lanes),
        "missing_paper_metrics": [
            "mabd_newton:pendulum_angle_error",
            "mabd_newton:joint_force_error",
            "mabd_newton:phase_drift",
            "physical_pendulum_mabd_development_diagnostic:joint_force_error",
            "physical_pendulum_mabd_development_diagnostic:phase_drift",
            "rbd_implicit_baseline:joint_force_error",
        ],
        "blocking_reasons": blocking_reasons,
        "mabd_sample_count": sample_diagnostics["mabd_sample_count"],
        "rbd_sample_count": sample_diagnostics["rbd_sample_count"],
        "matched_sample_count": sample_diagnostics["matched_sample_count"],
        "unmatched_mabd_samples": sample_diagnostics["unmatched_mabd_samples"],
        "unmatched_rbd_samples": sample_diagnostics["unmatched_rbd_samples"],
        "angle_sample_differences_rad": sample_diagnostics["angle_sample_differences_rad"],
        "max_mabd_rbd_abs_angle_delta_rad": sample_diagnostics[
            "max_mabd_rbd_abs_angle_delta_rad"
        ],
    }

    report = ClaimReport(
        claim_id=config.claim_id,
        scene_id=config.scene_id,
        asset_hashes={"physical_pendulum_procedural": "not_applicable_procedural"},
        solver_mode="physical_pendulum_multilane_comparison_development",
        backend="report_protocol",
        baseline_lane="physical_pendulum_comparison_protocol",
        expected={
            "paper_claim_status": (
                "requires paper-faithful M-ABD lane, implicit RBD baseline, "
                "joint-force waveform comparison, geometry, and timing evidence"
            ),
            "required_lanes": list(config.comparison.required_lanes),
            "diagnostic_lanes": list(config.comparison.diagnostic_lanes),
            "required_metrics": list(PHYSICAL_PENDULUM_REQUIRED_METRICS),
            "source_lines": list(config.source_lines),
            "full_experiment_claim_passed": False,
        },
        observed=observed,
        threshold=config.comparison.thresholds,
        unit="json_report",
        status=EvidenceStatus.INCOMPLETE,
        failure_reason=(
            "physical-pendulum comparison protocol is incomplete because mabd_newton, "
            "joint-force waveform agreement, paper geometry, and paper timing remain missing"
        ),
        timing_distribution={"scope": "not_timed"},
        raw_outputs={
            "analytic_report": Path(analytic_report_path).as_posix(),
            "mabd_report": Path(mabd_report_path).as_posix(),
            "rbd_report": Path(rbd_report_path).as_posix(),
        },
        plot_paths={},
        source_commit=source_commit,
        vendored_newton_commit=vendored_newton_commit,
        paper_source_version=paper_source_version,
    )
    write_claim_report(report, path)
    return report


__all__ = [
    "PHYSICAL_PENDULUM_REQUIRED_METRICS",
    "SPINNING_BOX_REQUIRED_METRICS",
    "SPINNING_BOX_REQUIRED_VECTOR_METRICS",
    "write_physical_pendulum_comparison_report",
    "write_spinning_box_comparison_report",
]
