# Phase 22 RBD Plane Placement Design

Date: 2026-05-17

## Scope

Phase 22 aligns the Newton `rbd_implicit_baseline` development lane with the
configured single-body spinning-box initial pose introduced for the M-ABD lane.
The RBD baseline must initialize the rigid cube center from
`config.initial_q[9:12]`, so the cube starts at `[0.0, 0.05, 0.0]` on the
frictionless plane instead of at the origin.

This phase does not make the RBD lane paper-faithful. It remains a
Newton `SolverSemiImplicit` free-body development baseline with no contact
solve, no collision detection, no gravity, no long-horizon paper comparison,
no timing claim, and no passed `experiment.*` claim.

## Design

The RBD baseline already derives mass, inertia, velocity, momentum, and energy
from the shared spinning-box paper-value helpers. Phase 22 adds the missing
configuration coupling for the rigid initial translation:

- derive `initial_position_m = config.initial_q[9:12]`;
- pass that value to `newton.ModelBuilder.add_body(xform=...)`;
- expose `initial_position_m` in `SpinningBoxRBDBaselineResult` and the JSON
  report;
- update tests to require final position `[4.0, 0.05, 0.0]` after four
  10 ms steps at `100 m/s`.

The orientation remains identity because the configured affine block is
identity at the initial state, and the existing RBD lane does not reconstruct
orientation from a non-rigid affine block.

## Evidence Boundary

Phase 22 verifies only that the RBD development baseline consumes the same
configured initial translation as the M-ABD development lane and reports that
translation. It does not verify paper-faithful implicit RBD, paper-faithful
affine collision/contact, post-step plane clearance, rendered trajectories,
paper timing, or comparative pass/fail evidence. The comparison report remains
`incomplete`.
