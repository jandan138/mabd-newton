# Phase 74 Rolling Cylinder RBD Baseline

## Status

passed_for_rolling_cylinder_rbd_development_baseline_lane

## Repository

- branch/worktree: `phase68-model-plane-report-lane`
- source commit: `415999bc3dea2becd183a7a21e94066bfdda528c`
- vendored Newton commit: `96713fa965463b69c229a4d30582c733ff3526bb`
- Python: `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python`
- paper source version: `2603.08079v2`
- config path: `configs/experiments/single_body_rolling_spinning.yaml`
- matrix path: `configs/experiments/paper_experiment_matrix.yaml`
- report path:
  `reports/experiment_matrix/single_body_rolling_spinning_rbd_implicit_baseline.json`
- random seed: `not applicable`
- backend: `cpu_newton_warp`

## Scope

Phase 74 adds a Newton CPU development baseline for the rolling-cylinder part of
`experiment.single_body.rolling_spinning`. It builds a procedural cylinder in
vendored Newton, allocates contacts, collides against a ground plane, and steps
the scene through `newton.solvers.SolverSemiImplicit`.

The report status is intentionally incomplete:

- status: `incomplete`
- backend: `cpu_newton_warp`
- solver mode: `newton_semimplicit_rolling_cylinder_rbd_cpu_development`
- baseline lane: `rbd_implicit_baseline`
- solver scope: `newton_development_baseline_not_paper_faithful_implicit_rbd`
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
- `SolverSemiImplicit`

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

- total local wall time: `7107.024885714054 ms`
- timing scope: `local_cpu_wall_clock_not_paper_comparable`
- contact_count_summary: `initial=2`, `final=2`, `min=2`, `max=2`
- min_center_height_m: `0.4314657151699066`
- max_center_penetration_m: `0.06853428483009338`
- no_slip_residual_m_s: `3.814697265625e-06`
- relative_energy_drift: `0.06666557812396937`
- raw_outputs.time_series: `not_written`
- plot_paths: `{}`

Retained blockers:

- `rbd_explicit_baseline_missing`
- `mabd_rolling_cylinder_lane_missing`
- `paper_comparable_timing_missing`
- `newton_semimplicit_not_paper_implicit_rbd_solver`

The report keeps `observed.required_lanes_missing` exactly:

```json
["rbd_explicit_baseline", "mabd_newton", "paper_comparable_timing"]
```

## Report Artifact

- `reports/experiment_matrix/single_body_rolling_spinning_rbd_implicit_baseline.json`
  - sha256:
    `c5a5263f4f98c087b5a689d5f46c59fdb1e7277fed0a105bebdb45fac5244da3`

Result summary:

```json
{"backend": "cpu_newton_warp", "baseline_lane": "rbd_implicit_baseline", "claim_id": "experiment.single_body.rolling_spinning", "paper_comparable": false, "scene_id": "single_body_rolling_spinning", "status": "incomplete"}
```

`docs/reference/reproduction-gap-audit.yaml` now records this implicit RBD
development baseline report as committed incomplete evidence. The overall
rolling/spinning matrix output remains incomplete, and `paper-claims.yaml` keeps
`experiment.single_body.rolling_spinning` at `intended`.

raw artifacts: no videos, run directories, raw logs, or raw paper assets are
committed. The committed artifact is the small JSON report above.

## Commands

TDD red checks:

```bash
PYTHONPATH=src:vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  -m unittest \
  tests.test_experiment_run_configs.ExperimentRunConfigTests.test_rolling_spinning_config_is_machine_checkable \
  tests.test_experiment_run_configs.ExperimentRunConfigTests.test_rolling_spinning_rbd_implicit_baseline_report_path_must_be_lane_specific

PYTHONPATH=src:vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  -m unittest \
  tests.test_experiment_runner.ExperimentRunnerTests.test_run_rolling_spinning_rbd_implicit_baseline_writes_newton_report \
  tests.test_experiment_runner.ExperimentRunnerTests.test_run_experiment_cli_runs_rolling_spinning_rbd_implicit_baseline_lane
```

Observed before implementation: config tests failed because
`config.rbd_implicit_baseline` was absent; runner tests failed because the
`rolling_spinning_rbd_implicit_baseline` runner and CLI lane were absent.

Focused implementation verification:

```bash
PYTHONPATH=src:vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  -m unittest \
  tests.test_experiment_run_configs.ExperimentRunConfigTests.test_rolling_spinning_config_is_machine_checkable \
  tests.test_experiment_run_configs.ExperimentRunConfigTests.test_rolling_spinning_config_matches_matrix \
  tests.test_experiment_run_configs.ExperimentRunConfigTests.test_rolling_spinning_rbd_implicit_baseline_report_path_must_be_lane_specific \
  tests.test_experiment_runner.ExperimentRunnerTests.test_run_rolling_spinning_protocol_writes_configured_report \
  tests.test_experiment_runner.ExperimentRunnerTests.test_run_rolling_spinning_protocol_rejects_ambiguous_output_selection \
  tests.test_experiment_runner.ExperimentRunnerTests.test_run_rolling_spinning_rbd_implicit_baseline_writes_newton_report \
  tests.test_experiment_runner.ExperimentRunnerTests.test_run_experiment_cli_runs_rolling_spinning_rbd_implicit_baseline_lane
```

Observed: `Ran 7 tests`, `OK`.

Report generation:

```bash
PYTHONPATH=src:vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  scripts/run_experiment.py \
  --lane rolling_spinning_rbd_implicit_baseline \
  --config configs/experiments/single_body_rolling_spinning.yaml \
  --matrix configs/experiments/paper_experiment_matrix.yaml \
  --output reports/experiment_matrix/single_body_rolling_spinning_rbd_implicit_baseline.json \
  --source-commit 415999bc3dea2becd183a7a21e94066bfdda528c \
  --vendored-newton-commit 96713fa965463b69c229a4d30582c733ff3526bb
```

Focused static verification:

```bash
PYTHONPATH=src:vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  -m ruff check \
  src/mabd_reproduction/rolling_spinning_reports.py \
  src/mabd_reproduction/experiment_configs.py \
  src/mabd_reproduction/experiment_runner.py \
  scripts/run_experiment.py \
  tests/test_experiment_run_configs.py \
  tests/test_experiment_runner.py

git diff --check
```

Observed: `All checks passed!`; `git diff --check` exited with no output.

Environment isolation fields:

- mutates_reference_environment=false
- uses_reference_python=false
- uses_ambient_python=false

## Claim Boundaries

No `experiment.*` claim is passed.

This record is:

- not a paper-faithful implicit RBD result;
- not an explicit RBD result;
- not an M-ABD rolling-cylinder result;
- not a co-rotated ABD timing result;
- not a same-hardware paper timing result;
- not paper-comparable timing evidence;
- not a completed rolling/spinning reproduction;
- not comparative baseline pass evidence;
- not full paper reproduction.
