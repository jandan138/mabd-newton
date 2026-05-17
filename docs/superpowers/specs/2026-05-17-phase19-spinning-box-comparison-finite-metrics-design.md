# Phase 19 Spinning-Box Comparison Finite Metrics Design

## Goal

Harden the spinning-box comparison protocol so required lane metrics must be
present and finite numeric values, and record cross-lane metric differences for
the existing M-ABD and RBD development reports.

## Problem

Phase 16/17 comparison reporting checks whether required metric keys exist.
That is too weak for paper reproduction evidence: `None`, `NaN`, infinities, or
non-numeric strings could be treated as available metrics. The comparison also
does not expose direct M-ABD-minus-RBD metric differences, which makes later
threshold gates harder to audit.

## Design

Keep `SPINNING_BOX_REQUIRED_METRICS` unchanged. Add helper logic in
`src/mabd_reproduction/comparison_reports.py` that classifies required metrics
as:

- missing: key absent from `report.observed`
- invalid: key present but value is not a finite scalar number
- valid: key present and finite

The comparison report keeps the existing `missing_required_metrics` field and
adds:

- `invalid_required_metrics`
- `lane_metric_differences`, with `mabd_newton_minus_rbd_implicit_baseline`
  values for metrics that are valid in both lane reports

Blocking reasons gain `<lane>:<metric>_invalid` entries for invalid required
metrics. The report remains `incomplete` because both lane reports are still
incomplete and the RBD solver mode is not paper-faithful.

## Validation

Add tests that fail on Phase 18:

- a comparison report generated from current lane reports has no missing or
  invalid required metrics and records finite metric differences
- a lane report with `observed.energy_drift = None` is not counted as missing
  but is counted as invalid and produces an invalid blocking reason
- docs validator requires Phase 19 boundary and record text

## Claim Boundaries

Phase 19 verifies only comparison-protocol metric validation and difference
recording. It does not verify the paper spinning-box experiment, paper-faithful
implicit RBD baseline, affine collision/contact, timing, trajectory agreement,
generated reports as committed evidence, or any passed `experiment.*` claim.
