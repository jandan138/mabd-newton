# Phase 76 Rolling Cylinder MABD Newton Diagnostic

## Status

passed_for_rolling_cylinder_mabd_newton_diagnostic_lane

## Repository

- branch/worktree: `phase68-model-plane-report-lane`
- source commit: `83e103a26bbfbb84190e21d9e5ad74787d0391e0`
- vendored Newton commit: `96713fa965463b69c229a4d30582c733ff3526bb`
- Python: `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python`
- paper source version: `2603.08079v2`
- config path: `configs/experiments/single_body_rolling_spinning.yaml`
- matrix path: `configs/experiments/paper_experiment_matrix.yaml`
- report path:
  `reports/experiment_matrix/single_body_rolling_spinning_mabd_newton.json`
- random seed: `not applicable`
- backend: `cpu_numpy_newton_solver_mabd_static_plane_contacts`

## Scope

Phase 76 adds a Newton-first `SolverMABD` diagnostic lane for the rolling
cylinder part of `experiment.single_body.rolling_spinning`. It extends
vendored Newton's bounded static-plane diagnostic contact path from affine box
corners to affine-cylinder support points against static infinite planes, then
uses that path through `SolverMABD.detect_static_plane_contacts` and
`SolverMABD.step`.

The report status is intentionally incomplete:

- status: `incomplete`
- backend: `cpu_numpy_newton_solver_mabd_static_plane_contacts`
- solver mode: `mabd_cpu_oracle_rolling_cylinder_newton_lane`
- baseline lane: `mabd_newton`
- solver scope: `mabd_affine_cylinder_static_plane_diagnostic_not_paper_faithful`
- local_runtime_measured=true
- paper_comparable=false
- full_experiment_claim_passed=false

Newton API and execution evidence recorded by the report:

- `newton.ModelBuilder(up_axis="Y", gravity=-9.81)`
- `builder.add_body`
- `SolverMABD.register_custom_attributes`
- `ModelBuilder.add_shape_cylinder`
- `ModelBuilder.add_ground_plane`
- `builder.finalize(device="cpu")`
- `SolverMABD.detect_static_plane_contacts`
- `SolverMABD.step`

Configured run:

- radius: `0.5 m`
- half height: `0.5 m`
- density: `1000.0 kg/m^3`
- steps: `10000`
- time step: `0.01 s`
- initial position: `[0.0, 0.5, 0.0]`
- initial linear velocity: `[1.0, 0.0, 0.0]`
- initial angular velocity: `[0.0, 0.0, -2.0]`
- rotation mode: `polar`

Observed report summary:

- lane_status: `incomplete_diagnostic_failed`
- timing scope: `local_cpu_wall_clock_not_paper_comparable`
- contact_count_summary: `initial=0`, `final=1`, `min=0`, `max=1`
- static_plane_collision_policy:
  `mabd_affine_cylinder_static_plane_support_diagnostic`
- static_plane_collision_scope:
  `affine_cylinder_support_points_vs_static_infinite_planes`
- static_plane_cylinder_shape_count: `1`
- max_support_penetration_m: `0.0059669688740227045`
- no_slip_residual_m_s: `0.9924336082562791`
- max_affine_shape_spread_m: `199.00593485274297`
- max_constraint_residual_norm: `1.1102230246308297e-16`
- threshold_violations:
  `["max_no_slip_residual_m_s", "max_affine_shape_spread_m", "max_runtime_wall_time_ms"]`
- raw_outputs.time_series: `not_written`
- plot_paths: `{}`

Retained blockers:

- `mabd_rolling_cylinder_report_incomplete`
- `paper_faithful_mabd_collision_missing`
- `paper_faithful_explicit_rbd_baseline_missing`
- `paper_comparable_timing_missing`

The report keeps `observed.required_lanes_missing` exactly:

```json
["paper_comparable_timing"]
```

## Report Artifact

- `reports/experiment_matrix/single_body_rolling_spinning_mabd_newton.json`
  - sha256:
    `12dd1d7452ebefed43f40893095affd60ddca419262f5b7e58e542794a33a2fe`

Result summary:

```json
{"backend": "cpu_numpy_newton_solver_mabd_static_plane_contacts", "baseline_lane": "mabd_newton", "claim_id": "experiment.single_body.rolling_spinning", "paper_comparable": false, "scene_id": "single_body_rolling_spinning", "status": "incomplete"}
```

`docs/reference/reproduction-gap-audit.yaml` now records this M-ABD Newton
development diagnostic report as committed incomplete evidence. The overall
rolling/spinning matrix output remains incomplete, and `paper-claims.yaml` keeps
`experiment.single_body.rolling_spinning` at `intended`.
The gap audit keeps `paper_faithful_mabd_rolling_cylinder`,
`paper_faithful_explicit_rbd_baseline`, and `paper_comparable_timing` in
`remaining_reproduction_gaps_after_phase76` because this lane is explicitly a
diagnostic, not a paper-faithful M-ABD rolling-cylinder solve.

raw artifacts: no videos, run directories, raw logs, or raw paper assets are
committed. The committed artifact is the small JSON report above.

## Commands

TDD red checks for the M-ABD rolling/spinning lane:

```bash
PYTHONPATH=src:vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  -m unittest \
  tests.test_experiment_run_configs.ExperimentRunConfigTests.test_rolling_spinning_config_is_machine_checkable \
  tests.test_experiment_runner.ExperimentRunnerTests.test_run_rolling_spinning_mabd_newton_writes_diagnostic_report \
  tests.test_experiment_runner.ExperimentRunnerTests.test_run_experiment_cli_runs_rolling_spinning_mabd_newton_lane
```

Observed before implementation: config test failed because
`config.mabd_newton` was absent; runner test failed because
`run_rolling_spinning_mabd_newton` was absent; CLI helper failed because the
YAML had no `mabd_newton` section.

Focused implementation verification:

```bash
PYTHONPATH=src:vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  -m unittest \
  tests.test_experiment_run_configs.ExperimentRunConfigTests.test_rolling_spinning_config_is_machine_checkable \
  tests.test_experiment_runner.ExperimentRunnerTests.test_run_rolling_spinning_mabd_newton_writes_diagnostic_report \
  tests.test_experiment_runner.ExperimentRunnerTests.test_run_experiment_cli_runs_rolling_spinning_mabd_newton_lane
```

Observed: `Ran 3 tests`, `OK`.

Rolling/spinning regression verification:

```bash
PYTHONPATH=src:vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  -m unittest \
  tests.test_experiment_run_configs.ExperimentRunConfigTests.test_rolling_spinning_config_is_machine_checkable \
  tests.test_experiment_run_configs.ExperimentRunConfigTests.test_rolling_spinning_config_matches_matrix \
  tests.test_experiment_runner.ExperimentRunnerTests.test_run_rolling_spinning_protocol_writes_configured_report \
  tests.test_experiment_runner.ExperimentRunnerTests.test_run_rolling_spinning_rbd_implicit_baseline_writes_newton_report \
  tests.test_experiment_runner.ExperimentRunnerTests.test_run_rolling_spinning_rbd_explicit_baseline_writes_newton_report \
  tests.test_experiment_runner.ExperimentRunnerTests.test_run_rolling_spinning_mabd_newton_writes_diagnostic_report \
  tests.test_experiment_runner.ExperimentRunnerTests.test_run_experiment_cli_runs_rolling_spinning_protocol_lane \
  tests.test_experiment_runner.ExperimentRunnerTests.test_run_experiment_cli_runs_rolling_spinning_rbd_implicit_baseline_lane \
  tests.test_experiment_runner.ExperimentRunnerTests.test_run_experiment_cli_runs_rolling_spinning_rbd_explicit_baseline_lane \
  tests.test_experiment_runner.ExperimentRunnerTests.test_run_experiment_cli_runs_rolling_spinning_mabd_newton_lane
```

Observed: `Ran 10 tests`, `OK`.

Full test discovery:

```bash
PYTHONPATH=src:vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  -m unittest discover -s tests
```

Observed: `Ran 597 tests`, `OK`.

Docs/provenance validation:

```bash
PYTHONPATH=src:vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  scripts/validate_docs.py
```

Observed:
`Phase 0/1/2/3/4/5/6/7/8/9/10/11/12/13/14/15/16/17/18/19/20/21/22/23/24/25/26/27/28/29/30/31/32/33/34/35/36/37/38/39/40/41/42/43/44/45/46/47/48/49/50/51/52/53/54/55/56/57/58/59/60/61/62/63/64/65/66/67/68/69/70/71/72/73/74/75/76 docs/provenance validation passed`.

Static and whitespace verification:

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
  --lane rolling_spinning_mabd_newton \
  --config configs/experiments/single_body_rolling_spinning.yaml \
  --matrix configs/experiments/paper_experiment_matrix.yaml \
  --source-commit 83e103a26bbfbb84190e21d9e5ad74787d0391e0 \
  --vendored-newton-commit 96713fa965463b69c229a4d30582c733ff3526bb
```

Observed:
`{"baseline_lane": "mabd_newton", "claim_id": "experiment.single_body.rolling_spinning", "output_report": "reports/experiment_matrix/single_body_rolling_spinning_mabd_newton.json", "scene_id": "single_body_rolling_spinning", "status": "incomplete"}`.

## Environment Isolation

- cloned env used:
  `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python`
- reference env not mutated:
  `/cpfs/user/zhuzihou/conda-managed/envs/physics-primitive-newton-py310`
- mutates_reference_environment=false
- uses_reference_python=false
- uses_ambient_python=false

## Claim Boundary

No `experiment.*` claim is passed. This evidence is a Newton `SolverMABD`
rolling-cylinder diagnostic with a bounded affine-cylinder static-plane contact
path. It is not a paper-faithful M-ABD rolling-cylinder collision/friction
solve, not paper-comparable timing, not a paper-faithful explicit RBD baseline,
and not a completed rolling/spinning reproduction.
