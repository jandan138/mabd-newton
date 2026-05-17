# Phase 47 Model Gravity Config Record

## Status

passed_for_solver_model_gravity_config_slice

## Repository

- Branch: `phase47-model-gravity-config`
- Base commit: `2d03449f079fb853dae64c672686edffae9b078b`
- Plan commit: `b6abb83f5ec70f7d8b02e1e450ef05f871c4e659`
- RED test commit: `804d8ea37e3adb2140bde10823e65dd4aa96c75d`
- Implementation commit: `f393c43831e7c5dd0a665a7b9e8f4d4ff49f81b4`
- Evidence record commit: `TO_BE_BACKFILLED_PHASE47`

## Vendored Newton

- Source URL: `https://github.com/newton-physics/newton.git`
- Source commit: `96713fa965463b69c229a4d30582c733ff3526bb`
- Vendored path: `vendor/newton`
- Local patch status: locally patched for audited M-ABD reproduction slices.

## Environment

- Python: `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python`
- Validation uses `PYTHONPATH=src:vendor/newton` or
  `PYTHONPATH=vendor/newton` so imports resolve to this repository's vendored
  Newton tree.
- Phase 47 does not install into the ambient DSW Python and does not mutate the
  shared Newton environment.

## Scope

Phase 47 verifies the model-derived storage path for uniform gravity in
`SolverMABD.step()`. Registered Newton rows on the `mabd:gravity` custom
frequency are translated into the existing CPU oracle field
`MABDCPUOracleConfig.gravity`.

## Implementation Evidence

- `SolverMABD.register_custom_attributes(...)` registers the `mabd:gravity`
  custom frequency.
- `mabd:gravity_enabled` selects participating gravity rows.
- `mabd:gravity_vector` stores the world-space uniform acceleration vector.
- Zero enabled rows leave `MABDCPUOracleConfig.gravity` as `None`.
- One enabled row is passed to `MABDCPUOracleConfig.gravity`.
- Multiple enabled rows raise `ValueError("mabd:gravity supports at most one enabled row")`.
- Manual `configure_cpu_oracle(...)` precedence is preserved; manual configs do
  not build or cache model-derived gravity configs.

## RED Evidence

Command:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_mabd_phase4_solver_step
```

Expected failure before implementation:

```text
AttributeError: Custom attribute 'mabd:gravity_enabled' is not defined.
FAILED (errors=4)
```

## GREEN Evidence

Command:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_mabd_phase4_solver_step
```

Observed after implementation:

```text
Ran 41 tests
OK
```

## Verification Commands

The final Phase 47 gate set is:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/env/readiness_check.py
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"
git diff --check
```

## Claim Impact

No `experiment.*` claim is passed by Phase 47.

This record does not claim a heavy-top reproduction, physical-pendulum scene
reproduction, Newton `Contacts` support, runtime Newton `Control` support,
GPU/Warp solver support, paper timing, comparative baselines, rendered output,
generated videos, raw simulation logs, or full paper reproduction.
