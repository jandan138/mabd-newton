# Phase 67 Model Plane Constraints

## Status

passed_for_solver_model_plane_constraint_config_slice

## Repository

- branch: `phase67-model-plane-constraints`
- implementation commit:
  `6252693a584e9a4cd5f1640440060c39c840fd33`
- local patch files:
  - `vendor/newton/newton/_src/solvers/mabd/solver_mabd.py`
  - `tests/test_mabd_phase4_solver_step.py`
  - `vendor/newton/newton/tests/test_mabd_phase4_solver_step.py`

## Vendored Newton

- vendored Newton upstream commit:
  `96713fa965463b69c229a4d30582c733ff3526bb`
- local patch status:
  `Phase67 modifies vendored Newton inside this repository; unmodified Newton support is not claimed.`

## Environment

- Python:
  `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python`
- reference environment:
  `/cpfs/user/zhuzihou/conda-managed/envs/physics-primitive-newton-py310`
- target environment:
  `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310`
- environment non-pollution:
  `mutates_reference_environment=false`, `uses_reference_python=false`,
  `uses_ambient_python=false`

## Evidence

- capability slice: `phase67-model-plane-constraints`
- model frequency: `mabd:plane_constraint`
- model attributes: `mabd:plane_body`, `mabd:plane_rest_point`,
  `mabd:plane_normal`, `mabd:plane_offset`, `mabd:plane_active`
- model smoke: `requested=1`, `accepted=1`, `skipped=0`
- manual-config precedence smoke:
  `model_cpu_oracle_config unset on fresh solver`
- contacts path: `NotImplementedError` retained
- paper claim status: `paper-claims.yaml` is unchanged.

## Result Boundary

No `experiment.*` claim is passed. `paper-claims.yaml` is unchanged. This is
not a contact solver, not collision detection, not Newton `Contacts` ingestion,
not paper-faithful affine collision/contact, not unmodified Newton M-ABD
support, and not full paper reproduction.

This is not unmodified Newton M-ABD support.

## Verification Commands

- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_mabd_phase4_solver_step`
  - result: `Ran 55 tests ... OK`
- `PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest newton.tests.test_mabd_phase4_solver_step`
  - result: `Ran 30 tests ... OK`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_phase0_bootstrap`
  - result: `Ran 159 tests in 52.748s ... OK`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py`
  - result: `Phase 0/1/2/3/4/5/6/7/8/9/10/11/12/13/14/15/16/17/18/19/20/21/22/23/24/25/26/27/28/29/30/31/32/33/34/35/36/37/38/39/40/41/42/43/44/45/46/47/48/49/50/51/52/53/54/55/56/57/58/59/60/61/62/63/64/65/66/67 docs/provenance validation passed`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests`
  - result: `Ran 523 tests in 520.969s ... OK`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .`
  - result: `All checks passed!`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/env/readiness_check.py`
  - result: `status=smoke_passed`,
    `role=mabd-newton-clone`, `mutates_reference_environment=false`,
    `uses_ambient_python=false`, `uses_reference_python=false`
- `PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"`
  - result:
    `/cpfs/user/zhuzihou/dev/mabd-newton/.worktrees/phase67-model-plane-constraints/vendor/newton/newton/__init__.py`
- `git diff --check`
  - result: passed with no output
