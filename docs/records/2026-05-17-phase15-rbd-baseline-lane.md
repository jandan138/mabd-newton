# Phase 15 RBD Baseline Lane Record

Date: 2026-05-17

## Status

passed

## Scope

Phase 15 adds a Newton `SolverSemiImplicit` CPU free-rigid development baseline
for the required single-body spinning-box `rbd_implicit_baseline` lane. The lane
computes deterministic rigid-cube mass, inertia, velocity, and angular velocity
from the paper values, executes vendored Newton steps on CPU, records final
pose/velocity and conservation diagnostics, writes a full-schema `ClaimReport`,
and is dispatchable from `scripts/run_experiment.py` with
`--lane rbd_implicit_baseline`.

This phase does not verify the paper spinning-box experiment, paper-faithful
implicit RBD baseline, paper-faithful affine collision, RK4 or analytic
baselines, paper timing, rendered output, paper trajectory agreement, committed
generated report artifacts, or any passed `experiment.*` claim. The generated
RBD baseline report remains `incomplete`.

## Config Path

- `configs/experiments/single_body_spinning_box.yaml`
- matrix: `configs/experiments/paper_experiment_matrix.yaml`

## Repository

- worktree:
  `/cpfs/user/zhuzihou/dev/mabd-newton/.worktrees/phase15-rbd-baseline-lane`
- branch: `phase15-rbd-baseline-lane`
- base commit: `186d001`
- plan commit: `c5191a9`
- implementation commits: `f075116`, `4564ea1`
- docs/provenance commit: `5fc77d9`
- review hardening commit: `5d7bc28`

## Vendored Newton

- vendored path: `vendor/newton`
- upstream commit: `96713fa965463b69c229a4d30582c733ff3526bb`
- local patch status: Phase 15 adds no vendored Newton source changes.

## Paper Source

- arXiv ID: `2603.08079`
- arXiv version: `v2`
- PDF SHA256:
  `a594e79093673c60fc59ad14f9b71f29a8f7f8e7b1c3d9c73efe6f5814cc6ec0`
- TeX source SHA256:
  `73ec398956c606dec2f8f40f0d38b9d5370e11b27830775e1b3765fe0efc563f`
- cited source lines: `experiment.tex:40-55`

## Environment

- Python: `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python`
- reference clone source:
  `/cpfs/user/zhuzihou/conda-managed/envs/physics-primitive-newton-py310`
- Backend: CPU Newton `SolverSemiImplicit` through vendored Newton/Warp with
  NumPy diagnostics
- readiness check:
  `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/env/readiness_check.py --output reports/generated/environment-readiness/local/readiness.json`
- readiness status: `smoke_passed`
- non-pollution result: `mutates_reference_environment=false`,
  `uses_reference_python=false`, `uses_ambient_python=false`

## Metrics And Thresholds

- random seed: not applicable; free rigid-body baseline is deterministic
- paper values used: `cube_size_m=0.1`, `density=1E3 kg/m^3`,
  `p0=[100, 0, 0]`, `L0=[0, 100, 0]`
- derived rigid properties:
  - `mass_kg=1.0`
  - `inertia_diag_kg_m2=[0.0016666666666666668, 0.0016666666666666668, 0.0016666666666666668]`
  - `linear_velocity_m_s=[100.0, 0.0, 0.0]`
  - `angular_velocity_rad_s=[0.0, 60000.0, 0.0]`
- solver mode: `newton_semimplicit_rbd_cpu_development`
- solver name: `newton.solvers.SolverSemiImplicit`
- Newton step count: `4`
- report metrics: `linear_momentum_error`, `angular_momentum_error`,
  `energy_drift`, `relative_energy_drift`, `step_count`, `time_step_s`,
  `final_position_m`, `final_rotation_xyzw`, `final_linear_velocity_m_s`,
  `final_angular_velocity_rad_s`
- thresholds: `linear_momentum_error <= 1.0e-6`,
  `angular_momentum_error <= 1.0e-3`,
  `relative_energy_drift <= 1.0e-5`
- observed deterministic Newton diagnostics:
  - `linear_momentum_error=2.842170943040401e-14`
  - `angular_momentum_error=5.2083333372365814e-05`
  - `energy_drift=3.1250008158385754`
  - `relative_energy_drift=1.03993371575327e-06`
  - `final_position_m=[4.0, 0.0, 0.0]`
  - `final_rotation_xyzw=[0.0, -0.013332884758710861, 0.0, 0.9999111294746399]`
  - `final_linear_velocity_m_s=[100.0, 0.0, 0.0]`
  - `final_angular_velocity_rad_s=[0.0, 60000.03125, -0.0]`

## Artifacts

- committed baseline implementation:
  `src/mabd_reproduction/rigid_baselines.py`
- committed runner API: `src/mabd_reproduction/experiment_runner.py`
- committed CLI: `scripts/run_experiment.py`
- committed tests: `tests/test_rigid_baselines.py`,
  `tests/test_experiment_runner.py`
- committed matrix blocker:
  `rbd_implicit_baseline_report_incomplete`
- generated reports: not committed; tests write JSON reports to temporary
  directories only
- `run_spinning_box_rbd_baseline` requires explicit `--output` so generated
  baseline artifacts are intentional.
- `scripts/run_experiment.py --lane rbd_implicit_baseline` validates the config
  and matrix before writing an incomplete
  `newton_semimplicit_rbd_cpu_development` report.
- No `experiment.*` claim is passed in this phase.

## TDD Evidence

RED result:

```text
rigid baseline tests: ModuleNotFoundError for mabd_reproduction.rigid_baselines
runner API: ImportError for run_spinning_box_rbd_baseline
runner CLI: unrecognized arguments: --lane rbd_implicit_baseline
docs: Phase 15 boundary and record missing
```

GREEN result:

```text
rigid baseline tests: Ran 3 tests, OK
experiment runner tests: Ran 11 tests, OK
```

Review hardening RED result:

```text
rigid baseline review tests: missing solver fields, bad physical values not rejected, stale solver_mode
experiment matrix review test: stale rbd_implicit_baseline_adapter_missing blocker
runner CLI review test: Warp stdout polluted JSON summary parsing
```

Review hardening GREEN result:

```text
rigid baseline tests: Ran 4 tests, OK
experiment runner tests: Ran 11 tests, OK
experiment run config tests: Ran 8 tests, OK
docs validator: Phase 0/1/2/3/4/5/6/7/8/9/10/11/12/13/14/15 docs/provenance validation passed
```

## Final Verification

Final verification commands:

```bash
/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_rigid_baselines tests.test_experiment_runner tests.test_experiment_run_configs tests.test_experiment_contracts tests.test_phase0_bootstrap
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"
git diff --check
```

Final verification result:

```text
ruff: All checks passed!
docs: Phase 0/1/2/3/4/5/6/7/8/9/10/11/12/13/14/15 docs/provenance validation passed
focused public tests: Ran 53 tests, OK
full public tests: Ran 131 tests, OK
vendored Newton import:
  /cpfs/user/zhuzihou/dev/mabd-newton/.worktrees/phase15-rbd-baseline-lane/vendor/newton/newton/__init__.py
git diff --check: clean
```

## Claim Impact

No `experiment.*` claim is passed in this phase.
