from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np

from mabd_reproduction.reporting import EvidenceStatus, load_claim_report
from mabd_reproduction.single_body_reports import (
    write_spinning_box_development_report,
    write_spinning_box_paper_horizon_report,
)


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
        self.assertGreater(
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
        self.assertTrue(np.isfinite(loaded.observed["final_energy_j"]))
        self.assertTrue(np.isfinite(loaded.observed["relative_energy_drift"]))
        self.assertGreater(loaded.observed["relative_energy_drift"], 0.1)
        self.assertLess(loaded.observed["relative_energy_drift"], 1.0)
        self.assertEqual(loaded.observed["initial_position_m"], [0.0, 0.05, 0.0])
        np.testing.assert_allclose(
            loaded.observed["final_position_m"],
            [4.0, 0.05, 0.0],
            atol=1.0e-12,
        )
        samples = loaded.observed["trajectory_samples"]
        self.assertEqual(len(samples), config.step_count + 1)
        self.assertEqual(samples[0]["step_index"], 0)
        self.assertEqual(samples[-1]["step_index"], config.step_count)
        self.assertEqual(samples[0]["position_m"], [0.0, 0.05, 0.0])
        np.testing.assert_allclose(
            samples[-1]["position_m"],
            [4.0, 0.05, 0.0],
            atol=1.0e-12,
        )
        self.assertEqual(len(samples[-1]["affine_matrix"]), 3)
        self.assertEqual(len(samples[-1]["affine_matrix"][0]), 3)
        self.assertEqual(len(samples[-1]["affine_singular_values"]), 3)
        self.assertAlmostEqual(samples[0]["affine_orthogonality_error"], 0.0)
        self.assertGreater(samples[-1]["affine_orthogonality_error"], 1.0)
        self.assertLess(samples[-1]["affine_orthogonality_error"], 10.0)
        self.assertEqual(loaded.observed["initial_affine_orthogonality_error"], 0.0)
        self.assertGreater(loaded.observed["final_affine_orthogonality_error"], 1.0)
        self.assertLess(loaded.observed["final_affine_orthogonality_error"], 10.0)
        self.assertLess(abs(loaded.observed["final_affine_determinant"]), 10.0)
        self.assertEqual(
            loaded.observed["affine_shape_diagnostic_status"],
            "development_gap_observed",
        )
        self.assertEqual(loaded.observed["mabd_rotation_mode"], "polar")
        self.assertEqual(
            loaded.observed["material_model"],
            "paper_linear_elastic_corotated_development",
        )
        self.assertEqual(
            loaded.observed["material_rhs_frame"],
            "corotated_local_all_blocks",
        )
        self.assertEqual(
            loaded.observed["translation_frame"],
            "corotated_polar_all_blocks",
        )
        self.assertAlmostEqual(loaded.observed["material_young_modulus_pa"], 1.0e9)
        self.assertAlmostEqual(loaded.observed["material_poisson_ratio"], 0.3)
        self.assertAlmostEqual(loaded.observed["material_volume_m3"], 0.001)
        self.assertGreater(loaded.observed["material_stiffness_trace"], 0.0)
        self.assertGreater(loaded.observed["material_stiffness_rank"], 0)
        self.assertTrue(np.isfinite(loaded.observed["final_affine_orthogonality_error"]))
        self.assertTrue(np.isfinite(loaded.observed["final_affine_determinant"]))
        self.assertTrue(
            np.all(np.isfinite(np.asarray(loaded.observed["final_affine_singular_values"])))
        )

    def test_spinning_box_paper_horizon_report_records_development_gap(self) -> None:
        from mabd_reproduction.experiment_configs import load_spinning_box_config

        root = Path(__file__).resolve().parents[1]
        config = load_spinning_box_config(root / "configs/experiments/single_body_spinning_box.yaml")
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "single_body_spinning_box_paper_horizon.json"
            report = write_spinning_box_paper_horizon_report(
                path,
                config=config,
                source_commit="test-source",
                vendored_newton_commit="test-newton",
            )
            loaded = load_claim_report(path)

        self.assertEqual(report.scene_id, config.scene_id)
        self.assertEqual(loaded.status, EvidenceStatus.INCOMPLETE)
        self.assertEqual(loaded.baseline_lane, "mabd_newton")
        self.assertEqual(loaded.solver_mode, "mabd_cpu_oracle_paper_horizon_diagnostic")
        self.assertNotIn("lane_gate_status", loaded.observed)
        self.assertEqual(loaded.observed["paper_horizon_duration_s"], 10.0)
        self.assertEqual(loaded.observed["paper_step_sizes_s"], [0.01, 0.001])
        self.assertEqual(
            loaded.observed["mabd_paper_horizon_status"],
            "development_gap_observed",
        )
        self.assertEqual(
            loaded.observed["mabd_kinematic_feasibility_status"],
            "paper_momentum_requires_affine_stretch_under_q_delta_over_h",
        )
        self.assertEqual(
            loaded.observed["mabd_kinematic_feasibility_statuses"],
            ["paper_momentum_requires_affine_stretch_under_q_delta_over_h"],
        )
        self.assertIn("mabd_newton_report_incomplete", loaded.observed["blocking_reasons"])
        self.assertIn(
            "mabd_kinematic_feasibility_blocker_recorded",
            loaded.observed["blocking_reasons"],
        )
        self.assertIn(
            "spinning_box_contact_response_missing",
            loaded.observed["blocking_reasons"],
        )
        self.assertEqual(
            loaded.observed["contact_diagnostic_policy"],
            "evaluated_from_current_mabd_states_not_applied_to_step",
        )
        self.assertEqual(
            loaded.observed["contact_diagnostic_status"],
            "contact_penetration_observed_without_response",
        )
        self.assertGreaterEqual(loaded.observed["max_contact_active_count"], 4)
        self.assertGreater(loaded.observed["max_contact_penetration_m"], 0.0)
        self.assertGreater(loaded.observed["max_contact_normal_force_n"], 0.0)
        self.assertEqual(len(loaded.observed["paper_horizon_results"]), 2)
        self.assertIn("figure_pdf_sha256", loaded.observed)
        self.assertEqual(
            loaded.observed["figure_pdf_sha256"],
            config.paper_horizon.figure_pdf_sha256,
        )
        self.assertIn("figure_text_source", loaded.observed)
        self.assertGreater(loaded.observed["linear_momentum_error"], 0.0)
        self.assertGreater(loaded.observed["angular_momentum_error"], 0.0)
        self.assertGreater(loaded.observed["energy_drift"], 0.0)
        self.assertEqual(loaded.observed["initial_position_m"], [0.0, 0.05, 0.0])
        self.assertEqual(len(loaded.observed["final_position_m"]), 3)

        for entry in loaded.observed["paper_horizon_results"]:
            self.assertIn(entry["time_step_s"], [0.01, 0.001])
            self.assertIn("steps_attempted", entry)
            self.assertIn("steps_completed", entry)
            self.assertIn("first_nonfinite_step", entry)
            self.assertIn("threshold_violations", entry)
            self.assertIn("trajectory_samples", entry)
            self.assertIn("kinematic_feasibility", entry)
            self.assertEqual(
                entry["contact_diagnostic_policy"],
                "evaluated_from_current_mabd_states_not_applied_to_step",
            )
            self.assertGreaterEqual(entry["max_contact_active_count"], 4)
            self.assertGreater(entry["max_contact_penetration_m"], 0.0)
            self.assertGreater(entry["max_contact_normal_force_n"], 0.0)
            feasibility = entry["kinematic_feasibility"]
            self.assertEqual(
                feasibility["status"],
                "paper_momentum_requires_affine_stretch_under_q_delta_over_h",
            )
            self.assertTrue(feasibility["requires_affine_stretch"])
            self.assertEqual(
                feasibility["velocity_update_relation"],
                "qd_next=(q_next-q_n)/h",
            )
            if entry["time_step_s"] == 0.01:
                self.assertAlmostEqual(feasibility["required_speed_to_bound_ratio"], 600.0)
            if entry["time_step_s"] == 0.001:
                self.assertAlmostEqual(feasibility["required_speed_to_bound_ratio"], 60.0)
            self.assertLessEqual(
                len(entry["trajectory_samples"]),
                config.paper_horizon.sample_count,
            )
            self.assertIn("max_affine_orthogonality_error", entry)
            self.assertIn("max_affine_orthogonality_error_step_index", entry)
            self.assertIn("kinetic_energy_initial_j", entry)
            self.assertIn("elastic_energy_initial_j", entry)
            self.assertIn("total_energy_initial_j", entry)
            self.assertIn("max_relative_kinetic_energy_drift", entry)
            self.assertIn("max_relative_total_energy_drift", entry)
            self.assertIn("max_abs_det_minus_one", entry)
            self.assertIn("max_abs_det_minus_one", entry["threshold_violations"])
            self.assertIn(
                "max_relative_total_energy_drift",
                entry["threshold_violations"],
            )
            self.assertGreater(entry["max_affine_orthogonality_error"], 1.0)
            self.assertGreater(entry["max_singular_value"], 1.1)
            self.assertIsNone(entry["first_nonfinite_step"])
            self.assertEqual(entry["steps_completed"], entry["steps_attempted"])
            for sample in entry["trajectory_samples"]:
                self.assertIn("total_energy_j", sample)
                self.assertIn("elastic_energy_j", sample)
                self.assertIn("affine_orthogonality_error", sample)
                self.assertTrue(np.isfinite(sample["total_energy_j"]))


if __name__ == "__main__":
    unittest.main()
