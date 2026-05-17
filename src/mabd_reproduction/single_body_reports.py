"""Development report lanes for single-body M-ABD experiments."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from newton.solvers import mabd

from .experiment_configs import SpinningBoxRunConfig
from .reporting import ClaimReport, EvidenceStatus, write_claim_report
from .spinning_box_physics import (
    abd_generalized_velocity_from_paper_momenta,
    mabd_momentum_diagnostics,
    spinning_box_contact_diagnostics,
    spinning_box_mabd_mass_diagonal,
    spinning_box_physical_properties,
)


def _oracle_body(config: SpinningBoxRunConfig | None = None) -> mabd.MABDCPUOracleBody:
    mass_matrix = np.eye(12)
    if config is not None:
        mass_matrix = np.diag(config.mass_diagonal)
    return mabd.MABDCPUOracleBody(
        precompute=mabd.SingleBodyABDPrecompute(
            rest_points=np.zeros((4, 3), dtype=float),
            masses=np.ones(4, dtype=float),
            mass_matrix=mass_matrix,
            stiffness_matrix=np.zeros((12, 12), dtype=float),
        )
    )


def _kinetic_energy(qd: np.ndarray, mass_matrix: np.ndarray) -> float:
    return float(0.5 * qd @ mass_matrix @ qd)


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
    initial_momentum = qd.copy()
    initial_energy = _kinetic_energy(qd, mass_matrix)
    initial_diagnostics = mabd_momentum_diagnostics(config, q, qd) if config is not None else None
    contact_diagnostics = spinning_box_contact_diagnostics(config, q, qd) if config is not None else None
    oracle_config = mabd.MABDCPUOracleConfig(bodies=[_oracle_body(config)])
    for _step in range(step_count):
        result = mabd.solve_cpu_oracle_step(q=[q], qd=[qd], dt=dt, config=oracle_config)
        q = result.q[0]
        qd = result.qd[0]
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


__all__ = ["write_spinning_box_development_report"]
