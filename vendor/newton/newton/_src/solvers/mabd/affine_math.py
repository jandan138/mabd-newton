# SPDX-FileCopyrightText: Copyright (c) 2026 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np


def _as_vec3(value: Any, name: str) -> np.ndarray:
    arr = np.asarray(value, dtype=float)
    if arr.shape != (3,):
        raise ValueError(f"{name} must have shape (3,), got {arr.shape}")
    return arr


def _as_mat33(value: Any, name: str) -> np.ndarray:
    arr = np.asarray(value, dtype=float)
    if arr.shape != (3, 3):
        raise ValueError(f"{name} must have shape (3, 3), got {arr.shape}")
    return arr


def _as_q(value: Any, name: str = "q") -> np.ndarray:
    arr = np.asarray(value, dtype=float)
    if arr.shape != (12,):
        raise ValueError(f"{name} must have shape (12,), got {arr.shape}")
    return arr


def _as_points(value: Any, name: str) -> np.ndarray:
    arr = np.asarray(value, dtype=float)
    if arr.ndim != 2 or arr.shape[1] != 3:
        raise ValueError(f"{name} must have shape (n, 3), got {arr.shape}")
    return arr


def _skew(value: np.ndarray) -> np.ndarray:
    x, y, z = value
    return np.array([[0.0, -z, y], [z, 0.0, -x], [-y, x, 0.0]])


def _block_diag4(R: np.ndarray) -> np.ndarray:
    return np.kron(np.eye(4), R)


def _pack_A_gradient(grad: np.ndarray) -> np.ndarray:
    out = np.zeros(12, dtype=float)
    out[0:3] = grad[:, 0]
    out[3:6] = grad[:, 1]
    out[6:9] = grad[:, 2]
    return out


def pack_q(A: Any, t: Any) -> np.ndarray:
    """Pack paper M-ABD state ``q = [q1, q2, q3, t]`` from affine map ``x = A xbar + t``."""

    A_arr = _as_mat33(A, "A")
    t_arr = _as_vec3(t, "t")
    return np.concatenate((A_arr[:, 0], A_arr[:, 1], A_arr[:, 2], t_arr)).astype(float, copy=False)


def unpack_q(q: Any) -> tuple[np.ndarray, np.ndarray]:
    """Unpack paper M-ABD state into ``(A, t)``."""

    q_arr = _as_q(q)
    A = np.column_stack((q_arr[0:3], q_arr[3:6], q_arr[6:9]))
    t = q_arr[9:12].copy()
    return A, t


def affine_points(q: Any, rest_points: Any) -> np.ndarray:
    A, t = unpack_q(q)
    points = _as_points(rest_points, "rest_points")
    return points @ A.T + t


def point_jacobian(rest_point: Any) -> np.ndarray:
    """Return the constant 3x12 Jacobian satisfying ``x = J q`` for one rest point."""

    r = _as_vec3(rest_point, "rest_point")
    J = np.zeros((3, 12), dtype=float)
    eye = np.eye(3)
    for block_id, coeff in enumerate(r):
        J[:, 3 * block_id : 3 * block_id + 3] = coeff * eye
    J[:, 9:12] = eye
    return J


def point_jacobians(rest_points: Any) -> np.ndarray:
    points = _as_points(rest_points, "rest_points")
    return np.stack([point_jacobian(point) for point in points], axis=0)


def element_jacobian(tet_rest_points: Any) -> np.ndarray:
    points = _as_points(tet_rest_points, "tet_rest_points")
    if points.shape != (4, 3):
        raise ValueError(f"tet_rest_points must have shape (4, 3), got {points.shape}")
    return np.vstack([point_jacobian(point) for point in points])


def volume_weighted_jacobian(tet_rest_points: Any, volumes: Any) -> np.ndarray:
    tets = np.asarray(tet_rest_points, dtype=float)
    if tets.shape == (4, 3):
        tets = tets[None, :, :]
    if tets.ndim != 3 or tets.shape[1:] != (4, 3):
        raise ValueError(f"tet_rest_points must have shape (elements, 4, 3), got {tets.shape}")
    volume_arr = np.asarray(volumes, dtype=float)
    if volume_arr.shape == ():
        volume_arr = np.full(tets.shape[0], float(volume_arr))
    if volume_arr.shape != (tets.shape[0],):
        raise ValueError(f"volumes must have shape ({tets.shape[0]},), got {volume_arr.shape}")

    bar_j = np.zeros((12, 12), dtype=float)
    for tet_points, volume in zip(tets, volume_arr, strict=True):
        bar_j += float(volume) * element_jacobian(tet_points)
    return bar_j


def volume_weighted_affine_force(tet_rest_points: Any, aggregated_force: Any, volumes: Any) -> np.ndarray:
    force = np.asarray(aggregated_force, dtype=float)
    if force.shape != (12,):
        raise ValueError(f"aggregated_force must have shape (12,), got {force.shape}")
    return volume_weighted_jacobian(tet_rest_points, volumes).T @ force


def tetra_volume(vertices: Any) -> float:
    points = _as_points(vertices, "vertices")
    if points.shape != (4, 3):
        raise ValueError(f"vertices must have shape (4, 3), got {points.shape}")
    basis = np.column_stack((points[1] - points[0], points[2] - points[0], points[3] - points[0]))
    return float(abs(np.linalg.det(basis)) / 6.0)


def generalized_mass_matrix(rest_points: Any, masses: Any) -> np.ndarray:
    points = _as_points(rest_points, "rest_points")
    mass_arr = np.asarray(masses, dtype=float)
    if mass_arr.shape != (points.shape[0],):
        raise ValueError(f"masses must have shape ({points.shape[0]},), got {mass_arr.shape}")
    M = np.zeros((12, 12), dtype=float)
    for point, mass in zip(points, mass_arr, strict=True):
        J = point_jacobian(point)
        M += float(mass) * (J.T @ J)
    return M


def volume_weighted_force(rest_points: Any, forces: Any, volumes: Any) -> np.ndarray:
    points = _as_points(rest_points, "rest_points")
    force_arr = _as_points(forces, "forces")
    if force_arr.shape[0] != points.shape[0]:
        raise ValueError("forces and rest_points must have the same number of rows")
    volume_arr = np.asarray(volumes, dtype=float)
    if volume_arr.shape == ():
        volume_arr = np.full(points.shape[0], float(volume_arr))
    if volume_arr.shape != (points.shape[0],):
        raise ValueError(f"volumes must have shape ({points.shape[0]},), got {volume_arr.shape}")

    out = np.zeros(12, dtype=float)
    for point, force, volume in zip(points, force_arr, volume_arr, strict=True):
        out += float(volume) * (point_jacobian(point).T @ force)
    return out


@dataclass(frozen=True)
class PointPlanePenaltyContact:
    rest_point: np.ndarray
    world_point: np.ndarray
    plane_normal: np.ndarray
    plane_offset: float
    signed_distance: float
    penetration_depth: float
    normal_velocity: float
    force: np.ndarray
    generalized_force: np.ndarray
    active: bool


def affine_force_from_point_force(rest_point: Any, force: Any) -> np.ndarray:
    """Map a world-space point force to affine generalized force by virtual work."""

    return point_jacobian(rest_point).T @ _as_vec3(force, "force")


def evaluate_point_plane_penalty_contact(
    q: Any,
    qd: Any,
    rest_point: Any,
    *,
    plane_normal: Any,
    plane_offset: float,
    stiffness: float,
    damping: float = 0.0,
) -> PointPlanePenaltyContact:
    """Evaluate a single point-plane normal penalty force in affine coordinates.

    The plane convention is ``normal dot x >= plane_offset``. Penetrating points
    receive an explicit normal penalty force. This is an oracle for scene force
    assembly, not collision detection or a full contact solve.
    """

    q_arr = _as_q(q)
    qd_arr = _as_q(qd, "qd")
    point = _as_vec3(rest_point, "rest_point")
    normal = _as_vec3(plane_normal, "plane_normal")
    normal_norm = float(np.linalg.norm(normal))
    if normal_norm == 0.0:
        raise ValueError("plane_normal must be nonzero")
    normal = normal / normal_norm

    stiffness_float = float(stiffness)
    damping_float = float(damping)
    if stiffness_float < 0.0:
        raise ValueError("stiffness must be nonnegative")
    if damping_float < 0.0:
        raise ValueError("damping must be nonnegative")

    J = point_jacobian(point)
    world_point = J @ q_arr
    world_velocity = J @ qd_arr
    offset = float(plane_offset)
    signed_distance = float(normal @ world_point - offset)
    penetration_depth = max(0.0, -signed_distance)
    active = penetration_depth > 0.0
    normal_velocity = float(normal @ world_velocity)
    normal_magnitude = 0.0
    if active:
        normal_magnitude = stiffness_float * penetration_depth + damping_float * max(0.0, -normal_velocity)
    force = normal * normal_magnitude
    generalized_force = J.T @ force
    return PointPlanePenaltyContact(
        rest_point=point.copy(),
        world_point=world_point,
        plane_normal=normal,
        plane_offset=offset,
        signed_distance=signed_distance,
        penetration_depth=penetration_depth,
        normal_velocity=normal_velocity,
        force=force,
        generalized_force=generalized_force,
        active=active,
    )


def lame_parameters(young_modulus: float, poisson_ratio: float) -> tuple[float, float]:
    E = float(young_modulus)
    nu = float(poisson_ratio)
    if E <= 0.0:
        raise ValueError("young_modulus must be positive")
    if not (-1.0 < nu < 0.5):
        raise ValueError("poisson_ratio must lie in (-1, 0.5)")
    mu = E / (2.0 * (1.0 + nu))
    lam = E * nu / ((1.0 + nu) * (1.0 - 2.0 * nu))
    return mu, lam


def _linear_strain(A: np.ndarray) -> np.ndarray:
    return 0.5 * (A + A.T) - np.eye(3)


def linear_elastic_energy(
    A: Any,
    young_modulus: float,
    poisson_ratio: float,
    volume: float = 1.0,
) -> float:
    A_arr = _as_mat33(A, "A")
    mu, lam = lame_parameters(young_modulus, poisson_ratio)
    eps = _linear_strain(A_arr)
    tr = float(np.trace(eps))
    density = mu * float(np.sum(eps * eps)) + 0.5 * lam * tr * tr
    return float(volume) * density


def linear_elastic_gradient(
    A: Any,
    young_modulus: float,
    poisson_ratio: float,
    volume: float = 1.0,
) -> np.ndarray:
    A_arr = _as_mat33(A, "A")
    mu, lam = lame_parameters(young_modulus, poisson_ratio)
    eye = np.eye(3)
    return float(volume) * (mu * (A_arr + A_arr.T - 2.0 * eye) + lam * np.trace(A_arr - eye) * eye)


def rest_generalized_stiffness_matrix(
    young_modulus: float,
    poisson_ratio: float,
    volume: float = 1.0,
) -> np.ndarray:
    """Return the rest generalized stiffness ``K_A_bar`` for paper column-major ``q``.

    The first nine rows/columns are the analytic linear-elastic material Hessian
    with respect to ``A``. Translation columns are zero because the material
    energy is translation invariant.
    """

    mu, lam = lame_parameters(young_modulus, poisson_ratio)
    volume_float = float(volume)
    K = np.zeros((12, 12), dtype=float)
    for col in range(9):
        dA = np.zeros((3, 3), dtype=float)
        dA[col % 3, col // 3] = 1.0
        dP = mu * (dA + dA.T) + lam * np.trace(dA) * np.eye(3)
        K[:, col] = _pack_A_gradient(volume_float * dP)
    return 0.5 * (K + K.T)


def polar_rotation(A: Any) -> np.ndarray:
    A_arr = _as_mat33(A, "A")
    U, _singular_values, Vt = np.linalg.svd(A_arr)
    R = U @ Vt
    if np.linalg.det(R) < 0.0:
        U = U.copy()
        U[:, -1] *= -1.0
        R = U @ Vt
    return R


def _apply_block_transform(A: np.ndarray, blocks: Any, transform: np.ndarray, preserve_norm: bool) -> np.ndarray:
    block_arr = _as_q(blocks, "blocks")
    out = np.zeros(12, dtype=float)
    for block_id in range(4):
        start = 3 * block_id
        block = block_arr[start : start + 3]
        transformed = transform @ block
        if preserve_norm:
            source_norm = float(np.linalg.norm(block))
            target_norm = float(np.linalg.norm(transformed))
            if source_norm == 0.0:
                transformed = np.zeros(3, dtype=float)
            elif target_norm != 0.0:
                transformed = transformed * (source_norm / target_norm)
        out[start : start + 3] = transformed
    return out


def apply_polar_rhs_rotation(A: Any, blocks: Any) -> np.ndarray:
    R = polar_rotation(A)
    return _apply_block_transform(_as_mat33(A, "A"), blocks, R.T, preserve_norm=False)


def apply_polar_increment_rotation(A: Any, blocks: Any) -> np.ndarray:
    R = polar_rotation(A)
    return _apply_block_transform(_as_mat33(A, "A"), blocks, R, preserve_norm=False)


def apply_no_polar_rhs_rotation(A: Any, blocks: Any) -> np.ndarray:
    A_arr = _as_mat33(A, "A")
    return _apply_block_transform(A_arr, blocks, A_arr.T, preserve_norm=True)


def apply_no_polar_increment_rotation(A: Any, blocks: Any) -> np.ndarray:
    A_arr = _as_mat33(A, "A")
    return _apply_block_transform(A_arr, blocks, A_arr, preserve_norm=True)


def co_rotated_linear_elastic_energy(
    A: Any,
    young_modulus: float,
    poisson_ratio: float,
    volume: float = 1.0,
) -> float:
    A_arr = _as_mat33(A, "A")
    R = polar_rotation(A_arr)
    return linear_elastic_energy(R.T @ A_arr, young_modulus, poisson_ratio, volume)


def co_rotated_linear_elastic_affine_force(
    A: Any,
    young_modulus: float,
    poisson_ratio: float,
    volume: float = 1.0,
) -> np.ndarray:
    A_arr = _as_mat33(A, "A")
    R = polar_rotation(A_arr)
    local_gradient = linear_elastic_gradient(R.T @ A_arr, young_modulus, poisson_ratio, volume)
    return -_pack_A_gradient(R @ local_gradient)


def co_rotated_generalized_stiffness_matrix(A: Any, rest_stiffness_matrix: Any) -> np.ndarray:
    A_arr = _as_mat33(A, "A")
    K_bar = np.asarray(rest_stiffness_matrix, dtype=float)
    if K_bar.shape != (12, 12):
        raise ValueError(f"rest_stiffness_matrix must have shape (12, 12), got {K_bar.shape}")
    D = _block_diag4(polar_rotation(A_arr))
    return D @ K_bar @ D.T


def twist_map_G(A: Any) -> np.ndarray:
    """Build the paper's 6x12 affine-to-spatial twist map for ``[omega, v]``."""

    A_arr = _as_mat33(A, "A")
    G = np.zeros((6, 12), dtype=float)
    for block_id in range(3):
        G[0:3, 3 * block_id : 3 * block_id + 3] = 0.5 * _skew(A_arr[:, block_id])
    G[3:6, 9:12] = np.eye(3)
    return G


def paper_rigid_embedding_E(A: Any) -> np.ndarray:
    """Build the paper's displayed rigid-motion embedding for ABD coordinates."""

    A_arr = _as_mat33(A, "A")
    E = np.zeros((12, 6), dtype=float)
    for block_id in range(3):
        E[3 * block_id : 3 * block_id + 3, 0:3] = -_skew(A_arr[:, block_id])
    E[9:12, 3:6] = np.eye(3)
    return E


def rigid_embedding_E(A: Any) -> np.ndarray:
    """Build a robust extension satisfying ``G(A) @ E(A) = I`` when possible.

    For rotations this equals :func:`paper_rigid_embedding_E`. For affine states that are
    not exact rotations, the angular blocks include the inverse normalizer of ``G`` so the
    oracle remains a left inverse.
    """

    A_arr = _as_mat33(A, "A")
    gram = A_arr.T @ A_arr
    angular_metric = 0.5 * (float(np.trace(gram)) * np.eye(3) - A_arr @ A_arr.T)
    angular_inverse = np.linalg.inv(angular_metric)
    E = np.zeros((12, 6), dtype=float)
    for block_id in range(3):
        E[3 * block_id : 3 * block_id + 3, 0:3] = -_skew(A_arr[:, block_id]) @ angular_inverse
    E[9:12, 3:6] = np.eye(3)
    return E


def affine_force_from_wrench(A: Any, wrench: Any) -> np.ndarray:
    wrench_arr = np.asarray(wrench, dtype=float)
    if wrench_arr.shape != (6,):
        raise ValueError(f"wrench must have shape (6,), got {wrench_arr.shape}")
    return twist_map_G(A).T @ wrench_arr


__all__ = [
    "PointPlanePenaltyContact",
    "affine_force_from_point_force",
    "affine_force_from_wrench",
    "affine_points",
    "apply_no_polar_increment_rotation",
    "apply_no_polar_rhs_rotation",
    "apply_polar_increment_rotation",
    "apply_polar_rhs_rotation",
    "co_rotated_generalized_stiffness_matrix",
    "co_rotated_linear_elastic_affine_force",
    "co_rotated_linear_elastic_energy",
    "element_jacobian",
    "evaluate_point_plane_penalty_contact",
    "generalized_mass_matrix",
    "lame_parameters",
    "linear_elastic_energy",
    "linear_elastic_gradient",
    "pack_q",
    "paper_rigid_embedding_E",
    "point_jacobian",
    "point_jacobians",
    "polar_rotation",
    "rest_generalized_stiffness_matrix",
    "rigid_embedding_E",
    "tetra_volume",
    "twist_map_G",
    "unpack_q",
    "volume_weighted_affine_force",
    "volume_weighted_force",
    "volume_weighted_jacobian",
]
