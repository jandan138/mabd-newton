# Phase 48 Physical Pendulum Model-Derived Lane Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the physical-pendulum `mabd_newton` report lane step through Newton model-derived `SolverMABD.step()` instead of a hand-built `MABDCPUOracleConfig`.

**Architecture:** Keep the existing manual rollout for the development diagnostic lane. Add a second rollout path that builds a Newton model with `mabd:body`, `mabd:world_constraint`, and `mabd:gravity` rows, then advances state through `SolverMABD.step()`. Report provenance records which solver config source was used while keeping all experiment pass claims incomplete.

**Tech Stack:** Python 3.10, vendored Newton, Warp custom attributes, NumPy, `unittest`, `scripts/validate_docs.py`.

---

### Task 1: RED Tests For Model-Derived Physical Pendulum Rollout

**Files:**
- Modify: `tests/test_physical_pendulum_mabd.py`
- Modify: `tests/test_experiment_runner.py`

- [ ] **Step 1: Add rollout API import and parity test**

Add this import:

```python
from mabd_reproduction.physical_pendulum_mabd import (
    roll_out_physical_pendulum_mabd_development,
    roll_out_physical_pendulum_mabd_model_derived,
)
```

Add:

```python
def test_model_derived_rollout_matches_manual_oracle_diagnostic(self) -> None:
    config = load_physical_pendulum_config(CONFIG_PATH)

    manual = roll_out_physical_pendulum_mabd_development(config, rotation_mode="polar")
    model = roll_out_physical_pendulum_mabd_model_derived(config, rotation_mode="polar")

    self.assertEqual(model.solver_model_config_source, "newton_model_derived")
    self.assertEqual(model.rotation_mode, "polar")
    self.assertEqual(model.sample_count, manual.sample_count)
    self.assertEqual(model.step_count, manual.step_count)
    self.assertTrue(model.finite)
    np.testing.assert_allclose(
        [sample.angle_rad for sample in model.samples],
        [sample.angle_rad for sample in manual.samples],
        atol=2.0e-6,
    )
    np.testing.assert_allclose(
        [sample.pivot_residual_m for sample in model.samples],
        [sample.pivot_residual_m for sample in manual.samples],
        atol=2.0e-6,
    )
    np.testing.assert_allclose(
        [sample.world_anchor_reaction_magnitude_n for sample in model.samples],
        [sample.world_anchor_reaction_magnitude_n for sample in manual.samples],
        atol=2.0e-5,
    )
```

- [ ] **Step 2: Add report provenance assertions**

In `test_run_physical_pendulum_mabd_newton_writes_required_lane_report`, add:

```python
self.assertEqual(
    loaded.observed["solver_model_config_source"],
    "newton_model_derived",
)
self.assertEqual(
    loaded.expected["solver_model_config_source"],
    "newton_model_derived",
)
```

- [ ] **Step 3: Verify RED**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_physical_pendulum_mabd tests.test_experiment_runner
```

Expected before implementation: import failure for
`roll_out_physical_pendulum_mabd_model_derived` or missing
`solver_model_config_source`.

### Task 2: Implement Model-Derived Rollout

**Files:**
- Modify: `src/mabd_reproduction/physical_pendulum_mabd.py`
- Modify: `src/mabd_reproduction/physical_pendulum_reports.py`

- [ ] **Step 1: Add imports**

In `physical_pendulum_mabd.py`, add:

```python
import newton
import warp as wp
from newton.solvers import SolverMABD
```

- [ ] **Step 2: Track rollout config source**

Add `solver_model_config_source: str` to `PhysicalPendulumMABDRollout`.

Manual rollouts return:

```python
solver_model_config_source="manual_cpu_oracle_config"
```

Model-derived rollouts return:

```python
solver_model_config_source="newton_model_derived"
```

- [ ] **Step 3: Add state helpers**

Add private helpers:

```python
def _assign_solver_state(state: object, q: np.ndarray, qd: np.ndarray) -> None:
    q_arr = np.asarray([q], dtype=np.float32)
    qd_arr = np.asarray([qd], dtype=np.float32)
    state.mabd.q0.assign(q_arr[:, 0:3])
    state.mabd.q1.assign(q_arr[:, 3:6])
    state.mabd.q2.assign(q_arr[:, 6:9])
    state.mabd.t.assign(q_arr[:, 9:12])
    state.mabd.qd0.assign(qd_arr[:, 0:3])
    state.mabd.qd1.assign(qd_arr[:, 3:6])
    state.mabd.qd2.assign(qd_arr[:, 6:9])
    state.mabd.td.assign(qd_arr[:, 9:12])


def _read_solver_state(state: object) -> tuple[np.ndarray, np.ndarray]:
    q = np.concatenate(
        [state.mabd.q0.numpy(), state.mabd.q1.numpy(), state.mabd.q2.numpy(), state.mabd.t.numpy()],
        axis=1,
    )[0].astype(float, copy=False)
    qd = np.concatenate(
        [state.mabd.qd0.numpy(), state.mabd.qd1.numpy(), state.mabd.qd2.numpy(), state.mabd.td.numpy()],
        axis=1,
    )[0].astype(float, copy=False)
    return q, qd
```

- [ ] **Step 4: Add model builder helper**

Add:

```python
def _physical_pendulum_solver_model(config: PhysicalPendulumRunConfig, *, rotation_mode: str) -> object:
    lane = config.mabd_development
    polar_mode = {"none": 0, "polar": 1}[rotation_mode]
    builder = newton.ModelBuilder()
    SolverMABD.register_custom_attributes(builder)
    body_id = builder.add_body()
    builder.add_custom_values(
        **{
            "mabd:body_index": body_id,
            "mabd:young_modulus": 0.0,
            "mabd:poisson_ratio": 0.25,
            "mabd:density": 1.0,
            "mabd:polar_mode": polar_mode,
            "mabd:rest_point0": wp.vec3(*lane.rest_points_m[0]),
            "mabd:rest_point1": wp.vec3(*lane.rest_points_m[1]),
            "mabd:rest_point2": wp.vec3(*lane.rest_points_m[2]),
            "mabd:rest_point3": wp.vec3(*lane.rest_points_m[3]),
            "mabd:point_mass0": float(lane.masses_kg[0]),
            "mabd:point_mass1": float(lane.masses_kg[1]),
            "mabd:point_mass2": float(lane.masses_kg[2]),
            "mabd:point_mass3": float(lane.masses_kg[3]),
            "mabd:volume": -1.0,
        }
    )
    builder.add_custom_values(
        **{
            "mabd:world_body": 0,
            "mabd:world_rest_point": wp.vec3(*lane.pivot_rest_point_m),
            "mabd:world_point": wp.vec3(*lane.pivot_world_point_m),
        }
    )
    builder.add_custom_values(
        **{
            "mabd:gravity_enabled": 1,
            "mabd:gravity_vector": wp.vec3(*lane.gravity_m_s2),
        }
    )
    return builder.finalize()
```

- [ ] **Step 5: Add model-derived rollout function**

Add `roll_out_physical_pendulum_mabd_model_derived(...)` that mirrors the
existing rollout loop but reads/writes Newton state and steps with
`SolverMABD(model).step(...)`.

- [ ] **Step 6: Use it for the formal `mabd_newton` report**

In `write_physical_pendulum_mabd_newton_report`, call:

```python
rollout = roll_out_physical_pendulum_mabd_model_derived(
    config,
    rotation_mode=config.mabd_newton.rotation_mode,
)
```

Add `solver_model_config_source` to the report `observed` and `expected`
sections.

- [ ] **Step 7: Verify GREEN**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_physical_pendulum_mabd tests.test_experiment_runner
```

Expected: targeted tests pass.

### Task 3: Records, Reports, And Validator

**Files:**
- Modify: `docs/reference/claim-boundaries.md`
- Create: `docs/records/2026-05-18-phase48-physical-pendulum-model-lane.md`
- Modify: `scripts/validate_docs.py`
- Modify: `tests/test_phase0_bootstrap.py`
- Modify: `reports/experiment_matrix/single_body_physical_pendulum_mabd_newton.json`
- Modify: `reports/experiment_matrix/single_body_physical_pendulum_comparison.json` if provenance or input report fields change.

- [ ] **Step 1: Regenerate small report artifacts**

Run the physical-pendulum `mabd_newton` lane and comparison lane with the
current source commit and vendored Newton commit so committed JSON reports
include `solver_model_config_source`.

- [ ] **Step 2: Update claim boundaries**

Add Phase48 current/verified/non-claim bullets stating that the formal
physical-pendulum `mabd_newton` lane now uses Newton model-derived
`SolverMABD.step()` body/world/gravity rows, but remains an incomplete
diagnostic and passes no `experiment.*` claim.

- [ ] **Step 3: Add the Phase48 record**

Record branch, base, plan, RED, implementation, evidence, vendored Newton,
environment isolation, RED/GREEN evidence, report artifact updates, review
results, and claim impact.

- [ ] **Step 4: Extend docs validator and bootstrap tests**

Require:

```python
"docs/records/2026-05-18-phase48-physical-pendulum-model-lane.md"
"docs/superpowers/specs/2026-05-18-phase48-physical-pendulum-model-lane-design.md"
"docs/superpowers/plans/2026-05-18-mabd-phase48-physical-pendulum-model-lane.md"
"solver_model_config_source"
"newton_model_derived"
"No `experiment.*` claim is passed"
```

Update the validator success string from Phase 0-47 to Phase 0-48.

- [ ] **Step 5: Run docs gates**

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
npm --prefix site run validate
git diff --check
```

Expected: all commands pass and all `experiment.*` claims remain incomplete or
blocked as before.
