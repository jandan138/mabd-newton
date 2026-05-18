# Phase58 T-Handle Figure Curve Digitization Design

## Goal

Phase58 adds a machine-checkable T-handle paper-figure digitization lane for
Fig. `T-handle.pdf`. The lane converts the recorded public paper figure into
compact calibrated color-family samples for:

- body-frame angular velocity along the intermediate principal axis over time;
- relative energy loss over time;
- visible blue, orange, and green paper figure color families.

This phase turns the public figure from a checksum-only artifact into auditable
numeric evidence. It does not claim authors' raw simulation data, exact curve
identity, line-style separation, paper-faithful geometry, paper timing
agreement, T-handle experiment pass, or full paper reproduction.

## Current Evidence

The T-handle public source material is already recorded as:

- arXiv source version: `2603.08079v2`
- figure PDF: `/tmp/mabd-paper/source/images/T-handle/T-handle.pdf`
- figure PDF sha256:
  `5ae6464fd7e7e6fd471ad56e67cdbead6014736cb731a232ce29d80630a72c1c`
- visible caption/source lines:
  `/tmp/mabd-paper/source/sections/experiment.tex:57-75`
- `pdftotext` exposes axis labels, ticks, and legend text but not raw curve data.
- `pdfinfo` identifies a one-page Adobe Illustrator PDF.
- `pdftocairo 22.02.0` and Pillow `12.2.0` are available in the isolated
  `mabd-newton-py310` environment.
- `pdftocairo -png -singlefile -r 300` renders a deterministic
  `3861 x 1541` RGB image.

The visible plot calibration for the rendered image is:

- left angular-velocity plot box: `(326, 410, 1858, 1260)`
- left axes: `time_s` from `0` to `100`, `omega_intermediate_rad_s` from `-2`
  to `6`
- right relative-energy-loss plot box: `(2204, 410, 3788, 1262)`
- right axes: `time_s` from `0` to `100`, `relative_energy_loss` from `0` to
  `0.25`
- curve color families:
  - blue: `(56, 112, 168)`
  - orange: `(200, 72, 32)`
  - green: `(32, 72, 48)`

With these calibrations, color-family coverage is at least `0.86` for every
plot/color family at an RGB distance threshold of `45`, and most families reach
full sample-grid coverage.

## Approaches Considered

1. **Preferred: deterministic raster color-family digitization.** Render the
   recorded PDF with Poppler, segment known RGB color families in fixed plot
   boxes, map pixels to visible axis values, and write compact samples plus
   provenance. This is deterministic and follows the heavy-top Phase53 pattern.
2. **PDF/SVG vector path extraction.** This could theoretically preserve exact
   Bezier curves, but the Illustrator PDF contains many clipped paths, text,
   and legend strokes. Stable curve identity and line style separation would
   require a larger parser and visual validation pass.
3. **Manual digitization.** Hand-entered samples are quick but not
   machine-checkable and would not meet the project provenance contract.

Phase58 uses approach 1.

## Design

Create `src/mabd_reproduction/t_handle_digitization.py` with:

- dataclasses for one digitized color-family curve and the full figure payload;
- source PDF checksum validation;
- Poppler rendering to a temporary PNG;
- strict rendered-size validation;
- fixed plot calibration and axis ranges;
- per-color color masks with a pinned RGB distance threshold;
- per-time-grid median pixel sampling with interpolation over sparse gaps;
- finite sample validation and coverage metrics;
- a report writer for
  `reports/experiment_matrix/single_body_t_handle_figure_curves.json`.

The figure report will use:

- `baseline_lane = paper_figure_digitization`
- `solver_mode = t_handle_paper_figure_digitization`
- `backend = pdftocairo_pillow`
- top-level status `incomplete`
- `observed.reference_curve_available = true`
- `observed.figure_curve_scope = color_family_digitization_only`
- `observed.limitations` including:
  - `not_authors_raw_data`
  - `no_solid_dashed_line_style_split`
  - `no_curve_identity_claim`
  - `no_curve_agreement_gate`
  - `no_runtime_timing_evidence`

No rendered PNG, PDF, SVG, base64 payload, or raw paper asset is committed.
Only compact JSON samples and provenance are committed.

## Comparison Integration

Add an optional `figure_curve_report_path` to the T-handle comparison writer and
runner. When a valid figure-curve report is supplied:

- record `paper_figure_curves` input provenance;
- set `digitized_figure_reference_available = true`;
- expose compact sample counts under `digitized_figure_reference_samples`;
- change the intermediate-axis waveform paper metric status from
  `diagnostic_available_not_paper_curve` to
  `paper_figure_digitized_color_family_available_not_curve_agreement`;
- change the energy-loss metric status from
  `signed_energy_drift_diagnostic_not_paper_loss` to
  `paper_figure_digitized_color_family_available_not_energy_agreement`;
- retain raw-data and pass-gate blockers;
- add `t_handle_digitized_figure_curve_agreement_not_passed`.

The comparison must remain `incomplete` with
`full_experiment_claim_passed = false`.

## Claim Boundaries

Phase58 may claim:

- the recorded T-handle paper figure was rendered deterministically;
- blue/orange/green color-family samples were digitized from visible axes;
- the comparison report is aware that digitized paper-figure color-family data
  exists.

Phase58 must not claim:

- authors' raw curve data was recovered;
- blue/orange/green families are separated into specific legend entries;
- solid and dashed line styles are separated;
- exact T-handle geometry, inertia, or subtle asymmetry is known;
- T-handle curve agreement, flip-timing agreement, energy-loss agreement, or
  runtime performance is passed;
- the T-handle experiment or any `experiment.*` claim is passed;
- full paper reproduction.

## Validation

Required checks:

- RED/GREEN tests for digitization and report writing;
- RED/GREEN tests for runner/CLI lanes;
- RED/GREEN tests for T-handle comparison consumption;
- regenerated figure-curve and comparison reports with pinned source commit;
- `docs/reference/claim-boundaries.md` Phase58 non-claims;
- `docs/records/2026-05-18-phase58-t-handle-figure-curves.md`;
- `scripts/validate_docs.py` Phase58 validator coverage;
- canonical isolated-environment gates:
  - `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py`
  - `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests`
  - `PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"`
  - `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .`
  - `git diff --check`
