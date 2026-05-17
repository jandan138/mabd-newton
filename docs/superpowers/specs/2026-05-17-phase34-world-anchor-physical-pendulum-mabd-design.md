# Phase 34 World-Anchor Physical Pendulum M-ABD Design

## Goal

Add the smallest Newton-first capability needed for a physical-pendulum M-ABD
development lane: a dense CPU-oracle world-anchor ball constraint plus a
bounded report that runs a short fixed-pivot, gravity-driven procedural
pendulum diagnostic.

## Scope

Phase 34 is not a full physical-pendulum reproduction. It adds:

- a vendored Newton CPU-oracle world-anchor constraint for one affine body
  point pinned to a fixed world point;
- a procedural physical-pendulum M-ABD development config block;
- an incomplete `physical_pendulum_mabd_development_diagnostic` report lane
  with finite angle, pivot residual, and analytic-reference diagnostic fields;
- CLI dispatch for the physical-pendulum M-ABD development lane;
- docs, records, and validators that keep all `experiment.*` claims unpassed.

It does not add a paper-faithful pendulum geometry, RBD implicit baseline,
joint-force waveform comparison, rendered output, or paper timing.

## Newton Design

Vendored Newton gets `MABDCPUOracleWorldConstraint` in
`newton._src.solvers.mabd.step_oracle`. The constraint stores:

- `body`: constrained body index;
- `rest_point`: local affine rest point whose world position is constrained;
- `world_point`: fixed target point in world coordinates.

For a body state `q`, the residual is
`point_jacobian(rest_point) @ q - world_point`. The gradient is the constant
`point_jacobian(rest_point)`. Dense topology is supported in Phase 34 by
assembling the world-anchor rows directly into the dense primal vector. Non-dense
topology rejects world constraints because the current topology solvers assume
body-body edges.

The result reports `world_constraint_residual_norm` through the existing
`constraint_residual_norm` field. Body-body constraints continue to work
unchanged.

## Physical-Pendulum Lane

The config gains a `mabd_development` block with:

- procedural rest points and masses that form a nondegenerate affine body;
- `pivot_rest_point_m` and `pivot_world_point_m`;
- `angle_probe_rest_point_m`;
- `gravity_m_s2`, `time_step_s`, `step_count`;
- an output report path and thresholds for finite-state, pivot residual, and
  angle error diagnostics.

The report writer runs `solve_cpu_oracle_step` for the configured steps using
the world-anchor constraint and gravity. It computes the pendulum angle from
the world vector between pivot and probe point, compares compact samples to the
Phase 33 elliptic reference, and records diagnostics under top-level
`incomplete` status.

The lane status is `development_diagnostic_generated` if all values are finite
and pivot residual is below threshold. This is not a pass gate and never marks
`experiment.single_body.physical_pendulum` as passed.
The report uses a distinct diagnostic lane id so the required paper
`mabd_newton` lane can remain explicitly missing until a paper-faithful M-ABD
experiment lane exists.

## Validation And Boundaries

The config validator must keep:

- `experiment.single_body.physical_pendulum` status unpassed;
- required missing lanes including `rbd_implicit_baseline`;
- `pendulum_geometry_unknown` as a blocker;
- the M-ABD development report path distinct from the analytic-reference report.

The Phase 34 record must list base commit, vendored Newton patch status,
paper source lines, environment, deterministic seed status, metrics, thresholds,
TDD red/green results, review outcome, and final gates.
