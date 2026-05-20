# Phase 73 Rolling-Spinning Report Lane Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a machine-checkable, non-passing report lane for `experiment.single_body.rolling_spinning` so the currently missing matrix output becomes auditable incomplete evidence.

**Architecture:** Reuse the existing config/report/runner pattern. Add a small rolling/spinning config dataclass and matrix validator, a focused `rolling_spinning_reports.py` writer that emits a protocol-only `ClaimReport`, and a `rolling_spinning_protocol` runner/CLI lane. Keep all claim statuses incomplete/intended and use `backend = report_protocol` so the report cannot be mistaken for a local runtime benchmark.

**Tech Stack:** Python 3.10, `unittest`, PyYAML, existing `ClaimReport` JSON schema.

---

### Task 1: Red Tests For Rolling-Spinning Config

**Files:**
- Modify: `tests/test_experiment_run_configs.py`
- Create: `configs/experiments/single_body_rolling_spinning.yaml`
- Modify: `src/mabd_reproduction/experiment_configs.py`

- [ ] **Step 1: Add imports and constants to the test file**

Add `load_rolling_spinning_config` and
`validate_rolling_spinning_config_against_matrix` to the import list in
`tests/test_experiment_run_configs.py`, then add:

```python
ROLLING_SPINNING_CONFIG_PATH = ROOT / "configs/experiments/single_body_rolling_spinning.yaml"
```

- [ ] **Step 2: Add the failing config test**

Add this test to `ExperimentRunConfigTests`:

```python
def test_rolling_spinning_config_is_machine_checkable(self) -> None:
    config = load_rolling_spinning_config(ROLLING_SPINNING_CONFIG_PATH)

    self.assertEqual(config.schema_version, 1)
    self.assertEqual(config.claim_id, "experiment.single_body.rolling_spinning")
    self.assertEqual(config.scene_id, "single_body_rolling_spinning")
    self.assertEqual(config.asset_ids, ("primitive_cylinder", "primitive_cube"))
    self.assertEqual(config.baseline_lane, "mabd_newton")
    self.assertEqual(
        config.required_missing_lanes,
        ("rbd_implicit_baseline", "rbd_explicit_baseline"),
    )
    self.assertEqual(config.report_status, EvidenceStatus.INCOMPLETE)
    self.assertEqual(config.performance.time_step_s, 0.01)
    self.assertEqual(config.performance.step_count, 10000)
    self.assertEqual(
        config.performance.paper_total_simulation_time_ms["vanilla_implicit_abd"],
        161.0,
    )
    self.assertEqual(
        config.performance.paper_total_simulation_time_ms["implicit_rbd"],
        44.0,
    )
    self.assertEqual(
        config.performance.paper_total_simulation_time_ms["explicit_rbd"],
        32.0,
    )
    self.assertEqual(
        config.performance.paper_total_simulation_time_ms["corotated_abd_with_polar"],
        34.0,
    )
    self.assertEqual(
        config.performance.paper_total_simulation_time_ms["corotated_abd_without_polar"],
        27.0,
    )
    self.assertEqual(config.performance.paper_hardware_context, "i7 CPU, single thread")
    self.assertIn("total_simulation_time_ms", config.thresholds)
    self.assertIn("energy_drift", config.thresholds)
    self.assertIn("linear_momentum_error", config.thresholds)
    self.assertIn("angular_momentum_error", config.thresholds)
```

- [ ] **Step 3: Add the failing matrix validation test**

Add:

```python
def test_rolling_spinning_config_matches_matrix(self) -> None:
    config = load_rolling_spinning_config(ROLLING_SPINNING_CONFIG_PATH)
    matrix = load_experiment_matrix(ROOT / "configs/experiments/paper_experiment_matrix.yaml")

    validate_rolling_spinning_config_against_matrix(config, matrix)
```

- [ ] **Step 4: Run red tests**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_run_configs.ExperimentRunConfigTests.test_rolling_spinning_config_is_machine_checkable tests.test_experiment_run_configs.ExperimentRunConfigTests.test_rolling_spinning_config_matches_matrix
```

Expected: FAIL because `load_rolling_spinning_config` is not implemented.

- [ ] **Step 5: Add the config file**

Create `configs/experiments/single_body_rolling_spinning.yaml`:

```yaml
schema_version: 1
claim_id: experiment.single_body.rolling_spinning
scene_id: single_body_rolling_spinning
source_lines:
  - /tmp/mabd-paper/source/sections/singleabd.tex:162-172
  - /tmp/mabd-paper/source/sections/experiment.tex:48-55
asset_ids:
  - primitive_cylinder
  - primitive_cube
baseline_lane: mabd_newton
required_missing_lanes:
  - rbd_implicit_baseline
  - rbd_explicit_baseline
paper_values:
  h: "10 ms for rolling performance figure; additional step sizes in single-body comparisons"
  duration: "10K steps for rolling cylinder performance figure"
  material_E: "1E9 Pa for cube single-body benchmark"
  density: "1E3 kg/m^3 for cube single-body benchmark"
performance:
  body: rolling_cylinder
  time_step_s: 0.01
  step_count: 10000
  paper_hardware_context: i7 CPU, single thread
  protocol_status: paper_text_timing_only_no_local_runtime_measurement
  paper_total_simulation_time_ms:
    vanilla_implicit_abd: 161.0
    implicit_rbd: 44.0
    explicit_rbd: 32.0
    corotated_abd_with_polar: 34.0
    corotated_abd_without_polar: 27.0
report:
  status: incomplete
  failure_reason: full paper claim requires paper-faithful rolling cylinder runtime benchmark plus implicit and explicit RBD baselines
  output_report: reports/experiment_matrix/single_body_rolling_spinning.json
  thresholds:
    total_simulation_time_ms: 0.0
    linear_momentum_error: 0.0
    angular_momentum_error: 0.0
    energy_drift: 0.0
```

- [ ] **Step 6: Implement the minimal config dataclasses and loader**

In `src/mabd_reproduction/experiment_configs.py`, add:

```python
@dataclass(frozen=True)
class RollingSpinningPerformanceConfig:
    body: str
    time_step_s: float
    step_count: int
    paper_hardware_context: str
    protocol_status: str
    paper_total_simulation_time_ms: dict[str, float]


@dataclass(frozen=True)
class RollingSpinningRunConfig:
    schema_version: int
    claim_id: str
    scene_id: str
    source_lines: tuple[str, ...]
    asset_ids: tuple[str, ...]
    baseline_lane: str
    required_missing_lanes: tuple[str, ...]
    paper_values: dict[str, Any]
    performance: RollingSpinningPerformanceConfig
    report_status: EvidenceStatus
    failure_reason: str
    output_report: str
    thresholds: dict[str, float]
```

Add constants:

```python
ROLLING_SPINNING_TIMING_KEYS = frozenset(
    {
        "vanilla_implicit_abd",
        "implicit_rbd",
        "explicit_rbd",
        "corotated_abd_with_polar",
        "corotated_abd_without_polar",
    }
)
ROLLING_SPINNING_REQUIRED_MISSING_LANES = (
    "rbd_implicit_baseline",
    "rbd_explicit_baseline",
)
```

Add:

```python
def _require_rolling_spinning_performance(data: dict[str, Any]) -> RollingSpinningPerformanceConfig:
    performance = _require_mapping(data, "performance")
    paper_timing = _require_float_mapping(performance, "paper_total_simulation_time_ms")
    if set(paper_timing) != ROLLING_SPINNING_TIMING_KEYS:
        raise ExperimentRunConfigError("paper_total_simulation_time_ms keys must match paper timing modes")
    if _require_str(performance, "body") != "rolling_cylinder":
        raise ExperimentRunConfigError("performance.body must be rolling_cylinder")
    if _require_str(performance, "protocol_status") != "paper_text_timing_only_no_local_runtime_measurement":
        raise ExperimentRunConfigError("performance.protocol_status must record no local runtime measurement")
    if _require_str(performance, "paper_hardware_context") != "i7 CPU, single thread":
        raise ExperimentRunConfigError("performance.paper_hardware_context must match the paper timing context")
    return RollingSpinningPerformanceConfig(
        body="rolling_cylinder",
        time_step_s=_require_positive_float(performance, "time_step_s"),
        step_count=_require_positive_int(performance, "step_count"),
        paper_hardware_context="i7 CPU, single thread",
        protocol_status="paper_text_timing_only_no_local_runtime_measurement",
        paper_total_simulation_time_ms=paper_timing,
    )
```

Add:

```python
def load_rolling_spinning_config(path: str | Path) -> RollingSpinningRunConfig:
    data = _read_mapping(Path(path))
    if not isinstance(data.get("schema_version"), int) or isinstance(data.get("schema_version"), bool):
        raise ExperimentRunConfigError("schema_version must be 1")
    if data.get("schema_version") != 1:
        raise ExperimentRunConfigError("schema_version must be 1")
    claim_id = _require_str(data, "claim_id")
    if claim_id != "experiment.single_body.rolling_spinning":
        raise ExperimentRunConfigError(
            "rolling-spinning config must target experiment.single_body.rolling_spinning"
        )
    report = _require_mapping(data, "report")
    try:
        status = EvidenceStatus(_require_str(report, "status"))
    except ValueError as exc:
        raise ExperimentRunConfigError("report.status is not a known EvidenceStatus") from exc
    if status == EvidenceStatus.PASSED:
        raise ExperimentRunConfigError("passed experiment configs require a dedicated evidence gate")
    return RollingSpinningRunConfig(
        schema_version=1,
        claim_id=claim_id,
        scene_id=_require_str(data, "scene_id"),
        source_lines=_require_str_tuple(data, "source_lines"),
        asset_ids=_require_str_tuple(data, "asset_ids"),
        baseline_lane=_require_str(data, "baseline_lane"),
        required_missing_lanes=_require_str_tuple(data, "required_missing_lanes"),
        paper_values=_require_mapping(data, "paper_values"),
        performance=_require_rolling_spinning_performance(data),
        report_status=status,
        failure_reason=_require_str(report, "failure_reason"),
        output_report=_require_str(report, "output_report"),
        thresholds=_require_float_mapping(report, "thresholds"),
    )
```

- [ ] **Step 7: Add matrix validation**

Add:

```python
def validate_rolling_spinning_config_against_matrix(
    config: RollingSpinningRunConfig,
    matrix: ExperimentMatrix,
) -> None:
    matches = [entry for entry in matrix.experiments if entry.claim_id == config.claim_id]
    if len(matches) != 1:
        raise ExperimentRunConfigError(f"{config.claim_id} must have exactly one matrix entry")
    entry = matches[0]
    if config.scene_id != entry.scene_id:
        raise ExperimentRunConfigError("scene_id must match experiment matrix")
    if config.source_lines != entry.source_lines:
        raise ExperimentRunConfigError("source_lines must match experiment matrix")
    if config.asset_ids != entry.asset_ids:
        raise ExperimentRunConfigError("asset_ids must match experiment matrix")
    if config.paper_values != entry.paper_values:
        raise ExperimentRunConfigError("paper_values must match experiment matrix")
    if config.output_report != entry.output_report:
        raise ExperimentRunConfigError("output_report must match experiment matrix")
    if config.baseline_lane not in entry.required_lanes:
        raise ExperimentRunConfigError("baseline_lane must be listed in required_lanes")
    if config.required_missing_lanes != ROLLING_SPINNING_REQUIRED_MISSING_LANES:
        raise ExperimentRunConfigError("required_missing_lanes must match rolling/spinning baseline blockers")
    for lane in config.required_missing_lanes:
        if lane not in entry.required_lanes:
            raise ExperimentRunConfigError("required_missing_lanes must be listed in required_lanes")
    for reason in ("rbd_baseline_adapter_missing", "benchmark_protocol_not_recorded"):
        if reason not in entry.blocking_reasons:
            raise ExperimentRunConfigError("matrix blocking_reasons must keep rolling/spinning blockers")
    if entry.reproduction_status != "blocked_by_baselines":
        raise ExperimentRunConfigError("matrix reproduction_status must remain blocked_by_baselines")
    for metric in entry.metrics:
        if metric not in config.thresholds:
            raise ExperimentRunConfigError("matrix metrics must be present in report.thresholds")
    if config.performance.time_step_s != 0.01:
        raise ExperimentRunConfigError("performance.time_step_s must match paper h = 0.01 sec")
    if config.performance.step_count != 10000:
        raise ExperimentRunConfigError("performance.step_count must match paper 10K steps")
```

Export these new names in `experiment_configs.__all__`:

```python
"ROLLING_SPINNING_REQUIRED_MISSING_LANES",
"ROLLING_SPINNING_TIMING_KEYS",
"RollingSpinningPerformanceConfig",
"RollingSpinningRunConfig",
"load_rolling_spinning_config",
"validate_rolling_spinning_config_against_matrix",
```

- [ ] **Step 8: Run green config tests**

Run the same command from Step 4. Expected: PASS.

### Task 2: Red Tests For Report Writer And Runner

**Files:**
- Modify: `tests/test_experiment_runner.py`
- Create: `src/mabd_reproduction/rolling_spinning_reports.py`
- Modify: `src/mabd_reproduction/experiment_runner.py`
- Modify: `scripts/run_experiment.py`

- [ ] **Step 1: Add config constant**

Add:

```python
ROLLING_SPINNING_CONFIG_PATH = ROOT / "configs/experiments/single_body_rolling_spinning.yaml"
```

- [ ] **Step 2: Add failing runner test**

Add:

```python
def test_run_rolling_spinning_protocol_writes_configured_report(self) -> None:
    from mabd_reproduction.experiment_runner import run_rolling_spinning_protocol

    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        result = run_rolling_spinning_protocol(
            config_path=ROLLING_SPINNING_CONFIG_PATH,
            matrix_path=MATRIX_PATH,
            output_root=root,
            source_commit="test-source",
            vendored_newton_commit="test-newton",
        )
        loaded = load_claim_report(result.report_path)

    self.assertEqual(
        result.report_path,
        root / "reports/experiment_matrix/single_body_rolling_spinning.json",
    )
    self.assertEqual(result.claim_id, "experiment.single_body.rolling_spinning")
    self.assertEqual(result.status, EvidenceStatus.INCOMPLETE)
    self.assertEqual(loaded.baseline_lane, "mabd_newton")
    self.assertEqual(loaded.solver_mode, "rolling_spinning_protocol_audit")
    self.assertEqual(loaded.backend, "report_protocol")
    self.assertFalse(loaded.observed["local_runtime_measured"])
    self.assertIn("rbd_implicit_baseline", loaded.observed["required_lanes_missing"])
    self.assertIn("rbd_explicit_baseline", loaded.observed["required_lanes_missing"])
    self.assertIn("rolling_cylinder_runtime_not_measured", loaded.observed["blocking_reasons"])
    self.assertEqual(
        loaded.observed["paper_metric_statuses"]["total_simulation_time_ms"],
        "paper_reference_recorded_no_local_runtime",
    )
    self.assertEqual(
        loaded.observed["paper_metric_statuses"]["linear_momentum_error"],
        "not_measured_by_phase73",
    )
    self.assertEqual(
        loaded.observed["paper_metric_statuses"]["angular_momentum_error"],
        "not_measured_by_phase73",
    )
    self.assertEqual(
        loaded.observed["paper_metric_statuses"]["energy_drift"],
        "not_measured_by_phase73",
    )
    self.assertEqual(loaded.timing_distribution["status"], "not_measured")
    self.assertFalse(loaded.timing_distribution["paper_comparable"])
    self.assertEqual(loaded.threshold["total_simulation_time_ms"], 0.0)
```

- [ ] **Step 3: Add failing explicit-output conflict test**

Add:

```python
def test_run_rolling_spinning_protocol_rejects_ambiguous_output_selection(self) -> None:
    from mabd_reproduction.experiment_runner import run_rolling_spinning_protocol

    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        with self.assertRaisesRegex(ValueError, "output_path and output_root"):
            run_rolling_spinning_protocol(
                config_path=ROLLING_SPINNING_CONFIG_PATH,
                matrix_path=MATRIX_PATH,
                output_path=root / "report.json",
                output_root=root,
                source_commit="test-source",
                vendored_newton_commit="test-newton",
            )
```

- [ ] **Step 4: Add failing CLI smoke test**

Add:

```python
def test_run_experiment_cli_runs_rolling_spinning_protocol_lane(self) -> None:
    import json
    import subprocess
    import sys

    with TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "rolling_spinning.json"
        result = subprocess.run(
            [
                sys.executable,
                "scripts/run_experiment.py",
                "--lane",
                "rolling_spinning_protocol",
                "--config",
                str(ROLLING_SPINNING_CONFIG_PATH),
                "--matrix",
                str(MATRIX_PATH),
                "--output",
                str(output_path),
                "--source-commit",
                "test-source",
                "--vendored-newton-commit",
                "test-newton",
            ],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    self.assertEqual(result.returncode, 0, msg=result.stderr)
    payload = json.loads(result.stdout)
    self.assertEqual(payload["claim_id"], "experiment.single_body.rolling_spinning")
    self.assertEqual(payload["status"], "incomplete")
    self.assertEqual(payload["baseline_lane"], "mabd_newton")
```

- [ ] **Step 5: Run red tests**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_runner.ExperimentRunnerTests.test_run_rolling_spinning_protocol_writes_configured_report tests.test_experiment_runner.ExperimentRunnerTests.test_run_rolling_spinning_protocol_rejects_ambiguous_output_selection tests.test_experiment_runner.ExperimentRunnerTests.test_run_experiment_cli_runs_rolling_spinning_protocol_lane
```

Expected: FAIL because `run_rolling_spinning_protocol` is not implemented.

- [ ] **Step 6: Add report writer**

Create `src/mabd_reproduction/rolling_spinning_reports.py`:

```python
"""Report lane for the rolling/spinning single-body experiment surface."""

from __future__ import annotations

from pathlib import Path

from .experiment_configs import RollingSpinningRunConfig
from .reporting import ClaimReport, write_claim_report


def write_rolling_spinning_protocol_report(
    path: str | Path,
    *,
    config: RollingSpinningRunConfig,
    source_commit: str,
    vendored_newton_commit: str,
    paper_source_version: str = "2603.08079v2",
) -> ClaimReport:
    expected = {
        "paper_claim_status": "requires rolling cylinder runtime benchmark and RBD baselines before pass",
        "source_lines": list(config.source_lines),
        "benchmark_body": config.performance.body,
        "benchmark_step_count": config.performance.step_count,
        "time_step_s": config.performance.time_step_s,
        "paper_hardware_context": config.performance.paper_hardware_context,
        "paper_total_simulation_time_ms": dict(config.performance.paper_total_simulation_time_ms),
        "required_metrics": list(config.thresholds),
        "full_experiment_claim_passed": False,
    }
    observed = {
        "local_runtime_measured": False,
        "protocol_status": config.performance.protocol_status,
        "required_lanes_missing": list(config.required_missing_lanes),
        "blocking_reasons": [
            "rbd_baseline_adapter_missing",
            "benchmark_protocol_not_recorded",
            "rolling_cylinder_runtime_not_measured",
        ],
        "paper_metric_statuses": {
            "total_simulation_time_ms": "paper_reference_recorded_no_local_runtime",
            "linear_momentum_error": "not_measured_by_phase73",
            "angular_momentum_error": "not_measured_by_phase73",
            "energy_drift": "not_measured_by_phase73",
        },
        "full_experiment_claim_passed": False,
    }
    report = ClaimReport(
        claim_id=config.claim_id,
        scene_id=config.scene_id,
        asset_hashes={
            "primitive_cylinder": "not_applicable_procedural",
            "primitive_cube": "not_applicable_procedural",
        },
        solver_mode="rolling_spinning_protocol_audit",
        backend="report_protocol",
        baseline_lane=config.baseline_lane,
        expected=expected,
        observed=observed,
        threshold=config.thresholds,
        unit="json_report",
        status=config.report_status,
        failure_reason=config.failure_reason,
        timing_distribution={
            "status": "not_measured",
            "paper_comparable": False,
        },
        raw_outputs={},
        plot_paths={},
        source_commit=source_commit,
        vendored_newton_commit=vendored_newton_commit,
        paper_source_version=paper_source_version,
    )
    write_claim_report(report, path)
    return report
```

- [ ] **Step 7: Add experiment runner function**

In `src/mabd_reproduction/experiment_runner.py`, import the new loader,
validator, and writer. Add:

```python
def run_rolling_spinning_protocol(
    *,
    config_path: str | Path,
    matrix_path: str | Path,
    source_commit: str,
    vendored_newton_commit: str,
    output_path: str | Path | None = None,
    output_root: str | Path | None = None,
    paper_source_version: str = "2603.08079v2",
) -> ExperimentRunResult:
    config = load_rolling_spinning_config(config_path)
    matrix = load_experiment_matrix(matrix_path)
    validate_rolling_spinning_config_against_matrix(config, matrix)
    if config.report_status != EvidenceStatus.INCOMPLETE:
        raise ValueError("Phase 73 rolling/spinning protocol runner requires incomplete report status")
    report_path = _resolve_output_path(
        config.output_report,
        output_path=output_path,
        output_root=output_root,
    )
    report = write_rolling_spinning_protocol_report(
        report_path,
        config=config,
        source_commit=source_commit,
        vendored_newton_commit=vendored_newton_commit,
        paper_source_version=paper_source_version,
    )
    return ExperimentRunResult(
        claim_id=report.claim_id,
        scene_id=report.scene_id,
        status=report.status,
        report_path=report_path,
        report=report,
    )
```

Add `run_rolling_spinning_protocol` to `experiment_runner.__all__`.

- [ ] **Step 8: Add CLI lane and exports**

In `scripts/run_experiment.py`, import `run_rolling_spinning_protocol`, add
`"rolling_spinning_protocol"` to `choices`, and add this branch before the
spinning-box fallback:

```python
elif args.lane == "rolling_spinning_protocol":
    result = run_rolling_spinning_protocol(
        config_path=Path(args.config),
        matrix_path=Path(args.matrix),
        output_path=Path(args.output) if args.output else None,
        output_root=Path(args.output_root) if args.output_root else None,
        source_commit=args.source_commit,
        vendored_newton_commit=args.vendored_newton_commit,
        paper_source_version=args.paper_source_version,
    )
```

Add `__all__ = ["write_rolling_spinning_protocol_report"]` to
`src/mabd_reproduction/rolling_spinning_reports.py`.

- [ ] **Step 9: Run green runner tests**

Run the same command from Step 5. Expected: PASS.

### Task 3: Generate Report And Documentation Gates

**Files:**
- Create: `reports/experiment_matrix/single_body_rolling_spinning.json`
- Modify: `docs/reference/claim-boundaries.md`
- Modify: `scripts/validate_docs.py`
- Modify: `tests/test_phase0_bootstrap.py`
- Create: `docs/records/2026-05-20-phase73-rolling-spinning-report-lane.md`

- [ ] **Step 1: Commit implementation before report generation**

Commit the config, source, CLI, tests, spec, and plan before generating the
committed report. This makes the report's `source_commit` name the actual code
that wrote it:

```bash
git add configs/experiments/single_body_rolling_spinning.yaml docs/superpowers/plans/2026-05-20-mabd-phase73-rolling-spinning-report-lane.md docs/superpowers/specs/2026-05-20-phase73-rolling-spinning-report-lane-design.md scripts/run_experiment.py src/mabd_reproduction/experiment_configs.py src/mabd_reproduction/experiment_runner.py src/mabd_reproduction/rolling_spinning_reports.py tests/test_experiment_run_configs.py tests/test_experiment_runner.py
git commit -m "feat: add rolling spinning protocol lane"
```

- [ ] **Step 2: Generate the report**

Run:

```bash
SOURCE_COMMIT=$(git rev-parse HEAD)
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/run_experiment.py --lane rolling_spinning_protocol --config configs/experiments/single_body_rolling_spinning.yaml --matrix configs/experiments/paper_experiment_matrix.yaml --output reports/experiment_matrix/single_body_rolling_spinning.json --source-commit "$SOURCE_COMMIT" --vendored-newton-commit 96713fa965463b69c229a4d30582c733ff3526bb
```

Expected stdout:

```json
{"baseline_lane": "mabd_newton", "claim_id": "experiment.single_body.rolling_spinning", "output_report": "reports/experiment_matrix/single_body_rolling_spinning.json", "scene_id": "single_body_rolling_spinning", "status": "incomplete"}
```

- [ ] **Step 3: Add claim-boundary text**

Append Phase 73 claim-boundary bullets to `docs/reference/claim-boundaries.md`
using the existing four-bullet shape:

```text
This repository contains Phase 73 rolling/spinning protocol report lane evidence ...
Phase 73 verifies ...
Phase 73 does not verify rolling-cylinder dynamics, local runtime timing,
implicit/explicit RBD baselines, spinning-box momentum or energy agreement,
comparative baseline results, any passed `experiment.*` claim, or full paper
reproduction.
Phase 73 rolling/spinning protocol report lane evidence must not be described as ...
```

- [ ] **Step 4: Add validator checks**

In `scripts/validate_docs.py`, add Phase 73 constants and a validator following
the Phase 70-72 pattern:

```python
PHASE73_ROLLING_SPINNING_REPORT_LANE_COMMIT = "the concrete git rev-parse HEAD value used in Step 2"
PHASE73_ROLLING_SPINNING_REPORT_SHA256 = "the concrete sha256sum value for reports/experiment_matrix/single_body_rolling_spinning.json"
ROLLING_SPINNING_REPORT_PATH = "reports/experiment_matrix/single_body_rolling_spinning.json"
```

Add all Phase 73 paths to `REQUIRED_PATHS`:

```python
"docs/superpowers/specs/2026-05-20-phase73-rolling-spinning-report-lane-design.md"
"docs/superpowers/plans/2026-05-20-mabd-phase73-rolling-spinning-report-lane.md"
"configs/experiments/single_body_rolling_spinning.yaml"
"reports/experiment_matrix/single_body_rolling_spinning.json"
"docs/records/2026-05-20-phase73-rolling-spinning-report-lane.md"
```

Implement `validate_phase73_record()` and call it from `main()`. The validator
should check stale marker strings, print-string phase list update, config-vs-matrix
validation, record snippets, boundary bullets, report SHA256, and load the
report with `load_claim_report`. It must require:

```python
report.claim_id == "experiment.single_body.rolling_spinning"
report.scene_id == "single_body_rolling_spinning"
report.status == EvidenceStatus.INCOMPLETE
report.solver_mode == "rolling_spinning_protocol_audit"
report.backend == "report_protocol"
report.baseline_lane == "mabd_newton"
report.asset_hashes == {
    "primitive_cylinder": "not_applicable_procedural",
    "primitive_cube": "not_applicable_procedural",
}
report.observed["local_runtime_measured"] is False
report.observed["full_experiment_claim_passed"] is False
report.expected["full_experiment_claim_passed"] is False
"rolling_cylinder_runtime_not_measured" in report.observed["blocking_reasons"]
"rbd_implicit_baseline" in report.observed["required_lanes_missing"]
"rbd_explicit_baseline" in report.observed["required_lanes_missing"]
report.expected["benchmark_step_count"] == 10000
report.expected["time_step_s"] == 0.01
report.expected["paper_hardware_context"] == "i7 CPU, single thread"
report.expected["paper_total_simulation_time_ms"] == {
    "vanilla_implicit_abd": 161.0,
    "implicit_rbd": 44.0,
    "explicit_rbd": 32.0,
    "corotated_abd_with_polar": 34.0,
    "corotated_abd_without_polar": 27.0,
}
report.observed["paper_metric_statuses"] == {
    "total_simulation_time_ms": "paper_reference_recorded_no_local_runtime",
    "linear_momentum_error": "not_measured_by_phase73",
    "angular_momentum_error": "not_measured_by_phase73",
    "energy_drift": "not_measured_by_phase73",
}
report.timing_distribution["status"] == "not_measured"
report.timing_distribution["paper_comparable"] is False
report.paper_source_version == "2603.08079v2"
report.vendored_newton_commit == VENDORED_NEWTON_COMMIT
report.source_commit == PHASE73_ROLLING_SPINNING_REPORT_LANE_COMMIT
```

Also require the claim-boundary bullets to contain the non-claims listed in the
claim-boundary step and require no `experiment.*` claim in `paper-claims.yaml`
changed away from `intended`.

- [ ] **Step 5: Add bootstrap test coverage**

In `tests/test_phase0_bootstrap.py`, add a focused test that calls the docs
validator or checks the new report fields through the same helper style used by
recent phases.

- [ ] **Step 6: Write Phase 73 record**

Create `docs/records/2026-05-20-phase73-rolling-spinning-report-lane.md` with:

```markdown
# Phase 73 Rolling-Spinning Report Lane

## Status

passed_for_rolling_spinning_report_lane

## Scope

- branch/worktree: `phase68-model-plane-report-lane`
- source commit: the concrete `git rev-parse HEAD` value used when generating
  the report in Step 2
- evidence record commit: the final evidence-record commit hash after the docs
  commit is created
- vendored Newton commit: `96713fa965463b69c229a4d30582c733ff3526bb`
- paper source version: `2603.08079v2`
- claim: `experiment.single_body.rolling_spinning`
- config: `configs/experiments/single_body_rolling_spinning.yaml`
- matrix: `configs/experiments/paper_experiment_matrix.yaml`
- report: `reports/experiment_matrix/single_body_rolling_spinning.json`
- report sha256: the concrete SHA256 of
  `reports/experiment_matrix/single_body_rolling_spinning.json`
- random seed: `not applicable`
- backend: `report_protocol`
- paper source lines:
  `/tmp/mabd-paper/source/sections/singleabd.tex:162-172`,
  `/tmp/mabd-paper/source/sections/experiment.tex:48-55`
- Python: `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python`
- reference environment:
  `/cpfs/user/zhuzihou/conda-managed/envs/physics-primitive-newton-py310`
- environment non-pollution:
  `mutates_reference_environment=false`, `uses_reference_python=false`,
  `uses_ambient_python=false`
- raw artifact policy: no generated videos, large raw logs, simulation run
  directories, or raw paper assets are committed.
- `paper-claims.yaml` is unchanged.

## Evidence

Phase 73 converts the missing rolling/spinning matrix output into an incomplete,
machine-checkable protocol report. It records the paper's rolling-cylinder
10K-step timing values and explicit blockers for runtime measurement plus
implicit/explicit RBD baseline adapters.

The report also records per-matrix-metric statuses. Only
`total_simulation_time_ms` has a paper reference recorded; no local runtime is
measured, and `linear_momentum_error`, `angular_momentum_error`, and
`energy_drift` are `not_measured_by_phase73`.

## Result Boundary

No `experiment.*` claim is passed. This record does not prove rolling-cylinder
dynamics, local runtime timing, implicit or explicit RBD baselines,
spinning-box momentum or energy agreement, comparative baseline results,
rendered output, or full paper reproduction.

## Commands

- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_run_configs tests.test_experiment_runner tests.test_phase0_bootstrap`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/env/readiness_check.py`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/env/clone_from_reference.py --dry-run`
- `PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"`
- `git diff --check`
```

Record the actual `git rev-parse HEAD` value used for the report and the report
SHA256 in the Phase 73 record.

### Task 4: Verification And Commit

**Files:**
- All files touched in Tasks 1-3

- [ ] **Step 1: Run focused tests**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_run_configs tests.test_experiment_runner tests.test_phase0_bootstrap
```

Expected: PASS.

- [ ] **Step 2: Run full validation gates**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/env/readiness_check.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/env/clone_from_reference.py --dry-run
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"
git diff --check
```

Expected: all pass.

- [ ] **Step 3: Commit**

Run:

```bash
git add docs/reference/claim-boundaries.md docs/records/2026-05-20-phase73-rolling-spinning-report-lane.md reports/experiment_matrix/single_body_rolling_spinning.json scripts/validate_docs.py tests/test_phase0_bootstrap.py
git commit -m "docs: record rolling spinning protocol lane"
```
