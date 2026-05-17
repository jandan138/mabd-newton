from __future__ import annotations

import unittest
from pathlib import Path

import numpy as np

from mabd_reproduction.experiment_configs import load_physical_pendulum_config
from mabd_reproduction.physical_pendulum_mabd import (
    roll_out_physical_pendulum_mabd_development,
    roll_out_physical_pendulum_mabd_model_derived,
)


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
        self.assertTrue(np.isfinite(rollout.max_abs_joint_force_error_n))
        self.assertGreaterEqual(rollout.max_abs_joint_force_error_n, 0.0)
        for sample in rollout.samples:
            self.assertTrue(np.isfinite(sample.phase_drift_rad))
            self.assertEqual(sample.world_anchor_reaction_vector_n.shape, (3,))
            self.assertTrue(np.all(np.isfinite(sample.world_anchor_reaction_vector_n)))
            self.assertGreaterEqual(sample.world_anchor_reaction_magnitude_n, 0.0)
            self.assertGreaterEqual(sample.reference_joint_force_magnitude_n, 0.0)
            self.assertGreaterEqual(sample.abs_joint_force_error_n, 0.0)

    def test_mabd_rollout_records_requested_polar_rotation_mode(self) -> None:
        config = load_physical_pendulum_config(CONFIG_PATH)
        rollout = roll_out_physical_pendulum_mabd_development(config, rotation_mode="polar")

        self.assertEqual(rollout.rotation_mode, "polar")
        self.assertTrue(rollout.finite)

    def test_model_derived_rollout_matches_manual_oracle_diagnostic(self) -> None:
        config = load_physical_pendulum_config(CONFIG_PATH)

        manual = roll_out_physical_pendulum_mabd_development(config, rotation_mode="polar")
        model = roll_out_physical_pendulum_mabd_model_derived(config, rotation_mode="polar")

        self.assertEqual(model.solver_model_config_source, "newton_model_derived")
        self.assertEqual(model.rotation_mode, "polar")
        self.assertEqual(model.sample_count, manual.sample_count)
        self.assertEqual(model.step_count, manual.step_count)
        self.assertTrue(model.finite)
        np.testing.assert_allclose(
            [sample.angle_rad for sample in model.samples],
            [sample.angle_rad for sample in manual.samples],
            atol=2.0e-6,
        )
        np.testing.assert_allclose(
            [sample.pivot_residual_m for sample in model.samples],
            [sample.pivot_residual_m for sample in manual.samples],
            atol=2.0e-6,
        )
        np.testing.assert_allclose(
            [sample.world_anchor_reaction_magnitude_n for sample in model.samples],
            [sample.world_anchor_reaction_magnitude_n for sample in manual.samples],
            atol=2.0e-5,
        )


if __name__ == "__main__":
    unittest.main()
