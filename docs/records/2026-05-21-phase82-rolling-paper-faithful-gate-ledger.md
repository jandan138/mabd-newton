# Phase 82 Rolling Paper-Faithful Gate Ledger

## Status

incomplete_paper_faithful_gate_ledger_recorded

## Scope

Phase 82 records a fail-closed paper-faithful gate ledger for
`experiment.single_body.rolling_spinning`.

This lane is a report-only ledger:

- lane: `rolling_spinning_paper_faithful_gate_ledger`
- report:
  `reports/experiment_matrix/single_body_rolling_spinning_paper_faithful_gate_ledger.json`
- report sha256:
  `76d4b5df92570ed6bedff2f902bd7e757de2cc3effaad41d72ba9d9ae1255a7d`
- source commit: `cf4e6ba`
- vendored Newton commit: `96713fa965463b69c229a4d30582c733ff3526bb`
- paper source version: `2603.08079v2`
- Python: `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python`
- backend: `report_gate_ledger`
- solver mode: `rolling_spinning_paper_faithful_gate_ledger`
- status = incomplete
- gate_ledger_status = fail_closed_requirements_recorded
- paper_comparable = false
- full_experiment_claim_passed = false

The report runs no solver and records no runtime measurement:

- timing_distribution.status = not_measured
- timing_distribution.scope = gate_ledger_no_runtime
- timing_distribution.paper_comparable = false

## Required Gates

The ledger requires all of these gates to pass before any rolling/spinning
experiment pass claim:

- `paper_faithful_explicit_rbd_baseline`
- `paper_faithful_implicit_rbd_baseline`
- `paper_faithful_mabd_rolling_cylinder`
- `paper_comparable_timing`

All four gates are recorded with:

- status = missing_paper_faithful_evidence
- paper_faithful_gate_passed = false
- required_status = passed

The current incomplete evidence reports are linked as context only:

- `rbd_explicit_no_slip_candidate`:
  `reports/experiment_matrix/single_body_rolling_spinning_rbd_explicit_no_slip_candidate.json`
- `rbd_implicit_development`:
  `reports/experiment_matrix/single_body_rolling_spinning_rbd_implicit_baseline.json`
- `mabd_rolling_contact_candidate`:
  `reports/experiment_matrix/single_body_rolling_spinning_mabd_rolling_contact_candidate.json`
- `timing_protocol`:
  `reports/experiment_matrix/single_body_rolling_spinning_timing_protocol.json`

## Blocking Reasons

The report intentionally keeps these blockers:

- `rolling_spinning_paper_faithful_gate_ledger_not_pass_gate`
- `paper_faithful_explicit_rbd_baseline_missing`
- `paper_faithful_implicit_rbd_baseline_missing`
- `paper_faithful_mabd_collision_missing`
- `paper_comparable_timing_missing`

It preserves the living gap-audit vocabulary:

- `paper_faithful_explicit_rbd_baseline`
- `paper_faithful_implicit_rbd_baseline`
- `paper_faithful_mabd_rolling_cylinder`
- `paper_comparable_timing`

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
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_run_configs.ExperimentRunConfigTests.test_rolling_spinning_paper_faithful_gate_ledger_is_fail_closed tests.test_experiment_runner.ExperimentRunnerTests.test_run_rolling_spinning_paper_faithful_gate_ledger_writes_report tests.test_experiment_runner.ExperimentRunnerTests.test_run_experiment_cli_runs_rolling_spinning_paper_faithful_gate_ledger_lane
```

Initial result: failed with missing `paper_faithful_gate_ledger` config,
missing `run_rolling_spinning_paper_faithful_gate_ledger`, and missing CLI lane
`rolling_spinning_paper_faithful_gate_ledger`.

Final result: `Ran 3 tests in 8.106s OK`.

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/run_experiment.py --lane rolling_spinning_paper_faithful_gate_ledger --config configs/experiments/single_body_rolling_spinning.yaml --matrix configs/experiments/paper_experiment_matrix.yaml --source-commit cf4e6ba --vendored-newton-commit 96713fa965463b69c229a4d30582c733ff3526bb
```

Result:

```json
{"baseline_lane": "paper_faithful_gate_ledger", "claim_id": "experiment.single_body.rolling_spinning", "output_report": "reports/experiment_matrix/single_body_rolling_spinning_paper_faithful_gate_ledger.json", "scene_id": "single_body_rolling_spinning", "status": "incomplete"}
```

```bash
sha256sum reports/experiment_matrix/single_body_rolling_spinning_paper_faithful_gate_ledger.json
```

Result:

```text
76d4b5df92570ed6bedff2f902bd7e757de2cc3effaad41d72ba9d9ae1255a7d  reports/experiment_matrix/single_body_rolling_spinning_paper_faithful_gate_ledger.json
```
