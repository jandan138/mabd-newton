# Phase57 T-Handle Comparison Protocol Design

## Goal

Phase57 adds a machine-checkable T-handle comparison protocol report at
`reports/experiment_matrix/single_body_t_handle_comparison.json`.

The report consumes the existing RK4 diagnostic lane and the existing Newton
`mabd_newton` diagnostic lane. It records sample-grid alignment, angular
velocity waveform deltas, first intermediate-axis flip timing diagnostics,
energy-drift snapshots, input report provenance, and explicit blockers.

This phase does not pass the T-handle paper experiment. It replaces the current
`t_handle_comparison_report_missing` blocker with
`t_handle_comparison_report_incomplete` while preserving all geometry, raw
curve, MABD-lane, and timing boundaries.

## Current Evidence

The T-handle experiment already has:

- `reports/experiment_matrix/single_body_t_handle_rk4_reference.json` from the
  torque-free RK4 diagnostic lane;
- `reports/experiment_matrix/single_body_t_handle_mabd_newton.json` from the
  Newton `SolverMABD.step()` diagnostic lane;
- source-backed config values for `h = 0.0001 s`, duration `4.0 s`, `9`
  samples, zero gravity, and initial angular velocity `[0.03, 3.0, 0.0]`;
- retained blockers for exact T-handle geometry, raw paper waveform data,
  incomplete MABD evidence, missing comparison report, and missing timing
  evidence.

The MABD report is deliberately incomplete and proxy-based. Its affine proxy
does not establish paper-faithful T-handle geometry or raw waveform agreement.

## Design

Add a `comparison` config section to
`configs/experiments/single_body_t_handle.yaml`:

```yaml
comparison:
  output_report: reports/experiment_matrix/single_body_t_handle_comparison.json
  required_lanes:
    - mabd_newton
    - rbd_rk4_reference
  required_metrics:
    - flip_timing_error
    - intermediate_axis_angular_velocity_waveform
    - energy_loss
  thresholds:
    max_sample_time_delta_s: 1.0e-12
```

The implementation reuses the established `comparison_reports.py` pattern used
by spinning-box, physical-pendulum, and heavy-top reports.

The report writer will:

- strictly validate input report identity: claim id, scene id, baseline lane,
  solver mode, backend, status, procedural asset hash, and
  `full_experiment_claim_passed = false`;
- strictly validate the semantic scope fields that keep the comparison bounded:
  RK4 `reference_not_paper_geometry = true`,
  RK4 `reference_scope = torque_free_principal_axis_rk4_diagnostic`,
  MABD `reference_not_paper_geometry = true`,
  MABD `mabd_diagnostic_scope = t_handle_model_derived_proxy`, and
  MABD `solver_model_config_source = newton_model_derived`;
- record SHA256 provenance for both input reports;
- match `angular_velocity_samples` by `sample_index`;
- record unmatched rows and nonfinite input diagnostics without writing bare
  `NaN` or `Infinity`;
- compute per-sample `mabd_minus_rk4` angular velocity component deltas;
- compute max absolute angular velocity delta across all three components;
- compute `intermediate_axis_waveform_rmse_rad_s` only over matched samples
  that are finite and whose time difference is at or below
  `max_sample_time_delta_s`; when no such aligned sample set exists, record
  `null` and add a time-alignment blocker;
- compute first sign-flip time along the configured intermediate axis using
  only sample-grid linear interpolation. Exact zero is treated as a crossing at
  that sample time. If no crossing exists, record `null` plus an unavailable
  status. This is not the RK4 step-resolution flip count and not paper timing;
- snapshot signed `relative_energy_drift` for each lane and the MABD-minus-RK4
  signed drift delta when both are finite. The paper metric remains
  `energy_loss`; signed drift is recorded only as a diagnostic, not a paper loss
  value;
- record explicit `paper_metric_statuses` for `flip_timing_error`,
  `intermediate_axis_angular_velocity_waveform`, and `energy_loss`, each marked
  diagnostic-only or unavailable rather than passed;
- keep the output report status `incomplete`;
- keep `full_experiment_claim_passed = false`;
- emit blockers including `exact_t_handle_geometry_unknown`,
  `raw_t_handle_reference_curve_data_missing`,
  `mabd_newton_report_incomplete`,
  `t_handle_comparison_report_incomplete`,
  `t_handle_comparison_pass_gate_not_enabled`, and
  `t_handle_timing_evidence_missing`.

The comparison protocol will not create a pass gate. It is a bounded diagnostic
that makes the missing comparison artifact auditable.

## Claim Boundaries

Phase57 may claim:

- a T-handle RK4-vs-MABD comparison report exists;
- the report consumes the committed RK4 and MABD diagnostic reports;
- the report validates lane identity and input provenance;
- the report records finite sample alignment and waveform diagnostics where
  finite samples are available;
- the matrix no longer has a missing-comparison-report blocker.

Phase57 must not claim:

- a passed T-handle experiment;
- a passed T-handle MABD lane;
- paper-faithful T-handle geometry or inertia;
- raw paper waveform agreement;
- a comparison pass gate;
- paper timing reproduction;
- rendered output, videos, or runtime performance;
- full M-ABD method completion or full paper reproduction.

## Validation

Required checks:

- RED/GREEN tests for `comparison` config parsing and validation;
- RED/GREEN tests for the comparison report writer, including identity rejection
  and nonfinite input handling;
- RED/GREEN tests for `run_t_handle_comparison` and CLI lane
  `t_handle_comparison`;
- generated `reports/experiment_matrix/single_body_t_handle_comparison.json`
  stamped with the implementation source commit;
- updated paper matrix, paper claim boundaries, Phase57 record, and docs
  validator;
- run:
  - `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests`;
  - `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py`;
  - `PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"`;
  - `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .`;
  - `git diff --check`.
