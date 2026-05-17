"""Fixed-pivot heavy-top RK4 reference diagnostics."""

from __future__ import annotations

from dataclasses import dataclass
from math import atan2, cos, degrees, radians, sin

import numpy as np

from .experiment_configs import HeavyTopReferenceConfig, HeavyTopRunConfig


@dataclass(frozen=True)
class HeavyTopReferenceTrajectory:
    samples: np.ndarray
    energy_initial: float
    energy_final: float
    relative_energy_drift: float
    angular_momentum_norm_initial: float
    angular_momentum_norm_final: float
    angular_momentum_norm_drift: float
    min_nutation_angle_deg: float
    max_nutation_angle_deg: float
    max_abs_precession_velocity_rad_s: float


def _reference_config(
    config: HeavyTopRunConfig | HeavyTopReferenceConfig,
) -> HeavyTopReferenceConfig:
    return config.reference if isinstance(config, HeavyTopRunConfig) else config


def _validate_reference(reference: HeavyTopReferenceConfig) -> None:
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
    if reference.mass_kg <= 0.0 or not np.isfinite(reference.mass_kg):
        raise ValueError("mass_kg must be finite and positive")
    if (
        reference.pivot_to_com_m.shape != (3,)
        or not np.all(np.isfinite(reference.pivot_to_com_m))
        or np.linalg.norm(reference.pivot_to_com_m) <= 0.0
    ):
        raise ValueError("pivot_to_com_m must contain 3 finite values and be nonzero")
    if not (
        reference.gravity_m_s2.shape == (3,)
        and np.isclose(reference.gravity_m_s2[0], 0.0, rtol=0.0, atol=1.0e-15)
        and reference.gravity_m_s2[1] < 0.0
        and np.isclose(reference.gravity_m_s2[2], 0.0, rtol=0.0, atol=1.0e-15)
    ):
        raise ValueError("gravity_m_s2 must point along the negative y axis")
    if reference.initial_tilt_deg <= 0.0 or not np.isfinite(reference.initial_tilt_deg):
        raise ValueError("initial_tilt_deg must be finite and positive")
    if reference.initial_spin_rad_s <= 0.0 or not np.isfinite(reference.initial_spin_rad_s):
        raise ValueError("initial_spin_rad_s must be finite and positive")
    step_count_float = reference.duration_s / reference.time_step_s
    step_count = round(step_count_float)
    if not np.isclose(step_count_float, float(step_count), rtol=0.0, atol=1.0e-10):
        raise ValueError("duration_s must be an integer multiple of time_step_s")
    if reference.sample_count > step_count + 1:
        raise ValueError("sample_count must be at most step_count + 1")


def _quat_multiply(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    aw, ax, ay, az = a
    bw, bx, by, bz = b
    return np.asarray(
        [
            aw * bw - ax * bx - ay * by - az * bz,
            aw * bx + ax * bw + ay * bz - az * by,
            aw * by - ax * bz + ay * bw + az * bx,
            aw * bz + ax * by - ay * bx + az * bw,
        ],
        dtype=float,
    )


def _normalize_quat(q: np.ndarray) -> np.ndarray:
    norm = float(np.linalg.norm(q))
    if norm <= 0.0 or not np.isfinite(norm):
        raise ValueError("orientation quaternion became invalid")
    result = q / norm
    return result if result[0] >= 0.0 else -result


def _rotation_matrix_from_quat(q: np.ndarray) -> np.ndarray:
    w, x, y, z = q
    return np.asarray(
        [
            [1.0 - 2.0 * (y * y + z * z), 2.0 * (x * y - z * w), 2.0 * (x * z + y * w)],
            [2.0 * (x * y + z * w), 1.0 - 2.0 * (x * x + z * z), 2.0 * (y * z - x * w)],
            [2.0 * (x * z - y * w), 2.0 * (y * z + x * w), 1.0 - 2.0 * (x * x + y * y)],
        ],
        dtype=float,
    )


def _quat_from_rotation_matrix(matrix: np.ndarray) -> np.ndarray:
    trace = float(np.trace(matrix))
    if trace > 0.0:
        scale = (trace + 1.0) ** 0.5 * 2.0
        return _normalize_quat(
            np.asarray(
                [
                    0.25 * scale,
                    (matrix[2, 1] - matrix[1, 2]) / scale,
                    (matrix[0, 2] - matrix[2, 0]) / scale,
                    (matrix[1, 0] - matrix[0, 1]) / scale,
                ],
                dtype=float,
            )
        )

    diagonal = np.diag(matrix)
    axis = int(np.argmax(diagonal))
    if axis == 0:
        scale = (1.0 + matrix[0, 0] - matrix[1, 1] - matrix[2, 2]) ** 0.5 * 2.0
        q = [
            (matrix[2, 1] - matrix[1, 2]) / scale,
            0.25 * scale,
            (matrix[0, 1] + matrix[1, 0]) / scale,
            (matrix[0, 2] + matrix[2, 0]) / scale,
        ]
    elif axis == 1:
        scale = (1.0 + matrix[1, 1] - matrix[0, 0] - matrix[2, 2]) ** 0.5 * 2.0
        q = [
            (matrix[0, 2] - matrix[2, 0]) / scale,
            (matrix[0, 1] + matrix[1, 0]) / scale,
            0.25 * scale,
            (matrix[1, 2] + matrix[2, 1]) / scale,
        ]
    else:
        scale = (1.0 + matrix[2, 2] - matrix[0, 0] - matrix[1, 1]) ** 0.5 * 2.0
        q = [
            (matrix[1, 0] - matrix[0, 1]) / scale,
            (matrix[0, 2] + matrix[2, 0]) / scale,
            (matrix[1, 2] + matrix[2, 1]) / scale,
            0.25 * scale,
        ]
    return _normalize_quat(np.asarray(q, dtype=float))


def _initial_orientation(initial_tilt_deg: float) -> np.ndarray:
    theta = radians(initial_tilt_deg)
    axis_z = np.asarray([sin(theta), cos(theta), 0.0], dtype=float)
    axis_x = np.asarray([cos(theta), -sin(theta), 0.0], dtype=float)
    axis_y = np.cross(axis_z, axis_x)
    matrix = np.column_stack((axis_x, axis_y, axis_z))
    return _quat_from_rotation_matrix(matrix)


def _rhs(
    q: np.ndarray,
    omega: np.ndarray,
    *,
    inertia: np.ndarray,
    mass_kg: float,
    pivot_to_com_m: np.ndarray,
    gravity_m_s2: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    rotation = _rotation_matrix_from_quat(_normalize_quat(q))
    force_body = rotation.T @ (mass_kg * gravity_m_s2)
    torque_body = np.cross(pivot_to_com_m, force_body)
    angular_momentum_body = inertia * omega
    omega_dot = (torque_body - np.cross(omega, angular_momentum_body)) / inertia
    q_dot = 0.5 * _quat_multiply(q, np.asarray([0.0, omega[0], omega[1], omega[2]]))
    return q_dot, omega_dot


def _state_add(
    q: np.ndarray,
    omega: np.ndarray,
    scale: float,
    derivative: tuple[np.ndarray, np.ndarray],
) -> tuple[np.ndarray, np.ndarray]:
    q_dot, omega_dot = derivative
    return q + scale * q_dot, omega + scale * omega_dot


def _rk4_step(
    q: np.ndarray,
    omega: np.ndarray,
    *,
    dt: float,
    inertia: np.ndarray,
    mass_kg: float,
    pivot_to_com_m: np.ndarray,
    gravity_m_s2: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    kwargs = {
        "inertia": inertia,
        "mass_kg": mass_kg,
        "pivot_to_com_m": pivot_to_com_m,
        "gravity_m_s2": gravity_m_s2,
    }
    k1 = _rhs(q, omega, **kwargs)
    q2, omega2 = _state_add(q, omega, 0.5 * dt, k1)
    k2 = _rhs(q2, omega2, **kwargs)
    q3, omega3 = _state_add(q, omega, 0.5 * dt, k2)
    k3 = _rhs(q3, omega3, **kwargs)
    q4, omega4 = _state_add(q, omega, dt, k3)
    k4 = _rhs(q4, omega4, **kwargs)
    q_next = q + (dt / 6.0) * (k1[0] + 2.0 * k2[0] + 2.0 * k3[0] + k4[0])
    omega_next = omega + (dt / 6.0) * (k1[1] + 2.0 * k2[1] + 2.0 * k3[1] + k4[1])
    return _normalize_quat(q_next), omega_next


def _energy(
    q: np.ndarray,
    omega: np.ndarray,
    *,
    inertia: np.ndarray,
    mass_kg: float,
    pivot_to_com_m: np.ndarray,
    gravity_m_s2: np.ndarray,
) -> float:
    rotation = _rotation_matrix_from_quat(q)
    rotational = 0.5 * float(np.dot(inertia, omega * omega))
    potential = -mass_kg * float(np.dot(gravity_m_s2, rotation @ pivot_to_com_m))
    return rotational + potential


def _angular_momentum_norm(omega: np.ndarray, inertia: np.ndarray) -> float:
    return float(np.linalg.norm(inertia * omega))


def _top_axis_world(q: np.ndarray) -> np.ndarray:
    return _rotation_matrix_from_quat(q)[:, 2]


def _nutation_angle_deg(q: np.ndarray) -> float:
    axis = _top_axis_world(q)
    return degrees(float(np.arccos(np.clip(axis[1], -1.0, 1.0))))


def _precession_angle_rad(q: np.ndarray) -> float:
    axis = _top_axis_world(q)
    return atan2(float(axis[2]), float(axis[0]))


def _normalize_quat_components(
    qw: float,
    qx: float,
    qy: float,
    qz: float,
) -> tuple[float, float, float, float]:
    norm = (qw * qw + qx * qx + qy * qy + qz * qz) ** 0.5
    if norm <= 0.0 or not np.isfinite(norm):
        raise ValueError("orientation quaternion became invalid")
    qw /= norm
    qx /= norm
    qy /= norm
    qz /= norm
    if qw < 0.0:
        return -qw, -qx, -qy, -qz
    return qw, qx, qy, qz


def _rotation_entries(
    qw: float,
    qx: float,
    qy: float,
    qz: float,
) -> tuple[float, float, float, float, float, float, float, float, float]:
    return (
        1.0 - 2.0 * (qy * qy + qz * qz),
        2.0 * (qx * qy - qz * qw),
        2.0 * (qx * qz + qy * qw),
        2.0 * (qx * qy + qz * qw),
        1.0 - 2.0 * (qx * qx + qz * qz),
        2.0 * (qy * qz - qx * qw),
        2.0 * (qx * qz - qy * qw),
        2.0 * (qy * qz + qx * qw),
        1.0 - 2.0 * (qx * qx + qy * qy),
    )


def _rhs_scalar(
    state: tuple[float, float, float, float, float, float, float],
    *,
    inertia: tuple[float, float, float],
    mass_kg: float,
    pivot_to_com_m: tuple[float, float, float],
    gravity_m_s2: tuple[float, float, float],
) -> tuple[float, float, float, float, float, float, float]:
    qw, qx, qy, qz, wx, wy, wz = state
    nqw, nqx, nqy, nqz = _normalize_quat_components(qw, qx, qy, qz)
    r00, r01, r02, r10, r11, r12, r20, r21, r22 = _rotation_entries(nqw, nqx, nqy, nqz)
    gx, gy, gz = gravity_m_s2
    fx = mass_kg * (r00 * gx + r10 * gy + r20 * gz)
    fy = mass_kg * (r01 * gx + r11 * gy + r21 * gz)
    fz = mass_kg * (r02 * gx + r12 * gy + r22 * gz)
    px, py, pz = pivot_to_com_m
    tau_x = py * fz - pz * fy
    tau_y = pz * fx - px * fz
    tau_z = px * fy - py * fx
    ix, iy, iz = inertia
    lx = ix * wx
    ly = iy * wy
    lz = iz * wz
    domega_x = (tau_x - (wy * lz - wz * ly)) / ix
    domega_y = (tau_y - (wz * lx - wx * lz)) / iy
    domega_z = (tau_z - (wx * ly - wy * lx)) / iz
    return (
        -0.5 * (qx * wx + qy * wy + qz * wz),
        0.5 * (qw * wx + qy * wz - qz * wy),
        0.5 * (qw * wy - qx * wz + qz * wx),
        0.5 * (qw * wz + qx * wy - qy * wx),
        domega_x,
        domega_y,
        domega_z,
    )


def _add_state_scalar(
    state: tuple[float, float, float, float, float, float, float],
    scale: float,
    derivative: tuple[float, float, float, float, float, float, float],
) -> tuple[float, float, float, float, float, float, float]:
    return tuple(value + scale * delta for value, delta in zip(state, derivative, strict=True))


def _rk4_step_scalar(
    state: tuple[float, float, float, float, float, float, float],
    *,
    dt: float,
    inertia: tuple[float, float, float],
    mass_kg: float,
    pivot_to_com_m: tuple[float, float, float],
    gravity_m_s2: tuple[float, float, float],
) -> tuple[float, float, float, float, float, float, float]:
    kwargs = {
        "inertia": inertia,
        "mass_kg": mass_kg,
        "pivot_to_com_m": pivot_to_com_m,
        "gravity_m_s2": gravity_m_s2,
    }
    k1 = _rhs_scalar(state, **kwargs)
    k2 = _rhs_scalar(_add_state_scalar(state, 0.5 * dt, k1), **kwargs)
    k3 = _rhs_scalar(_add_state_scalar(state, 0.5 * dt, k2), **kwargs)
    k4 = _rhs_scalar(_add_state_scalar(state, dt, k3), **kwargs)
    next_state = tuple(
        value + (dt / 6.0) * (d1 + 2.0 * d2 + 2.0 * d3 + d4)
        for value, d1, d2, d3, d4 in zip(state, k1, k2, k3, k4, strict=True)
    )
    qw, qx, qy, qz = _normalize_quat_components(*next_state[:4])
    return (qw, qx, qy, qz, next_state[4], next_state[5], next_state[6])


def _energy_scalar(
    state: tuple[float, float, float, float, float, float, float],
    *,
    inertia: tuple[float, float, float],
    mass_kg: float,
    pivot_to_com_m: tuple[float, float, float],
    gravity_m_s2: tuple[float, float, float],
) -> float:
    qw, qx, qy, qz, wx, wy, wz = state
    r00, r01, r02, r10, r11, r12, r20, r21, r22 = _rotation_entries(qw, qx, qy, qz)
    ix, iy, iz = inertia
    px, py, pz = pivot_to_com_m
    gx, gy, gz = gravity_m_s2
    rx = r00 * px + r01 * py + r02 * pz
    ry = r10 * px + r11 * py + r12 * pz
    rz = r20 * px + r21 * py + r22 * pz
    rotational = 0.5 * (ix * wx * wx + iy * wy * wy + iz * wz * wz)
    potential = -mass_kg * (gx * rx + gy * ry + gz * rz)
    return rotational + potential


def _angular_momentum_norm_scalar(
    state: tuple[float, float, float, float, float, float, float],
    inertia: tuple[float, float, float],
) -> float:
    _, _, _, _, wx, wy, wz = state
    ix, iy, iz = inertia
    return ((ix * wx) ** 2 + (iy * wy) ** 2 + (iz * wz) ** 2) ** 0.5


def _nutation_angle_deg_scalar(
    state: tuple[float, float, float, float, float, float, float],
) -> float:
    qw, qx, qy, qz = state[:4]
    _, _, _, _, _, r12, _, _, _ = _rotation_entries(qw, qx, qy, qz)
    return degrees(float(np.arccos(np.clip(r12, -1.0, 1.0))))


def _precession_angle_rad_scalar(
    state: tuple[float, float, float, float, float, float, float],
) -> float:
    qw, qx, qy, qz = state[:4]
    _, _, r02, _, _, _, _, _, r22 = _rotation_entries(qw, qx, qy, qz)
    return atan2(r22, r02)


def roll_out_heavy_top_rk4_reference(
    config: HeavyTopRunConfig | HeavyTopReferenceConfig,
) -> HeavyTopReferenceTrajectory:
    reference = _reference_config(config)
    _validate_reference(reference)

    inertia = tuple(float(value) for value in reference.principal_inertia_kg_m2)
    initial_q = _initial_orientation(reference.initial_tilt_deg)
    state = (
        float(initial_q[0]),
        float(initial_q[1]),
        float(initial_q[2]),
        float(initial_q[3]),
        0.0,
        0.0,
        float(reference.initial_spin_rad_s),
    )
    pivot_to_com = tuple(float(value) for value in reference.pivot_to_com_m)
    gravity = tuple(float(value) for value in reference.gravity_m_s2)
    dt = float(reference.time_step_s)
    step_count = int(round(reference.duration_s / dt))
    sample_indices = set(
        int(index)
        for index in np.rint(np.linspace(0, step_count, reference.sample_count)).astype(int)
    )

    energy_initial = _energy_scalar(
        state,
        inertia=inertia,
        mass_kg=reference.mass_kg,
        pivot_to_com_m=pivot_to_com,
        gravity_m_s2=gravity,
    )
    momentum_norm_initial = _angular_momentum_norm_scalar(state, inertia)
    if abs(energy_initial) <= 1.0e-15 or momentum_norm_initial <= 0.0:
        raise ValueError("initial state must produce nonzero energy and angular momentum")

    sample_times: list[float] = []
    nutation_angles_deg: list[float] = []
    precession_angles_rad: list[float] = []

    for step in range(step_count + 1):
        if step in sample_indices:
            sample_times.append(step * dt)
            nutation_angles_deg.append(_nutation_angle_deg_scalar(state))
            precession_angles_rad.append(_precession_angle_rad_scalar(state))
        if step == step_count:
            break
        state = _rk4_step_scalar(
            state,
            dt=dt,
            inertia=inertia,
            mass_kg=reference.mass_kg,
            pivot_to_com_m=pivot_to_com,
            gravity_m_s2=gravity,
        )

    times = np.asarray(sample_times, dtype=float)
    nutation = np.asarray(nutation_angles_deg, dtype=float)
    precession = np.unwrap(np.asarray(precession_angles_rad, dtype=float))
    precession_velocity = np.zeros_like(precession)
    if len(precession) > 1:
        precession_velocity[1:] = np.diff(precession) / np.diff(times)

    energy_final = _energy_scalar(
        state,
        inertia=inertia,
        mass_kg=reference.mass_kg,
        pivot_to_com_m=pivot_to_com,
        gravity_m_s2=gravity,
    )
    momentum_norm_final = _angular_momentum_norm_scalar(state, inertia)
    samples = np.column_stack((times, nutation, precession, precession_velocity))
    return HeavyTopReferenceTrajectory(
        samples=samples,
        energy_initial=energy_initial,
        energy_final=energy_final,
        relative_energy_drift=(energy_final - energy_initial) / energy_initial,
        angular_momentum_norm_initial=momentum_norm_initial,
        angular_momentum_norm_final=momentum_norm_final,
        angular_momentum_norm_drift=(
            (momentum_norm_final - momentum_norm_initial) / momentum_norm_initial
        ),
        min_nutation_angle_deg=float(np.min(nutation)),
        max_nutation_angle_deg=float(np.max(nutation)),
        max_abs_precession_velocity_rad_s=float(np.max(np.abs(precession_velocity))),
    )


__all__ = [
    "HeavyTopReferenceTrajectory",
    "roll_out_heavy_top_rk4_reference",
]
