"""Newton-only M-ABD development rollout for the physical-pendulum scene."""

from __future__ import annotations

import sys
from contextlib import redirect_stdout
from dataclasses import dataclass
from math import atan2
from typing import Callable

import numpy as np
from newton.solvers import mabd

from .experiment_configs import PhysicalPendulumRunConfig
from .physical_pendulum_reference import (
    physical_pendulum_angle_reference,
    physical_pendulum_joint_force_reference,
)


MANUAL_CPU_ORACLE_CONFIG_SOURCE = "manual_cpu_oracle_config"
NEWTON_MODEL_DERIVED_CONFIG_SOURCE = "newton_model_derived"
NEWTON_MODEL_DERIVED_CUSTOM_FREQUENCIES = (
    "mabd:body",
    "mabd:world_constraint",
    "mabd:gravity",
)


@dataclass(frozen=True)
class PhysicalPendulumMABDSample:
    sample_index: int
    step: int
    time_s: float
    angle_rad: float
    reference_angle_rad: float
    abs_angle_error_rad: float
    phase_drift_rad: float
    pivot_residual_m: float
    constraint_residual_norm: float
    world_anchor_reaction_vector_n: np.ndarray
    world_anchor_reaction_magnitude_n: float
    reference_joint_force_magnitude_n: float
    abs_joint_force_error_n: float


@dataclass(frozen=True)
class PhysicalPendulumMABDRollout:
    samples: tuple[PhysicalPendulumMABDSample, ...]
    step_count: int
    sample_count: int
    time_step_s: float
    rotation_mode: str
    max_pivot_residual_m: float
    max_constraint_residual_norm: float
    max_abs_angle_error_rad: float
    max_phase_drift_rad: float
    max_world_anchor_reaction_magnitude_n: float
    max_abs_joint_force_error_n: float
    solver_model_config_source: str
    finite: bool


@dataclass(frozen=True)
class _MABDStepOutput:
    q: np.ndarray
    qd: np.ndarray
    dlambda: np.ndarray
    constraint_residual_norm: float


def physical_pendulum_mabd_angle(
    q: np.ndarray,
    *,
    pivot_rest_point_m: np.ndarray,
    angle_probe_rest_point_m: np.ndarray,
) -> float:
    points = mabd.affine_points(q, np.vstack([pivot_rest_point_m, angle_probe_rest_point_m]))
    direction = points[1] - points[0]
    return float(atan2(-float(direction[1]), float(direction[0])))


def _pivot_residual(
    q: np.ndarray,
    *,
    pivot_rest_point_m: np.ndarray,
    pivot_world_point_m: np.ndarray,
) -> float:
    point = mabd.affine_points(q, np.asarray([pivot_rest_point_m], dtype=float))[0]
    return float(np.linalg.norm(point - pivot_world_point_m))


def _sample_steps(step_count: int, sample_count: int) -> tuple[int, ...]:
    return tuple(int(round(value)) for value in np.linspace(0, step_count, sample_count))


def _validate_rotation_mode(rotation_mode: str) -> None:
    if rotation_mode not in {"none", "polar"}:
        raise ValueError("physical pendulum MABD rollout supports rotation_mode none or polar")


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


def _physical_pendulum_solver_model(
    config: PhysicalPendulumRunConfig,
    *,
    rotation_mode: str = "none",
) -> object:
    _validate_rotation_mode(rotation_mode)
    lane = config.mabd_development
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
                "mabd:polar_mode": {"none": 0, "polar": 1}[rotation_mode],
                "mabd:rest_point0": _vec3(lane.rest_points_m[0], wp),
                "mabd:rest_point1": _vec3(lane.rest_points_m[1], wp),
                "mabd:rest_point2": _vec3(lane.rest_points_m[2], wp),
                "mabd:rest_point3": _vec3(lane.rest_points_m[3], wp),
                "mabd:point_mass0": float(lane.masses_kg[0]),
                "mabd:point_mass1": float(lane.masses_kg[1]),
                "mabd:point_mass2": float(lane.masses_kg[2]),
                "mabd:point_mass3": float(lane.masses_kg[3]),
                "mabd:volume": -1.0,
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


def _manual_cpu_oracle_stepper(
    config: PhysicalPendulumRunConfig,
    *,
    rotation_mode: str,
) -> Callable[[np.ndarray, np.ndarray], _MABDStepOutput]:
    _validate_rotation_mode(rotation_mode)
    lane = config.mabd_development
    body = mabd.MABDCPUOracleBody(
        precompute=mabd.SingleBodyABDPrecompute.from_points(
            lane.rest_points_m,
            lane.masses_kg,
        ),
        rest_q=lane.initial_q,
        rotation_mode=rotation_mode,
    )
    world_constraint = mabd.MABDCPUOracleWorldConstraint(
        body=0,
        rest_point=lane.pivot_rest_point_m,
        world_point=lane.pivot_world_point_m,
    )
    solver_config = mabd.MABDCPUOracleConfig(
        bodies=(body,),
        world_constraints=(world_constraint,),
        gravity=lane.gravity_m_s2,
        topology="dense",
        residual_correction=True,
    )

    def step_once(q: np.ndarray, qd: np.ndarray) -> _MABDStepOutput:
        result = mabd.solve_cpu_oracle_step(
            q=(q,),
            qd=(qd,),
            dt=lane.time_step_s,
            config=solver_config,
        )
        return _MABDStepOutput(
            q=result.q[0],
            qd=result.qd[0],
            dlambda=result.dlambda,
            constraint_residual_norm=result.constraint_residual_norm,
        )

    return step_once


def _model_derived_stepper(
    config: PhysicalPendulumRunConfig,
    *,
    rotation_mode: str,
) -> Callable[[np.ndarray, np.ndarray], _MABDStepOutput]:
    _validate_rotation_mode(rotation_mode)
    lane = config.mabd_development
    with redirect_stdout(sys.stderr):
        from newton.solvers import SolverMABD

        model = _physical_pendulum_solver_model(config, rotation_mode=rotation_mode)
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


def _roll_out_physical_pendulum_mabd(
    config: PhysicalPendulumRunConfig,
    *,
    rotation_mode: str,
    solver_model_config_source: str,
    step_once: Callable[[np.ndarray, np.ndarray], _MABDStepOutput],
) -> PhysicalPendulumMABDRollout:
    _validate_rotation_mode(rotation_mode)
    lane = config.mabd_development
    q = lane.initial_q.copy()
    qd = lane.initial_qd.copy()
    sample_steps = set(_sample_steps(lane.step_count, lane.sample_count))
    samples: list[PhysicalPendulumMABDSample] = []
    max_pivot_residual = 0.0
    max_constraint_residual = 0.0
    max_abs_angle_error = 0.0
    max_phase_drift = 0.0
    max_world_anchor_reaction = 0.0
    max_abs_joint_force_error = 0.0
    latest_world_anchor_reaction = np.zeros(3, dtype=float)
    gravity_magnitude = float(np.linalg.norm(config.rbd_baseline.gravity_m_s2))
    finite = True

    for step in range(lane.step_count + 1):
        pivot_residual = _pivot_residual(
            q,
            pivot_rest_point_m=lane.pivot_rest_point_m,
            pivot_world_point_m=lane.pivot_world_point_m,
        )
        max_pivot_residual = max(max_pivot_residual, pivot_residual)
        finite = finite and bool(np.all(np.isfinite(q))) and bool(np.all(np.isfinite(qd)))

        time_s = step * lane.time_step_s
        angle = physical_pendulum_mabd_angle(
            q,
            pivot_rest_point_m=lane.pivot_rest_point_m,
            angle_probe_rest_point_m=lane.angle_probe_rest_point_m,
        )
        reference = float(
            physical_pendulum_angle_reference(
                np.asarray([time_s], dtype=float),
                kappa=config.reference.kappa,
                omega_lin=config.reference.omega_lin_rad_s,
            )[0]
        )
        abs_error = abs(angle - reference)
        phase_drift = angle - reference
        max_abs_angle_error = max(max_abs_angle_error, abs_error)
        max_phase_drift = max(max_phase_drift, abs(phase_drift))
        reaction_magnitude = float(np.linalg.norm(latest_world_anchor_reaction))
        max_world_anchor_reaction = max(max_world_anchor_reaction, reaction_magnitude)
        reference_joint_force = float(
            physical_pendulum_joint_force_reference(
                np.asarray([time_s], dtype=float),
                kappa=config.reference.kappa,
                omega_lin=config.reference.omega_lin_rad_s,
                mass_kg=config.rbd_baseline.mass_kg,
                length_m=config.rbd_baseline.length_m,
                gravity_magnitude=gravity_magnitude,
            )[0]
        )
        abs_joint_force_error = abs(reaction_magnitude - reference_joint_force)
        max_abs_joint_force_error = max(max_abs_joint_force_error, abs_joint_force_error)
        if step in sample_steps:
            samples.append(
                PhysicalPendulumMABDSample(
                    sample_index=len(samples),
                    step=step,
                    time_s=time_s,
                    angle_rad=angle,
                    reference_angle_rad=reference,
                    abs_angle_error_rad=abs_error,
                    phase_drift_rad=phase_drift,
                    pivot_residual_m=pivot_residual,
                    constraint_residual_norm=max_constraint_residual,
                    world_anchor_reaction_vector_n=latest_world_anchor_reaction.copy(),
                    world_anchor_reaction_magnitude_n=reaction_magnitude,
                    reference_joint_force_magnitude_n=reference_joint_force,
                    abs_joint_force_error_n=abs_joint_force_error,
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

    return PhysicalPendulumMABDRollout(
        samples=tuple(samples),
        step_count=lane.step_count,
        sample_count=len(samples),
        time_step_s=lane.time_step_s,
        rotation_mode=rotation_mode,
        max_pivot_residual_m=max_pivot_residual,
        max_constraint_residual_norm=max_constraint_residual,
        max_abs_angle_error_rad=max_abs_angle_error,
        max_phase_drift_rad=max_phase_drift,
        max_world_anchor_reaction_magnitude_n=max_world_anchor_reaction,
        max_abs_joint_force_error_n=max_abs_joint_force_error,
        solver_model_config_source=solver_model_config_source,
        finite=finite,
    )


def roll_out_physical_pendulum_mabd_development(
    config: PhysicalPendulumRunConfig,
    *,
    rotation_mode: str = "none",
) -> PhysicalPendulumMABDRollout:
    return _roll_out_physical_pendulum_mabd(
        config,
        rotation_mode=rotation_mode,
        solver_model_config_source=MANUAL_CPU_ORACLE_CONFIG_SOURCE,
        step_once=_manual_cpu_oracle_stepper(config, rotation_mode=rotation_mode),
    )


def roll_out_physical_pendulum_mabd_model_derived(
    config: PhysicalPendulumRunConfig,
    *,
    rotation_mode: str = "none",
) -> PhysicalPendulumMABDRollout:
    return _roll_out_physical_pendulum_mabd(
        config,
        rotation_mode=rotation_mode,
        solver_model_config_source=NEWTON_MODEL_DERIVED_CONFIG_SOURCE,
        step_once=_model_derived_stepper(config, rotation_mode=rotation_mode),
    )


__all__ = [
    "PhysicalPendulumMABDRollout",
    "PhysicalPendulumMABDSample",
    "NEWTON_MODEL_DERIVED_CONFIG_SOURCE",
    "NEWTON_MODEL_DERIVED_CUSTOM_FREQUENCIES",
    "physical_pendulum_mabd_angle",
    "roll_out_physical_pendulum_mabd_development",
    "roll_out_physical_pendulum_mabd_model_derived",
]
