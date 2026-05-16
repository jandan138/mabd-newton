# 2026-05-16 Phase 2 Joints And Dense KKT

## Status

passed

## Scope

Phase 2 adds the first verified multi-body M-ABD oracle slice inside vendored
Newton:

- control tetrahedron maps `y = T q` and `q = T^-1 y`
- degenerate control tetrahedron rejection
- point-major CP selection helpers and `diag_4(R)` block rotations
- minimal-rank ball, hinge, universal, and prismatic joint residual builders
- translation-invariant prismatic plane-lock row for shared rigid translation
- explicit universal rank 4 behavior, following the equation rather than the
  inconsistent figure caption
- finite-difference joint-gradient oracle checks for hinge, universal, and
  prismatic residuals
- constant ball-joint gradient coverage
- dense direct primal KKT oracle
- dense dual-space KKT oracle
- residual-corrected lower RHS support for the paper footnote correction
- `mabd:constraint` custom frequency and constraint model attributes

This record does not verify `SolverMABD.step()`, topology solvers, contact,
joint limits, actuation, full paper scenes, timing, external baselines, or the
lightweight skew-symmetrized joint-gradient performance path.

## Commands

Focused project tests:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_mabd_phase2_joints_kkt
```

Observed before implementation: failed with missing `control_point_transform`,
`ball_joint`, `hinge_joint`, `universal_joint`, dense KKT helpers, and
`mabd:constraint` attributes.

Observed after review fixes: `Ran 11 tests in 0.462s` and `OK`.

Focused Newton-internal tests:

```bash
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest vendor.newton.newton.tests.test_mabd_phase2_joints_kkt
```

Observed before implementation: failed with missing internal Phase 2 helpers.

Observed after final verification: `Ran 3 tests in 0.029s` and `OK`.

Docs/provenance validation:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
```

Observed: `Phase 0/1/2 docs/provenance validation passed`.

Full project tests:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
```

Observed after final verification: `Ran 28 tests in 8.340s` and `OK`.

Focused lint:

```bash
/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check tests/test_mabd_phase2_joints_kkt.py tests/test_phase0_bootstrap.py vendor/newton/newton/_src/solvers/mabd vendor/newton/newton/tests/test_mabd_phase2_joints_kkt.py scripts/validate_docs.py
```

Observed: `All checks passed!`.

Whitespace validation:

```bash
git diff --check
```

Observed: exit 0 with no output.

## Config Path

No experiment config is used in Phase 2. The tested behavior is encoded in:

- `tests/test_mabd_phase2_joints_kkt.py`
- `vendor/newton/newton/tests/test_mabd_phase2_joints_kkt.py`

## Repository

- worktree: `/cpfs/user/zhuzihou/dev/mabd-newton/.worktrees/phase2-joints-kkt`
- branch: `phase2-joints-kkt`
- base commit: `63d64fc`

## Vendored Newton

- vendored path: `vendor/newton`
- upstream commit: `96713fa965463b69c229a4d30582c733ff3526bb`
- local patch status: Phase 2 adds `control_points.py`,
  `joint_constraints.py`, `dense_kkt.py`, `mabd:constraint` registration, and
  Newton-internal tests.

## Paper Source

- arXiv ID: `2603.08079`
- arXiv version: `v2`
- local PDF: `/tmp/mabd-paper/mabd.pdf`
- local TeX source: `/tmp/mabd-paper/source`
- PDF SHA256: `a594e79093673c60fc59ad14f9b71f29a8f7f8e7b1c3d9c73efe6f5814cc6ec0`
- TeX source SHA256: `73ec398956c606dec2f8f40f0d38b9d5370e11b27830775e1b3765fe0efc563f`
- Joint source: `/tmp/mabd-paper/source/sections_a/multiabd.tex`
- KKT source: `/tmp/mabd-paper/source/sections/solver.tex`

## Environment

- Python: `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python`
- Isolation: cloned from
  `/cpfs/user/zhuzihou/conda-managed/envs/physics-primitive-newton-py310`
  and used through explicit `PYTHONPATH`
- Backend: CPU NumPy oracle; Warp imports initialize available CPU/CUDA devices
  for Newton model storage but Phase 2 kernels are not implemented.

## Claim Impact

Set to `passed`:

- `method.joints.ball`
- `method.joints.hinge`
- `method.joints.universal`
- `method.joints.prismatic`
- `method.kkt.residual_corrected_rhs`

Left as `intended`:

- `method.single_body.corotated_stiffness`, because full FEM `K_A_bar`
  rest-stiffness precomputation still is not verified.
- all experiment and baseline claims

## Boundaries

The Phase 2 joint residuals are dense CPU oracle helpers. They are intended to
anchor later solver integration, not to claim real-time stepping or topology
acceleration. The lightweight paper gradient path that keeps only selected
skew-symmetrized rotation-gradient entries remains an implementation target for
later performance work. Calling `paper_faithful` gradient mode for compact
nonlinear joints raises `NotImplementedError` in Phase 2 rather than returning
an overclaimed approximation.
