# SPDX-FileCopyrightText: Copyright (c) 2026 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

import numpy as np

from .affine_math import point_jacobian, tetra_volume


def _as_q(value: Any, name: str = "q") -> np.ndarray:
    arr = np.asarray(value, dtype=float)
    if arr.shape != (12,):
        raise ValueError(f"{name} must have shape (12,), got {arr.shape}")
    return arr


def _as_control_points(value: Any, name: str) -> np.ndarray:
    arr = np.asarray(value, dtype=float)
    if arr.shape == (12,):
        arr = arr.reshape(4, 3)
    if arr.shape != (4, 3):
        raise ValueError(f"{name} must have shape (4, 3) or (12,), got {arr.shape}")
    return arr


def _as_control_tetrahedron(value: Any) -> np.ndarray:
    points = _as_control_points(value, "rest_points")
    if tetra_volume(points) <= 1.0e-12:
        raise ValueError("control tetrahedron must be non-degenerate")
    return points


@dataclass(frozen=True)
class ControlTetrahedron:
    """Control tetrahedron map for paper CP coordinates ``y = T q``."""

    rest_points: np.ndarray
    transform: np.ndarray
    inverse_transform: np.ndarray

    @classmethod
    def from_points(cls, rest_points: Any) -> ControlTetrahedron:
        points = _as_control_tetrahedron(rest_points)
        transform = control_point_transform(points)
        return cls(
            rest_points=points.copy(),
            transform=transform,
            inverse_transform=np.linalg.inv(transform),
        )


def control_point_transform(rest_points: Any) -> np.ndarray:
    """Return the paper's 12x12 CP transform ``y = T q`` for one affine body."""

    points = _as_control_tetrahedron(rest_points)
    return np.vstack([point_jacobian(point) for point in points])


def control_point_inverse_transform(rest_points: Any) -> np.ndarray:
    """Return ``T^-1`` for a non-degenerate control tetrahedron."""

    return np.linalg.inv(control_point_transform(rest_points))


def control_points_from_q(q: Any, rest_points: Any) -> np.ndarray:
    """Map paper affine coordinate ``q`` to stacked point-major CP coordinate ``y``."""

    return control_point_transform(rest_points) @ _as_q(q)


def q_from_control_points(control_points: Any, rest_points: Any) -> np.ndarray:
    """Map stacked point-major CP coordinate ``y`` back to paper affine coordinate ``q``."""

    y = _as_control_points(control_points, "control_points").reshape(12)
    return control_point_inverse_transform(rest_points) @ y


def control_point_selection(rows: Iterable[tuple[int, int] | tuple[int, int, float]]) -> np.ndarray:
    """Build a matrix selecting CP components from point-major CP coordinates.

    Rows use zero-based ``(cp_index, component)`` or weighted
    ``(cp_index, component, weight)`` descriptors.
    """

    descriptors = list(rows)
    S = np.zeros((len(descriptors), 12), dtype=float)
    for row_id, descriptor in enumerate(descriptors):
        if len(descriptor) == 2:
            cp_index, component = descriptor
            weight = 1.0
        elif len(descriptor) == 3:
            cp_index, component, weight = descriptor
        else:
            raise ValueError("selection rows must be (cp_index, component[, weight])")
        if not 0 <= int(cp_index) < 4:
            raise ValueError(f"cp_index must be in [0, 3], got {cp_index}")
        if not 0 <= int(component) < 3:
            raise ValueError(f"component must be in [0, 2], got {component}")
        S[row_id, 3 * int(cp_index) + int(component)] = float(weight)
    return S


def block_diag4(R: Any) -> np.ndarray:
    """Return ``diag_4(R)`` for point-major CP coordinates."""

    R_arr = np.asarray(R, dtype=float)
    if R_arr.shape != (3, 3):
        raise ValueError(f"R must have shape (3, 3), got {R_arr.shape}")
    return np.kron(np.eye(4), R_arr)


__all__ = [
    "ControlTetrahedron",
    "block_diag4",
    "control_point_inverse_transform",
    "control_point_selection",
    "control_point_transform",
    "control_points_from_q",
    "q_from_control_points",
]
