# Phase 9 Point Contact Forces Record

Date: 2026-05-16

## Status

passed

## Scope

Phase 9 adds CPU oracle helpers that map point loads and simple point-plane
normal penalty contacts into M-ABD affine generalized forces.

This phase verifies force mapping only. It does not verify collision detection,
broadphase, narrowphase, friction, full contact handling, generic inequality
constraints, production `SolverMABD.step()` contact input, actuation/controller
behavior, paper scenes, timing, or comparative baselines.

## Source And Environment

- repo base commit: `3aaab8e`
- plan commit: `47cd16b`
- implementation commit: `39030ef`
- review hardening commit: `REVIEW_HARDENING_COMMIT_PENDING`
- paper source version: arXiv `2603.08079v2`
- paper source paths:
  - `/tmp/mabd-paper/source/sections/singleabd.tex`
  - `/tmp/mabd-paper/source/sections/experiment.tex`
- source basis:
  - affine point map `x = J q`
  - virtual-work generalized-force mapping
  - experiment text describing implicit collision/contact penalty handling
- canonical Python:
  `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python`
- backend: CPU NumPy oracle, with existing Newton/Warp imports in test setup

## Config Path

No experiment config is used in Phase 9. The tested point-load and point-plane
force-mapping behavior is encoded in:

- `tests/test_mabd_single_body.py`
- `tests/test_mabd_phase4_solver_step.py`
- `vendor/newton/newton/tests/test_mabd_single_body.py`

## Repository

- worktree:
  `/cpfs/user/zhuzihou/dev/mabd-newton/.worktrees/phase9-point-contact-forces`
- branch: `phase9-point-contact-forces`
- base commit: `3aaab8e`
- plan commit: `47cd16b`
- implementation commit: `39030ef`
- review hardening commit: `REVIEW_HARDENING_COMMIT_PENDING`

## Vendored Newton

- vendored path: `vendor/newton`
- upstream commit: `96713fa965463b69c229a4d30582c733ff3526bb`
- local patch status: Phase 9 adds point-load and point-plane penalty force
  mapping helpers, exports, and Newton-internal tests on top of the existing
  M-ABD oracle patch stack.

## Paper Source

- arXiv ID: `2603.08079`
- arXiv version: `v2`
- local PDF: `/tmp/mabd-paper/mabd.pdf`
- local TeX source: `/tmp/mabd-paper/source`
- PDF SHA256:
  `a594e79093673c60fc59ad14f9b71f29a8f7f8e7b1c3d9c73efe6f5814cc6ec0`
- TeX source SHA256:
  `73ec398956c606dec2f8f40f0d38b9d5370e11b27830775e1b3765fe0efc563f`
- point-force source: `/tmp/mabd-paper/source/sections/singleabd.tex`
- contact-penalty source: `/tmp/mabd-paper/source/sections/experiment.tex`

## Environment

- Python: `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python`
- Isolation: cloned from
  `/cpfs/user/zhuzihou/conda-managed/envs/physics-primitive-newton-py310`
  and used through explicit `PYTHONPATH`
- Backend: CPU NumPy oracle; Warp imports initialize available CPU/CUDA devices
  for Newton state storage but Phase 9 kernels are not implemented.

## Metrics And Thresholds

- random seed: not applicable; tests use deterministic arrays only
- metrics: exact affine generalized force equality, virtual-work scalar
  equality, signed distance, penetration depth, normal velocity, active flag,
  normal force vector, generalized force vector, and configured CPU oracle
  external-force update
- thresholds: `unittest.assertAlmostEqual` defaults for scalar checks,
  `numpy.allclose` defaults for vector checks, and `atol=1.0e-12` for the
  configured CPU oracle state update

## Artifacts

- committed source: `vendor/newton/newton/_src/solvers/mabd/affine_math.py`
- committed exports: `vendor/newton/newton/_src/solvers/mabd/__init__.py`
- committed tests: `tests/test_mabd_single_body.py`,
  `tests/test_mabd_phase4_solver_step.py`, and
  `vendor/newton/newton/tests/test_mabd_single_body.py`
- committed evidence record:
  `docs/records/2026-05-16-phase9-point-contact-forces.md`
- raw artifacts: not applicable; no generated run directories, videos, or raw
  logs are committed in this phase

## TDD Evidence

RED commands:

```bash
PYTHONPATH=src:vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  -m unittest tests.test_mabd_single_body tests.test_mabd_phase4_solver_step

PYTHONPATH=vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  -m unittest vendor.newton.newton.tests.test_mabd_single_body
```

RED result:

```text
AttributeError: module 'newton._src.solvers.mabd' has no attribute
'affine_force_from_point_force'
AttributeError: module 'newton._src.solvers.mabd' has no attribute
'evaluate_point_plane_penalty_contact'
ImportError: cannot import name 'affine_force_from_point_force'
```

GREEN commands:

```bash
PYTHONPATH=src:vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  -m unittest tests.test_mabd_single_body tests.test_mabd_phase4_solver_step

PYTHONPATH=vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  -m unittest vendor.newton.newton.tests.test_mabd_single_body
```

GREEN result:

```text
public focused: Ran 28 tests in 0.427s, OK
vendored internal: Ran 6 tests in 0.369s, OK
```

## Verified Behavior

- `affine_force_from_point_force(rest_point, force)` returns `J(rest_point)^T
  force`.
- The point-force map satisfies virtual work against arbitrary affine
  increments.
- `evaluate_point_plane_penalty_contact(...)` normalizes the plane normal,
  rescales the plane offset by the same normal length, computes signed
  distance, penetration depth, normal velocity, normal force, and affine
  generalized force.
- Inactive contacts return zero world and generalized force.
- Damping is added only for inward normal velocity.
- The resulting generalized force can be passed through the configured CPU
  oracle `external_forces` path.

## Final Verification

Final verification commands:

```bash
/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check tests/test_mabd_single_body.py tests/test_mabd_phase4_solver_step.py tests/test_phase0_bootstrap.py vendor/newton/newton/_src/solvers/mabd vendor/newton/newton/tests/test_mabd_single_body.py scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_mabd_single_body tests.test_mabd_phase4_solver_step tests.test_phase0_bootstrap
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest vendor.newton.newton.tests.test_mabd_single_body
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
git diff --check
```

Implementation verification result:

```text
ruff: All checks passed!
docs: Phase 0/1/2/3/4/5/6/7/8/9 docs/provenance validation passed
focused tests: Ran 40 tests in 8.870s, OK
vendored internal tests: Ran 6 tests in 0.335s, OK
full tests: Ran 75 tests in 14.528s, OK
git diff --check: exit 0
```

## Claim Impact

New passed method claim:

- `method.force_mapping.point_load_penalty_contact`

No `experiment.*` claim is passed in this phase.
