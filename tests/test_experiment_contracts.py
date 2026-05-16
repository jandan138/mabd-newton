from __future__ import annotations

import unittest
from tempfile import TemporaryDirectory
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

    def test_asset_manifest_requires_boolean_support_flag(self) -> None:
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "assets.yaml"
            path.write_text(
                yaml.safe_dump(
                    {
                        "schema_version": 1,
                        "assets": [
                            {
                                "asset_id": "bad_asset",
                                "source_type": "procedural",
                                "source_uri": "procedural://bad",
                                "license_status": "generated_by_reproduction",
                                "checksum": "not_applicable_procedural",
                                "reconstruction_status": "planned",
                                "supports_full_paper_evidence": "false",
                                "notes": "String booleans must not be coerced.",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ExperimentMatrixError, "supports_full_paper_evidence"):
                load_asset_manifest(path)

    def test_experiment_entries_require_blocking_reasons_list(self) -> None:
        base_entry = {
            "claim_id": "experiment.single_body.spinning_box",
            "scene_id": "bad_scene",
            "source_lines": ["/tmp/mabd-paper/source/sections/experiment.tex:40-55"],
            "paper_values": {"h": "unknown_in_source"},
            "required_lanes": ["mabd_newton"],
            "asset_ids": ["primitive_cube"],
            "metrics": ["energy_drift"],
            "reproduction_status": "planned",
            "output_report": "reports/experiment_matrix/bad_scene.json",
        }
        bad_values = (
            base_entry,
            {**base_entry, "blocking_reasons": "not_a_list"},
        )
        with TemporaryDirectory() as tmpdir:
            for index, entry in enumerate(bad_values):
                path = Path(tmpdir) / f"experiments_{index}.yaml"
                path.write_text(
                    yaml.safe_dump({"schema_version": 1, "experiments": [entry]}),
                    encoding="utf-8",
                )

                with self.assertRaisesRegex(ExperimentMatrixError, "blocking_reasons"):
                    load_experiment_matrix(path)


if __name__ == "__main__":
    unittest.main()
