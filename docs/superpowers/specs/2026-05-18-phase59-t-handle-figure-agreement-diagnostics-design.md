# Phase59 T-Handle Figure Agreement Diagnostics Design

## Goal

Add bounded numeric diagnostics that compare current T-handle RK4 and M-ABD
diagnostic lane samples against the Phase58 digitized paper-figure color-family
curves. The diagnostics must make the figure comparison more machine-checkable
without claiming raw paper agreement, paper-faithful T-handle geometry, legend
identity, or a passed experiment.

## Scope

Phase59 covers `experiment.single_body.t_handle` only. It consumes the existing
`rbd_rk4_reference`, `mabd_newton`, and `paper_figure_digitization` reports and
augments the T-handle comparison report with deterministic curve-error
diagnostics.

The comparison uses the current diagnostic lane samples, not authors' raw data.
The paper figure x-axis is represented by the Phase58 digitizer as `0..100`.
The T-handle diagnostic lanes use a configured simulation horizon in seconds.
Phase59 maps each diagnostic sample time to figure time by:

```text
figure_time = diagnostic_time_s / diagnostic_duration_s * 100
```

The report must record that this is a normalized figure-time mapping, not paper
raw time alignment.

## Data Model

The T-handle lane reports gain per-sample `relative_energy_loss` values:

- RK4 reference samples compute energy from the reported angular velocity and
  configured principal inertia.
- M-ABD samples compute relative energy loss from the already reported sample
  energy and rollout initial energy.

The comparison report gains:

- `digitized_figure_curve_agreement_diagnostics`
- `digitized_figure_curve_agreement_available`
- `digitized_figure_curve_agreement_passed = false`

Diagnostics are recorded for two metric families:

- `intermediate_axis_angular_velocity_waveform`
- `energy_loss`

For each metric family and each lane, the report records:

- `status`
- `lane`
- `metric`
- `time_normalization`
- `matched_sample_count`
- `best_color_family`
- `best_rmse`
- `best_max_abs_error`
- `all_color_family_errors`

The best color family is a numeric minimum over the three color families. It is
not a legend-entry identity claim.

Each diagnostic entry must persist machine-checkable caveats:

- `time_normalization.claim_status = "normalized_figure_time_not_paper_raw_time"`
- `best_color_family_claim_status = "numeric_best_fit_not_legend_identity"`
- `agreement_claim_status = "diagnostic_only_not_curve_agreement"`

## Error Calculation

For each lane sample:

1. Validate finite sample time and finite lane value.
2. Normalize lane sample time to the digitized figure time range.
3. Linearly interpolate the digitized color-family curve at that normalized
   figure time.
4. Compute lane minus digitized-curve error.

For each color family, record:

- `rmse`
- `max_abs_error`
- `mean_error`
- `matched_sample_count`

If no valid samples are available, the diagnostic status is
`missing_finite_lane_samples`.

## Claim Boundaries

Phase59 must keep these blockers:

- `exact_t_handle_geometry_unknown`
- `raw_t_handle_reference_curve_data_missing`
- `mabd_newton_report_incomplete`
- `t_handle_comparison_report_incomplete`
- `t_handle_timing_evidence_missing`
- `t_handle_comparison_pass_gate_not_enabled`
- `sample_grid_flip_delta_unavailable`
- `t_handle_digitized_figure_curve_agreement_not_passed`

Phase59 must not claim:

- passed T-handle experiment
- passed M-ABD T-handle lane
- authors' raw simulation or curve data
- solid/dashed line-style separation
- legend-entry curve identity
- paper-faithful T-handle geometry or inertia
- raw waveform agreement
- paper energy-loss agreement
- comparison pass gate
- paper timing
- rendered-output evidence
- full paper reproduction
- any passed `experiment.*` claim

## Testing

Tests must be written before implementation:

1. RK4 and M-ABD T-handle lane reports expose finite
   `relative_energy_loss` samples.
2. A T-handle comparison report with a valid figure report records finite
   angular-velocity and energy-loss curve-error diagnostics for both lanes.
3. The comparison report retains incomplete status and all required blockers.
4. Invalid or missing figure reports continue to omit figure-agreement
   diagnostics.

## Validation

Phase59 completion requires:

- focused T-handle unit tests
- `scripts/validate_docs.py`
- full `unittest discover`
- vendored Newton import check
- `ruff check .`
- `git diff --check`

The dated Phase59 record must include the command, config path, repo commit,
vendored Newton source commit, paper source version, environment, backend, seed
status, metrics, thresholds, raw artifacts, report hashes, retained blockers,
and incomplete status.
