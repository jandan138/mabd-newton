# Phase 76 Rolling Cylinder MABD Newton Lane Design

## Problem

Phase 73-75 made `experiment.single_body.rolling_spinning` auditable at the
protocol, implicit RBD, and explicit RBD development-baseline levels. The
rolling/spinning claim still lacks a committed `mabd_newton` report artifact.
Existing vendored Newton `SolverMABD.detect_static_plane_contacts(...)` only
generates diagnostic contacts for affine boxes against static infinite planes,
so a rolling-cylinder M-ABD lane would otherwise have to be a report-only
placeholder or an affine-box proxy.

This phase adds a bounded Newton-side affine-cylinder static-plane contact
diagnostic and uses it to produce an incomplete `mabd_newton` rolling-cylinder
report. The output is stronger than a placeholder because it exercises
`SolverMABD.step()` through a model-derived M-ABD body, gravity, a procedural
cylinder shape, `SolverMABD.detect_static_plane_contacts(...)`, and Newton
`Contacts` ingestion. It still does not claim paper-faithful M-ABD collision,
friction, contact manifold generation, or paper-comparable timing.

## Scope

- Extend vendored Newton M-ABD static-plane contact detection for M-ABD-owned
  cylinder shapes against static infinite planes.
- Generate contacts from the affine cylinder's support point in the active
  plane-normal direction, not from a generic collision pipeline.
- Add `mabd_newton` config under
  `configs/experiments/single_body_rolling_spinning.yaml`.
- Add a rolling-cylinder M-ABD model-derived rollout using:
  - `ModelBuilder.add_shape_cylinder`;
  - `ModelBuilder.add_ground_plane`;
  - `SolverMABD.register_custom_attributes`;
  - `mabd:body`;
  - `mabd:gravity`;
  - `SolverMABD.detect_static_plane_contacts`;
  - `SolverMABD.step(..., contacts=...)`.
- Write
  `reports/experiment_matrix/single_body_rolling_spinning_mabd_newton.json`
  with `status = incomplete`.
- Update claim boundaries, the gap audit, and docs validation so the new
  report is machine-checkable.
- Keep `experiment.single_body.rolling_spinning` at `intended`.

## Non-Scope

- No pass status for `experiment.single_body.rolling_spinning`.
- No claim that this is the paper's exact M-ABD rolling-cylinder collision or
  contact solver.
- No frictional rolling solve or paper-faithful affine contact manifold.
- No co-rotated ABD timing lane.
- No same-hardware or paper-comparable timing claim.
- No completed rolling/spinning reproduction.
- No full paper reproduction or passed `experiment.*` claim.
- No installation into ambient DSW Python, the reference environment, or the
  shared Newton environment.

## Newton Patch

`vendor/newton/newton/_src/solvers/mabd/solver_mabd.py` currently records
affine box corner candidates and static planes. Phase 76 adds cylinder support:

- identify `GeoType.CYLINDER` shapes attached to Newton bodies mapped by
  `mabd:body_index`;
- for each affine cylinder and static infinite plane, compute the local shape
  direction corresponding to the world plane normal after the current affine map
  and shape transform;
- choose the cylinder support point that minimizes signed distance to the plane;
- emit a Newton `Contacts` row when that support point is penetrating the plane;
- preserve the existing affine-box summary behavior and add explicit cylinder
  summary fields/policy text for the new path.

This remains a diagnostic active-set source. It is intentionally narrower than a
paper-faithful collision pipeline.

## Report Contract

The new report path is:

`reports/experiment_matrix/single_body_rolling_spinning_mabd_newton.json`

The report must include:

- `claim_id = experiment.single_body.rolling_spinning`
- `scene_id = single_body_rolling_spinning`
- `baseline_lane = mabd_newton`
- `solver_mode = mabd_cpu_oracle_rolling_cylinder_newton_lane`
- `backend = cpu_numpy_newton_solver_mabd_static_plane_contacts`
- `status = incomplete`
- `expected.paper_total_simulation_time_ms.vanilla_implicit_abd = 161.0`
- `expected.paper_total_simulation_time_ms.corotated_abd_with_polar = 34.0`
- `expected.paper_total_simulation_time_ms.corotated_abd_without_polar = 27.0`
- `expected.paper_comparable = false`
- `expected.full_experiment_claim_passed = false`
- `observed.local_runtime_measured = true`
- `observed.paper_comparable = false`
- `observed.full_experiment_claim_passed = false`
- `observed.required_lanes_missing = ["paper_comparable_timing"]`
- `observed.blocking_reasons` containing
  `mabd_rolling_cylinder_report_incomplete`,
  `paper_faithful_mabd_collision_missing`,
  `paper_comparable_timing_missing`,
  and `paper_faithful_explicit_rbd_baseline_missing`
- `observed.newton_api` naming `ModelBuilder.add_shape_cylinder`,
  `ModelBuilder.add_ground_plane`,
  `SolverMABD.detect_static_plane_contacts`,
  `SolverMABD.step(..., contacts=...)`, and `mabd:gravity`
- `observed.static_plane_collision_policy =
  mabd_affine_cylinder_static_plane_support_diagnostic`
- `observed.static_plane_collision_scope =
  affine_cylinder_support_points_vs_static_infinite_planes`
- finite step, energy, contact, support-height, affine-shape, and local
  wall-clock diagnostics
- `timing_distribution.paper_comparable = false`
- `raw_outputs.time_series = not_written`
- `plot_paths = {}`

## Acceptance Criteria

- Vendored Newton tests prove `SolverMABD.detect_static_plane_contacts(...)`
  emits a bounded diagnostic contact for an M-ABD-owned cylinder against a
  static infinite plane and preserves the existing box path.
- Config tests load and validate the new `mabd_newton` section and reject unsafe
  or duplicate output paths.
- Runner and CLI tests cover `--lane rolling_spinning_mabd_newton`.
- The committed full-horizon M-ABD report exists and remains incomplete.
- `docs/reference/reproduction-gap-audit.yaml` distinguishes report-artifact
  progress from reproduction gaps:
  - after Phase 76, the missing report artifact list no longer includes
    `mabd_newton`;
  - the reproduction gaps still include paper-faithful explicit RBD,
    paper-faithful M-ABD rolling-cylinder collision/solve, and
    paper-comparable timing.
- `scripts/validate_docs.py` validates the Phase 76 spec, plan, record, report
  SHA256, claim boundaries, and non-passing paper-claim state.
