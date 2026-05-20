from __future__ import annotations

import unittest

import numpy as np
import warp as wp

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


def _add_model_body_row(
    builder: newton.ModelBuilder,
    *,
    young_modulus: float = 1.0,
    poisson_ratio: float = 0.25,
    density: float = 1.0,
    polar_mode: int = 0,
) -> int:
    body_id = builder.add_body()
    builder.add_custom_values(
        **{
            "mabd:body_index": body_id,
            "mabd:young_modulus": young_modulus,
            "mabd:poisson_ratio": poisson_ratio,
            "mabd:density": density,
            "mabd:polar_mode": polar_mode,
            "mabd:rest_point0": wp.vec3(0.0, 0.0, 0.0),
            "mabd:rest_point1": wp.vec3(1.0, 0.0, 0.0),
            "mabd:rest_point2": wp.vec3(0.0, 1.0, 0.0),
            "mabd:rest_point3": wp.vec3(0.0, 0.0, 1.0),
            "mabd:point_mass0": -1.0,
            "mabd:point_mass1": -1.0,
            "mabd:point_mass2": -1.0,
            "mabd:point_mass3": -1.0,
            "mabd:volume": -1.0,
        }
    )
    return body_id


def _model_path_body(
    *,
    young_modulus: float = 1.0,
    poisson_ratio: float = 0.25,
    density: float = 1.0,
    rotation_mode: str = "none",
) -> object:
    rest_points = np.array(
        [
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
        ],
        dtype=float,
    )
    volume = mabd.tetra_volume(rest_points)
    masses = np.full(4, density * volume / 4.0, dtype=float)
    return mabd.MABDCPUOracleBody(
        precompute=mabd.SingleBodyABDPrecompute.from_linear_elastic_points(
            rest_points,
            masses,
            young_modulus=young_modulus,
            poisson_ratio=poisson_ratio,
            volume=volume,
        ),
        rest_q=_identity_q(),
        rotation_mode=rotation_mode,
    )


def _add_model_plane_constraint_row(
    builder: newton.ModelBuilder,
    *,
    body: int,
    rest_point: tuple[float, float, float],
    plane_normal: tuple[float, float, float] = (0.0, 1.0, 0.0),
    plane_offset: float = 0.0,
    active: int = 1,
) -> None:
    builder.add_custom_values(
        **{
            "mabd:plane_body": body,
            "mabd:plane_rest_point": wp.vec3(*rest_point),
            "mabd:plane_normal": wp.vec3(*plane_normal),
            "mabd:plane_offset": plane_offset,
            "mabd:plane_active": active,
        }
    )


def _mabd_model_with_box_and_static_plane() -> tuple[object, int, int]:
    builder = newton.ModelBuilder()
    SolverMABD.register_custom_attributes(builder)
    mabd_body = _add_model_body_row(builder, young_modulus=1.0)
    box_shape = builder.add_shape_box(body=mabd_body, hx=0.5, hy=0.5, hz=0.5)
    plane_shape = builder.add_shape_plane(plane=(0.0, 1.0, 0.0, 0.0), width=0.0, length=0.0)
    return builder.finalize(), box_shape, plane_shape


def _mabd_model_with_cylinder_and_static_plane() -> tuple[object, int, int]:
    builder = newton.ModelBuilder()
    SolverMABD.register_custom_attributes(builder)
    mabd_body = _add_model_body_row(builder, young_modulus=1.0)
    cylinder_shape = builder.add_shape_cylinder(
        body=mabd_body,
        radius=0.5,
        half_height=0.5,
    )
    plane_shape = builder.add_shape_plane(plane=(0.0, 1.0, 0.0, 0.0), width=0.0, length=0.0)
    return builder.finalize(), cylinder_shape, plane_shape


def _mabd_model_with_box_and_dynamic_rigid_box() -> tuple[object, int, int]:
    builder = newton.ModelBuilder()
    SolverMABD.register_custom_attributes(builder)
    mabd_body = _add_model_body_row(builder, young_modulus=1.0)
    mabd_shape = builder.add_shape_box(body=mabd_body, hx=0.5, hy=0.5, hz=0.5)
    rigid_body = builder.add_body()
    rigid_shape = builder.add_shape_box(body=rigid_body, hx=0.25, hy=0.25, hz=0.25)
    return builder.finalize(), mabd_shape, rigid_shape


def _contacts_with_rigid_rows(
    rows: list[
        tuple[
            int,
            int,
            tuple[float, float, float],
            tuple[float, float, float],
            tuple[float, float, float],
        ]
    ],
    *,
    capacity: int | None = None,
    reported_count: int | None = None,
) -> object:
    capacity = max(len(rows), 1) if capacity is None else capacity
    reported_count = len(rows) if reported_count is None else reported_count
    contacts = newton.Contacts(rigid_contact_max=capacity, soft_contact_max=0)
    contacts.rigid_contact_count.assign(np.array([reported_count], dtype=np.int32))
    shape0_values = np.full(capacity, -1, dtype=np.int32)
    shape1_values = np.full(capacity, -1, dtype=np.int32)
    point0_values = np.zeros((capacity, 3), dtype=np.float32)
    point1_values = np.zeros((capacity, 3), dtype=np.float32)
    normal_values = np.zeros((capacity, 3), dtype=np.float32)
    for index, (shape0, shape1, point0, point1, normal) in enumerate(rows[:capacity]):
        shape0_values[index] = shape0
        shape1_values[index] = shape1
        point0_values[index] = np.asarray(point0, dtype=np.float32)
        point1_values[index] = np.asarray(point1, dtype=np.float32)
        normal_values[index] = np.asarray(normal, dtype=np.float32)
    contacts.rigid_contact_shape0.assign(shape0_values)
    contacts.rigid_contact_shape1.assign(shape1_values)
    contacts.rigid_contact_point0.assign(point0_values)
    contacts.rigid_contact_point1.assign(point1_values)
    contacts.rigid_contact_normal.assign(normal_values)
    return contacts


def _contacts_with_one_rigid_row(
    *,
    shape0: int,
    shape1: int,
    point0: tuple[float, float, float],
    point1: tuple[float, float, float],
    normal: tuple[float, float, float],
    capacity: int = 4,
    reported_count: int = 1,
) -> object:
    return _contacts_with_rigid_rows(
        [(shape0, shape1, point0, point1, normal)],
        capacity=capacity,
        reported_count=reported_count,
    )


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

    def test_dense_cpu_step_plane_constraint_preserves_tangent_motion(self) -> None:
        q = _identity_q((0.2, -0.3, 0.1))
        qd = np.zeros(12)
        qd[9:12] = np.array([2.0, 3.0, -1.0])
        dt = 0.05
        rest_point = np.array([0.3, -0.2, 0.1])
        normal = np.array([0.0, 2.0, 2.0])
        normal_norm = float(np.linalg.norm(normal))
        free = mabd.solve_cpu_oracle_step(
            q=[q],
            qd=[qd],
            dt=dt,
            config=mabd.MABDCPUOracleConfig(bodies=[_body()]),
        )
        point_jacobian = mabd.point_jacobian(rest_point)
        free_point = point_jacobian @ free.q[0]
        plane_offset = float(normal @ free_point + 0.1 * normal_norm)

        result = mabd.solve_cpu_oracle_step(
            q=[q],
            qd=[qd],
            dt=dt,
            config=mabd.MABDCPUOracleConfig(
                bodies=[_body()],
                plane_constraints=[
                    mabd.MABDCPUOraclePlaneConstraint(
                        body=0,
                        rest_point=rest_point,
                        plane_normal=normal,
                        plane_offset=plane_offset,
                    )
                ],
                topology="dense",
            ),
        )

        unit_normal = normal / normal_norm
        constrained_point = point_jacobian @ result.q[0]
        self.assertTrue(
            np.allclose(unit_normal @ constrained_point, plane_offset / normal_norm, atol=1.0e-10)
        )
        free_tangent = free_point - unit_normal * float(unit_normal @ free_point)
        constrained_tangent = constrained_point - unit_normal * float(
            unit_normal @ constrained_point
        )
        self.assertTrue(np.allclose(constrained_tangent, free_tangent, atol=1.0e-10))
        self.assertEqual(result.dlambda.shape, (1,))
        self.assertEqual(result.plane_constraint_requested_count, 1)
        self.assertEqual(result.plane_constraint_accepted_count, 1)
        self.assertEqual(result.plane_constraint_skipped_count, 0)

    def test_dense_cpu_step_plane_constraint_supports_polar_increment_map(self) -> None:
        theta = 0.35
        A = np.array(
            [
                [np.cos(theta), -np.sin(theta), 0.0],
                [np.sin(theta), np.cos(theta), 0.0],
                [0.0, 0.0, 1.0],
            ],
            dtype=float,
        )
        q = mabd.pack_q(A, np.array([0.0, -0.2, 0.0]))
        qd = np.zeros(12)
        qd[9:12] = np.array([0.0, -2.0, 0.0])
        rest_point = np.array([0.2, -0.3, 0.1])
        dt = 0.05
        normal = np.array([0.0, 1.0, 0.0])
        plane_offset = 0.0

        result = mabd.solve_cpu_oracle_step(
            q=[q],
            qd=[qd],
            dt=dt,
            config=mabd.MABDCPUOracleConfig(
                bodies=[_body(rotation_mode="polar")],
                plane_constraints=[
                    mabd.MABDCPUOraclePlaneConstraint(
                        body=0,
                        rest_point=rest_point,
                        plane_normal=normal,
                        plane_offset=plane_offset,
                    )
                ],
                topology="dense",
            ),
        )

        constrained_point = mabd.point_jacobian(rest_point) @ result.q[0]
        self.assertTrue(np.allclose(normal @ constrained_point, plane_offset, atol=1.0e-10))
        self.assertEqual(result.plane_constraint_accepted_count, 1)
        self.assertLess(result.constraint_residual_norm, 1.0e-10)

    def test_inactive_plane_constraint_is_ignored(self) -> None:
        q = _identity_q((0.0, 0.3, 0.0))
        qd = np.zeros(12)
        qd[9:12] = np.array([1.0, 2.0, 3.0])
        dt = 0.05

        free = mabd.solve_cpu_oracle_step(
            q=[q],
            qd=[qd],
            dt=dt,
            config=mabd.MABDCPUOracleConfig(bodies=[_body()]),
        )
        constrained = mabd.solve_cpu_oracle_step(
            q=[q],
            qd=[qd],
            dt=dt,
            config=mabd.MABDCPUOracleConfig(
                bodies=[_body()],
                plane_constraints=[
                    mabd.MABDCPUOraclePlaneConstraint(
                        body=0,
                        rest_point=np.zeros(3),
                        plane_normal=np.array([0.0, 1.0, 0.0]),
                        plane_offset=100.0,
                        active=False,
                    )
                ],
            ),
        )

        self.assertTrue(np.allclose(constrained.q[0], free.q[0], atol=1.0e-12))
        self.assertTrue(np.allclose(constrained.qd[0], free.qd[0], atol=1.0e-12))
        self.assertEqual(constrained.plane_constraint_requested_count, 0)
        self.assertEqual(constrained.plane_constraint_accepted_count, 0)
        self.assertEqual(constrained.plane_constraint_skipped_count, 0)

    def test_plane_constraint_rejects_invalid_parameters(self) -> None:
        with self.assertRaisesRegex(ValueError, "plane_constraints"):
            mabd.solve_cpu_oracle_step(
                q=[_identity_q()],
                qd=[np.zeros(12)],
                dt=0.1,
                config=mabd.MABDCPUOracleConfig(
                    bodies=[_body()],
                    plane_constraints=[
                        mabd.MABDCPUOraclePlaneConstraint(
                            body=1,
                            rest_point=np.zeros(3),
                            plane_normal=np.array([0.0, 1.0, 0.0]),
                            plane_offset=0.0,
                        )
                    ],
                ),
            )
        with self.assertRaisesRegex(ValueError, "plane_normal"):
            mabd.solve_cpu_oracle_step(
                q=[_identity_q()],
                qd=[np.zeros(12)],
                dt=0.1,
                config=mabd.MABDCPUOracleConfig(
                    bodies=[_body()],
                    plane_constraints=[
                        mabd.MABDCPUOraclePlaneConstraint(
                            body=0,
                            rest_point=np.zeros(3),
                            plane_normal=np.zeros(3),
                            plane_offset=0.0,
                        )
                    ],
                ),
            )
        with self.assertRaisesRegex(ValueError, "rest_point"):
            mabd.solve_cpu_oracle_step(
                q=[_identity_q()],
                qd=[np.zeros(12)],
                dt=0.1,
                config=mabd.MABDCPUOracleConfig(
                    bodies=[_body()],
                    plane_constraints=[
                        mabd.MABDCPUOraclePlaneConstraint(
                            body=0,
                            rest_point=np.zeros(2),
                            plane_normal=np.array([0.0, 1.0, 0.0]),
                            plane_offset=0.0,
                        )
                    ],
                ),
            )

    def test_dependent_plane_constraint_rows_are_rank_filtered(self) -> None:
        q = _identity_q((0.0, -0.05, 0.0))
        qd = np.zeros(12)
        dt = 0.05
        constraints = [
            mabd.MABDCPUOraclePlaneConstraint(
                body=0,
                rest_point=np.array([x, -0.5, z], dtype=float),
                plane_normal=np.array([0.0, 1.0, 0.0]),
                plane_offset=0.0,
            )
            for x, z in ((-0.5, -0.5), (-0.5, 0.5), (0.5, -0.5), (0.5, 0.5))
        ]

        result = mabd.solve_cpu_oracle_step(
            q=[q],
            qd=[qd],
            dt=dt,
            config=mabd.MABDCPUOracleConfig(
                bodies=[_body()],
                plane_constraints=constraints,
                topology="dense",
            ),
        )

        self.assertEqual(result.plane_constraint_requested_count, 4)
        self.assertEqual(result.plane_constraint_accepted_count, 3)
        self.assertEqual(result.plane_constraint_skipped_count, 1)
        self.assertEqual(result.dlambda.shape, (3,))
        self.assertTrue(np.all(np.isfinite(result.q[0])))

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

    def test_solver_step_model_path_consumes_plane_constraint_rows(self) -> None:
        builder = newton.ModelBuilder()
        SolverMABD.register_custom_attributes(builder)
        _add_model_body_row(builder, young_modulus=1.0)
        _add_model_plane_constraint_row(
            builder,
            body=0,
            rest_point=(0.25, 0.0, 0.0),
            plane_normal=(0.0, 2.0, 0.0),
            plane_offset=0.04,
        )
        model = builder.finalize()
        solver = SolverMABD(model)
        q = _identity_q((0.0, -0.1, 0.0))
        qd = np.zeros(12)
        qd[9:12] = np.array([0.5, -1.0, 0.25])
        state = model.state()
        _assign_mabd_state(state, q, qd)
        dt = 0.05

        solver.step(state, state, None, None, dt)

        expected = mabd.solve_cpu_oracle_step(
            q=[q],
            qd=[qd],
            dt=dt,
            config=mabd.MABDCPUOracleConfig(
                bodies=[_model_path_body(young_modulus=1.0)],
                plane_constraints=[
                    mabd.MABDCPUOraclePlaneConstraint(
                        body=0,
                        rest_point=np.array([0.25, 0.0, 0.0], dtype=float),
                        plane_normal=np.array([0.0, 2.0, 0.0], dtype=float),
                        plane_offset=0.04,
                    )
                ],
                topology="dense",
            ),
        )
        q_next, qd_next = _read_mabd_state(state)
        self.assertTrue(np.allclose(q_next[0], expected.q[0], atol=1.0e-7))
        self.assertTrue(np.allclose(qd_next[0], expected.qd[0], atol=1.0e-7))
        self.assertEqual(len(solver.model_cpu_oracle_config.plane_constraints), 1)
        self.assertEqual(solver.last_step_result.topology, "dense")
        self.assertEqual(solver.last_step_result.plane_constraint_requested_count, 1)
        self.assertEqual(solver.last_step_result.plane_constraint_accepted_count, 1)
        self.assertEqual(solver.last_step_result.plane_constraint_skipped_count, 0)
        point = mabd.point_jacobian(np.array([0.25, 0.0, 0.0], dtype=float)) @ q_next[0]
        self.assertLess(abs(float(np.array([0.0, 1.0, 0.0]) @ point) - 0.02), 1.0e-8)

    def test_solver_step_model_path_ignores_disabled_plane_constraint_rows(self) -> None:
        builder = newton.ModelBuilder()
        SolverMABD.register_custom_attributes(builder)
        _add_model_body_row(builder, young_modulus=1.0)
        _add_model_plane_constraint_row(
            builder,
            body=0,
            rest_point=(0.25, 0.0, 0.0),
            plane_normal=(0.0, 1.0, 0.0),
            plane_offset=0.0,
            active=0,
        )
        model = builder.finalize()
        solver = SolverMABD(model)
        q = _identity_q((0.0, -0.1, 0.0))
        qd = np.zeros(12)
        qd[9:12] = np.array([0.5, -1.0, 0.25])
        state = model.state()
        _assign_mabd_state(state, q, qd)
        dt = 0.05

        solver.step(state, state, None, None, dt)

        expected = mabd.solve_cpu_oracle_step(
            q=[q],
            qd=[qd],
            dt=dt,
            config=mabd.MABDCPUOracleConfig(
                bodies=[_model_path_body(young_modulus=1.0)],
                plane_constraints=[
                    mabd.MABDCPUOraclePlaneConstraint(
                        body=0,
                        rest_point=np.array([0.25, 0.0, 0.0], dtype=float),
                        plane_normal=np.array([0.0, 1.0, 0.0], dtype=float),
                        plane_offset=0.0,
                        active=False,
                    )
                ],
                topology="dense",
            ),
        )
        q_next, qd_next = _read_mabd_state(state)
        self.assertTrue(np.allclose(q_next[0], expected.q[0], atol=1.0e-7))
        self.assertTrue(np.allclose(qd_next[0], expected.qd[0], atol=1.0e-7))
        self.assertEqual(len(solver.model_cpu_oracle_config.plane_constraints), 1)
        self.assertFalse(solver.model_cpu_oracle_config.plane_constraints[0].active)
        self.assertEqual(solver.last_step_result.plane_constraint_requested_count, 0)
        self.assertEqual(solver.last_step_result.dlambda.shape, (0,))

    def test_solver_step_model_path_rejects_out_of_range_plane_body(self) -> None:
        builder = newton.ModelBuilder()
        SolverMABD.register_custom_attributes(builder)
        _add_model_body_row(builder, young_modulus=1.0)
        _add_model_plane_constraint_row(builder, body=1, rest_point=(0.0, 0.0, 0.0))
        model = builder.finalize()
        solver = SolverMABD(model)
        state = model.state()
        _assign_mabd_state(state, _identity_q(), np.zeros(12))

        with self.assertRaisesRegex(ValueError, "mabd:plane_body"):
            solver.step(state, state, None, None, 0.05)

    def test_solver_step_model_path_rejects_zero_plane_normal(self) -> None:
        builder = newton.ModelBuilder()
        SolverMABD.register_custom_attributes(builder)
        _add_model_body_row(builder, young_modulus=1.0)
        _add_model_plane_constraint_row(
            builder,
            body=0,
            rest_point=(0.0, 0.0, 0.0),
            plane_normal=(0.0, 0.0, 0.0),
        )
        model = builder.finalize()
        solver = SolverMABD(model)
        state = model.state()
        _assign_mabd_state(state, _identity_q(), np.zeros(12))

        with self.assertRaisesRegex(ValueError, "plane_normal"):
            solver.step(state, state, None, None, 0.05)

    def test_solver_step_manual_config_takes_precedence_over_model_plane_constraints(self) -> None:
        builder = newton.ModelBuilder()
        SolverMABD.register_custom_attributes(builder)
        _add_model_body_row(builder, young_modulus=1.0)
        _add_model_plane_constraint_row(builder, body=0, rest_point=(0.25, 0.0, 0.0))
        model = builder.finalize()
        solver = SolverMABD(model)
        manual_config = mabd.MABDCPUOracleConfig(bodies=[_body()])
        solver.configure_cpu_oracle(manual_config)
        q = _identity_q((0.0, -0.1, 0.0))
        qd = np.zeros(12)
        state = model.state()
        _assign_mabd_state(state, q, qd)

        solver.step(state, state, None, None, 0.05)

        self.assertIsNone(solver.model_cpu_oracle_config)
        self.assertEqual(solver.last_step_result.topology, "unconstrained")

    def test_solver_step_consumes_newton_contacts_as_plane_constraints(self) -> None:
        model, box_shape, plane_shape = _mabd_model_with_box_and_static_plane()
        solver = SolverMABD(model)
        q = _identity_q((0.0, -0.1, 0.0))
        qd = np.zeros(12)
        qd[9:12] = np.array([0.5, -1.0, 0.25])
        state = model.state()
        _assign_mabd_state(state, q, qd)
        contacts = _contacts_with_one_rigid_row(
            shape0=box_shape,
            shape1=plane_shape,
            point0=(0.25, 0.0, 0.0),
            point1=(0.25, 0.0, 0.0),
            normal=(0.0, 1.0, 0.0),
        )
        dt = 0.05

        solver.step(state, state, None, contacts, dt)

        expected = mabd.solve_cpu_oracle_step(
            q=[q],
            qd=[qd],
            dt=dt,
            config=mabd.MABDCPUOracleConfig(
                bodies=[_model_path_body(young_modulus=1.0)],
                plane_constraints=[
                    mabd.MABDCPUOraclePlaneConstraint(
                        body=0,
                        rest_point=np.array([0.25, 0.0, 0.0], dtype=float),
                        plane_normal=np.array([0.0, 1.0, 0.0], dtype=float),
                        plane_offset=0.0,
                    )
                ],
                topology="dense",
            ),
        )
        q_next, qd_next = _read_mabd_state(state)
        np.testing.assert_allclose(q_next[0], expected.q[0], atol=1.0e-7)
        np.testing.assert_allclose(qd_next[0], expected.qd[0], atol=1.0e-7)
        self.assertEqual(solver.last_step_result.plane_constraint_requested_count, 1)
        self.assertEqual(solver.last_contacts_input_summary.generated_plane_constraint_count, 1)
        self.assertEqual(solver.last_contacts_input_summary.skipped_contact_count, 0)
        self.assertEqual(
            solver.last_contacts_input_summary.policy,
            "rigid_contacts_to_point_plane_constraints_diagnostic",
        )

    def test_solver_step_flips_contact_normal_when_mabd_body_is_shape1(self) -> None:
        model, box_shape, plane_shape = _mabd_model_with_box_and_static_plane()
        solver = SolverMABD(model)
        q = _identity_q((0.0, -0.1, 0.0))
        qd = np.zeros(12)
        qd[9:12] = np.array([0.5, -1.0, 0.25])
        state = model.state()
        _assign_mabd_state(state, q, qd)
        contacts = _contacts_with_one_rigid_row(
            shape0=plane_shape,
            shape1=box_shape,
            point0=(0.25, 0.0, 0.0),
            point1=(0.25, 0.0, 0.0),
            normal=(0.0, -1.0, 0.0),
        )
        dt = 0.05

        solver.step(state, state, None, contacts, dt)

        expected = mabd.solve_cpu_oracle_step(
            q=[q],
            qd=[qd],
            dt=dt,
            config=mabd.MABDCPUOracleConfig(
                bodies=[_model_path_body(young_modulus=1.0)],
                plane_constraints=[
                    mabd.MABDCPUOraclePlaneConstraint(
                        body=0,
                        rest_point=np.array([0.25, 0.0, 0.0], dtype=float),
                        plane_normal=np.array([0.0, 1.0, 0.0], dtype=float),
                        plane_offset=0.0,
                    )
                ],
                topology="dense",
            ),
        )
        q_next, qd_next = _read_mabd_state(state)
        np.testing.assert_allclose(q_next[0], expected.q[0], atol=1.0e-7)
        np.testing.assert_allclose(qd_next[0], expected.qd[0], atol=1.0e-7)
        self.assertEqual(solver.last_contacts_input_summary.generated_plane_constraint_count, 1)

    def test_solver_step_records_skipped_and_overflow_contact_rows(self) -> None:
        model, _box_shape, plane_shape = _mabd_model_with_box_and_static_plane()
        solver = SolverMABD(model)
        state = model.state()
        _assign_mabd_state(state, _identity_q(), np.zeros(12))
        contacts = _contacts_with_one_rigid_row(
            shape0=plane_shape,
            shape1=plane_shape,
            point0=(0.0, 0.0, 0.0),
            point1=(0.0, 0.0, 0.0),
            normal=(0.0, 1.0, 0.0),
            capacity=1,
            reported_count=3,
        )

        solver.step(state, state, None, contacts, 0.05)

        summary = solver.last_contacts_input_summary
        self.assertEqual(summary.rigid_contact_count, 3)
        self.assertEqual(summary.rigid_contact_capacity, 1)
        self.assertEqual(summary.rigid_contact_overflow_count, 2)
        self.assertEqual(summary.rigid_contact_rows_read, 1)
        self.assertEqual(summary.generated_plane_constraint_count, 0)
        self.assertEqual(summary.skipped_contact_count, 3)
        self.assertEqual(solver.last_step_result.plane_constraint_requested_count, 0)

    def test_solver_step_skips_dynamic_non_mabd_contact_rows(self) -> None:
        model, mabd_shape, rigid_shape = _mabd_model_with_box_and_dynamic_rigid_box()
        solver = SolverMABD(model)
        state = model.state()
        _assign_mabd_state(state, _identity_q(), np.zeros(12))
        contacts = _contacts_with_rigid_rows(
            [
                (
                    mabd_shape,
                    rigid_shape,
                    (0.25, 0.0, 0.0),
                    (0.0, 0.25, 0.0),
                    (0.0, 1.0, 0.0),
                ),
                (
                    rigid_shape,
                    mabd_shape,
                    (0.0, 0.25, 0.0),
                    (0.25, 0.0, 0.0),
                    (0.0, -1.0, 0.0),
                ),
            ]
        )

        solver.step(state, state, None, contacts, 0.05)

        summary = solver.last_contacts_input_summary
        self.assertEqual(summary.rigid_contact_count, 2)
        self.assertEqual(summary.rigid_contact_rows_read, 2)
        self.assertEqual(summary.generated_plane_constraint_count, 0)
        self.assertEqual(summary.skipped_contact_count, 2)
        self.assertEqual(solver.last_step_result.plane_constraint_requested_count, 0)

    def test_solver_detects_affine_cylinder_static_plane_contact(self) -> None:
        model, cylinder_shape, plane_shape = _mabd_model_with_cylinder_and_static_plane()
        solver = SolverMABD(model)
        state = model.state()
        _assign_mabd_state(state, _identity_q((0.0, -0.1, 0.0)), np.zeros(12))

        contacts = solver.detect_static_plane_contacts(state)

        self.assertEqual(int(contacts.rigid_contact_count.numpy()[0]), 1)
        self.assertEqual(int(contacts.rigid_contact_max), 1)
        np.testing.assert_array_equal(
            contacts.rigid_contact_shape0.numpy()[:1],
            np.full(1, cylinder_shape, dtype=np.int32),
        )
        np.testing.assert_array_equal(
            contacts.rigid_contact_shape1.numpy()[:1],
            np.full(1, plane_shape, dtype=np.int32),
        )
        np.testing.assert_allclose(
            contacts.rigid_contact_normal.numpy()[:1],
            np.array([[0.0, 1.0, 0.0]], dtype=np.float32),
            atol=1.0e-7,
        )
        np.testing.assert_allclose(
            contacts.rigid_contact_point0.numpy()[:1],
            np.array([[0.0, -0.5, 0.0]], dtype=np.float32),
            atol=1.0e-7,
        )
        summary = solver.last_static_plane_collision_summary
        self.assertEqual(
            summary.policy,
            "mabd_affine_cylinder_static_plane_support_diagnostic",
        )
        self.assertEqual(
            summary.scope,
            "affine_cylinder_support_points_vs_static_infinite_planes",
        )
        self.assertEqual(summary.box_shape_count, 0)
        self.assertEqual(summary.cylinder_shape_count, 1)
        self.assertEqual(summary.static_plane_shape_count, 1)
        self.assertEqual(summary.candidate_contact_count, 1)
        self.assertEqual(summary.rigid_contact_rows_written, 1)

    def test_solver_step_rejects_duplicate_mabd_body_index_mapping_for_contacts(self) -> None:
        builder = newton.ModelBuilder()
        SolverMABD.register_custom_attributes(builder)
        body_id = builder.add_body()
        for _ in range(2):
            builder.add_custom_values(
                **{
                    "mabd:body_index": body_id,
                    "mabd:young_modulus": 1.0,
                    "mabd:poisson_ratio": 0.25,
                    "mabd:density": 1.0,
                    "mabd:polar_mode": 0,
                    "mabd:rest_point0": wp.vec3(0.0, 0.0, 0.0),
                    "mabd:rest_point1": wp.vec3(1.0, 0.0, 0.0),
                    "mabd:rest_point2": wp.vec3(0.0, 1.0, 0.0),
                    "mabd:rest_point3": wp.vec3(0.0, 0.0, 1.0),
                    "mabd:point_mass0": -1.0,
                    "mabd:point_mass1": -1.0,
                    "mabd:point_mass2": -1.0,
                    "mabd:point_mass3": -1.0,
                    "mabd:volume": -1.0,
                }
            )
        box_shape = builder.add_shape_box(body=body_id, hx=0.5, hy=0.5, hz=0.5)
        plane_shape = builder.add_shape_plane(plane=(0.0, 1.0, 0.0, 0.0), width=0.0, length=0.0)
        model = builder.finalize()
        solver = SolverMABD(model)
        state = model.state()
        _assign_mabd_state(state, [_identity_q(), _identity_q()], [np.zeros(12), np.zeros(12)])
        contacts = _contacts_with_one_rigid_row(
            shape0=box_shape,
            shape1=plane_shape,
            point0=(0.25, 0.0, 0.0),
            point1=(0.25, 0.0, 0.0),
            normal=(0.0, 1.0, 0.0),
        )

        with self.assertRaisesRegex(ValueError, "duplicate mabd:body_index"):
            solver.step(state, state, None, contacts, 0.05)

    def test_solver_step_clears_contacts_summary_when_contacts_none(self) -> None:
        model, _box_shape, _plane_shape = _mabd_model_with_box_and_static_plane()
        solver = SolverMABD(model)
        state = model.state()
        _assign_mabd_state(state, _identity_q(), np.zeros(12))

        solver.step(state, state, None, None, 0.05)

        self.assertIsNone(solver.last_contacts_input_summary)


if __name__ == "__main__":
    unittest.main()
