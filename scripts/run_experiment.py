#!/usr/bin/env python3
"""Run one configured M-ABD reproduction experiment lane."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from mabd_reproduction.experiment_runner import (
    run_physical_pendulum_analytic_reference,
    run_physical_pendulum_mabd_development,
    run_spinning_box_comparison,
    run_spinning_box_experiment,
    run_spinning_box_paper_horizon,
    run_spinning_box_rbd_baseline,
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run one configured M-ABD experiment lane.")
    parser.add_argument(
        "--lane",
        choices=(
            "analytic_reference",
            "mabd_newton",
            "mabd_paper_horizon",
            "physical_pendulum_mabd_development",
            "rbd_implicit_baseline",
            "spinning_box_comparison",
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
    parser.add_argument("--mabd-report", help="Existing M-ABD lane report for comparison lanes.")
    parser.add_argument("--rbd-report", help="Existing RBD baseline report for comparison lanes.")
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
    try:
        if args.lane == "spinning_box_comparison":
            result = run_spinning_box_comparison(
                config_path=Path(args.config),
                matrix_path=Path(args.matrix),
                mabd_report_path=Path(args.mabd_report) if args.mabd_report else None,
                rbd_report_path=Path(args.rbd_report) if args.rbd_report else None,
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
        else:
            runner = (
                run_spinning_box_rbd_baseline
                if args.lane == "rbd_implicit_baseline"
                else run_spinning_box_experiment
            )
            result = runner(
                config_path=Path(args.config),
                matrix_path=Path(args.matrix),
                output_path=Path(args.output) if args.output else None,
                output_root=Path(args.output_root) if args.output_root else None,
                source_commit=args.source_commit,
                vendored_newton_commit=args.vendored_newton_commit,
                paper_source_version=args.paper_source_version,
            )
    except Exception as exc:
        print(f"run_experiment.py: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result.to_summary(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
