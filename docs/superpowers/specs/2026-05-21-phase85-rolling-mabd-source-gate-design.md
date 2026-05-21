# Phase 85 Rolling MABD Source Gate Design

## Scope

Phase 85 adds a fail-closed source-audit gate for the rolling/spinning
`paper_faithful_mabd_rolling_cylinder` requirement.

The lane is report-only:

- lane: `rolling_spinning_mabd_source_gate`
- report:
  `reports/experiment_matrix/single_body_rolling_spinning_mabd_source_gate.json`
- backend: `paper_source_audit`
- solver mode: `rolling_spinning_mabd_source_gate`

It audits the public paper source for the rolling-cylinder M-ABD affine body,
contact, friction, and collision setup needed before any paper-faithful M-ABD
rolling-cylinder baseline can be claimed.

## Claim Boundary

This phase does not pass `experiment.single_body.rolling_spinning`.

The source gate must remain incomplete unless the public source discloses enough
M-ABD setup to support a paper-faithful rolling-cylinder baseline. Required
source parameters are:

- `rolling_cylinder_geometry`
- `rolling_cylinder_mass_or_density`
- `rolling_cylinder_initial_state`
- `mabd_affine_body_discretization`
- `mabd_rolling_contact_friction_model`
- `mabd_collision_parameters`

The report must keep `paper_faithful_gate_passed = false`,
`paper_comparable = false`, and `full_experiment_claim_passed = false`.

## Report Contract

Required fields:

- `baseline_lane = mabd_source_gate`
- `solver_mode = rolling_spinning_mabd_source_gate`
- `backend = paper_source_audit`
- `status = incomplete`
- `observed.source_audit_status = mabd_source_requirements_incomplete`
- `observed.missing_parameters` lists all six required source parameters
- `observed.blocking_reasons` includes
  `paper_mabd_affine_discretization_missing_from_public_source`
- `observed.blocking_reasons` includes
  `paper_mabd_rolling_contact_friction_missing_from_public_source`
- `observed.blocking_reasons` includes
  `paper_mabd_collision_parameters_missing_from_public_source`
- `timing_distribution.status = not_measured`
- `timing_distribution.scope = source_gate_no_runtime`
- `raw_outputs = {}`
- `plot_paths = {}`

## Acceptance Criteria

- Config validation covers `mabd_source_gate`.
- Runner and CLI tests cover `rolling_spinning_mabd_source_gate`.
- The generated report is machine-checkable, incomplete, and preserves all
  four rolling/spinning reproduction gaps.
- `docs/reference/reproduction-gap-audit.yaml` records the Phase85 report and
  keeps `experiment_claims_passed = 0`.
- No `experiment.*` claim is passed.
