# 2026-05-17 Phase 33 Physical Pendulum Analytic Reference

## Status

passed

## Config Path

- `configs/experiments/single_body_physical_pendulum.yaml`
- `configs/experiments/paper_experiment_matrix.yaml`

## Repository

- base commit: `52fa600`
- branch: `phase33-physical-pendulum-reference`
- worktree: `/cpfs/user/zhuzihou/dev/mabd-newton/.worktrees/phase33-audit`
- plan:
  `docs/superpowers/plans/2026-05-17-mabd-phase33-physical-pendulum-analytic-reference.md`
- spec:
  `docs/superpowers/specs/2026-05-17-phase33-physical-pendulum-analytic-reference-design.md`

## Vendored Newton

- source commit: `96713fa965463b69c229a4d30582c733ff3526bb`
- local patch status: Phase 33 does not modify vendored Newton

## Paper Source

- arXiv ID: `2603.08079`
- arXiv version: `v2`
- PDF SHA256: `a594e79093673c60fc59ad14f9b71f29a8f7f8e7b1c3d9c73efe6f5814cc6ec0`
- TeX source root: `/tmp/mabd-paper/source`
- `sections/experiment.tex` SHA256:
  `c5927183fe4e3f1c1c1617e5b10b7e9006da6a9eac537e891cb1dac03d58dd0f`
- cited lines: `/tmp/mabd-paper/source/sections/experiment.tex:77-91`
- cited formula:
  `theta(t)=pi/2 - 2 asin(kappa * sn(K(kappa) - omega_lin * t, kappa))`

## Environment

- Python: `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python`
- cloned from: `/cpfs/user/zhuzihou/conda-managed/envs/physics-primitive-newton-py310`
- readiness: `smoke_passed`
- SciPy: `1.15.3`
- mutates_reference_environment=false
- uses_reference_python=false
- uses_ambient_python=false

## Analytic Reference Evidence

- module: `src/mabd_reproduction/physical_pendulum_reference.py`
- report writer: `src/mabd_reproduction/physical_pendulum_reports.py`
- config loader: `load_physical_pendulum_config`
- matrix validator: `validate_physical_pendulum_config_against_matrix`
- runner: `run_physical_pendulum_analytic_reference`
- CLI lane: `--lane analytic_reference`
- formula helper: `physical_pendulum_angle_reference`
- SciPy parameterization: `ellipk` and `ellipj` use `m = kappa**2`
- paper reference checkpoints:
  `theta(0)=0`, `theta(K/omega_lin)=pi/2`, `theta(2K/omega_lin)=pi`
- report lane: `analytic_reference`
- solver mode: `analytic_elliptic_reference`
- backend: `cpu_scipy_reference`
- lane_status = passed
- top-level report status: `incomplete`
- report output contract:
  `reports/experiment_matrix/single_body_physical_pendulum_analytic_reference.json`
- review hardening:
  `lane_status` is derived from threshold violations, required missing lanes
  are fixed to `mabd_newton` and `rbd_implicit_baseline`, and horizontal-release
  reference parameters are cross-validated.

## Metrics And Thresholds

- random seed: not applicable deterministic analytic formula
- metric: `max_abs_reference_identity_error = 2.220446049250313e-16`
- threshold: `max_abs_reference_identity_error <= 1.0e-12`
- threshold status: `passed`
- complete elliptic integral: `K(kappa) = 1.8540746773013719`
- period_s: `2.3678419475762373`
- checkpoint time_s: `[0.0, 0.5919604868940593, 1.1839209737881187]`
- checkpoint observed angle_rad:
  `[-2.220446049250313e-16, 1.5707963267948966, 3.141592653589793]`
- checkpoint expected angle_rad:
  `[0.0, 1.5707963267948966, 3.141592653589793]`
- compact sample count: `9`

## TDD Evidence

- RED command:
  `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_physical_pendulum_reference tests.test_experiment_run_configs tests.test_experiment_runner`
- RED result: `FAILED (failures=1, errors=5)`
- RED missing symbols:
  `physical_pendulum_reference`,
  `load_physical_pendulum_config`,
  `validate_physical_pendulum_config_against_matrix`,
  `run_physical_pendulum_analytic_reference`,
  `--lane analytic_reference`
- GREEN command:
  `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_physical_pendulum_reference tests.test_experiment_run_configs tests.test_experiment_runner`
- GREEN result: `Ran 37 tests`, `OK`

## Claim Impact

- No `experiment.*` claim is passed.
- `experiment.single_body.physical_pendulum` remains not passed.
- The physical-pendulum M-ABD simulation lane remains missing.
- The physical-pendulum RBD implicit baseline remains missing.
- Joint-force waveform agreement remains missing.
- `pendulum_geometry_unknown` remains a blocker.
- This phase is analytic-reference lane evidence only, not full paper
  reproduction.

## Artifacts

- generated reports: not committed
- raw paper assets: not committed
- generated videos: not committed

## Verification Commands

- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_physical_pendulum_reference tests.test_experiment_run_configs tests.test_experiment_runner`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_phase0_bootstrap`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/env/readiness_check.py`
- `PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"`
- `git diff --check`
