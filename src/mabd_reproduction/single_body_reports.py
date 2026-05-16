"""Development report lanes for single-body M-ABD experiments."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from newton.solvers import mabd

from .reporting import ClaimReport, EvidenceStatus, write_claim_report


def _oracle_body() -> mabd.MABDCPUOracleBody:
    return mabd.MABDCPUOracleBody(
        precompute=mabd.SingleBodyABDPrecompute(
            rest_points=np.zeros((4, 3), dtype=float),
            masses=np.ones(4, dtype=float),
            mass_matrix=np.eye(12),
            stiffness_matrix=np.zeros((12, 12), dtype=float),
        )
    )


def _kinetic_energy(qd: np.ndarray) -> float:
    return float(0.5 * qd @ qd)


def write_spinning_box_development_report(
    path: str | Path,
    *,
    source_commit: str,
    vendored_newton_commit: str,
    paper_source_version: str = "2603.08079v2",
) -> ClaimReport:
    dt = 0.01
    step_count = 4
    q = mabd.pack_q(np.eye(3), np.zeros(3))
    qd = np.linspace(-0.2, 0.25, 12)
    initial_momentum = qd.copy()
    initial_energy = _kinetic_energy(qd)
    config = mabd.MABDCPUOracleConfig(bodies=[_oracle_body()])
    for _step in range(step_count):
        result = mabd.solve_cpu_oracle_step(q=[q], qd=[qd], dt=dt, config=config)
        q = result.q[0]
        qd = result.qd[0]
    energy_drift = abs(_kinetic_energy(qd) - initial_energy)
    momentum_delta = float(np.linalg.norm(qd - initial_momentum))
    report = ClaimReport(
        claim_id="experiment.single_body.spinning_box",
        scene_id="single_body_spinning_box",
        asset_hashes={"primitive_cube": "not_applicable_procedural"},
        solver_mode="mabd_cpu_oracle_development",
        backend="cpu_numpy",
        baseline_lane="mabd_newton",
        expected={"paper_claim_status": "requires comparative baseline lanes before pass"},
        observed={
            "step_count": step_count,
            "time_step_s": dt,
            "energy_drift": energy_drift,
            "generalized_momentum_delta_norm": momentum_delta,
        },
        threshold={"energy_drift": 1.0e-12, "generalized_momentum_delta_norm": 1.0e-12},
        unit="json_report",
        status=EvidenceStatus.INCOMPLETE,
        failure_reason="full paper claim still requires rbd_implicit_baseline",
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
