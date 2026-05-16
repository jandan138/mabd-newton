# Phase 9 Point Contact Forces Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add CPU oracle helpers that map point loads and simple point-plane penalty contacts into affine generalized forces, supporting later contact-, wind-, and actuation-heavy scene assembly without claiming a full contact solver.

**Architecture:** Extend vendored Newton's M-ABD affine math helpers with pure NumPy point-force and point-plane penalty utilities. The helpers use the paper affine point Jacobian `x = J q`, virtual work `Q = J^T f`, and an explicit penalty normal force for a single point against a plane. Tests prove virtual-work consistency, inactive/active penalty behavior, damping sign, and use inside the existing configured CPU oracle step.

**Tech Stack:** Python 3.10, NumPy, vendored Newton M-ABD helpers, `unittest`, ruff, docs/provenance validator.

---

### Task 1: RED Tests For Point Loads And Penalty Contacts

**Files:**
- Modify: `tests/test_mabd_single_body.py`
- Modify: `tests/test_mabd_phase4_solver_step.py`
- Modify: `vendor/newton/newton/tests/test_mabd_single_body.py`

- [ ] **Step 1: Add point-force virtual-work test**

Add to `tests/test_mabd_single_body.py`:

```python
    def test_point_force_mapping_obeys_virtual_work(self) -> None:
        rest_point = np.array([0.4, -0.2, 0.7])
        force = np.array([3.0, -1.5, 2.0])
        dq = np.linspace(-0.3, 0.4, 12)

        generalized = mabd.affine_force_from_point_force(rest_point, force)

        self.assertTrue(np.allclose(generalized, mabd.point_jacobian(rest_point).T @ force))
        self.assertAlmostEqual(float(generalized @ dq), float(force @ (mabd.point_jacobian(rest_point) @ dq)))
```

- [ ] **Step 2: Add point-plane penalty contact tests**

Add:

```python
    def test_point_plane_penalty_contact_maps_normal_force_to_affine_force(self) -> None:
        q = mabd.pack_q(np.eye(3), np.array([0.0, -0.08, 0.0]))
        qd = np.zeros(12)
        rest_point = np.array([0.25, 0.02, -0.1])
        normal = np.array([0.0, 1.0, 0.0])

        contact = mabd.evaluate_point_plane_penalty_contact(
            q,
            qd,
            rest_point,
            plane_normal=normal,
            plane_offset=0.0,
            stiffness=100.0,
        )

        self.assertTrue(contact.active)
        self.assertAlmostEqual(contact.signed_distance, -0.06)
        self.assertAlmostEqual(contact.penetration_depth, 0.06)
        self.assertTrue(np.allclose(contact.force, np.array([0.0, 6.0, 0.0])))
        self.assertTrue(np.allclose(contact.generalized_force, mabd.point_jacobian(rest_point).T @ contact.force))
```

```python
    def test_point_plane_penalty_contact_is_inactive_above_plane(self) -> None:
        q = mabd.pack_q(np.eye(3), np.array([0.0, 0.2, 0.0]))
        qd = np.zeros(12)

        contact = mabd.evaluate_point_plane_penalty_contact(
            q,
            qd,
            np.array([0.0, 0.1, 0.0]),
            plane_normal=np.array([0.0, 2.0, 0.0]),
            plane_offset=0.0,
            stiffness=50.0,
            damping=2.0,
        )

        self.assertFalse(contact.active)
        self.assertAlmostEqual(contact.penetration_depth, 0.0)
        self.assertTrue(np.allclose(contact.force, np.zeros(3)))
        self.assertTrue(np.allclose(contact.generalized_force, np.zeros(12)))
        self.assertTrue(np.allclose(contact.plane_normal, np.array([0.0, 1.0, 0.0])))
```

```python
    def test_point_plane_penalty_contact_damps_only_inward_normal_velocity(self) -> None:
        q = mabd.pack_q(np.eye(3), np.array([0.0, -0.05, 0.0]))
        rest_point = np.zeros(3)
        inward_qd = np.zeros(12)
        inward_qd[10] = -0.2
        outward_qd = np.zeros(12)
        outward_qd[10] = 0.2

        inward = mabd.evaluate_point_plane_penalty_contact(
            q,
            inward_qd,
            rest_point,
            plane_normal=np.array([0.0, 1.0, 0.0]),
            plane_offset=0.0,
            stiffness=100.0,
            damping=10.0,
        )
        outward = mabd.evaluate_point_plane_penalty_contact(
            q,
            outward_qd,
            rest_point,
            plane_normal=np.array([0.0, 1.0, 0.0]),
            plane_offset=0.0,
            stiffness=100.0,
            damping=10.0,
        )

        self.assertAlmostEqual(inward.normal_velocity, -0.2)
        self.assertAlmostEqual(outward.normal_velocity, 0.2)
        self.assertAlmostEqual(float(inward.force[1]), 7.0)
        self.assertAlmostEqual(float(outward.force[1]), 5.0)
```

- [ ] **Step 3: Add CPU oracle integration test**

Add to `tests/test_mabd_phase4_solver_step.py`:

```python
    def test_dense_cpu_step_accepts_point_contact_generalized_force(self) -> None:
        q = mabd.pack_q(np.eye(3), np.array([0.0, -0.05, 0.0]))
        qd = np.zeros(12)
        dt = 0.1
        contact = mabd.evaluate_point_plane_penalty_contact(
            q,
            qd,
            np.zeros(3),
            plane_normal=np.array([0.0, 1.0, 0.0]),
            plane_offset=0.0,
            stiffness=20.0,
        )

        result = mabd.solve_cpu_oracle_step(
            q=[q],
            qd=[qd],
            dt=dt,
            config=mabd.MABDCPUOracleConfig(bodies=[_body()], external_forces=[contact.generalized_force]),
        )

        self.assertTrue(contact.active)
        self.assertAlmostEqual(float(contact.force[1]), 1.0)
        self.assertTrue(np.allclose(result.q[0], q + dt * dt * contact.generalized_force, atol=1.0e-12))
```

- [ ] **Step 4: Add vendored internal mirror**

Mirror the point-force and active/inactive penalty contact tests in `vendor/newton/newton/tests/test_mabd_single_body.py`.

- [ ] **Step 5: Run RED**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_mabd_single_body tests.test_mabd_phase4_solver_step
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest vendor.newton.newton.tests.test_mabd_single_body
```

Expected: fail because `affine_force_from_point_force` and `evaluate_point_plane_penalty_contact` are missing.

### Task 2: Implement Point Load And Contact Helpers

**Files:**
- Modify: `vendor/newton/newton/_src/solvers/mabd/affine_math.py`
- Modify: `vendor/newton/newton/_src/solvers/mabd/__init__.py`

- [ ] **Step 1: Add `PointPlanePenaltyContact` dataclass**

Add immutable fields:

- `rest_point`
- `world_point`
- `plane_normal`
- `plane_offset`
- `signed_distance`
- `penetration_depth`
- `normal_velocity`
- `force`
- `generalized_force`
- `active`

- [ ] **Step 2: Add point-force mapper**

Implement:

```python
def affine_force_from_point_force(rest_point: Any, force: Any) -> np.ndarray:
    return point_jacobian(rest_point).T @ _as_vec3(force, "force")
```

- [ ] **Step 3: Add point-plane penalty evaluator**

Implement:

```python
def evaluate_point_plane_penalty_contact(
    q: Any,
    qd: Any,
    rest_point: Any,
    *,
    plane_normal: Any,
    plane_offset: float,
    stiffness: float,
    damping: float = 0.0,
) -> PointPlanePenaltyContact:
    ...
```

Required behavior:

- normalize `plane_normal`, rejecting zero vector
- reject negative `stiffness` or `damping`
- compute `world_point = point_jacobian(rest_point) @ q`
- compute `signed_distance = normal dot world_point - plane_offset`
- active iff `signed_distance < 0`
- penetration depth is `max(0, -signed_distance)`
- normal velocity is `normal dot (point_jacobian(rest_point) @ qd)`
- normal force magnitude is `stiffness * penetration_depth + damping * max(0, -normal_velocity)` when active, else `0`
- world force is `normal * magnitude`
- generalized force is `J.T @ world_force`

- [ ] **Step 4: Export helpers**

Add the dataclass and functions to `affine_math.__all__` and `mabd.__init__` imports/`__all__`.

- [ ] **Step 5: Run GREEN**

Run the RED commands again. Expected: pass.

### Task 3: Claims, Boundaries, Validator, Record

**Files:**
- Modify: `docs/reference/paper-claims.yaml`
- Modify: `docs/reference/claim-boundaries.md`
- Modify: `scripts/validate_docs.py`
- Modify: `tests/test_phase0_bootstrap.py`
- Create: `docs/records/2026-05-16-phase9-point-contact-forces.md`

- [ ] **Step 1: Add method claim**

Add `method.force_mapping.point_load_penalty_contact` with:

- source path `/tmp/mabd-paper/source/sections/singleabd.tex`
- source line `eq:abd_dof and external force RHS; experiment contact penalty text`
- expected value `point load J^T f and simple point-plane penalty generalized force`
- unit `oracle`
- conflict note `CPU oracle force mapping only; not collision detection, friction, broadphase, or a full contact solver`
- status `passed`

- [ ] **Step 2: Update claim boundaries**

Record Phase 9 current/verified boundaries. Explicitly exclude full contact handling, friction, collision detection, production stepping, paper scenes, and actuation/controller verification.

- [ ] **Step 3: Update docs validator and bootstrap tests**

Require Phase 9 record, claim ID, boundary text, and validator output:

```text
Phase 0/1/2/3/4/5/6/7/8/9 docs/provenance validation passed
```

- [ ] **Step 4: Create Phase 9 record**

Record RED/GREEN outputs, base commit `3aaab8e`, plan commit, implementation marker, paper source references, verification commands, environment, and claim impact.

### Task 4: Verification, Review, Commit, Merge

**Files:**
- All Phase 9 files.

- [ ] **Step 1: Run full verification**

Run:

```bash
/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check tests/test_mabd_single_body.py tests/test_mabd_phase4_solver_step.py tests/test_phase0_bootstrap.py vendor/newton/newton/_src/solvers/mabd vendor/newton/newton/tests/test_mabd_single_body.py scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_mabd_single_body tests.test_mabd_phase4_solver_step tests.test_phase0_bootstrap
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest vendor.newton.newton.tests.test_mabd_single_body
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
git diff --check
```

Expected: all exit 0.

- [ ] **Step 2: Commit implementation**

Run:

```bash
git add docs/records/2026-05-16-phase9-point-contact-forces.md docs/reference/claim-boundaries.md docs/reference/paper-claims.yaml docs/superpowers/plans/2026-05-16-mabd-phase9-point-contact-forces.md scripts/validate_docs.py tests/test_mabd_single_body.py tests/test_mabd_phase4_solver_step.py tests/test_phase0_bootstrap.py vendor/newton/newton/_src/solvers/mabd vendor/newton/newton/tests/test_mabd_single_body.py
git commit -m "feat: add Phase 9 point contact force oracle"
```

- [ ] **Step 3: Backfill implementation commit**

Replace the implementation marker in the record with the commit hash, rerun docs validation, and commit:

```bash
git add docs/records/2026-05-16-phase9-point-contact-forces.md
git commit -m "docs: record Phase 9 implementation commit"
```

- [ ] **Step 4: Review and merge**

Request independent review focused on force signs, virtual-work consistency, overclaiming contact support, and regression risk in existing force mappings. Fix blocking/important issues, rerun Step 1, fast-forward merge to `main`, verify on `main`, push, and clean the worktree.
