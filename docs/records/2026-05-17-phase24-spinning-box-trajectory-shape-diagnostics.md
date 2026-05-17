# Phase 24 Spinning-Box Trajectory Shape Diagnostics Record

Date: 2026-05-17

## Status

passed

## Scope

Phase 24 adds report-level trajectory diagnostics to the existing single-body
spinning-box development lanes. The M-ABD report now emits
`trajectory_samples` at step 0 and after each configured step, including
position, energy, momentum-error diagnostics, the affine matrix, affine
determinant, affine singular values, and `affine_orthogonality_error`. The
report also exposes top-level `final_affine_orthogonality_error`,
`final_affine_determinant`, `final_affine_singular_values`, and
`affine_shape_diagnostic_status = development_gap_observed`.

The RBD development baseline now emits `trajectory_samples` at step 0 and
after each Newton `SolverSemiImplicit` step, including position,
`rotation_xyzw`, energy, and momentum-error diagnostics.

This phase does not verify the paper spinning-box experiment,
paper-faithful implicit RBD baseline, paper-faithful affine collision,
collision detection, continuous collision detection, friction, implicit contact
solve, gravity, rendered output, paper timing, paper trajectory agreement,
committed generated report artifacts, or any passed `experiment.*` claim. The
M-ABD, RBD, and comparison reports remain `incomplete`.

## Config Path

- `configs/experiments/single_body_spinning_box.yaml`
- matrix: `configs/experiments/paper_experiment_matrix.yaml`

## Repository

- worktree:
  `/cpfs/user/zhuzihou/dev/mabd-newton/.worktrees/phase24-spinning-box-trajectory-shape-diagnostics`
- branch: `phase24-spinning-box-trajectory-shape-diagnostics`
- base commit: `d3b36c3699de66781dc43483a1006076c0b89547`
- plan commit: `f80cdc711719306f2b8babdc4e9c24af49175f83`
- M-ABD trajectory implementation commit: `5c42c19526de15bd662aaed65cbd0aa8ce7e50e2`
- RBD trajectory implementation commit: `4a18387cf9211a61d91fd8d87c1dfdf551f692b4`
- docs/provenance commit: `f79510d0cba4ededaa58f05c7040a45ca6dd3130`
- independent review: pending branch-gate review.

## Vendored Newton

- vendored path: `vendor/newton`
- upstream commit: `96713fa965463b69c229a4d30582c733ff3526bb`
- local patch status: Phase 24 adds no vendored Newton source changes.

## Paper Source

- arXiv ID: `2603.08079`
- arXiv version: `v2`
- PDF SHA256:
  `a594e79093673c60fc59ad14f9b71f29a8f7f8e7b1c3d9c73efe6f5814cc6ec0`
- TeX source SHA256:
  `73ec398956c606dec2f8f40f0d38b9d5370e11b27830775e1b3765fe0efc563f`
- cited source lines: `experiment.tex:40-55`

## Environment

- Python: `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python`
- reference clone source:
  `/cpfs/user/zhuzihou/conda-managed/envs/physics-primitive-newton-py310`
- readiness check:
  `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/env/readiness_check.py`
- readiness status: `smoke_passed`
- readiness JSON output: branch-gate stdout, not committed.
- clone drift command:
  `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m pip freeze`
  compared with
  `/cpfs/user/zhuzihou/conda-managed/envs/physics-primitive-newton-py310/bin/python -m pip freeze`
- clone drift check: `pip freeze` differs from
  `physics-primitive-newton-py310` only by the editable project line,
  `primitive_collision_compiler` versus `mabd_newton`.
- non-pollution result: `mutates_reference_environment=false`,
  `uses_reference_python=false`, `uses_ambient_python=false`

## Metrics And Thresholds

- random seed: not applicable; both trajectory-development lanes are
  deterministic.
- config lane: `mabd_newton`
- RBD lane: `rbd_implicit_baseline`
- M-ABD solver mode in report: `mabd_cpu_oracle_development`
- RBD solver mode in report: `newton_semimplicit_rbd_cpu_development`
- backend in M-ABD report: `cpu_numpy`
- backend in RBD report: `cpu_newton_warp`
- Newton step count: `4`
- time step: `0.01s`
- M-ABD `trajectory_samples` length: `step_count + 1`
- RBD `trajectory_samples` length: `step_count + 1`
- M-ABD sample fields include `position_m`, `energy_j`,
  `linear_momentum_error`, `angular_momentum_error`, `affine_matrix`,
  `affine_determinant`, `affine_singular_values`, and
  `affine_orthogonality_error`.
- final_affine_orthogonality_error is reported as a development diagnostic.
- final_affine_determinant is reported as a development diagnostic.
- final_affine_singular_values is reported as a development diagnostic.
- affine_shape_diagnostic_status = development_gap_observed
- RBD sample fields include `position_m`, `rotation_xyzw`, `energy_j`,
  `linear_momentum_error`, and `angular_momentum_error`.
- report status: `incomplete`
- no passed `experiment.*` claim is created in this phase.

## Artifacts

- committed code: `src/mabd_reproduction/spinning_box_physics.py`,
  `src/mabd_reproduction/single_body_reports.py`,
  `src/mabd_reproduction/rigid_baselines.py`
- committed tests: `tests/test_single_body_report_lane.py`,
  `tests/test_rigid_baselines.py`, `tests/test_phase0_bootstrap.py`
- docs validator: `scripts/validate_docs.py`
- new diagnostic helpers: `SpinningBoxAffineShapeDiagnostics`,
  `spinning_box_affine_shape_diagnostics`
- generated reports: not committed; tests write JSON reports to temporary
  directories only
- No `experiment.*` claim is passed in this phase.

## TDD Evidence

M-ABD trajectory RED result:

```text
KeyError: 'trajectory_samples'
```

M-ABD trajectory GREEN result:

```text
M-ABD report tests: Ran 2 tests, OK
ruff: All checks passed!
git diff --check: exit 0
```

RBD trajectory RED result:

```text
AttributeError: 'SpinningBoxRBDBaselineResult' object has no attribute 'trajectory_samples'
AssertionError: 'trajectory_samples' not found
```

RBD trajectory GREEN result:

```text
RBD tests: Ran 5 tests, OK
ruff: All checks passed!
git diff --check: exit 0
```

Docs RED result:

```text
missing claim boundary bullet: This repository contains Phase 24
record file missing:
  docs/records/2026-05-17-phase24-spinning-box-trajectory-shape-diagnostics.md
validator output still ended at Phase 23
```

Docs GREEN result:

```text
phase bootstrap docs tests: Ran 43 tests, OK
docs validator: Phase 0/1/2/3/4/5/6/7/8/9/10/11/12/13/14/15/16/17/18/19/20/21/22/23/24 docs/provenance validation passed
```

## Claim Impact

No `experiment.*` claim is passed in this phase.
