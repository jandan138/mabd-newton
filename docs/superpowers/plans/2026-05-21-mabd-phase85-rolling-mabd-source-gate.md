# Phase 85 Rolling MABD Source Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> superpowers:subagent-driven-development (recommended) or
> superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a fail-closed source-audit gate for the rolling/spinning
paper-faithful M-ABD rolling-cylinder baseline.

**Architecture:** Extend the rolling/spinning config with `mabd_source_gate`,
add a public-paper-source audit, and expose a report-only runner and CLI lane.
The report records missing M-ABD rolling-cylinder source parameters and keeps
the M-ABD paper-faithful gate unpassed.

No `experiment.*` claim is passed by this phase.

---

### Task 1: Source Audit Contract

**Files:**
- Modify: `src/mabd_reproduction/paper_source_audit.py`
- Test: `tests/test_paper_source_audit.py`

- [x] Add failing tests for `rolling_spinning_mabd_source_audit`.
- [x] Verify RED: import/function missing.
- [x] Implement the audit over `/tmp/mabd-paper/source`.
- [x] Ensure the default status is
  `mabd_source_requirements_incomplete`.

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
- [x] Add `run_rolling_spinning_mabd_source_gate`.
- [x] Add CLI lane `rolling_spinning_mabd_source_gate`.
- [x] Ensure the report uses `baseline_lane="mabd_source_gate"`,
  `backend="paper_source_audit"`, and
  `timing_distribution.scope = source_gate_no_runtime`.

### Task 3: Evidence And Validation

**Files:**
- Add:
  `reports/experiment_matrix/single_body_rolling_spinning_mabd_source_gate.json`
- Add:
  `docs/records/2026-05-21-phase85-rolling-mabd-source-gate.md`
- Modify: `docs/reference/claim-boundaries.md`
- Modify: `docs/reference/reproduction-gap-audit.yaml`
- Modify: `scripts/validate_docs.py`
- Modify: `tests/test_phase0_bootstrap.py`

- [x] Generate the report.
- [x] Record report SHA256
  `36b468396aa8a768fc66006cbf2a190ceef1e9dcc807c4bd7b8e317a2d7deb4f`.
- [x] Add `validate_phase85_record()`.
- [x] Verify claim boundaries explicitly forbid describing Phase85 evidence as
  a M-ABD rolling-cylinder pass or paper-faithful baseline.
