# Phase 88 Spinning-Box Contact/Collision Candidate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> superpowers:subagent-driven-development (recommended) or
> superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a persistent Newton `SolverMABD` affine static-plane contacts
rollout candidate lane for the single-body spinning-box affine body on a
static frictionless plane.

**Architecture:** Extend the spinning-box config with a
`affine_static_plane_contacts_rollout_candidate` section. Add a focused
rollout/report module that uses a persistent SolverMABD model, free-predicts
contacts, reruns the step with Newton `Contacts`, and writes an incomplete
`ClaimReport`. Wire the lane through the runner, CLI, committed report
artifacts, and docs/provenance validators.

**Tech Stack:** Python dataclasses, YAML config validation, Newton/Warp CPU
`SolverMABD`, existing `ClaimReport` JSON reporting, `unittest`.

---

### Task 1: Config Contract

**Files:**
- Modify: `configs/experiments/single_body_spinning_box.yaml`
- Modify: `src/mabd_reproduction/experiment_configs.py`
- Test: `tests/test_experiment_run_configs.py`

- [x] Write a failing config test asserting
  `config.affine_static_plane_contacts_rollout_candidate.output_report ==
  "reports/experiment_matrix/single_body_spinning_box_affine_static_plane_contacts_rollout_candidate.json"`.
- [x] Run the targeted test and verify it fails because the config dataclass
  field is missing.
- [x] Add `SpinningBoxAffineStaticPlaneContactsRolloutCandidateConfig` with
  `output_report`, `rollout_scope`, `paper_faithful`, `duration_s`,
  `time_step_s`, `sample_count`, initial velocities,
  `contact_constraint_mode`, and thresholds.
- [x] Add validation requiring `rollout_scope = development_only`,
  `paper_faithful = false`, `contact_constraint_mode = plane`, finite
  divisible duration/time step, nonzero initial velocities, and `sample_count`
  in `[2, step_count + 1]`.
- [x] Rerun the targeted config tests and verify they pass.

### Task 2: Persistent SolverMABD Contact Rollout

**Files:**
- Add:
  `src/mabd_reproduction/spinning_box_affine_static_plane_contacts_rollout_candidate.py`
- Test: `tests/test_experiment_runner.py`

- [x] Write a failing runner test for
  `run_spinning_box_affine_static_plane_contacts_rollout_candidate`.
- [x] Verify RED: import or CLI lane is missing.
- [x] Build a persistent `SolverMABD` model with one M-ABD box body and one
  static plane shape using the configured cube and plane values.
- [x] Implement the per-step policy:
  free predict, detect static-plane contacts, restore original state, rerun
  with contacts, then advance to the constrained state.
- [x] Record compact samples, penetration extrema, contact counts, generated
  plane-constraint counts, residuals, energy, and momentum.
- [x] Write a `ClaimReport` with `status = incomplete`,
  `paper_faithful = false`, and no lane gate.
- [x] Rerun the targeted runner test and verify it passes.

### Task 3: Runner And CLI

**Files:**
- Modify: `src/mabd_reproduction/experiment_runner.py`
- Modify: `scripts/run_experiment.py`
- Test: `tests/test_experiment_runner.py`

- [x] Add `run_spinning_box_affine_static_plane_contacts_rollout_candidate`.
- [x] Add CLI lane
  `spinning_box_affine_static_plane_contacts_rollout_candidate`.
- [x] Add a CLI test that writes the candidate report to a temporary path.
- [x] Rerun the runner/CLI tests and verify they pass.

### Task 4: Evidence And Provenance

**Files:**
- Add:
  `reports/experiment_matrix/single_body_spinning_box_affine_static_plane_contacts_rollout_candidate.json`
- Add:
  `docs/records/2026-05-21-phase88-spinning-box-contact-collision-candidate.md`
- Modify: `docs/reference/claim-boundaries.md`
- Modify: `docs/reference/reproduction-gap-audit.yaml`
- Modify: `scripts/validate_docs.py`
- Modify: `tests/test_phase0_bootstrap.py`
- Modify: `tests/test_spinning_box_report_artifacts.py`

- [ ] Generate the report from the implementation source commit.
- [ ] Record the report SHA256.
- [ ] Add an artifact test requiring a 10 second rollout, 101 samples, generated
  affine static-plane contact telemetry, and incomplete non-claim status.
- [ ] Add `validate_phase88_record()` and include the report in
  `REQUIRED_PATHS`.
- [ ] Update claim boundaries and gap audit without passing any
  `experiment.*` claim.
- [ ] Run docs/provenance validation, targeted tests, full tests, whitespace,
  and vendored Newton import checks.
