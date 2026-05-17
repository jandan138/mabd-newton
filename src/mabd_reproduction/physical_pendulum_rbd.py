"""Scalar implicit-RBD development rollout for the physical-pendulum scene."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .experiment_configs import PhysicalPendulumRunConfig
from .physical_pendulum_reference import physical_pendulum_angle_reference


@dataclass(frozen=True)
class PhysicalPendulumRBDSample:
    sample_index: int
    step: int
    time_s: float
    angle_rad: float
    previous_angle_rad: float
    angular_velocity_rad_s: float
    reference_angle_rad: float
    abs_angle_error_rad: float
    phase_drift_rad: float
    implicit_residual: float
    length_constraint_error_m: float
    joint_force_magnitude_n: float


@dataclass(frozen=True)
class PhysicalPendulumRBDRollout:
    samples: tuple[PhysicalPendulumRBDSample, ...]
    step_count: int
    sample_count: int
    time_step_s: float
    max_abs_angle_error_rad: float
    max_phase_drift_rad: float
    max_implicit_residual: float
    max_length_constraint_error_m: float
    max_joint_force_magnitude_n: float
    finite: bool


def physical_pendulum_rbd_point(angle_rad: float, *, length_m: float) -> np.ndarray:
    return np.asarray(
        [
            length_m * np.cos(angle_rad),
            -length_m * np.sin(angle_rad),
            0.0,
        ],
        dtype=float,
    )


def _sample_steps(step_count: int, sample_count: int) -> tuple[int, ...]:
    return tuple(int(round(value)) for value in np.linspace(0, step_count, sample_count))


def _implicit_angle_step(
    theta: float,
    omega: float,
    *,
    h: float,
    omega_lin: float,
    iteration_limit: int,
    residual_tolerance: float,
) -> tuple[float, float, float]:
    theta_next = theta + h * omega
    omega_lin_sq = omega_lin * omega_lin
    residual = 0.0
    for _ in range(iteration_limit):
        residual = theta_next - theta - h * (omega + h * omega_lin_sq * np.cos(theta_next))
        derivative = 1.0 + h * h * omega_lin_sq * np.sin(theta_next)
        theta_next -= residual / derivative
        if abs(residual) <= residual_tolerance:
            break
    omega_next = (theta_next - theta) / h
    kinematic_residual = theta_next - theta - h * omega_next
    dynamic_residual = omega_next - omega - h * omega_lin_sq * np.cos(theta_next)
    return (
        float(theta_next),
        float(omega_next),
        float(max(abs(kinematic_residual), abs(dynamic_residual))),
    )


def _joint_force_magnitude(
    *,
    mass_kg: float,
    length_m: float,
    gravity_magnitude: float,
    angle_rad: float,
    angular_velocity_rad_s: float,
) -> float:
    radial_acceleration_term = length_m * angular_velocity_rad_s * angular_velocity_rad_s
    gravity_radial_term = gravity_magnitude * np.sin(angle_rad)
    return float(mass_kg * abs(radial_acceleration_term + gravity_radial_term))


def roll_out_physical_pendulum_rbd_baseline(
    config: PhysicalPendulumRunConfig,
) -> PhysicalPendulumRBDRollout:
    lane = config.rbd_baseline
    theta = float(lane.initial_angle_rad)
    omega = float(lane.initial_angular_velocity_rad_s)
    previous_theta = theta
    sample_steps = set(_sample_steps(lane.step_count, lane.sample_count))
    gravity_magnitude = float(np.linalg.norm(lane.gravity_m_s2))
    omega_lin = (gravity_magnitude / lane.length_m) ** 0.5

    samples: list[PhysicalPendulumRBDSample] = []
    max_abs_angle_error = 0.0
    max_phase_drift = 0.0
    max_implicit_residual = 0.0
    max_length_constraint_error = 0.0
    max_joint_force = 0.0
    finite = True
    step_residual = 0.0

    for step in range(lane.step_count + 1):
        time_s = step * lane.time_step_s
        reference = float(
            physical_pendulum_angle_reference(
                np.asarray([time_s], dtype=float),
                kappa=config.reference.kappa,
                omega_lin=config.reference.omega_lin_rad_s,
            )[0]
        )
        phase_drift = theta - reference
        abs_error = abs(phase_drift)
        point = physical_pendulum_rbd_point(theta, length_m=lane.length_m)
        length_error = abs(float(np.linalg.norm(point)) - lane.length_m)
        joint_force = _joint_force_magnitude(
            mass_kg=lane.mass_kg,
            length_m=lane.length_m,
            gravity_magnitude=gravity_magnitude,
            angle_rad=theta,
            angular_velocity_rad_s=omega,
        )

        max_abs_angle_error = max(max_abs_angle_error, abs_error)
        max_phase_drift = max(max_phase_drift, abs(phase_drift))
        max_length_constraint_error = max(max_length_constraint_error, length_error)
        max_joint_force = max(max_joint_force, joint_force)
        finite = finite and bool(
            np.all(
                np.isfinite(
                    [
                        theta,
                        previous_theta,
                        omega,
                        reference,
                        phase_drift,
                        step_residual,
                        length_error,
                        joint_force,
                    ]
                )
            )
        )

        if step in sample_steps:
            samples.append(
                PhysicalPendulumRBDSample(
                    sample_index=len(samples),
                    step=step,
                    time_s=time_s,
                    angle_rad=theta,
                    previous_angle_rad=previous_theta,
                    angular_velocity_rad_s=omega,
                    reference_angle_rad=reference,
                    abs_angle_error_rad=abs_error,
                    phase_drift_rad=phase_drift,
                    implicit_residual=step_residual,
                    length_constraint_error_m=length_error,
                    joint_force_magnitude_n=joint_force,
                )
            )

        if step == lane.step_count:
            break

        previous_theta = theta
        theta, omega, step_residual = _implicit_angle_step(
            theta,
            omega,
            h=lane.time_step_s,
            omega_lin=omega_lin,
            iteration_limit=lane.newton_iteration_limit,
            residual_tolerance=lane.newton_residual_tolerance,
        )
        max_implicit_residual = max(max_implicit_residual, step_residual)

    return PhysicalPendulumRBDRollout(
        samples=tuple(samples),
        step_count=lane.step_count,
        sample_count=len(samples),
        time_step_s=lane.time_step_s,
        max_abs_angle_error_rad=max_abs_angle_error,
        max_phase_drift_rad=max_phase_drift,
        max_implicit_residual=max_implicit_residual,
        max_length_constraint_error_m=max_length_constraint_error,
        max_joint_force_magnitude_n=max_joint_force,
        finite=finite,
    )


__all__ = [
    "PhysicalPendulumRBDSample",
    "PhysicalPendulumRBDRollout",
    "physical_pendulum_rbd_point",
    "roll_out_physical_pendulum_rbd_baseline",
]
