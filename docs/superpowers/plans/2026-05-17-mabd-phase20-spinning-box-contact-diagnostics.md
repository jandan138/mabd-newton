# Phase 20 Spinning-Box Contact Diagnostics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add finite, machine-checkable M-ABD contact-force diagnostics for the procedural spinning-box cube against a frictionless plane.

**Architecture:** Parse a small `contact_surface` config block, derive cube corners from paper cube size, reuse the existing point-plane penalty oracle for each corner, and record diagnostics in the existing M-ABD lane report. Keep all experiment claims incomplete and explicitly bounded.

**Tech Stack:** Python 3.10, NumPy, PyYAML, `unittest`, vendored Newton M-ABD CPU oracle, canonical `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python`.

---

### Task 1: Config Contract

**Files:**
- Modify: `configs/experiments/single_body_spinning_box.yaml`
- Modify: `src/mabd_reproduction/experiment_configs.py`
- Test: `tests/test_experiment_run_configs.py`

- [ ] **Step 1: Write failing config tests**

Add assertions that the spinning-box config exposes:

```python
self.assertEqual(config.contact_surface["type"], "plane")
self.assertEqual(config.contact_surface["plane_normal"], (0.0, 1.0, 0.0))
self.assertEqual(config.contact_surface["plane_offset"], 0.0)
self.assertGreater(config.contact_surface["stiffness"], 0.0)
self.assertGreaterEqual(config.contact_surface["damping"], 0.0)
```

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_run_configs
```

Expected: fails because `SpinningBoxRunConfig` has no `contact_surface`.

- [ ] **Step 2: Implement config parsing**

Add `contact_surface: dict[str, object]` to `SpinningBoxRunConfig`, parse the
YAML mapping, normalize the plane normal into a 3-tuple of floats, and validate
positive stiffness plus nonnegative damping.

- [ ] **Step 3: Add YAML block**

Add:

```yaml
contact_surface:
  type: plane
  plane_normal: [0.0, 1.0, 0.0]
  plane_offset: 0.0
  stiffness: 1000000.0
  damping: 100.0
```

- [ ] **Step 4: Verify and commit**

Run the focused config tests and commit:

```bash
git add configs/experiments/single_body_spinning_box.yaml src/mabd_reproduction/experiment_configs.py tests/test_experiment_run_configs.py
git commit -m "feat: configure spinning-box contact surface"
```

### Task 2: Contact Diagnostics Helper

**Files:**
- Modify: `src/mabd_reproduction/spinning_box_physics.py`
- Test: `tests/test_single_body_report_lane.py`

- [ ] **Step 1: Write failing helper tests**

Add a test that loads the spinning-box config, derives eight corners at
`+/- cube_size_m / 2`, evaluates diagnostics at the configured initial `q/qd`,
and checks:

```python
self.assertEqual(corners.shape, (8, 3))
self.assertAlmostEqual(float(corners[:, 0].max()), 0.05)
self.assertAlmostEqual(float(corners[:, 0].min()), -0.05)
self.assertEqual(diagnostics.corner_count, 8)
self.assertGreaterEqual(diagnostics.active_contact_count, 0)
self.assertEqual(len(diagnostics.corner_signed_distances), 8)
self.assertEqual(diagnostics.total_generalized_force.shape, (12,))
```

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_single_body_report_lane
```

Expected: import failure for the new helper names.

- [ ] **Step 2: Implement helpers**

Add frozen dataclass `SpinningBoxContactDiagnostics`, then implement
`spinning_box_cube_corners(config)` and
`spinning_box_contact_diagnostics(config, q, qd)` using
`mabd.evaluate_point_plane_penalty_contact` over the eight corners.

- [ ] **Step 3: Verify and commit**

Run focused tests and ruff:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_single_body_report_lane
/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check src/mabd_reproduction/spinning_box_physics.py tests/test_single_body_report_lane.py
```

Commit:

```bash
git add src/mabd_reproduction/spinning_box_physics.py tests/test_single_body_report_lane.py
git commit -m "feat: derive spinning-box contact diagnostics"
```

### Task 3: Report Fields And Claim Boundaries

**Files:**
- Modify: `src/mabd_reproduction/single_body_reports.py`
- Modify: `docs/reference/claim-boundaries.md`
- Modify: `docs/records/2026-05-17-phase20-spinning-box-contact-diagnostics.md`
- Modify: `scripts/validate_docs.py`
- Modify: `tests/test_phase0_bootstrap.py`
- Test: `tests/test_single_body_report_lane.py`, `tests/test_phase0_bootstrap.py`

- [ ] **Step 1: Write failing report tests**

Assert configured M-ABD reports include:

```python
self.assertEqual(loaded.observed["contact_surface_type"], "plane")
self.assertEqual(loaded.observed["contact_corner_count"], 8)
self.assertIn("contact_active_count", loaded.observed)
self.assertIn("contact_min_signed_distance_m", loaded.observed)
self.assertIn("contact_max_penetration_m", loaded.observed)
self.assertIn("contact_total_normal_force_n", loaded.observed)
self.assertIn("contact_total_generalized_force", loaded.observed)
self.assertEqual(len(loaded.observed["contact_corner_signed_distances_m"]), 8)
self.assertEqual(len(loaded.observed["contact_total_generalized_force"]), 12)
```

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_single_body_report_lane
```

Expected: missing observed keys.

- [ ] **Step 2: Implement report fields**

Call `spinning_box_contact_diagnostics` in
`write_spinning_box_development_report` when config is present and add the
fields above to `observed`.

- [ ] **Step 3: Add record and validators**

Create the Phase 20 record with scope, commits, paper source checksums,
environment, contact diagnostic fields, TDD evidence, final verification
commands, and explicit non-claims. Update `claim-boundaries.md`,
`scripts/validate_docs.py`, and `tests/test_phase0_bootstrap.py` to require the
Phase 20 bounded language.

- [ ] **Step 4: Verify and commit**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_single_body_report_lane tests.test_phase0_bootstrap
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check src/mabd_reproduction scripts/validate_docs.py tests
```

Commit:

```bash
git add src/mabd_reproduction/single_body_reports.py docs/reference/claim-boundaries.md docs/records/2026-05-17-phase20-spinning-box-contact-diagnostics.md scripts/validate_docs.py tests/test_phase0_bootstrap.py tests/test_single_body_report_lane.py
git commit -m "docs: record Phase 20 contact diagnostics"
```

### Task 4: Final Verification

**Files:**
- No source edits unless verification exposes a defect.

- [ ] **Step 1: Run full gates**

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"
git diff --check
```

- [ ] **Step 2: Review**

Request independent review focused on overclaiming contact evidence, finite
diagnostic fields, and report compatibility. Fix findings with tests.

- [ ] **Step 3: Merge**

Fast-forward merge to `main`, rerun full gates on `main`, push, remove the
worktree, and delete the local branch.

