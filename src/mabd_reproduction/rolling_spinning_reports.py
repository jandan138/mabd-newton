"""Report lane for the rolling/spinning single-body experiment surface."""

from __future__ import annotations

from pathlib import Path

from .experiment_configs import RollingSpinningRunConfig
from .reporting import ClaimReport, write_claim_report


def write_rolling_spinning_protocol_report(
    path: str | Path,
    *,
    config: RollingSpinningRunConfig,
    source_commit: str,
    vendored_newton_commit: str,
    paper_source_version: str = "2603.08079v2",
) -> ClaimReport:
    expected = {
        "paper_claim_status": (
            "requires rolling cylinder runtime benchmark and RBD baselines before pass"
        ),
        "source_lines": list(config.source_lines),
        "benchmark_body": config.performance.body,
        "benchmark_step_count": config.performance.step_count,
        "time_step_s": config.performance.time_step_s,
        "paper_hardware_context": config.performance.paper_hardware_context,
        "paper_total_simulation_time_ms": dict(
            config.performance.paper_total_simulation_time_ms
        ),
        "required_metrics": list(config.thresholds),
        "full_experiment_claim_passed": False,
    }
    observed = {
        "local_runtime_measured": False,
        "protocol_status": config.performance.protocol_status,
        "required_lanes_missing": list(config.required_missing_lanes),
        "blocking_reasons": [
            "rbd_baseline_adapter_missing",
            "benchmark_protocol_not_recorded",
            "rolling_cylinder_runtime_not_measured",
        ],
        "paper_metric_statuses": {
            "total_simulation_time_ms": "paper_reference_recorded_no_local_runtime",
            "linear_momentum_error": "not_measured_by_phase73",
            "angular_momentum_error": "not_measured_by_phase73",
            "energy_drift": "not_measured_by_phase73",
        },
        "full_experiment_claim_passed": False,
    }
    report = ClaimReport(
        claim_id=config.claim_id,
        scene_id=config.scene_id,
        asset_hashes={
            "primitive_cylinder": "not_applicable_procedural",
            "primitive_cube": "not_applicable_procedural",
        },
        solver_mode="rolling_spinning_protocol_audit",
        backend="report_protocol",
        baseline_lane=config.baseline_lane,
        expected=expected,
        observed=observed,
        threshold=config.thresholds,
        unit="json_report",
        status=config.report_status,
        failure_reason=config.failure_reason,
        timing_distribution={
            "status": "not_measured",
            "paper_comparable": False,
        },
        raw_outputs={},
        plot_paths={},
        source_commit=source_commit,
        vendored_newton_commit=vendored_newton_commit,
        paper_source_version=paper_source_version,
    )
    write_claim_report(report, path)
    return report


__all__ = ["write_rolling_spinning_protocol_report"]
