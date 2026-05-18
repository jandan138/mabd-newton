# Phase56 T-Handle MABD Newton Diagnostic Design

## Goal

Phase56 adds a Newton-derived M-ABD diagnostic lane for
`experiment.single_body.t_handle`. The immediate goal is to replace the current
`mabd_newton_report_missing` blocker with auditable incomplete MABD evidence
while preserving all paper-faithfulness boundaries.

This phase does not make the T-handle geometry, raw waveform agreement, timing,
or full paper experiment pass. It only adds a finite, machine-checkable
`mabd_newton` report produced through vendored Newton `SolverMABD.step()`.

## Current Evidence

The T-handle config and Phase43 evidence currently provide:

- a source-backed torque-free RK4 reference lane;
- reference step size `h = 0.0001 s`;
- duration `4.0 s`;
- `9` samples;
- principal inertia diagnostic values `[1.0, 2.0, 3.0]`;
- initial angular velocity `[0.03, 3.0, 0.0]`;
- zero gravity;
- a public T-handle PDF hash;
- retained blockers for exact geometry, raw curves, missing MABD report,
  missing comparison report, and timing evidence.

The experiment matrix still lists required lanes `mabd_newton` and
`rbd_rk4_reference`, with `mabd_newton_report_missing` as a current blocker.

## Design

Add a `mabd_newton` config section to
`configs/experiments/single_body_t_handle.yaml`:

```yaml
mabd_newton:
  time_step_s: 0.001
  step_count: 4000
  sample_count: 9
  rest_points_m: [...]
  point_masses_kg: [0.25, 0.25, 0.25, 0.25]
  volume_m3: 1.0
  rotation_mode: polar
  initial_angular_velocity_rad_s: [0.03, 3.0, 0.0]
  gravity_m_s2: [0.0, 0.0, 0.0]
  output_report: reports/experiment_matrix/single_body_t_handle_mabd_newton.json
```

The rest points form a non-degenerate four-point proxy. A degenerate planar
proxy can exactly match the configured principal inertia triplet, but that
would make the affine mass matrix singular for the current CPU oracle Cholesky
path. Phase56 therefore records the proxy inertia separately from the RK4
reference inertia and keeps `exact_t_handle_geometry_unknown` as a blocker.

The implementation will:

- parse and validate `mabd_newton` as a new `THandleMABDNewtonConfig`;
- require `step_count * time_step_s == reference.duration_s`;
- require `sample_count == reference.sample_count`;
- require zero gravity and positive point masses;
- require a distinct lane-specific output report under the T-handle matrix
  stem;
- build a Newton `ModelBuilder` with `mabd:body` and disabled `mabd:gravity`
  rows;
- execute `SolverMABD.step()` through the model-derived CPU oracle path;
- record sample times, affine angular-velocity diagnostics, energy drift,
  angular momentum drift, proxy inertia mismatch, max affine shape spread, and
  Newton custom-frequency provenance;
- add `write_t_handle_mabd_newton_report`;
- add `run_t_handle_mabd_newton` and CLI lane `t_handle_mabd_newton`;
- update the experiment matrix blocker from `mabd_newton_report_missing` to
  `mabd_newton_report_incomplete`;
- update Phase43 validation to accept the later blocker wording while adding a
  stricter Phase56 validator for the new report.

## Claim Boundaries

Phase56 may claim:

- a Newton `SolverMABD.step()` diagnostic report exists for the T-handle
  required `mabd_newton` lane;
- the report covers the same 0 to 4 second sample grid as the RK4 diagnostic;
- the report is finite and machine-checkable;
- the matrix no longer has a missing-MABD-report blocker for T-handle.

Phase56 must not claim:

- a passed T-handle experiment;
- a passed T-handle MABD lane;
- paper-faithful T-handle geometry or inertia;
- raw paper waveform agreement;
- a comparison report pass;
- paper timing reproduction;
- rendered output or videos;
- comparative baseline results beyond the generated RK4 and MABD diagnostics;
- full paper reproduction.

## Validation

Required checks:

- RED/GREEN tests for `mabd_newton` config parsing and validation;
- RED/GREEN tests for `roll_out_t_handle_mabd_model_derived`;
- RED/GREEN tests for report writer, runner, and CLI lane;
- regenerated `reports/experiment_matrix/single_body_t_handle_mabd_newton.json`
  stamped with the implementation source commit;
- updated claim boundaries, paper experiment matrix, Phase56 record, and docs
  validator;
- run:
  - `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests`;
  - `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py`;
  - `PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"`;
  - `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .`;
  - `git diff --check`.
