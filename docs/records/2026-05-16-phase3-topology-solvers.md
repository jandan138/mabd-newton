# 2026-05-16 Phase 3 Topology Solvers

## Status

passed

## Scope

Phase 3 adds CPU topology-solver oracles above the Phase 2 dense KKT and joint
constraint helpers:

- canonical global dual assembly from body Hessians, body forces, edge
  gradients, and lower RHS blocks
- deterministic graph classification for chain, tree, single-loop, and general
  graph topologies
- Newton `mabd:constraint` graph reconstruction from finalized custom
  attributes
- chain block-tridiagonal dual solve with block Thomas
- tree parent/postorder traversal metadata and dense-dual-equivalent oracle solve
- loop Schur complement solve using declared loop-breaker edges
- explicit-schedule graph block Gauss-Seidel reconstruction with convergence
  diagnostics

This record does not verify `SolverMABD.step()`, paper ABD-ABA timing or
performance, paper tree elimination, paper-identical graph Gauss-Seidel
schedules, contact, joint limits, actuation, full paper scenes, external
baselines, or paper timing.

## Commands

Focused project tests:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_mabd_phase3_topology_solvers
```

Observed before implementation: failed with missing
`solve_chain_block_tridiagonal_kkt`, `solve_tree_elimination_kkt`,
`solve_loop_schur_complement_kkt`, `solve_graph_block_gauss_seidel_kkt`,
`classify_constraint_graph`, and `reconstruct_constraint_graph_from_model`.

Observed after implementation: `Ran 8 tests in 0.403s` and `OK`.

Focused Newton-internal tests:

```bash
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest vendor.newton.newton.tests.test_mabd_phase3_topology_solvers
```

Observed before implementation: failed with missing internal Phase 3 helpers.

Observed after implementation: `Ran 6 tests in 0.012s` and `OK`.

Docs/provenance validation:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
```

Observed: `Phase 0/1/2/3 docs/provenance validation passed`.

Full project tests:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
```

Observed: `Ran 37 tests in 9.236s` and `OK`.

Focused lint:

```bash
/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check tests/test_mabd_phase3_topology_solvers.py tests/test_phase0_bootstrap.py vendor/newton/newton/_src/solvers/mabd vendor/newton/newton/tests/test_mabd_phase3_topology_solvers.py scripts/validate_docs.py
```

Observed: `All checks passed!`.

Whitespace validation:

```bash
git diff --check
```

Observed: exit 0 with no output.

## Config Path

No experiment config is used in Phase 3. The tested behavior is encoded in:

- `tests/test_mabd_phase3_topology_solvers.py`
- `vendor/newton/newton/tests/test_mabd_phase3_topology_solvers.py`

## Repository

- worktree: `/cpfs/user/zhuzihou/dev/mabd-newton/.worktrees/phase3-topology-solvers`
- branch: `phase3-topology-solvers`
- base commit: `6d61cc6`

## Vendored Newton

- vendored path: `vendor/newton`
- upstream commit: `96713fa965463b69c229a4d30582c733ff3526bb`
- local patch status: Phase 3 adds `topology_solvers.py`, exports topology
  helpers, and adds Newton-internal tests.

## Paper Source

- arXiv ID: `2603.08079`
- arXiv version: `v2`
- local PDF: `/tmp/mabd-paper/mabd.pdf`
- local TeX source: `/tmp/mabd-paper/source`
- PDF SHA256: `a594e79093673c60fc59ad14f9b71f29a8f7f8e7b1c3d9c73efe6f5814cc6ec0`
- TeX source SHA256: `73ec398956c606dec2f8f40f0d38b9d5370e11b27830775e1b3765fe0efc563f`
- Topology source: `/tmp/mabd-paper/source/sections/solver.tex`

## Environment

- Python: `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python`
- Isolation: cloned from
  `/cpfs/user/zhuzihou/conda-managed/envs/physics-primitive-newton-py310`
  and used through explicit `PYTHONPATH`
- Backend: CPU NumPy oracle; Warp imports initialize available CPU/CUDA devices
  for Newton model storage but Phase 3 kernels are not implemented.

## Claim Impact

Set to `passed`:

- `method.topology.chain_block_tridiagonal`
- `method.topology.tree_traversal_dense_dual_oracle`
- `method.topology.loop_schur_complement`
- `method.topology.graph_gauss_seidel`
- `method.topology.graph_classification_reconstruction`

Left as `intended`:

- `method.single_body.corotated_stiffness`, because full FEM `K_A_bar`
  rest-stiffness precomputation still is not verified.
- all experiment and baseline claims

## Boundaries

The Phase 3 topology solvers are dense/block CPU oracle helpers. They anchor
later integration into `SolverMABD.step()` and paper scenes, but do not by
themselves constitute time stepping, collision handling, large-scale topology
performance reproduction, or full paper evidence.
