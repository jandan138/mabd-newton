from __future__ import annotations

import unittest
from pathlib import Path

import numpy as np

from mabd_reproduction.experiment_configs import load_heavy_top_config
from mabd_reproduction.heavy_top_mabd import (
    NEWTON_MODEL_DERIVED_CONFIG_SOURCE,
    NEWTON_MODEL_DERIVED_CUSTOM_FREQUENCIES,
    _point_mass_energy,
    _sampled_precession_velocities_rad_s,
    roll_out_heavy_top_mabd_model_derived,
)
from newton.solvers import mabd


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs/experiments/single_body_heavy_top.yaml"


class HeavyTopMABDTests(unittest.TestCase):
    def test_sampled_precession_velocity_stencil_handles_unwrapped_crossing(self) -> None:
        raw_precession = np.asarray([3.0, -3.0, -2.5], dtype=float)
        unwrapped_precession = np.unwrap(raw_precession)
        sample_times = np.asarray([0.0, 1.0, 3.0], dtype=float)

        velocities = _sampled_precession_velocities_rad_s(
            unwrapped_precession,
            sample_times,
        )

        expected = np.asarray(
            [
                (unwrapped_precession[1] - unwrapped_precession[0]) / 1.0,
                (unwrapped_precession[2] - unwrapped_precession[0]) / 3.0,
                (unwrapped_precession[2] - unwrapped_precession[1]) / 2.0,
            ],
            dtype=float,
        )
        np.testing.assert_allclose(velocities, expected, rtol=0.0, atol=1.0e-15)

    def test_point_mass_energy_fixture_matches_hand_calculation(self) -> None:
        rest_points_m = np.asarray(
            [
                [0.0, 1.0, 0.0],
                [0.0, 3.0, 0.0],
            ],
            dtype=float,
        )
        point_masses_kg = np.asarray([2.0, 3.0], dtype=float)
        gravity_m_s2 = np.asarray([0.0, -10.0, 0.0], dtype=float)
        q = mabd.pack_q(np.eye(3), np.zeros(3, dtype=float))
        qd = mabd.pack_q(np.zeros((3, 3), dtype=float), np.asarray([0.0, 2.0, 0.0]))

        energy = _point_mass_energy(
            q,
            qd,
            rest_points_m=rest_points_m,
            point_masses_kg=point_masses_kg,
            gravity_m_s2=gravity_m_s2,
        )

        self.assertAlmostEqual(energy, 120.0)

    def test_model_derived_heavy_top_lane_generates_bounded_diagnostics(self) -> None:
        config = load_heavy_top_config(CONFIG_PATH)

        rollout = roll_out_heavy_top_mabd_model_derived(config)

        self.assertEqual(rollout.solver_model_config_source, NEWTON_MODEL_DERIVED_CONFIG_SOURCE)
        self.assertEqual(
            rollout.newton_model_derived_custom_frequencies,
            NEWTON_MODEL_DERIVED_CUSTOM_FREQUENCIES,
        )
        self.assertEqual(rollout.sample_count, config.mabd_newton.sample_count)
        self.assertTrue(rollout.finite)
        self.assertLessEqual(
            rollout.max_pivot_residual_m,
            config.mabd_newton.thresholds["max_pivot_residual_m"],
        )
        self.assertLessEqual(
            rollout.max_constraint_residual_norm,
            config.mabd_newton.thresholds["max_constraint_residual_norm"],
        )
        self.assertGreaterEqual(
            rollout.max_nutation_angle_deg - rollout.min_nutation_angle_deg,
            config.mabd_newton.thresholds["min_nutation_angle_range_deg"],
        )
        self.assertTrue(
            np.all(
                np.isfinite(
                    [
                        sample.nutation_angle_deg
                        for sample in rollout.samples
                    ]
                )
            )
        )
        self.assertTrue(np.isfinite(rollout.energy_initial))
        self.assertTrue(np.isfinite(rollout.energy_final))
        self.assertTrue(np.isfinite(rollout.relative_energy_drift))
        self.assertGreater(rollout.energy_initial, 0.0)
        sample_precession_velocities = [
            sample.precession_velocity_rad_s for sample in rollout.samples
        ]
        self.assertTrue(np.all(np.isfinite(sample_precession_velocities)))
        self.assertAlmostEqual(
            max(abs(value) for value in sample_precession_velocities),
            rollout.max_abs_precession_velocity_rad_s,
        )

    def test_model_derived_heavy_top_paper_horizon_matches_reference_sample_grid(self) -> None:
        config = load_heavy_top_config(CONFIG_PATH)

        rollout = roll_out_heavy_top_mabd_model_derived(
            config,
            mabd_config=config.mabd_paper_horizon,
        )

        self.assertEqual(rollout.step_count, 10000)
        self.assertEqual(rollout.sample_count, config.reference.sample_count)
        self.assertEqual(len(rollout.samples), config.reference.sample_count)
        self.assertTrue(rollout.finite)
        self.assertLessEqual(
            rollout.max_pivot_residual_m,
            config.mabd_paper_horizon.thresholds["max_pivot_residual_m"],
        )
        self.assertLessEqual(
            rollout.max_constraint_residual_norm,
            config.mabd_paper_horizon.thresholds["max_constraint_residual_norm"],
        )
        self.assertTrue(np.isfinite(rollout.max_affine_shape_spread_m))
        self.assertTrue(np.isfinite(rollout.relative_energy_drift))
        expected_times = np.linspace(
            0.0,
            config.reference.duration_s,
            config.reference.sample_count,
        )
        actual_times = np.asarray([sample.time_s for sample in rollout.samples], dtype=float)
        np.testing.assert_allclose(actual_times, expected_times, rtol=0.0, atol=1.0e-12)
        self.assertAlmostEqual(rollout.samples[-1].time_s, 10.0)
        self.assertTrue(np.all(np.isfinite(actual_times)))
        self.assertTrue(
            np.all(
                np.isfinite(
                    [sample.precession_velocity_rad_s for sample in rollout.samples]
                )
            )
        )


if __name__ == "__main__":
    unittest.main()
