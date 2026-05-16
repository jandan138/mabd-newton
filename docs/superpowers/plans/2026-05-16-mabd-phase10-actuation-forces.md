# Phase 10 Actuation Forces Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a CPU oracle for scene-script affine actuation/control forces so later robot-like and wind/drive scenes can route target, damping, and feedforward forces into M-ABD generalized forces without claiming paper scene reproduction.

**Architecture:** Add a focused vendored Newton module for affine actuation specs and evaluations, then wire those specs into `MABDCPUOracleConfig` so configured CPU oracle steps can add actuation forces to existing external forces. Register `mabd:control` custom attributes as durable storage for later scene import, but keep production `SolverMABD.step(..., control=...)` unsupported until a separate phase reads Newton `Control` objects.

**Tech Stack:** Python 3.10, NumPy, vendored Newton M-ABD helpers, Newton custom attributes, `unittest`, ruff, docs/provenance validator.

---

### File Structure

- Create `vendor/newton/newton/_src/solvers/mabd/control_forces.py`.
  Owns `MABDActuationSpec`, `MABDControlEvaluation`, affine PD/feedforward evaluation, and per-body force assembly.
- Modify `vendor/newton/newton/_src/solvers/mabd/step_oracle.py`.
  Adds `actuations` to `MABDCPUOracleConfig` and combines them with `external_forces`.
- Modify `vendor/newton/newton/_src/solvers/mabd/solver_mabd.py`.
  Registers `mabd:control` custom frequency and control attributes only; it must still reject runtime Newton `Control` input.
- Modify `vendor/newton/newton/_src/solvers/mabd/__init__.py`.
  Exports Phase 10 control helpers.
- Create `tests/test_mabd_control_forces.py`.
  Public tests for control force formula, aggregation, validation, custom attributes, and CPU oracle integration.
- Create `vendor/newton/newton/tests/test_mabd_control_forces.py`.
  Vendored mirror tests for low-level control helper behavior.
- Modify `docs/reference/paper-claims.yaml`, `docs/reference/claim-boundaries.md`, `scripts/validate_docs.py`, and `tests/test_phase0_bootstrap.py`.
  Adds bounded Phase 10 method claim and validator coverage.
- Create `docs/records/2026-05-16-phase10-actuation-forces.md`.
  Dated evidence record with command outputs and explicit non-claims.

---

### Task 1: RED Tests For Affine Actuation Force Mapping

**Files:**
- Create: `tests/test_mabd_control_forces.py`
- Create: `vendor/newton/newton/tests/test_mabd_control_forces.py`

- [ ] **Step 1: Add public tests for affine PD plus feedforward force**

Create `tests/test_mabd_control_forces.py` with:

```python
from __future__ import annotations

import unittest

import numpy as np
import warp as wp

import newton
import newton.solvers.mabd as mabd
from newton.solvers import SolverMABD


class MABDControlForcePublicTests(unittest.TestCase):
    def test_affine_pd_control_force_matches_formula(self) -> None:
        q = np.linspace(-0.3, 0.8, 12)
        qd = np.linspace(0.2, -0.1, 12)
        target_q = q + np.linspace(0.05, -0.02, 12)
        target_qd = qd + np.linspace(-0.03, 0.04, 12)
        feedforward = np.linspace(0.1, 1.2, 12)
        spec = mabd.MABDActuationSpec(
            body_id=2,
            target_q=target_q,
            target_qd=target_qd,
            stiffness=3.0,
            damping=np.linspace(0.5, 1.6, 12),
            feedforward_force=feedforward,
        )

        evaluation = mabd.evaluate_affine_pd_control(q, qd, spec)

        expected = 3.0 * (target_q - q) + spec.damping * (target_qd - qd) + feedforward
        self.assertEqual(evaluation.body_id, 2)
        self.assertTrue(np.allclose(evaluation.position_error, target_q - q))
        self.assertTrue(np.allclose(evaluation.velocity_error, target_qd - qd))
        self.assertTrue(np.allclose(evaluation.generalized_force, expected))

    def test_affine_pd_control_allows_feedforward_only(self) -> None:
        q = np.zeros(12)
        qd = np.zeros(12)
        feedforward = np.linspace(-0.4, 0.7, 12)
        spec = mabd.MABDActuationSpec(body_id=0, feedforward_force=feedforward)

        evaluation = mabd.evaluate_affine_pd_control(q, qd, spec)

        self.assertTrue(np.allclose(evaluation.position_error, np.zeros(12)))
        self.assertTrue(np.allclose(evaluation.velocity_error, np.zeros(12)))
        self.assertTrue(np.allclose(evaluation.generalized_force, feedforward))

    def test_assemble_control_generalized_forces_sums_by_body(self) -> None:
        q = [np.zeros(12), np.ones(12)]
        qd = [np.zeros(12), np.zeros(12)]
        base = [np.ones(12), np.full(12, 2.0)]
        act_a = mabd.MABDActuationSpec(
            body_id=1,
            target_q=np.full(12, 3.0),
            stiffness=0.5,
        )
        act_b = mabd.MABDActuationSpec(
            body_id=1,
            target_qd=np.full(12, -2.0),
            damping=0.25,
            feedforward_force=np.arange(12, dtype=float),
        )
        act_c = mabd.MABDActuationSpec(body_id=0, feedforward_force=np.full(12, -0.5))

        observed = mabd.assemble_control_generalized_forces(
            q,
            qd,
            actuations=[act_a, act_b, act_c],
            base_external_forces=base,
        )

        self.assertTrue(np.allclose(observed[0], np.full(12, 0.5)))
        expected_body_1 = base[1] + 0.5 * (np.full(12, 3.0) - q[1]) + 0.25 * np.full(12, -2.0) + np.arange(12)
        self.assertTrue(np.allclose(observed[1], expected_body_1))

    def test_control_force_validation_rejects_bad_ids_shapes_and_gains(self) -> None:
        q = [np.zeros(12)]
        qd = [np.zeros(12)]
        with self.assertRaisesRegex(ValueError, "body_id"):
            mabd.assemble_control_generalized_forces(
                q,
                qd,
                actuations=[mabd.MABDActuationSpec(body_id=3, feedforward_force=np.zeros(12))],
            )
        with self.assertRaisesRegex(ValueError, "target_q"):
            mabd.evaluate_affine_pd_control(
                np.zeros(12),
                np.zeros(12),
                mabd.MABDActuationSpec(body_id=0, target_q=np.zeros(11)),
            )
        with self.assertRaisesRegex(ValueError, "stiffness"):
            mabd.evaluate_affine_pd_control(
                np.zeros(12),
                np.zeros(12),
                mabd.MABDActuationSpec(body_id=0, stiffness=-1.0),
            )

    def test_solver_registers_control_frequency_rows(self) -> None:
        builder = newton.ModelBuilder()
        SolverMABD.register_custom_attributes(builder)
        body_id = builder.add_body()
        builder.add_custom_values(**{"mabd:body_index": body_id})
        builder.add_custom_values(
            **{
                "mabd:control_body": 0,
                "mabd:control_enabled": 1,
                "mabd:control_stiffness": 2.0,
                "mabd:control_damping": 0.5,
                "mabd:control_target_q0": wp.vec3(1.0, 0.0, 0.0),
                "mabd:control_target_t": wp.vec3(0.1, 0.2, 0.3),
                "mabd:control_feedforward_t": wp.vec3(0.0, 1.0, 0.0),
            }
        )

        model = builder.finalize()

        self.assertIn("mabd:control", builder.custom_frequencies)
        self.assertEqual(model.get_custom_frequency_count("mabd:control"), 1)
        self.assertEqual(int(model.mabd.control_body.numpy()[0]), 0)
        self.assertEqual(int(model.mabd.control_enabled.numpy()[0]), 1)
        self.assertAlmostEqual(float(model.mabd.control_stiffness.numpy()[0]), 2.0)
        self.assertTrue(np.allclose(model.mabd.control_target_t.numpy()[0], [0.1, 0.2, 0.3]))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Add vendored mirror tests**

Create `vendor/newton/newton/tests/test_mabd_control_forces.py` with the same formula, aggregation, and validation checks, importing from `newton._src.solvers.mabd`.

- [ ] **Step 3: Run RED**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_mabd_control_forces
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest vendor.newton.newton.tests.test_mabd_control_forces
```

Expected: fail because `MABDActuationSpec`, `evaluate_affine_pd_control`, and `assemble_control_generalized_forces` are missing.

### Task 2: Implement Control Force Helpers And Exports

**Files:**
- Create: `vendor/newton/newton/_src/solvers/mabd/control_forces.py`
- Modify: `vendor/newton/newton/_src/solvers/mabd/__init__.py`

- [ ] **Step 1: Add `MABDActuationSpec` and `MABDControlEvaluation`**

Implement frozen dataclasses:

```python
@dataclass(frozen=True)
class MABDActuationSpec:
    body_id: int
    target_q: Any | None = None
    target_qd: Any | None = None
    stiffness: Any = 0.0
    damping: Any = 0.0
    feedforward_force: Any | None = None


@dataclass(frozen=True)
class MABDControlEvaluation:
    body_id: int
    position_error: np.ndarray
    velocity_error: np.ndarray
    feedforward_force: np.ndarray
    generalized_force: np.ndarray
```

- [ ] **Step 2: Implement helper validation**

Add `_as_q12(value, name)`, `_as_optional_q12(value, name)`, and `_as_gain(value, name)`:

- q-like arrays must have shape `(12,)`.
- gain accepts nonnegative scalar or nonnegative shape `(12,)`.
- negative gain raises `ValueError(f"{name} must be nonnegative")`.

- [ ] **Step 3: Implement evaluation and assembly**

```python
def evaluate_affine_pd_control(q: Any, qd: Any, spec: MABDActuationSpec) -> MABDControlEvaluation:
    q_arr = _as_q12(q, "q")
    qd_arr = _as_q12(qd, "qd")
    target_q = _as_optional_q12(spec.target_q, "target_q")
    target_qd = _as_optional_q12(spec.target_qd, "target_qd")
    position_error = np.zeros(12) if target_q is None else target_q - q_arr
    velocity_error = np.zeros(12) if target_qd is None else target_qd - qd_arr
    feedforward = np.zeros(12) if spec.feedforward_force is None else _as_q12(spec.feedforward_force, "feedforward_force")
    force = _as_gain(spec.stiffness, "stiffness") * position_error
    force = force + _as_gain(spec.damping, "damping") * velocity_error + feedforward
    return MABDControlEvaluation(
        body_id=int(spec.body_id),
        position_error=position_error,
        velocity_error=velocity_error,
        feedforward_force=feedforward,
        generalized_force=force,
    )
```

```python
def assemble_control_generalized_forces(
    q: Any,
    qd: Any,
    *,
    actuations: Any,
    base_external_forces: Any | None = None,
) -> tuple[np.ndarray, ...]:
    ...
```

Assembly starts from zeros or `base_external_forces`, validates body count from `q`, and sums each actuation into its target body.

- [ ] **Step 4: Export helpers**

Add imports and `__all__` entries in `vendor/newton/newton/_src/solvers/mabd/__init__.py`.

- [ ] **Step 5: Run GREEN for Task 1**

Run the RED commands again. Expected: both pass.

### Task 3: Wire Actuations Into Configured CPU Oracle And Control Attributes

**Files:**
- Modify: `vendor/newton/newton/_src/solvers/mabd/step_oracle.py`
- Modify: `vendor/newton/newton/_src/solvers/mabd/solver_mabd.py`
- Modify: `tests/test_mabd_phase4_solver_step.py`

- [ ] **Step 1: Add RED CPU oracle integration test**

Add to `tests/test_mabd_phase4_solver_step.py`:

```python
    def test_dense_cpu_step_adds_actuation_forces_to_external_forces(self) -> None:
        q = mabd.pack_q(np.eye(3), np.zeros(3))
        qd = np.zeros(12)
        dt = 0.1
        external = np.full(12, 0.25)
        actuation = mabd.MABDActuationSpec(
            body_id=0,
            target_q=q + np.full(12, 0.5),
            stiffness=2.0,
            feedforward_force=np.full(12, -0.1),
        )

        result = mabd.solve_cpu_oracle_step(
            q=[q],
            qd=[qd],
            dt=dt,
            config=mabd.MABDCPUOracleConfig(
                bodies=[_body()],
                external_forces=[external],
                actuations=[actuation],
            ),
        )

        expected_force = external + np.full(12, 0.9)
        self.assertTrue(np.allclose(result.q[0], q + dt * dt * expected_force, atol=1.0e-12))
```

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_mabd_phase4_solver_step.MABDPhase4SolverStepTests.test_dense_cpu_step_adds_actuation_forces_to_external_forces
```

Expected: fail because `MABDCPUOracleConfig` does not accept `actuations`.

- [ ] **Step 2: Add `actuations` to `MABDCPUOracleConfig`**

Add field:

```python
actuations: tuple[MABDActuationSpec, ...] | list[MABDActuationSpec] = field(default_factory=tuple)
```

Change external-force assembly so it calls `assemble_control_generalized_forces(q_blocks, qd_blocks, actuations=config.actuations, base_external_forces=external_forces)`.

- [ ] **Step 3: Register `mabd:control` custom storage**

In `SolverMABD` add:

```python
MABD_CONTROL_FREQUENCY = "mabd:control"
```

Register frequency `ModelBuilder.CustomFrequency(name="control", namespace="mabd")`.

Add model attributes:

- `control_body` int32 reference to `mabd:body`
- `control_enabled` int32
- `control_stiffness` float32
- `control_damping` float32
- `control_target_q0`, `control_target_q1`, `control_target_q2`, `control_target_t` vec3
- `control_target_qd0`, `control_target_qd1`, `control_target_qd2`, `control_target_td` vec3
- `control_feedforward_q0`, `control_feedforward_q1`, `control_feedforward_q2`, `control_feedforward_t` vec3

Keep `SolverMABD.step(..., control=...)` raising `NotImplementedError`; Phase 10 only registers storage and config-level CPU oracle actuation.

- [ ] **Step 4: Run GREEN for integration and custom attribute tests**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_mabd_control_forces tests.test_mabd_phase4_solver_step
```

Expected: pass.

### Task 4: Claims, Boundaries, Validator, Record

**Files:**
- Modify: `docs/reference/paper-claims.yaml`
- Modify: `docs/reference/claim-boundaries.md`
- Modify: `scripts/validate_docs.py`
- Modify: `tests/test_phase0_bootstrap.py`
- Create: `docs/records/2026-05-16-phase10-actuation-forces.md`

- [ ] **Step 1: Add bounded method claim**

Add:

```yaml
  - claim_id: method.actuation.affine_control_forces
    source_path: "/tmp/mabd-paper/source/sections/experiment.tex and docs/superpowers/specs/2026-05-16-mabd-newton-only-full-reproduction-design.md"
    source_line: "experiment.tex:51, experiment.tex:184, experiment.tex:224; spec Actuation section"
    expected_value: "scene-script affine target/damping/feedforward controls assemble to generalized forces"
    unit: "oracle"
    conflict_note: "CPU oracle force assembly only; not Newton Control object ingestion, robot IK, Franka scene, contact-rich grasping, timing, or baseline evidence"
    reproduction_status: passed
```

- [ ] **Step 2: Update claim boundaries**

Add Phase 10 current and verified text. Explicitly exclude Newton runtime `Control` object ingestion, robot IK/planning, Franka pick-place scene verification, contact-rich grasping, rendered output, timing, and comparative baselines.

- [ ] **Step 3: Add validator/bootstrap checks**

In `scripts/validate_docs.py`, require:

- Phase 10 record path.
- Phase 10 claim ID with status `passed`.
- Phase 10 claim cited in records.
- Phase 10 boundary non-claim snippets.
- Phase 10 record fields: status, config path/no scene config, repo commits, vendored Newton upstream/local patch status, paper checksums, environment/backend, seed, metrics/thresholds, artifacts.
- Output string becomes `Phase 0/1/2/3/4/5/6/7/8/9/10 docs/provenance validation passed`.

In `tests/test_phase0_bootstrap.py`, add `test_phase10_actuation_force_claim_is_bounded` and update the validator-output expectation.

- [ ] **Step 4: Create Phase 10 record**

Create `docs/records/2026-05-16-phase10-actuation-forces.md` with:

- `## Status` set to `passed`
- base commit `042d451`
- plan commit placeholder until committed
- implementation commit placeholder until committed
- paper version and checksums
- exact RED/GREEN command outputs
- final verification command list
- claim impact and explicit non-claims

- [ ] **Step 5: Run docs/bootstrap checks**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_phase0_bootstrap
```

Expected: pass after docs are complete.

### Task 5: Final Verification, Review, Merge

**Files:**
- No new files beyond prior tasks.

- [ ] **Step 1: Run final verification**

```bash
/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check tests/test_mabd_control_forces.py tests/test_mabd_phase4_solver_step.py tests/test_phase0_bootstrap.py vendor/newton/newton/_src/solvers/mabd vendor/newton/newton/tests/test_mabd_control_forces.py scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_mabd_control_forces tests.test_mabd_phase4_solver_step tests.test_phase0_bootstrap
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest vendor.newton.newton.tests.test_mabd_control_forces
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
git diff --check
```

- [ ] **Step 2: Commit implementation and backfill record**

Commit implementation:

```bash
git add docs/records/2026-05-16-phase10-actuation-forces.md docs/reference/claim-boundaries.md docs/reference/paper-claims.yaml docs/superpowers/plans/2026-05-16-mabd-phase10-actuation-forces.md scripts/validate_docs.py tests/test_mabd_control_forces.py tests/test_mabd_phase4_solver_step.py tests/test_phase0_bootstrap.py vendor/newton/newton/_src/solvers/mabd vendor/newton/newton/tests/test_mabd_control_forces.py
git commit -m "feat: add Phase 10 actuation force oracle"
```

Backfill implementation commit in the record and commit:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
git add docs/records/2026-05-16-phase10-actuation-forces.md
git commit -m "docs: record Phase 10 implementation commit"
```

- [ ] **Step 3: Request multi-angle review**

Ask independent reviewers to check:

- affine PD/feedforward formula and sign convention
- aggregation with existing `external_forces`
- `mabd:control` storage names and no accidental runtime `Control` claim
- Phase 10 claim/provenance boundaries

- [ ] **Step 4: Merge and push after review fixes**

After review issues are resolved and final verification passes on the feature branch:

```bash
cd /cpfs/user/zhuzihou/dev/mabd-newton
git merge --ff-only phase10-actuation-forces
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
GIT_TERMINAL_PROMPT=0 timeout 120s git push git@github.com:jandan138/mabd-newton.git main
GIT_TERMINAL_PROMPT=0 timeout 60s git fetch git@github.com:jandan138/mabd-newton.git main:refs/remotes/origin/main
git worktree remove /cpfs/user/zhuzihou/dev/mabd-newton/.worktrees/phase10-actuation-forces
git branch -d phase10-actuation-forces
```

---

### Plan Self-Review

- Spec coverage: covers the spec requirement that `mabd:control` exists and that scene scripts can map targets/drives into affine generalized forces.
- Scope boundary: does not claim Newton `Control` runtime ingestion, IK, robot planning, Franka scene, contact-rich grasping, paper timing, or baselines.
- TDD path: each implementation task starts with RED tests and records expected failures.
- Type consistency: `MABDActuationSpec`, `MABDControlEvaluation`, `evaluate_affine_pd_control`, and `assemble_control_generalized_forces` are used consistently across tests, implementation, exports, and docs.
