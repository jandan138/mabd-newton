"""Newton-only M-ABD development rollout for the physical-pendulum scene."""

from __future__ import annotations

from dataclasses import dataclass
from math import atan2

import numpy as np
from newton.solvers import mabd

from .experiment_configs import PhysicalPendulumRunConfig
from .physical_pendulum_reference import (
    physical_pendulum_angle_reference,
    physical_pendulum_joint_force_reference,
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
    *,
    rotation_mode: str = "none",
) -> PhysicalPendulumMABDRollout:
    if rotation_mode not in {"none", "polar"}:
        raise ValueError("physical pendulum MABD rollout supports rotation_mode none or polar")
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
        result = mabd.solve_cpu_oracle_step(
            q=(q,),
            qd=(qd,),
            dt=lane.time_step_s,
            config=solver_config,
        )
        q = result.q[0]
        qd = result.qd[0]
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
        finite=finite,
    )


__all__ = [
    "PhysicalPendulumMABDRollout",
    "PhysicalPendulumMABDSample",
    "physical_pendulum_mabd_angle",
    "roll_out_physical_pendulum_mabd_development",
]
