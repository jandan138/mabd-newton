# Vendored Newton Provenance

## Source

- Upstream URL: `https://github.com/newton-physics/newton.git`
- Local source path: `/cpfs/user/zhuzihou/dev/newton`
- Source commit: `96713fa965463b69c229a4d30582c733ff3526bb`
- Source status at copy time: clean on `main` against `origin/main`
- Copy date: `2026-05-16`
- Copy command:

```bash
rsync -a --delete \
  --exclude .git \
  --exclude __pycache__ \
  --exclude .pytest_cache \
  --exclude .mypy_cache \
  --exclude .ruff_cache \
  /cpfs/user/zhuzihou/dev/newton/ vendor/newton/
```

## License Inventory

- `vendor/newton/LICENSE.md`: Newton Apache-2.0 license.
- `vendor/newton/newton/licenses/CC-BY-4.0.txt`: Creative Commons Attribution 4.0 license text.
- `vendor/newton/newton/licenses/unittest-parallel-LICENSE.txt`: unittest-parallel license text.
- `vendor/newton/newton/licenses/viser_and_inter-font-family.txt`: viser and Inter font family license notices.

## Local Patch Policy

All M-ABD changes must be made inside this repository. Modified vendored Newton
files must keep upstream notices intact and include prominent modification
notes where required by Apache-2.0. Every solver-facing patch needs tests under
`vendor/newton/newton/tests/` or root `tests/`, plus a dated record when it
changes reproduction evidence.

## Import Isolation Check

Run:

```bash
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"
```

Expected output path begins with this repository and contains:

```text
vendor/newton/newton/__init__.py
```
