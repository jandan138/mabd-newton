from __future__ import annotations

import unittest

import numpy as np

import newton
from newton.solvers import SolverMABD, mabd


class MABDSingleBodyPublicTests(unittest.TestCase):
    def test_affine_q_uses_paper_column_blocks(self) -> None:
        A = np.array([[1.0, 0.2, 0.3], [0.4, 2.0, 0.6], [0.7, 0.8, 3.0]])
        t = np.array([3.0, -2.0, 0.5])

        q = mabd.pack_q(A, t)

        self.assertTrue(np.allclose(q[:3], A[:, 0]))
        self.assertTrue(np.allclose(q[3:6], A[:, 1]))
        self.assertTrue(np.allclose(q[6:9], A[:, 2]))
        self.assertTrue(np.allclose(q[9:12], t))
        A_round, t_round = mabd.unpack_q(q)
        self.assertTrue(np.allclose(A_round, A))
        self.assertTrue(np.allclose(t_round, t))

    def test_point_jacobian_matches_affine_kinematics(self) -> None:
        A = np.array([[1.0, 0.1, 0.0], [0.2, 1.5, -0.1], [0.3, 0.4, 0.8]])
        t = np.array([0.25, -0.5, 0.75])
        rest_point = np.array([2.0, -3.0, 0.5])

        q = mabd.pack_q(A, t)
        J = mabd.point_jacobian(rest_point)

        self.assertTrue(np.allclose(J @ q, A @ rest_point + t))

    def test_volume_weighted_force_matches_jacobian_transpose(self) -> None:
        rest_points = np.array([[0.0, 0.0, 0.0], [1.0, -2.0, 0.5]])
        forces = np.array([[3.0, 4.0, 5.0], [-1.0, 2.0, -3.0]])
        volumes = np.array([0.25, 0.75])
        expected = sum(
            volume * mabd.point_jacobian(point).T @ force
            for point, force, volume in zip(rest_points, forces, volumes, strict=True)
        )

        observed = mabd.volume_weighted_force(rest_points, forces, volumes)

        self.assertTrue(np.allclose(observed, expected))

    def test_volume_weighted_bar_j_maps_aggregated_tet_force(self) -> None:
        tet_points = np.array(
            [
                [
                    [0.0, 0.0, 0.0],
                    [1.0, 0.0, 0.0],
                    [0.0, 1.0, 0.0],
                    [0.0, 0.0, 1.0],
                ]
            ]
        )
        volumes = np.array([1.0 / 6.0])
        aggregated_force = np.arange(12, dtype=float) + 1.0

        bar_j = mabd.volume_weighted_jacobian(tet_points, volumes)
        observed = mabd.volume_weighted_affine_force(tet_points, aggregated_force, volumes)
        expected = volumes[0] * np.vstack([mabd.point_jacobian(point) for point in tet_points[0]]).T @ aggregated_force

        self.assertEqual(bar_j.shape, (12, 12))
        self.assertTrue(np.allclose(observed, expected))
        self.assertTrue(np.allclose(observed, bar_j.T @ aggregated_force))

    def test_tetra_volume_and_mass_matrix_are_positive(self) -> None:
        rest_points = np.array(
            [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
        )
        masses = np.full(4, 0.25)

        volume = mabd.tetra_volume(rest_points)
        M = mabd.generalized_mass_matrix(rest_points, masses)
        eigvals = np.linalg.eigvalsh(M)

        self.assertAlmostEqual(volume, 1.0 / 6.0)
        self.assertTrue(np.allclose(M, M.T))
        self.assertGreater(float(eigvals.min()), 0.0)

    def test_lame_parameters_and_linear_elastic_gradient(self) -> None:
        young = 20.0
        poisson = 0.25
        mu, lam = mabd.lame_parameters(young, poisson)
        self.assertAlmostEqual(mu, 8.0)
        self.assertAlmostEqual(lam, 8.0)

        A = np.array([[1.02, 0.03, -0.01], [0.04, 0.97, 0.02], [0.01, -0.02, 1.05]])
        volume = 0.7
        grad = mabd.linear_elastic_gradient(A, young, poisson, volume)
        eps = 1.0e-6
        fd = np.zeros((3, 3))
        for i in range(3):
            for j in range(3):
                dA = np.zeros((3, 3))
                dA[i, j] = eps
                ep = mabd.linear_elastic_energy(A + dA, young, poisson, volume)
                em = mabd.linear_elastic_energy(A - dA, young, poisson, volume)
                fd[i, j] = (ep - em) / (2.0 * eps)

        self.assertTrue(np.allclose(grad, fd, atol=1.0e-7))

    def test_polar_and_no_polar_block_rotations_preserve_expected_norms(self) -> None:
        A = np.array([[1.1, 0.2, 0.0], [0.0, 0.9, -0.1], [0.05, 0.0, 1.2]])

        R = mabd.polar_rotation(A)
        self.assertTrue(np.allclose(R.T @ R, np.eye(3), atol=1.0e-12))
        self.assertGreater(np.linalg.det(R), 0.0)

        blocks = np.arange(12, dtype=float) + 1.0
        rhs = mabd.apply_no_polar_rhs_rotation(A, blocks)
        inc = mabd.apply_no_polar_increment_rotation(A, blocks)
        for block_id in range(4):
            original = blocks[3 * block_id : 3 * block_id + 3]
            rhs_block = rhs[3 * block_id : 3 * block_id + 3]
            inc_block = inc[3 * block_id : 3 * block_id + 3]
            self.assertAlmostEqual(float(np.linalg.norm(original)), float(np.linalg.norm(rhs_block)))
            self.assertAlmostEqual(float(np.linalg.norm(original)), float(np.linalg.norm(inc_block)))

    def test_twist_embedding_and_wrench_mapping_obey_virtual_work(self) -> None:
        theta = 0.35
        R = np.array(
            [
                [np.cos(theta), -np.sin(theta), 0.0],
                [np.sin(theta), np.cos(theta), 0.0],
                [0.0, 0.0, 1.0],
            ]
        )
        G = mabd.twist_map_G(R)
        E_paper = mabd.paper_rigid_embedding_E(R)
        E = mabd.rigid_embedding_E(R)

        self.assertTrue(np.allclose(E_paper, E, atol=1.0e-10))
        self.assertTrue(np.allclose(G @ E, np.eye(6), atol=1.0e-10))

        wrench = np.array([0.2, -0.4, 0.6, 1.0, 2.0, -1.5])
        dq = np.linspace(-0.3, 0.4, 12)
        fa = mabd.affine_force_from_wrench(R, wrench)

        self.assertAlmostEqual(float(fa @ dq), float(wrench @ (G @ dq)))

        A = np.diag([1.2, 0.9, 1.4])
        self.assertFalse(np.allclose(mabd.twist_map_G(A) @ mabd.paper_rigid_embedding_E(A), np.eye(6)))
        self.assertTrue(np.allclose(mabd.twist_map_G(A) @ mabd.rigid_embedding_E(A), np.eye(6), atol=1.0e-10))

    def test_hessian_cache_key_uses_dt_device_and_model_version(self) -> None:
        rest_points = np.array(
            [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
        )
        masses = np.full(4, 0.25)
        pre = mabd.SingleBodyABDPrecompute.from_points(
            rest_points,
            masses,
            stiffness_matrix=np.eye(12),
        )
        cache = mabd.SingleBodyABDHessianCache(pre)

        a = cache.factor(dt=0.01, device="cpu", model_version=0)
        b = cache.factor(dt=0.01, device="cpu", model_version=0)
        c = cache.factor(dt=0.02, device="cpu", model_version=0)
        d = cache.factor(dt=0.01, device="cuda:0", model_version=0)
        e = cache.factor(dt=0.01, device="cpu", model_version=1)

        self.assertIs(a, b)
        self.assertIsNot(a, c)
        self.assertIsNot(a, d)
        self.assertIsNot(a, e)
        self.assertTrue(np.allclose(a.solve(a.matrix @ np.ones(12)), np.ones(12)))

    def test_single_body_delta_applies_paper_no_polar_algorithm(self) -> None:
        rest_points = np.array(
            [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
        )
        masses = np.full(4, 0.25)
        pre = mabd.SingleBodyABDPrecompute.from_points(
            rest_points,
            masses,
            stiffness_matrix=2.0 * np.eye(12),
        )
        cache = mabd.SingleBodyABDHessianCache(pre)
        A = np.array([[1.1, 0.2, 0.0], [0.0, 0.9, -0.1], [0.05, 0.0, 1.2]])
        rhs = np.arange(12, dtype=float) + 1.0
        factor = cache.factor(dt=0.1, device="cpu", model_version=0)
        expected = mabd.apply_no_polar_increment_rotation(
            A,
            factor.solve(mabd.apply_no_polar_rhs_rotation(A, rhs)),
        )

        observed = mabd.solve_single_body_delta(
            pre,
            rhs,
            dt=0.1,
            A=A,
            rotation_mode="no_polar",
            cache=cache,
        )

        self.assertTrue(np.allclose(observed, expected))

    def test_solver_export_registers_custom_attributes_and_invalidates_cache(self) -> None:
        self.assertIs(newton.solvers.SolverMABD, SolverMABD)
        self.assertTrue(hasattr(newton.solvers, "mabd"))

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

    def test_solver_custom_frequency_rows_finalize_to_model_and_state(self) -> None:
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
    unittest.main()
