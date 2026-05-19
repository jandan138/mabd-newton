# Phase 71 Affine Box Static-Plane Active Set Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move the spinning-box static-plane active-set generation into vendored/local Newton by adding a bounded affine box vs static infinite plane contact detector for `SolverMABD`.

**Architecture:** `SolverMABD.detect_static_plane_contacts(state, max_contacts=None)` reads M-ABD affine state and Newton model shape metadata, emits a `newton.Contacts` buffer, and records `last_static_plane_collision_summary`. The report lane calls this detector, passes the returned contacts into the existing Phase 69 `SolverMABD.step(..., contacts=...)` path, and records incomplete diagnostic evidence.

**Tech Stack:** Python 3.10, `unittest`, NumPy, Warp arrays, vendored Newton, `newton.Contacts`, YAML configs, JSON claim reports.

---

## File Structure

- Modify `vendor/newton/newton/_src/solvers/mabd/solver_mabd.py`: add summary dataclass, affine shape helpers, and `detect_static_plane_contacts`.
- Modify `tests/test_mabd_phase4_solver_step.py`: add TDD coverage for detector behavior and solver-step parity.
- Modify `configs/experiments/single_body_spinning_box.yaml`: add `paper_horizon.affine_static_plane_contacts_output_report`.
- Modify `src/mabd_reproduction/experiment_configs.py`: parse and validate the new report path.
- Modify `src/mabd_reproduction/single_body_reports.py`: add constants, solver-generated contacts step helper, report writer, and report contract fields.
- Modify `src/mabd_reproduction/experiment_runner.py`: expose `run_spinning_box_affine_static_plane_contacts`.
- Modify `scripts/run_experiment.py`: add CLI lane `spinning_box_affine_static_plane_contacts`.
- Modify tests:
  - `tests/test_experiment_run_configs.py`
  - `tests/test_single_body_report_lane.py`
  - `tests/test_experiment_runner.py`
  - `tests/test_spinning_box_report_artifacts.py`
  - `tests/test_phase0_bootstrap.py`
- Create `reports/experiment_matrix/single_body_spinning_box_affine_static_plane_contacts.json`.
- Modify `docs/reference/claim-boundaries.md`, `scripts/validate_docs.py`, and create `docs/records/2026-05-19-phase71-affine-box-static-plane-active-set.md`.

## Task 1: Solver Detector Tests

**Files:**
- Modify `tests/test_mabd_phase4_solver_step.py`
- Modify `vendor/newton/newton/_src/solvers/mabd/solver_mabd.py`

- [ ] **Step 1: Write failing tests**

Add tests that call `SolverMABD.detect_static_plane_contacts(state)` on the existing `_mabd_model_with_box_and_static_plane()` fixture.

Required assertions:

- penetrating affine state generates four rows for the lower box corners;
- separated affine state generates zero rows;
- `max_contacts=2` emits capacity two, reports overflow two, and still records four candidate contacts;
- `solver.step(state, state, None, detected_contacts, dt)` matches an explicit `MABDCPUOraclePlaneConstraint` solve.

- [ ] **Step 2: Verify RED**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_mabd_phase4_solver_step.SolverMABDStepTests.test_solver_detects_affine_box_static_plane_contacts tests.test_mabd_phase4_solver_step.SolverMABDStepTests.test_solver_detects_no_affine_box_static_plane_contacts_when_separated tests.test_mabd_phase4_solver_step.SolverMABDStepTests.test_solver_detects_affine_box_static_plane_contacts_with_capacity_limit tests.test_mabd_phase4_solver_step.SolverMABDStepTests.test_solver_step_matches_explicit_plane_constraints_with_detected_affine_contacts
```

Expected: FAIL because `detect_static_plane_contacts` does not exist.

- [ ] **Step 3: Implement minimal detector**

Add `MABDStaticPlaneCollisionSummary` and `SolverMABD.detect_static_plane_contacts`. The detector must:

- reject missing shape arrays with `ValueError`;
- support only `GeoType.BOX` M-ABD shapes and static infinite `GeoType.PLANE` shapes;
- generate corner contacts using affine state, not rigid `body_q`;
- write `newton.Contacts.rigid_contact_shape0`, `shape1`, `point0`, `point1`, and `normal`;
- set `last_static_plane_collision_summary`.

- [ ] **Step 4: Verify GREEN**

Run the same focused unittest command. Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/test_mabd_phase4_solver_step.py vendor/newton/newton/_src/solvers/mabd/solver_mabd.py
git commit -m "feat: detect MABD affine box static plane contacts"
```

## Task 2: Config And Report Lane

**Files:**
- Modify `tests/test_experiment_run_configs.py`
- Modify `configs/experiments/single_body_spinning_box.yaml`
- Modify `src/mabd_reproduction/experiment_configs.py`
- Modify `tests/test_single_body_report_lane.py`
- Modify `src/mabd_reproduction/single_body_reports.py`

- [ ] **Step 1: Write failing config/report tests**

Add assertions that the config contains:

```text
reports/experiment_matrix/single_body_spinning_box_affine_static_plane_contacts.json
```

Add report tests that the new writer records:

- `solver_mode = solver_mabd_affine_static_plane_contacts_diagnostic`;
- `affine_static_plane_contact_source = SolverMABD.detect_static_plane_contacts`;
- nonzero generated contacts on the paper-horizon diagnostic;
- `status = incomplete`;
- blocker `spinning_box_affine_static_plane_contacts_not_paper_faithful`;
- no `lane_gate_status`.

- [ ] **Step 2: Verify RED**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_run_configs tests.test_single_body_report_lane
```

Expected: FAIL because the config field and report writer do not exist.

- [ ] **Step 3: Implement config/report lane**

Add the config field, validation, constants, helper, and writer. The helper must
call `solver.detect_static_plane_contacts(free_state)` and then
`solver.step(..., contacts=contacts)`; it must not synthesize contact rows in
the report layer.

- [ ] **Step 4: Verify GREEN**

Run the same unittest command. Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/test_experiment_run_configs.py configs/experiments/single_body_spinning_box.yaml src/mabd_reproduction/experiment_configs.py tests/test_single_body_report_lane.py src/mabd_reproduction/single_body_reports.py
git commit -m "feat: add affine static-plane contacts report lane"
```

## Task 3: Runner, Artifact, And Provenance

**Files:**
- Modify `tests/test_experiment_runner.py`
- Modify `src/mabd_reproduction/experiment_runner.py`
- Modify `scripts/run_experiment.py`
- Modify `tests/test_spinning_box_report_artifacts.py`
- Modify `tests/test_phase0_bootstrap.py`
- Modify `scripts/validate_docs.py`
- Modify `docs/reference/claim-boundaries.md`
- Create `docs/records/2026-05-19-phase71-affine-box-static-plane-active-set.md`
- Create `reports/experiment_matrix/single_body_spinning_box_affine_static_plane_contacts.json`

- [ ] **Step 1: Write failing runner/artifact/docs tests**

Add runner and CLI tests for `spinning_box_affine_static_plane_contacts`, add artifact validation for the committed report, and add docs validator expectations for Phase71 boundaries.

- [ ] **Step 2: Verify RED**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_runner tests.test_spinning_box_report_artifacts tests.test_phase0_bootstrap
```

Expected: FAIL because the runner lane, committed report, and validator checks are missing.

- [ ] **Step 3: Implement runner/artifact/docs**

Add the runner function, CLI dispatch, committed report, Phase71 record, claim-boundary bullets, and docs validator checks. Keep all `experiment.*` claims `intended`.

- [ ] **Step 4: Verify GREEN**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_runner tests.test_spinning_box_report_artifacts tests.test_phase0_bootstrap
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/mabd_reproduction/experiment_runner.py scripts/run_experiment.py tests/test_experiment_runner.py tests/test_spinning_box_report_artifacts.py tests/test_phase0_bootstrap.py scripts/validate_docs.py docs/reference/claim-boundaries.md docs/records/2026-05-19-phase71-affine-box-static-plane-active-set.md reports/experiment_matrix/single_body_spinning_box_affine_static_plane_contacts.json
git commit -m "docs: record Phase71 affine static-plane contacts evidence"
```

## Task 4: Full Verification

**Files:** all changed files.

- [ ] **Step 1: Run docs validation**

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
```

Expected: Phase 0-71 validation passed.

- [ ] **Step 2: Run full tests**

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
```

Expected: PASS.

- [ ] **Step 3: Run lint and hygiene checks**

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/env/readiness_check.py
git diff --check
```

Expected: PASS, vendored Newton import, isolated environment smoke passed, no whitespace errors.

- [ ] **Step 4: Commit any verification-only metadata**

If report hashes or validator constants changed during verification:

```bash
git add <changed verification files>
git commit -m "docs: finalize Phase71 affine contacts validation"
```
