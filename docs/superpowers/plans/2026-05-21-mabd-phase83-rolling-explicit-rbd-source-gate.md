# Phase 83 Rolling Explicit RBD Source Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> superpowers:subagent-driven-development (recommended) or
> superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a fail-closed source-audit gate for the rolling/spinning
paper-faithful explicit RBD baseline.

**Architecture:** Extend the rolling/spinning config with
`rbd_explicit_source_gate`, add a public-paper-source audit, and expose a
report-only runner and CLI lane. The report records missing source parameters
and keeps the explicit RBD paper-faithful gate unpassed.

No `experiment.*` claim is passed by this phase.

---

### Task 1: Source Audit Contract

**Files:**
- Modify: `src/mabd_reproduction/paper_source_audit.py`
- Test: `tests/test_paper_source_audit.py`

- [ ] Add failing tests for
  `rolling_spinning_explicit_rbd_source_audit`.
- [ ] Verify RED: import/function missing.
- [ ] Implement the audit over `/tmp/mabd-paper/source`.
- [ ] Ensure the default status is
  `explicit_rbd_source_requirements_incomplete`.

### Task 2: Config, Runner, And CLI

**Files:**
- Modify: `src/mabd_reproduction/experiment_configs.py`
- Modify: `configs/experiments/single_body_rolling_spinning.yaml`
- Modify: `src/mabd_reproduction/rolling_spinning_reports.py`
- Modify: `src/mabd_reproduction/experiment_runner.py`
- Modify: `scripts/run_experiment.py`
- Test: `tests/test_experiment_run_configs.py`
- Test: `tests/test_experiment_runner.py`

- [ ] Add failing config, runner, and CLI tests.
- [ ] Add `run_rolling_spinning_rbd_explicit_source_gate`.
- [ ] Add CLI lane `rolling_spinning_rbd_explicit_source_gate`.
- [ ] Ensure the report uses
  `baseline_lane="rbd_explicit_source_gate"`,
  `backend="paper_source_audit"`, and
  `timing_distribution.scope = source_gate_no_runtime`.

### Task 3: Evidence And Validation

**Files:**
- Add:
  `reports/experiment_matrix/single_body_rolling_spinning_rbd_explicit_source_gate.json`
- Add:
  `docs/records/2026-05-21-phase83-rolling-explicit-rbd-source-gate.md`
- Modify: `docs/reference/claim-boundaries.md`
- Modify: `docs/reference/reproduction-gap-audit.yaml`
- Modify: `scripts/validate_docs.py`
- Modify: `tests/test_phase0_bootstrap.py`

- [ ] Generate the report.
- [ ] Record report SHA256
  `eb43b537e4bb92f1684a0b451efe924222819e4b1283c20f472326da2ae98c78`.
- [ ] Add `validate_phase83_record()`.
- [ ] Verify claim boundaries explicitly forbid describing Phase83 evidence as
  an explicit RBD pass or paper-faithful baseline.
