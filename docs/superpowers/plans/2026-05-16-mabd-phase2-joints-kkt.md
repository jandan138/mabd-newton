# M-ABD Phase 2 Joints And Dense KKT Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the first verified multi-body M-ABD oracle slice: control tetrahedron coordinates, paper minimal-rank joint residuals, finite-difference joint-gradient oracle coverage, and dense primal/dual KKT agreement.

**Architecture:** Phase 2 stays inside the public `newton.solvers.mabd` helper namespace and does not enable `SolverMABD.step()`. The implementation is split into pure NumPy CPU oracle modules for control points, joint constraints, and dense KKT assembly, plus custom Newton model attributes for solver-owned M-ABD constraints.

**Tech Stack:** Python 3.10, NumPy dense linear algebra, vendored Newton custom attributes, `unittest`.

---

## File Structure

- Create `vendor/newton/newton/_src/solvers/mabd/control_points.py` for `q <-> y` control tetrahedron maps.
- Create `vendor/newton/newton/_src/solvers/mabd/joint_constraints.py` for ball, hinge, universal, and prismatic residuals and gradients.
- Create `vendor/newton/newton/_src/solvers/mabd/dense_kkt.py` for direct primal KKT and dense dual-space oracle solves.
- Modify `vendor/newton/newton/_src/solvers/mabd/__init__.py` to export the new helper APIs through `newton.solvers.mabd`.
- Modify `vendor/newton/newton/_src/solvers/mabd/solver_mabd.py` to register `mabd:constraint` model attributes without implementing stepping.
- Create `tests/test_mabd_phase2_joints_kkt.py` for public API tests.
- Create `vendor/newton/newton/tests/test_mabd_phase2_joints_kkt.py` for Newton-internal import tests.
- Modify `docs/reference/paper-claims.yaml`, `docs/reference/claim-boundaries.md`, `scripts/validate_docs.py`, and `tests/test_phase0_bootstrap.py` after tests pass.
- Create `docs/records/2026-05-16-phase2-joints-kkt.md` after verification.

## Task 1: RED Tests For Control Tetrahedra And Minimal Joint Residuals

**Files:**
- Create: `tests/test_mabd_phase2_joints_kkt.py`
- Create: `vendor/newton/newton/tests/test_mabd_phase2_joints_kkt.py`

- [ ] **Step 1: Write public failing tests**

Add public tests for:

```python
from newton.solvers import mabd
```

Expected assertions:

- `mabd.control_point_transform(ct)` and `mabd.control_point_inverse_transform(ct)` are 12x12 inverses for a non-canonical tetrahedron.
- `mabd.control_points_from_q(q, ct)` equals four stacked points `A @ ybar_i + t`.
- `mabd.q_from_control_points(y, ct)` round-trips to `q`.
- degenerate CT input raises `ValueError`.
- `mabd.evaluate_joint(...)` returns residual ranks 3, 5, 4, and 5 for ball, hinge, universal, and prismatic fixtures.
- the universal joint explicitly uses rank 4, matching the equation rather than the inconsistent figure caption.
- ball residual equals selected CP displacement and ball gradient is constant across affine states.
- `SolverMABD.register_custom_attributes()` registers `mabd:constraint` and finalizes constraint rows into the Newton model.

- [ ] **Step 2: Run public tests to verify RED**

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_mabd_phase2_joints_kkt
```

Expected: fail because `control_points`, `joint_constraints`, and `mabd:constraint` exports do not exist.

- [ ] **Step 3: Mirror focused Newton-internal tests**

Create `vendor/newton/newton/tests/test_mabd_phase2_joints_kkt.py` with equivalent imports from `newton._src.solvers.mabd`.

- [ ] **Step 4: Run internal tests to verify RED**

```bash
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest vendor.newton.newton.tests.test_mabd_phase2_joints_kkt
```

Expected: fail for missing internal modules/exports.

## Task 2: Implement Control Point And Joint Oracle Helpers

**Files:**
- Create: `vendor/newton/newton/_src/solvers/mabd/control_points.py`
- Create: `vendor/newton/newton/_src/solvers/mabd/joint_constraints.py`
- Modify: `vendor/newton/newton/_src/solvers/mabd/__init__.py`
- Modify: `vendor/newton/newton/_src/solvers/mabd/solver_mabd.py`

- [ ] **Step 1: Implement control point maps**

Required API:

```python
@dataclass(frozen=True)
class ControlTetrahedron:
    rest_points: np.ndarray
    transform: np.ndarray
    inverse_transform: np.ndarray

def control_point_transform(rest_points) -> np.ndarray: ...
def control_point_inverse_transform(rest_points) -> np.ndarray: ...
def control_points_from_q(q, rest_points) -> np.ndarray: ...
def q_from_control_points(control_points, rest_points) -> np.ndarray: ...
def control_point_selection(rows) -> np.ndarray: ...
def block_diag4(R) -> np.ndarray: ...
```

- [ ] **Step 2: Implement joint residual APIs**

Required API:

```python
class MABDJointType(str, Enum): ...
class JointGradientMode(str, Enum): ...
@dataclass(frozen=True)
class MABDJointSpec: ...
@dataclass(frozen=True)
class JointEvaluation: ...
def ball_joint(...): ...
def hinge_joint(...): ...
def universal_joint(...): ...
def prismatic_joint(...): ...
def evaluate_joint(spec, q_a, q_b, gradient_mode="finite_difference_oracle") -> JointEvaluation: ...
```

Use the reviewed row semantics:

- ball: CP1 xyz equality, rank 3.
- hinge: CP1 xyz equality plus CP2 local x/z equality, rank 5.
- universal: CP2 xyz equality plus beta-only local `y1 - y2`, rank 4.
- prismatic: local `x2a-x1b`, `z2a-z1b`, `x1b-x2b`, `z1b-z2b`, and beta plane lock `x3b`, rank 5.

- [ ] **Step 3: Extend custom constraint attributes**

Register `MABD_CONSTRAINT_FREQUENCY = "mabd:constraint"` with model attributes:

- `constraint_type`
- `body_a`
- `body_b`
- `rank`
- `gradient_mode`
- `axis0`
- `axis1`

Use `references="mabd:body"` for `body_a` and `body_b`.

- [ ] **Step 4: Run Task 1 tests to verify GREEN**

Run both public and internal focused commands. Expected: pass.

## Task 3: RED/GREEN Tests For Dense KKT Oracles

**Files:**
- Modify: `tests/test_mabd_phase2_joints_kkt.py`
- Modify: `vendor/newton/newton/tests/test_mabd_phase2_joints_kkt.py`
- Create: `vendor/newton/newton/_src/solvers/mabd/dense_kkt.py`
- Modify: `vendor/newton/newton/_src/solvers/mabd/__init__.py`

- [ ] **Step 1: Add failing KKT tests**

Add tests for:

- direct primal solve of `[H J.T; J 0] [dq, dlambda] = [f, lower_rhs]`;
- dense dual solve with zero lower RHS matching direct primal;
- dense dual solve with residual-corrected lower RHS `-C(q_n)` matching direct primal;
- corrected and zero-RHS solutions differ for nonzero residuals.

- [ ] **Step 2: Run KKT tests to verify RED**

Expected: fail because dense KKT helpers do not exist.

- [ ] **Step 3: Implement dense KKT helper module**

Required API:

```python
class KKTLowerRHSMode(str, Enum): ...
@dataclass(frozen=True)
class DenseKKTResult: ...
def assemble_dense_primal_kkt(H, J) -> np.ndarray: ...
def solve_dense_primal_kkt(H, J, f, lower_rhs=None) -> DenseKKTResult: ...
def assemble_dense_dual_kkt(H, J) -> np.ndarray: ...
def solve_dense_dual_kkt(H, J, f, lower_rhs=None) -> DenseKKTResult: ...
def recover_primal_from_dual(H, J, f, dlambda) -> np.ndarray: ...
```

Dual equation:

```python
S = J @ inv(H) @ J.T
rhs = J @ inv(H) @ f - lower_rhs
dq = inv(H) @ (f - J.T @ dlambda)
```

- [ ] **Step 4: Run KKT tests to verify GREEN**

Run both focused test commands.

## Task 4: Docs, Records, And Verification

**Files:**
- Modify: `docs/reference/paper-claims.yaml`
- Modify: `docs/reference/claim-boundaries.md`
- Modify: `scripts/validate_docs.py`
- Modify: `tests/test_phase0_bootstrap.py`
- Create: `docs/records/2026-05-16-phase2-joints-kkt.md`

- [ ] **Step 1: Update claim boundaries conservatively**

Record that Phase 2 verifies CP transforms, minimal-rank joint residuals, finite-difference gradient oracle checks, custom constraint attributes, and dense KKT primal/dual agreement.

Keep unverified:

- `SolverMABD.step()`
- topology solvers
- chain/tree/loop/graph acceleration
- contact
- joint limits
- actuation
- paper experiments and baselines
- lightweight paper skew-symmetrized joint-gradient performance path

- [ ] **Step 2: Update claim statuses only for verified Phase 2 claims**

Set to `passed` only after tests and record exist:

- `method.joints.ball`
- `method.joints.hinge`
- `method.joints.universal`
- `method.joints.prismatic`
- `method.kkt.residual_corrected_rhs`

- [ ] **Step 3: Extend docs validator**

Require the Phase 2 record, require the Phase 2 scope boundary text, and require every newly passed Phase 2 claim to be cited in the Phase 2 record.

- [ ] **Step 4: Run full verification**

```bash
/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check tests/test_mabd_phase2_joints_kkt.py tests/test_phase0_bootstrap.py vendor/newton/newton/_src/solvers/mabd vendor/newton/newton/tests/test_mabd_phase2_joints_kkt.py scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest vendor.newton.newton.tests.test_mabd_phase2_joints_kkt
git diff --check
```

- [ ] **Step 5: Commit**

```bash
git add docs/reference/claim-boundaries.md docs/reference/paper-claims.yaml docs/records/2026-05-16-phase2-joints-kkt.md docs/superpowers/plans/2026-05-16-mabd-phase2-joints-kkt.md scripts/validate_docs.py tests/test_phase0_bootstrap.py tests/test_mabd_phase2_joints_kkt.py vendor/newton/newton/_src/solvers/mabd vendor/newton/newton/tests/test_mabd_phase2_joints_kkt.py
git commit -m "feat: add Phase 2 M-ABD joint and KKT oracles"
```
