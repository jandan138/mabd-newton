# Phase58 T-Handle Figure Curves Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a deterministic T-handle paper-figure color-family digitization lane and consume it in the T-handle comparison report without claiming a passed experiment.

**Architecture:** Mirror the proven heavy-top Phase53 pattern with a focused `t_handle_digitization` module, a `figure_curves` config block, a runner/CLI lane, optional comparison-report consumption, and bounded docs/validator evidence. The digitizer renders the recorded PDF with Poppler, samples calibrated plot boxes by RGB color family, and writes compact numeric JSON only.

**Tech Stack:** Python 3.10, Pillow, NumPy, Poppler `pdftocairo`, existing YAML config loader, existing `ClaimReport`, `unittest`, vendored Newton import isolation.

---

### Task 1: RED Tests For T-Handle Figure Digitization

**Files:**
- Create: `tests/test_t_handle_digitization.py`
- Modify: `tests/test_experiment_run_configs.py`

- [ ] **Step 1: Write failing digitization tests**

Create `tests/test_t_handle_digitization.py`:

```python
from __future__ import annotations

import unittest
from math import isfinite
from pathlib import Path
from tempfile import TemporaryDirectory

from mabd_reproduction.experiment_configs import load_t_handle_config
from mabd_reproduction.reporting import EvidenceStatus, load_claim_report
from mabd_reproduction.t_handle_digitization import (
    EXPECTED_RENDERED_SIZE_PX,
    RENDER_DPI,
    T_HANDLE_FIGURE_PDF,
    T_HANDLE_FIGURE_PDF_SHA256,
    digitize_t_handle_figure_curves,
    write_t_handle_figure_curve_report,
)


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs/experiments/single_body_t_handle.yaml"


class THandleDigitizationTests(unittest.TestCase):
    def test_digitizes_color_families_from_recorded_pdf(self) -> None:
        curves = digitize_t_handle_figure_curves(sample_count=51)

        self.assertEqual(curves.source_pdf_path, T_HANDLE_FIGURE_PDF.as_posix())
        self.assertEqual(curves.source_pdf_sha256, T_HANDLE_FIGURE_PDF_SHA256)
        self.assertEqual(curves.render_dpi, RENDER_DPI)
        self.assertEqual(curves.rendered_size_px, EXPECTED_RENDERED_SIZE_PX)
        self.assertEqual(curves.renderer_version, "pdftocairo 22.02.0")
        self.assertEqual(curves.sample_count, 51)
        self.assertEqual(curves.figure_curve_scope, "color_family_digitization_only")
        self.assertEqual(set(curves.angular_velocity_curves), {"blue", "orange", "green"})
        self.assertEqual(set(curves.energy_loss_curves), {"blue", "orange", "green"})
        for curve in (*curves.angular_velocity_curves.values(), *curves.energy_loss_curves.values()):
            self.assertTrue(curve.extraction_success)
            self.assertGreater(curve.sample_coverage, 0.80)
            self.assertEqual(curve.curve_identity_status, "color_family_not_legend_entry")
            self.assertAlmostEqual(curve.samples[0]["time_s"], 0.0)
            self.assertAlmostEqual(curve.samples[-1]["time_s"], 100.0)
            self.assertTrue(all(isfinite(sample["value"]) for sample in curve.samples))
        self.assertTrue(
            all(-2.0 <= sample["value"] <= 6.0 for sample in curves.angular_velocity_curves["green"].samples)
        )
        self.assertTrue(
            all(0.0 <= sample["value"] <= 0.25 for sample in curves.energy_loss_curves["blue"].samples)
        )

    def test_writes_incomplete_report_without_vendoring_raw_assets(self) -> None:
        config = load_t_handle_config(CONFIG_PATH)
        self.assertEqual(
            config.figure_curves.output_report,
            "reports/experiment_matrix/single_body_t_handle_figure_curves.json",
        )
        with TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "figure_curves.json"
            report = write_t_handle_figure_curve_report(
                output,
                config=config,
                source_commit="test-source",
                vendored_newton_commit="test-newton",
            )
            loaded = load_claim_report(output)

        self.assertEqual(report.status, EvidenceStatus.INCOMPLETE)
        self.assertEqual(loaded.baseline_lane, "paper_figure_digitization")
        self.assertEqual(loaded.solver_mode, "t_handle_paper_figure_digitization")
        self.assertEqual(loaded.backend, "pdftocairo_pillow")
        self.assertFalse(loaded.observed["full_experiment_claim_passed"])
        self.assertEqual(loaded.observed["lane_status"], "figure_color_families_digitized")
        self.assertTrue(loaded.observed["reference_curve_available"])
        self.assertEqual(loaded.observed["source_pdf_sha256"], T_HANDLE_FIGURE_PDF_SHA256)
        self.assertEqual(loaded.observed["rendered_size_px"], list(EXPECTED_RENDERED_SIZE_PX))
        self.assertIn("not_authors_raw_data", loaded.observed["limitations"])
        self.assertIn("no_solid_dashed_line_style_split", loaded.observed["limitations"])
        self.assertNotIn(".png", str(loaded.raw_outputs))
        self.assertNotIn(".pdf", str(loaded.raw_outputs))
        self.assertNotIn("base64", str(loaded.observed))
```

- [ ] **Step 2: Add config parser expectation**

In `tests/test_experiment_run_configs.py`, extend the T-handle config test:

```python
self.assertEqual(
    config.figure_curves.output_report,
    "reports/experiment_matrix/single_body_t_handle_figure_curves.json",
)
```

- [ ] **Step 3: Run RED**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_t_handle_digitization tests.test_experiment_run_configs
```

Expected: FAIL because `mabd_reproduction.t_handle_digitization` and `config.figure_curves` do not exist.

### Task 2: GREEN Digitizer, Config, And Report Writer

**Files:**
- Create: `src/mabd_reproduction/t_handle_digitization.py`
- Modify: `src/mabd_reproduction/experiment_configs.py`
- Modify: `configs/experiments/single_body_t_handle.yaml`
- Test: `tests/test_t_handle_digitization.py`
- Test: `tests/test_experiment_run_configs.py`

- [ ] **Step 1: Add config support**

Add to `configs/experiments/single_body_t_handle.yaml`:

```yaml
figure_curves:
  output_report: reports/experiment_matrix/single_body_t_handle_figure_curves.json
```

Add `THandleFigureCurvesConfig(output_report: str)` and a `figure_curves`
field to `THandleRunConfig`. Parse `figure_curves.output_report` and validate
that it lives under `reports/experiment_matrix/single_body_t_handle_*.json` and
does not collide with RK4, MABD, or comparison output reports.

- [ ] **Step 2: Implement `t_handle_digitization.py`**

Use these constants:

```python
T_HANDLE_FIGURE_PDF = Path("/tmp/mabd-paper/source/images/T-handle/T-handle.pdf")
T_HANDLE_FIGURE_PDF_SHA256 = "5ae6464fd7e7e6fd471ad56e67cdbead6014736cb731a232ce29d80630a72c1c"
RENDER_DPI = 300
EXPECTED_RENDERED_SIZE_PX = (3861, 1541)
ANGULAR_VELOCITY_BOX_PX = (326, 410, 1858, 1260)
ENERGY_LOSS_BOX_PX = (2204, 410, 3788, 1262)
COLOR_FAMILIES_RGB = {
    "blue": (56, 112, 168),
    "orange": (200, 72, 32),
    "green": (32, 72, 48),
}
RGB_DISTANCE_THRESHOLD = 45.0
MIN_SAMPLE_COVERAGE = 0.80
```

Create dataclasses:

```python
@dataclass(frozen=True)
class THandleDigitizedCurve:
    metric: str
    color_family: str
    unit: str
    axis_range: tuple[float, float]
    plot_box_px: tuple[int, int, int, int]
    extraction_success: bool
    sample_coverage: float
    curve_identity_status: str
    samples: tuple[dict[str, float], ...]


@dataclass(frozen=True)
class THandleFigureCurves:
    source_pdf_path: str
    source_pdf_sha256: str
    render_command: tuple[str, ...]
    renderer_version: str
    render_dpi: int
    rendered_size_px: tuple[int, int]
    sample_count: int
    figure_curve_scope: str
    angular_velocity_curves: dict[str, THandleDigitizedCurve]
    energy_loss_curves: dict[str, THandleDigitizedCurve]
```

Implement `digitize_t_handle_figure_curves(sample_count=101)` by rendering with
`pdftocairo`, validating the source hash and rendered size, sampling each color
family in both plot boxes, mapping `time_s` from `0` to `100`, mapping angular
velocity to `[-2, 6]`, and mapping relative energy loss to `[0, 0.25]`.

- [ ] **Step 3: Implement report writer**

`write_t_handle_figure_curve_report(...)` writes a `ClaimReport` with compact
numeric samples and:

- `baseline_lane = "paper_figure_digitization"`
- `solver_mode = "t_handle_paper_figure_digitization"`
- `backend = "pdftocairo_pillow"`
- `status = EvidenceStatus.INCOMPLETE`
- `observed.reference_curve_available = True`
- `observed.figure_curve_scope = "color_family_digitization_only"`
- `observed.limitations` containing:
  - `not_authors_raw_data`
  - `no_solid_dashed_line_style_split`
  - `no_curve_identity_claim`
  - `no_curve_agreement_gate`
  - `no_runtime_timing_evidence`

- [ ] **Step 4: Run GREEN**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_t_handle_digitization tests.test_experiment_run_configs
```

Expected: PASS.

### Task 3: RED Tests For Runner, CLI, And Comparison Consumption

**Files:**
- Modify: `tests/test_experiment_runner.py`
- Modify: `tests/test_t_handle_comparison_reports.py`

- [ ] **Step 1: Add runner and CLI tests**

Add tests that:

- `run_t_handle_figure_curves(...)` writes the configured figure report;
- `scripts/run_experiment.py --lane t_handle_figure_curves` writes the same lane;
- the JSON summary includes `"baseline_lane": "paper_figure_digitization"`.

- [ ] **Step 2: Add comparison consumption tests**

Extend `tests/test_t_handle_comparison_reports.py` so that, when
`figure_curve_report_path` is provided:

```python
self.assertTrue(loaded.observed["digitized_figure_reference_available"])
self.assertIn("paper_figure_curves", loaded.observed["input_report_provenance"])
self.assertEqual(
    loaded.observed["paper_metric_statuses"]["intermediate_axis_angular_velocity_waveform"]["status"],
    "paper_figure_digitized_color_family_available_not_curve_agreement",
)
self.assertEqual(
    loaded.observed["paper_metric_statuses"]["energy_loss"]["status"],
    "paper_figure_digitized_color_family_available_not_energy_agreement",
)
self.assertIn(
    "t_handle_digitized_figure_curve_agreement_not_passed",
    loaded.observed["blocking_reasons"],
)
self.assertIn(
    "raw_t_handle_reference_curve_data_missing",
    loaded.observed["blocking_reasons"],
)
```

Add a negative test mutating the figure report status or
`reference_curve_available`; expected comparison keeps the old metric statuses.

- [ ] **Step 3: Run RED**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_t_handle_digitization tests.test_t_handle_comparison_reports tests.test_experiment_runner
```

Expected: FAIL because the runner/CLI/comparison options do not exist.

### Task 4: GREEN Runner, CLI, And Comparison Integration

**Files:**
- Modify: `src/mabd_reproduction/experiment_runner.py`
- Modify: `scripts/run_experiment.py`
- Modify: `src/mabd_reproduction/comparison_reports.py`
- Test: `tests/test_experiment_runner.py`
- Test: `tests/test_t_handle_comparison_reports.py`

- [ ] **Step 1: Add runner and CLI lane**

Add `run_t_handle_figure_curves(...)`, import the report writer, and add CLI
choice `t_handle_figure_curves`.

- [ ] **Step 2: Add optional comparison input**

Add `figure_curve_report_path: str | Path | None = None` to
`write_t_handle_comparison_report(...)` and `run_t_handle_comparison(...)`.
Add `--figure-report` forwarding for the T-handle comparison CLI path.

When the figure report is valid:

- add `paper_figure_curves` provenance;
- set `digitized_figure_reference_available = true`;
- record sample counts for angular velocity and energy loss color families;
- update the two paper metric statuses specified in Task 3;
- append `t_handle_digitized_figure_curve_agreement_not_passed`;
- keep `raw_t_handle_reference_curve_data_missing`;
- keep top-level status `incomplete` and `full_experiment_claim_passed = false`.

- [ ] **Step 3: Run targeted GREEN**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_t_handle_digitization tests.test_t_handle_comparison_reports tests.test_experiment_runner
```

Expected: PASS.

### Task 5: Regenerate Reports, Docs, And Validator

**Files:**
- Create: `reports/experiment_matrix/single_body_t_handle_figure_curves.json`
- Modify: `reports/experiment_matrix/single_body_t_handle_comparison.json`
- Create: `docs/records/2026-05-18-phase58-t-handle-figure-curves.md`
- Modify: `docs/reference/claim-boundaries.md`
- Modify: `docs/reference/paper-claims.yaml` only if blocker vocabulary changes
- Modify: `scripts/validate_docs.py`
- Modify: `tests/test_phase0_bootstrap.py`

- [ ] **Step 1: Commit implementation before regenerating reports**

Run targeted tests, then commit implementation so regenerated reports can record
that commit as `source_commit`.

- [ ] **Step 2: Regenerate reports**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/run_experiment.py \
  --lane t_handle_figure_curves \
  --config configs/experiments/single_body_t_handle.yaml \
  --matrix configs/experiments/paper_experiment_matrix.yaml \
  --source-commit "$(git rev-parse HEAD)" \
  --vendored-newton-commit 96713fa965463b69c229a4d30582c733ff3526bb

PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/run_experiment.py \
  --lane t_handle_comparison \
  --config configs/experiments/single_body_t_handle.yaml \
  --matrix configs/experiments/paper_experiment_matrix.yaml \
  --rbd-report reports/experiment_matrix/single_body_t_handle_rk4_reference.json \
  --mabd-report reports/experiment_matrix/single_body_t_handle_mabd_newton.json \
  --figure-report reports/experiment_matrix/single_body_t_handle_figure_curves.json \
  --source-commit "$(git rev-parse HEAD)" \
  --vendored-newton-commit 96713fa965463b69c229a4d30582c733ff3526bb
```

- [ ] **Step 3: Update docs and validator**

Record:

- source PDF sha256;
- renderer version and command;
- rendered size `3861 x 1541`;
- plot boxes and axis ranges;
- color-family sample coverage and counts;
- comparison metric-status transitions;
- retained raw-data and pass-gate blockers;
- non-claims.

Extend `scripts/validate_docs.py` and `tests/test_phase0_bootstrap.py` to require
the Phase58 record, figure report, comparison provenance, and preserved
incomplete T-handle claim.

- [ ] **Step 4: Final validation**

Run:

```bash
/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"
git diff --check
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
```

Expected: all pass.
