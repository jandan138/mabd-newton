# Phase 74 Rolling Cylinder RBD Baseline Design

## Problem

Phase 73 made `experiment.single_body.rolling_spinning` auditable, but only as a
protocol report. The rolling-cylinder performance claim is still blocked because
there is no local Newton run for the rigid rolling cylinder and no RBD baseline
adapter evidence.

The paper source requires a rolling cylinder benchmark over 10K steps at
`h = 0.01 sec`, with reported total simulation times for implicit RBD, explicit
RBD, vanilla implicit ABD, and co-rotated ABD variants. A local reproduction lane
must first prove that Newton can build, collide, and step the procedural cylinder
scene in an isolated environment before any paper-comparable timing or pass gate
can be claimed.

## Scope

- Add a Newton-only `rolling_spinning_rbd_implicit_baseline` runner lane.
- Extend `configs/experiments/single_body_rolling_spinning.yaml` with an
  `rbd_implicit_baseline` section for a procedural rolling cylinder.
- Build the scene with vendored Newton:
  `newton.ModelBuilder(up_axis="Y", gravity=-9.81)`,
  `builder.add_body`, `ModelBuilder.ShapeConfig`, `add_shape_cylinder`,
  `add_ground_plane`, `model.contacts`, `model.collide`, and
  `newton.solvers.SolverSemiImplicit`.
- Pin Newton execution to CPU with `builder.finalize(device="cpu")`.
- Run the configured 10K steps on CPU and record the measured wall-clock runtime
  as local non-comparable timing evidence.
- Record initial/final pose, velocity, contact count summary, kinetic/potential
  energy drift, no-slip residual, and trajectory samples.
- Keep the report `status = incomplete`.
- Keep `experiment.single_body.rolling_spinning` at `intended`.
- Keep the post-Phase74 report `observed.required_lanes_missing` exactly
  `["rbd_explicit_baseline", "mabd_newton", "paper_comparable_timing"]`.
- Update validation so the committed report proves a real Newton cylinder
  baseline was executed while still blocking the full paper claim.

## Non-Scope

- No explicit RBD baseline.
- No M-ABD rolling-cylinder lane.
- No co-rotated ABD timing lane.
- No same-hardware paper timing claim.
- No claim that Newton SemiImplicit is the paper's exact implicit RBD solver.
- No claim that this lane fulfills the paper-faithful implicit RBD baseline; it
  is a Newton development baseline until a paper-faithful RBD adapter and pass
  gate are added.
- No claim that the local wall-clock timing is paper comparable.
- No pass status for `experiment.single_body.rolling_spinning`.
- No full paper reproduction claim.
- No package installation or mutation of the reference/shared environments.

## Architecture

`RollingSpinningRunConfig` gains a nested `RollingSpinningRBDBaselineConfig`
with these fields:

- `output_report`
- `radius_m`
- `half_height_m`
- `density_kg_m3`
- `time_step_s`
- `step_count`
- `sample_count`
- `initial_position_m`
- `initial_linear_velocity_m_s`
- `initial_angular_velocity_rad_s`
- `gravity_m_s2`
- `contact`
- `thresholds`

`src/mabd_reproduction/rolling_spinning_reports.py` owns the new scene
construction and report writer:

- compute solid-cylinder mass and inertia in NumPy for report metrics;
- build the same geometry in vendored Newton with the configured density and
  shape contact material;
- create the cylinder by first adding a body, then calling
  `builder.add_shape_cylinder(body, ..., cfg=ModelBuilder.ShapeConfig(...))`;
- keep the body orientation at identity so Newton's cylinder local Z axis is the
  world Z axis and the no-slip diagnostic `v_x + omega_z * radius` is
  well-defined;
- initialize the cylinder center at `y = radius` on a Y-up plane, with
  no-slip-compatible `omega_z = -v_x / radius`;
- allocate contacts with `model.contacts()` before `model.collide(...)`;
- run `model.collide(state, contacts)` before every solver step;
- call `SolverSemiImplicit(..., angular_damping=0.0)`;
- collect samples at deterministic step indices;
- write a `ClaimReport` with
  `solver_mode = newton_semimplicit_rolling_cylinder_rbd_cpu_development`,
  `backend = cpu_newton_warp`, `baseline_lane = rbd_implicit_baseline`, and
  `status = incomplete`.

The existing protocol report remains available as
`rolling_spinning_protocol`. The new baseline report is a separate file under
`reports/experiment_matrix/` so the Phase 73 artifact hash stays auditable.
The configured `rbd_implicit_baseline.output_report` must be relative, must stay
under `reports/experiment_matrix/`, must end in `.json`, must be distinct from
the Phase 73 protocol report, and must equal
`reports/experiment_matrix/single_body_rolling_spinning_rbd_implicit_baseline.json`.

## Report Contract

The new report path is:

`reports/experiment_matrix/single_body_rolling_spinning_rbd_implicit_baseline.json`

The report must include:

- `claim_id = experiment.single_body.rolling_spinning`
- `scene_id = single_body_rolling_spinning`
- `baseline_lane = rbd_implicit_baseline`
- `solver_mode = newton_semimplicit_rolling_cylinder_rbd_cpu_development`
- `backend = cpu_newton_warp`
- `status = incomplete`
- `failure_reason` states that explicit RBD, M-ABD rolling-cylinder, and
  paper-comparable timing evidence remain missing
- `asset_hashes.primitive_cylinder = not_applicable_procedural`
- `unit = json_report`
- top-level `threshold` entries matching
  `config.rbd_implicit_baseline.thresholds`
- `expected.paper_total_simulation_time_ms.implicit_rbd = 44.0`
- `expected.paper_hardware_context = i7 CPU, single thread`
- `expected.paper_comparable = false`
- `expected.full_experiment_claim_passed = false`
- `expected.source_lines` matching the rolling/spinning config
- `expected.config_path =
  configs/experiments/single_body_rolling_spinning.yaml`
- `expected.canonical_python =
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python`
- `observed.local_runtime_measured = true`
- `observed.paper_comparable = false`
- `observed.full_experiment_claim_passed = false`
- `observed.required_lanes_missing` exactly
  `["rbd_explicit_baseline", "mabd_newton", "paper_comparable_timing"]`
- `observed.blocking_reasons` containing
  `rbd_explicit_baseline_missing`, `mabd_rolling_cylinder_lane_missing`,
  `paper_comparable_timing_missing`, and
  `newton_semimplicit_not_paper_implicit_rbd_solver`
- `observed.newton_api` naming `ModelBuilder.add_shape_cylinder`,
  `ModelBuilder.add_ground_plane`, `Model.contacts`, `Model.collide`, and
  `SolverSemiImplicit`
- `observed.newton_device = cpu`
- `observed.cylinder_axis_world = [0.0, 0.0, 1.0]`
- `observed.contact_material` matching config `ke`, `kd`, `kf`, `mu`, and `gap`
- `observed.step_count = 10000`
- `observed.time_step_s = 0.01`
- `observed.contact_count_summary` with finite integer `initial`, `final`,
  `min`, and `max` fields
- `observed.contact_count_summary.max >= 1`
- `observed.min_center_height_m` and `observed.max_center_penetration_m`
  recorded from the cylinder center height relative to `radius_m`
- `observed.no_slip_residual_m_s` recorded from
  `v_x + omega_z * radius`
- `timing_distribution.total_wall_time_ms` recorded locally
- `timing_distribution.paper_comparable = false`
- `raw_outputs.time_series = not_written`
- `plot_paths = {}`
- top-level `source_commit`, `vendored_newton_commit`, and
  `paper_source_version`

## Acceptance Criteria

- Config tests load the new `rbd_implicit_baseline` section and reject invalid
  report paths, absolute paths, paths outside `reports/experiment_matrix/`, path
  reuse with the Phase 73 protocol report, or non-positive geometry/step values.
- Report-writer unit tests can run a short temporary config and verify that a
  real Newton cylinder scene produces contacts and a nonzero local runtime.
- Runner and CLI tests cover
  `--lane rolling_spinning_rbd_implicit_baseline`.
- The committed full-horizon report exists at the configured path.
- `scripts/validate_docs.py` validates the Phase 74 spec, plan, record, report
  SHA256, report schema fields, source/vendored commits, paper source version,
  and non-passing claim boundaries.
- `docs/reference/claim-boundaries.md` adds Phase 74 bullets for current claim,
  verified evidence, non-claims, and forbidden interpretations. Phase 74 must
  not be described as a paper-comparable timing result, explicit RBD result,
  M-ABD rolling-cylinder result, or completed rolling/spinning experiment.
- `docs/reference/reproduction-gap-audit.yaml` records that the implicit RBD
  baseline lane exists but the overall rolling/spinning experiment remains
  incomplete because explicit RBD, M-ABD rolling-cylinder, and paper-comparable
  timing are still missing.
