# 2026-05-16 Phase 4 Configured CPU Step Oracle

## Status

passed

## Scope

Phase 4 adds a guarded CPU oracle path for `SolverMABD.step()`:

- explicit `MABDCPUOracleConfig` with per-body single-body precomputes,
  optional external generalized forces, and optional dense equality constraints
- one implicit-Euler/Newton affine update using
  `H_A = M_A / h^2 + K_A_bar`
- dense dual KKT with residual-corrected lower RHS `J dq = -C(q_n)` for
  configured joint correction
- nonzero rest-stiffness RHS sign coverage
- custom state I/O through
  `state.mabd.{q0,q1,q2,t,qd0,qd1,qd2,td}` using `.assign()`
- in-place two-row custom state stepping
- `SolverMABD.step()` remains guarded: it runs only after
  `configure_cpu_oracle(...)`

This record does not verify unconfigured production `SolverMABD.step()`,
contact, collision, rigid-proxy affine collision faithfulness, joint limits,
actuation, robot controls, Warp kernels, GPU paths, multi-step paper scenes,
paper timing, paper ABD-ABA performance, paper-identical graph schedules,
external baselines, or comparative reports.

## Commands

Focused project tests:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_mabd_phase4_solver_step
```

Observed before implementation: failed with missing `MABDCPUOracleBody`,
`MABDCPUOracleConstraint`, `MABDCPUOracleConfig`, `solve_cpu_oracle_step`, and
`SolverMABD.configure_cpu_oracle`.

Observed after implementation: `Ran 7 tests in 0.421s` and `OK`.

Focused Newton-internal tests:

```bash
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest vendor.newton.newton.tests.test_mabd_phase4_solver_step
```

Observed before implementation: failed with missing Phase 4 CPU step helpers.

Observed after implementation: `Ran 4 tests in 0.601s` and `OK`.

Docs/provenance validation:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
```

Observed: `Phase 0/1/2/3/4 docs/provenance validation passed`.

Full project tests:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
```

Observed: `Ran 45 tests in 8.888s` and `OK`.

Focused lint:

```bash
/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check tests/test_mabd_phase4_solver_step.py tests/test_phase0_bootstrap.py vendor/newton/newton/_src/solvers/mabd vendor/newton/newton/tests/test_mabd_phase4_solver_step.py scripts/validate_docs.py
```

Observed: `All checks passed!`.

Whitespace validation:

```bash
git diff --check
```

Observed: exit 0 with no output.

## Config Path

No experiment config is used in Phase 4. The tested configured CPU step behavior
is encoded in:

- `tests/test_mabd_phase4_solver_step.py`
- `vendor/newton/newton/tests/test_mabd_phase4_solver_step.py`

## Repository

- worktree: `/cpfs/user/zhuzihou/dev/mabd-newton/.worktrees/phase4-solver-step`
- branch: `phase4-solver-step`
- base commit: `15732d2`

## Vendored Newton

- vendored path: `vendor/newton`
- upstream commit: `96713fa965463b69c229a4d30582c733ff3526bb`
- local patch status: Phase 4 adds `step_oracle.py`, exports CPU step helpers,
  extends `SolverMABD` with guarded configured CPU stepping, and adds
  Newton-internal tests.

## Paper Source

- arXiv ID: `2603.08079`
- arXiv version: `v2`
- local PDF: `/tmp/mabd-paper/mabd.pdf`
- local TeX source: `/tmp/mabd-paper/source`
- PDF SHA256: `a594e79093673c60fc59ad14f9b71f29a8f7f8e7b1c3d9c73efe6f5814cc6ec0`
- TeX source SHA256: `73ec398956c606dec2f8f40f0d38b9d5370e11b27830775e1b3765fe0efc563f`
- Step source: `/tmp/mabd-paper/source/sections/singleabd.tex`
- KKT source: `/tmp/mabd-paper/source/sections/solver.tex`

## Environment

- Python: `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python`
- Isolation: cloned from
  `/cpfs/user/zhuzihou/conda-managed/envs/physics-primitive-newton-py310`
  and used through explicit `PYTHONPATH`
- Backend: CPU NumPy oracle; Warp imports initialize available CPU/CUDA devices
  for Newton state storage but Phase 4 kernels are not implemented.

## Claim Impact

Set to `passed`:

- `method.solver.configured_cpu_step`

Left as `intended`:

- `method.single_body.corotated_stiffness`, because full FEM `K_A_bar`
  rest-stiffness precomputation still is not verified.
- all experiment and baseline claims

## Boundaries

The Phase 4 configured CPU step is a small-system oracle bridge. It makes
`SolverMABD.step()` executable only when the caller provides explicit oracle
data. It anchors later production stepping, contact, scene, and performance
work, but it is not itself paper scene evidence.
