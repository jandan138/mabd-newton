from __future__ import annotations

import unittest
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import yaml

from mabd_reproduction.experiment_configs import (
    ExperimentRunConfigError,
    load_heavy_top_config,
    load_physical_pendulum_config,
    load_spinning_box_config,
    load_t_handle_config,
    validate_heavy_top_config_against_matrix,
    validate_physical_pendulum_config_against_matrix,
    validate_spinning_box_config_against_matrix,
    validate_t_handle_config_against_matrix,
)
from mabd_reproduction.experiment_contracts import load_experiment_matrix
from mabd_reproduction.reporting import EvidenceStatus


ROOT = Path(__file__).resolve().parents[1]
HEAVY_TOP_CONFIG_PATH = ROOT / "configs/experiments/single_body_heavy_top.yaml"
PHYSICAL_PENDULUM_CONFIG_PATH = ROOT / "configs/experiments/single_body_physical_pendulum.yaml"
T_HANDLE_CONFIG_PATH = ROOT / "configs/experiments/single_body_t_handle.yaml"


class ExperimentRunConfigTests(unittest.TestCase):
    def _config_mapping(self) -> dict:
        return yaml.safe_load((ROOT / "configs/experiments/single_body_spinning_box.yaml").read_text())

    def _write_config(self, tmpdir: str, mapping: dict) -> Path:
        path = Path(tmpdir) / "single_body_spinning_box.yaml"
        path.write_text(yaml.safe_dump(mapping), encoding="utf-8")
        return path

    def _t_handle_mapping_with_comparison(self) -> dict:
        source = yaml.safe_load(T_HANDLE_CONFIG_PATH.read_text(encoding="utf-8"))
        source.setdefault(
            "comparison",
            {
                "output_report": "reports/experiment_matrix/single_body_t_handle_comparison.json",
                "required_lanes": ["mabd_newton", "rbd_rk4_reference"],
                "required_metrics": [
                    "flip_timing_error",
                    "intermediate_axis_angular_velocity_waveform",
                    "energy_loss",
                ],
                "thresholds": {"max_sample_time_delta_s": 1.0e-12},
            },
        )
        return source

    def test_spinning_box_config_is_machine_checkable(self) -> None:
        from newton.solvers import mabd

        from mabd_reproduction.spinning_box_physics import (
            abd_generalized_velocity_from_paper_momenta,
            spinning_box_mabd_mass_diagonal,
            spinning_box_physical_properties,
        )

        config = load_spinning_box_config(ROOT / "configs/experiments/single_body_spinning_box.yaml")
        properties = spinning_box_physical_properties(config)
        expected_mass_diagonal = spinning_box_mabd_mass_diagonal(config)

        self.assertEqual(config.schema_version, 1)
        self.assertEqual(config.claim_id, "experiment.single_body.spinning_box")
        self.assertEqual(config.scene_id, "single_body_spinning_box")
        self.assertEqual(config.asset_ids, ("primitive_cube",))
        self.assertEqual(config.baseline_lane, "mabd_newton")
        self.assertEqual(config.report_status, EvidenceStatus.INCOMPLETE)
        self.assertEqual(config.required_missing_lanes, ())
        self.assertIn("mabd_newton", config.failure_reason)
        self.assertIn("comparison", config.failure_reason)
        self.assertEqual(config.time_step_s, 0.01)
        self.assertEqual(config.step_count, 4)
        self.assertEqual(config.initial_qd.shape, (12,))
        self.assertEqual(config.mass_diagonal.shape, (12,))
        np.testing.assert_allclose(
            expected_mass_diagonal,
            [1.0 / 1200.0] * 9 + [1.0, 1.0, 1.0],
            rtol=0.0,
            atol=1.0e-15,
        )
        np.testing.assert_allclose(config.mass_diagonal, expected_mass_diagonal, atol=1.0e-15)
        self.assertAlmostEqual(
            float(0.5 * config.initial_qd @ np.diag(config.mass_diagonal) @ config.initial_qd),
            3005000.0,
        )
        self.assertIn("energy_drift", config.thresholds)
        self.assertIn("generalized_momentum_delta_norm", config.thresholds)
        self.assertEqual(config.paper_horizon.duration_s, 10.0)
        self.assertEqual(config.paper_horizon.time_step_grid_s, (0.01, 0.001))
        self.assertEqual(config.paper_horizon.sample_count, 11)
        self.assertEqual(
            config.paper_horizon.output_report,
            "reports/experiment_matrix/single_body_spinning_box_paper_horizon.json",
        )
        self.assertEqual(
            config.paper_horizon.contact_response_output_report,
            "reports/experiment_matrix/single_body_spinning_box_contact_response.json",
        )
        self.assertEqual(
            config.paper_horizon.figure_pdf_sha256,
            "7669b062348324a3b0090cc9f44930655c83233a87f63389db9198b88f95ae80",
        )
        self.assertEqual(
            config.paper_horizon.figure_text_source,
            "pdftotext /tmp/mabd-paper/source/images/cube/roll_cube.pdf -",
        )
        for key in (
            "max_linear_momentum_error",
            "max_angular_momentum_error",
            "max_relative_kinetic_energy_drift",
            "max_relative_total_energy_drift",
            "max_abs_det_minus_one",
            "min_singular_value",
            "max_singular_value",
            "max_affine_orthogonality_error",
            "max_residual_norm",
        ):
            self.assertIn(key, config.paper_horizon.thresholds)
        self.assertEqual(config.contact_surface["type"], "plane")
        self.assertEqual(config.contact_surface["plane_normal"], (0.0, 1.0, 0.0))
        self.assertEqual(config.contact_surface["plane_offset"], 0.0)
        self.assertGreater(config.contact_surface["stiffness"], 0.0)
        self.assertGreaterEqual(config.contact_surface["damping"], 0.0)
        self.assertAlmostEqual(float(config.initial_q[10]), 0.05)
        np.testing.assert_allclose(
            config.initial_qd,
            abd_generalized_velocity_from_paper_momenta(config),
            atol=1.0e-12,
        )
        np.testing.assert_allclose(
            mabd.twist_map_G(np.eye(3)) @ config.initial_qd,
            [0.0, 60000.0, 0.0, 100.0, 0.0, 0.0],
            atol=1.0e-12,
        )
        np.testing.assert_allclose(properties.linear_momentum_kg_m_s, [100.0, 0.0, 0.0])
        np.testing.assert_allclose(properties.angular_momentum_kg_m2_s, [0.0, 100.0, 0.0])
        self.assertIn("linear_momentum_error", config.thresholds)
        self.assertIn("angular_momentum_error", config.thresholds)

    def test_physical_pendulum_config_is_machine_checkable(self) -> None:
        config = load_physical_pendulum_config(PHYSICAL_PENDULUM_CONFIG_PATH)

        self.assertEqual(config.schema_version, 1)
        self.assertEqual(config.claim_id, "experiment.single_body.physical_pendulum")
        self.assertEqual(config.scene_id, "single_body_physical_pendulum")
        self.assertEqual(config.asset_ids, ("physical_pendulum_procedural",))
        self.assertEqual(config.baseline_lane, "analytic_reference")
        self.assertEqual(config.required_missing_lanes, ("mabd_newton",))
        self.assertEqual(config.report_status, EvidenceStatus.INCOMPLETE)
        self.assertEqual(config.reference.sample_count, 9)
        self.assertEqual(config.reference.initial_angle_rad, 0.0)
        self.assertAlmostEqual(config.reference.release_angle_rad, np.pi / 2.0)
        self.assertAlmostEqual(config.reference.kappa, np.sqrt(0.5))
        self.assertAlmostEqual(config.reference.omega_lin_rad_s, np.sqrt(9.81))
        self.assertEqual(config.mabd_development.time_step_s, 0.01)
        self.assertEqual(config.mabd_development.step_count, 16)
        self.assertEqual(config.mabd_development.sample_count, 5)
        self.assertEqual(config.mabd_development.rest_points_m.shape, (4, 3))
        self.assertEqual(config.mabd_development.masses_kg.shape, (4,))
        np.testing.assert_allclose(config.mabd_development.pivot_rest_point_m, [0.0, 0.0, 0.0])
        np.testing.assert_allclose(config.mabd_development.pivot_world_point_m, [0.0, 0.0, 0.0])
        np.testing.assert_allclose(config.mabd_development.angle_probe_rest_point_m, [1.0, 0.0, 0.0])
        np.testing.assert_allclose(config.mabd_development.gravity_m_s2, [0.0, -9.81, 0.0])
        self.assertEqual(
            config.mabd_development.output_report,
            "reports/experiment_matrix/single_body_physical_pendulum_mabd_development.json",
        )
        self.assertIn("max_pivot_residual_m", config.mabd_development.thresholds)
        self.assertIn("max_abs_angle_error_rad", config.mabd_development.thresholds)
        self.assertEqual(
            config.mabd_newton.output_report,
            "reports/experiment_matrix/single_body_physical_pendulum_mabd_newton.json",
        )
        self.assertEqual(config.mabd_newton.rotation_mode, "polar")
        self.assertIn("max_abs_angle_error_rad", config.mabd_newton.thresholds)
        self.assertIn("max_constraint_residual_norm", config.mabd_newton.thresholds)
        self.assertIn("max_phase_drift_rad", config.mabd_newton.thresholds)
        self.assertIn("max_pivot_residual_m", config.mabd_newton.thresholds)
        self.assertIn("max_world_anchor_reaction_magnitude_n", config.mabd_newton.thresholds)
        self.assertEqual(config.rbd_baseline.time_step_s, 0.01)
        self.assertEqual(config.rbd_baseline.step_count, 16)
        self.assertEqual(config.rbd_baseline.sample_count, 5)
        self.assertEqual(config.rbd_baseline.length_m, 1.0)
        self.assertEqual(config.rbd_baseline.mass_kg, 1.0)
        np.testing.assert_allclose(config.rbd_baseline.gravity_m_s2, [0.0, -9.81, 0.0])
        self.assertEqual(config.rbd_baseline.initial_angle_rad, 0.0)
        self.assertEqual(config.rbd_baseline.initial_angular_velocity_rad_s, 0.0)
        self.assertEqual(config.rbd_baseline.newton_iteration_limit, 12)
        self.assertEqual(config.rbd_baseline.newton_residual_tolerance, 1.0e-12)
        self.assertEqual(
            config.rbd_baseline.output_report,
            "reports/experiment_matrix/single_body_physical_pendulum_rbd_baseline.json",
        )
        self.assertIn("max_abs_angle_error_rad", config.rbd_baseline.thresholds)
        self.assertIn("max_implicit_residual", config.rbd_baseline.thresholds)
        self.assertIn("max_length_constraint_error_m", config.rbd_baseline.thresholds)
        self.assertIn("max_phase_drift_rad", config.rbd_baseline.thresholds)
        self.assertEqual(
            config.comparison.output_report,
            "reports/experiment_matrix/single_body_physical_pendulum_comparison.json",
        )
        self.assertEqual(
            config.comparison.required_lanes,
            ("mabd_newton", "analytic_reference", "rbd_implicit_baseline"),
        )
        self.assertEqual(
            config.comparison.diagnostic_lanes,
            ("physical_pendulum_mabd_development_diagnostic",),
        )
        self.assertEqual(
            config.comparison.required_metrics,
            ("pendulum_angle_error", "joint_force_error", "phase_drift"),
        )
        self.assertIn("max_mabd_rbd_abs_angle_delta_rad", config.comparison.thresholds)
        self.assertEqual(
            config.output_report,
            "reports/experiment_matrix/single_body_physical_pendulum_analytic_reference.json",
        )
        self.assertIn("pendulum_geometry_unknown", config.failure_reason)
        self.assertIn("mabd_newton", config.failure_reason)
        self.assertNotIn("rbd_implicit_baseline", config.failure_reason)

    def test_physical_pendulum_config_matches_experiment_matrix(self) -> None:
        config = load_physical_pendulum_config(PHYSICAL_PENDULUM_CONFIG_PATH)
        matrix = load_experiment_matrix(ROOT / "configs/experiments/paper_experiment_matrix.yaml")

        validate_physical_pendulum_config_against_matrix(config, matrix)

    def test_t_handle_config_is_machine_checkable(self) -> None:
        config = load_t_handle_config(T_HANDLE_CONFIG_PATH)

        self.assertEqual(config.schema_version, 1)
        self.assertEqual(config.claim_id, "experiment.single_body.t_handle")
        self.assertEqual(config.scene_id, "single_body_t_handle")
        self.assertEqual(config.source_lines, ("/tmp/mabd-paper/source/sections/experiment.tex:57-75",))
        self.assertEqual(config.asset_ids, ("t_handle_procedural",))
        self.assertEqual(config.baseline_lane, "rbd_rk4_reference")
        self.assertEqual(config.required_missing_lanes, ())
        self.assertEqual(config.report_status, EvidenceStatus.INCOMPLETE)
        self.assertEqual(config.reference.time_step_s, 1.0e-4)
        self.assertEqual(config.reference.duration_s, 4.0)
        self.assertEqual(config.reference.sample_count, 9)
        self.assertEqual(config.reference.intermediate_axis_index, 1)
        np.testing.assert_allclose(config.reference.principal_inertia_kg_m2, [1.0, 2.0, 3.0])
        np.testing.assert_allclose(config.reference.initial_angular_velocity_rad_s, [0.03, 3.0, 0.0])
        np.testing.assert_allclose(config.reference.gravity_m_s2, [0.0, 0.0, 0.0])
        self.assertEqual(
            config.reference.figure_pdf_sha256,
            "5ae6464fd7e7e6fd471ad56e67cdbead6014736cb731a232ce29d80630a72c1c",
        )
        self.assertEqual(
            config.reference.figure_text_source,
            "pdftotext /tmp/mabd-paper/source/images/T-handle/T-handle.pdf -",
        )
        self.assertEqual(
            config.reference.output_report,
            "reports/experiment_matrix/single_body_t_handle_rk4_reference.json",
        )
        self.assertIn("max_relative_energy_drift", config.reference.thresholds)
        self.assertIn("max_angular_momentum_norm_drift", config.reference.thresholds)
        self.assertIn("min_intermediate_axis_sign_flips", config.reference.thresholds)
        self.assertEqual(
            config.mabd_newton.output_report,
            "reports/experiment_matrix/single_body_t_handle_mabd_newton.json",
        )
        self.assertEqual(config.mabd_newton.time_step_s, 0.001)
        self.assertEqual(config.mabd_newton.step_count, 4000)
        self.assertEqual(config.mabd_newton.sample_count, config.reference.sample_count)
        self.assertEqual(config.mabd_newton.rotation_mode, "polar")
        self.assertEqual(config.mabd_newton.rest_points_m.shape, (4, 3))
        self.assertEqual(config.mabd_newton.point_masses_kg.shape, (4,))
        self.assertAlmostEqual(
            config.mabd_newton.step_count * config.mabd_newton.time_step_s,
            config.reference.duration_s,
        )
        np.testing.assert_allclose(
            config.mabd_newton.initial_angular_velocity_rad_s,
            config.reference.initial_angular_velocity_rad_s,
        )
        np.testing.assert_allclose(config.mabd_newton.gravity_m_s2, [0.0, 0.0, 0.0])
        self.assertIn("max_affine_shape_spread_m", config.mabd_newton.thresholds)
        self.assertIn("max_proxy_inertia_relative_error", config.mabd_newton.thresholds)
        self.assertEqual(
            config.comparison.output_report,
            "reports/experiment_matrix/single_body_t_handle_comparison.json",
        )
        self.assertEqual(
            config.figure_curves.output_report,
            "reports/experiment_matrix/single_body_t_handle_figure_curves.json",
        )
        self.assertEqual(config.comparison.required_lanes, ("mabd_newton", "rbd_rk4_reference"))
        self.assertEqual(
            config.comparison.required_metrics,
            (
                "flip_timing_error",
                "intermediate_axis_angular_velocity_waveform",
                "energy_loss",
            ),
        )
        self.assertIn("max_sample_time_delta_s", config.comparison.thresholds)
        self.assertIn("exact_t_handle_geometry_unknown", config.failure_reason)
        self.assertIn("raw_t_handle_reference_curve_data_missing", config.failure_reason)
        self.assertIn("mabd_newton_report_incomplete", config.failure_reason)
        self.assertIn("t_handle_comparison_report_incomplete", config.failure_reason)
        self.assertNotIn("mabd_newton_report_missing", config.failure_reason)
        self.assertNotIn("t_handle_comparison_report_missing", config.failure_reason)

    def test_t_handle_config_matches_experiment_matrix_without_overclaiming(self) -> None:
        config = load_t_handle_config(T_HANDLE_CONFIG_PATH)
        matrix = load_experiment_matrix(ROOT / "configs/experiments/paper_experiment_matrix.yaml")

        validate_t_handle_config_against_matrix(config, matrix)
        t_handle_entry = next(
            entry for entry in matrix.experiments if entry.claim_id == "experiment.single_body.t_handle"
        )
        self.assertIn("mabd_newton_report_incomplete", t_handle_entry.blocking_reasons)
        self.assertNotIn("mabd_newton_report_missing", t_handle_entry.blocking_reasons)
        self.assertIn("t_handle_comparison_report_incomplete", t_handle_entry.blocking_reasons)
        self.assertNotIn("t_handle_comparison_report_missing", t_handle_entry.blocking_reasons)

    def test_t_handle_config_rejects_passed_status(self) -> None:
        source = yaml.safe_load(T_HANDLE_CONFIG_PATH.read_text(encoding="utf-8"))
        source["report"]["status"] = "passed"
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "single_body_t_handle.yaml"
            path.write_text(yaml.safe_dump(source), encoding="utf-8")

            with self.assertRaisesRegex(ExperimentRunConfigError, "passed experiment configs"):
                load_t_handle_config(path)

    def test_t_handle_config_rejects_nonpositive_inertia(self) -> None:
        source = yaml.safe_load(T_HANDLE_CONFIG_PATH.read_text(encoding="utf-8"))
        source["reference"]["principal_inertia_kg_m2"][1] = 0.0
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "single_body_t_handle.yaml"
            path.write_text(yaml.safe_dump(source), encoding="utf-8")

            with self.assertRaisesRegex(ExperimentRunConfigError, "principal_inertia_kg_m2"):
                load_t_handle_config(path)

    def test_t_handle_config_rejects_mabd_sample_grid_mismatch(self) -> None:
        source = yaml.safe_load(T_HANDLE_CONFIG_PATH.read_text(encoding="utf-8"))
        source["mabd_newton"]["sample_count"] = 8
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "single_body_t_handle.yaml"
            path.write_text(yaml.safe_dump(source), encoding="utf-8")

            with self.assertRaisesRegex(ExperimentRunConfigError, "mabd_newton.sample_count"):
                load_t_handle_config(path)

    def test_t_handle_config_rejects_mabd_nonzero_gravity(self) -> None:
        source = yaml.safe_load(T_HANDLE_CONFIG_PATH.read_text(encoding="utf-8"))
        source["mabd_newton"]["gravity_m_s2"] = [0.0, -9.81, 0.0]
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "single_body_t_handle.yaml"
            path.write_text(yaml.safe_dump(source), encoding="utf-8")

            with self.assertRaisesRegex(ExperimentRunConfigError, "mabd_newton.gravity_m_s2"):
                load_t_handle_config(path)

    def test_t_handle_config_rejects_mabd_reference_report_overlap(self) -> None:
        source = yaml.safe_load(T_HANDLE_CONFIG_PATH.read_text(encoding="utf-8"))
        source["mabd_newton"]["output_report"] = source["reference"]["output_report"]
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "single_body_t_handle.yaml"
            path.write_text(yaml.safe_dump(source), encoding="utf-8")

            config = load_t_handle_config(path)
            matrix = load_experiment_matrix(ROOT / "configs/experiments/paper_experiment_matrix.yaml")
            with self.assertRaisesRegex(ExperimentRunConfigError, "mabd_newton.output_report"):
                validate_t_handle_config_against_matrix(config, matrix)

    def test_t_handle_config_rejects_nonpositive_mabd_point_mass(self) -> None:
        source = yaml.safe_load(T_HANDLE_CONFIG_PATH.read_text(encoding="utf-8"))
        source["mabd_newton"]["point_masses_kg"][0] = 0.0
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "single_body_t_handle.yaml"
            path.write_text(yaml.safe_dump(source), encoding="utf-8")

            with self.assertRaisesRegex(ExperimentRunConfigError, "point_masses_kg"):
                load_t_handle_config(path)

    def test_t_handle_config_rejects_zero_mabd_initial_angular_velocity(self) -> None:
        source = yaml.safe_load(T_HANDLE_CONFIG_PATH.read_text(encoding="utf-8"))
        source["reference"]["initial_angular_velocity_rad_s"] = [0.0, 0.0, 0.0]
        source["mabd_newton"]["initial_angular_velocity_rad_s"] = [0.0, 0.0, 0.0]
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "single_body_t_handle.yaml"
            path.write_text(yaml.safe_dump(source), encoding="utf-8")

            with self.assertRaisesRegex(
                ExperimentRunConfigError,
                "mabd_newton.initial_angular_velocity_rad_s",
            ):
                load_t_handle_config(path)

    def test_t_handle_config_rejects_degenerate_mabd_rest_points(self) -> None:
        source = yaml.safe_load(T_HANDLE_CONFIG_PATH.read_text(encoding="utf-8"))
        source["mabd_newton"]["rest_points_m"][3] = source["mabd_newton"]["rest_points_m"][2]
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "single_body_t_handle.yaml"
            path.write_text(yaml.safe_dump(source), encoding="utf-8")

            with self.assertRaisesRegex(ExperimentRunConfigError, "mabd_newton.rest_points_m"):
                load_t_handle_config(path)

    def test_t_handle_config_rejects_bad_comparison_lanes(self) -> None:
        source = self._t_handle_mapping_with_comparison()
        source["comparison"]["required_lanes"] = ["mabd_newton"]
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "single_body_t_handle.yaml"
            path.write_text(yaml.safe_dump(source), encoding="utf-8")

            with self.assertRaisesRegex(ExperimentRunConfigError, "comparison.required_lanes"):
                load_t_handle_config(path)

    def test_t_handle_config_rejects_bad_comparison_metrics(self) -> None:
        source = self._t_handle_mapping_with_comparison()
        source["comparison"]["required_metrics"] = ["energy_loss"]
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "single_body_t_handle.yaml"
            path.write_text(yaml.safe_dump(source), encoding="utf-8")

            with self.assertRaisesRegex(ExperimentRunConfigError, "comparison.required_metrics"):
                load_t_handle_config(path)

    def test_t_handle_config_rejects_bad_comparison_thresholds(self) -> None:
        source = self._t_handle_mapping_with_comparison()
        source["comparison"]["thresholds"] = {}
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "single_body_t_handle.yaml"
            path.write_text(yaml.safe_dump(source), encoding="utf-8")

            with self.assertRaisesRegex(ExperimentRunConfigError, "comparison.thresholds"):
                load_t_handle_config(path)

    def test_t_handle_config_rejects_negative_comparison_time_threshold(self) -> None:
        source = self._t_handle_mapping_with_comparison()
        source["comparison"]["thresholds"]["max_sample_time_delta_s"] = -1.0
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "single_body_t_handle.yaml"
            path.write_text(yaml.safe_dump(source), encoding="utf-8")

            with self.assertRaisesRegex(ExperimentRunConfigError, "max_sample_time_delta_s"):
                load_t_handle_config(path)

    def test_t_handle_config_rejects_comparison_report_overlap(self) -> None:
        source = self._t_handle_mapping_with_comparison()
        source["comparison"]["output_report"] = source["mabd_newton"]["output_report"]
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "single_body_t_handle.yaml"
            path.write_text(yaml.safe_dump(source), encoding="utf-8")

            config = load_t_handle_config(path)
            matrix = load_experiment_matrix(ROOT / "configs/experiments/paper_experiment_matrix.yaml")
            with self.assertRaisesRegex(ExperimentRunConfigError, "comparison.output_report"):
                validate_t_handle_config_against_matrix(config, matrix)

    def test_t_handle_config_rejects_figure_hash_drift(self) -> None:
        config = load_t_handle_config(T_HANDLE_CONFIG_PATH)
        matrix = load_experiment_matrix(ROOT / "configs/experiments/paper_experiment_matrix.yaml")
        drifted = replace(
            config,
            reference=replace(config.reference, figure_pdf_sha256="0" * 64),
        )

        with self.assertRaisesRegex(ExperimentRunConfigError, "figure_pdf_sha256"):
            validate_t_handle_config_against_matrix(drifted, matrix)

    def test_heavy_top_config_is_machine_checkable(self) -> None:
        config = load_heavy_top_config(HEAVY_TOP_CONFIG_PATH)

        self.assertEqual(config.schema_version, 1)
        self.assertEqual(config.claim_id, "experiment.single_body.heavy_top")
        self.assertEqual(config.scene_id, "single_body_heavy_top")
        self.assertEqual(config.source_lines, ("/tmp/mabd-paper/source/sections/experiment.tex:65-75",))
        self.assertEqual(config.asset_ids, ("heavy_top_procedural",))
        self.assertEqual(config.baseline_lane, "rbd_rk4_reference")
        self.assertEqual(config.required_missing_lanes, ())
        self.assertEqual(config.report_status, EvidenceStatus.INCOMPLETE)
        self.assertEqual(config.reference.time_step_s, 1.0e-4)
        self.assertEqual(config.reference.duration_s, 10.0)
        self.assertEqual(config.reference.sample_count, 11)
        self.assertEqual(config.reference.initial_tilt_deg, 5.0)
        self.assertEqual(config.reference.initial_spin_rad_s, 10.0)
        np.testing.assert_allclose(config.reference.principal_inertia_kg_m2, [0.18, 0.205, 0.05])
        self.assertEqual(config.reference.mass_kg, 1.0)
        np.testing.assert_allclose(config.reference.pivot_to_com_m, [0.0, 0.0, 0.25])
        np.testing.assert_allclose(config.reference.gravity_m_s2, [0.0, -9.81, 0.0])
        self.assertEqual(
            config.reference.figure_pdf_sha256,
            "c8f5e206415b9feb3578ee32aa3b7284e2695bdd84eeb0200f3b4aa01cf3422d",
        )
        self.assertEqual(
            config.reference.figure_text_source,
            "pdftotext /tmp/mabd-paper/source/images/spinning_top/spinning_top.pdf -",
        )
        self.assertEqual(
            config.reference.output_report,
            "reports/experiment_matrix/single_body_heavy_top_rk4_reference.json",
        )
        self.assertIn("max_relative_energy_drift", config.reference.thresholds)
        self.assertIn("min_nutation_angle_range_deg", config.reference.thresholds)
        self.assertIn("min_abs_precession_velocity_rad_s", config.reference.thresholds)
        self.assertIn("exact_heavy_top_inertia_unknown", config.failure_reason)
        self.assertIn("exact_heavy_top_geometry_unknown", config.failure_reason)
        self.assertIn("raw_heavy_top_reference_curve_data_missing", config.failure_reason)
        self.assertIn("mabd_newton_report_incomplete", config.failure_reason)
        self.assertEqual(config.mabd_newton.rotation_mode, "polar")
        self.assertEqual(
            config.mabd_newton.output_report,
            "reports/experiment_matrix/single_body_heavy_top_mabd_newton.json",
        )
        self.assertEqual(config.mabd_newton.sample_count, 6)
        self.assertEqual(config.mabd_newton.step_count, 250)
        self.assertEqual(config.mabd_newton.rest_points_m.shape, (4, 3))
        self.assertEqual(config.mabd_newton.point_masses_kg.shape, (4,))
        self.assertIn("max_pivot_residual_m", config.mabd_newton.thresholds)
        self.assertIn("max_constraint_residual_norm", config.mabd_newton.thresholds)
        self.assertIn("min_nutation_angle_range_deg", config.mabd_newton.thresholds)
        self.assertEqual(config.mabd_paper_horizon.rotation_mode, "polar")
        self.assertEqual(
            config.mabd_paper_horizon.output_report,
            "reports/experiment_matrix/single_body_heavy_top_mabd_paper_horizon.json",
        )
        self.assertEqual(config.mabd_paper_horizon.sample_count, config.reference.sample_count)
        self.assertEqual(config.mabd_paper_horizon.step_count, 10000)
        self.assertEqual(config.mabd_paper_horizon.time_step_s, 0.001)
        self.assertAlmostEqual(
            config.mabd_paper_horizon.step_count * config.mabd_paper_horizon.time_step_s,
            config.reference.duration_s,
        )
        np.testing.assert_allclose(
            config.mabd_paper_horizon.rest_points_m,
            config.mabd_newton.rest_points_m,
        )
        np.testing.assert_allclose(
            config.mabd_paper_horizon.point_masses_kg,
            config.mabd_newton.point_masses_kg,
        )
        np.testing.assert_allclose(
            config.mabd_paper_horizon.pivot_rest_point_m,
            config.mabd_newton.pivot_rest_point_m,
        )
        np.testing.assert_allclose(
            config.mabd_paper_horizon.pivot_world_point_m,
            config.mabd_newton.pivot_world_point_m,
        )
        np.testing.assert_allclose(
            config.mabd_paper_horizon.angle_probe_rest_point_m,
            config.mabd_newton.angle_probe_rest_point_m,
        )
        np.testing.assert_allclose(
            config.mabd_paper_horizon.gravity_m_s2,
            config.reference.gravity_m_s2,
        )
        self.assertEqual(
            config.mabd_paper_horizon.thresholds,
            config.mabd_newton.thresholds,
        )
        self.assertEqual(
            config.comparison.output_report,
            "reports/experiment_matrix/single_body_heavy_top_comparison.json",
        )
        self.assertEqual(config.comparison.required_lanes, ("mabd_newton", "rbd_rk4_reference"))
        self.assertEqual(
            config.comparison.required_metrics,
            ("precession_velocity_error", "nutation_angle_error", "energy_drift"),
        )
        self.assertIn("max_sample_time_delta_s", config.comparison.thresholds)

    def test_heavy_top_config_matches_experiment_matrix_without_overclaiming(self) -> None:
        config = load_heavy_top_config(HEAVY_TOP_CONFIG_PATH)
        matrix = load_experiment_matrix(ROOT / "configs/experiments/paper_experiment_matrix.yaml")

        validate_heavy_top_config_against_matrix(config, matrix)

    def test_heavy_top_config_rejects_missing_mabd_incomplete_blocker(self) -> None:
        config = load_heavy_top_config(HEAVY_TOP_CONFIG_PATH)
        matrix = load_experiment_matrix(ROOT / "configs/experiments/paper_experiment_matrix.yaml")
        entry = next(item for item in matrix.experiments if item.claim_id == config.claim_id)
        drifted_entry = replace(
            entry,
            blocking_reasons=tuple(
                blocker
                for blocker in entry.blocking_reasons
                if blocker != "mabd_newton_report_incomplete"
            ),
        )
        drifted_matrix = replace(
            matrix,
            experiments=tuple(
                drifted_entry if item.claim_id == config.claim_id else item
                for item in matrix.experiments
            ),
        )

        with self.assertRaisesRegex(ExperimentRunConfigError, "mabd_newton_report_incomplete"):
            validate_heavy_top_config_against_matrix(config, drifted_matrix)

    def test_heavy_top_config_rejects_bad_comparison_lanes(self) -> None:
        source = yaml.safe_load(HEAVY_TOP_CONFIG_PATH.read_text(encoding="utf-8"))
        source["comparison"]["required_lanes"] = ["mabd_newton"]
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "single_body_heavy_top.yaml"
            path.write_text(yaml.safe_dump(source), encoding="utf-8")

            with self.assertRaisesRegex(ExperimentRunConfigError, "comparison.required_lanes"):
                load_heavy_top_config(path)

    def test_heavy_top_config_rejects_bad_comparison_metrics(self) -> None:
        source = yaml.safe_load(HEAVY_TOP_CONFIG_PATH.read_text(encoding="utf-8"))
        source["comparison"]["required_metrics"] = ["nutation_angle_error"]
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "single_body_heavy_top.yaml"
            path.write_text(yaml.safe_dump(source), encoding="utf-8")

            with self.assertRaisesRegex(ExperimentRunConfigError, "comparison.required_metrics"):
                load_heavy_top_config(path)

    def test_heavy_top_config_rejects_empty_comparison_thresholds(self) -> None:
        source = yaml.safe_load(HEAVY_TOP_CONFIG_PATH.read_text(encoding="utf-8"))
        source["comparison"]["thresholds"] = {}
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "single_body_heavy_top.yaml"
            path.write_text(yaml.safe_dump(source), encoding="utf-8")

            with self.assertRaisesRegex(ExperimentRunConfigError, "comparison.thresholds"):
                load_heavy_top_config(path)

    def test_heavy_top_config_rejects_bad_paper_horizon_duration(self) -> None:
        source = yaml.safe_load(HEAVY_TOP_CONFIG_PATH.read_text(encoding="utf-8"))
        source["mabd_paper_horizon"] = deepcopy(source["mabd_newton"])
        source["mabd_paper_horizon"]["output_report"] = (
            "reports/experiment_matrix/single_body_heavy_top_mabd_paper_horizon.json"
        )
        source["mabd_paper_horizon"]["sample_count"] = source["reference"]["sample_count"]
        source["mabd_paper_horizon"]["step_count"] = 9999
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "single_body_heavy_top.yaml"
            path.write_text(yaml.safe_dump(source), encoding="utf-8")

            with self.assertRaisesRegex(
                ExperimentRunConfigError,
                "mabd_paper_horizon.*reference.duration_s",
            ):
                load_heavy_top_config(path)

    def test_heavy_top_config_rejects_paper_horizon_output_reuse(self) -> None:
        source = yaml.safe_load(HEAVY_TOP_CONFIG_PATH.read_text(encoding="utf-8"))
        source["mabd_paper_horizon"] = deepcopy(source["mabd_newton"])
        source["mabd_paper_horizon"]["step_count"] = 10000
        source["mabd_paper_horizon"]["sample_count"] = source["reference"]["sample_count"]
        source["mabd_paper_horizon"]["output_report"] = source["mabd_newton"]["output_report"]
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "single_body_heavy_top.yaml"
            path.write_text(yaml.safe_dump(source), encoding="utf-8")

            with self.assertRaisesRegex(
                ExperimentRunConfigError,
                "mabd_paper_horizon.output_report",
            ):
                load_heavy_top_config(path)

    def test_heavy_top_config_rejects_passed_status(self) -> None:
        source = yaml.safe_load(HEAVY_TOP_CONFIG_PATH.read_text(encoding="utf-8"))
        source["report"]["status"] = "passed"
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "single_body_heavy_top.yaml"
            path.write_text(yaml.safe_dump(source), encoding="utf-8")

            with self.assertRaisesRegex(ExperimentRunConfigError, "passed experiment configs"):
                load_heavy_top_config(path)

    def test_heavy_top_config_rejects_nonpositive_inertia(self) -> None:
        source = yaml.safe_load(HEAVY_TOP_CONFIG_PATH.read_text(encoding="utf-8"))
        source["reference"]["principal_inertia_kg_m2"][0] = 0.0
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "single_body_heavy_top.yaml"
            path.write_text(yaml.safe_dump(source), encoding="utf-8")

            with self.assertRaisesRegex(ExperimentRunConfigError, "principal_inertia_kg_m2"):
                load_heavy_top_config(path)

    def test_heavy_top_config_rejects_figure_hash_drift(self) -> None:
        config = load_heavy_top_config(HEAVY_TOP_CONFIG_PATH)
        matrix = load_experiment_matrix(ROOT / "configs/experiments/paper_experiment_matrix.yaml")
        drifted = replace(
            config,
            reference=replace(config.reference, figure_pdf_sha256="0" * 64),
        )

        with self.assertRaisesRegex(ExperimentRunConfigError, "figure_pdf_sha256"):
            validate_heavy_top_config_against_matrix(drifted, matrix)

    def test_heavy_top_config_rejects_paper_value_reference_drift(self) -> None:
        config = load_heavy_top_config(HEAVY_TOP_CONFIG_PATH)
        matrix = load_experiment_matrix(ROOT / "configs/experiments/paper_experiment_matrix.yaml")
        cases = (
            (
                "initial_tilt_deg",
                replace(config.reference, initial_tilt_deg=45.0),
                "paper_values.tilt_deg",
            ),
            (
                "initial_spin_rad_s",
                replace(config.reference, initial_spin_rad_s=1.0),
                "paper_values.angular_speed_rad_s",
            ),
            (
                "time_step_s",
                replace(config.reference, time_step_s=0.001),
                "paper_values.reference_h_s",
            ),
        )
        for _name, reference, expected_error in cases:
            with self.subTest(expected_error=expected_error):
                drifted = replace(config, reference=reference)
                with self.assertRaisesRegex(ExperimentRunConfigError, expected_error):
                    validate_heavy_top_config_against_matrix(drifted, matrix)

    def test_physical_pendulum_config_rejects_missing_required_incomplete_lanes(self) -> None:
        config = load_physical_pendulum_config(PHYSICAL_PENDULUM_CONFIG_PATH)
        matrix = load_experiment_matrix(ROOT / "configs/experiments/paper_experiment_matrix.yaml")
        drifted = replace(config, required_missing_lanes=())

        with self.assertRaisesRegex(ExperimentRunConfigError, "mabd_newton only"):
            validate_physical_pendulum_config_against_matrix(drifted, matrix)

    def test_physical_pendulum_config_rejects_reference_drift(self) -> None:
        config = load_physical_pendulum_config(PHYSICAL_PENDULUM_CONFIG_PATH)
        matrix = load_experiment_matrix(ROOT / "configs/experiments/paper_experiment_matrix.yaml")
        drifted_reference = replace(config.reference, kappa=0.5)
        drifted = replace(config, reference=drifted_reference)

        with self.assertRaisesRegex(ExperimentRunConfigError, "reference"):
            validate_physical_pendulum_config_against_matrix(drifted, matrix)

    def test_physical_pendulum_config_rejects_degenerate_mabd_points(self) -> None:
        source = yaml.safe_load(PHYSICAL_PENDULUM_CONFIG_PATH.read_text(encoding="utf-8"))
        source["mabd_development"]["rest_points_m"][3] = source["mabd_development"]["rest_points_m"][2]
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "single_body_physical_pendulum.yaml"
            path.write_text(yaml.safe_dump(source), encoding="utf-8")

            with self.assertRaisesRegex(ExperimentRunConfigError, "nondegenerate"):
                load_physical_pendulum_config(path)

    def test_physical_pendulum_config_rejects_mabd_newton_output_reuse(self) -> None:
        source = yaml.safe_load(PHYSICAL_PENDULUM_CONFIG_PATH.read_text(encoding="utf-8"))
        source["mabd_newton"]["output_report"] = source["mabd_development"]["output_report"]
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "single_body_physical_pendulum.yaml"
            path.write_text(yaml.safe_dump(source), encoding="utf-8")
            config = load_physical_pendulum_config(path)
            matrix = load_experiment_matrix(ROOT / "configs/experiments/paper_experiment_matrix.yaml")

            with self.assertRaisesRegex(ExperimentRunConfigError, "mabd_newton.output_report"):
                validate_physical_pendulum_config_against_matrix(config, matrix)

    def test_physical_pendulum_config_rejects_mabd_newton_missing_threshold(self) -> None:
        source = yaml.safe_load(PHYSICAL_PENDULUM_CONFIG_PATH.read_text(encoding="utf-8"))
        del source["mabd_newton"]["thresholds"]["max_phase_drift_rad"]
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "single_body_physical_pendulum.yaml"
            path.write_text(yaml.safe_dump(source), encoding="utf-8")

            with self.assertRaisesRegex(ExperimentRunConfigError, "mabd_newton.thresholds"):
                load_physical_pendulum_config(path)

    def test_physical_pendulum_config_rejects_mabd_newton_bad_rotation_mode(self) -> None:
        source = yaml.safe_load(PHYSICAL_PENDULUM_CONFIG_PATH.read_text(encoding="utf-8"))
        source["mabd_newton"]["rotation_mode"] = "no_polar"
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "single_body_physical_pendulum.yaml"
            path.write_text(yaml.safe_dump(source), encoding="utf-8")

            with self.assertRaisesRegex(ExperimentRunConfigError, "mabd_newton.rotation_mode"):
                load_physical_pendulum_config(path)

    def test_physical_pendulum_config_rejects_bad_rbd_baseline_length(self) -> None:
        source = yaml.safe_load(PHYSICAL_PENDULUM_CONFIG_PATH.read_text(encoding="utf-8"))
        source["rbd_baseline"] = {
            "time_step_s": 0.01,
            "step_count": 16,
            "sample_count": 5,
            "length_m": 0.0,
            "mass_kg": 1.0,
            "gravity_m_s2": [0.0, -9.81, 0.0],
            "initial_angle_rad": 0.0,
            "initial_angular_velocity_rad_s": 0.0,
            "newton_iteration_limit": 12,
            "newton_residual_tolerance": 1.0e-12,
            "output_report": "reports/experiment_matrix/single_body_physical_pendulum_rbd_baseline.json",
            "thresholds": {
                "max_abs_angle_error_rad": 2.0,
                "max_implicit_residual": 1.0e-12,
                "max_length_constraint_error_m": 1.0e-12,
                "max_phase_drift_rad": 2.0,
            },
        }
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "single_body_physical_pendulum.yaml"
            path.write_text(yaml.safe_dump(source), encoding="utf-8")

            with self.assertRaisesRegex(ExperimentRunConfigError, "length_m"):
                load_physical_pendulum_config(path)

    def test_physical_pendulum_config_rejects_rbd_gravity_direction_drift(self) -> None:
        source = yaml.safe_load(PHYSICAL_PENDULUM_CONFIG_PATH.read_text(encoding="utf-8"))
        source["rbd_baseline"]["gravity_m_s2"] = [9.81, 0.0, 0.0]
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "single_body_physical_pendulum.yaml"
            path.write_text(yaml.safe_dump(source), encoding="utf-8")

            with self.assertRaisesRegex(ExperimentRunConfigError, "gravity_m_s2"):
                load_physical_pendulum_config(path)

    def test_physical_pendulum_config_rejects_comparison_output_reuse(self) -> None:
        source = yaml.safe_load(PHYSICAL_PENDULUM_CONFIG_PATH.read_text(encoding="utf-8"))
        source["comparison"]["output_report"] = source["rbd_baseline"]["output_report"]
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "single_body_physical_pendulum.yaml"
            path.write_text(yaml.safe_dump(source), encoding="utf-8")
            config = load_physical_pendulum_config(path)
            matrix = load_experiment_matrix(ROOT / "configs/experiments/paper_experiment_matrix.yaml")

            with self.assertRaisesRegex(ExperimentRunConfigError, "comparison.output_report"):
                validate_physical_pendulum_config_against_matrix(config, matrix)

    def test_physical_pendulum_config_rejects_comparison_missing_mabd_lane(self) -> None:
        source = yaml.safe_load(PHYSICAL_PENDULUM_CONFIG_PATH.read_text(encoding="utf-8"))
        source["comparison"]["required_lanes"] = ["analytic_reference", "rbd_implicit_baseline"]
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "single_body_physical_pendulum.yaml"
            path.write_text(yaml.safe_dump(source), encoding="utf-8")

            with self.assertRaisesRegex(ExperimentRunConfigError, "comparison.required_lanes"):
                load_physical_pendulum_config(path)

    def test_physical_pendulum_config_rejects_comparison_bad_diagnostic_lane(self) -> None:
        source = yaml.safe_load(PHYSICAL_PENDULUM_CONFIG_PATH.read_text(encoding="utf-8"))
        source["comparison"]["diagnostic_lanes"] = ["mabd_newton"]
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "single_body_physical_pendulum.yaml"
            path.write_text(yaml.safe_dump(source), encoding="utf-8")

            with self.assertRaisesRegex(ExperimentRunConfigError, "comparison.diagnostic_lanes"):
                load_physical_pendulum_config(path)

    def test_physical_pendulum_config_rejects_comparison_missing_metric(self) -> None:
        source = yaml.safe_load(PHYSICAL_PENDULUM_CONFIG_PATH.read_text(encoding="utf-8"))
        source["comparison"]["required_metrics"] = ["pendulum_angle_error", "phase_drift"]
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "single_body_physical_pendulum.yaml"
            path.write_text(yaml.safe_dump(source), encoding="utf-8")

            with self.assertRaisesRegex(ExperimentRunConfigError, "comparison.required_metrics"):
                load_physical_pendulum_config(path)

    def test_physical_pendulum_config_rejects_comparison_missing_threshold(self) -> None:
        source = yaml.safe_load(PHYSICAL_PENDULUM_CONFIG_PATH.read_text(encoding="utf-8"))
        source["comparison"]["thresholds"] = {}
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "single_body_physical_pendulum.yaml"
            path.write_text(yaml.safe_dump(source), encoding="utf-8")

            with self.assertRaisesRegex(ExperimentRunConfigError, "comparison.thresholds"):
                load_physical_pendulum_config(path)

    def test_physical_pendulum_config_rejects_passed_experiment_status(self) -> None:
        source = yaml.safe_load(PHYSICAL_PENDULUM_CONFIG_PATH.read_text(encoding="utf-8"))
        source["report"]["status"] = "passed"
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "single_body_physical_pendulum.yaml"
            path.write_text(yaml.safe_dump(source), encoding="utf-8")

            with self.assertRaisesRegex(ExperimentRunConfigError, "passed experiment"):
                load_physical_pendulum_config(path)

    def test_spinning_box_config_matches_experiment_matrix(self) -> None:
        config = load_spinning_box_config(ROOT / "configs/experiments/single_body_spinning_box.yaml")
        matrix = load_experiment_matrix(ROOT / "configs/experiments/paper_experiment_matrix.yaml")

        validate_spinning_box_config_against_matrix(config, matrix)

        entry = next(item for item in matrix.experiments if item.claim_id == config.claim_id)
        self.assertNotIn("rbd_implicit_baseline_report_incomplete", entry.blocking_reasons)
        self.assertIn("mabd_newton_report_incomplete", entry.blocking_reasons)
        self.assertIn("spinning_box_comparison_report_incomplete", entry.blocking_reasons)
        self.assertNotIn("rbd_implicit_baseline_adapter_missing", entry.blocking_reasons)
        self.assertNotIn("paper_comparison_protocol_not_recorded", entry.blocking_reasons)

    def test_spinning_box_config_matrix_check_rejects_paper_value_drift(self) -> None:
        config = load_spinning_box_config(ROOT / "configs/experiments/single_body_spinning_box.yaml")
        matrix = load_experiment_matrix(ROOT / "configs/experiments/paper_experiment_matrix.yaml")
        drifted = replace(config, paper_values={**config.paper_values, "p0": [0, 0, 0]})

        with self.assertRaisesRegex(ExperimentRunConfigError, "paper_values"):
            validate_spinning_box_config_against_matrix(drifted, matrix)

    def test_spinning_box_config_rejects_passed_experiment_status(self) -> None:
        with TemporaryDirectory() as tmpdir:
            source = self._config_mapping()
            source["report"]["status"] = "passed"
            path = self._write_config(tmpdir, source)

            with self.assertRaisesRegex(ExperimentRunConfigError, "passed experiment"):
                load_spinning_box_config(path)

    def test_spinning_box_config_rejects_implicit_scalar_coercions(self) -> None:
        cases = (
            ("time_step_s", "0.01"),
            ("step_count", 4.5),
        )
        for key, value in cases:
            with self.subTest(key=key, value=value):
                source = self._config_mapping()
                source["simulation"][key] = value
                with TemporaryDirectory() as tmpdir:
                    path = self._write_config(tmpdir, source)

                    with self.assertRaisesRegex(ExperimentRunConfigError, key):
                        load_spinning_box_config(path)

    def test_spinning_box_config_rejects_non_finite_vectors(self) -> None:
        source = self._config_mapping()
        source["simulation"]["initial_qd"][0] = float("nan")
        with TemporaryDirectory() as tmpdir:
            path = self._write_config(tmpdir, source)

            with self.assertRaisesRegex(ExperimentRunConfigError, "initial_qd"):
                load_spinning_box_config(path)

    def test_spinning_box_config_rejects_coerced_thresholds(self) -> None:
        source = self._config_mapping()
        source["report"]["thresholds"]["energy_drift"] = "1.0e-12"
        with TemporaryDirectory() as tmpdir:
            path = self._write_config(tmpdir, source)

            with self.assertRaisesRegex(ExperimentRunConfigError, "thresholds"):
                load_spinning_box_config(path)

    def test_spinning_box_config_rejects_bad_paper_horizon_grid(self) -> None:
        source = self._config_mapping()
        source["paper_horizon"]["time_step_grid_s"] = [0.01, "0.001"]
        with TemporaryDirectory() as tmpdir:
            path = self._write_config(tmpdir, source)

            with self.assertRaisesRegex(ExperimentRunConfigError, "time_step_grid_s"):
                load_spinning_box_config(path)

    def test_docs_validator_checks_phase13_config_contract(self) -> None:
        import scripts.validate_docs as validate_docs

        source = deepcopy(self._config_mapping())
        source["report"]["status"] = "passed"
        with TemporaryDirectory() as tmpdir:
            path = self._write_config(tmpdir, source)

            with self.assertRaisesRegex(SystemExit, "passed experiment"):
                validate_docs.validate_phase13_config(
                    config_path=path,
                    matrix_path=ROOT / "configs/experiments/paper_experiment_matrix.yaml",
                )


if __name__ == "__main__":
    unittest.main()
