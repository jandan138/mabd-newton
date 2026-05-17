# Phase 29 Spinning-Box Kinematic Feasibility Design

Date: 2026-05-17

## Decision

Phase 29 records a machine-checkable kinematic feasibility audit for the
single-body spinning-box M-ABD gap exposed by Phase 28.

The multi-agent review first suggested a new single-body `polar_variational`
CPU oracle. A local root-cause probe found a stricter issue: with the standard
implicit-Euler velocity relation `qd_next = (q_next - q_n) / h`, the paper's
spinning-box angular momentum and time steps are incompatible with keeping the
affine matrix near a rotation. Therefore, Phase 29 will not hide the gap by
adding a projection, relaxing thresholds, or marking the M-ABD lane as passed.

## Source Basis

Paper source lines used by this phase:

- `/tmp/mabd-paper/source/sections/singleabd.tex:34-58`: ABD step is described
  through inertia and elastic potentials.
- `/tmp/mabd-paper/source/sections/singleabd.tex:121-156`: co-rotated and
  no-polar single-object ABD solve.
- `/tmp/mabd-paper/source/sections/solver.tex:219-241`: affine velocity maps to
  spatial twist through `G(A)` and spatial wrench maps through `G(A)^T`.
- `/tmp/mabd-paper/source/sections/experiment.tex:40-55`: spinning-box figure,
  `p0`, `L0`, `h = 1e-2`, `h = 1e-3`, and momentum comparison text.

## Root-Cause Finding

For the paper cube:

- side length is `0.1 m`;
- density is `1E3 kg/m^3`;
- mass is `1 kg`;
- isotropic inertia is `1/6 * m * side^2 = 0.0016666667 kg m^2`;
- paper angular momentum is `L0 = [0, 100, 0] kg m^2/s`;
- target angular speed is `60000 rad/s`.

If a step keeps `A_next` exactly orthogonal and uses
`qd_next = (q_next - q_n) / h`, the finite-difference affine velocity cannot
represent arbitrary angular speed. For a rotation around the paper axis, the
effective angular speed recovered by `G(A_next) qd_next` is bounded by about
`1 / h`.

Thus:

- at `h = 0.01`, an orthogonal affine update can represent at most about
  `100 rad/s`, or `0.1666667 kg m^2/s` angular momentum;
- at `h = 0.001`, it can represent at most about `1000 rad/s`, or
  `1.6666667 kg m^2/s` angular momentum;
- both are far below the paper target `100 kg m^2/s`.

The current Phase 28 result preserves momentum only by allowing very large
affine stretch. A pure post-step projection to `SO(3)` would improve shape
diagnostics but destroy the paper angular momentum diagnostic under the same
velocity relation.

## Scope

Phase 29 adds explicit feasibility diagnostics, not a new pass gate:

- a helper that computes the paper angular speed, orthogonal finite-difference
  speed bound, angular-momentum bound, and required ratio for each paper step
  size;
- report fields in the M-ABD paper-horizon diagnostic explaining whether the
  paper momentum requires affine stretch under the standard velocity update;
- tests that prove current `polar` first-step stretch and prove the orthogonal
  finite-difference bound for `h = 0.01` and `h = 0.001`;
- claim-boundary and dated record updates stating that Phase 29 identifies a
  kinematic feasibility blocker and still does not pass the M-ABD lane.

## Non-Goals

Phase 29 does not:

- pass `experiment.single_body.spinning_box`;
- create an M-ABD lane pass gate;
- enable the spinning-box comparison pass gate;
- relax Phase 28 shape or energy thresholds;
- replace the M-ABD step with an RBD projection;
- decouple `qd_next` from the implicit-Euler state update;
- implement constrained polar/no-polar KKT;
- implement unconfigured production `SolverMABD.step()`;
- implement Warp/CUDA kernels or paper timing;
- update any `experiment.*` status in `paper-claims.yaml` to `passed`.

## Exit Criteria

The phase is complete when:

- the feasibility helper is covered by unit tests;
- `write_spinning_box_paper_horizon_report(...)` records the feasibility
  diagnostics for both paper step sizes;
- the diagnostics explain why shape-preserving projection is not accepted as
  paper-faithful M-ABD evidence;
- docs validation requires the Phase 29 record and non-claims;
- all standard repo gates pass.

The next implementation phase may then choose between two explicit paths:

1. locate paper/source evidence that the authors use a different velocity
   update or momentum extraction for this figure; or
2. implement an alternative M-ABD stepping semantics and record it as a
   reconstruction until the paper-source basis is proven.
