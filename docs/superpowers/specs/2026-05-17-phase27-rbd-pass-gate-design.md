# Phase 27 RBD Pass Gate Design

Date: 2026-05-17

## Objective

Phase 27 removes the `rbd_implicit_baseline_report_incomplete` blocker from the
single-body spinning-box path by adding a dedicated lane-level pass gate for a
Newton-only, paper-scoped implicit RBD baseline. It does not pass the full
`experiment.single_body.spinning_box` paper claim.

## Current Gap

`experiment.single_body.spinning_box` still has two matrix blockers:

- `rbd_implicit_baseline_report_incomplete`
- `spinning_box_comparison_report_incomplete`

The current RBD report is a Newton `SolverSemiImplicit` development baseline.
It records correct paper values and finite diagnostics, but its report status is
`incomplete` and its solver mode is not `paper_faithful_implicit_rbd`. The
comparison protocol therefore always reports the RBD lane as incomplete and
adds `rbd_implicit_baseline_not_paper_faithful`.

## Design

Phase 27 adds a separate paper-scoped RBD baseline path for the spinning-box
cube. For this single scene, the body is a uniform cube with isotropic inertia,
zero gravity, no active contact force, and no torque. The implicit RBD velocity
solve is therefore constant over the configured four 10 ms steps. Position is
advanced by the configured linear velocity, and orientation is advanced with a
closed-form quaternion exponential from the constant angular velocity.

This path is Newton-only in project scope: it lives in the reproduction harness
and uses NumPy plus the vendored Newton coordinate conventions. It is not an
external RBD engine adapter, and it is not a generic RBD baseline for other
paper scenes.

## Report Gate

The existing report validator rejects `status=passed` for `experiment.*`
reports. Phase 27 keeps that default safety behavior unless the report carries
a dedicated experiment pass-gate payload:

- `expected["experiment_pass_gate"]`
- `observed["experiment_pass_gate"]`

For Phase 27, the gate scope is `required_lane_only`, the baseline lane is
`rbd_implicit_baseline`, and `full_experiment_claim_passed` must be `false`.
The gate allows a lane report to use `status=passed` while preserving the
project-wide rule that the full paper experiment claim remains unpassed until
the M-ABD lane and comparison report also pass their gates.

## Config And Matrix Impact

The spinning-box config no longer lists `rbd_implicit_baseline` under
`required_missing_lanes`. The experiment matrix removes
`rbd_implicit_baseline_report_incomplete` and keeps
`spinning_box_comparison_report_incomplete`. It also records
`mabd_newton_report_incomplete`, because the M-ABD lane is still a development
lane with non-passing diagnostics.

`paper-claims.yaml` remains unchanged for `experiment.single_body.spinning_box`;
its `reproduction_status` stays `intended`.

## Non-Goals

Phase 27 does not:

- pass `experiment.single_body.spinning_box`;
- pass any `experiment.*` entry in `paper-claims.yaml`;
- pass the spinning-box comparison report;
- make the M-ABD lane pass;
- implement paper-faithful affine collision, contact, gravity, friction, or
  rendered trajectory agreement;
- implement a general implicit RBD baseline for other scenes;
- implement external MuJoCo, Bullet, PhysX, VQ, RK4, or analytic baseline lanes;
- claim paper timing.

## Evidence

Evidence must include:

- tests proving default passed `experiment.*` reports remain rejected without a
  pass gate;
- tests proving the RBD pass-gate report is accepted and machine-readable;
- tests proving the RBD lane report has `status=passed`,
  `solver_mode=paper_faithful_implicit_rbd`, and finite metrics within
  thresholds;
- tests proving the comparison report consumes the passed RBD lane while still
  remaining `incomplete` because the M-ABD lane and comparison gate are not
  passed;
- updated claim boundaries, docs validator, and Phase 27 record.

