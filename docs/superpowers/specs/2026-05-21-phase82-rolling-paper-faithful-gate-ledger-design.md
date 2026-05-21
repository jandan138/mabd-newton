# Phase 82 Rolling Paper-Faithful Gate Ledger Design

## Scope

Phase 82 adds a fail-closed rolling/spinning paper-faithful gate ledger lane for
`experiment.single_body.rolling_spinning`:

```text
paper_faithful_gate_ledger
```

The lane does not run a solver and does not change Newton behavior. It records
the paper-faithful gates that must all pass before the rolling/spinning
experiment claim can pass, then links the current non-passing evidence reports
for each gate.

## Claim Boundary

This phase does not pass `experiment.single_body.rolling_spinning`.

The ledger is intentionally fail-closed. It records that all required gates
remain missing:

- `paper_faithful_explicit_rbd_baseline`
- `paper_faithful_implicit_rbd_baseline`
- `paper_faithful_mabd_rolling_cylinder`
- `paper_comparable_timing`

Each gate must have `paper_faithful_gate_passed = false` and
`status = missing_paper_faithful_evidence`. The ledger itself is not a pass
gate, not a solver result, and not paper-comparable timing.

The report must keep these blockers visible:

- `rolling_spinning_paper_faithful_gate_ledger_not_pass_gate`
- `paper_faithful_explicit_rbd_baseline_missing`
- `paper_faithful_implicit_rbd_baseline_missing`
- `paper_faithful_mabd_collision_missing`
- `paper_comparable_timing_missing`

## Config Contract

`configs/experiments/single_body_rolling_spinning.yaml` gets:

```yaml
paper_faithful_gate_ledger:
  output_report: reports/experiment_matrix/single_body_rolling_spinning_paper_faithful_gate_ledger.json
  required_gates:
    - paper_faithful_explicit_rbd_baseline
    - paper_faithful_implicit_rbd_baseline
    - paper_faithful_mabd_rolling_cylinder
    - paper_comparable_timing
  current_evidence_reports:
    rbd_explicit_no_slip_candidate: reports/experiment_matrix/single_body_rolling_spinning_rbd_explicit_no_slip_candidate.json
    rbd_implicit_development: reports/experiment_matrix/single_body_rolling_spinning_rbd_implicit_baseline.json
    mabd_rolling_contact_candidate: reports/experiment_matrix/single_body_rolling_spinning_mabd_rolling_contact_candidate.json
    timing_protocol: reports/experiment_matrix/single_body_rolling_spinning_timing_protocol.json
```

Validation must enforce the lane-specific report path, the exact four required
gates, the four current evidence report keys, and no changes to the top-level
`required_missing_lanes`.

## Report Contract

Report path:

```text
reports/experiment_matrix/single_body_rolling_spinning_paper_faithful_gate_ledger.json
```

Required report fields:

- `baseline_lane = paper_faithful_gate_ledger`
- `solver_mode = rolling_spinning_paper_faithful_gate_ledger`
- `backend = report_gate_ledger`
- `status = incomplete`
- `expected.required_gates` equals the exact four required gates
- `expected.required_gate_status = passed`
- `expected.paper_comparable = false`
- `expected.full_experiment_claim_passed = false`
- `observed.gate_ledger_status = fail_closed_requirements_recorded`
- `observed.paper_comparable = false`
- `observed.full_experiment_claim_passed = false`
- `observed.required_reproduction_gaps_remaining` preserves all four gate names
- each `observed.gate_statuses.*.status = missing_paper_faithful_evidence`
- each `observed.gate_statuses.*.paper_faithful_gate_passed = false`
- `timing_distribution.status = not_measured`
- `timing_distribution.scope = gate_ledger_no_runtime`
- `timing_distribution.paper_comparable = false`
- `raw_outputs = {}`
- `plot_paths = {}`

## Acceptance Criteria

- Config tests load and validate `paper_faithful_gate_ledger`.
- Runner and CLI tests cover
  `rolling_spinning_paper_faithful_gate_ledger`.
- The generated report is machine-checkable, incomplete, and preserves all
  rolling/spinning reproduction gaps.
- `docs/reference/reproduction-gap-audit.yaml` records the Phase82 report and
  keeps `experiment_claims_passed = 0`.
- `scripts/validate_docs.py` validates the Phase82 spec, plan, record, report,
  report hash, gap audit, and claim-boundary text.
- No `experiment.*` claim is passed.
