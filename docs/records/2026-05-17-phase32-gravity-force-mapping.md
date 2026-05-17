# Phase 32 Gravity Force Mapping Record

## Status

passed

## Scope

Phase 32 adds uniform gravity generalized-force assembly to the Newton vendored
M-ABD CPU oracle. The evidence is method-level force mapping only: point-mass
gravity forces are assembled as `sum_i J_i^T m_i g` and can be included in an
unconstrained configured CPU oracle step.

This phase does not pass any `experiment.*` claim and does not claim heavy-top,
physical-pendulum, contact, timing, rendered-output, or paper-scene
reproduction.

## Config Path

No experiment config is changed in Phase 32.

## Repository

- base commit: `f8d36da`
- worktree:
  `/cpfs/user/zhuzihou/dev/mabd-newton/.worktrees/phase32-gravity-force-mapping`
- branch: `phase32-gravity-force-mapping`

## Vendored Newton

- source commit: `96713fa965463b69c229a4d30582c733ff3526bb`
- source path: `vendor/newton`
- local patch status: Phase 32 modifies vendored Newton M-ABD CPU oracle code.
- modified files:
  - `vendor/newton/newton/_src/solvers/mabd/affine_math.py`
  - `vendor/newton/newton/_src/solvers/mabd/__init__.py`
  - `vendor/newton/newton/_src/solvers/mabd/step_oracle.py`
  - `vendor/newton/newton/tests/test_mabd_single_body.py`
  - `vendor/newton/newton/tests/test_mabd_phase4_solver_step.py`

## Paper Source

- arXiv ID: `2603.08079`
- arXiv version: `v2`
- PDF SHA256: `a594e79093673c60fc59ad14f9b71f29a8f7f8e7b1c3d9c73efe6f5814cc6ec0`
- TeX source SHA256:
  `73ec398956c606dec2f8f40f0d38b9d5370e11b27830775e1b3765fe0efc563f`
- source lines:
  - `/tmp/mabd-paper/source/sections/singleabd.tex:23-26`
  - `/tmp/mabd-paper/source/sections/singleabd.tex:42`
  - `/tmp/mabd-paper/source/sections/singleabd.tex:55-58`
  - `/tmp/mabd-paper/source/sections/solver.tex:238-242`
- non-claim experiment motivation, not passed evidence:
  - `/tmp/mabd-paper/source/sections/experiment.tex:67-75`
  - `/tmp/mabd-paper/source/sections/experiment.tex:80-91`

## Environment

- interpreter:
  `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python`
- reference clone source:
  `/cpfs/user/zhuzihou/conda-managed/envs/physics-primitive-newton-py310`
- readiness status: `smoke_passed`
- mutates_reference_environment=false
- uses_reference_python=false
- uses_ambient_python=false

## Method Evidence

- public helper: `mabd.gravity_generalized_force(rest_points, masses, gravity)`
- configured step field: `MABDCPUOracleConfig.gravity`
- mapped force: `sum_i point_jacobian(rest_point_i).T @ (mass_i * gravity)`
- step integration: gravity is added to configured external forces before
  actuation force assembly.
- validation: malformed gravity vectors are rejected.
- claim id: `method.force_mapping.gravity_generalized_force`
- reproduction status: `passed`

## TDD Evidence

RED:

```text
tests.test_mabd_single_body: AttributeError: gravity_generalized_force missing
tests.test_mabd_phase4_solver_step: TypeError: unexpected keyword argument 'gravity'
newton.tests.test_mabd_single_body: ImportError: cannot import name gravity_generalized_force
newton.tests.test_mabd_phase4_solver_step: TypeError: unexpected keyword argument 'gravity'
```

GREEN:

```text
PYTHONPATH=src:vendor/newton ... -m unittest tests.test_mabd_single_body tests.test_mabd_phase4_solver_step
Ran 42 tests, OK

PYTHONPATH=vendor/newton ... -m unittest newton.tests.test_mabd_single_body newton.tests.test_mabd_phase4_solver_step
Ran 22 tests, OK
```

## Claim Impact

- `method.force_mapping.gravity_generalized_force`: passed.
- No `experiment.*` claim is passed.
- Heavy-top and physical-pendulum experiments remain intended until scene
  geometry, joint setup, references, report lanes, and comparison gates exist.

## Artifacts

- generated reports: not committed
- raw logs: not committed
- paper PDF/TeX assets: not committed

## Verification Commands

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_mabd_single_body tests.test_mabd_phase4_solver_step tests.test_phase0_bootstrap
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest newton.tests.test_mabd_single_body newton.tests.test_mabd_phase4_solver_step
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/env/readiness_check.py
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"
git diff --check
```
