# SPDX-FileCopyrightText: Copyright (c) 2026 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from .affine_math import (
    apply_no_polar_increment_rotation,
    apply_no_polar_rhs_rotation,
    apply_polar_increment_rotation,
    apply_polar_rhs_rotation,
    generalized_mass_matrix,
    rest_generalized_stiffness_matrix,
)


def _as_matrix_12(value: Any, name: str) -> np.ndarray:
    arr = np.asarray(value, dtype=float)
    if arr.shape != (12, 12):
        raise ValueError(f"{name} must have shape (12, 12), got {arr.shape}")
    return arr


@dataclass(frozen=True)
class SingleBodyABDPrecompute:
    """Dense CPU oracle data for one single-body ABD solve."""

    rest_points: np.ndarray
    masses: np.ndarray
    mass_matrix: np.ndarray
    stiffness_matrix: np.ndarray

    @classmethod
    def from_points(
        cls,
        rest_points: Any,
        masses: Any,
        stiffness_matrix: Any | None = None,
    ) -> SingleBodyABDPrecompute:
        points = np.asarray(rest_points, dtype=float)
        mass_arr = np.asarray(masses, dtype=float)
        mass_matrix = generalized_mass_matrix(points, mass_arr)
        if stiffness_matrix is None:
            K = np.zeros((12, 12), dtype=float)
        else:
            K = _as_matrix_12(stiffness_matrix, "stiffness_matrix")
        return cls(
            rest_points=points.copy(),
            masses=mass_arr.copy(),
            mass_matrix=mass_matrix,
            stiffness_matrix=0.5 * (K + K.T),
        )

    @classmethod
    def from_linear_elastic_points(
        cls,
        rest_points: Any,
        masses: Any,
        young_modulus: float,
        poisson_ratio: float,
        volume: float,
    ) -> SingleBodyABDPrecompute:
        return cls.from_points(
            rest_points,
            masses,
            stiffness_matrix=rest_generalized_stiffness_matrix(young_modulus, poisson_ratio, volume),
        )

    def hessian(self, dt: float) -> np.ndarray:
        dt_float = float(dt)
        if dt_float <= 0.0:
            raise ValueError("dt must be positive")
        return self.mass_matrix / (dt_float * dt_float) + self.stiffness_matrix


@dataclass(frozen=True)
class DenseHessianFactor:
    key: tuple[float, str, int]
    matrix: np.ndarray
    cholesky: np.ndarray

    def solve(self, rhs: Any) -> np.ndarray:
        rhs_arr = np.asarray(rhs, dtype=float)
        y = np.linalg.solve(self.cholesky, rhs_arr)
        return np.linalg.solve(self.cholesky.T, y)


class SingleBodyABDHessianCache:
    """Cache dense Cholesky factors keyed by timestep, backend label, and model version."""

    def __init__(self, precompute: SingleBodyABDPrecompute):
        self.precompute = precompute
        self._factors: dict[tuple[float, str, int], DenseHessianFactor] = {}

    def factor(
        self,
        dt: float,
        device: str = "cpu",
        model_version: int = 0,
    ) -> DenseHessianFactor:
        key = (float(dt), str(device), int(model_version))
        cached = self._factors.get(key)
        if cached is not None:
            return cached
        H = self.precompute.hessian(dt)
        factor = DenseHessianFactor(key=key, matrix=H, cholesky=np.linalg.cholesky(H))
        self._factors[key] = factor
        return factor

    def clear(self) -> None:
        self._factors.clear()


def solve_single_body_delta(
    precompute: SingleBodyABDPrecompute,
    rhs: Any,
    dt: float,
    A: Any | None = None,
    rotation_mode: str = "none",
    device: str = "cpu",
    model_version: int = 0,
    cache: SingleBodyABDHessianCache | None = None,
) -> np.ndarray:
    factor_cache = cache if cache is not None else SingleBodyABDHessianCache(precompute)
    rhs_arr = np.asarray(rhs, dtype=float)
    if rhs_arr.shape != (12,):
        raise ValueError(f"rhs must have shape (12,), got {rhs_arr.shape}")
    factor = factor_cache.factor(dt=dt, device=device, model_version=model_version)

    if rotation_mode == "none":
        return factor.solve(rhs_arr)
    if A is None:
        raise ValueError("A is required when rotation_mode is not 'none'")
    if rotation_mode == "polar":
        delta_p = factor.solve(apply_polar_rhs_rotation(A, rhs_arr))
        return apply_polar_increment_rotation(A, delta_p)
    if rotation_mode == "no_polar":
        delta_p = factor.solve(apply_no_polar_rhs_rotation(A, rhs_arr))
        return apply_no_polar_increment_rotation(A, delta_p)
    raise ValueError("rotation_mode must be one of 'none', 'polar', or 'no_polar'")


__all__ = [
    "DenseHessianFactor",
    "SingleBodyABDHessianCache",
    "SingleBodyABDPrecompute",
    "solve_single_body_delta",
]
