# Phase 76 Rolling Cylinder MABD Newton Lane Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development and superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a Newton-only rolling-cylinder `mabd_newton` diagnostic lane and commit an incomplete machine-checkable report for `experiment.single_body.rolling_spinning`.

**Architecture:** Vendored Newton gains a narrow affine-cylinder static-plane contact diagnostic in `SolverMABD.detect_static_plane_contacts(...)`. The reproduction layer adds a `mabd_newton` config, a model-derived `SolverMABD` rollout, a report writer, runner/CLI dispatch, and docs validation while preserving all rolling/spinning pass gates as incomplete.

**Tech Stack:** Python 3.10, `unittest`, PyYAML, NumPy, vendored Newton/Warp CPU.

No `experiment.*` claim is passed by this phase.

---

### Task 1: Red Tests For Affine-Cylinder Static-Plane Contacts

**Files:**
- Modify: `vendor/newton/newton/_src/solvers/mabd/solver_mabd.py`
- Modify: `tests/test_mabd_phase4_solver_step.py`
- Modify: `vendor/newton/newton/tests/test_mabd_phase4_solver_step.py`

- [ ] Add a test that builds a Newton model with one `mabd:body`, one
  `ModelBuilder.add_shape_cylinder(...)` shape attached to that body, and one
  static infinite ground plane.
- [ ] Put the M-ABD state into slight penetration and assert
  `SolverMABD.detect_static_plane_contacts(state)` reports one cylinder contact,
  with the M-ABD cylinder shape as `rigid_contact_shape0`, the static plane as
  `rigid_contact_shape1`, normal `[0, 1, 0]`, and a rest contact point near
  local `y = -radius`.
- [ ] Assert the summary records
  `policy = mabd_affine_cylinder_static_plane_support_diagnostic`,
  `cylinder_shape_count = 1`, `static_plane_shape_count = 1`,
  and `scope = affine_cylinder_support_points_vs_static_infinite_planes`.
- [ ] Run:
  `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_mabd_phase4_solver_step.MABDPhase4SolverStepTests.test_solver_detects_affine_cylinder_static_plane_contact`
  and verify it fails because cylinders are ignored.
- [ ] Implement the narrow cylinder support-point path and preserve existing box
  summary behavior.
- [ ] Re-run the new test plus the existing affine-box static-plane tests and
  verify they pass.

### Task 2: Red Tests For Rolling MABD Config And Runner

**Files:**
- Modify: `configs/experiments/single_body_rolling_spinning.yaml`
- Modify: `src/mabd_reproduction/experiment_configs.py`
- Modify: `src/mabd_reproduction/rolling_spinning_reports.py`
- Modify: `src/mabd_reproduction/experiment_runner.py`
- Modify: `scripts/run_experiment.py`
- Modify: `tests/test_experiment_run_configs.py`
- Modify: `tests/test_experiment_runner.py`

- [ ] Add config tests asserting `config.mabd_newton.output_report` equals
  `reports/experiment_matrix/single_body_rolling_spinning_mabd_newton.json`,
  `time_step_s = 0.01`, `step_count = 10000`, `sample_count = 7`,
  `rotation_mode = polar`, and initial velocity satisfies the same no-slip
  diagnostic as the RBD lanes.
- [ ] Add validation coverage that rejects `mabd_newton.output_report` outside
  `reports/experiment_matrix/`, non-JSON paths, the Phase 73 protocol path, and
  both RBD baseline paths.
- [ ] Add a short-config runner test for
  `run_rolling_spinning_mabd_newton(...)` with `step_count = 4` and
  `sample_count = 3`. Verify `baseline_lane = mabd_newton`,
  `solver_mode = mabd_cpu_oracle_rolling_cylinder_newton_lane`,
  `backend = cpu_numpy_newton_solver_mabd_static_plane_contacts`,
  `status = incomplete`, and `observed.full_experiment_claim_passed = false`.
- [ ] Assert the report records `SolverMABD.detect_static_plane_contacts`,
  `SolverMABD.step(..., contacts=...)`,
  `contact_detection_policy =
  mabd_affine_cylinder_static_plane_support_diagnostic`,
  and `required_lanes_missing = ["paper_comparable_timing"]`.
- [ ] Add a CLI smoke test for
  `--lane rolling_spinning_mabd_newton`.
- [ ] Run the targeted tests and verify they fail because the config section,
  runner, and CLI lane do not exist.
- [ ] Implement the config parser, rollout, report writer, runner function, and
  CLI branch.
- [ ] Re-run the targeted tests and verify they pass.

### Task 3: Generate MABD Newton Report

**Files:**
- Add: `reports/experiment_matrix/single_body_rolling_spinning_mabd_newton.json`

- [ ] Run:
  `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/run_experiment.py --lane rolling_spinning_mabd_newton --config configs/experiments/single_body_rolling_spinning.yaml --matrix configs/experiments/paper_experiment_matrix.yaml --output reports/experiment_matrix/single_body_rolling_spinning_mabd_newton.json --source-commit $(git rev-parse HEAD) --vendored-newton-commit 96713fa965463b69c229a4d30582c733ff3526bb`
- [ ] Inspect the report and verify `status = incomplete`,
  `paper_comparable = false`, and no `experiment.*` claim is passed.
- [ ] Record the report SHA256 for docs validation.

### Task 4: Docs, Claim Boundaries, And Validator

**Files:**
- Modify: `docs/reference/claim-boundaries.md`
- Modify: `docs/reference/reproduction-gap-audit.yaml`
- Add: `docs/records/2026-05-20-phase76-rolling-cylinder-mabd-newton.md`
- Modify: `scripts/validate_docs.py`
- Modify: `tests/test_phase0_bootstrap.py`

- [ ] Add Phase 76 boundary bullets for current evidence, verified evidence,
  non-claims, and forbidden interpretations.
- [ ] Update the gap audit rolling/spinning entry to reference the M-ABD
  development report while keeping the overall experiment incomplete.
- [ ] Add a dated record with source commit, vendored Newton provenance, local
  patch files, report SHA, commands, environment isolation evidence, and
  explicit non-claims.
- [ ] Extend `scripts/validate_docs.py` with `validate_phase76_record()`.
- [ ] Add bootstrap tests that call the new validation function and inspect the
  committed M-ABD report fields.

### Task 5: Verification, Review, Commit, Push

- [ ] Run:
  `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_mabd_phase4_solver_step tests.test_experiment_run_configs tests.test_experiment_runner tests.test_phase0_bootstrap`
- [ ] Run:
  `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests`
- [ ] Run:
  `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py`
- [ ] Run:
  `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .`
- [ ] Run `git diff --check`.
- [ ] Request multi-agent code review for the Phase 76 diff and fix Critical or
  Important findings.
- [ ] Commit and push the Phase 76 implementation and evidence.
