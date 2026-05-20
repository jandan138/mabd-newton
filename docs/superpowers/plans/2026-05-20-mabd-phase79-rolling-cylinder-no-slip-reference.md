# Phase 79 Rolling Cylinder No-Slip Reference Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a fail-closed analytic no-slip rolling-cylinder reference report for the rolling/spinning experiment.

**Architecture:** Extend the rolling/spinning config with `rbd_no_slip_reference`, add a closed-form NumPy reference result and report writer, expose it through the experiment runner and CLI, then record the evidence without passing the paper claim.

**Tech Stack:** Python dataclasses, YAML configs, NumPy closed-form kinematics, `ClaimReport`, unittest, existing `mabd-newton-py310` environment.

---

### Task 1: Config Contract

**Files:**
- Modify: `src/mabd_reproduction/experiment_configs.py`
- Modify: `configs/experiments/single_body_rolling_spinning.yaml`
- Test: `tests/test_experiment_run_configs.py`

- [ ] **Step 1: Write the failing config test**

```python
def test_rolling_spinning_rbd_no_slip_reference_is_machine_checkable(self) -> None:
    config = load_rolling_spinning_config(ROLLING_SPINNING_CONFIG_PATH)
    lane = config.rbd_no_slip_reference
    self.assertEqual(
        lane.output_report,
        "reports/experiment_matrix/single_body_rolling_spinning_rbd_no_slip_reference.json",
    )
    self.assertAlmostEqual(
        lane.initial_linear_velocity_m_s[0]
        + lane.radius_m * lane.initial_angular_velocity_rad_s[2],
        0.0,
        places=12,
    )
```

- [ ] **Step 2: Run the test and verify it fails**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_run_configs.ExperimentRunConfigTests.test_rolling_spinning_rbd_no_slip_reference_is_machine_checkable
```

Expected: fail because `RollingSpinningRunConfig` has no `rbd_no_slip_reference`.

- [ ] **Step 3: Implement minimal config support**

Reuse `RollingSpinningRBDBaselineConfig` for the reference section. Parse
`rbd_no_slip_reference` from YAML. Validate output path, step count, sample
count, `time_step_s = 0.01`, center height, zero vertical/lateral velocity,
zero off-axis angular velocity, and the no-slip condition. Because the lane
reuses `RollingSpinningRBDBaselineConfig`, keep the existing RBD `contact` and
`thresholds` schema and record center-height drift with a report-level fixed
tolerance rather than a new config key.

- [ ] **Step 4: Run the config tests**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_run_configs
```

Expected: all config tests pass.

### Task 2: Closed-Form Reference And Runner

**Files:**
- Modify: `src/mabd_reproduction/rolling_spinning_reports.py`
- Modify: `src/mabd_reproduction/experiment_runner.py`
- Modify: `scripts/run_experiment.py`
- Test: `tests/test_experiment_runner.py`

- [ ] **Step 1: Write the failing runner test**

```python
def test_run_rolling_spinning_rbd_no_slip_reference_writes_report(self) -> None:
    from mabd_reproduction.experiment_runner import run_rolling_spinning_rbd_no_slip_reference

    with TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "rolling_spinning_no_slip_reference.json"
        result = run_rolling_spinning_rbd_no_slip_reference(
            config_path=ROLLING_SPINNING_CONFIG_PATH,
            matrix_path=MATRIX_PATH,
            output_path=output_path,
            source_commit="test-source",
            vendored_newton_commit="test-newton",
        )
        loaded = load_claim_report(result.report_path)

    self.assertEqual(result.status, EvidenceStatus.INCOMPLETE)
    self.assertEqual(loaded.baseline_lane, "rbd_no_slip_reference")
    self.assertEqual(loaded.observed["reference_status"], "analytic_no_slip_reference_generated")
    self.assertFalse(loaded.observed["local_runtime_measured"])
    self.assertLessEqual(loaded.observed["no_slip_residual_m_s"], 1.0e-12)
    self.assertEqual(loaded.timing_distribution["status"], "not_measured")
    self.assertNotIn("total_wall_time_ms", loaded.timing_distribution)
```

- [ ] **Step 2: Run the test and verify it fails**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_runner.ExperimentRunnerTests.test_run_rolling_spinning_rbd_no_slip_reference_writes_report
```

Expected: import failure because the runner does not exist.

- [ ] **Step 3: Implement the closed-form reference**

Add `RollingCylinderNoSlipReferenceResult`, compute mass/inertia using the
existing cylinder helper, compute constant center velocity and constant angular
velocity for `step_count * time_step_s`, sample the trajectory with
`_sample_indices`, and compute no-slip residual, center-height drift, and energy
drift. Do not write wall-clock timing into this deterministic report; paper
runtime evidence remains blocked and `local_runtime_measured` stays `false`.

- [ ] **Step 4: Add report writer, runner, and CLI lane**

Add `write_rolling_spinning_rbd_no_slip_reference_report`,
`run_rolling_spinning_rbd_no_slip_reference`, and CLI lane
`rolling_spinning_rbd_no_slip_reference`.

- [ ] **Step 5: Run runner and CLI tests**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_runner
```

Expected: all runner tests pass.

### Task 3: Evidence And Validation

**Files:**
- Add: `reports/experiment_matrix/single_body_rolling_spinning_rbd_no_slip_reference.json`
- Add: `docs/records/2026-05-20-phase79-rolling-cylinder-no-slip-reference.md`
- Modify: `docs/reference/claim-boundaries.md`
- Modify: `docs/reference/reproduction-gap-audit.yaml`
- Modify: `scripts/validate_docs.py`
- Test: `tests/test_phase0_bootstrap.py`

- [ ] **Step 1: Generate the report**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/run_experiment.py --lane rolling_spinning_rbd_no_slip_reference --config configs/experiments/single_body_rolling_spinning.yaml --matrix configs/experiments/paper_experiment_matrix.yaml --source-commit <current-commit> --vendored-newton-commit 96713fa965463b69c229a4d30582c733ff3526bb
```

- [ ] **Step 2: Add bootstrap validator tests**

Add tests requiring the report path, report SHA, `reference_status`,
`paper_comparable = false`, `full_experiment_claim_passed = false`,
`local_runtime_measured = false`, `timing_distribution.status = not_measured`,
`timing_distribution.paper_comparable = false`, deterministic repeated output,
zero no-slip residual within threshold, and the gap audit distinction that this
is a reference artifact, not a paper RBD solver pass. Preserve existing gap
vocabulary such as
`paper_faithful_mabd_rolling_cylinder` and `paper_comparable_timing` while
reporting the blocker reasons with `_missing` suffixes.

- [ ] **Step 3: Update `scripts/validate_docs.py`**

Validate the Phase79 spec, plan, record, report fields, thresholds, hash, gap
audit fields, and claim boundary.

- [ ] **Step 4: Run final validation**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .
git diff --check
```

Expected: all commands pass.
