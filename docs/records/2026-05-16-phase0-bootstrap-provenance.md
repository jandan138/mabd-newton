# 2026-05-16 Phase 0 Bootstrap And Provenance

## Date

2026-05-16

## Status

Complete for Phase 0 bootstrap. This record does not verify any M-ABD method,
scene, timing, or comparative baseline claim.

## Commands

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"
git diff --check
git status --short --branch
```

## Observed Results

- Documentation/provenance validator passed with
  `Phase 0 docs/provenance validation passed`.
- Unit tests passed: `Ran 5 tests`; `OK`.
- `import newton` resolved to
  `/cpfs/user/zhuzihou/dev/mabd-newton/.worktrees/phase0-bootstrap-provenance/vendor/newton/newton/__init__.py`.
- Whitespace check passed.
- Git status before this record was created showed no uncommitted files.

## Environment

- Dedicated M-ABD Python:
  `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python`
- Python version: `3.10.20`
- `warp-lang`: `1.13.0`
- `PyYAML`: `6.0.3`
- `newton` distribution metadata: `1.3.0.dev0`
- Clone source:
  `/cpfs/user/zhuzihou/conda-managed/envs/physics-primitive-newton-py310`
- Clone command:

```bash
/cpfs/user/zhuzihou/conda-managed/miniforge3/bin/conda create -y \
  -p /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310 \
  --clone /cpfs/user/zhuzihou/conda-managed/envs/physics-primitive-newton-py310
```

- Synchronization command after clone:

```bash
rsync -a --delete \
  /cpfs/user/zhuzihou/conda-managed/envs/physics-primitive-newton-py310/ \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/
```

The environment clone and synchronization do not modify the reference
`physics-primitive-agent` environment or the ambient Isaac/DSW Python.

## Source Versions

- Paper: arXiv `2603.08079v2`
- Paper PDF sha256:
  `a594e79093673c60fc59ad14f9b71f29a8f7f8e7b1c3d9c73efe6f5814cc6ec0`
- Paper TeX source sha256:
  `73ec398956c606dec2f8f40f0d38b9d5370e11b27830775e1b3765fe0efc563f`
- Vendored Newton source commit:
  `96713fa965463b69c229a4d30582c733ff3526bb`
- Vendored Newton copy status: copied from clean local source without `.git`

## Artifacts

- Claim boundaries: `docs/reference/claim-boundaries.md`
- Paper claim manifest: `docs/reference/paper-claims.yaml`
- Environment contract: `docs/operations/environment.md`
- Vendored Newton provenance: `vendor/newton/PROVENANCE.md`
- Validator: `scripts/validate_docs.py`
- Tests: `tests/test_phase0_bootstrap.py`

## Claim Impact

- Current claim expands from reviewed design only to reviewed design plus
  Phase 0 bootstrap/provenance infrastructure.
- No solver, scene, baseline, contact, timing, or full-reproduction claim is
  verified by this record.

## Next Phase

Phase 1 starts single-body ABD implementation with dense CPU oracles, affine
state tests, co-rotated stiffness, polar/no-polar modes, and invariants.
