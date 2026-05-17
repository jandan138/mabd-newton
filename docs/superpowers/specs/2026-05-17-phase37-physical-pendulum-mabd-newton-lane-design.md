# Phase 37 Physical Pendulum MABD Newton Lane Design

## Objective

Add a bounded `mabd_newton` report lane for
`experiment.single_body.physical_pendulum`.

The lane will reuse the existing Newton-only M-ABD CPU oracle physical-pendulum
rollout, but it will emit a formal required-lane report with additional
diagnostics that the Phase 36 comparison protocol can consume:

- M-ABD phase drift against the analytic reference.
- M-ABD world-anchor dual reaction samples from the dense KKT solve.
- A report identity of `baseline_lane = mabd_newton`.

This phase does not pass the physical-pendulum paper experiment.

## Current Gap

Phase 36 records a comparison protocol over three existing inputs:

- `analytic_reference`
- `physical_pendulum_mabd_development_diagnostic`
- `rbd_implicit_baseline`

The report correctly blocks on `mabd_newton_missing`. The M-ABD diagnostic also
records angle error, pivot residual, and constraint residual only. It does not
record per-sample phase drift or any force-like world-anchor reaction signal
from the KKT dual variables.

## Selected Design

Create a second M-ABD physical-pendulum report writer:

```python
write_physical_pendulum_mabd_newton_report(
    path,
    config=config,
    source_commit=source_commit,
    vendored_newton_commit=vendored_newton_commit,
)
```

The writer uses the same rollout function as the development diagnostic. The
rollout is extended to capture the world-anchor KKT dual vector for each step
after the first solve. For sampled step zero the vector is `[0, 0, 0]`; for
later samples it is the most recent dense KKT world-constraint `dlambda` block.

The report identity is:

- `baseline_lane = mabd_newton`
- `solver_mode = mabd_cpu_oracle_physical_pendulum_newton_lane`
- `backend = cpu_numpy_newton_only`
- `status = incomplete`
- `observed.full_experiment_claim_passed = False`

The report records:

- `max_abs_angle_error_rad`
- `max_phase_drift_rad`
- `max_pivot_residual_m`
- `max_constraint_residual_norm`
- `max_world_anchor_reaction_magnitude_n`
- `angle_samples_rad`, including `phase_drift_rad`,
  `world_anchor_reaction_vector_n`, and
  `world_anchor_reaction_magnitude_n`

The diagnostic lane remains in place. This avoids rewriting Phase 34 evidence
and keeps the older report available for provenance comparison.

## Comparison Protocol Update

Extend `write_physical_pendulum_comparison_report` to accept the formal
`mabd_newton` lane in addition to the existing development diagnostic lane.

For Phase 37 committed evidence, the comparison should be regenerated with:

- `--mabd-report reports/experiment_matrix/single_body_physical_pendulum_mabd_newton.json`

The comparison report should then show:

- `missing_required_lanes = []`
- `lane_metrics.mabd_newton.max_phase_drift_rad`
- `lane_metrics.mabd_newton.max_world_anchor_reaction_magnitude_n`
- MABD/RBD angle sample differences aligned by `(step, time_s)`
- `paper_metric_statuses.phase_drift.status = diagnostic_available`
- `paper_metric_statuses.joint_force_error.status =
  diagnostic_reaction_not_paper_waveform`

The report must remain incomplete because the force signal is a diagnostic KKT
reaction for the procedural world anchor, not a paper-faithful joint-force
waveform, and because paper geometry and timing remain unavailable.

## Config Update

Add a `mabd_newton` block to
`configs/experiments/single_body_physical_pendulum.yaml`.

The block contains:

- `output_report`
- `thresholds.max_abs_angle_error_rad`
- `thresholds.max_phase_drift_rad`
- `thresholds.max_pivot_residual_m`
- `thresholds.max_constraint_residual_norm`
- `thresholds.max_world_anchor_reaction_magnitude_n`

The physical-pendulum config validator must require that `mabd_newton` output
is a lane-specific JSON report under the experiment-matrix output stem and is
distinct from analytic, development, RBD, and comparison reports.

The top-level `required_missing_lanes` remains `["mabd_newton"]` for this
phase. It describes the full paper lane still being incomplete, not the
presence of a formal report artifact.

## Alternatives Considered

### Promote the existing diagnostic report in place

Changing `physical_pendulum_mabd_development_diagnostic` into `mabd_newton`
would erase useful provenance from Phase 34 and make old records ambiguous.
Keeping both reports is clearer.

### Mark joint-force error as available

The KKT dual reaction has force units and is useful for diagnostics, but it is
not the paper's joint-force waveform agreement. The comparison must keep a
specific non-claim status instead of treating it as a paper metric pass.

### Attempt paper geometry in this phase

The paper geometry remains underspecified in the current source audit. Phase 37
only adds a missing required-lane artifact and dual-reaction diagnostics. A
later phase can either recover geometry from source assets or keep
`pendulum_geometry_unknown` as a blocker.

## Validation

Tests must prove:

- physical-pendulum config parsing requires the `mabd_newton` block and
  rejects missing thresholds and report path collisions.
- the M-ABD rollout emits finite `phase_drift_rad` and finite
  `world_anchor_reaction_*` fields on compact samples.
- the new `mabd_newton` report has the required lane identity but remains
  incomplete.
- the comparison writer accepts `mabd_newton` as the M-ABD input lane and
  rejects a diagnostic report when the formal lane is required.
- the regenerated comparison report has no missing required lanes, but still
  blocks on paper geometry, paper timing, and non-paper force waveform status.
- docs/provenance validation requires the Phase 37 spec, plan, record, M-ABD
  Newton report artifact, and regenerated comparison report.
- `experiment.single_body.physical_pendulum` remains unpassed in
  `docs/reference/paper-claims.yaml`.

## Claim Boundaries

Allowed Phase 37 claims:

- a formal physical-pendulum `mabd_newton` report artifact exists
- the report is generated by the Newton-only M-ABD CPU oracle path
- the report contains phase-drift and world-anchor dual-reaction diagnostics
- the comparison protocol can consume the formal `mabd_newton` lane

Forbidden Phase 37 claims:

- the physical-pendulum paper experiment is passed
- the procedural pendulum geometry is paper-faithful
- the world-anchor dual reaction is the paper joint-force waveform
- paper timing or rendering is verified
- any `experiment.*` paper claim is passed
