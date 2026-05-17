# Phase 43 T-Handle RK4 Reference Design

## Goal

Add a machine-checkable RK4 reference diagnostic lane for
`experiment.single_body.t_handle`. This phase records source-backed T-handle
inputs and a bounded procedural rigid-body reference, but it does not pass the
T-handle experiment and does not claim paper-faithful geometry.

## Paper Source

- `/tmp/mabd-paper/source/sections/experiment.tex:57-75`
- `/tmp/mabd-paper/source/images/T-handle/T-handle.pdf`
- T-handle figure PDF sha256:
  `5ae6464fd7e7e6fd471ad56e67cdbead6014736cb731a232ce29d80630a72c1c`
- The paper states zero gravity, angular velocity aligned with the
  intermediate principal axis, initial angular speed `omega_0 = 3 rad/s`,
  subtle mass-distribution asymmetry, and an implicit RBD RK4 reference at
  `h = 10^-4 s`.
- The public TeX/PDF assets do not disclose the exact T-handle geometry,
  principal inertias, asymmetry magnitude, mesh, or raw plotted reference data.

## Design

Create `configs/experiments/single_body_t_handle.yaml` with the claim id,
scene id, paper source lines, paper values, figure hash, procedural diagnostic
parameters, report status `incomplete`, and a lane-specific output report path
under the matrix output stem. The matrix canonical claim report remains
`reports/experiment_matrix/single_body_t_handle.json`; Phase 43 writes only
`reports/experiment_matrix/single_body_t_handle_rk4_reference.json`. The config
must match the existing `paper_experiment_matrix.yaml` entry and keep
`exact_t_handle_geometry_unknown` plus
`raw_t_handle_reference_curve_data_missing`.

Add `mabd_reproduction.t_handle_reference` for a torque-free rigid-body RK4
reference in principal axes. The helper integrates Euler's equations with
diagonal positive inertias, zero gravity, fixed time step, finite step count,
and deterministic samples. The configured inertia and perturbation are
development diagnostics only, chosen to expose intermediate-axis sign flips;
they are not paper geometry.

Add a `t_handle_rk4_reference` report writer and runner lane. The report emits
a full-schema `ClaimReport` with:

- `baseline_lane = rbd_rk4_reference`
- `solver_mode = t_handle_torque_free_rk4_reference`
- `backend = cpu_numpy`
- finite sampled body-frame angular velocity values
- sign-flip count along the intermediate principal axis
- relative energy drift and angular momentum norm drift
- `full_experiment_claim_passed = false`
- blockers including `exact_t_handle_geometry_unknown`,
  `raw_t_handle_reference_curve_data_missing`,
  `mabd_newton_report_missing`, and `t_handle_comparison_report_missing`

The report status remains `incomplete` and the matrix/paper-claims status
remains non-passed.

## Boundaries

- This phase does not implement a Newton M-ABD T-handle lane.
- This phase does not implement an implicit RBD production baseline in Newton.
- This phase does not reconstruct paper geometry, mesh, mass distribution, or
  raw figure curves.
- This phase does not compare ABD against RBD.
- This phase does not produce timing evidence or the paper's `30% faster`
  claim.
- This phase does not change any `experiment.*` claim to `passed`.

## Validation

- Unit tests cover strict T-handle config parsing and matrix alignment.
- Unit tests cover RK4 deterministic finite output, zero-gravity source inputs,
  positive inertia validation, approximate energy preservation, and at least one
  intermediate-axis sign flip for the configured diagnostic horizon.
- Runner tests cover report writing and CLI dispatch.
- Docs validators require Phase43 spec, plan, record, config, report, claim
  boundaries, report sha256, source provenance, and non-overclaim language.
- Report provenance must use the implementation commit that can replay the
  lane, not the base main commit.
