# Phase 46 SolverMABD Model World Constraints Evidence

Date: 2026-05-18

## Status

passed_for_solver_model_world_constraint_config_slice

## Repository

- Branch: `phase46-model-world-constraints`
- Base commit: `f88b3e990dde2bf50810f5b8551c049c34106f1e`
- Plan commit: `bec91f550c320b00406c112cf8d9573d923ebd92`
- RED test commit: `dee93c4029cde024a6bd64cfa8b8cb9c7bf73ef6`
- Implementation commit: `0cef329e201d7d4a3d2b285420e092dc26d23ea4`
- Evidence record commit: `413b03e76ec52595fc83532ba4e89828d4e02029`
- Review hardening commit: `f3246df7df1461838a6a80e21dc8e2f7723288bd`
- Worktree:
  `/cpfs/user/zhuzihou/dev/mabd-newton/.worktrees/phase46-model-world-constraints`

## Vendored Newton

- Upstream source: `https://github.com/newton-physics/newton.git`
- Upstream commit: `96713fa965463b69c229a4d30582c733ff3526bb`
- Provenance file: `vendor/newton/PROVENANCE.md`
- Local patch status: locally patched for Phase 46 in
  `vendor/newton/newton/_src/solvers/mabd/solver_mabd.py`.
- Local patch commit: `0cef329e201d7d4a3d2b285420e092dc26d23ea4`
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

Phase 46 adds Newton-model world-anchor rows to the CPU development solver path:

- `SolverMABD.register_custom_attributes(...)` registers the
  `mabd:world_constraint` custom frequency.
- `mabd:world_body`, `mabd:world_rest_point`, and `mabd:world_point` model
  attributes are stored on `mabd:world_constraint` rows.
- Model-derived rows are translated into `MABDCPUOracleWorldConstraint`
  entries when `SolverMABD.step()` uses its model-derived config path.
- The existing dense CPU oracle enforces the world-anchor point residual and
  exposes the world-anchor reaction as the first three `dlambda` entries for a
  single world constraint.
- Invalid `mabd:world_body` references are rejected before solving.
- Existing manual `configure_cpu_oracle(...)` behavior remains supported and
  takes precedence over model-derived world constraints.

Changed implementation and tests:

- `vendor/newton/newton/_src/solvers/mabd/solver_mabd.py`
- `tests/test_mabd_phase4_solver_step.py`
- `tests/test_phase0_bootstrap.py`
- `scripts/validate_docs.py`
- `docs/reference/claim-boundaries.md`

## RED Evidence

Before the solver change, the new model-world-constraint tests failed because
the schema lacked `mabd:world_body`.

Command:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_mabd_phase4_solver_step
```

Observed failure:

```text
AttributeError: Custom attribute 'mabd:world_body' is not defined. Please declare it first using add_custom_attribute().
FAILED (errors=3)
```

## GREEN Evidence

Focused solver gate:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_mabd_phase4_solver_step
```

Result:

```text
Ran 37 tests in 0.576s

OK
```

## Verification Commands

These commands are required for this record and the final Phase 46 gate:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/env/readiness_check.py
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"
git diff --check
```

## Claim Impact

No `experiment.*` claim is passed.

This is not a full paper reproduction. Phase 46 verifies only model-derived CPU
world-constraint configuration for `SolverMABD.step()`. It does not verify
Newton `Contacts`, Newton `Control` input ingestion, GPU/Warp kernels, paper
scene assets, paper timing, comparative baselines, rendered output, generated
videos, or raw simulation logs.
