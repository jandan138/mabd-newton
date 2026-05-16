from __future__ import annotations

import unittest

import numpy as np
import warp as wp

import newton
from newton.solvers import SolverMABD, mabd


class MABDControlForcePublicTests(unittest.TestCase):
    def test_affine_pd_control_force_matches_formula(self) -> None:
        q = np.linspace(-0.3, 0.8, 12)
        qd = np.linspace(0.2, -0.1, 12)
        target_q = q + np.linspace(0.05, -0.02, 12)
        target_qd = qd + np.linspace(-0.03, 0.04, 12)
        feedforward = np.linspace(0.1, 1.2, 12)
        damping = np.linspace(0.5, 1.6, 12)
        spec = mabd.MABDActuationSpec(
            body_id=2,
            target_q=target_q,
            target_qd=target_qd,
            stiffness=3.0,
            damping=damping,
            feedforward_force=feedforward,
        )

        evaluation = mabd.evaluate_affine_pd_control(q, qd, spec)

        expected = 3.0 * (target_q - q) + damping * (target_qd - qd) + feedforward
        self.assertEqual(evaluation.body_id, 2)
        self.assertTrue(np.allclose(evaluation.position_error, target_q - q))
        self.assertTrue(np.allclose(evaluation.velocity_error, target_qd - qd))
        self.assertTrue(np.allclose(evaluation.generalized_force, expected))

    def test_affine_pd_control_allows_feedforward_only(self) -> None:
        q = np.zeros(12)
        qd = np.zeros(12)
        feedforward = np.linspace(-0.4, 0.7, 12)
        spec = mabd.MABDActuationSpec(body_id=0, feedforward_force=feedforward)

        evaluation = mabd.evaluate_affine_pd_control(q, qd, spec)

        self.assertTrue(np.allclose(evaluation.position_error, np.zeros(12)))
        self.assertTrue(np.allclose(evaluation.velocity_error, np.zeros(12)))
        self.assertTrue(np.allclose(evaluation.generalized_force, feedforward))

    def test_assemble_control_generalized_forces_sums_by_body(self) -> None:
        q = [np.zeros(12), np.ones(12)]
        qd = [np.zeros(12), np.zeros(12)]
        base = [np.ones(12), np.full(12, 2.0)]
        act_a = mabd.MABDActuationSpec(
            body_id=1,
            target_q=np.full(12, 3.0),
            stiffness=0.5,
        )
        act_b = mabd.MABDActuationSpec(
            body_id=1,
            target_qd=np.full(12, -2.0),
            damping=0.25,
            feedforward_force=np.arange(12, dtype=float),
        )
        act_c = mabd.MABDActuationSpec(body_id=0, feedforward_force=np.full(12, -0.5))

        observed = mabd.assemble_control_generalized_forces(
            q,
            qd,
            actuations=[act_a, act_b, act_c],
            base_external_forces=base,
        )

        expected_body_1 = (
            base[1]
            + 0.5 * (np.full(12, 3.0) - q[1])
            + 0.25 * np.full(12, -2.0)
            + np.arange(12)
        )
        self.assertTrue(np.allclose(observed[0], np.full(12, 0.5)))
        self.assertTrue(np.allclose(observed[1], expected_body_1))

    def test_control_force_validation_rejects_bad_ids_shapes_and_gains(self) -> None:
        q = [np.zeros(12)]
        qd = [np.zeros(12)]
        with self.assertRaisesRegex(ValueError, "body_id"):
            mabd.assemble_control_generalized_forces(
                q,
                qd,
                actuations=[mabd.MABDActuationSpec(body_id=3, feedforward_force=np.zeros(12))],
            )
        with self.assertRaisesRegex(ValueError, "target_q"):
            mabd.evaluate_affine_pd_control(
                np.zeros(12),
                np.zeros(12),
                mabd.MABDActuationSpec(body_id=0, target_q=np.zeros(11)),
            )
        with self.assertRaisesRegex(ValueError, "stiffness"):
            mabd.evaluate_affine_pd_control(
                np.zeros(12),
                np.zeros(12),
                mabd.MABDActuationSpec(body_id=0, stiffness=-1.0),
            )

    def test_solver_registers_control_frequency_rows(self) -> None:
        builder = newton.ModelBuilder()
        SolverMABD.register_custom_attributes(builder)
        body_id = builder.add_body()
        builder.add_custom_values(
            **{
                "mabd:body_index": body_id,
                "mabd:young_modulus": 1.0,
                "mabd:poisson_ratio": 0.25,
                "mabd:density": 1.0,
                "mabd:polar_mode": 0,
            }
        )
        builder.add_custom_values(
            **{
                "mabd:control_body": 0,
                "mabd:control_enabled": 1,
                "mabd:control_stiffness": 2.0,
                "mabd:control_damping": 0.5,
                "mabd:control_target_q0": wp.vec3(1.0, 0.0, 0.0),
                "mabd:control_target_q1": wp.vec3(0.0, 1.0, 0.0),
                "mabd:control_target_q2": wp.vec3(0.0, 0.0, 1.0),
                "mabd:control_target_t": wp.vec3(0.1, 0.2, 0.3),
                "mabd:control_target_qd0": wp.vec3(0.0, 0.0, 0.0),
                "mabd:control_target_qd1": wp.vec3(0.0, 0.0, 0.0),
                "mabd:control_target_qd2": wp.vec3(0.0, 0.0, 0.0),
                "mabd:control_target_td": wp.vec3(0.0, 0.0, 0.0),
                "mabd:control_feedforward_q0": wp.vec3(0.0, 0.0, 0.0),
                "mabd:control_feedforward_q1": wp.vec3(0.0, 0.0, 0.0),
                "mabd:control_feedforward_q2": wp.vec3(0.0, 0.0, 0.0),
                "mabd:control_feedforward_t": wp.vec3(0.0, 1.0, 0.0),
            }
        )

        model = builder.finalize()

        self.assertIn("mabd:control", builder.custom_frequencies)
        self.assertEqual(model.get_custom_frequency_count("mabd:control"), 1)
        self.assertEqual(int(model.mabd.control_body.numpy()[0]), 0)
        self.assertEqual(int(model.mabd.control_enabled.numpy()[0]), 1)
        self.assertAlmostEqual(float(model.mabd.control_stiffness.numpy()[0]), 2.0)
        self.assertTrue(np.allclose(model.mabd.control_target_t.numpy()[0], [0.1, 0.2, 0.3]))


if __name__ == "__main__":
    unittest.main()
