from __future__ import annotations

import unittest
from pathlib import Path

import numpy as np

from mabd_reproduction.experiment_configs import load_physical_pendulum_config


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs/experiments/single_body_physical_pendulum.yaml"


class PhysicalPendulumRBDBaselineTests(unittest.TestCase):
    def test_rbd_baseline_rollout_generates_finite_implicit_samples(self) -> None:
        from mabd_reproduction.physical_pendulum_rbd import (
            roll_out_physical_pendulum_rbd_baseline,
        )

        config = load_physical_pendulum_config(CONFIG_PATH)
        rollout = roll_out_physical_pendulum_rbd_baseline(config)

        self.assertEqual(rollout.step_count, 16)
        self.assertEqual(rollout.sample_count, 5)
        self.assertTrue(rollout.finite)
        self.assertLessEqual(
            rollout.max_implicit_residual,
            config.rbd_baseline.thresholds["max_implicit_residual"],
        )
        self.assertLessEqual(
            rollout.max_length_constraint_error_m,
            config.rbd_baseline.thresholds["max_length_constraint_error_m"],
        )
        self.assertLessEqual(
            rollout.max_abs_angle_error_rad,
            config.rbd_baseline.thresholds["max_abs_angle_error_rad"],
        )
        self.assertEqual(rollout.samples[0].angle_rad, 0.0)
        self.assertEqual(rollout.samples[0].angular_velocity_rad_s, 0.0)
        self.assertGreaterEqual(rollout.samples[-1].joint_force_magnitude_n, 0.0)
        self.assertTrue(np.isfinite(rollout.max_abs_joint_force_error_n))
        self.assertGreaterEqual(rollout.max_abs_joint_force_error_n, 0.0)
        for sample in rollout.samples:
            self.assertGreaterEqual(sample.reference_joint_force_magnitude_n, 0.0)
            self.assertGreaterEqual(sample.abs_joint_force_error_n, 0.0)

    def test_rbd_baseline_samples_satisfy_backward_euler_kinematic_residual(self) -> None:
        from mabd_reproduction.physical_pendulum_rbd import (
            roll_out_physical_pendulum_rbd_baseline,
        )

        config = load_physical_pendulum_config(CONFIG_PATH)
        rollout = roll_out_physical_pendulum_rbd_baseline(config)
        dt = config.rbd_baseline.time_step_s

        for sample in rollout.samples[1:]:
            residual = (
                sample.angle_rad
                - sample.previous_angle_rad
                - dt * sample.angular_velocity_rad_s
            )
            self.assertLess(abs(residual), 1.0e-12)

    def test_rbd_baseline_reconstructs_constant_length_point(self) -> None:
        from mabd_reproduction.physical_pendulum_rbd import (
            physical_pendulum_rbd_point,
            roll_out_physical_pendulum_rbd_baseline,
        )

        config = load_physical_pendulum_config(CONFIG_PATH)
        rollout = roll_out_physical_pendulum_rbd_baseline(config)

        for sample in rollout.samples:
            point = physical_pendulum_rbd_point(sample.angle_rad, length_m=config.rbd_baseline.length_m)
            self.assertTrue(np.all(np.isfinite(point)))
            self.assertLess(abs(np.linalg.norm(point) - config.rbd_baseline.length_m), 1.0e-12)


if __name__ == "__main__":
    unittest.main()
