# Phase 46 SolverMABD Model World Constraints Evidence

Date: 2026-05-18

## Status

passed_for_solver_model_world_constraint_config_slice

## Repository

- Branch: `phase46-model-world-constraints`
- Base commit: `aa9d8c6ca586d7d4faa15fda19be17a138cb8307`
- Plan commit: `a7d95d4ec069afd333de2582f9b198a62189ad73`
- RED test commit: `e53e842877b3ddd7bcaca8d56d584074601d40f7`
- Implementation commit: `da38183ca7090fc2ceb8a6f635a7aaf4c6bd02e4`
- Evidence record commit: `76ba6acba4b208b66e4088a08434a354ed3fd186`
- Review hardening commit: `47b3d63f63103ae1a81747fe7635975814b3f626`
- Worktree:
  `/cpfs/user/zhuzihou/dev/mabd-newton/.worktrees/phase46-model-world-constraints`

## Vendored Newton

- Upstream source: `https://github.com/newton-physics/newton.git`
- Upstream commit: `96713fa965463b69c229a4d30582c733ff3526bb`
- Provenance file: `vendor/newton/PROVENANCE.md`
- Local patch status: locally patched for Phase 46 in
  `vendor/newton/newton/_src/solvers/mabd/solver_mabd.py`.
- Local patch commit: `da38183ca7090fc2ceb8a6f635a7aaf4c6bd02e4`
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
