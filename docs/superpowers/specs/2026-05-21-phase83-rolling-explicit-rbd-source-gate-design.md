# Phase 83 Rolling Explicit RBD Source Gate Design

## Scope

Phase 83 adds a fail-closed source-audit gate for the rolling/spinning
`paper_faithful_explicit_rbd_baseline` requirement.

The lane is report-only:

- lane: `rolling_spinning_rbd_explicit_source_gate`
- report:
  `reports/experiment_matrix/single_body_rolling_spinning_rbd_explicit_source_gate.json`
- backend: `paper_source_audit`
- solver mode: `rolling_spinning_explicit_rbd_source_gate`

It audits the public paper source for the rolling-cylinder explicit RBD details
needed before any paper-faithful explicit RBD baseline can be claimed.

## Claim Boundary

This phase does not pass `experiment.single_body.rolling_spinning`.

The source gate must remain incomplete unless the public source discloses enough
explicit RBD setup to support a paper-faithful baseline. Required source
parameters are:

- `rolling_cylinder_geometry`
- `rolling_cylinder_mass_or_density`
- `rolling_cylinder_initial_state`
- `rolling_cylinder_contact_friction_model`
- `explicit_rbd_integrator_details`
- `explicit_rbd_collision_parameters`

The report must keep `paper_faithful_gate_passed = false`,
`paper_comparable = false`, and `full_experiment_claim_passed = false`.

## Report Contract

Required fields:

- `baseline_lane = rbd_explicit_source_gate`
- `solver_mode = rolling_spinning_explicit_rbd_source_gate`
- `backend = paper_source_audit`
- `status = incomplete`
- `observed.source_audit_status = explicit_rbd_source_requirements_incomplete`
- `observed.missing_parameters` lists all six required source parameters
- `observed.blocking_reasons` includes
  `paper_explicit_rbd_solver_details_missing_from_public_source`
- `timing_distribution.status = not_measured`
- `timing_distribution.scope = source_gate_no_runtime`
- `raw_outputs = {}`
- `plot_paths = {}`

## Acceptance Criteria

- Config validation covers `rbd_explicit_source_gate`.
- Runner and CLI tests cover
  `rolling_spinning_rbd_explicit_source_gate`.
- The generated report is machine-checkable, incomplete, and preserves all
  four rolling/spinning reproduction gaps.
- `docs/reference/reproduction-gap-audit.yaml` records the Phase83 report and
  keeps `experiment_claims_passed = 0`.
- No `experiment.*` claim is passed.
