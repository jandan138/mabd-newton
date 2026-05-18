# Phase57 T-Handle Comparison Protocol Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an incomplete, machine-checkable T-handle comparison protocol that consumes the existing RK4 reference and Newton M-ABD diagnostic reports.

**Architecture:** Extend the existing T-handle config with a `comparison` section, add a T-handle comparison writer to `comparison_reports.py`, expose it through `experiment_runner.py` and `scripts/run_experiment.py`, then generate a committed comparison report and evidence record while preserving claim boundaries.

**Tech Stack:** Python 3.10, NumPy-free report math where possible, unittest, YAML configs, existing `ClaimReport` JSON schema, vendored Newton import through `PYTHONPATH=src:vendor/newton`.

---

### Task 1: Config Schema And Matrix Contract

**Files:**
- Modify: `configs/experiments/single_body_t_handle.yaml`
- Modify: `configs/experiments/paper_experiment_matrix.yaml`
- Modify: `docs/reference/paper-claims.yaml`
- Modify: `src/mabd_reproduction/experiment_configs.py`
- Modify: `tests/test_experiment_run_configs.py`

- [ ] **Step 1: Write failing config tests**

Extend `tests/test_experiment_run_configs.py::test_t_handle_config_is_machine_checkable` with:

```python
self.assertEqual(
    config.comparison.output_report,
    "reports/experiment_matrix/single_body_t_handle_comparison.json",
)
self.assertEqual(config.comparison.required_lanes, ("mabd_newton", "rbd_rk4_reference"))
self.assertEqual(
    config.comparison.required_metrics,
    (
        "flip_timing_error",
        "intermediate_axis_angular_velocity_waveform",
        "energy_loss",
    ),
)
self.assertIn("max_sample_time_delta_s", config.comparison.thresholds)
self.assertIn("t_handle_comparison_report_incomplete", config.failure_reason)
self.assertNotIn("t_handle_comparison_report_missing", config.failure_reason)
```

Add a local helper so rejection tests do not fail at test setup before the
comparison YAML exists in the implementation:

```python
def _t_handle_mapping_with_comparison(self) -> dict:
    source = yaml.safe_load(T_HANDLE_CONFIG_PATH.read_text(encoding="utf-8"))
    source.setdefault(
        "comparison",
        {
            "output_report": "reports/experiment_matrix/single_body_t_handle_comparison.json",
            "required_lanes": ["mabd_newton", "rbd_rk4_reference"],
            "required_metrics": [
                "flip_timing_error",
                "intermediate_axis_angular_velocity_waveform",
                "energy_loss",
            ],
            "thresholds": {"max_sample_time_delta_s": 1.0e-12},
        },
    )
    return source
```

Add rejection tests that mutate that local mapping and expect
`ExperimentRunConfigError`:

```python
source["comparison"]["required_lanes"] = ["mabd_newton"]
source["comparison"]["required_metrics"] = ["energy_loss"]
source["comparison"]["output_report"] = source["mabd_newton"]["output_report"]
source["comparison"]["thresholds"] = {}
```

- [ ] **Step 2: Run the config tests and verify RED**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_run_configs
```

Expected: failure because `THandleRunConfig` has no `comparison` field yet.

- [ ] **Step 3: Implement config parsing**

In `src/mabd_reproduction/experiment_configs.py` add:

```python
@dataclass(frozen=True)
class THandleComparisonConfig:
    output_report: str
    required_lanes: tuple[str, ...]
    required_metrics: tuple[str, ...]
    thresholds: dict[str, float]
```

Add constants:

```python
T_HANDLE_COMPARISON_REQUIRED_LANES = ("mabd_newton", "rbd_rk4_reference")
T_HANDLE_COMPARISON_REQUIRED_METRICS = (
    "flip_timing_error",
    "intermediate_axis_angular_velocity_waveform",
    "energy_loss",
)
T_HANDLE_COMPARISON_THRESHOLD_KEYS = frozenset({"max_sample_time_delta_s"})
```

Parse `comparison` with `_require_t_handle_comparison(data)`, attach it to
`THandleRunConfig`, and validate that the comparison required lanes and metrics
match the T-handle matrix.

- [ ] **Step 4: Update YAML blockers**

In `single_body_t_handle.yaml` add the `comparison` block from the design spec
and change the report failure text to `t_handle_comparison_report_incomplete`.

In `paper_experiment_matrix.yaml` and `paper-claims.yaml`, replace
`t_handle_comparison_report_missing` with
`t_handle_comparison_report_incomplete`.

- [ ] **Step 5: Run config tests and verify GREEN**

Run the same unittest command. Expected: all config tests pass.

### Task 2: T-Handle Comparison Report Writer

**Files:**
- Modify: `src/mabd_reproduction/comparison_reports.py`
- Create: `tests/test_t_handle_comparison_reports.py`

- [ ] **Step 1: Write failing report tests**

Create `tests/test_t_handle_comparison_reports.py` with tests that generate
temporary RK4 and M-ABD reports using existing report writers, call
`write_t_handle_comparison_report(...)`, and assert:

```python
self.assertEqual(report.claim_id, "experiment.single_body.t_handle")
self.assertEqual(report.baseline_lane, "t_handle_comparison_protocol")
self.assertEqual(report.solver_mode, "t_handle_multilane_comparison_development")
self.assertEqual(report.backend, "report_protocol")
self.assertEqual(report.status, EvidenceStatus.INCOMPLETE)
self.assertFalse(report.observed["full_experiment_claim_passed"])
self.assertEqual(report.observed["missing_required_lanes"], [])
self.assertIn("input_report_provenance", report.observed)
self.assertIn("sample_index_differences", report.observed)
self.assertGreater(report.observed["matched_sample_index_count"], 0)
self.assertGreater(report.observed["time_aligned_sample_count"], 0)
self.assertIsNotNone(report.observed["intermediate_axis_waveform_rmse_rad_s"])
self.assertIsNotNone(report.observed["max_abs_angular_velocity_delta_rad_s"])
self.assertIn("flip_timing_diagnostics", report.observed)
self.assertIn("energy_drift_diagnostics", report.observed)
self.assertIn("t_handle_comparison_pass_gate_not_enabled", report.observed["blocking_reasons"])
self.assertIn("t_handle_comparison_report_incomplete", report.observed["blocking_reasons"])
self.assertIn("mabd_newton_report_incomplete", report.observed["blocking_reasons"])
self.assertEqual(
    report.observed["paper_metric_statuses"]["intermediate_axis_angular_velocity_waveform"]["status"],
    "diagnostic_available_not_paper_curve",
)
self.assertEqual(
    report.observed["paper_metric_statuses"]["flip_timing_error"]["status"],
    "sample_grid_diagnostic_not_paper_timing",
)
self.assertEqual(
    report.observed["paper_metric_statuses"]["energy_loss"]["status"],
    "signed_energy_drift_diagnostic_not_paper_loss",
)
```

Add identity rejection tests for wrong `claim_id`, wrong `baseline_lane`, wrong
`scene_id`, wrong solver mode, wrong backend, wrong status, missing procedural
asset hash, `full_experiment_claim_passed = true`, changed RK4
`reference_scope`, and changed MABD `mabd_diagnostic_scope`.

Add a nonfinite input test by mutating one angular velocity sample to
`float("nan")` in memory and writing it with `json.dumps(..., allow_nan=True)`.
The comparison writer should load the report, set `nonfinite = true`, add a
`nonfinite_sample_values` blocker, and write comparison JSON without bare
`NaN` or `Infinity`.

- [ ] **Step 2: Run report tests and verify RED**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_t_handle_comparison_reports
```

Expected: import failure because `write_t_handle_comparison_report` does not
exist.

- [ ] **Step 3: Implement report helpers**

In `comparison_reports.py`, add T-handle constants and helpers:

```python
T_HANDLE_REQUIRED_METRICS = (
    "flip_timing_error",
    "intermediate_axis_angular_velocity_waveform",
    "energy_loss",
)
T_HANDLE_INPUT_LANES = {
    "rbd_rk4_reference": {
        "solver_mode": "t_handle_torque_free_rk4_reference",
        "backend": "cpu_numpy",
    },
    "mabd_newton": {
        "solver_mode": "mabd_cpu_oracle_t_handle_newton_lane",
        "backend": "cpu_numpy_newton_only",
    },
}
```

Implement strict lane validation, provenance hashing, finite scalar extraction,
sample-key parsing by `sample_index`, angular velocity component extraction,
first sign-flip interpolation along the configured intermediate axis, and
waveform RMSE over matched finite samples that are also time-aligned according
to `max_sample_time_delta_s`.

- [ ] **Step 4: Implement report writer**

Add `write_t_handle_comparison_report(...)` with signature:

```python
def write_t_handle_comparison_report(
    path: str | Path,
    *,
    config: THandleRunConfig,
    rk4_report_path: str | Path,
    mabd_report_path: str | Path,
    source_commit: str,
    vendored_newton_commit: str,
    paper_source_version: str = "2603.08079v2",
) -> ClaimReport:
```

The writer must load both reports, reject invalid identities, compute
diagnostics, write `EvidenceStatus.INCOMPLETE`, keep
`full_experiment_claim_passed = false`, and include `raw_outputs` with both
input report paths.

- [ ] **Step 5: Run report tests and verify GREEN**

Run the report unittest. Expected: all tests pass.

### Task 3: Runner And CLI Dispatch

**Files:**
- Modify: `src/mabd_reproduction/experiment_runner.py`
- Modify: `scripts/run_experiment.py`
- Modify: `tests/test_experiment_runner.py`

- [ ] **Step 1: Add runner helper for lane inputs**

Add a private helper in `tests/test_experiment_runner.py` that writes temporary
T-handle RK4 and MABD lane reports:

```python
def _write_t_handle_lane_inputs(self, tmpdir: str) -> tuple[Path, Path]:
    from mabd_reproduction.experiment_configs import load_t_handle_config
    from mabd_reproduction.t_handle_reports import (
        write_t_handle_mabd_newton_report,
        write_t_handle_rk4_reference_report,
    )

    config = load_t_handle_config(T_HANDLE_CONFIG_PATH)
    rk4_path = Path(tmpdir) / "t_handle_rk4.json"
    mabd_path = Path(tmpdir) / "t_handle_mabd.json"
    write_t_handle_rk4_reference_report(
        rk4_path,
        config=config,
        source_commit="test-source",
        vendored_newton_commit="test-newton",
    )
    write_t_handle_mabd_newton_report(
        mabd_path,
        config=config,
        source_commit="test-source",
        vendored_newton_commit="test-newton",
    )
    return rk4_path, mabd_path
```

- [ ] **Step 2: Write failing runner tests**

Add tests that call `run_t_handle_comparison(...)` with both inputs and assert:

```python
self.assertEqual(result.report_path, output_path)
self.assertEqual(result.claim_id, "experiment.single_body.t_handle")
self.assertEqual(result.status, EvidenceStatus.INCOMPLETE)
self.assertEqual(result.report.baseline_lane, "t_handle_comparison_protocol")
self.assertEqual(loaded.solver_mode, "t_handle_multilane_comparison_development")
self.assertEqual(loaded.backend, "report_protocol")
self.assertIn("t_handle_comparison_report_incomplete", loaded.observed["blocking_reasons"])
```

Add a rejection test for missing `rk4_report_path` or `mabd_report_path` with
message `t_handle_comparison requires --mabd-report and --rbd-report`.

Add a runner test that omits `output_path` and verifies the configured default
`config.comparison.output_report` is used.

- [ ] **Step 3: Write failing CLI test**

Add a `scripts/run_experiment.py --lane t_handle_comparison` test that passes
`--rbd-report`, `--mabd-report`, `--output`, `--source-commit`, and
`--vendored-newton-commit`, then asserts:

```python
self.assertEqual(summary["claim_id"], "experiment.single_body.t_handle")
self.assertEqual(summary["status"], "incomplete")
self.assertEqual(summary["baseline_lane"], "t_handle_comparison_protocol")
self.assertEqual(loaded.solver_mode, "t_handle_multilane_comparison_development")
```

- [ ] **Step 4: Run runner tests and verify RED**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_runner
```

Expected: failure because runner and CLI dispatch are missing.

- [ ] **Step 5: Implement runner and CLI**

Add `run_t_handle_comparison(...)` to `experiment_runner.py`, import
`write_t_handle_comparison_report`, and resolve the default output through
`config.comparison.output_report`.

In `scripts/run_experiment.py`, import `run_t_handle_comparison`, add
`"t_handle_comparison"` to `--lane` choices, and dispatch with
`args.rbd_report` as the RK4 input and `args.mabd_report` as the MABD input.

- [ ] **Step 6: Run runner tests and verify GREEN**

Run the same unittest command. Expected: all runner tests pass.

### Task 4: Artifact, Claim Boundaries, And Validator

**Files:**
- Create: `reports/experiment_matrix/single_body_t_handle_comparison.json`
- Create: `docs/records/2026-05-18-phase57-t-handle-comparison-protocol.md`
- Modify: `docs/reference/claim-boundaries.md`
- Modify: `scripts/validate_docs.py`
- Modify: `tests/test_phase0_bootstrap.py`

- [ ] **Step 1: Add Phase57 validator tests**

In `tests/test_phase0_bootstrap.py`, add a Phase57 test that loads the matrix,
claim boundaries, Phase57 record, and comparison report. It should require
`t_handle_comparison_report_incomplete`, reject
`t_handle_comparison_report_missing` only in the Phase57 current-evidence
section, current paper-claims T-handle note, and current matrix blockers. It
must not reject historical Phase43 or Phase56 records/boundary bullets that
preserve prior provenance. Verify `baseline_lane = t_handle_comparison_protocol`, verify
`solver_mode = t_handle_multilane_comparison_development`, and verify
`full_experiment_claim_passed = false`.

- [ ] **Step 2: Add docs validator checks**

In `scripts/validate_docs.py`, add Phase57 required paths, load the generated
comparison report, check report hash in the Phase57 record, verify input report
provenance hashes for both lane reports, require finite matched samples, and
reject overclaims.

- [ ] **Step 3: Commit implementation before artifact generation**

Run targeted tests:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_run_configs tests.test_t_handle_comparison_reports tests.test_experiment_runner
```

Commit implementation code before generating the report so the artifact
`source_commit` points at the implementation commit.

- [ ] **Step 4: Generate comparison artifact**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/run_experiment.py \
  --lane t_handle_comparison \
  --config configs/experiments/single_body_t_handle.yaml \
  --matrix configs/experiments/paper_experiment_matrix.yaml \
  --rbd-report reports/experiment_matrix/single_body_t_handle_rk4_reference.json \
  --mabd-report reports/experiment_matrix/single_body_t_handle_mabd_newton.json \
  --source-commit "$(git rev-parse HEAD)" \
  --vendored-newton-commit 96713fa965463b69c229a4d30582c733ff3526bb
```

- [ ] **Step 5: Write Phase57 evidence record**

Create `docs/records/2026-05-18-phase57-t-handle-comparison-protocol.md` with:

- status `passed_for_t_handle_comparison_protocol`;
- comparison report path and SHA256;
- source commit and vendored Newton commit;
- exact commands and observed passing results;
- explicit non-claims for paper-faithful geometry, raw waveform agreement,
  comparison pass, timing, rendered output, and full reproduction.

- [ ] **Step 6: Run full verification**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"
/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .
git diff --check
```

Expected: all pass.
