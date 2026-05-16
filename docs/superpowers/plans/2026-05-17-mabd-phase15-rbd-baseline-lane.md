# M-ABD Phase 15 RBD Baseline Lane Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a Newton-only CPU development RBD implicit baseline lane for the single-body spinning-box claim.

**Architecture:** Keep baseline math in `src/mabd_reproduction/rigid_baselines.py` and reuse the existing config/report contracts. The baseline is a deterministic free rigid cube oracle derived from the paper's cube size, density, linear momentum `p0`, and angular momentum `L0`; it writes an incomplete `ClaimReport` with `baseline_lane="rbd_implicit_baseline"`. The lane is development evidence only and does not pass `experiment.single_body.spinning_box`.

**Tech Stack:** Python dataclasses, NumPy, `unittest`, existing YAML config loader, existing `ClaimReport`, existing `scripts/run_experiment.py` CLI.

---

## Files

- Create `src/mabd_reproduction/rigid_baselines.py`: rigid cube properties, momentum-to-twist conversion, free rigid baseline diagnostics, and report writer.
- Create `tests/test_rigid_baselines.py`: focused RBD baseline tests.
- Modify `src/mabd_reproduction/experiment_runner.py`: add `run_spinning_box_rbd_baseline(...)`.
- Modify `scripts/run_experiment.py`: add `--lane mabd_newton|rbd_implicit_baseline`.
- Modify `tests/test_experiment_runner.py`: CLI/API tests for the RBD lane.
- Modify `docs/reference/claim-boundaries.md`, `scripts/validate_docs.py`, and `tests/test_phase0_bootstrap.py`: Phase 15 boundaries.
- Create `docs/records/2026-05-17-phase15-rbd-baseline-lane.md`: evidence record.

## Task 1: RBD Baseline Oracle And Report

**Files:**
- Create: `tests/test_rigid_baselines.py`
- Create: `src/mabd_reproduction/rigid_baselines.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_rigid_baselines.py`:

```python
from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np

from mabd_reproduction.experiment_configs import load_spinning_box_config
from mabd_reproduction.reporting import EvidenceStatus, load_claim_report


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs/experiments/single_body_spinning_box.yaml"


class RigidBaselineTests(unittest.TestCase):
    def test_spinning_box_rbd_properties_follow_paper_values(self) -> None:
        from mabd_reproduction.rigid_baselines import spinning_box_rbd_properties

        config = load_spinning_box_config(CONFIG_PATH)
        props = spinning_box_rbd_properties(config)

        self.assertAlmostEqual(props.mass_kg, 1.0)
        np.testing.assert_allclose(props.inertia_diag_kg_m2, np.full(3, 1.0 / 600.0))
        np.testing.assert_allclose(props.linear_velocity_m_s, [100.0, 0.0, 0.0])
        np.testing.assert_allclose(props.angular_velocity_rad_s, [0.0, 60000.0, 0.0])

    def test_run_spinning_box_rbd_baseline_is_deterministic_and_incomplete(self) -> None:
        from mabd_reproduction.rigid_baselines import run_spinning_box_rbd_baseline

        config = load_spinning_box_config(CONFIG_PATH)
        result = run_spinning_box_rbd_baseline(config)

        self.assertEqual(result.step_count, config.step_count)
        self.assertEqual(result.time_step_s, config.time_step_s)
        self.assertEqual(result.status, EvidenceStatus.INCOMPLETE)
        self.assertEqual(result.baseline_lane, "rbd_implicit_baseline")
        self.assertLessEqual(result.linear_momentum_error, 1.0e-12)
        self.assertLessEqual(result.angular_momentum_error, 1.0e-12)
        self.assertLessEqual(result.energy_drift, 1.0e-12)

    def test_write_spinning_box_rbd_baseline_report(self) -> None:
        from mabd_reproduction.rigid_baselines import write_spinning_box_rbd_baseline_report

        config = load_spinning_box_config(CONFIG_PATH)
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "rbd_baseline.json"
            report = write_spinning_box_rbd_baseline_report(
                path,
                config=config,
                source_commit="test-source",
                vendored_newton_commit="test-newton",
            )
            loaded = load_claim_report(path)

        self.assertEqual(report.claim_id, "experiment.single_body.spinning_box")
        self.assertEqual(loaded.baseline_lane, "rbd_implicit_baseline")
        self.assertEqual(loaded.status, EvidenceStatus.INCOMPLETE)
        self.assertIn("development baseline", loaded.failure_reason)
        self.assertIn("linear_momentum_error", loaded.observed)
        self.assertIn("angular_momentum_error", loaded.observed)
        self.assertIn("energy_drift", loaded.observed)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run RED**

```bash
PYTHONPATH=src:vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  -m unittest tests.test_rigid_baselines
```

Expected: `ModuleNotFoundError: No module named 'mabd_reproduction.rigid_baselines'`.

- [ ] **Step 3: Implement minimal oracle/report**

Create `src/mabd_reproduction/rigid_baselines.py` with dataclasses:

- `SpinningBoxRBDProperties`
- `SpinningBoxRBDBaselineResult`

Implement:

- `_paper_float(value, name)` parsing strings like `"1E3 kg/m^3"`.
- `_paper_vector(value, name)` for `p0` and `L0`.
- `spinning_box_rbd_properties(config)` using `m = density * cube_size_m ** 3` and cube inertia `I = (1/6) * m * size ** 2`.
- `run_spinning_box_rbd_baseline(config)` for free rigid cube diagnostics with unchanged momentum and energy over `step_count`.
- `write_spinning_box_rbd_baseline_report(path, config, source_commit, vendored_newton_commit, paper_source_version="2603.08079v2")` writing an incomplete `ClaimReport`.

- [ ] **Step 4: Run GREEN and lint**

```bash
PYTHONPATH=src:vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  -m unittest tests.test_rigid_baselines

/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  -m ruff check src/mabd_reproduction/rigid_baselines.py tests/test_rigid_baselines.py
```

Expected: `Ran 3 tests, OK` and `All checks passed!`.

- [ ] **Step 5: Commit**

```bash
git add src/mabd_reproduction/rigid_baselines.py tests/test_rigid_baselines.py
git commit -m "feat: add spinning-box RBD baseline lane"
```

## Task 2: Runner And CLI Lane Dispatch

**Files:**
- Modify: `src/mabd_reproduction/experiment_runner.py`
- Modify: `scripts/run_experiment.py`
- Modify: `tests/test_experiment_runner.py`

- [ ] **Step 1: Write failing runner/CLI tests**

Add tests that:

- import and call `run_spinning_box_rbd_baseline(...)` with explicit `output_path`;
- assert the written report has `baseline_lane == "rbd_implicit_baseline"` and `status == incomplete`;
- invoke `scripts/run_experiment.py --lane rbd_implicit_baseline --output /tmp/rbd_baseline.json` with a temporary test path and assert JSON summary has `"baseline_lane": "rbd_implicit_baseline"`;
- invoke `scripts/run_experiment.py --lane rbd_implicit_baseline --output-root /tmp/rbd-root` with a temporary test path and assert it fails with a message that the RBD lane requires `--output`.

- [ ] **Step 2: Run RED**

```bash
PYTHONPATH=src:vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  -m unittest tests.test_experiment_runner
```

Expected: import/argparse failures for the new RBD lane.

- [ ] **Step 3: Implement dispatch**

- In `experiment_runner.py`, import `write_spinning_box_rbd_baseline_report`.
- Add `run_spinning_box_rbd_baseline(...)` that validates config/matrix and requires explicit `output_path`.
- In `scripts/run_experiment.py`, add `--lane` with choices `mabd_newton` and `rbd_implicit_baseline`; default `mabd_newton`.
- Route `mabd_newton` to existing `run_spinning_box_experiment`.
- Route `rbd_implicit_baseline` to `run_spinning_box_rbd_baseline`.

- [ ] **Step 4: Run GREEN and lint**

```bash
PYTHONPATH=src:vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  -m unittest tests.test_experiment_runner tests.test_rigid_baselines

/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  -m ruff check src/mabd_reproduction/experiment_runner.py scripts/run_experiment.py tests/test_experiment_runner.py
```

- [ ] **Step 5: Commit**

```bash
git add src/mabd_reproduction/experiment_runner.py scripts/run_experiment.py tests/test_experiment_runner.py
git commit -m "feat: dispatch spinning-box RBD baseline runner"
```

## Task 3: Phase 15 Docs And Record

**Files:**
- Modify: `docs/reference/claim-boundaries.md`
- Modify: `scripts/validate_docs.py`
- Modify: `tests/test_phase0_bootstrap.py`
- Create: `docs/records/2026-05-17-phase15-rbd-baseline-lane.md`

- [ ] **Step 1: Write failing docs tests/validator snippets**

Require Phase 15 boundary text:

- `Phase 15 verifies a Newton-only RBD implicit baseline development lane`
- `Phase 15 does not verify the paper spinning-box experiment`
- `any passed \`experiment.*\` claim`

Require record snippets:

- `## Status`, `passed`
- `configs/experiments/single_body_spinning_box.yaml`
- `plan commit:`
- `implementation commits:`
- `` `run_spinning_box_rbd_baseline` ``
- `` `rbd_implicit_baseline` ``
- `No \`experiment.*\` claim is passed in this phase.`

- [ ] **Step 2: Run RED**

```bash
PYTHONPATH=src:vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  -m unittest tests.test_phase0_bootstrap
PYTHONPATH=src:vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  scripts/validate_docs.py
```

- [ ] **Step 3: Implement docs and record**

Add Phase 15 boundary and create the record with final verification section initially marked as refreshed after final verification. Include paper source lines `experiment.tex:40-55`.

- [ ] **Step 4: Run GREEN and commit**

```bash
PYTHONPATH=src:vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  -m unittest tests.test_phase0_bootstrap
PYTHONPATH=src:vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  scripts/validate_docs.py
git diff --check
git add docs/reference/claim-boundaries.md docs/records/2026-05-17-phase15-rbd-baseline-lane.md scripts/validate_docs.py tests/test_phase0_bootstrap.py
git commit -m "docs: record Phase 15 RBD baseline lane"
```

## Task 4: Final Verification

- [ ] **Step 1: Run full verification**

```bash
/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_rigid_baselines tests.test_experiment_runner tests.test_experiment_run_configs tests.test_single_body_report_lane tests.test_reporting_contracts tests.test_phase0_bootstrap
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"
git diff --check
```

- [ ] **Step 2: Refresh record and commit**

Record actual counts and commit hashes, then:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
git diff --check
git add docs/records/2026-05-17-phase15-rbd-baseline-lane.md
git commit -m "docs: refresh Phase 15 verification evidence"
```

## Final Review And Merge

- Request two read-only reviews: implementation/API/CLI and docs/provenance.
- Fix Critical/Important feedback with TDD.
- Re-run full branch verification.
- Fast-forward merge to `main`, run the same gates on `main`, push to `git@github.com:jandan138/mabd-newton.git main`, verify remote head, and clean the worktree.

## Self-Review

- This plan advances the exact current blocker `rbd_implicit_baseline_adapter_missing`.
- The lane is explicitly development-only and keeps report status incomplete.
- No generated report artifact is committed.
- No `experiment.*` claim is passed.
