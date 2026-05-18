# Phase 67 Model Plane Constraints Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add model-derived `mabd:plane_constraint` rows to `SolverMABD.step()` without changing any paper-claim status.

**Architecture:** Reuse the Phase 63 vendored/local `MABDCPUOraclePlaneConstraint` CPU-oracle primitive and add only model-storage extraction in `solver_mabd.py`. Tests compare model-derived stepping against an explicit CPU-oracle config, and docs gates keep the work recorded as diagnostic plumbing rather than unmodified Newton support, paper-faithful contact, or full reproduction.

**Tech Stack:** Python 3.10, NumPy, Warp custom attributes, vendored Newton `newton.solvers.mabd`, `unittest`, canonical isolated environment `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310`.

---

## Files

- Modify `tests/test_mabd_phase4_solver_step.py`: red tests and helper for model plane rows.
- Modify `vendor/newton/newton/tests/test_mabd_phase4_solver_step.py`: mirrored red tests plus the minimal model-path helpers/imports needed by the vendored test module.
- Modify `vendor/newton/newton/_src/solvers/mabd/solver_mabd.py`: custom frequency, attributes, extraction, config wiring.
- Modify `docs/reference/claim-boundaries.md`: Phase 67 current/verified/non-claim bullets.
- Modify `scripts/validate_docs.py`: Phase 67 record/spec/plan/claim-boundary gates, paper-claim status gates, model-path smoke, and validator phase string.
- Modify `tests/test_phase0_bootstrap.py`: validator tests for Phase 67.
- Create `docs/records/2026-05-19-phase67-model-plane-constraints.md`: dated evidence record.

## Task 1: Solver Model-Path Red Tests

**Files:**
- Modify: `tests/test_mabd_phase4_solver_step.py`
- Modify: `vendor/newton/newton/tests/test_mabd_phase4_solver_step.py`

- [ ] **Step 1: Add model-path helpers for plane rows**

In `tests/test_mabd_phase4_solver_step.py`, add this helper after
`_add_model_world_constraint_row`:

```python
def _add_model_plane_constraint_row(
    builder: newton.ModelBuilder,
    *,
    body: int,
    rest_point: tuple[float, float, float],
    plane_normal: tuple[float, float, float] = (0.0, 1.0, 0.0),
    plane_offset: float = 0.0,
    active: int = 1,
) -> None:
    builder.add_custom_values(
        **{
            "mabd:plane_body": body,
            "mabd:plane_rest_point": wp.vec3(*rest_point),
            "mabd:plane_normal": wp.vec3(*plane_normal),
            "mabd:plane_offset": plane_offset,
            "mabd:plane_active": active,
        }
    )
```

In `vendor/newton/newton/tests/test_mabd_phase4_solver_step.py`, first add
the missing Warp import near the other imports:

```python
import warp as wp
```

Then add these model-path helpers after `_mabd_model`:

```python
def _add_model_body_row(
    builder: newton.ModelBuilder,
    *,
    young_modulus: float = 1.0,
    poisson_ratio: float = 0.25,
    density: float = 1.0,
    polar_mode: int = 0,
) -> int:
    body_id = builder.add_body()
    builder.add_custom_values(
        **{
            "mabd:body_index": body_id,
            "mabd:young_modulus": young_modulus,
            "mabd:poisson_ratio": poisson_ratio,
            "mabd:density": density,
            "mabd:polar_mode": polar_mode,
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
    return body_id


def _model_path_body(
    *,
    young_modulus: float = 1.0,
    poisson_ratio: float = 0.25,
    density: float = 1.0,
    rotation_mode: str = "none",
) -> object:
    rest_points = np.array(
        [
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
        ],
        dtype=float,
    )
    volume = mabd.tetra_volume(rest_points)
    masses = np.full(4, density * volume / 4.0, dtype=float)
    return mabd.MABDCPUOracleBody(
        precompute=mabd.SingleBodyABDPrecompute.from_linear_elastic_points(
            rest_points,
            masses,
            young_modulus=young_modulus,
            poisson_ratio=poisson_ratio,
            volume=volume,
        ),
        rest_q=_identity_q(),
        rotation_mode=rotation_mode,
    )


def _add_model_plane_constraint_row(
    builder: newton.ModelBuilder,
    *,
    body: int,
    rest_point: tuple[float, float, float],
    plane_normal: tuple[float, float, float] = (0.0, 1.0, 0.0),
    plane_offset: float = 0.0,
    active: int = 1,
) -> None:
    builder.add_custom_values(
        **{
            "mabd:plane_body": body,
            "mabd:plane_rest_point": wp.vec3(*rest_point),
            "mabd:plane_normal": wp.vec3(*plane_normal),
            "mabd:plane_offset": plane_offset,
            "mabd:plane_active": active,
        }
    )
```

- [ ] **Step 2: Add a one-row model-path comparison test**

Add this test after `test_solver_step_model_path_builds_world_constraint_from_model_rows` in both files:

```python
def test_solver_step_model_path_consumes_plane_constraint_rows(self) -> None:
    builder = newton.ModelBuilder()
    SolverMABD.register_custom_attributes(builder)
    _add_model_body_row(builder, young_modulus=1.0)
    _add_model_plane_constraint_row(
        builder,
        body=0,
        rest_point=(0.25, 0.0, 0.0),
        plane_normal=(0.0, 2.0, 0.0),
        plane_offset=0.04,
    )
    model = builder.finalize()
    solver = SolverMABD(model)
    q = _identity_q((0.0, -0.1, 0.0))
    qd = np.zeros(12)
    qd[9:12] = np.array([0.5, -1.0, 0.25])
    state = model.state()
    _assign_mabd_state(state, q, qd)
    dt = 0.05

    solver.step(state, state, None, None, dt)

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
                    plane_normal=np.array([0.0, 2.0, 0.0], dtype=float),
                    plane_offset=0.04,
                )
            ],
            topology="dense",
        ),
    )
    q_next, qd_next = _read_mabd_state(state)
    np.testing.assert_allclose(q_next[0], expected.q[0], atol=1.0e-7)
    np.testing.assert_allclose(qd_next[0], expected.qd[0], atol=1.0e-7)
    self.assertEqual(len(solver.model_cpu_oracle_config.plane_constraints), 1)
    self.assertEqual(solver.last_step_result.topology, "dense")
    self.assertEqual(solver.last_step_result.plane_constraint_requested_count, 1)
    self.assertEqual(solver.last_step_result.plane_constraint_accepted_count, 1)
    self.assertEqual(solver.last_step_result.plane_constraint_skipped_count, 0)
    point = mabd.point_jacobian(np.array([0.25, 0.0, 0.0], dtype=float)) @ q_next[0]
    self.assertLess(abs(float(np.array([0.0, 1.0, 0.0]) @ point) - 0.02), 1.0e-10)
```

- [ ] **Step 3: Add inactive, validation, and precedence tests**

Add these tests in both files:

```python
def test_solver_step_model_path_ignores_disabled_plane_constraint_rows(self) -> None:
    builder = newton.ModelBuilder()
    SolverMABD.register_custom_attributes(builder)
    _add_model_body_row(builder, young_modulus=1.0)
    _add_model_plane_constraint_row(
        builder,
        body=0,
        rest_point=(0.25, 0.0, 0.0),
        plane_normal=(0.0, 1.0, 0.0),
        plane_offset=0.0,
        active=0,
    )
    model = builder.finalize()
    solver = SolverMABD(model)
    q = _identity_q((0.0, -0.1, 0.0))
    qd = np.zeros(12)
    qd[9:12] = np.array([0.5, -1.0, 0.25])
    state = model.state()
    _assign_mabd_state(state, q, qd)
    dt = 0.05

    solver.step(state, state, None, None, dt)

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
                    active=False,
                )
            ],
            topology="dense",
        ),
    )
    q_next, qd_next = _read_mabd_state(state)
    np.testing.assert_allclose(q_next[0], expected.q[0], atol=1.0e-7)
    np.testing.assert_allclose(qd_next[0], expected.qd[0], atol=1.0e-7)
    self.assertEqual(len(solver.model_cpu_oracle_config.plane_constraints), 1)
    self.assertFalse(solver.model_cpu_oracle_config.plane_constraints[0].active)
    self.assertEqual(solver.last_step_result.plane_constraint_requested_count, 0)
    self.assertEqual(solver.last_step_result.dlambda.shape, (0,))


def test_solver_step_model_path_rejects_out_of_range_plane_body(self) -> None:
    builder = newton.ModelBuilder()
    SolverMABD.register_custom_attributes(builder)
    _add_model_body_row(builder, young_modulus=1.0)
    _add_model_plane_constraint_row(builder, body=1, rest_point=(0.0, 0.0, 0.0))
    model = builder.finalize()
    solver = SolverMABD(model)
    state = model.state()
    _assign_mabd_state(state, _identity_q(), np.zeros(12))

    with self.assertRaisesRegex(ValueError, "mabd:plane_body"):
        solver.step(state, state, None, None, 0.05)


def test_solver_step_model_path_rejects_zero_plane_normal(self) -> None:
    builder = newton.ModelBuilder()
    SolverMABD.register_custom_attributes(builder)
    _add_model_body_row(builder, young_modulus=1.0)
    _add_model_plane_constraint_row(
        builder,
        body=0,
        rest_point=(0.0, 0.0, 0.0),
        plane_normal=(0.0, 0.0, 0.0),
    )
    model = builder.finalize()
    solver = SolverMABD(model)
    state = model.state()
    _assign_mabd_state(state, _identity_q(), np.zeros(12))

    with self.assertRaisesRegex(ValueError, "plane_normal"):
        solver.step(state, state, None, None, 0.05)


def test_solver_step_manual_config_takes_precedence_over_model_plane_constraints(self) -> None:
    builder = newton.ModelBuilder()
    SolverMABD.register_custom_attributes(builder)
    _add_model_body_row(builder, young_modulus=1.0)
    _add_model_plane_constraint_row(builder, body=0, rest_point=(0.25, 0.0, 0.0))
    model = builder.finalize()
    solver = SolverMABD(model)
    manual_config = mabd.MABDCPUOracleConfig(bodies=[_body()])
    solver.configure_cpu_oracle(manual_config)
    q = _identity_q((0.0, -0.1, 0.0))
    qd = np.zeros(12)
    state = model.state()
    _assign_mabd_state(state, q, qd)

    solver.step(state, state, None, None, 0.05)

    self.assertIsNone(solver.model_cpu_oracle_config)
    self.assertEqual(solver.last_step_result.topology, "unconstrained")


def test_solver_step_still_rejects_newton_contacts_input_with_model_plane_rows(self) -> None:
    builder = newton.ModelBuilder()
    SolverMABD.register_custom_attributes(builder)
    _add_model_body_row(builder, young_modulus=1.0)
    _add_model_plane_constraint_row(builder, body=0, rest_point=(0.25, 0.0, 0.0))
    model = builder.finalize()
    solver = SolverMABD(model)
    state = model.state()
    _assign_mabd_state(state, _identity_q(), np.zeros(12))

    with self.assertRaisesRegex(NotImplementedError, "Contacts input"):
        solver.step(state, state, None, object(), 0.05)
```

- [ ] **Step 4: Verify RED**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_mabd_phase4_solver_step
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest newton.tests.test_mabd_phase4_solver_step
```

Expected: fail because `mabd:plane_*` attributes are not registered.

## Task 2: SolverMABD Plane Row Implementation

**Files:**
- Modify: `vendor/newton/newton/_src/solvers/mabd/solver_mabd.py`

- [ ] **Step 1: Import the existing dataclass**

Extend the `.step_oracle` import:

```python
from .step_oracle import (
    MABDCPUOracleBody,
    MABDCPUOracleConfig,
    MABDCPUOracleConstraint,
    MABDCPUOraclePlaneConstraint,
    MABDCPUOracleStepResult,
    MABDCPUOracleWorldConstraint,
    solve_cpu_oracle_step,
)
```

- [ ] **Step 2: Add the custom frequency constant**

Add this constant after `MABD_WORLD_CONSTRAINT_FREQUENCY`:

```python
MABD_PLANE_CONSTRAINT_FREQUENCY = "mabd:plane_constraint"
```

- [ ] **Step 3: Add row extraction**

Add this method after `_world_constraint_from_model_row`:

```python
def _plane_constraint_from_model_row(self, row: int, body_count: int) -> MABDCPUOraclePlaneConstraint:
    namespace = self.model.mabd
    body = int(namespace.plane_body.numpy()[row])
    if not 0 <= body < body_count:
        raise ValueError("mabd:plane_body must reference a mabd:body row")
    return MABDCPUOraclePlaneConstraint(
        body=body,
        rest_point=np.asarray(namespace.plane_rest_point.numpy()[row], dtype=float),
        plane_normal=np.asarray(namespace.plane_normal.numpy()[row], dtype=float),
        plane_offset=float(namespace.plane_offset.numpy()[row]),
        active=bool(int(namespace.plane_active.numpy()[row])),
    )
```

- [ ] **Step 4: Wire rows into cached model config**

In `_cpu_oracle_config_from_model`, add:

```python
plane_constraint_count = self._custom_frequency_count(self.MABD_PLANE_CONSTRAINT_FREQUENCY)
```

and pass:

```python
plane_constraints=tuple(
    self._plane_constraint_from_model_row(row, body_count)
    for row in range(plane_constraint_count)
),
```

to `MABDCPUOracleConfig(...)`.

- [ ] **Step 5: Register model attributes**

In `register_custom_attributes`, add:

```python
builder.add_custom_frequency(ModelBuilder.CustomFrequency(name="plane_constraint", namespace="mabd"))
```

Add `plane_constraint_attrs` after `world_constraint_attrs`:

```python
plane_constraint_attrs = (
    ModelBuilder.CustomAttribute(
        name="plane_body",
        frequency=cls.MABD_PLANE_CONSTRAINT_FREQUENCY,
        assignment=Model.AttributeAssignment.MODEL,
        dtype=wp.int32,
        default=-1,
        namespace="mabd",
        references=cls.MABD_BODY_FREQUENCY,
    ),
    ModelBuilder.CustomAttribute(
        name="plane_rest_point",
        frequency=cls.MABD_PLANE_CONSTRAINT_FREQUENCY,
        assignment=Model.AttributeAssignment.MODEL,
        dtype=wp.vec3,
        default=wp.vec3(0.0, 0.0, 0.0),
        namespace="mabd",
    ),
    ModelBuilder.CustomAttribute(
        name="plane_normal",
        frequency=cls.MABD_PLANE_CONSTRAINT_FREQUENCY,
        assignment=Model.AttributeAssignment.MODEL,
        dtype=wp.vec3,
        default=wp.vec3(0.0, 1.0, 0.0),
        namespace="mabd",
    ),
    ModelBuilder.CustomAttribute(
        name="plane_offset",
        frequency=cls.MABD_PLANE_CONSTRAINT_FREQUENCY,
        assignment=Model.AttributeAssignment.MODEL,
        dtype=wp.float32,
        default=0.0,
        namespace="mabd",
    ),
    ModelBuilder.CustomAttribute(
        name="plane_active",
        frequency=cls.MABD_PLANE_CONSTRAINT_FREQUENCY,
        assignment=Model.AttributeAssignment.MODEL,
        dtype=wp.int32,
        default=1,
        namespace="mabd",
    ),
)
```

Include `*plane_constraint_attrs` in the final `builder.add_custom_attribute`
loop.

- [ ] **Step 6: Verify GREEN**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_mabd_phase4_solver_step
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest newton.tests.test_mabd_phase4_solver_step
```

Expected: pass.

- [ ] **Step 7: Commit solver changes**

```bash
git add tests/test_mabd_phase4_solver_step.py vendor/newton/newton/tests/test_mabd_phase4_solver_step.py vendor/newton/newton/_src/solvers/mabd/solver_mabd.py
git commit -m "feat: add model-derived MABD plane constraints"
```

## Task 3: Provenance And Final Verification

**Files:**
- Modify: `docs/reference/claim-boundaries.md`
- Modify: `scripts/validate_docs.py`
- Modify: `tests/test_phase0_bootstrap.py`
- Create: `docs/records/2026-05-19-phase67-model-plane-constraints.md`

- [ ] **Step 1: Write failing docs/provenance tests**

Update `tests/test_phase0_bootstrap.py` to require:

```python
phase67_spec = ROOT / "docs/superpowers/specs/2026-05-19-phase67-model-plane-constraints-design.md"
phase67_plan = ROOT / "docs/superpowers/plans/2026-05-19-mabd-phase67-model-plane-constraints.md"
phase67_record = ROOT / "docs/records/2026-05-19-phase67-model-plane-constraints.md"
```

and assert that claim boundaries contain current, verified, non-claim, and
forbidden bullets for `Phase 67 model-derived point-plane normal constraint`,
`mabd:plane_constraint`, `mabd:plane_body`, `mabd:plane_normal`,
`mabd:plane_active`, `Newton Contacts`, `paper-faithful affine contact`, and
`no experiment claim is passed`.

Also add negative tests proving the validator rejects overclaim snippets such
as `contact solver implemented`, `paper-faithful affine collision`,
`passed experiment`, and `full reproduction complete`, and rejects a patched
`paper-claims.yaml` where any `experiment.*` status becomes `passed`.

- [ ] **Step 2: Verify docs RED**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_phase0_bootstrap
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
```

Expected: fail because Phase 67 validator and record text do not exist.

- [ ] **Step 3: Implement docs and validator**

Add Phase 67 claim-boundary bullets with the same shape as Phase 63/66:

```text
This repository contains Phase 67 model-derived point-plane normal constraint
row extraction evidence after the Phase 67 record is created.
Phase 67 verifies that explicit mabd:plane_constraint model rows with
mabd:plane_body, mabd:plane_rest_point, mabd:plane_normal,
mabd:plane_offset, and mabd:plane_active are extracted into the vendored/local
Newton CPU oracle config used by SolverMABD.step().
Phase 67 does not verify contact solving, Newton Contacts ingestion, collision
detection, active-set generation, IPC, generic inequality-constrained M-ABD
KKT, paper-faithful affine contact, paper-faithful M-ABD stepping, comparison
pass gates, runtime performance, any experiment pass, or full reproduction.
Phase 67 model-derived point-plane rows must not be described as unmodified
Newton M-ABD support, paper-faithful affine collision/contact, a contact solver,
or full paper reproduction.
```

Add `validate_phase67_record()` to `scripts/validate_docs.py` and call it from
`main()`. Update required path lists, the validator top-level docstring/phase
string, and the success message from Phase 0-66 to Phase 0-67.

Require the spec, plan, record, claim-boundary phrases, canonical Python path,
`implementation_commit`, `vendored Newton upstream commit`, `local patch files`,
and exact paper-claim status boundaries: all current method claims keep their
existing statuses, all current `experiment.*` claims remain `intended`, no new
claim is marked `passed`, and `method.force_mapping.point_load_penalty_contact`
retains its existing conflict note.

Add a validator smoke that constructs a model with one body and one
`mabd:plane_constraint`, runs `SolverMABD.step()`, and asserts:

```text
len(model_cpu_oracle_config.plane_constraints) == 1
plane_constraint_requested_count == 1
plane_constraint_accepted_count == 1
plane_constraint_skipped_count == 0
constraint_residual_norm is finite and below 1e-8
manual configure_cpu_oracle on a fresh solver leaves model_cpu_oracle_config unset
contacts input still raises NotImplementedError
```

- [ ] **Step 4: Add the dated evidence record**

Create `docs/records/2026-05-19-phase67-model-plane-constraints.md` with:

```text
# Phase 67 Model Plane Constraints

## Status

passed_for_solver_model_plane_constraint_config_slice

## Repository

- branch: `phase67-model-plane-constraints`
- implementation commit: `<commit after solver implementation>`
- local patch files:
  - `vendor/newton/newton/_src/solvers/mabd/solver_mabd.py`
  - `tests/test_mabd_phase4_solver_step.py`
  - `vendor/newton/newton/tests/test_mabd_phase4_solver_step.py`

## Vendored Newton

- vendored Newton upstream commit:
  `96713fa965463b69c229a4d30582c733ff3526bb`
- local patch status:
  `Phase67 modifies vendored Newton inside this repository; unmodified Newton
  support is not claimed.`

## Environment

- Python:
  `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python`
- reference environment:
  `/cpfs/user/zhuzihou/conda-managed/envs/physics-primitive-newton-py310`
- target environment:
  `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310`
- environment non-pollution:
  `mutates_reference_environment=false`, `uses_reference_python=false`,
  `uses_ambient_python=false`

## Evidence

- model frequency: `mabd:plane_constraint`
- model attributes: `mabd:plane_body`, `mabd:plane_rest_point`,
  `mabd:plane_normal`, `mabd:plane_offset`, `mabd:plane_active`
- model smoke: `requested=1`, `accepted=1`, `skipped=0`
- manual-config precedence smoke: `model_cpu_oracle_config unset on fresh solver`
- contacts path: `NotImplementedError` retained

## Result Boundary

No `experiment.*` claim is passed. `paper-claims.yaml` is unchanged. This is
not a contact solver, not collision detection, not Newton `Contacts` ingestion,
not paper-faithful affine collision/contact, not unmodified Newton M-ABD
support, and not full paper reproduction.
```

Record exact verification commands and results.

- [ ] **Step 5: Verify docs GREEN**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_phase0_bootstrap
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
```

Expected: pass.

- [ ] **Step 6: Final verification before merge**

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

- [ ] **Step 7: Commit docs/provenance**

```bash
git add docs/reference/claim-boundaries.md scripts/validate_docs.py tests/test_phase0_bootstrap.py docs/records/2026-05-19-phase67-model-plane-constraints.md
git commit -m "docs: record Phase67 model plane constraints"
```

## Self-Review

- Spec coverage: the plan covers model custom attributes, extraction,
  precedence, validation, mirrored solver tests, records, and docs gates.
- Placeholder scan: the evidence record must replace placeholder commit hashes
  before commit.
- Type consistency: `mabd:plane_constraint`, `mabd:plane_body`,
  `mabd:plane_rest_point`, `mabd:plane_normal`, `mabd:plane_offset`, and
  `mabd:plane_active` are used consistently.
