# Phase 66 Spinning-Box Figure Agreement Diagnostics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a bounded digitized-paper-figure diagnostic to the spinning-box comparison report without passing the spinning-box paper claim.

**Architecture:** Reuse the existing comparison-report pattern from T-handle: validate an optional figure report, record provenance and sample counts only when the input is valid, then emit diagnostic-only best-fit errors. Runner and CLI changes are pure pass-through plumbing; docs validation records the new incomplete evidence state.

**Tech Stack:** Python 3.10, `unittest`, local JSON claim reports, canonical isolated environment `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310`, `PYTHONPATH=src:vendor/newton`.

---

## Files

- Modify `tests/test_spinning_box_comparison.py`: red tests for valid and invalid figure report consumption.
- Modify `src/mabd_reproduction/comparison_reports.py`: optional figure report validation, provenance, sample counts, and diagnostic-only endpoint errors.
- Modify `tests/test_experiment_runner.py`: red tests for runner and CLI `--figure-report` pass-through.
- Modify `src/mabd_reproduction/experiment_runner.py`: pass `figure_curve_report_path` into the report writer.
- Modify `scripts/run_experiment.py`: pass `--figure-report` for `spinning_box_comparison`.
- Modify `reports/experiment_matrix/single_body_spinning_box_comparison.json`: regenerated incomplete report with Phase65 figure diagnostics.
- Modify `docs/reference/claim-boundaries.md`: Phase66 boundary bullets.
- Modify `scripts/validate_docs.py`: Phase66 spec, plan, record, and report gates.
- Modify `tests/test_phase0_bootstrap.py`: validator positive/negative tests for Phase66.
- Create `docs/records/2026-05-19-phase66-spinning-box-figure-agreement-diagnostics.md`: dated evidence record.

### Task 1: Comparison Report Red Tests

**Files:**
- Modify: `tests/test_spinning_box_comparison.py`

- [ ] **Step 1: Add the figure-report writer import inside the new helper**

Add this helper method inside `SpinningBoxComparisonTests`, below `_write_lane_reports`:

```python
    def _write_figure_report(self, tmpdir: str) -> Path:
        from mabd_reproduction.spinning_box_digitization import (
            write_spinning_box_figure_curve_report,
        )

        config = load_spinning_box_config(CONFIG_PATH)
        figure_path = Path(tmpdir) / "figure_curves.json"
        write_spinning_box_figure_curve_report(
            figure_path,
            config=config,
            source_commit="test-source",
            vendored_newton_commit="test-newton",
        )
        return figure_path
```

- [ ] **Step 2: Add valid figure diagnostic test**

Append this test before the existing overflow test:

```python
    def test_spinning_box_comparison_consumes_valid_figure_curve_report(self) -> None:
        from mabd_reproduction.comparison_reports import write_spinning_box_comparison_report

        config = load_spinning_box_config(CONFIG_PATH)
        with TemporaryDirectory() as tmpdir:
            mabd_path, rbd_path = self._write_lane_reports(tmpdir)
            figure_path = self._write_figure_report(tmpdir)
            output_path = Path(tmpdir) / "comparison.json"

            write_spinning_box_comparison_report(
                output_path,
                config=config,
                mabd_report_path=mabd_path,
                rbd_report_path=rbd_path,
                figure_curve_report_path=figure_path,
                source_commit="test-source",
                vendored_newton_commit="test-newton",
            )
            loaded = load_claim_report(output_path)

        self.assertTrue(loaded.observed["digitized_figure_reference_available"])
        self.assertTrue(loaded.observed["digitized_figure_curve_agreement_available"])
        self.assertFalse(loaded.observed["digitized_figure_curve_agreement_passed"])
        self.assertIn(
            "spinning_box_digitized_figure_curve_agreement_not_passed",
            loaded.observed["blocking_reasons"],
        )
        self.assertIn("paper_figure_curves", loaded.observed["input_report_provenance"])
        self.assertEqual(
            loaded.raw_outputs["figure_curve_report"],
            figure_path.as_posix(),
        )
        self.assertEqual(
            loaded.observed["digitized_figure_reference_samples"][
                "linear_momentum_color_families"
            ]["blue"],
            6,
        )
        diagnostics = loaded.observed["digitized_figure_curve_agreement_diagnostics"]
        linear_mabd = diagnostics["linear_momentum"]["mabd_newton"]
        self.assertEqual(linear_mabd["status"], "diagnostic_available_not_pass_gate")
        self.assertEqual(linear_mabd["lane_value_source"], "linear_momentum_error")
        self.assertEqual(linear_mabd["figure_time_s"], 10.0)
        self.assertIn(linear_mabd["best_color_family"], ["blue", "brown", "gray", "green", "orange"])
        self.assertEqual(
            linear_mabd["best_color_family_claim_status"],
            "numeric_best_fit_not_legend_identity",
        )
        self.assertEqual(
            linear_mabd["agreement_claim_status"],
            "diagnostic_only_not_curve_agreement",
        )
        self.assertIn("blue", linear_mabd["all_color_family_errors"])
        self.assertIn("angular_momentum", diagnostics)
        self.assertIn("rbd_implicit_baseline", diagnostics["angular_momentum"])
        self.assertEqual(loaded.status, EvidenceStatus.INCOMPLETE)
```

- [ ] **Step 3: Add invalid figure report test**

Append this test after the valid figure diagnostic test:

```python
    def test_spinning_box_comparison_ignores_invalid_figure_curve_report(self) -> None:
        import json

        from mabd_reproduction.comparison_reports import write_spinning_box_comparison_report

        config = load_spinning_box_config(CONFIG_PATH)
        with TemporaryDirectory() as tmpdir:
            mabd_path, rbd_path = self._write_lane_reports(tmpdir)
            figure_path = self._write_figure_report(tmpdir)
            figure_data = json.loads(figure_path.read_text(encoding="utf-8"))
            figure_data["observed"]["curve_agreement_status"] = "passed"
            figure_path.write_text(json.dumps(figure_data), encoding="utf-8")
            output_path = Path(tmpdir) / "comparison.json"

            write_spinning_box_comparison_report(
                output_path,
                config=config,
                mabd_report_path=mabd_path,
                rbd_report_path=rbd_path,
                figure_curve_report_path=figure_path,
                source_commit="test-source",
                vendored_newton_commit="test-newton",
            )
            loaded = load_claim_report(output_path)

        self.assertFalse(loaded.observed["digitized_figure_reference_available"])
        self.assertEqual(loaded.observed["digitized_figure_reference_samples"], {})
        self.assertFalse(loaded.observed["digitized_figure_curve_agreement_available"])
        self.assertFalse(loaded.observed["digitized_figure_curve_agreement_passed"])
        self.assertNotIn("digitized_figure_curve_agreement_diagnostics", loaded.observed)
        self.assertNotIn("paper_figure_curves", loaded.observed["input_report_provenance"])
        self.assertNotIn("figure_curve_report", loaded.raw_outputs)
        self.assertNotIn(
            "spinning_box_digitized_figure_curve_agreement_not_passed",
            loaded.observed["blocking_reasons"],
        )
```

- [ ] **Step 4: Run focused red test**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_spinning_box_comparison
```

Expected: FAIL because `write_spinning_box_comparison_report()` does not accept `figure_curve_report_path`.

### Task 2: Comparison Report Implementation

**Files:**
- Modify: `src/mabd_reproduction/comparison_reports.py`

- [ ] **Step 1: Add spinning-box figure constants**

Add these constants after the T-handle figure constants:

```python
SPINNING_BOX_FIGURE_BASELINE_LANE = "paper_figure_digitization"
SPINNING_BOX_FIGURE_SOLVER_MODE = "spinning_box_paper_figure_curve_digitization"
SPINNING_BOX_FIGURE_BACKEND = "paper_pdf_digitization"
SPINNING_BOX_FIGURE_COLOR_FAMILIES = ("blue", "brown", "gray", "green", "orange")
SPINNING_BOX_FIGURE_TIME_S = 10.0
SPINNING_BOX_FIGURE_METRICS = {
    "linear_momentum": {
        "curve_group": "linear_momentum_curves",
        "lane_metric": "linear_momentum_error",
    },
    "angular_momentum": {
        "curve_group": "angular_momentum_curves",
        "lane_metric": "angular_momentum_error",
    },
}
```

- [ ] **Step 2: Add spinning-box figure validation helpers**

Add these helpers after `_valid_t_handle_figure_report_or_none`:

```python
def _finite_spinning_box_figure_curve_samples(report: ClaimReport) -> bool:
    for metric_config in SPINNING_BOX_FIGURE_METRICS.values():
        curves = report.observed.get(metric_config["curve_group"])
        if not isinstance(curves, dict):
            return False
        for color_family in SPINNING_BOX_FIGURE_COLOR_FAMILIES:
            curve = curves.get(color_family)
            if not isinstance(curve, dict):
                return False
            if curve.get("curve_identity_status") != "color_family_not_legend_entry":
                return False
            samples = curve.get("samples")
            if not isinstance(samples, list) or not samples:
                return False
            finite_times: list[float] = []
            for sample in samples:
                if not isinstance(sample, dict):
                    return False
                time_s = _finite_scalar(sample.get("time_s"))
                value = _finite_scalar(sample.get("value"))
                if time_s is None or value is None:
                    return False
                finite_times.append(time_s)
            if finite_times[-1] != SPINNING_BOX_FIGURE_TIME_S:
                return False
            if any(rhs <= lhs for lhs, rhs in zip(finite_times, finite_times[1:])):
                return False
    return True


def _valid_spinning_box_figure_report_or_none(
    path: str | Path | None,
    *,
    config: SpinningBoxRunConfig,
) -> ClaimReport | None:
    if path is None:
        return None
    try:
        report = load_claim_report(path)
    except (OSError, ValueError):
        return None
    if report.claim_id != config.claim_id or report.scene_id != config.scene_id:
        return None
    if report.baseline_lane != SPINNING_BOX_FIGURE_BASELINE_LANE:
        return None
    if report.solver_mode != SPINNING_BOX_FIGURE_SOLVER_MODE:
        return None
    if report.backend != SPINNING_BOX_FIGURE_BACKEND:
        return None
    if report.status != EvidenceStatus.INCOMPLETE:
        return None
    if report.observed.get("full_experiment_claim_passed") is not False:
        return None
    if report.observed.get("color_family_curve_available") is not True:
        return None
    if report.observed.get("paper_reference_legend_identity_available") is not False:
        return None
    if report.observed.get("curve_identity_status") != "color_family_not_legend_entry":
        return None
    if report.observed.get("curve_agreement_status") != "not_evaluated":
        return None
    if not _finite_spinning_box_figure_curve_samples(report):
        return None
    return report
```

- [ ] **Step 3: Add sample-count and endpoint diagnostic helpers**

Add these helpers near the existing `_t_handle_digitized_figure_agreement_diagnostics` helpers:

```python
def _spinning_box_figure_sample_counts(report: ClaimReport) -> dict[str, dict[str, int]]:
    result: dict[str, dict[str, int]] = {}
    for output_key, report_key in (
        ("linear_momentum_color_families", "linear_momentum_curves"),
        ("angular_momentum_color_families", "angular_momentum_curves"),
    ):
        curves = report.observed[report_key]
        result[output_key] = {
            str(color_family): len(curve["samples"])
            for color_family, curve in curves.items()
            if isinstance(curve, dict) and isinstance(curve.get("samples"), list)
        }
    return result


def _spinning_box_figure_endpoint_value(
    figure_report: ClaimReport,
    *,
    curve_group: str,
    color_family: str,
) -> float | None:
    curves = figure_report.observed.get(curve_group)
    if not isinstance(curves, dict):
        return None
    curve = curves.get(color_family)
    if not isinstance(curve, dict):
        return None
    samples = curve.get("samples")
    if not isinstance(samples, list):
        return None
    for sample in reversed(samples):
        if not isinstance(sample, dict):
            continue
        time_s = _finite_scalar(sample.get("time_s"))
        value = _finite_scalar(sample.get("value"))
        if time_s == SPINNING_BOX_FIGURE_TIME_S and value is not None:
            return value
    return None


def _spinning_box_figure_metric_diagnostic(
    report: ClaimReport,
    figure_report: ClaimReport,
    *,
    lane: str,
    metric: str,
) -> dict[str, Any]:
    metric_config = SPINNING_BOX_FIGURE_METRICS[metric]
    lane_metric = metric_config["lane_metric"]
    lane_value = _finite_scalar(report.observed.get(lane_metric))
    all_color_errors: dict[str, dict[str, float | None]] = {}
    for color_family in SPINNING_BOX_FIGURE_COLOR_FAMILIES:
        figure_value = _spinning_box_figure_endpoint_value(
            figure_report,
            curve_group=metric_config["curve_group"],
            color_family=color_family,
        )
        signed_error = (
            _finite_difference(lane_value, figure_value)
            if lane_value is not None and figure_value is not None
            else None
        )
        all_color_errors[color_family] = {
            "figure_value": figure_value,
            "signed_error": signed_error,
            "abs_error": abs(signed_error) if signed_error is not None else None,
        }
    finite_color_errors = {
        color_family: errors
        for color_family, errors in all_color_errors.items()
        if _finite_scalar(errors["abs_error"]) is not None
    }
    if lane_value is None or not finite_color_errors:
        return {
            "status": "missing_finite_endpoint_values",
            "lane": lane,
            "metric": metric,
            "lane_value": lane_value,
            "lane_value_source": lane_metric,
            "figure_time_s": SPINNING_BOX_FIGURE_TIME_S,
            "best_color_family": None,
            "best_abs_error": None,
            "best_signed_error": None,
            "best_color_family_claim_status": "numeric_best_fit_not_legend_identity",
            "agreement_claim_status": "diagnostic_only_not_curve_agreement",
            "all_color_family_errors": all_color_errors,
        }

    best_color_family = min(
        finite_color_errors,
        key=lambda color_family: float(finite_color_errors[color_family]["abs_error"]),
    )
    best_errors = finite_color_errors[best_color_family]
    return {
        "status": "diagnostic_available_not_pass_gate",
        "lane": lane,
        "metric": metric,
        "lane_value": lane_value,
        "lane_value_source": lane_metric,
        "figure_time_s": SPINNING_BOX_FIGURE_TIME_S,
        "best_color_family": best_color_family,
        "best_abs_error": best_errors["abs_error"],
        "best_signed_error": best_errors["signed_error"],
        "best_color_family_claim_status": "numeric_best_fit_not_legend_identity",
        "agreement_claim_status": "diagnostic_only_not_curve_agreement",
        "all_color_family_errors": all_color_errors,
    }


def _spinning_box_digitized_figure_agreement_diagnostics(
    *,
    mabd_report: ClaimReport,
    rbd_report: ClaimReport,
    figure_report: ClaimReport,
) -> dict[str, dict[str, dict[str, Any]]]:
    reports = {
        "mabd_newton": mabd_report,
        "rbd_implicit_baseline": rbd_report,
    }
    return {
        metric: {
            lane: _spinning_box_figure_metric_diagnostic(
                report,
                figure_report,
                lane=lane,
                metric=metric,
            )
            for lane, report in reports.items()
        }
        for metric in SPINNING_BOX_FIGURE_METRICS
    }
```

- [ ] **Step 4: Wire the optional figure report into the writer**

Change the `write_spinning_box_comparison_report` signature:

```python
    vendored_newton_commit: str,
    figure_curve_report_path: str | Path | None = None,
    paper_source_version: str = "2603.08079v2",
) -> ClaimReport:
```

After loading `mabd_report` and `rbd_report`, add:

```python
    figure_report = _valid_spinning_box_figure_report_or_none(
        figure_curve_report_path,
        config=config,
    )
    figure_reference_available = figure_report is not None
```

Before creating `ClaimReport`, add:

```python
    input_report_provenance = {
        "mabd_newton": _physical_lane_provenance(mabd_report_path, mabd_report),
        "rbd_implicit_baseline": _physical_lane_provenance(rbd_report_path, rbd_report),
    }
    raw_outputs = {
        "mabd_report": Path(mabd_report_path).as_posix(),
        "rbd_report": Path(rbd_report_path).as_posix(),
    }
    figure_sample_counts: dict[str, dict[str, int]] = {}
    figure_agreement_diagnostics: dict[str, dict[str, dict[str, Any]]] = {}
    if figure_reference_available and figure_report is not None and figure_curve_report_path is not None:
        blocking_reasons.append("spinning_box_digitized_figure_curve_agreement_not_passed")
        input_report_provenance["paper_figure_curves"] = _physical_lane_provenance(
            figure_curve_report_path,
            figure_report,
        )
        raw_outputs["figure_curve_report"] = Path(figure_curve_report_path).as_posix()
        figure_sample_counts = _spinning_box_figure_sample_counts(figure_report)
        figure_agreement_diagnostics = _spinning_box_digitized_figure_agreement_diagnostics(
            mabd_report=mabd_report,
            rbd_report=rbd_report,
            figure_report=figure_report,
        )
```

At the top of the `observed` dict, add:

```python
            "full_experiment_claim_passed": False,
            "digitized_figure_reference_available": figure_reference_available,
            "digitized_figure_reference_samples": figure_sample_counts,
            "digitized_figure_curve_agreement_available": bool(figure_agreement_diagnostics),
            "digitized_figure_curve_agreement_passed": False,
            "input_report_provenance": input_report_provenance,
```

After constructing the report or before the report construction, include diagnostics only when present:

```python
    if figure_agreement_diagnostics:
        report.observed["digitized_figure_curve_agreement_diagnostics"] = (
            figure_agreement_diagnostics
        )
```

Replace the literal `raw_outputs={...}` with:

```python
        raw_outputs=raw_outputs,
```

- [ ] **Step 5: Run focused comparison tests**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_spinning_box_comparison
```

Expected: PASS.

- [ ] **Step 6: Commit comparison implementation**

Run:

```bash
git add tests/test_spinning_box_comparison.py src/mabd_reproduction/comparison_reports.py
git commit -m "feat: add spinning-box figure agreement diagnostics"
```

### Task 3: Runner And CLI Pass-Through

**Files:**
- Modify: `tests/test_experiment_runner.py`
- Modify: `src/mabd_reproduction/experiment_runner.py`
- Modify: `scripts/run_experiment.py`

- [ ] **Step 1: Add runner red assertion**

In `test_run_spinning_box_comparison_writes_explicit_output_report`, create a figure report and pass it through:

```python
            from mabd_reproduction.spinning_box_digitization import (
                write_spinning_box_figure_curve_report,
            )
            from mabd_reproduction.experiment_configs import load_spinning_box_config

            config = load_spinning_box_config(CONFIG_PATH)
            figure_path = Path(tmpdir) / "figure_curves.json"
            write_spinning_box_figure_curve_report(
                figure_path,
                config=config,
                source_commit="test-source",
                vendored_newton_commit="test-newton",
            )
```

Pass:

```python
                figure_curve_report_path=figure_path,
```

Assert:

```python
        self.assertTrue(loaded.observed["digitized_figure_reference_available"])
        self.assertEqual(loaded.raw_outputs["figure_curve_report"], figure_path.as_posix())
```

- [ ] **Step 2: Add CLI red assertion**

In `test_run_experiment_cli_writes_spinning_box_comparison_report`, create a figure report before running the subprocess:

```python
            from mabd_reproduction.experiment_configs import load_spinning_box_config
            from mabd_reproduction.spinning_box_digitization import (
                write_spinning_box_figure_curve_report,
            )

            config = load_spinning_box_config(CONFIG_PATH)
            figure_path = Path(tmpdir) / "figure_curves.json"
            write_spinning_box_figure_curve_report(
                figure_path,
                config=config,
                source_commit="test-source",
                vendored_newton_commit="test-newton",
            )
```

Add these CLI args:

```python
                    "--figure-report",
                    str(figure_path),
```

Assert after loading:

```python
            self.assertTrue(loaded.observed["digitized_figure_reference_available"])
            self.assertEqual(loaded.raw_outputs["figure_curve_report"], figure_path.as_posix())
```

- [ ] **Step 3: Run runner red tests**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_runner.ExperimentRunnerTests.test_run_spinning_box_comparison_writes_explicit_output_report tests.test_experiment_runner.ExperimentRunnerTests.test_run_experiment_cli_writes_spinning_box_comparison_report
```

Expected: FAIL because `run_spinning_box_comparison()` does not accept `figure_curve_report_path`, or because the CLI does not pass `--figure-report` into that lane.

- [ ] **Step 4: Implement runner pass-through**

Change `run_spinning_box_comparison` in `src/mabd_reproduction/experiment_runner.py` to accept:

```python
    figure_curve_report_path: str | Path | None = None,
```

Pass it into `write_spinning_box_comparison_report`:

```python
        figure_curve_report_path=figure_curve_report_path,
```

- [ ] **Step 5: Implement CLI pass-through**

In `scripts/run_experiment.py`, add this argument to the `spinning_box_comparison` call:

```python
                figure_curve_report_path=Path(args.figure_report) if args.figure_report else None,
```

- [ ] **Step 6: Run runner tests**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_runner.ExperimentRunnerTests.test_run_spinning_box_comparison_writes_explicit_output_report tests.test_experiment_runner.ExperimentRunnerTests.test_run_experiment_cli_writes_spinning_box_comparison_report
```

Expected: PASS.

- [ ] **Step 7: Commit runner/CLI implementation**

Run:

```bash
git add tests/test_experiment_runner.py src/mabd_reproduction/experiment_runner.py scripts/run_experiment.py
git commit -m "feat: pass spinning-box figure report through runner"
```

### Task 4: Generate The Updated Comparison Report

**Files:**
- Modify: `reports/experiment_matrix/single_body_spinning_box_comparison.json`

- [ ] **Step 1: Regenerate the report against the current code commit**

Run:

```bash
SOURCE_COMMIT=$(git rev-parse HEAD)
VENDORED_NEWTON_COMMIT=$(git -C vendor/newton rev-parse HEAD)
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/run_experiment.py \
  --lane spinning_box_comparison \
  --config configs/experiments/single_body_spinning_box.yaml \
  --matrix configs/experiments/paper_experiment_matrix.yaml \
  --mabd-report reports/experiment_matrix/single_body_spinning_box.json \
  --rbd-report reports/experiment_matrix/single_body_spinning_box_rbd_baseline.json \
  --figure-report reports/experiment_matrix/single_body_spinning_box_figure_curves.json \
  --output reports/experiment_matrix/single_body_spinning_box_comparison.json \
  --source-commit "$SOURCE_COMMIT" \
  --vendored-newton-commit "$VENDORED_NEWTON_COMMIT"
```

Expected: command exits 0 and prints JSON summary with `status` equal to `incomplete`.

- [ ] **Step 2: Inspect the regenerated report**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python - <<'PY'
from pathlib import Path
from mabd_reproduction.reporting import load_claim_report

report = load_claim_report(Path("reports/experiment_matrix/single_body_spinning_box_comparison.json"))
print(report.status.value)
print(report.observed["digitized_figure_reference_available"])
print(report.observed["digitized_figure_curve_agreement_available"])
print(report.observed["digitized_figure_curve_agreement_passed"])
print("paper_figure_curves" in report.observed["input_report_provenance"])
print(report.observed["blocking_reasons"][-1])
PY
```

Expected output:

```text
incomplete
True
True
False
True
spinning_box_digitized_figure_curve_agreement_not_passed
```

### Task 5: Docs, Validator, And Evidence Record

**Files:**
- Modify: `docs/reference/claim-boundaries.md`
- Modify: `scripts/validate_docs.py`
- Modify: `tests/test_phase0_bootstrap.py`
- Create: `docs/records/2026-05-19-phase66-spinning-box-figure-agreement-diagnostics.md`

- [ ] **Step 1: Update claim boundaries**

Add a Phase66 bullet group to `docs/reference/claim-boundaries.md`:

```markdown
- Phase 66 may state that the spinning-box comparison report consumes the
  Phase65 paper-figure digitization and records endpoint best-fit diagnostics.
- Phase 66 must state that digitized figure agreement remains unpassed and that
  color families are not paper legend-entry identities.
- Phase 66 must not claim the spinning-box experiment is reproduced, passed, or
  paper-faithful.
```

- [ ] **Step 2: Add validator constants and path gates**

In `scripts/validate_docs.py`, add constants:

```python
PHASE66_SPEC = ROOT / "docs/superpowers/specs/2026-05-19-phase66-spinning-box-figure-agreement-diagnostics-design.md"
PHASE66_PLAN = ROOT / "docs/superpowers/plans/2026-05-19-mabd-phase66-spinning-box-figure-agreement-diagnostics.md"
PHASE66_RECORD = ROOT / "docs/records/2026-05-19-phase66-spinning-box-figure-agreement-diagnostics.md"
PHASE66_SPINNING_BOX_COMPARISON = ROOT / "reports/experiment_matrix/single_body_spinning_box_comparison.json"
```

Add these paths to `REQUIRED_PATHS`:

```python
PHASE66_SPEC,
PHASE66_PLAN,
PHASE66_RECORD,
```

Add a `validate_phase66_record()` function that loads the report and enforces:

```python
report.claim_id == "experiment.single_body.spinning_box"
report.status.value == "incomplete"
report.baseline_lane == "spinning_box_comparison_protocol"
report.observed["full_experiment_claim_passed"] is False
report.observed["digitized_figure_reference_available"] is True
report.observed["digitized_figure_curve_agreement_available"] is True
report.observed["digitized_figure_curve_agreement_passed"] is False
"paper_figure_curves" in report.observed["input_report_provenance"]
"spinning_box_digitized_figure_curve_agreement_not_passed" in report.observed["blocking_reasons"]
```

Also require the Phase66 record to mention:

```text
digitized_figure_curve_agreement_passed=false
experiment.single_body.spinning_box remains intended
no experiment claim passed
```

Call `validate_phase66_record()` from `main()`.

- [ ] **Step 3: Add bootstrap validator tests**

In `tests/test_phase0_bootstrap.py`, add a positive test that calls the validator function and a negative test that copies the comparison report, flips `digitized_figure_curve_agreement_passed` to `true`, patches the validator path to the copy, and expects `SystemExit`.

Use the existing Phase64/Phase65 validator test style in the same file.

- [ ] **Step 4: Create Phase66 record**

Create `docs/records/2026-05-19-phase66-spinning-box-figure-agreement-diagnostics.md` with:

```markdown
# Phase 66 Spinning-Box Figure Agreement Diagnostics Record

Date: 2026-05-19

## Scope

Phase66 connects the Phase65 spinning-box paper-figure color-family digitization
to the spinning-box comparison report as diagnostic-only endpoint best-fit
errors.

## Evidence

- Report:
  `reports/experiment_matrix/single_body_spinning_box_comparison.json`
- Figure input:
  `reports/experiment_matrix/single_body_spinning_box_figure_curves.json`
- `digitized_figure_reference_available=true`
- `digitized_figure_curve_agreement_available=true`
- `digitized_figure_curve_agreement_passed=false`
- Blocking reason:
  `spinning_box_digitized_figure_curve_agreement_not_passed`

## Claim Boundary

`experiment.single_body.spinning_box remains intended`. This record passes no
`experiment.*` claim. The diagnostics compare lane scalar momentum errors with
digitized paper-figure color-family endpoint values, but the color families are
not paper legend-entry identities and the curve agreement gate is not passed.

No `experiment.*` claim is passed.
```

- [ ] **Step 5: Run focused docs tests**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_phase0_bootstrap
```

Expected: PASS.

- [ ] **Step 6: Commit docs, validator, and report**

Run:

```bash
git add docs/reference/claim-boundaries.md scripts/validate_docs.py tests/test_phase0_bootstrap.py docs/records/2026-05-19-phase66-spinning-box-figure-agreement-diagnostics.md reports/experiment_matrix/single_body_spinning_box_comparison.json
git commit -m "docs: record Phase66 spinning-box figure agreement diagnostics"
```

### Task 6: Full Verification And Push

**Files:**
- No source edits unless verification exposes a concrete defect.

- [ ] **Step 1: Validate docs and provenance**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
```

Expected: PASS.

- [ ] **Step 2: Run full tests**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
```

Expected: PASS.

- [ ] **Step 3: Run lint and whitespace checks**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .
git diff --check
```

Expected: both commands PASS.

- [ ] **Step 4: Confirm claim status stayed bounded**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python - <<'PY'
import yaml
from pathlib import Path

claims = yaml.safe_load(Path("docs/reference/paper-claims.yaml").read_text(encoding="utf-8"))
for claim in claims["claims"]:
    if claim["id"].startswith("experiment."):
        assert claim["reproduction_status"] == "intended", claim["id"]
print("all experiment claims remain intended")
PY
```

Expected output:

```text
all experiment claims remain intended
```

- [ ] **Step 5: Merge and push**

Run:

```bash
git status --short
git checkout main
git merge --no-ff phase66-spinning-box-figure-agreement
git push origin main
```

Expected: push succeeds, and `main` contains the Phase66 commits.
