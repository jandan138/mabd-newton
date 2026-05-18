"""Multi-lane comparison reports for paper experiment claims."""

from __future__ import annotations

import hashlib
from math import isfinite, sqrt
from pathlib import Path
from typing import Any

from .experiment_configs import (
    HeavyTopRunConfig,
    PhysicalPendulumRunConfig,
    SpinningBoxRunConfig,
    THandleRunConfig,
)
from .physical_pendulum_reports import physical_pendulum_timing_source_audit
from .reporting import ClaimReport, EvidenceStatus, load_claim_report, write_claim_report


SPINNING_BOX_REQUIRED_METRICS = (
    "linear_momentum_error",
    "angular_momentum_error",
    "energy_drift",
)
SPINNING_BOX_REQUIRED_VECTOR_METRICS = (
    "initial_position_m",
    "final_position_m",
)
PHYSICAL_PENDULUM_REQUIRED_METRICS = (
    "pendulum_angle_error",
    "joint_force_error",
    "phase_drift",
)
HEAVY_TOP_REQUIRED_METRICS = (
    "precession_velocity_error",
    "nutation_angle_error",
    "energy_drift",
)
T_HANDLE_REQUIRED_METRICS = (
    "flip_timing_error",
    "intermediate_axis_angular_velocity_waveform",
    "energy_loss",
)
PHYSICAL_PENDULUM_INPUT_LANES = {
    "analytic_reference": {
        "solver_mode": "analytic_elliptic_reference",
        "backend": "cpu_scipy_reference",
    },
    "mabd_newton": {
        "solver_mode": "mabd_cpu_oracle_physical_pendulum_newton_lane",
        "backend": "cpu_numpy_newton_only",
    },
    "rbd_implicit_baseline": {
        "solver_mode": "physical_pendulum_scalar_implicit_rbd_development",
        "backend": "cpu_numpy_newton_only",
    },
}
HEAVY_TOP_INPUT_LANES = {
    "rbd_rk4_reference": {
        "solver_mode": "heavy_top_rk4_reference_diagnostic",
        "backend": "cpu_numpy",
    },
    "mabd_newton": {
        "solver_mode": "mabd_cpu_oracle_heavy_top_newton_lane",
        "backend": "cpu_numpy_newton_only",
    },
}
T_HANDLE_INPUT_LANES = {
    "rbd_rk4_reference": {
        "solver_mode": "t_handle_torque_free_rk4_reference",
        "backend": "cpu_numpy",
    },
    "mabd_newton": {
        "solver_mode": "mabd_cpu_oracle_t_handle_newton_lane",
        "backend": "cpu_numpy_newton_only",
    },
}
HEAVY_TOP_FIGURE_BASELINE_LANE = "paper_figure_digitization"
HEAVY_TOP_FIGURE_SOLVER_MODE = "heavy_top_paper_figure_digitization"
HEAVY_TOP_FIGURE_BACKEND = "pdftocairo_pillow"
T_HANDLE_FIGURE_BASELINE_LANE = "paper_figure_digitization"
T_HANDLE_FIGURE_SOLVER_MODE = "t_handle_paper_figure_digitization"
T_HANDLE_FIGURE_BACKEND = "pdftocairo_pillow"


def _require_lane_report(
    path: str | Path,
    *,
    config: SpinningBoxRunConfig,
    lane: str,
) -> ClaimReport:
    report = load_claim_report(path)
    if report.claim_id != config.claim_id:
        raise ValueError(f"{lane} report claim_id must be {config.claim_id}")
    if report.scene_id != config.scene_id:
        raise ValueError(f"{lane} report scene_id must be {config.scene_id}")
    if report.baseline_lane != lane:
        raise ValueError(f"{lane} report must have baseline_lane={lane}")
    return report


def _sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _require_physical_pendulum_lane_report(
    path: str | Path,
    *,
    config: PhysicalPendulumRunConfig,
    lane: str,
) -> ClaimReport:
    report = load_claim_report(path)
    if report.claim_id != config.claim_id:
        raise ValueError(f"{lane} report claim_id must be {config.claim_id}")
    if report.scene_id != config.scene_id:
        raise ValueError(f"{lane} report scene_id must be {config.scene_id}")
    if report.baseline_lane != lane:
        raise ValueError(f"{lane} report must have baseline_lane={lane}")
    expected_identity = PHYSICAL_PENDULUM_INPUT_LANES[lane]
    expected_solver_mode = expected_identity["solver_mode"]
    if report.solver_mode != expected_solver_mode:
        raise ValueError(f"{lane} report solver_mode must be {expected_solver_mode}")
    expected_backend = expected_identity["backend"]
    if report.backend != expected_backend:
        raise ValueError(f"{lane} report backend must be {expected_backend}")
    if report.status != EvidenceStatus.INCOMPLETE:
        raise ValueError(f"{lane} report status must be incomplete")
    if report.asset_hashes.get("physical_pendulum_procedural") != "not_applicable_procedural":
        raise ValueError(f"{lane} report must use physical_pendulum_procedural")
    if report.observed.get("full_experiment_claim_passed") is not False:
        raise ValueError(f"{lane} report must not claim full experiment pass")
    return report


def _require_heavy_top_lane_report(
    path: str | Path,
    *,
    config: HeavyTopRunConfig,
    lane: str,
) -> ClaimReport:
    report = load_claim_report(path)
    if report.claim_id != config.claim_id:
        raise ValueError(f"{lane} report claim_id must be {config.claim_id}")
    if report.scene_id != config.scene_id:
        raise ValueError(f"{lane} report scene_id must be {config.scene_id}")
    if report.baseline_lane != lane:
        raise ValueError(f"{lane} report must have baseline_lane={lane}")
    expected_identity = HEAVY_TOP_INPUT_LANES[lane]
    expected_solver_mode = expected_identity["solver_mode"]
    if report.solver_mode != expected_solver_mode:
        raise ValueError(f"{lane} report solver_mode must be {expected_solver_mode}")
    expected_backend = expected_identity["backend"]
    if report.backend != expected_backend:
        raise ValueError(f"{lane} report backend must be {expected_backend}")
    if report.status != EvidenceStatus.INCOMPLETE:
        raise ValueError(f"{lane} report status must be incomplete")
    if report.asset_hashes.get("heavy_top_procedural") != "not_applicable_procedural":
        raise ValueError(f"{lane} report must use heavy_top_procedural")
    if report.observed.get("full_experiment_claim_passed") is not False:
        raise ValueError(f"{lane} report must not claim full experiment pass")
    return report


def _require_t_handle_lane_report(
    path: str | Path,
    *,
    config: THandleRunConfig,
    lane: str,
) -> ClaimReport:
    report = load_claim_report(path)
    if report.claim_id != config.claim_id:
        raise ValueError(f"{lane} report claim_id must be {config.claim_id}")
    if report.scene_id != config.scene_id:
        raise ValueError(f"{lane} report scene_id must be {config.scene_id}")
    if report.baseline_lane != lane:
        raise ValueError(f"{lane} report must have baseline_lane={lane}")
    expected_identity = T_HANDLE_INPUT_LANES[lane]
    expected_solver_mode = expected_identity["solver_mode"]
    if report.solver_mode != expected_solver_mode:
        raise ValueError(f"{lane} report solver_mode must be {expected_solver_mode}")
    expected_backend = expected_identity["backend"]
    if report.backend != expected_backend:
        raise ValueError(f"{lane} report backend must be {expected_backend}")
    if report.status != EvidenceStatus.INCOMPLETE:
        raise ValueError(f"{lane} report status must be incomplete")
    if report.asset_hashes.get("t_handle_procedural") != "not_applicable_procedural":
        raise ValueError(f"{lane} report must use t_handle_procedural")
    if report.observed.get("full_experiment_claim_passed") is not False:
        raise ValueError(f"{lane} report must not claim full experiment pass")
    if report.observed.get("reference_not_paper_geometry") is not True:
        raise ValueError(f"{lane} report reference_not_paper_geometry must be true")
    if lane == "rbd_rk4_reference":
        expected_scope = "torque_free_principal_axis_rk4_diagnostic"
        if report.observed.get("reference_scope") != expected_scope:
            raise ValueError(f"{lane} report reference_scope must be {expected_scope}")
    if lane == "mabd_newton":
        expected_scope = "t_handle_model_derived_proxy"
        if report.observed.get("mabd_diagnostic_scope") != expected_scope:
            raise ValueError(f"{lane} report mabd_diagnostic_scope must be {expected_scope}")
        expected_source = "newton_model_derived"
        if report.observed.get("solver_model_config_source") != expected_source:
            raise ValueError(
                f"{lane} report solver_model_config_source must be {expected_source}"
            )
    return report


def _finite_heavy_top_nutation_reference_samples(report: ClaimReport) -> bool:
    curves = report.observed.get("reference_curves")
    if not isinstance(curves, dict):
        return False
    nutation = curves.get("reference_nutation")
    if not isinstance(nutation, dict):
        return False
    samples = nutation.get("samples")
    if not isinstance(samples, list) or not samples:
        return False
    return all(
        isinstance(sample, dict)
        and _finite_scalar(sample.get("time_s")) is not None
        and _finite_scalar(sample.get("value")) is not None
        for sample in samples
    )


def _valid_heavy_top_figure_report_or_none(
    path: str | Path | None,
    *,
    config: HeavyTopRunConfig,
) -> ClaimReport | None:
    if path is None:
        return None
    try:
        report = load_claim_report(path)
    except (OSError, ValueError):
        return None
    if report.claim_id != config.claim_id or report.scene_id != config.scene_id:
        return None
    if report.baseline_lane != HEAVY_TOP_FIGURE_BASELINE_LANE:
        return None
    if report.solver_mode != HEAVY_TOP_FIGURE_SOLVER_MODE:
        return None
    if report.backend != HEAVY_TOP_FIGURE_BACKEND:
        return None
    if report.status != EvidenceStatus.INCOMPLETE:
        return None
    if report.observed.get("full_experiment_claim_passed") is not False:
        return None
    if report.observed.get("reference_curve_available") is not True:
        return None
    if not _finite_heavy_top_nutation_reference_samples(report):
        return None
    return report


def _finite_t_handle_figure_curve_samples(report: ClaimReport) -> bool:
    for metric_key in ("angular_velocity_curves", "energy_loss_curves"):
        curves = report.observed.get(metric_key)
        if not isinstance(curves, dict):
            return False
        for color_family in ("blue", "orange", "green"):
            curve = curves.get(color_family)
            if not isinstance(curve, dict):
                return False
            if curve.get("curve_identity_status") != "color_family_not_legend_entry":
                return False
            samples = curve.get("samples")
            if not isinstance(samples, list) or not samples:
                return False
            if not all(
                isinstance(sample, dict)
                and _finite_scalar(sample.get("time_s")) is not None
                and _finite_scalar(sample.get("value")) is not None
                for sample in samples
            ):
                return False
    return True


def _valid_t_handle_figure_report_or_none(
    path: str | Path | None,
    *,
    config: THandleRunConfig,
) -> ClaimReport | None:
    if path is None:
        return None
    try:
        report = load_claim_report(path)
    except (OSError, ValueError):
        return None
    if report.claim_id != config.claim_id or report.scene_id != config.scene_id:
        return None
    if report.baseline_lane != T_HANDLE_FIGURE_BASELINE_LANE:
        return None
    if report.solver_mode != T_HANDLE_FIGURE_SOLVER_MODE:
        return None
    if report.backend != T_HANDLE_FIGURE_BACKEND:
        return None
    if report.status != EvidenceStatus.INCOMPLETE:
        return None
    if report.observed.get("full_experiment_claim_passed") is not False:
        return None
    if report.observed.get("reference_curve_available") is not True:
        return None
    if report.observed.get("figure_curve_scope") != "color_family_digitization_only":
        return None
    if not _finite_t_handle_figure_curve_samples(report):
        return None
    return report


def _t_handle_figure_sample_counts(report: ClaimReport) -> dict[str, dict[str, int]]:
    result: dict[str, dict[str, int]] = {}
    for output_key, report_key in (
        ("angular_velocity_color_families", "angular_velocity_curves"),
        ("energy_loss_color_families", "energy_loss_curves"),
    ):
        curves = report.observed[report_key]
        result[output_key] = {
            str(color_family): len(curve["samples"])
            for color_family, curve in curves.items()
            if isinstance(curve, dict) and isinstance(curve.get("samples"), list)
        }
    return result


def _finite_scalar(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    result = float(value)
    return result if isfinite(result) else None


def _finite_vector3(value: Any) -> list[float] | None:
    if not isinstance(value, list | tuple) or len(value) != 3:
        return None
    result: list[float] = []
    for component in value:
        scalar = _finite_scalar(component)
        if scalar is None:
            return None
        result.append(scalar)
    return result


def _finite_difference(lhs: float, rhs: float) -> float | None:
    difference = lhs - rhs
    return difference if isfinite(difference) else None


def _physical_lane_provenance(path: str | Path, report: ClaimReport) -> dict[str, str]:
    return {
        "path": Path(path).as_posix(),
        "sha256": _sha256_file(path),
        "source_commit": report.source_commit,
        "vendored_newton_commit": report.vendored_newton_commit,
        "solver_mode": report.solver_mode,
        "backend": report.backend,
        "baseline_lane": report.baseline_lane,
        "status": report.status.value,
    }


def _heavy_top_lane_provenance(path: str | Path, report: ClaimReport) -> dict[str, str]:
    provenance = {
        "path": Path(path).as_posix(),
        "sha256": _sha256_file(path),
        "source_commit": report.source_commit,
        "vendored_newton_commit": report.vendored_newton_commit,
        "solver_mode": report.solver_mode,
        "backend": report.backend,
        "baseline_lane": report.baseline_lane,
        "status": report.status.value,
    }
    diagnostic_scope = report.observed.get("mabd_diagnostic_scope")
    if isinstance(diagnostic_scope, str) and diagnostic_scope:
        provenance["mabd_diagnostic_scope"] = diagnostic_scope
    return provenance


def _t_handle_lane_provenance(path: str | Path, report: ClaimReport) -> dict[str, str | bool]:
    provenance = {
        "path": Path(path).as_posix(),
        "sha256": _sha256_file(path),
        "source_commit": report.source_commit,
        "vendored_newton_commit": report.vendored_newton_commit,
        "solver_mode": report.solver_mode,
        "backend": report.backend,
        "baseline_lane": report.baseline_lane,
        "status": report.status.value,
    }
    reference_not_paper_geometry = report.observed.get("reference_not_paper_geometry")
    if isinstance(reference_not_paper_geometry, bool):
        provenance["reference_not_paper_geometry"] = reference_not_paper_geometry
    for key in (
        "reference_scope",
        "mabd_diagnostic_scope",
        "solver_model_config_source",
    ):
        value = report.observed.get(key)
        if isinstance(value, str) and value:
            provenance[key] = value
    return provenance


def _heavy_top_nutation_range_deg(report: ClaimReport) -> float | None:
    minimum = _finite_scalar(report.observed.get("min_nutation_angle_deg"))
    maximum = _finite_scalar(report.observed.get("max_nutation_angle_deg"))
    if minimum is None or maximum is None:
        return None
    result = maximum - minimum
    return result if isfinite(result) else None


def _heavy_top_metric_snapshot(report: ClaimReport, *, lane: str) -> dict[str, float | None]:
    energy_drift = (
        _finite_scalar(report.observed.get("relative_energy_drift"))
        if lane in {"rbd_rk4_reference", "mabd_newton"}
        else _finite_scalar(report.observed.get("energy_drift"))
    )
    return {
        "nutation_angle_range_deg": _heavy_top_nutation_range_deg(report),
        "max_abs_precession_velocity_rad_s": _finite_scalar(
            report.observed.get("max_abs_precession_velocity_rad_s")
        ),
        "energy_drift": energy_drift,
        "source_relative_energy_drift": _finite_scalar(
            report.observed.get("relative_energy_drift")
        ),
        "max_pivot_residual_m": _finite_scalar(report.observed.get("max_pivot_residual_m")),
        "max_constraint_residual_norm": _finite_scalar(
            report.observed.get("max_constraint_residual_norm")
        ),
        "max_affine_shape_spread_m": _finite_scalar(
            report.observed.get("max_affine_shape_spread_m")
        ),
    }


def _heavy_top_sample_rows(report: ClaimReport) -> list[dict[str, Any]]:
    rows = report.observed.get("precession_nutation_samples")
    if not isinstance(rows, list):
        return []
    return [dict(row) for row in rows if isinstance(row, dict)]


def _heavy_top_mabd_precession_velocity_available(report: ClaimReport) -> bool:
    if _finite_scalar(report.observed.get("max_abs_precession_velocity_rad_s")) is None:
        return False
    rows = _heavy_top_sample_rows(report)
    if not rows:
        return False
    return all(
        _finite_scalar(row.get("precession_velocity_rad_s")) is not None
        for row in rows
    )


def _heavy_top_sample_key(row: dict[str, Any]) -> int | None:
    sample_index = _finite_scalar(row.get("sample_index"))
    if sample_index is None:
        return None
    result = int(sample_index)
    return result if float(result) == sample_index else None


def _heavy_top_sample_identity(row: dict[str, Any]) -> dict[str, float | int | None]:
    sample_index = _finite_scalar(row.get("sample_index"))
    time_s = _finite_scalar(row.get("time_s"))
    return {
        "sample_index": int(sample_index) if sample_index is not None else None,
        "time_s": time_s,
    }


def _heavy_top_sample_index_differences(
    rk4_report: ClaimReport,
    mabd_report: ClaimReport,
    *,
    max_sample_time_delta_s: float,
) -> dict[str, Any]:
    rk4_rows = _heavy_top_sample_rows(rk4_report)
    mabd_rows = _heavy_top_sample_rows(mabd_report)
    rk4_by_key = {
        key: row for row in rk4_rows if (key := _heavy_top_sample_key(row)) is not None
    }
    mabd_by_key = {
        key: row for row in mabd_rows if (key := _heavy_top_sample_key(row)) is not None
    }
    matched_keys = sorted(set(rk4_by_key) & set(mabd_by_key))
    unmatched_rk4 = [
        _heavy_top_sample_identity(row)
        for row in rk4_rows
        if (key := _heavy_top_sample_key(row)) is None or key not in mabd_by_key
    ]
    unmatched_mabd = [
        _heavy_top_sample_identity(row)
        for row in mabd_rows
        if (key := _heavy_top_sample_key(row)) is None or key not in rk4_by_key
    ]
    differences: list[dict[str, float | int]] = []
    nonfinite = False
    time_grid_mismatch = False
    for key in matched_keys:
        rk4_row = rk4_by_key[key]
        mabd_row = mabd_by_key[key]
        rk4_time = _finite_scalar(rk4_row.get("time_s"))
        mabd_time = _finite_scalar(mabd_row.get("time_s"))
        rk4_nutation = _finite_scalar(rk4_row.get("nutation_angle_deg"))
        mabd_nutation = _finite_scalar(mabd_row.get("nutation_angle_deg"))
        rk4_precession = _finite_scalar(rk4_row.get("precession_angle_rad"))
        mabd_precession = _finite_scalar(mabd_row.get("precession_angle_rad"))
        if (
            rk4_time is None
            or mabd_time is None
            or rk4_nutation is None
            or mabd_nutation is None
            or rk4_precession is None
            or mabd_precession is None
        ):
            nonfinite = True
            continue
        time_delta = mabd_time - rk4_time
        nutation_delta = mabd_nutation - rk4_nutation
        precession_delta = mabd_precession - rk4_precession
        if not all(isfinite(value) for value in (time_delta, nutation_delta, precession_delta)):
            nonfinite = True
            continue
        abs_time_delta = abs(time_delta)
        if abs_time_delta > max_sample_time_delta_s:
            time_grid_mismatch = True
        differences.append(
            {
                "sample_index": key,
                "rk4_time_s": rk4_time,
                "mabd_time_s": mabd_time,
                "mabd_minus_rk4_time_s": time_delta,
                "abs_sample_time_delta_s": abs_time_delta,
                "rk4_nutation_angle_deg": rk4_nutation,
                "mabd_nutation_angle_deg": mabd_nutation,
                "mabd_minus_rk4_nutation_angle_deg": nutation_delta,
                "abs_nutation_delta_deg": abs(nutation_delta),
                "rk4_precession_angle_rad": rk4_precession,
                "mabd_precession_angle_rad": mabd_precession,
                "mabd_minus_rk4_precession_angle_rad": precession_delta,
                "abs_precession_delta_rad": abs(precession_delta),
            }
        )
    max_time_delta = (
        max(row["abs_sample_time_delta_s"] for row in differences)
        if differences
        else None
    )
    max_nutation_delta = (
        max(row["abs_nutation_delta_deg"] for row in differences)
        if differences
        else None
    )
    max_precession_delta = (
        max(row["abs_precession_delta_rad"] for row in differences)
        if differences
        else None
    )
    return {
        "rk4_sample_count": len(rk4_rows),
        "mabd_sample_count": len(mabd_rows),
        "matched_sample_index_count": len(matched_keys),
        "unmatched_rk4_samples": unmatched_rk4,
        "unmatched_mabd_samples": unmatched_mabd,
        "sample_index_differences": differences,
        "max_sample_time_delta_s": max_time_delta,
        "max_abs_nutation_delta_deg": max_nutation_delta,
        "max_abs_precession_delta_rad": max_precession_delta,
        "time_grid_mismatch": time_grid_mismatch,
        "nonfinite": nonfinite,
    }


def _t_handle_metric_snapshot(report: ClaimReport) -> dict[str, float | None]:
    return {
        "relative_energy_drift": _finite_scalar(report.observed.get("relative_energy_drift")),
        "energy_initial": _finite_scalar(report.observed.get("energy_initial")),
        "energy_final": _finite_scalar(report.observed.get("energy_final")),
        "angular_momentum_norm_drift": _finite_scalar(
            report.observed.get("angular_momentum_norm_drift")
        ),
    }


def _t_handle_sample_rows(report: ClaimReport) -> list[dict[str, Any]]:
    rows = report.observed.get("angular_velocity_samples")
    if not isinstance(rows, list):
        return []
    return [dict(row) for row in rows if isinstance(row, dict)]


def _t_handle_sample_key(row: dict[str, Any]) -> int | None:
    sample_index = _finite_scalar(row.get("sample_index"))
    if sample_index is None:
        return None
    result = int(sample_index)
    return result if float(result) == sample_index else None


def _t_handle_sample_identity(row: dict[str, Any]) -> dict[str, float | int | None]:
    sample_index = _finite_scalar(row.get("sample_index"))
    time_s = _finite_scalar(row.get("time_s"))
    return {
        "sample_index": int(sample_index) if sample_index is not None else None,
        "time_s": time_s,
    }


def _t_handle_omega(row: dict[str, Any]) -> list[float] | None:
    result = [
        _finite_scalar(row.get("omega_x_rad_s")),
        _finite_scalar(row.get("omega_y_rad_s")),
        _finite_scalar(row.get("omega_z_rad_s")),
    ]
    if any(component is None for component in result):
        return None
    return [float(component) for component in result]


def _t_handle_axis_component(axis_index: int) -> str:
    return ("omega_x_rad_s", "omega_y_rad_s", "omega_z_rad_s")[axis_index]


def _t_handle_first_sample_grid_flip_time(
    rows: list[dict[str, Any]],
    *,
    axis_index: int,
) -> float | None:
    finite_rows: list[tuple[float, float]] = []
    for row in rows:
        time_s = _finite_scalar(row.get("time_s"))
        omega = _t_handle_omega(row)
        if time_s is not None and omega is not None:
            finite_rows.append((time_s, omega[axis_index]))
    if not finite_rows:
        return None
    finite_rows.sort(key=lambda item: item[0])
    prev_time: float | None = None
    prev_value: float | None = None
    zero_run_start_time: float | None = None
    for time_s, value in finite_rows:
        if value == 0.0:
            if prev_value is not None and zero_run_start_time is None:
                zero_run_start_time = time_s
            continue
        if prev_value is not None and prev_time is not None and prev_value * value < 0.0:
            if zero_run_start_time is not None:
                return zero_run_start_time
            alpha = abs(prev_value) / (abs(prev_value) + abs(value))
            crossing = prev_time + alpha * (time_s - prev_time)
            return crossing if isfinite(crossing) else None
        prev_time = time_s
        prev_value = value
        zero_run_start_time = None
    return None


def _t_handle_rows_by_unique_sample_key(
    rows: list[dict[str, Any]],
) -> tuple[
    dict[int, dict[str, Any]],
    list[int],
    list[dict[str, float | int | None]],
    list[dict[str, float | int | None]],
]:
    grouped: dict[int, list[dict[str, Any]]] = {}
    invalid_samples: list[dict[str, float | int | None]] = []
    for row in rows:
        key = _t_handle_sample_key(row)
        if key is None:
            invalid_samples.append(_t_handle_sample_identity(row))
            continue
        grouped.setdefault(key, []).append(row)
    duplicate_keys = sorted(key for key, values in grouped.items() if len(values) > 1)
    duplicate_samples = [
        _t_handle_sample_identity(row)
        for key in duplicate_keys
        for row in grouped[key]
    ]
    unique_rows = {
        key: values[0]
        for key, values in grouped.items()
        if len(values) == 1
    }
    return unique_rows, duplicate_keys, duplicate_samples, invalid_samples


def _t_handle_sample_index_differences(
    rk4_report: ClaimReport,
    mabd_report: ClaimReport,
    *,
    axis_index: int,
    max_sample_time_delta_s: float,
) -> dict[str, Any]:
    rk4_rows = _t_handle_sample_rows(rk4_report)
    mabd_rows = _t_handle_sample_rows(mabd_report)
    (
        rk4_by_key,
        duplicate_rk4_keys,
        duplicate_rk4_samples,
        invalid_rk4_samples,
    ) = _t_handle_rows_by_unique_sample_key(rk4_rows)
    (
        mabd_by_key,
        duplicate_mabd_keys,
        duplicate_mabd_samples,
        invalid_mabd_samples,
    ) = _t_handle_rows_by_unique_sample_key(mabd_rows)
    matched_keys = sorted(set(rk4_by_key) & set(mabd_by_key))
    unmatched_rk4 = invalid_rk4_samples + duplicate_rk4_samples + [
        _t_handle_sample_identity(row)
        for row in rk4_rows
        if (key := _t_handle_sample_key(row)) is not None
        and key in rk4_by_key
        and key not in mabd_by_key
    ]
    unmatched_mabd = invalid_mabd_samples + duplicate_mabd_samples + [
        _t_handle_sample_identity(row)
        for row in mabd_rows
        if (key := _t_handle_sample_key(row)) is not None
        and key in mabd_by_key
        and key not in rk4_by_key
    ]
    differences: list[dict[str, float | int]] = []
    nonfinite = False
    time_grid_mismatch = False
    aligned_axis_delta_squared = 0.0
    time_aligned_count = 0
    for key in matched_keys:
        rk4_row = rk4_by_key[key]
        mabd_row = mabd_by_key[key]
        rk4_time = _finite_scalar(rk4_row.get("time_s"))
        mabd_time = _finite_scalar(mabd_row.get("time_s"))
        rk4_omega = _t_handle_omega(rk4_row)
        mabd_omega = _t_handle_omega(mabd_row)
        if rk4_time is None or mabd_time is None or rk4_omega is None or mabd_omega is None:
            nonfinite = True
            continue
        time_delta = _finite_difference(mabd_time, rk4_time)
        component_deltas = [
            _finite_difference(mabd_component, rk4_component)
            for rk4_component, mabd_component in zip(rk4_omega, mabd_omega, strict=True)
        ]
        if time_delta is None or any(component is None for component in component_deltas):
            nonfinite = True
            continue
        deltas = [float(component) for component in component_deltas]
        abs_time_delta = abs(time_delta)
        if abs_time_delta > max_sample_time_delta_s:
            time_grid_mismatch = True
        else:
            aligned_axis_delta_squared += deltas[axis_index] * deltas[axis_index]
            time_aligned_count += 1
        differences.append(
            {
                "sample_index": key,
                "rk4_time_s": rk4_time,
                "mabd_time_s": mabd_time,
                "mabd_minus_rk4_time_s": time_delta,
                "abs_sample_time_delta_s": abs_time_delta,
                "rk4_omega_x_rad_s": rk4_omega[0],
                "rk4_omega_y_rad_s": rk4_omega[1],
                "rk4_omega_z_rad_s": rk4_omega[2],
                "mabd_omega_x_rad_s": mabd_omega[0],
                "mabd_omega_y_rad_s": mabd_omega[1],
                "mabd_omega_z_rad_s": mabd_omega[2],
                "mabd_minus_rk4_omega_x_rad_s": deltas[0],
                "mabd_minus_rk4_omega_y_rad_s": deltas[1],
                "mabd_minus_rk4_omega_z_rad_s": deltas[2],
                "abs_omega_x_delta_rad_s": abs(deltas[0]),
                "abs_omega_y_delta_rad_s": abs(deltas[1]),
                "abs_omega_z_delta_rad_s": abs(deltas[2]),
            }
        )
    max_time_delta = (
        max(row["abs_sample_time_delta_s"] for row in differences)
        if differences
        else None
    )
    max_abs_omega_delta = (
        max(
            max(
                row["abs_omega_x_delta_rad_s"],
                row["abs_omega_y_delta_rad_s"],
                row["abs_omega_z_delta_rad_s"],
            )
            for row in differences
        )
        if differences
        else None
    )
    waveform_rmse = (
        sqrt(aligned_axis_delta_squared / float(time_aligned_count))
        if time_aligned_count > 0
        else None
    )
    return {
        "rk4_sample_count": len(rk4_rows),
        "mabd_sample_count": len(mabd_rows),
        "matched_sample_index_count": len(matched_keys),
        "finite_matched_sample_count": len(differences),
        "time_aligned_sample_count": time_aligned_count,
        "unmatched_rk4_samples": unmatched_rk4,
        "unmatched_mabd_samples": unmatched_mabd,
        "duplicate_rk4_sample_indices": duplicate_rk4_keys,
        "duplicate_mabd_sample_indices": duplicate_mabd_keys,
        "sample_index_differences": differences,
        "max_sample_time_delta_s": max_time_delta,
        "max_abs_angular_velocity_delta_rad_s": max_abs_omega_delta,
        "intermediate_axis_waveform_rmse_rad_s": waveform_rmse,
        "time_grid_mismatch": time_grid_mismatch,
        "sample_index_duplicate": bool(duplicate_rk4_keys or duplicate_mabd_keys),
        "nonfinite": nonfinite,
    }


def _t_handle_paper_metric_statuses(
    sample_diagnostics: dict[str, Any],
    *,
    flip_delta: float | None,
    digitized_figure_reference_available: bool = False,
) -> dict[str, dict[str, str]]:
    flip_status = (
        "sample_grid_diagnostic_not_paper_timing"
        if flip_delta is not None
        else "sample_grid_flip_delta_unavailable_not_paper_timing"
    )
    waveform_status = (
        "diagnostic_available_not_paper_curve"
        if sample_diagnostics["time_aligned_sample_count"] > 0
        else "diagnostic_unavailable_time_alignment_missing"
    )
    energy_status = "signed_energy_drift_diagnostic_not_paper_loss"
    waveform_limitation = "compares diagnostic lanes, not raw paper waveform curves"
    energy_limitation = "relative_energy_drift is signed diagnostic drift, not paper energy loss"
    if digitized_figure_reference_available:
        waveform_status = "paper_figure_digitized_color_family_available_not_curve_agreement"
        energy_status = "paper_figure_digitized_color_family_available_not_energy_agreement"
        waveform_limitation = (
            "paper figure color-family digitization is available, but no curve "
            "agreement gate has passed"
        )
        energy_limitation = (
            "paper figure color-family digitization is available, but no energy-loss "
            "agreement gate has passed"
        )
    return {
        "flip_timing_error": {
            "status": flip_status,
            "diagnostic_field": "flip_timing_diagnostics",
            "limitation": "sample-grid interpolation only; raw paper timing unavailable",
        },
        "intermediate_axis_angular_velocity_waveform": {
            "status": waveform_status,
            "diagnostic_field": "intermediate_axis_waveform_rmse_rad_s",
            "limitation": waveform_limitation,
        },
        "energy_loss": {
            "status": energy_status,
            "diagnostic_field": "energy_drift_diagnostics",
            "limitation": energy_limitation,
        },
    }


def _physical_pendulum_metric_snapshot(report: ClaimReport, metrics: tuple[str, ...]) -> dict[str, float | None]:
    return {
        metric: _finite_scalar(report.observed.get(metric))
        for metric in metrics
    }


def _physical_angle_rows(report: ClaimReport) -> list[dict[str, Any]]:
    rows = report.observed.get("angle_samples_rad")
    if not isinstance(rows, list):
        return []
    return [dict(row) for row in rows if isinstance(row, dict)]


def _physical_sample_key(row: dict[str, Any]) -> tuple[int, float] | None:
    step = _finite_scalar(row.get("step"))
    time_s = _finite_scalar(row.get("time_s"))
    if step is None or time_s is None:
        return None
    step_int = int(step)
    if float(step_int) != step:
        return None
    return (step_int, round(time_s, 12))


def _physical_sample_identity(row: dict[str, Any]) -> dict[str, float | int | None]:
    sample_index = _finite_scalar(row.get("sample_index"))
    step = _finite_scalar(row.get("step"))
    time_s = _finite_scalar(row.get("time_s"))
    return {
        "sample_index": int(sample_index) if sample_index is not None else None,
        "step": int(step) if step is not None and float(int(step)) == step else None,
        "time_s": time_s,
    }


def _physical_angle_sample_differences(
    mabd_report: ClaimReport,
    rbd_report: ClaimReport,
) -> dict[str, Any]:
    mabd_rows = _physical_angle_rows(mabd_report)
    rbd_rows = _physical_angle_rows(rbd_report)
    mabd_by_key = {
        key: row for row in mabd_rows if (key := _physical_sample_key(row)) is not None
    }
    rbd_by_key = {
        key: row for row in rbd_rows if (key := _physical_sample_key(row)) is not None
    }
    matched_keys = sorted(set(mabd_by_key) & set(rbd_by_key))
    unmatched_mabd = [
        _physical_sample_identity(row)
        for row in mabd_rows
        if (key := _physical_sample_key(row)) is None or key not in rbd_by_key
    ]
    unmatched_rbd = [
        _physical_sample_identity(row)
        for row in rbd_rows
        if (key := _physical_sample_key(row)) is None or key not in mabd_by_key
    ]
    differences: list[dict[str, float | int]] = []
    nonfinite = False
    for key in matched_keys:
        mabd_row = mabd_by_key[key]
        rbd_row = rbd_by_key[key]
        mabd_angle = _finite_scalar(mabd_row.get("angle_rad"))
        rbd_angle = _finite_scalar(rbd_row.get("angle_rad"))
        if mabd_angle is None or rbd_angle is None:
            nonfinite = True
            continue
        delta = _finite_difference(mabd_angle, rbd_angle)
        if delta is None:
            nonfinite = True
            continue
        sample_index = _finite_scalar(mabd_row.get("sample_index"))
        differences.append(
            {
                "sample_index": int(sample_index) if sample_index is not None else len(differences),
                "step": key[0],
                "time_s": key[1],
                "mabd_angle_rad": mabd_angle,
                "rbd_angle_rad": rbd_angle,
                "mabd_minus_rbd_angle_rad": delta,
                "abs_angle_delta_rad": abs(delta),
            }
        )
    max_delta = (
        max(row["abs_angle_delta_rad"] for row in differences)
        if differences
        else None
    )
    return {
        "mabd_sample_count": len(mabd_rows),
        "rbd_sample_count": len(rbd_rows),
        "matched_sample_count": len(matched_keys),
        "unmatched_mabd_samples": unmatched_mabd,
        "unmatched_rbd_samples": unmatched_rbd,
        "angle_sample_differences_rad": differences,
        "max_mabd_rbd_abs_angle_delta_rad": max_delta,
        "nonfinite": nonfinite,
    }


def _physical_joint_force_waveform_diagnostics(
    analytic_report: ClaimReport,
    mabd_report: ClaimReport,
    rbd_report: ClaimReport,
) -> dict[str, Any]:
    mabd_rows = _physical_angle_rows(mabd_report)
    rbd_rows = _physical_angle_rows(rbd_report)
    mabd_by_key = {
        key: row for row in mabd_rows if (key := _physical_sample_key(row)) is not None
    }
    rbd_by_key = {
        key: row for row in rbd_rows if (key := _physical_sample_key(row)) is not None
    }
    matched_keys = sorted(set(mabd_by_key) & set(rbd_by_key))
    rows: list[dict[str, float | int]] = []
    nonfinite = False
    for key in matched_keys:
        mabd_row = mabd_by_key[key]
        rbd_row = rbd_by_key[key]
        reference_force = _finite_scalar(mabd_row.get("reference_joint_force_magnitude_n"))
        rbd_reference_force = _finite_scalar(rbd_row.get("reference_joint_force_magnitude_n"))
        mabd_force = _finite_scalar(mabd_row.get("world_anchor_reaction_magnitude_n"))
        rbd_force = _finite_scalar(rbd_row.get("joint_force_magnitude_n"))
        mabd_error = _finite_scalar(mabd_row.get("abs_joint_force_error_n"))
        rbd_error = _finite_scalar(rbd_row.get("abs_joint_force_error_n"))
        if (
            reference_force is None
            or rbd_reference_force is None
            or mabd_force is None
            or rbd_force is None
            or mabd_error is None
            or rbd_error is None
        ):
            nonfinite = True
            continue
        reference_delta = _finite_difference(reference_force, rbd_reference_force)
        if reference_delta is None:
            nonfinite = True
            continue
        sample_index = _finite_scalar(mabd_row.get("sample_index"))
        rows.append(
            {
                "sample_index": int(sample_index) if sample_index is not None else len(rows),
                "step": key[0],
                "time_s": key[1],
                "reference_joint_force_magnitude_n": reference_force,
                "mabd_joint_force_magnitude_n": mabd_force,
                "mabd_abs_joint_force_error_n": mabd_error,
                "rbd_joint_force_magnitude_n": rbd_force,
                "rbd_abs_joint_force_error_n": rbd_error,
                "reference_delta_between_lanes_n": reference_delta,
            }
        )
    return {
        "reference_model": analytic_report.expected.get(
            "joint_force_reference_model",
            "scalar_point_pendulum_radial_reaction",
        ),
        "limitation": "diagnostic scalar reference, not paper geometry",
        "analytic_sample_count": len(
            analytic_report.observed.get("joint_force_samples_n", [])
            if isinstance(analytic_report.observed.get("joint_force_samples_n"), list)
            else []
        ),
        "mabd_sample_count": len(mabd_rows),
        "rbd_sample_count": len(rbd_rows),
        "matched_sample_count": len(matched_keys),
        "nonfinite": nonfinite,
        "max_mabd_abs_joint_force_error_n": _finite_scalar(
            mabd_report.observed.get("max_abs_joint_force_error_n")
        ),
        "max_rbd_abs_joint_force_error_n": _finite_scalar(
            rbd_report.observed.get("max_abs_joint_force_error_n")
        ),
        "joint_force_sample_differences_n": rows,
    }


def _physical_pendulum_paper_metric_statuses() -> dict[str, dict[str, str | None]]:
    return {
        "pendulum_angle_error": {
            "status": "diagnostic_available",
            "mabd_field": "max_abs_angle_error_rad",
            "rbd_field": "max_abs_angle_error_rad",
        },
        "phase_drift": {
            "status": "diagnostic_available",
            "mabd_field": "max_phase_drift_rad",
            "rbd_field": "max_phase_drift_rad",
        },
        "joint_force_error": {
            "status": "diagnostic_scalar_reference_not_paper_geometry",
            "mabd_field": "max_abs_joint_force_error_n",
            "rbd_field": "max_abs_joint_force_error_n",
            "limitation": "scalar reference does not reconstruct paper geometry",
        },
    }


def _lane_metric_snapshot(report: ClaimReport) -> dict[str, float | None]:
    return {
        metric: _finite_scalar(report.observed[metric]) if metric in report.observed else None
        for metric in SPINNING_BOX_REQUIRED_METRICS
    }


def _lane_vector_metric_snapshot(report: ClaimReport) -> dict[str, list[float] | None]:
    return {
        metric: _finite_vector3(report.observed[metric]) if metric in report.observed else None
        for metric in SPINNING_BOX_REQUIRED_VECTOR_METRICS
    }


def _lane_gate_status(report: ClaimReport) -> str:
    value = report.observed.get("lane_gate_status")
    return value if isinstance(value, str) and value else report.status.value


def _missing_metrics(lane: str, report: ClaimReport) -> list[str]:
    return [
        f"{lane}:{metric}" for metric in SPINNING_BOX_REQUIRED_METRICS if metric not in report.observed
    ]


def _missing_vector_metrics(lane: str, report: ClaimReport) -> list[str]:
    return [
        f"{lane}:{metric}"
        for metric in SPINNING_BOX_REQUIRED_VECTOR_METRICS
        if metric not in report.observed
    ]


def _invalid_metrics(lane: str, report: ClaimReport) -> list[str]:
    return [
        f"{lane}:{metric}"
        for metric in SPINNING_BOX_REQUIRED_METRICS
        if metric in report.observed and _finite_scalar(report.observed[metric]) is None
    ]


def _invalid_vector_metrics(lane: str, report: ClaimReport) -> list[str]:
    return [
        f"{lane}:{metric}"
        for metric in SPINNING_BOX_REQUIRED_VECTOR_METRICS
        if metric in report.observed and _finite_vector3(report.observed[metric]) is None
    ]


def _lane_metric_differences(
    mabd_report: ClaimReport,
    rbd_report: ClaimReport,
) -> dict[str, dict[str, float]]:
    differences: dict[str, float] = {}
    for metric in SPINNING_BOX_REQUIRED_METRICS:
        mabd_value = _finite_scalar(mabd_report.observed.get(metric))
        rbd_value = _finite_scalar(rbd_report.observed.get(metric))
        if mabd_value is not None and rbd_value is not None:
            difference = _finite_difference(mabd_value, rbd_value)
            if difference is not None:
                differences[metric] = difference
    return {"mabd_newton_minus_rbd_implicit_baseline": differences}


def _lane_vector_metric_differences(
    mabd_report: ClaimReport,
    rbd_report: ClaimReport,
) -> dict[str, dict[str, list[float]]]:
    differences: dict[str, list[float]] = {}
    for metric in SPINNING_BOX_REQUIRED_VECTOR_METRICS:
        mabd_value = _finite_vector3(mabd_report.observed.get(metric))
        rbd_value = _finite_vector3(rbd_report.observed.get(metric))
        if mabd_value is not None and rbd_value is not None:
            difference: list[float] = []
            for mabd_component, rbd_component in zip(mabd_value, rbd_value, strict=True):
                component_difference = _finite_difference(mabd_component, rbd_component)
                if component_difference is None:
                    break
                difference.append(component_difference)
            if len(difference) == 3:
                differences[metric] = difference
    return {"mabd_newton_minus_rbd_implicit_baseline": differences}


def write_spinning_box_comparison_report(
    path: str | Path,
    *,
    config: SpinningBoxRunConfig,
    mabd_report_path: str | Path,
    rbd_report_path: str | Path,
    source_commit: str,
    vendored_newton_commit: str,
    paper_source_version: str = "2603.08079v2",
) -> ClaimReport:
    mabd_report = _require_lane_report(mabd_report_path, config=config, lane="mabd_newton")
    rbd_report = _require_lane_report(rbd_report_path, config=config, lane="rbd_implicit_baseline")
    lane_statuses = {
        "mabd_newton": mabd_report.status.value,
        "rbd_implicit_baseline": rbd_report.status.value,
    }
    lane_gate_statuses = {
        "mabd_newton": _lane_gate_status(mabd_report),
        "rbd_implicit_baseline": _lane_gate_status(rbd_report),
    }
    missing_required_metrics = _missing_metrics("mabd_newton", mabd_report) + _missing_metrics(
        "rbd_implicit_baseline",
        rbd_report,
    )
    invalid_required_metrics = _invalid_metrics("mabd_newton", mabd_report) + _invalid_metrics(
        "rbd_implicit_baseline",
        rbd_report,
    )
    missing_required_vector_metrics = _missing_vector_metrics(
        "mabd_newton",
        mabd_report,
    ) + _missing_vector_metrics("rbd_implicit_baseline", rbd_report)
    invalid_required_vector_metrics = _invalid_vector_metrics(
        "mabd_newton",
        mabd_report,
    ) + _invalid_vector_metrics("rbd_implicit_baseline", rbd_report)
    metric_differences = _lane_metric_differences(mabd_report, rbd_report)
    vector_metric_differences = _lane_vector_metric_differences(mabd_report, rbd_report)
    incomplete_lanes = [
        lane
        for lane, status in lane_gate_statuses.items()
        if status != EvidenceStatus.PASSED.value
    ]
    blocking_reasons = [
        *(f"{lane}_report_{lane_statuses[lane]}" for lane in incomplete_lanes),
        *(f"{metric}_missing" for metric in missing_required_metrics),
        *(f"{metric}_invalid" for metric in invalid_required_metrics),
        *(f"{metric}_missing" for metric in missing_required_vector_metrics),
        *(f"{metric}_invalid" for metric in invalid_required_vector_metrics),
    ]
    if rbd_report.solver_mode != "paper_faithful_implicit_rbd":
        blocking_reasons.append("rbd_implicit_baseline_not_paper_faithful")
    blocking_reasons.append("spinning_box_comparison_pass_gate_not_enabled")

    report = ClaimReport(
        claim_id=config.claim_id,
        scene_id=config.scene_id,
        asset_hashes={"primitive_cube": "not_applicable_procedural"},
        solver_mode="spinning_box_multilane_comparison_development",
        backend="report_protocol",
        baseline_lane="spinning_box_comparison_protocol",
        expected={
            "paper_claim_status": "requires passed M-ABD and paper-faithful implicit RBD lane gates",
            "required_lanes": ["mabd_newton", "rbd_implicit_baseline"],
            "required_metrics": list(SPINNING_BOX_REQUIRED_METRICS),
            "required_vector_metrics": list(SPINNING_BOX_REQUIRED_VECTOR_METRICS),
            "source_lines": list(config.source_lines),
        },
        observed={
            "lane_statuses": lane_statuses,
            "lane_gate_statuses": lane_gate_statuses,
            "lane_solver_modes": {
                "mabd_newton": mabd_report.solver_mode,
                "rbd_implicit_baseline": rbd_report.solver_mode,
            },
            "lane_metrics": {
                "mabd_newton": _lane_metric_snapshot(mabd_report),
                "rbd_implicit_baseline": _lane_metric_snapshot(rbd_report),
            },
            "lane_vector_metrics": {
                "mabd_newton": _lane_vector_metric_snapshot(mabd_report),
                "rbd_implicit_baseline": _lane_vector_metric_snapshot(rbd_report),
            },
            "missing_required_metrics": missing_required_metrics,
            "invalid_required_metrics": invalid_required_metrics,
            "missing_required_vector_metrics": missing_required_vector_metrics,
            "invalid_required_vector_metrics": invalid_required_vector_metrics,
            "lane_metric_differences": metric_differences,
            "lane_vector_metric_differences": vector_metric_differences,
            "blocking_reasons": blocking_reasons,
        },
        threshold={
            "required_lane_status": EvidenceStatus.PASSED.value,
            "required_lane_gate_status": EvidenceStatus.PASSED.value,
            "required_metrics": list(SPINNING_BOX_REQUIRED_METRICS),
            "required_vector_metrics": list(SPINNING_BOX_REQUIRED_VECTOR_METRICS),
            "paper_faithful_rbd_solver_mode": "paper_faithful_implicit_rbd",
        },
        unit="json_report",
        status=EvidenceStatus.INCOMPLETE,
        failure_reason="required lane gate statuses or comparison pass gate remain incomplete",
        timing_distribution={"scope": "not_timed"},
        raw_outputs={
            "mabd_report": Path(mabd_report_path).as_posix(),
            "rbd_report": Path(rbd_report_path).as_posix(),
        },
        plot_paths={},
        source_commit=source_commit,
        vendored_newton_commit=vendored_newton_commit,
        paper_source_version=paper_source_version,
    )
    write_claim_report(report, path)
    return report


def write_physical_pendulum_comparison_report(
    path: str | Path,
    *,
    config: PhysicalPendulumRunConfig,
    analytic_report_path: str | Path,
    mabd_report_path: str | Path,
    rbd_report_path: str | Path,
    source_commit: str,
    vendored_newton_commit: str,
    paper_source_version: str = "2603.08079v2",
) -> ClaimReport:
    analytic_report = _require_physical_pendulum_lane_report(
        analytic_report_path,
        config=config,
        lane="analytic_reference",
    )
    mabd_report = _require_physical_pendulum_lane_report(
        mabd_report_path,
        config=config,
        lane="mabd_newton",
    )
    rbd_report = _require_physical_pendulum_lane_report(
        rbd_report_path,
        config=config,
        lane="rbd_implicit_baseline",
    )
    sample_diagnostics = _physical_angle_sample_differences(mabd_report, rbd_report)
    joint_force_diagnostics = _physical_joint_force_waveform_diagnostics(
        analytic_report,
        mabd_report,
        rbd_report,
    )
    blocking_reasons = [
        "pendulum_geometry_unknown",
        "physical_pendulum_comparison_pass_gate_not_enabled",
    ]
    if sample_diagnostics["matched_sample_count"] == 0:
        blocking_reasons.append("angle_sample_alignment_missing")
    if sample_diagnostics["nonfinite"]:
        blocking_reasons.append("angle_sample_nonfinite")

    observed = {
        "full_experiment_claim_passed": False,
        "lane_statuses": {
            "analytic_reference": analytic_report.status.value,
            "mabd_newton": mabd_report.status.value,
            "rbd_implicit_baseline": rbd_report.status.value,
        },
        "lane_observed_statuses": {
            "analytic_reference": analytic_report.observed.get("lane_status"),
            "mabd_newton": mabd_report.observed.get("lane_status"),
            "rbd_implicit_baseline": rbd_report.observed.get("lane_status"),
        },
        "lane_solver_modes": {
            "analytic_reference": analytic_report.solver_mode,
            "mabd_newton": mabd_report.solver_mode,
            "rbd_implicit_baseline": rbd_report.solver_mode,
        },
        "input_report_provenance": {
            "analytic_reference": _physical_lane_provenance(
                analytic_report_path,
                analytic_report,
            ),
            "mabd_newton": _physical_lane_provenance(
                mabd_report_path,
                mabd_report,
            ),
            "rbd_implicit_baseline": _physical_lane_provenance(
                rbd_report_path,
                rbd_report,
            ),
        },
        "lane_metrics": {
            "analytic_reference": _physical_pendulum_metric_snapshot(
                analytic_report,
                ("max_abs_reference_identity_error",),
            ),
            "mabd_newton": _physical_pendulum_metric_snapshot(
                mabd_report,
                (
                    "max_abs_angle_error_rad",
                    "max_phase_drift_rad",
                    "max_pivot_residual_m",
                    "max_constraint_residual_norm",
                    "max_world_anchor_reaction_magnitude_n",
                ),
            ),
            "rbd_implicit_baseline": _physical_pendulum_metric_snapshot(
                rbd_report,
                (
                    "max_abs_angle_error_rad",
                    "max_phase_drift_rad",
                    "max_implicit_residual",
                    "max_length_constraint_error_m",
                    "max_joint_force_magnitude_n",
                ),
            ),
        },
        "paper_metric_statuses": _physical_pendulum_paper_metric_statuses(),
        "paper_timing_source_audit": physical_pendulum_timing_source_audit(),
        "missing_required_lanes": [],
        "missing_paper_metrics": ["joint_force_error:paper_geometry_unknown"],
        "blocking_reasons": blocking_reasons,
        "mabd_sample_count": sample_diagnostics["mabd_sample_count"],
        "rbd_sample_count": sample_diagnostics["rbd_sample_count"],
        "matched_sample_count": sample_diagnostics["matched_sample_count"],
        "unmatched_mabd_samples": sample_diagnostics["unmatched_mabd_samples"],
        "unmatched_rbd_samples": sample_diagnostics["unmatched_rbd_samples"],
        "angle_sample_differences_rad": sample_diagnostics["angle_sample_differences_rad"],
        "max_mabd_rbd_abs_angle_delta_rad": sample_diagnostics[
            "max_mabd_rbd_abs_angle_delta_rad"
        ],
        "joint_force_waveform_diagnostics": joint_force_diagnostics,
    }

    report = ClaimReport(
        claim_id=config.claim_id,
        scene_id=config.scene_id,
        asset_hashes={"physical_pendulum_procedural": "not_applicable_procedural"},
        solver_mode="physical_pendulum_multilane_comparison_development",
        backend="report_protocol",
        baseline_lane="physical_pendulum_comparison_protocol",
        expected={
            "paper_claim_status": (
                "formal M-ABD and RBD lanes are present; scalar joint-force diagnostics "
                "exist, but paper geometry and pass gate remain required; runtime timing "
                "is not a cited physical-pendulum metric"
            ),
            "required_lanes": list(config.comparison.required_lanes),
            "diagnostic_lanes": list(config.comparison.diagnostic_lanes),
            "required_metrics": list(PHYSICAL_PENDULUM_REQUIRED_METRICS),
            "paper_timing_source_audit": physical_pendulum_timing_source_audit(),
            "source_lines": list(config.source_lines),
            "full_experiment_claim_passed": False,
        },
        observed=observed,
        threshold=config.comparison.thresholds,
        unit="json_report",
        status=EvidenceStatus.INCOMPLETE,
        failure_reason=(
            "physical-pendulum comparison protocol is incomplete because paper geometry "
            "and the comparison pass gate remain missing"
        ),
        timing_distribution={"scope": "not_timed"},
        raw_outputs={
            "analytic_report": Path(analytic_report_path).as_posix(),
            "mabd_report": Path(mabd_report_path).as_posix(),
            "rbd_report": Path(rbd_report_path).as_posix(),
        },
        plot_paths={},
        source_commit=source_commit,
        vendored_newton_commit=vendored_newton_commit,
        paper_source_version=paper_source_version,
    )
    write_claim_report(report, path)
    return report


def write_t_handle_comparison_report(
    path: str | Path,
    *,
    config: THandleRunConfig,
    rk4_report_path: str | Path,
    mabd_report_path: str | Path,
    source_commit: str,
    vendored_newton_commit: str,
    figure_curve_report_path: str | Path | None = None,
    paper_source_version: str = "2603.08079v2",
) -> ClaimReport:
    rk4_report = _require_t_handle_lane_report(
        rk4_report_path,
        config=config,
        lane="rbd_rk4_reference",
    )
    mabd_report = _require_t_handle_lane_report(
        mabd_report_path,
        config=config,
        lane="mabd_newton",
    )
    figure_report = _valid_t_handle_figure_report_or_none(
        figure_curve_report_path,
        config=config,
    )
    figure_reference_available = figure_report is not None
    axis_index = config.reference.intermediate_axis_index
    sample_diagnostics = _t_handle_sample_index_differences(
        rk4_report,
        mabd_report,
        axis_index=axis_index,
        max_sample_time_delta_s=config.comparison.thresholds["max_sample_time_delta_s"],
    )
    rk4_rows = _t_handle_sample_rows(rk4_report)
    mabd_rows = _t_handle_sample_rows(mabd_report)
    rk4_flip_time = _t_handle_first_sample_grid_flip_time(
        rk4_rows,
        axis_index=axis_index,
    )
    mabd_flip_time = _t_handle_first_sample_grid_flip_time(
        mabd_rows,
        axis_index=axis_index,
    )
    flip_delta = (
        _finite_difference(mabd_flip_time, rk4_flip_time)
        if mabd_flip_time is not None and rk4_flip_time is not None
        else None
    )
    rk4_energy_drift = _finite_scalar(rk4_report.observed.get("relative_energy_drift"))
    mabd_energy_drift = _finite_scalar(mabd_report.observed.get("relative_energy_drift"))
    energy_drift_delta = (
        _finite_difference(mabd_energy_drift, rk4_energy_drift)
        if mabd_energy_drift is not None and rk4_energy_drift is not None
        else None
    )
    blocking_reasons = [
        "exact_t_handle_geometry_unknown",
        "raw_t_handle_reference_curve_data_missing",
        "mabd_newton_report_incomplete",
        "t_handle_comparison_report_incomplete",
        "t_handle_timing_evidence_missing",
        "t_handle_comparison_pass_gate_not_enabled",
    ]
    if sample_diagnostics["matched_sample_index_count"] == 0:
        blocking_reasons.append("sample_index_alignment_missing")
    if sample_diagnostics["time_grid_mismatch"]:
        blocking_reasons.append("sample_time_grid_mismatch")
    if sample_diagnostics["time_aligned_sample_count"] == 0:
        blocking_reasons.append("time_aligned_waveform_samples_missing")
    if sample_diagnostics["sample_index_duplicate"]:
        blocking_reasons.append("duplicate_sample_indices")
    if sample_diagnostics["nonfinite"]:
        blocking_reasons.append("nonfinite_sample_values")
    if flip_delta is None:
        blocking_reasons.append("sample_grid_flip_delta_unavailable")
    if rk4_energy_drift is None or mabd_energy_drift is None:
        blocking_reasons.append("energy_drift_nonfinite")
    if figure_reference_available:
        blocking_reasons.append("t_handle_digitized_figure_curve_agreement_not_passed")

    input_report_provenance = {
        "rbd_rk4_reference": _t_handle_lane_provenance(
            rk4_report_path,
            rk4_report,
        ),
        "mabd_newton": _t_handle_lane_provenance(
            mabd_report_path,
            mabd_report,
        ),
    }
    raw_outputs = {
        "rk4_report": Path(rk4_report_path).as_posix(),
        "mabd_report": Path(mabd_report_path).as_posix(),
    }
    figure_sample_counts: dict[str, dict[str, int]] = {}
    if figure_reference_available and figure_report is not None and figure_curve_report_path is not None:
        input_report_provenance["paper_figure_curves"] = _t_handle_lane_provenance(
            figure_curve_report_path,
            figure_report,
        )
        raw_outputs["figure_curve_report"] = Path(figure_curve_report_path).as_posix()
        figure_sample_counts = _t_handle_figure_sample_counts(figure_report)

    observed = {
        "full_experiment_claim_passed": False,
        "digitized_figure_reference_available": figure_reference_available,
        "digitized_figure_reference_samples": figure_sample_counts,
        "lane_statuses": {
            "rbd_rk4_reference": rk4_report.status.value,
            "mabd_newton": mabd_report.status.value,
        },
        "lane_observed_statuses": {
            "rbd_rk4_reference": rk4_report.observed.get("lane_status"),
            "mabd_newton": mabd_report.observed.get("lane_status"),
        },
        "lane_solver_modes": {
            "rbd_rk4_reference": rk4_report.solver_mode,
            "mabd_newton": mabd_report.solver_mode,
        },
        "input_report_provenance": input_report_provenance,
        "lane_metrics": {
            "rbd_rk4_reference": _t_handle_metric_snapshot(rk4_report),
            "mabd_newton": _t_handle_metric_snapshot(mabd_report),
        },
        "paper_metric_statuses": _t_handle_paper_metric_statuses(
            sample_diagnostics,
            flip_delta=flip_delta,
            digitized_figure_reference_available=figure_reference_available,
        ),
        "missing_required_lanes": [],
        "missing_paper_metrics": [
            "flip_timing_error:raw_paper_timing_missing",
            "intermediate_axis_angular_velocity_waveform:raw_paper_curve_missing",
            "energy_loss:paper_energy_loss_metric_unavailable",
        ],
        "blocking_reasons": blocking_reasons,
        "intermediate_axis_index": axis_index,
        "intermediate_axis_component": _t_handle_axis_component(axis_index),
        "rk4_sample_count": sample_diagnostics["rk4_sample_count"],
        "mabd_sample_count": sample_diagnostics["mabd_sample_count"],
        "matched_sample_index_count": sample_diagnostics["matched_sample_index_count"],
        "finite_matched_sample_count": sample_diagnostics["finite_matched_sample_count"],
        "time_aligned_sample_count": sample_diagnostics["time_aligned_sample_count"],
        "unmatched_rk4_samples": sample_diagnostics["unmatched_rk4_samples"],
        "unmatched_mabd_samples": sample_diagnostics["unmatched_mabd_samples"],
        "duplicate_rk4_sample_indices": sample_diagnostics["duplicate_rk4_sample_indices"],
        "duplicate_mabd_sample_indices": sample_diagnostics["duplicate_mabd_sample_indices"],
        "sample_index_differences": sample_diagnostics["sample_index_differences"],
        "max_sample_time_delta_s": sample_diagnostics["max_sample_time_delta_s"],
        "max_abs_angular_velocity_delta_rad_s": sample_diagnostics[
            "max_abs_angular_velocity_delta_rad_s"
        ],
        "intermediate_axis_waveform_rmse_rad_s": sample_diagnostics[
            "intermediate_axis_waveform_rmse_rad_s"
        ],
        "time_grid_mismatch": sample_diagnostics["time_grid_mismatch"],
        "sample_index_duplicate": sample_diagnostics["sample_index_duplicate"],
        "sample_nonfinite": sample_diagnostics["nonfinite"],
        "flip_timing_diagnostics": {
            "axis_index": axis_index,
            "axis_component": _t_handle_axis_component(axis_index),
            "method": "sample_grid_linear_interpolation",
            "rk4_first_sample_grid_flip_time_s": rk4_flip_time,
            "mabd_first_sample_grid_flip_time_s": mabd_flip_time,
            "mabd_minus_rk4_flip_time_s": flip_delta,
            "rk4_status": (
                "sample_grid_flip_available"
                if rk4_flip_time is not None
                else "sample_grid_flip_unavailable"
            ),
            "mabd_status": (
                "sample_grid_flip_available"
                if mabd_flip_time is not None
                else "sample_grid_flip_unavailable"
            ),
            "comparison_status": (
                "sample_grid_flip_delta_available"
                if flip_delta is not None
                else "sample_grid_flip_delta_unavailable"
            ),
            "limitation": "sample-grid interpolation only; not RK4 step-resolution or paper timing",
        },
        "energy_drift_diagnostics": {
            "rk4_relative_energy_drift": rk4_energy_drift,
            "mabd_relative_energy_drift": mabd_energy_drift,
            "mabd_minus_rk4_relative_energy_drift": energy_drift_delta,
            "limitation": "signed relative_energy_drift diagnostic, not paper energy_loss",
        },
    }
    report = ClaimReport(
        claim_id=config.claim_id,
        scene_id=config.scene_id,
        asset_hashes={"t_handle_procedural": "not_applicable_procedural"},
        solver_mode="t_handle_multilane_comparison_development",
        backend="report_protocol",
        baseline_lane="t_handle_comparison_protocol",
        expected={
            "paper_claim_status": (
                "formal RK4 and M-ABD diagnostic lanes are present, but paper "
                "geometry, raw waveform curves, timing evidence, and the "
                "comparison pass gate remain required"
            ),
            "required_lanes": list(config.comparison.required_lanes),
            "required_metrics": list(T_HANDLE_REQUIRED_METRICS),
            "source_lines": list(config.source_lines),
            "paper_values": config.paper_values,
            "known_source_gaps": [
                "exact_t_handle_geometry_unknown",
                "raw_t_handle_reference_curve_data_missing",
                "paper_timing_curve_unavailable",
            ],
            "full_experiment_claim_passed": False,
        },
        observed=observed,
        threshold=config.comparison.thresholds,
        unit="json_report",
        status=EvidenceStatus.INCOMPLETE,
        failure_reason=(
            "T-handle comparison protocol is incomplete because exact geometry, "
            "raw paper waveform data, paper timing evidence, the MABD lane pass, "
            "and the comparison pass gate remain missing"
        ),
        timing_distribution={"scope": "not_timed", "paper_comparable": False},
        raw_outputs=raw_outputs,
        plot_paths={},
        source_commit=source_commit,
        vendored_newton_commit=vendored_newton_commit,
        paper_source_version=paper_source_version,
    )
    write_claim_report(report, path)
    return report


def write_heavy_top_comparison_report(
    path: str | Path,
    *,
    config: HeavyTopRunConfig,
    rk4_report_path: str | Path,
    mabd_report_path: str | Path,
    figure_curve_report_path: str | Path | None = None,
    source_commit: str,
    vendored_newton_commit: str,
    paper_source_version: str = "2603.08079v2",
) -> ClaimReport:
    rk4_report = _require_heavy_top_lane_report(
        rk4_report_path,
        config=config,
        lane="rbd_rk4_reference",
    )
    mabd_report = _require_heavy_top_lane_report(
        mabd_report_path,
        config=config,
        lane="mabd_newton",
    )
    sample_diagnostics = _heavy_top_sample_index_differences(
        rk4_report,
        mabd_report,
        max_sample_time_delta_s=config.comparison.thresholds["max_sample_time_delta_s"],
    )
    mabd_precession_available = _heavy_top_mabd_precession_velocity_available(mabd_report)
    mabd_energy_available = _finite_scalar(
        mabd_report.observed.get("relative_energy_drift")
    ) is not None
    figure_report = _valid_heavy_top_figure_report_or_none(
        figure_curve_report_path,
        config=config,
    )
    figure_reference_available = figure_report is not None
    missing_paper_metrics = []
    if not mabd_precession_available:
        missing_paper_metrics.append(
            "precession_velocity_error:mabd_precession_velocity_samples_missing"
        )
    if figure_reference_available:
        missing_paper_metrics.append(
            "nutation_angle_error:paper_figure_digitized_curve_agreement_not_passed"
        )
    else:
        missing_paper_metrics.append("nutation_angle_error:paper_reference_curve_missing")
    if not mabd_energy_available:
        missing_paper_metrics.append("energy_drift:mabd_energy_drift_missing")
    blocking_reasons = [
        "exact_heavy_top_inertia_unknown",
        "exact_heavy_top_geometry_unknown",
        "raw_heavy_top_reference_curve_data_missing",
        "mabd_newton_report_incomplete",
        "heavy_top_comparison_report_incomplete",
        "heavy_top_timing_evidence_missing",
        "heavy_top_comparison_pass_gate_not_enabled",
    ]
    if figure_reference_available:
        blocking_reasons.append("heavy_top_digitized_figure_curve_agreement_not_passed")
    if sample_diagnostics["matched_sample_index_count"] == 0:
        blocking_reasons.append("sample_index_alignment_missing")
    if sample_diagnostics["time_grid_mismatch"]:
        blocking_reasons.append("sample_time_grid_mismatch")
    if sample_diagnostics["nonfinite"]:
        blocking_reasons.append("sample_nonfinite")

    observed = {
        "full_experiment_claim_passed": False,
        "lane_statuses": {
            "rbd_rk4_reference": rk4_report.status.value,
            "mabd_newton": mabd_report.status.value,
        },
        "lane_observed_statuses": {
            "rbd_rk4_reference": rk4_report.observed.get("lane_status"),
            "mabd_newton": mabd_report.observed.get("lane_status"),
        },
        "lane_solver_modes": {
            "rbd_rk4_reference": rk4_report.solver_mode,
            "mabd_newton": mabd_report.solver_mode,
        },
        "input_report_provenance": {
            "rbd_rk4_reference": _heavy_top_lane_provenance(
                rk4_report_path,
                rk4_report,
            ),
            "mabd_newton": _heavy_top_lane_provenance(
                mabd_report_path,
                mabd_report,
            ),
        },
        "lane_metrics": {
            "rbd_rk4_reference": _heavy_top_metric_snapshot(
                rk4_report,
                lane="rbd_rk4_reference",
            ),
            "mabd_newton": _heavy_top_metric_snapshot(
                mabd_report,
                lane="mabd_newton",
            ),
        },
        "paper_metric_statuses": {
            "precession_velocity_error": {
                "status": (
                    "diagnostic_available"
                    if mabd_precession_available
                    else "missing_mabd_precession_velocity_samples"
                ),
                "rk4_field": "max_abs_precession_velocity_rad_s",
                "mabd_field": (
                    "precession_nutation_samples.precession_velocity_rad_s"
                    if mabd_precession_available
                    else None
                ),
            },
            "nutation_angle_error": {
                "status": (
                    "paper_figure_digitized_reference_available"
                    if figure_reference_available
                    else "paper_reference_curve_missing"
                ),
                "rk4_field": "precession_nutation_samples.nutation_angle_deg",
                "mabd_field": "precession_nutation_samples.nutation_angle_deg",
                "paper_figure_field": (
                    "reference_curves.reference_nutation.samples"
                    if figure_reference_available
                    else None
                ),
            },
            "energy_drift": {
                "status": (
                    "diagnostic_available"
                    if mabd_energy_available
                    else "mabd_energy_drift_missing"
                ),
                "rk4_field": "relative_energy_drift",
                "mabd_field": "relative_energy_drift" if mabd_energy_available else None,
            },
        },
        "missing_required_lanes": [],
        "missing_paper_metrics": missing_paper_metrics,
        "blocking_reasons": blocking_reasons,
        "digitized_figure_reference_available": figure_reference_available,
        "rk4_sample_count": sample_diagnostics["rk4_sample_count"],
        "mabd_sample_count": sample_diagnostics["mabd_sample_count"],
        "matched_sample_index_count": sample_diagnostics["matched_sample_index_count"],
        "unmatched_rk4_samples": sample_diagnostics["unmatched_rk4_samples"],
        "unmatched_mabd_samples": sample_diagnostics["unmatched_mabd_samples"],
        "sample_index_differences": sample_diagnostics["sample_index_differences"],
        "max_sample_time_delta_s": sample_diagnostics["max_sample_time_delta_s"],
        "max_abs_nutation_delta_deg": sample_diagnostics["max_abs_nutation_delta_deg"],
        "max_abs_precession_delta_rad": sample_diagnostics["max_abs_precession_delta_rad"],
        "time_grid_mismatch": sample_diagnostics["time_grid_mismatch"],
        "sample_nonfinite": sample_diagnostics["nonfinite"],
    }
    if figure_reference_available and figure_report is not None and figure_curve_report_path is not None:
        observed["input_report_provenance"]["paper_figure_curves"] = _heavy_top_lane_provenance(
            figure_curve_report_path,
            figure_report,
        )
        observed["digitized_figure_reference_samples"] = {
            "nutation": len(
                figure_report.observed["reference_curves"]["reference_nutation"]["samples"]
            ),
            "precession": len(
                figure_report.observed["reference_curves"]["reference_precession"]["samples"]
            ),
        }

    report = ClaimReport(
        claim_id=config.claim_id,
        scene_id=config.scene_id,
        asset_hashes={"heavy_top_procedural": "not_applicable_procedural"},
        solver_mode="heavy_top_multilane_comparison_development",
        backend="report_protocol",
        baseline_lane="heavy_top_comparison_protocol",
        expected={
            "paper_claim_status": (
                "formal RK4 and M-ABD diagnostic lanes are present, but paper "
                "geometry, inertia, raw reference curves, timing evidence, and "
                "the comparison pass gate remain required"
            ),
            "required_lanes": list(config.comparison.required_lanes),
            "required_metrics": list(HEAVY_TOP_REQUIRED_METRICS),
            "source_lines": list(config.source_lines),
            "paper_values": config.paper_values,
            "known_source_gaps": [
                "exact_heavy_top_inertia_unknown",
                "exact_heavy_top_geometry_unknown",
                "raw_heavy_top_reference_curve_data_missing",
            ],
            "full_experiment_claim_passed": False,
        },
        observed=observed,
        threshold=config.comparison.thresholds,
        unit="json_report",
        status=EvidenceStatus.INCOMPLETE,
        failure_reason=(
            "heavy-top comparison protocol is incomplete because paper reference "
            "curves, paper-faithful inertia/geometry, M-ABD energy/precession "
            "comparison metrics, timing evidence, and the comparison pass gate "
            "remain missing"
        ),
        timing_distribution={"scope": "not_timed", "paper_comparable": False},
        raw_outputs={
            "rk4_report": Path(rk4_report_path).as_posix(),
            "mabd_report": Path(mabd_report_path).as_posix(),
            **(
                {"figure_curve_report": Path(figure_curve_report_path).as_posix()}
                if figure_reference_available and figure_curve_report_path is not None
                else {}
            ),
        },
        plot_paths={},
        source_commit=source_commit,
        vendored_newton_commit=vendored_newton_commit,
        paper_source_version=paper_source_version,
    )
    write_claim_report(report, path)
    return report


__all__ = [
    "HEAVY_TOP_REQUIRED_METRICS",
    "PHYSICAL_PENDULUM_REQUIRED_METRICS",
    "SPINNING_BOX_REQUIRED_METRICS",
    "SPINNING_BOX_REQUIRED_VECTOR_METRICS",
    "T_HANDLE_REQUIRED_METRICS",
    "write_heavy_top_comparison_report",
    "write_physical_pendulum_comparison_report",
    "write_spinning_box_comparison_report",
    "write_t_handle_comparison_report",
]
