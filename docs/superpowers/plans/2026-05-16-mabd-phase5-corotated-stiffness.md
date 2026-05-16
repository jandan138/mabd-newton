# Phase 5 Corotated Stiffness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Promote `method.single_body.corotated_stiffness` from intended to passed with paper-faithful CPU oracle evidence for rest generalized stiffness, co-rotated material force, and reduced Newton solve algebra.

**Architecture:** Keep this as a small CPU-oracle phase inside vendored Newton. Add analytic linear-elastic rest stiffness helpers to `affine_math.py`, wire them through `single_body.py`, and prove equivalence with finite-difference energy/force tests plus the existing rotation-mode solve path. Documentation records the claim boundary: this is still not scene, contact, timing, GPU, or production Warp evidence.

**Tech Stack:** Python 3.10, NumPy, Newton vendored source, `unittest`, ruff, docs/provenance validator.

---

### Task 1: RED Tests For Rest Stiffness And Co-Rotated Force

**Files:**
- Modify: `tests/test_mabd_single_body.py`
- Modify: `vendor/newton/newton/tests/test_mabd_single_body.py`

- [ ] **Step 1: Add failing public tests**

Add tests that call the not-yet-existing public M-ABD helpers:

```python
    def test_rest_generalized_stiffness_matches_finite_difference_energy(self) -> None:
        young = 80.0
        poisson = 0.25
        volume = 0.35
        q_rest = mabd.pack_q(np.eye(3), np.array([0.2, -0.1, 0.4]))
        direction = np.linspace(-0.2, 0.3, 12)
        direction[9:12] = np.array([0.5, -0.25, 0.75])
        eps = 1.0e-6

        K = mabd.rest_generalized_stiffness_matrix(young, poisson, volume)

        def energy_at(q: np.ndarray) -> float:
            A, _t = mabd.unpack_q(q)
            return mabd.linear_elastic_energy(A, young, poisson, volume)

        fd_curvature = (energy_at(q_rest + eps * direction) - 2.0 * energy_at(q_rest) + energy_at(q_rest - eps * direction)) / (eps * eps)
        self.assertTrue(np.allclose(K, K.T, atol=1.0e-12))
        self.assertTrue(np.allclose(K[9:12], np.zeros((3, 12))))
        self.assertAlmostEqual(float(direction @ K @ direction), float(fd_curvature), places=5)
```

```python
    def test_corotated_elastic_force_vanishes_for_pure_rotation(self) -> None:
        theta = 0.37
        R = np.array(
            [
                [np.cos(theta), -np.sin(theta), 0.0],
                [np.sin(theta), np.cos(theta), 0.0],
                [0.0, 0.0, 1.0],
            ]
        )

        force = mabd.co_rotated_linear_elastic_affine_force(R, 80.0, 0.25, 1.7)

        self.assertTrue(np.allclose(force, np.zeros(12), atol=1.0e-12))
        self.assertGreater(np.linalg.norm(mabd.linear_elastic_gradient(R, 80.0, 0.25, 1.7)), 1.0)
```

```python
    def test_corotated_generalized_stiffness_matches_block_rotation_formula(self) -> None:
        theta = -0.41
        R = np.array(
            [
                [np.cos(theta), 0.0, np.sin(theta)],
                [0.0, 1.0, 0.0],
                [-np.sin(theta), 0.0, np.cos(theta)],
            ]
        )
        K_bar = mabd.rest_generalized_stiffness_matrix(50.0, 0.2, 0.9)
        D = np.kron(np.eye(4), R)

        observed = mabd.co_rotated_generalized_stiffness_matrix(R, K_bar)

        self.assertTrue(np.allclose(observed, D @ K_bar @ D.T, atol=1.0e-12))
```

- [ ] **Step 2: Add failing internal mirror tests**

Mirror the same three behaviors in `vendor/newton/newton/tests/test_mabd_single_body.py`, importing helpers directly from `newton._src.solvers.mabd`.

- [ ] **Step 3: Run tests to verify RED**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_mabd_single_body
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest vendor.newton.newton.tests.test_mabd_single_body
```

Expected: both fail with missing `rest_generalized_stiffness_matrix`, `co_rotated_linear_elastic_affine_force`, and `co_rotated_generalized_stiffness_matrix`.

### Task 2: GREEN Implementation In Affine Helpers

**Files:**
- Modify: `vendor/newton/newton/_src/solvers/mabd/affine_math.py`
- Modify: `vendor/newton/newton/_src/solvers/mabd/single_body.py`
- Modify: `vendor/newton/newton/_src/solvers/mabd/__init__.py`

- [ ] **Step 1: Implement analytic rest generalized stiffness**

Add helpers to `affine_math.py`:

```python
def _block_diag4(R: np.ndarray) -> np.ndarray:
    return np.kron(np.eye(4), R)


def _pack_A_gradient(grad: np.ndarray) -> np.ndarray:
    out = np.zeros(12, dtype=float)
    out[0:3] = grad[:, 0]
    out[3:6] = grad[:, 1]
    out[6:9] = grad[:, 2]
    return out


def rest_generalized_stiffness_matrix(
    young_modulus: float,
    poisson_ratio: float,
    volume: float = 1.0,
) -> np.ndarray:
    mu, lam = lame_parameters(young_modulus, poisson_ratio)
    K = np.zeros((12, 12), dtype=float)
    for col in range(9):
        dA = np.zeros((3, 3), dtype=float)
        dA[:, col // 3][col % 3] = 1.0
        dP = mu * (dA + dA.T) + lam * np.trace(dA) * np.eye(3)
        K[:, col] = _pack_A_gradient(float(volume) * dP)
    return 0.5 * (K + K.T)
```

- [ ] **Step 2: Implement co-rotated energy/force/stiffness helpers**

Add to `affine_math.py`:

```python
def co_rotated_linear_elastic_energy(
    A: Any,
    young_modulus: float,
    poisson_ratio: float,
    volume: float = 1.0,
) -> float:
    A_arr = _as_mat33(A, "A")
    R = polar_rotation(A_arr)
    return linear_elastic_energy(R.T @ A_arr, young_modulus, poisson_ratio, volume)


def co_rotated_linear_elastic_affine_force(
    A: Any,
    young_modulus: float,
    poisson_ratio: float,
    volume: float = 1.0,
) -> np.ndarray:
    A_arr = _as_mat33(A, "A")
    R = polar_rotation(A_arr)
    local_gradient = linear_elastic_gradient(R.T @ A_arr, young_modulus, poisson_ratio, volume)
    return -_pack_A_gradient(R @ local_gradient)


def co_rotated_generalized_stiffness_matrix(A: Any, rest_stiffness_matrix: Any) -> np.ndarray:
    A_arr = _as_mat33(A, "A")
    K_bar = np.asarray(rest_stiffness_matrix, dtype=float)
    if K_bar.shape != (12, 12):
        raise ValueError(f"rest_stiffness_matrix must have shape (12, 12), got {K_bar.shape}")
    D = _block_diag4(polar_rotation(A_arr))
    return D @ K_bar @ D.T
```

- [ ] **Step 3: Wire precompute construction**

Add `SingleBodyABDPrecompute.from_linear_elastic_points(...)` to `single_body.py`:

```python
    @classmethod
    def from_linear_elastic_points(
        cls,
        rest_points: Any,
        masses: Any,
        young_modulus: float,
        poisson_ratio: float,
        volume: float,
    ) -> SingleBodyABDPrecompute:
        return cls.from_points(
            rest_points,
            masses,
            stiffness_matrix=rest_generalized_stiffness_matrix(young_modulus, poisson_ratio, volume),
        )
```

- [ ] **Step 4: Export helpers**

Add the new helper names to `vendor/newton/newton/_src/solvers/mabd/__init__.py` and `affine_math.__all__`.

- [ ] **Step 5: Run focused tests to verify GREEN**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_mabd_single_body
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest vendor.newton.newton.tests.test_mabd_single_body
```

Expected: both pass.

### Task 3: Documentation, Claim Manifest, And Record

**Files:**
- Modify: `docs/reference/paper-claims.yaml`
- Modify: `docs/reference/claim-boundaries.md`
- Modify: `scripts/validate_docs.py`
- Modify: `tests/test_phase0_bootstrap.py`
- Create: `docs/records/2026-05-16-phase5-corotated-stiffness.md`

- [ ] **Step 1: Update claim and boundaries**

Set `method.single_body.corotated_stiffness` to `passed`. Add Phase 5 boundary text that says it verifies CPU oracle rest `K_A_bar`, co-rotated force zero on pure rotations, block-rotated stiffness, and precompute wiring. Explicitly keep scenes, contact, timing, Warp kernels, and full paper experiments unverified.

- [ ] **Step 2: Update docs validator**

Change the validator title/output to Phase 0/1/2/3/4/5, require the Phase 5 record path, require Phase 5 boundary snippets, and replace the old guard that rejected passed `method.single_body.corotated_stiffness` with a guard that requires the claim to be passed and cited in the Phase 5 record.

- [ ] **Step 3: Update bootstrap tests**

Update expected validator output and claim checks in `tests/test_phase0_bootstrap.py` so docs validation covers Phase 5.

- [ ] **Step 4: Create evidence record**

Write `docs/records/2026-05-16-phase5-corotated-stiffness.md` with status, scope, command outputs, source lines from `/tmp/mabd-paper/source/sections/singleabd.tex:87-123`, environment, base commit `71f274c`, an `IMPLEMENTATION_COMMIT_PENDING` marker that Step 3 replaces, and claim impact `method.single_body.corotated_stiffness`.

### Task 4: Verification And Commits

**Files:**
- All Phase 5 files.

- [ ] **Step 1: Run full verification**

Run:

```bash
/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check tests/test_mabd_single_body.py tests/test_phase0_bootstrap.py vendor/newton/newton/_src/solvers/mabd vendor/newton/newton/tests/test_mabd_single_body.py scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_mabd_single_body tests.test_phase0_bootstrap
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest vendor.newton.newton.tests.test_mabd_single_body
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
git diff --check
```

Expected: all exit 0.

- [ ] **Step 2: Commit implementation**

Run:

```bash
git add docs/records/2026-05-16-phase5-corotated-stiffness.md docs/reference/claim-boundaries.md docs/reference/paper-claims.yaml scripts/validate_docs.py tests/test_mabd_single_body.py tests/test_phase0_bootstrap.py vendor/newton/newton/_src/solvers/mabd vendor/newton/newton/tests/test_mabd_single_body.py
git commit -m "feat: add Phase 5 corotated stiffness oracle"
```

- [ ] **Step 3: Replace implementation commit marker**

Update the Phase 5 record with the commit hash from Step 2, rerun docs validation, and commit:

```bash
git add docs/records/2026-05-16-phase5-corotated-stiffness.md
git commit -m "docs: record Phase 5 implementation commit"
```

- [ ] **Step 4: Fresh final verification**

Repeat the verification commands from Step 1 after the record commit before merging or pushing.
