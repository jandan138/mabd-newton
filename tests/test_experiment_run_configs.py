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
    load_physical_pendulum_config,
    load_spinning_box_config,
    validate_physical_pendulum_config_against_matrix,
    validate_spinning_box_config_against_matrix,
)
from mabd_reproduction.experiment_contracts import load_experiment_matrix
from mabd_reproduction.reporting import EvidenceStatus


ROOT = Path(__file__).resolve().parents[1]
PHYSICAL_PENDULUM_CONFIG_PATH = ROOT / "configs/experiments/single_body_physical_pendulum.yaml"


class ExperimentRunConfigTests(unittest.TestCase):
    def _config_mapping(self) -> dict:
        return yaml.safe_load((ROOT / "configs/experiments/single_body_spinning_box.yaml").read_text())

    def _write_config(self, tmpdir: str, mapping: dict) -> Path:
        path = Path(tmpdir) / "single_body_spinning_box.yaml"
        path.write_text(yaml.safe_dump(mapping), encoding="utf-8")
        return path

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
