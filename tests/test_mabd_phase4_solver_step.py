from __future__ import annotations

import unittest

import numpy as np

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
    q = np.concatenate(
        [
            state.mabd.q0.numpy(),
            state.mabd.q1.numpy(),
            state.mabd.q2.numpy(),
            state.mabd.t.numpy(),
        ],
        axis=1,
    )
    qd = np.concatenate(
        [
            state.mabd.qd0.numpy(),
            state.mabd.qd1.numpy(),
            state.mabd.qd2.numpy(),
            state.mabd.td.numpy(),
        ],
        axis=1,
    )
    return q, qd


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


class MABDPhase4SolverStepTests(unittest.TestCase):
    def test_dense_cpu_step_matches_implicit_euler_single_body_force(self) -> None:
        q = np.array([1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.2, -0.1, 0.3], dtype=float)
        qd = np.linspace(-0.3, 0.4, 12)
        force = np.linspace(0.5, -0.25, 12)
        dt = 0.05

        result = mabd.solve_cpu_oracle_step(
            q=[q],
            qd=[qd],
            dt=dt,
            config=mabd.MABDCPUOracleConfig(bodies=[_body()], external_forces=[force]),
        )

        self.assertEqual(result.topology, "unconstrained")
        self.assertTrue(np.allclose(result.q[0], q + dt * qd + dt * dt * force, atol=1.0e-12))
        self.assertTrue(np.allclose(result.qd[0], qd + dt * force, atol=1.0e-12))
        self.assertEqual(result.dlambda.shape, (0,))

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

        result = mabd.solve_cpu_oracle_step(
            q=[q],
            qd=[qd],
            dt=dt,
            config=mabd.MABDCPUOracleConfig(
                bodies=[body],
                external_forces=[force],
            ),
        )

        expected_dq = mabd.solve_single_body_delta(
            body.precompute,
            rhs,
            dt,
            A=A,
            rotation_mode="no_polar",
        )
        none_dq = np.linalg.solve(body.precompute.hessian(dt), rhs)
        self.assertTrue(np.allclose(result.q[0], q + expected_dq, atol=1.0e-12))
        self.assertTrue(np.allclose(result.qd[0], expected_dq / dt, atol=1.0e-12))
        self.assertGreater(float(np.linalg.norm(expected_dq - none_dq)), 1.0e-6)

    def test_constrained_cpu_step_rejects_no_polar_until_rotated_kkt_exists(self) -> None:
        config = mabd.MABDCPUOracleConfig(
            bodies=[_body(rotation_mode="no_polar"), _body()],
            constraints=[
                mabd.MABDCPUOracleConstraint(
                    body_a=0,
                    body_b=1,
                    spec=mabd.ball_joint(HINGE_CT, HINGE_CT),
                )
            ],
            topology="dense",
        )

        with self.assertRaisesRegex(NotImplementedError, "constrained.*rotation_mode='none'"):
            mabd.solve_cpu_oracle_step(
                q=[_identity_q((0.2, 0.0, 0.0)), _identity_q()],
                qd=[np.zeros(12), np.zeros(12)],
                dt=0.1,
                config=config,
            )

    def test_dense_cpu_step_accepts_point_contact_generalized_force(self) -> None:
        q = mabd.pack_q(np.eye(3), np.array([0.0, -0.05, 0.0]))
        qd = np.zeros(12)
        dt = 0.1
        contact = mabd.evaluate_point_plane_penalty_contact(
            q,
            qd,
            np.zeros(3),
            plane_normal=np.array([0.0, 1.0, 0.0]),
            plane_offset=0.0,
            stiffness=20.0,
        )

        result = mabd.solve_cpu_oracle_step(
            q=[q],
            qd=[qd],
            dt=dt,
            config=mabd.MABDCPUOracleConfig(bodies=[_body()], external_forces=[contact.generalized_force]),
        )

        self.assertTrue(contact.active)
        self.assertAlmostEqual(float(contact.force[1]), 1.0)
        self.assertTrue(np.allclose(result.q[0], q + dt * dt * contact.generalized_force, atol=1.0e-12))

    def test_dense_cpu_step_adds_actuation_forces_to_external_forces(self) -> None:
        q = _identity_q((0.2, -0.1, 0.3))
        qd = np.zeros(12)
        dt = 0.1
        external_force = np.full(12, 0.25)
        target_q = q.copy()
        target_q[9:12] += np.array([0.5, 0.0, -0.25])
        feedforward = np.zeros(12)
        feedforward[11] = -0.1

        result = mabd.solve_cpu_oracle_step(
            q=[q],
            qd=[qd],
            dt=dt,
            config=mabd.MABDCPUOracleConfig(
                bodies=[_body()],
                external_forces=[external_force],
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
        expected_force[9] += 1.0
        expected_force[11] += -0.5 - 0.1
        self.assertTrue(np.allclose(result.q[0], q + dt * dt * expected_force, atol=1.0e-12))

    def test_dense_cpu_step_enforces_ball_joint_residual_correction(self) -> None:
        q_a = _identity_q((0.2, 0.0, 0.0))
        q_b = _identity_q()
        dt = 0.1
        config = mabd.MABDCPUOracleConfig(
            bodies=[_body(), _body()],
            constraints=[
                mabd.MABDCPUOracleConstraint(
                    body_a=0,
                    body_b=1,
                    spec=mabd.ball_joint(HINGE_CT, HINGE_CT),
                )
            ],
            topology="dense",
        )

        result = mabd.solve_cpu_oracle_step(
            q=[q_a, q_b],
            qd=[np.zeros(12), np.zeros(12)],
            dt=dt,
            config=config,
        )

        residual = mabd.joint_residual(config.constraints[0].spec, result.q[0], result.q[1])
        self.assertLess(result.constraint_residual_norm, 1.0e-10)
        self.assertTrue(np.allclose(residual, np.zeros(3), atol=1.0e-10))
        self.assertTrue(np.allclose(result.q[0][9:12], [0.1, 0.0, 0.0], atol=1.0e-10))
        self.assertTrue(np.allclose(result.q[1][9:12], [0.1, 0.0, 0.0], atol=1.0e-10))

    def test_auto_general_graph_requires_explicit_schedule_or_dense_topology(self) -> None:
        constraints = [
            mabd.MABDCPUOracleConstraint(body_a=a, body_b=b, spec=mabd.ball_joint(HINGE_CT, HINGE_CT))
            for a, b in ((0, 1), (1, 2), (2, 3), (3, 0), (0, 2))
        ]

        with self.assertRaisesRegex(ValueError, "topology='auto'.*graph_schedule"):
            mabd.solve_cpu_oracle_step(
                q=[_identity_q() for _ in range(4)],
                qd=[np.zeros(12) for _ in range(4)],
                dt=0.05,
                config=mabd.MABDCPUOracleConfig(
                    bodies=[_body() for _ in range(4)],
                    constraints=constraints,
                    topology="auto",
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
        self.assertIsNotNone(solver.last_step_result)

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
        expected_q = q + dt * qd + dt * dt * np.asarray(forces)
        expected_qd = qd + dt * np.asarray(forces)
        self.assertTrue(np.allclose(q_next, expected_q, atol=1.0e-7))
        self.assertTrue(np.allclose(qd_next, expected_qd, atol=1.0e-7))

    def test_solver_step_requires_cpu_oracle_configuration(self) -> None:
        model = _mabd_model()
        solver = SolverMABD(model)

        with self.assertRaisesRegex(NotImplementedError, "configure_cpu_oracle"):
            solver.step(model.state(), model.state(), None, None, 0.01)

    def test_solver_step_rejects_newton_control_input(self) -> None:
        model = _mabd_model()
        solver = SolverMABD(model)
        solver.configure_cpu_oracle(mabd.MABDCPUOracleConfig(bodies=[_body()]))

        with self.assertRaisesRegex(NotImplementedError, "Control input"):
            solver.step(model.state(), model.state(), model.control(), None, 0.01)


if __name__ == "__main__":
    unittest.main()
