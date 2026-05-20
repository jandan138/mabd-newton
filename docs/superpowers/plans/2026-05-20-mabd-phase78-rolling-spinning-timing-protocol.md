# Phase 78 Rolling/Spinning Timing Protocol Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a fail-closed rolling/spinning timing protocol report that records the paper timing table and local non-comparable timing diagnostics.

**Architecture:** Extend the rolling/spinning config with a `paper_timing_protocol` section, add a report writer that reads committed input reports, then expose the lane through the experiment runner and CLI. The output is machine-checkable evidence, not a passed paper timing claim.

**Tech Stack:** Python dataclasses, YAML configs, `ClaimReport`, unittest, existing `mabd-newton-py310` environment.

---

### Task 1: Config Contract

**Files:**
- Modify: `src/mabd_reproduction/experiment_configs.py`
- Modify: `configs/experiments/single_body_rolling_spinning.yaml`
- Test: `tests/test_experiment_run_configs.py`

- [ ] **Step 1: Write the failing config test**

```python
def test_rolling_spinning_paper_timing_protocol_is_fail_closed(self) -> None:
    config = load_rolling_spinning_config(ROLLING_SPINNING_CONFIG_PATH)
    self.assertEqual(
        config.paper_timing_protocol.output_report,
        "reports/experiment_matrix/single_body_rolling_spinning_timing_protocol.json",
    )
    self.assertIn(
        "reports/experiment_matrix/single_body_rolling_spinning_mabd_material_preflight.json",
        config.paper_timing_protocol.input_reports,
    )
```

- [ ] **Step 2: Run the test and verify it fails**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_run_configs.ExperimentRunConfigTests.test_rolling_spinning_paper_timing_protocol_is_fail_closed
```

Expected: fail because `RollingSpinningRunConfig` has no `paper_timing_protocol`.

- [ ] **Step 3: Implement minimal config support**

Add a small dataclass with `output_report` and `input_reports`, parse it from
YAML, and validate that the report path is a JSON file under
`reports/experiment_matrix` and distinct from all input reports.

- [ ] **Step 4: Run the config test and related config suite**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_run_configs
```

Expected: all tests pass.

### Task 2: Report Writer And Runner

**Files:**
- Modify: `src/mabd_reproduction/rolling_spinning_reports.py`
- Modify: `src/mabd_reproduction/experiment_runner.py`
- Modify: `scripts/run_experiment.py`
- Test: `tests/test_experiment_runner.py`

- [ ] **Step 1: Write the failing runner test**

```python
def test_run_rolling_spinning_paper_timing_protocol_writes_report(self) -> None:
    from mabd_reproduction.experiment_runner import run_rolling_spinning_paper_timing_protocol

    with TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "rolling_spinning_timing.json"
        result = run_rolling_spinning_paper_timing_protocol(
            config_path=ROLLING_SPINNING_CONFIG_PATH,
            matrix_path=MATRIX_PATH,
            output_path=output_path,
            source_commit="test-source",
            vendored_newton_commit="test-newton",
        )
        loaded = load_claim_report(result.report_path)

    self.assertEqual(result.status, EvidenceStatus.INCOMPLETE)
    self.assertEqual(loaded.baseline_lane, "paper_timing_protocol")
    self.assertFalse(loaded.observed["paper_comparable"])
    self.assertIn("paper_comparable_timing_missing", loaded.observed["blocking_reasons"])
```

- [ ] **Step 2: Run the test and verify it fails**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_runner.ExperimentRunnerTests.test_run_rolling_spinning_paper_timing_protocol_writes_report
```

Expected: import or attribute failure because the runner does not exist.

- [ ] **Step 3: Implement the report writer and runner**

Use `load_claim_report` to read each configured input report. Store each report's
path, status, baseline lane, solver mode, `observed.paper_comparable`, and
`timing_distribution.total_wall_time_ms` if present. Keep the new report
`status = incomplete`.

- [ ] **Step 4: Add CLI support**

Add `rolling_spinning_paper_timing_protocol` to `scripts/run_experiment.py` and
cover it with a CLI test.

- [ ] **Step 5: Run runner tests**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_runner
```

Expected: all tests pass.

### Task 3: Evidence And Validation

**Files:**
- Add: `reports/experiment_matrix/single_body_rolling_spinning_timing_protocol.json`
- Add: `docs/records/2026-05-20-phase78-rolling-spinning-timing-protocol.md`
- Modify: `docs/reference/claim-boundaries.md`
- Modify: `docs/reference/reproduction-gap-audit.yaml`
- Modify: `scripts/validate_docs.py`
- Test: `tests/test_phase0_bootstrap.py`

- [ ] **Step 1: Generate the report**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/run_experiment.py --lane rolling_spinning_paper_timing_protocol --config configs/experiments/single_body_rolling_spinning.yaml --matrix configs/experiments/paper_experiment_matrix.yaml --source-commit <current-commit> --vendored-newton-commit 96713fa965463b69c229a4d30582c733ff3526bb
```

- [ ] **Step 2: Write validator tests**

Add bootstrap tests that require the report SHA, `paper_comparable = false`,
and the gap audit distinction between "timing protocol artifact exists" and
`paper_comparable_timing` still missing.

- [ ] **Step 3: Update `scripts/validate_docs.py`**

Validate the Phase78 spec, plan, record, report fields, input report list, hash,
and claim boundary.

- [ ] **Step 4: Run final validation**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .
git diff --check
```

Expected: all commands pass.
