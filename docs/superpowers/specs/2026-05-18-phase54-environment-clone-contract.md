# Phase54 Environment Clone Contract Spec

## Goal

Make the reference-project environment clone process executable and auditable in this repository.
The project already uses the isolated target environment
`/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310`; Phase54 turns the Phase0 recorded
manual `conda create --clone` and `rsync` commands into a checked script contract.

## Reference Pattern

`/cpfs/user/zhuzihou/dev/physics-primitive-agent` keeps project dependencies lightweight in
`pyproject.toml`/`requirements.txt` while running Newton diagnostics through the external
conda-managed interpreter
`/cpfs/user/zhuzihou/conda-managed/envs/physics-primitive-newton-py310/bin/python`.

M-ABD should keep that useful separation:

- source and tests stay in the repository;
- Newton/runtime dependencies live in a project-owned conda-managed env;
- validation uses `PYTHONPATH=src:vendor/newton`;
- routine checks do not install into ambient DSW Python or the reference environment.

## Required Behavior

- Provide an executable script under `scripts/env/` that builds the clone plan from:
  - reference env: `/cpfs/user/zhuzihou/conda-managed/envs/physics-primitive-newton-py310`;
  - target env: `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310`;
  - conda executable: `/cpfs/user/zhuzihou/conda-managed/miniforge3/bin/conda`.
- Default behavior must refuse to overwrite or sync an existing target environment.
- A missing target environment may be created with `conda create -y -p TARGET --clone REFERENCE`.
- An existing target environment may only be synchronized with explicit `--sync-existing`, using:
  `rsync -a --delete REFERENCE/ TARGET/`.
- Dry-run JSON output must expose the command plan and non-pollution flags.
- Path validation must reject target/reference aliasing or nesting.

## Non-Claims

Phase54 environment clone scripting does not prove solver behavior, M-ABD correctness, paper
experiment reproduction, comparative baselines, timing, or dependency freshness.
