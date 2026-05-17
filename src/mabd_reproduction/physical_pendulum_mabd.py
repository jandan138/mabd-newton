"""Newton-only M-ABD development rollout for the physical-pendulum scene."""

from __future__ import annotations

from dataclasses import dataclass
from math import atan2

import numpy as np
from newton.solvers import mabd

from .experiment_configs import PhysicalPendulumRunConfig
from .physical_pendulum_reference import physical_pendulum_angle_reference


@dataclass(frozen=True)
class PhysicalPendulumMABDSample:
    sample_index: int
    step: int
    time_s: float
    angle_rad: float
    reference_angle_rad: float
    abs_angle_error_rad: float
    pivot_residual_m: float
    constraint_residual_norm: float


@dataclass(frozen=True)
class PhysicalPendulumMABDRollout:
    samples: tuple[PhysicalPendulumMABDSample, ...]
    step_count: int
    sample_count: int
    time_step_s: float
    max_pivot_residual_m: float
    max_constraint_residual_norm: float
    max_abs_angle_error_rad: float
    finite: bool


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


def roll_out_physical_pendulum_mabd_development(
    config: PhysicalPendulumRunConfig,
) -> PhysicalPendulumMABDRollout:
    lane = config.mabd_development
    body = mabd.MABDCPUOracleBody(
        precompute=mabd.SingleBodyABDPrecompute.from_points(
            lane.rest_points_m,
            lane.masses_kg,
        ),
        rest_q=lane.initial_q,
        rotation_mode="none",
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

    q = lane.initial_q.copy()
    qd = lane.initial_qd.copy()
    sample_steps = set(_sample_steps(lane.step_count, lane.sample_count))
    samples: list[PhysicalPendulumMABDSample] = []
    max_pivot_residual = 0.0
    max_constraint_residual = 0.0
    max_abs_angle_error = 0.0
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
        max_abs_angle_error = max(max_abs_angle_error, abs_error)
        if step in sample_steps:
            samples.append(
                PhysicalPendulumMABDSample(
                    sample_index=len(samples),
                    step=step,
                    time_s=time_s,
                    angle_rad=angle,
                    reference_angle_rad=reference,
                    abs_angle_error_rad=abs_error,
                    pivot_residual_m=pivot_residual,
                    constraint_residual_norm=max_constraint_residual,
                )
            )

        if step == lane.step_count:
            break
        result = mabd.solve_cpu_oracle_step(
            q=(q,),
            qd=(qd,),
            dt=lane.time_step_s,
            config=solver_config,
        )
        q = result.q[0]
        qd = result.qd[0]
        max_constraint_residual = max(max_constraint_residual, result.constraint_residual_norm)

    return PhysicalPendulumMABDRollout(
        samples=tuple(samples),
        step_count=lane.step_count,
        sample_count=len(samples),
        time_step_s=lane.time_step_s,
        max_pivot_residual_m=max_pivot_residual,
        max_constraint_residual_norm=max_constraint_residual,
        max_abs_angle_error_rad=max_abs_angle_error,
        finite=finite,
    )


__all__ = [
    "PhysicalPendulumMABDRollout",
    "PhysicalPendulumMABDSample",
    "physical_pendulum_mabd_angle",
    "roll_out_physical_pendulum_mabd_development",
]
