# Phase 37 Physical Pendulum MABD Newton Lane Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a formal but incomplete physical-pendulum `mabd_newton` report lane with M-ABD phase-drift and world-anchor dual-reaction diagnostics.

**Architecture:** Extend the existing physical-pendulum config and report stack without replacing the Phase 34 development diagnostic. Reuse the current M-ABD CPU oracle rollout, add diagnostic fields to its samples, then add a separate report writer and comparison acceptance path for `baseline_lane = mabd_newton`.

**Tech Stack:** Python dataclasses, NumPy, Newton vendored `newton.solvers.mabd`, `unittest`, JSON claim reports, YAML experiment configs.

---

### Task 1: Config Contract

**Files:**
- Modify: `configs/experiments/single_body_physical_pendulum.yaml`
- Modify: `src/mabd_reproduction/experiment_configs.py`
- Test: `tests/test_experiment_run_configs.py`

- [ ] **Step 1: Write failing config tests**

Add tests to `PhysicalPendulumRunConfigTests`:

```python
def test_physical_pendulum_config_loads_mabd_newton_lane(self) -> None:
    config = load_physical_pendulum_config(PHYSICAL_PENDULUM_CONFIG_PATH)

    self.assertEqual(
        config.mabd_newton.output_report,
        "reports/experiment_matrix/single_body_physical_pendulum_mabd_newton.json",
    )
    self.assertIn("max_phase_drift_rad", config.mabd_newton.thresholds)
    self.assertIn("max_world_anchor_reaction_magnitude_n", config.mabd_newton.thresholds)

def test_physical_pendulum_config_rejects_mabd_newton_output_reuse(self) -> None:
    data = _load_physical_pendulum_config_data()
    data["mabd_newton"]["output_report"] = data["mabd_development"]["output_report"]

    with self.assertRaisesRegex(ExperimentRunConfigError, "mabd_newton.output_report"):
        _load_physical_pendulum_config_from_data(data)

def test_physical_pendulum_config_rejects_mabd_newton_missing_threshold(self) -> None:
    data = _load_physical_pendulum_config_data()
    del data["mabd_newton"]["thresholds"]["max_phase_drift_rad"]

    with self.assertRaisesRegex(ExperimentRunConfigError, "mabd_newton.thresholds"):
        _load_physical_pendulum_config_from_data(data)
```

- [ ] **Step 2: Verify RED**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_run_configs
```

Expected: tests fail because `PhysicalPendulumRunConfig` has no `mabd_newton`.

- [ ] **Step 3: Implement config parsing**

Add:

```python
@dataclass(frozen=True)
class PhysicalPendulumMABDNewtonConfig:
    output_report: str
    thresholds: dict[str, float]
```

Add threshold keys:

```python
PHYSICAL_PENDULUM_MABD_NEWTON_THRESHOLD_KEYS = frozenset(
    {
        "max_abs_angle_error_rad",
        "max_constraint_residual_norm",
        "max_phase_drift_rad",
        "max_pivot_residual_m",
        "max_world_anchor_reaction_magnitude_n",
    }
)
```

Parse a required `mabd_newton` block and add it to
`PhysicalPendulumRunConfig`. Validate its `output_report` stem and collision in
`validate_physical_pendulum_config_against_matrix`.

Add YAML:

```yaml
mabd_newton:
  output_report: reports/experiment_matrix/single_body_physical_pendulum_mabd_newton.json
  thresholds:
    max_abs_angle_error_rad: 2.0
    max_constraint_residual_norm: 1.0e-10
    max_phase_drift_rad: 2.0
    max_pivot_residual_m: 1.0e-10
    max_world_anchor_reaction_magnitude_n: 100.0
```

- [ ] **Step 4: Verify GREEN**

Run the same unittest command. Expected: config tests pass.

- [ ] **Step 5: Commit**

```bash
git add configs/experiments/single_body_physical_pendulum.yaml src/mabd_reproduction/experiment_configs.py tests/test_experiment_run_configs.py
git commit -m "Add physical pendulum MABD Newton config"
```

### Task 2: Rollout Diagnostics

**Files:**
- Modify: `src/mabd_reproduction/physical_pendulum_mabd.py`
- Test: `tests/test_physical_pendulum_reference.py` or create `tests/test_physical_pendulum_mabd.py`

- [ ] **Step 1: Write failing rollout tests**

Create `tests/test_physical_pendulum_mabd.py`:

```python
from __future__ import annotations

import unittest
from pathlib import Path

import numpy as np

from mabd_reproduction.experiment_configs import load_physical_pendulum_config
from mabd_reproduction.physical_pendulum_mabd import roll_out_physical_pendulum_mabd_development

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs/experiments/single_body_physical_pendulum.yaml"


class PhysicalPendulumMABDTests(unittest.TestCase):
    def test_mabd_rollout_records_phase_drift_and_world_anchor_reaction(self) -> None:
        config = load_physical_pendulum_config(CONFIG_PATH)
        rollout = roll_out_physical_pendulum_mabd_development(config)

        self.assertEqual(rollout.step_count, 16)
        self.assertEqual(rollout.sample_count, 5)
        self.assertTrue(rollout.finite)
        self.assertGreaterEqual(rollout.max_world_anchor_reaction_magnitude_n, 0.0)
        for sample in rollout.samples:
            self.assertTrue(np.isfinite(sample.phase_drift_rad))
            self.assertEqual(sample.world_anchor_reaction_vector_n.shape, (3,))
            self.assertTrue(np.all(np.isfinite(sample.world_anchor_reaction_vector_n)))
            self.assertGreaterEqual(sample.world_anchor_reaction_magnitude_n, 0.0)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Verify RED**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_physical_pendulum_mabd
```

Expected: fails because rollout samples lack the new fields.

- [ ] **Step 3: Implement rollout fields**

Add fields to `PhysicalPendulumMABDSample`:

```python
phase_drift_rad: float
world_anchor_reaction_vector_n: np.ndarray
world_anchor_reaction_magnitude_n: float
```

Add field to `PhysicalPendulumMABDRollout`:

```python
max_world_anchor_reaction_magnitude_n: float
```

In the rollout loop, carry `latest_world_anchor_reaction = np.zeros(3)`.
After each `solve_cpu_oracle_step`, set it from `result.dlambda[:3]` and track
its norm. Store `phase_drift = angle - reference` on every sample.

- [ ] **Step 4: Verify GREEN**

Run the same unittest command. Expected: `OK`.

- [ ] **Step 5: Commit**

```bash
git add src/mabd_reproduction/physical_pendulum_mabd.py tests/test_physical_pendulum_mabd.py
git commit -m "Record MABD physical pendulum dual diagnostics"
```

### Task 3: MABD Newton Report And Runner

**Files:**
- Modify: `src/mabd_reproduction/physical_pendulum_reports.py`
- Modify: `src/mabd_reproduction/experiment_runner.py`
- Modify: `scripts/run_experiment.py`
- Test: `tests/test_experiment_runner.py`

- [ ] **Step 1: Write failing report and runner tests**

Add tests that:

```python
def test_physical_pendulum_mabd_newton_runner_writes_required_lane(self) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        output = Path(tmp) / "mabd_newton.json"
        report = run_physical_pendulum_mabd_newton(
            CONFIG_PATH,
            MATRIX_PATH,
            output=output,
            source_commit="phase37-test",
            vendored_newton_commit=VENDORED_NEWTON_COMMIT,
        )

        self.assertEqual(report.baseline_lane, "mabd_newton")
        self.assertEqual(report.solver_mode, "mabd_cpu_oracle_physical_pendulum_newton_lane")
        self.assertEqual(report.status.value, "incomplete")
        self.assertFalse(report.observed["full_experiment_claim_passed"])
        self.assertIn("max_phase_drift_rad", report.observed)
        self.assertIn("max_world_anchor_reaction_magnitude_n", report.observed)
```

Add a CLI test for:

```bash
--lane physical_pendulum_mabd_newton
```

- [ ] **Step 2: Verify RED**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_runner
```

Expected: import/CLI lane failures.

- [ ] **Step 3: Implement report writer and runner**

Add `_mabd_sample_rows` to include the new fields. Add
`write_physical_pendulum_mabd_newton_report` with `baseline_lane="mabd_newton"`
and incomplete non-claim limitations. Add `run_physical_pendulum_mabd_newton`
and CLI dispatch `physical_pendulum_mabd_newton`.

- [ ] **Step 4: Verify GREEN**

Run the same unittest command. Expected: `OK`.

- [ ] **Step 5: Commit**

```bash
git add src/mabd_reproduction/physical_pendulum_reports.py src/mabd_reproduction/experiment_runner.py scripts/run_experiment.py tests/test_experiment_runner.py
git commit -m "Add physical pendulum MABD Newton report lane"
```

### Task 4: Comparison Protocol Update

**Files:**
- Modify: `src/mabd_reproduction/comparison_reports.py`
- Test: `tests/test_physical_pendulum_comparison_reports.py`

- [ ] **Step 1: Write failing comparison tests**

Update the physical-pendulum comparison tests so the M-ABD input report uses
`baseline_lane="mabd_newton"` and expects:

```python
self.assertEqual(report.observed["missing_required_lanes"], [])
self.assertEqual(
    report.observed["paper_metric_statuses"]["phase_drift"]["status"],
    "diagnostic_available",
)
self.assertEqual(
    report.observed["paper_metric_statuses"]["joint_force_error"]["status"],
    "diagnostic_reaction_not_paper_waveform",
)
```

Add a rejection test showing that a
`physical_pendulum_mabd_development_diagnostic` report is not accepted as the
formal M-ABD comparison input.

- [ ] **Step 2: Verify RED**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_physical_pendulum_comparison_reports
```

Expected: fails because the comparison identity still expects the diagnostic
lane.

- [ ] **Step 3: Implement comparison update**

Add `mabd_newton` to `PHYSICAL_PENDULUM_INPUT_LANES` with solver mode
`mabd_cpu_oracle_physical_pendulum_newton_lane`. Snapshot MABD metrics from the
formal lane, compute missing required lanes from the required-lane list, and
set metric statuses to diagnostic availability when the formal fields exist.
Keep blockers for `pendulum_geometry_unknown`, `paper_timing_missing`, and
`joint_force_waveform_agreement_missing`.

- [ ] **Step 4: Verify GREEN**

Run the same unittest command. Expected: `OK`.

- [ ] **Step 5: Commit**

```bash
git add src/mabd_reproduction/comparison_reports.py tests/test_physical_pendulum_comparison_reports.py
git commit -m "Consume MABD Newton physical pendulum lane"
```

### Task 5: Records, Artifacts, And Validators

**Files:**
- Modify: `scripts/validate_docs.py`
- Modify: `docs/reference/claim-boundaries.md`
- Create: `docs/records/2026-05-17-phase37-physical-pendulum-mabd-newton-lane.md`
- Create: `reports/experiment_matrix/single_body_physical_pendulum_mabd_newton.json`
- Modify: `reports/experiment_matrix/single_body_physical_pendulum_comparison.json`
- Test: `tests/test_phase0_bootstrap.py`

- [ ] **Step 1: Write failing validator tests**

Add Phase 37 expectations to `tests/test_phase0_bootstrap.py`:

```python
def test_phase37_record_and_artifacts_are_registered(self) -> None:
    self.assertTrue((ROOT / "docs/records/2026-05-17-phase37-physical-pendulum-mabd-newton-lane.md").is_file())
    self.assertTrue((ROOT / "reports/experiment_matrix/single_body_physical_pendulum_mabd_newton.json").is_file())
```

Add checks that `validate_docs.py` requires the MABD Newton report,
`missing_required_lanes == []` in the regenerated comparison report, and
physical-pendulum paper claim status remains `intended`.

- [ ] **Step 2: Verify RED**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_phase0_bootstrap
```

Expected: Phase 37 record/artifact missing failures.

- [ ] **Step 3: Generate reports**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/run_experiment.py --lane physical_pendulum_mabd_newton --config configs/experiments/single_body_physical_pendulum.yaml --matrix configs/experiments/paper_experiment_matrix.yaml --output reports/experiment_matrix/single_body_physical_pendulum_mabd_newton.json
```

Then regenerate comparison with the formal lane:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/run_experiment.py --lane physical_pendulum_comparison --config configs/experiments/single_body_physical_pendulum.yaml --matrix configs/experiments/paper_experiment_matrix.yaml --analytic-report reports/experiment_matrix/single_body_physical_pendulum_analytic_reference.json --mabd-report reports/experiment_matrix/single_body_physical_pendulum_mabd_newton.json --rbd-report reports/experiment_matrix/single_body_physical_pendulum_rbd_baseline.json --output reports/experiment_matrix/single_body_physical_pendulum_comparison.json
```

- [ ] **Step 4: Implement docs validation and record**

Update `scripts/validate_docs.py` Phase 37 required path list and report
checks. Update `claim-boundaries.md` current, verified, and forbidden-claim
sections. Add the Phase 37 record with source commit, vendored Newton commit,
commands, metrics, and explicit non-claims.

- [ ] **Step 5: Verify GREEN**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_phase0_bootstrap
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
```

Expected: both commands pass.

- [ ] **Step 6: Commit**

```bash
git add scripts/validate_docs.py docs/reference/claim-boundaries.md docs/records/2026-05-17-phase37-physical-pendulum-mabd-newton-lane.md reports/experiment_matrix/single_body_physical_pendulum_mabd_newton.json reports/experiment_matrix/single_body_physical_pendulum_comparison.json tests/test_phase0_bootstrap.py
git commit -m "Record Phase 37 physical pendulum MABD lane"
```

### Task 6: Final Verification

**Files:**
- No new source files.

- [ ] **Step 1: Run focused tests**

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_run_configs tests.test_physical_pendulum_mabd tests.test_experiment_runner tests.test_physical_pendulum_comparison_reports tests.test_phase0_bootstrap
```

- [ ] **Step 2: Run full gates**

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/env/readiness_check.py
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"
git diff --check
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
```

- [ ] **Step 3: Commit any verification-only record fixes**

If verification requires record-only adjustments, make them and commit with:

```bash
git add docs reports scripts tests
git commit -m "Validate Phase 37 physical pendulum records"
```
