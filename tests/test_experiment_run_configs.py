from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import yaml

from mabd_reproduction.experiment_configs import (
    ExperimentRunConfigError,
    load_spinning_box_config,
    validate_spinning_box_config_against_matrix,
)
from mabd_reproduction.experiment_contracts import load_experiment_matrix
from mabd_reproduction.reporting import EvidenceStatus


ROOT = Path(__file__).resolve().parents[1]


class ExperimentRunConfigTests(unittest.TestCase):
    def test_spinning_box_config_is_machine_checkable(self) -> None:
        config = load_spinning_box_config(ROOT / "configs/experiments/single_body_spinning_box.yaml")

        self.assertEqual(config.schema_version, 1)
        self.assertEqual(config.claim_id, "experiment.single_body.spinning_box")
        self.assertEqual(config.scene_id, "single_body_spinning_box")
        self.assertEqual(config.asset_ids, ("primitive_cube",))
        self.assertEqual(config.baseline_lane, "mabd_newton")
        self.assertEqual(config.report_status, EvidenceStatus.INCOMPLETE)
        self.assertIn("rbd_implicit_baseline", config.failure_reason)
        self.assertEqual(config.time_step_s, 0.01)
        self.assertEqual(config.step_count, 4)
        self.assertEqual(config.initial_qd.shape, (12,))
        self.assertEqual(config.mass_diagonal.shape, (12,))
        self.assertIn("energy_drift", config.thresholds)
        self.assertIn("generalized_momentum_delta_norm", config.thresholds)

    def test_spinning_box_config_matches_experiment_matrix(self) -> None:
        config = load_spinning_box_config(ROOT / "configs/experiments/single_body_spinning_box.yaml")
        matrix = load_experiment_matrix(ROOT / "configs/experiments/paper_experiment_matrix.yaml")

        validate_spinning_box_config_against_matrix(config, matrix)

    def test_spinning_box_config_rejects_passed_experiment_status(self) -> None:
        with TemporaryDirectory() as tmpdir:
            source = yaml.safe_load((ROOT / "configs/experiments/single_body_spinning_box.yaml").read_text())
            source["report"]["status"] = "passed"
            path = Path(tmpdir) / "bad.yaml"
            path.write_text(yaml.safe_dump(source), encoding="utf-8")

            with self.assertRaisesRegex(ExperimentRunConfigError, "passed experiment"):
                load_spinning_box_config(path)


if __name__ == "__main__":
    unittest.main()
