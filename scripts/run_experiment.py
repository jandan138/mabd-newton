#!/usr/bin/env python3
"""Run one configured M-ABD reproduction experiment lane."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

from mabd_reproduction.experiment_runner import (
    run_heavy_top_comparison,
    run_heavy_top_figure_curves,
    run_heavy_top_mabd_newton,
    run_heavy_top_mabd_paper_horizon,
    run_heavy_top_rk4_reference,
    run_physical_pendulum_analytic_reference,
    run_physical_pendulum_comparison,
    run_physical_pendulum_mabd_development,
    run_physical_pendulum_mabd_newton,
    run_physical_pendulum_rbd_baseline,
    run_spinning_box_comparison,
    run_spinning_box_contacts_input,
    run_spinning_box_contact_response,
    run_spinning_box_decoupled_twist,
    run_spinning_box_experiment,
    run_spinning_box_figure_curves,
    run_spinning_box_model_plane_constraint,
    run_spinning_box_normal_constraint,
    run_spinning_box_paper_horizon,
    run_spinning_box_rbd_baseline,
    run_t_handle_comparison,
    run_t_handle_figure_curves,
    run_t_handle_mabd_newton,
    run_t_handle_rk4_reference,
)


def _config_claim_id(path: Path) -> str:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("claim_id"), str):
        raise ValueError("config must contain a string claim_id")
    return data["claim_id"]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run one configured M-ABD experiment lane.")
    parser.add_argument(
        "--lane",
        choices=(
            "analytic_reference",
            "heavy_top_comparison",
            "heavy_top_figure_curves",
            "heavy_top_mabd_newton",
            "heavy_top_mabd_paper_horizon",
            "heavy_top_rk4_reference",
            "mabd_newton",
            "mabd_paper_horizon",
            "physical_pendulum_comparison",
            "physical_pendulum_mabd_development",
            "physical_pendulum_mabd_newton",
            "rbd_implicit_baseline",
            "spinning_box_comparison",
            "spinning_box_contacts_input",
            "spinning_box_contact_response",
            "spinning_box_decoupled_twist",
            "spinning_box_figure_curves",
            "spinning_box_model_plane_constraint",
            "spinning_box_normal_constraint",
            "t_handle_comparison",
            "t_handle_figure_curves",
            "t_handle_mabd_newton",
            "t_handle_rk4_reference",
        ),
        default="mabd_newton",
        help="Experiment lane to run.",
    )
    parser.add_argument("--config", required=True, help="Experiment config YAML path.")
    parser.add_argument(
        "--matrix",
        default="configs/experiments/paper_experiment_matrix.yaml",
        help="Paper experiment matrix YAML path.",
    )
    parser.add_argument("--output", help="Override report output path.")
    parser.add_argument("--output-root", help="Root under which the config output_report path is written.")
    parser.add_argument(
        "--analytic-report",
        help="Existing analytic reference report for physical-pendulum comparison lane.",
    )
    parser.add_argument("--mabd-report", help="Existing M-ABD lane report for comparison lanes.")
    parser.add_argument("--rbd-report", help="Existing RBD baseline report for comparison lanes.")
    parser.add_argument("--figure-report", help="Existing digitized paper-figure report.")
    parser.add_argument("--source-commit", required=True, help="Repository source commit recorded in the report.")
    parser.add_argument(
        "--vendored-newton-commit",
        required=True,
        help="Vendored Newton source commit recorded in the report.",
    )
    parser.add_argument("--paper-source-version", default="2603.08079v2")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    json_stdout = sys.stdout
    sys.stdout = sys.stderr
    try:
        if args.lane == "spinning_box_comparison":
            result = run_spinning_box_comparison(
                config_path=Path(args.config),
                matrix_path=Path(args.matrix),
                mabd_report_path=Path(args.mabd_report) if args.mabd_report else None,
                rbd_report_path=Path(args.rbd_report) if args.rbd_report else None,
                figure_curve_report_path=Path(args.figure_report) if args.figure_report else None,
                output_path=Path(args.output) if args.output else None,
                output_root=Path(args.output_root) if args.output_root else None,
                source_commit=args.source_commit,
                vendored_newton_commit=args.vendored_newton_commit,
                paper_source_version=args.paper_source_version,
            )
        elif args.lane == "heavy_top_comparison":
            result = run_heavy_top_comparison(
                config_path=Path(args.config),
                matrix_path=Path(args.matrix),
                rk4_report_path=Path(args.rbd_report) if args.rbd_report else None,
                mabd_report_path=Path(args.mabd_report) if args.mabd_report else None,
                figure_curve_report_path=Path(args.figure_report) if args.figure_report else None,
                output_path=Path(args.output) if args.output else None,
                output_root=Path(args.output_root) if args.output_root else None,
                source_commit=args.source_commit,
                vendored_newton_commit=args.vendored_newton_commit,
                paper_source_version=args.paper_source_version,
            )
        elif args.lane == "heavy_top_figure_curves":
            result = run_heavy_top_figure_curves(
                config_path=Path(args.config),
                matrix_path=Path(args.matrix),
                output_path=Path(args.output) if args.output else None,
                output_root=Path(args.output_root) if args.output_root else None,
                source_commit=args.source_commit,
                vendored_newton_commit=args.vendored_newton_commit,
                paper_source_version=args.paper_source_version,
            )
        elif args.lane == "analytic_reference":
            result = run_physical_pendulum_analytic_reference(
                config_path=Path(args.config),
                matrix_path=Path(args.matrix),
                output_path=Path(args.output) if args.output else None,
                output_root=Path(args.output_root) if args.output_root else None,
                source_commit=args.source_commit,
                vendored_newton_commit=args.vendored_newton_commit,
                paper_source_version=args.paper_source_version,
            )
        elif args.lane == "mabd_paper_horizon":
            result = run_spinning_box_paper_horizon(
                config_path=Path(args.config),
                matrix_path=Path(args.matrix),
                output_path=Path(args.output) if args.output else None,
                output_root=Path(args.output_root) if args.output_root else None,
                source_commit=args.source_commit,
                vendored_newton_commit=args.vendored_newton_commit,
                paper_source_version=args.paper_source_version,
            )
        elif args.lane == "spinning_box_contact_response":
            result = run_spinning_box_contact_response(
                config_path=Path(args.config),
                matrix_path=Path(args.matrix),
                output_path=Path(args.output) if args.output else None,
                output_root=Path(args.output_root) if args.output_root else None,
                source_commit=args.source_commit,
                vendored_newton_commit=args.vendored_newton_commit,
                paper_source_version=args.paper_source_version,
            )
        elif args.lane == "spinning_box_normal_constraint":
            result = run_spinning_box_normal_constraint(
                config_path=Path(args.config),
                matrix_path=Path(args.matrix),
                output_path=Path(args.output) if args.output else None,
                output_root=Path(args.output_root) if args.output_root else None,
                source_commit=args.source_commit,
                vendored_newton_commit=args.vendored_newton_commit,
                paper_source_version=args.paper_source_version,
            )
        elif args.lane == "spinning_box_model_plane_constraint":
            result = run_spinning_box_model_plane_constraint(
                config_path=Path(args.config),
                matrix_path=Path(args.matrix),
                output_path=Path(args.output) if args.output else None,
                output_root=Path(args.output_root) if args.output_root else None,
                source_commit=args.source_commit,
                vendored_newton_commit=args.vendored_newton_commit,
                paper_source_version=args.paper_source_version,
            )
        elif args.lane == "spinning_box_contacts_input":
            result = run_spinning_box_contacts_input(
                config_path=Path(args.config),
                matrix_path=Path(args.matrix),
                output_path=Path(args.output) if args.output else None,
                output_root=Path(args.output_root) if args.output_root else None,
                source_commit=args.source_commit,
                vendored_newton_commit=args.vendored_newton_commit,
                paper_source_version=args.paper_source_version,
            )
        elif args.lane == "spinning_box_decoupled_twist":
            result = run_spinning_box_decoupled_twist(
                config_path=Path(args.config),
                matrix_path=Path(args.matrix),
                output_path=Path(args.output) if args.output else None,
                output_root=Path(args.output_root) if args.output_root else None,
                source_commit=args.source_commit,
                vendored_newton_commit=args.vendored_newton_commit,
                paper_source_version=args.paper_source_version,
            )
        elif args.lane == "spinning_box_figure_curves":
            result = run_spinning_box_figure_curves(
                config_path=Path(args.config),
                matrix_path=Path(args.matrix),
                output_path=Path(args.output) if args.output else None,
                output_root=Path(args.output_root) if args.output_root else None,
                source_commit=args.source_commit,
                vendored_newton_commit=args.vendored_newton_commit,
                paper_source_version=args.paper_source_version,
            )
        elif args.lane == "physical_pendulum_mabd_development":
            result = run_physical_pendulum_mabd_development(
                config_path=Path(args.config),
                matrix_path=Path(args.matrix),
                output_path=Path(args.output) if args.output else None,
                output_root=Path(args.output_root) if args.output_root else None,
                source_commit=args.source_commit,
                vendored_newton_commit=args.vendored_newton_commit,
                paper_source_version=args.paper_source_version,
            )
        elif args.lane == "physical_pendulum_mabd_newton":
            result = run_physical_pendulum_mabd_newton(
                config_path=Path(args.config),
                matrix_path=Path(args.matrix),
                output_path=Path(args.output) if args.output else None,
                output_root=Path(args.output_root) if args.output_root else None,
                source_commit=args.source_commit,
                vendored_newton_commit=args.vendored_newton_commit,
                paper_source_version=args.paper_source_version,
            )
        elif args.lane == "physical_pendulum_comparison":
            result = run_physical_pendulum_comparison(
                config_path=Path(args.config),
                matrix_path=Path(args.matrix),
                analytic_report_path=Path(args.analytic_report) if args.analytic_report else None,
                mabd_report_path=Path(args.mabd_report) if args.mabd_report else None,
                rbd_report_path=Path(args.rbd_report) if args.rbd_report else None,
                output_path=Path(args.output) if args.output else None,
                output_root=Path(args.output_root) if args.output_root else None,
                source_commit=args.source_commit,
                vendored_newton_commit=args.vendored_newton_commit,
                paper_source_version=args.paper_source_version,
            )
        elif args.lane == "t_handle_rk4_reference":
            result = run_t_handle_rk4_reference(
                config_path=Path(args.config),
                matrix_path=Path(args.matrix),
                output_path=Path(args.output) if args.output else None,
                output_root=Path(args.output_root) if args.output_root else None,
                source_commit=args.source_commit,
                vendored_newton_commit=args.vendored_newton_commit,
                paper_source_version=args.paper_source_version,
            )
        elif args.lane == "t_handle_mabd_newton":
            result = run_t_handle_mabd_newton(
                config_path=Path(args.config),
                matrix_path=Path(args.matrix),
                output_path=Path(args.output) if args.output else None,
                output_root=Path(args.output_root) if args.output_root else None,
                source_commit=args.source_commit,
                vendored_newton_commit=args.vendored_newton_commit,
                paper_source_version=args.paper_source_version,
            )
        elif args.lane == "t_handle_figure_curves":
            result = run_t_handle_figure_curves(
                config_path=Path(args.config),
                matrix_path=Path(args.matrix),
                output_path=Path(args.output) if args.output else None,
                output_root=Path(args.output_root) if args.output_root else None,
                source_commit=args.source_commit,
                vendored_newton_commit=args.vendored_newton_commit,
                paper_source_version=args.paper_source_version,
            )
        elif args.lane == "t_handle_comparison":
            result = run_t_handle_comparison(
                config_path=Path(args.config),
                matrix_path=Path(args.matrix),
                rk4_report_path=Path(args.rbd_report) if args.rbd_report else None,
                mabd_report_path=Path(args.mabd_report) if args.mabd_report else None,
                figure_curve_report_path=Path(args.figure_report) if args.figure_report else None,
                output_path=Path(args.output) if args.output else None,
                output_root=Path(args.output_root) if args.output_root else None,
                source_commit=args.source_commit,
                vendored_newton_commit=args.vendored_newton_commit,
                paper_source_version=args.paper_source_version,
            )
        elif args.lane == "heavy_top_rk4_reference":
            result = run_heavy_top_rk4_reference(
                config_path=Path(args.config),
                matrix_path=Path(args.matrix),
                output_path=Path(args.output) if args.output else None,
                output_root=Path(args.output_root) if args.output_root else None,
                source_commit=args.source_commit,
                vendored_newton_commit=args.vendored_newton_commit,
                paper_source_version=args.paper_source_version,
            )
        elif args.lane == "heavy_top_mabd_newton":
            result = run_heavy_top_mabd_newton(
                config_path=Path(args.config),
                matrix_path=Path(args.matrix),
                output_path=Path(args.output) if args.output else None,
                output_root=Path(args.output_root) if args.output_root else None,
                source_commit=args.source_commit,
                vendored_newton_commit=args.vendored_newton_commit,
                paper_source_version=args.paper_source_version,
            )
        elif args.lane == "heavy_top_mabd_paper_horizon":
            result = run_heavy_top_mabd_paper_horizon(
                config_path=Path(args.config),
                matrix_path=Path(args.matrix),
                output_path=Path(args.output) if args.output else None,
                output_root=Path(args.output_root) if args.output_root else None,
                source_commit=args.source_commit,
                vendored_newton_commit=args.vendored_newton_commit,
                paper_source_version=args.paper_source_version,
            )
        elif args.lane == "rbd_implicit_baseline":
            claim_id = _config_claim_id(Path(args.config))
            if claim_id == "experiment.single_body.physical_pendulum":
                result = run_physical_pendulum_rbd_baseline(
                    config_path=Path(args.config),
                    matrix_path=Path(args.matrix),
                    output_path=Path(args.output) if args.output else None,
                    output_root=Path(args.output_root) if args.output_root else None,
                    source_commit=args.source_commit,
                    vendored_newton_commit=args.vendored_newton_commit,
                    paper_source_version=args.paper_source_version,
                )
            else:
                result = run_spinning_box_rbd_baseline(
                    config_path=Path(args.config),
                    matrix_path=Path(args.matrix),
                    output_path=Path(args.output) if args.output else None,
                    output_root=Path(args.output_root) if args.output_root else None,
                    source_commit=args.source_commit,
                    vendored_newton_commit=args.vendored_newton_commit,
                    paper_source_version=args.paper_source_version,
                )
        else:
            result = run_spinning_box_experiment(
                config_path=Path(args.config),
                matrix_path=Path(args.matrix),
                output_path=Path(args.output) if args.output else None,
                output_root=Path(args.output_root) if args.output_root else None,
                source_commit=args.source_commit,
                vendored_newton_commit=args.vendored_newton_commit,
                paper_source_version=args.paper_source_version,
            )
    except Exception as exc:
        sys.stdout = json_stdout
        print(f"run_experiment.py: {exc}", file=sys.stderr)
        return 1
    sys.stdout = json_stdout
    print(json.dumps(result.to_summary(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
