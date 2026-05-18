# Phase 64 Spinning-Box Decoupled Twist Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a bounded decoupled spatial-twist diagnostic for the spinning-box paper horizon while preserving all non-pass claim boundaries.

**Architecture:** Add focused rigid exponential helpers in `spinning_box_physics.py`, then add a separate report/runner/CLI lane that uses those helpers for paper-horizon diagnostics. The lane records whether configured stretch thresholds are absent under a decoupled twist reconstruction, but remains explicitly incomplete and non-paper-faithful.

**Tech Stack:** Python 3.10, NumPy, vendored Newton `newton.solvers.mabd`, `unittest`, repo config/report/runner helpers, `scripts/validate_docs.py`.

**Claim Impact:** No `experiment.*` claim is passed.

---

## File Structure

- Modify `src/mabd_reproduction/spinning_box_physics.py` for SO(3) exponential and decoupled twist diagnostic state helpers.
- Modify `tests/test_rigid_baselines.py` for helper tests.
- Modify `src/mabd_reproduction/experiment_configs.py` and `configs/experiments/single_body_spinning_box.yaml` for `decoupled_twist_output_report`.
- Modify `src/mabd_reproduction/single_body_reports.py` for the decoupled twist report writer.
- Modify `src/mabd_reproduction/experiment_runner.py` and `scripts/run_experiment.py` for the new lane.
- Modify `tests/test_experiment_run_configs.py`, `tests/test_single_body_report_lane.py`, and `tests/test_experiment_runner.py` for config/report/runner/CLI coverage.
- Create `reports/experiment_matrix/single_body_spinning_box_decoupled_twist.json`.
- Modify `docs/reference/claim-boundaries.md`, `scripts/validate_docs.py`, and `tests/test_phase0_bootstrap.py` for Phase 64 provenance gates.
- Create `docs/records/2026-05-19-phase64-spinning-box-decoupled-twist.md`.

## Task 1: Rigid Exponential Helpers

- [ ] **Step 1: Write failing helper tests**

Add tests to `tests/test_rigid_baselines.py`:

```python
def test_spinning_box_so3_exponential_preserves_rotation_shape(self) -> None:
    from mabd_reproduction.spinning_box_physics import (
        spinning_box_so3_exp_from_angular_velocity,
    )

    rotation = spinning_box_so3_exp_from_angular_velocity(np.array([0.0, 60000.0, 0.0]), 0.01)

    np.testing.assert_allclose(rotation.T @ rotation, np.eye(3), atol=1.0e-12)
    self.assertAlmostEqual(float(np.linalg.det(rotation)), 1.0, places=12)
    self.assertTrue(np.all(np.isfinite(rotation)))


def test_spinning_box_decoupled_twist_state_preserves_paper_momentum(self) -> None:
    from mabd_reproduction.experiment_configs import load_spinning_box_config
    from mabd_reproduction.spinning_box_physics import (
        spinning_box_affine_shape_diagnostics,
        mabd_momentum_diagnostics,
        spinning_box_decoupled_twist_state,
        spinning_box_physical_properties,
    )

    config = load_spinning_box_config(CONFIG_PATH)
    q, qd = spinning_box_decoupled_twist_state(config, 0.01, 3)
    diagnostics = mabd_momentum_diagnostics(config, q, qd)
    shape = spinning_box_affine_shape_diagnostics(q)
    properties = spinning_box_physical_properties(config)

    np.testing.assert_allclose(
        diagnostics.linear_momentum_kg_m_s,
        properties.linear_momentum_kg_m_s,
        atol=1.0e-10,
    )
    np.testing.assert_allclose(
        diagnostics.angular_momentum_kg_m2_s,
        properties.angular_momentum_kg_m2_s,
        atol=1.0e-10,
    )
    self.assertAlmostEqual(shape.determinant, 1.0, places=12)
    np.testing.assert_allclose(shape.singular_values, np.ones(3), atol=1.0e-12)
    self.assertLess(shape.orthogonality_error, 1.0e-12)
    self.assertTrue(np.all(np.isfinite(q)))
    self.assertTrue(np.all(np.isfinite(qd)))


def test_spinning_box_decoupled_twist_state_respects_initial_orientation(self) -> None:
    from dataclasses import replace

    from mabd_reproduction.experiment_configs import load_spinning_box_config
    from mabd_reproduction.spinning_box_physics import (
        spinning_box_decoupled_twist_state,
        spinning_box_so3_exp_from_angular_velocity,
        spinning_box_physical_properties,
    )
    from newton.solvers import mabd

    config = load_spinning_box_config(CONFIG_PATH)
    initial_rotation = spinning_box_so3_exp_from_angular_velocity(np.array([1.0, 2.0, 3.0]), 0.125)
    _A0, t0 = mabd.unpack_q(config.initial_q)
    config = replace(config, initial_q=mabd.pack_q(initial_rotation, t0))
    q, _qd = spinning_box_decoupled_twist_state(config, 0.01, 2)
    A, _t = mabd.unpack_q(q)
    paper = spinning_box_physical_properties(config)
    expected = np.linalg.matrix_power(
        spinning_box_so3_exp_from_angular_velocity(paper.angular_velocity_rad_s, 0.01),
        2,
    ) @ initial_rotation

    np.testing.assert_allclose(A, expected, atol=1.0e-12)
```

- [ ] **Step 2: Verify RED**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_rigid_baselines
```

Expected: fail because the new helper functions do not exist.

- [ ] **Step 3: Implement helpers**

Add to `src/mabd_reproduction/spinning_box_physics.py`:

```python
def _skew(vector: np.ndarray) -> np.ndarray:
    x, y, z = np.asarray(vector, dtype=float)
    return np.array([[0.0, -z, y], [z, 0.0, -x], [-y, x, 0.0]], dtype=float)


def spinning_box_so3_exp_from_angular_velocity(angular_velocity: np.ndarray, time_step_s: float) -> np.ndarray:
    omega = _paper_vector(angular_velocity, "angular_velocity")
    dt = _paper_float(time_step_s, "time_step_s", positive=True)
    speed = float(np.linalg.norm(omega))
    if speed == 0.0:
        return np.eye(3)
    theta = speed * dt
    axis = omega / speed
    axis_cross = _skew(axis)
    return np.eye(3) + np.sin(theta) * axis_cross + (1.0 - np.cos(theta)) * (axis_cross @ axis_cross)


def spinning_box_decoupled_twist_state(
    config: SpinningBoxRunConfig,
    time_step_s: float,
    step_index: int,
) -> tuple[np.ndarray, np.ndarray]:
    if step_index < 0:
        raise ValueError("step_index must be nonnegative")
    properties = spinning_box_physical_properties(config)
    rotation_step = spinning_box_so3_exp_from_angular_velocity(
        properties.angular_velocity_rad_s,
        time_step_s,
    )
    A0, t0 = mabd.unpack_q(config.initial_q)
    A = np.linalg.matrix_power(rotation_step, int(step_index)) @ A0
    t = t0 + properties.linear_velocity_m_s * float(time_step_s) * int(step_index)
    q = mabd.pack_q(A, t)
    qd = abd_generalized_velocity_from_paper_momenta(config, A=A)
    return q, qd
```

Export `spinning_box_so3_exp_from_angular_velocity` and
`spinning_box_decoupled_twist_state` in `__all__`.

- [ ] **Step 4: Verify GREEN**

Run the same helper test command. Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add src/mabd_reproduction/spinning_box_physics.py tests/test_rigid_baselines.py
git commit -m "feat: add spinning-box decoupled twist helpers"
```

## Task 2: Decoupled Twist Report Lane

- [ ] **Step 1: Write failing config/report/runner tests**

Add assertions that `config.paper_horizon.decoupled_twist_output_report` equals
`reports/experiment_matrix/single_body_spinning_box_decoupled_twist.json`.

Add `test_spinning_box_decoupled_twist_report_records_velocity_semantics_diagnostic`
to `tests/test_single_body_report_lane.py`. It must assert:

```python
self.assertEqual(loaded.status, EvidenceStatus.INCOMPLETE)
self.assertEqual(loaded.solver_mode, "decoupled_twist_rigid_reconstruction_diagnostic")
self.assertNotIn("lane_gate_status", loaded.observed)
self.assertEqual(
    loaded.observed["velocity_semantics_policy"],
    "decoupled_spatial_twist_with_exponential_rigid_update",
)
self.assertEqual(
    loaded.observed["velocity_semantics_scope"],
    "diagnostic_only_no_lane_gate",
)
self.assertEqual(
    loaded.observed["blocking_reasons"],
    [
        "mabd_newton_report_incomplete",
        "spinning_box_decoupled_twist_not_paper_faithful",
        "spinning_box_comparison_pass_gate_not_enabled",
        "mabd_kinematic_feasibility_blocker_recorded",
    ],
)
self.assertEqual(
    loaded.observed["solver_step_policy"],
    "no_solver_step_rigid_reconstruction_diagnostic",
)
self.assertEqual(
    loaded.observed["solver_residual_status"],
    "not_evaluated_no_kkt_solve",
)
self.assertGreater(loaded.observed["max_velocity_state_inconsistency_norm"], 0.0)
self.assertGreater(loaded.observed["max_finite_difference_twist_error"], 0.0)
self.assertTrue(loaded.observed["shape_thresholds_met_by_decoupled_twist"])
self.assertTrue(loaded.observed["energy_thresholds_met_by_decoupled_twist"])
self.assertEqual(loaded.observed["threshold_violations"], [])
self.assertEqual(len(loaded.observed["decoupled_twist_results"]), 2)
```

For each result, assert finite extrema, zero threshold violations, no
penetration, determinant and singular-value extrema within the configured
thresholds, explicit no-KKT residual status, positive finite-difference
inconsistency fields, and retained Phase 29 feasibility status.

Add runner and CLI tests mirroring the `spinning_box_normal_constraint` lane,
using `spinning_box_decoupled_twist`.

- [ ] **Step 2: Verify RED**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_run_configs tests.test_single_body_report_lane tests.test_experiment_runner
```

Expected: fail because the config field, writer, runner, and CLI lane do not exist.

- [ ] **Step 3: Implement config, writer, runner, and CLI**

Add `decoupled_twist_output_report` to `SpinningBoxPaperHorizonConfig`, YAML
parsing, and config YAML.

Add constants and a writer in `single_body_reports.py`:

```python
DECOUPLED_TWIST_POLICY = "decoupled_spatial_twist_with_exponential_rigid_update"
DECOUPLED_TWIST_SCOPE = "diagnostic_only_no_lane_gate"
```

Add `_run_spinning_box_decoupled_twist_step_size(...)`. For each configured
step size it computes `step_count = round(duration_s / time_step_s)`, validates
divisibility, loops `step_index = 0..step_count`, calls
`spinning_box_decoupled_twist_state(config, time_step_s, step_index)`, reuses
`_paper_horizon_sample_indices`, computes the same state metrics as
`_paper_horizon_state_metrics` except solver residual is not evaluated, and
aggregates the same threshold keys after excluding `max_residual_norm` from this
no-solver diagnostic. Record `solver_residual_status =
"not_evaluated_no_kkt_solve"` and `solver_step_policy =
"no_solver_step_rigid_reconstruction_diagnostic"` in every result.

Compute explicit finite-difference inconsistency metrics from consecutive
states:

```text
velocity_state_inconsistency = qd_diag,n - (q_n - q_{n-1}) / h
finite_difference_twist_error = ||G(A_n) ((q_n - q_{n-1}) / h) - V_paper||
```

Record top-level maxima and threshold violations. The report must remain
`EvidenceStatus.INCOMPLETE`.

Add `run_spinning_box_decoupled_twist` to `experiment_runner.py`, import it in
`scripts/run_experiment.py`, add it to argparse choices, and dispatch it in
`main`.

- [ ] **Step 4: Verify GREEN**

Run the same config/report/runner command. Expected: pass.

- [ ] **Step 5: Generate committed report**

Commit the Task 2 code/config/tests before generating the committed report:

```bash
git add configs/experiments/single_body_spinning_box.yaml src/mabd_reproduction/experiment_configs.py src/mabd_reproduction/single_body_reports.py src/mabd_reproduction/experiment_runner.py scripts/run_experiment.py tests/test_experiment_run_configs.py tests/test_single_body_report_lane.py tests/test_experiment_runner.py
git commit -m "feat: add spinning-box decoupled twist diagnostic"
```

Then use that implementation commit SHA as `source_commit`:

```bash
SOURCE_COMMIT=$(git rev-parse HEAD)
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/run_experiment.py --lane spinning_box_decoupled_twist --config configs/experiments/single_body_spinning_box.yaml --matrix configs/experiments/paper_experiment_matrix.yaml --output reports/experiment_matrix/single_body_spinning_box_decoupled_twist.json --source-commit "$SOURCE_COMMIT" --vendored-newton-commit 96713fa965463b69c229a4d30582c733ff3526bb
```

- [ ] **Step 6: Commit**

```bash
git add reports/experiment_matrix/single_body_spinning_box_decoupled_twist.json
git commit -m "docs: add spinning-box decoupled twist report artifact"
```

## Task 3: Provenance, Validator, And Final Gates

- [ ] **Step 1: Write failing docs/provenance tests**

Update `tests/test_phase0_bootstrap.py` to require Phase 64 claim-boundary
bullets, the Phase 64 record, validator checks for the committed decoupled
twist report, and unchanged `paper-claims.yaml` experiment statuses.

- [ ] **Step 2: Verify RED**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_phase0_bootstrap
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
```

Expected: fail because Phase 64 record, claim-boundary bullets, and validator
checks do not exist.

- [ ] **Step 3: Implement validator and docs**

Add Phase 64 required docs lists, report handling, `validate_phase64_record`,
claim-boundary bullets, and
`docs/records/2026-05-19-phase64-spinning-box-decoupled-twist.md` with report
sha256 and exact verification commands.

- [ ] **Step 4: Verify docs GREEN**

Run the same docs/provenance tests. Expected: pass.

- [ ] **Step 5: Run final verification**

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/env/readiness_check.py
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"
git diff --check
```

- [ ] **Step 6: Commit docs/provenance**

```bash
git add docs/reference/claim-boundaries.md scripts/validate_docs.py tests/test_phase0_bootstrap.py docs/records/2026-05-19-phase64-spinning-box-decoupled-twist.md docs/superpowers/specs/2026-05-19-phase64-spinning-box-decoupled-twist-design.md docs/superpowers/plans/2026-05-19-mabd-phase64-spinning-box-decoupled-twist.md
git commit -m "docs: record Phase64 decoupled twist diagnostics"
```

## Self-Review

- Spec coverage: covers helper math, report lane, config/runner/CLI, tests, validator, records, and claim boundaries.
- Source commit scan: no temporary source commit may remain in committed reports or records.
- Type consistency: use `spinning_box_decoupled_twist_state`, `spinning_box_so3_exp_from_angular_velocity`, `decoupled_twist_output_report`, `write_spinning_box_decoupled_twist_report`, `run_spinning_box_decoupled_twist`, and CLI lane `spinning_box_decoupled_twist` consistently.
