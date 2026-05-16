# SPDX-FileCopyrightText: Copyright (c) 2026 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import unittest

import numpy as np

import newton
from newton._src.solvers.mabd import (
    SingleBodyABDHessianCache,
    SingleBodyABDPrecompute,
    affine_force_from_point_force,
    affine_force_from_wrench,
    apply_no_polar_increment_rotation,
    apply_no_polar_rhs_rotation,
    co_rotated_generalized_stiffness_matrix,
    co_rotated_linear_elastic_affine_force,
    co_rotated_linear_elastic_energy,
    evaluate_point_plane_penalty_contact,
    generalized_mass_matrix,
    lame_parameters,
    linear_elastic_energy,
    linear_elastic_gradient,
    pack_q,
    paper_rigid_embedding_E,
    point_jacobian,
    polar_rotation,
    rest_generalized_stiffness_matrix,
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

        point_force = np.array([3.0, -1.5, 2.0])
        dq = np.linspace(-0.3, 0.4, 12)
        generalized = affine_force_from_point_force(rest_points[2], point_force)
        self.assertTrue(np.allclose(generalized, point_jacobian(rest_points[2]).T @ point_force))
        self.assertAlmostEqual(float(generalized @ dq), float(point_force @ (point_jacobian(rest_points[2]) @ dq)))

        bar_j = volume_weighted_jacobian(rest_points[None, :, :], np.array([1.0 / 6.0]))
        aggregated_force = np.arange(12, dtype=float) + 1.0
        self.assertTrue(
            np.allclose(
                volume_weighted_affine_force(rest_points[None, :, :], aggregated_force, np.array([1.0 / 6.0])),
                bar_j.T @ aggregated_force,
            )
        )

    def test_point_plane_penalty_contact_oracle(self) -> None:
        rest_point = np.array([0.25, 0.02, -0.1])
        q = pack_q(np.eye(3), np.array([0.0, -0.08, 0.0]))
        qd = np.zeros(12)

        active = evaluate_point_plane_penalty_contact(
            q,
            qd,
            rest_point,
            plane_normal=np.array([0.0, 2.0, 0.0]),
            plane_offset=0.0,
            stiffness=100.0,
        )

        self.assertTrue(active.active)
        self.assertAlmostEqual(active.signed_distance, -0.06)
        self.assertAlmostEqual(active.penetration_depth, 0.06)
        self.assertTrue(np.allclose(active.plane_normal, np.array([0.0, 1.0, 0.0])))
        self.assertTrue(np.allclose(active.force, np.array([0.0, 6.0, 0.0])))
        self.assertTrue(np.allclose(active.generalized_force, point_jacobian(rest_point).T @ active.force))

        inactive = evaluate_point_plane_penalty_contact(
            pack_q(np.eye(3), np.array([0.0, 0.2, 0.0])),
            qd,
            np.array([0.0, 0.1, 0.0]),
            plane_normal=np.array([0.0, 1.0, 0.0]),
            plane_offset=0.0,
            stiffness=100.0,
        )
        self.assertFalse(inactive.active)
        self.assertTrue(np.allclose(inactive.force, np.zeros(3)))
        self.assertTrue(np.allclose(inactive.generalized_force, np.zeros(12)))

    def test_elasticity_rotation_twist_and_cache_oracles(self) -> None:
        A = np.array([[1.1, 0.2, 0.0], [0.0, 0.9, -0.1], [0.05, 0.0, 1.2]])
        mu, lam = lame_parameters(20.0, 0.25)
        self.assertAlmostEqual(mu, 8.0)
        self.assertAlmostEqual(lam, 8.0)
        self.assertEqual(linear_elastic_gradient(np.eye(3), 20.0, 0.25).shape, (3, 3))
        self.assertGreater(linear_elastic_energy(A, 20.0, 0.25), 0.0)

        K = rest_generalized_stiffness_matrix(80.0, 0.25, 0.35)
        q_rest = pack_q(np.eye(3), np.array([0.2, -0.1, 0.4]))
        direction = np.linspace(-0.2, 0.3, 12)
        direction[9:12] = np.array([0.5, -0.25, 0.75])
        eps = 1.0e-6

        def energy_at(q: np.ndarray) -> float:
            A_q, _t = unpack_q(q)
            return linear_elastic_energy(A_q, 80.0, 0.25, 0.35)

        fd_curvature = (
            energy_at(q_rest + eps * direction)
            - 2.0 * energy_at(q_rest)
            + energy_at(q_rest - eps * direction)
        ) / (eps * eps)
        self.assertTrue(np.allclose(K, K.T, atol=1.0e-12))
        self.assertTrue(np.allclose(K[9:12], np.zeros((3, 12))))
        self.assertAlmostEqual(float(direction @ K @ direction), float(fd_curvature), places=5)

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

        pure_rotation_force = co_rotated_linear_elastic_affine_force(R, 80.0, 0.25, 1.7)
        self.assertAlmostEqual(co_rotated_linear_elastic_energy(R, 80.0, 0.25, 1.7), 0.0, places=12)
        self.assertTrue(np.allclose(pure_rotation_force, np.zeros(12), atol=1.0e-12))
        self.assertGreater(np.linalg.norm(linear_elastic_gradient(R, 80.0, 0.25, 1.7)), 1.0)

        D = np.kron(np.eye(4), R)
        K_bar = rest_generalized_stiffness_matrix(50.0, 0.2, 0.9)
        self.assertTrue(
            np.allclose(co_rotated_generalized_stiffness_matrix(R, K_bar), D @ K_bar @ D.T, atol=1.0e-12)
        )

        rest_points = np.array(
            [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
        )
        linear_pre = SingleBodyABDPrecompute.from_linear_elastic_points(
            rest_points,
            np.full(4, 0.25),
            60.0,
            0.2,
            1.0 / 6.0,
        )
        self.assertTrue(
            np.allclose(
                linear_pre.stiffness_matrix,
                rest_generalized_stiffness_matrix(60.0, 0.2, 1.0 / 6.0),
            )
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
