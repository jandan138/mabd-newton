# Phase 22 RBD Plane Placement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Align the Newton RBD development baseline initial position with the configured spinning-box plane placement.

**Architecture:** Keep the lane incomplete and Newton-only. Thread `config.initial_q[9:12]` into the RBD body transform, report `initial_position_m`, and extend validator/docs evidence without changing solver mode or experiment status.

**Tech Stack:** Python 3.10, NumPy, vendored Newton/Warp, `unittest`, Markdown records, `scripts/validate_docs.py`.

---

### Task 1: RBD Baseline Pose Alignment

**Files:**
- Modify: `src/mabd_reproduction/rigid_baselines.py`
- Modify: `tests/test_rigid_baselines.py`

- [ ] **Step 1: Write the failing tests**

In `tests/test_rigid_baselines.py`, update `test_run_spinning_box_rbd_baseline_is_deterministic_and_incomplete`:

```python
np.testing.assert_allclose(result.initial_position_m, [0.0, 0.05, 0.0], atol=1.0e-15)
np.testing.assert_allclose(result.final_position_m, [4.0, 0.05, 0.0], atol=1.0e-6)
```

In `test_write_spinning_box_rbd_baseline_report`, add:

```python
self.assertEqual(loaded.observed["initial_position_m"], [0.0, 0.05, 0.0])
self.assertEqual(loaded.observed["final_position_m"][1], 0.05)
```

- [ ] **Step 2: Run the focused RED test**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_rigid_baselines
```

Expected: fails because `SpinningBoxRBDBaselineResult` has no `initial_position_m` and the final RBD position y component is still `0.0`.

- [ ] **Step 3: Implement the minimal RBD pose wiring**

In `src/mabd_reproduction/rigid_baselines.py`, add `initial_position_m: np.ndarray` to `SpinningBoxRBDBaselineResult`.

Change `_run_newton_semimplicit_free_body(...)` so it reads:

```python
initial_position = np.asarray(config.initial_q[9:12], dtype=float)
...
body = builder.add_body(
    xform=wp.transform(wp.vec3(*initial_position.tolist()), wp.quat_identity()),
    mass=properties.mass_kg,
    inertia=inertia,
    lock_inertia=True,
    label="spinning_box_rbd_baseline",
)
```

Change the return value to include `initial_position`, and assign it into `SpinningBoxRBDBaselineResult`.

In `write_spinning_box_rbd_baseline_report`, add:

```python
"initial_position_m": result.initial_position_m.tolist(),
```

- [ ] **Step 4: Run the focused GREEN test**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_rigid_baselines
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check src/mabd_reproduction/rigid_baselines.py tests/test_rigid_baselines.py
git diff --check
```

Expected: RBD tests pass, ruff passes, and whitespace check is clean.

- [ ] **Step 5: Commit**

```bash
git add src/mabd_reproduction/rigid_baselines.py tests/test_rigid_baselines.py
git commit -m "fix: align RBD spinning box initial pose"
```

### Task 2: Phase 22 Records And Validator Gates

**Files:**
- Modify: `docs/reference/claim-boundaries.md`
- Create: `docs/records/2026-05-17-phase22-rbd-plane-placement.md`
- Modify: `scripts/validate_docs.py`
- Modify: `tests/test_phase0_bootstrap.py`

- [ ] **Step 1: Write failing docs tests**

In `tests/test_phase0_bootstrap.py`, add Phase 22 tests requiring:

```python
"Phase 22 verifies"
"RBD development baseline consumes the configured spinning-box initial translation"
"initial_position_m = [0.0, 0.05, 0.0]"
"final_position_m = [4.0, 0.05, 0.0]"
"Phase 22 does not verify the paper spinning-box experiment"
"paper-faithful implicit RBD baseline"
"any passed `experiment.*` claim"
"docs/provenance validation passed"  # output must include /22
```

- [ ] **Step 2: Run the docs RED test**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_phase0_bootstrap
```

Expected: fails because Phase 22 boundary/record text does not exist and validator output ends at Phase 21.

- [ ] **Step 3: Add docs, record, and validator checks**

Update `docs/reference/claim-boundaries.md` with Phase 22 current/verified/non-claim bullets.

Create `docs/records/2026-05-17-phase22-rbd-plane-placement.md` with:

- status `passed`;
- config path `configs/experiments/single_body_spinning_box.yaml`;
- plan commit and implementation commit;
- vendored Newton commit `96713fa965463b69c229a4d30582c733ff3526bb`;
- paper PDF and TeX SHA256 values;
- environment clone details;
- `initial_position_m = [0.0, 0.05, 0.0]`;
- `final_position_m = [4.0, 0.05, 0.0]`;
- explicit no-claim language.

Update `scripts/validate_docs.py`:

- docstring and output include `/22`;
- `REQUIRED_PATHS` includes the Phase 22 record;
- `validate_claim_boundaries()` checks Phase 22 bullets;
- add `validate_phase22_record()`;
- call it from `main()`.

- [ ] **Step 4: Run docs GREEN checks**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_phase0_bootstrap
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check scripts/validate_docs.py tests/test_phase0_bootstrap.py
git diff --check
```

Expected: bootstrap tests pass, validator passes through Phase 22, ruff passes, and whitespace check is clean.

- [ ] **Step 5: Commit**

```bash
git add docs/reference/claim-boundaries.md docs/records/2026-05-17-phase22-rbd-plane-placement.md scripts/validate_docs.py tests/test_phase0_bootstrap.py
git commit -m "docs: record Phase 22 RBD plane placement"
```

### Task 3: Final Verification And Integration

**Files:**
- No code changes expected unless review finds a defect.

- [ ] **Step 1: Run full branch gates**

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/env/readiness_check.py
git diff --check
```

Expected: all commands exit 0; full tests report all tests OK.

- [ ] **Step 2: Request review**

Request read-only review for:

- RBD config/physics behavior: packed q translation, Newton transform, report fields.
- Claim/provenance boundaries: no paper-faithful baseline claim, no passed experiment claim.

- [ ] **Step 3: Merge, verify on main, push, cleanup**

Fast-forward merge to `main`, rerun the full gates on main, push `main`, remove the Phase 22 worktree, and delete the local branch.
