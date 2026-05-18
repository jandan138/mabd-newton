# Phase 65 Spinning-Box Figure Curve Digitization Design

Date: 2026-05-19

## Objective

Phase 65 adds a bounded, machine-checkable digitization lane for the
spinning-box paper figure `roll_cube.pdf`. The lane extracts color-family
momentum curves from the paper artifact already recorded in the spinning-box
config and writes a compact JSON claim report.

This phase does not modify `SolverMABD`, does not assert curve agreement, does
not pass `experiment.single_body.spinning_box`, and does not change
`docs/reference/paper-claims.yaml`.

## Current Gap

The current spinning-box evidence has several diagnostic lanes:

- the M-ABD paper-horizon lane reports large affine stretch and energy
  threshold violations;
- the contact and normal-constraint lanes are still explicitly diagnostic;
- the decoupled twist lane keeps shape and energy thresholds bounded but is not
  a paper-faithful solver step.

The paper figure itself plots linear and angular momentum over `0..10 s` for
the cube scene. Before any lane can claim visual or curve agreement, the paper
figure curves need a committed, reproducible extraction record with source
hashes, renderer metadata, plot boxes, color-family coverage, and samples. The
existing T-handle and heavy-top digitizers provide the local pattern.

## Design

Add `src/mabd_reproduction/spinning_box_digitization.py` with the same style as
the existing figure digitizers:

- source PDF:
  `/tmp/mabd-paper/source/images/cube/roll_cube.pdf`;
- source SHA256:
  `7669b062348324a3b0090cc9f44930655c83233a87f63389db9198b88f95ae80`;
- renderer: `pdftocairo -png -singlefile -r 300`;
- expected rendered size: `(3570, 2187)`;
- left plot box: angular momentum, pixels `(394, 1139, 1751, 1956)`;
- right plot box: linear momentum, pixels `(2142, 1139, 3528, 1956)`;
- time range: `0..10 s`;
- momentum axis range: `95..100`;
- color families: blue, orange, green, gray, and brown.

The digitizer samples each color family at a configurable sample count. Missing
columns are linearly interpolated if there is at least one detected source
pixel, as in the existing digitizers. Every curve records:

- metric name;
- color family;
- unit;
- plot box;
- axis range;
- extraction success;
- sample coverage;
- curve identity status;
- samples.

The curve identity is deliberately recorded as color-family only. The report
must not infer which color or style is the paper's ABD/RBD/reference series
until a later agreement phase validates that mapping.

## Report Lane

Add a report writer:

```text
write_spinning_box_figure_curve_report(...)
```

The report path is:

```text
reports/experiment_matrix/single_body_spinning_box_figure_curves.json
```

The report uses:

```text
claim_id = experiment.single_body.spinning_box
solver_mode = spinning_box_paper_figure_curve_digitization
backend = paper_pdf_digitization
status = incomplete
```

Observed payload requirements:

- `figure_curve_scope = "paper_roll_cube_color_family_digitization"`;
- `source_pdf_path`;
- `source_pdf_sha256`;
- `render_command`;
- `renderer_version`;
- `render_dpi`;
- `rendered_size_px`;
- `sample_count`;
- `reference_curve_available = true` when both panels meet coverage;
- `curve_identity_status = "color_family_not_legend_entry"`;
- `curve_agreement_status = "not_evaluated"`;
- `angular_momentum_curves`;
- `linear_momentum_curves`;
- `blocking_reasons` must include:
  - `spinning_box_figure_curve_agreement_not_evaluated`;
  - `mabd_newton_report_incomplete`;
  - `spinning_box_comparison_pass_gate_not_enabled`.

The report must not include `lane_gate_status`.

## Config, Runner, And CLI

Add `figure_curve_output_report` under
`configs/experiments/single_body_spinning_box.yaml` `paper_horizon`.

Expose a runner and CLI lane:

```text
--lane spinning_box_figure_curves
```

Like the other diagnostic side lanes, the runner requires explicit `--output`.

## Tests

Write tests first for:

- digitizer rejects bad `sample_count`;
- digitizer checks the exact source PDF hash and rendered image size;
- digitizer returns both momentum panels, expected plot boxes, finite samples,
  and coverage at or above `0.80` for required color families;
- the report writer emits `status = incomplete`, exact solver mode/backend,
  no `lane_gate_status`, exact blockers, and color-family-only identity;
- config parsing includes `figure_curve_output_report`;
- runner and CLI dispatch write the report to an explicit output;
- docs/provenance validation checks the committed report and record without
  changing paper claim statuses.

## Claim Boundaries

Phase 65 verifies only that the recorded paper figure can be rendered and
sampled into finite color-family momentum curves. It does not verify:

- M-ABD/RBD/reference curve identity;
- agreement between Newton output and paper curves;
- paper-faithful M-ABD stepping;
- contact or collision handling;
- timing;
- any passed `experiment.*` claim;
- full paper reproduction.
