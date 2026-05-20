"""Report lane for the rolling/spinning single-body experiment surface."""

from __future__ import annotations

import sys
from contextlib import redirect_stdout
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter

import numpy as np
from newton.solvers import mabd

from .experiment_configs import (
    RollingSpinningMABDNewtonConfig,
    RollingSpinningRBDBaselineConfig,
    RollingSpinningRunConfig,
)
from .reporting import ClaimReport, EvidenceStatus, load_claim_report, write_claim_report


CANONICAL_PYTHON = "/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python"
ROLLING_SPINNING_CONFIG_PATH = "configs/experiments/single_body_rolling_spinning.yaml"
ROLLING_SPINNING_RBD_REQUIRED_MISSING_LANES = [
    "rbd_explicit_baseline",
    "mabd_newton",
    "paper_comparable_timing",
]
ROLLING_SPINNING_RBD_BLOCKING_REASONS = [
    "rbd_explicit_baseline_missing",
    "mabd_rolling_cylinder_lane_missing",
    "paper_comparable_timing_missing",
    "newton_semimplicit_not_paper_implicit_rbd_solver",
]
ROLLING_SPINNING_RBD_NEWTON_API = [
    "ModelBuilder.add_shape_cylinder",
    "ModelBuilder.add_ground_plane",
    "Model.contacts",
    "Model.collide",
    "SolverSemiImplicit",
]
ROLLING_SPINNING_RBD_EXPLICIT_REQUIRED_MISSING_LANES = [
    "mabd_newton",
    "paper_comparable_timing",
]
ROLLING_SPINNING_RBD_EXPLICIT_BLOCKING_REASONS = [
    "mabd_rolling_cylinder_lane_missing",
    "paper_comparable_timing_missing",
    "newton_explicit_euler_not_paper_explicit_rbd_solver",
]
ROLLING_SPINNING_RBD_EXPLICIT_NEWTON_API = [
    "ModelBuilder.add_shape_cylinder",
    "ModelBuilder.add_ground_plane",
    "Model.contacts",
    "Model.collide",
    "SolverExplicitEuler",
]
ROLLING_SPINNING_NO_SLIP_REQUIRED_REPRODUCTION_GAPS = [
    "paper_faithful_explicit_rbd_baseline",
    "paper_faithful_implicit_rbd_baseline",
    "paper_faithful_mabd_rolling_cylinder",
    "paper_comparable_timing",
]
ROLLING_SPINNING_NO_SLIP_BLOCKING_REASONS = [
    "paper_faithful_explicit_rbd_baseline_missing",
    "paper_faithful_implicit_rbd_baseline_missing",
    "paper_faithful_mabd_collision_missing",
    "paper_comparable_timing_missing",
    "paper_rbd_solver_details_missing",
]
ROLLING_SPINNING_MABD_REQUIRED_MISSING_LANES = [
    "paper_comparable_timing",
]
ROLLING_SPINNING_MABD_BLOCKING_REASONS = [
    "mabd_rolling_cylinder_report_incomplete",
    "paper_faithful_mabd_collision_missing",
    "paper_faithful_explicit_rbd_baseline_missing",
    "paper_comparable_timing_missing",
]
ROLLING_SPINNING_MABD_MATERIAL_PREFLIGHT_REQUIRED_MISSING_LANES = [
    "paper_comparable_timing",
    "paper_faithful_implicit_rbd_baseline",
    "paper_faithful_explicit_rbd_baseline",
]
ROLLING_SPINNING_MABD_MATERIAL_PREFLIGHT_BLOCKING_REASONS = [
    "mabd_material_preflight_incomplete",
    "paper_faithful_mabd_collision_missing",
    "paper_faithful_explicit_rbd_baseline_missing",
    "paper_faithful_implicit_rbd_baseline_missing",
    "paper_comparable_timing_missing",
]
ROLLING_SPINNING_TIMING_PROTOCOL_BLOCKING_REASONS = [
    "paper_comparable_timing_missing",
    "paper_hardware_mismatch",
    "paper_single_thread_protocol_not_enforced",
    "paper_faithful_mabd_collision_missing",
    "paper_faithful_explicit_rbd_baseline_missing",
    "paper_faithful_implicit_rbd_baseline_missing",
]
ROLLING_SPINNING_MABD_NEWTON_API = [
    "ModelBuilder.add_shape_cylinder",
    "ModelBuilder.add_ground_plane",
    "SolverMABD",
    "SolverMABD.detect_static_plane_contacts",
    "SolverMABD.step",
]


@dataclass(frozen=True)
class RollingCylinderRBDBaselineResult:
    status: EvidenceStatus
    step_count: int
    time_step_s: float
    radius_m: float
    half_height_m: float
    density_kg_m3: float
    mass_kg: float
    inertia_diag_kg_m2: np.ndarray
    initial_position_m: np.ndarray
    final_position_m: np.ndarray
    final_rotation_xyzw: np.ndarray
    final_linear_velocity_m_s: np.ndarray
    final_angular_velocity_rad_s: np.ndarray
    initial_energy_j: float
    final_energy_j: float
    energy_drift_j: float
    relative_energy_drift: float
    no_slip_residual_m_s: float
    center_height_min_m: float
    max_center_penetration_m: float
    contact_count_summary: dict[str, int]
    contact_material: dict[str, float]
    total_wall_time_ms: float
    trajectory_samples: tuple[dict[str, object], ...]


@dataclass(frozen=True)
class RollingCylinderNoSlipReferenceResult:
    status: EvidenceStatus
    step_count: int
    time_step_s: float
    radius_m: float
    half_height_m: float
    density_kg_m3: float
    mass_kg: float
    inertia_diag_kg_m2: np.ndarray
    initial_position_m: np.ndarray
    final_position_m: np.ndarray
    final_linear_velocity_m_s: np.ndarray
    final_angular_velocity_rad_s: np.ndarray
    initial_energy_j: float
    final_energy_j: float
    energy_drift_j: float
    relative_energy_drift: float
    no_slip_residual_m_s: float
    center_height_drift_m: float
    contact_count_summary: dict[str, int]
    total_wall_time_ms: float
    trajectory_samples: tuple[dict[str, object], ...]


@dataclass(frozen=True)
class RollingCylinderMABDNewtonResult:
    status: EvidenceStatus
    step_count: int
    time_step_s: float
    radius_m: float
    half_height_m: float
    density_kg_m3: float
    mass_kg: float
    volume_m3: float
    rotation_mode: str
    rest_points_m: np.ndarray
    point_masses_kg: np.ndarray
    initial_position_m: np.ndarray
    final_center_of_mass_m: np.ndarray
    final_linear_velocity_m_s: np.ndarray
    final_angular_velocity_rad_s: np.ndarray
    initial_energy_j: float
    final_energy_j: float
    energy_drift_j: float
    relative_energy_drift: float
    no_slip_residual_m_s: float
    min_support_height_m: float
    max_support_penetration_m: float
    max_affine_shape_spread_m: float
    max_constraint_residual_norm: float
    contact_count_summary: dict[str, int]
    static_plane_collision_policy: str
    static_plane_collision_scope: str
    static_plane_candidate_count: int
    static_plane_cylinder_shape_count: int
    static_plane_plane_shape_count: int
    total_wall_time_ms: float
    trajectory_samples: tuple[dict[str, object], ...]


def _rolling_cylinder_mass_and_inertia(
    config: RollingSpinningRBDBaselineConfig,
) -> tuple[float, np.ndarray]:
    height = 2.0 * config.half_height_m
    mass = config.density_kg_m3 * np.pi * config.radius_m**2 * height
    transverse = (1.0 / 12.0) * mass * (3.0 * config.radius_m**2 + height**2)
    axial = 0.5 * mass * config.radius_m**2
    return float(mass), np.asarray([transverse, transverse, axial], dtype=float)


def _rolling_cylinder_energy(
    *,
    mass_kg: float,
    inertia_diag_kg_m2: np.ndarray,
    gravity_m_s2: np.ndarray,
    position_m: np.ndarray,
    linear_velocity_m_s: np.ndarray,
    angular_velocity_rad_s: np.ndarray,
) -> float:
    kinetic_linear = 0.5 * mass_kg * float(linear_velocity_m_s @ linear_velocity_m_s)
    kinetic_angular = 0.5 * float(
        angular_velocity_rad_s @ (inertia_diag_kg_m2 * angular_velocity_rad_s)
    )
    potential = mass_kg * (-float(gravity_m_s2[1])) * float(position_m[1])
    return kinetic_linear + kinetic_angular + potential


def _sample_indices(step_count: int, sample_count: int) -> set[int]:
    count = min(sample_count, step_count + 1)
    return {int(round(value)) for value in np.linspace(0, step_count, count)}


def _vec3(values: np.ndarray, wp_module: object) -> object:
    values = np.asarray(values, dtype=float)
    if values.shape != (3,):
        raise ValueError(f"expected vec3-compatible value with shape (3,), got {values.shape}")
    return wp_module.vec3(float(values[0]), float(values[1]), float(values[2]))


def _assign_mabd_solver_state(state: object, q: np.ndarray, qd: np.ndarray) -> None:
    q_arr = np.asarray([q], dtype=np.float32)
    qd_arr = np.asarray([qd], dtype=np.float32)
    state.mabd.q0.assign(q_arr[:, 0:3])
    state.mabd.q1.assign(q_arr[:, 3:6])
    state.mabd.q2.assign(q_arr[:, 6:9])
    state.mabd.t.assign(q_arr[:, 9:12])
    state.mabd.qd0.assign(qd_arr[:, 0:3])
    state.mabd.qd1.assign(qd_arr[:, 3:6])
    state.mabd.qd2.assign(qd_arr[:, 6:9])
    state.mabd.td.assign(qd_arr[:, 9:12])


def _read_mabd_solver_state(state: object) -> tuple[np.ndarray, np.ndarray]:
    q = np.concatenate(
        [
            state.mabd.q0.numpy(),
            state.mabd.q1.numpy(),
            state.mabd.q2.numpy(),
            state.mabd.t.numpy(),
        ],
        axis=1,
    )[0].astype(float, copy=False)
    qd = np.concatenate(
        [
            state.mabd.qd0.numpy(),
            state.mabd.qd1.numpy(),
            state.mabd.qd2.numpy(),
            state.mabd.td.numpy(),
        ],
        axis=1,
    )[0].astype(float, copy=False)
    return q, qd


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


def _rolling_mabd_initial_state(
    config: RollingSpinningMABDNewtonConfig,
) -> tuple[np.ndarray, np.ndarray]:
    rotation = np.eye(3, dtype=float)
    q = mabd.pack_q(rotation, config.initial_position_m)
    rotation_velocity = _skew(config.initial_angular_velocity_rad_s) @ rotation
    qd = mabd.pack_q(rotation_velocity, config.initial_linear_velocity_m_s)
    return q, qd


def _center_of_mass(points: np.ndarray, masses: np.ndarray) -> np.ndarray:
    return np.sum(points * masses[:, None], axis=0) / float(np.sum(masses))


def _affine_angular_velocity(q: np.ndarray, qd: np.ndarray) -> np.ndarray:
    matrix, _translation = mabd.unpack_q(q)
    matrix_velocity, _translation_velocity = mabd.unpack_q(qd)
    omega_matrix = matrix_velocity @ np.linalg.inv(matrix)
    skew_part = 0.5 * (omega_matrix - omega_matrix.T)
    return np.asarray(
        [
            skew_part[2, 1],
            skew_part[0, 2],
            skew_part[1, 0],
        ],
        dtype=float,
    )


def _affine_shape_spread(q: np.ndarray, rest_points_m: np.ndarray) -> float:
    points = mabd.affine_points(q, rest_points_m)
    max_spread = 0.0
    for row in range(rest_points_m.shape[0]):
        for col in range(row + 1, rest_points_m.shape[0]):
            rest_distance = float(np.linalg.norm(rest_points_m[row] - rest_points_m[col]))
            world_distance = float(np.linalg.norm(points[row] - points[col]))
            max_spread = max(max_spread, abs(world_distance - rest_distance))
    return float(max_spread)


def _rolling_mabd_energy(
    q: np.ndarray,
    qd: np.ndarray,
    config: RollingSpinningMABDNewtonConfig,
) -> float:
    points = mabd.affine_points(q, config.rest_points_m)
    velocities = mabd.affine_points(qd, config.rest_points_m)
    kinetic = 0.5 * float(
        np.sum(config.point_masses_kg * np.sum(velocities * velocities, axis=1))
    )
    potential = -float(np.sum(config.point_masses_kg * (points @ config.gravity_m_s2)))
    return kinetic + potential


def _rolling_mabd_support_height(
    q: np.ndarray,
    config: RollingSpinningMABDNewtonConfig,
) -> float:
    matrix, translation = mabd.unpack_q(q)
    normal = np.asarray([0.0, 1.0, 0.0], dtype=float)
    local_direction = matrix.T @ normal
    xy_norm = float(np.linalg.norm(local_direction[:2]))
    if xy_norm > 0.0:
        xy = -config.radius_m * local_direction[:2] / xy_norm
    else:
        xy = np.asarray([config.radius_m, 0.0], dtype=float)
    z_deadband = 1.0e-10 * float(np.linalg.norm(local_direction))
    if local_direction[2] > z_deadband:
        z = -config.half_height_m
    elif local_direction[2] < -z_deadband:
        z = config.half_height_m
    else:
        z = 0.0
    support = np.asarray([xy[0], xy[1], z], dtype=float)
    world_support = matrix @ support + translation
    return float(world_support[1])


def _rolling_mabd_sample(
    *,
    step_index: int,
    config: RollingSpinningMABDNewtonConfig,
    q: np.ndarray,
    qd: np.ndarray,
    contact_count: int,
    constraint_residual_norm: float,
) -> dict[str, object]:
    points = mabd.affine_points(q, config.rest_points_m)
    velocities = mabd.affine_points(qd, config.rest_points_m)
    center = _center_of_mass(points, config.point_masses_kg)
    center_velocity = _center_of_mass(velocities, config.point_masses_kg)
    angular_velocity = _affine_angular_velocity(q, qd)
    support_height = _rolling_mabd_support_height(q, config)
    return {
        "step_index": int(step_index),
        "time_s": float(step_index * config.time_step_s),
        "center_of_mass_m": center.tolist(),
        "linear_velocity_m_s": center_velocity.tolist(),
        "angular_velocity_rad_s": angular_velocity.tolist(),
        "contact_count": int(contact_count),
        "support_height_m": support_height,
        "support_penetration_m": float(max(0.0, -support_height)),
        "no_slip_residual_m_s": float(
            abs(center_velocity[0] + angular_velocity[2] * config.radius_m)
        ),
        "total_energy_j": _rolling_mabd_energy(q, qd, config),
        "affine_shape_spread_m": _affine_shape_spread(q, config.rest_points_m),
        "constraint_residual_norm": float(constraint_residual_norm),
    }


def _rolling_cylinder_sample(
    *,
    step_index: int,
    config: RollingSpinningRBDBaselineConfig,
    mass_kg: float,
    inertia_diag_kg_m2: np.ndarray,
    q: np.ndarray,
    qd: np.ndarray,
    contact_count: int,
) -> dict[str, object]:
    position = q[:3]
    linear_velocity = qd[:3]
    angular_velocity = qd[3:]
    energy = _rolling_cylinder_energy(
        mass_kg=mass_kg,
        inertia_diag_kg_m2=inertia_diag_kg_m2,
        gravity_m_s2=config.gravity_m_s2,
        position_m=position,
        linear_velocity_m_s=linear_velocity,
        angular_velocity_rad_s=angular_velocity,
    )
    return {
        "step_index": int(step_index),
        "time_s": float(step_index * config.time_step_s),
        "position_m": position.tolist(),
        "rotation_xyzw": q[3:].tolist(),
        "linear_velocity_m_s": linear_velocity.tolist(),
        "angular_velocity_rad_s": angular_velocity.tolist(),
        "contact_count": int(contact_count),
        "center_height_m": float(position[1]),
        "center_penetration_m": float(max(0.0, config.radius_m - position[1])),
        "no_slip_residual_m_s": float(
            abs(linear_velocity[0] + angular_velocity[2] * config.radius_m)
        ),
        "total_energy_j": energy,
    }


def _rolling_cylinder_no_slip_sample(
    *,
    step_index: int,
    config: RollingSpinningRBDBaselineConfig,
    position_m: np.ndarray,
    linear_velocity_m_s: np.ndarray,
    angular_velocity_rad_s: np.ndarray,
) -> dict[str, object]:
    return {
        "step_index": int(step_index),
        "time_s": float(step_index * config.time_step_s),
        "position_m": position_m.tolist(),
        "linear_velocity_m_s": linear_velocity_m_s.tolist(),
        "angular_velocity_rad_s": angular_velocity_rad_s.tolist(),
        "no_slip_residual_m_s": float(
            abs(linear_velocity_m_s[0] + angular_velocity_rad_s[2] * config.radius_m)
        ),
        "center_height_m": float(position_m[1]),
    }


def run_rolling_cylinder_rbd_no_slip_reference(
    config: RollingSpinningRBDBaselineConfig,
) -> RollingCylinderNoSlipReferenceResult:
    mass_kg, inertia_diag_kg_m2 = _rolling_cylinder_mass_and_inertia(config)
    duration_s = float(config.step_count * config.time_step_s)
    final_position = np.asarray(
        config.initial_position_m + config.initial_linear_velocity_m_s * duration_s,
        dtype=float,
    )
    final_linear_velocity = np.asarray(config.initial_linear_velocity_m_s, dtype=float)
    final_angular_velocity = np.asarray(config.initial_angular_velocity_rad_s, dtype=float)
    initial_energy = _rolling_cylinder_energy(
        mass_kg=mass_kg,
        inertia_diag_kg_m2=inertia_diag_kg_m2,
        gravity_m_s2=config.gravity_m_s2,
        position_m=config.initial_position_m,
        linear_velocity_m_s=config.initial_linear_velocity_m_s,
        angular_velocity_rad_s=config.initial_angular_velocity_rad_s,
    )
    final_energy = _rolling_cylinder_energy(
        mass_kg=mass_kg,
        inertia_diag_kg_m2=inertia_diag_kg_m2,
        gravity_m_s2=config.gravity_m_s2,
        position_m=final_position,
        linear_velocity_m_s=final_linear_velocity,
        angular_velocity_rad_s=final_angular_velocity,
    )
    trajectory_samples = []
    for step_index in sorted(_sample_indices(config.step_count, config.sample_count)):
        position = np.asarray(
            config.initial_position_m
            + config.initial_linear_velocity_m_s * (step_index * config.time_step_s),
            dtype=float,
        )
        trajectory_samples.append(
            _rolling_cylinder_no_slip_sample(
                step_index=step_index,
                config=config,
                position_m=position,
                linear_velocity_m_s=final_linear_velocity,
                angular_velocity_rad_s=final_angular_velocity,
            )
        )
    energy_drift = abs(final_energy - initial_energy)
    return RollingCylinderNoSlipReferenceResult(
        status=EvidenceStatus.INCOMPLETE,
        step_count=config.step_count,
        time_step_s=config.time_step_s,
        radius_m=config.radius_m,
        half_height_m=config.half_height_m,
        density_kg_m3=config.density_kg_m3,
        mass_kg=mass_kg,
        inertia_diag_kg_m2=inertia_diag_kg_m2,
        initial_position_m=np.asarray(config.initial_position_m, dtype=float),
        final_position_m=final_position,
        final_linear_velocity_m_s=final_linear_velocity,
        final_angular_velocity_rad_s=final_angular_velocity,
        initial_energy_j=float(initial_energy),
        final_energy_j=float(final_energy),
        energy_drift_j=float(energy_drift),
        relative_energy_drift=float(energy_drift / initial_energy),
        no_slip_residual_m_s=float(
            abs(final_linear_velocity[0] + final_angular_velocity[2] * config.radius_m)
        ),
        center_height_drift_m=float(abs(final_position[1] - config.initial_position_m[1])),
        contact_count_summary={
            "initial": 1,
            "final": 1,
            "min": 1,
            "max": 1,
        },
        total_wall_time_ms=0.0,
        trajectory_samples=tuple(trajectory_samples),
    )


def _run_rolling_cylinder_rbd_baseline(
    config: RollingSpinningRBDBaselineConfig,
    *,
    solver_kind: str,
) -> RollingCylinderRBDBaselineResult:
    mass_kg, inertia_diag_kg_m2 = _rolling_cylinder_mass_and_inertia(config)
    contact_counts: list[int] = []
    center_heights: list[float] = []
    trajectory_samples: list[dict[str, object]] = []
    sample_steps = _sample_indices(config.step_count, config.sample_count)

    with redirect_stdout(sys.stderr):
        import newton
        import warp as wp

        shape_config = newton.ModelBuilder.ShapeConfig(
            density=config.density_kg_m3,
            ke=config.contact["ke"],
            kd=config.contact["kd"],
            kf=config.contact["kf"],
            mu=config.contact["mu"],
            gap=config.contact["gap"],
        )
        builder = newton.ModelBuilder(up_axis="Y", gravity=float(config.gravity_m_s2[1]))
        body = builder.add_body(
            xform=wp.transform(
                wp.vec3(*config.initial_position_m.tolist()),
                wp.quat_identity(),
            ),
            label=f"rolling_cylinder_rbd_{solver_kind}_baseline",
        )
        builder.add_shape_cylinder(
            body,
            radius=config.radius_m,
            half_height=config.half_height_m,
            cfg=shape_config,
            label="rolling_cylinder",
        )
        builder.add_ground_plane(
            height=0.0,
            cfg=shape_config,
            label="rolling_ground_plane",
        )
        model = builder.finalize(device="cpu")
        state_in = model.state()
        state_out = model.state()
        control = model.control()
        contacts = model.contacts()

        body_qd = state_in.body_qd.numpy()
        body_qd[body] = np.concatenate(
            [
                config.initial_linear_velocity_m_s,
                config.initial_angular_velocity_rad_s,
            ]
        ).astype(np.float32)
        state_in.body_qd.assign(body_qd)

        if solver_kind == "implicit":
            solver = newton.solvers.SolverSemiImplicit(model, angular_damping=0.0)
        elif solver_kind == "explicit":
            solver = newton.solvers.SolverExplicitEuler(model, angular_damping=0.0)
        else:
            raise ValueError(f"unknown rolling-cylinder RBD solver kind: {solver_kind}")

        def record(step_index: int) -> None:
            contact_count = int(contacts.rigid_contact_count.numpy()[0])
            q = np.asarray(state_in.body_q.numpy()[body], dtype=float)
            qd = np.asarray(state_in.body_qd.numpy()[body], dtype=float)
            contact_counts.append(contact_count)
            center_heights.append(float(q[1]))
            if step_index in sample_steps:
                trajectory_samples.append(
                    _rolling_cylinder_sample(
                        step_index=step_index,
                        config=config,
                        mass_kg=mass_kg,
                        inertia_diag_kg_m2=inertia_diag_kg_m2,
                        q=q,
                        qd=qd,
                        contact_count=contact_count,
                    )
                )

        start = perf_counter()
        model.collide(state_in, contacts)
        record(0)
        for step_index in range(1, config.step_count + 1):
            state_in.clear_forces()
            model.collide(state_in, contacts)
            solver.step(state_in, state_out, control, contacts, config.time_step_s)
            state_in, state_out = state_out, state_in
            model.collide(state_in, contacts)
            record(step_index)
        total_wall_time_ms = (perf_counter() - start) * 1000.0

        final_q = np.asarray(state_in.body_q.numpy()[body], dtype=float)
        final_qd = np.asarray(state_in.body_qd.numpy()[body], dtype=float)

    initial_energy = _rolling_cylinder_energy(
        mass_kg=mass_kg,
        inertia_diag_kg_m2=inertia_diag_kg_m2,
        gravity_m_s2=config.gravity_m_s2,
        position_m=config.initial_position_m,
        linear_velocity_m_s=config.initial_linear_velocity_m_s,
        angular_velocity_rad_s=config.initial_angular_velocity_rad_s,
    )
    final_energy = _rolling_cylinder_energy(
        mass_kg=mass_kg,
        inertia_diag_kg_m2=inertia_diag_kg_m2,
        gravity_m_s2=config.gravity_m_s2,
        position_m=final_q[:3],
        linear_velocity_m_s=final_qd[:3],
        angular_velocity_rad_s=final_qd[3:],
    )
    energy_drift = abs(final_energy - initial_energy)
    min_center_height = min(center_heights)
    return RollingCylinderRBDBaselineResult(
        status=EvidenceStatus.INCOMPLETE,
        step_count=config.step_count,
        time_step_s=config.time_step_s,
        radius_m=config.radius_m,
        half_height_m=config.half_height_m,
        density_kg_m3=config.density_kg_m3,
        mass_kg=mass_kg,
        inertia_diag_kg_m2=inertia_diag_kg_m2,
        initial_position_m=config.initial_position_m,
        final_position_m=final_q[:3],
        final_rotation_xyzw=final_q[3:],
        final_linear_velocity_m_s=final_qd[:3],
        final_angular_velocity_rad_s=final_qd[3:],
        initial_energy_j=initial_energy,
        final_energy_j=final_energy,
        energy_drift_j=energy_drift,
        relative_energy_drift=energy_drift / initial_energy,
        no_slip_residual_m_s=float(abs(final_qd[0] + final_qd[5] * config.radius_m)),
        center_height_min_m=min_center_height,
        max_center_penetration_m=float(max(0.0, config.radius_m - min_center_height)),
        contact_count_summary={
            "initial": contact_counts[0],
            "final": contact_counts[-1],
            "min": min(contact_counts),
            "max": max(contact_counts),
        },
        contact_material=dict(config.contact),
        total_wall_time_ms=total_wall_time_ms,
        trajectory_samples=tuple(trajectory_samples),
    )


def run_rolling_cylinder_rbd_implicit_baseline(
    config: RollingSpinningRBDBaselineConfig,
) -> RollingCylinderRBDBaselineResult:
    return _run_rolling_cylinder_rbd_baseline(config, solver_kind="implicit")


def run_rolling_cylinder_rbd_explicit_baseline(
    config: RollingSpinningRBDBaselineConfig,
) -> RollingCylinderRBDBaselineResult:
    return _run_rolling_cylinder_rbd_baseline(config, solver_kind="explicit")


def _rolling_cylinder_mabd_solver_model(
    config: RollingSpinningMABDNewtonConfig,
) -> tuple[object, object, object]:
    with redirect_stdout(sys.stderr):
        import newton
        import warp as wp
        from newton.solvers import SolverMABD

        builder = newton.ModelBuilder(up_axis="Y", gravity=float(config.gravity_m_s2[1]))
        SolverMABD.register_custom_attributes(builder)
        body_id = builder.add_body(label="rolling_cylinder_mabd_newton")
        builder.add_custom_values(
            **{
                "mabd:body_index": body_id,
                "mabd:young_modulus": float(config.young_modulus_pa),
                "mabd:poisson_ratio": float(config.poisson_ratio),
                "mabd:density": config.density_kg_m3,
                "mabd:polar_mode": 1,
                "mabd:rest_point0": _vec3(config.rest_points_m[0], wp),
                "mabd:rest_point1": _vec3(config.rest_points_m[1], wp),
                "mabd:rest_point2": _vec3(config.rest_points_m[2], wp),
                "mabd:rest_point3": _vec3(config.rest_points_m[3], wp),
                "mabd:point_mass0": float(config.point_masses_kg[0]),
                "mabd:point_mass1": float(config.point_masses_kg[1]),
                "mabd:point_mass2": float(config.point_masses_kg[2]),
                "mabd:point_mass3": float(config.point_masses_kg[3]),
                "mabd:volume": float(config.volume_m3),
                "mabd:zero_stiffness_diagnostic": int(config.zero_stiffness_diagnostic),
            }
        )
        builder.add_custom_values(
            **{
                "mabd:gravity_enabled": 1,
                "mabd:gravity_vector": _vec3(config.gravity_m_s2, wp),
            }
        )
        builder.add_shape_cylinder(
            body=body_id,
            radius=config.radius_m,
            half_height=config.half_height_m,
            label="rolling_cylinder_mabd_shape",
        )
        builder.add_ground_plane(height=0.0, label="rolling_ground_plane")
        model = builder.finalize(device="cpu")
        solver = SolverMABD(model)
        state = model.state()
    return model, solver, state


def run_rolling_cylinder_mabd_newton(
    config: RollingSpinningMABDNewtonConfig,
) -> RollingCylinderMABDNewtonResult:
    contact_counts: list[int] = []
    support_heights: list[float] = []
    shape_spreads: list[float] = []
    constraint_residuals: list[float] = []
    trajectory_samples: list[dict[str, object]] = []
    sample_steps = _sample_indices(config.step_count, config.sample_count)

    _model, solver, state = _rolling_cylinder_mabd_solver_model(config)
    q, qd = _rolling_mabd_initial_state(config)
    _assign_mabd_solver_state(state, q, qd)
    initial_energy = _rolling_mabd_energy(q, qd, config)
    latest_summary = None
    latest_constraint_residual = 0.0

    with redirect_stdout(sys.stderr):
        start = perf_counter()
        for step_index in range(config.step_count + 1):
            q, qd = _read_mabd_solver_state(state)
            contacts = solver.detect_static_plane_contacts(state)
            latest_summary = solver.last_static_plane_collision_summary
            contact_count = int(contacts.rigid_contact_count.numpy()[0])
            support_height = _rolling_mabd_support_height(q, config)
            shape_spread = _affine_shape_spread(q, config.rest_points_m)
            contact_counts.append(contact_count)
            support_heights.append(support_height)
            shape_spreads.append(shape_spread)
            constraint_residuals.append(latest_constraint_residual)
            if step_index in sample_steps:
                trajectory_samples.append(
                    _rolling_mabd_sample(
                        step_index=step_index,
                        config=config,
                        q=q,
                        qd=qd,
                        contact_count=contact_count,
                        constraint_residual_norm=latest_constraint_residual,
                    )
                )
            if step_index == config.step_count:
                break
            solver.step(state, state, None, contacts, config.time_step_s)
            if solver.last_step_result is not None:
                latest_constraint_residual = float(
                    solver.last_step_result.constraint_residual_norm
                )
        total_wall_time_ms = (perf_counter() - start) * 1000.0
        final_q, final_qd = _read_mabd_solver_state(state)

    final_points = mabd.affine_points(final_q, config.rest_points_m)
    final_velocities = mabd.affine_points(final_qd, config.rest_points_m)
    final_center = _center_of_mass(final_points, config.point_masses_kg)
    final_linear_velocity = _center_of_mass(final_velocities, config.point_masses_kg)
    final_angular_velocity = _affine_angular_velocity(final_q, final_qd)
    final_energy = _rolling_mabd_energy(final_q, final_qd, config)
    energy_drift = abs(final_energy - initial_energy)
    min_support_height = min(support_heights)
    if latest_summary is None:
        static_policy = "not_recorded"
        static_scope = "not_recorded"
        static_candidate_count = 0
        static_cylinder_shape_count = 0
        static_plane_shape_count = 0
    else:
        static_policy = latest_summary.policy
        static_scope = latest_summary.scope
        static_candidate_count = int(latest_summary.candidate_contact_count)
        static_cylinder_shape_count = int(latest_summary.cylinder_shape_count)
        static_plane_shape_count = int(latest_summary.static_plane_shape_count)

    return RollingCylinderMABDNewtonResult(
        status=EvidenceStatus.INCOMPLETE,
        step_count=config.step_count,
        time_step_s=config.time_step_s,
        radius_m=config.radius_m,
        half_height_m=config.half_height_m,
        density_kg_m3=config.density_kg_m3,
        mass_kg=float(np.sum(config.point_masses_kg)),
        volume_m3=config.volume_m3,
        rotation_mode=config.rotation_mode,
        rest_points_m=config.rest_points_m,
        point_masses_kg=config.point_masses_kg,
        initial_position_m=config.initial_position_m,
        final_center_of_mass_m=final_center,
        final_linear_velocity_m_s=final_linear_velocity,
        final_angular_velocity_rad_s=final_angular_velocity,
        initial_energy_j=float(initial_energy),
        final_energy_j=float(final_energy),
        energy_drift_j=float(energy_drift),
        relative_energy_drift=float(energy_drift / initial_energy),
        no_slip_residual_m_s=float(
            abs(final_linear_velocity[0] + final_angular_velocity[2] * config.radius_m)
        ),
        min_support_height_m=float(min_support_height),
        max_support_penetration_m=float(max(0.0, -min_support_height)),
        max_affine_shape_spread_m=float(max(shape_spreads)),
        max_constraint_residual_norm=float(max(constraint_residuals)),
        contact_count_summary={
            "initial": contact_counts[0],
            "final": contact_counts[-1],
            "min": min(contact_counts),
            "max": max(contact_counts),
        },
        static_plane_collision_policy=static_policy,
        static_plane_collision_scope=static_scope,
        static_plane_candidate_count=static_candidate_count,
        static_plane_cylinder_shape_count=static_cylinder_shape_count,
        static_plane_plane_shape_count=static_plane_shape_count,
        total_wall_time_ms=total_wall_time_ms,
        trajectory_samples=tuple(trajectory_samples),
    )


def write_rolling_spinning_protocol_report(
    path: str | Path,
    *,
    config: RollingSpinningRunConfig,
    source_commit: str,
    vendored_newton_commit: str,
    paper_source_version: str = "2603.08079v2",
) -> ClaimReport:
    expected = {
        "paper_claim_status": (
            "requires rolling cylinder runtime benchmark and RBD baselines before pass"
        ),
        "source_lines": list(config.source_lines),
        "benchmark_body": config.performance.body,
        "benchmark_step_count": config.performance.step_count,
        "time_step_s": config.performance.time_step_s,
        "paper_hardware_context": config.performance.paper_hardware_context,
        "paper_total_simulation_time_ms": dict(
            config.performance.paper_total_simulation_time_ms
        ),
        "required_metrics": list(config.thresholds),
        "full_experiment_claim_passed": False,
    }
    observed = {
        "local_runtime_measured": False,
        "protocol_status": config.performance.protocol_status,
        "required_lanes_missing": list(config.required_missing_lanes),
        "blocking_reasons": [
            "rbd_baseline_adapter_missing",
            "benchmark_protocol_not_recorded",
            "rolling_cylinder_runtime_not_measured",
        ],
        "paper_metric_statuses": {
            "total_simulation_time_ms": "paper_reference_recorded_no_local_runtime",
            "linear_momentum_error": "not_measured_by_phase73",
            "angular_momentum_error": "not_measured_by_phase73",
            "energy_drift": "not_measured_by_phase73",
        },
        "full_experiment_claim_passed": False,
    }
    report = ClaimReport(
        claim_id=config.claim_id,
        scene_id=config.scene_id,
        asset_hashes={
            "primitive_cylinder": "not_applicable_procedural",
            "primitive_cube": "not_applicable_procedural",
        },
        solver_mode="rolling_spinning_protocol_audit",
        backend="report_protocol",
        baseline_lane=config.baseline_lane,
        expected=expected,
        observed=observed,
        threshold=config.thresholds,
        unit="json_report",
        status=config.report_status,
        failure_reason=config.failure_reason,
        timing_distribution={
            "status": "not_measured",
            "paper_comparable": False,
        },
        raw_outputs={},
        plot_paths={},
        source_commit=source_commit,
        vendored_newton_commit=vendored_newton_commit,
        paper_source_version=paper_source_version,
    )
    write_claim_report(report, path)
    return report


def write_rolling_spinning_rbd_implicit_baseline_report(
    path: str | Path,
    *,
    config: RollingSpinningRunConfig,
    source_commit: str,
    vendored_newton_commit: str,
    paper_source_version: str = "2603.08079v2",
) -> ClaimReport:
    result = run_rolling_cylinder_rbd_implicit_baseline(config.rbd_implicit_baseline)
    expected = {
        "paper_claim_status": (
            "requires explicit RBD, M-ABD rolling-cylinder, and paper-comparable "
            "timing before pass"
        ),
        "source_lines": list(config.source_lines),
        "config_path": ROLLING_SPINNING_CONFIG_PATH,
        "canonical_python": CANONICAL_PYTHON,
        "benchmark_body": config.performance.body,
        "paper_total_simulation_time_ms": dict(
            config.performance.paper_total_simulation_time_ms
        ),
        "paper_hardware_context": config.performance.paper_hardware_context,
        "paper_comparable": False,
        "full_experiment_claim_passed": False,
    }
    observed = {
        "local_runtime_measured": True,
        "paper_comparable": False,
        "full_experiment_claim_passed": False,
        "required_lanes_missing": list(ROLLING_SPINNING_RBD_REQUIRED_MISSING_LANES),
        "blocking_reasons": list(ROLLING_SPINNING_RBD_BLOCKING_REASONS),
        "newton_api": list(ROLLING_SPINNING_RBD_NEWTON_API),
        "newton_device": "cpu",
        "cylinder_axis_world": [0.0, 0.0, 1.0],
        "solver_name": "newton.solvers.SolverSemiImplicit",
        "solver_scope": "newton_development_baseline_not_paper_faithful_implicit_rbd",
        "step_count": result.step_count,
        "time_step_s": result.time_step_s,
        "radius_m": result.radius_m,
        "half_height_m": result.half_height_m,
        "density_kg_m3": result.density_kg_m3,
        "mass_kg": result.mass_kg,
        "inertia_diag_kg_m2": result.inertia_diag_kg_m2.tolist(),
        "initial_position_m": result.initial_position_m.tolist(),
        "final_position_m": result.final_position_m.tolist(),
        "final_rotation_xyzw": result.final_rotation_xyzw.tolist(),
        "final_linear_velocity_m_s": result.final_linear_velocity_m_s.tolist(),
        "final_angular_velocity_rad_s": result.final_angular_velocity_rad_s.tolist(),
        "initial_energy_j": result.initial_energy_j,
        "final_energy_j": result.final_energy_j,
        "energy_drift_j": result.energy_drift_j,
        "relative_energy_drift": result.relative_energy_drift,
        "no_slip_residual_m_s": result.no_slip_residual_m_s,
        "min_center_height_m": result.center_height_min_m,
        "max_center_penetration_m": result.max_center_penetration_m,
        "contact_count_summary": dict(result.contact_count_summary),
        "contact_material": dict(result.contact_material),
        "trajectory_samples": list(result.trajectory_samples),
    }
    report = ClaimReport(
        claim_id=config.claim_id,
        scene_id=config.scene_id,
        asset_hashes={
            "primitive_cylinder": "not_applicable_procedural",
            "primitive_cube": "not_applicable_procedural",
        },
        solver_mode="newton_semimplicit_rolling_cylinder_rbd_cpu_development",
        backend="cpu_newton_warp",
        baseline_lane="rbd_implicit_baseline",
        expected=expected,
        observed=observed,
        threshold=dict(config.rbd_implicit_baseline.thresholds),
        unit="json_report",
        status=result.status,
        failure_reason=(
            "Newton SemiImplicit rolling-cylinder development baseline only; explicit "
            "RBD, M-ABD rolling-cylinder, and paper-comparable timing evidence remain missing"
        ),
        timing_distribution={
            "total_wall_time_ms": result.total_wall_time_ms,
            "step_count": result.step_count,
            "paper_comparable": False,
            "scope": "local_cpu_wall_clock_not_paper_comparable",
        },
        raw_outputs={"time_series": "not_written"},
        plot_paths={},
        source_commit=source_commit,
        vendored_newton_commit=vendored_newton_commit,
        paper_source_version=paper_source_version,
    )
    write_claim_report(report, path)
    return report


def write_rolling_spinning_rbd_explicit_baseline_report(
    path: str | Path,
    *,
    config: RollingSpinningRunConfig,
    source_commit: str,
    vendored_newton_commit: str,
    paper_source_version: str = "2603.08079v2",
) -> ClaimReport:
    result = run_rolling_cylinder_rbd_explicit_baseline(config.rbd_explicit_baseline)
    expected = {
        "paper_claim_status": (
            "requires M-ABD rolling-cylinder and paper-comparable timing before pass; "
            "this explicit RBD lane is a Newton development baseline"
        ),
        "source_lines": list(config.source_lines),
        "config_path": ROLLING_SPINNING_CONFIG_PATH,
        "canonical_python": CANONICAL_PYTHON,
        "benchmark_body": config.performance.body,
        "paper_total_simulation_time_ms": dict(
            config.performance.paper_total_simulation_time_ms
        ),
        "paper_hardware_context": config.performance.paper_hardware_context,
        "paper_comparable": False,
        "full_experiment_claim_passed": False,
    }
    observed = {
        "local_runtime_measured": True,
        "paper_comparable": False,
        "full_experiment_claim_passed": False,
        "required_lanes_missing": list(
            ROLLING_SPINNING_RBD_EXPLICIT_REQUIRED_MISSING_LANES
        ),
        "blocking_reasons": list(ROLLING_SPINNING_RBD_EXPLICIT_BLOCKING_REASONS),
        "newton_api": list(ROLLING_SPINNING_RBD_EXPLICIT_NEWTON_API),
        "newton_device": "cpu",
        "cylinder_axis_world": [0.0, 0.0, 1.0],
        "solver_name": "newton.solvers.SolverExplicitEuler",
        "solver_scope": "newton_development_baseline_not_paper_faithful_explicit_rbd",
        "step_count": result.step_count,
        "time_step_s": result.time_step_s,
        "radius_m": result.radius_m,
        "half_height_m": result.half_height_m,
        "density_kg_m3": result.density_kg_m3,
        "mass_kg": result.mass_kg,
        "inertia_diag_kg_m2": result.inertia_diag_kg_m2.tolist(),
        "initial_position_m": result.initial_position_m.tolist(),
        "final_position_m": result.final_position_m.tolist(),
        "final_rotation_xyzw": result.final_rotation_xyzw.tolist(),
        "final_linear_velocity_m_s": result.final_linear_velocity_m_s.tolist(),
        "final_angular_velocity_rad_s": result.final_angular_velocity_rad_s.tolist(),
        "initial_energy_j": result.initial_energy_j,
        "final_energy_j": result.final_energy_j,
        "energy_drift_j": result.energy_drift_j,
        "relative_energy_drift": result.relative_energy_drift,
        "no_slip_residual_m_s": result.no_slip_residual_m_s,
        "min_center_height_m": result.center_height_min_m,
        "max_center_penetration_m": result.max_center_penetration_m,
        "contact_count_summary": dict(result.contact_count_summary),
        "contact_material": dict(result.contact_material),
        "trajectory_samples": list(result.trajectory_samples),
    }
    report = ClaimReport(
        claim_id=config.claim_id,
        scene_id=config.scene_id,
        asset_hashes={
            "primitive_cylinder": "not_applicable_procedural",
            "primitive_cube": "not_applicable_procedural",
        },
        solver_mode="newton_explicit_euler_rolling_cylinder_rbd_cpu_development",
        backend="cpu_newton_warp",
        baseline_lane="rbd_explicit_baseline",
        expected=expected,
        observed=observed,
        threshold=dict(config.rbd_explicit_baseline.thresholds),
        unit="json_report",
        status=result.status,
        failure_reason=(
            "Newton ExplicitEuler rolling-cylinder development baseline only; M-ABD "
            "rolling-cylinder and paper-comparable timing evidence remain missing"
        ),
        timing_distribution={
            "total_wall_time_ms": result.total_wall_time_ms,
            "step_count": result.step_count,
            "paper_comparable": False,
            "scope": "local_cpu_wall_clock_not_paper_comparable",
        },
        raw_outputs={"time_series": "not_written"},
        plot_paths={},
        source_commit=source_commit,
        vendored_newton_commit=vendored_newton_commit,
        paper_source_version=paper_source_version,
    )
    write_claim_report(report, path)
    return report


def write_rolling_spinning_rbd_no_slip_reference_report(
    path: str | Path,
    *,
    config: RollingSpinningRunConfig,
    source_commit: str,
    vendored_newton_commit: str,
    paper_source_version: str = "2603.08079v2",
) -> ClaimReport:
    lane_config = config.rbd_no_slip_reference
    result = run_rolling_cylinder_rbd_no_slip_reference(lane_config)
    thresholds = dict(lane_config.thresholds)
    thresholds["max_center_height_drift_m"] = 1.0e-12
    threshold_violations: list[str] = []
    if result.no_slip_residual_m_s > thresholds["max_no_slip_residual_m_s"]:
        threshold_violations.append("max_no_slip_residual_m_s")
    if abs(result.relative_energy_drift) > thresholds["max_relative_energy_drift"]:
        threshold_violations.append("max_relative_energy_drift")
    if result.contact_count_summary["max"] < thresholds["min_contact_count"]:
        threshold_violations.append("min_contact_count")
    if result.center_height_drift_m > thresholds["max_center_height_drift_m"]:
        threshold_violations.append("max_center_height_drift_m")

    expected = {
        "paper_claim_status": (
            "analytic no-slip rolling-cylinder reference generated; this is not "
            "paper-faithful RBD, M-ABD contact/friction, or paper-comparable timing"
        ),
        "source_lines": list(config.source_lines),
        "config_path": ROLLING_SPINNING_CONFIG_PATH,
        "canonical_python": CANONICAL_PYTHON,
        "benchmark_body": config.performance.body,
        "paper_total_simulation_time_ms": dict(
            config.performance.paper_total_simulation_time_ms
        ),
        "paper_hardware_context": config.performance.paper_hardware_context,
        "paper_comparable": False,
        "full_experiment_claim_passed": False,
        "known_source_gaps": [
            "paper does not specify cylinder dimensions, mass, or initial state",
            "paper exact explicit and implicit RBD solver details are not available",
            "paper affine rolling contact/friction solve is not yet implemented",
            "paper-comparable i7 single-thread timing is not measured by this lane",
        ],
    }
    observed = {
        "reference_status": "analytic_no_slip_reference_generated",
        "local_runtime_measured": False,
        "paper_comparable": False,
        "full_experiment_claim_passed": False,
        "required_reproduction_gaps_remaining": list(
            ROLLING_SPINNING_NO_SLIP_REQUIRED_REPRODUCTION_GAPS
        ),
        "blocking_reasons": list(ROLLING_SPINNING_NO_SLIP_BLOCKING_REASONS),
        "threshold_violations": threshold_violations,
        "step_count": result.step_count,
        "time_step_s": result.time_step_s,
        "sample_count": len(result.trajectory_samples),
        "radius_m": result.radius_m,
        "half_height_m": result.half_height_m,
        "density_kg_m3": result.density_kg_m3,
        "mass_kg": result.mass_kg,
        "inertia_diag_kg_m2": result.inertia_diag_kg_m2.tolist(),
        "initial_position_m": result.initial_position_m.tolist(),
        "final_position_m": result.final_position_m.tolist(),
        "final_linear_velocity_m_s": result.final_linear_velocity_m_s.tolist(),
        "final_angular_velocity_rad_s": result.final_angular_velocity_rad_s.tolist(),
        "initial_energy_j": result.initial_energy_j,
        "final_energy_j": result.final_energy_j,
        "energy_drift_j": result.energy_drift_j,
        "relative_energy_drift": result.relative_energy_drift,
        "no_slip_residual_m_s": result.no_slip_residual_m_s,
        "center_height_drift_m": result.center_height_drift_m,
        "contact_count_summary": dict(result.contact_count_summary),
        "contact_material": dict(lane_config.contact),
        "trajectory_samples": list(result.trajectory_samples),
    }
    report = ClaimReport(
        claim_id=config.claim_id,
        scene_id=config.scene_id,
        asset_hashes={
            "primitive_cylinder": "not_applicable_procedural",
            "primitive_cube": "not_applicable_procedural",
        },
        solver_mode="analytic_no_slip_rolling_cylinder_reference",
        backend="cpu_numpy_closed_form",
        baseline_lane="rbd_no_slip_reference",
        expected=expected,
        observed=observed,
        threshold=thresholds,
        unit="json_report",
        status=result.status,
        failure_reason=(
            "Analytic no-slip reference only; paper-faithful explicit RBD, implicit "
            "RBD, M-ABD rolling-cylinder contact/friction, and paper-comparable "
            "timing evidence remain missing"
        ),
        timing_distribution={
            "status": "not_measured",
            "step_count": result.step_count,
            "paper_comparable": False,
            "scope": "local_closed_form_reference_not_paper_comparable",
        },
        raw_outputs={},
        plot_paths={},
        source_commit=source_commit,
        vendored_newton_commit=vendored_newton_commit,
        paper_source_version=paper_source_version,
    )
    write_claim_report(report, path)
    return report


def write_rolling_spinning_mabd_newton_report(
    path: str | Path,
    *,
    config: RollingSpinningRunConfig,
    source_commit: str,
    vendored_newton_commit: str,
    paper_source_version: str = "2603.08079v2",
) -> ClaimReport:
    result = run_rolling_cylinder_mabd_newton(config.mabd_newton)
    thresholds = config.mabd_newton.thresholds
    threshold_violations: list[str] = []
    if result.no_slip_residual_m_s > thresholds["max_no_slip_residual_m_s"]:
        threshold_violations.append("max_no_slip_residual_m_s")
    if result.relative_energy_drift > thresholds["max_relative_energy_drift"]:
        threshold_violations.append("max_relative_energy_drift")
    if result.contact_count_summary["max"] < thresholds["min_contact_count"]:
        threshold_violations.append("min_contact_count")
    if result.max_affine_shape_spread_m > thresholds["max_affine_shape_spread_m"]:
        threshold_violations.append("max_affine_shape_spread_m")
    if result.max_constraint_residual_norm > thresholds["max_constraint_residual_norm"]:
        threshold_violations.append("max_constraint_residual_norm")
    if result.total_wall_time_ms > thresholds["max_runtime_wall_time_ms"]:
        threshold_violations.append("max_runtime_wall_time_ms")

    expected = {
        "paper_claim_status": (
            "M-ABD rolling-cylinder Newton diagnostic generated; full paper claim "
            "requires paper-faithful affine contact/friction and paper-comparable timing"
        ),
        "source_lines": list(config.source_lines),
        "config_path": ROLLING_SPINNING_CONFIG_PATH,
        "canonical_python": CANONICAL_PYTHON,
        "benchmark_body": config.performance.body,
        "paper_total_simulation_time_ms": dict(
            config.performance.paper_total_simulation_time_ms
        ),
        "paper_hardware_context": config.performance.paper_hardware_context,
        "paper_comparable": False,
        "known_source_gaps": [
            "paper affine-cylinder contact manifold details are not yet implemented",
            "paper rolling friction/no-slip solve is not yet implemented",
            "paper-comparable i7 single-thread timing protocol is not yet measured",
        ],
        "full_experiment_claim_passed": False,
    }
    observed = {
        "lane_status": (
            "incomplete_diagnostic_generated"
            if not threshold_violations
            else "incomplete_diagnostic_failed"
        ),
        "local_runtime_measured": True,
        "paper_comparable": False,
        "full_experiment_claim_passed": False,
        "required_lanes_missing": list(ROLLING_SPINNING_MABD_REQUIRED_MISSING_LANES),
        "blocking_reasons": list(ROLLING_SPINNING_MABD_BLOCKING_REASONS),
        "threshold_violations": threshold_violations,
        "newton_api": list(ROLLING_SPINNING_MABD_NEWTON_API),
        "newton_device": "cpu",
        "solver_name": "newton.solvers.SolverMABD",
        "solver_scope": "mabd_affine_cylinder_static_plane_diagnostic_not_paper_faithful",
        "step_count": result.step_count,
        "time_step_s": result.time_step_s,
        "radius_m": result.radius_m,
        "half_height_m": result.half_height_m,
        "density_kg_m3": result.density_kg_m3,
        "mass_kg": result.mass_kg,
        "volume_m3": result.volume_m3,
        "rotation_mode": result.rotation_mode,
        "rest_points_m": result.rest_points_m.tolist(),
        "point_masses_kg": result.point_masses_kg.tolist(),
        "initial_position_m": result.initial_position_m.tolist(),
        "final_center_of_mass_m": result.final_center_of_mass_m.tolist(),
        "final_linear_velocity_m_s": result.final_linear_velocity_m_s.tolist(),
        "final_angular_velocity_rad_s": result.final_angular_velocity_rad_s.tolist(),
        "initial_energy_j": result.initial_energy_j,
        "final_energy_j": result.final_energy_j,
        "energy_drift_j": result.energy_drift_j,
        "relative_energy_drift": result.relative_energy_drift,
        "no_slip_residual_m_s": result.no_slip_residual_m_s,
        "min_support_height_m": result.min_support_height_m,
        "max_support_penetration_m": result.max_support_penetration_m,
        "max_affine_shape_spread_m": result.max_affine_shape_spread_m,
        "max_constraint_residual_norm": result.max_constraint_residual_norm,
        "contact_count_summary": dict(result.contact_count_summary),
        "static_plane_collision_policy": result.static_plane_collision_policy,
        "static_plane_collision_scope": result.static_plane_collision_scope,
        "static_plane_candidate_count": result.static_plane_candidate_count,
        "static_plane_cylinder_shape_count": result.static_plane_cylinder_shape_count,
        "static_plane_plane_shape_count": result.static_plane_plane_shape_count,
        "trajectory_samples": list(result.trajectory_samples),
    }
    report = ClaimReport(
        claim_id=config.claim_id,
        scene_id=config.scene_id,
        asset_hashes={
            "primitive_cylinder": "not_applicable_procedural",
            "primitive_cube": "not_applicable_procedural",
        },
        solver_mode="mabd_cpu_oracle_rolling_cylinder_newton_lane",
        backend="cpu_numpy_newton_solver_mabd_static_plane_contacts",
        baseline_lane="mabd_newton",
        expected=expected,
        observed=observed,
        threshold=dict(thresholds),
        unit="json_report",
        status=result.status,
        failure_reason=(
            "SolverMABD rolling-cylinder diagnostic only; paper-faithful M-ABD "
            "affine contact/friction, paper-faithful explicit RBD, and "
            "paper-comparable timing evidence remain missing"
        ),
        timing_distribution={
            "total_wall_time_ms": result.total_wall_time_ms,
            "step_count": result.step_count,
            "paper_comparable": False,
            "scope": "local_cpu_wall_clock_not_paper_comparable",
        },
        raw_outputs={"time_series": "not_written"},
        plot_paths={},
        source_commit=source_commit,
        vendored_newton_commit=vendored_newton_commit,
        paper_source_version=paper_source_version,
    )
    write_claim_report(report, path)
    return report


def write_rolling_spinning_mabd_material_preflight_report(
    path: str | Path,
    *,
    config: RollingSpinningRunConfig,
    source_commit: str,
    vendored_newton_commit: str,
    paper_source_version: str = "2603.08079v2",
) -> ClaimReport:
    material_config = config.mabd_material_preflight
    result = run_rolling_cylinder_mabd_newton(material_config)
    thresholds = material_config.thresholds
    threshold_violations: list[str] = []
    if result.no_slip_residual_m_s > thresholds["max_no_slip_residual_m_s"]:
        threshold_violations.append("max_no_slip_residual_m_s")
    if result.relative_energy_drift > thresholds["max_relative_energy_drift"]:
        threshold_violations.append("max_relative_energy_drift")
    if result.contact_count_summary["max"] < thresholds["min_contact_count"]:
        threshold_violations.append("min_contact_count")
    if result.max_affine_shape_spread_m > thresholds["max_affine_shape_spread_m"]:
        threshold_violations.append("max_affine_shape_spread_m")
    if result.max_constraint_residual_norm > thresholds["max_constraint_residual_norm"]:
        threshold_violations.append("max_constraint_residual_norm")
    if result.total_wall_time_ms > thresholds["max_runtime_wall_time_ms"]:
        threshold_violations.append("max_runtime_wall_time_ms")

    expected = {
        "paper_claim_status": (
            "finite-stiffness M-ABD rolling-cylinder preflight only; full paper "
            "claim requires paper-faithful contact/friction, RBD baselines, and timing"
        ),
        "source_lines": list(config.source_lines),
        "config_path": ROLLING_SPINNING_CONFIG_PATH,
        "canonical_python": CANONICAL_PYTHON,
        "benchmark_body": config.performance.body,
        "paper_total_simulation_time_ms": dict(
            config.performance.paper_total_simulation_time_ms
        ),
        "paper_hardware_context": config.performance.paper_hardware_context,
        "paper_comparable": False,
        "full_experiment_claim_passed": False,
        "known_source_gaps": [
            "paper affine-cylinder contact manifold details are not yet implemented",
            "paper rolling friction/no-slip solve is not yet implemented",
            "paper-faithful explicit and implicit RBD baselines are not yet recorded",
            "paper-comparable i7 single-thread timing protocol is not yet measured",
        ],
    }
    observed = {
        "material_preflight_status": "finite_stiffness_preflight_incomplete",
        "lane_status": "incomplete_material_preflight_generated",
        "local_runtime_measured": True,
        "paper_comparable": False,
        "full_experiment_claim_passed": False,
        "required_lanes_missing": list(
            ROLLING_SPINNING_MABD_MATERIAL_PREFLIGHT_REQUIRED_MISSING_LANES
        ),
        "blocking_reasons": list(ROLLING_SPINNING_MABD_MATERIAL_PREFLIGHT_BLOCKING_REASONS),
        "threshold_violations": threshold_violations,
        "newton_api": list(ROLLING_SPINNING_MABD_NEWTON_API),
        "newton_device": "cpu",
        "solver_name": "newton.solvers.SolverMABD",
        "solver_scope": "mabd_affine_cylinder_material_preflight_not_paper_faithful",
        "young_modulus_pa": material_config.young_modulus_pa,
        "poisson_ratio": material_config.poisson_ratio,
        "zero_stiffness_diagnostic": material_config.zero_stiffness_diagnostic,
        "step_count": result.step_count,
        "time_step_s": result.time_step_s,
        "radius_m": result.radius_m,
        "half_height_m": result.half_height_m,
        "density_kg_m3": result.density_kg_m3,
        "mass_kg": result.mass_kg,
        "volume_m3": result.volume_m3,
        "rotation_mode": result.rotation_mode,
        "rest_points_m": result.rest_points_m.tolist(),
        "point_masses_kg": result.point_masses_kg.tolist(),
        "initial_position_m": result.initial_position_m.tolist(),
        "final_center_of_mass_m": result.final_center_of_mass_m.tolist(),
        "final_linear_velocity_m_s": result.final_linear_velocity_m_s.tolist(),
        "final_angular_velocity_rad_s": result.final_angular_velocity_rad_s.tolist(),
        "initial_energy_j": result.initial_energy_j,
        "final_energy_j": result.final_energy_j,
        "energy_drift_j": result.energy_drift_j,
        "relative_energy_drift": result.relative_energy_drift,
        "no_slip_residual_m_s": result.no_slip_residual_m_s,
        "min_support_height_m": result.min_support_height_m,
        "max_support_penetration_m": result.max_support_penetration_m,
        "max_affine_shape_spread_m": result.max_affine_shape_spread_m,
        "max_constraint_residual_norm": result.max_constraint_residual_norm,
        "contact_count_summary": dict(result.contact_count_summary),
        "static_plane_collision_policy": result.static_plane_collision_policy,
        "static_plane_collision_scope": result.static_plane_collision_scope,
        "static_plane_candidate_count": result.static_plane_candidate_count,
        "static_plane_cylinder_shape_count": result.static_plane_cylinder_shape_count,
        "static_plane_plane_shape_count": result.static_plane_plane_shape_count,
        "trajectory_samples": list(result.trajectory_samples),
    }
    report = ClaimReport(
        claim_id=config.claim_id,
        scene_id=config.scene_id,
        asset_hashes={
            "primitive_cylinder": "not_applicable_procedural",
            "primitive_cube": "not_applicable_procedural",
        },
        solver_mode="mabd_cpu_oracle_rolling_cylinder_material_preflight",
        backend="cpu_numpy_newton_solver_mabd_static_plane_contacts",
        baseline_lane="mabd_newton",
        expected=expected,
        observed=observed,
        threshold=dict(thresholds),
        unit="json_report",
        status=result.status,
        failure_reason=(
            "Finite-stiffness SolverMABD rolling-cylinder material preflight only; "
            "paper-faithful M-ABD contact/friction, RBD baselines, and "
            "paper-comparable timing evidence remain missing"
        ),
        timing_distribution={
            "total_wall_time_ms": result.total_wall_time_ms,
            "step_count": result.step_count,
            "paper_comparable": False,
            "scope": "local_cpu_wall_clock_not_paper_comparable",
        },
        raw_outputs={"time_series": "not_written"},
        plot_paths={},
        source_commit=source_commit,
        vendored_newton_commit=vendored_newton_commit,
        paper_source_version=paper_source_version,
    )
    write_claim_report(report, path)
    return report


def _summarize_timing_input_report(report_path: str) -> dict[str, object]:
    report = load_claim_report(report_path)
    paper_comparable = report.observed.get(
        "paper_comparable",
        report.timing_distribution.get("paper_comparable", False),
    )
    return {
        "path": report_path,
        "status": report.status.value,
        "baseline_lane": report.baseline_lane,
        "solver_mode": report.solver_mode,
        "paper_comparable": bool(paper_comparable),
        "total_wall_time_ms": report.timing_distribution.get("total_wall_time_ms"),
    }


def write_rolling_spinning_paper_timing_protocol_report(
    path: str | Path,
    *,
    config: RollingSpinningRunConfig,
    source_commit: str,
    vendored_newton_commit: str,
    paper_source_version: str = "2603.08079v2",
) -> ClaimReport:
    timing_config = config.paper_timing_protocol
    input_reports = [
        _summarize_timing_input_report(report_path)
        for report_path in timing_config.input_reports
    ]
    expected = {
        "paper_claim_status": (
            "paper timing table and local input report timings are recorded; full "
            "claim requires a paper-comparable single-thread timing run and "
            "paper-faithful RBD/M-ABD lanes"
        ),
        "source_lines": list(config.source_lines),
        "config_path": ROLLING_SPINNING_CONFIG_PATH,
        "canonical_python": CANONICAL_PYTHON,
        "benchmark_body": config.performance.body,
        "paper_step_count": config.performance.step_count,
        "paper_time_step_s": config.performance.time_step_s,
        "paper_total_simulation_time_ms": dict(
            config.performance.paper_total_simulation_time_ms
        ),
        "paper_hardware_context": config.performance.paper_hardware_context,
        "paper_comparable": True,
        "full_experiment_claim_passed": False,
    }
    observed = {
        "timing_protocol_status": "paper_timing_protocol_incomplete",
        "local_runtime_inputs_recorded": True,
        "paper_comparable": timing_config.paper_comparable,
        "full_experiment_claim_passed": False,
        "local_environment_python": CANONICAL_PYTHON,
        "input_reports": input_reports,
        "blocking_reasons": list(ROLLING_SPINNING_TIMING_PROTOCOL_BLOCKING_REASONS),
    }
    report = ClaimReport(
        claim_id=config.claim_id,
        scene_id=config.scene_id,
        asset_hashes={
            "primitive_cylinder": "not_applicable_procedural",
            "primitive_cube": "not_applicable_procedural",
        },
        solver_mode="rolling_spinning_paper_timing_protocol_audit",
        backend="report_protocol",
        baseline_lane="paper_timing_protocol",
        expected=expected,
        observed=observed,
        threshold=dict(config.thresholds),
        unit="json_report",
        status=EvidenceStatus.INCOMPLETE,
        failure_reason=(
            "Paper timing protocol artifact only; paper-comparable hardware/threading "
            "run plus paper-faithful M-ABD, explicit RBD, and implicit RBD lanes "
            "remain missing"
        ),
        timing_distribution={
            "paper_comparable": False,
            "scope": "paper_timing_protocol_artifact_not_comparable",
            "paper_hardware_context": config.performance.paper_hardware_context,
            "local_input_report_count": len(input_reports),
        },
        raw_outputs={},
        plot_paths={},
        source_commit=source_commit,
        vendored_newton_commit=vendored_newton_commit,
        paper_source_version=paper_source_version,
    )
    write_claim_report(report, path)
    return report


__all__ = [
    "RollingCylinderMABDNewtonResult",
    "RollingCylinderRBDBaselineResult",
    "run_rolling_cylinder_mabd_newton",
    "run_rolling_cylinder_rbd_explicit_baseline",
    "run_rolling_cylinder_rbd_implicit_baseline",
    "write_rolling_spinning_mabd_material_preflight_report",
    "write_rolling_spinning_mabd_newton_report",
    "write_rolling_spinning_paper_timing_protocol_report",
    "write_rolling_spinning_rbd_explicit_baseline_report",
    "write_rolling_spinning_protocol_report",
    "write_rolling_spinning_rbd_implicit_baseline_report",
]
