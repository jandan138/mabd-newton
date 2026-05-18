# Environment Contract

## Canonical Local Runtime

Use the project-owned Newton Python environment cloned from the reference
project's clean Newton environment:

```text
/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310
```

Canonical interpreter:

```text
/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python
```

This environment was cloned from
`/cpfs/user/zhuzihou/conda-managed/envs/physics-primitive-newton-py310` on
2026-05-16 and contains Newton runtime dependencies such as
`warp-lang==1.13.0`, `PyYAML==6.0.3`, and the importer stack validated by
`physics-primitive-agent`.

Clone command used on this machine:

```bash
/cpfs/user/zhuzihou/conda-managed/miniforge3/bin/conda create -y \
  -p /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310 \
  --clone /cpfs/user/zhuzihou/conda-managed/envs/physics-primitive-newton-py310
```

The target was then synchronized with:

```bash
rsync -a --delete \
  /cpfs/user/zhuzihou/conda-managed/envs/physics-primitive-newton-py310/ \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/
```

## Non-Pollution Rule

Routine validation in this repository must not install packages into:

- the ambient Isaac/DSW Python;
- the shared reference Newton environment;
- the local vendored Newton tree.

Use `PYTHONPATH` to point at this repository's source and vendored Newton copy
instead of running `pip install -e .` during normal validation.

## Commands

```bash
MABD_PYTHON=/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python
PYTHONPATH=src:vendor/newton "$MABD_PYTHON" scripts/validate_docs.py
PYTHONPATH=src:vendor/newton "$MABD_PYTHON" -m unittest discover -s tests
PYTHONPATH=vendor/newton "$MABD_PYTHON" -c "import newton; print(newton.__file__)"
```

The import check must print a path under this repository's `vendor/newton`
directory. If it imports `/cpfs/user/zhuzihou/dev/newton`, the `PYTHONPATH` is
wrong for this repo.

## Machine-Checkable Readiness

Phase 8 adds a diagnostic readiness command that proves the cloned environment
contract before scene runs or benchmark records cite the interpreter:

```bash
PYTHONPATH=src:vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  scripts/env/readiness_check.py \
  --output reports/generated/environment-readiness/local/readiness.json
```

The command checks that:

- the interpreter lives under
  `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310`;
- it is not the reference environment at
  `/cpfs/user/zhuzihou/conda-managed/envs/physics-primitive-newton-py310`;
- it is not the ambient `/usr/bin` or Isaac/DSW Python;
- `newton` imports from this repository's `vendor/newton` tree;
- required runtime modules such as `yaml` and `warp` import from the cloned
  environment.

Status `smoke_passed` is environment evidence only. It does not prove solver
behavior, method correctness, scene dynamics, timing, or paper experiment
reproduction. Generated readiness JSON under `reports/generated/` is not
committed.

## Clone And Sync Maintenance

Phase 54 makes the reference-project clone process executable:

```bash
PYTHONPATH=src:vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  scripts/env/clone_from_reference.py --dry-run
```

On the current machine this dry run is expected to report `target_exists`
because `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310` already
exists. The script refuses to overwrite or refresh that target by default.

If the target environment is absent, the planned command is:

```bash
/cpfs/user/zhuzihou/conda-managed/miniforge3/bin/conda create -y \
  -p /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310 \
  --clone /cpfs/user/zhuzihou/conda-managed/envs/physics-primitive-newton-py310
```

That missing-target dry run reports `ready_to_clone`.

If an operator intentionally wants to refresh the existing target clone, the
script requires the explicit sync flag:

```bash
PYTHONPATH=src:vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  scripts/env/clone_from_reference.py --sync-existing --dry-run
```

The non-dry-run sync command is:

```bash
rsync -a --delete \
  /cpfs/user/zhuzihou/conda-managed/envs/physics-primitive-newton-py310/ \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/
```

The script's JSON plan records `mutates_reference_environment=false`,
`uses_reference_python=false`, and `uses_ambient_python=false`. A non-dry-run
`--sync-existing` mutates only the project-owned target environment and should
be recorded under `docs/records/` before its results are used as evidence.

## Dependency Changes

Dependency installation is an explicit environment-maintenance action, not part
of Phase 0 validation. If a future phase needs dependency mutation, record the
interpreter path, command, indexes, package versions, and reason in
`docs/records/` before using the mutated environment for evidence.
