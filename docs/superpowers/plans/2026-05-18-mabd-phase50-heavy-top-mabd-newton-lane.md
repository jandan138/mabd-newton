# Phase 50 Heavy Top MABD Newton Lane Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a formal but incomplete heavy-top `mabd_newton` diagnostic report lane.

**Architecture:** Extend the heavy-top config with a short model-derived
SolverMABD diagnostic, implement a rollout module modeled on the physical
pendulum lane, write a full-schema incomplete report, add runner/CLI dispatch,
and bind the new artifact into docs/provenance checks.

**Tech Stack:** Python 3.10, NumPy, vendored Newton `SolverMABD`, `unittest`,
PyYAML, existing `mabd-newton-py310` isolated environment.

---

### Task 1: RED Tests

**Files:**
- Modify: `tests/test_experiment_run_configs.py`
- Create: `tests/test_heavy_top_mabd.py`
- Modify: `tests/test_experiment_runner.py`
- Modify: `tests/test_phase0_bootstrap.py`

- [ ] **Step 1: Add config expectations**

Assert `load_heavy_top_config(...)` exposes `config.mabd_newton`, with:

```python
self.assertEqual(config.required_missing_lanes, ())
self.assertEqual(config.mabd_newton.output_report, "reports/experiment_matrix/single_body_heavy_top_mabd_newton.json")
self.assertEqual(config.mabd_newton.rotation_mode, "polar")
self.assertIn("max_pivot_residual_m", config.mabd_newton.thresholds)
```

Assert matrix validation rejects missing `mabd_newton_report_incomplete`.

- [ ] **Step 2: Add rollout tests**

Create `tests/test_heavy_top_mabd.py` and assert
`roll_out_heavy_top_mabd_model_derived(config)` returns finite compact samples,
uses `solver_model_config_source = newton_model_derived`, records custom
frequencies `("mabd:body", "mabd:world_constraint", "mabd:gravity")`, keeps
the pivot residual under threshold, and returns nonconstant nutation samples.

- [ ] **Step 3: Add report/runner tests**

Assert `run_heavy_top_mabd_newton(...)` writes a report with
`baseline_lane = "mabd_newton"`, `solver_mode =
"mabd_cpu_oracle_heavy_top_newton_lane"`, `status = incomplete`,
`observed.full_experiment_claim_passed is False`, no `lane_gate_status`, and
blocking reasons including `mabd_newton_report_incomplete`,
`exact_heavy_top_geometry_unknown`, and `heavy_top_comparison_report_missing`.

- [ ] **Step 4: Verify RED**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_heavy_top_mabd tests.test_experiment_run_configs tests.test_experiment_runner tests.test_phase0_bootstrap
```

Expected: fail because `heavy_top_mabd` and `heavy_top_mabd_newton` config and
runner support do not exist.

### Task 2: Implement Config And Rollout

**Files:**
- Modify: `configs/experiments/single_body_heavy_top.yaml`
- Modify: `configs/experiments/paper_experiment_matrix.yaml`
- Modify: `docs/reference/paper-claims.yaml`
- Modify: `src/mabd_reproduction/experiment_configs.py`
- Create: `src/mabd_reproduction/heavy_top_mabd.py`

- [ ] **Step 1: Add config dataclass and parser**

Add `HeavyTopMABDNewtonConfig` with time step, step count, sample count,
diagnostic rest points, masses, pivot/world constraint points, rotation mode,
output report, and thresholds. Require `required_missing_lanes == ()` once the
formal lane exists.

- [ ] **Step 2: Add model-derived rollout**

Build a Newton model with one `mabd:body`, one `mabd:world_constraint`, and one
enabled `mabd:gravity` row. Assign initial affine orientation from the Phase 49
tilt and initial affine velocity from body spin. Step through `SolverMABD.step`.

- [ ] **Step 3: Verify GREEN for rollout/config**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_heavy_top_mabd tests.test_experiment_run_configs
```

Expected: new heavy-top MABD config and rollout tests pass.

### Task 3: Report, Runner, CLI, And Artifact

**Files:**
- Modify: `src/mabd_reproduction/heavy_top_reports.py`
- Modify: `src/mabd_reproduction/experiment_runner.py`
- Modify: `scripts/run_experiment.py`
- Create: `reports/experiment_matrix/single_body_heavy_top_mabd_newton.json`

- [ ] **Step 1: Add report writer**

Write `write_heavy_top_mabd_newton_report(...)` with full schema, incomplete
status, compact sample rows, source metadata, retained blockers, and no pass
gate.

- [ ] **Step 2: Add runner/CLI dispatch**

Expose `run_heavy_top_mabd_newton(...)` and the CLI lane
`heavy_top_mabd_newton`.

- [ ] **Step 3: Generate artifact**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/run_experiment.py --lane heavy_top_mabd_newton --config configs/experiments/single_body_heavy_top.yaml --matrix configs/experiments/paper_experiment_matrix.yaml --source-commit PHASE50_COMMIT --vendored-newton-commit 96713fa965463b69c229a4d30582c733ff3526bb --output reports/experiment_matrix/single_body_heavy_top_mabd_newton.json
```

### Task 4: Docs, Validator, And Final Gates

**Files:**
- Create: `docs/records/2026-05-18-phase50-heavy-top-mabd-newton-lane.md`
- Modify: `docs/reference/claim-boundaries.md`
- Modify: `scripts/validate_docs.py`
- Modify: `tests/test_phase0_bootstrap.py`

- [ ] **Step 1: Record Phase 50**

Record branch, source commit, artifact hash, canonical Python, retained
blockers, and explicit non-claims.

- [ ] **Step 2: Extend docs validator**

Require the Phase 50 record, report, matrix blocker transition, and claim
boundary text.

- [ ] **Step 3: Run final gates**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/env/readiness_check.py
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"
npm --prefix site run validate
git diff --check
```
