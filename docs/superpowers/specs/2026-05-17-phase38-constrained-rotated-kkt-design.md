# Phase 38 Constrained Rotated KKT Design

## Completion Audit

Objective: fully implement the Newton-only M-ABD reproduction, using the local
Newton source when needed, without polluting the reference environment, and push
auditable progress.

Current evidence:

- Environment isolation is satisfied by `scripts/env/readiness_check.py`: the
  active interpreter is `mabd-newton-py310`, the reference environment is only
  recorded as a source, and vendored Newton imports from this repo.
- Paper PDF and TeX provenance are recorded in
  `docs/reference/paper-claims.yaml` for arXiv `2603.08079v2`.
- Method claims in `docs/reference/paper-claims.yaml` currently have 19
  `passed` entries and experiment claims have 15 `intended` entries.
- Phase 37 produced a formal physical-pendulum `mabd_newton` lane, but
  `docs/reference/claim-boundaries.md` and
  `reports/experiment_matrix/single_body_physical_pendulum_comparison.json`
  still keep the physical-pendulum experiment `incomplete`.

Conclusion: the full objective is not achieved. The next concrete blocker is
inside the solver path: constrained CPU-oracle steps reject
`rotation_mode = polar`, which prevents pivoted or jointed scenes from using
the paper-facing co-rotated single-body material lane.

## Problem

`vendor/newton/newton/_src/solvers/mabd/step_oracle.py` currently calls
`_require_constrained_none_rotation` before solving constrained KKT systems.
This rejects any constrained body whose `MABDCPUOracleBody.rotation_mode` is
`polar` or `no_polar`.

Unconstrained `polar` bodies already solve in a local rotated frame and map the
increment back to the world-frame affine state. The constrained path needs the
same coordinate-frame discipline for KKT assembly.

Unconstrained `no_polar` uses normalization helpers that are not a linear
increment map for non-orthogonal `A`. Phase 38 therefore keeps constrained
`no_polar` explicitly unsupported instead of forcing it into a KKT coordinate
transform that would not preserve virtual work.

## Scope

Phase 38 implements CPU-oracle support for constrained bodies with
`rotation_mode in {"none", "polar"}`.

It covers:

- dense constrained KKT with body-body constraints;
- dense constrained KKT with world-anchor constraints;
- explicit rejection for constrained rotated modes outside `topology = dense`;
- explicit rejection coverage for constrained `no_polar`;
- report-level evidence that the physical-pendulum `mabd_newton` lane can
  exercise the constrained rotated path.

It does not cover:

- Warp/CUDA kernels;
- chain/tree/loop/general-graph topology solvers with rotated constrained
  bodies;
- paper ABD-ABA performance;
- paper-faithful physical-pendulum geometry;
- paper joint-force waveform agreement;
- collision, friction, or contact solve;
- marking any `experiment.*` paper claim as passed.

## Design

Each constrained solve assembles KKT unknowns in a per-body solve frame:

- `none`: local increment is the world increment.
- `polar`: local increment is the increment used by
  `apply_polar_increment_rotation(A, local_delta)`.
Constrained `no_polar` is rejected before KKT assembly because its current
normalizing increment helper is nonlinear for general affine states.

For each body, the solver builds:

- `solve_rhs`: the body RHS expressed in that body's solve frame;
- `increment_map`: a 12x12 matrix whose columns map local increments to
  world-frame affine increments.

Then the constrained KKT system uses:

- `H_local` as the existing precomputed Hessian;
- `f_local = solve_rhs`;
- `J_local = J_world @ increment_map` for every participating body;
- the same world-space residual correction `-C(q)` as before.

After solving, the local per-body increments are mapped back through
`increment_map` before updating `q_next` and `qd_next`.

This keeps the KKT equation in the same unknown frame as the body Hessian while
preserving world-space constraints and residual checks.

## Physical-Pendulum Lane

The Phase 37 physical-pendulum `mabd_newton` lane currently reuses the
development rollout and always builds a constrained body with `rotation_mode =
none`. Phase 38 adds a scoped `mabd_newton.rotation_mode` config field and sets
it to `polar` for the formal lane. The development diagnostic stays `none`.

The report records `mabd_rotation_mode = polar` and keeps status
`incomplete`. This proves the lane exercises the new constrained rotated KKT
path without claiming paper-faithful geometry or joint-force agreement.

## Validation

Required checks:

- TDD red tests must fail before implementation:
  - constrained polar CPU step should no longer reject;
  - constrained no-polar CPU step should no longer reject;
  - physical-pendulum `mabd_newton` report should record `mabd_rotation_mode`.
- Target tests pass:
  - `tests.test_mabd_phase4_solver_step`
  - `tests.test_physical_pendulum_mabd`
  - `tests.test_experiment_run_configs`
  - `tests.test_experiment_runner`
  - `tests.test_phase0_bootstrap`
- Docs validator passes through Phase 38.
- Readiness check continues to report no reference-environment mutation.

## Claim Boundary

Phase 38 may claim only that constrained CPU-oracle KKT supports local-frame
polar solve coordinates for dense CPU KKT under unit and report tests, while
constrained `no_polar` and non-dense rotated topologies remain unsupported.

Phase 38 must not claim:

- full M-ABD reproduction;
- a passed physical-pendulum experiment;
- paper-faithful physical-pendulum geometry;
- paper joint-force waveform agreement;
- paper timing;
- GPU or production Warp support.
