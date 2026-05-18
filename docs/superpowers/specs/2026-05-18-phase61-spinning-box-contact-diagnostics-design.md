# Phase 61 Spinning-Box Contact Diagnostics Design

## Goal

Phase 61 narrows the spinning-box paper-horizon M-ABD gap by recording contact
penetration and normal-force diagnostics on the current M-ABD trajectory. It
does not add a contact response to the implicit solve and does not pass the
spinning-box paper experiment.

## Scope

The affected lane is `mabd_paper_horizon` for
`configs/experiments/single_body_spinning_box.yaml`, written to:

- `reports/experiment_matrix/single_body_spinning_box_paper_horizon.json`

The report must keep `baseline_lane = mabd_newton`,
`solver_mode = mabd_cpu_oracle_paper_horizon_diagnostic`, and top-level status
`incomplete`.

## Diagnostic Policy

Every paper-horizon state sample evaluates the existing procedural cube-corner
point-plane contact diagnostic from the current M-ABD state. The policy string
is:

- `evaluated_from_current_mabd_states_not_applied_to_step`

This records the policy that diagnostics are not applied to the implicit step:
the diagnostic contact force is observed after each state update as a gap
signal, not a solver pass.

## Report Contract

The paper-horizon report records:

- top-level `contact_diagnostic_policy`;
- top-level `contact_diagnostic_status`;
- `max_contact_active_count`;
- `max_contact_penetration_m`;
- `max_contact_normal_force_n`;
- `max_contact_generalized_force_norm`;
- matching per-step extrema in each `paper_horizon_results` entry;
- per-sample contact scalar fields in compact trajectory samples;
- `spinning_box_contact_response_missing` in `blocking_reasons` when contact
  penetration is observed.

## Claim Boundaries

This is still not a passed spinning-box paper experiment. Phase 61 does not
implement a contact solver, collision detection, paper-faithful affine
collision, a comparison pass gate, rendered output, runtime timing, or a full
paper reproduction. No `experiment.*` claim is passed.

## Testing

Focused tests assert the report records the new contact diagnostic fields,
retains the existing shape/energy/kinematic blockers, and does not expose a
lane pass gate. Validator coverage pins the dated record, claim boundaries,
report hash, provenance, and the Phase 60 audit hash update.

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_single_body_report_lane tests.test_spinning_box_report_artifacts
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
```
