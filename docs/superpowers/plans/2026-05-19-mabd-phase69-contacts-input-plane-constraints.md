# Phase 69 Contacts Input Plane Constraints Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let `SolverMABD.step(..., contacts=...)` consume bounded Newton rigid contact rows and convert the supported static-geometry subset into existing M-ABD point-plane constraint rows.

**Architecture:** Add contact-row conversion inside vendored Newton `solver_mabd.py`, keep the existing CPU oracle plane-constraint solver unchanged, and mirror tests in repo and vendored Newton test suites. The conversion is limited to exactly one M-ABD side against static geometry with `shape_body == -1`; dynamic non-M-ABD contacts are skipped. Record docs, boundaries, and validator evidence without changing any paper claim to passed.

**Tech Stack:** Python 3.10, `unittest`, vendored Newton `Contacts`, `ModelBuilder`, `SolverMABD`, existing docs validator.

---

## File Structure

- Modify `vendor/newton/newton/_src/solvers/mabd/solver_mabd.py`: add contact-summary dataclass, Newton-body to M-ABD-row mapping, `Contacts` to `MABDCPUOraclePlaneConstraint` conversion, and config merge before stepping.
- Modify `vendor/newton/newton/tests/test_mabd_phase4_solver_step.py`: add red-green tests for contact ingestion.
- Modify `tests/test_mabd_phase4_solver_step.py`: mirror vendored tests through the repo test lane.
- Modify `docs/reference/claim-boundaries.md`: add Phase 69 current/verified/non-claim bullets.
- Create `docs/records/2026-05-19-phase69-contacts-input-plane-constraints.md`: dated evidence record.
- Modify `scripts/validate_docs.py`: require Phase 69 artifacts, claim boundaries, contact-summary contract, paper-claim status preservation, and overclaim guards.
- Modify `tests/test_phase0_bootstrap.py`: add focused Phase 69 validator regression coverage.

## Task 1: Red Tests For Contacts Input

**Files:**
- Modify `vendor/newton/newton/tests/test_mabd_phase4_solver_step.py`
- Modify `tests/test_mabd_phase4_solver_step.py`

- [ ] **Step 1: Add contact-buffer helpers**

Add helper functions near `_add_model_plane_constraint_row`:

```python
def _mabd_model_with_box_and_static_plane() -> tuple[object, int, int]:
    builder = newton.ModelBuilder()
    SolverMABD.register_custom_attributes(builder)
    mabd_body = _add_model_body_row(builder, young_modulus=1.0)
    box_shape = builder.add_shape_box(body=mabd_body, hx=0.5, hy=0.5, hz=0.5)
    plane_shape = builder.add_shape_plane(plane=(0.0, 1.0, 0.0, 0.0), width=0.0, length=0.0)
    return builder.finalize(), box_shape, plane_shape


def _contacts_with_one_rigid_row(
    *,
    shape0: int,
    shape1: int,
    point0: tuple[float, float, float],
    point1: tuple[float, float, float],
    normal: tuple[float, float, float],
    capacity: int = 4,
    reported_count: int = 1,
) -> object:
    contacts = newton.Contacts(rigid_contact_max=capacity, soft_contact_max=0)
    contacts.rigid_contact_count.assign(np.array([reported_count], dtype=np.int32))
    shape0_values = np.full(capacity, -1, dtype=np.int32)
    shape1_values = np.full(capacity, -1, dtype=np.int32)
    point0_values = np.zeros((capacity, 3), dtype=np.float32)
    point1_values = np.zeros((capacity, 3), dtype=np.float32)
    normal_values = np.zeros((capacity, 3), dtype=np.float32)
    shape0_values[0] = shape0
    shape1_values[0] = shape1
    point0_values[0] = np.asarray(point0, dtype=np.float32)
    point1_values[0] = np.asarray(point1, dtype=np.float32)
    normal_values[0] = np.asarray(normal, dtype=np.float32)
    contacts.rigid_contact_shape0.assign(shape0_values)
    contacts.rigid_contact_shape1.assign(shape1_values)
    contacts.rigid_contact_point0.assign(point0_values)
    contacts.rigid_contact_point1.assign(point1_values)
    contacts.rigid_contact_normal.assign(normal_values)
    return contacts
```

- [ ] **Step 2: Add contact ingestion parity test**

Add `test_solver_step_consumes_newton_contacts_as_plane_constraints`:

```python
def test_solver_step_consumes_newton_contacts_as_plane_constraints(self) -> None:
    model, box_shape, plane_shape = _mabd_model_with_box_and_static_plane()
    solver = SolverMABD(model)
    q = _identity_q((0.0, -0.1, 0.0))
    qd = np.zeros(12)
    qd[9:12] = np.array([0.5, -1.0, 0.25])
    state = model.state()
    _assign_mabd_state(state, q, qd)
    contacts = _contacts_with_one_rigid_row(
        shape0=box_shape,
        shape1=plane_shape,
        point0=(0.25, 0.0, 0.0),
        point1=(0.25, 0.0, 0.0),
        normal=(0.0, 1.0, 0.0),
    )
    dt = 0.05

    solver.step(state, state, None, contacts, dt)

    expected = mabd.solve_cpu_oracle_step(
        q=[q],
        qd=[qd],
        dt=dt,
        config=mabd.MABDCPUOracleConfig(
            bodies=[_model_path_body(young_modulus=1.0)],
            plane_constraints=[
                mabd.MABDCPUOraclePlaneConstraint(
                    body=0,
                    rest_point=np.array([0.25, 0.0, 0.0], dtype=float),
                    plane_normal=np.array([0.0, 1.0, 0.0], dtype=float),
                    plane_offset=0.0,
                )
            ],
            topology="dense",
        ),
    )
    q_next, qd_next = _read_mabd_state(state)
    np.testing.assert_allclose(q_next[0], expected.q[0], atol=1.0e-7)
    np.testing.assert_allclose(qd_next[0], expected.qd[0], atol=1.0e-7)
    self.assertEqual(solver.last_step_result.plane_constraint_requested_count, 1)
    self.assertEqual(solver.last_contacts_input_summary.generated_plane_constraint_count, 1)
    self.assertEqual(solver.last_contacts_input_summary.skipped_contact_count, 0)
    self.assertEqual(
        solver.last_contacts_input_summary.policy,
        "rigid_contacts_to_point_plane_constraints_diagnostic",
    )
```

- [ ] **Step 3: Add normal-flip, dynamic-skip, and skip-count tests**

Add these tests:

```python
def test_solver_step_flips_contact_normal_when_mabd_body_is_shape1(self) -> None:
    model, box_shape, plane_shape = _mabd_model_with_box_and_static_plane()
    solver = SolverMABD(model)
    q = _identity_q((0.0, -0.1, 0.0))
    qd = np.zeros(12)
    qd[9:12] = np.array([0.5, -1.0, 0.25])
    state = model.state()
    _assign_mabd_state(state, q, qd)
    contacts = _contacts_with_one_rigid_row(
        shape0=plane_shape,
        shape1=box_shape,
        point0=(0.25, 0.0, 0.0),
        point1=(0.25, 0.0, 0.0),
        normal=(0.0, -1.0, 0.0),
    )
    dt = 0.05

    solver.step(state, state, None, contacts, dt)

    expected = mabd.solve_cpu_oracle_step(
        q=[q],
        qd=[qd],
        dt=dt,
        config=mabd.MABDCPUOracleConfig(
            bodies=[_model_path_body(young_modulus=1.0)],
            plane_constraints=[
                mabd.MABDCPUOraclePlaneConstraint(
                    body=0,
                    rest_point=np.array([0.25, 0.0, 0.0], dtype=float),
                    plane_normal=np.array([0.0, 1.0, 0.0], dtype=float),
                    plane_offset=0.0,
                )
            ],
            topology="dense",
        ),
    )
    q_next, qd_next = _read_mabd_state(state)
    np.testing.assert_allclose(q_next[0], expected.q[0], atol=1.0e-7)
    np.testing.assert_allclose(qd_next[0], expected.qd[0], atol=1.0e-7)
    self.assertEqual(solver.last_contacts_input_summary.generated_plane_constraint_count, 1)


def test_solver_step_records_skipped_and_overflow_contact_rows(self) -> None:
    model, _box_shape, plane_shape = _mabd_model_with_box_and_static_plane()
    solver = SolverMABD(model)
    state = model.state()
    _assign_mabd_state(state, _identity_q(), np.zeros(12))
    contacts = _contacts_with_one_rigid_row(
        shape0=plane_shape,
        shape1=plane_shape,
        point0=(0.0, 0.0, 0.0),
        point1=(0.0, 0.0, 0.0),
        normal=(0.0, 1.0, 0.0),
        capacity=1,
        reported_count=3,
    )

    solver.step(state, state, None, contacts, 0.05)

    summary = solver.last_contacts_input_summary
    self.assertEqual(summary.rigid_contact_count, 3)
    self.assertEqual(summary.rigid_contact_capacity, 1)
    self.assertEqual(summary.rigid_contact_overflow_count, 2)
    self.assertEqual(summary.rigid_contact_rows_read, 1)
    self.assertEqual(summary.generated_plane_constraint_count, 0)
    self.assertEqual(summary.skipped_contact_count, 3)
    self.assertEqual(solver.last_step_result.plane_constraint_requested_count, 0)


def test_solver_step_skips_dynamic_non_mabd_contact_rows(self) -> None:
    # Covers both M-ABD shape 0 vs dynamic non-M-ABD shape 1 and the flipped order.
    # Expected: generated_plane_constraint_count=0, skipped_contact_count=2.
    ...


def test_solver_step_rejects_duplicate_mabd_body_index_mapping_for_contacts(self) -> None:
    builder = newton.ModelBuilder()
    SolverMABD.register_custom_attributes(builder)
    body_id = builder.add_body()
    for _ in range(2):
        builder.add_custom_values(
            **{
                "mabd:body_index": body_id,
                "mabd:young_modulus": 1.0,
                "mabd:poisson_ratio": 0.25,
                "mabd:density": 1.0,
                "mabd:polar_mode": 0,
                "mabd:rest_point0": wp.vec3(0.0, 0.0, 0.0),
                "mabd:rest_point1": wp.vec3(1.0, 0.0, 0.0),
                "mabd:rest_point2": wp.vec3(0.0, 1.0, 0.0),
                "mabd:rest_point3": wp.vec3(0.0, 0.0, 1.0),
                "mabd:point_mass0": -1.0,
                "mabd:point_mass1": -1.0,
                "mabd:point_mass2": -1.0,
                "mabd:point_mass3": -1.0,
                "mabd:volume": -1.0,
            }
        )
    box_shape = builder.add_shape_box(body=body_id, hx=0.5, hy=0.5, hz=0.5)
    plane_shape = builder.add_shape_plane(plane=(0.0, 1.0, 0.0, 0.0), width=0.0, length=0.0)
    model = builder.finalize()
    solver = SolverMABD(model)
    state = model.state()
    _assign_mabd_state(state, [_identity_q(), _identity_q()], [np.zeros(12), np.zeros(12)])
    contacts = _contacts_with_one_rigid_row(
        shape0=box_shape,
        shape1=plane_shape,
        point0=(0.25, 0.0, 0.0),
        point1=(0.25, 0.0, 0.0),
        normal=(0.0, 1.0, 0.0),
    )

    with self.assertRaisesRegex(ValueError, "duplicate mabd:body_index"):
        solver.step(state, state, None, contacts, 0.05)
```

- [ ] **Step 4: Verify red**

Run:

```bash
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest newton.tests.test_mabd_phase4_solver_step.MABDPhase4InternalTests.test_solver_step_consumes_newton_contacts_as_plane_constraints
```

Expected: FAIL with `NotImplementedError: SolverMABD Phase 4 CPU oracle step does not support Contacts input`.

## Task 2: Implement Contacts Conversion

**Files:**
- Modify `vendor/newton/newton/_src/solvers/mabd/solver_mabd.py`

- [ ] **Step 1: Add imports and summary dataclass**

Import `dataclass` and `replace` from `dataclasses`. Add `MABDContactsInputSummary` near the class definition with the fields listed in the spec.

- [ ] **Step 2: Add body mapping helper**

Add `_mabd_body_row_by_newton_body()` that reads `self.model.mabd.body_index.numpy()`, skips negative ids, and raises `ValueError("duplicate mabd:body_index")` on duplicate nonnegative Newton body ids.

- [ ] **Step 3: Add contact conversion helper**

Add `_plane_constraints_from_contacts(contacts)` that reads rigid contact arrays up to `min(reported_count, rigid_contact_max)`, checks `model.shape_body`, maps exactly-one-MABD-side contacts into `MABDCPUOraclePlaneConstraint` only when the opposite side has `shape_body == -1`, records skipped and overflow counts, sets `self.last_contacts_input_summary`, and returns a tuple of generated constraints.

- [ ] **Step 4: Merge contacts into config**

Add `_cpu_oracle_config_with_contacts(config, contacts)` that appends generated contact constraints to `config.plane_constraints` with `dataclasses.replace`. In `step()`, remove the unconditional Contacts `NotImplementedError`, compute base config as before, then call the merge helper before `solve_cpu_oracle_step(...)`.

- [ ] **Step 5: Verify green focused tests**

Run:

```bash
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest newton.tests.test_mabd_phase4_solver_step
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_mabd_phase4_solver_step
```

Expected: OK.

- [ ] **Step 6: Commit solver and tests**

Run:

```bash
git add vendor/newton/newton/_src/solvers/mabd/solver_mabd.py vendor/newton/newton/tests/test_mabd_phase4_solver_step.py tests/test_mabd_phase4_solver_step.py
git commit -m "feat: let SolverMABD consume rigid contacts"
```

## Task 3: Docs And Validator

**Files:**
- Modify `docs/reference/claim-boundaries.md`
- Create `docs/records/2026-05-19-phase69-contacts-input-plane-constraints.md`
- Modify `scripts/validate_docs.py`
- Modify `tests/test_phase0_bootstrap.py`

- [ ] **Step 1: Add Phase 69 record and boundaries**

Record the implementation commit, canonical Python, vendored Newton commit,
summary contract, and non-claims. Add Phase 69 current/verified/non-claim
bullets to `claim-boundaries.md`.

- [ ] **Step 2: Add validator checks**

Require spec, plan, record, claim-boundary snippets, `last_contacts_input_summary`, the policy string, unchanged paper-claim statuses, and the forbidden overclaim phrase guard.

- [ ] **Step 3: Add focused bootstrap validator test**

Add a focused Phase 69 test in `tests/test_phase0_bootstrap.py` that checks the validator coverage and confirms `experiment.single_body.spinning_box` remains `intended`.

- [ ] **Step 4: Run docs gates**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_phase0_bootstrap
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
```

Expected: OK.

- [ ] **Step 5: Commit docs and validator**

Run:

```bash
git add docs/superpowers/specs/2026-05-19-phase69-contacts-input-plane-constraints-design.md docs/superpowers/plans/2026-05-19-mabd-phase69-contacts-input-plane-constraints.md docs/reference/claim-boundaries.md docs/records/2026-05-19-phase69-contacts-input-plane-constraints.md scripts/validate_docs.py tests/test_phase0_bootstrap.py
git commit -m "docs: record Phase69 contacts input evidence"
```

## Task 4: Final Verification

- [ ] **Step 1: Run final gates**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest newton.tests.test_mabd_phase4_solver_step
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/env/readiness_check.py
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"
git diff --check
```

Expected: all commands exit 0 and Newton imports from this repo's
`vendor/newton`.
