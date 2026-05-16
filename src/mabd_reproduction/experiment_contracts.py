"""Machine-checkable experiment and asset contracts for paper evidence."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


class ExperimentMatrixError(ValueError):
    """Raised when experiment evidence contracts are incomplete or inconsistent."""


@dataclass(frozen=True)
class ExperimentEntry:
    claim_id: str
    scene_id: str
    source_lines: tuple[str, ...]
    paper_values: dict[str, Any]
    required_lanes: tuple[str, ...]
    asset_ids: tuple[str, ...]
    metrics: tuple[str, ...]
    reproduction_status: str
    blocking_reasons: tuple[str, ...]
    output_report: str


@dataclass(frozen=True)
class ExperimentMatrix:
    schema_version: int
    experiments: tuple[ExperimentEntry, ...]


@dataclass(frozen=True)
class AssetEntry:
    asset_id: str
    source_type: str
    source_uri: str
    license_status: str
    checksum: str
    reconstruction_status: str
    supports_full_paper_evidence: bool
    notes: str


@dataclass(frozen=True)
class AssetManifest:
    schema_version: int
    assets: tuple[AssetEntry, ...]


def _read_yaml_mapping(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ExperimentMatrixError(f"{path} must contain a YAML mapping")
    return data


def _require_str(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value:
        raise ExperimentMatrixError(f"{key} must be a non-empty string")
    return value


def _require_str_tuple(data: dict[str, Any], key: str) -> tuple[str, ...]:
    value = data.get(key)
    if not isinstance(value, list) or not value or not all(isinstance(item, str) and item for item in value):
        raise ExperimentMatrixError(f"{key} must be a non-empty list of strings")
    return tuple(value)


def _require_mapping(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = data.get(key)
    if not isinstance(value, dict) or not value:
        raise ExperimentMatrixError(f"{key} must be a non-empty mapping")
    return dict(value)


def _require_schema_version(data: dict[str, Any], path: Path) -> int:
    version = data.get("schema_version")
    if version != 1:
        raise ExperimentMatrixError(f"{path} schema_version must be 1")
    return int(version)


def _entry_from_mapping(data: Any) -> ExperimentEntry:
    if not isinstance(data, dict):
        raise ExperimentMatrixError("experiment entries must be mappings")
    return ExperimentEntry(
        claim_id=_require_str(data, "claim_id"),
        scene_id=_require_str(data, "scene_id"),
        source_lines=_require_str_tuple(data, "source_lines"),
        paper_values=_require_mapping(data, "paper_values"),
        required_lanes=_require_str_tuple(data, "required_lanes"),
        asset_ids=_require_str_tuple(data, "asset_ids"),
        metrics=_require_str_tuple(data, "metrics"),
        reproduction_status=_require_str(data, "reproduction_status"),
        blocking_reasons=tuple(data.get("blocking_reasons") or ()),
        output_report=_require_str(data, "output_report"),
    )


def load_experiment_matrix(path: str | Path) -> ExperimentMatrix:
    matrix_path = Path(path)
    data = _read_yaml_mapping(matrix_path)
    experiments = data.get("experiments")
    if not isinstance(experiments, list) or not experiments:
        raise ExperimentMatrixError("experiments must be a non-empty list")
    return ExperimentMatrix(
        schema_version=_require_schema_version(data, matrix_path),
        experiments=tuple(_entry_from_mapping(entry) for entry in experiments),
    )


def _asset_from_mapping(data: Any) -> AssetEntry:
    if not isinstance(data, dict):
        raise ExperimentMatrixError("asset entries must be mappings")
    return AssetEntry(
        asset_id=_require_str(data, "asset_id"),
        source_type=_require_str(data, "source_type"),
        source_uri=_require_str(data, "source_uri"),
        license_status=_require_str(data, "license_status"),
        checksum=_require_str(data, "checksum"),
        reconstruction_status=_require_str(data, "reconstruction_status"),
        supports_full_paper_evidence=bool(data.get("supports_full_paper_evidence")),
        notes=_require_str(data, "notes"),
    )


def load_asset_manifest(path: str | Path) -> AssetManifest:
    manifest_path = Path(path)
    data = _read_yaml_mapping(manifest_path)
    assets = data.get("assets")
    if not isinstance(assets, list) or not assets:
        raise ExperimentMatrixError("assets must be a non-empty list")
    return AssetManifest(
        schema_version=_require_schema_version(data, manifest_path),
        assets=tuple(_asset_from_mapping(asset) for asset in assets),
    )


def validate_experiment_matrix(matrix: ExperimentMatrix, paper_claims: list[dict[str, Any]]) -> None:
    experiment_claims = {
        str(claim["claim_id"])
        for claim in paper_claims
        if str(claim.get("claim_id", "")).startswith("experiment.")
    }
    matrix_claims = [entry.claim_id for entry in matrix.experiments]
    duplicate_claims = sorted({claim_id for claim_id in matrix_claims if matrix_claims.count(claim_id) > 1})
    if duplicate_claims:
        raise ExperimentMatrixError("duplicate experiment configs: " + ", ".join(duplicate_claims))
    unknown = sorted(set(matrix_claims) - experiment_claims)
    if unknown:
        raise ExperimentMatrixError("unknown experiment configs: " + ", ".join(unknown))
    missing = sorted(experiment_claims - set(matrix_claims))
    if missing:
        raise ExperimentMatrixError("missing experiment configs: " + ", ".join(missing))

    scene_ids = [entry.scene_id for entry in matrix.experiments]
    duplicate_scenes = sorted({scene_id for scene_id in scene_ids if scene_ids.count(scene_id) > 1})
    if duplicate_scenes:
        raise ExperimentMatrixError("duplicate scene ids: " + ", ".join(duplicate_scenes))

    allowed_statuses = {"planned", "blocked_by_assets", "blocked_by_baselines"}
    for entry in matrix.experiments:
        if entry.reproduction_status not in allowed_statuses:
            raise ExperimentMatrixError(f"{entry.claim_id} has invalid reproduction_status {entry.reproduction_status}")
        if not entry.required_lanes or "mabd_newton" not in entry.required_lanes:
            raise ExperimentMatrixError(f"{entry.claim_id} must include mabd_newton lane")
        if not entry.metrics:
            raise ExperimentMatrixError(f"{entry.claim_id} must define metrics")
        if not entry.source_lines:
            raise ExperimentMatrixError(f"{entry.claim_id} must define source lines")
        if not entry.asset_ids:
            raise ExperimentMatrixError(f"{entry.claim_id} must reference at least one asset")


__all__ = [
    "AssetEntry",
    "AssetManifest",
    "ExperimentEntry",
    "ExperimentMatrix",
    "ExperimentMatrixError",
    "load_asset_manifest",
    "load_experiment_matrix",
    "validate_experiment_matrix",
]
