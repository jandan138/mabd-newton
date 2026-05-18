# Phase53 Heavy-Top Figure Curve Digitization Design

## Goal

Phase53 adds a machine-checkable paper-figure digitization lane for the
heavy-top experiment in Fig. `spinning_top.pdf`. The lane converts the local
paper figure into calibrated digitized paper-figure reference-family samples for:

- precession velocity over time;
- nutation angle over time;
- reference-family identity from the paper legend.

This phase converts the missing figure-reference input into auditable digitized
paper-figure samples. Authors' raw simulation/curve data remains unavailable,
and the current Newton-backed M-ABD lane is not made to match those curves.

## Current Evidence

The paper source is already recorded as arXiv `2603.08079v2` with local source
path `/tmp/mabd-paper/source/`. The heavy-top figure source is:

- `/tmp/mabd-paper/source/images/spinning_top/spinning_top.pdf`
- sha256 `c8f5e206415b9feb3578ee32aa3b7284e2695bdd84eeb0200f3b4aa01cf3422d`
- `pdftotext` exposes the visible labels, legend, and axis tick labels.
- `pdfinfo` identifies an Adobe Illustrator PDF with one page.
- Poppler `pdftocairo`/`pdfinfo`/`pdftotext` version `22.02.0` is available
  in the local environment.
- `pdftocairo -png -singlefile -r 300` produces a deterministic `3179 x 1924`
  RGB raster that exposes clear colored curve families.

The visible plot axes are:

- top plot: `time_s` from 0 to 10 and `precession_velocity_rad_s` from 0 to 8;
- bottom plot: `time_s` from 0 to 10 and `nutation_angle_deg` from 5 to 30.

## Approaches Considered

1. **Preferred: deterministic raster digitization.** Render the local figure
   with `pdftocairo`, crop hard-coded plot boxes in page pixel coordinates,
   segment known curve colors, map pixels to axis values, and write a small
   JSON report with provenance and calibration residuals. This is auditable and
   works with installed tools.
2. **Vector extraction from SVG/PDF paths.** Convert to SVG and parse paths.
   This is attractive in principle, but the converted SVG contains embedded
   image data and many clipping groups, so path identity is not reliable enough
   for this phase.
3. **Manual digitization.** Hand-enter points from the rendered figure. This is
   quick but not reproducible or machine-checkable.

Phase53 uses approach 1.

## Design

Create a focused module `src/mabd_reproduction/heavy_top_digitization.py`.
It will:

- render the source PDF to a temporary PNG with `pdftocairo`;
- assert the rendered image dimensions are exactly `3179 x 1924` pixels for
  the pinned 300 DPI Poppler render;
- use fixed plot boxes calibrated from the rendered figure:
  - top precession plot box;
  - bottom nutation plot box;
- use fixed axis ranges from visible tick labels;
- segment the paper reference curve by nearest RGB distance to the green legend
  stroke;
- return compact reference samples on a fixed time grid.

Blue/orange co-rotated ABD and implicit RBD figure curves are intentionally not
split in Phase53 because each color contains both solid and dashed line styles.
That separation needs a dedicated line-style classifier before it can become
claim-bearing data.

The report writer will create:

- `reports/experiment_matrix/single_body_heavy_top_figure_curves.json`.

The report must include:

- source PDF path, sha256, renderer command, renderer version, rendered image
  size;
- plot calibration boxes and axis ranges;
- per-plot reference sample arrays;
- extraction status for each reference curve;
- visible non-reference color-family counts for audit only;
- explicit limitations and non-claims.

No rendered PNG, PDF, SVG, or raw paper asset is committed. The JSON contains
only compact numeric samples and provenance; it must not contain raster pixels,
base64 image payloads, SVG/PDF dumps, or raw paper assets.

## Comparison Integration

The heavy-top comparison report will read an explicitly supplied
`figure_curve_report_path`. It will change the nutation metric status from
`paper_reference_curve_missing` to
`paper_figure_digitized_reference_available` only when the figure report has
finite digitized paper-figure reference-family samples for the nutation plot.

The comparison report will retain:

- `exact_heavy_top_inertia_unknown`;
- `exact_heavy_top_geometry_unknown`;
- `mabd_newton_report_incomplete`;
- `heavy_top_comparison_report_incomplete`;
- `heavy_top_comparison_pass_gate_not_enabled`;
- `sample_time_grid_mismatch` while the current M-ABD lane remains shorter than
  the paper plot horizon;
- `raw_author_heavy_top_curve_data_missing`, or the existing
  `raw_heavy_top_reference_curve_data_missing` if the blocker is not renamed.

The comparison may add `digitized_figure_reference_available` and
`heavy_top_digitized_figure_curve_agreement_not_passed`, but it must retain or
rename the raw-data blocker as `raw_author_heavy_top_curve_data_missing`.
Digitized figure samples are not authors' raw simulation data.

## Claim Boundaries

Phase53 may claim:

- heavy-top digitized paper-figure reference-family samples are extracted from
  the recorded source PDF;
- digitized paper-figure samples are finite and calibrated to visible axes;
- the comparison report can identify paper figure data availability.

Phase53 must not claim:

- exact paper simulation parameters, inertia, or geometry;
- that digitization is equivalent to authors' raw simulation data;
- that blue/orange solid and dashed paper curves have been separated;
- heavy-top curve agreement;
- heavy-top experiment pass;
- runtime performance reproduction;
- generated video or rendered-output reproduction;
- full paper reproduction.

## Validation

Required checks:

- targeted RED/GREEN tests for the digitizer;
- targeted RED/GREEN tests for heavy-top comparison report consumption;
- report regeneration for the new figure-curve report and heavy-top comparison;
- `docs/reference/claim-boundaries.md` update documenting Phase53 non-claims;
- `docs/reference/paper-claims.yaml` update only if blocker names change;
- `docs/records/2026-05-18-phase53-heavy-top-figure-curves.md` with source
  commit, source PDF sha256, Poppler/Pillow versions, commands, environment,
  report sha256, and incomplete status;
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests`;
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py`;
- `PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"`;
- `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .`;
- `git diff --check`.
