# Phase 25 Spinning-Box No-Polar Material Lane Design

Date: 2026-05-17

## Scope

Phase 25 reduces the known spinning-box M-ABD development gap by wiring the
paper-valued cube material model into the configured M-ABD lane and by enabling
the CPU oracle's existing single-body no-polar rotation path for unconstrained
steps.

The paper's spinning-box setup uses a cube of side length `0.1m`, density
`1E3`, Young's modulus `1E9`, Poisson ratio `0.3`, initial linear momentum
`p0 = [100, 0, 0]`, and initial angular momentum `L0 = [0, 100, 0]`. Earlier
phases already map the mass, initial generalized velocity, contact diagnostics,
and trajectory samples. Phase 24 exposes that the current M-ABD lane, which
uses a zero stiffness matrix and `rotation_mode = "none"`, develops a large
affine shape error under the paper angular momentum. Phase 25 makes that
limitation actionable.

This phase does not pass the paper spinning-box experiment. It does not add a
paper-faithful implicit RBD baseline, paper-faithful affine collision, contact
solving, gravity, long-horizon plots, timing comparison, rendered output, or a
passed `experiment.*` claim.

## Design

The M-ABD CPU oracle already contains the lower-level
`solve_single_body_delta(..., rotation_mode="no_polar")` helper introduced by
Phase 5. The configured CPU step still rejects non-`none` rotation modes. Phase
25 will allow `rotation_mode = "no_polar"` only for unconstrained CPU oracle
steps and route those body solves through `solve_single_body_delta`.

Constrained solves remain restricted to `rotation_mode = "none"` because the
joint/topology KKT path still assembles unrotated Hessian and RHS blocks. This
keeps the local Newton patch auditable and avoids implying multi-body
co-rotated constraint support.

The configured spinning-box M-ABD report lane will build a continuous-cube
linear elastic generalized stiffness from the paper material constants:

- Young's modulus: `1.0e9 Pa`;
- Poisson ratio: `0.3`;
- material volume: `cube_size_m ** 3`;
- translation stiffness rows and columns remain zero as in the existing affine
  material helper.

The report will record the material and rotation routing as machine-checkable
observed fields:

- `mabd_rotation_mode = "no_polar"`;
- `material_model = "paper_linear_elastic_no_polar_development"`;
- `material_young_modulus_pa`;
- `material_poisson_ratio`;
- `material_volume_m3`;
- `material_stiffness_trace`;
- `material_stiffness_rank`.

The existing `trajectory_samples`, final affine determinant, singular values,
and orthogonality error remain the diagnostic evidence. If no-polar plus paper
material reduces the Phase 24 shape blow-up, the report may replace
`affine_shape_diagnostic_status = "development_gap_observed"` with a more
specific development status. The status must still communicate that the lane is
not a passed paper experiment.

## Evidence Boundary

Phase 25 verifies that:

- the cloned project environment remains isolated from the reference
  `physics-primitive-newton-py310` environment;
- the unconstrained CPU oracle accepts and exercises `rotation_mode =
  "no_polar"`;
- constrained CPU oracle solves still reject no-polar bodies;
- the configured spinning-box report uses the paper material constants and
  records no-polar routing;
- diagnostics remain finite and machine-checkable.

Phase 25 does not verify full M-ABD dynamics, multi-body no-polar constraints,
paper trajectory agreement, paper timing, paper-faithful implicit RBD,
paper-faithful affine collision, generated video output, or any passed
`experiment.*` claim.
