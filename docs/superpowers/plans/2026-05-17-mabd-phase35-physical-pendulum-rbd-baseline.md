# Phase 35 Physical Pendulum RBD Baseline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a bounded physical-pendulum `rbd_implicit_baseline` diagnostic report lane.

**Architecture:** Config parsing owns the new `rbd_baseline` block. A focused NumPy module performs the scalar implicit-Euler rigid-pendulum rollout. The report/runner/CLI layer writes an incomplete `ClaimReport`, while docs and validators preserve claim boundaries.

**Tech Stack:** Python 3.10, NumPy, PyYAML, SciPy analytic reference helpers, `unittest`, ruff.

---

### Task 1: Config Contract

**Files:**
- Modify: `configs/experiments/single_body_physical_pendulum.yaml`
- Modify: `src/mabd_reproduction/experiment_configs.py`
- Modify: `tests/test_experiment_run_configs.py`

- [ ] **Step 1: Write failing config tests**

Add assertions to `test_physical_pendulum_config_is_machine_checkable`:

```python
self.assertEqual(config.required_missing_lanes, ("mabd_newton",))
self.assertEqual(config.rbd_baseline.time_step_s, 0.01)
self.assertEqual(config.rbd_baseline.step_count, 16)
self.assertEqual(config.rbd_baseline.sample_count, 5)
self.assertEqual(config.rbd_baseline.length_m, 1.0)
self.assertEqual(config.rbd_baseline.mass_kg, 1.0)
np.testing.assert_allclose(config.rbd_baseline.gravity_m_s2, [0.0, -9.81, 0.0])
self.assertEqual(config.rbd_baseline.initial_angle_rad, 0.0)
self.assertEqual(config.rbd_baseline.initial_angular_velocity_rad_s, 0.0)
self.assertEqual(
    config.rbd_baseline.output_report,
    "reports/experiment_matrix/single_body_physical_pendulum_rbd_baseline.json",
)
self.assertIn("max_abs_angle_error_rad", config.rbd_baseline.thresholds)
self.assertIn("max_implicit_residual", config.rbd_baseline.thresholds)
self.assertIn("max_length_constraint_error_m", config.rbd_baseline.thresholds)
```

Add a malformed-config test:

```python
def test_physical_pendulum_config_rejects_bad_rbd_baseline_length(self) -> None:
    source = yaml.safe_load(PHYSICAL_PENDULUM_CONFIG_PATH.read_text(encoding="utf-8"))
    source["rbd_baseline"]["length_m"] = 0.0
    with TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "single_body_physical_pendulum.yaml"
        path.write_text(yaml.safe_dump(source), encoding="utf-8")
        with self.assertRaisesRegex(ExperimentRunConfigError, "length_m"):
            load_physical_pendulum_config(path)
```

- [ ] **Step 2: Run RED**

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_run_configs
```

Expected: missing `rbd_baseline` attribute or parser error.

- [ ] **Step 3: Implement config support**

Add `PhysicalPendulumRBDBaselineConfig`:

```python
@dataclass(frozen=True)
class PhysicalPendulumRBDBaselineConfig:
    time_step_s: float
    step_count: int
    sample_count: int
    length_m: float
    mass_kg: float
    gravity_m_s2: np.ndarray
    initial_angle_rad: float
    initial_angular_velocity_rad_s: float
    newton_iteration_limit: int
    newton_residual_tolerance: float
    output_report: str
    thresholds: dict[str, float]
```

Add threshold keys:

```python
PHYSICAL_PENDULUM_RBD_BASELINE_THRESHOLD_KEYS = frozenset(
    {
        "max_abs_angle_error_rad",
        "max_implicit_residual",
        "max_length_constraint_error_m",
        "max_phase_drift_rad",
    }
)
```

Parse `rbd_baseline` with positive length/mass/time step, sample count in
`[2, step_count + 1]`, positive Newton iteration limit, positive residual
tolerance, and required threshold keys.

Update `PHYSICAL_PENDULUM_REQUIRED_MISSING_LANES` to:

```python
PHYSICAL_PENDULUM_REQUIRED_MISSING_LANES = ("mabd_newton",)
```

Update `validate_physical_pendulum_config_against_matrix` to require
`rbd_baseline.output_report` under the matrix output stem, ending in `.json`,
and distinct from analytic and M-ABD output reports.

Update YAML:

```yaml
required_missing_lanes:
  - mabd_newton
rbd_baseline:
  time_step_s: 0.01
  step_count: 16
  sample_count: 5
  length_m: 1.0
  mass_kg: 1.0
  gravity_m_s2: [0.0, -9.81, 0.0]
  initial_angle_rad: 0.0
  initial_angular_velocity_rad_s: 0.0
  newton_iteration_limit: 12
  newton_residual_tolerance: 1.0e-12
  output_report: reports/experiment_matrix/single_body_physical_pendulum_rbd_baseline.json
  thresholds:
    max_abs_angle_error_rad: 2.0
    max_implicit_residual: 1.0e-12
    max_length_constraint_error_m: 1.0e-12
    max_phase_drift_rad: 2.0
```

- [ ] **Step 4: Run GREEN**

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_run_configs
```

Expected: config tests pass.

### Task 2: RBD Rollout

**Files:**
- Create: `src/mabd_reproduction/physical_pendulum_rbd.py`
- Create: `tests/test_physical_pendulum_rbd.py`

- [ ] **Step 1: Write failing rollout tests**

Create tests that load `single_body_physical_pendulum.yaml` and assert:

```python
rollout = roll_out_physical_pendulum_rbd_baseline(config)
self.assertEqual(rollout.step_count, 16)
self.assertEqual(rollout.sample_count, 5)
self.assertTrue(rollout.finite)
self.assertLessEqual(rollout.max_implicit_residual, 1.0e-12)
self.assertLessEqual(rollout.max_length_constraint_error_m, 1.0e-12)
self.assertLessEqual(rollout.max_abs_angle_error_rad, 2.0)
self.assertEqual(rollout.samples[0].angle_rad, 0.0)
self.assertEqual(rollout.samples[0].angular_velocity_rad_s, 0.0)
self.assertGreaterEqual(rollout.samples[-1].joint_force_magnitude_n, 0.0)
```

Add a unit test for one backward-Euler residual:

```python
sample = rollout.samples[-1]
residual = (
    sample.angle_rad
    - previous_angle
    - config.rbd_baseline.time_step_s * sample.angular_velocity_rad_s
)
self.assertLess(abs(residual), 1.0e-12)
```

- [ ] **Step 2: Run RED**

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_physical_pendulum_rbd
```

Expected: module import fails.

- [ ] **Step 3: Implement rollout module**

Implement:

```python
@dataclass(frozen=True)
class PhysicalPendulumRBDSample:
    sample_index: int
    step: int
    time_s: float
    angle_rad: float
    previous_angle_rad: float
    angular_velocity_rad_s: float
    reference_angle_rad: float
    abs_angle_error_rad: float
    phase_drift_rad: float
    implicit_residual: float
    length_constraint_error_m: float
    joint_force_magnitude_n: float

@dataclass(frozen=True)
class PhysicalPendulumRBDRollout:
    samples: tuple[PhysicalPendulumRBDSample, ...]
    step_count: int
    sample_count: int
    time_step_s: float
    max_abs_angle_error_rad: float
    max_phase_drift_rad: float
    max_implicit_residual: float
    max_length_constraint_error_m: float
    max_joint_force_magnitude_n: float
    finite: bool
```

Use Newton iteration for `theta_next`:

```python
def _implicit_angle_step(theta, omega, *, h, omega_lin, limit, tol):
    theta_next = theta + h * omega
    for _ in range(limit):
        residual = theta_next - theta - h * (omega + h * omega_lin * omega_lin * np.cos(theta_next))
        derivative = 1.0 + h * h * omega_lin * omega_lin * np.sin(theta_next)
        delta = residual / derivative
        theta_next -= delta
        if abs(residual) <= tol:
            break
    omega_next = (theta_next - theta) / h
    final_residual = theta_next - theta - h * omega_next
    dynamic_residual = omega_next - omega - h * omega_lin * omega_lin * np.cos(theta_next)
    return theta_next, omega_next, max(abs(final_residual), abs(dynamic_residual))
```

Compute diagnostic joint-force magnitude:

```python
joint_force = mass * abs(length * omega_next * omega_next + g * np.sin(theta_next))
```

Compute length error from the reconstructed rigid point:

```python
point = np.array([length * np.cos(theta), -length * np.sin(theta), 0.0])
length_error = abs(np.linalg.norm(point) - length)
```

- [ ] **Step 4: Run GREEN**

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_physical_pendulum_rbd
```

Expected: rollout tests pass.

### Task 3: Report, Runner, And CLI

**Files:**
- Modify: `src/mabd_reproduction/physical_pendulum_reports.py`
- Modify: `src/mabd_reproduction/experiment_runner.py`
- Modify: `scripts/run_experiment.py`
- Modify: `tests/test_experiment_runner.py`

- [ ] **Step 1: Write failing report and CLI tests**

Add `test_run_physical_pendulum_rbd_baseline_writes_report` asserting:

```python
self.assertEqual(result.claim_id, "experiment.single_body.physical_pendulum")
self.assertEqual(result.status, EvidenceStatus.INCOMPLETE)
self.assertEqual(result.report.baseline_lane, "rbd_implicit_baseline")
self.assertEqual(loaded.solver_mode, "physical_pendulum_scalar_implicit_rbd_development")
self.assertEqual(loaded.backend, "cpu_numpy_newton_only")
self.assertEqual(loaded.observed["lane_status"], "development_diagnostic_generated")
self.assertEqual(loaded.observed["required_missing_lanes"], ["mabd_newton"])
self.assertFalse(loaded.observed["full_experiment_claim_passed"])
self.assertIn("joint_force_waveform_agreement_missing", loaded.observed["blocking_reasons"])
```

Add a CLI test using:

```bash
scripts/run_experiment.py --lane rbd_implicit_baseline \
  --config configs/experiments/single_body_physical_pendulum.yaml \
  --matrix configs/experiments/paper_experiment_matrix.yaml \
  --output /tmp/physical_pendulum_rbd.json \
  --source-commit cli-source \
  --vendored-newton-commit cli-newton
```

Expected summary baseline lane: `rbd_implicit_baseline`.

- [ ] **Step 2: Run RED**

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_runner
```

Expected: missing runner or CLI dispatch failure for physical-pendulum config.

- [ ] **Step 3: Implement report and dispatch**

Add `write_physical_pendulum_rbd_baseline_report` to
`physical_pendulum_reports.py`.

Add `run_physical_pendulum_rbd_baseline` to `experiment_runner.py`.

In `scripts/run_experiment.py`, when `--lane rbd_implicit_baseline`, inspect
the config `claim_id`. If it is `experiment.single_body.physical_pendulum`,
call `run_physical_pendulum_rbd_baseline`; otherwise call the existing
spinning-box runner. Keep the existing explicit `--output` requirement for the
spinning-box runner; allow the physical-pendulum runner to use either explicit
`--output`, `--output-root`, or the configured `rbd_baseline.output_report`.

- [ ] **Step 4: Run GREEN**

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_runner
```

Expected: report and CLI tests pass.

### Task 4: Docs, Validators, And Report Artifact

**Files:**
- Modify: `docs/reference/claim-boundaries.md`
- Modify: `scripts/validate_docs.py`
- Modify: `tests/test_phase0_bootstrap.py`
- Create: `docs/records/2026-05-17-phase35-physical-pendulum-rbd-baseline.md`
- Create: `reports/experiment_matrix/single_body_physical_pendulum_rbd_baseline.json`

- [ ] **Step 1: Write failing docs tests**

Add Phase 35 tests requiring:

- claim boundaries mention the RBD baseline diagnostic
- no `experiment.*` claim is passed
- Phase 35 record exists
- report artifact exists and is schema-valid
- current config `required_missing_lanes == ("mabd_newton",)`
- Phase 34 historical report still records its original missing lanes

- [ ] **Step 2: Run RED**

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_phase0_bootstrap
```

Expected: missing Phase 35 docs/record/validator snippets.

- [ ] **Step 3: Implement docs and validators**

Update `validate_docs.py` to Phase 0-35. Require:

- Phase 35 spec, plan, record, and report artifact paths
- current physical-pendulum config missing lanes exactly `("mabd_newton",)`
- RBD report `baseline_lane == "rbd_implicit_baseline"`
- RBD report `status == incomplete`
- RBD report `observed.full_experiment_claim_passed is False`
- RBD report `observed.required_missing_lanes == ["mabd_newton"]`
- no `experiment.*` claim status is `passed`

Generate the RBD report with:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/run_experiment.py \
  --lane rbd_implicit_baseline \
  --config configs/experiments/single_body_physical_pendulum.yaml \
  --matrix configs/experiments/paper_experiment_matrix.yaml \
  --source-commit phase35-working-tree \
  --vendored-newton-commit 96713fa965463b69c229a4d30582c733ff3526bb
```

- [ ] **Step 4: Run GREEN**

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_phase0_bootstrap
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
```

Expected: docs tests and validator pass.

### Task 5: Final Gates, Commit, Push

**Files:**
- All changed files.

- [ ] **Step 1: Run full gates**

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/env/readiness_check.py
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"
git diff --check
```

- [ ] **Step 2: Commit implementation**

Commit code, config, docs, and tests. Then regenerate the JSON report with the
implementation commit hash as `source_commit`, commit the report artifact, and
rerun affected docs validation.

- [ ] **Step 3: Push and cleanup**

Fast-forward `main`, push `origin/main`, verify local `main` and `origin/main`
match, and remove the Phase 35 worktree/branch.
