from __future__ import annotations

import unittest
from dataclasses import replace
from pathlib import Path

import numpy as np

from mabd_reproduction.experiment_configs import load_t_handle_config
from mabd_reproduction.t_handle_mabd import roll_out_t_handle_mabd_model_derived
from mabd_reproduction.t_handle_reference import roll_out_t_handle_rk4_reference


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs/experiments/single_body_t_handle.yaml"


class THandleReferenceTests(unittest.TestCase):
    def test_rk4_reference_generates_torque_free_flip_diagnostics(self) -> None:
        config = load_t_handle_config(CONFIG_PATH)

        trajectory = roll_out_t_handle_rk4_reference(config)

        self.assertEqual(trajectory.samples.shape, (config.reference.sample_count, 4))
        self.assertAlmostEqual(float(trajectory.samples[0, 0]), 0.0)
        self.assertAlmostEqual(float(trajectory.samples[-1, 0]), config.reference.duration_s)
        self.assertTrue(np.all(np.isfinite(trajectory.samples)))
        self.assertGreaterEqual(
            trajectory.intermediate_axis_sign_flips,
            int(config.reference.thresholds["min_intermediate_axis_sign_flips"]),
        )
        self.assertLessEqual(
            abs(trajectory.relative_energy_drift),
            config.reference.thresholds["max_relative_energy_drift"],
        )
        self.assertLessEqual(
            abs(trajectory.angular_momentum_norm_drift),
            config.reference.thresholds["max_angular_momentum_norm_drift"],
        )
        intermediate_axis = int(config.reference.intermediate_axis_index)
        angular_velocity_samples = trajectory.samples[:, 1 + intermediate_axis]
        self.assertLess(float(np.min(angular_velocity_samples)), 0.0)
        self.assertGreater(float(np.max(angular_velocity_samples)), 0.0)

    def test_rk4_reference_rejects_nonzero_gravity(self) -> None:
        config = load_t_handle_config(CONFIG_PATH)
        drifted = replace(
            config,
            reference=replace(config.reference, gravity_m_s2=np.asarray([0.0, -9.81, 0.0])),
        )

        with self.assertRaisesRegex(ValueError, "zero gravity"):
            roll_out_t_handle_rk4_reference(drifted)

    def test_mabd_newton_rollout_generates_finite_diagnostic_samples(self) -> None:
        config = load_t_handle_config(CONFIG_PATH)

        rollout = roll_out_t_handle_mabd_model_derived(config)

        self.assertEqual(rollout.step_count, config.mabd_newton.step_count)
        self.assertEqual(rollout.sample_count, config.mabd_newton.sample_count)
        self.assertEqual(rollout.rotation_mode, "polar")
        self.assertAlmostEqual(rollout.samples[0].time_s, 0.0)
        self.assertAlmostEqual(rollout.samples[-1].time_s, config.reference.duration_s)
        self.assertTrue(rollout.finite)
        self.assertEqual(rollout.solver_model_config_source, "newton_model_derived")
        self.assertEqual(
            rollout.newton_model_derived_custom_frequencies,
            ("mabd:body", "mabd:gravity"),
        )
        self.assertGreaterEqual(rollout.max_proxy_inertia_relative_error, 0.0)
        self.assertGreaterEqual(rollout.max_affine_shape_spread_m, 0.0)
        self.assertTrue(all(np.isfinite(sample.angular_velocity_rad_s).all() for sample in rollout.samples))


if __name__ == "__main__":
    unittest.main()
