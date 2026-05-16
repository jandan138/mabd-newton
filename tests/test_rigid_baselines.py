from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np

from mabd_reproduction.experiment_configs import load_spinning_box_config
from mabd_reproduction.reporting import EvidenceStatus, load_claim_report


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs/experiments/single_body_spinning_box.yaml"


class RigidBaselineTests(unittest.TestCase):
    def test_spinning_box_rbd_properties_follow_paper_values(self) -> None:
        from mabd_reproduction.rigid_baselines import spinning_box_rbd_properties

        config = load_spinning_box_config(CONFIG_PATH)
        props = spinning_box_rbd_properties(config)

        self.assertAlmostEqual(props.mass_kg, 1.0)
        np.testing.assert_allclose(props.inertia_diag_kg_m2, np.full(3, 1.0 / 600.0))
        np.testing.assert_allclose(props.linear_velocity_m_s, [100.0, 0.0, 0.0])
        np.testing.assert_allclose(props.angular_velocity_rad_s, [0.0, 60000.0, 0.0])

    def test_run_spinning_box_rbd_baseline_is_deterministic_and_incomplete(self) -> None:
        from mabd_reproduction.rigid_baselines import run_spinning_box_rbd_baseline

        config = load_spinning_box_config(CONFIG_PATH)
        result = run_spinning_box_rbd_baseline(config)

        self.assertEqual(result.step_count, config.step_count)
        self.assertEqual(result.time_step_s, config.time_step_s)
        self.assertEqual(result.status, EvidenceStatus.INCOMPLETE)
        self.assertEqual(result.baseline_lane, "rbd_implicit_baseline")
        self.assertLessEqual(result.linear_momentum_error, 1.0e-12)
        self.assertLessEqual(result.angular_momentum_error, 1.0e-12)
        self.assertLessEqual(result.energy_drift, 1.0e-12)

    def test_write_spinning_box_rbd_baseline_report(self) -> None:
        from mabd_reproduction.rigid_baselines import write_spinning_box_rbd_baseline_report

        config = load_spinning_box_config(CONFIG_PATH)
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "rbd_baseline.json"
            report = write_spinning_box_rbd_baseline_report(
                path,
                config=config,
                source_commit="test-source",
                vendored_newton_commit="test-newton",
            )
            loaded = load_claim_report(path)

        self.assertEqual(report.claim_id, "experiment.single_body.spinning_box")
        self.assertEqual(loaded.baseline_lane, "rbd_implicit_baseline")
        self.assertEqual(loaded.status, EvidenceStatus.INCOMPLETE)
        self.assertIn("development baseline", loaded.failure_reason)
        self.assertIn("linear_momentum_error", loaded.observed)
        self.assertIn("angular_momentum_error", loaded.observed)
        self.assertIn("energy_drift", loaded.observed)


if __name__ == "__main__":
    unittest.main()
