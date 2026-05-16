# Phase 11 Control Row Extraction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert Newton `mabd:control` model rows into `MABDActuationSpec` objects so scene builders can store affine controls in Newton custom attributes and route them into the configured CPU oracle.

**Architecture:** Extend `control_forces.py` with model-row extraction helpers that read `model.mabd.control_*` arrays, validate enabled rows and body references, and produce immutable `MABDActuationSpec` values. Keep `SolverMABD.step(..., control=...)` unsupported; Phase 11 only bridges solver-owned model storage to existing Phase 10 CPU-oracle actuation specs.

**Tech Stack:** Python 3.10, NumPy, vendored Newton custom attributes, `unittest`, ruff, docs/provenance validator.

---

### File Structure

- Modify `vendor/newton/newton/_src/solvers/mabd/control_forces.py`.
  Add `actuation_specs_from_model(model, *, enabled_only=True)` plus small row-packing helpers.
- Modify `vendor/newton/newton/_src/solvers/mabd/__init__.py`.
  Export the model-row extraction helper.
- Modify `tests/test_mabd_control_forces.py`.
  Add public tests that build a Newton model with `mabd:control` rows and verify extraction, skipping disabled rows, validation, and CPU oracle use.
- Modify `vendor/newton/newton/tests/test_mabd_control_forces.py`.
  Add a vendored internal extraction smoke test against Newton `ModelBuilder`.
- Modify `docs/reference/claim-boundaries.md`.
  Add bounded Phase 11 evidence and non-claims.
- Modify `scripts/validate_docs.py` and `tests/test_phase0_bootstrap.py`.
  Require the Phase 11 record and boundary snippets.
- Create `docs/records/2026-05-17-phase11-control-row-extraction.md`.
  Record commands, environment, paper source checksums, verification evidence, and claim impact.

### Task 1: RED Tests For Model Control Extraction

**Files:**
- Modify: `tests/test_mabd_control_forces.py`
- Modify: `vendor/newton/newton/tests/test_mabd_control_forces.py`

- [ ] **Step 1: Add a public model builder helper**

Add this helper near the existing public control-force tests:

```python
def _add_mabd_body(builder: newton.ModelBuilder) -> int:
    body_id = builder.add_body()
    builder.add_custom_values(
        **{
            "mabd:body_index": body_id,
            "mabd:young_modulus": 1.0,
            "mabd:poisson_ratio": 0.25,
            "mabd:density": 1.0,
            "mabd:polar_mode": 0,
        }
    )
    return body_id
```

- [ ] **Step 2: Add a public RED test for enabled row extraction**

Add this test:

```python
def test_actuation_specs_from_model_reads_enabled_control_rows(self) -> None:
    builder = newton.ModelBuilder()
    SolverMABD.register_custom_attributes(builder)
    _add_mabd_body(builder)
    target_t = wp.vec3(0.25, -0.5, 0.75)
    target_td = wp.vec3(0.1, 0.2, 0.3)
    feedforward_t = wp.vec3(1.0, 2.0, 3.0)
    builder.add_custom_values(
        **{
            "mabd:control_body": 0,
            "mabd:control_enabled": 1,
            "mabd:control_stiffness": 2.5,
            "mabd:control_damping": 0.75,
            "mabd:control_target_q0": wp.vec3(1.0, 0.0, 0.0),
            "mabd:control_target_q1": wp.vec3(0.0, 1.0, 0.0),
            "mabd:control_target_q2": wp.vec3(0.0, 0.0, 1.0),
            "mabd:control_target_t": target_t,
            "mabd:control_target_qd0": wp.vec3(0.0, 0.0, 0.0),
            "mabd:control_target_qd1": wp.vec3(0.0, 0.0, 0.0),
            "mabd:control_target_qd2": wp.vec3(0.0, 0.0, 0.0),
            "mabd:control_target_td": target_td,
            "mabd:control_feedforward_q0": wp.vec3(0.0, 0.0, 0.0),
            "mabd:control_feedforward_q1": wp.vec3(0.0, 0.0, 0.0),
            "mabd:control_feedforward_q2": wp.vec3(0.0, 0.0, 0.0),
            "mabd:control_feedforward_t": feedforward_t,
        }
    )

    specs = mabd.actuation_specs_from_model(builder.finalize())

    self.assertEqual(len(specs), 1)
    self.assertEqual(specs[0].body_id, 0)
    self.assertAlmostEqual(float(specs[0].stiffness), 2.5)
    self.assertAlmostEqual(float(specs[0].damping), 0.75)
    self.assertTrue(np.allclose(specs[0].target_q[9:12], [0.25, -0.5, 0.75]))
    self.assertTrue(np.allclose(specs[0].target_qd[9:12], [0.1, 0.2, 0.3]))
    self.assertTrue(np.allclose(specs[0].feedforward_force[9:12], [1.0, 2.0, 3.0]))
```

Expected RED failure: `AttributeError: module 'newton._src.solvers.mabd' has no attribute 'actuation_specs_from_model'`.

- [ ] **Step 3: Add public tests for disabled rows and CPU oracle use**

Add these tests:

```python
def test_actuation_specs_from_model_filters_disabled_rows_by_default(self) -> None:
    builder = newton.ModelBuilder()
    SolverMABD.register_custom_attributes(builder)
    _add_mabd_body(builder)
    for enabled, x_target in ((1, 0.5), (0, 9.0)):
        builder.add_custom_values(
            **{
                "mabd:control_body": 0,
                "mabd:control_enabled": enabled,
                "mabd:control_stiffness": 1.0,
                "mabd:control_damping": 0.0,
                "mabd:control_target_q0": wp.vec3(1.0, 0.0, 0.0),
                "mabd:control_target_q1": wp.vec3(0.0, 1.0, 0.0),
                "mabd:control_target_q2": wp.vec3(0.0, 0.0, 1.0),
                "mabd:control_target_t": wp.vec3(x_target, 0.0, 0.0),
                "mabd:control_target_qd0": wp.vec3(0.0, 0.0, 0.0),
                "mabd:control_target_qd1": wp.vec3(0.0, 0.0, 0.0),
                "mabd:control_target_qd2": wp.vec3(0.0, 0.0, 0.0),
                "mabd:control_target_td": wp.vec3(0.0, 0.0, 0.0),
                "mabd:control_feedforward_q0": wp.vec3(0.0, 0.0, 0.0),
                "mabd:control_feedforward_q1": wp.vec3(0.0, 0.0, 0.0),
                "mabd:control_feedforward_q2": wp.vec3(0.0, 0.0, 0.0),
                "mabd:control_feedforward_t": wp.vec3(0.0, 0.0, 0.0),
            }
        )
    model = builder.finalize()

    enabled_specs = mabd.actuation_specs_from_model(model)
    all_specs = mabd.actuation_specs_from_model(model, enabled_only=False)

    self.assertEqual(len(enabled_specs), 1)
    self.assertEqual(len(all_specs), 2)
    self.assertAlmostEqual(float(enabled_specs[0].target_q[9]), 0.5)
    self.assertAlmostEqual(float(all_specs[1].target_q[9]), 9.0)


def test_extracted_model_actuations_drive_cpu_oracle(self) -> None:
    builder = newton.ModelBuilder()
    SolverMABD.register_custom_attributes(builder)
    _add_mabd_body(builder)
    builder.add_custom_values(
        **{
            "mabd:control_body": 0,
            "mabd:control_enabled": 1,
            "mabd:control_stiffness": 2.0,
            "mabd:control_damping": 0.0,
            "mabd:control_target_q0": wp.vec3(1.0, 0.0, 0.0),
            "mabd:control_target_q1": wp.vec3(0.0, 1.0, 0.0),
            "mabd:control_target_q2": wp.vec3(0.0, 0.0, 1.0),
            "mabd:control_target_t": wp.vec3(0.5, 0.0, 0.0),
            "mabd:control_target_qd0": wp.vec3(0.0, 0.0, 0.0),
            "mabd:control_target_qd1": wp.vec3(0.0, 0.0, 0.0),
            "mabd:control_target_qd2": wp.vec3(0.0, 0.0, 0.0),
            "mabd:control_target_td": wp.vec3(0.0, 0.0, 0.0),
            "mabd:control_feedforward_q0": wp.vec3(0.0, 0.0, 0.0),
            "mabd:control_feedforward_q1": wp.vec3(0.0, 0.0, 0.0),
            "mabd:control_feedforward_q2": wp.vec3(0.0, 0.0, 0.0),
            "mabd:control_feedforward_t": wp.vec3(0.0, 0.25, 0.0),
        }
    )
    q = mabd.pack_q(np.eye(3), np.zeros(3))
    dt = 0.1

    result = mabd.solve_cpu_oracle_step(
        q=[q],
        qd=[np.zeros(12)],
        dt=dt,
        config=mabd.MABDCPUOracleConfig(
            bodies=[
                mabd.MABDCPUOracleBody(
                    precompute=mabd.SingleBodyABDPrecompute(
                        rest_points=np.zeros((4, 3), dtype=float),
                        masses=np.ones(4, dtype=float),
                        mass_matrix=np.eye(12),
                        stiffness_matrix=np.zeros((12, 12), dtype=float),
                    )
                )
            ],
            actuations=mabd.actuation_specs_from_model(builder.finalize()),
        ),
    )

    expected_force = np.zeros(12)
    expected_force[9] = 1.0
    expected_force[10] = 0.25
    self.assertTrue(np.allclose(result.q[0], q + dt * dt * expected_force, atol=1.0e-12))
```

- [ ] **Step 4: Add public validation tests**

Add a test that mutates a finalized model's `mabd.control_body` array to an invalid enabled body id and asserts:

```python
with self.assertRaisesRegex(ValueError, "control row 0 body"):
    mabd.actuation_specs_from_model(model)
```

- [ ] **Step 5: Add a vendored smoke test**

In `vendor/newton/newton/tests/test_mabd_control_forces.py`, import `newton`, `SolverMABD`, and `wp`, build one body plus one enabled control row, call `actuation_specs_from_model(model)`, and assert body id plus translation feedforward values.

- [ ] **Step 6: Run RED**

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_mabd_control_forces
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest vendor.newton.newton.tests.test_mabd_control_forces
```

Expected: both fail because `actuation_specs_from_model` is missing.

### Task 2: Implement Extraction Helper

**Files:**
- Modify: `vendor/newton/newton/_src/solvers/mabd/control_forces.py`
- Modify: `vendor/newton/newton/_src/solvers/mabd/__init__.py`

- [ ] **Step 1: Add row packing helpers**

In `control_forces.py`, add helpers:

```python
def _vec3_rows(value: Any, name: str, count: int) -> np.ndarray:
    rows = np.asarray(value.numpy(), dtype=float)
    if rows.shape != (count, 3):
        raise ValueError(f"{name} must have shape ({count}, 3), got {rows.shape}")
    return rows


def _pack_rows(q0: np.ndarray, q1: np.ndarray, q2: np.ndarray, t: np.ndarray) -> tuple[np.ndarray, ...]:
    return tuple(np.concatenate((q0[row], q1[row], q2[row], t[row])).astype(float, copy=True) for row in range(len(t)))
```

- [ ] **Step 2: Implement `actuation_specs_from_model`**

Add:

```python
def actuation_specs_from_model(model: Any, *, enabled_only: bool = True) -> tuple[MABDActuationSpec, ...]:
    row_count = int(model.get_custom_frequency_count("mabd:control"))
    body_count = int(model.get_custom_frequency_count("mabd:body"))
    if row_count == 0:
        return ()
    namespace = model.mabd
    control_body = np.asarray(namespace.control_body.numpy(), dtype=int)
    control_enabled = np.asarray(namespace.control_enabled.numpy(), dtype=int)
    stiffness = np.asarray(namespace.control_stiffness.numpy(), dtype=float)
    damping = np.asarray(namespace.control_damping.numpy(), dtype=float)
    target_q = _pack_rows(
        _vec3_rows(namespace.control_target_q0, "control_target_q0", row_count),
        _vec3_rows(namespace.control_target_q1, "control_target_q1", row_count),
        _vec3_rows(namespace.control_target_q2, "control_target_q2", row_count),
        _vec3_rows(namespace.control_target_t, "control_target_t", row_count),
    )
    target_qd = _pack_rows(
        _vec3_rows(namespace.control_target_qd0, "control_target_qd0", row_count),
        _vec3_rows(namespace.control_target_qd1, "control_target_qd1", row_count),
        _vec3_rows(namespace.control_target_qd2, "control_target_qd2", row_count),
        _vec3_rows(namespace.control_target_td, "control_target_td", row_count),
    )
    feedforward = _pack_rows(
        _vec3_rows(namespace.control_feedforward_q0, "control_feedforward_q0", row_count),
        _vec3_rows(namespace.control_feedforward_q1, "control_feedforward_q1", row_count),
        _vec3_rows(namespace.control_feedforward_q2, "control_feedforward_q2", row_count),
        _vec3_rows(namespace.control_feedforward_t, "control_feedforward_t", row_count),
    )
    specs = []
    for row in range(row_count):
        if enabled_only and int(control_enabled[row]) == 0:
            continue
        body_id = int(control_body[row])
        if not 0 <= body_id < body_count:
            raise ValueError(f"control row {row} body {body_id} is outside [0, {body_count})")
        specs.append(
            MABDActuationSpec(
                body_id=body_id,
                target_q=target_q[row],
                target_qd=target_qd[row],
                stiffness=float(stiffness[row]),
                damping=float(damping[row]),
                feedforward_force=feedforward[row],
            )
        )
    return tuple(specs)
```

Use the same `_pack_rows` call pattern for `target_qd` and `feedforward`.

- [ ] **Step 3: Export the helper**

Add `actuation_specs_from_model` to `vendor/newton/newton/_src/solvers/mabd/__init__.py` imports and `__all__`, keeping ruff sort order.

- [ ] **Step 4: Run GREEN**

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_mabd_control_forces
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest vendor.newton.newton.tests.test_mabd_control_forces
```

Expected: tests pass.

- [ ] **Step 5: Commit code**

```bash
git add tests/test_mabd_control_forces.py vendor/newton/newton/tests/test_mabd_control_forces.py vendor/newton/newton/_src/solvers/mabd/control_forces.py vendor/newton/newton/_src/solvers/mabd/__init__.py
git commit -m "feat: extract MABD controls from model rows"
```

### Task 3: Documentation, Validator, And Record

**Files:**
- Modify: `docs/reference/claim-boundaries.md`
- Modify: `scripts/validate_docs.py`
- Modify: `tests/test_phase0_bootstrap.py`
- Create: `docs/records/2026-05-17-phase11-control-row-extraction.md`

- [ ] **Step 1: Add Phase 11 boundaries**

Add to Current:

```markdown
- This repository contains Phase 11 `mabd:control` model-row extraction tests
  after the Phase 11 record is created.
```

Add to Verified:

```markdown
- Phase 11 verifies extraction of enabled Newton `mabd:control` model rows into
  `MABDActuationSpec` values, disabled-row filtering, bad body-reference
  validation, and use of extracted specs in the configured CPU oracle actuation
  path.
- Phase 11 does not verify Newton `Control` object ingestion, time-varying
  controller updates, robot inverse kinematics, Franka pick-and-place,
  contact-rich grasping, paper scenes, timing, or comparative baselines.
```

- [ ] **Step 2: Add validator requirements**

Update `scripts/validate_docs.py` to:

- include `docs/records/2026-05-17-phase11-control-row-extraction.md` in `REQUIRED_PATHS`;
- require the Phase 11 boundary and non-claim snippets;
- add `validate_phase11_record()` requiring status, plan commit, implementation commit, environment, paper checksums, `method.actuation.affine_control_forces`, and final verification snippets;
- include the Phase 11 record in passed-claim citation text;
- print `Phase 0/1/2/3/4/5/6/7/8/9/10/11 docs/provenance validation passed`.

- [ ] **Step 3: Add bootstrap tests**

Add tests in `tests/test_phase0_bootstrap.py` that check:

- claim boundaries contain Phase 11 evidence and non-claims;
- the Phase 11 record has required evidence fields;
- docs validator output includes `/11`.

- [ ] **Step 4: Create record**

Create `docs/records/2026-05-17-phase11-control-row-extraction.md` with the same structure as Phase 10. Required scope text:

```markdown
Phase 11 strengthens `method.actuation.affine_control_forces` by proving that
stored Newton `mabd:control` rows can be converted into CPU-oracle actuation
specs.

This phase does not verify Newton `Control` object ingestion, time-varying
controller updates, robot inverse kinematics, Franka pick-and-place,
contact-rich grasping, paper scenes, timing, or comparative baselines.
```

- [ ] **Step 5: Run docs GREEN**

```bash
/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_phase0_bootstrap
git diff --check
```

Expected: all pass.

- [ ] **Step 6: Commit docs**

```bash
git add docs/reference/claim-boundaries.md scripts/validate_docs.py tests/test_phase0_bootstrap.py docs/records/2026-05-17-phase11-control-row-extraction.md
git commit -m "docs: record Phase 11 control row extraction"
```

### Task 4: Final Verification And Merge

**Files:**
- No new files.

- [ ] **Step 1: Run final branch verification**

```bash
/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_mabd_control_forces tests.test_mabd_phase4_solver_step tests.test_phase0_bootstrap
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest vendor.newton.newton.tests.test_mabd_control_forces
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"
git diff --check
```

- [ ] **Step 2: Request review**

Request focused review for:

- extraction correctness and validation;
- claim-boundary preservation.

- [ ] **Step 3: Merge and push after review**

Fast-forward merge into `main`, rerun the same verification on merged `main`, push to `git@github.com:jandan138/mabd-newton.git main`, fetch back, and verify `origin/main` equals local `HEAD`.
