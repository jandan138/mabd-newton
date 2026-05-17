from __future__ import annotations

import unittest

import numpy as np

import newton
from newton._src.solvers import mabd
from newton.solvers import SolverMABD

HINGE_CT = np.array(
    [
        [0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0],
        [1.0, 0.0, 0.0],
    ],
    dtype=float,
)


def _body(rotation_mode: str = "none") -> object:
    return mabd.MABDCPUOracleBody(
        precompute=mabd.SingleBodyABDPrecompute(
            rest_points=np.zeros((4, 3), dtype=float),
            masses=np.ones(4, dtype=float),
            mass_matrix=np.eye(12),
            stiffness_matrix=np.zeros((12, 12), dtype=float),
        ),
        rotation_mode=rotation_mode,
    )


def _body_with_stiffness(
    stiffness: np.ndarray,
    rest_q: np.ndarray,
    rotation_mode: str = "none",
) -> object:
    return mabd.MABDCPUOracleBody(
        precompute=mabd.SingleBodyABDPrecompute(
            rest_points=np.zeros((4, 3), dtype=float),
            masses=np.ones(4, dtype=float),
            mass_matrix=np.eye(12),
            stiffness_matrix=stiffness,
        ),
        rest_q=rest_q,
        rotation_mode=rotation_mode,
    )


def _identity_q(translation: tuple[float, float, float] = (0.0, 0.0, 0.0)) -> np.ndarray:
    return mabd.pack_q(np.eye(3), np.array(translation, dtype=float))


def _no_polar_affine_only_rhs(A: np.ndarray, rhs: np.ndarray) -> np.ndarray:
    affine_rhs = np.zeros(12, dtype=float)
    affine_rhs[:9] = rhs[:9]
    rotated = rhs.copy()
    rotated[:9] = mabd.apply_no_polar_rhs_rotation(A, affine_rhs)[:9]
    return rotated


def _no_polar_affine_only_increment(A: np.ndarray, delta: np.ndarray) -> np.ndarray:
    affine_delta = np.zeros(12, dtype=float)
    affine_delta[:9] = delta[:9]
    rotated = delta.copy()
    rotated[:9] = mabd.apply_no_polar_increment_rotation(A, affine_delta)[:9]
    return rotated


def _assign_mabd_state(state: object, q: np.ndarray | list[np.ndarray], qd: np.ndarray | list[np.ndarray]) -> None:
    q_arr = np.asarray([q], dtype=float) if np.asarray(q).shape == (12,) else np.asarray(q, dtype=float)
    qd_arr = np.asarray([qd], dtype=float) if np.asarray(qd).shape == (12,) else np.asarray(qd, dtype=float)
    state.mabd.q0.assign(np.asarray(q_arr[:, 0:3], dtype=np.float32))
    state.mabd.q1.assign(np.asarray(q_arr[:, 3:6], dtype=np.float32))
    state.mabd.q2.assign(np.asarray(q_arr[:, 6:9], dtype=np.float32))
    state.mabd.t.assign(np.asarray(q_arr[:, 9:12], dtype=np.float32))
    state.mabd.qd0.assign(np.asarray(qd_arr[:, 0:3], dtype=np.float32))
    state.mabd.qd1.assign(np.asarray(qd_arr[:, 3:6], dtype=np.float32))
    state.mabd.qd2.assign(np.asarray(qd_arr[:, 6:9], dtype=np.float32))
    state.mabd.td.assign(np.asarray(qd_arr[:, 9:12], dtype=np.float32))


def _read_mabd_state(state: object) -> tuple[np.ndarray, np.ndarray]:
    return (
        np.concatenate([state.mabd.q0.numpy(), state.mabd.q1.numpy(), state.mabd.q2.numpy(), state.mabd.t.numpy()], axis=1),
        np.concatenate([state.mabd.qd0.numpy(), state.mabd.qd1.numpy(), state.mabd.qd2.numpy(), state.mabd.td.numpy()], axis=1),
    )


def _mabd_model(body_count: int = 1) -> object:
    builder = newton.ModelBuilder()
    SolverMABD.register_custom_attributes(builder)
    for _ in range(body_count):
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
    return builder.finalize()


class MABDPhase4InternalTests(unittest.TestCase):
    def test_dense_cpu_step_matches_implicit_euler_single_body_force(self) -> None:
        q = _identity_q((0.2, -0.1, 0.3))
        qd = np.linspace(-0.3, 0.4, 12)
        force = np.linspace(0.5, -0.25, 12)
        dt = 0.05

        result = mabd.solve_cpu_oracle_step(
            q=[q],
            qd=[qd],
            dt=dt,
            config=mabd.MABDCPUOracleConfig(bodies=[_body()], external_forces=[force]),
        )

        self.assertTrue(np.allclose(result.q[0], q + dt * qd + dt * dt * force, atol=1.0e-12))
        self.assertTrue(np.allclose(result.qd[0], qd + dt * force, atol=1.0e-12))

    def test_dense_cpu_step_includes_rest_stiffness_rhs_sign(self) -> None:
        q = _identity_q((0.2, -0.1, 0.3)) + np.linspace(-0.04, 0.05, 12)
        qd = np.linspace(-0.2, 0.15, 12)
        rest_q = _identity_q((0.05, 0.02, -0.03))
        stiffness = np.diag(np.linspace(0.4, 1.5, 12))
        force = np.linspace(0.1, -0.25, 12)
        dt = 0.08
        H = np.eye(12) / (dt * dt) + stiffness
        rhs = qd / dt + force - stiffness @ (q - rest_q)

        result = mabd.solve_cpu_oracle_step(
            q=[q],
            qd=[qd],
            dt=dt,
            config=mabd.MABDCPUOracleConfig(
                bodies=[_body_with_stiffness(stiffness, rest_q)],
                external_forces=[force],
            ),
        )

        expected_dq = np.linalg.solve(H, rhs)
        self.assertTrue(np.allclose(result.q[0], q + expected_dq, atol=1.0e-12))
        self.assertTrue(np.allclose(result.qd[0], expected_dq / dt, atol=1.0e-12))

    def test_unconstrained_cpu_step_adds_uniform_gravity_generalized_force(self) -> None:
        rest_points = np.array(
            [
                [-0.5, -0.5, -0.5],
                [0.5, -0.5, 0.5],
                [-0.5, 0.5, 0.5],
                [0.5, 0.5, -0.5],
            ],
            dtype=float,
        )
        masses = np.array([0.2, 0.3, 0.4, 0.5], dtype=float)
        stiffness = 0.25 * np.eye(12)
        body = mabd.MABDCPUOracleBody(
            precompute=mabd.SingleBodyABDPrecompute.from_points(
                rest_points,
                masses,
                stiffness_matrix=stiffness,
            ),
            rest_q=_identity_q(),
        )
        q = _identity_q((0.1, 0.2, -0.3)) + np.linspace(-0.02, 0.03, 12)
        qd = np.linspace(0.05, -0.04, 12)
        gravity = np.array([0.0, -9.81, 1.25], dtype=float)
        dt = 0.02

        result = mabd.solve_cpu_oracle_step(
            q=[q],
            qd=[qd],
            dt=dt,
            config=mabd.MABDCPUOracleConfig(
                bodies=[body],
                gravity=gravity,
            ),
        )

        H = body.precompute.hessian(dt)
        gravity_force = mabd.gravity_generalized_force(rest_points, masses, gravity)
        rhs = (body.precompute.mass_matrix @ qd) / dt
        rhs += gravity_force - stiffness @ (q - _identity_q())
        expected_dq = np.linalg.solve(H, rhs)
        self.assertTrue(np.allclose(result.dq, expected_dq, atol=1.0e-12))
        self.assertTrue(np.allclose(result.q[0], q + expected_dq, atol=1.0e-12))
        self.assertTrue(np.allclose(result.qd[0], expected_dq / dt, atol=1.0e-12))

    def test_cpu_oracle_rejects_bad_gravity_vector_shape(self) -> None:
        with self.assertRaisesRegex(ValueError, "gravity"):
            mabd.solve_cpu_oracle_step(
                q=[_identity_q()],
                qd=[np.zeros(12)],
                dt=0.01,
                config=mabd.MABDCPUOracleConfig(
                    bodies=[_body()],
                    gravity=np.array([0.0, -9.81]),
                ),
            )

    def test_cpu_step_combines_external_gravity_and_actuation_forces(self) -> None:
        q = _identity_q((0.2, -0.1, 0.3))
        qd = np.zeros(12)
        dt = 0.1
        body = _body()
        external_force = np.full(12, 0.25)
        gravity = np.array([0.1, -0.2, 0.3], dtype=float)
        target_q = q.copy()
        target_q[9:12] += np.array([0.5, 0.0, -0.25])
        feedforward = np.zeros(12)
        feedforward[11] = -0.1

        result = mabd.solve_cpu_oracle_step(
            q=[q],
            qd=[qd],
            dt=dt,
            config=mabd.MABDCPUOracleConfig(
                bodies=[body],
                external_forces=[external_force],
                gravity=gravity,
                actuations=[
                    mabd.MABDActuationSpec(
                        body_id=0,
                        target_q=target_q,
                        stiffness=2.0,
                        feedforward_force=feedforward,
                    )
                ],
            ),
        )

        expected_force = external_force.copy()
        expected_force += mabd.gravity_generalized_force(
            body.precompute.rest_points,
            body.precompute.masses,
            gravity,
        )
        expected_force[9] += 1.0
        expected_force[11] += -0.5 - 0.1
        self.assertTrue(np.allclose(result.q[0], q + dt * dt * expected_force, atol=1.0e-12))

    def test_unconstrained_cpu_step_applies_no_polar_body_rotation(self) -> None:
        A = np.array([[1.1, 0.2, 0.0], [0.0, 0.9, -0.1], [0.05, 0.0, 1.2]])
        q = mabd.pack_q(A, np.array([0.2, -0.1, 0.3]))
        qd = np.linspace(-0.2, 0.25, 12)
        rest_q = _identity_q((0.05, 0.02, -0.03))
        stiffness = mabd.rest_generalized_stiffness_matrix(80.0, 0.25, 0.35)
        force = np.linspace(0.1, -0.25, 12)
        dt = 0.04
        body = _body_with_stiffness(stiffness, rest_q, rotation_mode="no_polar")
        rhs = qd / dt + force - stiffness @ (q - rest_q)
        local_rhs = _no_polar_affine_only_rhs(A, rhs)

        result = mabd.solve_cpu_oracle_step(
            q=[q],
            qd=[qd],
            dt=dt,
            config=mabd.MABDCPUOracleConfig(
                bodies=[body],
                external_forces=[force],
            ),
        )

        local_delta = np.linalg.solve(body.precompute.hessian(dt), local_rhs)
        expected_dq = _no_polar_affine_only_increment(A, local_delta)
        none_dq = np.linalg.solve(body.precompute.hessian(dt), rhs)
        self.assertTrue(np.allclose(result.q[0], q + expected_dq, atol=1.0e-12))
        self.assertTrue(np.allclose(result.qd[0], expected_dq / dt, atol=1.0e-12))
        self.assertLess(result.residual_norm, 1.0e-10)
        self.assertGreater(float(np.linalg.norm(expected_dq - none_dq)), 1.0e-6)

    def test_no_polar_cpu_step_preserves_free_translation_in_world_frame(self) -> None:
        A = np.array([[1.1, 0.2, 0.0], [0.0, 0.9, -0.1], [0.05, 0.0, 1.2]])
        q = mabd.pack_q(A, np.array([0.2, -0.1, 0.3]))
        qd = np.zeros(12)
        qd[9:12] = np.array([1.0, 2.0, 3.0])
        dt = 0.04

        result = mabd.solve_cpu_oracle_step(
            q=[q],
            qd=[qd],
            dt=dt,
            config=mabd.MABDCPUOracleConfig(bodies=[_body(rotation_mode="no_polar")]),
        )

        self.assertTrue(np.allclose(result.qd[0][9:12], qd[9:12], atol=1.0e-12))
        self.assertTrue(np.allclose(result.q[0][9:12], q[9:12] + dt * qd[9:12], atol=1.0e-12))
        self.assertLess(result.residual_norm, 1.0e-12)

    def test_polar_cpu_step_treats_pure_rotation_as_zero_material_strain(self) -> None:
        theta = 0.43
        R = np.array(
            [
                [np.cos(theta), -np.sin(theta), 0.0],
                [np.sin(theta), np.cos(theta), 0.0],
                [0.0, 0.0, 1.0],
            ],
            dtype=float,
        )
        q = mabd.pack_q(R, np.array([0.2, -0.1, 0.3]))
        rest_q = _identity_q((0.2, -0.1, 0.3))
        stiffness = mabd.rest_generalized_stiffness_matrix(80.0, 0.25, 0.35)
        dt = 0.04

        result = mabd.solve_cpu_oracle_step(
            q=[q],
            qd=[np.zeros(12)],
            dt=dt,
            config=mabd.MABDCPUOracleConfig(
                bodies=[_body_with_stiffness(stiffness, rest_q, rotation_mode="polar")]
            ),
        )

        self.assertTrue(np.allclose(result.q[0], q, atol=1.0e-12))
        self.assertTrue(np.allclose(result.qd[0], np.zeros(12), atol=1.0e-12))
        self.assertLess(result.residual_norm, 1.0e-12)

    def test_polar_cpu_step_matches_corotated_material_force_for_small_deformation(self) -> None:
        theta = 0.2
        R = np.array(
            [
                [np.cos(theta), -np.sin(theta), 0.0],
                [np.sin(theta), np.cos(theta), 0.0],
                [0.0, 0.0, 1.0],
            ],
            dtype=float,
        )
        stretch = np.diag([1.02, 0.99, 1.01])
        A = R @ stretch
        q = mabd.pack_q(A, np.array([0.2, -0.1, 0.3]))
        rest_q = _identity_q((0.2, -0.1, 0.3))
        young = 80.0
        poisson = 0.25
        volume = 0.35
        stiffness = mabd.rest_generalized_stiffness_matrix(young, poisson, volume)
        dt = 0.04

        result = mabd.solve_cpu_oracle_step(
            q=[q],
            qd=[np.zeros(12)],
            dt=dt,
            config=mabd.MABDCPUOracleConfig(
                bodies=[_body_with_stiffness(stiffness, rest_q, rotation_mode="polar")]
            ),
        )

        material_force = mabd.co_rotated_linear_elastic_affine_force(A, young, poisson, volume)
        expected_dq = np.linalg.solve(
            np.eye(12) / (dt * dt) + stiffness,
            mabd.apply_polar_rhs_rotation(A, material_force),
        )
        expected_q = q + mabd.apply_polar_increment_rotation(A, expected_dq)
        self.assertTrue(np.allclose(result.q[0], expected_q, atol=1.0e-10))
        self.assertLess(result.residual_norm, 1.0e-10)

    def test_polar_cpu_step_preserves_free_translation_under_rigid_rotation(self) -> None:
        theta = -0.37
        R = np.array(
            [
                [np.cos(theta), 0.0, np.sin(theta)],
                [0.0, 1.0, 0.0],
                [-np.sin(theta), 0.0, np.cos(theta)],
            ],
            dtype=float,
        )
        q = mabd.pack_q(R, np.array([0.2, -0.1, 0.3]))
        qd = np.zeros(12)
        qd[9:12] = np.array([1.0, 2.0, 3.0])
        dt = 0.04

        result = mabd.solve_cpu_oracle_step(
            q=[q],
            qd=[qd],
            dt=dt,
            config=mabd.MABDCPUOracleConfig(bodies=[_body(rotation_mode="polar")]),
        )

        self.assertTrue(np.allclose(result.qd[0][9:12], qd[9:12], atol=1.0e-12))
        self.assertTrue(np.allclose(result.q[0][9:12], q[9:12] + dt * qd[9:12], atol=1.0e-12))

    def test_constrained_cpu_step_supports_polar_world_anchor(self) -> None:
        theta = 0.31
        R = np.array(
            [
                [np.cos(theta), -np.sin(theta), 0.0],
                [np.sin(theta), np.cos(theta), 0.0],
                [0.0, 0.0, 1.0],
            ],
            dtype=float,
        )
        q = mabd.pack_q(R, np.array([0.2, -0.1, 0.05]))
        rest_point = np.array([0.4, -0.2, 0.1], dtype=float)
        world_point = mabd.point_jacobian(rest_point) @ q
        world_point += np.array([0.03, -0.02, 0.01], dtype=float)

        result = mabd.solve_cpu_oracle_step(
            q=[q],
            qd=[np.zeros(12)],
            dt=0.05,
            config=mabd.MABDCPUOracleConfig(
                bodies=[_body(rotation_mode="polar")],
                world_constraints=[
                    mabd.MABDCPUOracleWorldConstraint(
                        body=0,
                        rest_point=rest_point,
                        world_point=world_point,
                    )
                ],
                topology="dense",
            ),
        )

        pinned = mabd.point_jacobian(rest_point) @ result.q[0]
        self.assertLess(result.constraint_residual_norm, 1.0e-10)
        self.assertTrue(np.allclose(pinned, world_point, atol=1.0e-10))
        self.assertEqual(result.topology, "dense")

    def test_constrained_cpu_step_rejects_no_polar_because_map_is_nonlinear(self) -> None:
        stretch_shear = np.array(
            [
                [1.05, 0.08, 0.0],
                [0.0, 0.97, 0.03],
                [0.0, 0.0, 1.02],
            ],
            dtype=float,
        )
        config = mabd.MABDCPUOracleConfig(
            bodies=[_body(rotation_mode="no_polar"), _body(rotation_mode="polar")],
            constraints=[
                mabd.MABDCPUOracleConstraint(
                    body_a=0,
                    body_b=1,
                    spec=mabd.ball_joint(HINGE_CT, HINGE_CT),
                )
            ],
            topology="dense",
        )

        with self.assertRaisesRegex(NotImplementedError, "constrained.*no_polar"):
            mabd.solve_cpu_oracle_step(
                q=[mabd.pack_q(stretch_shear, np.array([0.2, 0.0, 0.0])), _identity_q()],
                qd=[np.zeros(12), np.zeros(12)],
                dt=0.1,
                config=config,
            )

    def test_constrained_cpu_step_rejects_polar_non_dense_topology_until_tested(self) -> None:
        config = mabd.MABDCPUOracleConfig(
            bodies=[_body(rotation_mode="polar"), _body()],
            constraints=[
                mabd.MABDCPUOracleConstraint(
                    body_a=0,
                    body_b=1,
                    spec=mabd.ball_joint(HINGE_CT, HINGE_CT),
                )
            ],
            topology="chain",
        )

        with self.assertRaisesRegex(NotImplementedError, "rotated.*topology='dense'"):
            mabd.solve_cpu_oracle_step(
                q=[_identity_q((0.2, 0.0, 0.0)), _identity_q()],
                qd=[np.zeros(12), np.zeros(12)],
                dt=0.1,
                config=config,
            )

    def test_dense_cpu_step_enforces_world_anchor_residual_correction(self) -> None:
        q = _identity_q((0.2, -0.1, 0.05))
        dt = 0.1
        rest_point = np.zeros(3, dtype=float)
        world_point = np.zeros(3, dtype=float)
        config = mabd.MABDCPUOracleConfig(
            bodies=[_body()],
            world_constraints=[
                mabd.MABDCPUOracleWorldConstraint(
                    body=0,
                    rest_point=rest_point,
                    world_point=world_point,
                )
            ],
            topology="dense",
        )

        result = mabd.solve_cpu_oracle_step(
            q=[q],
            qd=[np.zeros(12)],
            dt=dt,
            config=config,
        )

        pinned = mabd.point_jacobian(rest_point) @ result.q[0]
        self.assertLess(result.constraint_residual_norm, 1.0e-10)
        self.assertTrue(np.allclose(pinned, world_point, atol=1.0e-10))

    def test_dense_cpu_step_enforces_nonzero_world_anchor_affine_residual_correction(self) -> None:
        A = np.array([[1.2, 0.1, -0.05], [0.0, 0.9, 0.2], [0.08, -0.03, 1.1]], dtype=float)
        q = mabd.pack_q(A, np.array([0.2, -0.1, 0.05], dtype=float))
        dt = 0.1
        rest_point = np.array([1.0, -0.5, 0.25], dtype=float)
        world_point = np.array([-0.15, 0.35, 0.5], dtype=float)
        config = mabd.MABDCPUOracleConfig(
            bodies=[_body()],
            world_constraints=[
                mabd.MABDCPUOracleWorldConstraint(
                    body=0,
                    rest_point=rest_point,
                    world_point=world_point,
                )
            ],
            topology="dense",
        )

        result = mabd.solve_cpu_oracle_step(
            q=[q],
            qd=[np.zeros(12)],
            dt=dt,
            config=config,
        )

        pinned = mabd.point_jacobian(rest_point) @ result.q[0]
        self.assertLess(result.constraint_residual_norm, 1.0e-10)
        self.assertGreater(float(np.linalg.norm(result.q[0][:9] - q[:9])), 1.0e-6)
        self.assertTrue(np.allclose(pinned, world_point, atol=1.0e-10))

    def test_world_anchor_constraints_require_dense_topology(self) -> None:
        config = mabd.MABDCPUOracleConfig(
            bodies=[_body()],
            world_constraints=[
                mabd.MABDCPUOracleWorldConstraint(
                    body=0,
                    rest_point=np.zeros(3),
                    world_point=np.zeros(3),
                )
            ],
            topology="chain",
        )

        with self.assertRaisesRegex(ValueError, "world.*dense"):
            mabd.solve_cpu_oracle_step(
                q=[_identity_q((0.2, 0.0, 0.0))],
                qd=[np.zeros(12)],
                dt=0.1,
                config=config,
            )

    def test_world_anchor_constraint_rejects_bad_vector_shapes(self) -> None:
        with self.assertRaisesRegex(ValueError, "rest_point"):
            mabd.solve_cpu_oracle_step(
                q=[_identity_q()],
                qd=[np.zeros(12)],
                dt=0.1,
                config=mabd.MABDCPUOracleConfig(
                    bodies=[_body()],
                    world_constraints=[
                        mabd.MABDCPUOracleWorldConstraint(
                            body=0,
                            rest_point=np.zeros(2),
                            world_point=np.zeros(3),
                        )
                    ],
                    topology="dense",
                ),
            )

    def test_solver_step_writes_custom_state_when_cpu_oracle_configured(self) -> None:
        model = _mabd_model()
        solver = SolverMABD(model)
        q = _identity_q((0.2, -0.1, 0.3))
        qd = np.linspace(-0.2, 0.25, 12)
        force = np.linspace(0.3, -0.15, 12)
        dt = 0.02
        state_in = model.state()
        state_out = model.state()
        _assign_mabd_state(state_in, q, qd)
        solver.configure_cpu_oracle(mabd.MABDCPUOracleConfig(bodies=[_body()], external_forces=[force]))

        solver.step(state_in, state_out, None, None, dt)

        q_next, qd_next = _read_mabd_state(state_out)
        self.assertTrue(np.allclose(q_next[0], q + dt * qd + dt * dt * force, atol=1.0e-7))
        self.assertTrue(np.allclose(qd_next[0], qd + dt * force, atol=1.0e-7))

    def test_solver_step_supports_in_place_multi_body_custom_state(self) -> None:
        model = _mabd_model(body_count=2)
        solver = SolverMABD(model)
        q = np.asarray([_identity_q((0.2, -0.1, 0.3)), _identity_q((-0.4, 0.2, 0.1))], dtype=float)
        qd = np.asarray([np.linspace(-0.2, 0.25, 12), np.linspace(0.1, -0.15, 12)], dtype=float)
        forces = [np.linspace(0.3, -0.15, 12), np.linspace(-0.2, 0.1, 12)]
        dt = 0.02
        state = model.state()
        _assign_mabd_state(state, q, qd)
        solver.configure_cpu_oracle(mabd.MABDCPUOracleConfig(bodies=[_body(), _body()], external_forces=forces))

        solver.step(state, state, None, None, dt)

        q_next, qd_next = _read_mabd_state(state)
        self.assertTrue(np.allclose(q_next, q + dt * qd + dt * dt * np.asarray(forces), atol=1.0e-7))
        self.assertTrue(np.allclose(qd_next, qd + dt * np.asarray(forces), atol=1.0e-7))


if __name__ == "__main__":
    unittest.main()
