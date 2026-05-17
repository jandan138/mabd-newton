# Phase 23 Spinning-Box Position Comparison Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add machine-checkable initial/final position propagation and comparison metrics for the existing spinning-box development lanes.

**Architecture:** Keep the existing report protocol and incomplete experiment status. Add position vectors to the M-ABD lane report, then teach the comparison report to validate and diff finite 3-vectors alongside existing scalar metrics.

**Tech Stack:** Python 3.10, NumPy, vendored Newton/Warp, `unittest`, Markdown records, `scripts/validate_docs.py`.

---

### Task 1: M-ABD Lane Position Fields

**Files:**
- Modify: `src/mabd_reproduction/single_body_reports.py`
- Modify: `tests/test_single_body_report_lane.py`

- [ ] **Step 1: Write the failing test**

In `tests/test_single_body_report_lane.py`, extend `test_spinning_box_report_uses_run_config`:

```python
self.assertEqual(loaded.observed["initial_position_m"], [0.0, 0.05, 0.0])
np.testing.assert_allclose(
    loaded.observed["final_position_m"],
    [4.0, 0.05, 0.0],
    atol=1.0e-12,
)
```

- [ ] **Step 2: Run RED**

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_single_body_report_lane
```

Expected: fails with `KeyError: 'initial_position_m'`.

- [ ] **Step 3: Implement minimal position propagation**

In `write_spinning_box_development_report`, capture `initial_q = q.copy()` before stepping and add to `observed` when `config is not None`:

```python
"initial_position_m": initial_q[9:12].tolist(),
"final_position_m": q[9:12].tolist(),
```

- [ ] **Step 4: Run GREEN**

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_single_body_report_lane
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check src/mabd_reproduction/single_body_reports.py tests/test_single_body_report_lane.py
git diff --check
```

- [ ] **Step 5: Commit**

```bash
git add src/mabd_reproduction/single_body_reports.py tests/test_single_body_report_lane.py
git commit -m "feat: report spinning box M-ABD positions"
```

### Task 2: Comparison Protocol Vector Metrics

**Files:**
- Modify: `src/mabd_reproduction/comparison_reports.py`
- Modify: `tests/test_spinning_box_comparison.py`

- [ ] **Step 1: Write failing comparison tests**

In `test_write_spinning_box_comparison_report_records_incomplete_protocol`, assert:

```python
self.assertEqual(
    loaded.observed["lane_vector_metrics"]["mabd_newton"]["initial_position_m"],
    [0.0, 0.05, 0.0],
)
np.testing.assert_allclose(
    loaded.observed["lane_vector_metrics"]["rbd_implicit_baseline"]["final_position_m"],
    [4.0, 0.05, 0.0],
    atol=1.0e-6,
)
vector_differences = loaded.observed["lane_vector_metric_differences"][
    "mabd_newton_minus_rbd_implicit_baseline"
]
np.testing.assert_allclose(vector_differences["initial_position_m"], [0.0, 0.0, 0.0])
np.testing.assert_allclose(vector_differences["final_position_m"], [0.0, 0.0, 0.0], atol=1.0e-6)
```

Add an invalid vector test that mutates the M-ABD JSON:

```python
data["observed"]["final_position_m"] = [0.0, float("nan"), 0.0]
...
self.assertIn("mabd_newton:final_position_m", loaded.observed["invalid_required_vector_metrics"])
self.assertIn("mabd_newton:final_position_m_invalid", loaded.observed["blocking_reasons"])
```

- [ ] **Step 2: Run RED**

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_spinning_box_comparison
```

Expected: fails because `lane_vector_metrics` and vector invalid lists do not exist.

- [ ] **Step 3: Implement vector metric helpers**

In `src/mabd_reproduction/comparison_reports.py`, add:

```python
SPINNING_BOX_REQUIRED_VECTOR_METRICS = ("initial_position_m", "final_position_m")
```

Add helpers that accept only finite length-three numeric lists/tuples and return `list[float] | None`. Add vector snapshots, missing vectors, invalid vectors, and vector differences to the comparison report `observed`, `expected`, `threshold`, and `blocking_reasons`.

- [ ] **Step 4: Run GREEN**

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_spinning_box_comparison
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check src/mabd_reproduction/comparison_reports.py tests/test_spinning_box_comparison.py
git diff --check
```

- [ ] **Step 5: Commit**

```bash
git add src/mabd_reproduction/comparison_reports.py tests/test_spinning_box_comparison.py
git commit -m "feat: compare spinning box lane positions"
```

### Task 3: Phase 23 Docs And Gates

**Files:**
- Modify: `docs/reference/claim-boundaries.md`
- Create: `docs/records/2026-05-17-phase23-spinning-box-position-comparison.md`
- Modify: `scripts/validate_docs.py`
- Modify: `tests/test_phase0_bootstrap.py`

- [ ] **Step 1: Write failing docs tests**

Add Phase 23 bootstrap tests requiring:

```python
"Phase 23 verifies"
"initial_position_m"
"final_position_m"
"lane_vector_metric_differences"
"Phase 23 does not verify the paper spinning-box experiment"
"paper-faithful implicit RBD baseline"
"any passed `experiment.*` claim"
"Phase 0/1/.../22/23 docs/provenance validation passed"
```

- [ ] **Step 2: Run RED**

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_phase0_bootstrap
```

Expected: missing Phase 23 boundary, record, and validator output.

- [ ] **Step 3: Add docs, record, and validator checks**

Update claim boundaries with Phase 23 current/verified/non-claim bullets.

Create the Phase 23 record with status `passed`, config path, plan and implementation commits, vendored Newton commit, paper SHA256 values, environment clone details, metrics, TDD evidence, and explicit no-claim language.

Update `scripts/validate_docs.py` to require the Phase 23 record, validate Phase 23 boundary text, validate record snippets, and print `/23`.

- [ ] **Step 4: Run docs GREEN**

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_phase0_bootstrap
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check scripts/validate_docs.py tests/test_phase0_bootstrap.py
git diff --check
```

- [ ] **Step 5: Commit and harden provenance**

Commit the docs record, then backfill the docs/provenance commit hash into the record, validator, and test. Re-run focused docs checks and commit the hardening change.

### Task 4: Review, Full Verification, Merge

**Files:**
- No code changes expected unless review finds a defect.

- [ ] **Step 1: Run full gates**

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/env/readiness_check.py
git diff --check
```

- [ ] **Step 2: Request two read-only reviews**

Review 1: position metric behavior and finite vector validation.

Review 2: claim/provenance boundaries and record completeness.

- [ ] **Step 3: Merge, verify on main, push, cleanup**

Fast-forward merge to `main`, re-run full gates on main, push `main`, remove the worktree, and delete the branch.
