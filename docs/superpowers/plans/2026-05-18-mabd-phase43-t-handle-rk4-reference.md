# Phase 43 T-Handle RK4 Reference Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a bounded, source-backed RK4 reference diagnostic lane for the paper T-handle scene.

**Architecture:** Add a strict per-scene config, a small NumPy torque-free rigid-body RK4 helper, a full-schema incomplete report writer, and runner/CLI dispatch. Preserve claim boundaries by keeping exact geometry, M-ABD lane, comparison, timing, and `experiment.*` pass status incomplete.

**Tech Stack:** Python 3.10, NumPy, PyYAML, `unittest`, existing `mabd-newton-py310` environment.

---

### Task 1: Write Failing Tests

**Files:**
- Create: `tests/test_t_handle_reference.py`
- Modify: `tests/test_experiment_run_configs.py`
- Modify: `tests/test_experiment_runner.py`
- Modify: `tests/test_phase0_bootstrap.py`

- [ ] **Step 1: Add T-handle config tests**

Add tests that load `configs/experiments/single_body_t_handle.yaml` and assert:

```python
config.claim_id == "experiment.single_body.t_handle"
config.scene_id == "single_body_t_handle"
config.baseline_lane == "rbd_rk4_reference"
config.report_status == EvidenceStatus.INCOMPLETE
config.asset_ids == ("t_handle_procedural",)
config.reference.time_step_s == 1.0e-4
config.reference.duration_s == 4.0
config.reference.initial_angular_velocity_rad_s.tolist() == [0.03, 3.0, 0.0]
config.reference.figure_pdf_sha256 == "5ae6464fd7e7e6fd471ad56e67cdbead6014736cb731a232ce29d80630a72c1c"
config.reference.gravity_m_s2.tolist() == [0.0, 0.0, 0.0]
config.reference.output_report == "reports/experiment_matrix/single_body_t_handle_rk4_reference.json"
```

Also test `validate_t_handle_config_against_matrix(config, matrix)`, rejection
of `report.status = passed`, rejection of nonpositive inertia, and rejection of
figure-hash drift.

- [ ] **Step 2: Add RK4 reference tests**

Create tests for:

```python
config = load_t_handle_config(ROOT / "configs/experiments/single_body_t_handle.yaml")
trajectory = roll_out_t_handle_rk4_reference(config)
self.assertGreaterEqual(trajectory.intermediate_axis_sign_flips, 1)
self.assertLess(abs(trajectory.relative_energy_drift), 1.0e-8)
self.assertLess(abs(trajectory.angular_momentum_norm_drift), 1.0e-8)
self.assertEqual(trajectory.samples.shape, (config.reference.sample_count, 4))
```

Add invalid-input tests for negative time step, invalid axis index, non-finite
angular velocity, nonzero gravity, and nonpositive inertia.

- [ ] **Step 3: Add runner/CLI tests**

Test `run_t_handle_rk4_reference(...)` writes a report with
`baseline_lane=rbd_rk4_reference`,
`solver_mode=t_handle_torque_free_rk4_reference`, status `incomplete`,
`observed.full_experiment_claim_passed is False`, and blockers containing
`exact_t_handle_geometry_unknown`,
`raw_t_handle_reference_curve_data_missing`, `mabd_newton_report_missing`, and
`t_handle_comparison_report_missing`.

Add CLI coverage for:

```bash
scripts/run_experiment.py --lane t_handle_rk4_reference \
  --config configs/experiments/single_body_t_handle.yaml \
  --matrix configs/experiments/paper_experiment_matrix.yaml \
  --source-commit test-source \
  --vendored-newton-commit test-newton \
  --output <tmp>/single_body_t_handle_rk4_reference.json
```

- [ ] **Step 4: Add Phase43 bootstrap tests**

Assert `validate_docs.py` requires the Phase43 spec, plan, record, config,
report artifact, boundary snippets, record hash, and no passed
`experiment.*` claim.

- [ ] **Step 5: Verify RED**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_t_handle_reference tests.test_experiment_run_configs tests.test_experiment_runner tests.test_phase0_bootstrap
```

Expected: fail because the config, helper, report writer, runner lane, and
Phase43 validator do not exist.

### Task 2: Implement Config And RK4 Helper

**Files:**
- Create: `configs/experiments/single_body_t_handle.yaml`
- Modify: `src/mabd_reproduction/experiment_configs.py`
- Create: `src/mabd_reproduction/t_handle_reference.py`

- [ ] **Step 1: Add strict config dataclasses**

Add `THandleReferenceConfig` and `THandleRunConfig` with strict validation for
finite scalars, positive time step/duration/sample count, positive diagonal
inertias, a valid intermediate-axis index, finite initial angular velocity,
zero gravity, and status `incomplete`.

- [ ] **Step 2: Add matrix validation**

Add `load_t_handle_config(path)` and
`validate_t_handle_config_against_matrix(config, matrix)`. The validator must
check claim id, scene id, source lines, paper values, required lanes, asset ids,
the lane-specific output report under the matrix stem, the
`exact_t_handle_geometry_unknown` blocker, and the
`raw_t_handle_reference_curve_data_missing` blocker.

- [ ] **Step 3: Add RK4 torque-free reference**

Implement `roll_out_t_handle_rk4_reference(config)` using Euler's equations in
principal axes and fixed-step RK4. Return deterministic samples with columns
`time_s`, `omega_x_rad_s`, `omega_y_rad_s`, `omega_z_rad_s`, plus summary
energy/momentum drift and sign-flip count.

- [ ] **Step 4: Verify focused GREEN for config/helper**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_t_handle_reference tests.test_experiment_run_configs
```

Expected: config/helper tests pass; runner and docs tests still fail until
later tasks are complete.

### Task 3: Implement Report, Runner, And CLI

**Files:**
- Create: `src/mabd_reproduction/t_handle_reports.py`
- Modify: `src/mabd_reproduction/experiment_runner.py`
- Modify: `scripts/run_experiment.py`
- Create: `reports/experiment_matrix/single_body_t_handle_rk4_reference.json`

- [ ] **Step 1: Add report writer**

Create `write_t_handle_rk4_reference_report(...)` that writes a full-schema
`ClaimReport` with finite metrics, source commit, vendored Newton commit,
figure hash, blockers, and `status=incomplete`.

- [ ] **Step 2: Add runner function**

Add `run_t_handle_rk4_reference(...)` with explicit output handling consistent
with existing runners.

- [ ] **Step 3: Add CLI lane**

Extend `scripts/run_experiment.py` with `--lane t_handle_rk4_reference` and
dispatch only for `experiment.single_body.t_handle`.

- [ ] **Step 4: Generate committed compact report**

Use the canonical env and a fixed report source commit equal to the
implementation commit that contains the T-handle lane code and config. Do not
record the base main commit for this artifact.

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/run_experiment.py \
  --lane t_handle_rk4_reference \
  --config configs/experiments/single_body_t_handle.yaml \
  --matrix configs/experiments/paper_experiment_matrix.yaml \
  --source-commit <phase43-implementation-commit> \
  --vendored-newton-commit 96713fa965463b69c229a4d30582c733ff3526bb \
  --output reports/experiment_matrix/single_body_t_handle_rk4_reference.json
```

### Task 4: Update Claim Boundaries, Record, And Validators

**Files:**
- Modify: `docs/reference/claim-boundaries.md`
- Create: `docs/records/2026-05-18-phase43-t-handle-rk4-reference.md`
- Modify: `scripts/validate_docs.py`
- Modify: `tests/test_phase0_bootstrap.py`

- [ ] **Step 1: Add Phase43 boundary text**

State that Phase43 verifies a compact RK4 T-handle reference diagnostic only,
and does not verify M-ABD, exact geometry, figure curve agreement, timing, or a
passed experiment.

- [ ] **Step 2: Add dated record**

Record branch, report source commit, environment isolation, paper source lines,
figure hash, report artifact hash, lane-specific report path, blockers, and
verification commands.

- [ ] **Step 3: Extend docs validator**

Require all Phase43 files and report fields. Validate report hash path binding,
non-placeholder source commit, `baseline_lane`, `solver_mode`, finite metrics,
sign flip count, blocker retention, matrix status still `planned`, and no
passed `experiment.*` claim.

### Task 5: Verify, Commit, Merge, Push

**Files:** all Phase43 files.

- [ ] **Step 1: Run focused gates**

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_t_handle_reference tests.test_experiment_run_configs tests.test_experiment_runner tests.test_phase0_bootstrap
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
git diff --check
```

- [ ] **Step 2: Run full gates**

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/env/readiness_check.py
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"
npm --prefix site run validate
```

- [ ] **Step 3: Commit and integrate**

Commit Phase43 on `phase43-t-handle-reference`, fast-forward or merge into
`main` after fetch, rerun main gates, and push `origin main` without force.
