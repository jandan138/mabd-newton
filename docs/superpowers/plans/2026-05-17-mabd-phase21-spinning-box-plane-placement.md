# Phase 21 Spinning-Box Plane Placement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Correct the configured spinning-box initial pose so the cube rests on the frictionless plane without initial penetration.

**Architecture:** Keep the existing M-ABD development lane incomplete. Update the scene config, tighten report/config tests around contact signed distances, and record Phase 21 claim boundaries without enabling any passed experiment claim.

**Tech Stack:** Python 3.10, NumPy, PyYAML, `unittest`, vendored Newton M-ABD CPU oracle, canonical `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python`.

---

### Task 1: Plane-Aligned Config And Report Diagnostics

**Files:**
- Modify: `configs/experiments/single_body_spinning_box.yaml`
- Modify: `tests/test_experiment_run_configs.py`
- Modify: `tests/test_single_body_report_lane.py`

- [ ] **Step 1: Write failing config/report assertions**

Add config assertions:

```python
self.assertAlmostEqual(float(config.initial_q[10]), 0.05)
```

Add report/contact assertions:

```python
self.assertEqual(diagnostics.active_contact_count, 0)
self.assertAlmostEqual(diagnostics.min_signed_distance, 0.0)
self.assertAlmostEqual(diagnostics.max_penetration_depth, 0.0)
self.assertTrue(np.allclose(diagnostics.total_normal_force, np.zeros(3)))
self.assertTrue(np.allclose(diagnostics.total_generalized_force, np.zeros(12)))
self.assertEqual(loaded.observed["contact_active_count"], 0)
self.assertAlmostEqual(loaded.observed["contact_min_signed_distance_m"], 0.0)
self.assertAlmostEqual(loaded.observed["contact_max_penetration_m"], 0.0)
```

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_run_configs tests.test_single_body_report_lane
```

Expected: fails because `initial_q[10]` is `0.0`, four corners are penetrating, and the total contact force is nonzero.

- [ ] **Step 2: Update the config**

Change `simulation.initial_q[10]` in
`configs/experiments/single_body_spinning_box.yaml` from `0.0` to `0.05`.

- [ ] **Step 3: Verify and commit**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_run_configs tests.test_single_body_report_lane
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check tests/test_experiment_run_configs.py tests/test_single_body_report_lane.py
git diff --check
```

Commit:

```bash
git add configs/experiments/single_body_spinning_box.yaml tests/test_experiment_run_configs.py tests/test_single_body_report_lane.py
git commit -m "fix: place spinning box on contact plane"
```

### Task 2: Phase 21 Records And Claim Boundaries

**Files:**
- Modify: `docs/reference/claim-boundaries.md`
- Add: `docs/records/2026-05-17-phase21-spinning-box-plane-placement.md`
- Modify: `scripts/validate_docs.py`
- Modify: `tests/test_phase0_bootstrap.py`

- [ ] **Step 1: Write failing docs assertions**

Require claim-boundary snippets:

```python
"Phase 21 verifies the configured spinning-box resting pose"
"contact_min_signed_distance_m = 0.0"
"Phase 21 does not verify the paper spinning-box experiment"
```

Require record snippets:

```python
"## Status\n\npassed"
"configs/experiments/single_body_spinning_box.yaml"
"contact_active_count = 0"
"contact_total_generalized_force = [0.0] * 12"
"No `experiment.*` claim is passed in this phase."
```

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_phase0_bootstrap
```

Expected: fails because Phase 21 boundary and record evidence do not exist.

- [ ] **Step 2: Add docs, validator, and record**

Add the Phase 21 current/verified/non-claim bullets, add the dated record, and
teach `scripts/validate_docs.py` to require the new record and config value
`initial_q[10] == 0.05`.

- [ ] **Step 3: Verify and commit**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_phase0_bootstrap
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check scripts/validate_docs.py tests/test_phase0_bootstrap.py
git diff --check
```

Commit:

```bash
git add docs/reference/claim-boundaries.md docs/records/2026-05-17-phase21-spinning-box-plane-placement.md scripts/validate_docs.py tests/test_phase0_bootstrap.py
git commit -m "docs: record Phase 21 plane placement"
```

### Task 3: Final Verification And Review

**Files:**
- No source edits unless verification or review exposes a defect.

- [ ] **Step 1: Run full gates**

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/env/readiness_check.py
git diff --check
```

- [ ] **Step 2: Request review**

Request read-only review focused on plane placement, no-overclaim docs, and
generated artifact policy. Fix any blocking findings with tests.

- [ ] **Step 3: Merge and push**

Fast-forward merge to `main`, rerun full gates on `main`, push, remove the
worktree, and delete the local branch.
