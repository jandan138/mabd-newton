# Phase 45 SolverMABD Model Constraint Config Evidence

Date: 2026-05-18

## Status

passed_for_solver_model_constraint_config_slice

## Repository

- Branch: `phase45-model-constraint-config`
- Base commit: `35975a9a70213c4f91867395229d697fa30f73a9`
- Plan commit: `00e54159fcc18cd02f7c2cff74426d276b4f2e11`
- RED test commit: `83534a45b9ec1be456b3eaf9512a0a06b6639402`
- Implementation commit: `ca8c8a100471ff0b7a5a42adbb795f64f16a90a6`
- Evidence record commit: `2eb5e39126b12d4609aa51309c9a78d6a9016fbc`
- Worktree:
  `/cpfs/user/zhuzihou/dev/mabd-newton/.worktrees/phase45-model-constraint-config`

## Vendored Newton

- Upstream source: `https://github.com/newton-physics/newton.git`
- Upstream commit: `96713fa965463b69c229a4d30582c733ff3526bb`
- Provenance file: `vendor/newton/PROVENANCE.md`
- Local patch status: locally patched for Phase 45 in
  `vendor/newton/newton/_src/solvers/mabd/solver_mabd.py`.
- Local patch commit: `ca8c8a100471ff0b7a5a42adbb795f64f16a90a6`
- This record does not claim unmodified Newton supports affine-body dynamics.

## Environment

- Canonical Python:
  `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python`
- Reference project Python:
  `/cpfs/user/zhuzihou/conda-managed/envs/physics-primitive-newton-py310/bin/python`
- The Phase 44 environment clone check remains the environment guard for this
  phase: the validator rechecks editable roots and core package parity.
- No package install was performed into the DSW ambient Python or the reference
  `physics-primitive-newton-py310` environment.

## Implementation Evidence

Phase 45 adds Newton-model constraint rows to the CPU development solver path:

- model-derived `mabd:constraint` rows are translated into
  `MABDCPUOracleConstraint` entries when `SolverMABD.step()` uses its
  model-derived config path.
- Explicit `mabd:constraint_type` values now select `ball_joint(...)`,
  `hinge_joint(...)`, `universal_joint(...)`, or `prismatic_joint(...)`.
- Legacy/inferred rows with `mabd:constraint_type` 0 or 1 dispatch by rank:
  rank 3 to ball, rank 4 to universal, and rank 5 to hinge.
- `mabd:cp_index` is registered for ball-joint control-point selection.
- `mabd:rank`, `mabd:body_a`, `mabd:body_b`, `mabd:constraint_type`, and
  `mabd:gradient_mode` are validated before the config is cached.
- Existing manual `configure_cpu_oracle(...)` behavior remains supported and
  takes precedence over model-derived constraints.

Changed implementation and tests:

- `vendor/newton/newton/_src/solvers/mabd/solver_mabd.py`
- `tests/test_mabd_phase4_solver_step.py`
- `tests/test_mabd_phase2_joints_kkt.py`
- `tests/test_mabd_phase3_topology_solvers.py`
- `tests/test_phase0_bootstrap.py`
- `scripts/validate_docs.py`
- `docs/reference/claim-boundaries.md`

## RED Evidence

Before the solver change, the new model-constraint tests failed because the
schema lacked `mabd:cp_index`.

Command:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_mabd_phase4_solver_step tests.test_mabd_phase2_joints_kkt
```

Observed failure:

```text
AttributeError: Custom attribute 'mabd:cp_index' is not defined. Please declare it first using add_custom_attribute().
FAILED (errors=7)
```

After the implementation but before docs updates, the Phase45 bootstrap tests
failed because claim boundaries, the Phase45 record, and validator output were
still Phase 44-only.

## GREEN Evidence

Focused solver gate:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_mabd_phase4_solver_step tests.test_mabd_phase2_joints_kkt tests.test_mabd_phase3_topology_solvers tests.test_mabd_single_body
```

Result:

```text
Ran 78 tests in 0.686s

OK
```

## Verification Commands

These commands are required for this record and the final Phase 45 gate:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/env/readiness_check.py
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"
npm --prefix site run validate
git diff --check
```

## Claim Impact

No `experiment.*` claim is passed.

This is not a full paper reproduction. Phase 45 verifies only model-derived CPU
joint-constraint configuration for `SolverMABD.step()`. It does not verify
model-derived world constraints, Newton `Contacts`, Newton `Control` input
ingestion, GPU/Warp kernels, paper scene assets, paper timing, comparative
baselines, rendered output, generated videos, or raw simulation logs.
