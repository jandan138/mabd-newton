"""Newton-derived M-ABD diagnostic rollout for the T-handle scene."""

from __future__ import annotations

import sys
from contextlib import redirect_stdout
from dataclasses import dataclass

import numpy as np
from newton.solvers import mabd

from .experiment_configs import THandleRunConfig


NEWTON_MODEL_DERIVED_CONFIG_SOURCE = "newton_model_derived"
NEWTON_MODEL_DERIVED_CUSTOM_FREQUENCIES = ("mabd:body", "mabd:gravity")


@dataclass(frozen=True)
class THandleMABDSample:
    sample_index: int
    step: int
    time_s: float
    angular_velocity_rad_s: np.ndarray
    energy: float
    angular_momentum_norm: float
    affine_shape_spread_m: float


@dataclass(frozen=True)
class THandleMABDRollout:
    samples: tuple[THandleMABDSample, ...]
    step_count: int
    sample_count: int
    time_step_s: float
    rotation_mode: str
    energy_initial: float
    energy_final: float
    relative_energy_drift: float
    angular_momentum_norm_initial: float
    angular_momentum_norm_final: float
    angular_momentum_norm_drift: float
    proxy_inertia_kg_m2: np.ndarray
    reference_inertia_kg_m2: np.ndarray
    max_proxy_inertia_relative_error: float
    max_affine_shape_spread_m: float
    solver_model_config_source: str
    newton_model_derived_custom_frequencies: tuple[str, ...]
    finite: bool


def _vec3(values: np.ndarray, wp_module: object) -> object:
    values = np.asarray(values, dtype=float)
    if values.shape != (3,):
        raise ValueError(f"expected vec3-compatible value with shape (3,), got {values.shape}")
    return wp_module.vec3(float(values[0]), float(values[1]), float(values[2]))


def _assign_solver_state(state: object, q: np.ndarray, qd: np.ndarray) -> None:
    q_arr = np.asarray([q], dtype=np.float32)
    qd_arr = np.asarray([qd], dtype=np.float32)
    state.mabd.q0.assign(q_arr[:, 0:3])
    state.mabd.q1.assign(q_arr[:, 3:6])
    state.mabd.q2.assign(q_arr[:, 6:9])
    state.mabd.t.assign(q_arr[:, 9:12])
    state.mabd.qd0.assign(qd_arr[:, 0:3])
    state.mabd.qd1.assign(qd_arr[:, 3:6])
    state.mabd.qd2.assign(qd_arr[:, 6:9])
    state.mabd.td.assign(qd_arr[:, 9:12])


def _read_solver_state(state: object) -> tuple[np.ndarray, np.ndarray]:
    q = np.concatenate(
        [
            state.mabd.q0.numpy(),
            state.mabd.q1.numpy(),
            state.mabd.q2.numpy(),
            state.mabd.t.numpy(),
        ],
        axis=1,
    )[0].astype(float, copy=False)
    qd = np.concatenate(
        [
            state.mabd.qd0.numpy(),
            state.mabd.qd1.numpy(),
            state.mabd.qd2.numpy(),
            state.mabd.td.numpy(),
        ],
        axis=1,
    )[0].astype(float, copy=False)
    return q, qd


def _skew(vector: np.ndarray) -> np.ndarray:
    x, y, z = np.asarray(vector, dtype=float)
    return np.array(
        [
            [0.0, -z, y],
            [z, 0.0, -x],
            [-y, x, 0.0],
        ],
        dtype=float,
    )


def _initial_state(config: THandleRunConfig) -> tuple[np.ndarray, np.ndarray]:
    rotation = np.eye(3, dtype=float)
    q = mabd.pack_q(rotation, np.zeros(3, dtype=float))
    rotation_velocity = _skew(config.mabd_newton.initial_angular_velocity_rad_s) @ rotation
    qd = mabd.pack_q(rotation_velocity, np.zeros(3, dtype=float))
    return q, qd


def _t_handle_solver_model(config: THandleRunConfig) -> object:
    lane = config.mabd_newton
    with redirect_stdout(sys.stderr):
        import newton
        import warp as wp
        from newton.solvers import SolverMABD

        builder = newton.ModelBuilder()
        SolverMABD.register_custom_attributes(builder)
        body_id = builder.add_body()
        builder.add_custom_values(
            **{
                "mabd:body_index": body_id,
                "mabd:young_modulus": 0.0,
                "mabd:poisson_ratio": 0.25,
                "mabd:density": 1.0,
                "mabd:polar_mode": 1,
                "mabd:rest_point0": _vec3(lane.rest_points_m[0], wp),
                "mabd:rest_point1": _vec3(lane.rest_points_m[1], wp),
                "mabd:rest_point2": _vec3(lane.rest_points_m[2], wp),
                "mabd:rest_point3": _vec3(lane.rest_points_m[3], wp),
                "mabd:point_mass0": float(lane.point_masses_kg[0]),
                "mabd:point_mass1": float(lane.point_masses_kg[1]),
                "mabd:point_mass2": float(lane.point_masses_kg[2]),
                "mabd:point_mass3": float(lane.point_masses_kg[3]),
                "mabd:volume": float(lane.volume_m3),
                "mabd:zero_stiffness_diagnostic": 1,
            }
        )
        builder.add_custom_values(
            **{
                "mabd:gravity_enabled": 0,
                "mabd:gravity_vector": _vec3(lane.gravity_m_s2, wp),
            }
        )
        return builder.finalize()


def _model_derived_stepper(config: THandleRunConfig):
    lane = config.mabd_newton
    with redirect_stdout(sys.stderr):
        from newton.solvers import SolverMABD

        model = _t_handle_solver_model(config)
        solver = SolverMABD(model)
        state = model.state()

    def step_once(q: np.ndarray, qd: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        _assign_solver_state(state, q, qd)
        solver.step(state, state, None, None, lane.time_step_s)
        if solver.last_step_result is None:
            raise RuntimeError("SolverMABD.step did not record a last_step_result")
        return _read_solver_state(state)

    return step_once


def _sample_steps(step_count: int, sample_count: int) -> tuple[int, ...]:
    return tuple(int(round(value)) for value in np.linspace(0, step_count, sample_count))


def _center_of_mass(points: np.ndarray, masses: np.ndarray) -> np.ndarray:
    return np.sum(points * masses[:, None], axis=0) / float(np.sum(masses))


def _proxy_inertia(points: np.ndarray, masses: np.ndarray) -> np.ndarray:
    com = _center_of_mass(points, masses)
    inertia = np.zeros((3, 3), dtype=float)
    for point, mass in zip(points - com, masses):
        inertia += mass * (float(np.dot(point, point)) * np.eye(3) - np.outer(point, point))
    return np.diag(inertia)


def _affine_angular_velocity(q: np.ndarray, qd: np.ndarray) -> np.ndarray:
    matrix, _ = mabd.unpack_q(q)
    matrix_velocity, _ = mabd.unpack_q(qd)
    omega_matrix = matrix_velocity @ np.linalg.inv(matrix)
    skew_part = 0.5 * (omega_matrix - omega_matrix.T)
    return np.asarray(
        [
            skew_part[2, 1],
            skew_part[0, 2],
            skew_part[1, 0],
        ],
        dtype=float,
    )


def _point_mass_energy(
    q: np.ndarray,
    qd: np.ndarray,
    *,
    rest_points_m: np.ndarray,
    point_masses_kg: np.ndarray,
) -> float:
    velocities = mabd.affine_points(qd, rest_points_m)
    return 0.5 * float(np.sum(point_masses_kg * np.sum(velocities * velocities, axis=1)))


def _angular_momentum_norm(
    q: np.ndarray,
    qd: np.ndarray,
    *,
    rest_points_m: np.ndarray,
    point_masses_kg: np.ndarray,
) -> float:
    points = mabd.affine_points(q, rest_points_m)
    velocities = mabd.affine_points(qd, rest_points_m)
    com = _center_of_mass(points, point_masses_kg)
    v_com = _center_of_mass(velocities, point_masses_kg)
    momentum = np.zeros(3, dtype=float)
    for point, velocity, mass in zip(points - com, velocities - v_com, point_masses_kg):
        momentum += mass * np.cross(point, velocity)
    return float(np.linalg.norm(momentum))


def _affine_shape_spread(q: np.ndarray, rest_points_m: np.ndarray) -> float:
    points = mabd.affine_points(q, rest_points_m)
    max_spread = 0.0
    for row in range(rest_points_m.shape[0]):
        for col in range(row + 1, rest_points_m.shape[0]):
            rest_distance = float(np.linalg.norm(rest_points_m[row] - rest_points_m[col]))
            world_distance = float(np.linalg.norm(points[row] - points[col]))
            max_spread = max(max_spread, abs(world_distance - rest_distance))
    return max_spread


def roll_out_t_handle_mabd_model_derived(config: THandleRunConfig) -> THandleMABDRollout:
    lane = config.mabd_newton
    q, qd = _initial_state(config)
    step_once = _model_derived_stepper(config)
    sample_steps = set(_sample_steps(lane.step_count, lane.sample_count))
    samples: list[THandleMABDSample] = []
    max_affine_shape_spread = 0.0
    finite = True
    proxy_inertia = _proxy_inertia(lane.rest_points_m, lane.point_masses_kg)
    reference_inertia = config.reference.principal_inertia_kg_m2.astype(float, copy=True)
    relative_errors = np.abs(proxy_inertia - reference_inertia) / reference_inertia
    max_proxy_inertia_relative_error = float(np.max(relative_errors))
    energy_initial = _point_mass_energy(
        q,
        qd,
        rest_points_m=lane.rest_points_m,
        point_masses_kg=lane.point_masses_kg,
    )
    momentum_initial = _angular_momentum_norm(
        q,
        qd,
        rest_points_m=lane.rest_points_m,
        point_masses_kg=lane.point_masses_kg,
    )
    energy_final = energy_initial
    momentum_final = momentum_initial

    for step in range(lane.step_count + 1):
        finite = finite and bool(np.all(np.isfinite(q))) and bool(np.all(np.isfinite(qd)))
        energy_final = _point_mass_energy(
            q,
            qd,
            rest_points_m=lane.rest_points_m,
            point_masses_kg=lane.point_masses_kg,
        )
        momentum_final = _angular_momentum_norm(
            q,
            qd,
            rest_points_m=lane.rest_points_m,
            point_masses_kg=lane.point_masses_kg,
        )
        shape_spread = _affine_shape_spread(q, lane.rest_points_m)
        max_affine_shape_spread = max(max_affine_shape_spread, shape_spread)
        if step in sample_steps:
            samples.append(
                THandleMABDSample(
                    sample_index=len(samples),
                    step=step,
                    time_s=step * lane.time_step_s,
                    angular_velocity_rad_s=_affine_angular_velocity(q, qd),
                    energy=float(energy_final),
                    angular_momentum_norm=float(momentum_final),
                    affine_shape_spread_m=float(shape_spread),
                )
            )
        if step == lane.step_count:
            break
        q, qd = step_once(q, qd)

    relative_energy_drift = (
        (energy_final - energy_initial) / energy_initial
        if energy_initial != 0.0 and np.isfinite(energy_initial)
        else np.nan
    )
    angular_momentum_norm_drift = (
        (momentum_final - momentum_initial) / momentum_initial
        if momentum_initial != 0.0 and np.isfinite(momentum_initial)
        else np.nan
    )
    finite = (
        finite
        and bool(np.isfinite(energy_initial))
        and bool(np.isfinite(energy_final))
        and bool(np.isfinite(relative_energy_drift))
        and bool(np.isfinite(momentum_initial))
        and bool(np.isfinite(momentum_final))
        and bool(np.isfinite(angular_momentum_norm_drift))
        and bool(np.all(np.isfinite(proxy_inertia)))
        and bool(np.all(np.isfinite(reference_inertia)))
        and bool(np.all([np.all(np.isfinite(sample.angular_velocity_rad_s)) for sample in samples]))
    )
    return THandleMABDRollout(
        samples=tuple(samples),
        step_count=lane.step_count,
        sample_count=len(samples),
        time_step_s=lane.time_step_s,
        rotation_mode=lane.rotation_mode,
        energy_initial=float(energy_initial),
        energy_final=float(energy_final),
        relative_energy_drift=float(relative_energy_drift),
        angular_momentum_norm_initial=float(momentum_initial),
        angular_momentum_norm_final=float(momentum_final),
        angular_momentum_norm_drift=float(angular_momentum_norm_drift),
        proxy_inertia_kg_m2=proxy_inertia,
        reference_inertia_kg_m2=reference_inertia,
        max_proxy_inertia_relative_error=max_proxy_inertia_relative_error,
        max_affine_shape_spread_m=max_affine_shape_spread,
        solver_model_config_source=NEWTON_MODEL_DERIVED_CONFIG_SOURCE,
        newton_model_derived_custom_frequencies=NEWTON_MODEL_DERIVED_CUSTOM_FREQUENCIES,
        finite=finite,
    )


__all__ = [
    "NEWTON_MODEL_DERIVED_CONFIG_SOURCE",
    "NEWTON_MODEL_DERIVED_CUSTOM_FREQUENCIES",
    "THandleMABDRollout",
    "THandleMABDSample",
    "roll_out_t_handle_mabd_model_derived",
]
