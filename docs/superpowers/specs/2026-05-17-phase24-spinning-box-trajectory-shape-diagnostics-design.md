# Phase 24 Spinning-Box Trajectory And Shape Diagnostics Design

Date: 2026-05-17

## Scope

Phase 24 adds report-level trajectory samples and affine shape diagnostics for
the existing single-body spinning-box development lanes. The paper's spinning
box evidence is a curve-based comparison of ABD against an implicit RBD
baseline. Phases 17 through 23 only expose final or aggregate metrics. Phase 24
starts recording the per-step data needed for those curves and makes the
current M-ABD affine-shape gap explicit.

This phase does not pass the paper spinning-box experiment. It does not make
the M-ABD lane co-rotated or paper-faithful, does not make the Newton
`SolverSemiImplicit` lane a paper-faithful implicit RBD baseline, and does not
claim trajectory agreement, timing, collision detection, contact solving, or
any passed `experiment.*` claim.

## Design

The M-ABD spinning-box report will record one sample at step 0 plus one sample
after each configured step. Each sample contains:

- `step_index` and `time_s`;
- `position_m`;
- `energy_j`;
- `linear_momentum_error` and `angular_momentum_error`;
- `affine_matrix`;
- `affine_determinant`;
- `affine_singular_values`;
- `affine_orthogonality_error = ||A^T A - I||_F`.

The report also promotes final affine shape values to top-level observed
fields so validators and later comparison phases can find them without parsing
the full sample list:

- `initial_affine_orthogonality_error`;
- `final_affine_orthogonality_error`;
- `final_affine_determinant`;
- `final_affine_singular_values`;
- `affine_shape_diagnostic_status = "development_gap_observed"`.

The RBD development lane will record the same step count cadence with rigid
sample fields:

- `step_index` and `time_s`;
- `position_m`;
- `rotation_xyzw`;
- `energy_j`;
- `linear_momentum_error`;
- `angular_momentum_error`.

The trajectory arrays are intentionally small for this phase because the
configured scene still runs only four 10 ms steps. Later phases can use the
same schema for longer runs and multiple step sizes.

## Evidence Boundary

Phase 24 verifies that the current reports expose per-step diagnostic data and
that the M-ABD lane records its affine deformation gap. A large
`final_affine_orthogonality_error` is evidence that the current development
lane is not yet the paper's co-rotated rigid-like ABD result. This phase does
not verify the paper plot, paper timing, paper trajectory agreement, rendered
output, paper-faithful affine collision, paper-faithful implicit RBD, or any
passed experiment claim.
