# 2026-05-17 Phase 34 World Anchor Physical Pendulum M-ABD Diagnostic

## Status

passed

## Config Path

- `configs/experiments/single_body_physical_pendulum.yaml`
- `configs/experiments/paper_experiment_matrix.yaml`

## Repository

- base commit: `81785e0`
- branch: `phase34-physical-pendulum-mabd-lane`
- worktree:
  `/cpfs/user/zhuzihou/dev/mabd-newton/.worktrees/phase34-physical-pendulum-mabd-lane`
- plan:
  `docs/superpowers/plans/2026-05-17-mabd-phase34-world-anchor-physical-pendulum-mabd.md`
- spec:
  `docs/superpowers/specs/2026-05-17-phase34-world-anchor-physical-pendulum-mabd-design.md`

## Vendored Newton

- source commit: `96713fa965463b69c229a4d30582c733ff3526bb`
- local patch status: Phase 34 modifies vendored Newton M-ABD CPU oracle code
- patched files:
  - `vendor/newton/newton/_src/solvers/mabd/step_oracle.py`
  - `vendor/newton/newton/_src/solvers/mabd/__init__.py`
  - `vendor/newton/newton/tests/test_mabd_phase4_solver_step.py`

## Paper Source

- arXiv ID: `2603.08079`
- arXiv version: `v2`
- PDF SHA256:
  `a594e79093673c60fc59ad14f9b71f29a8f7f8e7b1c3d9c73efe6f5814cc6ec0`
- TeX source root: `/tmp/mabd-paper/source`
- `sections/experiment.tex` SHA256:
  `c5927183fe4e3f1c1c1617e5b10b7e9006da6a9eac537e891cb1dac03d58dd0f`
- cited lines: `/tmp/mabd-paper/source/sections/experiment.tex:77-91`
- cited paper requirements: fixed pivot, horizontal release, zero initial
  velocity, gravity, analytic angle reference, joint-force waveform comparison,
  and implicit RBD baseline comparison.

## Environment

- Python:
  `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python`
- cloned from:
  `/cpfs/user/zhuzihou/conda-managed/envs/physics-primitive-newton-py310`
- readiness: `smoke_passed`
- mutates_reference_environment=false
- uses_reference_python=false
- uses_ambient_python=false

## Newton World Anchor Evidence

- API: `MABDCPUOracleWorldConstraint`
- config field: `MABDCPUOracleConfig.world_constraints`
- dense KKT assembly includes single-body world rows using
  `point_jacobian(rest_point)`.
- residual correction enforces `J q_next - world_point = 0` for the pivot.
- topology gate: world-anchor constraints currently require `topology='dense'`.
- validation gate: malformed rest/world vectors are rejected.
- repo tests: `tests.test_mabd_phase4_solver_step`
- vendored tests: `newton.tests.test_mabd_phase4_solver_step`

## Physical Pendulum M-ABD Diagnostic Evidence

- module: `src/mabd_reproduction/physical_pendulum_mabd.py`
- report writer: `src/mabd_reproduction/physical_pendulum_reports.py`
- config loader: `load_physical_pendulum_config`
- matrix validator: `validate_physical_pendulum_config_against_matrix`
- runner: `run_physical_pendulum_mabd_development`
- CLI lane: `--lane physical_pendulum_mabd_development`
- report lane: `physical_pendulum_mabd_development_diagnostic`
- solver mode: `mabd_cpu_oracle_physical_pendulum_development`
- backend: `cpu_numpy_newton_only`
- lane_status = development_diagnostic_generated
- top-level report status: `incomplete`
- report output contract:
  `reports/experiment_matrix/single_body_physical_pendulum_mabd_development.json`
- non-claim limitations:
  - paper pendulum geometry remains unknown
  - no implicit RBD baseline is run
  - no joint-force waveform comparison is generated
  - no rendered figure is generated
  - no paper timing distribution is generated
- required `mabd_newton` experiment lane remains listed as missing in
  `required_missing_lanes`; this diagnostic lane is not that required lane.

## Metrics And Thresholds

- random seed: not applicable deterministic config-driven CPU oracle rollout
- time_step_s: `0.01`
- step_count: `16`
- compact sample count: `5`
- threshold: `max_pivot_residual_m <= 1.0e-10`
- observed: `max_pivot_residual_m = 0.0`
- threshold: `max_constraint_residual_norm <= 1.0e-10`
- observed: `max_constraint_residual_norm = 0.0`
- threshold: `max_abs_angle_error_rad <= 2.0`
- observed: `max_abs_angle_error_rad = 0.007130697850637885`
- threshold status: `passed`
- sample steps: `[0, 4, 8, 12, 16]`
- sample angle_rad:
  `[0.0, 0.009809685326122591, 0.03530132870528927, 0.0763691846994714, 0.13263275412431139]`
- sample reference_angle_rad:
  `[0.0, 0.007847983887816712, 0.03139096886790638, 0.07062025711132391, 0.1255020562736735]`

## TDD Evidence

- RED command:
  `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_mabd_phase4_solver_step`
- RED result: `AttributeError: module 'newton.solvers.mabd' has no attribute 'MABDCPUOracleWorldConstraint'`
- RED command:
  `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_run_configs tests.test_experiment_runner`
- RED result: missing `mabd_development` config parsing and
  `run_physical_pendulum_mabd_development`
- RED command:
  `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_runner.ExperimentRunnerTests.test_run_experiment_cli_writes_physical_pendulum_mabd_development_report`
- RED result: invalid CLI choice `physical_pendulum_mabd_development`
- GREEN command:
  `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_mabd_phase4_solver_step`
- GREEN result: `Ran 22 tests`, `OK`
- GREEN command:
  `PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest newton.tests.test_mabd_phase4_solver_step`
- GREEN result: `Ran 17 tests`, `OK`
- GREEN command:
  `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_run_configs tests.test_experiment_runner`
- GREEN result: `Ran 38 tests`, `OK`

## Claim Impact

- No `experiment.*` claim is passed.
- `experiment.single_body.physical_pendulum` remains not passed.
- This is a Newton-only M-ABD development diagnostic lane, not a full paper
  reproduction.
- The required physical-pendulum `mabd_newton` experiment lane remains missing.
- The physical-pendulum RBD implicit baseline remains missing.
- Joint-force waveform agreement remains missing.
- Paper-faithful pendulum geometry remains missing.
- Rendered output and timing evidence remain missing.
- `pendulum_geometry_unknown` remains a blocker.

## Artifacts

- generated reports: not committed
- raw paper assets: not committed
- generated videos: not committed

## Verification Commands

- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_mabd_phase4_solver_step`
- `PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest newton.tests.test_mabd_phase4_solver_step`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_run_configs tests.test_experiment_runner`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_phase0_bootstrap`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/env/readiness_check.py`
- `PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"`
- `git diff --check`
