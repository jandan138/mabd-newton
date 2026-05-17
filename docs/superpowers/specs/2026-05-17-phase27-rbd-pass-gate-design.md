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
reports. Phase 27 keeps that default safety behavior. The new gate records that
one required lane has passed without changing the top-level experiment report
status:

- `expected["lane_pass_gate"]`
- `observed["lane_pass_gate"]`
- `observed["lane_gate_status"] = "passed"`

For Phase 27, the gate scope is `required_lane_only`, the baseline lane is
`rbd_implicit_baseline`, `solver_mode` is `paper_faithful_implicit_rbd`,
`backend` is `cpu_numpy_newton_only`, and
`full_experiment_claim_passed` must be `false`. The report itself remains
`status=incomplete` with a failure reason naming the missing M-ABD and
comparison gates. Consumers must read `observed["lane_gate_status"]` to see the
passed lane evidence and must not treat it as a passed paper experiment claim.

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

- tests proving passed `experiment.*` reports remain rejected, even when lane
  gate fields are present;
- tests proving the incomplete RBD lane-gate report is accepted and
  machine-readable;
- tests proving the RBD lane report has `status=incomplete`,
  `observed["lane_gate_status"]="passed"`,
  `solver_mode=paper_faithful_implicit_rbd`,
  `backend=cpu_numpy_newton_only`, and finite metrics within strict
  thresholds;
- tests proving the closed-form orientation path records the expected xyzw
  quaternion, unit norm, and per-sample time and position values;
- tests proving the comparison report consumes the passed RBD lane while still
  remaining `incomplete` because the M-ABD lane and comparison gate are not
  passed;
- updated claim boundaries, docs validator, and Phase 27 record with config
  path, repo commit, vendored Newton provenance, paper source version, backend,
  seed policy, raw artifact paths, gate status, and explicit non-claims.
