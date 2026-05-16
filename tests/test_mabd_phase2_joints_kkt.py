from __future__ import annotations

import unittest

import numpy as np
import warp as wp

import newton
from newton.solvers import SolverMABD, mabd


HINGE_CT = np.array(
    [
        [0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0],
        [1.0, 0.0, 0.0],
    ],
    dtype=float,
)

UNIVERSAL_CT = np.array(
    [
        [0.0, 0.0, 0.0],
        [0.0, 0.0, 1.0],
        [0.0, 1.0, 0.0],
        [1.0, 0.0, 0.0],
    ],
    dtype=float,
)


def _identity_q(translation: tuple[float, float, float] = (0.0, 0.0, 0.0)) -> np.ndarray:
    return mabd.pack_q(np.eye(3), np.array(translation, dtype=float))


def _finite_difference_gradient(spec: object, q_a: np.ndarray, q_b: np.ndarray) -> np.ndarray:
    base = mabd.joint_residual(spec, q_a, q_b)
    grad = np.zeros((base.shape[0], 24), dtype=float)
    eps = 1.0e-6
    for col in range(24):
        dq_a = np.zeros(12, dtype=float)
        dq_b = np.zeros(12, dtype=float)
        if col < 12:
            dq_a[col] = eps
        else:
            dq_b[col - 12] = eps
        plus = mabd.joint_residual(spec, q_a + dq_a, q_b + dq_b)
        minus = mabd.joint_residual(spec, q_a - dq_a, q_b - dq_b)
        grad[:, col] = (plus - minus) / (2.0 * eps)
    return grad


class MABDPhase2JointAndKKTTests(unittest.TestCase):
    def test_control_tetrahedron_transform_round_trips_arbitrary_ct(self) -> None:
        ct = np.array(
            [
                [-0.2, 0.1, 0.3],
                [1.4, -0.1, 0.2],
                [0.2, 1.1, -0.4],
                [0.1, 0.3, 1.2],
            ],
            dtype=float,
        )
        A = np.array([[1.2, 0.1, -0.2], [0.3, 0.9, 0.4], [-0.1, 0.2, 1.1]], dtype=float)
        t = np.array([0.25, -0.5, 0.75], dtype=float)
        q = mabd.pack_q(A, t)

        T = mabd.control_point_transform(ct)
        T_inv = mabd.control_point_inverse_transform(ct)
        y = mabd.control_points_from_q(q, ct)
        expected = np.concatenate([A @ point + t for point in ct])

        self.assertEqual(T.shape, (12, 12))
        self.assertEqual(T_inv.shape, (12, 12))
        self.assertEqual(np.linalg.matrix_rank(T), 12)
        self.assertTrue(np.allclose(T @ q, expected))
        self.assertTrue(np.allclose(y, expected))
        self.assertTrue(np.allclose(T_inv @ y, q))
        self.assertTrue(np.allclose(mabd.q_from_control_points(y, ct), q))

    def test_control_tetrahedron_transform_rejects_degenerate_ct(self) -> None:
        coplanar = np.array(
            [
                [0.0, 0.0, 0.0],
                [1.0, 0.0, 0.0],
                [0.0, 1.0, 0.0],
                [1.0, 1.0, 0.0],
            ],
            dtype=float,
        )

        with self.assertRaises(ValueError):
            mabd.control_point_transform(coplanar)

    def test_joint_residuals_have_paper_minimal_ranks_at_rest_fixture(self) -> None:
        q = _identity_q()
        cases = [
            (mabd.ball_joint(HINGE_CT, HINGE_CT), 3),
            (mabd.hinge_joint(HINGE_CT, HINGE_CT, axis=np.array([0.0, 1.0, 0.0])), 5),
            (
                mabd.universal_joint(
                    UNIVERSAL_CT,
                    UNIVERSAL_CT,
                    axis0=np.array([0.0, 1.0, 0.0]),
                    axis1=np.array([0.0, 0.0, 1.0]),
                ),
                4,
            ),
            (mabd.prismatic_joint(HINGE_CT, HINGE_CT, axis=np.array([0.0, 1.0, 0.0])), 5),
        ]

        for spec, expected_rank in cases:
            with self.subTest(joint=spec.joint_type):
                evaluation = mabd.evaluate_joint(spec, q, q)

                self.assertEqual(evaluation.residual.shape, (expected_rank,))
                self.assertEqual(evaluation.gradient.shape, (expected_rank, 24))
                self.assertEqual(evaluation.rank, expected_rank)
                self.assertEqual(np.linalg.matrix_rank(evaluation.gradient), expected_rank)
                self.assertTrue(np.allclose(evaluation.residual, np.zeros(expected_rank)))

    def test_universal_joint_uses_equation_rank_four_not_caption_rank_five(self) -> None:
        spec = mabd.universal_joint(
            UNIVERSAL_CT,
            UNIVERSAL_CT,
            axis0=np.array([0.0, 1.0, 0.0]),
            axis1=np.array([0.0, 0.0, 1.0]),
        )

        evaluation = mabd.evaluate_joint(spec, _identity_q(), _identity_q())

        self.assertEqual(evaluation.rank, 4)
        self.assertEqual(evaluation.residual.shape, (4,))

    def test_ball_residual_equals_selected_control_point_delta_and_gradient_is_constant(self) -> None:
        spec = mabd.ball_joint(HINGE_CT, HINGE_CT, cp_index=0)
        q_a = _identity_q((0.5, -0.25, 0.75))
        q_b = _identity_q((-0.1, 0.4, 0.25))

        evaluation = mabd.evaluate_joint(spec, q_a, q_b)
        expected_delta = np.array([0.6, -0.65, 0.5])

        self.assertTrue(np.allclose(evaluation.residual, expected_delta))

        q_a_2 = mabd.pack_q(np.array([[1.1, 0.2, 0.0], [0.0, 0.9, -0.1], [0.0, 0.0, 1.0]]), [0.0, 0.0, 0.0])
        q_b_2 = mabd.pack_q(np.eye(3), [0.25, 0.5, -0.75])
        gradient_2 = mabd.evaluate_joint(spec, q_a_2, q_b_2).gradient

        self.assertTrue(np.allclose(evaluation.gradient, gradient_2))

    def test_finite_difference_joint_gradients_match_returned_gradients(self) -> None:
        q_a = mabd.pack_q(
            np.array([[1.0, 0.02, 0.0], [-0.01, 1.0, 0.03], [0.0, -0.02, 1.0]], dtype=float),
            np.array([0.1, -0.2, 0.3], dtype=float),
        )
        q_b = mabd.pack_q(
            np.array([[0.98, -0.01, 0.02], [0.03, 1.01, -0.02], [-0.01, 0.02, 0.99]], dtype=float),
            np.array([-0.15, 0.25, -0.05], dtype=float),
        )
        specs = [
            mabd.hinge_joint(HINGE_CT, HINGE_CT, axis=np.array([0.0, 1.0, 0.0])),
            mabd.universal_joint(
                UNIVERSAL_CT,
                UNIVERSAL_CT,
                axis0=np.array([0.0, 1.0, 0.0]),
                axis1=np.array([0.0, 0.0, 1.0]),
            ),
            mabd.prismatic_joint(HINGE_CT, HINGE_CT, axis=np.array([0.0, 1.0, 0.0])),
        ]

        for spec in specs:
            with self.subTest(joint=spec.joint_type):
                evaluation = mabd.evaluate_joint(
                    spec,
                    q_a,
                    q_b,
                    gradient_mode=mabd.JointGradientMode.FINITE_DIFFERENCE_ORACLE,
                )
                expected = _finite_difference_gradient(spec, q_a, q_b)

                self.assertTrue(np.allclose(evaluation.gradient, expected, atol=5.0e-6, rtol=5.0e-5))

    def test_prismatic_residual_is_invariant_to_shared_translation(self) -> None:
        spec = mabd.prismatic_joint(HINGE_CT, HINGE_CT, axis=np.array([0.0, 1.0, 0.0]))
        q_a = _identity_q((1.0, -0.25, 0.5))
        q_b = _identity_q((1.0, -0.25, 0.5))

        evaluation = mabd.evaluate_joint(spec, q_a, q_b)

        self.assertTrue(np.allclose(evaluation.residual, np.zeros(5), atol=1.0e-12))

    def test_paper_faithful_gradient_mode_is_not_exposed_before_rotation_gradient_path(self) -> None:
        spec = mabd.hinge_joint(HINGE_CT, HINGE_CT, axis=np.array([0.0, 1.0, 0.0]))

        with self.assertRaises(NotImplementedError):
            mabd.evaluate_joint(spec, _identity_q(), _identity_q(), gradient_mode="paper_faithful")

    def test_dense_dual_kkt_matches_direct_primal_kkt_with_zero_lower_rhs(self) -> None:
        q = _identity_q()
        spec = mabd.hinge_joint(HINGE_CT, HINGE_CT, axis=np.array([0.0, 1.0, 0.0]))
        J = mabd.evaluate_joint(spec, q, q).gradient
        H = np.diag(np.linspace(2.0, 5.0, 24))
        f = np.linspace(-0.4, 0.6, 24)

        primal = mabd.solve_dense_primal_kkt(H, J, f)
        dual = mabd.solve_dense_dual_kkt(H, J, f)

        self.assertTrue(np.allclose(primal.dq, dual.dq, atol=1.0e-10))
        self.assertTrue(np.allclose(primal.dlambda, dual.dlambda, atol=1.0e-10))
        self.assertTrue(np.allclose(H @ dual.dq + J.T @ dual.dlambda, f, atol=1.0e-10))
        self.assertTrue(np.allclose(J @ dual.dq, np.zeros(J.shape[0]), atol=1.0e-10))

    def test_dense_dual_kkt_matches_direct_primal_kkt_with_residual_corrected_rhs(self) -> None:
        q_a = _identity_q((0.2, 0.0, 0.0))
        q_b = _identity_q()
        spec = mabd.ball_joint(HINGE_CT, HINGE_CT)
        evaluation = mabd.evaluate_joint(spec, q_a, q_b)
        J = evaluation.gradient
        H = np.diag(np.linspace(1.5, 4.0, 24))
        f = np.linspace(0.2, -0.3, 24)
        lower_rhs = -evaluation.residual

        zero_rhs = mabd.solve_dense_dual_kkt(H, J, f)
        primal = mabd.solve_dense_primal_kkt(H, J, f, lower_rhs=lower_rhs)
        corrected = mabd.solve_dense_dual_kkt(H, J, f, lower_rhs=lower_rhs)

        self.assertTrue(np.allclose(primal.dq, corrected.dq, atol=1.0e-10))
        self.assertTrue(np.allclose(primal.dlambda, corrected.dlambda, atol=1.0e-10))
        self.assertTrue(np.allclose(J @ corrected.dq, lower_rhs, atol=1.0e-10))
        self.assertFalse(np.allclose(zero_rhs.dq, corrected.dq))

    def test_solver_registers_constraint_frequency_rows(self) -> None:
        builder = newton.ModelBuilder()
        SolverMABD.register_custom_attributes(builder)
        body_id = builder.add_body()
        builder.add_custom_values(
            **{
                "mabd:body_index": body_id,
                "mabd:young_modulus": 50.0,
                "mabd:poisson_ratio": 0.25,
                "mabd:density": 2.0,
                "mabd:polar_mode": 1,
            }
        )
        builder.add_custom_values(
            **{
                "mabd:constraint_type": 1,
                "mabd:body_a": 0,
                "mabd:body_b": 0,
                "mabd:rank": 3,
                "mabd:gradient_mode": 1,
                "mabd:axis0": wp.vec3(0.0, 1.0, 0.0),
                "mabd:axis1": wp.vec3(0.0, 0.0, 1.0),
            }
        )

        model = builder.finalize()

        self.assertIn("mabd:constraint", builder.custom_frequencies)
        self.assertEqual(model.get_custom_frequency_count("mabd:constraint"), 1)
        self.assertEqual(int(model.mabd.constraint_type.numpy()[0]), 1)
        self.assertEqual(int(model.mabd.body_a.numpy()[0]), 0)
        self.assertEqual(int(model.mabd.body_b.numpy()[0]), 0)
        self.assertEqual(int(model.mabd.rank.numpy()[0]), 3)
        self.assertTrue(np.allclose(model.mabd.axis0.numpy()[0], [0.0, 1.0, 0.0]))


if __name__ == "__main__":
    unittest.main()
