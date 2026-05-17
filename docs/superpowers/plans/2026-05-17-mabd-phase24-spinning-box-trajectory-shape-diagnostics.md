# Phase 24 Spinning-Box Trajectory And Shape Diagnostics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add per-step trajectory samples and affine shape diagnostics to the existing spinning-box M-ABD and RBD development reports.

**Architecture:** Keep report status `incomplete`. Add a small affine-shape helper in shared spinning-box physics, use it from the M-ABD report writer, and record RBD samples from the Newton semi-implicit stepping loop. Do not add paper-pass logic or committed generated report artifacts.

**Tech Stack:** Python 3.10, NumPy, vendored Newton/Warp, `unittest`, Markdown records, `scripts/validate_docs.py`.

---

### Task 1: M-ABD Trajectory And Affine Shape Diagnostics

**Files:**
- Modify: `src/mabd_reproduction/spinning_box_physics.py`
- Modify: `src/mabd_reproduction/single_body_reports.py`
- Modify: `tests/test_single_body_report_lane.py`

- [ ] **Step 1: Write the failing test**

In `tests/test_single_body_report_lane.py`, extend `test_spinning_box_report_uses_run_config` with:

```python
samples = loaded.observed["trajectory_samples"]
self.assertEqual(len(samples), config.step_count + 1)
self.assertEqual(samples[0]["step_index"], 0)
self.assertEqual(samples[-1]["step_index"], config.step_count)
self.assertEqual(samples[0]["position_m"], [0.0, 0.05, 0.0])
np.testing.assert_allclose(samples[-1]["position_m"], [4.0, 0.05, 0.0], atol=1.0e-12)
self.assertEqual(len(samples[-1]["affine_matrix"]), 3)
self.assertEqual(len(samples[-1]["affine_matrix"][0]), 3)
self.assertEqual(len(samples[-1]["affine_singular_values"]), 3)
self.assertAlmostEqual(samples[0]["affine_orthogonality_error"], 0.0)
self.assertGreater(samples[-1]["affine_orthogonality_error"], 1.0e6)
self.assertEqual(loaded.observed["initial_affine_orthogonality_error"], 0.0)
self.assertGreater(loaded.observed["final_affine_orthogonality_error"], 1.0e6)
self.assertGreater(loaded.observed["final_affine_determinant"], 1.0e6)
self.assertEqual(
    loaded.observed["affine_shape_diagnostic_status"],
    "development_gap_observed",
)
```

- [ ] **Step 2: Run RED**

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_single_body_report_lane
```

Expected: fails with `KeyError: 'trajectory_samples'`.

- [ ] **Step 3: Add affine shape helper**

In `src/mabd_reproduction/spinning_box_physics.py`, add:

```python
@dataclass(frozen=True)
class SpinningBoxAffineShapeDiagnostics:
    affine_matrix: np.ndarray
    determinant: float
    singular_values: np.ndarray
    orthogonality_error: float


def spinning_box_affine_shape_diagnostics(q: np.ndarray) -> SpinningBoxAffineShapeDiagnostics:
    A, _t = mabd.unpack_q(q)
    return SpinningBoxAffineShapeDiagnostics(
        affine_matrix=A,
        determinant=float(np.linalg.det(A)),
        singular_values=np.linalg.svd(A, compute_uv=False),
        orthogonality_error=float(np.linalg.norm(A.T @ A - np.eye(3))),
    )
```

Export both names from `__all__`.

- [ ] **Step 4: Record M-ABD samples**

In `src/mabd_reproduction/single_body_reports.py`, add a local helper:

```python
def _mabd_trajectory_sample(
    *,
    config: SpinningBoxRunConfig,
    q: np.ndarray,
    qd: np.ndarray,
    mass_matrix: np.ndarray,
    step_index: int,
) -> dict[str, object]:
    shape = spinning_box_affine_shape_diagnostics(q)
    momentum = mabd_momentum_diagnostics(config, q, qd)
    return {
        "step_index": int(step_index),
        "time_s": float(step_index * config.time_step_s),
        "position_m": q[9:12].tolist(),
        "energy_j": _kinetic_energy(qd, mass_matrix),
        "linear_momentum_error": momentum.linear_momentum_error,
        "angular_momentum_error": momentum.angular_momentum_error,
        "affine_matrix": shape.affine_matrix.tolist(),
        "affine_determinant": shape.determinant,
        "affine_singular_values": shape.singular_values.tolist(),
        "affine_orthogonality_error": shape.orthogonality_error,
    }
```

Build `trajectory_samples` only when `config is not None` by appending the
initial sample and one sample after each step. Promote the initial/final affine
fields into `observed`.

- [ ] **Step 5: Run GREEN**

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_single_body_report_lane
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check src/mabd_reproduction/spinning_box_physics.py src/mabd_reproduction/single_body_reports.py tests/test_single_body_report_lane.py
git diff --check
```

- [ ] **Step 6: Commit**

```bash
git add src/mabd_reproduction/spinning_box_physics.py src/mabd_reproduction/single_body_reports.py tests/test_single_body_report_lane.py
git commit -m "feat: report spinning box M-ABD trajectory diagnostics"
```

### Task 2: RBD Baseline Trajectory Samples

**Files:**
- Modify: `src/mabd_reproduction/rigid_baselines.py`
- Modify: `tests/test_rigid_baselines.py`

- [ ] **Step 1: Write the failing test**

In `tests/test_rigid_baselines.py`, extend `test_run_spinning_box_rbd_baseline_is_deterministic_and_incomplete`:

```python
self.assertEqual(len(result.trajectory_samples), config.step_count + 1)
self.assertEqual(result.trajectory_samples[0]["step_index"], 0)
self.assertEqual(result.trajectory_samples[-1]["step_index"], config.step_count)
np.testing.assert_allclose(result.trajectory_samples[0]["position_m"], [0.0, 0.05, 0.0], atol=1.0e-15)
np.testing.assert_allclose(result.trajectory_samples[-1]["position_m"], [4.0, 0.05, 0.0], atol=1.0e-6)
self.assertIn("rotation_xyzw", result.trajectory_samples[-1])
```

In `test_write_spinning_box_rbd_baseline_report`, add:

```python
self.assertIn("trajectory_samples", loaded.observed)
self.assertEqual(len(loaded.observed["trajectory_samples"]), config.step_count + 1)
self.assertIn("rotation_xyzw", loaded.observed["trajectory_samples"][-1])
```

- [ ] **Step 2: Run RED**

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_rigid_baselines
```

Expected: fails with `AttributeError` or missing `trajectory_samples`.

- [ ] **Step 3: Add RBD sampling**

In `SpinningBoxRBDBaselineResult`, add:

```python
trajectory_samples: tuple[dict[str, object], ...]
```

Create `_rbd_trajectory_sample(...)` that records step index, time, position,
rotation, kinetic energy, linear momentum error, and angular momentum error.
Update `_run_newton_semimplicit_free_body` to collect the step 0 sample and
one sample after each solver step, then return it. Add
`"trajectory_samples": list(result.trajectory_samples)` to the report observed
mapping.

- [ ] **Step 4: Run GREEN**

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_rigid_baselines
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check src/mabd_reproduction/rigid_baselines.py tests/test_rigid_baselines.py
git diff --check
```

- [ ] **Step 5: Commit**

```bash
git add src/mabd_reproduction/rigid_baselines.py tests/test_rigid_baselines.py
git commit -m "feat: report spinning box RBD trajectory diagnostics"
```

### Task 3: Phase 24 Docs And Gates

**Files:**
- Modify: `docs/reference/claim-boundaries.md`
- Create: `docs/records/2026-05-17-phase24-spinning-box-trajectory-shape-diagnostics.md`
- Modify: `scripts/validate_docs.py`
- Modify: `tests/test_phase0_bootstrap.py`

- [ ] **Step 1: Write failing docs tests**

Add Phase 24 bootstrap tests requiring:

```python
"This repository contains Phase 24"
"spinning-box trajectory samples"
"affine shape diagnostics"
"trajectory_samples"
"final_affine_orthogonality_error"
"affine_shape_diagnostic_status"
"development_gap_observed"
"Phase 24 does not verify the paper spinning-box experiment"
"paper trajectory agreement"
"any passed `experiment.*` claim"
"Phase 0/1/.../23/24 docs/provenance validation passed"
```

- [ ] **Step 2: Run RED**

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_phase0_bootstrap
```

Expected: missing Phase 24 boundary, record, and validator output.

- [ ] **Step 3: Add docs, record, and validator checks**

Update claim boundaries with Phase 24 current/verified/non-claim bullets.

Create the Phase 24 record with status `passed`, config path, plan and
implementation commits, vendored Newton commit, paper SHA256 values,
environment clone details, metrics, TDD evidence, and explicit no-claim
language.

Update `scripts/validate_docs.py` to require the Phase 24 record, validate
Phase 24 boundary text, validate record snippets, and print `/24`.

- [ ] **Step 4: Run docs GREEN**

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_phase0_bootstrap
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check scripts/validate_docs.py tests/test_phase0_bootstrap.py
git diff --check
```

- [ ] **Step 5: Commit and harden provenance**

Commit the docs record, then backfill the docs/provenance commit hash into the
record, validator, and test. Re-run focused docs checks and commit the
hardening change.

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

Review 1: trajectory and affine shape metric semantics.

Review 2: claim/provenance boundaries and no-paper-pass language.

- [ ] **Step 3: Merge, verify on main, push, cleanup**

Fast-forward merge to `main`, re-run full gates on main, push `main`, remove
the worktree, and delete the branch.
