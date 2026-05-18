# Phase56 T-Handle MABD Newton Lane Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> superpowers:subagent-driven-development or superpowers:executing-plans to
> implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for
> tracking.

**Goal:** Add an auditable Newton `mabd_newton` diagnostic report for the
T-handle experiment without passing or overclaiming the paper experiment.

**Architecture:** Extend the existing T-handle RK4 config/report pipeline with
a separate MABD lane. The MABD rollout uses vendored Newton `SolverMABD.step()`
from model-derived `mabd:body` custom values and records incomplete diagnostic
evidence under the paper experiment matrix.

**Tech Stack:** Python 3.10, NumPy, vendored Newton `SolverMABD`, JSON
`ClaimReport`, YAML config, `unittest`, existing docs validator.

---

### Task 1: RED Tests For T-Handle MABD Config

**Files:**
- Modify: `tests/test_experiment_run_configs.py`

- [ ] **Step 1: Add config expectations**

Extend `test_t_handle_config_is_machine_checkable` to assert:

```python
self.assertEqual(
    config.mabd_newton.output_report,
    "reports/experiment_matrix/single_body_t_handle_mabd_newton.json",
)
self.assertEqual(config.mabd_newton.time_step_s, 0.001)
self.assertEqual(config.mabd_newton.step_count, 4000)
self.assertEqual(config.mabd_newton.sample_count, config.reference.sample_count)
self.assertEqual(config.mabd_newton.rotation_mode, "polar")
self.assertEqual(config.mabd_newton.rest_points_m.shape, (4, 3))
self.assertEqual(config.mabd_newton.point_masses_kg.shape, (4,))
self.assertAlmostEqual(
    config.mabd_newton.step_count * config.mabd_newton.time_step_s,
    config.reference.duration_s,
)
np.testing.assert_allclose(
    config.mabd_newton.initial_angular_velocity_rad_s,
    config.reference.initial_angular_velocity_rad_s,
)
np.testing.assert_allclose(config.mabd_newton.gravity_m_s2, [0.0, 0.0, 0.0])
```

Also assert the matrix blocker is `mabd_newton_report_incomplete`, not
`mabd_newton_report_missing`.

- [ ] **Step 2: Add rejection tests**

Add tests that mutate the YAML and expect `ExperimentRunConfigError` when:

```python
source["mabd_newton"]["sample_count"] = 8
source["mabd_newton"]["gravity_m_s2"] = [0.0, -9.81, 0.0]
source["mabd_newton"]["output_report"] = source["reference"]["output_report"]
source["mabd_newton"]["point_masses_kg"][0] = 0.0
```

- [ ] **Step 3: Verify RED**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_run_configs
```

Expected: fail because `THandleRunConfig.mabd_newton` does not exist.

### Task 2: GREEN Config Parser And Matrix Contract

**Files:**
- Modify: `configs/experiments/single_body_t_handle.yaml`
- Modify: `configs/experiments/paper_experiment_matrix.yaml`
- Modify: `src/mabd_reproduction/experiment_configs.py`

- [ ] **Step 1: Add dataclass**

Create:

```python
@dataclass(frozen=True)
class THandleMABDNewtonConfig:
    time_step_s: float
    step_count: int
    sample_count: int
    rest_points_m: np.ndarray
    point_masses_kg: np.ndarray
    volume_m3: float
    rotation_mode: str
    initial_angular_velocity_rad_s: np.ndarray
    gravity_m_s2: np.ndarray
    output_report: str
    thresholds: dict[str, float]
```

Add it to `THandleRunConfig` and `__all__`.

- [ ] **Step 2: Add YAML section**

Add `mabd_newton` to the T-handle YAML with a non-degenerate four-point proxy,
positive point masses, zero gravity, and output report
`reports/experiment_matrix/single_body_t_handle_mabd_newton.json`.

- [ ] **Step 3: Parse and validate**

Add `_require_t_handle_mabd_newton(data)` that validates:

```python
time_step_s > 0
step_count > 0
sample_count >= 2
rest_points_m has shape (4, 3)
point_masses_kg has shape (4,) and all positive
volume_m3 > 0
rotation_mode == "polar"
gravity_m_s2 == [0, 0, 0]
thresholds contain max_relative_energy_drift, max_angular_momentum_norm_drift,
max_affine_shape_spread_m, max_proxy_inertia_relative_error
```

Validate alignment to the RK4 reference and distinct lane output in
`validate_t_handle_config_against_matrix`.

- [ ] **Step 4: Run GREEN tests**

Run the targeted config tests from Task 1 and confirm they pass.

### Task 3: RED Tests For T-Handle MABD Rollout And Report

**Files:**
- Modify: `tests/test_t_handle_reference.py`
- Modify: `tests/test_experiment_runner.py`

- [ ] **Step 1: Add rollout test**

Import `roll_out_t_handle_mabd_model_derived` and assert:

```python
rollout = roll_out_t_handle_mabd_model_derived(config)
self.assertEqual(rollout.step_count, config.mabd_newton.step_count)
self.assertEqual(rollout.sample_count, config.mabd_newton.sample_count)
self.assertAlmostEqual(rollout.samples[0].time_s, 0.0)
self.assertAlmostEqual(rollout.samples[-1].time_s, config.reference.duration_s)
self.assertTrue(rollout.finite)
self.assertEqual(rollout.solver_model_config_source, "newton_model_derived")
self.assertEqual(
    rollout.newton_model_derived_custom_frequencies,
    ("mabd:body", "mabd:gravity"),
)
```

- [ ] **Step 2: Add report/runner test**

Add `test_run_t_handle_mabd_newton_writes_incomplete_newton_diagnostic_report`
in `tests/test_experiment_runner.py` asserting:

```python
self.assertEqual(loaded.solver_mode, "mabd_cpu_oracle_t_handle_newton_lane")
self.assertEqual(loaded.backend, "cpu_numpy_newton_only")
self.assertEqual(loaded.baseline_lane, "mabd_newton")
self.assertEqual(loaded.observed["solver_model_config_source"], "newton_model_derived")
self.assertFalse(loaded.observed["full_experiment_claim_passed"])
self.assertIn("exact_t_handle_geometry_unknown", loaded.observed["blocking_reasons"])
self.assertIn("raw_t_handle_reference_curve_data_missing", loaded.observed["blocking_reasons"])
self.assertIn("mabd_newton_report_incomplete", loaded.observed["blocking_reasons"])
self.assertNotIn("mabd_newton_report_missing", loaded.observed["blocking_reasons"])
self.assertNotIn("lane_gate_status", loaded.observed)
```

- [ ] **Step 3: Add CLI test**

Add a `scripts/run_experiment.py --lane t_handle_mabd_newton` test mirroring
the existing RK4 CLI test.

- [ ] **Step 4: Verify RED**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_t_handle_reference tests.test_experiment_runner
```

Expected: fail because the rollout, report writer, runner, and CLI lane do not
exist.

### Task 4: GREEN Rollout, Report Writer, Runner, And CLI

**Files:**
- Create: `src/mabd_reproduction/t_handle_mabd.py`
- Modify: `src/mabd_reproduction/t_handle_reports.py`
- Modify: `src/mabd_reproduction/experiment_runner.py`
- Modify: `scripts/run_experiment.py`

- [ ] **Step 1: Implement rollout**

Create `t_handle_mabd.py` with:

- `_t_handle_solver_model(config)` using `ModelBuilder`,
  `SolverMABD.register_custom_attributes`, one `mabd:body` row, and one
  disabled `mabd:gravity` row;
- `_initial_state(config)` using `mabd.pack_q(np.eye(3), np.zeros(3))` and
  `skew(initial_angular_velocity) @ np.eye(3)`;
- `_read_solver_state` and `_assign_solver_state` matching existing
  MABD helpers;
- `roll_out_t_handle_mabd_model_derived(config)`.

- [ ] **Step 2: Implement report writer**

Add `write_t_handle_mabd_newton_report` that records:

- status `EvidenceStatus.INCOMPLETE`;
- solver mode `mabd_cpu_oracle_t_handle_newton_lane`;
- backend `cpu_numpy_newton_only`;
- baseline lane `mabd_newton`;
- finite rollout metrics;
- proxy inertia and reference inertia;
- threshold violations;
- blockers with `mabd_newton_report_incomplete`.

- [ ] **Step 3: Implement runner and CLI**

Add `run_t_handle_mabd_newton` to `experiment_runner.py` and lane
`t_handle_mabd_newton` to `scripts/run_experiment.py`.

- [ ] **Step 4: Run GREEN tests**

Run the targeted tests from Task 3 and confirm they pass.

### Task 5: Docs, Validator, Evidence, And Final Gates

**Files:**
- Modify: `scripts/validate_docs.py`
- Modify: `tests/test_phase0_bootstrap.py`
- Modify: `docs/reference/claim-boundaries.md`
- Add: `docs/records/2026-05-18-phase56-t-handle-mabd-newton.md`
- Add: `reports/experiment_matrix/single_body_t_handle_mabd_newton.json`

- [ ] **Step 1: Add Phase56 validation**

Add validator checks that load the generated MABD report, recompute the rollout,
check report hash in the Phase56 record, require incomplete status, and reject
overclaims.

- [ ] **Step 2: Regenerate report**

After committing implementation code, run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/run_experiment.py --lane t_handle_mabd_newton --config configs/experiments/single_body_t_handle.yaml --matrix configs/experiments/paper_experiment_matrix.yaml --source-commit "$(git rev-parse HEAD)" --vendored-newton-commit 96713fa965463b69c229a4d30582c733ff3526bb
```

- [ ] **Step 3: Run full verification**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"
/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .
git diff --check
```
