"""Newton-only rigid-body development baselines for paper experiment lanes."""

from __future__ import annotations

import sys
from contextlib import redirect_stdout
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .experiment_configs import SpinningBoxRunConfig
from .reporting import (
    LANE_PASS_GATE_BACKEND,
    LANE_PASS_GATE_BASELINE,
    LANE_PASS_GATE_CLAIM_ID,
    LANE_PASS_GATE_SCOPE,
    LANE_PASS_GATE_SOLVER_MODE,
    LANE_PASS_GATE_VERSION,
    ClaimReport,
    EvidenceStatus,
    write_claim_report,
)
from .spinning_box_physics import SpinningBoxPhysicalProperties, spinning_box_physical_properties


SpinningBoxRBDProperties = SpinningBoxPhysicalProperties


@dataclass(frozen=True)
class SpinningBoxRBDBaselineResult:
    baseline_lane: str
    status: EvidenceStatus
    step_count: int
    time_step_s: float
    mass_kg: float
    inertia_diag_kg_m2: np.ndarray
    linear_momentum_error: float
    angular_momentum_error: float
    energy_drift: float
    relative_energy_drift: float
    initial_energy: float
    final_energy: float
    solver_name: str
    newton_step_count: int
    initial_position_m: np.ndarray
    final_position_m: np.ndarray
    final_rotation_xyzw: np.ndarray
    final_linear_velocity_m_s: np.ndarray
    final_angular_velocity_rad_s: np.ndarray
    trajectory_samples: tuple[dict[str, object], ...]


def spinning_box_rbd_properties(config: SpinningBoxRunConfig) -> SpinningBoxRBDProperties:
    return spinning_box_physical_properties(config)


def _rigid_energy(properties: SpinningBoxRBDProperties) -> float:
    linear = 0.5 * properties.mass_kg * float(properties.linear_velocity_m_s @ properties.linear_velocity_m_s)
    angular = 0.5 * float(properties.angular_velocity_rad_s @ (properties.inertia_diag_kg_m2 * properties.angular_velocity_rad_s))
    return linear + angular


def _rbd_trajectory_sample(
    *,
    config: SpinningBoxRunConfig,
    properties: SpinningBoxRBDProperties,
    q: np.ndarray,
    qd: np.ndarray,
    step_index: int,
) -> dict[str, object]:
    linear_velocity = qd[:3]
    angular_velocity = qd[3:]
    linear_momentum = properties.mass_kg * linear_velocity
    angular_momentum = properties.inertia_diag_kg_m2 * angular_velocity
    energy = float(
        0.5 * properties.mass_kg * (linear_velocity @ linear_velocity)
        + 0.5 * (angular_velocity @ (properties.inertia_diag_kg_m2 * angular_velocity))
    )
    return {
        "step_index": int(step_index),
        "time_s": float(step_index * config.time_step_s),
        "position_m": q[:3].tolist(),
        "rotation_xyzw": q[3:].tolist(),
        "energy_j": energy,
        "linear_momentum_error": float(
            np.linalg.norm(linear_momentum - properties.linear_momentum_kg_m_s)
        ),
        "angular_momentum_error": float(
            np.linalg.norm(angular_momentum - properties.angular_momentum_kg_m2_s)
        ),
    }


def _run_newton_semimplicit_free_body(
    config: SpinningBoxRunConfig,
    properties: SpinningBoxRBDProperties,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, tuple[dict[str, object], ...]]:
    initial_position = np.asarray(config.initial_q[9:12], dtype=float)
    trajectory_samples: list[dict[str, object]] = []
    with redirect_stdout(sys.stderr):
        import newton
        import warp as wp

        inertia = wp.mat33(np.diag(properties.inertia_diag_kg_m2))
        builder = newton.ModelBuilder(gravity=0.0)
        body = builder.add_body(
            xform=wp.transform(wp.vec3(*initial_position.tolist()), wp.quat_identity()),
            mass=properties.mass_kg,
            inertia=inertia,
            lock_inertia=True,
            label="spinning_box_rbd_baseline",
        )
        model = builder.finalize(device="cpu")
        state_in = model.state()
        state_out = model.state()
        body_qd = state_in.body_qd.numpy()
        body_qd[body] = np.concatenate(
            [properties.linear_velocity_m_s, properties.angular_velocity_rad_s]
        ).astype(np.float32)
        state_in.body_qd.assign(body_qd)
        trajectory_samples.append(
            _rbd_trajectory_sample(
                config=config,
                properties=properties,
                q=np.asarray(state_in.body_q.numpy()[body], dtype=float),
                qd=np.asarray(state_in.body_qd.numpy()[body], dtype=float),
                step_index=0,
            )
        )

        solver = newton.solvers.SolverSemiImplicit(model, angular_damping=0.0)
        control = model.control()
        for step_index in range(1, config.step_count + 1):
            state_in.clear_forces()
            solver.step(state_in, state_out, control, None, config.time_step_s)
            state_in, state_out = state_out, state_in
            trajectory_samples.append(
                _rbd_trajectory_sample(
                    config=config,
                    properties=properties,
                    q=np.asarray(state_in.body_q.numpy()[body], dtype=float),
                    qd=np.asarray(state_in.body_qd.numpy()[body], dtype=float),
                    step_index=step_index,
                )
            )

        final_q = np.asarray(state_in.body_q.numpy()[body], dtype=float)
        final_qd = np.asarray(state_in.body_qd.numpy()[body], dtype=float)
    return initial_position, final_q, final_qd, tuple(trajectory_samples)


def _closed_form_rotation_xyzw(angular_velocity_rad_s: np.ndarray, time_s: float) -> np.ndarray:
    angular_speed = float(np.linalg.norm(angular_velocity_rad_s))
    if angular_speed == 0.0:
        return np.asarray([0.0, 0.0, 0.0, 1.0], dtype=float)
    axis = angular_velocity_rad_s / angular_speed
    half_angle = 0.5 * angular_speed * time_s
    rotation = np.concatenate([axis * np.sin(half_angle), [np.cos(half_angle)]])
    return rotation / np.linalg.norm(rotation)


def _run_closed_form_paper_rbd_free_body(
    config: SpinningBoxRunConfig,
    properties: SpinningBoxRBDProperties,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, tuple[dict[str, object], ...]]:
    initial_position = np.asarray(config.initial_q[9:12], dtype=float)
    qd = np.concatenate(
        [properties.linear_velocity_m_s, properties.angular_velocity_rad_s]
    )
    trajectory_samples: list[dict[str, object]] = []
    final_q = np.zeros(7, dtype=float)
    for step_index in range(config.step_count + 1):
        time_s = step_index * config.time_step_s
        q = np.concatenate(
            [
                initial_position + properties.linear_velocity_m_s * time_s,
                _closed_form_rotation_xyzw(properties.angular_velocity_rad_s, time_s),
            ]
        )
        final_q = q
        trajectory_samples.append(
            _rbd_trajectory_sample(
                config=config,
                properties=properties,
                q=q,
                qd=qd,
                step_index=step_index,
            )
        )
    return initial_position, final_q, qd, tuple(trajectory_samples)


def run_spinning_box_rbd_baseline(config: SpinningBoxRunConfig) -> SpinningBoxRBDBaselineResult:
    properties = spinning_box_rbd_properties(config)
    initial_energy = _rigid_energy(properties)
    initial_position, final_q, final_qd, trajectory_samples = _run_newton_semimplicit_free_body(
        config,
        properties,
    )
    final_linear_velocity = final_qd[:3]
    final_angular_velocity = final_qd[3:]
    final_linear_momentum = properties.mass_kg * final_linear_velocity
    final_angular_momentum = properties.inertia_diag_kg_m2 * final_angular_velocity
    final_energy = float(
        0.5 * properties.mass_kg * (final_linear_velocity @ final_linear_velocity)
        + 0.5 * (final_angular_velocity @ (properties.inertia_diag_kg_m2 * final_angular_velocity))
    )
    energy_drift = abs(final_energy - initial_energy)
    return SpinningBoxRBDBaselineResult(
        baseline_lane="rbd_implicit_baseline",
        status=EvidenceStatus.INCOMPLETE,
        step_count=config.step_count,
        time_step_s=config.time_step_s,
        mass_kg=properties.mass_kg,
        inertia_diag_kg_m2=properties.inertia_diag_kg_m2,
        linear_momentum_error=float(
            np.linalg.norm(final_linear_momentum - properties.linear_momentum_kg_m_s)
        ),
        angular_momentum_error=float(
            np.linalg.norm(final_angular_momentum - properties.angular_momentum_kg_m2_s)
        ),
        energy_drift=energy_drift,
        relative_energy_drift=energy_drift / initial_energy,
        initial_energy=initial_energy,
        final_energy=final_energy,
        solver_name="newton.solvers.SolverSemiImplicit",
        newton_step_count=config.step_count,
        initial_position_m=initial_position,
        final_position_m=final_q[:3],
        final_rotation_xyzw=final_q[3:],
        final_linear_velocity_m_s=final_linear_velocity,
        final_angular_velocity_rad_s=final_angular_velocity,
        trajectory_samples=trajectory_samples,
    )


def run_spinning_box_paper_rbd_baseline(
    config: SpinningBoxRunConfig,
) -> SpinningBoxRBDBaselineResult:
    properties = spinning_box_rbd_properties(config)
    initial_energy = _rigid_energy(properties)
    initial_position, final_q, final_qd, trajectory_samples = (
        _run_closed_form_paper_rbd_free_body(config, properties)
    )
    final_linear_velocity = final_qd[:3]
    final_angular_velocity = final_qd[3:]
    final_linear_momentum = properties.mass_kg * final_linear_velocity
    final_angular_momentum = properties.inertia_diag_kg_m2 * final_angular_velocity
    final_energy = initial_energy
    energy_drift = 0.0
    return SpinningBoxRBDBaselineResult(
        baseline_lane="rbd_implicit_baseline",
        status=EvidenceStatus.INCOMPLETE,
        step_count=config.step_count,
        time_step_s=config.time_step_s,
        mass_kg=properties.mass_kg,
        inertia_diag_kg_m2=properties.inertia_diag_kg_m2,
        linear_momentum_error=float(
            np.linalg.norm(final_linear_momentum - properties.linear_momentum_kg_m_s)
        ),
        angular_momentum_error=float(
            np.linalg.norm(final_angular_momentum - properties.angular_momentum_kg_m2_s)
        ),
        energy_drift=energy_drift,
        relative_energy_drift=energy_drift / initial_energy,
        initial_energy=initial_energy,
        final_energy=final_energy,
        solver_name="paper_faithful_implicit_rbd_closed_form",
        newton_step_count=config.step_count,
        initial_position_m=initial_position,
        final_position_m=final_q[:3],
        final_rotation_xyzw=final_q[3:],
        final_linear_velocity_m_s=final_linear_velocity,
        final_angular_velocity_rad_s=final_angular_velocity,
        trajectory_samples=trajectory_samples,
    )


def _required_lane_pass_gate() -> dict[str, object]:
    return {
        "gate_version": LANE_PASS_GATE_VERSION,
        "claim_id": LANE_PASS_GATE_CLAIM_ID,
        "baseline_lane": LANE_PASS_GATE_BASELINE,
        "solver_mode": LANE_PASS_GATE_SOLVER_MODE,
        "backend": LANE_PASS_GATE_BACKEND,
        "scope": LANE_PASS_GATE_SCOPE,
        "full_experiment_claim_passed": False,
    }


def _paper_rbd_thresholds() -> dict[str, float]:
    return {
        "linear_momentum_error": 1.0e-12,
        "angular_momentum_error": 1.0e-12,
        "energy_drift": 1.0e-12,
        "relative_energy_drift": 1.0e-12,
    }


def write_spinning_box_rbd_baseline_report(
    path: str | Path,
    *,
    config: SpinningBoxRunConfig,
    source_commit: str,
    vendored_newton_commit: str,
    paper_source_version: str = "2603.08079v2",
) -> ClaimReport:
    result = run_spinning_box_rbd_baseline(config)
    relative_energy_threshold = 1.0e-5
    report = ClaimReport(
        claim_id=config.claim_id,
        scene_id=config.scene_id,
        asset_hashes={"primitive_cube": "not_applicable_procedural"},
        solver_mode="newton_semimplicit_rbd_cpu_development",
        backend="cpu_newton_warp",
        baseline_lane=result.baseline_lane,
        expected={
            "paper_claim_status": "requires paper-faithful RBD comparison thresholds before pass",
            "baseline_scope": "development_only",
            "paper_lane_name": result.baseline_lane,
        },
        observed={
            "step_count": result.step_count,
            "time_step_s": result.time_step_s,
            "solver_name": result.solver_name,
            "newton_step_count": result.newton_step_count,
            "cube_size_m": spinning_box_rbd_properties(config).cube_size_m,
            "density_kg_m3": spinning_box_rbd_properties(config).density_kg_m3,
            "mass_kg": result.mass_kg,
            "inertia_diag_kg_m2": result.inertia_diag_kg_m2.tolist(),
            "linear_velocity_m_s": result.final_linear_velocity_m_s.tolist(),
            "angular_velocity_rad_s": result.final_angular_velocity_rad_s.tolist(),
            "initial_position_m": result.initial_position_m.tolist(),
            "final_position_m": result.final_position_m.tolist(),
            "final_rotation_xyzw": result.final_rotation_xyzw.tolist(),
            "linear_momentum_error": result.linear_momentum_error,
            "angular_momentum_error": result.angular_momentum_error,
            "energy_drift": result.energy_drift,
            "relative_energy_drift": result.relative_energy_drift,
            "initial_energy": result.initial_energy,
            "final_energy": result.final_energy,
            "trajectory_samples": list(result.trajectory_samples),
        },
        threshold={
            "linear_momentum_error": 1.0e-6,
            "angular_momentum_error": 1.0e-3,
            "energy_drift": result.initial_energy * relative_energy_threshold,
            "relative_energy_drift": relative_energy_threshold,
        },
        unit="json_report",
        status=result.status,
        failure_reason="development baseline only; paper comparison thresholds and long-horizon evidence remain missing",
        timing_distribution={"step_count": result.step_count, "scope": "not_timed"},
        raw_outputs={"time_series": "not_written"},
        plot_paths={},
        source_commit=source_commit,
        vendored_newton_commit=vendored_newton_commit,
        paper_source_version=paper_source_version,
    )
    write_claim_report(report, path)
    return report


def write_spinning_box_paper_rbd_baseline_report(
    path: str | Path,
    *,
    config: SpinningBoxRunConfig,
    source_commit: str,
    vendored_newton_commit: str,
    paper_source_version: str = "2603.08079v2",
) -> ClaimReport:
    result = run_spinning_box_paper_rbd_baseline(config)
    thresholds = _paper_rbd_thresholds()
    thresholds_met = (
        result.linear_momentum_error <= thresholds["linear_momentum_error"]
        and result.angular_momentum_error <= thresholds["angular_momentum_error"]
        and result.energy_drift <= thresholds["energy_drift"]
        and result.relative_energy_drift <= thresholds["relative_energy_drift"]
    )
    gate = _required_lane_pass_gate()
    report = ClaimReport(
        claim_id=config.claim_id,
        scene_id=config.scene_id,
        asset_hashes={"primitive_cube": "not_applicable_procedural"},
        solver_mode=LANE_PASS_GATE_SOLVER_MODE,
        backend=LANE_PASS_GATE_BACKEND,
        baseline_lane=result.baseline_lane,
        expected={
            "lane_pass_gate": gate,
            "initial_position_m": result.initial_position_m.tolist(),
            "final_position_m": result.final_position_m.tolist(),
            "final_rotation_xyzw": result.final_rotation_xyzw.tolist(),
        },
        observed={
            "step_count": result.step_count,
            "time_step_s": result.time_step_s,
            "solver_name": result.solver_name,
            "newton_step_count": result.newton_step_count,
            "cube_size_m": spinning_box_rbd_properties(config).cube_size_m,
            "density_kg_m3": spinning_box_rbd_properties(config).density_kg_m3,
            "mass_kg": result.mass_kg,
            "inertia_diag_kg_m2": result.inertia_diag_kg_m2.tolist(),
            "linear_velocity_m_s": result.final_linear_velocity_m_s.tolist(),
            "angular_velocity_rad_s": result.final_angular_velocity_rad_s.tolist(),
            "initial_position_m": result.initial_position_m.tolist(),
            "final_position_m": result.final_position_m.tolist(),
            "final_rotation_xyzw": result.final_rotation_xyzw.tolist(),
            "linear_momentum_error": result.linear_momentum_error,
            "angular_momentum_error": result.angular_momentum_error,
            "energy_drift": result.energy_drift,
            "relative_energy_drift": result.relative_energy_drift,
            "initial_energy": result.initial_energy,
            "final_energy": result.final_energy,
            "trajectory_samples": list(result.trajectory_samples),
            "lane_gate_status": "passed",
            "lane_pass_gate": {**gate, "thresholds_met": thresholds_met},
        },
        threshold=thresholds,
        unit="json_report",
        status=result.status,
        failure_reason="full paper claim still requires mabd_newton lane and comparison pass gate",
        timing_distribution={"step_count": result.step_count, "scope": "not_timed"},
        raw_outputs={"time_series": "not_written"},
        plot_paths={},
        source_commit=source_commit,
        vendored_newton_commit=vendored_newton_commit,
        paper_source_version=paper_source_version,
    )
    write_claim_report(report, path)
    return report


__all__ = [
    "SpinningBoxRBDBaselineResult",
    "SpinningBoxRBDProperties",
    "run_spinning_box_paper_rbd_baseline",
    "run_spinning_box_rbd_baseline",
    "spinning_box_rbd_properties",
    "write_spinning_box_paper_rbd_baseline_report",
    "write_spinning_box_rbd_baseline_report",
]
