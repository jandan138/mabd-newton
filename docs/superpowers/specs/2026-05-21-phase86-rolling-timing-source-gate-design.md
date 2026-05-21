# Phase 86 Rolling Timing Source Gate Design

## Scope

Phase 86 adds a fail-closed source/runtime audit gate for the rolling/spinning
`paper_comparable_timing` requirement.

The lane is report-only:

- lane: `rolling_spinning_timing_source_gate`
- report:
  `reports/experiment_matrix/single_body_rolling_spinning_timing_source_gate.json`
- backend: `paper_source_audit`
- solver mode: `rolling_spinning_timing_source_gate`

It audits the public paper source for timing details beyond the reported table
values and ties the result to the current incomplete timing protocol plus the
three paper-faithful source gates.

## Claim Boundary

This phase does not pass `experiment.single_body.rolling_spinning`.

The timing source gate must remain incomplete unless the source and local
records disclose enough to support paper-comparable timing. Required source or
runtime parameters are:

- `exact_cpu_model`
- `single_thread_enforcement`
- `compiler_and_blas_configuration`
- `timing_repetition_or_warmup_policy`
- `paper_faithful_lane_runtime_inputs`
- `measurement_timer_scope`

The report must keep `paper_timing_gate_passed = false`,
`paper_comparable = false`, and `full_experiment_claim_passed = false`.

## Report Contract

Required fields:

- `baseline_lane = timing_source_gate`
- `solver_mode = rolling_spinning_timing_source_gate`
- `backend = paper_source_audit`
- `status = incomplete`
- `observed.source_audit_status = timing_source_requirements_incomplete`
- `observed.missing_parameters` lists all six required timing parameters
- `observed.blocking_reasons` includes
  `paper_timing_exact_cpu_model_missing_from_public_source`
- `observed.blocking_reasons` includes
  `paper_timing_measurement_protocol_missing_from_public_source`
- `observed.current_evidence_reports` references the timing protocol, explicit
  RBD source gate, implicit RBD source gate, and M-ABD source gate reports
- `timing_distribution.status = not_measured`
- `timing_distribution.scope = source_gate_no_runtime`
- `raw_outputs = {}`
- `plot_paths = {}`

## Acceptance Criteria

- Config validation covers `timing_source_gate`.
- Runner and CLI tests cover `rolling_spinning_timing_source_gate`.
- The generated report is machine-checkable, incomplete, and preserves all
  four rolling/spinning reproduction gaps.
- `docs/reference/reproduction-gap-audit.yaml` records the Phase86 report and
  keeps `experiment_claims_passed = 0`.
- No `experiment.*` claim is passed.
