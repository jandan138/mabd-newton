# Phase 44 Solver Model Config Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let `SolverMABD.step()` build and use a CPU M-ABD body config from Newton `mabd:body` model rows when no manual `configure_cpu_oracle(...)` config is supplied.

**Architecture:** Extend the vendored Newton M-ABD body custom attributes with rest tetrahedron, optional point masses, and optional volume. Add a cached model-derived config builder inside `SolverMABD`, and keep unsupported model constraint rows, `Contacts`, and runtime `Control` as explicit guarded boundaries.

**Tech Stack:** Python 3.10, vendored Newton, Warp custom attributes, `unittest`, `scripts/validate_docs.py`.

---

### Task 1: RED Tests For Model-Derived Solver Step

**Files:**
- Modify: `tests/test_mabd_phase4_solver_step.py`
- Modify: `tests/test_mabd_single_body.py`

- [ ] **Step 1: Add failing tests**

Add tests that expect:

```python
def test_solver_step_builds_cpu_config_from_model_body_rows(self) -> None:
    model = _mabd_model()
    solver = SolverMABD(model)
    q = _identity_q((0.2, -0.1, 0.3))
    qd = np.linspace(-0.2, 0.25, 12)
    dt = 0.02
    state_in = model.state()
    state_out = model.state()
    _assign_mabd_state(state_in, q, qd)

    solver.step(state_in, state_out, None, None, dt)

    q_next, qd_next = _read_mabd_state(state_out)
    np.testing.assert_allclose(q_next[0], q + dt * qd, atol=1.0e-7)
    np.testing.assert_allclose(qd_next[0], qd, atol=1.0e-7)
    self.assertEqual(solver.last_step_result.topology, "unconstrained")
```

```python
def test_solver_step_model_path_consumes_enabled_control_rows(self) -> None:
    builder = newton.ModelBuilder()
    SolverMABD.register_custom_attributes(builder)
    _add_mabd_body(builder)
    _add_control_row(builder, stiffness=2.0, target_t=(0.5, 0.0, 0.0), feedforward_t=(0.0, 0.25, 0.0))
    model = builder.finalize()
    solver = SolverMABD(model)
    q = _identity_q()
    dt = 0.1
    state = model.state()
    _assign_mabd_state(state, q, np.zeros(12))

    solver.step(state, state, None, None, dt)

    q_next, _qd_next = _read_mabd_state(state)
    expected_force = np.zeros(12)
    expected_force[9] = 1.0
    expected_force[10] = 0.25
    np.testing.assert_allclose(q_next[0], q + dt * dt * expected_force, atol=1.0e-7)
```

```python
def test_solver_step_model_path_rejects_constraint_rows_until_specs_are_stored(self) -> None:
    model = _loop_model_with_mabd_constraints()
    solver = SolverMABD(model)

    with self.assertRaisesRegex(NotImplementedError, "model-derived.*constraint"):
        solver.step(model.state(), model.state(), None, None, 0.01)
```

- [ ] **Step 2: Verify RED**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_mabd_phase4_solver_step tests.test_mabd_single_body tests.test_mabd_control_forces
```

Expected before implementation: failures show unconfigured `SolverMABD.step()`
still requires `configure_cpu_oracle(...)`.

### Task 2: Implement Model Body Attributes And Config Builder

**Files:**
- Modify: `vendor/newton/newton/_src/solvers/mabd/solver_mabd.py`
- Modify: `tests/test_mabd_single_body.py`

- [ ] **Step 1: Add custom body attributes**

Add body-row attributes for `rest_point0..3`, `point_mass0..3`, and `volume`.
Default rest points are the unit tetrahedron:

```python
wp.vec3(0.0, 0.0, 0.0)
wp.vec3(1.0, 0.0, 0.0)
wp.vec3(0.0, 1.0, 0.0)
wp.vec3(0.0, 0.0, 1.0)
```

Default point masses and volume use `-1.0` sentinel values.

- [ ] **Step 2: Add model-derived helpers**

Add private helpers on `SolverMABD` with these signatures:

```python
def _rotation_mode_from_model(value: int) -> str:
    """Return one of 'none', 'polar', or 'no_polar' for model polar_mode."""

def _body_precompute_from_model_row(self, row: int) -> MABDCPUOracleBody:
    """Build one CPU oracle body from a row of model.mabd body data."""

def _cpu_oracle_config_from_model(self) -> MABDCPUOracleConfig:
    """Build or return the cached model-derived CPU oracle config."""
```

The builder must derive mass and volume deterministically, reject mixed explicit
and derived point masses, reject nonpositive volume, reject bad `polar_mode`,
and include `actuation_specs_from_model(self.model)`.

- [ ] **Step 3: Use model config in `step()`**

When `self.cpu_oracle_config` is `None`, call the cached model-derived config
builder instead of raising. Preserve current explicit rejections for non-`None`
`control` and `contacts`.

- [ ] **Step 4: Verify GREEN**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_mabd_phase4_solver_step tests.test_mabd_single_body tests.test_mabd_control_forces
```

Expected after implementation: all focused tests pass.

### Task 3: Documentation, Boundaries, And Validator

**Files:**
- Modify: `docs/reference/claim-boundaries.md`
- Modify: `scripts/validate_docs.py`
- Modify: `tests/test_phase0_bootstrap.py`
- Create: `docs/records/2026-05-18-phase44-solver-model-config.md`

- [ ] **Step 1: Add Phase44 boundary tests**

Add tests requiring Phase44 current/verified/forbidden text and the Phase44
record path.

- [ ] **Step 2: Verify RED**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_phase0_bootstrap
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
```

Expected before docs update: failures mention missing Phase44 boundary or
record evidence.

- [ ] **Step 3: Update docs and validator**

Record Phase44 as solver integration evidence only. The record must include the
canonical env, branch, commit, commands, focused tests, unsupported boundaries,
and status `passed_for_solver_model_config_slice`.

- [ ] **Step 4: Verify GREEN**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_phase0_bootstrap
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
```

Expected after docs update: both pass and validator prints Phase 0-44.

### Task 4: Final Gates And Push

**Files:**
- All changed files.

- [ ] **Step 1: Run final gates**

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/env/readiness_check.py
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"
git diff --check
```

- [ ] **Step 2: Review and merge**

Request code review, fix Critical or Important findings, fast-forward `main`,
rerun merged-result gates, and push `main` to `origin`.
