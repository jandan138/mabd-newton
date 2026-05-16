# Phase 7 Joint Limits Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a small CPU oracle for the paper's strain-limited joint DOF clamp and explicit dual-space penalty RHS term without claiming generic inequality-constrained M-ABD.

**Architecture:** Keep the feature inside vendored Newton's M-ABD joint helpers. Add immutable joint-limit dataclasses and pure NumPy helpers that clamp a scalar joint DOF to its nearest valid range, produce `k(theta - theta_hat)`, and add those terms to selected KKT lower-RHS entries. Prove the helpers against direct dense KKT behavior and document the narrow boundary.

**Tech Stack:** Python 3.10, NumPy, Newton vendored source, `unittest`, ruff, docs/provenance validator.

---

### Task 1: RED Tests For Joint Limit Clamp And Dual RHS

**Files:**
- Modify: `tests/test_mabd_phase2_joints_kkt.py`
- Modify: `vendor/newton/newton/tests/test_mabd_phase2_joints_kkt.py`

- [ ] **Step 1: Add failing public tests**

Add tests that require:

```python
    def test_joint_limit_clamps_out_of_range_dof_and_penalty_rhs(self) -> None:
        lower = -0.25
        upper = 0.5
        stiffness = 40.0

        low = mabd.evaluate_joint_limit(-0.4, lower, upper, stiffness)
        inside = mabd.evaluate_joint_limit(0.1, lower, upper, stiffness)
        high = mabd.evaluate_joint_limit(0.8, lower, upper, stiffness)

        self.assertTrue(low.active)
        self.assertAlmostEqual(low.clamped_theta, lower)
        self.assertAlmostEqual(low.violation, -0.15)
        self.assertAlmostEqual(low.penalty_rhs, stiffness * (-0.15))
        self.assertFalse(inside.active)
        self.assertAlmostEqual(inside.penalty_rhs, 0.0)
        self.assertTrue(high.active)
        self.assertAlmostEqual(high.clamped_theta, upper)
        self.assertAlmostEqual(high.violation, 0.3)
        self.assertAlmostEqual(high.penalty_rhs, stiffness * 0.3)
```

```python
    def test_joint_limit_penalty_rhs_adds_selected_dual_rows(self) -> None:
        base = np.array([0.0, -0.2, 0.4])
        evaluations = [
            mabd.evaluate_joint_limit(0.8, -0.1, 0.5, 10.0),
            mabd.evaluate_joint_limit(0.0, -0.1, 0.5, 10.0),
        ]

        observed = mabd.apply_joint_limit_penalty_rhs(base, row_indices=[1, 2], evaluations=evaluations)

        expected = base.copy()
        expected[1] += 3.0
        self.assertTrue(np.allclose(observed, expected))
        self.assertTrue(np.allclose(base, [0.0, -0.2, 0.4]))
```

```python
    def test_joint_limit_penalty_rhs_changes_dense_kkt_target(self) -> None:
        H = np.eye(2)
        J = np.array([[1.0, 0.0]])
        f = np.zeros(2)
        limit = mabd.evaluate_joint_limit(0.75, -0.5, 0.25, stiffness=2.0)
        lower_rhs = mabd.apply_joint_limit_penalty_rhs(np.zeros(1), row_indices=[0], evaluations=[limit])

        result = mabd.solve_dense_dual_kkt(H, J, f, lower_rhs=lower_rhs)

        self.assertAlmostEqual(float(lower_rhs[0]), 1.0)
        self.assertTrue(np.allclose(J @ result.dq, lower_rhs))
```

- [ ] **Step 2: Add failing internal mirrors**

Mirror the same behaviors in `vendor/newton/newton/tests/test_mabd_phase2_joints_kkt.py`.

- [ ] **Step 3: Run tests to verify RED**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_mabd_phase2_joints_kkt
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest vendor.newton.newton.tests.test_mabd_phase2_joints_kkt
```

Expected: fail because `evaluate_joint_limit` and `apply_joint_limit_penalty_rhs` are missing.

### Task 2: Implement Joint Limit Helpers

**Files:**
- Modify: `vendor/newton/newton/_src/solvers/mabd/joint_constraints.py`
- Modify: `vendor/newton/newton/_src/solvers/mabd/__init__.py`

- [ ] **Step 1: Add dataclass**

Add `JointLimitEvaluation` with fields:

- `theta`
- `lower`
- `upper`
- `stiffness`
- `clamped_theta`
- `violation`
- `penalty_rhs`
- `active`

- [ ] **Step 2: Add scalar clamp helper**

Implement `evaluate_joint_limit(theta, lower, upper, stiffness)`:

- reject `lower > upper`
- reject negative stiffness
- if `theta < lower`, clamp to `lower`
- if `theta > upper`, clamp to `upper`
- otherwise keep `theta`
- compute `violation = theta - clamped_theta`
- compute `penalty_rhs = stiffness * violation` only when active, otherwise `0.0`

- [ ] **Step 3: Add lower-RHS composition helper**

Implement `apply_joint_limit_penalty_rhs(base_lower_rhs, row_indices, evaluations)`:

- return a copy of `base_lower_rhs`
- require `len(row_indices) == len(evaluations)`
- require row indices are in range
- add each evaluation's `penalty_rhs` to the selected row

- [ ] **Step 4: Export helpers**

Export `JointLimitEvaluation`, `evaluate_joint_limit`, and `apply_joint_limit_penalty_rhs` from `mabd.__init__` and `joint_constraints.__all__`.

### Task 3: Claim Manifest, Boundaries, Validator, Record

**Files:**
- Modify: `docs/reference/paper-claims.yaml`
- Modify: `docs/reference/claim-boundaries.md`
- Modify: `scripts/validate_docs.py`
- Modify: `tests/test_phase0_bootstrap.py`
- Create: `docs/records/2026-05-16-phase7-joint-limits.md`

- [ ] **Step 1: Add passed method claim**

Add `method.joint_limits.strain_clamp_penalty` to `paper-claims.yaml` with source line `/tmp/mabd-paper/source/sections_a/multiabd.tex:119`, expected value `theta clamp plus k(theta-theta_hat) dual RHS`, unit `algorithm`, and status `passed`.

- [ ] **Step 2: Update claim boundaries**

Record that Phase 7 verifies only scalar joint-limit clamp and explicit dual RHS composition through CPU oracle tests. Explicitly say it does not verify generic inequality KKT, contact, production stepping, scene dynamics, or paper experiments.

- [ ] **Step 3: Update docs validator and bootstrap tests**

Require the Phase 7 record, the new claim ID, Phase 7 boundary text, and Phase 7 validator output `Phase 0/1/2/3/4/5/6/7 docs/provenance validation passed`.

- [ ] **Step 4: Create Phase 7 record**

Create a dated record with RED/GREEN outputs, final verification command slots that are filled after the commands run, base commit `2fb91ff`, an `IMPLEMENTATION_COMMIT_PENDING` marker, paper source path, environment, and claim impact.

### Task 4: Verification, Review, And Commits

**Files:**
- All Phase 7 files.

- [ ] **Step 1: Run verification**

Run:

```bash
/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check tests/test_mabd_phase2_joints_kkt.py tests/test_phase0_bootstrap.py vendor/newton/newton/_src/solvers/mabd vendor/newton/newton/tests/test_mabd_phase2_joints_kkt.py scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_mabd_phase2_joints_kkt tests.test_phase0_bootstrap
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest vendor.newton.newton.tests.test_mabd_phase2_joints_kkt
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
git diff --check
```

Expected: all exit 0.

- [ ] **Step 2: Commit implementation**

Run:

```bash
git add docs/records/2026-05-16-phase7-joint-limits.md docs/reference/claim-boundaries.md docs/reference/paper-claims.yaml docs/superpowers/plans/2026-05-16-mabd-phase7-joint-limits.md scripts/validate_docs.py tests/test_mabd_phase2_joints_kkt.py tests/test_phase0_bootstrap.py vendor/newton/newton/_src/solvers/mabd vendor/newton/newton/tests/test_mabd_phase2_joints_kkt.py
git commit -m "feat: add Phase 7 joint limit oracle"
```

- [ ] **Step 3: Backfill record commit hash**

Replace the implementation marker in the Phase 7 record with the commit hash from Step 2, rerun docs validation, and commit:

```bash
git add docs/records/2026-05-16-phase7-joint-limits.md
git commit -m "docs: record Phase 7 implementation commit"
```

- [ ] **Step 4: Fresh final verification and review**

Repeat Step 1 after the record commit, request independent review, fix any blocking/important feedback, then merge/push if clean.
