# Phase 23 Spinning-Box Position Comparison Design

Date: 2026-05-17

## Scope

Phase 23 extends the existing single-body spinning-box comparison protocol with
machine-checkable position fields. Phase 21 aligned the M-ABD lane initial pose
with the plane, and Phase 22 aligned the RBD development lane initial pose with
the same config. Phase 23 makes that alignment visible at the comparison-report
level.

This phase does not pass the paper spinning-box experiment. It does not make
the RBD lane paper-faithful, does not add collision detection, does not add a
contact solve, and does not create paper timing or trajectory-agreement claims.

## Design

The M-ABD development report already advances the configured 12-DOF affine
state for four 10 ms steps. Phase 23 reports the translational slice
`q[9:12]` before and after stepping:

- `initial_position_m = [0.0, 0.05, 0.0]`;
- `final_position_m = [4.0, 0.05, 0.0]`.

The comparison protocol then treats `initial_position_m` and
`final_position_m` as vector comparison metrics in addition to the existing
scalar momentum and energy metrics. Vector metrics are valid only when present,
finite, and length three. The report records per-lane vector snapshots and
`mabd_newton_minus_rbd_implicit_baseline` vector differences.

## Evidence Boundary

Phase 23 verifies report-level position propagation and finite vector
comparison for the existing development lanes. It does not verify collision,
post-contact clearance, long-horizon paper trajectory agreement, rendered
output, paper timing, paper-faithful implicit RBD, or any passed
`experiment.*` claim.
