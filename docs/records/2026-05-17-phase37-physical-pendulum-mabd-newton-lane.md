# 2026-05-17 Phase 37 Physical Pendulum MABD Newton Lane

## Status

passed

## Config Path

- `configs/experiments/single_body_physical_pendulum.yaml`
- `configs/experiments/paper_experiment_matrix.yaml`

## Repository

- base commit: `c753b56`
- plan commit: `5947077`
- implementation commit: `cf45239`
- branch: `phase37-mabd-solver-core`
- plan:
  `docs/superpowers/plans/2026-05-17-mabd-phase37-physical-pendulum-mabd-newton-lane.md`
- spec:
  `docs/superpowers/specs/2026-05-17-phase37-physical-pendulum-mabd-newton-lane-design.md`

## Vendored Newton

- source commit: `96713fa965463b69c229a4d30582c733ff3526bb`
- local patch status: Phase 37 does not modify vendored Newton

## Paper Source

- arXiv ID: `2603.08079`
- arXiv version: `v2`
- source lines: `/tmp/mabd-paper/source/sections/experiment.tex:77-91`
- scoped paper phrase: physical pendulum M-ABD comparison against analytic
  solution and implicit RBD baseline.

## Environment

- project environment: `mabd-newton-py310`
- reference environment: `physics-primitive-newton-py310`
- readiness status: `smoke_passed`
- mutates_reference_environment=false
- uses_reference_python=false
- uses_ambient_python=false

## Physical Pendulum MABD Newton Evidence

- writer: `write_physical_pendulum_mabd_newton_report`
- runner: `run_physical_pendulum_mabd_newton`
- CLI: `--lane physical_pendulum_mabd_newton`
- solver mode: `mabd_cpu_oracle_physical_pendulum_newton_lane`
- backend: `cpu_numpy_newton_only`
- baseline lane: `mabd_newton`
- top-level report status: `incomplete`
- lane_status: `incomplete_diagnostic_generated`
- report:
  `reports/experiment_matrix/single_body_physical_pendulum_mabd_newton.json`
- report source_commit: `cf45239`
- diagnostics include `phase_drift_rad`,
  `world_anchor_reaction_vector_n`, and
  `max_world_anchor_reaction_magnitude_n`.

## Regenerated Comparison Evidence

- writer: `write_physical_pendulum_comparison_report`
- runner: `run_physical_pendulum_comparison`
- CLI: `--lane physical_pendulum_comparison`
- solver mode: `physical_pendulum_multilane_comparison_development`
- backend: `report_protocol`
- baseline lane: `physical_pendulum_comparison_protocol`
- comparison report:
  `reports/experiment_matrix/single_body_physical_pendulum_comparison.json`
- comparison report source_commit: `cf45239`
- input report provenance lanes: `analytic_reference`, `mabd_newton`,
  `rbd_implicit_baseline`
- missing_required_lanes = `[]`
- missing_paper_metrics = [`joint_force_error:paper_waveform_agreement`]
- paper_metric_statuses.phase_drift.status = `diagnostic_available`
- paper_metric_statuses.joint_force_error.status =
  `diagnostic_reaction_not_paper_waveform`

## Metrics And Thresholds

- random seed: not applicable deterministic report protocol
- max_abs_angle_error_rad = `0.007130697850637885`
- max_phase_drift_rad = `0.007130697850637885`
- max_world_anchor_reaction_magnitude_n = `0.00981000000001586`
- matched_sample_count = `5`
- max_mabd_rbd_abs_angle_delta_rad = `0.0006717899335180466`
- threshold status: diagnostic thresholds are satisfied, but no full
  experiment pass gate is enabled.

## TDD Evidence

- RED: `tests.test_experiment_run_configs` failed because the
  physical-pendulum config had no `mabd_newton` block.
- GREEN: `Ran 24 tests` for `tests.test_experiment_run_configs`.
- RED: `tests.test_physical_pendulum_mabd` failed because rollout samples
  lacked world-anchor reaction diagnostics.
- GREEN: `Ran 1 test` for `tests.test_physical_pendulum_mabd`.
- RED: `tests.test_experiment_runner` failed because
  `run_physical_pendulum_mabd_newton` and
  `--lane physical_pendulum_mabd_newton` were absent.
- GREEN: `Ran 30 tests` for `tests.test_experiment_runner`.
- RED: `tests.test_physical_pendulum_comparison_reports
  tests.test_experiment_runner` failed because the comparison still required
  `physical_pendulum_mabd_development_diagnostic`.
- GREEN: `Ran 36 tests` for
  `tests.test_physical_pendulum_comparison_reports tests.test_experiment_runner`.

## Claim Impact

- No `experiment.*` claim is passed.
- `experiment.single_body.physical_pendulum` remains intended.
- A formal but incomplete physical-pendulum `mabd_newton` report artifact now
  exists.
- Joint-force waveform agreement remains missing.
- Paper-faithful pendulum geometry remains missing.
- `pendulum_geometry_unknown` remains a blocker.
- paper timing remains missing.

## Verification Commands

- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_run_configs`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_physical_pendulum_mabd`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_physical_pendulum_comparison_reports tests.test_experiment_runner`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_phase0_bootstrap`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/env/readiness_check.py`
- `PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"`
- `git diff --check`
