from __future__ import annotations

import unittest
from pathlib import Path

import numpy as np

from mabd_reproduction.experiment_configs import load_heavy_top_config
from mabd_reproduction.heavy_top_mabd import (
    NEWTON_MODEL_DERIVED_CONFIG_SOURCE,
    NEWTON_MODEL_DERIVED_CUSTOM_FREQUENCIES,
    roll_out_heavy_top_mabd_model_derived,
)


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs/experiments/single_body_heavy_top.yaml"


class HeavyTopMABDTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
