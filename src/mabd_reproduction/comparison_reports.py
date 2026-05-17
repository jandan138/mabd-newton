"""Multi-lane comparison reports for paper experiment claims."""

from __future__ import annotations

from math import isfinite
from pathlib import Path
from typing import Any

from .experiment_configs import SpinningBoxRunConfig
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
            differences[metric] = mabd_value - rbd_value
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
            differences[metric] = [
                mabd_component - rbd_component
                for mabd_component, rbd_component in zip(mabd_value, rbd_value, strict=True)
            ]
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
        lane for lane, status in lane_statuses.items() if status != EvidenceStatus.PASSED.value
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
    if not blocking_reasons:
        blocking_reasons.append("experiment_pass_gate_not_enabled")

    report = ClaimReport(
        claim_id=config.claim_id,
        scene_id=config.scene_id,
        asset_hashes={"primitive_cube": "not_applicable_procedural"},
        solver_mode="spinning_box_multilane_comparison_development",
        backend="report_protocol",
        baseline_lane="spinning_box_comparison_protocol",
        expected={
            "paper_claim_status": "requires passed M-ABD and paper-faithful implicit RBD lanes",
            "required_lanes": ["mabd_newton", "rbd_implicit_baseline"],
            "required_metrics": list(SPINNING_BOX_REQUIRED_METRICS),
            "required_vector_metrics": list(SPINNING_BOX_REQUIRED_VECTOR_METRICS),
            "source_lines": list(config.source_lines),
        },
        observed={
            "lane_statuses": lane_statuses,
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
            "required_metrics": list(SPINNING_BOX_REQUIRED_METRICS),
            "required_vector_metrics": list(SPINNING_BOX_REQUIRED_VECTOR_METRICS),
            "paper_faithful_rbd_solver_mode": "paper_faithful_implicit_rbd",
        },
        unit="json_report",
        status=EvidenceStatus.INCOMPLETE,
        failure_reason="required lane reports remain incomplete or missing paper comparison metrics",
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


__all__ = [
    "SPINNING_BOX_REQUIRED_METRICS",
    "SPINNING_BOX_REQUIRED_VECTOR_METRICS",
    "write_spinning_box_comparison_report",
]
