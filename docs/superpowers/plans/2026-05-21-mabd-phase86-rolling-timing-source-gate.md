# Phase 86 Rolling Timing Source Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> superpowers:subagent-driven-development (recommended) or
> superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a fail-closed source/runtime audit gate for rolling/spinning
paper-comparable timing.

**Architecture:** Extend the rolling/spinning config with
`timing_source_gate`, add a paper-source audit for missing timing protocol
parameters, and expose a report-only runner plus CLI lane. The report records
why current timing evidence is not paper-comparable and keeps the timing gate
unpassed.

**Tech Stack:** Python dataclasses, YAML config validation, `unittest`, existing
`ClaimReport` JSON reporting.

---

### Task 1: Source Audit Contract

**Files:**
- Modify: `src/mabd_reproduction/paper_source_audit.py`
- Test: `tests/test_paper_source_audit.py`

- [x] Add failing tests for `rolling_spinning_timing_source_audit`.
- [x] Verify RED: import/function missing.
- [x] Implement the audit over `/tmp/mabd-paper/source`.
- [x] Ensure the default status is
  `timing_source_requirements_incomplete`.

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
- [x] Verify RED: timing source gate interfaces are missing.
- [x] Add `run_rolling_spinning_timing_source_gate`.
- [x] Add CLI lane `rolling_spinning_timing_source_gate`.
- [x] Ensure the report uses `baseline_lane="timing_source_gate"`,
  `backend="paper_source_audit"`, and
  `timing_distribution.scope = source_gate_no_runtime`.

### Task 3: Evidence And Validation

**Files:**
- Add:
  `reports/experiment_matrix/single_body_rolling_spinning_timing_source_gate.json`
- Add:
  `docs/records/2026-05-21-phase86-rolling-timing-source-gate.md`
- Modify: `docs/reference/claim-boundaries.md`
- Modify: `docs/reference/reproduction-gap-audit.yaml`
- Modify: `scripts/validate_docs.py`
- Modify: `tests/test_phase0_bootstrap.py`

- [x] Generate the report.
- [x] Record report SHA256
  `5215b20a92c514a48d13f23c9ee046c3d38c302dd64ec9afc36a86cdd93a6845`.
- [x] Add `validate_phase86_record()`.
- [x] Verify claim boundaries explicitly forbid describing Phase86 evidence as
  paper-comparable timing or a rolling/spinning pass.
