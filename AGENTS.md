# Agent Rules

## Project Context

This repository is a Newton-first reproduction of "M-ABD: Scalable, Efficient,
and Robust Multi-Affine-Body Dynamics". The current repository claim is
bootstrap/provenance until method and experiment records prove more.

## Priority Order

1. Preserve the claim boundaries in `docs/reference/claim-boundaries.md`.
2. Keep Newton source provenance and local patches auditable.
3. Keep reproduction configs, manifests, records, and reports machine-checkable.
4. Prefer small tested gates over broad unverified solver changes.

## Claim Boundary Rules

- Do not claim M-ABD is implemented until `SolverMABD` code and method records exist.
- Do not claim full paper reproduction until every required paper claim is passed or explicitly incomplete.
- Do not claim unmodified Newton supports affine-body dynamics.
- Do not claim rigid `body_q` proxy collision is paper-faithful affine collision.
- Do not claim comparative baselines without installed, run, and recorded adapters.

## Source And Documentation Rules

- Durable design lives under `docs/superpowers/specs/`.
- Executable implementation plans live under `docs/superpowers/plans/`.
- Source claim boundaries live in `docs/reference/claim-boundaries.md`.
- Paper claim mappings live in `docs/reference/paper-claims.yaml`.
- Dated evidence records live under `docs/records/`.

## Artifact Policy

- Do not commit generated videos, large raw logs, simulation run directories, or raw paper assets.
- Commit small configs, manifests, tests, source code, and Markdown records.
- Paper PDF/TeX checksums may be recorded; do not vendor paper files unless a manifest proves license compatibility.

## Commands

- Canonical Python: `/cpfs/user/zhuzihou/conda-managed/envs/physics-primitive-newton-py310/bin/python`
- Do not install into the ambient DSW Python or mutate the shared Newton environment during routine validation.
- Validate docs and provenance: `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/physics-primitive-newton-py310/bin/python scripts/validate_docs.py`
- Run tests: `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/physics-primitive-newton-py310/bin/python -m unittest discover -s tests`
- Check vendored Newton import: `PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/physics-primitive-newton-py310/bin/python -c "import newton; print(newton.__file__)"`
- Whitespace check: `git diff --check`
