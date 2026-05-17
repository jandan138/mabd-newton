# 2026-05-17 Phase 36 Physical Pendulum Comparison Protocol

## Status

passed

## Config Path

- `configs/experiments/single_body_physical_pendulum.yaml`
- `configs/experiments/paper_experiment_matrix.yaml`

## Repository

- base commit: `91275d8`
- implementation commit: `a2a9374`
- branch: `phase36-physical-pendulum-comparison-protocol`
- plan:
  `docs/superpowers/plans/2026-05-17-mabd-phase36-physical-pendulum-comparison-protocol.md`
- spec:
  `docs/superpowers/specs/2026-05-17-phase36-physical-pendulum-comparison-protocol-design.md`

## Vendored Newton

- source commit: `96713fa965463b69c229a4d30582c733ff3526bb`
- local patch status: Phase 36 does not modify vendored Newton

## Paper Source

- arXiv ID: `2603.08079`
- arXiv version: `v2`
- source lines: `/tmp/mabd-paper/source/sections/experiment.tex:77-91`
- scoped paper phrase: physical pendulum comparison against analytic solution
  and implicit RBD baseline.

## Environment

- project environment: `mabd-newton-py310`
- reference environment: `physics-primitive-newton-py310`
- readiness status: `smoke_passed`
- mutates_reference_environment=false
- uses_reference_python=false
- uses_ambient_python=false

## Physical Pendulum Comparison Evidence

- writer: `write_physical_pendulum_comparison_report`
- runner: `run_physical_pendulum_comparison`
- CLI: `--lane physical_pendulum_comparison`
- solver mode: `physical_pendulum_multilane_comparison_development`
- backend: `report_protocol`
- baseline lane: `physical_pendulum_comparison_protocol`
- top-level report status: `incomplete`
- input_report_provenance records per-lane path, SHA256, source commit,
  vendored Newton commit, solver mode, backend, baseline lane, and status.
- paper_metric_statuses maps canonical matrix metrics to current diagnostic
  fields or missing reasons.
- analytic report:
  `reports/experiment_matrix/single_body_physical_pendulum_analytic_reference.json`
- analytic report source_commit: `a2a9374`
- comparison report:
  `reports/experiment_matrix/single_body_physical_pendulum_comparison.json`
- comparison report source_commit: `a2a9374`
- M-ABD diagnostic input report source_commit: `88c8195`
- RBD diagnostic input report source_commit: `88c8195`

## Metrics And Thresholds

- random seed: not applicable deterministic report protocol
- required_missing_lanes = [`mabd_newton`]
- matched_sample_count = `5`
- mabd_sample_count = `5`
- rbd_sample_count = `5`
- unmatched_mabd_samples = `[]`
- unmatched_rbd_samples = `[]`
- max_mabd_rbd_abs_angle_delta_rad <= 2.0
- max_mabd_rbd_abs_angle_delta_rad = 0.0006717899335180466
- joint_force_error status = `missing_waveform_not_max_magnitude`
- threshold status: incomplete protocol only; no full experiment pass gate is
  enabled.

## TDD Evidence

- RED: `tests.test_experiment_run_configs` failed because
  `PhysicalPendulumRunConfig` had no `comparison` block.
- GREEN: `Ran 22 tests` for `tests.test_experiment_run_configs`.
- RED: `tests.test_physical_pendulum_comparison_reports` failed because
  `write_physical_pendulum_comparison_report` was absent.
- GREEN: `Ran 5 tests` for
  `tests.test_physical_pendulum_comparison_reports`.
- RED: `tests.test_experiment_runner` failed because
  `run_physical_pendulum_comparison`, `--lane physical_pendulum_comparison`,
  and `--analytic-report` were absent.
- GREEN: `Ran 33 tests` for
  `tests.test_experiment_runner tests.test_physical_pendulum_comparison_reports`.

## Claim Impact

- No `experiment.*` claim is passed.
- `experiment.single_body.physical_pendulum` remains intended.
- required physical-pendulum `mabd_newton` experiment lane remains missing.
- Joint-force waveform agreement remains missing.
- Paper-faithful pendulum geometry remains missing.
- `pendulum_geometry_unknown` remains a blocker.
- paper timing remains missing.

## Verification Commands

- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_run_configs tests.test_physical_pendulum_comparison_reports tests.test_experiment_runner`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_phase0_bootstrap`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/env/readiness_check.py`
- `PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"`
- `git diff --check`
