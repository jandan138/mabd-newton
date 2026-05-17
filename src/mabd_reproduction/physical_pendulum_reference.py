"""Analytic reference curve for the paper physical-pendulum scene."""

from __future__ import annotations

from math import isfinite, pi
from numbers import Real
from typing import Iterable

import numpy as np
from scipy import special


def _validate_kappa(kappa: float) -> float:
    if not isinstance(kappa, Real) or isinstance(kappa, bool):
        raise ValueError("kappa must be a finite scalar in (0, 1)")
    value = float(kappa)
    if not isfinite(value) or value <= 0.0 or value >= 1.0:
        raise ValueError("kappa must be a finite scalar in (0, 1)")
    return value


def _validate_omega_lin(omega_lin: float) -> float:
    if not isinstance(omega_lin, Real) or isinstance(omega_lin, bool):
        raise ValueError("omega_lin must be finite and positive")
    value = float(omega_lin)
    if not isfinite(value) or value <= 0.0:
        raise ValueError("omega_lin must be finite and positive")
    return value


def _validate_positive_scalar(value: float, *, name: str) -> float:
    if not isinstance(value, Real) or isinstance(value, bool):
        raise ValueError(f"{name} must be finite and positive")
    result = float(value)
    if not isfinite(result) or result <= 0.0:
        raise ValueError(f"{name} must be finite and positive")
    return result


def _validate_times(times: Iterable[float]) -> np.ndarray:
    values = np.asarray(list(times), dtype=float)
    if values.ndim != 1:
        raise ValueError("times must be a one-dimensional sequence")
    if values.size == 0:
        raise ValueError("times must be non-empty")
    if not np.all(np.isfinite(values)) or np.any(values < 0.0):
        raise ValueError("times must contain finite nonnegative values")
    return values


def physical_pendulum_complete_elliptic_k(kappa: float) -> float:
    """Return K(kappa) using SciPy's parameterized m=kappa**2 convention."""

    value = _validate_kappa(kappa)
    return float(special.ellipk(value * value))


def physical_pendulum_period_s(*, kappa: float, omega_lin: float) -> float:
    """Return the analytic-reference oscillation period."""

    return 4.0 * physical_pendulum_complete_elliptic_k(kappa) / _validate_omega_lin(
        omega_lin
    )


def physical_pendulum_angle_reference(
    times: Iterable[float],
    *,
    kappa: float,
    omega_lin: float,
) -> np.ndarray:
    """Evaluate the paper elliptic-integral physical-pendulum angle formula.

    The paper writes ``sn(..., kappa)`` with kappa as elliptic modulus. SciPy
    uses the parameter ``m``, so this implementation passes ``kappa**2``.
    """

    kappa_value = _validate_kappa(kappa)
    omega_value = _validate_omega_lin(omega_lin)
    time_values = _validate_times(times)
    parameter_m = kappa_value * kappa_value
    complete = special.ellipk(parameter_m)
    sn, _cn, _dn, _ph = special.ellipj(complete - omega_value * time_values, parameter_m)
    return np.asarray(pi / 2.0 - 2.0 * np.arcsin(kappa_value * sn), dtype=float)


def physical_pendulum_angular_velocity_reference(
    times: Iterable[float],
    *,
    kappa: float,
    omega_lin: float,
) -> np.ndarray:
    """Evaluate the analytic derivative of the paper angle reference."""

    kappa_value = _validate_kappa(kappa)
    omega_value = _validate_omega_lin(omega_lin)
    time_values = _validate_times(times)
    parameter_m = kappa_value * kappa_value
    complete = special.ellipk(parameter_m)
    sn, cn, dn, _ph = special.ellipj(complete - omega_value * time_values, parameter_m)
    denominator = np.sqrt(np.maximum(0.0, 1.0 - parameter_m * sn * sn))
    velocities = 2.0 * kappa_value * omega_value * cn * dn / denominator
    return np.asarray(velocities, dtype=float)


def physical_pendulum_joint_force_reference(
    times: Iterable[float],
    *,
    kappa: float,
    omega_lin: float,
    mass_kg: float,
    length_m: float,
    gravity_magnitude: float,
) -> np.ndarray:
    """Return the scalar-pendulum radial joint-force magnitude reference."""

    mass = _validate_positive_scalar(mass_kg, name="mass_kg")
    length = _validate_positive_scalar(length_m, name="length_m")
    gravity = _validate_positive_scalar(gravity_magnitude, name="gravity_magnitude")
    angles = physical_pendulum_angle_reference(times, kappa=kappa, omega_lin=omega_lin)
    velocities = physical_pendulum_angular_velocity_reference(
        times,
        kappa=kappa,
        omega_lin=omega_lin,
    )
    forces = mass * np.abs(length * velocities * velocities + gravity * np.sin(angles))
    return np.asarray(forces, dtype=float)


__all__ = [
    "physical_pendulum_angle_reference",
    "physical_pendulum_angular_velocity_reference",
    "physical_pendulum_complete_elliptic_k",
    "physical_pendulum_joint_force_reference",
    "physical_pendulum_period_s",
]
