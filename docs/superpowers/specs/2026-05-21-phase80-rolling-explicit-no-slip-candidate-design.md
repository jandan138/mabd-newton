# Phase 80 Rolling Explicit No-Slip Candidate Design

## Scope

Phase 80 adds a fail-closed local candidate lane for
`experiment.single_body.rolling_spinning`:

```text
rbd_explicit_no_slip_candidate
```

The lane records a deterministic no-slip projected rolling-cylinder trajectory
with local wall-clock timing. It is a Newton-first reproduction artifact because
it lives in the same config, runner, report, CLI, and validation surfaces as the
other rolling/spinning evidence, but it is not the paper's explicit RBD solver
and it is not a contact-dynamics pass gate.

## Claim Boundary

This phase does not pass `experiment.single_body.rolling_spinning`.

The paper source gives the rolling cylinder, `10K` steps, `h = 0.01 sec`,
the explicit RBD timing value `32 ms`, and `i7 CPU, single thread`. It does not
provide exact cylinder dimensions, mass, initial state, contact solver, friction
solver, or explicit RBD implementation details. Phase 80 therefore uses the
repository's current rolling-cylinder config parameters and records those
assumptions directly in the report.

The lane must keep these blockers visible:

- `newton_explicit_no_slip_candidate_not_paper_explicit_rbd_solver`
- `paper_rbd_solver_details_missing`
- `paper_no_slip_condition_inferred`
- `no_slip_projection_not_contact_dynamics`
- `paper_faithful_explicit_rbd_baseline_missing`
- `paper_faithful_implicit_rbd_baseline_missing`
- `paper_faithful_mabd_collision_missing`
- `paper_comparable_timing_missing`

The gap audit must preserve these remaining reproduction gaps:

- `paper_faithful_explicit_rbd_baseline`
- `paper_faithful_implicit_rbd_baseline`
- `paper_faithful_mabd_rolling_cylinder`
- `paper_comparable_timing`

The phase must not edit `paper-claims.yaml` experiment statuses and must not
alter the exact top-level `required_missing_lanes` for the rolling/spinning
config.

## Config Contract

`configs/experiments/single_body_rolling_spinning.yaml` gets a section:

```yaml
rbd_explicit_no_slip_candidate:
  output_report: reports/experiment_matrix/single_body_rolling_spinning_rbd_explicit_no_slip_candidate.json
```

The section reuses `RollingSpinningRBDBaselineConfig` and the same local
parameters as the current rolling-cylinder RBD lanes:

- `radius_m = 0.5`
- `half_height_m = 0.5`
- `density_kg_m3 = 1000.0`
- `time_step_s = 0.01`
- `step_count = 10000`
- `initial_linear_velocity_m_s = [1.0, 0.0, 0.0]`
- `initial_angular_velocity_rad_s = [0.0, 0.0, -2.0]`

Validation must enforce:

- lane-specific relative JSON output under `reports/experiment_matrix`
- output path distinct from all existing rolling/spinning lane reports
- `time_step_s = performance.time_step_s`
- `step_count = performance.step_count = 10000`
- `sample_count >= 3`
- cylinder center starts at `radius_m`
- no vertical or lateral initial linear velocity
- no off-axis initial angular velocity
- initial velocity satisfies `vx + radius_m * wz = 0`

## Report Contract

The report path is:

```text
reports/experiment_matrix/single_body_rolling_spinning_rbd_explicit_no_slip_candidate.json
```

The report must include:

- `claim_id = experiment.single_body.rolling_spinning`
- `scene_id = single_body_rolling_spinning`
- `baseline_lane = rbd_explicit_no_slip_candidate`
- `solver_mode = newton_explicit_no_slip_rolling_cylinder_candidate`
- `backend = cpu_numpy_projected_no_slip`
- `status = incomplete`
- `expected.paper_total_simulation_time_ms.explicit_rbd = 32.0`
- `expected.paper_comparable = false`
- `expected.full_experiment_claim_passed = false`
- `observed.candidate_status = local_no_slip_projection_generated`
- `observed.local_runtime_measured = true`
- `observed.paper_comparable = false`
- `observed.full_experiment_claim_passed = false`
- `observed.required_reproduction_gaps_remaining` preserving the four gap names
- `observed.blocking_reasons` containing all Phase80 blockers listed above
- deterministic physical state fields for mass, inertia, final pose, velocities,
  no-slip residual, energy drift, center-height drift, and trajectory samples
- `timing_distribution.total_wall_time_ms` for local runtime only
- `timing_distribution.paper_comparable = false`
- `timing_distribution.scope = local_no_slip_projection_not_paper_timing`
- `raw_outputs = {}`
- `plot_paths = {}`

The report may record local runtime, but it must not compare local runtime
against the paper's `32 ms` timing value as a pass/fail condition.

## Acceptance Criteria

- Config tests load and validate `rbd_explicit_no_slip_candidate`.
- Validation rejects path reuse, bad no-slip initial conditions, and non-paper
  step horizon for the candidate.
- Runner and CLI tests cover
  `rolling_spinning_rbd_explicit_no_slip_candidate`.
- The generated report is machine-checkable, incomplete, and preserves all
  paper-faithful rolling/spinning blockers.
- `scripts/validate_docs.py` validates the Phase80 spec, plan, record, report,
  report hash, gap audit, and claim-boundary text.
