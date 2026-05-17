from __future__ import annotations

import unittest
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np

from mabd_reproduction.experiment_configs import load_spinning_box_config
from mabd_reproduction.reporting import EvidenceStatus, load_claim_report


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs/experiments/single_body_spinning_box.yaml"


class RigidBaselineTests(unittest.TestCase):
    def test_spinning_box_rbd_properties_follow_paper_values(self) -> None:
        from mabd_reproduction.rigid_baselines import spinning_box_rbd_properties

        config = load_spinning_box_config(CONFIG_PATH)
        props = spinning_box_rbd_properties(config)

        self.assertAlmostEqual(props.mass_kg, 1.0)
        np.testing.assert_allclose(props.inertia_diag_kg_m2, np.full(3, 1.0 / 600.0))
        np.testing.assert_allclose(props.linear_velocity_m_s, [100.0, 0.0, 0.0])
        np.testing.assert_allclose(props.angular_velocity_rad_s, [0.0, 60000.0, 0.0])

    def test_shared_spinning_box_physics_maps_paper_momenta_to_abd_velocity(self) -> None:
        from newton.solvers import mabd

        from mabd_reproduction.spinning_box_physics import (
            abd_generalized_velocity_from_paper_momenta,
            spinning_box_physical_properties,
        )

        config = load_spinning_box_config(CONFIG_PATH)
        properties = spinning_box_physical_properties(config)
        qd = abd_generalized_velocity_from_paper_momenta(config)

        self.assertEqual(qd.shape, (12,))
        np.testing.assert_allclose(properties.mass_kg, 1.0)
        np.testing.assert_allclose(properties.inertia_diag_kg_m2, [1.0 / 600.0] * 3)
        np.testing.assert_allclose(properties.linear_velocity_m_s, [100.0, 0.0, 0.0])
        np.testing.assert_allclose(properties.angular_velocity_rad_s, [0.0, 60000.0, 0.0])
        np.testing.assert_allclose(
            mabd.twist_map_G(np.eye(3)) @ qd,
            [0.0, 60000.0, 0.0, 100.0, 0.0, 0.0],
            atol=1.0e-12,
        )

    def test_run_spinning_box_rbd_baseline_is_deterministic_and_incomplete(self) -> None:
        from mabd_reproduction.rigid_baselines import run_spinning_box_rbd_baseline

        config = load_spinning_box_config(CONFIG_PATH)
        result = run_spinning_box_rbd_baseline(config)

        self.assertEqual(result.step_count, config.step_count)
        self.assertEqual(result.time_step_s, config.time_step_s)
        self.assertEqual(result.status, EvidenceStatus.INCOMPLETE)
        self.assertEqual(result.baseline_lane, "rbd_implicit_baseline")
        self.assertEqual(result.solver_name, "newton.solvers.SolverSemiImplicit")
        self.assertEqual(result.newton_step_count, config.step_count)
        np.testing.assert_allclose(result.initial_position_m, [0.0, 0.05, 0.0], atol=1.0e-15)
        np.testing.assert_allclose(result.final_position_m, [4.0, 0.05, 0.0], atol=1.0e-6)
        self.assertFalse(np.allclose(result.final_rotation_xyzw, [0.0, 0.0, 0.0, 1.0]))
        self.assertLessEqual(result.linear_momentum_error, 1.0e-6)
        self.assertLessEqual(result.angular_momentum_error, 1.0e-3)
        self.assertLessEqual(result.relative_energy_drift, 1.0e-5)

    def test_spinning_box_rbd_properties_reject_bad_physical_values(self) -> None:
        from mabd_reproduction.rigid_baselines import spinning_box_rbd_properties

        config = load_spinning_box_config(CONFIG_PATH)
        for paper_values, pattern in (
            ({**config.paper_values, "cube_size_m": 0.0}, "cube_size_m"),
            ({**config.paper_values, "density": "nan kg/m^3"}, "density"),
            ({**config.paper_values, "p0": [100.0, float("inf"), 0.0]}, "p0"),
        ):
            with self.subTest(pattern=pattern):
                with self.assertRaisesRegex(ValueError, pattern):
                    spinning_box_rbd_properties(replace(config, paper_values=paper_values))

    def test_write_spinning_box_rbd_baseline_report(self) -> None:
        from mabd_reproduction.rigid_baselines import write_spinning_box_rbd_baseline_report

        config = load_spinning_box_config(CONFIG_PATH)
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "rbd_baseline.json"
            report = write_spinning_box_rbd_baseline_report(
                path,
                config=config,
                source_commit="test-source",
                vendored_newton_commit="test-newton",
            )
            loaded = load_claim_report(path)

        self.assertEqual(report.claim_id, "experiment.single_body.spinning_box")
        self.assertEqual(loaded.baseline_lane, "rbd_implicit_baseline")
        self.assertEqual(loaded.solver_mode, "newton_semimplicit_rbd_cpu_development")
        self.assertEqual(loaded.backend, "cpu_newton_warp")
        self.assertEqual(loaded.status, EvidenceStatus.INCOMPLETE)
        self.assertIn("development baseline", loaded.failure_reason)
        self.assertEqual(loaded.observed["solver_name"], "newton.solvers.SolverSemiImplicit")
        self.assertEqual(loaded.observed["newton_step_count"], config.step_count)
        self.assertEqual(loaded.observed["initial_position_m"], [0.0, 0.05, 0.0])
        self.assertIn("linear_velocity_m_s", loaded.observed)
        self.assertIn("angular_velocity_rad_s", loaded.observed)
        self.assertIn("final_position_m", loaded.observed)
        self.assertAlmostEqual(loaded.observed["final_position_m"][1], 0.05)
        self.assertIn("final_rotation_xyzw", loaded.observed)
        self.assertIn("linear_momentum_error", loaded.observed)
        self.assertIn("angular_momentum_error", loaded.observed)
        self.assertIn("energy_drift", loaded.observed)
        self.assertIn("relative_energy_drift", loaded.observed)
        self.assertIn("energy_drift", loaded.threshold)
        self.assertLessEqual(loaded.observed["energy_drift"], loaded.threshold["energy_drift"])
        self.assertAlmostEqual(
            loaded.threshold["energy_drift"],
            loaded.observed["initial_energy"] * loaded.threshold["relative_energy_drift"],
        )


if __name__ == "__main__":
    unittest.main()
