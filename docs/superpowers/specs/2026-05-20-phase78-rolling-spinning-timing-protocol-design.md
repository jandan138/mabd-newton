# Phase 78 Rolling/Spinning Timing Protocol Design

## Scope

Phase 78 adds a fail-closed timing protocol artifact for
`experiment.single_body.rolling_spinning`.

The artifact records the paper timing table for the rolling-cylinder benchmark
and cross-references the committed Newton-only local timing reports already
produced for the protocol, implicit RBD, explicit RBD, M-ABD diagnostic, and
finite-stiffness M-ABD material preflight lanes.

## Claim Boundary

This phase does not pass `experiment.single_body.rolling_spinning`.

The paper timing caption states a 10K step rolling-cylinder benchmark with
`h = 0.01 sec`, total wall times of `161 ms`, `44 ms`, `32 ms`, `34 ms`, and
`27 ms`, and an i7 CPU single-thread hardware context. The current environment
is not that paper hardware/protocol. Local timings may be useful diagnostics,
but they are not paper-comparable performance evidence.

The report must keep these blockers visible:

- `paper_comparable_timing_missing`
- `paper_hardware_mismatch`
- `paper_single_thread_protocol_not_enforced`
- `paper_faithful_mabd_collision_missing`
- `paper_faithful_explicit_rbd_baseline_missing`
- `paper_faithful_implicit_rbd_baseline_missing`

## Config Contract

`configs/experiments/single_body_rolling_spinning.yaml` gets a
`paper_timing_protocol` section with output report:

```text
reports/experiment_matrix/single_body_rolling_spinning_timing_protocol.json
```

The section lists required input reports:

- `reports/experiment_matrix/single_body_rolling_spinning.json`
- `reports/experiment_matrix/single_body_rolling_spinning_rbd_implicit_baseline.json`
- `reports/experiment_matrix/single_body_rolling_spinning_rbd_explicit_baseline.json`
- `reports/experiment_matrix/single_body_rolling_spinning_mabd_newton.json`
- `reports/experiment_matrix/single_body_rolling_spinning_mabd_material_preflight.json`

## Report Contract

The timing protocol report must include:

- `claim_id = experiment.single_body.rolling_spinning`
- `scene_id = single_body_rolling_spinning`
- `baseline_lane = paper_timing_protocol`
- `solver_mode = rolling_spinning_paper_timing_protocol_audit`
- `backend = report_protocol`
- `status = incomplete`
- `expected.paper_total_simulation_time_ms` copied from the paper source
- `expected.paper_hardware_context = i7 CPU, single thread`
- `expected.paper_comparable = true`
- `observed.paper_comparable = false`
- `observed.full_experiment_claim_passed = false`
- `observed.local_environment_python` set to the canonical cloned environment
- `observed.input_reports` with each input report path, status, baseline lane,
  solver mode, `paper_comparable` flag, and any local wall time
- `timing_distribution.paper_comparable = false`
- `raw_outputs = {}`
- `plot_paths = {}`

## Acceptance Criteria

- Config tests load and validate `paper_timing_protocol`.
- Runner and CLI tests cover `rolling_spinning_paper_timing_protocol`.
- `scripts/validate_docs.py` validates the spec, plan, record, report, and
  fail-closed audit updates.
- Gap audit no longer lists the timing protocol report as a missing artifact,
  but still lists `paper_comparable_timing` as a reproduction gap.
