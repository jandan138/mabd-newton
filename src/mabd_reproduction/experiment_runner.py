"""Config-driven experiment report runners for M-ABD reproduction."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .comparison_reports import (
    write_physical_pendulum_comparison_report,
    write_spinning_box_comparison_report,
)
from .experiment_configs import (
    load_physical_pendulum_config,
    load_spinning_box_config,
    validate_physical_pendulum_config_against_matrix,
    validate_spinning_box_config_against_matrix,
)
from .experiment_contracts import load_experiment_matrix
from .physical_pendulum_reports import (
    write_physical_pendulum_analytic_reference_report,
    write_physical_pendulum_mabd_development_report,
    write_physical_pendulum_rbd_baseline_report,
)
from .reporting import ClaimReport, EvidenceStatus
from .rigid_baselines import write_spinning_box_paper_rbd_baseline_report
from .single_body_reports import (
    write_spinning_box_development_report,
    write_spinning_box_paper_horizon_report,
)


@dataclass(frozen=True)
class ExperimentRunResult:
    claim_id: str
    scene_id: str
    status: EvidenceStatus
    report_path: Path
    report: ClaimReport

    def to_summary(self) -> dict[str, str]:
        return {
            "claim_id": self.claim_id,
            "scene_id": self.scene_id,
            "status": self.status.value,
            "output_report": self.report_path.as_posix(),
            "baseline_lane": self.report.baseline_lane,
        }


def _resolve_output_path(
    configured_output_report: str,
    *,
    output_path: str | Path | None,
    output_root: str | Path | None,
) -> Path:
    if output_path is not None and output_root is not None:
        raise ValueError("output_path and output_root are mutually exclusive")
    if output_path is not None:
        return Path(output_path)
    configured = Path(configured_output_report)
    if output_root is not None:
        if configured.is_absolute() or ".." in configured.parts:
            raise ValueError("output_report must stay within output_root")
        return Path(output_root) / configured
    return configured


def run_spinning_box_experiment(
    *,
    config_path: str | Path,
    matrix_path: str | Path,
    source_commit: str,
    vendored_newton_commit: str,
    output_path: str | Path | None = None,
    output_root: str | Path | None = None,
    paper_source_version: str = "2603.08079v2",
) -> ExperimentRunResult:
    config = load_spinning_box_config(config_path)
    matrix = load_experiment_matrix(matrix_path)
    validate_spinning_box_config_against_matrix(config, matrix)
    if config.report_status != EvidenceStatus.INCOMPLETE:
        raise ValueError("Phase 14 experiment runner requires incomplete report status")
    report_path = _resolve_output_path(
        config.output_report,
        output_path=output_path,
        output_root=output_root,
    )
    report = write_spinning_box_development_report(
        report_path,
        config=config,
        source_commit=source_commit,
        vendored_newton_commit=vendored_newton_commit,
        paper_source_version=paper_source_version,
    )
    return ExperimentRunResult(
        claim_id=report.claim_id,
        scene_id=report.scene_id,
        status=report.status,
        report_path=report_path,
        report=report,
    )


def run_spinning_box_rbd_baseline(
    *,
    config_path: str | Path,
    matrix_path: str | Path,
    source_commit: str,
    vendored_newton_commit: str,
    output_path: str | Path | None = None,
    output_root: str | Path | None = None,
    paper_source_version: str = "2603.08079v2",
) -> ExperimentRunResult:
    if output_path is None:
        raise ValueError("rbd_implicit_baseline requires --output")
    if output_root is not None:
        raise ValueError("rbd_implicit_baseline uses --output, not --output-root")

    config = load_spinning_box_config(config_path)
    matrix = load_experiment_matrix(matrix_path)
    validate_spinning_box_config_against_matrix(config, matrix)
    if config.report_status != EvidenceStatus.INCOMPLETE:
        raise ValueError("Phase 15 RBD baseline runner requires incomplete report status")

    report_path = Path(output_path)
    report = write_spinning_box_paper_rbd_baseline_report(
        report_path,
        config=config,
        source_commit=source_commit,
        vendored_newton_commit=vendored_newton_commit,
        paper_source_version=paper_source_version,
    )
    return ExperimentRunResult(
        claim_id=report.claim_id,
        scene_id=report.scene_id,
        status=report.status,
        report_path=report_path,
        report=report,
    )


def run_spinning_box_paper_horizon(
    *,
    config_path: str | Path,
    matrix_path: str | Path,
    source_commit: str,
    vendored_newton_commit: str,
    output_path: str | Path | None = None,
    output_root: str | Path | None = None,
    paper_source_version: str = "2603.08079v2",
) -> ExperimentRunResult:
    if output_path is None:
        raise ValueError("mabd_paper_horizon requires --output")
    if output_root is not None:
        raise ValueError("mabd_paper_horizon uses --output, not --output-root")

    config = load_spinning_box_config(config_path)
    matrix = load_experiment_matrix(matrix_path)
    validate_spinning_box_config_against_matrix(config, matrix)
    if config.report_status != EvidenceStatus.INCOMPLETE:
        raise ValueError("Phase 28 M-ABD paper-horizon runner requires incomplete report status")

    report_path = Path(output_path)
    report = write_spinning_box_paper_horizon_report(
        report_path,
        config=config,
        source_commit=source_commit,
        vendored_newton_commit=vendored_newton_commit,
        paper_source_version=paper_source_version,
    )
    return ExperimentRunResult(
        claim_id=report.claim_id,
        scene_id=report.scene_id,
        status=report.status,
        report_path=report_path,
        report=report,
    )


def run_spinning_box_comparison(
    *,
    config_path: str | Path,
    matrix_path: str | Path,
    source_commit: str,
    vendored_newton_commit: str,
    mabd_report_path: str | Path | None = None,
    rbd_report_path: str | Path | None = None,
    output_path: str | Path | None = None,
    output_root: str | Path | None = None,
    paper_source_version: str = "2603.08079v2",
) -> ExperimentRunResult:
    if output_path is None:
        raise ValueError("spinning_box_comparison requires --output")
    if output_root is not None:
        raise ValueError("spinning_box_comparison uses --output, not --output-root")
    if mabd_report_path is None or rbd_report_path is None:
        raise ValueError("spinning_box_comparison requires --mabd-report and --rbd-report")

    config = load_spinning_box_config(config_path)
    matrix = load_experiment_matrix(matrix_path)
    validate_spinning_box_config_against_matrix(config, matrix)

    report_path = Path(output_path)
    report = write_spinning_box_comparison_report(
        report_path,
        config=config,
        mabd_report_path=mabd_report_path,
        rbd_report_path=rbd_report_path,
        source_commit=source_commit,
        vendored_newton_commit=vendored_newton_commit,
        paper_source_version=paper_source_version,
    )
    return ExperimentRunResult(
        claim_id=report.claim_id,
        scene_id=report.scene_id,
        status=report.status,
        report_path=report_path,
        report=report,
    )


def run_physical_pendulum_analytic_reference(
    *,
    config_path: str | Path,
    matrix_path: str | Path,
    source_commit: str,
    vendored_newton_commit: str,
    output_path: str | Path | None = None,
    output_root: str | Path | None = None,
    paper_source_version: str = "2603.08079v2",
) -> ExperimentRunResult:
    config = load_physical_pendulum_config(config_path)
    matrix = load_experiment_matrix(matrix_path)
    validate_physical_pendulum_config_against_matrix(config, matrix)
    if config.report_status != EvidenceStatus.INCOMPLETE:
        raise ValueError("Phase 33 physical-pendulum analytic runner requires incomplete status")
    report_path = _resolve_output_path(
        config.output_report,
        output_path=output_path,
        output_root=output_root,
    )
    report = write_physical_pendulum_analytic_reference_report(
        report_path,
        config=config,
        source_commit=source_commit,
        vendored_newton_commit=vendored_newton_commit,
        paper_source_version=paper_source_version,
    )
    return ExperimentRunResult(
        claim_id=report.claim_id,
        scene_id=report.scene_id,
        status=report.status,
        report_path=report_path,
        report=report,
    )


def run_physical_pendulum_mabd_development(
    *,
    config_path: str | Path,
    matrix_path: str | Path,
    source_commit: str,
    vendored_newton_commit: str,
    output_path: str | Path | None = None,
    output_root: str | Path | None = None,
    paper_source_version: str = "2603.08079v2",
) -> ExperimentRunResult:
    config = load_physical_pendulum_config(config_path)
    matrix = load_experiment_matrix(matrix_path)
    validate_physical_pendulum_config_against_matrix(config, matrix)
    if config.report_status != EvidenceStatus.INCOMPLETE:
        raise ValueError("Phase 34 physical-pendulum M-ABD runner requires incomplete status")
    report_path = _resolve_output_path(
        config.mabd_development.output_report,
        output_path=output_path,
        output_root=output_root,
    )
    report = write_physical_pendulum_mabd_development_report(
        report_path,
        config=config,
        source_commit=source_commit,
        vendored_newton_commit=vendored_newton_commit,
        paper_source_version=paper_source_version,
    )
    return ExperimentRunResult(
        claim_id=report.claim_id,
        scene_id=report.scene_id,
        status=report.status,
        report_path=report_path,
        report=report,
    )


def run_physical_pendulum_rbd_baseline(
    *,
    config_path: str | Path,
    matrix_path: str | Path,
    source_commit: str,
    vendored_newton_commit: str,
    output_path: str | Path | None = None,
    output_root: str | Path | None = None,
    paper_source_version: str = "2603.08079v2",
) -> ExperimentRunResult:
    config = load_physical_pendulum_config(config_path)
    matrix = load_experiment_matrix(matrix_path)
    validate_physical_pendulum_config_against_matrix(config, matrix)
    if config.report_status != EvidenceStatus.INCOMPLETE:
        raise ValueError("Phase 35 physical-pendulum RBD runner requires incomplete status")
    report_path = _resolve_output_path(
        config.rbd_baseline.output_report,
        output_path=output_path,
        output_root=output_root,
    )
    report = write_physical_pendulum_rbd_baseline_report(
        report_path,
        config=config,
        source_commit=source_commit,
        vendored_newton_commit=vendored_newton_commit,
        paper_source_version=paper_source_version,
    )
    return ExperimentRunResult(
        claim_id=report.claim_id,
        scene_id=report.scene_id,
        status=report.status,
        report_path=report_path,
        report=report,
    )


def run_physical_pendulum_comparison(
    *,
    config_path: str | Path,
    matrix_path: str | Path,
    source_commit: str,
    vendored_newton_commit: str,
    analytic_report_path: str | Path | None = None,
    mabd_report_path: str | Path | None = None,
    rbd_report_path: str | Path | None = None,
    output_path: str | Path | None = None,
    output_root: str | Path | None = None,
    paper_source_version: str = "2603.08079v2",
) -> ExperimentRunResult:
    if analytic_report_path is None or mabd_report_path is None or rbd_report_path is None:
        raise ValueError(
            "physical_pendulum_comparison requires --analytic-report, --mabd-report, and --rbd-report"
        )

    config = load_physical_pendulum_config(config_path)
    matrix = load_experiment_matrix(matrix_path)
    validate_physical_pendulum_config_against_matrix(config, matrix)
    if config.report_status != EvidenceStatus.INCOMPLETE:
        raise ValueError("Phase 36 physical-pendulum comparison runner requires incomplete status")
    report_path = _resolve_output_path(
        config.comparison.output_report,
        output_path=output_path,
        output_root=output_root,
    )
    report = write_physical_pendulum_comparison_report(
        report_path,
        config=config,
        analytic_report_path=analytic_report_path,
        mabd_report_path=mabd_report_path,
        rbd_report_path=rbd_report_path,
        source_commit=source_commit,
        vendored_newton_commit=vendored_newton_commit,
        paper_source_version=paper_source_version,
    )
    return ExperimentRunResult(
        claim_id=report.claim_id,
        scene_id=report.scene_id,
        status=report.status,
        report_path=report_path,
        report=report,
    )


__all__ = [
    "ExperimentRunResult",
    "run_physical_pendulum_analytic_reference",
    "run_physical_pendulum_comparison",
    "run_physical_pendulum_mabd_development",
    "run_physical_pendulum_rbd_baseline",
    "run_spinning_box_comparison",
    "run_spinning_box_experiment",
    "run_spinning_box_paper_horizon",
    "run_spinning_box_rbd_baseline",
]
