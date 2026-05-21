# Phase 82 Rolling Paper-Faithful Gate Ledger Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a fail-closed rolling/spinning paper-faithful gate ledger lane that records the exact missing gates before any rolling/spinning pass claim.

**Architecture:** Extend the rolling/spinning config with a `paper_faithful_gate_ledger` section, then add a report-only runner and CLI lane. The report links current incomplete evidence reports and records every required paper-faithful gate as missing, with no solver execution and no experiment claim pass.

**Tech Stack:** Python 3.10, `unittest`, PyYAML, existing `ClaimReport`, canonical `mabd-newton-py310` environment.

No `experiment.*` claim is passed by this phase.

---

### Task 1: Gate Ledger Config Contract

**Files:**
- Modify: `src/mabd_reproduction/experiment_configs.py`
- Modify: `configs/experiments/single_body_rolling_spinning.yaml`
- Test: `tests/test_experiment_run_configs.py`

- [ ] **Step 1: Write the failing config test**

Add `test_rolling_spinning_paper_faithful_gate_ledger_is_fail_closed`.
It must load `single_body_rolling_spinning.yaml` and assert:

```python
lane = config.paper_faithful_gate_ledger
self.assertEqual(
    lane.output_report,
    "reports/experiment_matrix/single_body_rolling_spinning_paper_faithful_gate_ledger.json",
)
self.assertEqual(
    lane.required_gates,
    (
        "paper_faithful_explicit_rbd_baseline",
        "paper_faithful_implicit_rbd_baseline",
        "paper_faithful_mabd_rolling_cylinder",
        "paper_comparable_timing",
    ),
)
self.assertEqual(
    lane.current_evidence_reports["mabd_rolling_contact_candidate"],
    "reports/experiment_matrix/single_body_rolling_spinning_mabd_rolling_contact_candidate.json",
)
self.assertEqual(config.required_missing_lanes, ("rbd_implicit_baseline", "rbd_explicit_baseline"))
```

- [ ] **Step 2: Run the test and verify it fails**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_run_configs.ExperimentRunConfigTests.test_rolling_spinning_paper_faithful_gate_ledger_is_fail_closed
```

Expected: fail because `RollingSpinningRunConfig` has no
`paper_faithful_gate_ledger` field.

- [ ] **Step 3: Implement minimal config support**

Add `RollingSpinningPaperFaithfulGateLedgerConfig` with `output_report`,
`required_gates`, and `current_evidence_reports`. Parse the new YAML section and
validate the exact report path, four gate names, and four evidence report keys.

- [ ] **Step 4: Run config tests**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_run_configs.ExperimentRunConfigTests.test_rolling_spinning_paper_faithful_gate_ledger_is_fail_closed
```

Expected: pass.

### Task 2: Gate Ledger Runner And CLI

**Files:**
- Modify: `src/mabd_reproduction/rolling_spinning_reports.py`
- Modify: `src/mabd_reproduction/experiment_runner.py`
- Modify: `scripts/run_experiment.py`
- Test: `tests/test_experiment_runner.py`

- [ ] **Step 1: Write the failing runner tests**

Add tests for `run_rolling_spinning_paper_faithful_gate_ledger` and the CLI lane
`rolling_spinning_paper_faithful_gate_ledger`. The report test must assert:

```python
self.assertEqual(loaded.baseline_lane, "paper_faithful_gate_ledger")
self.assertEqual(loaded.solver_mode, "rolling_spinning_paper_faithful_gate_ledger")
self.assertEqual(loaded.backend, "report_gate_ledger")
self.assertEqual(loaded.status.value, "incomplete")
self.assertEqual(loaded.observed["gate_ledger_status"], "fail_closed_requirements_recorded")
self.assertFalse(loaded.observed["paper_comparable"])
self.assertFalse(loaded.observed["full_experiment_claim_passed"])
for gate in loaded.expected["required_gates"]:
    self.assertFalse(loaded.observed["gate_statuses"][gate]["paper_faithful_gate_passed"])
    self.assertEqual(
        loaded.observed["gate_statuses"][gate]["status"],
        "missing_paper_faithful_evidence",
    )
```

- [ ] **Step 2: Run the tests and verify they fail**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_runner.ExperimentRunnerTests.test_run_rolling_spinning_paper_faithful_gate_ledger_writes_report tests.test_experiment_runner.ExperimentRunnerTests.test_run_experiment_cli_runs_rolling_spinning_paper_faithful_gate_ledger_lane
```

Expected: fail because the runner and CLI lane do not exist.

- [ ] **Step 3: Implement report-only execution**

Add `write_rolling_spinning_paper_faithful_gate_ledger_report(...)` and
`run_rolling_spinning_paper_faithful_gate_ledger(...)`. The report must use:

```python
baseline_lane="paper_faithful_gate_ledger"
solver_mode="rolling_spinning_paper_faithful_gate_ledger"
backend="report_gate_ledger"
status=EvidenceStatus.INCOMPLETE
observed["gate_ledger_status"] = "fail_closed_requirements_recorded"
timing_distribution = {
    "status": "not_measured",
    "scope": "gate_ledger_no_runtime",
    "paper_comparable": False,
}
```

- [ ] **Step 4: Add CLI dispatch and rerun target tests**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_run_configs.ExperimentRunConfigTests.test_rolling_spinning_paper_faithful_gate_ledger_is_fail_closed tests.test_experiment_runner.ExperimentRunnerTests.test_run_rolling_spinning_paper_faithful_gate_ledger_writes_report tests.test_experiment_runner.ExperimentRunnerTests.test_run_experiment_cli_runs_rolling_spinning_paper_faithful_gate_ledger_lane
```

Expected: all three tests pass.

### Task 3: Evidence, Claim Boundaries, And Validation

**Files:**
- Add: `reports/experiment_matrix/single_body_rolling_spinning_paper_faithful_gate_ledger.json`
- Add: `docs/records/2026-05-21-phase82-rolling-paper-faithful-gate-ledger.md`
- Modify: `docs/reference/claim-boundaries.md`
- Modify: `docs/reference/reproduction-gap-audit.yaml`
- Modify: `scripts/validate_docs.py`
- Test: `tests/test_phase0_bootstrap.py`

- [ ] **Step 1: Generate the gate ledger report**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/run_experiment.py --lane rolling_spinning_paper_faithful_gate_ledger --config configs/experiments/single_body_rolling_spinning.yaml --matrix configs/experiments/paper_experiment_matrix.yaml --source-commit cf4e6ba --vendored-newton-commit 96713fa965463b69c229a4d30582c733ff3526bb
```

Record the report SHA256:

```text
76d4b5df92570ed6bedff2f902bd7e757de2cc3effaad41d72ba9d9ae1255a7d
```

- [ ] **Step 2: Update docs and gap audit**

Add Phase82 claim-boundary bullets, record the report and SHA in the living gap
audit, add `remaining_reproduction_gaps_after_phase82` with the exact four gap
names, and keep `No experiment.* claim is passed.`

- [ ] **Step 3: Add docs validation and bootstrap tests**

Add `validate_phase82_record()` to `scripts/validate_docs.py`, then add
bootstrap tests that call it and verify report fields, claim boundaries, gap
audit fields, and required evidence snippets.

- [ ] **Step 4: Run validation**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"
git diff --check
```

Expected: all commands pass, and the import path resolves to this worktree's
`vendor/newton/newton/__init__.py`.
