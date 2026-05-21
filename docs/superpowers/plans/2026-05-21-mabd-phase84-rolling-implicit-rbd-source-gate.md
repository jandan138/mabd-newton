# Phase 84 Rolling Implicit RBD Source Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> superpowers:subagent-driven-development (recommended) or
> superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a fail-closed source-audit gate for the rolling/spinning
paper-faithful implicit RBD baseline.

**Architecture:** Extend the rolling/spinning config with
`rbd_implicit_source_gate`, add a public-paper-source audit, and expose a
report-only runner and CLI lane. The report records missing source parameters
and keeps the implicit RBD paper-faithful gate unpassed.

No `experiment.*` claim is passed by this phase.

---

### Task 1: Source Audit Contract

**Files:**
- Modify: `src/mabd_reproduction/paper_source_audit.py`
- Test: `tests/test_paper_source_audit.py`

- [x] Add failing tests for
  `rolling_spinning_implicit_rbd_source_audit`.
- [x] Verify RED: import/function missing.
- [x] Implement the audit over `/tmp/mabd-paper/source`.
- [x] Ensure the default status is
  `implicit_rbd_source_requirements_incomplete`.

### Task 2: Config, Runner, And CLI

**Files:**
- Modify: `src/mabd_reproduction/experiment_configs.py`
- Modify: `configs/experiments/single_body_rolling_spinning.yaml`
- Modify: `src/mabd_reproduction/rolling_spinning_reports.py`
- Modify: `src/mabd_reproduction/experiment_runner.py`
- Modify: `scripts/run_experiment.py`
- Test: `tests/test_experiment_run_configs.py`
- Test: `tests/test_experiment_runner.py`

- [x] Add failing config, runner, and CLI tests.
- [x] Add `run_rolling_spinning_rbd_implicit_source_gate`.
- [x] Add CLI lane `rolling_spinning_rbd_implicit_source_gate`.
- [x] Ensure the report uses
  `baseline_lane="rbd_implicit_source_gate"`,
  `backend="paper_source_audit"`, and
  `timing_distribution.scope = source_gate_no_runtime`.

### Task 3: Evidence And Validation

**Files:**
- Add:
  `reports/experiment_matrix/single_body_rolling_spinning_rbd_implicit_source_gate.json`
- Add:
  `docs/records/2026-05-21-phase84-rolling-implicit-rbd-source-gate.md`
- Modify: `docs/reference/claim-boundaries.md`
- Modify: `docs/reference/reproduction-gap-audit.yaml`
- Modify: `scripts/validate_docs.py`
- Modify: `tests/test_phase0_bootstrap.py`

- [x] Generate the report.
- [x] Record report SHA256
  `0a17ce33534cf3624c8c734cbaf44306fd29bf6918d4503af32f66e532e43b02`.
- [x] Add `validate_phase84_record()`.
- [x] Verify claim boundaries explicitly forbid describing Phase84 evidence as
  an implicit RBD pass or paper-faithful baseline.
