# Phase53 Heavy-Top Figure Curves Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a deterministic paper-figure reference-family digitization lane for the heavy-top experiment and consume it in the comparison report without claiming a passed experiment.

**Architecture:** Put rendering, calibration, color segmentation, and report creation in a focused `heavy_top_digitization` module. Add a small config entry for the figure-curve output report, a runner/CLI lane, and optional comparison-report consumption when the digitized report is supplied.

**Tech Stack:** Python 3.10, Pillow, NumPy, `pdftocairo`, vendored Newton path isolation, JSON `ClaimReport`, `unittest`.

---

### Task 1: RED Tests For Figure Reference Digitization

**Files:**
- Create: `tests/test_heavy_top_digitization.py`
- Test: `tests/test_heavy_top_digitization.py`

- [ ] **Step 1: Write the failing tests**

Create tests that specify the public API:

```python
from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np

from mabd_reproduction.experiment_configs import load_heavy_top_config
from mabd_reproduction.heavy_top_digitization import (
    HEAVY_TOP_FIGURE_PDF,
    HEAVY_TOP_FIGURE_PDF_SHA256,
    digitize_heavy_top_reference_curves,
    write_heavy_top_figure_curve_report,
)
from mabd_reproduction.reporting import EvidenceStatus, load_claim_report


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs/experiments/single_body_heavy_top.yaml"


class HeavyTopDigitizationTests(unittest.TestCase):
    def test_digitizes_reference_curves_from_recorded_pdf(self) -> None:
        curves = digitize_heavy_top_reference_curves()

        self.assertEqual(curves.source_pdf_path, HEAVY_TOP_FIGURE_PDF.as_posix())
        self.assertEqual(curves.source_pdf_sha256, HEAVY_TOP_FIGURE_PDF_SHA256)
        self.assertEqual(curves.render_dpi, 300)
        self.assertEqual(curves.rendered_size_px, (3179, 1924))
        self.assertEqual(curves.renderer_version, "pdftocairo 22.02.0")
        self.assertGreaterEqual(curves.sample_count, 51)
        self.assertTrue(curves.reference_precession.extraction_success)
        self.assertTrue(curves.reference_nutation.extraction_success)
        self.assertEqual(curves.reference_precession.unit, "rad/s")
        self.assertEqual(curves.reference_nutation.unit, "deg")
        self.assertAlmostEqual(curves.reference_precession.samples[0]["time_s"], 0.0)
        self.assertAlmostEqual(curves.reference_precession.samples[-1]["time_s"], 10.0)
        self.assertAlmostEqual(curves.reference_nutation.samples[0]["time_s"], 0.0)
        self.assertAlmostEqual(curves.reference_nutation.samples[-1]["time_s"], 10.0)
        self.assertTrue(
            np.all(
                np.isfinite(
                    [row["value"] for row in curves.reference_precession.samples]
                    + [row["value"] for row in curves.reference_nutation.samples]
                )
            )
        )
        self.assertGreater(curves.reference_precession.sample_coverage, 0.80)
        self.assertGreater(curves.reference_nutation.sample_coverage, 0.80)
        self.assertEqual(curves.non_reference_curve_status, "color_family_counts_only")

    def test_writes_incomplete_claim_report_without_vendoring_raw_assets(self) -> None:
        config = load_heavy_top_config(CONFIG_PATH)
        with TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "figure_curves.json"
            report = write_heavy_top_figure_curve_report(
                output,
                config=config,
                source_commit="test-source",
                vendored_newton_commit="test-newton",
            )
            loaded = load_claim_report(output)

        self.assertEqual(report.status, EvidenceStatus.INCOMPLETE)
        self.assertEqual(loaded.baseline_lane, "paper_figure_digitization")
        self.assertEqual(loaded.solver_mode, "heavy_top_paper_figure_digitization")
        self.assertEqual(loaded.backend, "pdftocairo_pillow")
        self.assertFalse(loaded.observed["full_experiment_claim_passed"])
        self.assertEqual(loaded.observed["lane_status"], "reference_curves_digitized")
        self.assertTrue(loaded.observed["reference_curve_available"])
        self.assertEqual(loaded.observed["source_pdf_sha256"], HEAVY_TOP_FIGURE_PDF_SHA256)
        self.assertNotIn(".png", str(loaded.raw_outputs))
        self.assertNotIn("base64", str(loaded.observed))
        self.assertIn("not_authors_raw_data", loaded.observed["limitations"])
        self.assertIn("no_blue_orange_line_style_split", loaded.observed["limitations"])
```

- [ ] **Step 2: Run tests and verify RED**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_heavy_top_digitization
```

Expected: FAIL because `mabd_reproduction.heavy_top_digitization` does not exist.

### Task 2: GREEN Digitizer And Report Writer

**Files:**
- Create: `src/mabd_reproduction/heavy_top_digitization.py`
- Modify: `src/mabd_reproduction/experiment_configs.py`
- Modify: `configs/experiments/single_body_heavy_top.yaml`
- Test: `tests/test_heavy_top_digitization.py`

- [ ] **Step 1: Add config field**

Add:

```yaml
figure_curves:
  output_report: reports/experiment_matrix/single_body_heavy_top_figure_curves.json
```

Add `figure_curve_output_report: str` to `HeavyTopRunConfig`, and parse it from
`figure_curves.output_report`.

- [ ] **Step 2: Implement digitization dataclasses and helpers**

Create immutable dataclasses:

```python
@dataclass(frozen=True)
class HeavyTopDigitizedCurve:
    metric: str
    unit: str
    axis_range: tuple[float, float]
    plot_box_px: tuple[int, int, int, int]
    extraction_success: bool
    sample_coverage: float
    samples: tuple[dict[str, float], ...]


@dataclass(frozen=True)
class HeavyTopFigureCurves:
    source_pdf_path: str
    source_pdf_sha256: str
    render_command: tuple[str, ...]
    renderer_version: str
    render_dpi: int
    rendered_size_px: tuple[int, int]
    sample_count: int
    reference_precession: HeavyTopDigitizedCurve
    reference_nutation: HeavyTopDigitizedCurve
    non_reference_curve_status: str
    non_reference_color_counts: dict[str, int]
```

Use constants:

```python
HEAVY_TOP_FIGURE_PDF = Path("/tmp/mabd-paper/source/images/spinning_top/spinning_top.pdf")
HEAVY_TOP_FIGURE_PDF_SHA256 = "c8f5e206415b9feb3578ee32aa3b7284e2695bdd84eeb0200f3b4aa01cf3422d"
RENDER_DPI = 300
EXPECTED_RENDERED_SIZE_PX = (3179, 1924)
PRECESSION_BOX_PX = (1508, 72, 3154, 672)
NUTATION_BOX_PX = (1508, 1010, 3154, 1710)
REFERENCE_RGB = (32, 72, 48)
```

Render to a `TemporaryDirectory` with:

```python
subprocess.run(
    ["pdftocairo", "-png", "-singlefile", "-r", str(RENDER_DPI), str(pdf_path), str(output_prefix)],
    check=True,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
)
```

For each sampled `time_s`, map to pixel `x`, scan the plot box for pixels
within an RGB squared distance threshold from `REFERENCE_RGB`, choose the median
matched `y`, and map it to the metric axis range. Interpolate across at most
two missing neighboring samples; fail extraction if coverage is below 0.80.

- [ ] **Step 3: Implement report writer**

`write_heavy_top_figure_curve_report(...)` writes a compact `ClaimReport` with:

- `baseline_lane="paper_figure_digitization"`;
- `solver_mode="heavy_top_paper_figure_digitization"`;
- `backend="pdftocairo_pillow"`;
- `status=EvidenceStatus.INCOMPLETE`;
- `observed.reference_curve_available = True`;
- finite reference samples under `observed.reference_curves`.
- `observed.limitations` containing `not_authors_raw_data` and
  `no_blue_orange_line_style_split`.
- no committed raster pixels, base64 image data, SVG/PDF dumps, or raw paper
  assets.

- [ ] **Step 4: Run tests and verify GREEN**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_heavy_top_digitization tests.test_experiment_run_configs
```

Expected: PASS.

### Task 3: RED Tests For Runner, CLI, And Comparison Consumption

**Files:**
- Modify: `tests/test_experiment_runner.py`
- Modify: `tests/test_heavy_top_comparison_reports.py`

- [ ] **Step 1: Add runner and CLI expectations**

Add tests that:

- `run_heavy_top_figure_curves(...)` writes the configured figure report;
- `scripts/run_experiment.py --lane heavy_top_figure_curves` writes the same lane;
- summary `baseline_lane` is `paper_figure_digitization`.

- [ ] **Step 2: Add comparison expectations**

Extend heavy-top comparison tests so, when `figure_curve_report_path` is
provided:

```python
self.assertEqual(
    loaded.observed["paper_metric_statuses"]["nutation_angle_error"]["status"],
    "paper_figure_digitized_reference_available",
)
self.assertEqual(
    loaded.observed["missing_paper_metrics"],
    ["nutation_angle_error:paper_figure_digitized_curve_agreement_not_passed"],
)
self.assertIn(
    "raw_heavy_top_reference_curve_data_missing",
    loaded.observed["blocking_reasons"],
)
self.assertIn(
    "heavy_top_digitized_figure_curve_agreement_not_passed",
    loaded.observed["blocking_reasons"],
)
self.assertIn("paper_figure_curves", loaded.observed["input_report_provenance"])
```

Add a negative test mutating the figure report status or removing
`reference_curve_available`; expected comparison keeps
`nutation_angle_error:paper_reference_curve_missing`.

- [ ] **Step 3: Run tests and verify RED**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_runner tests.test_heavy_top_comparison_reports
```

Expected: FAIL because runner/CLI/comparison arguments do not exist.

### Task 4: GREEN Runner, CLI, And Comparison Integration

**Files:**
- Modify: `src/mabd_reproduction/experiment_runner.py`
- Modify: `scripts/run_experiment.py`
- Modify: `src/mabd_reproduction/comparison_reports.py`
- Test: `tests/test_experiment_runner.py`
- Test: `tests/test_heavy_top_comparison_reports.py`

- [ ] **Step 1: Add runner and CLI lane**

Add `run_heavy_top_figure_curves(...)` using `config.figure_curve_output_report`.
Add CLI choice `heavy_top_figure_curves`.

- [ ] **Step 2: Add optional comparison input**

Add `figure_curve_report_path: str | Path | None = None` to
`write_heavy_top_comparison_report(...)` and `run_heavy_top_comparison(...)`.
Add CLI option `--figure-report`.

When the figure report is valid, add its provenance and update the nutation
status/missing metric/blockers as specified in Task 3. Keep
`raw_heavy_top_reference_curve_data_missing` because digitized figure samples
are not authors' raw simulation data. Keep the comparison status `incomplete`
and `full_experiment_claim_passed = False`.

- [ ] **Step 3: Run targeted tests**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_heavy_top_digitization tests.test_heavy_top_comparison_reports tests.test_experiment_runner
```

Expected: PASS.

### Task 5: Regenerate Reports And Documentation

**Files:**
- Create: `reports/experiment_matrix/single_body_heavy_top_figure_curves.json`
- Modify: `reports/experiment_matrix/single_body_heavy_top_comparison.json`
- Modify: `reports/experiment_matrix/single_body_heavy_top_rk4_reference.json`
- Modify: `reports/experiment_matrix/single_body_heavy_top_mabd_newton.json`
- Modify: `docs/reference/claim-boundaries.md`
- Modify: `docs/reference/paper-claims.yaml` only if blocker names change
- Create: `docs/records/2026-05-18-phase53-heavy-top-figure-curves.md`
- Modify: `scripts/validate_docs.py`

- [ ] **Step 1: Regenerate lane reports**

Use the final implementation commit as `--source-commit` and Newton commit
`96713fa965463b69c229a4d30582c733ff3526bb`.

Run the new figure lane, existing RK4/MABD lanes, then comparison with
`--figure-report`.

- [ ] **Step 2: Update docs and validator**

Record:

- new report sha256;
- source PDF checksum and renderer command;
- Poppler renderer version and `3179 x 1924` rendered size;
- reference sample counts and coverage;
- comparison metric-status transition;
- retained raw-author-data blocker and non-claims.

Update `validate_docs.py` to require Phase53 report, record, source hash,
comparison provenance, and preserved incomplete claim boundaries.

- [ ] **Step 3: Run final validation**

Run:

```bash
/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"
git diff --check
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
```

Expected: all pass.
