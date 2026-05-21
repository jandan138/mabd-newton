"""Development-only 10 second spinning-box MABD/RBD comparison lane."""

from __future__ import annotations

import sys
from contextlib import redirect_stdout
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter

import numpy as np
from newton.solvers import SolverMABD, mabd

from .experiment_configs import (
    SpinningBoxDevelopmentComparisonConfig,
    SpinningBoxRunConfig,
)
from .reporting import ClaimReport, EvidenceStatus, write_claim_report
from .single_body_reports import (
    _assign_solver_mabd_state,
    _elastic_energy,
    _kinetic_energy,
    _read_solver_mabd_state,
    _spinning_box_solver_mabd_body_points,
)
from .spinning_box_physics import (
    mabd_momentum_diagnostics,
    spinning_box_mabd_material_properties,
    spinning_box_mabd_material_stiffness,
    spinning_box_physical_properties,
)


@dataclass(frozen=True)
class SpinningBoxDevelopmentRollout:
    solver_name: str
    backend: str
    step_count: int
    time_step_s: float
    duration_s: float
    total_wall_time_ms: float
    initial_energy_j: float
    final_energy_j: float
    energy_drift_j: float
    final_position_m: np.ndarray
    final_linear_momentum_kg_m_s: np.ndarray
    final_angular_momentum_kg_m2_s: np.ndarray
    trajectory_samples: tuple[dict[str, object], ...]


def _sample_indices(step_count: int, sample_count: int) -> set[int]:
    if sample_count >= step_count + 1:
        return set(range(step_count + 1))
    return {int(round(value)) for value in np.linspace(0, step_count, sample_count)}


def _development_step_count(config: SpinningBoxDevelopmentComparisonConfig) -> int:
    return int(round(config.duration_s / config.time_step_s))


def _development_initial_qd(config: SpinningBoxRunConfig) -> np.ndarray:
    lane = config.development_comparison
    spatial_twist = np.concatenate(
        [
            lane.initial_angular_velocity_rad_s,
            lane.initial_linear_velocity_m_s,
        ]
    )
    return mabd.rigid_embedding_E(np.eye(3)) @ spatial_twist


def _mabd_sample(
    *,
    config: SpinningBoxRunConfig,
    q: np.ndarray,
    qd: np.ndarray,
    step_index: int,
    time_step_s: float,
    mass_matrix: np.ndarray,
) -> dict[str, object]:
    momentum = mabd_momentum_diagnostics(config, q, qd)
    kinetic_energy = _kinetic_energy(qd, mass_matrix)
    elastic_energy = _elastic_energy(config=config, q=q)
    return {
        "step_index": int(step_index),
        "time_s": float(step_index * time_step_s),
        "position_m": q[9:12].tolist(),
        "kinetic_energy_j": kinetic_energy,
        "elastic_energy_j": elastic_energy,
        "total_energy_j": kinetic_energy + elastic_energy,
        "linear_momentum_kg_m_s": momentum.linear_momentum_kg_m_s.tolist(),
        "angular_momentum_kg_m2_s": momentum.angular_momentum_kg_m2_s.tolist(),
        "linear_momentum_error": momentum.linear_momentum_error,
        "angular_momentum_error": momentum.angular_momentum_error,
    }


def _rbd_energy(
    *,
    mass_kg: float,
    inertia_diag_kg_m2: np.ndarray,
    linear_velocity_m_s: np.ndarray,
    angular_velocity_rad_s: np.ndarray,
) -> float:
    return float(
        0.5 * mass_kg * (linear_velocity_m_s @ linear_velocity_m_s)
        + 0.5
        * (angular_velocity_rad_s @ (inertia_diag_kg_m2 * angular_velocity_rad_s))
    )


def _rbd_sample(
    *,
    step_index: int,
    time_step_s: float,
    q: np.ndarray,
    qd: np.ndarray,
    mass_kg: float,
    inertia_diag_kg_m2: np.ndarray,
) -> dict[str, object]:
    linear_velocity = qd[:3]
    angular_velocity = qd[3:]
    linear_momentum = mass_kg * linear_velocity
    angular_momentum = inertia_diag_kg_m2 * angular_velocity
    return {
        "step_index": int(step_index),
        "time_s": float(step_index * time_step_s),
        "position_m": q[:3].tolist(),
        "rotation_xyzw": q[3:].tolist(),
        "energy_j": _rbd_energy(
            mass_kg=mass_kg,
            inertia_diag_kg_m2=inertia_diag_kg_m2,
            linear_velocity_m_s=linear_velocity,
            angular_velocity_rad_s=angular_velocity,
        ),
        "linear_momentum_kg_m_s": linear_momentum.tolist(),
        "angular_momentum_kg_m2_s": angular_momentum.tolist(),
    }


def run_spinning_box_solver_mabd_development_rollout(
    config: SpinningBoxRunConfig,
) -> SpinningBoxDevelopmentRollout:
    with redirect_stdout(sys.stderr):
        import newton
        import warp as wp

    lane = config.development_comparison
    step_count = _development_step_count(lane)
    sample_indices = _sample_indices(step_count, lane.sample_count)
    properties = spinning_box_physical_properties(config)
    material = spinning_box_mabd_material_properties(config)
    rest_points = _spinning_box_solver_mabd_body_points(config)
    point_mass = properties.mass_kg / 4.0
    mass_matrix = np.diag(config.mass_diagonal)

    builder = newton.ModelBuilder()
    SolverMABD.register_custom_attributes(builder)
    body_id = builder.add_body()
    builder.add_custom_values(
        **{
            "mabd:body_index": body_id,
            "mabd:young_modulus": material.young_modulus_pa,
            "mabd:poisson_ratio": material.poisson_ratio,
            "mabd:density": properties.density_kg_m3,
            "mabd:polar_mode": 1,
            "mabd:rest_point0": wp.vec3(*rest_points[0]),
            "mabd:rest_point1": wp.vec3(*rest_points[1]),
            "mabd:rest_point2": wp.vec3(*rest_points[2]),
            "mabd:rest_point3": wp.vec3(*rest_points[3]),
            "mabd:point_mass0": point_mass,
            "mabd:point_mass1": point_mass,
            "mabd:point_mass2": point_mass,
            "mabd:point_mass3": point_mass,
            "mabd:volume": material.volume_m3,
            "mabd:zero_stiffness_diagnostic": 0,
        }
    )
    model = builder.finalize(device="cpu")
    state = model.state()
    solver = SolverMABD(model)
    q = config.initial_q.copy()
    qd = _development_initial_qd(config)
    _assign_solver_mabd_state(state, q, qd)

    trajectory_samples: list[dict[str, object]] = []
    initial_energy = _kinetic_energy(qd, mass_matrix) + _elastic_energy(config=config, q=q)
    start = perf_counter()
    for step_index in range(step_count + 1):
        q, qd = _read_solver_mabd_state(state)
        if step_index in sample_indices:
            trajectory_samples.append(
                _mabd_sample(
                    config=config,
                    q=q,
                    qd=qd,
                    step_index=step_index,
                    time_step_s=lane.time_step_s,
                    mass_matrix=mass_matrix,
                )
            )
        if step_index == step_count:
            break
        solver.step(state, state, control=None, contacts=None, dt=lane.time_step_s)
    total_wall_time_ms = (perf_counter() - start) * 1000.0
    q, qd = _read_solver_mabd_state(state)
    final_momentum = mabd_momentum_diagnostics(config, q, qd)
    final_energy = _kinetic_energy(qd, mass_matrix) + _elastic_energy(config=config, q=q)

    return SpinningBoxDevelopmentRollout(
        solver_name="newton.solvers.SolverMABD",
        backend="cpu_newton_warp",
        step_count=step_count,
        time_step_s=lane.time_step_s,
        duration_s=lane.duration_s,
        total_wall_time_ms=total_wall_time_ms,
        initial_energy_j=initial_energy,
        final_energy_j=final_energy,
        energy_drift_j=abs(final_energy - initial_energy),
        final_position_m=q[9:12],
        final_linear_momentum_kg_m_s=final_momentum.linear_momentum_kg_m_s,
        final_angular_momentum_kg_m2_s=final_momentum.angular_momentum_kg_m2_s,
        trajectory_samples=tuple(trajectory_samples),
    )


def run_spinning_box_rbd_development_rollout(
    config: SpinningBoxRunConfig,
) -> SpinningBoxDevelopmentRollout:
    with redirect_stdout(sys.stderr):
        import newton
        import warp as wp

    lane = config.development_comparison
    step_count = _development_step_count(lane)
    sample_indices = _sample_indices(step_count, lane.sample_count)
    properties = spinning_box_physical_properties(config)
    initial_position = np.asarray(config.initial_q[9:12], dtype=float)
    initial_linear_velocity = lane.initial_linear_velocity_m_s
    initial_angular_velocity = lane.initial_angular_velocity_rad_s
    initial_energy = _rbd_energy(
        mass_kg=properties.mass_kg,
        inertia_diag_kg_m2=properties.inertia_diag_kg_m2,
        linear_velocity_m_s=initial_linear_velocity,
        angular_velocity_rad_s=initial_angular_velocity,
    )

    builder = newton.ModelBuilder(gravity=0.0)
    body = builder.add_body(
        xform=wp.transform(wp.vec3(*initial_position.tolist()), wp.quat_identity()),
        mass=properties.mass_kg,
        inertia=wp.mat33(np.diag(properties.inertia_diag_kg_m2)),
        lock_inertia=True,
        label="spinning_box_development_comparison_rbd",
    )
    model = builder.finalize(device="cpu")
    state_in = model.state()
    state_out = model.state()
    body_qd = state_in.body_qd.numpy()
    body_qd[body] = np.concatenate(
        [initial_linear_velocity, initial_angular_velocity]
    ).astype(np.float32)
    state_in.body_qd.assign(body_qd)
    solver = newton.solvers.SolverSemiImplicit(model, angular_damping=0.0)
    control = model.control()

    trajectory_samples: list[dict[str, object]] = []
    start = perf_counter()
    for step_index in range(step_count + 1):
        q = np.asarray(state_in.body_q.numpy()[body], dtype=float)
        qd = np.asarray(state_in.body_qd.numpy()[body], dtype=float)
        if step_index in sample_indices:
            trajectory_samples.append(
                _rbd_sample(
                    step_index=step_index,
                    time_step_s=lane.time_step_s,
                    q=q,
                    qd=qd,
                    mass_kg=properties.mass_kg,
                    inertia_diag_kg_m2=properties.inertia_diag_kg_m2,
                )
            )
        if step_index == step_count:
            break
        state_in.clear_forces()
        solver.step(state_in, state_out, control, None, lane.time_step_s)
        state_in, state_out = state_out, state_in
    total_wall_time_ms = (perf_counter() - start) * 1000.0
    q = np.asarray(state_in.body_q.numpy()[body], dtype=float)
    qd = np.asarray(state_in.body_qd.numpy()[body], dtype=float)
    final_linear_velocity = qd[:3]
    final_angular_velocity = qd[3:]
    final_energy = _rbd_energy(
        mass_kg=properties.mass_kg,
        inertia_diag_kg_m2=properties.inertia_diag_kg_m2,
        linear_velocity_m_s=final_linear_velocity,
        angular_velocity_rad_s=final_angular_velocity,
    )

    return SpinningBoxDevelopmentRollout(
        solver_name="newton.solvers.SolverSemiImplicit",
        backend="cpu_newton_warp",
        step_count=step_count,
        time_step_s=lane.time_step_s,
        duration_s=lane.duration_s,
        total_wall_time_ms=total_wall_time_ms,
        initial_energy_j=initial_energy,
        final_energy_j=final_energy,
        energy_drift_j=abs(final_energy - initial_energy),
        final_position_m=q[:3],
        final_linear_momentum_kg_m_s=properties.mass_kg * final_linear_velocity,
        final_angular_momentum_kg_m2_s=(
            properties.inertia_diag_kg_m2 * final_angular_velocity
        ),
        trajectory_samples=tuple(trajectory_samples),
    )


def _energy_curve_samples(
    mabd_rollout: SpinningBoxDevelopmentRollout,
    rbd_rollout: SpinningBoxDevelopmentRollout,
) -> list[dict[str, float]]:
    samples: list[dict[str, float]] = []
    for mabd_sample, rbd_sample in zip(
        mabd_rollout.trajectory_samples,
        rbd_rollout.trajectory_samples,
        strict=True,
    ):
        mabd_energy = float(mabd_sample["total_energy_j"])
        rbd_energy = float(rbd_sample["energy_j"])
        samples.append(
            {
                "time_s": float(mabd_sample["time_s"]),
                "mabd_total_energy_j": mabd_energy,
                "rbd_energy_j": rbd_energy,
                "energy_delta_j": abs(mabd_energy - rbd_energy),
            }
        )
    return samples


def _comparison_metrics(
    mabd_rollout: SpinningBoxDevelopmentRollout,
    rbd_rollout: SpinningBoxDevelopmentRollout,
    energy_curve_samples: list[dict[str, float]],
) -> dict[str, float]:
    position_deltas = [
        float(
            np.linalg.norm(
                np.asarray(mabd_sample["position_m"], dtype=float)
                - np.asarray(rbd_sample["position_m"], dtype=float)
            )
        )
        for mabd_sample, rbd_sample in zip(
            mabd_rollout.trajectory_samples,
            rbd_rollout.trajectory_samples,
            strict=True,
        )
    ]
    linear_momentum_deltas = [
        float(
            np.linalg.norm(
                np.asarray(mabd_sample["linear_momentum_kg_m_s"], dtype=float)
                - np.asarray(rbd_sample["linear_momentum_kg_m_s"], dtype=float)
            )
        )
        for mabd_sample, rbd_sample in zip(
            mabd_rollout.trajectory_samples,
            rbd_rollout.trajectory_samples,
            strict=True,
        )
    ]
    angular_momentum_deltas = [
        float(
            np.linalg.norm(
                np.asarray(mabd_sample["angular_momentum_kg_m2_s"], dtype=float)
                - np.asarray(rbd_sample["angular_momentum_kg_m2_s"], dtype=float)
            )
        )
        for mabd_sample, rbd_sample in zip(
            mabd_rollout.trajectory_samples,
            rbd_rollout.trajectory_samples,
            strict=True,
        )
    ]
    energy_deltas = [sample["energy_delta_j"] for sample in energy_curve_samples]
    return {
        "final_position_delta_m": position_deltas[-1],
        "max_position_delta_m": max(position_deltas),
        "final_energy_delta_j": energy_deltas[-1],
        "max_energy_delta_j": max(energy_deltas),
        "final_linear_momentum_delta_norm": linear_momentum_deltas[-1],
        "max_linear_momentum_delta_norm": max(linear_momentum_deltas),
        "final_angular_momentum_delta_norm": angular_momentum_deltas[-1],
        "max_angular_momentum_delta_norm": max(angular_momentum_deltas),
    }


def write_spinning_box_development_comparison_report(
    path: str | Path,
    *,
    config: SpinningBoxRunConfig,
    source_commit: str,
    vendored_newton_commit: str,
    paper_source_version: str = "2603.08079v2",
) -> ClaimReport:
    mabd_rollout = run_spinning_box_solver_mabd_development_rollout(config)
    rbd_rollout = run_spinning_box_rbd_development_rollout(config)
    energy_curve = _energy_curve_samples(mabd_rollout, rbd_rollout)
    comparison_metrics = _comparison_metrics(mabd_rollout, rbd_rollout, energy_curve)
    lane = config.development_comparison

    observed = {
        "comparison_status": "development_comparison_recorded",
        "comparison_scope": lane.comparison_scope,
        "paper_faithful": False,
        "full_experiment_claim_passed": False,
        "duration_s": lane.duration_s,
        "time_step_s": lane.time_step_s,
        "step_count": mabd_rollout.step_count,
        "sample_count": len(energy_curve),
        "initial_linear_velocity_m_s": lane.initial_linear_velocity_m_s.tolist(),
        "initial_angular_velocity_rad_s": lane.initial_angular_velocity_rad_s.tolist(),
        "mabd_solver_name": mabd_rollout.solver_name,
        "rbd_solver_name": rbd_rollout.solver_name,
        "mabd_total_wall_time_ms": mabd_rollout.total_wall_time_ms,
        "rbd_total_wall_time_ms": rbd_rollout.total_wall_time_ms,
        "mabd_initial_energy_j": mabd_rollout.initial_energy_j,
        "mabd_final_energy_j": mabd_rollout.final_energy_j,
        "mabd_energy_drift_j": mabd_rollout.energy_drift_j,
        "rbd_initial_energy_j": rbd_rollout.initial_energy_j,
        "rbd_final_energy_j": rbd_rollout.final_energy_j,
        "rbd_energy_drift_j": rbd_rollout.energy_drift_j,
        "comparison_metrics": comparison_metrics,
        "trajectory_samples": {
            "mabd": list(mabd_rollout.trajectory_samples),
            "rbd": list(rbd_rollout.trajectory_samples),
        },
        "energy_curve_samples": energy_curve,
        "blocking_reasons": [
            "development_comparison_only",
            "paper_faithful_gate_not_evaluated",
        ],
    }
    report = ClaimReport(
        claim_id=config.claim_id,
        scene_id=config.scene_id,
        asset_hashes={"primitive_cube": "not_applicable_procedural"},
        solver_mode="spinning_box_newton_mabd_rbd_development_comparison",
        backend="cpu_newton_warp",
        baseline_lane="spinning_box_development_comparison",
        expected={
            "comparison_scope": "development_only",
            "paper_faithful": False,
            "full_experiment_claim_passed": False,
            "duration_s": lane.duration_s,
            "time_step_s": lane.time_step_s,
            "sample_count": lane.sample_count,
        },
        observed=observed,
        threshold={},
        unit="json_report",
        status=EvidenceStatus.INCOMPLETE,
        failure_reason=(
            "development comparison only; uses reasonable local defaults and does "
            "not claim paper-faithful spinning-box reproduction"
        ),
        timing_distribution={
            "scope": "local_cpu_wall_clock_not_paper_comparable",
            "paper_comparable": False,
            "mabd_total_wall_time_ms": mabd_rollout.total_wall_time_ms,
            "rbd_total_wall_time_ms": rbd_rollout.total_wall_time_ms,
        },
        raw_outputs={
            "trajectory": "embedded_compact_samples",
            "energy_curve": "embedded_energy_curve_samples",
        },
        plot_paths={},
        source_commit=source_commit,
        vendored_newton_commit=vendored_newton_commit,
        paper_source_version=paper_source_version,
    )
    write_claim_report(report, path)
    return report


__all__ = [
    "SpinningBoxDevelopmentRollout",
    "run_spinning_box_rbd_development_rollout",
    "run_spinning_box_solver_mabd_development_rollout",
    "write_spinning_box_development_comparison_report",
]
