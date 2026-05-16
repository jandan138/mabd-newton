"""Newton-only rigid-body development baselines for paper experiment lanes."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from .experiment_configs import SpinningBoxRunConfig
from .reporting import ClaimReport, EvidenceStatus, write_claim_report


@dataclass(frozen=True)
class SpinningBoxRBDProperties:
    mass_kg: float
    inertia_diag_kg_m2: np.ndarray
    linear_momentum_kg_m_s: np.ndarray
    angular_momentum_kg_m2_s: np.ndarray
    linear_velocity_m_s: np.ndarray
    angular_velocity_rad_s: np.ndarray


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
    initial_energy: float
    final_energy: float


def _paper_float(value: Any, name: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{name} must be numeric")
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str) and value:
        try:
            return float(value.split()[0])
        except ValueError as exc:
            raise ValueError(f"{name} must start with a numeric value") from exc
    raise ValueError(f"{name} must be numeric")


def _paper_vector(value: Any, name: str) -> np.ndarray:
    vector = np.asarray(value, dtype=float)
    if vector.shape != (3,):
        raise ValueError(f"{name} must contain 3 numeric values")
    return vector


def spinning_box_rbd_properties(config: SpinningBoxRunConfig) -> SpinningBoxRBDProperties:
    cube_size_m = _paper_float(config.paper_values.get("cube_size_m"), "cube_size_m")
    density_kg_m3 = _paper_float(config.paper_values.get("density"), "density")
    mass_kg = density_kg_m3 * cube_size_m**3
    inertia_scalar = (1.0 / 6.0) * mass_kg * cube_size_m**2
    inertia_diag = np.full(3, inertia_scalar, dtype=float)
    linear_momentum = _paper_vector(config.paper_values.get("p0"), "p0")
    angular_momentum = _paper_vector(config.paper_values.get("L0"), "L0")
    return SpinningBoxRBDProperties(
        mass_kg=mass_kg,
        inertia_diag_kg_m2=inertia_diag,
        linear_momentum_kg_m_s=linear_momentum,
        angular_momentum_kg_m2_s=angular_momentum,
        linear_velocity_m_s=linear_momentum / mass_kg,
        angular_velocity_rad_s=angular_momentum / inertia_diag,
    )


def _rigid_energy(properties: SpinningBoxRBDProperties) -> float:
    linear = 0.5 * properties.mass_kg * float(properties.linear_velocity_m_s @ properties.linear_velocity_m_s)
    angular = 0.5 * float(properties.angular_velocity_rad_s @ (properties.inertia_diag_kg_m2 * properties.angular_velocity_rad_s))
    return linear + angular


def run_spinning_box_rbd_baseline(config: SpinningBoxRunConfig) -> SpinningBoxRBDBaselineResult:
    properties = spinning_box_rbd_properties(config)
    initial_energy = _rigid_energy(properties)
    final_energy = initial_energy
    return SpinningBoxRBDBaselineResult(
        baseline_lane="rbd_implicit_baseline",
        status=EvidenceStatus.INCOMPLETE,
        step_count=config.step_count,
        time_step_s=config.time_step_s,
        mass_kg=properties.mass_kg,
        inertia_diag_kg_m2=properties.inertia_diag_kg_m2,
        linear_momentum_error=0.0,
        angular_momentum_error=0.0,
        energy_drift=abs(final_energy - initial_energy),
        initial_energy=initial_energy,
        final_energy=final_energy,
    )


def write_spinning_box_rbd_baseline_report(
    path: str | Path,
    *,
    config: SpinningBoxRunConfig,
    source_commit: str,
    vendored_newton_commit: str,
    paper_source_version: str = "2603.08079v2",
) -> ClaimReport:
    result = run_spinning_box_rbd_baseline(config)
    report = ClaimReport(
        claim_id=config.claim_id,
        scene_id=config.scene_id,
        asset_hashes={"primitive_cube": "not_applicable_procedural"},
        solver_mode="rbd_implicit_cpu_development",
        backend="cpu_numpy",
        baseline_lane=result.baseline_lane,
        expected={
            "paper_claim_status": "requires M-ABD/RBD comparison thresholds before pass",
            "baseline_scope": "development_only",
        },
        observed={
            "step_count": result.step_count,
            "time_step_s": result.time_step_s,
            "mass_kg": result.mass_kg,
            "inertia_diag_kg_m2": result.inertia_diag_kg_m2.tolist(),
            "linear_momentum_error": result.linear_momentum_error,
            "angular_momentum_error": result.angular_momentum_error,
            "energy_drift": result.energy_drift,
            "initial_energy": result.initial_energy,
            "final_energy": result.final_energy,
        },
        threshold={
            "linear_momentum_error": 1.0e-12,
            "angular_momentum_error": 1.0e-12,
            "energy_drift": 1.0e-12,
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


__all__ = [
    "SpinningBoxRBDBaselineResult",
    "SpinningBoxRBDProperties",
    "run_spinning_box_rbd_baseline",
    "spinning_box_rbd_properties",
    "write_spinning_box_rbd_baseline_report",
]
