# Phase 46 Model World Constraints Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let `SolverMABD.step()` build CPU oracle world-anchor constraints from Newton `mabd:world_constraint` model rows.

**Architecture:** Add a small world-constraint-row translation layer inside `SolverMABD` that reuses the existing `MABDCPUOracleWorldConstraint` dense CPU oracle support. The model path derives body configs, joint constraints, world constraints, and controls into one cached `MABDCPUOracleConfig`, while manual `configure_cpu_oracle(...)` remains authoritative.

**Tech Stack:** Python 3.10, vendored Newton, Warp custom attributes, `unittest`, `scripts/validate_docs.py`.

---

### Task 1: RED Tests For Model-Derived World Constraints

**Files:**
- Modify: `tests/test_mabd_phase4_solver_step.py`

- [ ] **Step 1: Add a test helper for model world-anchor rows**

Add this helper near `_add_model_constraint_row(...)`:

```python
def _add_model_world_constraint_row(
    builder: newton.ModelBuilder,
    *,
    body: int,
    rest_point: tuple[float, float, float],
    world_point: tuple[float, float, float],
) -> None:
    builder.add_custom_values(
        **{
            "mabd:world_body": body,
            "mabd:world_rest_point": wp.vec3(*rest_point),
            "mabd:world_point": wp.vec3(*world_point),
        }
    )
```

- [ ] **Step 2: Add a failing model-path world-anchor test**

Add:

```python
def test_solver_step_model_path_builds_world_constraint_from_model_rows(self) -> None:
    builder = newton.ModelBuilder()
    SolverMABD.register_custom_attributes(builder)
    _add_model_body_row(builder, young_modulus=1.0)
    _add_model_world_constraint_row(
        builder,
        body=0,
        rest_point=(1.0, 0.0, 0.0),
        world_point=(1.25, 0.0, 0.0),
    )
    model = builder.finalize()
    solver = SolverMABD(model)
    state = model.state()
    q = _identity_q((0.0, 0.0, 0.0))
    _assign_mabd_state(state, q, np.zeros(12))

    solver.step(state, state, None, None, 0.05)

    config = solver.model_cpu_oracle_config
    self.assertIsNotNone(config)
    self.assertEqual(len(config.world_constraints), 1)
    pinned = mabd.point_jacobian(np.array([1.0, 0.0, 0.0], dtype=float)) @ _read_mabd_state(state)[0][0]
    self.assertTrue(np.allclose(pinned, np.array([1.25, 0.0, 0.0]), atol=1.0e-10))
    self.assertLess(solver.last_step_result.constraint_residual_norm, 1.0e-10)
    self.assertEqual(solver.last_step_result.dlambda.shape, (3,))
```

- [ ] **Step 3: Add invalid body-reference test**

Add:

```python
def test_solver_step_model_world_constraint_rejects_bad_body_index(self) -> None:
    builder = newton.ModelBuilder()
    SolverMABD.register_custom_attributes(builder)
    _add_model_body_row(builder, young_modulus=1.0)
    _add_model_world_constraint_row(
        builder,
        body=1,
        rest_point=(1.0, 0.0, 0.0),
        world_point=(1.25, 0.0, 0.0),
    )
    model = builder.finalize()
    solver = SolverMABD(model)
    state = model.state()
    _assign_mabd_state(state, _identity_q(), np.zeros(12))

    with self.assertRaisesRegex(ValueError, "mabd:world_body"):
        solver.step(state, state, None, None, 0.05)
```

- [ ] **Step 4: Verify RED**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_mabd_phase4_solver_step
```

Expected before implementation: tests fail because `mabd:world_body` is not a
registered custom attribute.

### Task 2: Implement Model World Constraint Translation

**Files:**
- Modify: `vendor/newton/newton/_src/solvers/mabd/solver_mabd.py`

- [ ] **Step 1: Import the world-constraint oracle type**

Extend the `step_oracle` import with:

```python
MABDCPUOracleWorldConstraint,
```

- [ ] **Step 2: Register the `mabd:world_constraint` frequency**

Add:

```python
MABD_WORLD_CONSTRAINT_FREQUENCY = "mabd:world_constraint"
```

Register the custom frequency:

```python
builder.add_custom_frequency(ModelBuilder.CustomFrequency(name="world_constraint", namespace="mabd"))
```

Add model attributes:

```python
world_constraint_attrs = (
    ModelBuilder.CustomAttribute(
        name="world_body",
        frequency=cls.MABD_WORLD_CONSTRAINT_FREQUENCY,
        assignment=Model.AttributeAssignment.MODEL,
        dtype=wp.int32,
        default=-1,
        namespace="mabd",
        references=cls.MABD_BODY_FREQUENCY,
    ),
    ModelBuilder.CustomAttribute(
        name="world_rest_point",
        frequency=cls.MABD_WORLD_CONSTRAINT_FREQUENCY,
        assignment=Model.AttributeAssignment.MODEL,
        dtype=wp.vec3,
        default=wp.vec3(0.0, 0.0, 0.0),
        namespace="mabd",
    ),
    ModelBuilder.CustomAttribute(
        name="world_point",
        frequency=cls.MABD_WORLD_CONSTRAINT_FREQUENCY,
        assignment=Model.AttributeAssignment.MODEL,
        dtype=wp.vec3,
        default=wp.vec3(0.0, 0.0, 0.0),
        namespace="mabd",
    ),
)
```

Include `*world_constraint_attrs` in the registration loop.

- [ ] **Step 3: Add row translation**

Add:

```python
def _world_constraint_from_model_row(self, row: int, body_count: int) -> MABDCPUOracleWorldConstraint:
    namespace = self.model.mabd
    body = int(namespace.world_body.numpy()[row])
    if not 0 <= body < body_count:
        raise ValueError("mabd:world_body must reference a mabd:body row")
    return MABDCPUOracleWorldConstraint(
        body=body,
        rest_point=np.asarray(namespace.world_rest_point.numpy()[row], dtype=float),
        world_point=np.asarray(namespace.world_point.numpy()[row], dtype=float),
    )
```

- [ ] **Step 4: Include world constraints in model-derived config**

In `_cpu_oracle_config_from_model()`, read:

```python
world_constraint_count = self._custom_frequency_count(self.MABD_WORLD_CONSTRAINT_FREQUENCY)
```

Then pass:

```python
world_constraints=tuple(
    self._world_constraint_from_model_row(row, body_count)
    for row in range(world_constraint_count)
),
```

- [ ] **Step 5: Verify GREEN**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_mabd_phase4_solver_step
```

Expected: all solver-step tests pass.

### Task 3: Documentation, Provenance, And Validator

**Files:**
- Modify: `docs/reference/claim-boundaries.md`
- Create: `docs/records/2026-05-18-phase46-model-world-constraints.md`
- Modify: `scripts/validate_docs.py`
- Modify: `tests/test_phase0_bootstrap.py`

- [ ] **Step 1: Update claim boundaries**

Add Phase 46 current/verified bullets that state model-derived
`mabd:world_constraint` rows are verified for dense CPU oracle configuration
only. Also add a forbidden-claim bullet saying Phase 46 is not a paper
experiment pass, contact implementation, GPU/Warp solver, or full reproduction.

- [ ] **Step 2: Add the Phase46 record**

Create `docs/records/2026-05-18-phase46-model-world-constraints.md` with:

- status `passed_for_solver_model_world_constraint_config_slice`;
- branch and commit fields;
- vendored Newton provenance;
- environment isolation statement;
- RED/GREEN evidence;
- claim impact saying no `experiment.*` claim is passed.

- [ ] **Step 3: Extend docs validator**

Add `validate_phase46_record()` and a smoke test that builds a one-body model
with a `mabd:world_constraint` row, runs `SolverMABD.step()`, confirms one
cached world constraint, dense topology, low residual, and a 3-vector
`dlambda`.

- [ ] **Step 4: Extend bootstrap docs tests**

Add a `tests/test_phase0_bootstrap.py` test that checks the Phase 46 claim
boundary snippets and the Phase 46 record are present while experiment claims
remain unpassed.

- [ ] **Step 5: Run documentation gates**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_phase0_bootstrap
```

Expected: both pass.

### Task 4: Final Verification

**Files:**
- No additional code changes expected.

- [ ] **Step 1: Run full gates**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/env/readiness_check.py
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"
git diff --check
```

Expected: all commands pass and vendored Newton resolves under this worktree.

- [ ] **Step 2: Review claim boundaries**

Confirm Phase 46 does not mark any `experiment.*` claim as passed and does not
claim contacts, Control ingestion, GPU/Warp kernels, paper timing, rendered
results, or a full paper reproduction.
