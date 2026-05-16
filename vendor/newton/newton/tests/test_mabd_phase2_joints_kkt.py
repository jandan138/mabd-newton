from __future__ import annotations

import unittest

import numpy as np

from newton._src.solvers import mabd

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


def _identity_q() -> np.ndarray:
    return mabd.pack_q(np.eye(3), np.zeros(3, dtype=float))


class MABDPhase2InternalTests(unittest.TestCase):
    def test_control_tetrahedron_transform_round_trips(self) -> None:
        ct = np.array(
            [
                [-0.2, 0.1, 0.3],
                [1.4, -0.1, 0.2],
                [0.2, 1.1, -0.4],
                [0.1, 0.3, 1.2],
            ],
            dtype=float,
        )
        q = mabd.pack_q(
            np.array([[1.2, 0.1, -0.2], [0.3, 0.9, 0.4], [-0.1, 0.2, 1.1]], dtype=float),
            np.array([0.25, -0.5, 0.75], dtype=float),
        )

        y = mabd.control_points_from_q(q, ct)

        self.assertEqual(mabd.control_point_transform(ct).shape, (12, 12))
        self.assertTrue(np.allclose(mabd.q_from_control_points(y, ct), q))

    def test_joint_residuals_have_paper_minimal_ranks(self) -> None:
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
            evaluation = mabd.evaluate_joint(spec, q, q)
            self.assertEqual(evaluation.rank, expected_rank)
            self.assertEqual(evaluation.gradient.shape, (expected_rank, 24))
            self.assertTrue(np.allclose(evaluation.residual, np.zeros(expected_rank)))

    def test_dense_dual_kkt_matches_direct_primal_kkt(self) -> None:
        spec = mabd.hinge_joint(HINGE_CT, HINGE_CT, axis=np.array([0.0, 1.0, 0.0]))
        J = mabd.evaluate_joint(spec, _identity_q(), _identity_q()).gradient
        H = np.diag(np.linspace(2.0, 5.0, 24))
        f = np.linspace(-0.4, 0.6, 24)
        lower_rhs = np.linspace(-0.02, 0.03, J.shape[0])

        primal = mabd.solve_dense_primal_kkt(H, J, f, lower_rhs=lower_rhs)
        dual = mabd.solve_dense_dual_kkt(H, J, f, lower_rhs=lower_rhs)

        self.assertTrue(np.allclose(primal.dq, dual.dq, atol=1.0e-10))
        self.assertTrue(np.allclose(primal.dlambda, dual.dlambda, atol=1.0e-10))
        self.assertTrue(np.allclose(J @ dual.dq, lower_rhs, atol=1.0e-10))


if __name__ == "__main__":
    unittest.main()
