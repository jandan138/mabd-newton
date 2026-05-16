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
