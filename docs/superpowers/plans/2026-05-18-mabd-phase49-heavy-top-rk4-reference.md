# Phase 49 Heavy Top RK4 Reference Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a source-backed heavy-top RK4 reference diagnostic lane for `experiment.single_body.heavy_top`.

**Architecture:** Follow the existing T-handle reference-lane pattern: strict YAML config, NumPy RK4 rigid heavy-top reference, full-schema incomplete claim report, runner/CLI dispatch, committed report artifact, and docs/provenance validation. Keep all experiment pass gates false because exact heavy-top inertia/geometry and raw paper curves are not public.

**Tech Stack:** Python 3.10, NumPy, PyYAML, `unittest`, existing `mabd-newton-py310` environment, vendored Newton only for project import consistency.

---

### Task 1: RED Tests For Heavy Top Config And Reference

**Files:**
- Create: `tests/test_heavy_top_reference.py`
- Modify: `tests/test_experiment_run_configs.py`

- [ ] **Step 1: Add config loader tests**

Add imports:

```python
from mabd_reproduction.experiment_configs import (
    load_heavy_top_config,
    validate_heavy_top_config_against_matrix,
)
```

Add `HEAVY_TOP_CONFIG_PATH = ROOT / "configs/experiments/single_body_heavy_top.yaml"`.

Add assertions:

```python
config = load_heavy_top_config(HEAVY_TOP_CONFIG_PATH)
self.assertEqual(config.claim_id, "experiment.single_body.heavy_top")
self.assertEqual(config.scene_id, "single_body_heavy_top")
self.assertEqual(config.baseline_lane, "rbd_rk4_reference")
self.assertEqual(config.required_missing_lanes, ("mabd_newton",))
self.assertEqual(config.asset_ids, ("heavy_top_procedural",))
self.assertEqual(config.reference.time_step_s, 1.0e-4)
self.assertEqual(config.reference.duration_s, 10.0)
self.assertEqual(config.reference.sample_count, 11)
self.assertEqual(config.reference.initial_tilt_deg, 5.0)
self.assertEqual(config.reference.initial_spin_rad_s, 10.0)
self.assertEqual(config.reference.figure_pdf_sha256, "c8f5e206415b9feb3578ee32aa3b7284e2695bdd84eeb0200f3b4aa01cf3422d")
self.assertEqual(
    config.reference.output_report,
    "reports/experiment_matrix/single_body_heavy_top_rk4_reference.json",
)
```

Also test `validate_heavy_top_config_against_matrix(config, matrix)`, rejection
of `report.status = passed`, rejection of nonpositive inertia, and rejection of
figure-hash drift.

- [ ] **Step 2: Add RK4 reference tests**

Create `tests/test_heavy_top_reference.py` with:

```python
config = load_heavy_top_config(CONFIG_PATH)
trajectory = roll_out_heavy_top_rk4_reference(config)
self.assertEqual(trajectory.samples.shape, (config.reference.sample_count, 4))
self.assertAlmostEqual(float(trajectory.samples[0, 0]), 0.0)
self.assertAlmostEqual(float(trajectory.samples[-1, 0]), config.reference.duration_s)
self.assertTrue(np.all(np.isfinite(trajectory.samples)))
self.assertLessEqual(
    abs(trajectory.relative_energy_drift),
    config.reference.thresholds["max_relative_energy_drift"],
)
self.assertGreater(
    trajectory.max_nutation_angle_deg - trajectory.min_nutation_angle_deg,
    config.reference.thresholds["min_nutation_angle_range_deg"],
)
self.assertGreater(
    abs(trajectory.max_abs_precession_velocity_rad_s),
    config.reference.thresholds["min_abs_precession_velocity_rad_s"],
)
```

Add invalid-input tests for negative gravity direction, nonpositive inertia,
invalid sample count, and nonpositive pivot-to-COM length.

- [ ] **Step 3: Verify RED**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_heavy_top_reference tests.test_experiment_run_configs
```

Expected: fail because the heavy-top config loader and reference helper do not
exist.

### Task 2: Implement Config And RK4 Reference

**Files:**
- Create: `configs/experiments/single_body_heavy_top.yaml`
- Modify: `src/mabd_reproduction/experiment_configs.py`
- Create: `src/mabd_reproduction/heavy_top_reference.py`

- [ ] **Step 1: Add strict config dataclasses**

Add `HeavyTopReferenceConfig` and `HeavyTopRunConfig`. The loader must validate:

- `claim_id == experiment.single_body.heavy_top`;
- status is not `passed`;
- `baseline_lane == rbd_rk4_reference`;
- `required_missing_lanes == ("mabd_newton",)`;
- positive `time_step_s`, `duration_s`, `sample_count`;
- `duration_s / time_step_s` is an integer;
- positive principal inertias, mass, and pivot-to-COM length;
- negative-y gravity;
- figure hash and figure text command match the public source.

- [ ] **Step 2: Add YAML config**

Create `configs/experiments/single_body_heavy_top.yaml` with paper values from
the experiment matrix and diagnostic reference fields:

```yaml
schema_version: 1
claim_id: experiment.single_body.heavy_top
scene_id: single_body_heavy_top
source_lines:
  - /tmp/mabd-paper/source/sections/experiment.tex:65-75
asset_ids:
  - heavy_top_procedural
baseline_lane: rbd_rk4_reference
required_missing_lanes:
  - mabd_newton
paper_values:
  tilt_deg: 5
  angular_speed_rad_s: 10
  reference_h_s: 0.0001
reference:
  time_step_s: 0.0001
  duration_s: 10.0
  sample_count: 11
  principal_inertia_kg_m2: [0.18, 0.205, 0.05]
  mass_kg: 1.0
  pivot_to_com_m: [0.0, 0.0, 0.25]
  gravity_m_s2: [0.0, -9.81, 0.0]
  initial_tilt_deg: 5.0
  initial_spin_rad_s: 10.0
  figure_pdf_sha256: c8f5e206415b9feb3578ee32aa3b7284e2695bdd84eeb0200f3b4aa01cf3422d
  figure_text_source: pdftotext /tmp/mabd-paper/source/images/spinning_top/spinning_top.pdf -
  output_report: reports/experiment_matrix/single_body_heavy_top_rk4_reference.json
  thresholds:
    max_relative_energy_drift: 1.0e-7
    min_nutation_angle_range_deg: 0.01
    min_abs_precession_velocity_rad_s: 0.01
report:
  status: incomplete
  failure_reason: >-
    rbd_rk4_reference diagnostic only; exact_heavy_top_inertia_unknown,
    raw_heavy_top_reference_curve_data_missing, mabd_newton_report_missing,
    and heavy_top_comparison_report_missing remain incomplete
  output_report: reports/experiment_matrix/single_body_heavy_top_rk4_reference.json
  thresholds:
    max_relative_energy_drift: 1.0e-7
    min_nutation_angle_range_deg: 0.01
    min_abs_precession_velocity_rad_s: 0.01
```

- [ ] **Step 3: Implement RK4 reference**

`roll_out_heavy_top_rk4_reference(config)` must integrate world-from-body
rotation `R` and body-frame angular velocity `omega`:

```python
tau_body = np.cross(r_body, R.T @ (mass * gravity_world))
omega_dot = inv_inertia * (tau_body - np.cross(omega, inertia * omega))
R_dot = R @ skew(omega)
```

Use fixed-step RK4 over `(R, omega)`, re-orthonormalize `R` by SVD after each
step, sample 11 rows `[time_s, nutation_angle_deg, precession_angle_rad,
precession_velocity_rad_s]`, and compute energy drift from rotational plus
gravitational potential energy.

- [ ] **Step 4: Verify GREEN for config/reference**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_heavy_top_reference tests.test_experiment_run_configs
```

Expected: heavy-top config/reference tests pass.

### Task 3: Report Writer, Runner, CLI, And Artifact

**Files:**
- Create: `src/mabd_reproduction/heavy_top_reports.py`
- Modify: `src/mabd_reproduction/experiment_runner.py`
- Modify: `scripts/run_experiment.py`
- Modify: `tests/test_experiment_runner.py`
- Create: `reports/experiment_matrix/single_body_heavy_top_rk4_reference.json`

- [ ] **Step 1: Add report/runner RED tests**

Add tests for `run_heavy_top_rk4_reference(...)` and CLI lane
`heavy_top_rk4_reference`. Assert:

- `claim_id == experiment.single_body.heavy_top`;
- `baseline_lane == rbd_rk4_reference`;
- `solver_mode == heavy_top_rk4_reference_diagnostic`;
- `status == incomplete`;
- `observed.full_experiment_claim_passed is False`;
- blockers include `exact_heavy_top_inertia_unknown`,
  `raw_heavy_top_reference_curve_data_missing`, `mabd_newton_report_missing`,
  and `heavy_top_comparison_report_missing`;
- CLI stdout is valid JSON.

- [ ] **Step 2: Implement report writer**

`write_heavy_top_rk4_reference_report(...)` writes a full-schema `ClaimReport`
with finite samples, source metadata, threshold violations, and incomplete
status.

- [ ] **Step 3: Add runner and CLI dispatch**

Add `run_heavy_top_rk4_reference(...)` to `experiment_runner.py`, export it,
and extend `scripts/run_experiment.py` choices/dispatch with
`heavy_top_rk4_reference`.

- [ ] **Step 4: Generate report artifact**

After implementation commit, regenerate:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/run_experiment.py \
  --lane heavy_top_rk4_reference \
  --config configs/experiments/single_body_heavy_top.yaml \
  --matrix configs/experiments/paper_experiment_matrix.yaml \
  --source-commit PHASE49_IMPLEMENTATION_COMMIT \
  --vendored-newton-commit 96713fa965463b69c229a4d30582c733ff3526bb \
  --output reports/experiment_matrix/single_body_heavy_top_rk4_reference.json
```

### Task 4: Claim Boundaries, Record, And Validator

**Files:**
- Modify: `docs/reference/claim-boundaries.md`
- Create: `docs/records/2026-05-18-phase49-heavy-top-rk4-reference.md`
- Modify: `scripts/validate_docs.py`
- Modify: `tests/test_phase0_bootstrap.py`

- [ ] **Step 1: Add boundary text**

State that Phase49 verifies only the heavy-top RK4 reference diagnostic lane and
does not verify paper-faithful inertia, M-ABD heavy-top dynamics, implicit RBD
baseline parity, raw curve agreement, paper timing, or any passed
`experiment.*` claim.

- [ ] **Step 2: Add dated record**

Record worktree, branch, base commit, spec commit, implementation commit,
report source commit, paper source lines, figure hash, environment, RED/GREEN
evidence, artifact path, and verification commands.

- [ ] **Step 3: Extend docs validator**

Require Phase49 record/spec/plan/boundary snippets, validate the config against
the experiment matrix, recompute the RK4 rollout and compare report metrics and
samples, require source commit not placeholder, require blockers, and require
`experiment.single_body.heavy_top` in `paper-claims.yaml` to remain `intended`.

### Task 5: Verification, Commit, Merge, Push

**Files:** all Phase49 changes.

- [ ] **Step 1: Run focused gates**

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_heavy_top_reference tests.test_experiment_run_configs tests.test_experiment_runner tests.test_phase0_bootstrap
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

- [ ] **Step 3: Integrate**

Fast-forward `main`, rerun main gates, push `origin main`, and keep the claim
boundary explicit that Phase49 is not a passed heavy-top experiment.
