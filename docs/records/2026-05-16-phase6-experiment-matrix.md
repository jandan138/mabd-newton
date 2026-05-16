# 2026-05-16 Phase 6 Experiment Evidence Matrix

## Status

passed

## Scope

Phase 6 adds machine-checkable infrastructure for the remaining paper
experiment claims:

- `configs/experiments/paper_experiment_matrix.yaml` contains exactly one entry
  for every current `experiment.*` claim in `docs/reference/paper-claims.yaml`
- each experiment entry records source lines, known paper values, required
  lanes, asset IDs, metrics, blocking reasons, and output report path
- `assets/manifests/paper_asset_sources.yaml` records procedural, external, and
  reconstructed asset source status for every referenced asset
- `src/mabd_reproduction/experiment_contracts.py` loads and validates the
  experiment and asset contracts
- `scripts/validate_docs.py` rejects missing experiment claim coverage, missing
  asset references, duplicate scenes, and any prematurely passed experiment
  claim
- review hardening rejects string-coerced `supports_full_paper_evidence` values
  and missing or malformed `blocking_reasons`

This record does not verify scene dynamics, rendered images or videos, contact
behavior, actuation behavior, external baseline runs, timing values, paper visual
matches, or comparative reports.

## Commands

Focused contract tests:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_contracts
```

Observed before implementation: failed with missing
`mabd_reproduction.experiment_contracts`.

Observed after implementation: `Ran 3 tests in 0.085s` and `OK`.

Docs/provenance validation:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
```

Observed: `Phase 0/1/2/3/4/5/6 docs/provenance validation passed`.

Focused project tests:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_contracts tests.test_phase0_bootstrap
```

Observed after review hardening: `Ran 14 tests in 8.774s` and `OK`.

Full project tests:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
```

Observed after review hardening: `Ran 56 tests in 8.998s` and `OK`.

Focused lint:

```bash
/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check src/mabd_reproduction tests scripts/validate_docs.py
```

Observed: `All checks passed!`.

Whitespace validation:

```bash
git diff --check
```

Observed: exit 0 with no output.

## Config Paths

- `configs/experiments/paper_experiment_matrix.yaml`
- `assets/manifests/paper_asset_sources.yaml`

## Repository

- worktree:
  `/cpfs/user/zhuzihou/dev/mabd-newton/.worktrees/phase6-experiment-matrix`
- branch: `phase6-experiment-matrix`
- base commit: `a5d6546`
- plan commit: `fc38a5a`
- implementation commit: `fdb9095`
- review hardening commit: `e754917`

## Vendored Newton

- vendored path: `vendor/newton`
- upstream commit: `96713fa965463b69c229a4d30582c733ff3526bb`
- local patch status: Phase 6 does not modify vendored Newton.

## Paper Source

- arXiv ID: `2603.08079`
- arXiv version: `v2`
- local PDF: `/tmp/mabd-paper/mabd.pdf`
- local TeX source: `/tmp/mabd-paper/source`
- PDF SHA256: `a594e79093673c60fc59ad14f9b71f29a8f7f8e7b1c3d9c73efe6f5814cc6ec0`
- TeX source SHA256: `73ec398956c606dec2f8f40f0d38b9d5370e11b27830775e1b3765fe0efc563f`
- Experiment source: `/tmp/mabd-paper/source/sections/experiment.tex`

## Environment

- Python: `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python`
- Isolation: cloned from
  `/cpfs/user/zhuzihou/conda-managed/envs/physics-primitive-newton-py310`
  and used through explicit `PYTHONPATH`
- Backend: contract validation only; no simulation backend is exercised.

## Claim Impact

No paper experiment claim is set to `passed` in Phase 6.

Still not passed:

- all `experiment.*` claims

## Boundaries

The Phase 6 evidence is infrastructure evidence. It proves the experiment
matrix is complete and machine-checkable, so future scene runs can produce
auditable reports against stable contracts. It is not evidence that any paper
experiment, baseline, contact scenario, timing value, or visual result has been
reproduced.
