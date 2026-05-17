from __future__ import annotations

import unittest
from pathlib import Path

import numpy as np

from mabd_reproduction.experiment_configs import load_physical_pendulum_config
from mabd_reproduction.physical_pendulum_mabd import roll_out_physical_pendulum_mabd_development


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs/experiments/single_body_physical_pendulum.yaml"


class PhysicalPendulumMABDTests(unittest.TestCase):
    def test_mabd_rollout_records_phase_drift_and_world_anchor_reaction(self) -> None:
        config = load_physical_pendulum_config(CONFIG_PATH)
        rollout = roll_out_physical_pendulum_mabd_development(config)

        self.assertEqual(rollout.step_count, 16)
        self.assertEqual(rollout.sample_count, 5)
        self.assertEqual(rollout.rotation_mode, "none")
        self.assertTrue(rollout.finite)
        self.assertGreaterEqual(rollout.max_world_anchor_reaction_magnitude_n, 0.0)
        for sample in rollout.samples:
            self.assertTrue(np.isfinite(sample.phase_drift_rad))
            self.assertEqual(sample.world_anchor_reaction_vector_n.shape, (3,))
            self.assertTrue(np.all(np.isfinite(sample.world_anchor_reaction_vector_n)))
            self.assertGreaterEqual(sample.world_anchor_reaction_magnitude_n, 0.0)

    def test_mabd_rollout_records_requested_polar_rotation_mode(self) -> None:
        config = load_physical_pendulum_config(CONFIG_PATH)
        rollout = roll_out_physical_pendulum_mabd_development(config, rotation_mode="polar")

        self.assertEqual(rollout.rotation_mode, "polar")
        self.assertTrue(rollout.finite)


if __name__ == "__main__":
    unittest.main()
