# Phase 51 Heavy-Top Comparison Protocol Design

## Goal

Create a machine-checkable heavy-top comparison protocol that consumes the
existing `rbd_rk4_reference` and `mabd_newton` diagnostic lane reports and
writes `reports/experiment_matrix/single_body_heavy_top_comparison.json`.

## Claim Boundary

Phase 51 is not a passed heavy-top experiment. It does not remove the public
source gaps for exact heavy-top inertia, exact heavy-top geometry, or raw paper
precession/nutation curve data. It does not produce paper timing evidence,
rendered output, video, or a paper-faithful ABD-vs-RBD pass gate.

The report remains `incomplete` and keeps
`full_experiment_claim_passed = false`.

## Inputs

- `reports/experiment_matrix/single_body_heavy_top_rk4_reference.json`
- `reports/experiment_matrix/single_body_heavy_top_mabd_newton.json`
- `configs/experiments/single_body_heavy_top.yaml`
- `configs/experiments/paper_experiment_matrix.yaml`

The input lane identities are strict:

- `rbd_rk4_reference` must use solver mode
  `heavy_top_rk4_reference_diagnostic`, backend `cpu_numpy`, report status
  `incomplete`, and procedural heavy-top asset hash.
- `mabd_newton` must use solver mode `mabd_cpu_oracle_heavy_top_newton_lane`,
  backend `cpu_numpy_newton_only`, report status `incomplete`, and procedural
  heavy-top asset hash.

## Output Contract

`single_body_heavy_top_comparison.json` records:

- input report provenance with paths, SHA256 digests, source commits, vendored
  Newton commits, solver modes, backends, baseline lanes, and statuses;
- lane observed statuses and solver modes;
- finite lane metric snapshots for nutation range, precession velocity,
  energy drift where available, pivot residual, constraint residual, and affine
  shape spread;
- sample-index diagnostic differences between compact
  `precession_nutation_samples` rows;
- explicit missing paper metrics:
  `nutation_angle_error:paper_reference_curve_missing`,
  `precession_velocity_error:mabd_precession_velocity_samples_missing`, and
  `energy_drift:mabd_energy_drift_missing`;
- explicit blockers including `heavy_top_comparison_pass_gate_not_enabled`,
  `mabd_newton_report_incomplete`, `heavy_top_comparison_report_incomplete`,
  `exact_heavy_top_inertia_unknown`, `exact_heavy_top_geometry_unknown`,
  `raw_heavy_top_reference_curve_data_missing`, and
  `heavy_top_timing_evidence_missing`.

The output report status remains `incomplete`.

## Config Changes

`single_body_heavy_top.yaml` gains:

```yaml
comparison:
  output_report: reports/experiment_matrix/single_body_heavy_top_comparison.json
  required_lanes:
    - mabd_newton
    - rbd_rk4_reference
  required_metrics:
    - precession_velocity_error
    - nutation_angle_error
    - energy_drift
  thresholds:
    max_sample_time_delta_s: 1.0e-12
```

The paper claim and matrix blockers replace
`heavy_top_comparison_report_missing` with
`heavy_top_comparison_report_incomplete`.

## Non-Goals

- No `experiment.*` claim is marked `passed`.
- No raw paper curve digitization or figure-matching gate is introduced.
- No paper-faithful heavy-top inertia or geometry is asserted.
- No Newton contact, rendering, GPU/Warp timing, or external baseline adapter is
  claimed.
