# Phase 87 Spinning-Box Development Comparison Design

## Scope

Phase 87 adds a development-only internal comparison for the
`single_body_spinning_box` scene.

The lane runs the same reasonable local initial condition through:

- Newton `SolverMABD`
- Newton `SolverSemiImplicit`

It records 10 seconds of compact trajectory samples and energy-curve samples in
a JSON report:

- lane: `spinning_box_development_comparison`
- report:
  `reports/experiment_matrix/single_body_spinning_box_development_comparison.json`
- backend: `cpu_newton_warp`
- solver mode: `spinning_box_newton_mabd_rbd_development_comparison`

## Claim Boundary

This phase is a development comparison only. It is not paper-faithful, does not
enable a spinning-box pass gate, and does not pass
`experiment.single_body.spinning_box`.

The report must keep:

- `comparison_scope = development_only`
- `paper_faithful = false`
- `full_experiment_claim_passed = false`
- `status = incomplete`
- `timing_distribution.paper_comparable = false`
- `plot_paths = {}`

## Report Contract

Required fields:

- `baseline_lane = spinning_box_development_comparison`
- `solver_mode = spinning_box_newton_mabd_rbd_development_comparison`
- `backend = cpu_newton_warp`
- `observed.duration_s = 10.0`
- `observed.time_step_s = 0.01`
- `observed.step_count = 1000`
- `observed.sample_count = 101`
- `observed.mabd_solver_name = newton.solvers.SolverMABD`
- `observed.rbd_solver_name = newton.solvers.SolverSemiImplicit`
- `observed.comparison_metrics` includes momentum, energy, and position deltas
- `observed.trajectory_samples` embeds compact M-ABD and RBD samples
- `observed.energy_curve_samples` embeds compact energy samples
- `observed.blocking_reasons` includes `development_comparison_only`

## Acceptance Criteria

- Config validation accepts only the dedicated development report path and
  rejects paper-faithful comparison scope.
- Runner and CLI tests cover the new lane.
- The committed report is machine-checkable and incomplete.
- Claim boundaries and gap audit entries mark this as development-only evidence.
- No `experiment.*` claim is passed.
