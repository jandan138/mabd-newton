# Phase 87 Spinning-Box Development Comparison Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> superpowers:subagent-driven-development (recommended) or
> superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Record a development-only 10 second internal comparison between
Newton `SolverMABD` and Newton `SolverSemiImplicit` on the configured
single-body spinning box scene.

**Architecture:** Add a `development_comparison` config block, expose a runner
and CLI lane, step both Newton solvers with local default velocities, and write
compact trajectory and energy-curve samples into an incomplete `ClaimReport`.

**Tech Stack:** Python dataclasses, Newton/Warp CPU solvers, YAML config
validation, `unittest`, existing `ClaimReport` JSON reporting.

---

### Task 1: Config Contract

**Files:**
- Modify: `configs/experiments/single_body_spinning_box.yaml`
- Modify: `src/mabd_reproduction/experiment_configs.py`
- Test: `tests/test_experiment_run_configs.py`

- [x] Add failing tests for a `development_comparison` config section.
- [x] Verify RED: the loader ignores or rejects the missing development lane.
- [x] Implement a development-only config dataclass and validation.
- [x] Require the report path
  `reports/experiment_matrix/single_body_spinning_box_development_comparison.json`.

### Task 2: Solver Rollouts And Report

**Files:**
- Add: `src/mabd_reproduction/spinning_box_development_comparison.py`
- Modify: `src/mabd_reproduction/experiment_runner.py`
- Modify: `scripts/run_experiment.py`
- Test: `tests/test_experiment_runner.py`

- [x] Add failing runner and CLI tests.
- [x] Verify RED: `run_spinning_box_development_comparison` and the CLI lane
  are missing.
- [x] Run Newton `SolverMABD` for 10 seconds.
- [x] Run Newton `SolverSemiImplicit` for the same scene and initial velocity.
- [x] Record M-ABD vs RBD momentum, energy, and position deltas.
- [x] Keep `paper_faithful = false` and `full_experiment_claim_passed = false`.

### Task 3: Evidence And Validation

**Files:**
- Add:
  `reports/experiment_matrix/single_body_spinning_box_development_comparison.json`
- Add:
  `docs/records/2026-05-21-phase87-spinning-box-development-comparison.md`
- Modify: `docs/reference/claim-boundaries.md`
- Modify: `docs/reference/reproduction-gap-audit.yaml`
- Modify: `scripts/validate_docs.py`
- Modify: `tests/test_phase0_bootstrap.py`
- Modify: `tests/test_spinning_box_report_artifacts.py`

- [x] Generate the report from implementation source commit `ce0c5bd`.
- [x] Record report SHA256
  `37d5dec0c0dbecf66c538ed0662cb19741af9cc22dea8f90ea7ecbdc749cca22`.
- [x] Add `validate_phase87_record()`.
- [x] Verify claim boundaries explicitly forbid treating this lane as
  paper-faithful or as a spinning-box pass gate.
