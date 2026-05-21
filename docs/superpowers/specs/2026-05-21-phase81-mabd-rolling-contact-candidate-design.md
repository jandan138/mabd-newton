# Phase 81 MABD Rolling Contact Candidate Design

## Scope

Phase 81 adds a fail-closed rolling-cylinder M-ABD contact candidate lane for
`experiment.single_body.rolling_spinning`:

```text
mabd_rolling_contact_candidate
```

The lane uses the existing `SolverMABD.detect_static_plane_contacts()` static
plane active set and the existing `contact_constraint_mode = "world"` CPU oracle
path. Unlike the Phase 76/77 `plane` contact diagnostics, this candidate
constrains the detected affine-cylinder support point to the projected world
contact point, so tangential slip is reduced by an actual M-ABD constraint solve
rather than by a closed-form trajectory proxy.

## Claim Boundary

This phase does not pass `experiment.single_body.rolling_spinning`.

The paper source gives the rolling cylinder benchmark timing context but does
not specify exact cylinder dimensions, initial state, contact manifold,
friction/no-slip law, RBD solver implementation, or the exact affine rolling
contact solve. Phase 81 therefore records a Newton-local M-ABD contact
candidate, not a paper-faithful reproduction.

The report must keep these blockers visible:

- `mabd_rolling_contact_candidate_not_paper_faithful`
- `diagnostic_world_constraints_not_paper_friction_law`
- `paper_affine_rolling_contact_details_missing`
- `paper_faithful_explicit_rbd_baseline_missing`
- `paper_faithful_implicit_rbd_baseline_missing`
- `paper_comparable_timing_missing`

The gap audit must preserve these remaining reproduction gaps:

- `paper_faithful_explicit_rbd_baseline`
- `paper_faithful_implicit_rbd_baseline`
- `paper_faithful_mabd_rolling_cylinder`
- `paper_comparable_timing`

## Config Contract

`configs/experiments/single_body_rolling_spinning.yaml` gets:

```yaml
mabd_rolling_contact_candidate:
  output_report: reports/experiment_matrix/single_body_rolling_spinning_mabd_rolling_contact_candidate.json
  contact_constraint_mode: world
```

The lane reuses `RollingSpinningMABDNewtonConfig` fields and the finite material
settings from `mabd_material_preflight`:

- `young_modulus_pa = 1.0e9`
- `poisson_ratio = 0.3`
- `zero_stiffness_diagnostic = false`
- `time_step_s = 0.01`
- `step_count = 10000`
- `rotation_mode = polar`

Validation must enforce a lane-specific report path, finite material values,
`contact_constraint_mode = world`, and no changes to the top-level
`required_missing_lanes`.

## Runtime Contract

The runner builds the same affine cylinder and static ground plane as the
current M-ABD lanes, but configures the CPU oracle with:

```python
MABDCPUOracleConfig(
    bodies=[...],
    gravity=config.gravity_m_s2,
    contact_constraint_mode="world",
    topology="dense",
)
```

Each step:

1. reads the current M-ABD state,
2. calls `SolverMABD.detect_static_plane_contacts(state)`,
3. passes those contacts to `solver.step(...)`,
4. records the contact conversion summary and constraint residual.

The report records no-slip residual, support penetration, contact counts,
`generated_world_constraint_count`, static-plane candidate counts, affine shape
spread, constraint residuals, wall-clock time, and trajectory samples.

## Report Contract

Report path:

```text
reports/experiment_matrix/single_body_rolling_spinning_mabd_rolling_contact_candidate.json
```

Required report fields:

- `baseline_lane = mabd_rolling_contact_candidate`
- `solver_mode = newton_mabd_rolling_contact_world_constraint_candidate`
- `backend = cpu_newton_mabd_world_constraints`
- `status = incomplete`
- `observed.contact_constraint_mode = world`
- `observed.generated_world_constraint_count_summary`
- `observed.local_runtime_measured = true`
- `observed.paper_comparable = false`
- `observed.full_experiment_claim_passed = false`
- `observed.required_reproduction_gaps_remaining` preserving all four gap names
- `observed.blocking_reasons` containing all Phase81 blockers
- `timing_distribution.paper_comparable = false`
- `raw_outputs.time_series = not_written`
- `plot_paths = {}`

The lane may improve no-slip residual relative to the Phase 77 material
preflight, but improvement is not a pass gate. Threshold violations are local
diagnostics only and must not close any paper claim.

## Acceptance Criteria

- Config tests load and validate `mabd_rolling_contact_candidate`.
- Unit tests prove `SolverMABD` contact inputs in `world` mode are used by the
  rolling candidate runner.
- Runner and CLI tests cover
  `rolling_spinning_mabd_rolling_contact_candidate`.
- The generated report is machine-checkable, incomplete, and preserves all
  rolling/spinning reproduction gaps.
- `scripts/validate_docs.py` validates the Phase81 spec, plan, record, report,
  report hash, gap audit, and claim-boundary text.
