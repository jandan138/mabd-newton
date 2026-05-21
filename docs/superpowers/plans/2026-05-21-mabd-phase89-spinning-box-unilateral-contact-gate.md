# Phase 89 Spinning-Box Unilateral Contact Gate Candidate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> superpowers:subagent-driven-development (recommended) or
> superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a fail-closed single-body spinning-box contact/collision gate
candidate backed by an opt-in unilateral frictionless static-plane contact mode
in Newton `SolverMABD`.

The lane remains `status = incomplete` with `paper_faithful = false`.

**Architecture:** Extend the dense CPU oracle with
`MABDCPUOraclePlaneConstraint(unilateral=True)` and an active-set loop that
drops tensile unilateral rows. Wire `SolverMABD` contact conversion through a
new `contact_constraint_mode = unilateral_plane`, then add a Phase89
machine-checkable incomplete report lane.

**Tech Stack:** Python dataclasses, Newton/Warp CPU `SolverMABD`, M-ABD dense
CPU oracle, YAML config validation, existing `ClaimReport` JSON reporting,
`unittest`.

---

### Task 1: Solver Unilateral Plane Contact

**Files:**
- Modify: `vendor/newton/newton/_src/solvers/mabd/step_oracle.py`
- Modify: `vendor/newton/newton/_src/solvers/mabd/solver_mabd.py`
- Test: `tests/test_mabd_phase4_solver_step.py`

- [x] Add RED tests for `MABDCPUOraclePlaneConstraint(unilateral=True)`:
  a separating stale row must match the unconstrained step and record one
  rejected unilateral row; a penetrating row must enforce nonpenetration and
  keep a compressive multiplier (`dlambda <= 0`).
- [x] Add a RED `SolverMABD.step(..., contacts=...)` test with
  `contact_constraint_mode = "unilateral_plane"` requiring converted contacts
  to set `unilateral=True` and record unilateral telemetry.
- [x] Add `unilateral: bool = False` to
  `MABDCPUOraclePlaneConstraint`.
- [x] Extend `MABDCPUOracleStepResult` with
  `unilateral_plane_constraint_requested_count`,
  `unilateral_plane_constraint_accepted_count`,
  `unilateral_plane_constraint_rejected_count`, and
  `unilateral_plane_constraint_skipped_count`.
- [x] Preserve plane-row unilateral metadata through dense assembly, solve,
  reject tensile unilateral rows, and re-solve until stable.
- [x] Allow `contact_constraint_mode = "unilateral_plane"` in `MABDCPUOracleConfig`
  and `SolverMABD._constraints_from_contacts`.
- [x] Keep existing `plane` and `world` behavior unchanged.
- [x] Run the targeted solver tests.

### Task 2: Phase89 Config, Runner, And Report

**Files:**
- Modify: `configs/experiments/single_body_spinning_box.yaml`
- Modify: `src/mabd_reproduction/experiment_configs.py`
- Add: `src/mabd_reproduction/spinning_box_contact_collision_gate_candidate.py`
- Modify: `src/mabd_reproduction/experiment_runner.py`
- Modify: `scripts/run_experiment.py`
- Test: `tests/test_experiment_run_configs.py`
- Test: `tests/test_experiment_runner.py`

- [x] Add a fail-closed config section
  `contact_collision_gate_candidate` with report path
  `reports/experiment_matrix/single_body_spinning_box_contact_collision_gate_candidate.json`,
  `gate_scope = single_body_spinning_box_contact_collision_candidate`,
  `paper_faithful = false`, 10 second duration, 0.01 second timestep, 101
  samples, initial velocities, `contact_constraint_mode = unilateral_plane`,
  and thresholds.
- [x] Add config dataclass and validation requiring exact path, false
  paper-faithful flags, nonzero velocities, divisible duration, bounded sample
  count, and `unilateral_plane` mode.
- [x] Add a report module that reuses the Phase88 free-predict/detect/restore
  rollout policy but configures `SolverMABD` with unilateral contacts and records
  unilateral row telemetry.
- [x] Add runner and CLI lane
  `spinning_box_contact_collision_gate_candidate` through
  `run_spinning_box_contact_collision_gate_candidate`.
- [x] Add config, runner, and CLI tests.

### Task 3: Phase89 Evidence And Validators

**Files:**
- Add:
  `reports/experiment_matrix/single_body_spinning_box_contact_collision_gate_candidate.json`
- Add:
  `docs/records/2026-05-21-phase89-spinning-box-unilateral-contact-gate.md`
- Modify: `docs/reference/claim-boundaries.md`
- Modify: `docs/reference/reproduction-gap-audit.yaml`
- Modify: `scripts/validate_docs.py`
- Modify: `tests/test_phase0_bootstrap.py`
- Modify: `tests/test_spinning_box_report_artifacts.py`

- [x] Generate the report from the implementation source commit.
- [x] Record the report SHA256.
- [x] Add artifact tests requiring 10 seconds, 101 samples, unilateral telemetry,
  Phase88 evidence linkage, and incomplete non-claim status.
- [x] Add `validate_phase89_record()` and include the record/spec/plan/report in
  `REQUIRED_PATHS`.
- [x] Update claim boundaries and gap audit without passing any `experiment.*`
  claim.
- [x] Run docs/provenance validation, targeted tests, full tests, whitespace,
  and vendored Newton import checks.
