"""Shared paper-value physics helpers for the single-body spinning-box scene."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Any

import numpy as np
from newton.solvers import mabd

from .experiment_configs import SpinningBoxRunConfig


@dataclass(frozen=True)
class SpinningBoxPhysicalProperties:
    cube_size_m: float
    density_kg_m3: float
    mass_kg: float
    inertia_diag_kg_m2: np.ndarray
    linear_momentum_kg_m_s: np.ndarray
    angular_momentum_kg_m2_s: np.ndarray
    linear_velocity_m_s: np.ndarray
    angular_velocity_rad_s: np.ndarray


@dataclass(frozen=True)
class SpinningBoxMABDMomentumDiagnostics:
    spatial_twist: np.ndarray
    linear_momentum_kg_m_s: np.ndarray
    angular_momentum_kg_m2_s: np.ndarray
    linear_momentum_error: float
    angular_momentum_error: float


def _paper_float(value: Any, name: str, *, positive: bool = False) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{name} must be numeric")
    if isinstance(value, int | float):
        result = float(value)
    elif isinstance(value, str) and value:
        try:
            result = float(value.split()[0])
        except ValueError as exc:
            raise ValueError(f"{name} must start with a numeric value") from exc
    else:
        raise ValueError(f"{name} must be numeric")
    if not isfinite(result):
        raise ValueError(f"{name} must be finite")
    if positive and result <= 0.0:
        raise ValueError(f"{name} must be positive")
    return result


def _paper_vector(value: Any, name: str) -> np.ndarray:
    vector = np.asarray(value, dtype=float)
    if vector.shape != (3,):
        raise ValueError(f"{name} must contain 3 numeric values")
    if not np.all(np.isfinite(vector)):
        raise ValueError(f"{name} must contain 3 finite numeric values")
    return vector


def spinning_box_physical_properties(config: SpinningBoxRunConfig) -> SpinningBoxPhysicalProperties:
    cube_size_m = _paper_float(config.paper_values.get("cube_size_m"), "cube_size_m", positive=True)
    density_kg_m3 = _paper_float(config.paper_values.get("density"), "density", positive=True)
    mass_kg = density_kg_m3 * cube_size_m**3
    inertia_diag = np.full(3, (1.0 / 6.0) * mass_kg * cube_size_m**2, dtype=float)
    linear_momentum = _paper_vector(config.paper_values.get("p0"), "p0")
    angular_momentum = _paper_vector(config.paper_values.get("L0"), "L0")
    return SpinningBoxPhysicalProperties(
        cube_size_m=cube_size_m,
        density_kg_m3=density_kg_m3,
        mass_kg=mass_kg,
        inertia_diag_kg_m2=inertia_diag,
        linear_momentum_kg_m_s=linear_momentum,
        angular_momentum_kg_m2_s=angular_momentum,
        linear_velocity_m_s=linear_momentum / mass_kg,
        angular_velocity_rad_s=angular_momentum / inertia_diag,
    )


def paper_spatial_twist_from_momenta(config: SpinningBoxRunConfig) -> np.ndarray:
    properties = spinning_box_physical_properties(config)
    return np.concatenate([properties.angular_velocity_rad_s, properties.linear_velocity_m_s])


def spinning_box_mabd_mass_diagonal(config: SpinningBoxRunConfig) -> np.ndarray:
    properties = spinning_box_physical_properties(config)
    affine_second_moment = properties.mass_kg * properties.cube_size_m**2 / 12.0
    return np.concatenate(
        [
            np.full(9, affine_second_moment, dtype=float),
            np.full(3, properties.mass_kg, dtype=float),
        ]
    )


def abd_generalized_velocity_from_paper_momenta(
    config: SpinningBoxRunConfig,
    A: np.ndarray | None = None,
) -> np.ndarray:
    A_arr = np.eye(3) if A is None else np.asarray(A, dtype=float)
    return mabd.rigid_embedding_E(A_arr) @ paper_spatial_twist_from_momenta(config)


def mabd_momentum_diagnostics(
    config: SpinningBoxRunConfig,
    q: np.ndarray,
    qd: np.ndarray,
) -> SpinningBoxMABDMomentumDiagnostics:
    properties = spinning_box_physical_properties(config)
    A, _t = mabd.unpack_q(q)
    spatial_twist = mabd.twist_map_G(A) @ np.asarray(qd, dtype=float)
    linear_momentum = properties.mass_kg * spatial_twist[3:6]
    angular_momentum = properties.inertia_diag_kg_m2 * spatial_twist[0:3]
    return SpinningBoxMABDMomentumDiagnostics(
        spatial_twist=spatial_twist,
        linear_momentum_kg_m_s=linear_momentum,
        angular_momentum_kg_m2_s=angular_momentum,
        linear_momentum_error=float(np.linalg.norm(linear_momentum - properties.linear_momentum_kg_m_s)),
        angular_momentum_error=float(np.linalg.norm(angular_momentum - properties.angular_momentum_kg_m2_s)),
    )


__all__ = [
    "SpinningBoxMABDMomentumDiagnostics",
    "SpinningBoxPhysicalProperties",
    "abd_generalized_velocity_from_paper_momenta",
    "mabd_momentum_diagnostics",
    "paper_spatial_twist_from_momenta",
    "spinning_box_mabd_mass_diagonal",
    "spinning_box_physical_properties",
]
