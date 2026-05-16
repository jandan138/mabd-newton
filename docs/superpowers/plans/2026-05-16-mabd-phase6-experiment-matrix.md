# Phase 6 Experiment Matrix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add machine-checkable experiment, asset, baseline, metric, and report contracts for every remaining paper experiment claim without marking any scene result as reproduced.

**Architecture:** Keep Phase 6 in the project orchestration layer, not the Newton solver. Add a small typed validator in `src/mabd_reproduction/experiment_contracts.py`, seed one paper experiment matrix YAML and one asset source matrix YAML, extend docs validation to require matrix completeness, and record the phase as infrastructure evidence only.

**Tech Stack:** Python 3.10, PyYAML, dataclasses, `unittest`, ruff, existing isolated M-ABD Python environment.

---

### Task 1: RED Tests For Experiment Matrix Completeness

**Files:**
- Create: `tests/test_experiment_contracts.py`

- [ ] **Step 1: Add failing tests**

Create `tests/test_experiment_contracts.py`:

```python
from __future__ import annotations

import unittest
from pathlib import Path

import yaml

from mabd_reproduction.experiment_contracts import (
    ExperimentMatrixError,
    load_asset_manifest,
    load_experiment_matrix,
    validate_experiment_matrix,
)


ROOT = Path(__file__).resolve().parents[1]


class ExperimentContractTests(unittest.TestCase):
    def test_every_experiment_claim_has_matrix_entry(self) -> None:
        claims = yaml.safe_load((ROOT / "docs/reference/paper-claims.yaml").read_text())["claims"]
        experiment_claim_ids = {
            claim["claim_id"] for claim in claims if str(claim["claim_id"]).startswith("experiment.")
        }

        matrix = load_experiment_matrix(ROOT / "configs/experiments/paper_experiment_matrix.yaml")

        self.assertEqual({entry.claim_id for entry in matrix.experiments}, experiment_claim_ids)
        self.assertGreaterEqual(len(matrix.experiments), 15)

    def test_experiment_matrix_references_assets_and_baselines(self) -> None:
        matrix = load_experiment_matrix(ROOT / "configs/experiments/paper_experiment_matrix.yaml")
        assets = load_asset_manifest(ROOT / "assets/manifests/paper_asset_sources.yaml")
        asset_ids = {asset.asset_id for asset in assets.assets}

        for entry in matrix.experiments:
            self.assertTrue(entry.scene_id)
            self.assertIn(entry.reproduction_status, {"planned", "blocked_by_assets", "blocked_by_baselines"})
            self.assertIn("mabd_newton", entry.required_lanes)
            self.assertTrue(set(entry.asset_ids).issubset(asset_ids))
            self.assertTrue(entry.metrics)

    def test_validator_rejects_missing_claim_coverage(self) -> None:
        matrix = load_experiment_matrix(ROOT / "configs/experiments/paper_experiment_matrix.yaml")
        claims = yaml.safe_load((ROOT / "docs/reference/paper-claims.yaml").read_text())["claims"]
        trimmed = type(matrix)(
            schema_version=matrix.schema_version,
            experiments=tuple(matrix.experiments[1:]),
        )

        with self.assertRaisesRegex(ExperimentMatrixError, "missing experiment configs"):
            validate_experiment_matrix(trimmed, claims)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests to verify RED**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_contracts
```

Expected: fail because `mabd_reproduction.experiment_contracts` and the YAML matrices do not exist.

### Task 2: Implement Contract Loader And Validator

**Files:**
- Create: `src/mabd_reproduction/experiment_contracts.py`
- Modify: `src/mabd_reproduction/__init__.py`

- [ ] **Step 1: Add dataclasses and loader**

Implement immutable dataclasses for `ExperimentEntry`, `ExperimentMatrix`, `AssetEntry`, and `AssetManifest`, plus YAML loaders that reject missing mappings/lists and unknown schema versions.

- [ ] **Step 2: Add matrix validation**

Implement `validate_experiment_matrix(matrix, paper_claims)` so it:

- extracts all `experiment.*` claim IDs from `paper_claims`
- requires exact one-to-one coverage by matrix entries
- rejects duplicate claim IDs and duplicate scene IDs
- requires non-empty `required_lanes`, `metrics`, `source_lines`, and `asset_ids`
- rejects matrix entries whose `claim_id` is not an experiment claim
- returns `None` on success and raises `ExperimentMatrixError` on failure

- [ ] **Step 3: Export helpers**

Update `src/mabd_reproduction/__init__.py` to expose the contract module names used by tests.

### Task 3: Seed Paper Experiment And Asset Matrices

**Files:**
- Create: `configs/experiments/paper_experiment_matrix.yaml`
- Create: `assets/manifests/paper_asset_sources.yaml`
- Modify: `configs/experiments/README.md`
- Modify: `assets/manifests/README.md`

- [ ] **Step 1: Seed all experiment claim entries**

Create `paper_experiment_matrix.yaml` with `schema_version: 1` and exactly one entry for each current `experiment.*` claim in `docs/reference/paper-claims.yaml`. Each entry must include:

- `claim_id`
- `scene_id`
- `source_lines`
- `paper_values`
- `required_lanes`
- `asset_ids`
- `metrics`
- `reproduction_status`
- `blocking_reasons`
- `output_report`

Use paper lines from `/tmp/mabd-paper/source/sections/experiment.tex`. Use `unknown_in_source` where parameters are missing and keep every scene status as `planned`, `blocked_by_assets`, or `blocked_by_baselines`.

- [ ] **Step 2: Seed asset source entries**

Create `paper_asset_sources.yaml` with procedural primitive assets, reconstructed geometry entries, and external-source assets for trees, cloak/avatar, armadillo, Franka, ragdoll, and protein. Each asset must include:

- `asset_id`
- `source_type`
- `source_uri`
- `license_status`
- `checksum`
- `reconstruction_status`
- `supports_full_paper_evidence`
- `notes`

- [ ] **Step 3: Update READMEs**

Document that Phase 6 commits small manifests only and that raw assets remain out of git until license/size checks pass.

### Task 4: Wire Docs Validation And Phase Record

**Files:**
- Modify: `scripts/validate_docs.py`
- Modify: `tests/test_phase0_bootstrap.py`
- Modify: `docs/reference/claim-boundaries.md`
- Create: `docs/records/2026-05-16-phase6-experiment-matrix.md`

- [ ] **Step 1: Extend docs validator**

Make `scripts/validate_docs.py` require the Phase 6 record, experiment matrix, and asset manifest. Import `validate_experiment_matrix`, load paper claims, and fail if any experiment claim lacks matrix coverage. Update output text to `Phase 0/1/2/3/4/5/6 docs/provenance validation passed`.

- [ ] **Step 2: Extend bootstrap tests**

Add tests that docs validator output includes Phase 6 and experiment claims remain not passed. Keep all current experiment paper claims as `intended`; this phase is infrastructure only.

- [ ] **Step 3: Update claim boundaries**

Add Phase 6 current/verified boundary text:

- verifies machine-checkable experiment/asset/report contracts
- does not verify any scene dynamics, image/video result, timing, baseline, contact, or comparative claim

- [ ] **Step 4: Write Phase 6 record**

Create `docs/records/2026-05-16-phase6-experiment-matrix.md` with scope, commands, base commit `a5d6546`, implementation commit marker, environment, and explicit claim impact: no experiment claims are passed.

### Task 5: Verification And Commits

**Files:**
- All Phase 6 files.

- [ ] **Step 1: Run verification**

Run:

```bash
/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check src/mabd_reproduction tests scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_contracts tests.test_phase0_bootstrap
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
git diff --check
```

Expected: all exit 0.

- [ ] **Step 2: Commit implementation**

Run:

```bash
git add assets/manifests configs/experiments docs/records/2026-05-16-phase6-experiment-matrix.md docs/reference/claim-boundaries.md docs/superpowers/plans/2026-05-16-mabd-phase6-experiment-matrix.md scripts/validate_docs.py src/mabd_reproduction tests/test_experiment_contracts.py tests/test_phase0_bootstrap.py
git commit -m "feat: add Phase 6 experiment evidence matrix"
```

- [ ] **Step 3: Backfill record commit hash**

Replace the implementation marker in the Phase 6 record with the commit hash from Step 2, rerun docs validation, then commit:

```bash
git add docs/records/2026-05-16-phase6-experiment-matrix.md
git commit -m "docs: record Phase 6 implementation commit"
```

- [ ] **Step 4: Fresh final verification**

Repeat Step 1 after the record commit before requesting review, merging, or pushing.
