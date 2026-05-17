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
    load_spinning_box_config,
    validate_spinning_box_config_against_matrix,
)
from mabd_reproduction.experiment_contracts import load_experiment_matrix
from mabd_reproduction.reporting import EvidenceStatus


ROOT = Path(__file__).resolve().parents[1]


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
        self.assertIn("rbd_implicit_baseline", config.failure_reason)
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
        self.assertEqual(config.contact_surface["type"], "plane")
        self.assertEqual(config.contact_surface["plane_normal"], (0.0, 1.0, 0.0))
        self.assertEqual(config.contact_surface["plane_offset"], 0.0)
        self.assertGreater(config.contact_surface["stiffness"], 0.0)
        self.assertGreaterEqual(config.contact_surface["damping"], 0.0)
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

    def test_spinning_box_config_matches_experiment_matrix(self) -> None:
        config = load_spinning_box_config(ROOT / "configs/experiments/single_body_spinning_box.yaml")
        matrix = load_experiment_matrix(ROOT / "configs/experiments/paper_experiment_matrix.yaml")

        validate_spinning_box_config_against_matrix(config, matrix)

        entry = next(item for item in matrix.experiments if item.claim_id == config.claim_id)
        self.assertIn("rbd_implicit_baseline_report_incomplete", entry.blocking_reasons)
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
