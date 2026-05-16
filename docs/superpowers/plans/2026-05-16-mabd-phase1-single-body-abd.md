# M-ABD Phase 1 Single-Body ABD Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the first verified Newton-native M-ABD slice: paper-faithful single-body affine kinematics, dense CPU oracle math, Hessian caching, and a public `newton.solvers.SolverMABD` shell.

**Architecture:** Phase 1 is deliberately a small, testable gate. It adds pure NumPy dense-oracle helpers under `newton._src.solvers.mabd`, then exposes those helpers through `newton.solvers.mabd` and `SolverMABD`; it does not claim joint solves, contact, or paper experiments. The affine state follows the paper's four-block layout `q = [q1, q2, q3, t]`, where `q1..q3` are the columns of `A` in `x = A xbar + t`.

**Tech Stack:** Python 3.10, NumPy dense linear algebra, vendored Newton, Warp only for Newton custom attribute registration, `unittest`.

---

## File Structure

- Create `vendor/newton/newton/_src/solvers/mabd/__init__.py` for internal M-ABD exports.
- Create `vendor/newton/newton/_src/solvers/mabd/affine_math.py` for CPU oracle equations: `pack_q`, `point_jacobian`, `generalized_mass_matrix`, Lamé parameters, linear elastic gradient, polar/no-polar block rotations, `G(A)`, `E(A)`, and virtual-work mapping.
- Create `vendor/newton/newton/_src/solvers/mabd/single_body.py` for `SingleBodyABDPrecompute`, `SingleBodyABDHessianCache`, and one-step dense solve helpers.
- Create `vendor/newton/newton/_src/solvers/mabd/solver_mabd.py` for `SolverMABD`, custom attributes, Hessian cache invalidation, and an explicit unsupported-step boundary for unimplemented multi-body dynamics.
- Modify `vendor/newton/newton/_src/solvers/__init__.py` and `vendor/newton/newton/solvers.py` to export `SolverMABD` and the `mabd` helper namespace.
- Create `tests/test_mabd_single_body.py` for project-level checks run by the root validation command.
- Create `vendor/newton/newton/tests/test_mabd_single_body.py` for Newton-internal tests that may import `_src` directly.
- Modify `docs/reference/paper-claims.yaml` so Phase 1 method claims become `passed` only after verification records are written; until then keep them `intended`.
- Create `docs/records/2026-05-16-phase1-single-body-abd.md` after tests pass, recording commands and scope boundaries.

## Task 1: Failing Tests For Affine State, J, Mass, And Elasticity

**Files:**
- Create: `tests/test_mabd_single_body.py`
- Create: `vendor/newton/newton/tests/test_mabd_single_body.py`

- [ ] **Step 1: Write the failing project-level tests**

Add tests that import from `newton.solvers.mabd` and assert these behaviors:

```python
import unittest

import numpy as np

import newton
from newton.solvers import SolverMABD
from newton.solvers import mabd


class TestMABDSingleBodyMath(unittest.TestCase):
    def test_affine_q_uses_paper_column_blocks(self):
        A = np.array([[1.0, 0.2, 0.3], [0.4, 2.0, 0.6], [0.7, 0.8, 3.0]])
        t = np.array([3.0, -2.0, 0.5])
        q = mabd.pack_q(A, t)
        self.assertTrue(np.allclose(q[:3], A[:, 0]))
        self.assertTrue(np.allclose(q[3:6], A[:, 1]))
        self.assertTrue(np.allclose(q[6:9], A[:, 2]))
        self.assertTrue(np.allclose(q[9:12], t))
        A_round, t_round = mabd.unpack_q(q)
        self.assertTrue(np.allclose(A_round, A))
        self.assertTrue(np.allclose(t_round, t))

    def test_point_jacobian_matches_affine_kinematics(self):
        A = np.array([[1.0, 0.1, 0.0], [0.2, 1.5, -0.1], [0.3, 0.4, 0.8]])
        t = np.array([0.25, -0.5, 0.75])
        rest_point = np.array([2.0, -3.0, 0.5])
        q = mabd.pack_q(A, t)
        J = mabd.point_jacobian(rest_point)
        self.assertTrue(np.allclose(J @ q, A @ rest_point + t))

    def test_tetra_mass_matrix_is_symmetric_positive_definite(self):
        rest_points = np.array(
            [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
        )
        masses = np.array([0.25, 0.25, 0.25, 0.25])
        M = mabd.generalized_mass_matrix(rest_points, masses)
        eigvals = np.linalg.eigvalsh(M)
        self.assertTrue(np.allclose(M, M.T))
        self.assertGreater(float(eigvals.min()), 0.0)

    def test_linear_elastic_gradient_matches_finite_difference(self):
        A = np.array([[1.02, 0.03, -0.01], [0.04, 0.97, 0.02], [0.01, -0.02, 1.05]])
        young = 20.0
        poisson = 0.25
        volume = 0.7
        grad = mabd.linear_elastic_gradient(A, young, poisson, volume)
        eps = 1.0e-6
        fd = np.zeros((3, 3))
        for i in range(3):
            for j in range(3):
                dA = np.zeros((3, 3))
                dA[i, j] = eps
                ep = mabd.linear_elastic_energy(A + dA, young, poisson, volume)
                em = mabd.linear_elastic_energy(A - dA, young, poisson, volume)
                fd[i, j] = (ep - em) / (2.0 * eps)
        self.assertTrue(np.allclose(grad, fd, atol=1.0e-7))

    def test_public_solver_export_exists(self):
        self.assertIs(newton.solvers.SolverMABD, SolverMABD)
        self.assertTrue(hasattr(newton.solvers, "mabd"))
```

- [ ] **Step 2: Run tests to verify RED**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_mabd_single_body
```

Expected: FAIL because `SolverMABD` and `newton.solvers.mabd` are not defined.

- [ ] **Step 3: Mirror the same tests in Newton's internal test tree**

Create `vendor/newton/newton/tests/test_mabd_single_body.py` with equivalent assertions, importing internal helpers from `newton._src.solvers.mabd`.

- [ ] **Step 4: Run the Newton-internal test to verify RED**

Run:

```bash
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest vendor.newton.newton.tests.test_mabd_single_body
```

Expected: FAIL because `newton._src.solvers.mabd` is not implemented.

## Task 2: Implement Affine CPU Oracle Math

**Files:**
- Create: `vendor/newton/newton/_src/solvers/mabd/__init__.py`
- Create: `vendor/newton/newton/_src/solvers/mabd/affine_math.py`
- Modify: `vendor/newton/newton/_src/solvers/__init__.py`
- Modify: `vendor/newton/newton/solvers.py`

- [ ] **Step 1: Implement `affine_math.py` minimally**

Implement the exact API exercised by Task 1:

```python
def pack_q(A: ArrayLike, t: ArrayLike) -> np.ndarray: ...
def unpack_q(q: ArrayLike) -> tuple[np.ndarray, np.ndarray]: ...
def point_jacobian(rest_point: ArrayLike) -> np.ndarray: ...
def point_jacobians(rest_points: ArrayLike) -> np.ndarray: ...
def generalized_mass_matrix(rest_points: ArrayLike, masses: ArrayLike) -> np.ndarray: ...
def lame_parameters(young_modulus: float, poisson_ratio: float) -> tuple[float, float]: ...
def linear_elastic_energy(A: ArrayLike, young_modulus: float, poisson_ratio: float, volume: float = 1.0) -> float: ...
def linear_elastic_gradient(A: ArrayLike, young_modulus: float, poisson_ratio: float, volume: float = 1.0) -> np.ndarray: ...
```

Use the paper equation:

```python
grad = volume * (mu * (A + A.T - 2.0 * I) + lam * np.trace(A - I) * I)
```

- [ ] **Step 2: Export the helper namespace**

Expose `mabd` and `SolverMABD` through Newton's existing public solver export pattern.

- [ ] **Step 3: Run Task 1 tests to verify GREEN**

Run both commands from Task 1. Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add tests/test_mabd_single_body.py vendor/newton/newton/tests/test_mabd_single_body.py vendor/newton/newton/_src/solvers vendor/newton/newton/solvers.py
git commit -m "feat: add single-body ABD affine math"
```

## Task 3: Add Rotation, No-Polar, Twist, Wrench, And Hessian Tests

**Files:**
- Modify: `tests/test_mabd_single_body.py`
- Modify: `vendor/newton/newton/tests/test_mabd_single_body.py`

- [ ] **Step 1: Add failing tests for rotation maps**

Add assertions for:

```python
R = mabd.polar_rotation(A)
np.allclose(R.T @ R, np.eye(3))
np.linalg.det(R) > 0.0
```

Add no-polar block checks:

```python
blocks = np.arange(12, dtype=float) + 1.0
rhs = mabd.apply_no_polar_rhs_rotation(A, blocks)
for block_id in range(4):
    original = blocks[3 * block_id : 3 * block_id + 3]
    rotated = rhs[3 * block_id : 3 * block_id + 3]
    self.assertAlmostEqual(np.linalg.norm(original), np.linalg.norm(rotated))
```

- [ ] **Step 2: Add failing tests for `G(A)`, `E(A)`, and virtual work**

Use a diagonal non-singular `A` and assert:

```python
G = mabd.twist_map_G(A)
E = mabd.rigid_embedding_E(A)
self.assertTrue(np.allclose(G @ E, np.eye(6), atol=1.0e-10))
wrench = np.array([0.2, -0.4, 0.6, 1.0, 2.0, -1.5])
dq = np.linspace(-0.3, 0.4, 12)
fa = mabd.affine_force_from_wrench(A, wrench)
self.assertAlmostEqual(float(fa @ dq), float(wrench @ (G @ dq)))
```

- [ ] **Step 3: Add failing tests for `SingleBodyABDHessianCache`**

Assert that cache entries are reused for identical `(dt, device, model_version)` and rebuilt when any key changes:

```python
pre = mabd.SingleBodyABDPrecompute.from_points(rest_points, masses, stiffness_matrix=np.eye(12))
cache = mabd.SingleBodyABDHessianCache(pre)
a = cache.factor(dt=0.01, device="cpu", model_version=0)
b = cache.factor(dt=0.01, device="cpu", model_version=0)
c = cache.factor(dt=0.02, device="cpu", model_version=0)
self.assertIs(a, b)
self.assertIsNot(a, c)
```

- [ ] **Step 4: Run tests to verify RED**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_mabd_single_body
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest vendor.newton.newton.tests.test_mabd_single_body
```

Expected: FAIL because these helpers are not implemented.

## Task 4: Implement Rotation Maps And Dense Hessian Cache

**Files:**
- Modify: `vendor/newton/newton/_src/solvers/mabd/affine_math.py`
- Create: `vendor/newton/newton/_src/solvers/mabd/single_body.py`
- Modify: `vendor/newton/newton/_src/solvers/mabd/__init__.py`

- [ ] **Step 1: Implement polar/no-polar helpers**

Implement SVD polar rotation with determinant correction. Implement no-polar block normalization from Algorithm 1: multiply each 3-vector block by `A.T` for RHS or `A` for increments, then rescale to preserve the original block norm.

- [ ] **Step 2: Implement `G(A)`, exact-left-inverse `E(A)`, and virtual work**

Implement `twist_map_G(A)` from Eq. 37. Implement `rigid_embedding_E(A)` as a robust left inverse of `G(A)` by inserting the inverse of `0.5 * (trace(A.T @ A) * I - A @ A.T)` into the angular blocks; this equals the paper Eq. 43 for rotations and makes `G(A)E(A)=I` for non-singular diagonal affine states. Implement `affine_force_from_wrench(A, wrench)` as `G(A).T @ wrench`.

- [ ] **Step 3: Implement `single_body.py`**

Add:

```python
@dataclass(frozen=True)
class SingleBodyABDPrecompute:
    rest_points: np.ndarray
    masses: np.ndarray
    mass_matrix: np.ndarray
    stiffness_matrix: np.ndarray

    @classmethod
    def from_points(cls, rest_points, masses, stiffness_matrix=None): ...

    def hessian(self, dt: float) -> np.ndarray:
        return self.mass_matrix / (dt * dt) + self.stiffness_matrix


@dataclass(frozen=True)
class DenseHessianFactor:
    key: tuple[float, str, int]
    matrix: np.ndarray
    cholesky: np.ndarray

    def solve(self, rhs): ...


class SingleBodyABDHessianCache:
    def __init__(self, precompute): ...
    def factor(self, dt: float, device: str = "cpu", model_version: int = 0): ...
    def clear(self): ...
```

- [ ] **Step 4: Run tests to verify GREEN**

Run both focused commands from Task 3. Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/test_mabd_single_body.py vendor/newton/newton/tests/test_mabd_single_body.py vendor/newton/newton/_src/solvers/mabd
git commit -m "feat: add M-ABD rotation maps and Hessian cache"
```

## Task 5: Add SolverMABD Shell And Custom Attribute Tests

**Files:**
- Create: `vendor/newton/newton/_src/solvers/mabd/solver_mabd.py`
- Modify: `vendor/newton/newton/_src/solvers/mabd/__init__.py`
- Modify: `vendor/newton/newton/_src/solvers/__init__.py`
- Modify: `vendor/newton/newton/solvers.py`
- Modify: `tests/test_mabd_single_body.py`
- Modify: `vendor/newton/newton/tests/test_mabd_single_body.py`

- [ ] **Step 1: Add failing tests for custom attributes and cache invalidation**

Add tests that:

```python
builder = newton.ModelBuilder()
SolverMABD.register_custom_attributes(builder)
self.assertIn("mabd:body", builder.custom_frequencies)
self.assertIn("mabd:body_index", builder.custom_attributes)
self.assertIn("mabd:q0", builder.custom_attributes)
```

Add a solver cache invalidation test:

```python
builder = newton.ModelBuilder()
SolverMABD.register_custom_attributes(builder)
model = builder.finalize()
solver = SolverMABD(model)
self.assertEqual(solver.model_version, 0)
solver.notify_model_changed(0)
self.assertEqual(solver.model_version, 1)
```

- [ ] **Step 2: Run tests to verify RED**

Run the focused commands. Expected: FAIL because `SolverMABD` shell is incomplete.

- [ ] **Step 3: Implement `SolverMABD`**

Derive from `SolverBase`, register the `mabd:body` custom frequency, add namespaced model attributes (`body_index`, `young_modulus`, `poisson_ratio`, `density`, `polar_mode`) and state attributes (`q0`, `q1`, `q2`, `t`, `qd0`, `qd1`, `qd2`, `td`). Implement `notify_model_changed()` by incrementing `model_version` and clearing dense caches. Keep `step()` explicit:

```python
raise NotImplementedError("SolverMABD Phase 1 exposes verified single-body ABD oracles; time stepping is implemented in later phases.")
```

- [ ] **Step 4: Run tests to verify GREEN**

Run both focused commands. Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/test_mabd_single_body.py vendor/newton/newton/tests/test_mabd_single_body.py vendor/newton/newton/_src/solvers vendor/newton/newton/solvers.py
git commit -m "feat: expose SolverMABD shell"
```

## Task 6: Documentation Record And Phase Validation

**Files:**
- Modify: `docs/reference/paper-claims.yaml`
- Create: `docs/records/2026-05-16-phase1-single-body-abd.md`

- [ ] **Step 1: Update claim statuses for verified Phase 1 scope**

Only mark these method claims as `passed` after the focused tests pass:

- `method.single_body.affine_kinematics`
- `method.single_body.corotated_stiffness`
- `method.single_body.no_polar_mode`
- `method.single_body.twist_wrench_maps`

Keep joint, KKT, contact, and experiment claims as `intended`.

- [ ] **Step 2: Write the Phase 1 record**

Record:

- Worktree path.
- Dedicated Python path.
- Paper source paths and checksums from Phase 0.
- Exact validation commands and observed outcomes.
- Explicit non-claims: no joints, no contact, no benchmarks, no full paper reproduction yet.

- [ ] **Step 3: Run full validation**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest vendor.newton.newton.tests.test_mabd_single_body
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__); print(newton.solvers.SolverMABD)"
git diff --check
git status --short --branch
```

Expected: all commands exit 0, and git status only shows planned Phase 1 changes before commit.

- [ ] **Step 4: Commit**

```bash
git add docs/reference/paper-claims.yaml docs/records/2026-05-16-phase1-single-body-abd.md
git commit -m "docs: record Phase 1 single-body ABD evidence"
```

## Self-Review

- Spec coverage: This plan covers only Phase 1 single-body method claims from the paper and multi-agent review findings. It intentionally does not cover joints, KKT graph solvers, contact, asset manifests, baseline lanes, or experiments.
- Placeholder scan: No placeholder markers or unbounded "add tests" steps remain; each test category has concrete code or command expectations.
- Type consistency: Public tests use `newton.solvers.mabd`; internal implementation lives under `newton._src.solvers.mabd`; `SolverMABD` is exported through both Newton solver export files.
