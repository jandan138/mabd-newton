# Phase 28 Spinning-Box Paper Horizon Design

Date: 2026-05-17

## Objective

Phase 28 replaces the current four-step spinning-box M-ABD smoke evidence with
a paper-horizon diagnostic protocol for Fig. cube: 10 seconds at `h = 1e-2`
and `h = 1e-3`, using the paper's stated cube size, density, material
parameters, initial linear momentum, and initial angular momentum. The phase
does not pass the M-ABD lane or the full spinning-box experiment unless the
paper-horizon diagnostics meet explicit thresholds.

## Current Gap

The current `mabd_newton` report for
`experiment.single_body.spinning_box` is a configured development lane. It
runs only four 10 ms steps. It records paper momenta, physical mass, material
stiffness, trajectory samples, and affine shape diagnostics, but remains
`status=incomplete` with `affine_shape_diagnostic_status =
development_gap_observed`.

The paper source describes the spinning-box figure as a 10 second comparison
with `h = 1e-2` and `h = 1e-3` curves for co-rotated ABD, implicit RBD, and a
reference. The current report cannot support or falsify that figure-level
claim because it does not run the paper horizon or the paper step-size grid.

## Design

Phase 28 adds a separate paper-horizon M-ABD diagnostic path rather than
changing the existing development report in place. The new path runs the
existing Newton M-ABD CPU oracle for each configured paper step size. It scans
every integration step for extrema and threshold violations, while storing only
a compact `trajectory_samples` subset in the JSON report. The every-step scan
must summarize final, minimum, maximum, and step-index information for:

- linear momentum error;
- angular momentum error;
- kinetic energy and relative kinetic-energy drift;
- elastic potential energy;
- total mechanical energy and relative total-energy drift;
- affine determinant;
- affine singular values;
- affine orthogonality error;
- solver residual norm;
- finite-state status.

The diagnostic report is machine-readable and intentionally conservative. It
does not use `lane_gate_status`, because that field is currently validated and
consumed as the Phase 27 RBD-only required-lane gate. Phase 28 instead records
diagnostic-only status fields. A future M-ABD pass gate must add its own
explicit schema, validator checks, comparison semantics, and dated claim
boundary record. Phase 28 is expected to keep the lane incomplete if the
current solver shows large affine shape drift or energy loss. That incomplete
result is progress because it turns an untested paper-scene gap into
reproducible evidence.

## Report Contract

The report remains a top-level
`experiment.single_body.spinning_box` claim report with
`baseline_lane = "mabd_newton"`, `status = "incomplete"`, and a failure reason
that names the paper-horizon M-ABD gap. The report uses a new solver mode:

```text
mabd_cpu_oracle_paper_horizon_diagnostic
```

The report `observed` payload must include:

- `paper_horizon_duration_s = 10.0`;
- `paper_step_sizes_s = [0.01, 0.001]`;
- `paper_source_lines` pointing to the local TeX source lines for the figure;
- `figure_text_source` identifying the extracted figure/PDF text used for the
  10 second axis and `h = 1e-2`, `h = 1e-3` labels;
- `figure_pdf_sha256` for `/tmp/mabd-paper/source/images/cube/roll_cube.pdf`;
- one result entry per step size;
- finite metric snapshots for each entry;
- `steps_attempted`, `steps_completed`, and `first_nonfinite_step` for each
  step size;
- `threshold_violations` for each failed named threshold;
- `mabd_paper_horizon_status = "development_gap_observed"` when any required
  diagnostic violates the configured thresholds;
- `blocking_reasons` including `mabd_newton_report_incomplete`.

The report must not use the Phase 27 RBD lane-pass gate constants. It must not
set `status = "passed"` for an `experiment.*` report. It must not write
`observed["lane_gate_status"]`, so the existing comparison protocol continues
to treat the M-ABD lane as incomplete.

## Config Impact

`configs/experiments/single_body_spinning_box.yaml` keeps the four-step smoke
settings for fast unit tests and local development. Phase 28 adds a nested
paper-horizon section with:

- `duration_s = 10.0`;
- `time_step_grid_s = [0.01, 0.001]`;
- `sample_count` small enough to keep JSON reports compact;
- named finite thresholds with units for:
  `max_linear_momentum_error`,
  `max_angular_momentum_error`,
  `max_relative_kinetic_energy_drift`,
  `max_relative_total_energy_drift`,
  `max_abs_det_minus_one`,
  `min_singular_value`,
  `max_singular_value`,
  `max_affine_orthogonality_error`, and `max_residual_norm`.
- `output_report` for the paper-horizon diagnostic so it cannot overwrite the
  existing four-step development report.

The experiment matrix keeps:

- `mabd_newton_report_incomplete`;
- `spinning_box_comparison_report_incomplete`.

`docs/reference/paper-claims.yaml` remains unchanged for
`experiment.single_body.spinning_box`; no `experiment.*` claim is marked
passed in Phase 28.

## Non-Goals

Phase 28 does not:

- pass `experiment.single_body.spinning_box`;
- pass the `mabd_newton` lane;
- enable the spinning-box comparison pass gate;
- modify the RBD lane gate from Phase 27;
- claim paper-faithful affine collision, implicit contact, gravity, friction,
  rendered agreement, or paper timing;
- hide affine shape drift behind momentum-only thresholds;
- introduce external MuJoCo, Bullet, PhysX, VQ, RK4, or analytic baselines.

## Evidence

Evidence must include:

- tests proving the config parses the paper-horizon duration, step grid,
  sample count, and thresholds;
- tests proving the paper-horizon diagnostic runner records both `h = 1e-2`
  and `h = 1e-3`;
- tests proving all recorded scalars and vectors are finite;
- tests proving extrema and threshold violations are computed from every
  integration step, not only from compact `trajectory_samples`;
- tests proving kinetic, elastic, and total mechanical energy are separate
  fields, and that kinetic drift is not labeled as paper total-energy evidence;
- tests proving current M-ABD paper-horizon diagnostics stay incomplete when
  shape or energy thresholds are violated;
- tests proving the Phase 28 M-ABD report has no `lane_gate_status`, and that
  the comparison report still records `lane_gate_statuses["mabd_newton"] =
  "incomplete"` and keeps `mabd_newton_report_incomplete`;
- tests proving the existing four-step development report remains available;
- updated claim boundaries and a Phase 28 record that states the current M-ABD
  lane is still incomplete;
- a Phase 28 record with config paths, repository commit, vendored Newton
  provenance, paper source version, paper PDF/TeX checksums or previously
  recorded checksum references, local TeX source lines, figure/PDF text
  extraction provenance, backend label, seed policy, generated report paths,
  raw artifact policy, metrics, thresholds, status, and whether vendored Newton
  was modified;
- full validation through the canonical isolated Python environment.
