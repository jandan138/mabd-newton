# 2026-05-16 Phase 1 Single-Body ABD

## Status

passed

## Scope

Phase 1 adds the first verified single-body M-ABD slice inside vendored Newton:

- paper column-block affine state `q = [q1, q2, q3, t]`
- constant rest point Jacobians for `x = A xbar + t`
- dense generalized mass matrix oracle
- Lamé parameter and linear elasticity energy/gradient oracle
- volume-weighted point `J^T f` and tetrahedral `bar J^T f` generalized force helpers
- polar and no-polar block rotation helpers
- `G(A)`, robust `E(A)`, and virtual-work wrench mapping
- paper-displayed `E(A)` for rigid rotations, distinct from the robust
  left-inverse extension used for non-rigid affine states
- single-body dense delta solve with paper polar/no-polar RHS and increment
  transforms
- dense Hessian cache keyed by timestep, backend label, and model version
- public `newton.solvers.SolverMABD` shell and `mabd` helper namespace

This record does not verify multi-body joints, KKT graph solvers, contact,
full FEM rest-stiffness precomputation, assets, timing, baselines, or paper
experiments.

## Commands

Focused project tests:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_mabd_single_body
```

Observed before implementation: failed with missing `SolverMABD`.

Observed after initial implementation: `Ran 9 tests in 0.829s` and `OK`.
Observed after review fixes: `Ran 12 tests in 0.347s` and `OK`.

Focused Newton-internal tests:

```bash
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest vendor.newton.newton.tests.test_mabd_single_body
```

Observed before implementation: failed with missing `newton._src.solvers.mabd`.

Observed after initial implementation: `Ran 4 tests in 0.470s` and `OK`.
Observed after review fixes: `Ran 5 tests in 0.270s` and `OK`.

Docs/provenance validation:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
```

Observed: `Phase 0/1 docs/provenance validation passed`.

Full project tests:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
```

Observed after review fixes: `Ran 17 tests in 8.440s` and `OK`.

Focused lint:

```bash
/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check tests/test_mabd_single_body.py vendor/newton/newton/_src/solvers/mabd vendor/newton/newton/tests/test_mabd_single_body.py
```

Observed after review fixes: `All checks passed!`.

Public Newton import:

```bash
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__); print(newton.solvers.SolverMABD)"
```

Observed:

```text
/cpfs/user/zhuzihou/dev/mabd-newton/.worktrees/phase1-single-body-abd/vendor/newton/newton/__init__.py
<class 'newton._src.solvers.mabd.solver_mabd.SolverMABD'>
```

Whitespace validation:

```bash
git diff --check
```

Observed: exit 0 with no output.

## Config Path

No experiment config is used in Phase 1. The tested behavior is encoded in:

- `tests/test_mabd_single_body.py`
- `vendor/newton/newton/tests/test_mabd_single_body.py`

## Repository

- worktree: `/cpfs/user/zhuzihou/dev/mabd-newton/.worktrees/phase1-single-body-abd`
- branch: `phase1-single-body-abd`
- base commit: `f072d3f`

## Vendored Newton

- vendored path: `vendor/newton`
- upstream commit: `96713fa965463b69c229a4d30582c733ff3526bb`
- local patch status: Phase 1 adds `newton._src.solvers.mabd`, exports
  `SolverMABD`, and adds Newton-internal tests.

## Paper Source

- arXiv ID: `2603.08079`
- arXiv version: `v2`
- local PDF: `/tmp/mabd-paper/mabd.pdf`
- local TeX source: `/tmp/mabd-paper/source`
- PDF SHA256: `a594e79093673c60fc59ad14f9b71f29a8f7f8e7b1c3d9c73efe6f5814cc6ec0`
- TeX source SHA256: `73ec398956c606dec2f8f40f0d38b9d5370e11b27830775e1b3765fe0efc563f`

## Environment

- Python: `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python`
- Isolation: cloned from
  `/cpfs/user/zhuzihou/conda-managed/envs/physics-primitive-newton-py310`
  and used through explicit `PYTHONPATH`
- Backend: CPU NumPy oracle; Warp imports initialize available CPU/CUDA devices
  but Phase 1 kernels are not implemented.

## Claim Impact

Set to `passed`:

- `method.single_body.affine_kinematics`
- `method.single_body.no_polar_mode`
- `method.single_body.twist_wrench_maps`

Left as `intended`:

- `method.single_body.corotated_stiffness`, because Phase 1 verifies dense
  Hessian plumbing, paper RHS/increment transforms, and `bar J` force mapping,
  but not full FEM `K_A_bar = J^T Kbar J` rest-stiffness precomputation.
- all joint method claims
- KKT residual-corrected RHS claim
- all experiment and baseline claims
