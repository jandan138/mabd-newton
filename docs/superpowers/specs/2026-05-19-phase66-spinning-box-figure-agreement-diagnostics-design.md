# Phase 66 Spinning-Box Figure Agreement Diagnostics Design

## Objective

Add a bounded spinning-box digitized-paper-figure agreement diagnostic to the
existing spinning-box comparison report. The diagnostic consumes the Phase 65
`single_body_spinning_box_figure_curves.json` report, compares available
Newton/RBD lane momentum diagnostics against the paper-figure color-family
curves, and records finite best-fit error summaries without claiming paper
curve agreement or passing the spinning-box experiment.

## Current Evidence

- `reports/experiment_matrix/single_body_spinning_box_figure_curves.json`
  contains color-family samples for angular and linear momentum from
  `roll_cube.pdf`.
- `reports/experiment_matrix/single_body_spinning_box_comparison.json`
  currently compares M-ABD and RBD lane scalar/vector metrics but does not
  consume the paper-figure digitization report.
- The T-handle comparison lane already records a similar diagnostic via
  `digitized_figure_curve_agreement_diagnostics`; Phase 66 should reuse that
  report vocabulary where it fits.

## Scope

Phase 66 adds:

- an optional `figure_curve_report_path` parameter to
  `write_spinning_box_comparison_report`;
- an optional `figure_curve_report_path` parameter to
  `run_spinning_box_comparison`;
- `scripts/run_experiment.py --lane spinning_box_comparison --figure-report ...`
  dispatch support;
- comparison-report observed fields:
  - `digitized_figure_reference_available`;
  - `digitized_figure_reference_samples`;
  - `digitized_figure_curve_agreement_available`;
  - `digitized_figure_curve_agreement_passed = false`;
  - `digitized_figure_curve_agreement_diagnostics`;
  - `input_report_provenance.paper_figure_curves`;
- regenerated
  `reports/experiment_matrix/single_body_spinning_box_comparison.json`;
- Phase 66 record, claim-boundary text, and `validate_docs.py` gates.

## Non-Goals

Phase 66 does not:

- pass `experiment.single_body.spinning_box`;
- infer paper legend-entry identity from color families;
- split solid and dashed line styles;
- claim the digitized curves are authors' raw simulation data;
- enable the spinning-box comparison pass gate;
- claim paper-faithful affine collision, contact, or runtime performance;
- alter `docs/reference/paper-claims.yaml` reproduction statuses.

## Diagnostic Model

The Phase 65 figure report has two curve groups:

- `angular_momentum_curves`;
- `linear_momentum_curves`.

Each group contains five color families: `blue`, `orange`, `green`, `gray`, and
`brown`. Phase 66 treats these as color-family candidates only, not as legend
entries.

The spinning-box lane reports do not currently expose time-series momentum
traces in the comparison-friendly form used by T-handle. They do expose final
diagnostic scalar values:

- `linear_momentum_error`;
- `angular_momentum_error`;
- related lane statuses and vector metrics.

Therefore Phase 66 records a conservative endpoint-style diagnostic:

- lane value source:
  - `linear_momentum_error` for `linear_momentum`;
  - `angular_momentum_error` for `angular_momentum`;
- figure value source:
  - the last sample of each color-family curve at `time_s = 10.0`;
- error:
  - `abs(lane_value - figure_value)`;
  - `signed_error = lane_value - figure_value`;
- best color:
  - the color family with the smallest finite absolute error.

This is intentionally called a diagnostic rather than agreement because the
lane values and figure values are not guaranteed to share normalization,
legend identity, or raw-data provenance.

## Report Semantics

When a valid figure report is supplied, the comparison report records:

```text
digitized_figure_reference_available = true
digitized_figure_curve_agreement_available = true
digitized_figure_curve_agreement_passed = false
```

For each metric and lane, the diagnostic entry records:

- `metric`;
- `lane`;
- `status = diagnostic_available_not_pass_gate`;
- `lane_value`;
- `lane_value_source`;
- `figure_time_s = 10.0`;
- `best_color_family`;
- `best_abs_error`;
- `best_signed_error`;
- `best_color_family_claim_status = numeric_best_fit_not_legend_identity`;
- `agreement_claim_status = diagnostic_only_not_curve_agreement`;
- `all_color_family_errors`.

The comparison report appends:

```text
spinning_box_digitized_figure_curve_agreement_not_passed
```

to `observed.blocking_reasons` when the figure diagnostic is available.

## Valid Figure Report Criteria

The figure report is valid only if:

- `status == incomplete`;
- `claim_id == experiment.single_body.spinning_box`;
- `baseline_lane == paper_figure_digitization`;
- `solver_mode == spinning_box_paper_figure_curve_digitization`;
- `observed.color_family_curve_available == true`;
- `observed.paper_reference_legend_identity_available == false`;
- `observed.curve_identity_status == color_family_not_legend_entry`;
- `observed.curve_agreement_status == not_evaluated`;
- both curve groups are present and contain finite samples.

Invalid or missing figure reports preserve current comparison behavior and set:

```text
digitized_figure_reference_available = false
digitized_figure_curve_agreement_available = false
digitized_figure_curve_agreement_passed = false
```

No pass or failure is inferred from invalid figure input.

## Claim Boundaries

Phase 66 verifies only that the spinning-box comparison report can consume the
Phase 65 paper-figure digitization and record bounded numeric diagnostics. It
does not verify paper agreement, curve identity, line-style identity, raw data,
or full experiment reproduction.

The Phase 66 record must state:

- report status remains `incomplete`;
- `digitized_figure_curve_agreement_passed = false`;
- no `experiment.*` claim is passed;
- `experiment.single_body.spinning_box.reproduction_status` remains
  `intended`.

## Verification

Required focused tests:

- `tests.test_spinning_box_comparison`;
- relevant `tests.test_experiment_runner` spinning-box comparison CLI/runner
  cases;
- `tests.test_phase0_bootstrap` Phase66 evidence and validator cases.

Required repo gates:

- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py`;
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests`;
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .`;
- `git diff --check`.
