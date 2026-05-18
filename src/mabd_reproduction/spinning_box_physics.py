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
class SpinningBoxMaterialProperties:
    young_modulus_pa: float
    poisson_ratio: float
    volume_m3: float


@dataclass(frozen=True)
class SpinningBoxMABDMomentumDiagnostics:
    spatial_twist: np.ndarray
    linear_momentum_kg_m_s: np.ndarray
    angular_momentum_kg_m2_s: np.ndarray
    linear_momentum_error: float
    angular_momentum_error: float


@dataclass(frozen=True)
class SpinningBoxAffineShapeDiagnostics:
    affine_matrix: np.ndarray
    determinant: float
    singular_values: np.ndarray
    orthogonality_error: float


@dataclass(frozen=True)
class SpinningBoxContactDiagnostics:
    corner_count: int
    active_contact_count: int
    corner_signed_distances: np.ndarray
    min_signed_distance: float
    max_penetration_depth: float
    total_normal_force: np.ndarray
    total_generalized_force: np.ndarray


@dataclass(frozen=True)
class SpinningBoxKinematicFeasibility:
    time_step_s: float
    paper_angular_speed_rad_s: float
    orthogonal_update_angular_speed_bound_rad_s: float
    paper_angular_momentum_norm_kg_m2_s: float
    orthogonal_update_angular_momentum_bound_kg_m2_s: float
    required_speed_to_bound_ratio: float
    requires_affine_stretch: bool
    velocity_update_relation: str
    status: str

    def to_report(self) -> dict[str, object]:
        return {
            "time_step_s": self.time_step_s,
            "paper_angular_speed_rad_s": self.paper_angular_speed_rad_s,
            "orthogonal_update_angular_speed_bound_rad_s": (
                self.orthogonal_update_angular_speed_bound_rad_s
            ),
            "paper_angular_momentum_norm_kg_m2_s": self.paper_angular_momentum_norm_kg_m2_s,
            "orthogonal_update_angular_momentum_bound_kg_m2_s": (
                self.orthogonal_update_angular_momentum_bound_kg_m2_s
            ),
            "required_speed_to_bound_ratio": self.required_speed_to_bound_ratio,
            "requires_affine_stretch": self.requires_affine_stretch,
            "velocity_update_relation": self.velocity_update_relation,
            "status": self.status,
        }


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


def _skew(vector: np.ndarray) -> np.ndarray:
    x, y, z = np.asarray(vector, dtype=float)
    return np.array(
        [
            [0.0, -z, y],
            [z, 0.0, -x],
            [-y, x, 0.0],
        ],
        dtype=float,
    )


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


def spinning_box_kinematic_feasibility(
    config: SpinningBoxRunConfig,
    time_step_s: float,
) -> SpinningBoxKinematicFeasibility:
    dt = float(time_step_s)
    if not isfinite(dt) or dt <= 0.0:
        raise ValueError("time_step_s must be positive")

    properties = spinning_box_physical_properties(config)
    paper_angular_speed = float(np.linalg.norm(properties.angular_velocity_rad_s))
    paper_angular_momentum = float(np.linalg.norm(properties.angular_momentum_kg_m2_s))
    speed_bound = 1.0 / dt
    momentum_bound = float(np.max(properties.inertia_diag_kg_m2)) * speed_bound
    required_ratio = paper_angular_speed / speed_bound
    requires_stretch = bool(paper_angular_momentum > momentum_bound * (1.0 + 1.0e-12))
    status = (
        "paper_momentum_requires_affine_stretch_under_q_delta_over_h"
        if requires_stretch
        else "orthogonal_update_can_represent_paper_momentum"
    )
    return SpinningBoxKinematicFeasibility(
        time_step_s=dt,
        paper_angular_speed_rad_s=paper_angular_speed,
        orthogonal_update_angular_speed_bound_rad_s=speed_bound,
        paper_angular_momentum_norm_kg_m2_s=paper_angular_momentum,
        orthogonal_update_angular_momentum_bound_kg_m2_s=momentum_bound,
        required_speed_to_bound_ratio=required_ratio,
        requires_affine_stretch=requires_stretch,
        velocity_update_relation="qd_next=(q_next-q_n)/h",
        status=status,
    )


def paper_spatial_twist_from_momenta(config: SpinningBoxRunConfig) -> np.ndarray:
    properties = spinning_box_physical_properties(config)
    return np.concatenate([properties.angular_velocity_rad_s, properties.linear_velocity_m_s])


def spinning_box_so3_exp_from_angular_velocity(
    angular_velocity: np.ndarray,
    time_step_s: float,
) -> np.ndarray:
    omega = _paper_vector(angular_velocity, "angular_velocity")
    dt = _paper_float(time_step_s, "time_step_s", positive=True)
    speed = float(np.linalg.norm(omega))
    if speed == 0.0:
        return np.eye(3)
    theta = speed * dt
    axis_cross = _skew(omega / speed)
    return np.eye(3) + np.sin(theta) * axis_cross + (1.0 - np.cos(theta)) * (axis_cross @ axis_cross)


def spinning_box_decoupled_twist_state(
    config: SpinningBoxRunConfig,
    time_step_s: float,
    step_index: int,
) -> tuple[np.ndarray, np.ndarray]:
    if step_index < 0:
        raise ValueError("step_index must be nonnegative")
    step_count = int(step_index)
    properties = spinning_box_physical_properties(config)
    rotation_step = spinning_box_so3_exp_from_angular_velocity(
        properties.angular_velocity_rad_s,
        time_step_s,
    )
    A0, t0 = mabd.unpack_q(config.initial_q)
    A = np.linalg.matrix_power(rotation_step, step_count) @ A0
    t = t0 + properties.linear_velocity_m_s * float(time_step_s) * step_count
    q = mabd.pack_q(A, t)
    qd = abd_generalized_velocity_from_paper_momenta(config, A=A)
    return q, qd


def spinning_box_mabd_mass_diagonal(config: SpinningBoxRunConfig) -> np.ndarray:
    properties = spinning_box_physical_properties(config)
    affine_second_moment = properties.mass_kg * properties.cube_size_m**2 / 12.0
    return np.concatenate(
        [
            np.full(9, affine_second_moment, dtype=float),
            np.full(3, properties.mass_kg, dtype=float),
        ]
    )


def spinning_box_mabd_material_properties(config: SpinningBoxRunConfig) -> SpinningBoxMaterialProperties:
    properties = spinning_box_physical_properties(config)
    young_modulus_pa = _paper_float(
        config.paper_values.get("material_E"),
        "material_E",
        positive=True,
    )
    poisson_ratio = _paper_float(config.paper_values.get("poisson_ratio"), "poisson_ratio")
    if not -1.0 < poisson_ratio < 0.5:
        raise ValueError("poisson_ratio must be in the open interval (-1, 0.5)")
    return SpinningBoxMaterialProperties(
        young_modulus_pa=young_modulus_pa,
        poisson_ratio=poisson_ratio,
        volume_m3=properties.cube_size_m**3,
    )


def spinning_box_mabd_material_stiffness(config: SpinningBoxRunConfig) -> np.ndarray:
    material = spinning_box_mabd_material_properties(config)
    return mabd.rest_generalized_stiffness_matrix(
        material.young_modulus_pa,
        material.poisson_ratio,
        material.volume_m3,
    )


def spinning_box_cube_corners(config: SpinningBoxRunConfig) -> np.ndarray:
    half_size = 0.5 * spinning_box_physical_properties(config).cube_size_m
    return np.array(
        [
            [x, y, z]
            for x in (-half_size, half_size)
            for y in (-half_size, half_size)
            for z in (-half_size, half_size)
        ],
        dtype=float,
    )


def spinning_box_affine_shape_diagnostics(q: np.ndarray) -> SpinningBoxAffineShapeDiagnostics:
    A, _t = mabd.unpack_q(q)
    return SpinningBoxAffineShapeDiagnostics(
        affine_matrix=A,
        determinant=float(np.linalg.det(A)),
        singular_values=np.linalg.svd(A, compute_uv=False),
        orthogonality_error=float(np.linalg.norm(A.T @ A - np.eye(3))),
    )


def spinning_box_contact_diagnostics(
    config: SpinningBoxRunConfig,
    q: np.ndarray,
    qd: np.ndarray,
) -> SpinningBoxContactDiagnostics:
    surface = config.contact_surface
    if surface.get("type") != "plane":
        raise ValueError("spinning-box contact diagnostics require a plane contact_surface")
    corners = spinning_box_cube_corners(config)
    contacts = [
        mabd.evaluate_point_plane_penalty_contact(
            q,
            qd,
            corner,
            plane_normal=surface["plane_normal"],
            plane_offset=float(surface["plane_offset"]),
            stiffness=float(surface["stiffness"]),
            damping=float(surface["damping"]),
        )
        for corner in corners
    ]
    signed_distances = np.asarray([contact.signed_distance for contact in contacts], dtype=float)
    penetration_depths = np.asarray([contact.penetration_depth for contact in contacts], dtype=float)
    active_count = sum(1 for contact in contacts if contact.active)
    return SpinningBoxContactDiagnostics(
        corner_count=int(corners.shape[0]),
        active_contact_count=active_count,
        corner_signed_distances=signed_distances,
        min_signed_distance=float(signed_distances.min()),
        max_penetration_depth=float(penetration_depths.max()),
        total_normal_force=sum((contact.force for contact in contacts), np.zeros(3, dtype=float)),
        total_generalized_force=sum(
            (contact.generalized_force for contact in contacts),
            np.zeros(12, dtype=float),
        ),
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
    "SpinningBoxAffineShapeDiagnostics",
    "SpinningBoxContactDiagnostics",
    "SpinningBoxKinematicFeasibility",
    "SpinningBoxMABDMomentumDiagnostics",
    "SpinningBoxMaterialProperties",
    "SpinningBoxPhysicalProperties",
    "abd_generalized_velocity_from_paper_momenta",
    "spinning_box_decoupled_twist_state",
    "spinning_box_affine_shape_diagnostics",
    "spinning_box_kinematic_feasibility",
    "mabd_momentum_diagnostics",
    "paper_spatial_twist_from_momenta",
    "spinning_box_contact_diagnostics",
    "spinning_box_cube_corners",
    "spinning_box_mabd_material_properties",
    "spinning_box_mabd_material_stiffness",
    "spinning_box_mabd_mass_diagonal",
    "spinning_box_physical_properties",
    "spinning_box_so3_exp_from_angular_velocity",
]
