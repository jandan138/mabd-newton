# Phase 65 Spinning-Box Figure Curve Digitization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a deterministic paper-figure color-family digitization lane for the spinning-box `roll_cube.pdf` figure without claiming the spinning-box experiment is passed.

**Architecture:** Mirror the existing heavy-top and T-handle figure digitizers with a focused `spinning_box_digitization` module, a small config field, a runner/CLI lane, a compact JSON report, and docs/provenance gates. The lane renders the paper PDF through Poppler, samples calibrated plot boxes by RGB color family, and records limitations instead of solver agreement.

**Tech Stack:** Python 3.10, Pillow, NumPy, Poppler `pdftocairo`, existing YAML config loader, `ClaimReport`, `unittest`, vendored Newton path isolation.

**Claim Impact:** No `experiment.*` claim is passed.

---

## File Structure

- Create `src/mabd_reproduction/spinning_box_digitization.py` for source hashing, rendering, color-family sampling, dataclasses, and report writing.
- Create `tests/test_spinning_box_digitization.py` for digitizer and report writer behavior.
- Modify `src/mabd_reproduction/experiment_configs.py` and `configs/experiments/single_body_spinning_box.yaml` for `paper_horizon.figure_curve_output_report`.
- Modify `src/mabd_reproduction/experiment_runner.py` and `scripts/run_experiment.py` for the `spinning_box_figure_curves` lane.
- Modify `tests/test_experiment_run_configs.py` and `tests/test_experiment_runner.py` for config, runner, and CLI coverage.
- Create `reports/experiment_matrix/single_body_spinning_box_figure_curves.json`.
- Modify `docs/reference/claim-boundaries.md`, `scripts/validate_docs.py`, and `tests/test_phase0_bootstrap.py` for Phase 65 provenance gates.
- Create `docs/records/2026-05-19-phase65-spinning-box-figure-curves.md`.

## Task 1: RED Tests For Digitization And Report Writer

**Files:**
- Create: `tests/test_spinning_box_digitization.py`
- Modify: `tests/test_experiment_run_configs.py`

- [ ] **Step 1: Write failing digitizer tests**

Create `tests/test_spinning_box_digitization.py`:

```python
from __future__ import annotations

import unittest
from math import isfinite
from pathlib import Path
from tempfile import TemporaryDirectory

from mabd_reproduction.experiment_configs import load_spinning_box_config
from mabd_reproduction.reporting import EvidenceStatus, load_claim_report
from mabd_reproduction.spinning_box_digitization import (
    ANGULAR_MOMENTUM_BOX_PX,
    EXPECTED_RENDERED_SIZE_PX,
    LINEAR_MOMENTUM_BOX_PX,
    RENDER_DPI,
    SPINNING_BOX_FIGURE_PDF,
    SPINNING_BOX_FIGURE_PDF_SHA256,
    digitize_spinning_box_figure_curves,
    write_spinning_box_figure_curve_report,
)


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs/experiments/single_body_spinning_box.yaml"


class SpinningBoxDigitizationTests(unittest.TestCase):
    def test_digitizer_rejects_bad_sample_count(self) -> None:
        for sample_count in (1, 0, -3):
            with self.subTest(sample_count=sample_count):
                with self.assertRaisesRegex(ValueError, "sample_count must be at least 2"):
                    digitize_spinning_box_figure_curves(sample_count=sample_count)

    def test_digitizes_color_families_from_recorded_pdf(self) -> None:
        curves = digitize_spinning_box_figure_curves(sample_count=31)

        self.assertEqual(curves.source_pdf_path, SPINNING_BOX_FIGURE_PDF.as_posix())
        self.assertEqual(curves.source_pdf_sha256, SPINNING_BOX_FIGURE_PDF_SHA256)
        self.assertEqual(curves.render_dpi, RENDER_DPI)
        self.assertEqual(curves.rendered_size_px, EXPECTED_RENDERED_SIZE_PX)
        self.assertRegex(curves.rendered_image_sha256, r"^[0-9a-f]{64}$")
        self.assertEqual(curves.renderer_version, "pdftocairo 22.02.0")
        self.assertEqual(curves.sample_count, 31)
        self.assertEqual(curves.figure_curve_scope, "paper_roll_cube_color_family_digitization")
        self.assertEqual(curves.color_assignment_policy, "nearest_color_family_within_threshold")
        self.assertEqual(curves.curve_identity_status, "color_family_not_legend_entry")
        self.assertEqual(curves.curve_agreement_status, "not_evaluated")
        self.assertTrue(curves.color_family_curve_available)
        self.assertFalse(curves.paper_reference_legend_identity_available)
        self.assertEqual(set(curves.angular_momentum_curves), {"blue", "orange", "green", "gray", "brown"})
        self.assertEqual(set(curves.linear_momentum_curves), {"blue", "orange", "green", "gray", "brown"})

        for curve in (*curves.angular_momentum_curves.values(), *curves.linear_momentum_curves.values()):
            self.assertTrue(curve.extraction_success)
            self.assertGreaterEqual(curve.sample_coverage, 0.80)
            self.assertGreaterEqual(curve.matched_sample_count, 25)
            self.assertLessEqual(curve.interpolated_sample_count, 6)
            self.assertLessEqual(curve.longest_missing_run, 5)
            self.assertGreater(curve.source_pixel_count, 0)
            self.assertEqual(curve.curve_identity_status, "color_family_not_legend_entry")
            self.assertEqual(curve.axis_range, (95.0, 100.0))
            self.assertAlmostEqual(curve.samples[0]["time_s"], 0.0)
            self.assertAlmostEqual(curve.samples[-1]["time_s"], 10.0)
            self.assertEqual(len(curve.samples), 31)
            self.assertTrue(all(isfinite(sample["value"]) for sample in curve.samples))
            self.assertTrue(all(95.0 <= sample["value"] <= 100.0 for sample in curve.samples))

        self.assertEqual(curves.angular_momentum_curves["blue"].plot_box_px, ANGULAR_MOMENTUM_BOX_PX)
        self.assertEqual(curves.linear_momentum_curves["blue"].plot_box_px, LINEAR_MOMENTUM_BOX_PX)

    def test_writes_incomplete_report_without_lane_gate_status(self) -> None:
        config = load_spinning_box_config(CONFIG_PATH)
        self.assertEqual(
            config.paper_horizon.figure_curve_output_report,
            "reports/experiment_matrix/single_body_spinning_box_figure_curves.json",
        )
        with TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "figure_curves.json"
            report = write_spinning_box_figure_curve_report(
                output,
                config=config,
                source_commit="test-source",
                vendored_newton_commit="test-newton",
                sample_count=31,
            )
            loaded = load_claim_report(output)

        self.assertEqual(report.status, EvidenceStatus.INCOMPLETE)
        self.assertEqual(loaded.claim_id, "experiment.single_body.spinning_box")
        self.assertEqual(loaded.baseline_lane, "paper_figure_digitization")
        self.assertEqual(loaded.solver_mode, "spinning_box_paper_figure_curve_digitization")
        self.assertEqual(loaded.backend, "paper_pdf_digitization")
        self.assertEqual(loaded.observed["figure_curve_scope"], "paper_roll_cube_color_family_digitization")
        self.assertEqual(loaded.observed["source_pdf_sha256"], SPINNING_BOX_FIGURE_PDF_SHA256)
        self.assertEqual(loaded.observed["rendered_size_px"], list(EXPECTED_RENDERED_SIZE_PX))
        self.assertRegex(loaded.observed["rendered_image_sha256"], r"^[0-9a-f]{64}$")
        self.assertTrue(loaded.observed["color_family_curve_available"])
        self.assertFalse(loaded.observed["paper_reference_legend_identity_available"])
        self.assertEqual(loaded.observed["color_assignment_policy"], "nearest_color_family_within_threshold")
        self.assertEqual(loaded.observed["curve_identity_status"], "color_family_not_legend_entry")
        self.assertEqual(loaded.observed["curve_agreement_status"], "not_evaluated")
        self.assertEqual(
            loaded.observed["blocking_reasons"],
            [
                "spinning_box_figure_curve_agreement_not_evaluated",
                "spinning_box_reference_legend_identity_not_evaluated",
                "spinning_box_line_style_split_not_evaluated",
                "mabd_newton_report_incomplete",
                "spinning_box_comparison_pass_gate_not_enabled",
            ],
        )
        self.assertNotIn("reference_curve_available", loaded.observed)
        self.assertNotIn("lane_gate_status", loaded.observed)
        self.assertNotIn(".png", str(loaded.raw_outputs))
        self.assertNotIn(".pdf", str(loaded.raw_outputs))
        self.assertNotIn("base64", str(loaded.observed))
```

- [ ] **Step 2: Add config parser expectation**

In `tests/test_experiment_run_configs.py`, extend the spinning-box config test:

```python
self.assertEqual(
    config.paper_horizon.figure_curve_output_report,
    "reports/experiment_matrix/single_body_spinning_box_figure_curves.json",
)
```

- [ ] **Step 3: Run RED**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_spinning_box_digitization tests.test_experiment_run_configs
```

Expected: fail because `mabd_reproduction.spinning_box_digitization` and `figure_curve_output_report` do not exist.

## Task 2: GREEN Digitizer, Config, And Report Writer

**Files:**
- Create: `src/mabd_reproduction/spinning_box_digitization.py`
- Modify: `src/mabd_reproduction/experiment_configs.py`
- Modify: `configs/experiments/single_body_spinning_box.yaml`
- Test: `tests/test_spinning_box_digitization.py`
- Test: `tests/test_experiment_run_configs.py`

- [ ] **Step 1: Add config support**

Add under `configs/experiments/single_body_spinning_box.yaml` `paper_horizon`:

```yaml
  figure_curve_output_report: reports/experiment_matrix/single_body_spinning_box_figure_curves.json
```

Add a `figure_curve_output_report: str` field to `SpinningBoxPaperHorizonConfig`, parse it from `paper_horizon.figure_curve_output_report`, and validate that it lives under `reports/experiment_matrix/single_body_spinning_box_*.json` without colliding with existing spinning-box report paths.

- [ ] **Step 2: Implement digitization dataclasses and constants**

Create `src/mabd_reproduction/spinning_box_digitization.py` with immutable dataclasses:

```python
@dataclass(frozen=True)
class SpinningBoxDigitizedCurve:
    metric: str
    color_family: str
    unit: str
    axis_range: tuple[float, float]
    plot_box_px: tuple[int, int, int, int]
    extraction_success: bool
    sample_coverage: float
    matched_sample_count: int
    interpolated_sample_count: int
    longest_missing_run: int
    source_pixel_count: int
    curve_identity_status: str
    samples: tuple[dict[str, float], ...]


@dataclass(frozen=True)
class SpinningBoxFigureCurves:
    source_pdf_path: str
    source_pdf_sha256: str
    render_command: tuple[str, ...]
    renderer_version: str
    render_dpi: int
    rendered_size_px: tuple[int, int]
    rendered_image_sha256: str
    sample_count: int
    figure_curve_scope: str
    color_family_curve_available: bool
    paper_reference_legend_identity_available: bool
    color_assignment_policy: str
    curve_identity_status: str
    curve_agreement_status: str
    angular_momentum_curves: dict[str, SpinningBoxDigitizedCurve]
    linear_momentum_curves: dict[str, SpinningBoxDigitizedCurve]
```

Use constants:

```python
SPINNING_BOX_FIGURE_PDF = Path("/tmp/mabd-paper/source/images/cube/roll_cube.pdf")
SPINNING_BOX_FIGURE_PDF_SHA256 = "7669b062348324a3b0090cc9f44930655c83233a87f63389db9198b88f95ae80"
RENDER_DPI = 300
EXPECTED_RENDERED_SIZE_PX = (3570, 2187)
ANGULAR_MOMENTUM_BOX_PX = (394, 1139, 1751, 1956)
LINEAR_MOMENTUM_BOX_PX = (2142, 1139, 3528, 1956)
COLOR_FAMILIES_RGB = {
    "blue": (56, 112, 168),
    "orange": (200, 72, 32),
    "green": (32, 72, 48),
    "gray": (176, 160, 144),
    "brown": (160, 144, 128),
}
RGB_DISTANCE_THRESHOLD = 55.0
MIN_SAMPLE_COVERAGE = 0.80
TIME_AXIS_RANGE_S = (0.0, 10.0)
MOMENTUM_AXIS_RANGE = (95.0, 100.0)
```

- [ ] **Step 3: Implement render and sampling helpers**

Implement `digitize_spinning_box_figure_curves(sample_count=101)` by:

- rejecting `sample_count < 2` with `ValueError("sample_count must be at least 2")`;
- checking the PDF SHA256 before rendering;
- rendering with `pdftocairo -png -singlefile -r 300`;
- checking the output image size equals `(3570, 2187)`;
- recording the rendered PNG SHA256 before deleting the temporary raster;
- assigning pixels to the nearest configured color family within `RGB_DISTANCE_THRESHOLD`;
- sampling each assigned color family in both plot boxes;
- mapping x to `time_s` over `0..10`;
- mapping y to `value` over `95..100`;
- linearly interpolating missing sample columns when at least one source column was detected;
- recording matched sample count, interpolated sample count, longest missing run, and source pixel count;
- marking extraction successful only when sample coverage is at least `0.80`.

Use the existing heavy-top/T-handle helper style: `subprocess.run(..., check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)`, `PIL.Image.open(...).convert("RGB")`, NumPy RGB distance masks, and compact `dict[str, float]` samples.

- [ ] **Step 4: Implement report writer**

Implement `write_spinning_box_figure_curve_report(...)` so it writes a `ClaimReport` with:

```python
claim_id="experiment.single_body.spinning_box"
baseline_lane="paper_figure_digitization"
solver_mode="spinning_box_paper_figure_curve_digitization"
backend="paper_pdf_digitization"
status=EvidenceStatus.INCOMPLETE
```

The `observed` payload must include the fields required by the spec, compact serialized curves, and exactly these blockers:

```python
[
    "spinning_box_figure_curve_agreement_not_evaluated",
    "spinning_box_reference_legend_identity_not_evaluated",
    "spinning_box_line_style_split_not_evaluated",
    "mabd_newton_report_incomplete",
    "spinning_box_comparison_pass_gate_not_enabled",
]
```

It must not include `lane_gate_status`, committed raster/PDF paths, base64 image data, or raw paper assets.

- [ ] **Step 5: Run GREEN**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_spinning_box_digitization tests.test_experiment_run_configs
```

Expected: pass.

- [ ] **Step 6: Commit**

```bash
git add src/mabd_reproduction/spinning_box_digitization.py src/mabd_reproduction/experiment_configs.py configs/experiments/single_body_spinning_box.yaml tests/test_spinning_box_digitization.py tests/test_experiment_run_configs.py
git commit -m "feat: add spinning-box figure curve digitizer"
```

## Task 3: RED/GREEN Runner And CLI Lane

**Files:**
- Modify: `src/mabd_reproduction/experiment_runner.py`
- Modify: `scripts/run_experiment.py`
- Modify: `tests/test_experiment_runner.py`

- [ ] **Step 1: Write failing runner and CLI tests**

In `tests/test_experiment_runner.py`, add tests mirroring the existing spinning-box side lanes:

```python
def test_run_spinning_box_figure_curves_writes_report(self) -> None:
    from mabd_reproduction.experiment_runner import run_spinning_box_figure_curves

    with TemporaryDirectory() as tmpdir:
        output = Path(tmpdir) / "spinning_box_figure_curves.json"
        result = run_spinning_box_figure_curves(
            config_path=SPINNING_BOX_CONFIG_PATH,
            matrix_path=MATRIX_PATH,
            output_path=output,
            source_commit="test-source",
            vendored_newton_commit="test-newton",
        )
        loaded = load_claim_report(output)

    self.assertEqual(result.claim_id, "experiment.single_body.spinning_box")
    self.assertEqual(result.status.value, "incomplete")
    self.assertEqual(result.report_path, output)
    self.assertEqual(loaded.baseline_lane, "paper_figure_digitization")
    self.assertEqual(loaded.solver_mode, "spinning_box_paper_figure_curve_digitization")


def test_run_experiment_cli_dispatches_spinning_box_figure_curves(self) -> None:
    with TemporaryDirectory() as tmpdir:
        output = Path(tmpdir) / "spinning_box_figure_curves.json"
        result = subprocess.run(
            [
                sys.executable,
                "scripts/run_experiment.py",
                "--lane",
                "spinning_box_figure_curves",
                "--config",
                str(SPINNING_BOX_CONFIG_PATH),
                "--output",
                str(output),
                "--source-commit",
                "test-source",
                "--vendored-newton-commit",
                "test-newton",
            ],
            cwd=ROOT,
            env={**os.environ, "PYTHONPATH": f"{ROOT / 'src'}:{ROOT / 'vendor/newton'}"},
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        loaded = load_claim_report(output)

    summary = json.loads(result.stdout)
    self.assertEqual(summary["claim_id"], "experiment.single_body.spinning_box")
    self.assertEqual(summary["status"], "incomplete")
    self.assertEqual(loaded.backend, "paper_pdf_digitization")


def test_run_spinning_box_figure_curves_requires_explicit_output(self) -> None:
    from mabd_reproduction.experiment_runner import run_spinning_box_figure_curves

    with self.assertRaisesRegex(ValueError, "spinning_box_figure_curves requires --output"):
        run_spinning_box_figure_curves(
            config_path=SPINNING_BOX_CONFIG_PATH,
            matrix_path=MATRIX_PATH,
            source_commit="test-source",
            vendored_newton_commit="test-newton",
        )
```

- [ ] **Step 2: Run RED**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_runner
```

Expected: fail because the runner function and CLI lane do not exist.

- [ ] **Step 3: Implement runner**

Add `run_spinning_box_figure_curves(...)` in `src/mabd_reproduction/experiment_runner.py`. It must load the spinning-box config, load the experiment matrix, validate the config against the matrix, require an explicit `output_path`, reject `output_root`, call `write_spinning_box_figure_curve_report`, and return `ExperimentRunResult`.

- [ ] **Step 4: Implement CLI lane**

Add `spinning_box_figure_curves` to `scripts/run_experiment.py` lane dispatch. It must use the same explicit output behavior as the other diagnostic side lanes.

- [ ] **Step 5: Run GREEN**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_runner
```

Expected: pass.

- [ ] **Step 6: Commit**

```bash
git add src/mabd_reproduction/experiment_runner.py scripts/run_experiment.py tests/test_experiment_runner.py
git commit -m "feat: add spinning-box figure curve runner"
```

## Task 4: Generate Report And Add Provenance Gates

**Files:**
- Create: `reports/experiment_matrix/single_body_spinning_box_figure_curves.json`
- Create: `docs/records/2026-05-19-phase65-spinning-box-figure-curves.md`
- Modify: `docs/reference/claim-boundaries.md`
- Modify: `scripts/validate_docs.py`
- Modify: `tests/test_phase0_bootstrap.py`

- [ ] **Step 1: Generate the committed report**

Run:

```bash
SOURCE_COMMIT=$(git rev-parse HEAD)
VENDORED_NEWTON_COMMIT=96713fa965463b69c229a4d30582c733ff3526bb
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/run_experiment.py \
  --lane spinning_box_figure_curves \
  --config configs/experiments/single_body_spinning_box.yaml \
  --output reports/experiment_matrix/single_body_spinning_box_figure_curves.json \
  --source-commit "$SOURCE_COMMIT" \
  --vendored-newton-commit "$VENDORED_NEWTON_COMMIT"
```

Expected: writes an incomplete `paper_figure_digitization` report with finite angular and linear momentum color-family curves.

- [ ] **Step 2: Record the report hash**

Run:

```bash
sha256sum reports/experiment_matrix/single_body_spinning_box_figure_curves.json
```

Copy the hash into `scripts/validate_docs.py` and the Phase65 record.

- [ ] **Step 3: Write the Phase65 record**

Create `docs/records/2026-05-19-phase65-spinning-box-figure-curves.md` with:

```markdown
# Phase 65 Spinning-Box Figure Curve Digitization Record

Date: 2026-05-19

## Scope

Phase 65 adds a paper-PDF digitization lane for
`/tmp/mabd-paper/source/images/cube/roll_cube.pdf`. The lane records
color-family momentum curves from the paper figure only.

## Evidence

- Spec: `docs/superpowers/specs/2026-05-19-phase65-spinning-box-figure-curves-design.md`
- Plan: `docs/superpowers/plans/2026-05-19-mabd-phase65-spinning-box-figure-curves.md`
- Report: `reports/experiment_matrix/single_body_spinning_box_figure_curves.json`
- Report SHA256: the exact `sha256sum` output from Step 2
- Source commit: the `source_commit` recorded in the report
- Vendored Newton commit: the `vendored_newton_commit` recorded in the report
- Paper source version: `2603.08079v2`
- Config: `configs/experiments/single_body_spinning_box.yaml`
- Backend: `paper_pdf_digitization`
- Paper PDF SHA256: `7669b062348324a3b0090cc9f44930655c83233a87f63389db9198b88f95ae80`
- Rendered image SHA256: the `rendered_image_sha256` recorded in the report
- Render command starts with `pdftocairo -png -singlefile -r 300 /tmp/mabd-paper/source/images/cube/roll_cube.pdf` and ends with a temporary output prefix.
- Report status: `incomplete`
- Curve identity status: `color_family_not_legend_entry`
- Curve agreement status: `not_evaluated`

## Claim Boundary

This phase does not pass `experiment.single_body.spinning_box` and does not
change `docs/reference/paper-claims.yaml`. Curve identity and curve agreement
remain unevaluated.

## Verification

- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_spinning_box_digitization tests.test_experiment_run_configs tests.test_experiment_runner tests.test_phase0_bootstrap`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py`
- `git diff --check`
```

- [ ] **Step 4: Update claim boundaries**

Add a Phase 65 bullet to `docs/reference/claim-boundaries.md` stating that the spinning-box figure curve report is a color-family paper-figure digitization only, with curve identity/agreement unevaluated and no `experiment.*` claim passed.

- [ ] **Step 5: Update validation gates**

Update `scripts/validate_docs.py` and `tests/test_phase0_bootstrap.py` so validation requires:

- the Phase65 spec path;
- the Phase65 plan path;
- the Phase65 record path;
- the committed figure-curve report path;
- exact report SHA256;
- report `status == "incomplete"`;
- solver mode `spinning_box_paper_figure_curve_digitization`;
- backend `paper_pdf_digitization`;
- exact source PDF path and SHA256;
- exact render command prefix, render DPI, renderer version, rendered size, and rendered image SHA256 shape;
- `color_family_curve_available == true`;
- `paper_reference_legend_identity_available == false`;
- `color_assignment_policy == "nearest_color_family_within_threshold"`;
- `curve_identity_status == "color_family_not_legend_entry"`;
- `curve_agreement_status == "not_evaluated"`;
- no `lane_gate_status`;
- exact blocker list;
- every curve has finite samples, nonzero source pixel count, matched/interpolated/gap statistics, and coverage at or above `0.80`;
- `paper-claims.yaml` still has `experiment.single_body.spinning_box.reproduction_status: intended`.

- [ ] **Step 6: Run focused provenance tests**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_phase0_bootstrap
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
```

Expected: pass.

- [ ] **Step 7: Commit**

```bash
git add reports/experiment_matrix/single_body_spinning_box_figure_curves.json docs/records/2026-05-19-phase65-spinning-box-figure-curves.md docs/reference/claim-boundaries.md scripts/validate_docs.py tests/test_phase0_bootstrap.py
git commit -m "docs: record Phase65 spinning-box figure curves"
```

## Task 5: Final Verification And Integration

**Files:**
- Verify all changed files.

- [ ] **Step 1: Run full validation commands**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/env/readiness_check.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .
git diff --check
```

Expected: all pass with no ambient Python or shared Newton environment mutation.

- [ ] **Step 2: Review changed files**

Run:

```bash
git status --short
git log --oneline --decorate -5
```

Expected: only Phase65 files are changed or committed on the feature branch.

- [ ] **Step 3: Merge and push after green verification**

From `/cpfs/user/zhuzihou/dev/mabd-newton`, merge the Phase65 branch into `main` and push:

```bash
git switch main
git merge --ff-only phase65-spinning-box-figure-curves
git push origin main
```

Expected: `main` advances by fast-forward and pushes to `https://github.com/jandan138/mabd-newton.git`.
