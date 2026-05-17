# Phase 32 Gravity Force Mapping Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add uniform gravity generalized-force assembly to the Newton vendored M-ABD CPU oracle.

**Architecture:** Implement a small public helper that maps point-mass gravity through affine point Jacobians, then wire optional `gravity` into `MABDCPUOracleConfig`. Keep the feature bounded to CPU oracle method evidence and update records/validators without passing experiment claims.

**Tech Stack:** Python 3.10, NumPy, Newton vendored M-ABD modules, `unittest`, PyYAML, existing isolated `mabd-newton-py310` environment.

---

### Task 1: Add Failing Gravity Mapping Tests

**Files:**
- Modify: `tests/test_mabd_single_body.py`
- Modify: `tests/test_mabd_phase4_solver_step.py`
- Modify: `vendor/newton/newton/tests/test_mabd_single_body.py`
- Modify: `vendor/newton/newton/tests/test_mabd_phase4_solver_step.py`

- [x] **Step 1: Add helper-level gravity test**

Add a test that calls `mabd.gravity_generalized_force(points, masses, gravity)`
and compares it with explicit `sum(point_jacobian(point).T @ (mass * gravity))`.

- [x] **Step 2: Add CPU oracle step gravity test**

Add a test that constructs `MABDCPUOracleConfig(..., gravity=gravity)`, runs one
unconstrained CPU oracle step from rest, and checks `q_next`, `qd_next`, and
`dq` against solving `H dq = gravity_generalized_force(...)`.

- [x] **Step 3: Verify RED**

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_mabd_single_body tests.test_mabd_phase4_solver_step
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest newton.tests.test_mabd_single_body newton.tests.test_mabd_phase4_solver_step
```

Expected: fail because `gravity_generalized_force` and `MABDCPUOracleConfig.gravity`
do not exist yet.

### Task 2: Implement Gravity Force Mapping

**Files:**
- Modify: `vendor/newton/newton/_src/solvers/mabd/affine_math.py`
- Modify: `vendor/newton/newton/_src/solvers/mabd/__init__.py`
- Modify: `vendor/newton/newton/_src/solvers/mabd/step_oracle.py`

- [x] **Step 1: Add `gravity_generalized_force`**

Use existing validation helpers and `point_jacobian` to assemble:

```python
out = np.zeros(12, dtype=float)
for point, mass in zip(points, masses, strict=True):
    out += point_jacobian(point).T @ (float(mass) * gravity_arr)
```

- [x] **Step 2: Export the helper**

Import and expose the helper from `mabd/__init__.py`.

- [x] **Step 3: Wire optional gravity into `MABDCPUOracleConfig`**

Add `gravity: np.ndarray | None = None` and combine assembled gravity forces
with configured external forces before actuation forces.

- [x] **Step 4: Verify GREEN**

Run the RED commands again. Expected: all tests pass.

### Task 3: Update Claim Evidence And Validators

**Files:**
- Modify: `docs/reference/paper-claims.yaml`
- Modify: `docs/reference/claim-boundaries.md`
- Create: `docs/records/2026-05-17-phase32-gravity-force-mapping.md`
- Modify: `scripts/validate_docs.py`
- Modify: `tests/test_phase0_bootstrap.py`

- [x] **Step 1: Add method claim**

Add `method.force_mapping.gravity_generalized_force` with status `passed` and a
conflict note that this is CPU oracle force mapping only.

- [x] **Step 2: Add claim boundary bullets**

Record Phase 32 current, verified, non-claim, and forbidden overclaim bullets.

- [x] **Step 3: Add dated record**

Record base commit `f8d36da`, vendored Newton source commit
`96713fa965463b69c229a4d30582c733ff3526bb`, paper source lines,
environment, tests, and claim impact.

- [x] **Step 4: Extend validator and bootstrap tests**

Require the new spec, plan, record, claim, boundary snippets, final validator
message `/32`, and no `experiment.*` passed statuses.

### Task 4: Verify, Commit, Merge, Push

**Files:** all Phase 32 files.

- [x] **Step 1: Run focused gates**

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_mabd_single_body tests.test_mabd_phase4_solver_step tests.test_phase0_bootstrap
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest newton.tests.test_mabd_single_body newton.tests.test_mabd_phase4_solver_step
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
```

- [x] **Step 2: Run full gates**

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest newton.tests.test_mabd_single_body newton.tests.test_mabd_phase4_solver_step
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/env/readiness_check.py
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"
git diff --check
```

- [ ] **Step 3: Commit, merge, and push**

Commit on `phase32-gravity-force-mapping`, fast-forward merge to `main`, rerun
main gates, push `origin/main`, then remove the worktree.
