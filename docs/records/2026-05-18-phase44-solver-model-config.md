# Phase 44 SolverMABD Model Config Evidence

Date: 2026-05-18

## Status

passed_for_solver_model_config_slice

## Repository

- Branch: `phase44-solver-model-config`
- Base commit: `ddd2696fbbc958b5f313dd40ee49b27e9b89b454`
- Plan commit: `5d39ca8aeb29e4c353687058cb430b72625df27d`
- Implementation commit: `0e506bf9a0e53d74a06eb55d8c093909e3a72f8d`
- Worktree: `/cpfs/user/zhuzihou/dev/mabd-newton/.worktrees/phase44-solver-model-config`

## Environment

- Canonical Python:
  `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python`
- Reference project Python:
  `/cpfs/user/zhuzihou/conda-managed/envs/physics-primitive-newton-py310/bin/python`
- Both interpreters report Python 3.10.20.
- The reference environment comes from
  `/cpfs/user/zhuzihou/dev/physics-primitive-agent`.
- `pip freeze --local | sort`, ignoring editable `-e` project roots, has the
  same package set except editable project root.
- The reference project editable install points at `primitive_collision_compiler`;
  this project editable install points at `mabd_newton`.
- No package install was performed into the DSW ambient Python or the reference
  `physics-primitive-newton-py310` environment.

## Implementation Evidence

Phase 44 adds a Newton-model path for the CPU development solver:

- model-derived `SolverMABD.step()` can build its CPU oracle configuration from
  model custom `mabd:body` rows without requiring a prior manual
  `configure_cpu_oracle(...)` call.
- The registered body attributes now include `mabd:rest_point0` through
  `mabd:rest_point3`, `mabd:point_mass0` through `mabd:point_mass3`, and
  `mabd:volume`.
- The model path supports positive explicit point masses or density-derived
  uniform point masses from a positive tetrahedron volume.
- Enabled `mabd:control` rows are consumed through the model-derived path.
- Existing manual `configure_cpu_oracle(...)` behavior remains supported and
  takes precedence over the model-derived cache.
- `notify_model_changed()` clears the model-derived CPU oracle cache.
- Model-derived `mabd:constraint` rows are rejected with a clear unsupported
  message until constraint specs are stored and consumed through the model path.

Changed implementation and tests:

- `vendor/newton/newton/_src/solvers/mabd/solver_mabd.py`
- `tests/test_mabd_phase4_solver_step.py`
- `tests/test_mabd_single_body.py`
- `tests/test_mabd_control_forces.py`
- `tests/test_mabd_phase2_joints_kkt.py`
- `tests/test_mabd_phase3_topology_solvers.py`

## RED Evidence

Before the solver change, the new model-path tests failed because
`SolverMABD.step()` still required `configure_cpu_oracle(...)`, the model lacked
body rest-point attributes, and model-derived constraint rows did not have the
required boundary message.

Command:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_mabd_phase4_solver_step tests.test_mabd_single_body tests.test_mabd_control_forces tests.test_mabd_phase2_joints_kkt tests.test_mabd_phase3_topology_solvers
```

Observed failure class: missing model-derived SolverMABD CPU config path.

## GREEN Evidence

Focused solver gate:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_mabd_phase4_solver_step tests.test_mabd_single_body tests.test_mabd_control_forces tests.test_mabd_phase2_joints_kkt tests.test_mabd_phase3_topology_solvers
```

Result:

```text
Ran 82 tests in 0.562s

OK
```

Environment clone comparison:

```bash
tmp1=$(mktemp); tmp2=$(mktemp); /cpfs/user/zhuzihou/conda-managed/envs/physics-primitive-newton-py310/bin/python -m pip freeze --local | sort | grep -v '^-e ' > "$tmp1"; /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m pip freeze --local | sort | grep -v '^-e ' > "$tmp2"; diff -u "$tmp1" "$tmp2"; status=$?; rm -f "$tmp1" "$tmp2"; exit $status
```

Result: exit 0, no diff output.

## Verification Commands

These commands are required for this record and the final Phase 44 gate:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_mabd_phase4_solver_step tests.test_mabd_single_body tests.test_mabd_control_forces tests.test_mabd_phase2_joints_kkt tests.test_mabd_phase3_topology_solvers
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_phase0_bootstrap
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
git diff --check
```

## Claim Impact

No `experiment.*` claim is passed.

This is not a full paper reproduction. Phase 44 verifies only the
model-derived CPU configuration slice for `SolverMABD.step()`. It does not
verify model-derived joints or constraints, Newton `Contacts`, Newton `Control`
input ingestion, GPU/Warp kernels, paper scene assets, paper timing,
comparative baselines, rendered output, generated videos, or raw simulation
logs.
