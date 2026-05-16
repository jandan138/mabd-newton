# M-ABD Phase 3 Topology Solvers Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add verified CPU oracle topology solvers for M-ABD dual systems: chain block-tridiagonal solve, tree topology elimination validation, loop Schur complement, graph block Gauss-Seidel reconstruction, and deterministic graph classification.

**Architecture:** Phase 3 adds a pure NumPy layer above Phase 2's `dense_kkt.py` and `joint_constraints.py`. It validates topology-specific algebra against the existing dense dual oracle on small systems; it does not implement `SolverMABD.step()`, contact, joint limits, actuation, paper scenes, timing, or paper-comparable performance.

**Tech Stack:** Python 3.10, NumPy dense/block linear algebra, vendored Newton custom attributes, `unittest`.

---

## File Structure

- Create `vendor/newton/newton/_src/solvers/mabd/topology_solvers.py` for graph classification, global dual assembly, chain block Thomas, tree dense-equivalence elimination, loop Schur complement, and graph block Gauss-Seidel.
- Modify `vendor/newton/newton/_src/solvers/mabd/__init__.py` to export Phase 3 APIs through `newton.solvers.mabd`.
- Create `tests/test_mabd_phase3_topology_solvers.py` for public API tests.
- Create `vendor/newton/newton/tests/test_mabd_phase3_topology_solvers.py` for Newton-internal import tests.
- Modify `docs/reference/paper-claims.yaml`, `docs/reference/claim-boundaries.md`, `scripts/validate_docs.py`, and `tests/test_phase0_bootstrap.py` after tests pass.
- Create `docs/records/2026-05-16-phase3-topology-solvers.md` after verification.

## Task 1: RED Tests For Topology Solver APIs

**Files:**
- Create: `tests/test_mabd_phase3_topology_solvers.py`
- Create: `vendor/newton/newton/tests/test_mabd_phase3_topology_solvers.py`

- [ ] **Step 1: Write public failing tests**

Add public tests that import `from newton.solvers import mabd` and construct synthetic M-ABD dual problems from:

- `body_hessians`: tuple of 12x12 SPD matrices
- `body_forces`: tuple of 12-vectors
- `edges`: tuple of `(body_a, body_b)` integer pairs
- `edge_gradients`: tuple of `(gradient_a, gradient_b)` arrays
- `lower_rhs_blocks`: tuple of residual-corrected lower RHS vectors

Expected public tests:

- `test_chain_block_tridiagonal_matches_dense_dual_kkt`
- `test_tree_elimination_matches_dense_dual_kkt_and_records_orders`
- `test_loop_schur_complement_matches_dense_dual_and_uses_declared_breaker`
- `test_graph_block_gauss_seidel_converges_to_dense_dual_with_recorded_schedule`
- `test_graph_classification_and_model_reconstruction_are_deterministic`
- `test_solver_step_remains_unsupported_in_phase3`

Each direct topology result must compare `dq`, `dlambda`, stationarity, and constraint residuals to `mabd.solve_dense_dual_kkt(...)`.

- [ ] **Step 2: Run public tests to verify RED**

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_mabd_phase3_topology_solvers
```

Expected: fail because Phase 3 topology APIs are not exported.

- [ ] **Step 3: Mirror internal failing tests**

Create `vendor/newton/newton/tests/test_mabd_phase3_topology_solvers.py` with focused chain, loop, graph, and classification checks importing `from newton._src.solvers import mabd`.

- [ ] **Step 4: Run internal tests to verify RED**

```bash
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest vendor.newton.newton.tests.test_mabd_phase3_topology_solvers
```

Expected: fail because Phase 3 topology APIs are not exported.

## Task 2: Implement Topology Solver Helpers

**Files:**
- Create: `vendor/newton/newton/_src/solvers/mabd/topology_solvers.py`
- Modify: `vendor/newton/newton/_src/solvers/mabd/__init__.py`

- [ ] **Step 1: Implement canonical assembly and result types**

Required API:

```python
@dataclass(frozen=True)
class ConstraintGraphClassification: ...
@dataclass(frozen=True)
class ReconstructedConstraintGraph: ...
@dataclass(frozen=True)
class TopologyKKTResult: ...
def assemble_topology_dual_inputs(body_hessians, edges, edge_gradients, body_forces, lower_rhs_blocks=None): ...
```

- [ ] **Step 2: Implement graph classification**

Required API:

```python
def classify_constraint_graph(num_bodies, edges, root=0) -> ConstraintGraphClassification: ...
def reconstruct_constraint_graph_from_model(model, root=0) -> ReconstructedConstraintGraph: ...
```

Classification rules:

- connected with `E = N - 1` and max degree <= 2: `chain`
- connected with `E = N - 1`: `tree`
- connected with cycle rank `E - N + 1 = 1`: `single_loop`
- otherwise connected: `general_graph`

- [ ] **Step 3: Implement direct and iterative topology solvers**

Required API:

```python
def solve_chain_block_tridiagonal_kkt(...): ...
def solve_tree_elimination_kkt(...): ...
def solve_loop_schur_complement_kkt(...): ...
def solve_graph_block_gauss_seidel_kkt(...): ...
```

Implementation constraints:

- Chain must solve the dual block-tridiagonal matrix with block Thomas.
- Tree must validate tree topology, record parent/postorder, and match dense dual algebra; this Phase 3 function is a CPU algebra oracle and not a paper timing claim.
- Loop must partition the dual system by declared loop breaker edges and solve the Schur complement `D - C A^-1 C^T`.
- Graph must implement block Gauss-Seidel over an explicit complete edge schedule, tolerance, max iterations, and relaxation parameter.

- [ ] **Step 4: Export Phase 3 APIs**

Update `vendor/newton/newton/_src/solvers/mabd/__init__.py`.

- [ ] **Step 5: Run focused tests to verify GREEN**

Run the two focused Phase 3 test commands.

## Task 3: Docs, Claims, Record, And Verification

**Files:**
- Modify: `docs/reference/paper-claims.yaml`
- Modify: `docs/reference/claim-boundaries.md`
- Modify: `scripts/validate_docs.py`
- Modify: `tests/test_phase0_bootstrap.py`
- Create: `docs/records/2026-05-16-phase3-topology-solvers.md`

- [ ] **Step 1: Add conservative topology claims**

Add and later set to `passed` only after tests and record exist:

- `method.topology.chain_block_tridiagonal`
- `method.topology.tree_traversal_dense_dual_oracle`
- `method.topology.loop_schur_complement`
- `method.topology.graph_gauss_seidel`
- `method.topology.graph_classification_reconstruction`

Do not mark any experiment, scene, timing, contact, joint-limit, actuation, or full `SolverMABD.step()` claim as passed.

- [ ] **Step 2: Extend claim boundaries**

Record that Phase 3 verifies CPU topology solver algebra against dense dual oracles, and explicitly does not verify `SolverMABD.step()`, paper experiments, timing, contact, joint limits, actuation, or paper-comparable performance.

- [ ] **Step 3: Extend docs validator**

Require the Phase 3 record, Phase 3 boundary text, and passed topology claims cited by the Phase 3 record. Update stdout to `Phase 0/1/2/3 docs/provenance validation passed`.

- [ ] **Step 4: Run final verification**

```bash
/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check tests/test_mabd_phase3_topology_solvers.py tests/test_phase0_bootstrap.py vendor/newton/newton/_src/solvers/mabd vendor/newton/newton/tests/test_mabd_phase3_topology_solvers.py scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest vendor.newton.newton.tests.test_mabd_phase3_topology_solvers
git diff --check
```

- [ ] **Step 5: Request review and commit**

After fresh verification and code review:

```bash
git add docs/reference/claim-boundaries.md docs/reference/paper-claims.yaml docs/records/2026-05-16-phase3-topology-solvers.md docs/superpowers/plans/2026-05-16-mabd-phase3-topology-solvers.md scripts/validate_docs.py tests/test_phase0_bootstrap.py tests/test_mabd_phase3_topology_solvers.py vendor/newton/newton/_src/solvers/mabd vendor/newton/newton/tests/test_mabd_phase3_topology_solvers.py
git commit -m "feat: add Phase 3 M-ABD topology solver oracles"
```
