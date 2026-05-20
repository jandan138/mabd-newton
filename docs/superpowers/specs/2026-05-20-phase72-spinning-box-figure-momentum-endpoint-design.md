# Phase 72 Spinning-Box Figure Momentum Endpoint Design

## Problem

The Phase 66 spinning-box paper-figure agreement diagnostic compares digitized
`roll_cube.pdf` endpoint momentum values against lane fields named
`linear_momentum_error` and `angular_momentum_error`. Those fields are errors
relative to the paper initial momenta, not the momentum values plotted in the
paper figure. This creates a diagnostic false negative with errors near `100`
even when the lane endpoint momentum magnitude is near the plotted value.

## Scope

- Update only the diagnostic comparison value source for spinning-box digitized
  figure endpoints.
- Use endpoint momentum magnitudes:
  - `final_linear_momentum_kg_m_s` for M-ABD reports when present.
  - `final_angular_momentum_kg_m2_s` for M-ABD reports when present.
  - `mass_kg * linear_velocity_m_s` for RBD reports when present.
  - `inertia_diag_kg_m2 * angular_velocity_rad_s` for RBD reports when present.
- Keep `digitized_figure_curve_agreement_passed = false`.
- Keep `agreement_claim_status = diagnostic_only_not_curve_agreement`.
- Keep `experiment.single_body.spinning_box` at `intended`.
- Do not alter solver dynamics, contact behavior, lane gates, or paper claim
  statuses.

## Non-Scope

- No paper reference legend-entry identity claim.
- No solid/dashed line-style split claim.
- No Newton-vs-paper curve agreement pass.
- No M-ABD lane pass.
- No comparison pass gate.
- No rendered-output agreement.
- No runtime-performance evidence.
- No passed `experiment.*` claim.
- No full paper reproduction claim.

## Acceptance Criteria

- `tests.test_spinning_box_comparison` proves the figure diagnostic uses
  endpoint momentum magnitude sources, not momentum error fields.
- The regenerated `reports/experiment_matrix/single_body_spinning_box_comparison.json`
  records `lane_value_source = final_linear_momentum_norm` and
  `final_angular_momentum_norm` for the digitized figure diagnostics.
- The best endpoint errors become small diagnostic values instead of the old
  near-100 false-negative values.
- Docs validation records Phase 72 as bounded diagnostic evidence only.
