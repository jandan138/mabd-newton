from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np

from mabd_reproduction.reporting import EvidenceStatus, load_claim_report
from mabd_reproduction.single_body_reports import write_spinning_box_development_report


class SingleBodyReportLaneTests(unittest.TestCase):
    def test_spinning_box_development_report_is_machine_checkable(self) -> None:
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "single_body_spinning_box.json"
            report = write_spinning_box_development_report(
                path,
                source_commit="test-source",
                vendored_newton_commit="test-newton",
            )
            loaded = load_claim_report(path)

        self.assertEqual(report.claim_id, "experiment.single_body.spinning_box")
        self.assertEqual(loaded.status, EvidenceStatus.INCOMPLETE)
        self.assertEqual(loaded.baseline_lane, "mabd_newton")
        self.assertIn("rbd_implicit_baseline", loaded.failure_reason)
        self.assertEqual(loaded.observed["step_count"], 4)
        self.assertLessEqual(loaded.observed["energy_drift"], loaded.threshold["energy_drift"])
        self.assertLessEqual(
            loaded.observed["generalized_momentum_delta_norm"],
            loaded.threshold["generalized_momentum_delta_norm"],
        )

    def test_spinning_box_report_uses_run_config(self) -> None:
        from mabd_reproduction.experiment_configs import load_spinning_box_config
        from mabd_reproduction.spinning_box_physics import (
            spinning_box_contact_diagnostics,
            spinning_box_cube_corners,
        )

        root = Path(__file__).resolve().parents[1]
        config = load_spinning_box_config(root / "configs/experiments/single_body_spinning_box.yaml")
        corners = spinning_box_cube_corners(config)
        diagnostics = spinning_box_contact_diagnostics(config, config.initial_q, config.initial_qd)
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "single_body_spinning_box.json"
            report = write_spinning_box_development_report(
                path,
                config=config,
                source_commit="test-source",
                vendored_newton_commit="test-newton",
            )
            loaded = load_claim_report(path)

        self.assertEqual(report.scene_id, config.scene_id)
        self.assertEqual(report.asset_hashes, {"primitive_cube": "not_applicable_procedural"})
        self.assertEqual(loaded.observed["step_count"], config.step_count)
        self.assertEqual(loaded.observed["time_step_s"], config.time_step_s)
        self.assertEqual(loaded.threshold, config.thresholds)
        self.assertEqual(loaded.status, config.report_status)
        self.assertEqual(loaded.failure_reason, config.failure_reason)
        self.assertIn("linear_momentum_error", loaded.observed)
        self.assertIn("angular_momentum_error", loaded.observed)
        self.assertIn("final_linear_momentum_kg_m_s", loaded.observed)
        self.assertIn("final_angular_momentum_kg_m2_s", loaded.observed)
        self.assertIn("paper_spatial_twist", loaded.observed)
        self.assertLessEqual(
            loaded.observed["linear_momentum_error"],
            loaded.threshold["linear_momentum_error"],
        )
        self.assertLessEqual(
            loaded.observed["angular_momentum_error"],
            loaded.threshold["angular_momentum_error"],
        )
        self.assertEqual(
            loaded.observed["mass_diagonal_source"],
            "paper_uniform_centered_cube_continuous",
        )
        self.assertEqual(len(loaded.observed["mabd_mass_diagonal"]), 12)
        self.assertEqual(corners.shape, (8, 3))
        self.assertAlmostEqual(float(corners[:, 0].max()), 0.05)
        self.assertAlmostEqual(float(corners[:, 0].min()), -0.05)
        self.assertEqual(diagnostics.corner_count, 8)
        self.assertEqual(diagnostics.active_contact_count, 0)
        self.assertEqual(len(diagnostics.corner_signed_distances), 8)
        self.assertEqual(diagnostics.total_generalized_force.shape, (12,))
        self.assertAlmostEqual(diagnostics.min_signed_distance, 0.0)
        self.assertAlmostEqual(diagnostics.max_penetration_depth, 0.0)
        self.assertTrue(np.allclose(diagnostics.total_normal_force, np.zeros(3)))
        self.assertTrue(np.allclose(diagnostics.total_generalized_force, np.zeros(12)))
        self.assertEqual(loaded.observed["contact_surface_type"], "plane")
        self.assertEqual(loaded.observed["contact_corner_count"], 8)
        self.assertEqual(loaded.observed["contact_active_count"], 0)
        self.assertAlmostEqual(loaded.observed["contact_min_signed_distance_m"], 0.0)
        self.assertAlmostEqual(loaded.observed["contact_max_penetration_m"], 0.0)
        self.assertIn("contact_total_normal_force_n", loaded.observed)
        self.assertIn("contact_total_generalized_force", loaded.observed)
        self.assertEqual(len(loaded.observed["contact_corner_signed_distances_m"]), 8)
        self.assertEqual(len(loaded.observed["contact_total_generalized_force"]), 12)
        self.assertTrue(
            np.allclose(loaded.observed["contact_total_normal_force_n"], np.zeros(3))
        )
        self.assertTrue(
            np.allclose(loaded.observed["contact_total_generalized_force"], np.zeros(12))
        )
        self.assertAlmostEqual(loaded.observed["mass_kg"], 1.0)
        self.assertAlmostEqual(loaded.observed["initial_energy_j"], 3005000.0)
        self.assertAlmostEqual(loaded.observed["final_energy_j"], 3005000.0)
        self.assertLessEqual(loaded.observed["relative_energy_drift"], 1.0e-15)
        self.assertEqual(loaded.observed["initial_position_m"], [0.0, 0.05, 0.0])
        np.testing.assert_allclose(
            loaded.observed["final_position_m"],
            [4.0, 0.05, 0.0],
            atol=1.0e-12,
        )


if __name__ == "__main__":
    unittest.main()
