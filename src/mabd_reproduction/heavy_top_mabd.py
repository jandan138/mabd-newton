"""Newton-derived M-ABD diagnostic rollout for the heavy-top scene."""

from __future__ import annotations

import sys
from contextlib import redirect_stdout
from dataclasses import dataclass
from math import acos, atan2, cos, degrees, radians, sin
from typing import Callable

import numpy as np
from newton.solvers import mabd

from .experiment_configs import HeavyTopRunConfig


NEWTON_MODEL_DERIVED_CONFIG_SOURCE = "newton_model_derived"
NEWTON_MODEL_DERIVED_CUSTOM_FREQUENCIES = (
    "mabd:body",
    "mabd:world_constraint",
    "mabd:gravity",
)


@dataclass(frozen=True)
class HeavyTopMABDSample:
    sample_index: int
    step: int
    time_s: float
    nutation_angle_deg: float
    precession_angle_rad: float
    pivot_residual_m: float
    constraint_residual_norm: float
    affine_shape_spread_m: float
    world_anchor_reaction_vector_n: np.ndarray
    world_anchor_reaction_magnitude_n: float


@dataclass(frozen=True)
class HeavyTopMABDRollout:
    samples: tuple[HeavyTopMABDSample, ...]
    step_count: int
    sample_count: int
    time_step_s: float
    rotation_mode: str
    min_nutation_angle_deg: float
    max_nutation_angle_deg: float
    max_abs_precession_velocity_rad_s: float
    max_pivot_residual_m: float
    max_constraint_residual_norm: float
    max_affine_shape_spread_m: float
    max_world_anchor_reaction_magnitude_n: float
    solver_model_config_source: str
    newton_model_derived_custom_frequencies: tuple[str, ...]
    finite: bool


@dataclass(frozen=True)
class _MABDStepOutput:
    q: np.ndarray
    qd: np.ndarray
    dlambda: np.ndarray
    constraint_residual_norm: float


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


def _initial_rotation_matrix(initial_tilt_deg: float) -> np.ndarray:
    theta = radians(initial_tilt_deg)
    axis_z = np.array([sin(theta), cos(theta), 0.0], dtype=float)
    axis_x = np.array([cos(theta), -sin(theta), 0.0], dtype=float)
    axis_y = np.cross(axis_z, axis_x)
    return np.column_stack((axis_x, axis_y, axis_z))


def _initial_state(config: HeavyTopRunConfig) -> tuple[np.ndarray, np.ndarray]:
    lane = config.mabd_newton
    rotation = _initial_rotation_matrix(config.reference.initial_tilt_deg)
    translation = lane.pivot_world_point_m - rotation @ lane.pivot_rest_point_m
    q = mabd.pack_q(rotation, translation)
    omega_world = config.reference.initial_spin_rad_s * rotation[:, 2]
    rotation_velocity = _skew(omega_world) @ rotation
    translation_velocity = -rotation_velocity @ lane.pivot_rest_point_m
    qd = mabd.pack_q(rotation_velocity, translation_velocity)
    return q, qd


def heavy_top_mabd_axis(
    q: np.ndarray,
    *,
    pivot_rest_point_m: np.ndarray,
    angle_probe_rest_point_m: np.ndarray,
) -> np.ndarray:
    points = mabd.affine_points(q, np.vstack([pivot_rest_point_m, angle_probe_rest_point_m]))
    direction = points[1] - points[0]
    norm = float(np.linalg.norm(direction))
    if norm <= 0.0:
        return np.full(3, np.nan, dtype=float)
    return direction / norm


def _nutation_angle_deg(axis: np.ndarray) -> float:
    return degrees(acos(float(np.clip(axis[1], -1.0, 1.0))))


def _precession_angle_rad(axis: np.ndarray) -> float:
    return float(atan2(float(axis[2]), float(axis[0])))


def _pivot_residual(
    q: np.ndarray,
    *,
    pivot_rest_point_m: np.ndarray,
    pivot_world_point_m: np.ndarray,
) -> float:
    point = mabd.affine_points(q, np.asarray([pivot_rest_point_m], dtype=float))[0]
    return float(np.linalg.norm(point - pivot_world_point_m))


def _affine_shape_spread(q: np.ndarray, rest_points_m: np.ndarray) -> float:
    points = mabd.affine_points(q, rest_points_m)
    max_spread = 0.0
    for row in range(rest_points_m.shape[0]):
        for col in range(row + 1, rest_points_m.shape[0]):
            rest_distance = float(np.linalg.norm(rest_points_m[row] - rest_points_m[col]))
            world_distance = float(np.linalg.norm(points[row] - points[col]))
            max_spread = max(max_spread, abs(world_distance - rest_distance))
    return max_spread


def _sample_steps(step_count: int, sample_count: int) -> tuple[int, ...]:
    return tuple(int(round(value)) for value in np.linspace(0, step_count, sample_count))


def _heavy_top_solver_model(config: HeavyTopRunConfig) -> object:
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
                "mabd:volume": -1.0,
                "mabd:zero_stiffness_diagnostic": 1,
            }
        )
        builder.add_custom_values(
            **{
                "mabd:world_body": 0,
                "mabd:world_rest_point": _vec3(lane.pivot_rest_point_m, wp),
                "mabd:world_point": _vec3(lane.pivot_world_point_m, wp),
            }
        )
        builder.add_custom_values(
            **{
                "mabd:gravity_enabled": 1,
                "mabd:gravity_vector": _vec3(lane.gravity_m_s2, wp),
            }
        )
        return builder.finalize()


def _model_derived_stepper(config: HeavyTopRunConfig) -> Callable[[np.ndarray, np.ndarray], _MABDStepOutput]:
    lane = config.mabd_newton
    with redirect_stdout(sys.stderr):
        from newton.solvers import SolverMABD

        model = _heavy_top_solver_model(config)
        solver = SolverMABD(model)
        state = model.state()

    def step_once(q: np.ndarray, qd: np.ndarray) -> _MABDStepOutput:
        _assign_solver_state(state, q, qd)
        solver.step(state, state, None, None, lane.time_step_s)
        if solver.last_step_result is None:
            raise RuntimeError("SolverMABD.step did not record a last_step_result")
        state_q, state_qd = _read_solver_state(state)
        return _MABDStepOutput(
            q=state_q,
            qd=state_qd,
            dlambda=solver.last_step_result.dlambda,
            constraint_residual_norm=solver.last_step_result.constraint_residual_norm,
        )

    return step_once


def roll_out_heavy_top_mabd_model_derived(config: HeavyTopRunConfig) -> HeavyTopMABDRollout:
    lane = config.mabd_newton
    q, qd = _initial_state(config)
    step_once = _model_derived_stepper(config)
    sample_steps = set(_sample_steps(lane.step_count, lane.sample_count))
    samples: list[HeavyTopMABDSample] = []
    max_pivot_residual = 0.0
    max_constraint_residual = 0.0
    max_affine_shape_spread = 0.0
    max_world_anchor_reaction = 0.0
    latest_world_anchor_reaction = np.zeros(3, dtype=float)
    finite = True

    for step in range(lane.step_count + 1):
        finite = finite and bool(np.all(np.isfinite(q))) and bool(np.all(np.isfinite(qd)))
        pivot_residual = _pivot_residual(
            q,
            pivot_rest_point_m=lane.pivot_rest_point_m,
            pivot_world_point_m=lane.pivot_world_point_m,
        )
        shape_spread = _affine_shape_spread(q, lane.rest_points_m)
        max_pivot_residual = max(max_pivot_residual, pivot_residual)
        max_affine_shape_spread = max(max_affine_shape_spread, shape_spread)
        axis = heavy_top_mabd_axis(
            q,
            pivot_rest_point_m=lane.pivot_rest_point_m,
            angle_probe_rest_point_m=lane.angle_probe_rest_point_m,
        )
        nutation = _nutation_angle_deg(axis)
        precession = _precession_angle_rad(axis)
        reaction_magnitude = float(np.linalg.norm(latest_world_anchor_reaction))
        max_world_anchor_reaction = max(max_world_anchor_reaction, reaction_magnitude)

        if step in sample_steps:
            samples.append(
                HeavyTopMABDSample(
                    sample_index=len(samples),
                    step=step,
                    time_s=step * lane.time_step_s,
                    nutation_angle_deg=nutation,
                    precession_angle_rad=precession,
                    pivot_residual_m=pivot_residual,
                    constraint_residual_norm=max_constraint_residual,
                    affine_shape_spread_m=shape_spread,
                    world_anchor_reaction_vector_n=latest_world_anchor_reaction.copy(),
                    world_anchor_reaction_magnitude_n=reaction_magnitude,
                )
            )

        if step == lane.step_count:
            break
        result = step_once(q, qd)
        q = result.q
        qd = result.qd
        latest_world_anchor_reaction = (
            np.asarray(result.dlambda[:3], dtype=float).copy()
            if result.dlambda.shape[0] >= 3
            else np.zeros(3, dtype=float)
        )
        max_constraint_residual = max(max_constraint_residual, result.constraint_residual_norm)

    nutations = np.asarray([sample.nutation_angle_deg for sample in samples], dtype=float)
    precessions = np.unwrap(np.asarray([sample.precession_angle_rad for sample in samples], dtype=float))
    sample_times = np.asarray([sample.time_s for sample in samples], dtype=float)
    if len(samples) >= 2:
        precession_velocities = np.diff(precessions) / np.diff(sample_times)
        max_abs_precession_velocity = float(np.max(np.abs(precession_velocities)))
    else:
        max_abs_precession_velocity = 0.0
    return HeavyTopMABDRollout(
        samples=tuple(samples),
        step_count=lane.step_count,
        sample_count=len(samples),
        time_step_s=lane.time_step_s,
        rotation_mode=lane.rotation_mode,
        min_nutation_angle_deg=float(np.min(nutations)),
        max_nutation_angle_deg=float(np.max(nutations)),
        max_abs_precession_velocity_rad_s=max_abs_precession_velocity,
        max_pivot_residual_m=max_pivot_residual,
        max_constraint_residual_norm=max_constraint_residual,
        max_affine_shape_spread_m=max_affine_shape_spread,
        max_world_anchor_reaction_magnitude_n=max_world_anchor_reaction,
        solver_model_config_source=NEWTON_MODEL_DERIVED_CONFIG_SOURCE,
        newton_model_derived_custom_frequencies=NEWTON_MODEL_DERIVED_CUSTOM_FREQUENCIES,
        finite=finite,
    )


__all__ = [
    "HeavyTopMABDRollout",
    "HeavyTopMABDSample",
    "NEWTON_MODEL_DERIVED_CONFIG_SOURCE",
    "NEWTON_MODEL_DERIVED_CUSTOM_FREQUENCIES",
    "heavy_top_mabd_axis",
    "roll_out_heavy_top_mabd_model_derived",
]
