"""Report lane for the rolling/spinning single-body experiment surface."""

from __future__ import annotations

import sys
from contextlib import redirect_stdout
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter

import numpy as np

from .experiment_configs import (
    RollingSpinningRBDBaselineConfig,
    RollingSpinningRunConfig,
)
from .reporting import ClaimReport, EvidenceStatus, write_claim_report


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


def run_rolling_cylinder_rbd_implicit_baseline(
    config: RollingSpinningRBDBaselineConfig,
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
            label="rolling_cylinder_rbd_implicit_baseline",
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

        solver = newton.solvers.SolverSemiImplicit(model, angular_damping=0.0)

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


__all__ = [
    "RollingCylinderRBDBaselineResult",
    "run_rolling_cylinder_rbd_implicit_baseline",
    "write_rolling_spinning_protocol_report",
    "write_rolling_spinning_rbd_implicit_baseline_report",
]
