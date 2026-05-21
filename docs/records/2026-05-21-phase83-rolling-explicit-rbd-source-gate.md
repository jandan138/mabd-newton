# Phase 83 Rolling Explicit RBD Source Gate

## Status

incomplete_explicit_rbd_source_gate_recorded

## Scope

Phase 83 records a fail-closed public-source audit gate for the
`paper_faithful_explicit_rbd_baseline` requirement in
`experiment.single_body.rolling_spinning`.

This lane is report-only:

- lane: `rolling_spinning_rbd_explicit_source_gate`
- report:
  `reports/experiment_matrix/single_body_rolling_spinning_rbd_explicit_source_gate.json`
- report sha256:
  `eb43b537e4bb92f1684a0b451efe924222819e4b1283c20f472326da2ae98c78`
- source commit: `bcb6202`
- vendored Newton commit: `96713fa965463b69c229a4d30582c733ff3526bb`
- paper source version: `2603.08079v2`
- Python: `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python`
- backend: `paper_source_audit`
- solver mode: `rolling_spinning_explicit_rbd_source_gate`
- status = incomplete
- source_audit_status = explicit_rbd_source_requirements_incomplete
- paper_faithful_gate_passed = false
- paper_comparable = false
- full_experiment_claim_passed = false

The report runs no solver and records no runtime measurement:

- timing_distribution.status = not_measured
- timing_distribution.scope = source_gate_no_runtime
- timing_distribution.paper_comparable = false

## Source Parameters Missing

The public paper source contains the rolling-cylinder timing context but does
not provide the explicit RBD setup required for a paper-faithful baseline:

- `rolling_cylinder_geometry`
- `rolling_cylinder_mass_or_density`
- `rolling_cylinder_initial_state`
- `rolling_cylinder_contact_friction_model`
- `explicit_rbd_integrator_details`
- `explicit_rbd_collision_parameters`

The source audit records these blockers:

- `rolling_cylinder_geometry_parameters_missing_from_public_source`
- `rolling_cylinder_initial_state_missing_from_public_source`
- `rolling_cylinder_contact_friction_model_missing_from_public_source`
- `paper_explicit_rbd_solver_details_missing_from_public_source`
- `paper_explicit_rbd_collision_parameters_missing_from_public_source`
- `paper_faithful_explicit_rbd_baseline_missing`
- `paper_faithful_implicit_rbd_baseline_missing`
- `paper_faithful_mabd_collision_missing`
- `paper_comparable_timing_missing`

This phase does not prove paper-faithful explicit RBD, paper-faithful implicit
RBD, paper-faithful M-ABD rolling-cylinder contact/friction,
paper-comparable timing, same-hardware paper timing, comparative baseline pass,
or any passed `experiment.*` claim.

No experiment.* claim is passed.
No `experiment.*` claim is passed; there is no evidence for any passed
`experiment.*` claim.

## Environment Isolation

- mutates_reference_environment=false
- uses_reference_python=false
- uses_ambient_python=false
- canonical environment:
  `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310`
- reference environment:
  `/cpfs/user/zhuzihou/conda-managed/envs/physics-primitive-newton-py310`

## Commands

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_paper_source_audit.PaperSourceAuditTests.test_rolling_spinning_explicit_rbd_source_audit_is_fail_closed tests.test_paper_source_audit.PaperSourceAuditTests.test_rolling_spinning_explicit_rbd_source_disclosure_triggers_manual_review tests.test_experiment_run_configs.ExperimentRunConfigTests.test_rolling_spinning_rbd_explicit_source_gate_is_fail_closed tests.test_experiment_runner.ExperimentRunnerTests.test_run_rolling_spinning_rbd_explicit_source_gate_writes_report tests.test_experiment_runner.ExperimentRunnerTests.test_run_experiment_cli_runs_rolling_spinning_rbd_explicit_source_gate_lane
```

Initial result: failed with missing
`rolling_spinning_explicit_rbd_source_audit`, missing
`rbd_explicit_source_gate`, missing
`run_rolling_spinning_rbd_explicit_source_gate`, and missing CLI lane
`rolling_spinning_rbd_explicit_source_gate`.

Final targeted result: all five target tests passed.

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/run_experiment.py --lane rolling_spinning_rbd_explicit_source_gate --config configs/experiments/single_body_rolling_spinning.yaml --matrix configs/experiments/paper_experiment_matrix.yaml --source-commit bcb6202 --vendored-newton-commit 96713fa965463b69c229a4d30582c733ff3526bb
```

Result:

```json
{"baseline_lane": "rbd_explicit_source_gate", "claim_id": "experiment.single_body.rolling_spinning", "output_report": "reports/experiment_matrix/single_body_rolling_spinning_rbd_explicit_source_gate.json", "scene_id": "single_body_rolling_spinning", "status": "incomplete"}
```

```bash
sha256sum reports/experiment_matrix/single_body_rolling_spinning_rbd_explicit_source_gate.json
```

Result:

```text
eb43b537e4bb92f1684a0b451efe924222819e4b1283c20f472326da2ae98c78  reports/experiment_matrix/single_body_rolling_spinning_rbd_explicit_source_gate.json
```
