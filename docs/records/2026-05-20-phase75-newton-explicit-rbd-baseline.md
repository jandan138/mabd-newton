# Phase 75 Newton Explicit RBD Baseline

## Status

passed_for_rolling_cylinder_explicit_rbd_development_baseline_lane

## Repository

- branch/worktree: `phase68-model-plane-report-lane`
- Newton explicit Euler solver patch commit: `659da60`
- source commit: `a84eb12`
- vendored Newton commit: `96713fa965463b69c229a4d30582c733ff3526bb`
- Python: `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python`
- paper source version: `2603.08079v2`
- config path: `configs/experiments/single_body_rolling_spinning.yaml`
- matrix path: `configs/experiments/paper_experiment_matrix.yaml`
- report path:
  `reports/experiment_matrix/single_body_rolling_spinning_rbd_explicit_baseline.json`
- random seed: `not applicable`
- backend: `cpu_newton_warp`

## Scope

Phase 75 adds a Newton CPU explicit Euler development baseline for the
rolling-cylinder part of `experiment.single_body.rolling_spinning`. It uses a
vendored Newton local patch, `newton.solvers.SolverExplicitEuler`, which reuses
Newton's current-state rigid-body force/contact path and advances the pose from
old velocity before updating velocity.

Local vendored Newton patch files:

- `vendor/newton/newton/_src/solvers/explicit_euler/solver_explicit_euler.py`
- `vendor/newton/newton/_src/solvers/explicit_euler/__init__.py`
- `vendor/newton/newton/_src/solvers/__init__.py`
- `vendor/newton/newton/solvers.py`

The report status is intentionally incomplete:

- status: `incomplete`
- backend: `cpu_newton_warp`
- solver mode: `newton_explicit_euler_rolling_cylinder_rbd_cpu_development`
- baseline lane: `rbd_explicit_baseline`
- solver scope: `newton_development_baseline_not_paper_faithful_explicit_rbd`
- local_runtime_measured=true
- paper_comparable=false
- full_experiment_claim_passed=false

Newton API and execution evidence recorded by the report:

- `newton.ModelBuilder(up_axis="Y", gravity=-9.81)`
- `builder.add_body`
- `ModelBuilder.ShapeConfig`
- `ModelBuilder.add_shape_cylinder`
- `ModelBuilder.add_ground_plane`
- `builder.finalize(device="cpu")`
- `Model.contacts`
- `Model.collide`
- `SolverExplicitEuler`

Configured run:

- radius: `0.5 m`
- half height: `0.5 m`
- density: `1000.0 kg/m^3`
- steps: `10000`
- time step: `0.01 s`
- initial position: `[0.0, 0.5, 0.0]`
- initial linear velocity: `[1.0, 0.0, 0.0]`
- initial angular velocity: `[0.0, 0.0, -2.0]`
- cylinder_axis_world: `[0.0, 0.0, 1.0]`
- contact material: `ke=100000.0`, `kd=1000.0`, `kf=1000.0`, `mu=1.0`,
  `gap=0.02`

Observed report summary:

- total local wall time: `7072.187442332506 ms`
- timing scope: `local_cpu_wall_clock_not_paper_comparable`
- contact_count_summary: `initial=2`, `final=0`, `min=0`, `max=3`
- min_center_height_m: `-3.560969352722168`
- max_center_penetration_m: `4.060969352722168`
- no_slip_residual_m_s: `16.937204360961914`
- relative_energy_drift: `981.1944554514057`
- raw_outputs.time_series: `not_written`
- plot_paths: `{}`

Retained blockers:

- `mabd_rolling_cylinder_lane_missing`
- `paper_comparable_timing_missing`
- `newton_explicit_euler_not_paper_explicit_rbd_solver`

The report keeps `observed.required_lanes_missing` exactly:

```json
["mabd_newton", "paper_comparable_timing"]
```

## Report Artifact

- `reports/experiment_matrix/single_body_rolling_spinning_rbd_explicit_baseline.json`
  - sha256:
    `f4367249a44a22df0a1450e6a49c8389054dad7b95cb3843f3dc3e0f96739633`

Result summary:

```json
{"backend": "cpu_newton_warp", "baseline_lane": "rbd_explicit_baseline", "claim_id": "experiment.single_body.rolling_spinning", "paper_comparable": false, "scene_id": "single_body_rolling_spinning", "status": "incomplete"}
```

`docs/reference/reproduction-gap-audit.yaml` now records this explicit RBD
development baseline report as committed incomplete evidence. The overall
rolling/spinning matrix output remains incomplete, and `paper-claims.yaml` keeps
`experiment.single_body.rolling_spinning` at `intended`.
The gap audit still keeps `paper_faithful_explicit_rbd_baseline` in
`remaining_reproduction_gaps_after_phase75` because this lane is explicitly a
Newton development diagnostic, not the paper's explicit RBD solver.

raw artifacts: no videos, run directories, raw logs, or raw paper assets are
committed. The committed artifact is the small JSON report above.

## Commands

TDD red check for the Newton solver:

```bash
PYTHONPATH=src:vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  -m unittest tests.test_newton_explicit_euler_solver
```

Observed before implementation: failed because
`newton.solvers.SolverExplicitEuler` did not exist.

TDD red checks for the rolling/spinning explicit lane:

```bash
PYTHONPATH=src:vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  -m unittest \
  tests.test_experiment_run_configs.ExperimentRunConfigTests.test_rolling_spinning_config_is_machine_checkable \
  tests.test_experiment_run_configs.ExperimentRunConfigTests.test_rolling_spinning_rbd_explicit_baseline_report_path_must_be_lane_specific \
  tests.test_experiment_runner.ExperimentRunnerTests.test_run_rolling_spinning_rbd_explicit_baseline_writes_newton_report \
  tests.test_experiment_runner.ExperimentRunnerTests.test_run_experiment_cli_runs_rolling_spinning_rbd_explicit_baseline_lane
```

Observed before implementation: config tests failed because
`config.rbd_explicit_baseline` was absent; runner tests failed because the
`run_rolling_spinning_rbd_explicit_baseline` runner and CLI lane were absent.

Focused implementation verification:

```bash
PYTHONPATH=src:vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  -m unittest \
  tests.test_experiment_run_configs.ExperimentRunConfigTests.test_rolling_spinning_config_is_machine_checkable \
  tests.test_experiment_run_configs.ExperimentRunConfigTests.test_rolling_spinning_rbd_explicit_baseline_report_path_must_be_lane_specific \
  tests.test_experiment_runner.ExperimentRunnerTests.test_run_rolling_spinning_rbd_explicit_baseline_writes_newton_report \
  tests.test_experiment_runner.ExperimentRunnerTests.test_run_experiment_cli_runs_rolling_spinning_rbd_explicit_baseline_lane
```

Observed: `Ran 4 tests`, `OK`.

Broader focused verification:

```bash
PYTHONPATH=src:vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  -m unittest tests.test_experiment_run_configs tests.test_experiment_runner
```

Observed: `Ran 147 tests`, `OK`.

Plan Task 5 targeted verification:

```bash
PYTHONPATH=src:vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  -m unittest \
  tests.test_newton_explicit_euler_solver \
  tests.test_experiment_run_configs \
  tests.test_experiment_runner \
  tests.test_phase0_bootstrap
```

Observed: `Ran 330 tests`, `OK`.

Plan Task 5 full test discovery:

```bash
PYTHONPATH=src:vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  -m unittest discover -s tests
```

Observed: `Ran 591 tests`, `OK`.

Plan Task 5 docs/provenance validation:

```bash
PYTHONPATH=src:vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  scripts/validate_docs.py
```

Observed:
`Phase 0/1/2/3/4/5/6/7/8/9/10/11/12/13/14/15/16/17/18/19/20/21/22/23/24/25/26/27/28/29/30/31/32/33/34/35/36/37/38/39/40/41/42/43/44/45/46/47/48/49/50/51/52/53/54/55/56/57/58/59/60/61/62/63/64/65/66/67/68/69/70/71/72/73/74/75 docs/provenance validation passed`.

Plan Task 5 full static verification:

```bash
PYTHONPATH=src:vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  -m ruff check .

git diff --check
```

Observed: `All checks passed!`; `git diff --check` exited with no output.

Report generation:

```bash
PYTHONPATH=src:vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  scripts/run_experiment.py \
  --lane rolling_spinning_rbd_explicit_baseline \
  --config configs/experiments/single_body_rolling_spinning.yaml \
  --matrix configs/experiments/paper_experiment_matrix.yaml \
  --output reports/experiment_matrix/single_body_rolling_spinning_rbd_explicit_baseline.json \
  --source-commit a84eb12 \
  --vendored-newton-commit 96713fa965463b69c229a4d30582c733ff3526bb
```

Observed summary:

```json
{"baseline_lane": "rbd_explicit_baseline", "claim_id": "experiment.single_body.rolling_spinning", "output_report": "reports/experiment_matrix/single_body_rolling_spinning_rbd_explicit_baseline.json", "scene_id": "single_body_rolling_spinning", "status": "incomplete"}
```

Environment isolation fields:

- mutates_reference_environment=false
- uses_reference_python=false
- uses_ambient_python=false
- readiness check: `smoke_passed`
- clone dry-run: `target_exists` with `executed=false`
- sync-existing dry-run: `ready_to_sync_existing` with `executed=false`
- vendored import:
  `/cpfs/user/zhuzihou/dev/mabd-newton/.worktrees/phase68-model-plane-report-lane/vendor/newton/newton/__init__.py`

## Claim Boundaries

No `experiment.*` claim is passed.

This record is:

- not a paper-faithful explicit RBD result;
- not an M-ABD rolling-cylinder result;
- not a co-rotated ABD timing result;
- not a same-hardware paper timing result;
- not paper-comparable timing evidence;
- not a completed rolling/spinning reproduction;
- not comparative baseline pass evidence;
- not full paper reproduction.
