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

## Dependency Changes

Dependency installation is an explicit environment-maintenance action, not part
of Phase 0 validation. If a future phase needs dependency mutation, record the
interpreter path, command, indexes, package versions, and reason in
`docs/records/` before using the mutated environment for evidence.
