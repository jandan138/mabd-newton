# 2026-05-16 Phase 7 Joint Limit Oracle

## Status

passed

## Scope

Phase 7 adds CPU oracle evidence for the paper's joint-limit treatment:

- scalar joint DOF `theta` clamps to the nearest valid range endpoint
- in-range values remain inactive and produce zero penalty
- out-of-range values produce `violation = theta - theta_hat`
- explicit dual-space penalty RHS is `k(theta - theta_hat)`
- selected KKT lower-RHS entries receive the penalty through a copy-preserving
  composition helper
- review hardening rejects non-integral row indices instead of silently
  truncating them
- dense dual KKT tests show the composed lower RHS changes the solved
  constraint target

This record does not verify generic inequality-constrained M-ABD KKT, contact,
collision, production stepping, joint-limit parameter extraction from scenes,
actuation, paper experiments, timing, or comparative baselines.

## Commands

Focused project tests:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_mabd_phase2_joints_kkt
```

Observed before implementation: failed with missing `evaluate_joint_limit` and
`apply_joint_limit_penalty_rhs`.

Observed after implementation: `Ran 14 tests in 0.434s` and `OK`.

Focused Newton-internal tests:

```bash
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest vendor.newton.newton.tests.test_mabd_phase2_joints_kkt
```

Observed before implementation: failed with missing Phase 7 joint-limit helpers.

Observed after implementation: `Ran 5 tests in 0.032s` and `OK`.

Docs/provenance validation:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
```

Observed: `Phase 0/1/2/3/4/5/6/7 docs/provenance validation passed`.

Focused project/bootstrap tests:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_mabd_phase2_joints_kkt tests.test_phase0_bootstrap
```

Observed after review hardening: `Ran 25 tests in 9.330s` and `OK`.

Full project tests:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
```

Observed after review hardening: `Ran 61 tests in 9.136s` and `OK`.

Focused lint:

```bash
/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check tests/test_mabd_phase2_joints_kkt.py tests/test_phase0_bootstrap.py vendor/newton/newton/_src/solvers/mabd vendor/newton/newton/tests/test_mabd_phase2_joints_kkt.py scripts/validate_docs.py
```

Observed after fixing `__all__` ordering: `All checks passed!`.

Whitespace validation:

```bash
git diff --check
```

Observed: exit 0 with no output.

## Config Path

No experiment config is used in Phase 7. The tested joint-limit behavior is
encoded in:

- `tests/test_mabd_phase2_joints_kkt.py`
- `vendor/newton/newton/tests/test_mabd_phase2_joints_kkt.py`

## Repository

- worktree: `/cpfs/user/zhuzihou/dev/mabd-newton/.worktrees/phase7-joint-limits`
- branch: `phase7-joint-limits`
- base commit: `2fb91ff`
- plan commit: `0565432`
- implementation commit: `5aac3c3`
- review hardening commit: `995fd92`

## Vendored Newton

- vendored path: `vendor/newton`
- upstream commit: `96713fa965463b69c229a4d30582c733ff3526bb`
- local patch status: Phase 7 adds CPU oracle joint-limit helpers, exports,
  and Newton-internal tests.

## Paper Source

- arXiv ID: `2603.08079`
- arXiv version: `v2`
- local PDF: `/tmp/mabd-paper/mabd.pdf`
- local TeX source: `/tmp/mabd-paper/source`
- PDF SHA256: `a594e79093673c60fc59ad14f9b71f29a8f7f8e7b1c3d9c73efe6f5814cc6ec0`
- TeX source SHA256: `73ec398956c606dec2f8f40f0d38b9d5370e11b27830775e1b3765fe0efc563f`
- Joint-limit source: `/tmp/mabd-paper/source/sections_a/multiabd.tex:119`

## Environment

- Python: `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python`
- Isolation: cloned from
  `/cpfs/user/zhuzihou/conda-managed/envs/physics-primitive-newton-py310`
  and used through explicit `PYTHONPATH`
- Backend: CPU NumPy oracle; no Warp joint-limit kernel is implemented.

## Claim Impact

Set to `passed`:

- `method.joint_limits.strain_clamp_penalty`

Still not passed:

- all `experiment.*` claims

## Boundaries

The Phase 7 evidence is method-level CPU oracle evidence. It proves the scalar
joint-limit clamp and explicit dual RHS algebra from the paper. It is not a
generic inequality solver, contact solver, production stepping path, or paper
scene result.
