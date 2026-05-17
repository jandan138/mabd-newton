# Phase 45 Model Constraint Config Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let `SolverMABD.step()` build CPU oracle joint constraints from Newton `mabd:constraint` model rows.

**Architecture:** Add a small constraint-row translation layer inside `SolverMABD` that reuses existing `MABDCPUOracleConstraint` and joint-spec constructors. The model path derives body configs, model constraints, and model controls into one cached `MABDCPUOracleConfig`, while manual `configure_cpu_oracle(...)` remains authoritative.

**Tech Stack:** Python 3.10, vendored Newton, Warp custom attributes, `unittest`, `scripts/validate_docs.py`.

---

### Task 1: RED Tests For Model-Derived Constraint Rows

**Files:**
- Modify: `tests/test_mabd_phase4_solver_step.py`
- Modify: `tests/test_mabd_phase2_joints_kkt.py`

- [ ] **Step 1: Add model helper functions**

Add helpers in `tests/test_mabd_phase4_solver_step.py`:

```python
def _add_model_constraint_row(
    builder: newton.ModelBuilder,
    *,
    body_a: int,
    body_b: int,
    rank: int,
    constraint_type: int = 0,
    gradient_mode: int = 0,
    axis0: tuple[float, float, float] = (0.0, 1.0, 0.0),
    axis1: tuple[float, float, float] = (0.0, 0.0, 1.0),
    cp_index: int = 0,
) -> None:
    builder.add_custom_values(
        **{
            "mabd:constraint_type": constraint_type,
            "mabd:body_a": body_a,
            "mabd:body_b": body_b,
            "mabd:rank": rank,
            "mabd:gradient_mode": gradient_mode,
            "mabd:axis0": wp.vec3(*axis0),
            "mabd:axis1": wp.vec3(*axis1),
            "mabd:cp_index": cp_index,
        }
    )
```

- [ ] **Step 2: Add failing ball-constraint step test**

Add:

```python
def test_solver_step_model_path_builds_ball_constraint_from_model_rows(self) -> None:
    builder = newton.ModelBuilder()
    SolverMABD.register_custom_attributes(builder)
    for _ in range(2):
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
    _add_model_constraint_row(builder, body_a=0, body_b=1, rank=3, constraint_type=0)
    model = builder.finalize()
    solver = SolverMABD(model)
    q = [_identity_q((0.0, 0.0, 0.0)), _identity_q((0.2, 0.0, 0.0))]
    qd = [np.zeros(12), np.zeros(12)]
    state = model.state()
    _assign_mabd_state(state, q, qd)

    solver.step(state, state, None, None, 0.01)

    self.assertEqual(len(solver.model_cpu_oracle_config.constraints), 1)
    self.assertLess(solver.last_step_result.constraint_residual_norm, 1.0e-10)
```

- [ ] **Step 3: Add manual-precedence regression**

Add:

```python
def test_solver_step_manual_config_takes_precedence_over_model_constraints(self) -> None:
    model = _mabd_model_with_one_constraint()
    solver = SolverMABD(model)
    solver.configure_cpu_oracle(mabd.MABDCPUOracleConfig(bodies=[_body()]))
    state = model.state()
    _assign_mabd_state(state, _identity_q(), np.zeros(12))

    solver.step(state, state, None, None, 0.01)

    self.assertIsNone(solver.model_cpu_oracle_config)
    self.assertEqual(solver.last_step_result.topology, "unconstrained")
```

- [ ] **Step 4: Add constraint schema registration test**

Extend `test_solver_registers_constraint_frequency_rows` in
`tests/test_mabd_phase2_joints_kkt.py` to assert `mabd:cp_index` exists and
defaults or stores an integer value.

- [ ] **Step 5: Verify RED**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_mabd_phase4_solver_step tests.test_mabd_phase2_joints_kkt
```

Expected before implementation: the model-derived ball-constraint test fails
with the Phase44 `NotImplementedError` that model-derived constraints are not
supported, and the schema test fails because `cp_index` is not registered.

### Task 2: Implement Model Constraint Translation

**Files:**
- Modify: `vendor/newton/newton/_src/solvers/mabd/solver_mabd.py`

- [ ] **Step 1: Import existing joint constructors and oracle constraint**

Add imports for:

```python
from .joint_constraints import (
    JointGradientMode,
    ball_joint,
    hinge_joint,
    prismatic_joint,
    universal_joint,
)
from .step_oracle import MABDCPUOracleConstraint
```

- [ ] **Step 2: Register `mabd:cp_index`**

Add `cp_index` as an `wp.int32` model attribute on `mabd:constraint`, default
`0`.

- [ ] **Step 3: Add constraint-row helper**

Add:

```python
def _rest_points_from_model_body_row(self, row: int) -> np.ndarray:
    namespace = self.model.mabd
    return np.asarray(
        [
            namespace.rest_point0.numpy()[row],
            namespace.rest_point1.numpy()[row],
            namespace.rest_point2.numpy()[row],
            namespace.rest_point3.numpy()[row],
        ],
        dtype=float,
    )

def _gradient_mode_from_model(self, value: int) -> JointGradientMode:
    if int(value) == 0:
        return JointGradientMode.FINITE_DIFFERENCE_ORACLE
    if int(value) == 1:
        return JointGradientMode.PAPER_FAITHFUL
    raise ValueError("mabd:gradient_mode must be 0 or 1")
```

Refactor `_body_precompute_from_model_row(...)` to call
`_rest_points_from_model_body_row(row)`.

- [ ] **Step 4: Build constraints from rows**

Add:

```python
def _constraint_from_model_row(self, row: int, body_count: int) -> MABDCPUOracleConstraint:
    namespace = self.model.mabd
    body_a = int(namespace.body_a.numpy()[row])
    body_b = int(namespace.body_b.numpy()[row])
    if not 0 <= body_a < body_count or not 0 <= body_b < body_count:
        raise ValueError("mabd:constraint body indices must reference mabd:body rows")
    rank = int(namespace.rank.numpy()[row])
    constraint_type = int(namespace.constraint_type.numpy()[row])
    ct_a = self._rest_points_from_model_body_row(body_a)
    ct_b = self._rest_points_from_model_body_row(body_b)
    axis0 = namespace.axis0.numpy()[row]
    axis1 = namespace.axis1.numpy()[row]
    cp_index = int(namespace.cp_index.numpy()[row])

    if constraint_type in (0, 1):
        if rank == 3:
            spec = ball_joint(ct_a, ct_b, cp_index=cp_index)
        elif rank == 4:
            spec = universal_joint(ct_a, ct_b, axis0=axis0, axis1=axis1)
        elif rank == 5:
            spec = hinge_joint(ct_a, ct_b, axis=axis0)
        else:
            raise ValueError("mabd:rank must be 3, 4, or 5 for inferred constraints")
    elif constraint_type == 2:
        spec = ball_joint(ct_a, ct_b, cp_index=cp_index)
    elif constraint_type == 3:
        spec = hinge_joint(ct_a, ct_b, axis=axis0)
    elif constraint_type == 4:
        spec = universal_joint(ct_a, ct_b, axis0=axis0, axis1=axis1)
    elif constraint_type == 5:
        spec = prismatic_joint(ct_a, ct_b, axis=axis0)
    else:
        raise ValueError("mabd:constraint_type must be 0..5")
    if rank and rank != int(spec_rank):
        raise ValueError("mabd:rank does not match derived joint rank")
    return MABDCPUOracleConstraint(
        body_a=body_a,
        body_b=body_b,
        spec=spec,
        gradient_mode=self._gradient_mode_from_model(int(namespace.gradient_mode.numpy()[row])),
    )
```

Use `evaluate_joint(spec, zeros, zeros).rank` or an equivalent local mapping to
compute `spec_rank` without duplicating joint internals.

- [ ] **Step 5: Include model constraints in config**

Replace the Phase44 constraint rejection in `_cpu_oracle_config_from_model()`
with:

```python
constraints=tuple(
    self._constraint_from_model_row(row, body_count)
    for row in range(constraint_count)
)
```

- [ ] **Step 6: Verify GREEN**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_mabd_phase4_solver_step tests.test_mabd_phase2_joints_kkt
```

Expected: all tests pass.

### Task 3: Broaden Constraint Coverage

**Files:**
- Modify: `tests/test_mabd_phase4_solver_step.py`

- [ ] **Step 1: Add hinge/universal model-path comparison test**

Add a test that builds three model bodies with a rank-5 hinge row and rank-4
universal row. Compare `solver.step(...)` against `mabd.solve_cpu_oracle_step`
with explicit `MABDCPUOracleConstraint` specs built from the same unit tetra and
axes.

- [ ] **Step 2: Add invalid-row tests**

Add tests for:

- bad `mabd:constraint_type`;
- bad `mabd:rank`;
- out-of-range body index.

Each test must assert the clear error message.

- [ ] **Step 3: Verify focused tests**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_mabd_phase4_solver_step tests.test_mabd_phase2_joints_kkt tests.test_mabd_phase3_topology_solvers
```

Expected: all tests pass.

### Task 4: Phase45 Docs And Validator

**Files:**
- Modify: `docs/reference/claim-boundaries.md`
- Modify: `scripts/validate_docs.py`
- Modify: `tests/test_phase0_bootstrap.py`
- Create: `docs/records/2026-05-18-phase45-model-constraint-config.md`

- [ ] **Step 1: Add RED doc tests**

Add Phase45 tests requiring:

- boundary bullets for current/verified/non-claim/forbidden text;
- record evidence for model-derived constraints, vendored Newton patch, and
  verification commands;
- `validate_docs.py` final success text to include Phase 45.

- [ ] **Step 2: Verify RED**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_phase0_bootstrap
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
```

Expected before docs update: missing Phase45 boundary/record/validator failures.

- [ ] **Step 3: Implement docs and validator**

Record Phase45 as model constraint config evidence only. `validate_docs.py`
must include the spec, plan, record path, Phase45 record checks, a minimal
model-derived ball-constraint smoke, and a guard that no `experiment.*` claim is
passed.

- [ ] **Step 4: Verify GREEN**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_phase0_bootstrap
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
```

Expected: both pass and validator prints Phase 0-45.

### Task 5: Review, Final Gates, Merge, Push

**Files:**
- All changed files.

- [ ] **Step 1: Run final gates**

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/env/readiness_check.py
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"
npm --prefix site run validate
git diff --check
```

- [ ] **Step 2: Request multi-agent review**

Dispatch one solver reviewer and one claims/evidence reviewer. Fix Critical and
Important findings before merging.

- [ ] **Step 3: Merge and push**

Fast-forward `main`, rerun merged-result gates, push `origin main`, verify local
and remote SHAs match, and clean the Phase45 worktree.
