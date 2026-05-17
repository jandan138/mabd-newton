# Phase 26 Co-Rotated Material RHS Record

Date: 2026-05-17

## Status

passed

## Scope

Phase 26 adds bounded single-body CPU oracle evidence for a polar co-rotated
material RHS. The unconstrained CPU oracle now accepts `rotation_mode = polar`
and applies the paper co-rotated full-block local solve pattern for the material
RHS. The configured spinning-box M-ABD development lane now records
`mabd_rotation_mode = polar`,
`material_model = paper_linear_elastic_corotated_development`,
`material_rhs_frame = corotated_local_all_blocks`, and
`translation_frame = corotated_polar_all_blocks`.

This phase does not verify the paper spinning-box experiment, full M-ABD
dynamics, multi-body polar or no-polar constraints, unconfigured production
`SolverMABD.step()`, Warp/CUDA/GPU paths, paper ABD-ABA performance,
paper-faithful implicit RBD baseline, paper-faithful affine collision,
collision detection, continuous collision detection, friction, implicit contact
solve, gravity, rendered output, paper timing, paper trajectory agreement,
committed generated report artifacts, or any passed `experiment.*` claim.

## Config Path

- `configs/experiments/single_body_spinning_box.yaml`
- matrix: `configs/experiments/paper_experiment_matrix.yaml`

## Repository

- worktree:
  `/cpfs/user/zhuzihou/dev/mabd-newton/.worktrees/phase26-corotated-material-rhs`
- branch: `phase26-corotated-material-rhs`
- base commit: `524bddd1e51deb46b6ad7c8c92f9c446fcf3e433`
- plan commit: `96509da8cd8f98124d885b8b1377351329b886ba`
- polar CPU oracle implementation commit: `d2ddb2a2e1e6b74d4deb1c6d8720ca7ee09f7ddb`
- spinning-box polar report lane implementation commit: `a5755baaed1d577fa23a6bd47e3ef4751a5e191a`
- docs/record creation commit: `982ebaa60907e1666e3acc6f3cf8ffdabc1d207a`
- review disposition record commit: `d500f97cee6f66a2a5a4aae23275d09ac4dd0df3`
- provenance hardening commit: `d500f97cee6f66a2a5a4aae23275d09ac4dd0df3`
- independent review: Newton/numerics review found that the initial Phase 26
  spec used an affine-only local transform that was not paper-equivalent unless
  the 12x12 system was translation-decoupled. Claim/provenance review found
  that exploratory metrics were not evidence. Claim/provenance review also
  found record/validator requirements were under-specified. The spec and plan
  were revised before implementation: Phase 26 now implements only polar
  full-block co-rotated local RHS evidence, leaves Phase 25 no-polar
  development behavior unchanged, and requires concrete record, validator, and
  non-claim fields.

## Vendored Newton

- vendored path: `vendor/newton`
- upstream commit: `96713fa965463b69c229a4d30582c733ff3526bb`
- local patch status: Phase 26 modifies vendored Newton
  `vendor/newton/newton/_src/solvers/mabd/step_oracle.py` to accept
  unconstrained `rotation_mode = polar`, assemble a full-block co-rotated local
  material RHS, preserve constrained rotated KKT rejection, and keep Phase 25
  no-polar development behavior unchanged.

## Paper Source

- arXiv ID: `2603.08079`
- arXiv version: `v2`
- PDF SHA256:
  `a594e79093673c60fc59ad14f9b71f29a8f7f8e7b1c3d9c73efe6f5814cc6ec0`
- TeX source SHA256:
  `73ec398956c606dec2f8f40f0d38b9d5370e11b27830775e1b3765fe0efc563f`
- cited source lines: `singleabd.tex:87-125`
- no-polar boundary source lines: `singleabd.tex:127-156`
- spinning-box source lines: `experiment.tex:40-55`

## Environment

- Python: `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python`
- reference clone source:
  `/cpfs/user/zhuzihou/conda-managed/envs/physics-primitive-newton-py310`
- readiness check:
  `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/env/readiness_check.py`
- readiness status: `smoke_passed`
- readiness JSON output: branch-gate stdout, not committed.
- non-pollution result: `mutates_reference_environment=false`,
  `uses_reference_python=false`, `uses_ambient_python=false`

## Metrics And Diagnostics

- random seed: not applicable; the report lane is deterministic.
- config lane: `mabd_newton`
- solver mode in report: `mabd_cpu_oracle_development`
- backend in report: `cpu_numpy`
- step count: `4`
- time step: `0.01s`
- mabd_rotation_mode = polar
- material_model = paper_linear_elastic_corotated_development
- material_rhs_frame = corotated_local_all_blocks
- translation_frame = corotated_polar_all_blocks
- material_young_modulus_pa = 1000000000.0
- material_poisson_ratio = 0.3
- material_volume_m3 = 0.001
- material_stiffness_trace = 6346153.846153847
- material_stiffness_rank = 6
- initial_energy_j = 3005000.0
- final_energy_j = 1487499.944548701
- energy_drift = 1517500.055451299
- relative_energy_drift = 0.5049916989854573
- linear_momentum_error <= 1.0e-9
- observed final `linear_momentum_error`: `7.679322694214913e-14`
- angular_momentum_error remains a development gap
- observed final `angular_momentum_error`: `1.472344024477934e-09`
- relative_energy_drift remains a development gap
- affine_shape_diagnostic_status = development_gap_observed
- final_affine_orthogonality_error = 2.862240022389957
- final_affine_determinant = 3.011131583264857
- final_affine_singular_values =
  `[1.7389366164867617, 1.738936616486421, 0.995777317191541]`
- final_position_m =
  `[3.9999999999999987, 0.05, 7.109507246450778e-16]`
- report status: `incomplete`
- no passed `experiment.*` claim is created in this phase.

## Artifacts

- committed vendored Newton patch:
  `vendor/newton/newton/_src/solvers/mabd/step_oracle.py`
- committed project code:
  `src/mabd_reproduction/single_body_reports.py`
- committed tests:
  `tests/test_mabd_phase4_solver_step.py`,
  `vendor/newton/newton/tests/test_mabd_phase4_solver_step.py`,
  `tests/test_single_body_report_lane.py`,
  `tests/test_phase0_bootstrap.py`
- docs validator: `scripts/validate_docs.py`
- generated reports: not committed; tests write JSON reports to temporary
  directories only
- No `experiment.*` claim is passed in this phase.

## Verification Commands

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_mabd_phase4_solver_step
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest newton.tests.test_mabd_phase4_solver_step
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_single_body_report_lane tests.test_spinning_box_comparison tests.test_experiment_runner
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_phase0_bootstrap
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/env/readiness_check.py
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"
git diff --check
```

## TDD Evidence

CPU oracle RED result:

```text
ValueError: rotation_mode must be one of 'none' or 'no_polar'
```

CPU oracle GREEN result:

```text
CPU oracle tests: Ran 17 tests, OK
vendored CPU oracle tests: Ran 11 tests, OK
ruff: All checks passed!
git diff --check: exit 0
```

M-ABD report RED result:

```text
AssertionError: 53103644458.08528 not less than 1.0
```

M-ABD report GREEN result:

```text
comparison and runner tests: Ran 21 tests, OK
ruff: All checks passed!
git diff --check: exit 0
```

Docs RED result:

```text
missing claim boundary bullet: This repository contains Phase 26
record file missing:
  docs/records/2026-05-17-phase26-corotated-material-rhs.md
validator output still ended at Phase 25
```

Docs GREEN result:

```text
phase bootstrap docs tests: Ran 47 tests, OK
docs validator: Phase 0/1/2/3/4/5/6/7/8/9/10/11/12/13/14/15/16/17/18/19/20/21/22/23/24/25/26 docs/provenance validation passed
```

## Claim Impact

No `experiment.*` claim is passed in this phase. The M-ABD spinning-box lane
remains incomplete and records polar co-rotated material RHS development
diagnostics.
