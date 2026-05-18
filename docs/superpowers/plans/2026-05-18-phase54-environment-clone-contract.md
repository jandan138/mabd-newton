# Phase54 Environment Clone Contract Plan

## Scope

Turn the existing Phase0 environment clone record into a small tested maintenance tool and record
the exact non-pollution boundary.

## Steps

- [ ] Add failing tests for clone-plan defaults, target-exists refusal, explicit sync, and CLI
      dry-run JSON.
- [ ] Implement a small environment clone planner/runner module and `scripts/env/clone_from_reference.py`.
- [ ] Update `docs/operations/environment.md`, `docs/reference/claim-boundaries.md`, and the docs
      validator so the script contract stays machine-checkable.
- [ ] Add a dated Phase54 record with commands and claim impact.
- [ ] Run targeted environment tests, readiness check, docs validator, ruff, unittest discovery,
      Newton import check, and `git diff --check`.

## Guardrails

- Do not mutate `/cpfs/user/zhuzihou/conda-managed/envs/physics-primitive-newton-py310`.
- Do not install into `/usr/bin/python3`, Isaac/DSW Python, or the vendored Newton tree.
- Do not run destructive target sync unless an operator explicitly invokes `--sync-existing`.
