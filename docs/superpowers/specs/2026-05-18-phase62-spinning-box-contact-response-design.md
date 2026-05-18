# Phase 62 Spinning-Box Contact Response Design

## Purpose

Phase 62 adds a Newton-only diagnostic lane that applies the existing
spinning-box point-plane penalty contact generalized force through the CPU M-ABD
oracle `external_forces` input. This narrows the Phase 61 gap from "contact
diagnostics are only observed" to "an explicit contact response diagnostic was
run and recorded".

This is not a contact solver, not collision detection, not a paper-faithful
affine contact implementation, and not a passed spinning-box paper experiment.

## Approach

Create a separate report artifact:

`reports/experiment_matrix/single_body_spinning_box_contact_response.json`

The existing Phase 61 paper-horizon report remains the no-response diagnostic
baseline with:

`contact_diagnostic_policy = evaluated_from_current_mabd_states_not_applied_to_step`

The new Phase 62 report uses:

`contact_response_policy = explicit_current_state_penalty_force_as_external_force_next_step`

At each step, the lane evaluates `spinning_box_contact_diagnostics(config, q,
qd)` from the current M-ABD state, passes `total_generalized_force` into
`mabd.MABDCPUOracleConfig(external_forces=[...])`, advances one CPU oracle step,
and records post-step contact/shape/energy metrics. This is an explicit,
state-lagged diagnostic response. It does not solve an implicit contact KKT and
does not claim paper faithfulness.

## Report Contract

The report records:

- paper-horizon duration and step-size grid;
- source line and figure provenance inherited from the spinning-box config;
- no-response vs explicit-response maximum penetration comparison;
- response per-step-size summaries under `contact_response_results`;
- per-summary `contact_response_policy`;
- applied contact-force extrema;
- retained blockers and `status = incomplete`.

The expected blocker set includes:

- `mabd_newton_report_incomplete`;
- `mabd_paper_horizon_diagnostic_thresholds_violated`;
- `mabd_kinematic_feasibility_blocker_recorded`;
- `spinning_box_contact_response_not_paper_faithful`;
- `spinning_box_comparison_pass_gate_not_enabled`.

If the explicit response increases or fails to reduce penetration, the report
also records `contact_response_does_not_reduce_penetration`.

## Runner Contract

Add `spinning_box_contact_response` to `scripts/run_experiment.py`. Like the
existing `mabd_paper_horizon` lane, it requires `--output` and rejects
`--output-root`; the configured report path is recorded in
`paper_horizon.contact_response_output_report` for provenance and validator
checks.

## Validation

Focused tests must prove:

- the config exposes `contact_response_output_report`;
- the report is machine-checkable and incomplete;
- the report records the explicit response policy and applied force extrema;
- the report compares against the no-response diagnostic without mutating the
  Phase 61 artifact;
- the CLI runner dispatches the new lane;
- claim boundaries forbid describing Phase 62 as a solver, collision
  implementation, paper-faithful affine contact, or experiment pass.

## Claim Boundaries

Phase 62 verifies only that the current Newton-only CPU oracle can consume the
existing diagnostic contact generalized force through `external_forces` in a
paper-horizon spinning-box diagnostic report. It does not verify a passed
`experiment.*` claim, full paper reproduction, contact solve, collision
detection, friction, rendered output, runtime timing, or comparative baseline
agreement.
