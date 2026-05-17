"""Torque-free RK4 reference diagnostics for the T-handle source claim."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .experiment_configs import THandleReferenceConfig, THandleRunConfig


@dataclass(frozen=True)
class THandleReferenceTrajectory:
    samples: np.ndarray
    energy_initial: float
    energy_final: float
    relative_energy_drift: float
    angular_momentum_norm_initial: float
    angular_momentum_norm_final: float
    angular_momentum_norm_drift: float
    intermediate_axis_sign_flips: int


def _reference_config(config: THandleRunConfig | THandleReferenceConfig) -> THandleReferenceConfig:
    return config.reference if isinstance(config, THandleRunConfig) else config


def _validate_reference(reference: THandleReferenceConfig) -> None:
    if reference.time_step_s <= 0.0 or not np.isfinite(reference.time_step_s):
        raise ValueError("time_step_s must be finite and positive")
    if reference.duration_s <= 0.0 or not np.isfinite(reference.duration_s):
        raise ValueError("duration_s must be finite and positive")
    if reference.sample_count < 2:
        raise ValueError("sample_count must be at least 2")
    if reference.principal_inertia_kg_m2.shape != (3,) or np.any(
        reference.principal_inertia_kg_m2 <= 0.0
    ):
        raise ValueError("principal_inertia_kg_m2 must contain 3 positive values")
    if reference.initial_angular_velocity_rad_s.shape != (3,) or not np.all(
        np.isfinite(reference.initial_angular_velocity_rad_s)
    ):
        raise ValueError("initial_angular_velocity_rad_s must contain 3 finite values")
    if reference.intermediate_axis_index not in (0, 1, 2):
        raise ValueError("intermediate_axis_index must be 0, 1, or 2")
    if reference.gravity_m_s2.shape != (3,) or not np.allclose(
        reference.gravity_m_s2,
        np.zeros(3),
        rtol=0.0,
        atol=1.0e-15,
    ):
        raise ValueError("T-handle RK4 reference is source-backed only for zero gravity")
    step_count_float = reference.duration_s / reference.time_step_s
    step_count = round(step_count_float)
    if not np.isclose(step_count_float, float(step_count), rtol=0.0, atol=1.0e-10):
        raise ValueError("duration_s must be an integer multiple of time_step_s")
    if reference.sample_count > step_count + 1:
        raise ValueError("sample_count must be at most step_count + 1")


def _torque_free_rhs(omega: np.ndarray, inertia: np.ndarray) -> np.ndarray:
    ix, iy, iz = inertia
    wx, wy, wz = omega
    return np.asarray(
        [
            ((iy - iz) / ix) * wy * wz,
            ((iz - ix) / iy) * wz * wx,
            ((ix - iy) / iz) * wx * wy,
        ],
        dtype=float,
    )


def _rk4_step(omega: np.ndarray, inertia: np.ndarray, dt: float) -> np.ndarray:
    k1 = _torque_free_rhs(omega, inertia)
    k2 = _torque_free_rhs(omega + 0.5 * dt * k1, inertia)
    k3 = _torque_free_rhs(omega + 0.5 * dt * k2, inertia)
    k4 = _torque_free_rhs(omega + dt * k3, inertia)
    return omega + (dt / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)


def _energy(omega: np.ndarray, inertia: np.ndarray) -> float:
    return float(0.5 * np.dot(inertia, omega * omega))


def _angular_momentum_norm(omega: np.ndarray, inertia: np.ndarray) -> float:
    return float(np.linalg.norm(inertia * omega))


def _sign(value: float) -> int:
    if value > 0.0:
        return 1
    if value < 0.0:
        return -1
    return 0


def roll_out_t_handle_rk4_reference(
    config: THandleRunConfig | THandleReferenceConfig,
) -> THandleReferenceTrajectory:
    reference = _reference_config(config)
    _validate_reference(reference)

    inertia = reference.principal_inertia_kg_m2.astype(float, copy=True)
    omega = reference.initial_angular_velocity_rad_s.astype(float, copy=True)
    dt = float(reference.time_step_s)
    step_count = int(round(reference.duration_s / dt))
    sample_indices = set(
        int(index)
        for index in np.rint(np.linspace(0, step_count, reference.sample_count)).astype(int)
    )

    energy_initial = _energy(omega, inertia)
    momentum_norm_initial = _angular_momentum_norm(omega, inertia)
    if energy_initial <= 0.0 or momentum_norm_initial <= 0.0:
        raise ValueError("initial angular velocity must produce nonzero energy and angular momentum")

    rows: list[list[float]] = []
    axis = int(reference.intermediate_axis_index)
    previous_sign = _sign(float(omega[axis]))
    sign_flips = 0

    for step in range(step_count + 1):
        if step in sample_indices:
            rows.append([step * dt, float(omega[0]), float(omega[1]), float(omega[2])])
        if step == step_count:
            break
        omega_next = _rk4_step(omega, inertia, dt)
        current_sign = _sign(float(omega_next[axis]))
        if current_sign != 0:
            if previous_sign != 0 and current_sign != previous_sign:
                sign_flips += 1
            previous_sign = current_sign
        omega = omega_next

    energy_final = _energy(omega, inertia)
    momentum_norm_final = _angular_momentum_norm(omega, inertia)
    return THandleReferenceTrajectory(
        samples=np.asarray(rows, dtype=float),
        energy_initial=energy_initial,
        energy_final=energy_final,
        relative_energy_drift=(energy_final - energy_initial) / energy_initial,
        angular_momentum_norm_initial=momentum_norm_initial,
        angular_momentum_norm_final=momentum_norm_final,
        angular_momentum_norm_drift=(
            (momentum_norm_final - momentum_norm_initial) / momentum_norm_initial
        ),
        intermediate_axis_sign_flips=sign_flips,
    )


__all__ = [
    "THandleReferenceTrajectory",
    "roll_out_t_handle_rk4_reference",
]
