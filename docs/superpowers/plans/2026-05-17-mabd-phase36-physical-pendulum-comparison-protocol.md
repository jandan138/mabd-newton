# Phase 36 Physical Pendulum Comparison Protocol Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a bounded physical-pendulum comparison report protocol for the existing analytic, M-ABD development, and RBD diagnostic lanes.

**Architecture:** The physical-pendulum config owns the comparison output contract. The existing `comparison_reports.py` module loads and validates lane `ClaimReport` files, computes report-only diagnostics, and writes an incomplete comparison `ClaimReport`. Runner and CLI changes mirror the existing spinning-box comparison path while requiring explicit input report files.

**Tech Stack:** Python 3.10, NumPy, PyYAML, `unittest`, existing `ClaimReport` JSON schema, ruff.

---

### Task 1: Config Contract

**Files:**
- Modify: `configs/experiments/single_body_physical_pendulum.yaml`
- Modify: `src/mabd_reproduction/experiment_configs.py`
- Modify: `tests/test_experiment_run_configs.py`

- [ ] **Step 1: Write the failing config test**

Extend `test_physical_pendulum_config_is_machine_checkable`:

```python
self.assertEqual(
    config.comparison.output_report,
    "reports/experiment_matrix/single_body_physical_pendulum_comparison.json",
)
self.assertEqual(
    config.comparison.required_lanes,
    ("mabd_newton", "analytic_reference", "rbd_implicit_baseline"),
)
self.assertEqual(
    config.comparison.diagnostic_lanes,
    ("physical_pendulum_mabd_development_diagnostic",),
)
self.assertEqual(
    config.comparison.required_metrics,
    ("pendulum_angle_error", "joint_force_error", "phase_drift"),
)
self.assertIn("max_mabd_rbd_abs_angle_delta_rad", config.comparison.thresholds)
```

Add a malformed config test:

```python
def test_physical_pendulum_config_rejects_comparison_output_reuse(self) -> None:
    source = yaml.safe_load(PHYSICAL_PENDULUM_CONFIG_PATH.read_text(encoding="utf-8"))
    source["comparison"]["output_report"] = source["rbd_baseline"]["output_report"]
    with TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "single_body_physical_pendulum.yaml"
        path.write_text(yaml.safe_dump(source), encoding="utf-8")
        config = load_physical_pendulum_config(path)
        matrix = load_experiment_matrix(ROOT / "configs/experiments/paper_experiment_matrix.yaml")
        with self.assertRaisesRegex(ExperimentRunConfigError, "comparison.output_report"):
            validate_physical_pendulum_config_against_matrix(config, matrix)
```

Add malformed config tests for comparison lane and metric drift:

```python
def test_physical_pendulum_config_rejects_comparison_missing_mabd_lane(self) -> None:
    source = yaml.safe_load(PHYSICAL_PENDULUM_CONFIG_PATH.read_text(encoding="utf-8"))
    source["comparison"]["required_lanes"] = ["analytic_reference", "rbd_implicit_baseline"]
    with TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "single_body_physical_pendulum.yaml"
        path.write_text(yaml.safe_dump(source), encoding="utf-8")
        with self.assertRaisesRegex(ExperimentRunConfigError, "comparison.required_lanes"):
            load_physical_pendulum_config(path)

def test_physical_pendulum_config_rejects_comparison_bad_diagnostic_lane(self) -> None:
    source = yaml.safe_load(PHYSICAL_PENDULUM_CONFIG_PATH.read_text(encoding="utf-8"))
    source["comparison"]["diagnostic_lanes"] = ["mabd_newton"]
    with TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "single_body_physical_pendulum.yaml"
        path.write_text(yaml.safe_dump(source), encoding="utf-8")
        with self.assertRaisesRegex(ExperimentRunConfigError, "comparison.diagnostic_lanes"):
            load_physical_pendulum_config(path)

def test_physical_pendulum_config_rejects_comparison_missing_metric(self) -> None:
    source = yaml.safe_load(PHYSICAL_PENDULUM_CONFIG_PATH.read_text(encoding="utf-8"))
    source["comparison"]["required_metrics"] = ["pendulum_angle_error", "phase_drift"]
    with TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "single_body_physical_pendulum.yaml"
        path.write_text(yaml.safe_dump(source), encoding="utf-8")
        with self.assertRaisesRegex(ExperimentRunConfigError, "comparison.required_metrics"):
            load_physical_pendulum_config(path)

def test_physical_pendulum_config_rejects_comparison_missing_threshold(self) -> None:
    source = yaml.safe_load(PHYSICAL_PENDULUM_CONFIG_PATH.read_text(encoding="utf-8"))
    source["comparison"]["thresholds"] = {}
    with TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "single_body_physical_pendulum.yaml"
        path.write_text(yaml.safe_dump(source), encoding="utf-8")
        with self.assertRaisesRegex(ExperimentRunConfigError, "comparison.thresholds"):
            load_physical_pendulum_config(path)
```

- [ ] **Step 2: Run RED**

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_run_configs
```

Expected: failure because `PhysicalPendulumRunConfig` has no `comparison`
attribute.

- [ ] **Step 3: Implement config support**

Add:

```python
@dataclass(frozen=True)
class PhysicalPendulumComparisonConfig:
    output_report: str
    required_lanes: tuple[str, ...]
    diagnostic_lanes: tuple[str, ...]
    required_metrics: tuple[str, ...]
    thresholds: dict[str, float]
```

Add required keys:

```python
PHYSICAL_PENDULUM_COMPARISON_THRESHOLD_KEYS = frozenset(
    {"max_mabd_rbd_abs_angle_delta_rad"}
)
PHYSICAL_PENDULUM_COMPARISON_REQUIRED_LANES = (
    "mabd_newton",
    "analytic_reference",
    "rbd_implicit_baseline",
)
PHYSICAL_PENDULUM_COMPARISON_DIAGNOSTIC_LANES = (
    "physical_pendulum_mabd_development_diagnostic",
)
PHYSICAL_PENDULUM_COMPARISON_REQUIRED_METRICS = (
    "pendulum_angle_error",
    "joint_force_error",
    "phase_drift",
)
```

Parse the new YAML block:

```yaml
comparison:
  output_report: reports/experiment_matrix/single_body_physical_pendulum_comparison.json
  required_lanes:
    - mabd_newton
    - analytic_reference
    - rbd_implicit_baseline
  diagnostic_lanes:
    - physical_pendulum_mabd_development_diagnostic
  required_metrics:
    - pendulum_angle_error
    - joint_force_error
    - phase_drift
  thresholds:
    max_mabd_rbd_abs_angle_delta_rad: 2.0
```

Update `validate_physical_pendulum_config_against_matrix` to require the
comparison output under the matrix stem, ending in `.json`, and distinct from
analytic, M-ABD, and RBD report paths.

Also require `set(config.comparison.required_lanes) == set(entry.required_lanes)`
so the machine-checkable invariant follows the matrix even if display order
changes later.

- [ ] **Step 4: Run GREEN**

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_run_configs
```

Expected: config tests pass.

### Task 2: Comparison Writer

**Files:**
- Modify: `src/mabd_reproduction/comparison_reports.py`
- Create: `tests/test_physical_pendulum_comparison_reports.py`

- [ ] **Step 1: Write failing comparison tests**

Create input reports in a temporary directory:

```python
config = load_physical_pendulum_config(PHYSICAL_PENDULUM_CONFIG_PATH)
write_physical_pendulum_analytic_reference_report(analytic_path, config=config, source_commit="test-source", vendored_newton_commit="test-newton")
write_physical_pendulum_mabd_development_report(mabd_path, config=config, source_commit="test-source", vendored_newton_commit="test-newton")
write_physical_pendulum_rbd_baseline_report(rbd_path, config=config, source_commit="test-source", vendored_newton_commit="test-newton")
```

Assert the comparison output:

```python
report = write_physical_pendulum_comparison_report(
    output_path,
    config=config,
    analytic_report_path=analytic_path,
    mabd_report_path=mabd_path,
    rbd_report_path=rbd_path,
    source_commit="test-source",
    vendored_newton_commit="test-newton",
)
self.assertEqual(report.baseline_lane, "physical_pendulum_comparison_protocol")
self.assertEqual(report.status, EvidenceStatus.INCOMPLETE)
self.assertFalse(report.observed["full_experiment_claim_passed"])
self.assertEqual(report.observed["missing_required_lanes"], ["mabd_newton"])
self.assertIn("joint_force_waveform_agreement_missing", report.observed["blocking_reasons"])
self.assertIn("max_mabd_rbd_abs_angle_delta_rad", report.observed)
self.assertEqual(report.observed["matched_sample_count"], 5)
self.assertEqual(report.observed["unmatched_mabd_samples"], [])
self.assertEqual(report.observed["unmatched_rbd_samples"], [])
self.assertEqual(
    report.observed["paper_metric_statuses"]["joint_force_error"]["status"],
    "missing_waveform_not_max_magnitude",
)
self.assertIn("input_report_provenance", report.observed)
self.assertEqual(
    report.observed["input_report_provenance"]["rbd_implicit_baseline"]["source_commit"],
    "test-source",
)
self.assertGreater(len(report.observed["angle_sample_differences_rad"]), 0)
```

Add rejection tests that mutate each input report `claim_id`, `scene_id`,
`baseline_lane`, `solver_mode`, and `backend`, asserting `ValueError` and that
no output report is written. For example:

```python
with self.assertRaisesRegex(ValueError, "analytic_reference report must have baseline_lane"):
    write_physical_pendulum_comparison_report(...)
self.assertFalse(output_path.exists())
```

Add sample coverage tests:

```python
def test_physical_pendulum_comparison_blocks_zero_matched_samples(self) -> None:
    rbd_payload = json.loads(rbd_path.read_text(encoding="utf-8"))
    for row in rbd_payload["observed"]["angle_samples_rad"]:
        row["step"] += 1000
    rbd_path.write_text(json.dumps(rbd_payload), encoding="utf-8")
    report = write_physical_pendulum_comparison_report(...)
    self.assertEqual(report.observed["matched_sample_count"], 0)
    self.assertIn("angle_sample_alignment_missing", report.observed["blocking_reasons"])

def test_physical_pendulum_comparison_blocks_nonfinite_samples_without_nan_json(self) -> None:
    mabd_payload = json.loads(mabd_path.read_text(encoding="utf-8"))
    mabd_payload["observed"]["angle_samples_rad"][1]["angle_rad"] = float("nan")
    mabd_path.write_text(json.dumps(mabd_payload), encoding="utf-8")
    report = write_physical_pendulum_comparison_report(...)
    payload = output_path.read_text(encoding="utf-8")
    self.assertNotIn("NaN", payload)
    self.assertNotIn("Infinity", payload)
    self.assertIn("angle_sample_nonfinite", report.observed["blocking_reasons"])
```

- [ ] **Step 2: Run RED**

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_physical_pendulum_comparison_reports
```

Expected: import fails for `write_physical_pendulum_comparison_report`.

- [ ] **Step 3: Implement writer**

Add constants:

```python
PHYSICAL_PENDULUM_REQUIRED_METRICS = (
    "pendulum_angle_error",
    "joint_force_error",
    "phase_drift",
)
```

Add lane validation:

```python
def _require_physical_pendulum_lane_report(path, *, config, lane, solver_mode, backend):
    report = load_claim_report(path)
    if report.claim_id != config.claim_id:
        raise ValueError(f"{lane} report claim_id must be {config.claim_id}")
    if report.scene_id != config.scene_id:
        raise ValueError(f"{lane} report scene_id must be {config.scene_id}")
    if report.baseline_lane != lane:
        raise ValueError(f"{lane} report must have baseline_lane={lane}")
    if report.solver_mode != solver_mode:
        raise ValueError(f"{lane} report solver_mode must be {solver_mode}")
    if report.backend != backend:
        raise ValueError(f"{lane} report backend must be {backend}")
    if report.status != EvidenceStatus.INCOMPLETE:
        raise ValueError(f"{lane} report status must be incomplete")
    if report.asset_hashes.get("physical_pendulum_procedural") != "not_applicable_procedural":
        raise ValueError(f"{lane} report must use physical_pendulum_procedural")
    if report.observed.get("full_experiment_claim_passed") is not False:
        raise ValueError(f"{lane} report must not claim full experiment pass")
    return report
```

Compute matched angle sample differences by aligning M-ABD and RBD sample rows
on `(step, time_s)`. Record sample counts and unmatched rows. If there are no
matched rows, add `angle_sample_alignment_missing` to blockers. If any matched
sample has non-finite scalar values, omit that row from differences and add
`angle_sample_nonfinite` to blockers. Do not serialize `NaN` or `Infinity`.

Record `input_report_provenance` for each input lane:

```python
{
    "path": Path(path).as_posix(),
    "sha256": _sha256_file(path),
    "source_commit": report.source_commit,
    "vendored_newton_commit": report.vendored_newton_commit,
    "solver_mode": report.solver_mode,
    "backend": report.backend,
    "baseline_lane": report.baseline_lane,
    "status": report.status.value,
}
```

Record `paper_metric_statuses` using canonical matrix metric names:

```python
{
    "pendulum_angle_error": {
        "status": "diagnostic_available",
        "mabd_field": "max_abs_angle_error_rad",
        "rbd_field": "max_abs_angle_error_rad",
    },
    "phase_drift": {
        "status": "rbd_diagnostic_only",
        "rbd_field": "max_phase_drift_rad",
        "mabd_field": None,
    },
    "joint_force_error": {
        "status": "missing_waveform_not_max_magnitude",
        "rbd_diagnostic_field": "max_joint_force_magnitude_n",
    },
}
```

- [ ] **Step 4: Run GREEN**

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_physical_pendulum_comparison_reports
```

Expected: comparison report tests pass.

### Task 3: Runner And CLI

**Files:**
- Modify: `src/mabd_reproduction/experiment_runner.py`
- Modify: `scripts/run_experiment.py`
- Modify: `tests/test_experiment_runner.py`

- [ ] **Step 1: Write failing runner and CLI tests**

Add `test_run_physical_pendulum_comparison_writes_report`:

```python
result = run_physical_pendulum_comparison(
    config_path=PHYSICAL_PENDULUM_CONFIG_PATH,
    matrix_path=MATRIX_PATH,
    analytic_report_path=analytic_path,
    mabd_report_path=mabd_path,
    rbd_report_path=rbd_path,
    output_path=output_path,
    source_commit="test-source",
    vendored_newton_commit="test-newton",
)
self.assertEqual(result.claim_id, "experiment.single_body.physical_pendulum")
self.assertEqual(result.status, EvidenceStatus.INCOMPLETE)
self.assertEqual(result.report.baseline_lane, "physical_pendulum_comparison_protocol")
```

Add CLI tests:

```python
cmd = [
    sys.executable,
    "scripts/run_experiment.py",
    "--lane",
    "physical_pendulum_comparison",
    "--config",
    str(PHYSICAL_PENDULUM_CONFIG_PATH),
    "--matrix",
    str(MATRIX_PATH),
    "--analytic-report",
    str(analytic_path),
    "--mabd-report",
    str(mabd_path),
    "--rbd-report",
    str(rbd_path),
    "--output",
    str(output_path),
    "--source-commit",
    "cli-source",
    "--vendored-newton-commit",
    "cli-newton",
]
```

Assert the JSON summary `baseline_lane` is
`physical_pendulum_comparison_protocol`.

The parser must add:

```python
parser.add_argument(
    "--analytic-report",
    help="Existing analytic reference report for physical-pendulum comparison lane.",
)
```

Add a missing-input test that omits `--analytic-report` and expects:

```python
self.assertIn(
    "physical_pendulum_comparison requires --analytic-report, --mabd-report, and --rbd-report",
    result.stderr,
)
```

- [ ] **Step 2: Run RED**

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_runner
```

Expected: missing runner or CLI lane support.

- [ ] **Step 3: Implement runner and CLI**

Add `run_physical_pendulum_comparison` to `experiment_runner.py`. Require all
three report paths, use `config.comparison.output_report` via
`_resolve_output_path`, and call `write_physical_pendulum_comparison_report`.

In `scripts/run_experiment.py`, add `physical_pendulum_comparison` to the
allowed lane list and dispatch it with `args.analytic_report`,
`args.mabd_report`, and `args.rbd_report`.

- [ ] **Step 4: Run GREEN**

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_runner tests.test_physical_pendulum_comparison_reports
```

Expected: focused tests pass.

### Task 4: Report Artifact And Provenance Gates

**Files:**
- Modify: `docs/reference/claim-boundaries.md`
- Modify: `scripts/validate_docs.py`
- Modify: `tests/test_phase0_bootstrap.py`
- Create: `docs/records/2026-05-17-phase36-physical-pendulum-comparison-protocol.md`
- Create: `reports/experiment_matrix/single_body_physical_pendulum_analytic_reference.json`
- Create: `reports/experiment_matrix/single_body_physical_pendulum_comparison.json`

- [ ] **Step 1: Write failing provenance tests**

Add bootstrap assertions that:

```python
text = (ROOT / "docs/reference/claim-boundaries.md").read_text()
self.assertIn("Phase 36 verifies a physical-pendulum comparison protocol", text)
self.assertIn("Phase 36 does not verify the physical-pendulum paper experiment", text)
report = load_claim_report(ROOT / "reports/experiment_matrix/single_body_physical_pendulum_comparison.json")
self.assertEqual(report.baseline_lane, "physical_pendulum_comparison_protocol")
self.assertEqual(report.status, EvidenceStatus.INCOMPLETE)
self.assertFalse(report.observed["full_experiment_claim_passed"])
```

Update `scripts/validate_docs.py` to require the new paths and fail unless the
comparison report has:

```python
baseline_lane == "physical_pendulum_comparison_protocol"
status.value == "incomplete"
observed["missing_required_lanes"] == ["mabd_newton"]
"joint_force_waveform_agreement_missing" in observed["blocking_reasons"]
observed["input_report_provenance"]["rbd_implicit_baseline"]["vendored_newton_commit"] == "96713fa965463b69c229a4d30582c733ff3526bb"
observed["matched_sample_count"] > 0
observed["paper_metric_statuses"]["joint_force_error"]["status"] == "missing_waveform_not_max_magnitude"
```

Also require:

```python
analytic.source_commit not in PLACEHOLDER_SOURCE_COMMITS
comparison.source_commit not in PLACEHOLDER_SOURCE_COMMITS
analytic.vendored_newton_commit == "96713fa965463b69c229a4d30582c733ff3526bb"
comparison.vendored_newton_commit == "96713fa965463b69c229a4d30582c733ff3526bb"
phase36_record contains f"analytic report source_commit: `{analytic.source_commit}`"
phase36_record contains f"comparison report source_commit: `{comparison.source_commit}`"
paper_claims["experiment.single_body.physical_pendulum"].reproduction_status == "intended"
```

Add a Forbidden Claims validator check for:

```text
Phase 36 physical-pendulum comparison protocol is not a passed
physical-pendulum experiment, M-ABD lane pass, joint-force waveform agreement,
paper geometry result, paper timing result, or any passed `experiment.*` claim.
```

- [ ] **Step 2: Run RED**

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_phase0_bootstrap
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
```

Expected: missing Phase 36 docs/report artifact failures.

- [ ] **Step 3: Generate reports and add docs**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/run_experiment.py --lane analytic_reference --config configs/experiments/single_body_physical_pendulum.yaml --matrix configs/experiments/paper_experiment_matrix.yaml --output reports/experiment_matrix/single_body_physical_pendulum_analytic_reference.json --source-commit <implementation-commit> --vendored-newton-commit 96713fa965463b69c229a4d30582c733ff3526bb
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/run_experiment.py --lane physical_pendulum_comparison --config configs/experiments/single_body_physical_pendulum.yaml --matrix configs/experiments/paper_experiment_matrix.yaml --analytic-report reports/experiment_matrix/single_body_physical_pendulum_analytic_reference.json --mabd-report reports/experiment_matrix/single_body_physical_pendulum_mabd_development.json --rbd-report reports/experiment_matrix/single_body_physical_pendulum_rbd_baseline.json --output reports/experiment_matrix/single_body_physical_pendulum_comparison.json --source-commit <implementation-commit> --vendored-newton-commit 96713fa965463b69c229a4d30582c733ff3526bb
```

Add a Phase 36 record that lists the committed reports, metrics, TDD evidence,
and non-claims.

- [ ] **Step 4: Run GREEN**

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_phase0_bootstrap
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
```

Expected: provenance tests pass.

### Task 5: Final Verification

**Files:**
- All changed files

- [ ] **Step 1: Run full gates**

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/env/readiness_check.py
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"
git diff --check
```

Expected: all commands pass and Newton imports from this worktree's
`vendor/newton`.

- [ ] **Step 2: Commit and integrate**

Commit implementation/docs/reports in small commits. Merge back to `main` only
after all gates pass, then push `main` to origin.
