# Phase 89 Spinning-Box Unilateral Contact Gate Candidate Design

## Scope

Phase 89 adds the smallest solver-level improvement after Phase 88: an opt-in
`unilateral_plane` contact mode for the dense CPU `SolverMABD` oracle.

Phase 88 proves that affine static-plane contacts can be detected and consumed,
but those rows are bilateral plane equalities. A stale or separating contact can
therefore behave like an adhesive constraint. Phase 89 keeps the same affine
box/static infinite-plane diagnostic scope, then adds unilateral row handling:

1. contact rows are converted to `MABDCPUOraclePlaneConstraint(unilateral=True)`,
2. the dense solve drops tensile unilateral plane rows,
3. the solve repeats until the active unilateral set is stable,
4. telemetry records requested, accepted, rejected, and skipped unilateral rows.

This is still not a generic paper-faithful contact/collision solver.

## Claim Boundary

The lane remains a fail-closed candidate:

- `status = incomplete`
- `paper_faithful = false`
- `paper_comparable = false`
- `full_experiment_claim_passed = false`
- `comparison_pass_gate_enabled = false`
- no `lane_gate_status`

Phase 89 may claim only that the Newton M-ABD dense CPU oracle has an opt-in
unilateral frictionless static-plane contact diagnostic mode and that the
spinning-box contact/collision gate candidate records it.

Phase 89 must not claim paper-faithful affine contact/collision, finite-plane
clipping, body-body affine contact, friction, restitution, CCD, complementarity
coverage beyond dense active-set row rejection, a passed M-ABD lane, a passed
RBD baseline, paper-comparable timing, a comparison pass gate, or any passed
`experiment.*` claim.

No `experiment.*` claim is passed.

## Solver Contract

`MABDCPUOraclePlaneConstraint` gains `unilateral: bool = False`.

`MABDCPUOracleConfig.contact_constraint_mode` accepts:

- `plane`: existing bilateral diagnostic plane constraints
- `world`: existing sticking diagnostic world constraints
- `unilateral_plane`: opt-in frictionless unilateral diagnostic plane constraints

For `unilateral_plane`, `SolverMABD.step(..., contacts=...)` converts contact
rows into unilateral plane constraints. The dense CPU oracle solves with all
active unilateral rows, rejects rows with tensile multipliers, and re-solves.
Under the current KKT sign convention, compressive upward support has
`dlambda <= 0`.

Existing `plane` and `world` behavior must remain unchanged.

## Report Contract

New lane:

- lane: `spinning_box_contact_collision_gate_candidate`
- report:
  `reports/experiment_matrix/single_body_spinning_box_contact_collision_gate_candidate.json`
- backend: `cpu_newton_solver_mabd_unilateral_static_plane_contact_gate_candidate`
- solver mode: `solver_mabd_unilateral_static_plane_contact_gate_candidate`

Required observed fields:

- `candidate_status = contact_collision_gate_candidate_recorded`
- `gate_scope = single_body_spinning_box_contact_collision_candidate`
- `contact_constraint_mode = unilateral_plane`
- `unilateral_contact_policy = dense_cpu_active_set_drop_tensile_plane_rows`
- `paper_faithful = false`
- `paper_comparable = false`
- `full_experiment_claim_passed = false`
- `comparison_pass_gate_enabled = false`
- `phase88_rollout_candidate_report`
- `phase88_rollout_candidate_sha256`
- `max_unilateral_plane_requested_count`
- `max_unilateral_plane_accepted_count`
- `max_unilateral_plane_rejected_count`
- `max_unilateral_plane_skipped_count`
- penetration, residual, contact count, energy, momentum, and compact trajectory
  telemetry over 10 seconds
- blocking reasons include
  `unilateral_static_plane_contact_not_paper_faithful` and
  `paper_faithful_affine_collision_missing`

## Acceptance Criteria

- Unit tests prove stale/separating unilateral plane rows are rejected and match
  the unconstrained step.
- Unit tests prove penetrating unilateral plane rows enforce nonpenetration and
  use compressive multipliers.
- `SolverMABD.step(..., contacts=...)` supports `contact_constraint_mode =
  unilateral_plane` without changing existing `plane` and `world` tests.
- The Phase89 report is committed, machine-checkable, incomplete, and
  fail-closed.
- Claim boundaries, gap audit, docs validator, and bootstrap tests keep all
  `experiment.*` claims unpassed.
