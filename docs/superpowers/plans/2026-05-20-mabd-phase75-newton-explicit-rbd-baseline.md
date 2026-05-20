# Phase 75 Newton Explicit RBD Baseline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development and superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a Newton-only explicit Euler rigid-body development solver and use it to write an incomplete rolling-cylinder `rbd_explicit_baseline` report.

**Architecture:** Vendored Newton gains a small `SolverExplicitEuler` that reuses the semi-implicit force path but integrates rigid-body pose from old velocity before updating velocity. The experiment layer reuses the Phase 74 rolling-cylinder scene builder and sampling surface with a lane-specific config, report writer, runner, CLI branch, and docs validation.

**Tech Stack:** Python 3.10, `unittest`, PyYAML, NumPy, vendored Newton/Warp CPU.

No `experiment.*` claim is passed by this phase.

---

### Task 1: Red Tests For Newton Explicit Euler Solver

**Files:**
- Add: `tests/test_newton_explicit_euler_solver.py`
- Add: `vendor/newton/newton/_src/solvers/explicit_euler/__init__.py`
- Add: `vendor/newton/newton/_src/solvers/explicit_euler/solver_explicit_euler.py`
- Modify: `vendor/newton/newton/_src/solvers/__init__.py`
- Modify: `vendor/newton/newton/solvers.py`

- [ ] Add a test that imports `newton.solvers.SolverExplicitEuler` and verifies it is public.
- [ ] Add a gravity-only single-body test:
  - build a Y-up Newton model with one dynamic box shape and gravity `-9.81`;
  - initialize body velocity to zero;
  - run one `dt = 0.1` step;
  - assert the explicit pose remains at the old height for the first step;
  - assert vertical velocity becomes approximately `-0.981`.
- [ ] Run:
  `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_newton_explicit_euler_solver`
  and verify it fails because `SolverExplicitEuler` does not exist.
- [ ] Implement `SolverExplicitEuler` with rigid-body-only explicit pose update and public exports.
- [ ] Re-run the same test and verify it passes.

### Task 2: Red Tests For Explicit Rolling Config And Runner

**Files:**
- Modify: `configs/experiments/single_body_rolling_spinning.yaml`
- Modify: `src/mabd_reproduction/experiment_configs.py`
- Modify: `src/mabd_reproduction/rolling_spinning_reports.py`
- Modify: `src/mabd_reproduction/experiment_runner.py`
- Modify: `scripts/run_experiment.py`
- Modify: `tests/test_experiment_run_configs.py`
- Modify: `tests/test_experiment_runner.py`

- [ ] Add config tests asserting `config.rbd_explicit_baseline.output_report` equals
  `reports/experiment_matrix/single_body_rolling_spinning_rbd_explicit_baseline.json`
  and geometry/contact/timing fields match the implicit baseline.
- [ ] Add validation coverage that rejects explicit report paths outside
  `reports/experiment_matrix/`, non-JSON paths, the Phase 73 protocol path, and
  the Phase 74 implicit baseline path.
- [ ] Add a runner test with a short temporary explicit config that verifies:
  `baseline_lane = rbd_explicit_baseline`,
  `solver_mode = newton_explicit_euler_rolling_cylinder_rbd_cpu_development`,
  `backend = cpu_newton_warp`,
  `observed.newton_device = cpu`,
  `observed.newton_api` contains `SolverExplicitEuler`,
  `observed.required_lanes_missing = ["mabd_newton", "paper_comparable_timing"]`,
  and `status = incomplete`.
- [ ] Add a CLI smoke test for
  `--lane rolling_spinning_rbd_explicit_baseline`.
- [ ] Run the targeted tests and verify they fail because the config field and
  lane do not exist.
- [ ] Implement the config parser, shared rolling-cylinder runner path, explicit
  report writer, experiment runner function, and CLI branch.
- [ ] Re-run the targeted tests and verify they pass.

### Task 3: Generate Explicit Baseline Report

**Files:**
- Add:
  `reports/experiment_matrix/single_body_rolling_spinning_rbd_explicit_baseline.json`

- [ ] Run the full configured lane with the current implementation commit as
  `--source-commit` and vendored Newton commit
  `96713fa965463b69c229a4d30582c733ff3526bb`.
- [ ] Inspect the report and verify `status = incomplete`,
  `paper_comparable = false`, and no `experiment.*` claim is passed.
- [ ] Record the report SHA256 for docs validation.

### Task 4: Docs, Claim Boundaries, And Validator

**Files:**
- Modify: `docs/reference/claim-boundaries.md`
- Modify: `docs/reference/reproduction-gap-audit.yaml`
- Add: `docs/records/2026-05-20-phase75-newton-explicit-rbd-baseline.md`
- Modify: `scripts/validate_docs.py`
- Modify: `tests/test_phase0_bootstrap.py`

- [ ] Add Phase 75 boundary bullets for current evidence, verified evidence,
  non-claims, and forbidden interpretations.
- [ ] Update the gap audit rolling/spinning entry to reference the explicit RBD
  development report while keeping the overall experiment incomplete.
- [ ] Add a dated record with source commit, vendored Newton provenance, local
  patch files, report SHA, commands, and explicit non-claims.
- [ ] Extend `scripts/validate_docs.py` with `validate_phase75_record()`.
- [ ] Add bootstrap tests that call the new validation function and inspect the
  committed explicit report fields.

### Task 5: Verification And Commit

- [ ] Run:
  `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_newton_explicit_euler_solver tests.test_experiment_run_configs tests.test_experiment_runner tests.test_phase0_bootstrap`
- [ ] Run:
  `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests`
- [ ] Run:
  `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py`
- [ ] Run:
  `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .`
- [ ] Run `git diff --check`.
- [ ] Commit and push the Phase 75 implementation and evidence.
