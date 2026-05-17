# Phase 25 Spinning-Box No-Polar Material Lane Record

Date: 2026-05-17

## Status

passed

## Scope

Phase 25 enables the unconstrained M-ABD CPU oracle path to use
`rotation_mode = no_polar` and wires the configured spinning-box M-ABD lane to
the paper material constants. The configured report now records
`mabd_rotation_mode = no_polar`,
`material_model = paper_linear_elastic_no_polar_development`,
`material_young_modulus_pa`, `material_poisson_ratio`, `material_volume_m3`,
`material_stiffness_trace`, and `material_stiffness_rank`.

The phase also records that constrained CPU oracle no-polar KKT remains
unsupported. Constrained CPU oracle steps still require `rotation_mode = none`
until rotated Hessian/RHS KKT assembly is implemented and tested.

This phase does not verify the paper spinning-box experiment, full M-ABD
dynamics, multi-body no-polar constraints, paper-faithful implicit RBD
baseline, paper-faithful affine collision, collision detection, continuous
collision detection, friction, implicit contact solve, gravity, rendered
output, paper timing, paper trajectory agreement, committed generated report
artifacts, or any passed `experiment.*` claim.

## Config Path

- `configs/experiments/single_body_spinning_box.yaml`
- matrix: `configs/experiments/paper_experiment_matrix.yaml`

## Repository

- worktree:
  `/cpfs/user/zhuzihou/dev/mabd-newton/.worktrees/phase25-spinning-box-material-stiffness`
- branch: `phase25-spinning-box-material-stiffness`
- base commit: `a91b660cfc06853b9beb974f50def89a4ae29ded`
- plan commit: `9cff8b74521ec3ae2395bb5ceac42651cb1f2a40`
- CPU oracle no-polar implementation commit: `80a32a1e2f5a1a3ab80bec2460562cbcfd54c0bf`
- spinning-box material lane implementation commit: `c0cef676e5265c659ca2bd9bd58165f357d8b1fa`
- docs/record creation commit: `aa7eb983471ac1f2f6abdf27af7641b131533ea4`
- docs/provenance hardening commit: `511f2d13baf67dcc478494a4022bfd6cf959e82b`
- CPU oracle review disposition commit: `f8998822bc5d9a911c2a48fc3de93ffad204e6d8`
- review disposition record commit: `TO_BE_BACKFILLED_PHASE25_REVIEW_DISPOSITION_COMMIT`
- independent review: Newton/numerics review found that the first no-polar CPU
  oracle route rotated the translation block and reported residuals in the
  unrotated system. The disposition commit keeps translation inertial in the
  world frame, reports residuals in the local no-polar solve system, and adds
  independent invariant tests. Claim/provenance review found the Phase 25
  record did not list the docs/provenance hardening commit; this record now
  lists it explicitly.

## Vendored Newton

- vendored path: `vendor/newton`
- upstream commit: `96713fa965463b69c229a4d30582c733ff3526bb`
- local patch status: Phase 25 modifies vendored Newton
  `vendor/newton/newton/_src/solvers/mabd/step_oracle.py` to route
  unconstrained no-polar single-body steps through the existing
  `solve_single_body_delta` helper.

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

## Metrics And Diagnostics

- random seed: not applicable; the report lane is deterministic.
- config lane: `mabd_newton`
- solver mode in report: `mabd_cpu_oracle_development`
- backend in report: `cpu_numpy`
- step count: `4`
- time step: `0.01s`
- mabd_rotation_mode = no_polar
- material_model = paper_linear_elastic_no_polar_development
- material_young_modulus_pa = 1000000000.0
- material_poisson_ratio = 0.3
- material_volume_m3 = 0.001
- material_stiffness_trace = 6346153.846153847
- material_stiffness_rank = 6
- linear_momentum_error <= 1.0e-9
- observed final `linear_momentum_error`: `1.421085527484291e-14`
- angular_momentum_error remains a development gap
- observed final `angular_momentum_error`: `5327060168820.915`
- relative_energy_drift remains a development gap
- observed final `relative_energy_drift`: `53103644458.085396`
- affine_shape_diagnostic_status = development_gap_observed
- constrained CPU oracle no-polar KKT remains unsupported
- report status: `incomplete`
- no passed `experiment.*` claim is created in this phase.

## Artifacts

- committed vendored Newton patch:
  `vendor/newton/newton/_src/solvers/mabd/step_oracle.py`
- committed project code:
  `src/mabd_reproduction/spinning_box_physics.py`,
  `src/mabd_reproduction/single_body_reports.py`
- committed tests:
  `tests/test_mabd_phase4_solver_step.py`,
  `vendor/newton/newton/tests/test_mabd_phase4_solver_step.py`,
  `tests/test_single_body_report_lane.py`,
  `tests/test_spinning_box_comparison.py`,
  `tests/test_phase0_bootstrap.py`
- docs validator: `scripts/validate_docs.py`
- new material helpers: `SpinningBoxMaterialProperties`,
  `spinning_box_mabd_material_properties`,
  `spinning_box_mabd_material_stiffness`
- generated reports: not committed; tests write JSON reports to temporary
  directories only
- No `experiment.*` claim is passed in this phase.

## TDD Evidence

CPU oracle RED result:

```text
NotImplementedError: Phase 4 CPU step supports rotation_mode='none' only
```

CPU oracle GREEN result:

```text
CPU oracle tests: Ran 13 tests, OK
vendored CPU oracle tests: Ran 7 tests, OK
ruff: All checks passed!
git diff --check: exit 0
```

M-ABD report RED result:

```text
KeyError: 'mabd_rotation_mode'
```

M-ABD report GREEN result:

```text
M-ABD report tests: Ran 2 tests, OK
comparison and runner tests: Ran 21 tests, OK
ruff: All checks passed!
git diff --check: exit 0
```

Docs RED result:

```text
missing claim boundary bullet: This repository contains Phase 25
record file missing:
  docs/records/2026-05-17-phase25-spinning-box-no-polar-material-lane.md
validator output still ended at Phase 24
```

Docs GREEN result:

```text
phase bootstrap docs tests: Ran 45 tests, OK
docs validator: Phase 0/1/2/3/4/5/6/7/8/9/10/11/12/13/14/15/16/17/18/19/20/21/22/23/24/25 docs/provenance validation passed
```

## Claim Impact

No `experiment.*` claim is passed in this phase. The M-ABD spinning-box lane
remains incomplete and explicitly records no-polar/material development
diagnostics.
