# Phase 35 Physical Pendulum RBD Baseline Diagnostic

## Status

passed

## Config Path

- `configs/experiments/single_body_physical_pendulum.yaml`
- `configs/experiments/paper_experiment_matrix.yaml`

## Repository

- base commit: `7778469`
- branch: `phase35-physical-pendulum-rbd-baseline`
- plan:
  `docs/superpowers/plans/2026-05-17-mabd-phase35-physical-pendulum-rbd-baseline.md`
- spec:
  `docs/superpowers/specs/2026-05-17-phase35-physical-pendulum-rbd-baseline-design.md`

## Vendored Newton

- source commit: `96713fa965463b69c229a4d30582c733ff3526bb`
- local patch status: Phase 35 does not modify vendored Newton.

## Paper Source

- arXiv ID: `2603.08079`
- arXiv version: `v2`
- paper source root: `/tmp/mabd-paper/source`
- source lines: `/tmp/mabd-paper/source/sections/experiment.tex:77-91`
- scoped paper phrase: implicit RBD baseline against the analytic solution.

## Environment

- project environment: `mabd-newton-py310`
- reference environment: `physics-primitive-newton-py310`
- clone evidence: `mabd-newton-py310` was created by cloning
  `physics-primitive-newton-py310`.
- readiness status: `smoke_passed`
- mutates_reference_environment=false
- uses_reference_python=false
- uses_ambient_python=false

## Physical Pendulum RBD Evidence

- implementation: `src/mabd_reproduction/physical_pendulum_rbd.py`
- runner: `run_physical_pendulum_rbd_baseline`
- CLI: `--lane rbd_implicit_baseline`
- solver mode: `physical_pendulum_scalar_implicit_rbd_development`
- backend: `cpu_numpy_newton_only`
- baseline lane: `rbd_implicit_baseline`
- lane_status = development_diagnostic_generated
- top-level report status: `incomplete`
- required_missing_lanes = [`mabd_newton`]
- report:
  `reports/experiment_matrix/single_body_physical_pendulum_rbd_baseline.json`
- joint-force magnitude is diagnostic only; this is not paper waveform
  agreement.
- the diagnostic uses a scalar implicit pendulum update and point-position
  reconstruction to keep the fixed-length constraint machine-checkable.

## Metrics And Thresholds

- random seed: not applicable deterministic scalar implicit RBD rollout
- time_step_s: `0.01`
- step_count: `16`
- compact sample count: `5`
- max_abs_angle_error_rad <= 2.0
- max_abs_angle_error_rad = 0.0078024877841559315
- max_phase_drift_rad <= 2.0
- max_phase_drift_rad = 0.0078024877841559315
- max_implicit_residual <= 1.0e-12
- max_implicit_residual = 6.245004513516506e-16
- max_length_constraint_error_m <= 1.0e-12
- max_length_constraint_error_m = 1.1102230246251565e-16
- max_joint_force_magnitude_n = 3.7570647135963737
- threshold status: `passed`
- sample steps: `[0, 4, 8, 12, 16]`

## TDD Evidence

- RED: `tests.test_physical_pendulum_rbd` initially failed with missing
  `mabd_reproduction.physical_pendulum_rbd`.
- RED: `tests.test_experiment_runner` initially failed because
  `run_physical_pendulum_rbd_baseline` and `--lane rbd_implicit_baseline`
  physical-pendulum dispatch were absent.
- GREEN: `Ran 3 tests` for `tests.test_physical_pendulum_rbd`.
- GREEN: `Ran 16 tests` for `tests.test_experiment_run_configs`.
- GREEN: `Ran 25 tests` for `tests.test_experiment_runner`.

## Claim Impact

- No `experiment.*` claim is passed.
- `experiment.single_body.physical_pendulum` remains not passed.
- required physical-pendulum `mabd_newton` experiment lane remains missing.
- RBD implicit baseline diagnostic is now present.
- Joint-force waveform agreement remains missing.
- Paper-faithful pendulum geometry remains missing.
- `pendulum_geometry_unknown` remains a blocker.
- paper timing remains missing.

## Verification Commands

- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_physical_pendulum_rbd tests.test_experiment_run_configs tests.test_experiment_runner`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_phase0_bootstrap`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/env/readiness_check.py`
- `PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"`
- `git diff --check`
