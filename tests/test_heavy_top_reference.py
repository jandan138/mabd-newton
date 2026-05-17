from __future__ import annotations

import unittest
from dataclasses import replace
from pathlib import Path

import numpy as np

from mabd_reproduction.experiment_configs import load_heavy_top_config
from mabd_reproduction.heavy_top_reference import roll_out_heavy_top_rk4_reference


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs/experiments/single_body_heavy_top.yaml"


class HeavyTopReferenceTests(unittest.TestCase):
    def test_rk4_reference_generates_finite_heavy_top_diagnostics(self) -> None:
        config = load_heavy_top_config(CONFIG_PATH)

        trajectory = roll_out_heavy_top_rk4_reference(config)

        self.assertEqual(trajectory.samples.shape, (config.reference.sample_count, 4))
        self.assertAlmostEqual(float(trajectory.samples[0, 0]), 0.0)
        self.assertAlmostEqual(float(trajectory.samples[-1, 0]), config.reference.duration_s)
        self.assertTrue(np.all(np.isfinite(trajectory.samples)))
        self.assertLessEqual(
            abs(trajectory.relative_energy_drift),
            config.reference.thresholds["max_relative_energy_drift"],
        )
        self.assertGreater(
            trajectory.max_nutation_angle_deg - trajectory.min_nutation_angle_deg,
            config.reference.thresholds["min_nutation_angle_range_deg"],
        )
        self.assertGreater(
            abs(trajectory.max_abs_precession_velocity_rad_s),
            config.reference.thresholds["min_abs_precession_velocity_rad_s"],
        )

    def test_rk4_reference_rejects_nonnegative_y_gravity(self) -> None:
        config = load_heavy_top_config(CONFIG_PATH)
        drifted = replace(
            config,
            reference=replace(config.reference, gravity_m_s2=np.asarray([0.0, 9.81, 0.0])),
        )

        with self.assertRaisesRegex(ValueError, "negative y"):
            roll_out_heavy_top_rk4_reference(drifted)

    def test_rk4_reference_rejects_nonpositive_inertia(self) -> None:
        config = load_heavy_top_config(CONFIG_PATH)
        drifted = replace(
            config,
            reference=replace(config.reference, principal_inertia_kg_m2=np.asarray([0.0, 1.0, 2.0])),
        )

        with self.assertRaisesRegex(ValueError, "principal_inertia_kg_m2"):
            roll_out_heavy_top_rk4_reference(drifted)

    def test_rk4_reference_rejects_invalid_sample_count(self) -> None:
        config = load_heavy_top_config(CONFIG_PATH)
        drifted = replace(config, reference=replace(config.reference, sample_count=1))

        with self.assertRaisesRegex(ValueError, "sample_count"):
            roll_out_heavy_top_rk4_reference(drifted)

    def test_rk4_reference_rejects_zero_pivot_to_com_length(self) -> None:
        config = load_heavy_top_config(CONFIG_PATH)
        drifted = replace(
            config,
            reference=replace(config.reference, pivot_to_com_m=np.zeros(3)),
        )

        with self.assertRaisesRegex(ValueError, "pivot_to_com_m"):
            roll_out_heavy_top_rk4_reference(drifted)


if __name__ == "__main__":
    unittest.main()
