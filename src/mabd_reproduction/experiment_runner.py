"""Config-driven experiment report runners for M-ABD reproduction."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .experiment_configs import (
    load_spinning_box_config,
    validate_spinning_box_config_against_matrix,
)
from .experiment_contracts import load_experiment_matrix
from .reporting import ClaimReport, EvidenceStatus
from .single_body_reports import write_spinning_box_development_report


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


__all__ = ["ExperimentRunResult", "run_spinning_box_experiment"]
