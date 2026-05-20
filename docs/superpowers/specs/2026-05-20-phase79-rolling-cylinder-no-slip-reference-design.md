# Phase 79 Rolling Cylinder No-Slip Reference Design

## Scope

Phase 79 adds a fail-closed analytic no-slip rolling-cylinder reference lane for
`experiment.single_body.rolling_spinning`.

The existing Newton RBD and M-ABD rolling-cylinder lanes are development
diagnostics. They record useful local trajectories and timings, but they do not
prove that the rolling-cylinder scene itself is reproduced with a
paper-faithful contact/friction solve. Phase 79 adds a deterministic reference
for the kinematic no-slip rolling constraint implied by the paper's rigid
rolling-cylinder benchmark.

## Claim Boundary

This phase does not pass `experiment.single_body.rolling_spinning`.

The paper source gives the rolling-cylinder timing table, `10K` steps,
`h = 0.01 sec`, and the i7 single-thread context. It does not specify cylinder
dimensions, mass, initial velocities, or the exact RBD contact solver. The
reference lane therefore records an analytic no-slip physical baseline using the
project's current rolling-cylinder config parameters, and keeps the remaining
paper-faithful solver and timing blockers visible.

The report must keep these blockers visible:

- `paper_faithful_explicit_rbd_baseline_missing`
- `paper_faithful_implicit_rbd_baseline_missing`
- `paper_faithful_mabd_collision_missing`
- `paper_comparable_timing_missing`
- `paper_rbd_solver_details_missing`

The gap audit must also preserve the existing living-audit vocabulary for
remaining reproduction gaps:

- `paper_faithful_explicit_rbd_baseline`
- `paper_faithful_implicit_rbd_baseline`
- `paper_faithful_mabd_rolling_cylinder`
- `paper_comparable_timing`

## Config Contract

`configs/experiments/single_body_rolling_spinning.yaml` gets a
`rbd_no_slip_reference` section with output report:

```text
reports/experiment_matrix/single_body_rolling_spinning_rbd_no_slip_reference.json
```

The section reuses the same cylinder parameters and initial state as the RBD
development lanes through `RollingSpinningRBDBaselineConfig`, so it includes the
same `contact` keys (`ke`, `kd`, `kf`, `mu`, `gap`) and RBD threshold keys
(`max_no_slip_residual_m_s`, `max_relative_energy_drift`, `min_contact_count`,
`max_runtime_wall_time_ms`). It must explicitly validate:

- `time_step_s = 0.01`
- `step_count = 10000`
- `sample_count >= 3`
- `initial_position_m[1] = radius_m`
- `initial_linear_velocity_m_s[1] = 0`
- `initial_linear_velocity_m_s[2] = 0`
- `initial_angular_velocity_rad_s[0] = 0`
- `initial_angular_velocity_rad_s[1] = 0`
- `initial_linear_velocity_m_s[0] + radius_m * initial_angular_velocity_rad_s[2] = 0`

Center-height drift is recorded with a fixed report threshold
`max_center_height_drift_m = 1.0e-12` instead of adding a new config key to the
shared RBD threshold schema.

## Report Contract

The no-slip reference report must include:

- `claim_id = experiment.single_body.rolling_spinning`
- `scene_id = single_body_rolling_spinning`
- `baseline_lane = rbd_no_slip_reference`
- `solver_mode = analytic_no_slip_rolling_cylinder_reference`
- `backend = cpu_numpy_closed_form`
- `status = incomplete`
- `observed.reference_status = analytic_no_slip_reference_generated`
- `observed.local_runtime_measured = false`
- `observed.paper_comparable = false`
- `observed.full_experiment_claim_passed = false`
- final center position from closed-form constant-velocity rolling
- final angular velocity matching the no-slip condition
- zero no-slip residual within threshold
- zero center-height drift within threshold
- constant-energy diagnostic within threshold
- sampled trajectory points
- deterministic JSON payload across repeated runs with identical commit inputs
- no `timing_distribution.total_wall_time_ms` field
- `timing_distribution.status = not_measured`
- `timing_distribution.paper_comparable = false`
- `raw_outputs = {}`
- `plot_paths = {}`

## Acceptance Criteria

- Config tests load and validate `rbd_no_slip_reference`.
- Runner and CLI tests cover `rolling_spinning_rbd_no_slip_reference`.
- The generated report is machine-checkable and keeps the top-level experiment
  claim incomplete.
- `scripts/validate_docs.py` validates the Phase79 spec, plan, record, report,
  and fail-closed audit updates.
