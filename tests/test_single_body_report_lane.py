from __future__ import annotations

import unittest
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np

from mabd_reproduction.reporting import EvidenceStatus, load_claim_report
from mabd_reproduction.single_body_reports import (
    _run_spinning_box_solver_mabd_model_step,
    write_spinning_box_contact_response_report,
    write_spinning_box_decoupled_twist_report,
    write_spinning_box_development_report,
    write_spinning_box_model_plane_constraint_report,
    write_spinning_box_normal_constraint_report,
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

    def test_spinning_box_contact_response_report_records_explicit_force_lane(self) -> None:
        from mabd_reproduction.experiment_configs import load_spinning_box_config

        root = Path(__file__).resolve().parents[1]
        config = load_spinning_box_config(root / "configs/experiments/single_body_spinning_box.yaml")
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "single_body_spinning_box_contact_response.json"
            report = write_spinning_box_contact_response_report(
                path,
                config=config,
                source_commit="test-source",
                vendored_newton_commit="test-newton",
            )
            loaded = load_claim_report(path)

        self.assertEqual(report.scene_id, config.scene_id)
        self.assertEqual(loaded.status, EvidenceStatus.INCOMPLETE)
        self.assertEqual(loaded.baseline_lane, "mabd_newton")
        self.assertEqual(loaded.solver_mode, "mabd_cpu_oracle_contact_response_diagnostic")
        self.assertNotIn("lane_gate_status", loaded.observed)
        self.assertEqual(
            loaded.observed["contact_response_policy"],
            "explicit_current_state_penalty_force_as_external_force_next_step",
        )
        self.assertEqual(
            loaded.observed["contact_response_scope"],
            "diagnostic_only_no_lane_gate",
        )
        self.assertIn("mabd_newton_report_incomplete", loaded.observed["blocking_reasons"])
        self.assertIn(
            "spinning_box_contact_response_not_paper_faithful",
            loaded.observed["blocking_reasons"],
        )
        self.assertIn(
            "spinning_box_comparison_pass_gate_not_enabled",
            loaded.observed["blocking_reasons"],
        )
        self.assertGreaterEqual(
            loaded.observed["response_max_contact_active_count"],
            4,
        )
        self.assertGreater(loaded.observed["response_max_contact_penetration_m"], 0.0)
        self.assertGreater(loaded.observed["response_max_applied_contact_force_norm"], 0.0)
        self.assertGreater(loaded.observed["no_response_max_contact_penetration_m"], 0.0)
        self.assertIn("penetration_delta_vs_no_response_m", loaded.observed)
        self.assertEqual(
            len(loaded.observed["contact_response_results"]),
            len(config.paper_horizon.time_step_grid_s),
        )
        for entry in loaded.observed["contact_response_results"]:
            self.assertIn(entry["time_step_s"], [0.01, 0.001])
            self.assertEqual(
                entry["contact_response_policy"],
                "explicit_current_state_penalty_force_as_external_force_next_step",
            )
            self.assertGreater(entry["max_applied_contact_generalized_force_norm"], 0.0)
            self.assertIn("max_contact_penetration_m", entry)
            self.assertIn("threshold_violations", entry)
            self.assertLessEqual(
                len(entry["trajectory_samples"]),
                config.paper_horizon.sample_count,
            )

    def test_spinning_box_contact_response_step_passes_current_contact_force_to_oracle(
        self,
    ) -> None:
        from mabd_reproduction import single_body_reports
        from mabd_reproduction.experiment_configs import load_spinning_box_config
        from mabd_reproduction.spinning_box_physics import spinning_box_contact_diagnostics

        root = Path(__file__).resolve().parents[1]
        config = load_spinning_box_config(root / "configs/experiments/single_body_spinning_box.yaml")
        penetrating_q = config.initial_q.copy()
        penetrating_q[10] = 0.049
        short_config = replace(
            config,
            initial_q=penetrating_q,
            paper_horizon=replace(config.paper_horizon, duration_s=0.01, sample_count=2),
        )
        expected_contact = spinning_box_contact_diagnostics(
            short_config,
            short_config.initial_q,
            short_config.initial_qd,
        )
        captured_forces: list[np.ndarray] = []

        def fake_solve_cpu_oracle_step(*, q, qd, dt, config):
            self.assertEqual(len(config.external_forces), 1)
            captured_forces.append(config.external_forces[0].copy())
            return SimpleNamespace(q=(q[0].copy(),), qd=(qd[0].copy(),), residual_norm=0.0)

        with patch.object(
            single_body_reports.mabd,
            "solve_cpu_oracle_step",
            side_effect=fake_solve_cpu_oracle_step,
        ):
            result = single_body_reports._run_spinning_box_paper_horizon_step_size(
                config=short_config,
                time_step_s=0.01,
                contact_response_policy=single_body_reports.CONTACT_RESPONSE_POLICY,
            )

        self.assertEqual(len(captured_forces), 1)
        np.testing.assert_allclose(
            captured_forces[0],
            expected_contact.total_generalized_force,
            rtol=0.0,
            atol=1.0e-12,
        )
        self.assertGreater(float(np.linalg.norm(captured_forces[0])), 0.0)
        self.assertGreater(result["max_applied_contact_generalized_force_norm"], 0.0)

    def test_spinning_box_normal_constraint_report_records_active_set_lane(self) -> None:
        from mabd_reproduction.experiment_configs import load_spinning_box_config

        root = Path(__file__).resolve().parents[1]
        config = load_spinning_box_config(root / "configs/experiments/single_body_spinning_box.yaml")
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "single_body_spinning_box_normal_constraint.json"
            report = write_spinning_box_normal_constraint_report(
                path,
                config=config,
                source_commit="test-source",
                vendored_newton_commit="test-newton",
            )
            loaded = load_claim_report(path)

        self.assertEqual(report.scene_id, config.scene_id)
        self.assertEqual(loaded.status, EvidenceStatus.INCOMPLETE)
        self.assertEqual(loaded.baseline_lane, "mabd_newton")
        self.assertEqual(
            loaded.solver_mode,
            "mabd_cpu_oracle_point_plane_normal_constraint_diagnostic",
        )
        self.assertNotIn("lane_gate_status", loaded.observed)
        self.assertEqual(
            loaded.observed["contact_constraint_policy"],
            "free_predict_then_active_point_plane_normal_constraints",
        )
        self.assertEqual(
            loaded.observed["contact_constraint_scope"],
            "diagnostic_only_no_lane_gate",
        )
        self.assertEqual(
            loaded.observed["rank_filter_policy"],
            "increment_map_row_rank_filter",
        )
        self.assertIn("mabd_newton_report_incomplete", loaded.observed["blocking_reasons"])
        self.assertIn(
            "spinning_box_normal_constraint_not_paper_faithful",
            loaded.observed["blocking_reasons"],
        )
        self.assertIn(
            "spinning_box_comparison_pass_gate_not_enabled",
            loaded.observed["blocking_reasons"],
        )
        self.assertGreater(loaded.observed["max_free_predicted_contact_penetration_m"], 0.0)
        self.assertGreaterEqual(loaded.observed["max_requested_plane_constraint_count"], 1)
        self.assertGreaterEqual(loaded.observed["max_accepted_plane_constraint_count"], 1)
        self.assertGreaterEqual(loaded.observed["max_skipped_plane_constraint_count"], 0)
        self.assertTrue(np.isfinite(loaded.observed["normal_constraint_residual_norm"]))
        self.assertEqual(
            len(loaded.observed["normal_constraint_results"]),
            len(config.paper_horizon.time_step_grid_s),
        )
        for entry in loaded.observed["normal_constraint_results"]:
            self.assertIn(entry["time_step_s"], [0.01, 0.001])
            self.assertEqual(
                entry["contact_constraint_policy"],
                "free_predict_then_active_point_plane_normal_constraints",
            )
            self.assertIn("max_free_predicted_contact_penetration_m", entry)
            self.assertIn("max_constrained_contact_penetration_m", entry)
            self.assertIn("max_requested_plane_constraint_count", entry)
            self.assertIn("max_accepted_plane_constraint_count", entry)
            self.assertIn("max_skipped_plane_constraint_count", entry)
            self.assertIn("max_normal_constraint_residual_norm", entry)
            self.assertTrue(np.isfinite(entry["max_normal_constraint_residual_norm"]))
            self.assertLessEqual(
                len(entry["trajectory_samples"]),
                config.paper_horizon.sample_count,
            )

    def test_solver_mabd_model_step_matches_cpu_oracle_plane_constraints(self) -> None:
        from newton.solvers import mabd

        from mabd_reproduction.experiment_configs import load_spinning_box_config
        from mabd_reproduction.single_body_reports import _oracle_body
        from mabd_reproduction.spinning_box_physics import (
            spinning_box_contact_diagnostics,
            spinning_box_cube_corners,
        )

        root = Path(__file__).resolve().parents[1]
        config = load_spinning_box_config(root / "configs/experiments/single_body_spinning_box.yaml")
        penetrating_q = config.initial_q.copy()
        penetrating_q[10] = 0.049
        free_result = mabd.solve_cpu_oracle_step(
            q=[penetrating_q],
            qd=[config.initial_qd],
            dt=0.01,
            config=mabd.MABDCPUOracleConfig(bodies=[_oracle_body(config)]),
        )
        free_contact = spinning_box_contact_diagnostics(
            config,
            free_result.q[0],
            free_result.qd[0],
        )
        constraints = [
            mabd.MABDCPUOraclePlaneConstraint(
                body=0,
                rest_point=corner,
                plane_normal=config.contact_surface["plane_normal"],
                plane_offset=float(config.contact_surface["plane_offset"]),
            )
            for corner, signed_distance in zip(
                spinning_box_cube_corners(config),
                free_contact.corner_signed_distances,
                strict=True,
            )
            if float(signed_distance) < 0.0
        ]
        self.assertGreater(len(constraints), 0)

        oracle_result = mabd.solve_cpu_oracle_step(
            q=[penetrating_q],
            qd=[config.initial_qd],
            dt=0.01,
            config=mabd.MABDCPUOracleConfig(
                bodies=[_oracle_body(config)],
                plane_constraints=constraints,
                topology="dense",
            ),
        )
        model_result = _run_spinning_box_solver_mabd_model_step(
            config=config,
            q=penetrating_q,
            qd=config.initial_qd,
            time_step_s=0.01,
            plane_constraints=constraints,
        )

        np.testing.assert_allclose(model_result.q, oracle_result.q[0], rtol=1.0e-6, atol=1.0e-5)
        np.testing.assert_allclose(model_result.qd, oracle_result.qd[0], rtol=1.0e-6, atol=1.0e-5)
        self.assertEqual(model_result.plane_constraint_requested_count, len(constraints))
        self.assertEqual(
            model_result.plane_constraint_accepted_count,
            int(getattr(oracle_result, "plane_constraint_accepted_count", 0)),
        )
        self.assertEqual(
            model_result.plane_constraint_skipped_count,
            int(getattr(oracle_result, "plane_constraint_skipped_count", 0)),
        )
        self.assertAlmostEqual(
            model_result.constraint_residual_norm,
            float(getattr(oracle_result, "constraint_residual_norm", 0.0)),
            places=8,
        )

    def test_spinning_box_model_plane_constraint_report_records_solver_model_rows(self) -> None:
        from mabd_reproduction.experiment_configs import load_spinning_box_config

        root = Path(__file__).resolve().parents[1]
        config = load_spinning_box_config(root / "configs/experiments/single_body_spinning_box.yaml")
        short_config = replace(
            config,
            paper_horizon=replace(config.paper_horizon, duration_s=0.02, sample_count=3),
        )
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "single_body_spinning_box_model_plane_constraint.json"
            report = write_spinning_box_model_plane_constraint_report(
                path,
                config=short_config,
                source_commit="test-source",
                vendored_newton_commit="test-newton",
            )
            loaded = load_claim_report(path)

        self.assertEqual(report.scene_id, config.scene_id)
        self.assertEqual(loaded.status, EvidenceStatus.INCOMPLETE)
        self.assertEqual(loaded.baseline_lane, "mabd_newton")
        self.assertEqual(loaded.solver_mode, "solver_mabd_model_plane_constraint_diagnostic")
        self.assertEqual(loaded.backend, "cpu_numpy_newton_solver_mabd_model_rows")
        self.assertNotIn("lane_gate_status", loaded.observed)
        self.assertEqual(
            loaded.observed["model_plane_constraint_policy"],
            "solver_mabd_model_rows_free_predict_then_active_plane_constraints",
        )
        self.assertEqual(
            loaded.observed["model_plane_constraint_scope"],
            "diagnostic_only_no_lane_gate",
        )
        self.assertEqual(
            loaded.observed["model_plane_constraint_config_source"],
            "mabd:plane_constraint_custom_rows",
        )
        self.assertEqual(
            loaded.observed["contact_constraint_policy"],
            "free_predict_then_active_point_plane_normal_constraints",
        )
        self.assertEqual(
            loaded.observed["rank_filter_policy"],
            "increment_map_row_rank_filter",
        )
        self.assertEqual(
            len(loaded.observed["model_plane_constraint_results"]),
            len(short_config.paper_horizon.time_step_grid_s),
        )
        self.assertGreater(loaded.observed["max_free_predicted_contact_penetration_m"], 0.0)
        self.assertGreaterEqual(loaded.observed["max_requested_plane_constraint_count"], 1)
        self.assertGreaterEqual(loaded.observed["max_accepted_plane_constraint_count"], 1)
        self.assertGreaterEqual(loaded.observed["max_model_plane_constraint_residual_norm"], 0.0)
        self.assertLess(
            loaded.observed["max_constrained_contact_penetration_m"],
            loaded.observed["max_free_predicted_contact_penetration_m"],
        )
        self.assertTrue(loaded.observed["model_plane_constraint_reduced_free_predicted_penetration"])
        self.assertIn("mabd_newton_report_incomplete", loaded.observed["blocking_reasons"])
        self.assertIn(
            "spinning_box_model_plane_constraint_not_paper_faithful",
            loaded.observed["blocking_reasons"],
        )
        self.assertIn(
            "spinning_box_comparison_pass_gate_not_enabled",
            loaded.observed["blocking_reasons"],
        )
        for entry in loaded.observed["model_plane_constraint_results"]:
            self.assertIn(entry["time_step_s"], [0.01, 0.001])
            self.assertEqual(
                entry["model_plane_constraint_policy"],
                "solver_mabd_model_rows_free_predict_then_active_plane_constraints",
            )
            self.assertEqual(
                entry["model_plane_constraint_config_source"],
                "mabd:plane_constraint_custom_rows",
            )
            self.assertNotEqual(
                entry["contact_diagnostic_status"],
                "contact_penetration_observed_without_response",
            )
            self.assertIn("max_model_plane_constraint_residual_norm", entry)
            self.assertTrue(np.isfinite(entry["max_model_plane_constraint_residual_norm"]))
            self.assertLessEqual(
                len(entry["trajectory_samples"]),
                short_config.paper_horizon.sample_count,
            )

    def test_spinning_box_decoupled_twist_report_records_velocity_semantics_diagnostic(self) -> None:
        from mabd_reproduction.experiment_configs import load_spinning_box_config

        root = Path(__file__).resolve().parents[1]
        config = load_spinning_box_config(root / "configs/experiments/single_body_spinning_box.yaml")
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "single_body_spinning_box_decoupled_twist.json"
            report = write_spinning_box_decoupled_twist_report(
                path,
                config=config,
                source_commit="test-source",
                vendored_newton_commit="test-newton",
            )
            loaded = load_claim_report(path)

        self.assertEqual(report.scene_id, config.scene_id)
        self.assertEqual(loaded.status, EvidenceStatus.INCOMPLETE)
        self.assertEqual(loaded.baseline_lane, "mabd_newton")
        self.assertEqual(
            loaded.solver_mode,
            "decoupled_twist_rigid_reconstruction_diagnostic",
        )
        self.assertNotIn("lane_gate_status", loaded.observed)
        self.assertEqual(
            loaded.observed["velocity_semantics_policy"],
            "decoupled_spatial_twist_with_exponential_rigid_update",
        )
        self.assertEqual(
            loaded.observed["velocity_semantics_scope"],
            "diagnostic_only_no_lane_gate",
        )
        self.assertEqual(
            loaded.observed["blocking_reasons"],
            [
                "mabd_newton_report_incomplete",
                "spinning_box_decoupled_twist_not_paper_faithful",
                "spinning_box_comparison_pass_gate_not_enabled",
                "mabd_kinematic_feasibility_blocker_recorded",
            ],
        )
        self.assertEqual(
            loaded.observed["solver_step_policy"],
            "no_solver_step_rigid_reconstruction_diagnostic",
        )
        self.assertEqual(
            loaded.observed["solver_residual_status"],
            "not_evaluated_no_kkt_solve",
        )
        self.assertEqual(
            loaded.observed["decoupled_twist_status"],
            "decoupled_twist_thresholds_met_no_lane_gate",
        )
        self.assertTrue(loaded.observed["shape_thresholds_met_by_decoupled_twist"])
        self.assertTrue(loaded.observed["energy_thresholds_met_by_decoupled_twist"])
        self.assertEqual(loaded.observed["threshold_violations"], [])
        self.assertGreater(loaded.observed["max_velocity_state_inconsistency_norm"], 0.0)
        self.assertGreater(loaded.observed["max_finite_difference_twist_error"], 0.0)
        self.assertEqual(
            len(loaded.observed["decoupled_twist_results"]),
            len(config.paper_horizon.time_step_grid_s),
        )
        for entry in loaded.observed["decoupled_twist_results"]:
            self.assertIn(entry["time_step_s"], [0.01, 0.001])
            self.assertEqual(entry["threshold_violations"], [])
            self.assertEqual(
                entry["solver_step_policy"],
                "no_solver_step_rigid_reconstruction_diagnostic",
            )
            self.assertEqual(
                entry["solver_residual_status"],
                "not_evaluated_no_kkt_solve",
            )
            self.assertGreater(entry["max_velocity_state_inconsistency_norm"], 0.0)
            self.assertGreater(entry["max_finite_difference_twist_error"], 0.0)
            self.assertEqual(entry["max_contact_penetration_m"], 0.0)
            self.assertLessEqual(
                entry["max_abs_det_minus_one"],
                config.paper_horizon.thresholds["max_abs_det_minus_one"],
            )
            self.assertGreaterEqual(
                entry["min_singular_value"],
                config.paper_horizon.thresholds["min_singular_value"],
            )
            self.assertLessEqual(
                entry["max_singular_value"],
                config.paper_horizon.thresholds["max_singular_value"],
            )
            self.assertLessEqual(
                entry["max_affine_orthogonality_error"],
                config.paper_horizon.thresholds["max_affine_orthogonality_error"],
            )
            self.assertLessEqual(
                entry["max_relative_kinetic_energy_drift"],
                config.paper_horizon.thresholds["max_relative_kinetic_energy_drift"],
            )
            self.assertLessEqual(
                entry["max_relative_total_energy_drift"],
                config.paper_horizon.thresholds["max_relative_total_energy_drift"],
            )
            self.assertTrue(np.isfinite(entry["max_velocity_state_inconsistency_norm"]))
            self.assertTrue(np.isfinite(entry["max_finite_difference_twist_error"]))
            self.assertEqual(
                entry["kinematic_feasibility"]["status"],
                "paper_momentum_requires_affine_stretch_under_q_delta_over_h",
            )
            self.assertLessEqual(
                len(entry["trajectory_samples"]),
                config.paper_horizon.sample_count,
            )

    def test_spinning_box_normal_constraint_skips_rerun_when_free_prediction_is_clear(
        self,
    ) -> None:
        from mabd_reproduction import single_body_reports
        from mabd_reproduction.experiment_configs import load_spinning_box_config

        root = Path(__file__).resolve().parents[1]
        config = load_spinning_box_config(root / "configs/experiments/single_body_spinning_box.yaml")
        short_config = replace(
            config,
            paper_horizon=replace(config.paper_horizon, duration_s=0.01, sample_count=2),
        )
        captured_configs = []

        def fake_solve_cpu_oracle_step(*, q, qd, dt, config):
            captured_configs.append(config)
            return SimpleNamespace(q=(q[0].copy(),), qd=(qd[0].copy(),), residual_norm=0.0)

        with patch.object(
            single_body_reports.mabd,
            "solve_cpu_oracle_step",
            side_effect=fake_solve_cpu_oracle_step,
        ):
            result = single_body_reports._run_spinning_box_paper_horizon_step_size(
                config=short_config,
                time_step_s=0.01,
                normal_constraint_policy=single_body_reports.NORMAL_CONSTRAINT_POLICY,
            )

        self.assertEqual(len(captured_configs), 1)
        self.assertEqual(result["max_requested_plane_constraint_count"], 0)
        self.assertEqual(result["max_accepted_plane_constraint_count"], 0)

    def test_spinning_box_normal_constraint_rerun_receives_active_plane_rows(
        self,
    ) -> None:
        from mabd_reproduction import single_body_reports
        from mabd_reproduction.experiment_configs import load_spinning_box_config

        root = Path(__file__).resolve().parents[1]
        config = load_spinning_box_config(root / "configs/experiments/single_body_spinning_box.yaml")
        short_config = replace(
            config,
            paper_horizon=replace(config.paper_horizon, duration_s=0.01, sample_count=2),
        )
        penetrating_q = short_config.initial_q.copy()
        penetrating_q[10] = 0.049
        captured_plane_constraints = []

        def fake_solve_cpu_oracle_step(*, q, qd, dt, config):
            if not captured_plane_constraints:
                captured_plane_constraints.append(None)
                return SimpleNamespace(
                    q=(penetrating_q.copy(),),
                    qd=(qd[0].copy(),),
                    residual_norm=0.0,
                )
            captured_plane_constraints.append(tuple(config.plane_constraints))
            return SimpleNamespace(
                q=(q[0].copy(),),
                qd=(qd[0].copy(),),
                residual_norm=0.0,
                constraint_residual_norm=0.0,
                plane_constraint_requested_count=len(config.plane_constraints),
                plane_constraint_accepted_count=len(config.plane_constraints),
                plane_constraint_skipped_count=0,
            )

        with patch.object(
            single_body_reports.mabd,
            "solve_cpu_oracle_step",
            side_effect=fake_solve_cpu_oracle_step,
        ):
            result = single_body_reports._run_spinning_box_paper_horizon_step_size(
                config=short_config,
                time_step_s=0.01,
                normal_constraint_policy=single_body_reports.NORMAL_CONSTRAINT_POLICY,
            )

        self.assertEqual(len(captured_plane_constraints), 2)
        plane_constraints = captured_plane_constraints[1]
        self.assertIsNotNone(plane_constraints)
        self.assertGreaterEqual(len(plane_constraints), 4)
        for constraint in plane_constraints:
            self.assertIsInstance(constraint, single_body_reports.mabd.MABDCPUOraclePlaneConstraint)
            np.testing.assert_allclose(
                constraint.plane_normal,
                short_config.contact_surface["plane_normal"],
            )
            self.assertEqual(constraint.plane_offset, short_config.contact_surface["plane_offset"])
        self.assertGreaterEqual(result["max_requested_plane_constraint_count"], 4)


if __name__ == "__main__":
    unittest.main()
