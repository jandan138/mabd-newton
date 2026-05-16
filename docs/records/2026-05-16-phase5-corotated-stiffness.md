# 2026-05-16 Phase 5 Corotated Stiffness Oracle

## Status

passed

## Scope

Phase 5 adds CPU oracle evidence for the single-body co-rotated stiffness
portion of the M-ABD method:

- analytic linear-elastic rest generalized stiffness `K_A_bar` for the paper's
  column-major affine coordinate `q`
- finite-difference curvature agreement between `K_A_bar` and the linear
  elastic energy around rest shape
- co-rotated linear elastic energy that vanishes for pure rotations
- co-rotated affine elastic force that vanishes for a pure rotation while the
  non-co-rotated linear elastic gradient does not
- block-rotated generalized stiffness
  `diag_4(R) K_A_bar diag_4(R)^T`
- `SingleBodyABDPrecompute.from_linear_elastic_points(...)` wiring into the
  existing dense single-body Hessian/cache path

This record does not verify unconfigured production `SolverMABD.step()`,
contact, collision, rigid-proxy affine collision faithfulness, joint limits,
actuation, robot controls, Warp kernels, GPU paths, multi-step paper scenes,
paper timing, paper ABD-ABA performance, external baselines, or comparative
reports.

## Commands

Focused project tests:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_mabd_single_body
```

Observed before implementation: failed with missing
`rest_generalized_stiffness_matrix`,
`co_rotated_linear_elastic_affine_force`, and
`co_rotated_generalized_stiffness_matrix`.

Observed after implementation: `Ran 16 tests in 0.365s` and `OK`.

Focused Newton-internal tests:

```bash
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest vendor.newton.newton.tests.test_mabd_single_body
```

Observed before implementation: failed with missing Phase 5 corotated
stiffness helpers.

Observed after implementation: `Ran 5 tests in 0.306s` and `OK`.

Precompute wiring RED check:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_mabd_single_body.MABDSingleBodyPublicTests.test_linear_elastic_precompute_builds_rest_stiffness
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest vendor.newton.newton.tests.test_mabd_single_body.TestMABDSingleBodyInternal.test_elasticity_rotation_twist_and_cache_oracles
```

Observed before wiring implementation: both failed with
`SingleBodyABDPrecompute` missing `from_linear_elastic_points`.

Docs/provenance validation:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
```

Observed: `Phase 0/1/2/3/4/5 docs/provenance validation passed`.

Focused project/bootstrap tests:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_mabd_single_body tests.test_phase0_bootstrap
```

Observed: `Ran 24 tests in 9.016s` and `OK`.

Full project tests:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
```

Observed: `Ran 50 tests in 9.155s` and `OK`.

Focused lint:

```bash
/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check tests/test_mabd_single_body.py tests/test_phase0_bootstrap.py vendor/newton/newton/_src/solvers/mabd vendor/newton/newton/tests/test_mabd_single_body.py scripts/validate_docs.py
```

Observed after fixing `__all__` ordering: `All checks passed!`.

Whitespace validation:

```bash
git diff --check
```

Observed: exit 0 with no output.

## Config Path

No experiment config is used in Phase 5. The tested corotated stiffness behavior
is encoded in:

- `tests/test_mabd_single_body.py`
- `vendor/newton/newton/tests/test_mabd_single_body.py`

## Repository

- worktree:
  `/cpfs/user/zhuzihou/dev/mabd-newton/.worktrees/phase5-corotated-stiffness`
- branch: `phase5-corotated-stiffness`
- base commit: `71f274c`
- plan commit: `29cb626`
- implementation commit: `IMPLEMENTATION_COMMIT_PENDING`

## Vendored Newton

- vendored path: `vendor/newton`
- upstream commit: `96713fa965463b69c229a4d30582c733ff3526bb`
- local patch status: Phase 5 adds corotated stiffness helpers, precompute
  wiring, exports, and Newton-internal tests.

## Paper Source

- arXiv ID: `2603.08079`
- arXiv version: `v2`
- local PDF: `/tmp/mabd-paper/mabd.pdf`
- local TeX source: `/tmp/mabd-paper/source`
- PDF SHA256: `a594e79093673c60fc59ad14f9b71f29a8f7f8e7b1c3d9c73efe6f5814cc6ec0`
- TeX source SHA256: `73ec398956c606dec2f8f40f0d38b9d5370e11b27830775e1b3765fe0efc563f`
- Co-rotated stiffness source:
  `/tmp/mabd-paper/source/sections/singleabd.tex:87-123`
- No-polar algorithm source:
  `/tmp/mabd-paper/source/sections/singleabd.tex:127-156`

## Environment

- Python: `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python`
- Isolation: cloned from
  `/cpfs/user/zhuzihou/conda-managed/envs/physics-primitive-newton-py310`
  and used through explicit `PYTHONPATH`
- Backend: CPU NumPy oracle; Warp imports initialize available CPU/CUDA devices
  for Newton state storage but Phase 5 kernels are not implemented.

## Claim Impact

Set to `passed`:

- `method.single_body.corotated_stiffness`

Still not passed:

- all experiment and baseline claims

## Boundaries

The Phase 5 evidence is method-level CPU oracle evidence. It proves the
rest-stiffness and co-rotated material algebra used by later stepping and
scene work. It is not paper scene evidence, contact evidence, timing evidence,
or proof of paper-comparable performance.
