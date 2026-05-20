"""Config-driven experiment report runners for M-ABD reproduction."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .comparison_reports import (
    write_heavy_top_comparison_report,
    write_physical_pendulum_comparison_report,
    write_spinning_box_comparison_report,
    write_t_handle_comparison_report,
)
from .experiment_configs import (
    load_heavy_top_config,
    load_physical_pendulum_config,
    load_rolling_spinning_config,
    load_spinning_box_config,
    load_t_handle_config,
    validate_heavy_top_config_against_matrix,
    validate_physical_pendulum_config_against_matrix,
    validate_rolling_spinning_config_against_matrix,
    validate_spinning_box_config_against_matrix,
    validate_t_handle_config_against_matrix,
)
from .experiment_contracts import load_experiment_matrix
from .heavy_top_digitization import write_heavy_top_figure_curve_report
from .heavy_top_reports import (
    write_heavy_top_mabd_newton_report,
    write_heavy_top_mabd_paper_horizon_report,
    write_heavy_top_rk4_reference_report,
)
from .physical_pendulum_reports import (
    write_physical_pendulum_analytic_reference_report,
    write_physical_pendulum_mabd_development_report,
    write_physical_pendulum_mabd_newton_report,
    write_physical_pendulum_rbd_baseline_report,
)
from .reporting import ClaimReport, EvidenceStatus
from .rigid_baselines import write_spinning_box_paper_rbd_baseline_report
from .rolling_spinning_reports import (
    write_rolling_spinning_mabd_material_preflight_report,
    write_rolling_spinning_mabd_newton_report,
    write_rolling_spinning_paper_timing_protocol_report,
    write_rolling_spinning_protocol_report,
    write_rolling_spinning_rbd_explicit_baseline_report,
    write_rolling_spinning_rbd_implicit_baseline_report,
)
from .single_body_reports import (
    write_spinning_box_affine_static_plane_contacts_report,
    write_spinning_box_contacts_input_report,
    write_spinning_box_contact_response_report,
    write_spinning_box_decoupled_twist_report,
    write_spinning_box_development_report,
    write_spinning_box_model_plane_constraint_report,
    write_spinning_box_normal_constraint_report,
    write_spinning_box_paper_horizon_report,
)
from .spinning_box_digitization import write_spinning_box_figure_curve_report
from .t_handle_reports import (
    write_t_handle_mabd_newton_report,
    write_t_handle_rk4_reference_report,
)
from .t_handle_digitization import write_t_handle_figure_curve_report


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


def run_rolling_spinning_protocol(
    *,
    config_path: str | Path,
    matrix_path: str | Path,
    source_commit: str,
    vendored_newton_commit: str,
    output_path: str | Path | None = None,
    output_root: str | Path | None = None,
    paper_source_version: str = "2603.08079v2",
) -> ExperimentRunResult:
    config = load_rolling_spinning_config(config_path)
    matrix = load_experiment_matrix(matrix_path)
    validate_rolling_spinning_config_against_matrix(config, matrix)
    if config.report_status != EvidenceStatus.INCOMPLETE:
        raise ValueError(
            "Phase 73 rolling/spinning protocol runner requires incomplete report status"
        )
    report_path = _resolve_output_path(
        config.output_report,
        output_path=output_path,
        output_root=output_root,
    )
    report = write_rolling_spinning_protocol_report(
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


def run_rolling_spinning_rbd_implicit_baseline(
    *,
    config_path: str | Path,
    matrix_path: str | Path,
    source_commit: str,
    vendored_newton_commit: str,
    output_path: str | Path | None = None,
    output_root: str | Path | None = None,
    paper_source_version: str = "2603.08079v2",
) -> ExperimentRunResult:
    config = load_rolling_spinning_config(config_path)
    matrix = load_experiment_matrix(matrix_path)
    validate_rolling_spinning_config_against_matrix(config, matrix)
    if config.report_status != EvidenceStatus.INCOMPLETE:
        raise ValueError(
            "Phase 74 rolling/spinning RBD runner requires incomplete report status"
        )
    report_path = _resolve_output_path(
        config.rbd_implicit_baseline.output_report,
        output_path=output_path,
        output_root=output_root,
    )
    report = write_rolling_spinning_rbd_implicit_baseline_report(
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


def run_rolling_spinning_rbd_explicit_baseline(
    *,
    config_path: str | Path,
    matrix_path: str | Path,
    source_commit: str,
    vendored_newton_commit: str,
    output_path: str | Path | None = None,
    output_root: str | Path | None = None,
    paper_source_version: str = "2603.08079v2",
) -> ExperimentRunResult:
    config = load_rolling_spinning_config(config_path)
    matrix = load_experiment_matrix(matrix_path)
    validate_rolling_spinning_config_against_matrix(config, matrix)
    if config.report_status != EvidenceStatus.INCOMPLETE:
        raise ValueError(
            "Phase 75 rolling/spinning explicit RBD runner requires incomplete report status"
        )
    report_path = _resolve_output_path(
        config.rbd_explicit_baseline.output_report,
        output_path=output_path,
        output_root=output_root,
    )
    report = write_rolling_spinning_rbd_explicit_baseline_report(
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


def run_rolling_spinning_mabd_newton(
    *,
    config_path: str | Path,
    matrix_path: str | Path,
    source_commit: str,
    vendored_newton_commit: str,
    output_path: str | Path | None = None,
    output_root: str | Path | None = None,
    paper_source_version: str = "2603.08079v2",
) -> ExperimentRunResult:
    config = load_rolling_spinning_config(config_path)
    matrix = load_experiment_matrix(matrix_path)
    validate_rolling_spinning_config_against_matrix(config, matrix)
    if config.report_status != EvidenceStatus.INCOMPLETE:
        raise ValueError(
            "Phase 76 rolling/spinning M-ABD runner requires incomplete report status"
        )
    report_path = _resolve_output_path(
        config.mabd_newton.output_report,
        output_path=output_path,
        output_root=output_root,
    )
    report = write_rolling_spinning_mabd_newton_report(
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


def run_rolling_spinning_mabd_material_preflight(
    *,
    config_path: str | Path,
    matrix_path: str | Path,
    source_commit: str,
    vendored_newton_commit: str,
    output_path: str | Path | None = None,
    output_root: str | Path | None = None,
    paper_source_version: str = "2603.08079v2",
) -> ExperimentRunResult:
    config = load_rolling_spinning_config(config_path)
    matrix = load_experiment_matrix(matrix_path)
    validate_rolling_spinning_config_against_matrix(config, matrix)
    if config.report_status != EvidenceStatus.INCOMPLETE:
        raise ValueError(
            "Phase 77 rolling/spinning M-ABD material preflight requires incomplete report status"
        )
    report_path = _resolve_output_path(
        config.mabd_material_preflight.output_report,
        output_path=output_path,
        output_root=output_root,
    )
    report = write_rolling_spinning_mabd_material_preflight_report(
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


def run_rolling_spinning_paper_timing_protocol(
    *,
    config_path: str | Path,
    matrix_path: str | Path,
    source_commit: str,
    vendored_newton_commit: str,
    output_path: str | Path | None = None,
    output_root: str | Path | None = None,
    paper_source_version: str = "2603.08079v2",
) -> ExperimentRunResult:
    config = load_rolling_spinning_config(config_path)
    matrix = load_experiment_matrix(matrix_path)
    validate_rolling_spinning_config_against_matrix(config, matrix)
    if config.report_status != EvidenceStatus.INCOMPLETE:
        raise ValueError(
            "Phase 78 rolling/spinning timing protocol requires incomplete report status"
        )
    report_path = _resolve_output_path(
        config.paper_timing_protocol.output_report,
        output_path=output_path,
        output_root=output_root,
    )
    report = write_rolling_spinning_paper_timing_protocol_report(
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


def run_spinning_box_contact_response(
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
        raise ValueError("spinning_box_contact_response requires --output")
    if output_root is not None:
        raise ValueError("spinning_box_contact_response uses --output, not --output-root")

    config = load_spinning_box_config(config_path)
    matrix = load_experiment_matrix(matrix_path)
    validate_spinning_box_config_against_matrix(config, matrix)
    if config.report_status != EvidenceStatus.INCOMPLETE:
        raise ValueError("Phase 62 contact-response runner requires incomplete report status")

    report_path = Path(output_path)
    report = write_spinning_box_contact_response_report(
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
    figure_curve_report_path: str | Path | None = None,
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
        figure_curve_report_path=figure_curve_report_path,
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


def run_spinning_box_normal_constraint(
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
        raise ValueError("spinning_box_normal_constraint requires --output")
    if output_root is not None:
        raise ValueError("spinning_box_normal_constraint uses --output, not --output-root")

    config = load_spinning_box_config(config_path)
    matrix = load_experiment_matrix(matrix_path)
    validate_spinning_box_config_against_matrix(config, matrix)
    if config.report_status != EvidenceStatus.INCOMPLETE:
        raise ValueError("Phase 63 normal-constraint runner requires incomplete report status")

    report_path = Path(output_path)
    report = write_spinning_box_normal_constraint_report(
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


def run_spinning_box_model_plane_constraint(
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
        raise ValueError("spinning_box_model_plane_constraint requires --output")
    if output_root is not None:
        raise ValueError("spinning_box_model_plane_constraint uses --output, not --output-root")

    config = load_spinning_box_config(config_path)
    matrix = load_experiment_matrix(matrix_path)
    validate_spinning_box_config_against_matrix(config, matrix)
    if config.report_status != EvidenceStatus.INCOMPLETE:
        raise ValueError("Phase 68 model-plane runner requires incomplete report status")

    report_path = Path(output_path)
    report = write_spinning_box_model_plane_constraint_report(
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


def run_spinning_box_contacts_input(
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
        raise ValueError("spinning_box_contacts_input requires --output")
    if output_root is not None:
        raise ValueError("spinning_box_contacts_input uses --output, not --output-root")

    config = load_spinning_box_config(config_path)
    matrix = load_experiment_matrix(matrix_path)
    validate_spinning_box_config_against_matrix(config, matrix)
    if config.report_status != EvidenceStatus.INCOMPLETE:
        raise ValueError("Phase 70 contacts-input runner requires incomplete report status")

    report_path = Path(output_path)
    report = write_spinning_box_contacts_input_report(
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


def run_spinning_box_affine_static_plane_contacts(
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
        raise ValueError("spinning_box_affine_static_plane_contacts requires --output")
    if output_root is not None:
        raise ValueError("spinning_box_affine_static_plane_contacts uses --output, not --output-root")

    config = load_spinning_box_config(config_path)
    matrix = load_experiment_matrix(matrix_path)
    validate_spinning_box_config_against_matrix(config, matrix)
    if config.report_status != EvidenceStatus.INCOMPLETE:
        raise ValueError("Phase 71 affine static-plane contacts runner requires incomplete report status")

    report_path = Path(output_path)
    report = write_spinning_box_affine_static_plane_contacts_report(
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


def run_spinning_box_decoupled_twist(
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
        raise ValueError("spinning_box_decoupled_twist requires --output")
    if output_root is not None:
        raise ValueError("spinning_box_decoupled_twist uses --output, not --output-root")

    config = load_spinning_box_config(config_path)
    matrix = load_experiment_matrix(matrix_path)
    validate_spinning_box_config_against_matrix(config, matrix)
    if config.report_status != EvidenceStatus.INCOMPLETE:
        raise ValueError("Phase 64 decoupled-twist runner requires incomplete report status")

    report_path = Path(output_path)
    report = write_spinning_box_decoupled_twist_report(
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


def run_spinning_box_figure_curves(
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
        raise ValueError("spinning_box_figure_curves requires --output")
    if output_root is not None:
        raise ValueError("spinning_box_figure_curves uses --output, not --output-root")

    config = load_spinning_box_config(config_path)
    matrix = load_experiment_matrix(matrix_path)
    validate_spinning_box_config_against_matrix(config, matrix)
    if config.report_status != EvidenceStatus.INCOMPLETE:
        raise ValueError("Phase 65 figure-curve runner requires incomplete report status")

    report_path = Path(output_path)
    report = write_spinning_box_figure_curve_report(
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


def run_physical_pendulum_mabd_newton(
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
        raise ValueError("Phase 37 physical-pendulum M-ABD Newton runner requires incomplete status")
    report_path = _resolve_output_path(
        config.mabd_newton.output_report,
        output_path=output_path,
        output_root=output_root,
    )
    report = write_physical_pendulum_mabd_newton_report(
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


def run_t_handle_rk4_reference(
    *,
    config_path: str | Path,
    matrix_path: str | Path,
    source_commit: str,
    vendored_newton_commit: str,
    output_path: str | Path | None = None,
    output_root: str | Path | None = None,
    paper_source_version: str = "2603.08079v2",
) -> ExperimentRunResult:
    config = load_t_handle_config(config_path)
    matrix = load_experiment_matrix(matrix_path)
    validate_t_handle_config_against_matrix(config, matrix)
    if config.report_status != EvidenceStatus.INCOMPLETE:
        raise ValueError("Phase 43 T-handle RK4 reference runner requires incomplete status")
    report_path = _resolve_output_path(
        config.reference.output_report,
        output_path=output_path,
        output_root=output_root,
    )
    report = write_t_handle_rk4_reference_report(
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


def run_t_handle_mabd_newton(
    *,
    config_path: str | Path,
    matrix_path: str | Path,
    source_commit: str,
    vendored_newton_commit: str,
    output_path: str | Path | None = None,
    output_root: str | Path | None = None,
    paper_source_version: str = "2603.08079v2",
) -> ExperimentRunResult:
    config = load_t_handle_config(config_path)
    matrix = load_experiment_matrix(matrix_path)
    validate_t_handle_config_against_matrix(config, matrix)
    if config.report_status != EvidenceStatus.INCOMPLETE:
        raise ValueError("Phase 56 T-handle MABD runner requires incomplete status")
    report_path = _resolve_output_path(
        config.mabd_newton.output_report,
        output_path=output_path,
        output_root=output_root,
    )
    report = write_t_handle_mabd_newton_report(
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


def run_t_handle_comparison(
    *,
    config_path: str | Path,
    matrix_path: str | Path,
    source_commit: str,
    vendored_newton_commit: str,
    rk4_report_path: str | Path | None = None,
    mabd_report_path: str | Path | None = None,
    figure_curve_report_path: str | Path | None = None,
    output_path: str | Path | None = None,
    output_root: str | Path | None = None,
    paper_source_version: str = "2603.08079v2",
) -> ExperimentRunResult:
    if rk4_report_path is None or mabd_report_path is None:
        raise ValueError("t_handle_comparison requires --mabd-report and --rbd-report")

    config = load_t_handle_config(config_path)
    matrix = load_experiment_matrix(matrix_path)
    validate_t_handle_config_against_matrix(config, matrix)
    if config.report_status != EvidenceStatus.INCOMPLETE:
        raise ValueError("Phase 57 T-handle comparison runner requires incomplete status")
    report_path = _resolve_output_path(
        config.comparison.output_report,
        output_path=output_path,
        output_root=output_root,
    )
    report = write_t_handle_comparison_report(
        report_path,
        config=config,
        rk4_report_path=rk4_report_path,
        mabd_report_path=mabd_report_path,
        figure_curve_report_path=figure_curve_report_path,
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


def run_t_handle_figure_curves(
    *,
    config_path: str | Path,
    matrix_path: str | Path,
    source_commit: str,
    vendored_newton_commit: str,
    output_path: str | Path | None = None,
    output_root: str | Path | None = None,
    paper_source_version: str = "2603.08079v2",
) -> ExperimentRunResult:
    config = load_t_handle_config(config_path)
    matrix = load_experiment_matrix(matrix_path)
    validate_t_handle_config_against_matrix(config, matrix)
    if config.report_status != EvidenceStatus.INCOMPLETE:
        raise ValueError("Phase 58 T-handle figure-curve runner requires incomplete status")
    report_path = _resolve_output_path(
        config.figure_curves.output_report,
        output_path=output_path,
        output_root=output_root,
    )
    report = write_t_handle_figure_curve_report(
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


def run_heavy_top_rk4_reference(
    *,
    config_path: str | Path,
    matrix_path: str | Path,
    source_commit: str,
    vendored_newton_commit: str,
    output_path: str | Path | None = None,
    output_root: str | Path | None = None,
    paper_source_version: str = "2603.08079v2",
) -> ExperimentRunResult:
    config = load_heavy_top_config(config_path)
    matrix = load_experiment_matrix(matrix_path)
    validate_heavy_top_config_against_matrix(config, matrix)
    if config.report_status != EvidenceStatus.INCOMPLETE:
        raise ValueError("Phase 49 heavy-top RK4 reference runner requires incomplete status")
    report_path = _resolve_output_path(
        config.reference.output_report,
        output_path=output_path,
        output_root=output_root,
    )
    report = write_heavy_top_rk4_reference_report(
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


def run_heavy_top_mabd_newton(
    *,
    config_path: str | Path,
    matrix_path: str | Path,
    source_commit: str,
    vendored_newton_commit: str,
    output_path: str | Path | None = None,
    output_root: str | Path | None = None,
    paper_source_version: str = "2603.08079v2",
) -> ExperimentRunResult:
    config = load_heavy_top_config(config_path)
    matrix = load_experiment_matrix(matrix_path)
    validate_heavy_top_config_against_matrix(config, matrix)
    if config.report_status != EvidenceStatus.INCOMPLETE:
        raise ValueError("Phase 50 heavy-top M-ABD Newton runner requires incomplete status")
    report_path = _resolve_output_path(
        config.mabd_newton.output_report,
        output_path=output_path,
        output_root=output_root,
    )
    report = write_heavy_top_mabd_newton_report(
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


def run_heavy_top_mabd_paper_horizon(
    *,
    config_path: str | Path,
    matrix_path: str | Path,
    source_commit: str,
    vendored_newton_commit: str,
    output_path: str | Path | None = None,
    output_root: str | Path | None = None,
    paper_source_version: str = "2603.08079v2",
) -> ExperimentRunResult:
    config = load_heavy_top_config(config_path)
    matrix = load_experiment_matrix(matrix_path)
    validate_heavy_top_config_against_matrix(config, matrix)
    if config.report_status != EvidenceStatus.INCOMPLETE:
        raise ValueError("Phase 55 heavy-top M-ABD paper-horizon runner requires incomplete status")
    report_path = _resolve_output_path(
        config.mabd_paper_horizon.output_report,
        output_path=output_path,
        output_root=output_root,
    )
    report = write_heavy_top_mabd_paper_horizon_report(
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


def run_heavy_top_figure_curves(
    *,
    config_path: str | Path,
    matrix_path: str | Path,
    source_commit: str,
    vendored_newton_commit: str,
    output_path: str | Path | None = None,
    output_root: str | Path | None = None,
    paper_source_version: str = "2603.08079v2",
) -> ExperimentRunResult:
    config = load_heavy_top_config(config_path)
    matrix = load_experiment_matrix(matrix_path)
    validate_heavy_top_config_against_matrix(config, matrix)
    if config.report_status != EvidenceStatus.INCOMPLETE:
        raise ValueError("Phase 53 heavy-top figure-curve runner requires incomplete status")
    report_path = _resolve_output_path(
        config.figure_curves.output_report,
        output_path=output_path,
        output_root=output_root,
    )
    report = write_heavy_top_figure_curve_report(
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


def run_heavy_top_comparison(
    *,
    config_path: str | Path,
    matrix_path: str | Path,
    source_commit: str,
    vendored_newton_commit: str,
    rk4_report_path: str | Path | None = None,
    mabd_report_path: str | Path | None = None,
    figure_curve_report_path: str | Path | None = None,
    output_path: str | Path | None = None,
    output_root: str | Path | None = None,
    paper_source_version: str = "2603.08079v2",
) -> ExperimentRunResult:
    if rk4_report_path is None or mabd_report_path is None:
        raise ValueError("heavy_top_comparison requires --mabd-report and --rbd-report")

    config = load_heavy_top_config(config_path)
    matrix = load_experiment_matrix(matrix_path)
    validate_heavy_top_config_against_matrix(config, matrix)
    if config.report_status != EvidenceStatus.INCOMPLETE:
        raise ValueError("Phase 51 heavy-top comparison runner requires incomplete status")
    report_path = _resolve_output_path(
        config.comparison.output_report,
        output_path=output_path,
        output_root=output_root,
    )
    report = write_heavy_top_comparison_report(
        report_path,
        config=config,
        rk4_report_path=rk4_report_path,
        mabd_report_path=mabd_report_path,
        figure_curve_report_path=figure_curve_report_path,
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
    "run_heavy_top_comparison",
    "run_heavy_top_figure_curves",
    "run_heavy_top_mabd_newton",
    "run_heavy_top_mabd_paper_horizon",
    "run_heavy_top_rk4_reference",
    "run_physical_pendulum_analytic_reference",
    "run_physical_pendulum_comparison",
    "run_physical_pendulum_mabd_development",
    "run_physical_pendulum_mabd_newton",
    "run_physical_pendulum_rbd_baseline",
    "run_rolling_spinning_mabd_material_preflight",
    "run_rolling_spinning_mabd_newton",
    "run_rolling_spinning_paper_timing_protocol",
    "run_rolling_spinning_protocol",
    "run_rolling_spinning_rbd_explicit_baseline",
    "run_rolling_spinning_rbd_implicit_baseline",
    "run_spinning_box_comparison",
    "run_spinning_box_contact_response",
    "run_spinning_box_decoupled_twist",
    "run_spinning_box_experiment",
    "run_spinning_box_model_plane_constraint",
    "run_spinning_box_normal_constraint",
    "run_spinning_box_paper_horizon",
    "run_spinning_box_rbd_baseline",
    "run_t_handle_comparison",
    "run_t_handle_figure_curves",
    "run_t_handle_mabd_newton",
    "run_t_handle_rk4_reference",
]
