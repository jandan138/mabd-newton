# Phase 54 Environment Clone Contract

## Status

passed_for_environment_clone_contract

## Scope

- branch: `phase54-environment-clone-contract`
- base source commit: `75eb19423f5b7a3be1129bf44341fb19901c4276`
- vendored Newton upstream commit: `96713fa965463b69c229a4d30582c733ff3526bb`
- paper source version: `2603.08079v2`
- Python: `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python`
- reference environment:
  `/cpfs/user/zhuzihou/conda-managed/envs/physics-primitive-newton-py310`
- target environment:
  `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310`

## Evidence

Phase 54 makes the Phase 0 environment clone procedure executable and tested:

- script: `scripts/env/clone_from_reference.py`
- planner: `src/mabd_reproduction/environment_clone.py`
- tests: `tests/test_environment_clone.py`
- default dry-run status on this machine: `target_exists`
- missing-target plan status: `ready_to_clone`
- explicit existing-target sync plan status: `ready_to_sync_existing`
- path validation rejects reference/target aliasing and nesting
- clone command:
  `/cpfs/user/zhuzihou/conda-managed/miniforge3/bin/conda create -y -p /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310 --clone /cpfs/user/zhuzihou/conda-managed/envs/physics-primitive-newton-py310`
- sync command:
  `rsync -a --delete /cpfs/user/zhuzihou/conda-managed/envs/physics-primitive-newton-py310/ /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/`
- non-pollution fields:
  `mutates_reference_environment=false`, `uses_reference_python=false`,
  `uses_ambient_python=false`

## Result Boundary

Phase 54 records environment maintenance tooling only. It does not install
packages, refresh the target clone during routine validation, mutate the
reference `physics-primitive-agent` environment, mutate the ambient DSW Python,
or modify the vendored Newton tree.

No `experiment.*` claim is passed. This record does not prove dependency freshness,
solver behavior, M-ABD method correctness, scene dynamics, paper experiment
reproduction, timing, comparative baselines, runtime performance, rendered
output, or a full paper reproduction.

## Commands

- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_environment_clone tests.test_environment_readiness`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/env/clone_from_reference.py --dry-run`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/env/readiness_check.py`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests`
- `PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"`
- `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .`
- `git diff --check`
