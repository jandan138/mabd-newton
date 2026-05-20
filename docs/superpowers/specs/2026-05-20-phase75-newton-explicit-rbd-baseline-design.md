# Phase 75 Newton Explicit RBD Baseline Design

## Problem

Phase 74 added a real Newton CPU rolling-cylinder rigid-body development
baseline, but `experiment.single_body.rolling_spinning` still lists
`rbd_explicit_baseline` as a missing lane. Vendored Newton exposes
`SolverSemiImplicit`, `SolverXPBD`, `SolverFeatherstone`, and other solvers, but
does not expose a simple maximal-coordinate explicit Euler rigid-body solver
that can serve as an auditable Newton-only explicit RBD development baseline.

The paper reports `explicit_rbd = 32.0 ms` for the 10K rolling-cylinder timing
table. This phase creates a Newton-only local explicit Euler development lane
that can run the same procedural rolling-cylinder scene and record the same
evidence surface as Phase 74, while explicitly preserving the claim boundary
that this is not a paper-faithful explicit RBD result.

## Scope

- Add a vendored Newton `newton.solvers.SolverExplicitEuler` class for rigid
  bodies.
- Keep upstream Newton notices intact and make the local patch auditable through
  Phase 75 tests and records.
- Implement explicit rigid-body integration semantics:
  - evaluate forces/contact forces at the current state;
  - update position/orientation from current velocity;
  - update velocity/angular velocity from current forces/torques;
  - keep angular gyroscopic handling consistent with the existing Newton
    semi-implicit rigid-body force path, except that pose advancement uses the
    old velocity.
- Reuse Phase 74 rolling-cylinder scene construction, contact allocation, and
  sampling for a new `rbd_explicit_baseline` lane.
- Add `rbd_explicit_baseline` config under
  `configs/experiments/single_body_rolling_spinning.yaml`.
- Write
  `reports/experiment_matrix/single_body_rolling_spinning_rbd_explicit_baseline.json`
  with `status = incomplete`.
- Keep `experiment.single_body.rolling_spinning` at `intended`.

## Non-Scope

- No claim that `SolverExplicitEuler` is the paper's exact explicit RBD solver.
- No paper-comparable timing claim.
- No M-ABD rolling-cylinder lane.
- No co-rotated ABD timing lane.
- No completed rolling/spinning reproduction claim.
- No passed `experiment.*` claim.
- No package installation or mutation of reference/shared environments.

## Newton Patch

Add a new package under vendored Newton:

- `vendor/newton/newton/_src/solvers/explicit_euler/__init__.py`
- `vendor/newton/newton/_src/solvers/explicit_euler/solver_explicit_euler.py`

Export it from:

- `vendor/newton/newton/_src/solvers/__init__.py`
- `vendor/newton/newton/solvers.py`

`SolverExplicitEuler` is intentionally small and rigid-body focused. It mirrors
the force evaluation order of `SolverSemiImplicit`, including body joint,
contact, and particle-body contact force calls, then launches an explicit rigid
body integration kernel. Particle integration remains unsupported for this
solver and raises `NotImplementedError` if particles are present.

## Report Contract

The new report path is:

`reports/experiment_matrix/single_body_rolling_spinning_rbd_explicit_baseline.json`

The report must include:

- `claim_id = experiment.single_body.rolling_spinning`
- `scene_id = single_body_rolling_spinning`
- `baseline_lane = rbd_explicit_baseline`
- `solver_mode = newton_explicit_euler_rolling_cylinder_rbd_cpu_development`
- `backend = cpu_newton_warp`
- `status = incomplete`
- `expected.paper_total_simulation_time_ms.explicit_rbd = 32.0`
- `expected.paper_comparable = false`
- `expected.full_experiment_claim_passed = false`
- `observed.local_runtime_measured = true`
- `observed.paper_comparable = false`
- `observed.full_experiment_claim_passed = false`
- `observed.required_lanes_missing` exactly
  `["mabd_newton", "paper_comparable_timing"]`
- `observed.blocking_reasons` containing
  `mabd_rolling_cylinder_lane_missing`,
  `paper_comparable_timing_missing`, and
  `newton_explicit_euler_not_paper_explicit_rbd_solver`
- `observed.newton_api` naming `ModelBuilder.add_shape_cylinder`,
  `ModelBuilder.add_ground_plane`, `Model.contacts`, `Model.collide`, and
  `SolverExplicitEuler`
- `observed.newton_device = cpu`
- `observed.cylinder_axis_world = [0.0, 0.0, 1.0]`
- `observed.contact_material` matching config
- `observed.step_count = 10000`
- `observed.time_step_s = 0.01`
- finite contact count, center penetration, no-slip residual, and local wall
  time diagnostics
- `timing_distribution.paper_comparable = false`
- `raw_outputs.time_series = not_written`
- `plot_paths = {}`

## Acceptance Criteria

- Unit tests prove `newton.solvers.SolverExplicitEuler` is public and advances a
  gravity-only rigid body with explicit Euler pose semantics.
- Config tests load and validate `rbd_explicit_baseline`, including path
  distinctness from the Phase 73 protocol and Phase 74 implicit baseline
  reports.
- Runner and CLI tests cover
  `--lane rolling_spinning_rbd_explicit_baseline`.
- The committed full-horizon explicit report exists and remains incomplete.
- `scripts/validate_docs.py` validates the Phase 75 spec, plan, record, report
  SHA256, vendored Newton patch provenance, and non-passing claim boundaries.
