# Phase 47 Model Gravity Config Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let `SolverMABD.step()` build `MABDCPUOracleConfig.gravity` from Newton `mabd:gravity` model rows.

**Architecture:** Add a small gravity-row translation layer inside `SolverMABD` that reuses the existing Phase 32 CPU oracle gravity field. The model path derives body configs, joint constraints, world constraints, gravity, and controls into one cached `MABDCPUOracleConfig`, while manual `configure_cpu_oracle(...)` remains authoritative.

**Tech Stack:** Python 3.10, vendored Newton, Warp custom attributes, `unittest`, `scripts/validate_docs.py`.

---

### Task 1: RED Tests For Model-Derived Gravity

**Files:**
- Modify: `tests/test_mabd_phase4_solver_step.py`

- [ ] **Step 1: Add a helper for gravity rows**

Add this helper near `_add_model_world_constraint_row(...)`:

```python
def _add_model_gravity_row(
    builder: newton.ModelBuilder,
    *,
    enabled: int = 1,
    gravity: tuple[float, float, float] = (0.0, -9.81, 0.0),
) -> None:
    builder.add_custom_values(
        **{
            "mabd:gravity_enabled": enabled,
            "mabd:gravity_vector": wp.vec3(*gravity),
        }
    )
```

- [ ] **Step 2: Add a failing model-path gravity test**

Add:

```python
def test_solver_step_model_path_consumes_enabled_gravity_row(self) -> None:
    builder = newton.ModelBuilder()
    SolverMABD.register_custom_attributes(builder)
    _add_model_body_row(builder, young_modulus=1.0)
    _add_model_gravity_row(builder, gravity=(0.0, -9.81, 1.25))
    model = builder.finalize()
    solver = SolverMABD(model)
    q = _identity_q((0.1, 0.2, -0.3))
    qd = np.zeros(12)
    state = model.state()
    _assign_mabd_state(state, q, qd)
    dt = 0.02

    solver.step(state, state, None, None, dt)

    expected = mabd.solve_cpu_oracle_step(
        q=[q],
        qd=[qd],
        dt=dt,
        config=mabd.MABDCPUOracleConfig(
            bodies=[_model_path_body(young_modulus=1.0)],
            gravity=np.array([0.0, -9.81, 1.25], dtype=float),
        ),
    )
    q_next, qd_next = _read_mabd_state(state)
    np.testing.assert_allclose(q_next[0], expected.q[0], atol=1.0e-7)
    np.testing.assert_allclose(qd_next[0], expected.qd[0], atol=1.0e-7)
    np.testing.assert_allclose(solver.model_cpu_oracle_config.gravity, [0.0, -9.81, 1.25])
```

- [ ] **Step 3: Add disabled-row test**

Add:

```python
def test_solver_step_model_path_ignores_disabled_gravity_rows(self) -> None:
    builder = newton.ModelBuilder()
    SolverMABD.register_custom_attributes(builder)
    _add_model_body_row(builder, young_modulus=1.0)
    _add_model_gravity_row(builder, enabled=0, gravity=(0.0, -9.81, 1.25))
    model = builder.finalize()
    solver = SolverMABD(model)
    q = _identity_q((0.1, 0.2, -0.3))
    qd = np.zeros(12)
    state = model.state()
    _assign_mabd_state(state, q, qd)
    dt = 0.02

    solver.step(state, state, None, None, dt)

    expected = mabd.solve_cpu_oracle_step(
        q=[q],
        qd=[qd],
        dt=dt,
        config=mabd.MABDCPUOracleConfig(bodies=[_model_path_body(young_modulus=1.0)]),
    )
    q_next, qd_next = _read_mabd_state(state)
    np.testing.assert_allclose(q_next[0], expected.q[0], atol=1.0e-7)
    np.testing.assert_allclose(qd_next[0], expected.qd[0], atol=1.0e-7)
    self.assertIsNone(solver.model_cpu_oracle_config.gravity)
```

- [ ] **Step 4: Add multiple-enabled-row rejection test**

Add:

```python
def test_solver_step_model_path_rejects_multiple_enabled_gravity_rows(self) -> None:
    builder = newton.ModelBuilder()
    SolverMABD.register_custom_attributes(builder)
    _add_model_body_row(builder, young_modulus=1.0)
    _add_model_gravity_row(builder, gravity=(0.0, -9.81, 0.0))
    _add_model_gravity_row(builder, gravity=(0.0, -1.0, 0.0))
    model = builder.finalize()
    solver = SolverMABD(model)
    state = model.state()
    _assign_mabd_state(state, _identity_q(), np.zeros(12))

    with self.assertRaisesRegex(ValueError, "mabd:gravity"):
        solver.step(state, state, None, None, 0.02)
```

- [ ] **Step 5: Add manual-config precedence test**

Add:

```python
def test_solver_step_manual_config_takes_precedence_over_model_gravity(self) -> None:
    builder = newton.ModelBuilder()
    SolverMABD.register_custom_attributes(builder)
    _add_model_body_row(builder, young_modulus=1.0)
    _add_model_gravity_row(builder, gravity=(0.0, -9.81, 1.25))
    model = builder.finalize()
    solver = SolverMABD(model)
    solver.configure_cpu_oracle(mabd.MABDCPUOracleConfig(bodies=[_body()]))
    state = model.state()
    _assign_mabd_state(state, _identity_q(), np.zeros(12))

    solver.step(state, state, None, None, 0.02)

    self.assertIsNone(solver.model_cpu_oracle_config)
    self.assertEqual(solver.last_step_result.topology, "unconstrained")
```

- [ ] **Step 6: Verify RED**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_mabd_phase4_solver_step
```

Expected before implementation: tests fail because `mabd:gravity_enabled` is
not a registered custom attribute.

### Task 2: Implement Model Gravity Translation

**Files:**
- Modify: `vendor/newton/newton/_src/solvers/mabd/solver_mabd.py`

- [ ] **Step 1: Register gravity frequency and attributes**

Add:

```python
MABD_GRAVITY_FREQUENCY = "mabd:gravity"
```

Register:

```python
builder.add_custom_frequency(ModelBuilder.CustomFrequency(name="gravity", namespace="mabd"))
```

Add model attributes:

```python
gravity_attrs = (
    ModelBuilder.CustomAttribute(
        name="gravity_enabled",
        frequency=cls.MABD_GRAVITY_FREQUENCY,
        assignment=Model.AttributeAssignment.MODEL,
        dtype=wp.int32,
        default=0,
        namespace="mabd",
    ),
    ModelBuilder.CustomAttribute(
        name="gravity_vector",
        frequency=cls.MABD_GRAVITY_FREQUENCY,
        assignment=Model.AttributeAssignment.MODEL,
        dtype=wp.vec3,
        default=wp.vec3(0.0, 0.0, 0.0),
        namespace="mabd",
    ),
)
```

Include `*gravity_attrs` in the registration loop.

- [ ] **Step 2: Add row translation**

Add:

```python
def _gravity_from_model(self) -> np.ndarray | None:
    count = self._custom_frequency_count(self.MABD_GRAVITY_FREQUENCY)
    namespace = self.model.mabd
    enabled = [
        row
        for row in range(count)
        if int(namespace.gravity_enabled.numpy()[row]) != 0
    ]
    if not enabled:
        return None
    if len(enabled) > 1:
        raise ValueError("mabd:gravity supports at most one enabled row")
    return np.asarray(namespace.gravity_vector.numpy()[enabled[0]], dtype=float)
```

- [ ] **Step 3: Include gravity in model-derived config**

Pass:

```python
gravity=self._gravity_from_model(),
```

to `MABDCPUOracleConfig(...)`.

- [ ] **Step 4: Verify GREEN**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_mabd_phase4_solver_step
```

Expected: all solver-step tests pass.

### Task 3: Documentation, Provenance, And Validator

**Files:**
- Modify: `docs/reference/claim-boundaries.md`
- Create: `docs/records/2026-05-18-phase47-model-gravity-config.md`
- Modify: `scripts/validate_docs.py`
- Modify: `tests/test_phase0_bootstrap.py`

- [ ] **Step 1: Update claim boundaries**

Add this bullet under the current evidence section:

```markdown
- Phase 47 adds model-derived `mabd:gravity` rows for CPU oracle configuration
  only. It translates a single enabled model gravity row into
  `MABDCPUOracleConfig.gravity`, ignores disabled rows, rejects multiple enabled
  rows, and preserves manual `configure_cpu_oracle(...)` precedence.
```

Add this bullet under the verified section:

```markdown
- Phase 47 verifies model-derived `mabd:gravity` rows through unit tests and a
  docs-validator smoke test that compares `SolverMABD.step()` against explicit
  `MABDCPUOracleConfig.gravity` behavior for one unconstrained body.
```

Add this bullet under forbidden or not-yet-supported claims:

```markdown
- Phase 47 model gravity configuration is not a heavy-top pass, physical
  pendulum scene pass, contact implementation, runtime `Control` integration,
  GPU/Warp solver, paper timing result, rendered-output result, or full paper
  reproduction.
```

- [ ] **Step 2: Add the Phase47 record**

Create `docs/records/2026-05-18-phase47-model-gravity-config.md` with:

Use this structure and fill the commit hashes after the commits exist:

```markdown
# Phase 47 Model Gravity Config Record

## Status

passed_for_solver_model_gravity_config_slice

## Scope

Phase 47 verifies that model-derived `mabd:gravity` rows can configure the
existing CPU oracle uniform gravity field used by `SolverMABD.step()`.

## Provenance

- Branch: `phase47-model-gravity-config`
- Plan commit: `<plan-commit>`
- RED test commit: `<red-test-commit>`
- Implementation commit: `<implementation-commit>`
- Evidence commit: `<evidence-commit>`
- Vendored Newton path: `vendor/newton`
- Environment: `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python`

## Evidence

- RED: targeted solver-step tests failed before `mabd:gravity` registration.
- GREEN: targeted solver-step tests pass after `mabd:gravity` registration and
  model translation.
- Validator: `scripts/validate_docs.py` checks this record, claim boundaries,
  spec/plan guardrails, and a model-derived gravity smoke test.

## Claim Impact

No `experiment.*` claim is passed by Phase 47. This record does not claim a
heavy-top pass, physical-pendulum scene pass, Contacts support, runtime
`Control` support, GPU/Warp solver support, paper timing, rendered output, or
full paper reproduction.
```

- [ ] **Step 3: Extend docs validator required paths**

In `scripts/validate_docs.py`, add these paths to `REQUIRED_PATHS`:

```python
"docs/records/2026-05-18-phase47-model-gravity-config.md",
"docs/superpowers/specs/2026-05-18-phase47-model-gravity-config-design.md",
"docs/superpowers/plans/2026-05-18-mabd-phase47-model-gravity-config.md",
```

- [ ] **Step 4: Add docs-validator smoke test**

Add `validate_phase47_model_gravity_smoke()` near the Phase 46 smoke test:

```python
def validate_phase47_model_gravity_smoke() -> None:
    import numpy as np
    import warp as wp
    import newton
    from newton.solvers import SolverMABD, mabd

    builder = newton.ModelBuilder()
    SolverMABD.register_custom_attributes(builder)
    body_id = builder.add_body()
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
    builder.add_custom_values(
        **{
            "mabd:gravity_enabled": 1,
            "mabd:gravity_vector": wp.vec3(0.0, -9.81, 1.25),
        }
    )
    model = builder.finalize()
    solver = SolverMABD(model)
    state = model.state()
    state.mabd.q0.assign(np.asarray([[1.0, 0.0, 0.0]], dtype=np.float32))
    state.mabd.q1.assign(np.asarray([[0.0, 1.0, 0.0]], dtype=np.float32))
    state.mabd.q2.assign(np.asarray([[0.0, 0.0, 1.0]], dtype=np.float32))
    state.mabd.t.assign(np.asarray([[0.1, 0.2, -0.3]], dtype=np.float32))
    state.mabd.qd0.assign(np.zeros((1, 3), dtype=np.float32))
    state.mabd.qd1.assign(np.zeros((1, 3), dtype=np.float32))
    state.mabd.qd2.assign(np.zeros((1, 3), dtype=np.float32))
    state.mabd.td.assign(np.zeros((1, 3), dtype=np.float32))

    solver.step(state, state, None, None, 0.02)

    config = solver.model_cpu_oracle_config
    if config is None or not np.allclose(config.gravity, [0.0, -9.81, 1.25]):
        fail("Phase 47 model gravity smoke failed to cache MABDCPUOracleConfig.gravity")
```

- [ ] **Step 5: Add record and guardrail validators**

Add a `validate_phase47_record()` that checks for these snippets:

```python
"## Status\n\npassed_for_solver_model_gravity_config_slice",
"`mabd:gravity`",
"MABDCPUOracleConfig.gravity",
"manual `configure_cpu_oracle(...)` precedence",
"No `experiment.*` claim is passed",
```

Add a `validate_phase47_spec_and_plan()` that checks the spec and plan contain:

```python
"`mabd:gravity`",
"multiple enabled gravity rows",
"manual `configure_cpu_oracle(...)` remains",
"not a heavy-top pass",
"not a paper experiment pass",
```

- [ ] **Step 6: Run documentation gates**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_phase0_bootstrap
```

Expected: both pass.

### Task 4: Final Verification

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/env/readiness_check.py
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"
git diff --check
```

Expected: all commands pass and no `experiment.*` claim is marked passed.
