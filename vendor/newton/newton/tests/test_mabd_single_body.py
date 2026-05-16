# SPDX-FileCopyrightText: Copyright (c) 2026 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import unittest

import numpy as np

import newton
from newton._src.solvers.mabd import (
    SingleBodyABDHessianCache,
    SingleBodyABDPrecompute,
    affine_force_from_wrench,
    apply_no_polar_increment_rotation,
    apply_no_polar_rhs_rotation,
    generalized_mass_matrix,
    lame_parameters,
    linear_elastic_energy,
    linear_elastic_gradient,
    pack_q,
    paper_rigid_embedding_E,
    point_jacobian,
    polar_rotation,
    rigid_embedding_E,
    solve_single_body_delta,
    tetra_volume,
    twist_map_G,
    unpack_q,
    volume_weighted_affine_force,
    volume_weighted_force,
    volume_weighted_jacobian,
)
from newton.solvers import SolverMABD


class TestMABDSingleBodyInternal(unittest.TestCase):
    def test_affine_q_uses_paper_column_blocks(self) -> None:
        A = np.array([[1.0, 0.2, 0.3], [0.4, 2.0, 0.6], [0.7, 0.8, 3.0]])
        t = np.array([3.0, -2.0, 0.5])

        q = pack_q(A, t)

        self.assertTrue(np.allclose(q[:3], A[:, 0]))
        self.assertTrue(np.allclose(q[3:6], A[:, 1]))
        self.assertTrue(np.allclose(q[6:9], A[:, 2]))
        self.assertTrue(np.allclose(q[9:12], t))
        A_round, t_round = unpack_q(q)
        self.assertTrue(np.allclose(A_round, A))
        self.assertTrue(np.allclose(t_round, t))

    def test_point_jacobian_force_and_mass_oracles(self) -> None:
        rest_points = np.array(
            [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
        )
        masses = np.full(4, 0.25)
        A = np.array([[1.0, 0.1, 0.0], [0.2, 1.5, -0.1], [0.3, 0.4, 0.8]])
        t = np.array([0.25, -0.5, 0.75])

        self.assertTrue(np.allclose(point_jacobian(rest_points[2]) @ pack_q(A, t), A @ rest_points[2] + t))
        self.assertAlmostEqual(tetra_volume(rest_points), 1.0 / 6.0)

        M = generalized_mass_matrix(rest_points, masses)
        self.assertGreater(float(np.linalg.eigvalsh(M).min()), 0.0)

        forces = np.ones((4, 3))
        volumes = np.full(4, 0.125)
        expected = sum(
            volume * point_jacobian(point).T @ force
            for point, force, volume in zip(rest_points, forces, volumes, strict=True)
        )
        self.assertTrue(np.allclose(volume_weighted_force(rest_points, forces, volumes), expected))

        bar_j = volume_weighted_jacobian(rest_points[None, :, :], np.array([1.0 / 6.0]))
        aggregated_force = np.arange(12, dtype=float) + 1.0
        self.assertTrue(
            np.allclose(
                volume_weighted_affine_force(rest_points[None, :, :], aggregated_force, np.array([1.0 / 6.0])),
                bar_j.T @ aggregated_force,
            )
        )

    def test_elasticity_rotation_twist_and_cache_oracles(self) -> None:
        A = np.array([[1.1, 0.2, 0.0], [0.0, 0.9, -0.1], [0.05, 0.0, 1.2]])
        mu, lam = lame_parameters(20.0, 0.25)
        self.assertAlmostEqual(mu, 8.0)
        self.assertAlmostEqual(lam, 8.0)
        self.assertEqual(linear_elastic_gradient(np.eye(3), 20.0, 0.25).shape, (3, 3))
        self.assertGreater(linear_elastic_energy(A, 20.0, 0.25), 0.0)

        R = polar_rotation(A)
        self.assertTrue(np.allclose(R.T @ R, np.eye(3), atol=1.0e-12))
        blocks = np.arange(12, dtype=float) + 1.0
        self.assertAlmostEqual(np.linalg.norm(blocks[:3]), np.linalg.norm(apply_no_polar_rhs_rotation(A, blocks)[:3]))
        self.assertAlmostEqual(
            np.linalg.norm(blocks[:3]),
            np.linalg.norm(apply_no_polar_increment_rotation(A, blocks)[:3]),
        )

        theta = 0.35
        R = np.array(
            [
                [np.cos(theta), -np.sin(theta), 0.0],
                [np.sin(theta), np.cos(theta), 0.0],
                [0.0, 0.0, 1.0],
            ]
        )
        G = twist_map_G(R)
        self.assertTrue(np.allclose(paper_rigid_embedding_E(R), rigid_embedding_E(R), atol=1.0e-10))
        E = rigid_embedding_E(R)
        self.assertTrue(np.allclose(G @ E, np.eye(6), atol=1.0e-10))
        wrench = np.array([0.2, -0.4, 0.6, 1.0, 2.0, -1.5])
        dq = np.linspace(-0.3, 0.4, 12)
        self.assertAlmostEqual(float(affine_force_from_wrench(R, wrench) @ dq), float(wrench @ (G @ dq)))

        A_diag = np.diag([1.2, 0.9, 1.4])
        self.assertFalse(np.allclose(twist_map_G(A_diag) @ paper_rigid_embedding_E(A_diag), np.eye(6)))
        self.assertTrue(np.allclose(twist_map_G(A_diag) @ rigid_embedding_E(A_diag), np.eye(6), atol=1.0e-10))

        rest_points = np.array(
            [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
        )
        pre = SingleBodyABDPrecompute.from_points(rest_points, np.full(4, 0.25), stiffness_matrix=np.eye(12))
        cache = SingleBodyABDHessianCache(pre)
        self.assertIs(cache.factor(0.01, "cpu", 0), cache.factor(0.01, "cpu", 0))
        self.assertIsNot(cache.factor(0.01, "cpu", 0), cache.factor(0.02, "cpu", 0))
        factor = cache.factor(0.01, "cpu", 0)
        rhs = np.arange(12, dtype=float) + 1.0
        self.assertTrue(
            np.allclose(
                solve_single_body_delta(pre, rhs, 0.01, A=A, rotation_mode="no_polar", cache=cache),
                apply_no_polar_increment_rotation(A, factor.solve(apply_no_polar_rhs_rotation(A, rhs))),
            )
        )

    def test_solver_registers_custom_attributes_and_invalidates_cache(self) -> None:
        builder = newton.ModelBuilder()
        SolverMABD.register_custom_attributes(builder)
        self.assertIn("mabd:body", builder.custom_frequencies)
        self.assertIn("mabd:body_index", builder.custom_attributes)
        self.assertIn("mabd:q0", builder.custom_attributes)

        model = builder.finalize()
        solver = SolverMABD(model)
        self.assertEqual(solver.model_version, 0)
        solver.notify_model_changed(0)
        self.assertEqual(solver.model_version, 1)

    def test_custom_frequency_rows_finalize_to_model_and_state(self) -> None:
        builder = newton.ModelBuilder()
        SolverMABD.register_custom_attributes(builder)
        body_id = builder.add_body()
        builder.add_custom_values(
            **{
                "mabd:body_index": body_id,
                "mabd:young_modulus": 50.0,
                "mabd:poisson_ratio": 0.2,
                "mabd:density": 3.0,
                "mabd:polar_mode": 1,
            }
        )

        model = builder.finalize()
        state = model.state()

        self.assertEqual(model.get_custom_frequency_count("mabd:body"), 1)
        self.assertEqual(int(model.mabd.body_index.numpy()[0]), body_id)
        self.assertAlmostEqual(float(model.mabd.young_modulus.numpy()[0]), 50.0)
        self.assertTrue(np.allclose(state.mabd.q0.numpy()[0], [1.0, 0.0, 0.0]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
