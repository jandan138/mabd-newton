"""Development report lanes for single-body M-ABD experiments."""

from __future__ import annotations

from math import isfinite
from pathlib import Path

import numpy as np
from newton.solvers import mabd

from .experiment_configs import SpinningBoxRunConfig
from .reporting import ClaimReport, EvidenceStatus, write_claim_report
from .spinning_box_physics import (
    abd_generalized_velocity_from_paper_momenta,
    mabd_momentum_diagnostics,
    spinning_box_affine_shape_diagnostics,
    spinning_box_contact_diagnostics,
    spinning_box_kinematic_feasibility,
    spinning_box_mabd_mass_diagonal,
    spinning_box_mabd_material_properties,
    spinning_box_mabd_material_stiffness,
    spinning_box_physical_properties,
)


def _oracle_body(config: SpinningBoxRunConfig | None = None) -> mabd.MABDCPUOracleBody:
    mass_matrix = np.eye(12)
    stiffness_matrix = np.zeros((12, 12), dtype=float)
    rest_q = None
    rotation_mode = "none"
    if config is not None:
        mass_matrix = np.diag(config.mass_diagonal)
        stiffness_matrix = spinning_box_mabd_material_stiffness(config)
        rest_q = mabd.pack_q(np.eye(3), config.initial_q[9:12])
        rotation_mode = "polar"
    return mabd.MABDCPUOracleBody(
        precompute=mabd.SingleBodyABDPrecompute(
            rest_points=np.zeros((4, 3), dtype=float),
            masses=np.ones(4, dtype=float),
            mass_matrix=mass_matrix,
            stiffness_matrix=stiffness_matrix,
        ),
        rest_q=rest_q,
        rotation_mode=rotation_mode,
    )


def _kinetic_energy(qd: np.ndarray, mass_matrix: np.ndarray) -> float:
    return float(0.5 * qd @ mass_matrix @ qd)


def _mabd_trajectory_sample(
    *,
    config: SpinningBoxRunConfig,
    q: np.ndarray,
    qd: np.ndarray,
    mass_matrix: np.ndarray,
    step_index: int,
) -> dict[str, object]:
    shape = spinning_box_affine_shape_diagnostics(q)
    momentum = mabd_momentum_diagnostics(config, q, qd)
    return {
        "step_index": int(step_index),
        "time_s": float(step_index * config.time_step_s),
        "position_m": q[9:12].tolist(),
        "energy_j": _kinetic_energy(qd, mass_matrix),
        "linear_momentum_error": momentum.linear_momentum_error,
        "angular_momentum_error": momentum.angular_momentum_error,
        "affine_matrix": shape.affine_matrix.tolist(),
        "affine_determinant": shape.determinant,
        "affine_singular_values": shape.singular_values.tolist(),
        "affine_orthogonality_error": shape.orthogonality_error,
    }


def _elastic_energy(
    *,
    config: SpinningBoxRunConfig,
    q: np.ndarray,
) -> float:
    material = spinning_box_mabd_material_properties(config)
    A, _t = mabd.unpack_q(q)
    return float(
        mabd.co_rotated_linear_elastic_energy(
            A,
            material.young_modulus_pa,
            material.poisson_ratio,
            material.volume_m3,
        )
    )


def _relative_drift(value: float, initial_value: float) -> float:
    return 0.0 if initial_value == 0.0 else abs(value - initial_value) / abs(initial_value)


def _paper_horizon_sample_indices(step_count: int, sample_count: int) -> set[int]:
    if sample_count >= step_count + 1:
        return set(range(step_count + 1))
    return {int(round(value)) for value in np.linspace(0, step_count, sample_count)}


def _paper_horizon_state_metrics(
    *,
    config: SpinningBoxRunConfig,
    q: np.ndarray,
    qd: np.ndarray,
    mass_matrix: np.ndarray,
    step_index: int,
    time_step_s: float,
    residual_norm: float,
    initial_kinetic_energy: float,
    initial_total_energy: float,
) -> dict[str, object]:
    shape = spinning_box_affine_shape_diagnostics(q)
    momentum = mabd_momentum_diagnostics(config, q, qd)
    contact = spinning_box_contact_diagnostics(config, q, qd)
    kinetic_energy = _kinetic_energy(qd, mass_matrix)
    elastic_energy = _elastic_energy(config=config, q=q)
    total_energy = kinetic_energy + elastic_energy
    return {
        "step_index": int(step_index),
        "time_s": float(step_index * time_step_s),
        "position_m": q[9:12].tolist(),
        "linear_momentum_error": momentum.linear_momentum_error,
        "angular_momentum_error": momentum.angular_momentum_error,
        "kinetic_energy_j": kinetic_energy,
        "elastic_energy_j": elastic_energy,
        "total_energy_j": total_energy,
        "relative_kinetic_energy_drift": _relative_drift(
            kinetic_energy,
            initial_kinetic_energy,
        ),
        "relative_total_energy_drift": _relative_drift(
            total_energy,
            initial_total_energy,
        ),
        "affine_determinant": shape.determinant,
        "affine_abs_det_minus_one": abs(shape.determinant - 1.0),
        "affine_singular_values": shape.singular_values.tolist(),
        "affine_min_singular_value": float(np.min(shape.singular_values)),
        "affine_max_singular_value": float(np.max(shape.singular_values)),
        "affine_orthogonality_error": shape.orthogonality_error,
        "contact_diagnostic_policy": "evaluated_from_current_mabd_states_not_applied_to_step",
        "contact_active_count": contact.active_contact_count,
        "contact_min_signed_distance_m": contact.min_signed_distance,
        "contact_max_penetration_m": contact.max_penetration_depth,
        "contact_normal_force_norm_n": float(np.linalg.norm(contact.total_normal_force)),
        "contact_generalized_force_norm": float(np.linalg.norm(contact.total_generalized_force)),
        "residual_norm": float(residual_norm),
    }


def _finite_metric_value(value: object) -> bool:
    if isinstance(value, bool) or not isinstance(value, int | float):
        return False
    return isfinite(float(value))


def _all_state_values_finite(q: np.ndarray, qd: np.ndarray, metrics: dict[str, object]) -> bool:
    finite_scalars = (
        "linear_momentum_error",
        "angular_momentum_error",
        "kinetic_energy_j",
        "elastic_energy_j",
        "total_energy_j",
        "relative_kinetic_energy_drift",
        "relative_total_energy_drift",
        "affine_determinant",
        "affine_abs_det_minus_one",
        "affine_min_singular_value",
        "affine_max_singular_value",
        "affine_orthogonality_error",
        "contact_min_signed_distance_m",
        "contact_max_penetration_m",
        "contact_normal_force_norm_n",
        "contact_generalized_force_norm",
        "residual_norm",
    )
    return (
        np.all(np.isfinite(q))
        and np.all(np.isfinite(qd))
        and all(_finite_metric_value(metrics[key]) for key in finite_scalars)
    )


def _threshold_violations(
    summary: dict[str, object],
    thresholds: dict[str, float],
) -> list[str]:
    violations: list[str] = []
    for key, threshold in thresholds.items():
        value = summary[key]
        if not _finite_metric_value(value):
            violations.append(key)
            continue
        value_float = float(value)
        if key == "min_singular_value":
            if value_float < threshold:
                violations.append(key)
        elif value_float > threshold:
            violations.append(key)
    if summary["first_nonfinite_step"] is not None:
        violations.append("finite_state")
    return violations


def _run_spinning_box_paper_horizon_step_size(
    *,
    config: SpinningBoxRunConfig,
    time_step_s: float,
) -> dict[str, object]:
    duration = config.paper_horizon.duration_s
    feasibility = spinning_box_kinematic_feasibility(config, time_step_s)
    step_count = int(round(duration / time_step_s))
    if abs(step_count * time_step_s - duration) > 1.0e-12:
        raise ValueError("paper_horizon duration_s must be divisible by time_step_grid_s entries")

    q = config.initial_q.copy()
    qd = config.initial_qd.copy()
    mass_matrix = np.diag(config.mass_diagonal)
    initial_kinetic_energy = _kinetic_energy(qd, mass_matrix)
    initial_elastic_energy = _elastic_energy(config=config, q=q)
    initial_total_energy = initial_kinetic_energy + initial_elastic_energy
    sample_indices = _paper_horizon_sample_indices(
        step_count,
        config.paper_horizon.sample_count,
    )
    samples: list[dict[str, object]] = []
    extrema: dict[str, tuple[float, int]] = {
        "max_linear_momentum_error": (-np.inf, 0),
        "max_angular_momentum_error": (-np.inf, 0),
        "max_kinetic_energy_drift_j": (-np.inf, 0),
        "max_total_energy_drift_j": (-np.inf, 0),
        "max_relative_kinetic_energy_drift": (-np.inf, 0),
        "max_relative_total_energy_drift": (-np.inf, 0),
        "max_abs_det_minus_one": (-np.inf, 0),
        "min_singular_value": (np.inf, 0),
        "max_singular_value": (-np.inf, 0),
        "max_affine_orthogonality_error": (-np.inf, 0),
        "max_contact_active_count": (-np.inf, 0),
        "min_contact_signed_distance_m": (np.inf, 0),
        "max_contact_penetration_m": (-np.inf, 0),
        "max_contact_normal_force_n": (-np.inf, 0),
        "max_contact_generalized_force_norm": (-np.inf, 0),
        "max_residual_norm": (-np.inf, 0),
    }

    def update(metrics: dict[str, object]) -> None:
        step_index = int(metrics["step_index"])
        candidates = {
            "max_linear_momentum_error": float(metrics["linear_momentum_error"]),
            "max_angular_momentum_error": float(metrics["angular_momentum_error"]),
            "max_kinetic_energy_drift_j": abs(
                float(metrics["kinetic_energy_j"]) - initial_kinetic_energy
            ),
            "max_total_energy_drift_j": abs(
                float(metrics["total_energy_j"]) - initial_total_energy
            ),
            "max_relative_kinetic_energy_drift": float(
                metrics["relative_kinetic_energy_drift"]
            ),
            "max_relative_total_energy_drift": float(
                metrics["relative_total_energy_drift"]
            ),
            "max_abs_det_minus_one": float(metrics["affine_abs_det_minus_one"]),
            "min_singular_value": float(metrics["affine_min_singular_value"]),
            "max_singular_value": float(metrics["affine_max_singular_value"]),
            "max_affine_orthogonality_error": float(
                metrics["affine_orthogonality_error"]
            ),
            "max_contact_active_count": float(metrics["contact_active_count"]),
            "min_contact_signed_distance_m": float(metrics["contact_min_signed_distance_m"]),
            "max_contact_penetration_m": float(metrics["contact_max_penetration_m"]),
            "max_contact_normal_force_n": float(metrics["contact_normal_force_norm_n"]),
            "max_contact_generalized_force_norm": float(
                metrics["contact_generalized_force_norm"]
            ),
            "max_residual_norm": float(metrics["residual_norm"]),
        }
        for key, value in candidates.items():
            current, _current_step = extrema[key]
            if key in {"min_singular_value", "min_contact_signed_distance_m"}:
                if value < current:
                    extrema[key] = (value, step_index)
            elif value > current:
                extrema[key] = (value, step_index)

    metrics = _paper_horizon_state_metrics(
        config=config,
        q=q,
        qd=qd,
        mass_matrix=mass_matrix,
        step_index=0,
        time_step_s=time_step_s,
        residual_norm=0.0,
        initial_kinetic_energy=initial_kinetic_energy,
        initial_total_energy=initial_total_energy,
    )
    update(metrics)
    if 0 in sample_indices:
        samples.append(metrics)

    oracle_body = _oracle_body(config)
    oracle_config = mabd.MABDCPUOracleConfig(bodies=[oracle_body])
    first_nonfinite_step: int | None = None
    steps_completed = 0
    for step_index in range(1, step_count + 1):
        result = mabd.solve_cpu_oracle_step(q=[q], qd=[qd], dt=time_step_s, config=oracle_config)
        q = result.q[0]
        qd = result.qd[0]
        metrics = _paper_horizon_state_metrics(
            config=config,
            q=q,
            qd=qd,
            mass_matrix=mass_matrix,
            step_index=step_index,
            time_step_s=time_step_s,
            residual_norm=result.residual_norm,
            initial_kinetic_energy=initial_kinetic_energy,
            initial_total_energy=initial_total_energy,
        )
        if not _all_state_values_finite(q, qd, metrics):
            first_nonfinite_step = step_index
            break
        update(metrics)
        steps_completed = step_index
        if step_index in sample_indices:
            samples.append(metrics)

    summary: dict[str, object] = {
        "time_step_s": float(time_step_s),
        "duration_s": duration,
        "steps_attempted": step_count,
        "steps_completed": steps_completed,
        "first_nonfinite_step": first_nonfinite_step,
        "initial_position_m": config.initial_q[9:12].tolist(),
        "final_position_m": q[9:12].tolist(),
        "kinetic_energy_initial_j": initial_kinetic_energy,
        "elastic_energy_initial_j": initial_elastic_energy,
        "total_energy_initial_j": initial_total_energy,
        "kinetic_energy_final_j": _kinetic_energy(qd, mass_matrix),
        "elastic_energy_final_j": _elastic_energy(config=config, q=q),
        "kinematic_feasibility": feasibility.to_report(),
        "trajectory_samples": samples,
    }
    for key, (value, step_index) in extrema.items():
        summary[key] = int(value) if key == "max_contact_active_count" else value
        summary[f"{key}_step_index"] = step_index
    summary["contact_diagnostic_policy"] = "evaluated_from_current_mabd_states_not_applied_to_step"
    summary["contact_diagnostic_status"] = (
        "contact_penetration_observed_without_response"
        if summary["max_contact_active_count"] > 0
        else "no_contact_penetration_observed"
    )
    summary["threshold_violations"] = _threshold_violations(
        summary,
        config.paper_horizon.thresholds,
    )
    summary["diagnostic_status"] = (
        "development_gap_observed"
        if summary["threshold_violations"]
        else "thresholds_met_no_lane_gate"
    )
    return summary


def write_spinning_box_development_report(
    path: str | Path,
    *,
    source_commit: str,
    vendored_newton_commit: str,
    paper_source_version: str = "2603.08079v2",
    config: SpinningBoxRunConfig | None = None,
) -> ClaimReport:
    dt = 0.01 if config is None else config.time_step_s
    step_count = 4 if config is None else config.step_count
    q = mabd.pack_q(np.eye(3), np.zeros(3)) if config is None else config.initial_q.copy()
    qd = np.linspace(-0.2, 0.25, 12) if config is None else config.initial_qd.copy()
    mass_matrix = np.eye(12) if config is None else np.diag(config.mass_diagonal)
    if config is not None:
        expected_qd = abd_generalized_velocity_from_paper_momenta(config)
        if not np.allclose(qd, expected_qd, rtol=0.0, atol=1.0e-9):
            raise ValueError("single_body_spinning_box initial_qd must map paper p0/L0 to ABD velocity")
        expected_mass_diagonal = spinning_box_mabd_mass_diagonal(config)
        if not np.allclose(config.mass_diagonal, expected_mass_diagonal, rtol=0.0, atol=1.0e-15):
            raise ValueError("single_body_spinning_box mass_diagonal must match paper cube ABD mass")
    initial_q = q.copy()
    initial_momentum = qd.copy()
    initial_energy = _kinetic_energy(qd, mass_matrix)
    initial_diagnostics = mabd_momentum_diagnostics(config, q, qd) if config is not None else None
    contact_diagnostics = spinning_box_contact_diagnostics(config, q, qd) if config is not None else None
    trajectory_samples: list[dict[str, object]] = []
    if config is not None:
        trajectory_samples.append(
            _mabd_trajectory_sample(
                config=config,
                q=q,
                qd=qd,
                mass_matrix=mass_matrix,
                step_index=0,
            )
        )
    oracle_body = _oracle_body(config)
    oracle_config = mabd.MABDCPUOracleConfig(bodies=[oracle_body])
    for step_index in range(1, step_count + 1):
        result = mabd.solve_cpu_oracle_step(q=[q], qd=[qd], dt=dt, config=oracle_config)
        q = result.q[0]
        qd = result.qd[0]
        if config is not None:
            trajectory_samples.append(
                _mabd_trajectory_sample(
                    config=config,
                    q=q,
                    qd=qd,
                    mass_matrix=mass_matrix,
                    step_index=step_index,
                )
            )
    final_energy = _kinetic_energy(qd, mass_matrix)
    energy_drift = abs(final_energy - initial_energy)
    momentum_delta = float(np.linalg.norm(qd - initial_momentum))
    final_diagnostics = mabd_momentum_diagnostics(config, q, qd) if config is not None else None
    thresholds = (
        {"energy_drift": 1.0e-12, "generalized_momentum_delta_norm": 1.0e-12}
        if config is None
        else config.thresholds
    )
    observed = {
        "step_count": step_count,
        "time_step_s": dt,
        "energy_drift": energy_drift,
        "generalized_momentum_delta_norm": momentum_delta,
    }
    if initial_diagnostics is not None and final_diagnostics is not None:
        properties = spinning_box_physical_properties(config)
        material = spinning_box_mabd_material_properties(config)
        material_stiffness = oracle_body.precompute.stiffness_matrix
        initial_shape = trajectory_samples[0]
        final_shape = trajectory_samples[-1]
        observed.update(
            {
                "mass_kg": properties.mass_kg,
                "mabd_mass_diagonal": mass_matrix.diagonal().tolist(),
                "mass_diagonal_source": "paper_uniform_centered_cube_continuous",
                "initial_energy_j": initial_energy,
                "final_energy_j": final_energy,
                "relative_energy_drift": 0.0
                if initial_energy == 0.0
                else energy_drift / abs(initial_energy),
                "paper_spatial_twist": initial_diagnostics.spatial_twist.tolist(),
                "final_spatial_twist": final_diagnostics.spatial_twist.tolist(),
                "final_linear_momentum_kg_m_s": final_diagnostics.linear_momentum_kg_m_s.tolist(),
                "final_angular_momentum_kg_m2_s": final_diagnostics.angular_momentum_kg_m2_s.tolist(),
                "linear_momentum_error": final_diagnostics.linear_momentum_error,
                "angular_momentum_error": final_diagnostics.angular_momentum_error,
                "initial_position_m": initial_q[9:12].tolist(),
                "final_position_m": q[9:12].tolist(),
                "trajectory_samples": trajectory_samples,
                "initial_affine_orthogonality_error": initial_shape[
                    "affine_orthogonality_error"
                ],
                "final_affine_orthogonality_error": final_shape[
                    "affine_orthogonality_error"
                ],
                "final_affine_determinant": final_shape["affine_determinant"],
                "final_affine_singular_values": final_shape["affine_singular_values"],
                "affine_shape_diagnostic_status": "development_gap_observed",
                "mabd_rotation_mode": oracle_body.rotation_mode,
                "material_model": "paper_linear_elastic_corotated_development",
                "material_rhs_frame": "corotated_local_all_blocks",
                "translation_frame": "corotated_polar_all_blocks",
                "material_young_modulus_pa": material.young_modulus_pa,
                "material_poisson_ratio": material.poisson_ratio,
                "material_volume_m3": material.volume_m3,
                "material_stiffness_trace": float(np.trace(material_stiffness)),
                "material_stiffness_rank": int(np.linalg.matrix_rank(material_stiffness)),
            }
        )
    if contact_diagnostics is not None and config is not None:
        observed.update(
            {
                "contact_evaluation_state": "initial_configured_q_qd",
                "contact_surface_type": config.contact_surface["type"],
                "contact_corner_count": contact_diagnostics.corner_count,
                "contact_active_count": contact_diagnostics.active_contact_count,
                "contact_min_signed_distance_m": contact_diagnostics.min_signed_distance,
                "contact_max_penetration_m": contact_diagnostics.max_penetration_depth,
                "contact_total_normal_force_n": contact_diagnostics.total_normal_force.tolist(),
                "contact_total_generalized_force": contact_diagnostics.total_generalized_force.tolist(),
                "contact_corner_signed_distances_m": (
                    contact_diagnostics.corner_signed_distances.tolist()
                ),
            }
        )
    report = ClaimReport(
        claim_id="experiment.single_body.spinning_box",
        scene_id="single_body_spinning_box" if config is None else config.scene_id,
        asset_hashes={"primitive_cube": "not_applicable_procedural"},
        solver_mode="mabd_cpu_oracle_development",
        backend="cpu_numpy",
        baseline_lane="mabd_newton" if config is None else config.baseline_lane,
        expected={"paper_claim_status": "requires comparative baseline lanes before pass"},
        observed=observed,
        threshold=thresholds,
        unit="json_report",
        status=EvidenceStatus.INCOMPLETE if config is None else config.report_status,
        failure_reason="full paper claim still requires rbd_implicit_baseline"
        if config is None
        else config.failure_reason,
        timing_distribution={"step_count": step_count, "scope": "not_timed"},
        raw_outputs={"time_series": "not_written"},
        plot_paths={},
        source_commit=source_commit,
        vendored_newton_commit=vendored_newton_commit,
        paper_source_version=paper_source_version,
    )
    write_claim_report(report, path)
    return report


def write_spinning_box_paper_horizon_report(
    path: str | Path,
    *,
    config: SpinningBoxRunConfig,
    source_commit: str,
    vendored_newton_commit: str,
    paper_source_version: str = "2603.08079v2",
) -> ClaimReport:
    expected_mass_diagonal = spinning_box_mabd_mass_diagonal(config)
    if not np.allclose(config.mass_diagonal, expected_mass_diagonal, rtol=0.0, atol=1.0e-15):
        raise ValueError("single_body_spinning_box mass_diagonal must match paper cube ABD mass")
    results = [
        _run_spinning_box_paper_horizon_step_size(
            config=config,
            time_step_s=time_step_s,
        )
        for time_step_s in config.paper_horizon.time_step_grid_s
    ]
    all_violations = sorted(
        {
            violation
            for result in results
            for violation in result["threshold_violations"]
        }
    )
    diagnostic_status = (
        "development_gap_observed"
        if all_violations
        else "thresholds_met_no_lane_gate"
    )
    feasibility_statuses = sorted(
        {
            str(result["kinematic_feasibility"]["status"])
            for result in results
        }
    )
    feasibility_blockers = (
        ["mabd_kinematic_feasibility_blocker_recorded"]
        if "paper_momentum_requires_affine_stretch_under_q_delta_over_h"
        in feasibility_statuses
        else []
    )
    top_linear_momentum_error = max(
        float(result["max_linear_momentum_error"]) for result in results
    )
    top_angular_momentum_error = max(
        float(result["max_angular_momentum_error"]) for result in results
    )
    top_total_energy_drift = max(
        float(result["max_total_energy_drift_j"]) for result in results
    )
    top_contact_active_count = max(int(result["max_contact_active_count"]) for result in results)
    top_contact_penetration = max(float(result["max_contact_penetration_m"]) for result in results)
    top_contact_normal_force = max(float(result["max_contact_normal_force_n"]) for result in results)
    top_contact_generalized_force = max(
        float(result["max_contact_generalized_force_norm"]) for result in results
    )
    contact_diagnostic_status = (
        "contact_penetration_observed_without_response"
        if top_contact_active_count > 0
        else "no_contact_penetration_observed"
    )
    contact_blockers = (
        ["spinning_box_contact_response_missing"]
        if contact_diagnostic_status == "contact_penetration_observed_without_response"
        else []
    )
    observed = {
        "paper_horizon_duration_s": config.paper_horizon.duration_s,
        "paper_step_sizes_s": list(config.paper_horizon.time_step_grid_s),
        "paper_source_lines": list(config.source_lines),
        "figure_text_source": config.paper_horizon.figure_text_source,
        "figure_pdf_sha256": config.paper_horizon.figure_pdf_sha256,
        "mabd_paper_horizon_status": diagnostic_status,
        "mabd_kinematic_feasibility_status": (
            feasibility_statuses[0]
            if len(feasibility_statuses) == 1
            else "mixed_kinematic_feasibility_statuses"
        ),
        "mabd_kinematic_feasibility_statuses": feasibility_statuses,
        "threshold_violations": all_violations,
        "linear_momentum_error": top_linear_momentum_error,
        "angular_momentum_error": top_angular_momentum_error,
        "energy_drift": top_total_energy_drift,
        "contact_diagnostic_policy": "evaluated_from_current_mabd_states_not_applied_to_step",
        "contact_diagnostic_status": contact_diagnostic_status,
        "max_contact_active_count": top_contact_active_count,
        "max_contact_penetration_m": top_contact_penetration,
        "max_contact_normal_force_n": top_contact_normal_force,
        "max_contact_generalized_force_norm": top_contact_generalized_force,
        "initial_position_m": config.initial_q[9:12].tolist(),
        "final_position_m": results[0]["final_position_m"],
        "paper_horizon_results": results,
    }
    blockers = ["mabd_newton_report_incomplete", *feasibility_blockers, *contact_blockers]
    if all_violations:
        blockers.insert(1, "mabd_paper_horizon_diagnostic_thresholds_violated")
    observed["blocking_reasons"] = blockers
    report = ClaimReport(
        claim_id=config.claim_id,
        scene_id=config.scene_id,
        asset_hashes={"primitive_cube": "not_applicable_procedural"},
        solver_mode="mabd_cpu_oracle_paper_horizon_diagnostic",
        backend="cpu_numpy",
        baseline_lane=config.baseline_lane,
        expected={
            "paper_claim_status": "mabd paper-horizon diagnostics must pass before lane gate",
            "paper_horizon_duration_s": config.paper_horizon.duration_s,
            "paper_step_sizes_s": list(config.paper_horizon.time_step_grid_s),
            "source_lines": list(config.source_lines),
            "figure_text_source": config.paper_horizon.figure_text_source,
            "figure_pdf_sha256": config.paper_horizon.figure_pdf_sha256,
            "phase28_mabd_gate_policy": "diagnostic_only_no_lane_gate",
        },
        observed=observed,
        threshold=config.paper_horizon.thresholds,
        unit="json_report",
        status=EvidenceStatus.INCOMPLETE,
        failure_reason="M-ABD paper-horizon diagnostics remain incomplete; shape or energy thresholds are violated",
        timing_distribution={
            "scope": "not_timed",
            "step_sizes_s": list(config.paper_horizon.time_step_grid_s),
        },
        raw_outputs={"time_series": "compact_samples_only"},
        plot_paths={},
        source_commit=source_commit,
        vendored_newton_commit=vendored_newton_commit,
        paper_source_version=paper_source_version,
    )
    write_claim_report(report, path)
    return report


__all__ = [
    "write_spinning_box_development_report",
    "write_spinning_box_paper_horizon_report",
]
