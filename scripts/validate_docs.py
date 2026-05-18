#!/usr/bin/env python3
"""Validate Phase 0-54 docs and provenance contracts."""

from __future__ import annotations

import json
import os
import subprocess
import hashlib
import tempfile
from pathlib import Path
from typing import Any

import numpy as np
import yaml

from mabd_reproduction.experiment_contracts import (
    ExperimentMatrixError,
    load_asset_manifest,
    load_experiment_matrix,
    validate_experiment_matrix,
)
from mabd_reproduction.experiment_configs import (
    ExperimentRunConfigError,
    load_heavy_top_config,
    load_physical_pendulum_config,
    load_spinning_box_config,
    load_t_handle_config,
    validate_heavy_top_config_against_matrix,
    validate_physical_pendulum_config_against_matrix,
    validate_spinning_box_config_against_matrix,
    validate_t_handle_config_against_matrix,
)
from mabd_reproduction.paper_source_audit import (
    physical_pendulum_geometry_source_audit,
    velocity_semantics_source_audit,
)
from mabd_reproduction.reporting import load_claim_report
from mabd_reproduction.heavy_top_mabd import (
    NEWTON_MODEL_DERIVED_CONFIG_SOURCE,
    NEWTON_MODEL_DERIVED_CUSTOM_FREQUENCIES,
    roll_out_heavy_top_mabd_model_derived,
)
from mabd_reproduction.heavy_top_reference import roll_out_heavy_top_rk4_reference
from mabd_reproduction.heavy_top_digitization import (
    EXPECTED_RENDERED_SIZE_PX,
    HEAVY_TOP_FIGURE_PDF,
    HEAVY_TOP_FIGURE_PDF_SHA256,
    RENDER_DPI,
)
from mabd_reproduction.spinning_box_physics import (
    spinning_box_contact_diagnostics,
    spinning_box_kinematic_feasibility,
    spinning_box_mabd_mass_diagonal,
)
from mabd_reproduction.t_handle_reference import roll_out_t_handle_rk4_reference


ROOT = Path(__file__).resolve().parents[1]
MABD_PYTHON = Path("/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python")
PAPER_SOURCE_ROOT = Path("/tmp/mabd-paper/source")
REQUIRED_PATHS = (
    "AGENTS.md",
    "LICENSE.md",
    "pyproject.toml",
    "docs/operations/environment.md",
    "docs/reference/claim-boundaries.md",
    "docs/reference/official-artifact-sources.yaml",
    "docs/reference/paper-claims.yaml",
    "docs/records/README.md",
    "docs/records/2026-05-16-phase1-single-body-abd.md",
    "docs/records/2026-05-16-phase2-joints-kkt.md",
    "docs/records/2026-05-16-phase3-topology-solvers.md",
    "docs/records/2026-05-16-phase4-configured-cpu-step.md",
    "docs/records/2026-05-16-phase5-corotated-stiffness.md",
    "docs/records/2026-05-16-phase6-experiment-matrix.md",
    "docs/records/2026-05-16-phase7-joint-limits.md",
    "docs/records/2026-05-16-phase8-environment-readiness.md",
    "docs/records/2026-05-16-phase9-point-contact-forces.md",
    "docs/records/2026-05-16-phase10-actuation-forces.md",
    "docs/records/2026-05-17-phase11-control-row-extraction.md",
    "docs/records/2026-05-17-phase12-single-body-report-lane.md",
    "docs/records/2026-05-17-phase13-configured-spinning-box.md",
    "docs/records/2026-05-17-phase14-experiment-runner.md",
    "docs/records/2026-05-17-phase15-rbd-baseline-lane.md",
    "docs/records/2026-05-17-phase16-spinning-box-comparison-protocol.md",
    "docs/records/2026-05-17-phase17-spinning-box-mabd-paper-metrics.md",
    "docs/records/2026-05-17-phase18-spinning-box-mabd-physical-mass.md",
    "docs/records/2026-05-17-phase19-spinning-box-comparison-finite-metrics.md",
    "docs/records/2026-05-17-phase20-spinning-box-contact-diagnostics.md",
    "docs/records/2026-05-17-phase21-spinning-box-plane-placement.md",
    "docs/records/2026-05-17-phase22-rbd-plane-placement.md",
    "docs/records/2026-05-17-phase23-spinning-box-position-comparison.md",
    "docs/records/2026-05-17-phase24-spinning-box-trajectory-shape-diagnostics.md",
    "docs/records/2026-05-17-phase25-spinning-box-no-polar-material-lane.md",
    "docs/records/2026-05-17-phase26-corotated-material-rhs.md",
    "docs/records/2026-05-17-phase27-rbd-pass-gate.md",
    "docs/records/2026-05-17-phase28-spinning-box-paper-horizon.md",
    "docs/records/2026-05-17-phase29-spinning-box-kinematic-feasibility.md",
    "docs/records/2026-05-17-phase30-velocity-semantics-source-audit.md",
    "docs/records/2026-05-17-phase31-official-artifact-availability.md",
    "docs/records/2026-05-17-phase32-gravity-force-mapping.md",
    "docs/records/2026-05-17-phase33-physical-pendulum-analytic-reference.md",
    "docs/records/2026-05-17-phase34-world-anchor-physical-pendulum-mabd.md",
    "docs/records/2026-05-17-phase35-physical-pendulum-rbd-baseline.md",
    "docs/records/2026-05-17-phase36-physical-pendulum-comparison-protocol.md",
    "docs/records/2026-05-17-phase37-physical-pendulum-mabd-newton-lane.md",
    "docs/records/2026-05-17-phase39-physical-pendulum-timing-source-audit.md",
    "docs/records/2026-05-17-phase40-physical-pendulum-joint-force-reference.md",
    "docs/records/2026-05-17-phase41-physical-pendulum-geometry-source-audit.md",
    "docs/records/2026-05-17-phase42-spinning-box-report-artifacts.md",
    "docs/records/2026-05-18-phase43-t-handle-rk4-reference.md",
    "docs/records/2026-05-18-phase44-solver-model-config.md",
    "docs/records/2026-05-18-phase45-model-constraint-config.md",
    "docs/records/2026-05-18-phase46-model-world-constraints.md",
    "docs/records/2026-05-18-phase47-model-gravity-config.md",
    "docs/records/2026-05-18-phase48-physical-pendulum-model-lane.md",
    "docs/records/2026-05-18-phase49-heavy-top-rk4-reference.md",
    "docs/records/2026-05-18-phase50-heavy-top-mabd-newton-lane.md",
    "docs/records/2026-05-18-phase51-heavy-top-comparison-protocol.md",
    "docs/records/2026-05-18-phase52-heavy-top-mabd-metrics.md",
    "docs/records/2026-05-18-phase53-heavy-top-figure-curves.md",
    "docs/records/2026-05-18-phase54-environment-clone-contract.md",
    "docs/superpowers/specs/2026-05-17-phase31-official-artifact-availability-design.md",
    "docs/superpowers/plans/2026-05-17-mabd-phase31-official-artifact-availability.md",
    "docs/superpowers/specs/2026-05-17-phase32-gravity-force-mapping-design.md",
    "docs/superpowers/plans/2026-05-17-mabd-phase32-gravity-force-mapping.md",
    "docs/superpowers/specs/2026-05-17-phase33-physical-pendulum-analytic-reference-design.md",
    "docs/superpowers/plans/2026-05-17-mabd-phase33-physical-pendulum-analytic-reference.md",
    "docs/superpowers/specs/2026-05-17-phase34-world-anchor-physical-pendulum-mabd-design.md",
    "docs/superpowers/plans/2026-05-17-mabd-phase34-world-anchor-physical-pendulum-mabd.md",
    "docs/superpowers/specs/2026-05-17-phase35-physical-pendulum-rbd-baseline-design.md",
    "docs/superpowers/plans/2026-05-17-mabd-phase35-physical-pendulum-rbd-baseline.md",
    "docs/superpowers/specs/2026-05-17-phase36-physical-pendulum-comparison-protocol-design.md",
    "docs/superpowers/plans/2026-05-17-mabd-phase36-physical-pendulum-comparison-protocol.md",
    "docs/superpowers/specs/2026-05-17-phase37-physical-pendulum-mabd-newton-lane-design.md",
    "docs/superpowers/plans/2026-05-17-mabd-phase37-physical-pendulum-mabd-newton-lane.md",
    "docs/superpowers/specs/2026-05-17-phase39-physical-pendulum-timing-source-audit-design.md",
    "docs/superpowers/plans/2026-05-17-mabd-phase39-physical-pendulum-timing-source-audit.md",
    "docs/superpowers/specs/2026-05-17-phase40-physical-pendulum-joint-force-reference-design.md",
    "docs/superpowers/plans/2026-05-17-mabd-phase40-physical-pendulum-joint-force-reference.md",
    "docs/superpowers/specs/2026-05-17-phase41-physical-pendulum-geometry-source-audit-design.md",
    "docs/superpowers/plans/2026-05-17-mabd-phase41-physical-pendulum-geometry-source-audit.md",
    "docs/superpowers/specs/2026-05-17-phase42-spinning-box-report-artifacts-design.md",
    "docs/superpowers/plans/2026-05-17-mabd-phase42-spinning-box-report-artifacts.md",
    "docs/superpowers/specs/2026-05-18-phase43-t-handle-rk4-reference-design.md",
    "docs/superpowers/plans/2026-05-18-mabd-phase43-t-handle-rk4-reference.md",
    "docs/superpowers/specs/2026-05-18-phase44-solver-model-config-design.md",
    "docs/superpowers/plans/2026-05-18-mabd-phase44-solver-model-config.md",
    "docs/superpowers/specs/2026-05-18-phase45-model-constraint-config-design.md",
    "docs/superpowers/plans/2026-05-18-mabd-phase45-model-constraint-config.md",
    "docs/superpowers/specs/2026-05-18-phase46-model-world-constraints-design.md",
    "docs/superpowers/plans/2026-05-18-mabd-phase46-model-world-constraints.md",
    "docs/superpowers/specs/2026-05-18-phase47-model-gravity-config-design.md",
    "docs/superpowers/plans/2026-05-18-mabd-phase47-model-gravity-config.md",
    "docs/superpowers/specs/2026-05-18-phase48-physical-pendulum-model-lane-design.md",
    "docs/superpowers/plans/2026-05-18-mabd-phase48-physical-pendulum-model-lane.md",
    "docs/superpowers/specs/2026-05-18-phase49-heavy-top-rk4-reference-design.md",
    "docs/superpowers/plans/2026-05-18-mabd-phase49-heavy-top-rk4-reference.md",
    "docs/superpowers/specs/2026-05-18-phase50-heavy-top-mabd-newton-lane-design.md",
    "docs/superpowers/plans/2026-05-18-mabd-phase50-heavy-top-mabd-newton-lane.md",
    "docs/superpowers/specs/2026-05-18-phase51-heavy-top-comparison-protocol-design.md",
    "docs/superpowers/plans/2026-05-18-mabd-phase51-heavy-top-comparison-protocol.md",
    "docs/superpowers/specs/2026-05-18-phase52-heavy-top-mabd-metrics-design.md",
    "docs/superpowers/plans/2026-05-18-mabd-phase52-heavy-top-mabd-metrics.md",
    "docs/superpowers/specs/2026-05-18-phase53-heavy-top-figure-curve-digitization-design.md",
    "docs/superpowers/plans/2026-05-18-mabd-phase53-heavy-top-figure-curves.md",
    "docs/superpowers/specs/2026-05-18-phase54-environment-clone-contract.md",
    "docs/superpowers/plans/2026-05-18-phase54-environment-clone-contract.md",
    "reports/experiment_matrix/single_body_spinning_box.json",
    "reports/experiment_matrix/single_body_spinning_box_paper_horizon.json",
    "reports/experiment_matrix/single_body_spinning_box_rbd_baseline.json",
    "reports/experiment_matrix/single_body_spinning_box_comparison.json",
    "reports/experiment_matrix/single_body_physical_pendulum_analytic_reference.json",
    "reports/experiment_matrix/single_body_physical_pendulum_mabd_development.json",
    "reports/experiment_matrix/single_body_physical_pendulum_mabd_newton.json",
    "reports/experiment_matrix/single_body_physical_pendulum_rbd_baseline.json",
    "reports/experiment_matrix/single_body_physical_pendulum_comparison.json",
    "reports/experiment_matrix/single_body_t_handle_rk4_reference.json",
    "reports/experiment_matrix/single_body_heavy_top_rk4_reference.json",
    "reports/experiment_matrix/single_body_heavy_top_mabd_newton.json",
    "reports/experiment_matrix/single_body_heavy_top_figure_curves.json",
    "reports/experiment_matrix/single_body_heavy_top_comparison.json",
    "reports/README.md",
    "assets/manifests/README.md",
    "assets/manifests/paper_asset_sources.yaml",
    "configs/experiments/README.md",
    "configs/experiments/paper_experiment_matrix.yaml",
    "configs/experiments/single_body_physical_pendulum.yaml",
    "configs/experiments/single_body_heavy_top.yaml",
    "configs/experiments/single_body_spinning_box.yaml",
    "configs/experiments/single_body_t_handle.yaml",
    "scripts/run_experiment.py",
    "scripts/env/readiness_check.py",
    "scripts/env/clone_from_reference.py",
    "src/mabd_reproduction/environment_clone.py",
    "tests/test_environment_clone.py",
    "tests/test_environment_readiness.py",
    "vendor/newton/PROVENANCE.md",
    "vendor/newton/LICENSE.md",
    "vendor/newton/newton/solvers.py",
)
STATUS_VALUES = {
    "intended",
    "passed",
    "failed",
    "incomplete",
    "not_verified",
    "unsupported",
    "qualitative_reconstruction",
}
VENDORED_NEWTON_COMMIT = "96713fa965463b69c229a4d30582c733ff3526bb"
PHASE44_REFERENCE_PYTHON = Path(
    "/cpfs/user/zhuzihou/conda-managed/envs/physics-primitive-newton-py310/bin/python"
)
PHASE44_CORE_ENV_PACKAGES = ("numpy", "PyYAML", "warp-lang", "ruff", "pytest")
PHYSICAL_PENDULUM_TIMING_SOURCE_LINES = [
    "/tmp/mabd-paper/source/sections/experiment.tex:77-91"
]
PHYSICAL_PENDULUM_TIMING_AUDIT_STATUS = "not_a_physical_pendulum_paper_metric"
PLACEHOLDER_SOURCE_COMMITS = {
    "test-source",
    "phase36-working-tree",
    "phase37-working-tree",
    "phase39-working-tree",
    "phase40-working-tree",
    "phase41-working-tree",
    "phase42-working-tree",
    "phase43-working-tree",
    "phase44-working-tree",
    "pending branch-local",
    "<implementation-commit>",
    "TO_BE_BACKFILLED_PHASE39",
    "TO_BE_BACKFILLED_PHASE40",
    "TO_BE_BACKFILLED_PHASE41",
    "TO_BE_BACKFILLED_PHASE42",
    "TO_BE_BACKFILLED_PHASE43",
    "TO_BE_BACKFILLED_PHASE44",
    "TO_BE_BACKFILLED_PHASE49",
    "TO_BE_BACKFILLED_PHASE51",
    "phase51-working-tree",
    "TO_BE_BACKFILLED_PHASE52",
    "phase52-working-tree",
    "TO_BE_BACKFILLED_PHASE53",
    "phase53-working-tree",
}


def fail(message: str) -> None:
    raise SystemExit(f"validate_docs.py: {message}")


def validate_physical_pendulum_timing_source_audit(payload: Any, context: str) -> None:
    if not isinstance(payload, dict):
        fail(f"{context} paper_timing_source_audit must be a mapping")
    if payload.get("source_lines") != PHYSICAL_PENDULUM_TIMING_SOURCE_LINES:
        fail(f"{context} paper_timing_source_audit source_lines changed")
    if payload.get("status") != PHYSICAL_PENDULUM_TIMING_AUDIT_STATUS:
        fail(f"{context} paper_timing_source_audit status changed")
    if payload.get("runtime_timing_claim_present") is not False:
        fail(f"{context} paper_timing_source_audit must record no runtime timing claim")
    if payload.get("required_metric") is not False:
        fail(f"{context} paper_timing_source_audit must record required_metric=false")
    finding = str(payload.get("finding", "")).lower()
    if "no runtime timing" not in finding or "physical-pendulum source lines" not in finding:
        fail(f"{context} paper_timing_source_audit finding changed")


def read_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        fail(f"{path} must contain a YAML mapping")
    return data


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def claim_boundary_bullet(text: str, starts_with: str) -> str:
    parts: list[str] = []
    capturing = False
    for line in text.splitlines():
        if line.startswith("- "):
            if capturing:
                break
            bullet = line[2:].strip()
            if bullet.startswith(starts_with):
                capturing = True
                parts.append(bullet)
            continue
        if capturing:
            if line.startswith("  "):
                parts.append(line.strip())
            elif line.strip():
                break
    if not parts:
        fail(f"claim-boundaries.md missing bullet starting with: {starts_with}")
    return " ".join(parts)


def require_paths() -> None:
    missing = [path for path in REQUIRED_PATHS if not (ROOT / path).exists()]
    if missing:
        fail("missing required paths: " + ", ".join(missing))
    if (ROOT / "vendor/newton/.git").exists():
        fail("vendor/newton must not contain an embedded .git directory")


def validate_environment_contract() -> None:
    if not MABD_PYTHON.exists():
        fail(f"dedicated M-ABD Python does not exist: {MABD_PYTHON}")
    text = (ROOT / "docs/operations/environment.md").read_text(encoding="utf-8")
    for snippet in (
        str(MABD_PYTHON),
        "mabd-newton-py310",
        "physics-primitive-newton-py310",
        "Non-Pollution Rule",
        "rsync -a --delete",
        "readiness_check.py",
        "reports/generated/environment-readiness/local/readiness.json",
        "smoke_passed",
        "Clone And Sync Maintenance",
        "scripts/env/clone_from_reference.py --dry-run",
        "target_exists",
        "ready_to_clone",
        "--sync-existing",
        "mutates_reference_environment=false",
        "uses_reference_python=false",
        "uses_ambient_python=false",
    ):
        if snippet not in text:
            fail(f"environment.md missing {snippet}")


def validate_claim_boundaries() -> None:
    text = (ROOT / "docs/reference/claim-boundaries.md").read_text(encoding="utf-8")
    normalized_text = " ".join(text.split())
    for placeholder in ("TO_BE_BACKFILLED_PHASE31", "pending branch-local"):
        if placeholder in text:
            fail("claim-boundaries.md contains stale Phase 31 placeholder")
    if "TO_BE_BACKFILLED_PHASE32" in text:
        fail("claim-boundaries.md contains stale Phase 32 placeholder")
    if "TO_BE_BACKFILLED_PHASE33" in text:
        fail("claim-boundaries.md contains stale Phase 33 placeholder")
    if "TO_BE_BACKFILLED_PHASE34" in text:
        fail("claim-boundaries.md contains stale Phase 34 placeholder")
    if "TO_BE_BACKFILLED_PHASE35" in text:
        fail("claim-boundaries.md contains stale Phase 35 placeholder")
    if "TO_BE_BACKFILLED_PHASE36" in text:
        fail("claim-boundaries.md contains stale Phase 36 placeholder")
    if "TO_BE_BACKFILLED_PHASE37" in text:
        fail("claim-boundaries.md contains stale Phase 37 placeholder")
    for heading in ("## Current", "## Intended", "## Verified", "## Forbidden Claims"):
        if heading not in text:
            fail(f"claim-boundaries.md missing {heading}")
    if "No method-level M-ABD result is verified at Phase 0." not in text:
        fail("claim-boundaries.md must explicitly deny Phase 0 method verification")
    if "full FEM rest-stiffness precomputation" not in text:
        fail("claim-boundaries.md must explicitly bound Phase 1 stiffness evidence")
    if "Phase 2 verifies control tetrahedron" not in text:
        fail("claim-boundaries.md must explicitly state Phase 2 joint/KKT evidence")
    if "skew-symmetrized joint-gradient" not in text or "performance path" not in text:
        fail("claim-boundaries.md must bound Phase 2 gradient performance evidence")
    if "Phase 3 verifies chain block-tridiagonal" not in text:
        fail("claim-boundaries.md must explicitly state Phase 3 topology evidence")
    if (
        "tree parent/postorder" not in text
        or "traversal metadata" not in text
        or "paper tree elimination" not in text
    ):
        fail("claim-boundaries.md must bound Phase 3 tree topology evidence")
    if "Phase 3 does not verify `SolverMABD.step()`" not in text:
        fail("claim-boundaries.md must bound Phase 3 step evidence")
    if "Phase 4 verifies explicitly configured CPU oracle `SolverMABD.step()`" not in text:
        fail("claim-boundaries.md must explicitly state Phase 4 configured step evidence")
    if "unconfigured production `SolverMABD.step()`" not in text or "Warp kernels" not in text:
        fail("claim-boundaries.md must bound Phase 4 production step evidence")
    if "Phase 5 verifies linear-elastic rest generalized stiffness `K_A_bar`" not in text:
        fail("claim-boundaries.md must explicitly state Phase 5 corotated stiffness evidence")
    if "co-rotated affine elastic force" not in text or "SingleBodyABDPrecompute.from_linear_elastic_points" not in text:
        fail("claim-boundaries.md must bound Phase 5 material oracle evidence")
    if "Phase 5 does not verify unconfigured production `SolverMABD.step()`" not in text:
        fail("claim-boundaries.md must bound Phase 5 production step evidence")
    if "Phase 6 verifies only that every `experiment.*` paper claim" not in text:
        fail("claim-boundaries.md must explicitly state Phase 6 experiment matrix evidence")
    if "does not verify any scene dynamics" not in text or "external baseline run" not in text:
        fail("claim-boundaries.md must bound Phase 6 scene/baseline evidence")
    if "Phase 7 verifies scalar joint-limit strain clamping" not in text:
        fail("claim-boundaries.md must explicitly state Phase 7 joint-limit evidence")
    if "generic inequality-constrained M-ABD KKT" not in text or "joint-limit parameter extraction from scenes" not in text:
        fail("claim-boundaries.md must bound Phase 7 inequality and scene evidence")
    if "Phase 8 verifies the cloned M-ABD Newton environment contract" not in text:
        fail("claim-boundaries.md must explicitly state Phase 8 environment readiness evidence")
    if "Phase 8 does not verify solver behavior" not in text or "paper experiments" not in text:
        fail("claim-boundaries.md must bound Phase 8 solver and experiment evidence")
    if "Phase 9 verifies point-load affine generalized force mapping" not in text:
        fail("claim-boundaries.md must explicitly state Phase 9 point force evidence")
    phase9_non_claims = (
        "Phase 9 does not verify collision detection",
        "broadphase",
        "narrowphase",
        "friction",
        "full contact handling",
        "production `SolverMABD.step()` contact input",
        "actuation/controller behavior",
        "paper scenes",
        "timing",
        "comparative baselines",
    )
    for snippet in phase9_non_claims:
        if snippet not in normalized_text:
            fail(f"claim-boundaries.md must bound Phase 9 contact evidence: {snippet}")
    if "Phase 10 verifies scene-script affine target" not in text:
        fail("claim-boundaries.md must explicitly state Phase 10 actuation evidence")
    phase10_non_claims = (
        "Phase 10 does not verify Newton `Control` object ingestion",
        "robot inverse kinematics",
        "Franka pick-and-place",
        "contact-rich grasping",
        "wind/aerodynamic scene dynamics",
        "closed-loop controllers",
        "GPU/Warp control kernels",
        "timing",
        "paper scenes",
        "comparative baselines",
    )
    for snippet in phase10_non_claims:
        if snippet not in normalized_text:
            fail(f"claim-boundaries.md must bound Phase 10 actuation evidence: {snippet}")
    if "Phase 11 verifies extraction of enabled Newton `mabd:control` model rows" not in text:
        fail("claim-boundaries.md must explicitly state Phase 11 control-row extraction evidence")
    phase11_non_claims = (
        "Phase 11 does not verify Newton `Control` object ingestion",
        "time-varying controller updates",
        "robot inverse kinematics",
        "Franka pick-and-place",
        "contact-rich grasping",
        "paper scenes",
        "timing",
        "comparative baselines",
    )
    for snippet in phase11_non_claims:
        if snippet not in normalized_text:
            fail(f"claim-boundaries.md must bound Phase 11 control extraction evidence: {snippet}")
    if "Phase 12 verifies full-schema `ClaimReport` JSON round trips" not in text:
        fail("claim-boundaries.md must explicitly state Phase 12 report-lane evidence")
    phase12_non_claims = (
        "Phase 12 does not verify the paper spinning-box experiment",
        "paper timing",
        "RK4/RBD/analytic baselines",
        "rendered output",
        "paper trajectory agreement",
        "any passed `experiment.*` claim",
    )
    for snippet in phase12_non_claims:
        if snippet not in normalized_text:
            fail(f"claim-boundaries.md must bound Phase 12 report-lane evidence: {snippet}")
    if "Phase 13 verifies a config-driven single-body spinning-box" not in text:
        fail("claim-boundaries.md must explicitly state Phase 13 configured-lane evidence")
    phase13_non_claims = (
        "Phase 13 does not verify the paper spinning-box experiment",
        "RBD baselines",
        "paper timing",
        "rendered output",
        "paper trajectory agreement",
        "generated report artifacts as committed evidence",
        "any passed `experiment.*` claim",
    )
    for snippet in phase13_non_claims:
        if snippet not in normalized_text:
            fail(f"claim-boundaries.md must bound Phase 13 configured-lane evidence: {snippet}")
    if "Phase 14 verifies an executable config-driven experiment runner" not in text:
        fail("claim-boundaries.md must explicitly state Phase 14 runner evidence")
    phase14_non_claims = (
        "Phase 14 does not verify the paper spinning-box experiment",
        "RBD baselines",
        "paper timing",
        "rendered output",
        "paper trajectory agreement",
        "any passed `experiment.*` claim",
    )
    for snippet in phase14_non_claims:
        if snippet not in normalized_text:
            fail(f"claim-boundaries.md must bound Phase 14 runner evidence: {snippet}")
    if "Phase 15 verifies a Newton `SolverSemiImplicit` CPU free-rigid" not in text:
        fail("claim-boundaries.md must explicitly state Phase 15 RBD baseline evidence")
    phase15_non_claims = (
        "Phase 15 does not verify the paper spinning-box experiment",
        "paper-faithful implicit RBD baseline",
        "paper-faithful affine collision",
        "RK4 or analytic baselines",
        "paper timing",
        "generated report artifacts as committed evidence",
        "any passed `experiment.*` claim",
    )
    for snippet in phase15_non_claims:
        if snippet not in normalized_text:
            fail(f"claim-boundaries.md must bound Phase 15 RBD baseline evidence: {snippet}")
    if "Phase 16 verifies a machine-checkable spinning-box comparison protocol" not in text:
        fail("claim-boundaries.md must explicitly state Phase 16 comparison protocol evidence")
    phase16_non_claims = (
        "Phase 16 does not verify the paper spinning-box experiment",
        "paper-faithful implicit RBD baseline",
        "paper-faithful affine collision",
        "paper timing",
        "rendered output",
        "paper trajectory agreement",
        "generated report artifacts as committed evidence",
        "any passed `experiment.*` claim",
    )
    for snippet in phase16_non_claims:
        if snippet not in normalized_text:
            fail(f"claim-boundaries.md must bound Phase 16 comparison evidence: {snippet}")
    if "Phase 17 verifies paper-value momentum metric reporting" not in text:
        fail("claim-boundaries.md must explicitly state Phase 17 paper-momentum metric evidence")
    phase17_required = (
        "M-ABD single-body spinning-box development lane",
        "paper p0/L0 parsing",
        "ABD generalized velocity initialization",
        "final spatial twist extraction",
        "linear_momentum_error",
        "angular_momentum_error",
        "comparison protocol",
    )
    for snippet in phase17_required:
        if snippet not in normalized_text:
            fail(f"claim-boundaries.md must describe Phase 17 metric evidence: {snippet}")
    phase17_non_claims = (
        "Phase 17 does not verify the paper spinning-box experiment",
        "paper-faithful implicit RBD baseline",
        "paper-faithful affine collision",
        "paper timing",
        "rendered output",
        "paper trajectory agreement",
        "generated report artifacts as committed evidence",
        "any passed `experiment.*` claim",
    )
    for snippet in phase17_non_claims:
        if snippet not in normalized_text:
            fail(f"claim-boundaries.md must bound Phase 17 paper-momentum evidence: {snippet}")
    if "Phase 18 verifies physical affine mass-diagonal reporting" not in text:
        fail("claim-boundaries.md must explicitly state Phase 18 physical mass evidence")
    phase18_required = (
        "M-ABD single-body spinning-box development lane",
        "paper uniform centered cube",
        "Newton affine packing order",
        "mass_diagonal = [m*s^2/12] * 9 + [m] * 3",
        "initial_energy_j",
        "final_energy_j",
        "relative_energy_drift",
    )
    for snippet in phase18_required:
        if snippet not in normalized_text:
            fail(f"claim-boundaries.md must describe Phase 18 physical mass evidence: {snippet}")
    phase18_non_claims = (
        "Phase 18 does not verify the paper spinning-box experiment",
        "paper-faithful implicit RBD baseline",
        "paper-faithful affine collision",
        "paper timing",
        "rendered output",
        "paper trajectory agreement",
        "generated report artifacts as committed evidence",
        "any passed `experiment.*` claim",
    )
    for snippet in phase18_non_claims:
        if snippet not in normalized_text:
            fail(f"claim-boundaries.md must bound Phase 18 physical mass evidence: {snippet}")
    if "Phase 19 verifies finite required-metric validation" not in text:
        fail("claim-boundaries.md must explicitly state Phase 19 finite metric evidence")
    phase19_required = (
        "spinning-box comparison protocol",
        "invalid_required_metrics",
        "lane_metric_differences",
        "invalid metric blocking reasons",
    )
    for snippet in phase19_required:
        if snippet not in normalized_text:
            fail(f"claim-boundaries.md must describe Phase 19 finite metric evidence: {snippet}")
    phase19_non_claims = (
        "Phase 19 does not verify the paper spinning-box experiment",
        "paper-faithful implicit RBD baseline",
        "paper-faithful affine collision",
        "paper timing",
        "rendered output",
        "paper trajectory agreement",
        "generated report artifacts as committed evidence",
        "any passed `experiment.*` claim",
    )
    for snippet in phase19_non_claims:
        if snippet not in normalized_text:
            fail(f"claim-boundaries.md must bound Phase 19 finite metric evidence: {snippet}")
    phase20_verified = claim_boundary_bullet(text, "Phase 20 verifies")
    phase20_non_claim = claim_boundary_bullet(text, "Phase 20 does not verify")
    if "Phase 20 verifies procedural spinning-box cube corner derivation" not in phase20_verified:
        fail("claim-boundaries.md must explicitly state Phase 20 contact diagnostics evidence")
    phase20_required = (
        "configured frictionless plane metadata",
        "point-plane normal penalty contact diagnostics",
        "finite contact diagnostic fields",
        "M-ABD development lane report",
    )
    for snippet in phase20_required:
        if snippet not in phase20_verified:
            fail(f"claim-boundaries.md must describe Phase 20 contact diagnostics evidence: {snippet}")
    phase20_non_claims = (
        "the paper spinning-box experiment",
        "collision detection",
        "continuous collision detection",
        "friction",
        "implicit contact solve",
        "paper-faithful affine collision",
        "paper-faithful implicit RBD baseline",
        "paper timing",
        "rendered output",
        "paper trajectory agreement",
        "generated report artifacts as committed evidence",
        "any passed `experiment.*` claim",
    )
    for snippet in phase20_non_claims:
        if snippet not in phase20_non_claim:
            fail(f"claim-boundaries.md must bound Phase 20 contact diagnostics evidence: {snippet}")
    phase21_current = claim_boundary_bullet(text, "This repository contains Phase 21")
    phase21_verified = claim_boundary_bullet(text, "Phase 21 verifies")
    phase21_non_claim = claim_boundary_bullet(text, "Phase 21 does not verify")
    if "spinning-box plane-aligned initial placement" not in phase21_current:
        fail("claim-boundaries.md must state Phase 21 current plane-placement evidence")
    phase21_required = (
        "configured spinning-box resting pose",
        "cube side length 0.1m",
        "plane normal [0, 1, 0]",
        "plane offset 0",
        "initial translation y=0.05m",
        "zero initial penetration",
        "zero point-plane penalty contact force fields",
        "M-ABD development lane report",
    )
    for snippet in phase21_required:
        if snippet not in phase21_verified:
            fail(f"claim-boundaries.md must describe Phase 21 plane-placement evidence: {snippet}")
    phase21_non_claims = (
        "the paper spinning-box experiment",
        "collision detection",
        "continuous collision detection",
        "friction",
        "implicit contact solve",
        "gravity",
        "paper-faithful affine collision",
        "paper-faithful implicit RBD baseline",
        "paper timing",
        "rendered output",
        "paper trajectory agreement",
        "generated report artifacts as committed evidence",
        "any passed `experiment.*` claim",
    )
    for snippet in phase21_non_claims:
        if snippet not in phase21_non_claim:
            fail(f"claim-boundaries.md must bound Phase 21 plane-placement evidence: {snippet}")
    phase22_current = claim_boundary_bullet(text, "This repository contains Phase 22")
    phase22_verified = claim_boundary_bullet(text, "Phase 22 verifies")
    phase22_non_claim = claim_boundary_bullet(text, "Phase 22 does not verify")
    if "RBD development baseline configured initial placement" not in phase22_current:
        fail("claim-boundaries.md must state Phase 22 current RBD placement evidence")
    phase22_required = (
        "RBD development baseline consumes the configured spinning-box initial translation",
        "initial_position_m = [0.0, 0.05, 0.0]",
        "final_position_m = [4.0, 0.05, 0.0]",
        "four 10 ms free-body steps at 100 m/s",
        "report propagation for the RBD lane",
    )
    for snippet in phase22_required:
        if snippet not in phase22_verified:
            fail(f"claim-boundaries.md must describe Phase 22 RBD placement evidence: {snippet}")
    phase22_non_claims = (
        "the paper spinning-box experiment",
        "paper-faithful implicit RBD baseline",
        "paper-faithful affine collision",
        "collision detection",
        "continuous collision detection",
        "friction",
        "implicit contact solve",
        "gravity",
        "rendered output",
        "paper timing",
        "paper trajectory agreement",
        "generated report artifacts as committed evidence",
        "any passed `experiment.*` claim",
    )
    for snippet in phase22_non_claims:
        if snippet not in phase22_non_claim:
            fail(f"claim-boundaries.md must bound Phase 22 RBD placement evidence: {snippet}")
    phase23_current = claim_boundary_bullet(text, "This repository contains Phase 23")
    phase23_verified = claim_boundary_bullet(text, "Phase 23 verifies")
    phase23_non_claim = claim_boundary_bullet(text, "Phase 23 does not verify")
    if "spinning-box position comparison metrics" not in phase23_current:
        fail("claim-boundaries.md must state Phase 23 position-comparison evidence")
    phase23_required = (
        "initial_position_m",
        "final_position_m",
        "M-ABD spinning-box development lane",
        "finite length-three vector validation",
        "lane_vector_metrics",
        "invalid_required_vector_metrics",
        "lane_vector_metric_differences",
    )
    for snippet in phase23_required:
        if snippet not in phase23_verified:
            fail(f"claim-boundaries.md must describe Phase 23 position evidence: {snippet}")
    phase23_non_claims = (
        "the paper spinning-box experiment",
        "paper-faithful implicit RBD baseline",
        "paper-faithful affine collision",
        "collision detection",
        "continuous collision detection",
        "friction",
        "implicit contact solve",
        "gravity",
        "rendered output",
        "paper timing",
        "paper trajectory agreement",
        "generated report artifacts as committed evidence",
        "any passed `experiment.*` claim",
    )
    for snippet in phase23_non_claims:
        if snippet not in phase23_non_claim:
            fail(f"claim-boundaries.md must bound Phase 23 position evidence: {snippet}")
    phase24_current = claim_boundary_bullet(text, "This repository contains Phase 24")
    phase24_verified = claim_boundary_bullet(text, "Phase 24 verifies")
    phase24_non_claim = claim_boundary_bullet(text, "Phase 24 does not verify")
    if "trajectory samples" not in phase24_current or "affine shape diagnostics" not in phase24_current:
        fail("claim-boundaries.md must state Phase 24 trajectory/shape evidence")
    phase24_required = (
        "trajectory_samples",
        "M-ABD and RBD",
        "affine matrix",
        "determinant",
        "singular values",
        "affine_orthogonality_error",
        "affine_shape_diagnostic_status = development_gap_observed",
        "RBD `rotation_xyzw`",
    )
    for snippet in phase24_required:
        if snippet not in phase24_verified:
            fail(f"claim-boundaries.md must describe Phase 24 trajectory evidence: {snippet}")
    phase24_non_claims = (
        "the paper spinning-box experiment",
        "paper-faithful implicit RBD baseline",
        "paper-faithful affine collision",
        "collision detection",
        "continuous collision detection",
        "friction",
        "implicit contact solve",
        "gravity",
        "rendered output",
        "paper timing",
        "paper trajectory agreement",
        "generated report artifacts as committed evidence",
        "any passed `experiment.*` claim",
    )
    for snippet in phase24_non_claims:
        if snippet not in phase24_non_claim:
            fail(f"claim-boundaries.md must bound Phase 24 trajectory evidence: {snippet}")
    phase25_current = claim_boundary_bullet(text, "This repository contains Phase 25")
    phase25_verified = claim_boundary_bullet(text, "Phase 25 verifies")
    phase25_non_claim = claim_boundary_bullet(text, "Phase 25 does not verify")
    if "no-polar" not in phase25_current or "paper material stiffness" not in phase25_current:
        fail("claim-boundaries.md must state Phase 25 no-polar/material evidence")
    phase25_required = (
        "unconstrained CPU oracle",
        "rotation_mode = no_polar",
        "mabd_rotation_mode",
        "material_model",
        "material_young_modulus_pa",
        "material_poisson_ratio",
        "material_volume_m3",
        "material_stiffness_trace",
        "material_stiffness_rank",
        "constrained CPU oracle KKT",
        "rotation_mode = none",
        "angular momentum",
        "energy",
        "development gap",
    )
    for snippet in phase25_required:
        if snippet not in phase25_verified:
            fail(f"claim-boundaries.md must describe Phase 25 material evidence: {snippet}")
    phase25_non_claims = (
        "the paper spinning-box experiment",
        "full M-ABD dynamics",
        "multi-body no-polar constraints",
        "paper-faithful implicit RBD baseline",
        "paper-faithful affine collision",
        "collision detection",
        "continuous collision detection",
        "friction",
        "implicit contact solve",
        "gravity",
        "rendered output",
        "paper timing",
        "paper trajectory agreement",
        "generated report artifacts as committed evidence",
        "any passed `experiment.*` claim",
    )
    for snippet in phase25_non_claims:
        if snippet not in phase25_non_claim:
            fail(f"claim-boundaries.md must bound Phase 25 material evidence: {snippet}")
    phase26_current = claim_boundary_bullet(text, "This repository contains Phase 26")
    phase26_verified = claim_boundary_bullet(text, "Phase 26 verifies")
    phase26_non_claim = claim_boundary_bullet(text, "Phase 26 does not verify")
    if "co-rotated material RHS" not in phase26_current or "rotation_mode = polar" not in phase26_current:
        fail("claim-boundaries.md must state Phase 26 co-rotated polar evidence")
    phase26_required = (
        "unconstrained CPU oracle",
        "rotation_mode = polar",
        "pure-rotation zero material strain",
        "co-rotated material force helper",
        "constrained CPU oracle polar rejection",
        "mabd_rotation_mode = polar",
        "material_model = paper_linear_elastic_corotated_development",
        "material_rhs_frame = corotated_local_all_blocks",
        "translation_frame = corotated_polar_all_blocks",
        "report status: `incomplete`",
        "angular momentum",
        "relative energy drift",
        "affine shape",
        "development diagnostics",
    )
    for snippet in phase26_required:
        if snippet not in phase26_verified:
            fail(f"claim-boundaries.md must describe Phase 26 corotated evidence: {snippet}")
    phase26_non_claims = (
        "the paper spinning-box experiment",
        "full M-ABD dynamics",
        "multi-body polar or no-polar constraints",
        "unconfigured production `SolverMABD.step()`",
        "Warp/CUDA/GPU paths",
        "paper ABD-ABA performance",
        "paper-faithful implicit RBD baseline",
        "paper-faithful affine collision",
        "collision detection",
        "continuous collision detection",
        "friction",
        "implicit contact solve",
        "gravity",
        "rendered output",
        "paper timing",
        "paper trajectory agreement",
        "generated report artifacts as committed evidence",
        "any passed `experiment.*` claim",
    )
    for snippet in phase26_non_claims:
        if snippet not in phase26_non_claim:
            fail(f"claim-boundaries.md must bound Phase 26 corotated evidence: {snippet}")
    phase27_current = claim_boundary_bullet(text, "This repository contains Phase 27")
    phase27_verified = claim_boundary_bullet(text, "Phase 27 verifies")
    phase27_non_claim = claim_boundary_bullet(text, "Phase 27 does not verify")
    if "paper-scoped RBD lane gate" not in phase27_current:
        fail("claim-boundaries.md must state Phase 27 RBD lane-gate evidence")
    phase27_required = (
        "top-level report remains `incomplete`",
        "lane_gate_status = passed",
        "paper_faithful_implicit_rbd",
        "cpu_numpy_newton_only",
        "closed-form xyzw quaternion",
        "strict conservation thresholds",
        "comparison protocol consumes the RBD lane gate",
    )
    for snippet in phase27_required:
        if snippet not in phase27_verified:
            fail(f"claim-boundaries.md must describe Phase 27 lane-gate evidence: {snippet}")
    phase27_non_claims = (
        "the paper spinning-box experiment",
        "M-ABD lane pass",
        "spinning-box comparison pass",
        "full M-ABD dynamics",
        "paper-faithful affine collision",
        "collision detection",
        "continuous collision detection",
        "friction",
        "implicit contact solve",
        "gravity",
        "rendered output",
        "paper timing",
        "paper trajectory agreement",
        "generated report artifacts as committed evidence",
        "any passed `experiment.*` claim",
    )
    for snippet in phase27_non_claims:
        if snippet not in phase27_non_claim:
            fail(f"claim-boundaries.md must bound Phase 27 lane-gate evidence: {snippet}")
    phase28_current = claim_boundary_bullet(text, "This repository contains Phase 28")
    phase28_verified = claim_boundary_bullet(text, "Phase 28 verifies")
    phase28_non_claim = claim_boundary_bullet(text, "Phase 28 does not verify")
    phase28_current_required = (
        "paper-horizon M-ABD diagnostic",
        "10 second",
        "h = 1e-2",
        "h = 1e-3",
    )
    for snippet in phase28_current_required:
        if snippet not in phase28_current:
            fail(f"claim-boundaries.md must state Phase 28 paper-horizon evidence: {snippet}")
    phase28_verified_required = (
        "mabd_cpu_oracle_paper_horizon_diagnostic",
        "every-step extrema",
        "threshold_violations",
        "mabd_paper_horizon_status = development_gap_observed",
        "no `lane_gate_status`",
        "report status: `incomplete`",
    )
    for snippet in phase28_verified_required:
        if snippet not in phase28_verified:
            fail(f"claim-boundaries.md must describe Phase 28 paper-horizon evidence: {snippet}")
    phase28_non_claims = (
        "the paper spinning-box experiment",
        "M-ABD lane pass",
        "spinning-box comparison pass",
        "full M-ABD dynamics",
        "paper-faithful affine collision",
        "collision detection",
        "continuous collision detection",
        "friction",
        "implicit contact solve",
        "gravity",
        "rendered output",
        "paper timing",
        "paper trajectory agreement",
        "generated report artifacts as committed evidence",
        "any passed `experiment.*` claim",
    )
    for snippet in phase28_non_claims:
        if snippet not in phase28_non_claim:
            fail(f"claim-boundaries.md must bound Phase 28 paper-horizon evidence: {snippet}")
    phase29_current = claim_boundary_bullet(text, "This repository contains Phase 29")
    phase29_verified = claim_boundary_bullet(text, "Phase 29 verifies")
    phase29_non_claim = claim_boundary_bullet(text, "Phase 29 does not verify")
    phase29_current_required = (
        "spinning-box kinematic feasibility diagnostics",
        "M-ABD paper-horizon report",
    )
    for snippet in phase29_current_required:
        if snippet not in phase29_current:
            fail(f"claim-boundaries.md must state Phase 29 feasibility evidence: {snippet}")
    phase29_verified_required = (
        "paper angular speed 60000",
        "orthogonal finite-difference bounds 100 and 1000 rad/s",
        "momentum bounds 1/6 and 10/6",
        "ratios 600 and 60",
        "paper_momentum_requires_affine_stretch_under_q_delta_over_h",
        "qd_next=(q_next-q_n)/h",
    )
    for snippet in phase29_verified_required:
        if snippet not in phase29_verified:
            fail(f"claim-boundaries.md must describe Phase 29 feasibility evidence: {snippet}")
    phase29_non_claims = (
        "the paper spinning-box experiment",
        "M-ABD lane pass",
        "spinning-box comparison pass",
        "full M-ABD dynamics",
        "solver fix",
        "decoupled velocity semantics",
        "paper-faithful affine collision",
        "contact solve",
        "timing",
        "generated report artifacts as committed evidence",
        "any passed `experiment.*` claim",
    )
    for snippet in phase29_non_claims:
        if snippet not in phase29_non_claim:
            fail(f"claim-boundaries.md must bound Phase 29 feasibility evidence: {snippet}")
    phase30_current = claim_boundary_bullet(text, "This repository contains Phase 30")
    phase30_verified = claim_boundary_bullet(text, "Phase 30 verifies")
    phase30_non_claim = claim_boundary_bullet(text, "Phase 30 does not verify")
    phase30_current_required = (
        "velocity semantics source audit",
        "source_does_not_prove_decoupled_velocity_semantics",
    )
    for snippet in phase30_current_required:
        if snippet not in phase30_current:
            fail(f"claim-boundaries.md must state Phase 30 source-audit evidence: {snippet}")
    phase30_verified_required = (
        "implicit Euler inertia potential",
        "`G(A)` twist mapping",
        "`G(A)^T` wrench mapping",
        "spinning-box twist initialization",
        "source_does_not_specify_decoupled_velocity_semantics",
        "source_does_not_specify_alternative_momentum_extraction",
    )
    for snippet in phase30_verified_required:
        if snippet not in phase30_verified:
            fail(f"claim-boundaries.md must describe Phase 30 source-audit evidence: {snippet}")
    phase30_non_claims = (
        "paper spinning-box experiment",
        "Newton solver modification",
        "decoupled velocity semantics",
        "alternative momentum extraction",
        "M-ABD lane pass",
        "spinning-box comparison pass",
        "paper timing",
        "paper trajectory agreement",
        "any passed `experiment.*` claim",
    )
    for snippet in phase30_non_claims:
        if snippet not in phase30_non_claim:
            fail(f"claim-boundaries.md must bound Phase 30 source-audit evidence: {snippet}")
    phase31_current = claim_boundary_bullet(text, "This repository contains Phase 31")
    phase31_verified = claim_boundary_bullet(text, "Phase 31 verifies")
    phase31_non_claim = claim_boundary_bullet(text, "Phase 31 does not verify")
    phase31_current_required = (
        "official artifact availability audit",
        "official_project_and_video_found_implementation_code_coming_soon_as_of_2026-05-17",
    )
    for snippet in phase31_current_required:
        if snippet not in phase31_current:
            fail(f"claim-boundaries.md must state Phase 31 artifact-audit evidence: {snippet}")
    phase31_verified_required = (
        "arXiv page",
        "SIGGRAPH 2026 schedule page",
        "Minghao Guo author page",
        "first-author homepage data",
        "first-author project page",
        "MINSUGLLY/mabd",
        "Yin Yang author page",
        "GitHub repository search",
        "supplementary video were found",
        "Code (coming soon)",
        "released implementation-code URL",
    )
    for snippet in phase31_verified_required:
        if snippet not in phase31_verified:
            fail(f"claim-boundaries.md must describe Phase 31 artifact-audit evidence: {snippet}")
    phase31_non_claims = (
        "private author-code absence",
        "unpublished implementation-code absence",
        "paper experiment pass",
        "Newton solver modification",
        "M-ABD lane pass",
        "spinning-box comparison pass",
        "paper timing",
        "paper trajectory agreement",
        "any passed `experiment.*` claim",
    )
    for snippet in phase31_non_claims:
        if snippet not in phase31_non_claim:
            fail(f"claim-boundaries.md must bound Phase 31 artifact-audit evidence: {snippet}")
    phase31_forbidden = claim_boundary_bullet(
        text, "Phase 31 project-page/video availability"
    )
    for snippet in (
        "private author code",
        "unpublished implementation code",
        "author-owned solver artifacts do not exist",
    ):
        if snippet not in phase31_forbidden:
            fail(f"claim-boundaries.md must forbid Phase 31 overclaim: {snippet}")
    phase32_current = claim_boundary_bullet(text, "This repository contains Phase 32")
    phase32_verified = claim_boundary_bullet(text, "Phase 32 verifies")
    phase32_non_claim = claim_boundary_bullet(text, "Phase 32 does not verify")
    phase32_current_required = (
        "uniform gravity generalized-force CPU oracle support",
        "Phase 32 record",
    )
    for snippet in phase32_current_required:
        if snippet not in phase32_current:
            fail(f"claim-boundaries.md must state Phase 32 gravity evidence: {snippet}")
    phase32_verified_required = (
        "gravity_generalized_force",
        "J_i^T m_i g",
        "MABDCPUOracleConfig",
        "gravity input",
        "configured unconstrained CPU oracle step",
        "malformed gravity-vector rejection",
        "repo and vendored Newton unit tests",
    )
    for snippet in phase32_verified_required:
        if snippet not in phase32_verified:
            fail(f"claim-boundaries.md must describe Phase 32 gravity evidence: {snippet}")
    phase32_non_claims = (
        "heavy-top scene reproduction",
        "physical-pendulum scene reproduction",
        "analytic or RK4 reference agreement",
        "joints under gravity",
        "contact",
        "collision",
        "friction",
        "implicit contact solve",
        "Warp/CUDA/GPU paths",
        "paper timing",
        "rendered output",
        "any passed `experiment.*` claim",
    )
    for snippet in phase32_non_claims:
        if snippet not in phase32_non_claim:
            fail(f"claim-boundaries.md must bound Phase 32 gravity evidence: {snippet}")
    phase32_forbidden = claim_boundary_bullet(
        text, "Phase 32 gravity generalized-force mapping"
    )
    for snippet in (
        "passed heavy-top",
        "physical-pendulum",
        "paper experiment reproduction",
    ):
        if snippet not in phase32_forbidden:
            fail(f"claim-boundaries.md must forbid Phase 32 overclaim: {snippet}")
    phase33_current = claim_boundary_bullet(text, "This repository contains Phase 33")
    phase33_verified = claim_boundary_bullet(text, "Phase 33 verifies")
    phase33_non_claim = claim_boundary_bullet(text, "Phase 33 does not verify")
    phase33_current_required = (
        "physical-pendulum analytic-reference lane",
        "Phase 33 record",
    )
    for snippet in phase33_current_required:
        if snippet not in phase33_current:
            fail(f"claim-boundaries.md must state Phase 33 analytic-reference evidence: {snippet}")
    phase33_verified_required = (
        "elliptic-reference formula",
        "SciPy CPU analytic lane",
        "physical_pendulum_angle_reference",
        "experiment-matrix validation",
        "`analytic_reference` CLI dispatch",
        "compact angle samples",
        "`lane_status = passed`",
        "top-level report status: `incomplete`",
    )
    for snippet in phase33_verified_required:
        if snippet not in phase33_verified:
            fail(f"claim-boundaries.md must describe Phase 33 analytic-reference evidence: {snippet}")
    phase33_non_claims = (
        "M-ABD physical-pendulum dynamics",
        "RBD implicit baseline dynamics",
        "joint-force waveform agreement",
        "pendulum geometry",
        "contact",
        "collision",
        "rendered output",
        "paper timing",
        "full physical-pendulum experiment",
        "any passed `experiment.*` claim",
    )
    for snippet in phase33_non_claims:
        if snippet not in phase33_non_claim:
            fail(f"claim-boundaries.md must bound Phase 33 analytic-reference evidence: {snippet}")
    phase33_forbidden = claim_boundary_bullet(
        text, "Phase 33 analytic-reference lane status"
    )
    for snippet in (
        "passed physical-pendulum experiment",
        "M-ABD dynamics result",
        "RBD baseline result",
        "joint-force agreement result",
    ):
        if snippet not in phase33_forbidden:
            fail(f"claim-boundaries.md must forbid Phase 33 overclaim: {snippet}")
    phase34_current = claim_boundary_bullet(text, "This repository contains Phase 34")
    phase34_verified = claim_boundary_bullet(text, "Phase 34 verifies")
    phase34_non_claim = claim_boundary_bullet(text, "Phase 34 does not verify")
    phase34_current_required = (
        "world-anchor CPU-oracle support",
        "physical-pendulum M-ABD development diagnostic lane",
        "Phase 34 record",
    )
    for snippet in phase34_current_required:
        if snippet not in phase34_current:
            fail(f"claim-boundaries.md must state Phase 34 M-ABD diagnostic evidence: {snippet}")
    phase34_verified_required = (
        "MABDCPUOracleWorldConstraint",
        "dense-only topology gating",
        "malformed vector rejection",
        "mabd_development",
        "`physical_pendulum_mabd_development` CLI dispatch",
        "`physical_pendulum_mabd_development_diagnostic` report lane id",
        "compact angle samples",
        "`lane_status = development_diagnostic_generated`",
        "top-level report status: `incomplete`",
    )
    for snippet in phase34_verified_required:
        if snippet not in phase34_verified:
            fail(f"claim-boundaries.md must describe Phase 34 M-ABD diagnostic evidence: {snippet}")
    phase34_non_claims = (
        "full physical-pendulum experiment",
        "paper-faithful pendulum geometry",
        "RBD implicit baseline dynamics",
        "joint-force waveform agreement",
        "rendered output",
        "paper timing",
        "topology solvers for world anchors beyond dense CPU oracle",
        "generated report artifacts as committed evidence",
        "any passed `experiment.*` claim",
    )
    for snippet in phase34_non_claims:
        if snippet not in phase34_non_claim:
            fail(f"claim-boundaries.md must bound Phase 34 M-ABD diagnostic evidence: {snippet}")
    phase34_forbidden = claim_boundary_bullet(
        text, "Phase 34 physical-pendulum M-ABD development diagnostic"
    )
    for snippet in (
        "passed physical-pendulum experiment",
        "paper-faithful pendulum geometry result",
        "RBD baseline result",
        "joint-force agreement result",
        "paper timing result",
    ):
        if snippet not in phase34_forbidden:
            fail(f"claim-boundaries.md must forbid Phase 34 overclaim: {snippet}")
    phase35_current = claim_boundary_bullet(text, "This repository contains Phase 35")
    phase35_verified = claim_boundary_bullet(text, "Phase 35 verifies")
    phase35_non_claim = claim_boundary_bullet(text, "Phase 35 does not verify")
    phase35_current_required = (
        "physical-pendulum RBD implicit baseline diagnostic lane",
        "Phase 35 record",
    )
    for snippet in phase35_current_required:
        if snippet not in phase35_current:
            fail(f"claim-boundaries.md must state Phase 35 RBD evidence: {snippet}")
    phase35_verified_required = (
        "rbd_baseline",
        "`rbd_implicit_baseline` CLI dispatch",
        "`physical_pendulum_scalar_implicit_rbd_development`",
        "compact angle samples",
        "finite implicit residual",
        "length constraint diagnostics",
        "`lane_status = development_diagnostic_generated`",
        "`required_missing_lanes = [mabd_newton]`",
        "top-level report status: `incomplete`",
    )
    for snippet in phase35_verified_required:
        if snippet not in phase35_verified:
            fail(f"claim-boundaries.md must describe Phase 35 RBD evidence: {snippet}")
    phase35_non_claims = (
        "full physical-pendulum experiment",
        "paper-faithful pendulum geometry",
        "M-ABD physical-pendulum experiment lane",
        "joint-force waveform agreement",
        "rendered output",
        "paper timing",
        "paper trajectory agreement",
        "any passed `experiment.*` claim",
    )
    for snippet in phase35_non_claims:
        if snippet not in phase35_non_claim:
            fail(f"claim-boundaries.md must bound Phase 35 RBD evidence: {snippet}")
    phase35_forbidden = claim_boundary_bullet(
        text, "Phase 35 physical-pendulum RBD diagnostic"
    )
    for snippet in (
        "passed physical-pendulum experiment",
        "paper-faithful pendulum geometry result",
        "M-ABD dynamics result",
        "joint-force agreement result",
        "paper timing result",
    ):
        if snippet not in phase35_forbidden:
            fail(f"claim-boundaries.md must forbid Phase 35 overclaim: {snippet}")
    phase36_current = claim_boundary_bullet(text, "This repository contains Phase 36")
    phase36_verified = claim_boundary_bullet(text, "Phase 36 verifies")
    phase36_non_claim = claim_boundary_bullet(text, "Phase 36 does not verify")
    for snippet in (
        "physical-pendulum comparison protocol",
        "Phase 36 record",
    ):
        if snippet not in phase36_current:
            fail(f"claim-boundaries.md must state Phase 36 comparison evidence: {snippet}")
    for snippet in (
        "physical_pendulum_comparison",
        "run_physical_pendulum_comparison",
        "`--lane physical_pendulum_comparison`",
        "input report provenance",
        "matched/unmatched sample coverage",
        "paper_metric_statuses",
        "`missing_required_lanes = [mabd_newton]`",
        "`physical_pendulum_multilane_comparison_development`",
        "top-level report status: `incomplete`",
    ):
        if snippet not in phase36_verified:
            fail(f"claim-boundaries.md must describe Phase 36 comparison evidence: {snippet}")
    for snippet in (
        "full physical-pendulum experiment",
        "M-ABD lane pass",
        "joint-force waveform agreement",
        "paper geometry",
        "paper timing",
        "paper trajectory agreement",
        "any passed `experiment.*` claim",
    ):
        if snippet not in phase36_non_claim:
            fail(f"claim-boundaries.md must bound Phase 36 comparison evidence: {snippet}")
    phase36_forbidden = claim_boundary_bullet(
        text, "Phase 36 physical-pendulum comparison protocol"
    )
    for snippet in (
        "passed physical-pendulum experiment",
        "M-ABD lane pass",
        "joint-force waveform agreement",
        "paper geometry result",
        "paper timing result",
        "any passed `experiment.*` claim",
    ):
        if snippet not in phase36_forbidden:
            fail(f"claim-boundaries.md must forbid Phase 36 overclaim: {snippet}")
    phase37_current = claim_boundary_bullet(text, "This repository contains Phase 37")
    phase37_verified = claim_boundary_bullet(text, "Phase 37 verifies")
    phase37_non_claim = claim_boundary_bullet(text, "Phase 37 does not verify")
    for snippet in (
        "formal physical-pendulum `mabd_newton` lane",
        "regenerated comparison evidence",
        "Phase 37 record",
    ):
        if snippet not in phase37_current:
            fail(f"claim-boundaries.md must state Phase 37 evidence: {snippet}")
    for snippet in (
        "run_physical_pendulum_mabd_newton",
        "`--lane physical_pendulum_mabd_newton`",
        "`mabd_cpu_oracle_physical_pendulum_newton_lane`",
        "`phase_drift_rad`",
        "`world_anchor_reaction_vector_n`",
        "`max_world_anchor_reaction_magnitude_n`",
        "`baseline_lane = mabd_newton`",
        "`missing_required_lanes = []`",
        "diagnostic_available",
        "diagnostic_reaction_not_paper_waveform",
        "top-level report status: `incomplete`",
    ):
        if snippet not in phase37_verified:
            fail(f"claim-boundaries.md must describe Phase 37 evidence: {snippet}")
    for snippet in (
        "full physical-pendulum experiment",
        "paper-faithful pendulum geometry",
        "joint-force waveform agreement",
        "paper timing",
        "paper trajectory agreement",
        "any passed `experiment.*` claim",
    ):
        if snippet not in phase37_non_claim:
            fail(f"claim-boundaries.md must bound Phase 37 evidence: {snippet}")
    phase37_forbidden = claim_boundary_bullet(
        text, "Phase 37 physical-pendulum `mabd_newton` lane"
    )
    for snippet in (
        "passed physical-pendulum experiment",
        "paper-faithful pendulum geometry result",
        "joint-force waveform agreement",
        "paper timing result",
        "rendered result",
        "any passed `experiment.*` claim",
    ):
        if snippet not in phase37_forbidden:
            fail(f"claim-boundaries.md must forbid Phase 37 overclaim: {snippet}")


def validate_phase9_record() -> None:
    text = (ROOT / "docs/records/2026-05-16-phase9-point-contact-forces.md").read_text(
        encoding="utf-8"
    )
    required_snippets = (
        "## Status\n\npassed",
        "## Config Path",
        "No experiment config is used in Phase 9",
        "## Repository",
        "implementation commit: `39030ef`",
        "review hardening commit:",
        "## Vendored Newton",
        "96713fa965463b69c229a4d30582c733ff3526bb",
        "local patch status:",
        "## Paper Source",
        "PDF SHA256:",
        "TeX source SHA256:",
        "## Environment",
        "mabd-newton-py310",
        "## Metrics And Thresholds",
        "random seed: not applicable",
        "thresholds:",
        "## Artifacts",
        "raw artifacts: not applicable",
        "method.force_mapping.point_load_penalty_contact",
    )
    for snippet in required_snippets:
        if snippet not in text:
            fail(f"Phase 9 record missing required evidence field: {snippet}")

    forbidden_snippets = (
        "Phase 9 verifies collision detection",
        "Phase 9 verifies friction",
        "Phase 9 verifies production `SolverMABD.step()` contact",
        "Phase 9 verifies paper scenes",
        "Phase 9 verifies timing",
        "Phase 9 verifies comparative baselines",
    )
    for snippet in forbidden_snippets:
        if snippet in text:
            fail(f"Phase 9 record overclaims unsupported evidence: {snippet}")


def validate_phase9_claim(claims: list[dict[str, Any]]) -> None:
    claim = next(
        (c for c in claims if c["claim_id"] == "method.force_mapping.point_load_penalty_contact"),
        None,
    )
    if claim is None:
        fail("paper-claims.yaml missing Phase 9 point contact force claim")
    if claim["reproduction_status"] != "passed":
        fail("method.force_mapping.point_load_penalty_contact must remain passed after Phase 9 evidence exists")
    if "not collision detection" not in claim["conflict_note"] or "friction" not in claim["conflict_note"]:
        fail("Phase 9 point contact claim must retain bounded conflict note")


def validate_phase10_record() -> None:
    text = (ROOT / "docs/records/2026-05-16-phase10-actuation-forces.md").read_text(
        encoding="utf-8"
    )
    required_snippets = (
        "## Status\n\npassed",
        "## Config Path",
        "No experiment config is used in Phase 10",
        "## Repository",
        "plan commit: `236b9bf`",
        "implementation commit:",
        "## Vendored Newton",
        "96713fa965463b69c229a4d30582c733ff3526bb",
        "local patch status:",
        "## Paper Source",
        "PDF SHA256:",
        "TeX source SHA256:",
        "experiment.tex:51",
        "experiment.tex:184",
        "experiment.tex:224",
        "## Environment",
        "mabd-newton-py310",
        "## Metrics And Thresholds",
        "random seed: not applicable",
        "thresholds:",
        "## Artifacts",
        "method.actuation.affine_control_forces",
    )
    for snippet in required_snippets:
        if snippet not in text:
            fail(f"Phase 10 record missing required evidence field: {snippet}")

    forbidden_snippets = (
        "Phase 10 verifies Newton `Control` object ingestion",
        "Phase 10 verifies robot inverse kinematics",
        "Phase 10 verifies Franka pick-and-place",
        "Phase 10 verifies timing",
        "Phase 10 verifies comparative baselines",
    )
    for snippet in forbidden_snippets:
        if snippet in text:
            fail(f"Phase 10 record overclaims unsupported evidence: {snippet}")


def validate_phase10_claim(claims: list[dict[str, Any]]) -> None:
    claim = next(
        (c for c in claims if c["claim_id"] == "method.actuation.affine_control_forces"),
        None,
    )
    if claim is None:
        fail("paper-claims.yaml missing Phase 10 actuation force claim")
    if claim["reproduction_status"] != "passed":
        fail("method.actuation.affine_control_forces must pass after Phase 10 evidence exists")
    if "not Newton Control object ingestion" not in claim["conflict_note"] or "Franka" not in claim["conflict_note"]:
        fail("Phase 10 actuation claim must retain bounded conflict note")


def validate_phase11_record() -> None:
    text = (ROOT / "docs/records/2026-05-17-phase11-control-row-extraction.md").read_text(
        encoding="utf-8"
    )
    required_snippets = (
        "## Status\n\npassed",
        "## Config Path",
        "No experiment config is used in Phase 11",
        "## Repository",
        "plan commit: `8d2ca19`",
        "implementation commit: `06fb7b3`",
        "## Vendored Newton",
        "96713fa965463b69c229a4d30582c733ff3526bb",
        "local patch status:",
        "## Paper Source",
        "PDF SHA256:",
        "TeX source SHA256:",
        "experiment.tex:224",
        "## Environment",
        "mabd-newton-py310",
        "## Metrics And Thresholds",
        "random seed: not applicable",
        "thresholds:",
        "## Artifacts",
        "stored Newton `mabd:control` rows can be converted into CPU-oracle actuation",
        "specs.",
        "`actuation_specs_from_model(model)` extracts enabled `mabd:control` rows",
        "`MABDActuationSpec` values",
        "Disabled control rows are skipped by default",
        "Extracted specs can be passed to `MABDCPUOracleConfig.actuations`",
        "method.actuation.affine_control_forces",
    )
    for snippet in required_snippets:
        if snippet not in text:
            fail(f"Phase 11 record missing required evidence field: {snippet}")

    forbidden_snippets = (
        "Phase 11 verifies Newton `Control` object ingestion",
        "Phase 11 verifies time-varying controller updates",
        "Phase 11 verifies robot inverse kinematics",
        "Phase 11 verifies Franka pick-and-place",
        "Phase 11 verifies contact-rich grasping",
        "Phase 11 verifies paper scenes",
        "Phase 11 verifies timing",
        "Phase 11 verifies comparative baselines",
    )
    for snippet in forbidden_snippets:
        if snippet in text:
            fail(f"Phase 11 record overclaims unsupported evidence: {snippet}")


def validate_phase12_record() -> None:
    text = (ROOT / "docs/records/2026-05-17-phase12-single-body-report-lane.md").read_text(
        encoding="utf-8"
    )
    required_snippets = (
        "## Status\n\npassed",
        "## Config Path",
        "No experiment config is used in Phase 12",
        "## Repository",
        "plan commit: `f9df80e`",
        "implementation commits: `bf3e0fc`, `6d484da`",
        "verification evidence commit: `99cb9e9`",
        "review hardening commits: `b6442ae`, `b38269a`",
        "## Vendored Newton",
        "96713fa965463b69c229a4d30582c733ff3526bb",
        "local patch status:",
        "## Paper Source",
        "PDF SHA256:",
        "TeX source SHA256:",
        "experiment.tex:40-55",
        "## Environment",
        "mabd-newton-py310",
        "## Metrics And Thresholds",
        "random seed: not applicable",
        "thresholds:",
        "## Artifacts",
        "Full-schema `ClaimReport` JSON round trips",
        "Report validation rejects `status=passed` for `experiment.*` claim reports",
        "`write_spinning_box_development_report`",
        "`EvidenceStatus.INCOMPLETE`",
        "No `experiment.*` claim is passed in this phase.",
    )
    for snippet in required_snippets:
        if snippet not in text:
            fail(f"Phase 12 record missing required evidence field: {snippet}")

    forbidden_snippets = (
        "Phase 12 verifies the paper spinning-box experiment",
        "Phase 12 verifies paper timing",
        "Phase 12 verifies RK4 baselines",
        "Phase 12 verifies RBD baselines",
        "Phase 12 verifies rendered output",
        "Phase 12 passes experiment.single_body.spinning_box",
    )
    for snippet in forbidden_snippets:
        if snippet in text:
            fail(f"Phase 12 record overclaims unsupported evidence: {snippet}")


def validate_phase13_record() -> None:
    text = (ROOT / "docs/records/2026-05-17-phase13-configured-spinning-box.md").read_text(
        encoding="utf-8"
    )
    required_snippets = (
        "## Status\n\npassed",
        "## Config Path",
        "configs/experiments/single_body_spinning_box.yaml",
        "## Repository",
        "plan commit: `7f68fd7`",
        "implementation commits: `9dd5d10`, `bbb4836`",
        "docs/provenance commit: `acffaf6`",
        "verification evidence commit: `48d96c8`",
        "review hardening commit: `d66cafb`",
        "## Vendored Newton",
        "96713fa965463b69c229a4d30582c733ff3526bb",
        "local patch status:",
        "## Paper Source",
        "PDF SHA256:",
        "TeX source SHA256:",
        "experiment.tex:40-55",
        "## Environment",
        "mabd-newton-py310",
        "## Metrics And Thresholds",
        "random seed: not applicable",
        "Report validation rejects `status=passed`",
        "## Artifacts",
        "`load_spinning_box_config`",
        "`validate_spinning_box_config_against_matrix`",
        "`write_spinning_box_development_report`",
        "No `experiment.*` claim is passed in this phase.",
    )
    for snippet in required_snippets:
        if snippet not in text:
            fail(f"Phase 13 record missing required evidence field: {snippet}")

    forbidden_snippets = (
        "Phase 13 verifies the paper spinning-box experiment",
        "Phase 13 verifies RBD baselines",
        "Phase 13 verifies paper timing",
        "Phase 13 verifies rendered output",
        "Phase 13 passes experiment.single_body.spinning_box",
    )
    for snippet in forbidden_snippets:
        if snippet in text:
            fail(f"Phase 13 record overclaims unsupported evidence: {snippet}")


def validate_phase14_record() -> None:
    text = (ROOT / "docs/records/2026-05-17-phase14-experiment-runner.md").read_text(
        encoding="utf-8"
    )
    required_snippets = (
        "## Status\n\npassed",
        "## Config Path",
        "configs/experiments/single_body_spinning_box.yaml",
        "## Repository",
        "plan commit:",
        "implementation commits:",
        "verification evidence commit: `f4e4bd6`",
        "review hardening commit: `ad42baf`",
        "## Vendored Newton",
        "96713fa965463b69c229a4d30582c733ff3526bb",
        "## Paper Source",
        "PDF SHA256:",
        "TeX source SHA256:",
        "experiment.tex:40-55",
        "## Artifacts",
        "`scripts/run_experiment.py`",
        "`run_spinning_box_experiment`",
        "generated reports: not committed",
        "No `experiment.*` claim is passed in this phase.",
    )
    for snippet in required_snippets:
        if snippet not in text:
            fail(f"Phase 14 record missing required evidence field: {snippet}")

    forbidden_snippets = (
        "Phase 14 verifies the paper spinning-box experiment",
        "Phase 14 verifies RBD baselines",
        "Phase 14 verifies paper timing",
        "Phase 14 verifies rendered output",
        "Phase 14 passes experiment.single_body.spinning_box",
    )
    for snippet in forbidden_snippets:
        if snippet in text:
            fail(f"Phase 14 record overclaims unsupported evidence: {snippet}")


def validate_phase15_record() -> None:
    text = (ROOT / "docs/records/2026-05-17-phase15-rbd-baseline-lane.md").read_text(
        encoding="utf-8"
    )
    required_snippets = (
        "## Status\n\npassed",
        "## Config Path",
        "configs/experiments/single_body_spinning_box.yaml",
        "## Repository",
        "plan commit:",
        "implementation commits:",
        "review hardening commit:",
        "## Vendored Newton",
        "96713fa965463b69c229a4d30582c733ff3526bb",
        "## Paper Source",
        "PDF SHA256:",
        "TeX source SHA256:",
        "experiment.tex:40-55",
        "## Environment",
        "mabd-newton-py310",
        "physics-primitive-newton-py310",
        "smoke_passed",
        "cpu_newton_warp",
        "## Metrics And Thresholds",
        "newton_semimplicit_rbd_cpu_development",
        "newton.solvers.SolverSemiImplicit",
        "Newton step count: `4`",
        "linear_momentum_error",
        "angular_momentum_error",
        "energy_drift <= 30.050000000000004",
        "relative_energy_drift",
        "rbd_implicit_baseline_report_incomplete",
        "## Artifacts",
        "`src/mabd_reproduction/rigid_baselines.py`",
        "`run_spinning_box_rbd_baseline`",
        "`--lane rbd_implicit_baseline`",
        "generated reports: not committed",
        "No `experiment.*` claim is passed in this phase.",
    )
    for snippet in required_snippets:
        if snippet not in text:
            fail(f"Phase 15 record missing required evidence field: {snippet}")

    forbidden_snippets = (
        "Phase 15 verifies the paper spinning-box experiment",
        "Phase 15 verifies paper-faithful implicit RBD baseline",
        "Phase 15 verifies paper-faithful affine collision",
        "Phase 15 verifies RK4 baselines",
        "Phase 15 verifies analytic baselines",
        "Phase 15 verifies paper timing",
        "Phase 15 passes experiment.single_body.spinning_box",
    )
    for snippet in forbidden_snippets:
        if snippet in text:
            fail(f"Phase 15 record overclaims unsupported evidence: {snippet}")


def validate_phase16_record() -> None:
    text = (
        ROOT / "docs/records/2026-05-17-phase16-spinning-box-comparison-protocol.md"
    ).read_text(encoding="utf-8")
    required_snippets = (
        "## Status\n\npassed",
        "## Config Path",
        "configs/experiments/single_body_spinning_box.yaml",
        "configs/experiments/paper_experiment_matrix.yaml",
        "## Repository",
        "plan commit: `a3a722a`",
        "implementation commits: `30ede4d`, `ec2a39c`",
        "## Vendored Newton",
        "96713fa965463b69c229a4d30582c733ff3526bb",
        "## Paper Source",
        "PDF SHA256:",
        "TeX source SHA256:",
        "experiment.tex:40-55",
        "## Environment",
        "mabd-newton-py310",
        "physics-primitive-newton-py310",
        "smoke_passed",
        "## Metrics And Thresholds",
        "spinning_box_comparison_protocol",
        "spinning_box_comparison_report_incomplete",
        "spinning_box_multilane_comparison_development",
        "report_protocol",
        "mabd_newton",
        "rbd_implicit_baseline",
        "required lane reports remain incomplete",
        "## Artifacts",
        "`src/mabd_reproduction/comparison_reports.py`",
        "`run_spinning_box_comparison`",
        "`--lane spinning_box_comparison`",
        "generated reports: not committed",
        "No `experiment.*` claim is passed in this phase.",
    )
    for snippet in required_snippets:
        if snippet not in text:
            fail(f"Phase 16 record missing required evidence field: {snippet}")

    forbidden_snippets = (
        "Phase 16 verifies the paper spinning-box experiment",
        "Phase 16 passes experiment.single_body.spinning_box",
        "Phase 16 verifies paper-faithful implicit RBD baseline",
        "Phase 16 verifies paper timing",
    )
    for snippet in forbidden_snippets:
        if snippet in text:
            fail(f"Phase 16 record overclaims unsupported evidence: {snippet}")


def validate_phase17_record() -> None:
    text = (
        ROOT / "docs/records/2026-05-17-phase17-spinning-box-mabd-paper-metrics.md"
    ).read_text(encoding="utf-8")
    required_snippets = (
        "## Status\n\npassed",
        "## Config Path",
        "configs/experiments/single_body_spinning_box.yaml",
        "## Repository",
        "plan commit: `5cc171a`",
        "implementation commits: `ebf7d86`, `da56334`, `ff24a68`",
        "docs/provenance commit: `d25e3bd3b7b60655285d3d077e600c438737cd48`",
        "## Vendored Newton",
        "96713fa965463b69c229a4d30582c733ff3526bb",
        "## Paper Source",
        "PDF SHA256:",
        "TeX source SHA256:",
        "experiment.tex:40-55",
        "## Environment",
        "mabd-newton-py310",
        "physics-primitive-newton-py310",
        "smoke_passed",
        "## Metrics And Thresholds",
        "paper p0/L0",
        "paper_spatial_twist",
        "linear_momentum_error <= 1.0e-9",
        "angular_momentum_error <= 1.0e-9",
        "spinning_box_comparison_report_incomplete",
        "## Artifacts",
        "`src/mabd_reproduction/spinning_box_physics.py`",
        "abd_generalized_velocity_from_paper_momenta",
        "mabd_momentum_diagnostics",
        "`write_spinning_box_development_report`",
        "generated reports: not committed",
        "No `experiment.*` claim is passed in this phase.",
    )
    for snippet in required_snippets:
        if snippet not in text:
            fail(f"Phase 17 record missing required evidence field: {snippet}")

    forbidden_snippets = (
        "Phase 17 verifies the paper spinning-box experiment",
        "Phase 17 passes experiment.single_body.spinning_box",
        "Phase 17 verifies paper-faithful implicit RBD baseline",
        "Phase 17 verifies paper-faithful affine collision",
        "Phase 17 verifies paper timing",
    )
    for snippet in forbidden_snippets:
        if snippet in text:
            fail(f"Phase 17 record overclaims unsupported evidence: {snippet}")


def validate_phase18_record() -> None:
    text = (
        ROOT / "docs/records/2026-05-17-phase18-spinning-box-mabd-physical-mass.md"
    ).read_text(encoding="utf-8")
    required_snippets = (
        "## Status\n\npassed",
        "## Config Path",
        "configs/experiments/single_body_spinning_box.yaml",
        "## Repository",
        "plan commit: `5f8c3de029f20b157b9a50d624223d05e21a7720`",
        "implementation commit: `c7710f0f3ab6656a41968b3fe230e274d5f77f8b`",
        "docs/provenance commit: `632946ffa567ef7cac15868b92b8a5db936ec739`",
        "review hardening commit: `054d454caa55c10b9094a536ef4d0dd10047b041`",
        "independent review:",
        "## Vendored Newton",
        "96713fa965463b69c229a4d30582c733ff3526bb",
        "## Paper Source",
        "PDF SHA256:",
        "TeX source SHA256:",
        "experiment.tex:40-55",
        "## Environment",
        "mabd-newton-py310",
        "physics-primitive-newton-py310",
        "## Metrics And Thresholds",
        "mass_diagonal = [1/1200] * 9 + [1.0] * 3",
        "initial_energy_j = 3005000.0",
        "relative_energy_drift",
        "## Artifacts",
        "`spinning_box_mabd_mass_diagonal`",
        "generated reports: not committed",
        "No `experiment.*` claim is passed in this phase.",
        "phase bootstrap docs tests: Ran 31 tests, OK",
    )
    for snippet in required_snippets:
        if snippet not in text:
            fail(f"Phase 18 record missing required evidence field: {snippet}")

    forbidden_snippets = (
        "Phase 18 verifies the paper spinning-box experiment",
        "Phase 18 passes experiment.single_body.spinning_box",
        "Phase 18 verifies paper-faithful implicit RBD baseline",
        "Phase 18 verifies paper-faithful affine collision",
        "Phase 18 verifies paper timing",
    )
    for snippet in forbidden_snippets:
        if snippet in text:
            fail(f"Phase 18 record overclaims unsupported evidence: {snippet}")


def validate_phase19_record() -> None:
    text = (
        ROOT / "docs/records/2026-05-17-phase19-spinning-box-comparison-finite-metrics.md"
    ).read_text(encoding="utf-8")
    required_snippets = (
        "## Status\n\npassed",
        "## Config Path",
        "configs/experiments/single_body_spinning_box.yaml",
        "## Repository",
        "plan commit: `5af27323947b296b3ebf1956a5799d0906dfea03`",
        "implementation commit: `947bbfa4ba1e3f5ed805585d41ba3a562039441a`",
        "docs/provenance commit: `0dc83f269c4a72545c6e3fbe006ae334e4d41202`",
        "review hardening commits: `6dd48d33fecaf33c970a0a6676ff8134467262fe`,",
        "`df6bb3e94310178ed1fa5a9184fd02bf7f020fec`",
        "independent review:",
        "## Vendored Newton",
        "96713fa965463b69c229a4d30582c733ff3526bb",
        "## Paper Source",
        "PDF SHA256:",
        "TeX source SHA256:",
        "experiment.tex:40-55",
        "## Environment",
        "mabd-newton-py310",
        "physics-primitive-newton-py310",
        "## Metrics And Thresholds",
        "invalid_required_metrics",
        "lane_metric_differences",
        "mabd_newton:energy_drift_invalid",
        "invalid metric snapshot value: JSON `null`",
        "## Artifacts",
        "`src/mabd_reproduction/comparison_reports.py`",
        "generated reports: not committed",
        "No `experiment.*` claim is passed in this phase.",
        "phase bootstrap docs tests: Ran 33 tests, OK",
        "not emitted as bare NaN or Infinity tokens",
    )
    for snippet in required_snippets:
        if snippet not in text:
            fail(f"Phase 19 record missing required evidence field: {snippet}")

    forbidden_snippets = (
        "Phase 19 verifies the paper spinning-box experiment",
        "Phase 19 passes experiment.single_body.spinning_box",
        "Phase 19 verifies paper-faithful implicit RBD baseline",
        "Phase 19 verifies paper-faithful affine collision",
        "Phase 19 verifies paper timing",
    )
    for snippet in forbidden_snippets:
        if snippet in text:
            fail(f"Phase 19 record overclaims unsupported evidence: {snippet}")


def validate_phase20_record() -> None:
    text = (
        ROOT / "docs/records/2026-05-17-phase20-spinning-box-contact-diagnostics.md"
    ).read_text(encoding="utf-8")
    required_snippets = (
        "## Status\n\npassed",
        "## Config Path",
        "configs/experiments/single_body_spinning_box.yaml",
        "## Repository",
        "plan commit: `773a0ef60c4357a3083e30918c915f08a6eb1e88`",
        "config commit: `d10ca0176cd678d76ed9a0c6d48339d4bdcdcf22`",
        "implementation commit: `6bc889a6f7f9d2c19d9a487e37b9f9286ff4cf03`",
        "report commit: `f4b5212cdf5543021dcf7d7a3b29731f237773c2`",
        "docs/provenance commit: `b24eb15a15f47fd6a0a024eebd1b815fd474c505`",
        "review hardening commit: `f5fe643200a510368a240459d598289ff6e499ba`",
        "independent review:",
        "Phase 20 non-claim substring checks",
        "## Vendored Newton",
        "96713fa965463b69c229a4d30582c733ff3526bb",
        "## Paper Source",
        "PDF SHA256:",
        "TeX source SHA256:",
        "experiment.tex:40-55",
        "## Environment",
        "mabd-newton-py310",
        "physics-primitive-newton-py310",
        "## Metrics And Thresholds",
        "contact_surface",
        "contact_surface_type",
        "contact_corner_count",
        "contact_active_count",
        "contact_min_signed_distance_m",
        "contact_max_penetration_m",
        "contact_total_normal_force_n",
        "contact_total_generalized_force",
        "contact_corner_signed_distances_m",
        "initial_configured_q_qd",
        "mabd.evaluate_point_plane_penalty_contact",
        "## Artifacts",
        "`src/mabd_reproduction/spinning_box_physics.py`",
        "`src/mabd_reproduction/single_body_reports.py`",
        "generated reports: not committed",
        "No `experiment.*` claim is passed in this phase.",
        "phase bootstrap docs tests:",
    )
    for snippet in required_snippets:
        if snippet not in text:
            fail(f"Phase 20 record missing required evidence field: {snippet}")

    forbidden_snippets = (
        "Phase 20 verifies the paper spinning-box experiment",
        "Phase 20 passes experiment.single_body.spinning_box",
        "Phase 20 verifies paper-faithful implicit RBD baseline",
        "Phase 20 verifies paper-faithful affine collision",
        "Phase 20 verifies paper timing",
        "Phase 20 verifies collision detection",
    )
    for snippet in forbidden_snippets:
        if snippet in text:
            fail(f"Phase 20 record overclaims unsupported evidence: {snippet}")


def validate_phase21_record() -> None:
    text = (
        ROOT / "docs/records/2026-05-17-phase21-spinning-box-plane-placement.md"
    ).read_text(encoding="utf-8")
    required_snippets = (
        "## Status\n\npassed",
        "## Config Path",
        "configs/experiments/single_body_spinning_box.yaml",
        "## Repository",
        "plan commit: `d6c2265ea9f23b867cd88a0881f0275aa341c4da`",
        "implementation commit: `29a210d28446d2f5dd0fa816a35dde894aa7b639`",
        "docs/provenance commit: `630a60b18e85d6481944abadc743da28655dcc09`",
        "review hardening commit: `9c099e5788fb3d29f541f90eab45a877b2d7650b`",
        "independent review:",
        "physics/config/report review found no findings",
        "boundary/provenance review found",
        "hardening commit",
        "## Vendored Newton",
        "96713fa965463b69c229a4d30582c733ff3526bb",
        "## Paper Source",
        "PDF SHA256:",
        "TeX source SHA256:",
        "experiment.tex:40-55",
        "## Environment",
        "mabd-newton-py310",
        "physics-primitive-newton-py310",
        "## Metrics And Thresholds",
        "initial_q[10] = 0.05",
        "contact_min_signed_distance_m = 0.0",
        "contact_max_penetration_m = 0.0",
        "contact_active_count = 0",
        "contact_total_normal_force_n = [0.0, 0.0, 0.0]",
        "contact_total_generalized_force = [0.0] * 12",
        "## Artifacts",
        "`configs/experiments/single_body_spinning_box.yaml`",
        "generated reports: not committed",
        "No `experiment.*` claim is passed in this phase.",
        "config/report tests: Ran 10 tests, OK",
    )
    for snippet in required_snippets:
        if snippet not in text:
            fail(f"Phase 21 record missing required evidence field: {snippet}")

    forbidden_snippets = (
        "Phase 21 verifies the paper spinning-box experiment",
        "Phase 21 passes experiment.single_body.spinning_box",
        "Phase 21 verifies collision detection",
        "Phase 21 verifies implicit contact solve",
        "Phase 21 verifies paper-faithful affine collision",
        "Phase 21 verifies paper-faithful implicit RBD baseline",
        "Phase 21 verifies paper timing",
    )
    for snippet in forbidden_snippets:
        if snippet in text:
            fail(f"Phase 21 record overclaims unsupported evidence: {snippet}")


def validate_phase22_record() -> None:
    text = (
        ROOT / "docs/records/2026-05-17-phase22-rbd-plane-placement.md"
    ).read_text(encoding="utf-8")
    required_snippets = (
        "## Status\n\npassed",
        "## Config Path",
        "configs/experiments/single_body_spinning_box.yaml",
        "## Repository",
        "plan commit: `50816b9ba11c80e9993d067bfbbdcc579e2c5fa3`",
        "implementation commit: `c7a22b1a0fb400da47c2a715b9ac32333aed67d2`",
        "docs/provenance commit: `2bb28f572427fb879f3168265b0e3e26f0e0a1f5`",
        "review hardening commit: `1c6125ed899cd57d1d39096fd70d52b657cef440`",
        "independent review:",
        "RBD config/physics review found no findings",
        "claim/provenance review found",
        "## Vendored Newton",
        "96713fa965463b69c229a4d30582c733ff3526bb",
        "## Paper Source",
        "PDF SHA256:",
        "TeX source SHA256:",
        "experiment.tex:40-55",
        "## Environment",
        "mabd-newton-py310",
        "physics-primitive-newton-py310",
        "smoke_passed",
        "clone drift check:",
        "## Metrics And Thresholds",
        "initial_position_m = [0.0, 0.05, 0.0]",
        "final_position_m = [4.0, 0.05, 0.0]",
        "newton_semimplicit_rbd_cpu_development",
        "newton.solvers.SolverSemiImplicit",
        "report status: `incomplete`",
        "## Artifacts",
        "`src/mabd_reproduction/rigid_baselines.py`",
        "generated reports: not committed",
        "No `experiment.*` claim is passed in this phase.",
        "RBD tests: Ran 5 tests, OK",
        "Docs GREEN result:",
        "phase bootstrap docs tests: Ran 39 tests, OK",
        (
            "docs validator: Phase "
            "0/1/2/3/4/5/6/7/8/9/10/11/12/13/14/15/16/17/18/19/20/21/22 "
            "docs/provenance validation passed"
        ),
    )
    for snippet in required_snippets:
        if snippet not in text:
            fail(f"Phase 22 record missing required evidence field: {snippet}")

    forbidden_snippets = (
        "Phase 22 verifies the paper spinning-box experiment",
        "Phase 22 passes experiment.single_body.spinning_box",
        "Phase 22 verifies paper-faithful implicit RBD baseline",
        "Phase 22 verifies paper-faithful affine collision",
        "Phase 22 verifies collision detection",
        "Phase 22 verifies implicit contact solve",
        "Phase 22 verifies paper timing",
    )
    for snippet in forbidden_snippets:
        if snippet in text:
            fail(f"Phase 22 record overclaims unsupported evidence: {snippet}")


def validate_phase23_record() -> None:
    text = (
        ROOT / "docs/records/2026-05-17-phase23-spinning-box-position-comparison.md"
    ).read_text(encoding="utf-8")
    required_snippets = (
        "## Status\n\npassed",
        "## Config Path",
        "configs/experiments/single_body_spinning_box.yaml",
        "## Repository",
        "plan commit: `080f4908c9a16f5e707a1175ceb33c4e7bda8c2d`",
        "implementation commit: `434bdeab71a024277311bfc0925eb9b09630bf41`",
        "implementation commit: `57c8365262f12fd4f026da14163f493c60a86974`",
        "review hardening commit: `c116a6fc1e499f99ab69aafc0c8c997930d14469`",
        "docs/provenance commit: `27a305329df473bc4c30f63ad7e36f058e3e3a6f`",
        "independent review:",
        "source/numerics review found",
        "non-finite comparison differences",
        "docs/provenance review found",
        "pending independent-review placeholder",
        "environment evidence gates",
        "## Vendored Newton",
        "96713fa965463b69c229a4d30582c733ff3526bb",
        "## Paper Source",
        "PDF SHA256:",
        "TeX source SHA256:",
        "experiment.tex:40-55",
        "## Environment",
        "mabd-newton-py310",
        "physics-primitive-newton-py310",
        "smoke_passed",
        "readiness JSON output: branch-gate stdout, not committed",
        "clone drift command:",
        "clone drift check:",
        "mutates_reference_environment=false",
        "uses_reference_python=false",
        "uses_ambient_python=false",
        "## Metrics And Thresholds",
        "initial_position_m = [0.0, 0.05, 0.0]",
        "final_position_m = [4.0, 0.05, 0.0]",
        "required_vector_metrics = [`initial_position_m`, `final_position_m`]",
        "lane_vector_metrics",
        "lane_vector_metric_differences",
        "invalid_required_vector_metrics",
        "mabd_newton:final_position_m_invalid",
        "spinning_box_comparison_report_incomplete",
        "report status: `incomplete`",
        "## Artifacts",
        "`src/mabd_reproduction/single_body_reports.py`",
        "`src/mabd_reproduction/comparison_reports.py`",
        "generated reports: not committed",
        "No `experiment.*` claim is passed in this phase.",
        "M-ABD report tests: Ran 2 tests, OK",
        "comparison tests: Ran 5 tests, OK",
        "AssertionError: 'Infinity' unexpectedly found",
        "Docs GREEN result:",
        "phase bootstrap docs tests: Ran 41 tests, OK",
        (
            "docs validator: Phase "
            "0/1/2/3/4/5/6/7/8/9/10/11/12/13/14/15/16/17/18/19/20/21/22/23 "
            "docs/provenance validation passed"
        ),
    )
    for snippet in required_snippets:
        if snippet not in text:
            fail(f"Phase 23 record missing required evidence field: {snippet}")

    forbidden_snippets = (
        "Phase 23 verifies the paper spinning-box experiment",
        "Phase 23 passes experiment.single_body.spinning_box",
        "Phase 23 verifies paper-faithful implicit RBD baseline",
        "Phase 23 verifies paper-faithful affine collision",
        "Phase 23 verifies collision detection",
        "Phase 23 verifies implicit contact solve",
        "Phase 23 verifies paper timing",
        "Phase 23 verifies paper trajectory agreement",
    )
    for snippet in forbidden_snippets:
        if snippet in text:
            fail(f"Phase 23 record overclaims unsupported evidence: {snippet}")


def validate_phase24_record() -> None:
    text = (
        ROOT / "docs/records/2026-05-17-phase24-spinning-box-trajectory-shape-diagnostics.md"
    ).read_text(encoding="utf-8")
    required_snippets = (
        "## Status\n\npassed",
        "## Config Path",
        "configs/experiments/single_body_spinning_box.yaml",
        "## Repository",
        "plan commit: `f80cdc711719306f2b8babdc4e9c24af49175f83`",
        "M-ABD trajectory implementation commit: `5c42c19526de15bd662aaed65cbd0aa8ce7e50e2`",
        "RBD trajectory implementation commit: `4a18387cf9211a61d91fd8d87c1dfdf551f692b4`",
        "docs/record creation commit: `f79510d0cba4ededaa58f05c7040a45ca6dd3130`",
        "docs/provenance hardening commit: `089a8548a4ae3344bb6cb88507378baf12744885`",
        "independent review:",
        "implementation/numerics review found no findings",
        "claim/provenance review found",
        "stale docs/provenance commit semantics",
        "pending branch-gate review placeholder",
        "## Vendored Newton",
        "96713fa965463b69c229a4d30582c733ff3526bb",
        "## Paper Source",
        "PDF SHA256:",
        "TeX source SHA256:",
        "experiment.tex:40-55",
        "## Environment",
        "mabd-newton-py310",
        "physics-primitive-newton-py310",
        "smoke_passed",
        "readiness JSON output: branch-gate stdout, not committed",
        "clone drift command:",
        "clone drift check:",
        "mutates_reference_environment=false",
        "uses_reference_python=false",
        "uses_ambient_python=false",
        "## Metrics And Thresholds",
        "trajectory_samples",
        "final_affine_orthogonality_error",
        "final_affine_determinant",
        "final_affine_singular_values",
        "affine_shape_diagnostic_status = development_gap_observed",
        "rotation_xyzw",
        "report status: `incomplete`",
        "## Artifacts",
        "`src/mabd_reproduction/spinning_box_physics.py`",
        "`src/mabd_reproduction/single_body_reports.py`",
        "`src/mabd_reproduction/rigid_baselines.py`",
        "`SpinningBoxAffineShapeDiagnostics`",
        "`spinning_box_affine_shape_diagnostics`",
        "generated reports: not committed",
        "No `experiment.*` claim is passed in this phase.",
        "M-ABD report tests: Ran 2 tests, OK",
        "RBD tests: Ran 5 tests, OK",
        "phase bootstrap docs tests: Ran 43 tests, OK",
        (
            "docs validator: Phase "
            "0/1/2/3/4/5/6/7/8/9/10/11/12/13/14/15/16/17/18/19/20/21/22/23/24 "
            "docs/provenance validation passed"
        ),
    )
    for snippet in required_snippets:
        if snippet not in text:
            fail(f"Phase 24 record missing required evidence field: {snippet}")
    for stale_snippet in (
        "independent review: pending",
        "TO_BE_BACKFILLED_PHASE24_DOCS_COMMIT",
    ):
        if stale_snippet in text:
            fail(f"Phase 24 record contains stale placeholder: {stale_snippet}")

    forbidden_snippets = (
        "Phase 24 verifies the paper spinning-box experiment",
        "Phase 24 passes experiment.single_body.spinning_box",
        "Phase 24 verifies paper-faithful implicit RBD baseline",
        "Phase 24 verifies paper-faithful affine collision",
        "Phase 24 verifies collision detection",
        "Phase 24 verifies implicit contact solve",
        "Phase 24 verifies paper timing",
        "Phase 24 verifies paper trajectory agreement",
    )
    for snippet in forbidden_snippets:
        if snippet in text:
            fail(f"Phase 24 record overclaims unsupported evidence: {snippet}")


def validate_phase25_record() -> None:
    text = (
        ROOT / "docs/records/2026-05-17-phase25-spinning-box-no-polar-material-lane.md"
    ).read_text(encoding="utf-8")
    required_snippets = (
        "## Status\n\npassed",
        "## Config Path",
        "configs/experiments/single_body_spinning_box.yaml",
        "## Repository",
        "plan commit: `9cff8b74521ec3ae2395bb5ceac42651cb1f2a40`",
        "CPU oracle no-polar implementation commit: `80a32a1e2f5a1a3ab80bec2460562cbcfd54c0bf`",
        "spinning-box material lane implementation commit:",
        "`c0cef676e5265c659ca2bd9bd58165f357d8b1fa`",
        "docs/record creation commit: `aa7eb983471ac1f2f6abdf27af7641b131533ea4`",
        "docs/provenance hardening commit: `511f2d13baf67dcc478494a4022bfd6cf959e82b`",
        "CPU oracle review disposition commit: `f8998822bc5d9a911c2a48fc3de93ffad204e6d8`",
        "review disposition record commit: `766a863491855fecba03033c4baeca818f6c480f`",
        "independent review:",
        "rotated the translation block",
        "reported residuals in the",
        "unrotated system",
        "keeps translation inertial",
        "world frame",
        "reports residuals in the local no-polar solve system",
        "did not list the docs/provenance hardening commit",
        "## Vendored Newton",
        "96713fa965463b69c229a4d30582c733ff3526bb",
        "local patch status: Phase 25 modifies vendored Newton",
        "## Paper Source",
        "PDF SHA256:",
        "TeX source SHA256:",
        "experiment.tex:40-55",
        "## Environment",
        "mabd-newton-py310",
        "physics-primitive-newton-py310",
        "smoke_passed",
        "readiness JSON output: branch-gate stdout, not committed",
        "clone drift command:",
        "clone drift check:",
        "mutates_reference_environment=false",
        "uses_reference_python=false",
        "uses_ambient_python=false",
        "## Metrics And Diagnostics",
        "mabd_rotation_mode = no_polar",
        "material_model = paper_linear_elastic_no_polar_development",
        "material_young_modulus_pa = 1000000000.0",
        "material_poisson_ratio = 0.3",
        "material_volume_m3 = 0.001",
        "material_stiffness_trace",
        "material_stiffness_rank",
        "linear_momentum_error <= 1.0e-9",
        "angular_momentum_error remains a development gap",
        "relative_energy_drift remains a development gap",
        "affine_shape_diagnostic_status = development_gap_observed",
        "constrained CPU oracle no-polar KKT remains unsupported",
        "report status: `incomplete`",
        "## Artifacts",
        "`vendor/newton/newton/_src/solvers/mabd/step_oracle.py`",
        "`src/mabd_reproduction/spinning_box_physics.py`",
        "`src/mabd_reproduction/single_body_reports.py`",
        "`spinning_box_mabd_material_stiffness`",
        "`spinning_box_mabd_material_properties`",
        "generated reports: not committed",
        "No `experiment.*` claim is passed in this phase.",
        "CPU oracle tests: Ran 13 tests, OK",
        "vendored CPU oracle tests: Ran 7 tests, OK",
        "M-ABD report tests: Ran 2 tests, OK",
        "comparison and runner tests: Ran 21 tests, OK",
        "phase bootstrap docs tests: Ran 45 tests, OK",
        (
            "docs validator: Phase "
            "0/1/2/3/4/5/6/7/8/9/10/11/12/13/14/15/16/17/18/19/20/21/22/23/24/25 "
            "docs/provenance validation passed"
        ),
    )
    for snippet in required_snippets:
        if snippet not in text:
            fail(f"Phase 25 record missing required evidence field: {snippet}")
    if "TO_BE_BACKFILLED_PHASE25_DOCS_COMMIT" in text:
        fail("Phase 25 record contains stale docs commit placeholder")
    if "TO_BE_BACKFILLED_PHASE25_REVIEW_DISPOSITION_COMMIT" in text:
        fail("Phase 25 record contains stale review disposition commit placeholder")
    forbidden_snippets = (
        "Phase 25 verifies the paper spinning-box experiment",
        "Phase 25 passes experiment.single_body.spinning_box",
        "Phase 25 verifies full M-ABD dynamics",
        "Phase 25 verifies multi-body no-polar constraints",
        "Phase 25 verifies paper-faithful implicit RBD baseline",
        "Phase 25 verifies paper-faithful affine collision",
        "Phase 25 verifies collision detection",
        "Phase 25 verifies implicit contact solve",
        "Phase 25 verifies paper timing",
        "Phase 25 verifies paper trajectory agreement",
    )
    for snippet in forbidden_snippets:
        if snippet in text:
            fail(f"Phase 25 record overclaims unsupported evidence: {snippet}")


def validate_phase26_record() -> None:
    text = (ROOT / "docs/records/2026-05-17-phase26-corotated-material-rhs.md").read_text(
        encoding="utf-8"
    )
    required_snippets = (
        "## Status\n\npassed",
        "## Config Path",
        "configs/experiments/single_body_spinning_box.yaml",
        "## Repository",
        "plan commit: `96509da8cd8f98124d885b8b1377351329b886ba`",
        "polar CPU oracle implementation commit:",
        "`d2ddb2a2e1e6b74d4deb1c6d8720ca7ee09f7ddb`",
        "spinning-box polar report lane implementation commit:",
        "`a5755baaed1d577fa23a6bd47e3ef4751a5e191a`",
        "docs/record creation commit: `982ebaa60907e1666e3acc6f3cf8ffdabc1d207a`",
        "review disposition record commit: `aa18dda3111de820e617d1b6515d1d547445efa5`",
        "provenance hardening commit: `d500f97cee6f66a2a5a4aae23275d09ac4dd0df3`",
        "verification-command hardening commit: `aa18dda3111de820e617d1b6515d1d547445efa5`",
        "independent review:",
        "affine-only local transform",
        "not paper-equivalent",
        "exploratory metrics were not evidence",
        "record/validator requirements were under-specified",
        "## Vendored Newton",
        "96713fa965463b69c229a4d30582c733ff3526bb",
        "local patch status: Phase 26 modifies vendored Newton",
        "## Paper Source",
        "PDF SHA256:",
        "TeX source SHA256:",
        "singleabd.tex:87-125",
        "singleabd.tex:127-156",
        "experiment.tex:40-55",
        "## Environment",
        "mabd-newton-py310",
        "physics-primitive-newton-py310",
        "smoke_passed",
        "mutates_reference_environment=false",
        "uses_reference_python=false",
        "uses_ambient_python=false",
        "## Metrics And Diagnostics",
        "mabd_rotation_mode = polar",
        "material_model = paper_linear_elastic_corotated_development",
        "material_rhs_frame = corotated_local_all_blocks",
        "translation_frame = corotated_polar_all_blocks",
        "material_young_modulus_pa = 1000000000.0",
        "material_poisson_ratio = 0.3",
        "material_volume_m3 = 0.001",
        "material_stiffness_trace",
        "material_stiffness_rank",
        "linear_momentum_error <= 1.0e-9",
        "angular_momentum_error remains a development gap",
        "relative_energy_drift remains a development gap",
        "affine_shape_diagnostic_status = development_gap_observed",
        "report status: `incomplete`",
        "## Artifacts",
        "`vendor/newton/newton/_src/solvers/mabd/step_oracle.py`",
        "`src/mabd_reproduction/single_body_reports.py`",
        "generated reports: not committed",
        "No `experiment.*` claim is passed in this phase.",
        "## Verification Commands",
        "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_mabd_phase4_solver_step",
        "PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest newton.tests.test_mabd_phase4_solver_step",
        "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_single_body_report_lane tests.test_spinning_box_comparison tests.test_experiment_runner",
        "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_phase0_bootstrap",
        "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests",
        "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .",
        "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py",
        "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/env/readiness_check.py",
        'PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"',
        "git diff --check",
        "CPU oracle tests: Ran 17 tests, OK",
        "vendored CPU oracle tests: Ran 11 tests, OK",
        "comparison and runner tests: Ran 21 tests, OK",
        (
            "docs validator: Phase "
            "0/1/2/3/4/5/6/7/8/9/10/11/12/13/14/15/16/17/18/19/20/21/22/23/24/25/26 "
            "docs/provenance validation passed"
        ),
    )
    for snippet in required_snippets:
        if snippet not in text:
            fail(f"Phase 26 record missing required evidence field: {snippet}")
    if "TO_BE_BACKFILLED_PHASE26_DOCS_COMMIT" in text:
        fail("Phase 26 record contains stale docs commit placeholder")
    if "TO_BE_BACKFILLED_PHASE26_REVIEW_DISPOSITION_COMMIT" in text:
        fail("Phase 26 record contains stale review disposition commit placeholder")
    if "pending branch-local" in text:
        fail("Phase 26 record contains pending branch-local provenance placeholder")
    forbidden_snippets = (
        "Phase 26 verifies the paper spinning-box experiment",
        "Phase 26 passes experiment.single_body.spinning_box",
        "Phase 26 verifies paper-faithful implicit RBD baseline",
        "Phase 26 verifies paper-faithful affine collision",
        "Phase 26 verifies collision detection",
        "Phase 26 verifies implicit contact solve",
        "Phase 26 verifies paper timing",
        "Phase 26 verifies paper trajectory agreement",
    )
    for snippet in forbidden_snippets:
        if snippet in text:
            fail(f"Phase 26 record overclaims unsupported evidence: {snippet}")

    data = read_yaml(ROOT / "docs/reference/paper-claims.yaml")
    claims = data.get("claims")
    if not isinstance(claims, list):
        fail("paper-claims.yaml missing claims list")
    for claim in claims:
        if isinstance(claim, dict) and str(claim.get("claim_id", "")).startswith("experiment."):
            if claim.get("reproduction_status") == "passed":
                fail("Phase 26 must not pass experiment.* claims")

def validate_phase27_record() -> None:
    text = (ROOT / "docs/records/2026-05-17-phase27-rbd-pass-gate.md").read_text(
        encoding="utf-8"
    )
    required_snippets = (
        "## Status\n\npassed",
        "## Config Path",
        "configs/experiments/single_body_spinning_box.yaml",
        "configs/experiments/paper_experiment_matrix.yaml",
        "## Repository",
        "plan commit: `423313d`",
        "design hardening commit:",
        "report gate validation commit:",
        "paper RBD baseline commit:",
        "runner/comparison commit:",
        "docs/record commit:",
        "independent review:",
        "top-level experiment reports must remain incomplete",
        "## Vendored Newton",
        "96713fa965463b69c229a4d30582c733ff3526bb",
        "local patch status: Phase 27 does not modify vendored Newton",
        "## Paper Source",
        "PDF SHA256:",
        "TeX source SHA256:",
        "experiment.tex:40-55",
        "## Environment",
        "mabd-newton-py310",
        "physics-primitive-newton-py310",
        "smoke_passed",
        "mutates_reference_environment=false",
        "uses_reference_python=false",
        "uses_ambient_python=false",
        "## Metrics And Diagnostics",
        "baseline_lane = rbd_implicit_baseline",
        "solver_mode = paper_faithful_implicit_rbd",
        "backend = cpu_numpy_newton_only",
        "lane_gate_status = passed",
        "report status: `incomplete`",
        "full_experiment_claim_passed = false",
        "linear_momentum_error <= 1.0e-12",
        "angular_momentum_error <= 1.0e-12",
        "energy_drift <= 1.0e-12",
        "relative_energy_drift <= 1.0e-12",
        "final_rotation_xyzw = [0.0, -0.08827860647172615, 0.0, 0.9960958225188027]",
        "spinning_box_comparison_pass_gate_not_enabled",
        "No `experiment.*` claim is passed in this phase.",
        "## Artifacts",
        "generated reports: not committed",
        "## Verification Commands",
        "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_reporting_contracts",
        "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_rigid_baselines",
        "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_runner tests.test_spinning_box_comparison",
        "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_run_configs tests.test_phase0_bootstrap",
        "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py",
        "git diff --check",
    )
    for snippet in required_snippets:
        if snippet not in text:
            fail(f"Phase 27 record missing required evidence field: {snippet}")
    if "TO_BE_BACKFILLED_PHASE27_DOCS_COMMIT" in text:
        fail("Phase 27 record contains stale docs commit placeholder")
    if "pending branch-local" in text:
        fail("Phase 27 record contains pending branch-local provenance placeholder")
    forbidden_snippets = (
        "Phase 27 verifies the paper spinning-box experiment",
        "Phase 27 passes experiment.single_body.spinning_box",
        "Phase 27 passes the M-ABD lane",
        "Phase 27 passes the spinning-box comparison",
        "Phase 27 verifies paper-faithful affine collision",
        "Phase 27 verifies collision detection",
        "Phase 27 verifies implicit contact solve",
        "Phase 27 verifies paper timing",
        "Phase 27 verifies paper trajectory agreement",
    )
    for snippet in forbidden_snippets:
        if snippet in text:
            fail(f"Phase 27 record overclaims unsupported evidence: {snippet}")

    data = read_yaml(ROOT / "docs/reference/paper-claims.yaml")
    claims = data.get("claims")
    if not isinstance(claims, list):
        fail("paper-claims.yaml missing claims list")
    for claim in claims:
        if isinstance(claim, dict) and str(claim.get("claim_id", "")).startswith("experiment."):
            if claim.get("reproduction_status") == "passed":
                fail("Phase 27 must not pass experiment.* claims")

    matrix = load_experiment_matrix(ROOT / "configs/experiments/paper_experiment_matrix.yaml")
    spinning_box = next(
        experiment
        for experiment in matrix.experiments
        if experiment.claim_id == "experiment.single_body.spinning_box"
    )
    if "rbd_implicit_baseline_report_incomplete" in spinning_box.blocking_reasons:
        fail("Phase 27 spinning-box matrix must remove incomplete RBD baseline blocker")
    if "mabd_newton_report_incomplete" not in spinning_box.blocking_reasons:
        fail("Phase 27 spinning-box matrix must retain incomplete M-ABD lane blocker")
    if "spinning_box_comparison_report_incomplete" not in spinning_box.blocking_reasons:
        fail("Phase 27 spinning-box matrix must retain incomplete comparison report blocker")


def validate_phase28_record() -> None:
    text = (
        ROOT / "docs/records/2026-05-17-phase28-spinning-box-paper-horizon.md"
    ).read_text(encoding="utf-8")
    required_snippets = (
        "## Status\n\npassed",
        "## Config Path",
        "configs/experiments/single_body_spinning_box.yaml",
        "configs/experiments/paper_experiment_matrix.yaml",
        "## Repository",
        "design commit:",
        "plan commit:",
        "config commit:",
        "report implementation commit:",
        "runner/comparison commit:",
        "docs/record commit:",
        "independent review:",
        "## Vendored Newton",
        "96713fa965463b69c229a4d30582c733ff3526bb",
        "local patch status: Phase 28 does not modify vendored Newton",
        "## Paper Source",
        "PDF SHA256:",
        "TeX source SHA256:",
        "figure PDF SHA256:",
        "7669b062348324a3b0090cc9f44930655c83233a87f63389db9198b88f95ae80",
        "pdftotext /tmp/mabd-paper/source/images/cube/roll_cube.pdf -",
        "experiment.tex:40-55",
        "## Environment",
        "mabd-newton-py310",
        "physics-primitive-newton-py310",
        "smoke_passed",
        "mutates_reference_environment=false",
        "uses_reference_python=false",
        "uses_ambient_python=false",
        "## Metrics And Diagnostics",
        "solver_mode = mabd_cpu_oracle_paper_horizon_diagnostic",
        "baseline_lane = mabd_newton",
        "report status: `incomplete`",
        "mabd_paper_horizon_status = development_gap_observed",
        "no `lane_gate_status`",
        "paper_horizon_duration_s = 10.0",
        "paper_step_sizes_s = [0.01, 0.001]",
        "threshold_violations",
        "max_relative_total_energy_drift",
        "max_abs_det_minus_one",
        "spinning_box_comparison_pass_gate_not_enabled",
        "No `experiment.*` claim is passed in this phase.",
        "## Artifacts",
        "generated reports: not committed",
        "## Verification Commands",
        "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_single_body_report_lane",
        "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_runner tests.test_spinning_box_comparison",
        "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py",
        "git diff --check",
    )
    for snippet in required_snippets:
        if snippet not in text:
            fail(f"Phase 28 record missing required evidence field: {snippet}")
    if "TO_BE_BACKFILLED_PHASE28_DOCS_COMMIT" in text:
        fail("Phase 28 record contains stale docs commit placeholder")
    if "pending branch-local" in text:
        fail("Phase 28 record contains pending branch-local provenance placeholder")
    forbidden_snippets = (
        "Phase 28 verifies the paper spinning-box experiment",
        "Phase 28 passes experiment.single_body.spinning_box",
        "Phase 28 passes the M-ABD lane",
        "Phase 28 passes the spinning-box comparison",
        "Phase 28 verifies paper-faithful affine collision",
        "Phase 28 verifies collision detection",
        "Phase 28 verifies implicit contact solve",
        "Phase 28 verifies paper timing",
        "Phase 28 verifies paper trajectory agreement",
    )
    for snippet in forbidden_snippets:
        if snippet in text:
            fail(f"Phase 28 record overclaims unsupported evidence: {snippet}")

    data = read_yaml(ROOT / "docs/reference/paper-claims.yaml")
    claims = data.get("claims")
    if not isinstance(claims, list):
        fail("paper-claims.yaml missing claims list")
    for claim in claims:
        if isinstance(claim, dict) and str(claim.get("claim_id", "")).startswith("experiment."):
            if claim.get("reproduction_status") == "passed":
                fail("Phase 28 must not pass experiment.* claims")

    matrix = load_experiment_matrix(ROOT / "configs/experiments/paper_experiment_matrix.yaml")
    spinning_box = next(
        experiment
        for experiment in matrix.experiments
        if experiment.claim_id == "experiment.single_body.spinning_box"
    )
    if "mabd_newton_report_incomplete" not in spinning_box.blocking_reasons:
        fail("Phase 28 spinning-box matrix must retain incomplete M-ABD lane blocker")
    if "spinning_box_comparison_report_incomplete" not in spinning_box.blocking_reasons:
        fail("Phase 28 spinning-box matrix must retain incomplete comparison report blocker")


def validate_phase29_record() -> None:
    record_path = ROOT / "docs/records/2026-05-17-phase29-spinning-box-kinematic-feasibility.md"
    text = record_path.read_text(encoding="utf-8")
    required_snippets = (
        "## Status\n\npassed",
        "## Config Path",
        "configs/experiments/single_body_spinning_box.yaml",
        "configs/experiments/paper_experiment_matrix.yaml",
        "## Repository",
        "base commit: `df9ff5f`",
        "design commit: `68a95b6`",
        "plan commit: `d18942c`",
        "helper implementation commit: `7cec405`",
        "report implementation commit: `061f916`",
        "docs/record commit:",
        "independent review:",
        "## Vendored Newton",
        "96713fa965463b69c229a4d30582c733ff3526bb",
        "local patch status: Phase 29 does not modify vendored Newton",
        "## Paper Source",
        "PDF SHA256:",
        "TeX source SHA256:",
        "experiment.tex:40-55",
        "## Environment",
        "mabd-newton-py310",
        "physics-primitive-newton-py310",
        "smoke_passed",
        "mutates_reference_environment=false",
        "uses_reference_python=false",
        "uses_ambient_python=false",
        "## Metrics And Diagnostics",
        "paper_angular_speed_rad_s = 60000.0",
        "paper_angular_momentum_norm_kg_m2_s = 100.0",
        "h = 0.01 orthogonal_update_angular_speed_bound_rad_s = 100.0",
        "h = 0.01 orthogonal_update_angular_momentum_bound_kg_m2_s =",
        "0.16666666666666666",
        "h = 0.01 required_speed_to_bound_ratio = 600.0",
        "h = 0.001 orthogonal_update_angular_speed_bound_rad_s = 1000.0",
        "h = 0.001 orthogonal_update_angular_momentum_bound_kg_m2_s =",
        "1.6666666666666667",
        "h = 0.001 required_speed_to_bound_ratio = 60.0",
        "paper_momentum_requires_affine_stretch_under_q_delta_over_h",
        "qd_next=(q_next-q_n)/h",
        "no `lane_gate_status`",
        "No `experiment.*` claim is passed in this phase.",
        "## Artifacts",
        "generated reports: not committed",
        "## Verification Commands",
        "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_rigid_baselines",
        "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_single_body_report_lane",
        "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py",
        "git diff --check",
    )
    for snippet in required_snippets:
        if snippet not in text:
            fail(f"Phase 29 record missing required evidence field: {snippet}")
    if "TO_BE_BACKFILLED_PHASE29_DOCS_COMMIT" in text:
        fail("Phase 29 record contains stale docs commit placeholder")
    if "pending branch-local" in text:
        fail("Phase 29 record contains pending branch-local provenance placeholder")
    forbidden_snippets = (
        "Phase 29 verifies the paper spinning-box experiment",
        "Phase 29 passes experiment.single_body.spinning_box",
        "Phase 29 passes the M-ABD lane",
        "Phase 29 passes the spinning-box comparison",
        "Phase 29 fixes the M-ABD solver",
        "Phase 29 verifies paper-faithful affine collision",
        "Phase 29 verifies collision detection",
        "Phase 29 verifies implicit contact solve",
        "Phase 29 verifies paper timing",
        "Phase 29 verifies paper trajectory agreement",
    )
    for snippet in forbidden_snippets:
        if snippet in text:
            fail(f"Phase 29 record overclaims unsupported evidence: {snippet}")

    data = read_yaml(ROOT / "docs/reference/paper-claims.yaml")
    claims = data.get("claims")
    if not isinstance(claims, list):
        fail("paper-claims.yaml missing claims list")
    for claim in claims:
        if isinstance(claim, dict) and str(claim.get("claim_id", "")).startswith("experiment."):
            if claim.get("reproduction_status") == "passed":
                fail("Phase 29 must not pass experiment.* claims")

    config = load_spinning_box_config(ROOT / "configs/experiments/single_body_spinning_box.yaml")
    coarse = spinning_box_kinematic_feasibility(config, 0.01)
    fine = spinning_box_kinematic_feasibility(config, 0.001)
    if coarse.status != "paper_momentum_requires_affine_stretch_under_q_delta_over_h":
        fail("Phase 29 coarse feasibility status changed")
    if fine.status != "paper_momentum_requires_affine_stretch_under_q_delta_over_h":
        fail("Phase 29 fine feasibility status changed")
    if not np.isclose(coarse.paper_angular_speed_rad_s, 60000.0):
        fail("Phase 29 paper angular speed changed")
    if not np.isclose(coarse.orthogonal_update_angular_speed_bound_rad_s, 100.0):
        fail("Phase 29 coarse orthogonal speed bound changed")
    if not np.isclose(fine.orthogonal_update_angular_speed_bound_rad_s, 1000.0):
        fail("Phase 29 fine orthogonal speed bound changed")
    if not np.isclose(coarse.paper_angular_momentum_norm_kg_m2_s, 100.0):
        fail("Phase 29 paper angular momentum norm changed")
    if not np.isclose(coarse.orthogonal_update_angular_momentum_bound_kg_m2_s, 1.0 / 6.0):
        fail("Phase 29 coarse angular momentum bound changed")
    if not np.isclose(fine.orthogonal_update_angular_momentum_bound_kg_m2_s, 10.0 / 6.0):
        fail("Phase 29 fine angular momentum bound changed")
    if not np.isclose(coarse.required_speed_to_bound_ratio, 600.0):
        fail("Phase 29 coarse speed ratio changed")
    if not np.isclose(fine.required_speed_to_bound_ratio, 60.0):
        fail("Phase 29 fine speed ratio changed")

    matrix = load_experiment_matrix(ROOT / "configs/experiments/paper_experiment_matrix.yaml")
    spinning_box = next(
        experiment
        for experiment in matrix.experiments
        if experiment.claim_id == "experiment.single_body.spinning_box"
    )
    if "mabd_newton_report_incomplete" not in spinning_box.blocking_reasons:
        fail("Phase 29 spinning-box matrix must retain incomplete M-ABD lane blocker")
    if "spinning_box_comparison_report_incomplete" not in spinning_box.blocking_reasons:
        fail("Phase 29 spinning-box matrix must retain incomplete comparison report blocker")


def validate_phase30_record() -> None:
    record_path = ROOT / "docs/records/2026-05-17-phase30-velocity-semantics-source-audit.md"
    text = record_path.read_text(encoding="utf-8")
    required_snippets = (
        "## Status\n\npassed",
        "## Config Path",
        "configs/experiments/single_body_spinning_box.yaml",
        "configs/experiments/paper_experiment_matrix.yaml",
        "## Repository",
        "base commit: `6683d92`",
        "design/plan commit: `c97ee49`",
        "source-audit implementation commit: `d180e58`",
        "docs/record commit: `ee188d0`",
        "review hardening commit: `ebc9c25`",
        "## Vendored Newton",
        "96713fa965463b69c229a4d30582c733ff3526bb",
        "local patch status: Phase 30 does not modify vendored Newton",
        "## Paper Source",
        "arXiv ID: `2603.08079`",
        "arXiv version: `v2`",
        "source root setup: `/tmp/mabd-paper/source` must exist locally",
        "sections/singleabd.tex SHA256:",
        "0f18165cba13d358a07c67a652e728170abecd7372b5ba905ff2b4a5950a3e8d",
        "sections/solver.tex SHA256:",
        "871dbd7ae7f5544b95c6c4dc0940cb6a0e73eca48415b1abed2e3599db90c97e",
        "sections/experiment.tex SHA256:",
        "c5927183fe4e3f1c1c1617e5b10b7e9006da6a9eac537e891cb1dac03d58dd0f",
        "images/cube/roll_cube.pdf SHA256:",
        "7669b062348324a3b0090cc9f44930655c83233a87f63389db9198b88f95ae80",
        "singleabd.tex:34-42",
        "solver.tex:219-241",
        "experiment.tex:40-55",
        "scanned TeX source includes: `arxiv.tex`, `sections/singleabd.tex`, `sections/solver.tex`, `sections/experiment.tex`, `sections_a/multiabd.tex`",
        "## Environment",
        "mabd-newton-py310",
        "physics-primitive-newton-py310",
        "smoke_passed",
        "mutates_reference_environment=false",
        "uses_reference_python=false",
        "uses_ambient_python=false",
        "## Metrics And Diagnostics",
        "audit_status = source_does_not_prove_decoupled_velocity_semantics",
        "implicit_euler_inertia_potential = present",
        "g_map_twist_velocity = present",
        "wrench_map_generalized_force = present",
        "spinning_box_twist_initialization = present",
        "source_does_not_specify_decoupled_velocity_semantics",
        "source_does_not_specify_alternative_momentum_extraction",
        "No `experiment.*` claim is passed in this phase.",
        "## Artifacts",
        "raw paper assets: not committed",
        "generated reports: not committed",
        "## Verification Commands",
        "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_paper_source_audit",
        "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_phase0_bootstrap",
        "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py",
        "git diff --check",
    )
    for snippet in required_snippets:
        if snippet not in text:
            fail(f"Phase 30 record missing required evidence field: {snippet}")
    if "TO_BE_BACKFILLED_PHASE30_DOCS_COMMIT" in text:
        fail("Phase 30 record contains stale docs commit placeholder")
    if "to be recorded after the Phase 30 docs commit" in text:
        fail("Phase 30 record contains stale docs commit placeholder")
    if "pending branch-local" in text:
        fail("Phase 30 record contains pending branch-local provenance placeholder")
    forbidden_snippets = (
        "Phase 30 verifies the paper spinning-box experiment",
        "Phase 30 passes experiment.single_body.spinning_box",
        "Phase 30 passes the M-ABD lane",
        "Phase 30 passes the spinning-box comparison",
        "Phase 30 fixes the M-ABD solver",
        "Phase 30 verifies decoupled velocity semantics",
        "Phase 30 verifies alternative momentum extraction",
        "Phase 30 verifies paper timing",
        "Phase 30 verifies paper trajectory agreement",
    )
    for snippet in forbidden_snippets:
        if snippet in text:
            fail(f"Phase 30 record overclaims unsupported evidence: {snippet}")

    if not PAPER_SOURCE_ROOT.exists():
        fail(f"Phase 30 paper source root missing: {PAPER_SOURCE_ROOT}")
    audit = velocity_semantics_source_audit(PAPER_SOURCE_ROOT)
    if audit.status != "source_does_not_prove_decoupled_velocity_semantics":
        fail("Phase 30 source audit status changed")
    findings = {finding.key: finding for finding in audit.findings}
    for key in (
        "implicit_euler_inertia_potential",
        "g_map_twist_velocity",
        "wrench_map_generalized_force",
        "spinning_box_twist_initialization",
    ):
        if not findings[key].present:
            fail(f"Phase 30 source audit missing positive finding: {key}")
    if findings["decoupled_velocity_semantics"].present:
        fail("Phase 30 source audit found unexpected decoupled velocity semantics")
    if findings["alternative_momentum_extraction"].present:
        fail("Phase 30 source audit found unexpected alternative momentum extraction")
    for blocker in (
        "source_does_not_specify_decoupled_velocity_semantics",
        "source_does_not_specify_alternative_momentum_extraction",
    ):
        if blocker not in audit.blockers:
            fail(f"Phase 30 source audit missing blocker: {blocker}")
    for relative_path in (
        "arxiv.tex",
        "sections/singleabd.tex",
        "sections/solver.tex",
        "sections/experiment.tex",
        "sections_a/multiabd.tex",
    ):
        if relative_path not in audit.scanned_tex_paths:
            fail(f"Phase 30 source audit did not scan {relative_path}")
    for relative_path, expected_hash in {
        "sections/singleabd.tex": (
            "0f18165cba13d358a07c67a652e728170abecd7372b5ba905ff2b4a5950a3e8d"
        ),
        "sections/solver.tex": (
            "871dbd7ae7f5544b95c6c4dc0940cb6a0e73eca48415b1abed2e3599db90c97e"
        ),
        "sections/experiment.tex": (
            "c5927183fe4e3f1c1c1617e5b10b7e9006da6a9eac537e891cb1dac03d58dd0f"
        ),
        "images/cube/roll_cube.pdf": (
            "7669b062348324a3b0090cc9f44930655c83233a87f63389db9198b88f95ae80"
        ),
    }.items():
        if audit.file_hashes[relative_path] != expected_hash:
            fail(f"Phase 30 source audit hash changed for {relative_path}")

    data = read_yaml(ROOT / "docs/reference/paper-claims.yaml")
    claims = data.get("claims")
    if not isinstance(claims, list):
        fail("paper-claims.yaml missing claims list")
    for claim in claims:
        if isinstance(claim, dict) and str(claim.get("claim_id", "")).startswith("experiment."):
            if claim.get("reproduction_status") == "passed":
                fail("Phase 30 must not pass experiment.* claims")

    matrix = load_experiment_matrix(ROOT / "configs/experiments/paper_experiment_matrix.yaml")
    spinning_box = next(
        experiment
        for experiment in matrix.experiments
        if experiment.claim_id == "experiment.single_body.spinning_box"
    )
    if "mabd_newton_report_incomplete" not in spinning_box.blocking_reasons:
        fail("Phase 30 spinning-box matrix must retain incomplete M-ABD lane blocker")
    if "spinning_box_comparison_report_incomplete" not in spinning_box.blocking_reasons:
        fail("Phase 30 spinning-box matrix must retain incomplete comparison report blocker")


def validate_phase31_record() -> None:
    record_path = ROOT / "docs/records/2026-05-17-phase31-official-artifact-availability.md"
    text = record_path.read_text(encoding="utf-8")
    required_snippets = (
        "## Status\n\npassed",
        "## Config Path",
        "configs/experiments/paper_experiment_matrix.yaml",
        "docs/reference/official-artifact-sources.yaml",
        "## Repository",
        "base commit: `6093ae4`",
        "## Vendored Newton",
        "96713fa965463b69c229a4d30582c733ff3526bb",
        "local patch status: Phase 31 does not modify vendored Newton",
        "## Paper Source",
        "arXiv ID: `2603.08079`",
        "arXiv version: `v2`",
        "sections/experiment.tex:38",
        "## Environment",
        "mabd-newton-py310",
        "physics-primitive-newton-py310",
        "smoke_passed",
        "mutates_reference_environment=false",
        "uses_reference_python=false",
        "uses_ambient_python=false",
        "## External Source Audit",
        "audited_on_utc: `2026-05-17`",
        (
            "status: "
            "`official_project_and_video_found_implementation_code_coming_soon_as_of_2026-05-17`"
        ),
        "https://arxiv.org/abs/2603.08079",
        "https://s2026.conference-schedule.org/presentation/?id=papers_116&sess=sess102",
        "https://www.minghaoguo.com/",
        "https://minsuglly.github.io/content.json",
        "https://minsuglly.github.io/mabd/",
        "https://www.youtube-nocookie.com/embed/xnLCdUfq52w?rel=0",
        "https://github.com/MINSUGLLY/mabd",
        "https://yangzzzy.github.io/",
        "https://api.github.com/search/repositories?q=",
        "total_count = 0",
        "incomplete_results = false",
        "official_implementation_code_marked_coming_soon",
        "official_implementation_code_not_found_in_audited_public_sources",
        "not proof of private author-code absence",
        "No `experiment.*` claim is passed in this phase.",
        "## Artifacts",
        "structured manifest: `docs/reference/official-artifact-sources.yaml`",
        "raw web pages: not committed",
        "generated reports: not committed",
        "## Verification Commands",
        "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_official_artifact_audit",
        "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_phase0_bootstrap",
        "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py",
        "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/env/readiness_check.py",
        "git diff --check",
    )
    for snippet in required_snippets:
        if snippet not in text:
            fail(f"Phase 31 record missing required evidence field: {snippet}")
    if "TO_BE_BACKFILLED_PHASE31_DOCS_COMMIT" in text:
        fail("Phase 31 record contains stale docs commit placeholder")
    if "pending branch-local" in text:
        fail("Phase 31 record contains pending branch-local provenance placeholder")
    for stale_snippet in (
        "not_found_in_audited_public_sources_as_of_2026-05-17",
        "official_code_repository_url_missing",
        "official_project_page_url_missing",
        "official_supplementary_video_url_missing",
    ):
        if stale_snippet in text:
            fail(f"Phase 31 record contains stale artifact-audit status: {stale_snippet}")

    lower_text = text.lower()
    forbidden_snippets = (
        "official code does not exist",
        "no private author code exists",
        "full reproduction complete",
        "phase 31 verifies the paper spinning-box experiment",
        "phase 31 passes experiment.single_body.spinning_box",
        "phase 31 fixes the m-abd solver",
        "phase 31 verifies paper timing",
        "phase 31 verifies paper trajectory agreement",
    )
    for snippet in forbidden_snippets:
        if snippet in lower_text:
            fail(f"Phase 31 record overclaims unsupported evidence: {snippet}")

    manifest = read_yaml(ROOT / "docs/reference/official-artifact-sources.yaml")
    audit = manifest.get("audit")
    if not isinstance(audit, dict):
        fail("official-artifact-sources.yaml missing audit mapping")
    if audit.get("id") != "phase31-official-artifact-availability":
        fail("Phase 31 artifact manifest has wrong audit id")
    if audit.get("audited_on_utc") != "2026-05-17":
        fail("Phase 31 artifact manifest has wrong audit date")
    if (
        audit.get("status")
        != "official_project_and_video_found_implementation_code_coming_soon_as_of_2026-05-17"
    ):
        fail("Phase 31 artifact manifest has wrong scoped status")
    scope_boundary = str(audit.get("scope_boundary", ""))
    if "not proof of private author-code absence" not in scope_boundary:
        fail("Phase 31 artifact manifest must keep private-code boundary")
    blockers = audit.get("blockers")
    if not isinstance(blockers, list):
        fail("Phase 31 artifact manifest missing blockers list")
    for blocker in (
        "official_implementation_code_marked_coming_soon",
        "official_implementation_code_not_found_in_audited_public_sources",
    ):
        if blocker not in blockers:
            fail(f"Phase 31 artifact manifest missing blocker: {blocker}")
    for stale_blocker in (
        "official_code_repository_url_missing",
        "official_project_page_url_missing",
        "official_supplementary_video_url_missing",
    ):
        if stale_blocker in blockers:
            fail(f"Phase 31 artifact manifest contains stale blocker: {stale_blocker}")

    paper = manifest.get("paper")
    if not isinstance(paper, dict):
        fail("official-artifact-sources.yaml missing paper mapping")
    if paper.get("arxiv_id") != "2603.08079" or paper.get("arxiv_version") != "v2":
        fail("Phase 31 artifact manifest has wrong arXiv metadata")

    sources = manifest.get("audited_sources")
    if not isinstance(sources, list):
        fail("official-artifact-sources.yaml missing audited_sources list")
    source_map = {source.get("source_id"): source for source in sources if isinstance(source, dict)}
    required_source_ids = (
        "arxiv_abs_2603_08079",
        "siggraph_2026_schedule_papers_116",
        "minghao_guo_author_page",
        "zhiyong_he_author_content",
        "first_author_project_page",
        "first_author_github_mabd_repo",
        "yin_yang_author_page",
        "paper_tex_source_tree",
        "github_repository_exact_search",
    )
    for source_id in required_source_ids:
        if source_id not in source_map:
            fail(f"Phase 31 artifact manifest missing audited source: {source_id}")
    for source_id, source in source_map.items():
        if "url" not in source or "observation" not in source:
            fail(f"Phase 31 source {source_id} must include url and observation")
        if source.get("has_official_implementation_code_link") is not False:
            fail(f"Phase 31 source {source_id} must not report implementation code")
    if source_map["github_repository_exact_search"].get("official") is not False:
        fail("GitHub repository search must not be classified as an official source")
    if source_map["github_repository_exact_search"].get("observed_total_count") != 0:
        fail("GitHub repository exact search result changed from total_count 0")
    if source_map["github_repository_exact_search"].get("incomplete_results") is not False:
        fail("GitHub repository exact search must report incomplete_results false")
    tex_source = source_map["paper_tex_source_tree"]
    if tex_source.get("mentions_supplementary_video") is not True:
        fail("Phase 31 TeX source audit must record supplementary-video mention")
    if tex_source.get("has_supplementary_video_url") is not False:
        fail("Phase 31 TeX source audit must record missing supplementary-video URL")
    if source_map["zhiyong_he_author_content"].get("has_official_project_page_link") is not True:
        fail("Phase 31 first-author homepage data must record the project page link")
    project_page = source_map["first_author_project_page"]
    if project_page.get("has_official_project_page_link") is not True:
        fail("Phase 31 first-author project page must be recorded as found")
    if project_page.get("implementation_code_status") != "coming_soon":
        fail("Phase 31 first-author project page must mark implementation code coming soon")
    if project_page.get("has_supplementary_video_url") is not True:
        fail("Phase 31 first-author project page must record supplementary video availability")
    if (
        project_page.get("supplementary_video_url")
        != "https://www.youtube-nocookie.com/embed/xnLCdUfq52w?rel=0"
    ):
        fail("Phase 31 first-author project page must record the supplementary video URL")
    github_page_repo = source_map["first_author_github_mabd_repo"]
    if github_page_repo.get("repository_url") != "https://github.com/MINSUGLLY/mabd":
        fail("Phase 31 first-author mabd repository must record its GitHub URL")
    if github_page_repo.get("repository_language") != "HTML":
        fail("Phase 31 first-author mabd repository must be HTML project-page source")
    if github_page_repo.get("root_contents") != ["index.html", "static"]:
        fail("Phase 31 first-author mabd repository must record project-page root contents")
    if github_page_repo.get("has_pages") is not True:
        fail("Phase 31 first-author mabd repository must record GitHub Pages availability")
    if github_page_repo.get("has_supplementary_video_url") is not False:
        fail("Phase 31 first-author mabd repository must not duplicate project-page video evidence")
    if github_page_repo.get("implementation_code_status") != "project_page_source_only":
        fail("Phase 31 first-author mabd repository must not be treated as solver code")

    manifest_text = (ROOT / "docs/reference/official-artifact-sources.yaml").read_text(
        encoding="utf-8"
    )
    for placeholder in ("TO_BE_BACKFILLED_PHASE31", "pending branch-local"):
        if placeholder in manifest_text:
            fail("Phase 31 artifact manifest contains stale docs commit placeholder")
    manifest_lower = manifest_text.lower()
    for snippet in (
        "official code does not exist",
        "no private author code exists",
        "full reproduction complete",
    ):
        if snippet in manifest_lower:
            fail(f"Phase 31 artifact manifest overclaims unsupported evidence: {snippet}")
    for stale_snippet in (
        "official_code_repository_url_missing",
        "official_project_page_url_missing",
        "official_supplementary_video_url_missing",
    ):
        if stale_snippet in manifest_text:
            fail(f"Phase 31 artifact manifest contains stale availability gap: {stale_snippet}")

    data = read_yaml(ROOT / "docs/reference/paper-claims.yaml")
    claims = data.get("claims")
    if not isinstance(claims, list):
        fail("paper-claims.yaml missing claims list")
    for claim in claims:
        if isinstance(claim, dict) and str(claim.get("claim_id", "")).startswith("experiment."):
            if claim.get("reproduction_status") == "passed":
                fail("Phase 31 must not pass experiment.* claims")

    matrix = load_experiment_matrix(ROOT / "configs/experiments/paper_experiment_matrix.yaml")
    spinning_box = next(
        experiment
        for experiment in matrix.experiments
        if experiment.claim_id == "experiment.single_body.spinning_box"
    )
    if "mabd_newton_report_incomplete" not in spinning_box.blocking_reasons:
        fail("Phase 31 spinning-box matrix must retain incomplete M-ABD lane blocker")
    if "spinning_box_comparison_report_incomplete" not in spinning_box.blocking_reasons:
        fail("Phase 31 spinning-box matrix must retain incomplete comparison report blocker")


def validate_phase32_record() -> None:
    record_path = ROOT / "docs/records/2026-05-17-phase32-gravity-force-mapping.md"
    text = record_path.read_text(encoding="utf-8")
    required_snippets = (
        "## Status\n\npassed",
        "## Config Path",
        "No experiment config is changed in Phase 32.",
        "## Repository",
        "base commit: `f8d36da`",
        "phase32-gravity-force-mapping",
        "## Vendored Newton",
        "96713fa965463b69c229a4d30582c733ff3526bb",
        "local patch status: Phase 32 modifies vendored Newton M-ABD CPU oracle code",
        "vendor/newton/newton/_src/solvers/mabd/affine_math.py",
        "vendor/newton/newton/_src/solvers/mabd/__init__.py",
        "vendor/newton/newton/_src/solvers/mabd/step_oracle.py",
        "vendor/newton/newton/tests/test_mabd_single_body.py",
        "vendor/newton/newton/tests/test_mabd_phase4_solver_step.py",
        "## Paper Source",
        "PDF SHA256: `a594e79093673c60fc59ad14f9b71f29a8f7f8e7b1c3d9c73efe6f5814cc6ec0`",
        "TeX source SHA256:",
        "/tmp/mabd-paper/source/sections/singleabd.tex:23-26",
        "/tmp/mabd-paper/source/sections/singleabd.tex:42",
        "/tmp/mabd-paper/source/sections/singleabd.tex:55-58",
        "/tmp/mabd-paper/source/sections/solver.tex:238-242",
        "non-claim experiment motivation, not passed evidence",
        "/tmp/mabd-paper/source/sections/experiment.tex:67-75",
        "/tmp/mabd-paper/source/sections/experiment.tex:80-91",
        "## Environment",
        "mabd-newton-py310",
        "physics-primitive-newton-py310",
        "smoke_passed",
        "mutates_reference_environment=false",
        "uses_reference_python=false",
        "uses_ambient_python=false",
        "## Method Evidence",
        "mabd.gravity_generalized_force(rest_points, masses, gravity)",
        "MABDCPUOracleConfig.gravity",
        "sum_i point_jacobian(rest_point_i).T @ (mass_i * gravity)",
        "method.force_mapping.gravity_generalized_force",
        "reproduction status: `passed`",
        "## TDD Evidence",
        "AttributeError: gravity_generalized_force missing",
        "unexpected keyword argument 'gravity'",
        "Ran 42 tests, OK",
        "Ran 22 tests, OK",
        "## Claim Impact",
        "No `experiment.*` claim is passed.",
        "Heavy-top and physical-pendulum experiments remain intended",
        "## Verification Commands",
        "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_mabd_single_body tests.test_mabd_phase4_solver_step tests.test_phase0_bootstrap",
        "PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest newton.tests.test_mabd_single_body newton.tests.test_mabd_phase4_solver_step",
        "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py",
        "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .",
        "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests",
        "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/env/readiness_check.py",
        'PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"',
        "git diff --check",
    )
    for snippet in required_snippets:
        if snippet not in text:
            fail(f"Phase 32 record missing required evidence field: {snippet}")
    for placeholder in ("TO_BE_BACKFILLED_PHASE32", "pending branch-local"):
        if placeholder in text:
            fail("Phase 32 record contains stale placeholder")

    lower_text = text.lower()
    for snippet in (
        "phase 32 passes experiment",
        "heavy-top experiment passed",
        "physical-pendulum experiment passed",
        "full reproduction complete",
        "paper timing verified",
        "contact solve implemented",
    ):
        if snippet in lower_text:
            fail(f"Phase 32 record overclaims unsupported evidence: {snippet}")

    data = read_yaml(ROOT / "docs/reference/paper-claims.yaml")
    claims = data.get("claims")
    if not isinstance(claims, list):
        fail("paper-claims.yaml missing claims list")
    claim_map = {claim.get("claim_id"): claim for claim in claims if isinstance(claim, dict)}
    gravity_claim = claim_map.get("method.force_mapping.gravity_generalized_force")
    if not isinstance(gravity_claim, dict):
        fail("paper-claims.yaml missing gravity generalized force claim")
    if gravity_claim.get("reproduction_status") != "passed":
        fail("gravity generalized force claim must be passed after Phase 32")
    for snippet in (
        "J_i^T m_i g",
        "singleabd.tex:23-26,42,55-58",
        "solver.tex:238-242",
        "CPU oracle force mapping",
        "not heavy-top",
        "pendulum",
    ):
        gravity_claim_text = " ".join(str(value) for value in gravity_claim.values())
        if snippet not in gravity_claim_text:
            fail(f"gravity generalized force claim must stay bounded: {snippet}")
    if "experiment.tex:67-75" in gravity_claim_text or "experiment.tex:80-91" in gravity_claim_text:
        fail("gravity generalized force claim must not cite experiment result lines as passed evidence")
    for claim in claims:
        if isinstance(claim, dict) and str(claim.get("claim_id", "")).startswith("experiment."):
            if claim.get("reproduction_status") == "passed":
                fail("Phase 32 must not pass experiment.* claims")


def validate_phase33_record() -> None:
    record_path = ROOT / "docs/records/2026-05-17-phase33-physical-pendulum-analytic-reference.md"
    text = record_path.read_text(encoding="utf-8")
    required_snippets = (
        "## Status\n\npassed",
        "## Config Path",
        "configs/experiments/single_body_physical_pendulum.yaml",
        "configs/experiments/paper_experiment_matrix.yaml",
        "## Repository",
        "base commit: `52fa600`",
        "phase33-physical-pendulum-reference",
        "## Vendored Newton",
        "96713fa965463b69c229a4d30582c733ff3526bb",
        "local patch status: Phase 33 does not modify vendored Newton",
        "## Paper Source",
        "arXiv ID: `2603.08079`",
        "arXiv version: `v2`",
        "PDF SHA256: `a594e79093673c60fc59ad14f9b71f29a8f7f8e7b1c3d9c73efe6f5814cc6ec0`",
        "`sections/experiment.tex` SHA256:",
        "`c5927183fe4e3f1c1c1617e5b10b7e9006da6a9eac537e891cb1dac03d58dd0f`",
        "/tmp/mabd-paper/source/sections/experiment.tex:77-91",
        "theta(t)=pi/2 - 2 asin(kappa * sn(K(kappa) - omega_lin * t, kappa))",
        "## Environment",
        "mabd-newton-py310",
        "physics-primitive-newton-py310",
        "smoke_passed",
        "SciPy: `1.15.3`",
        "mutates_reference_environment=false",
        "uses_reference_python=false",
        "uses_ambient_python=false",
        "## Analytic Reference Evidence",
        "src/mabd_reproduction/physical_pendulum_reference.py",
        "src/mabd_reproduction/physical_pendulum_reports.py",
        "load_physical_pendulum_config",
        "validate_physical_pendulum_config_against_matrix",
        "run_physical_pendulum_analytic_reference",
        "--lane analytic_reference",
        "physical_pendulum_angle_reference",
        "m = kappa**2",
        "theta(0)=0",
        "theta(K/omega_lin)=pi/2",
        "theta(2K/omega_lin)=pi",
        "lane_status = passed",
        "top-level report status: `incomplete`",
        "reports/experiment_matrix/single_body_physical_pendulum_analytic_reference.json",
        "review hardening:",
        "`lane_status` is derived from threshold violations",
        "required missing lanes",
        "reference parameters are cross-validated",
        "## Metrics And Thresholds",
        "random seed: not applicable deterministic analytic formula",
        "metric: `max_abs_reference_identity_error = 2.220446049250313e-16`",
        "max_abs_reference_identity_error <= 1.0e-12",
        "threshold status: `passed`",
        "K(kappa) = 1.8540746773013719",
        "period_s: `2.3678419475762373`",
        "checkpoint time_s: `[0.0, 0.5919604868940593, 1.1839209737881187]`",
        "checkpoint observed angle_rad:",
        "[-2.220446049250313e-16, 1.5707963267948966, 3.141592653589793]",
        "checkpoint expected angle_rad:",
        "[0.0, 1.5707963267948966, 3.141592653589793]",
        "compact sample count: `9`",
        "## TDD Evidence",
        "FAILED (failures=1, errors=5)",
        "physical_pendulum_reference",
        "run_physical_pendulum_analytic_reference",
        "--lane analytic_reference",
        "Ran 37 tests",
        "OK",
        "## Claim Impact",
        "No `experiment.*` claim is passed.",
        "`experiment.single_body.physical_pendulum` remains not passed.",
        "M-ABD simulation lane remains missing",
        "RBD implicit baseline remains missing",
        "Joint-force waveform agreement remains missing",
        "`pendulum_geometry_unknown` remains a blocker",
        "analytic-reference lane evidence only",
        "## Verification Commands",
        "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_physical_pendulum_reference tests.test_experiment_run_configs tests.test_experiment_runner",
        "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_phase0_bootstrap",
        "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py",
        "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .",
        "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests",
        "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/env/readiness_check.py",
        'PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"',
        "git diff --check",
    )
    for snippet in required_snippets:
        if snippet not in text:
            fail(f"Phase 33 record missing required evidence field: {snippet}")
    for placeholder in ("TO_BE_BACKFILLED_PHASE33", "pending branch-local"):
        if placeholder in text:
            fail("Phase 33 record contains stale placeholder")

    lower_text = text.lower()
    for snippet in (
        "physical-pendulum experiment passed",
        "physical pendulum experiment passed",
        "full reproduction complete",
        "paper timing verified",
        "joint-force agreement passed",
        "m-abd physical-pendulum dynamics passed",
    ):
        if snippet in lower_text:
            fail(f"Phase 33 record overclaims unsupported evidence: {snippet}")

    try:
        config = load_physical_pendulum_config(
            ROOT / "configs/experiments/single_body_physical_pendulum.yaml"
        )
        matrix = load_experiment_matrix(ROOT / "configs/experiments/paper_experiment_matrix.yaml")
        validate_physical_pendulum_config_against_matrix(config, matrix)
    except (ExperimentRunConfigError, ExperimentMatrixError) as exc:
        fail(f"Phase 33 physical-pendulum config validation failed: {exc}")
    if config.baseline_lane != "analytic_reference":
        fail("Phase 33 config must target analytic_reference baseline lane")
    if config.report_status.value != "incomplete":
        fail("Phase 33 physical-pendulum report status must remain incomplete")
    if config.required_missing_lanes != ("mabd_newton",):
        fail("current physical-pendulum missing lanes must keep only mabd_newton")
    if "pendulum_geometry_unknown" not in config.failure_reason:
        fail("Phase 33 physical-pendulum failure reason must retain geometry blocker")

    claims = read_yaml(ROOT / "docs/reference/paper-claims.yaml").get("claims")
    if not isinstance(claims, list):
        fail("paper-claims.yaml missing claims list")
    for claim in claims:
        if isinstance(claim, dict) and str(claim.get("claim_id", "")).startswith("experiment."):
            if claim.get("reproduction_status") == "passed":
                fail("Phase 33 must not pass experiment.* claims")


def validate_phase34_record() -> None:
    record_path = ROOT / "docs/records/2026-05-17-phase34-world-anchor-physical-pendulum-mabd.md"
    text = record_path.read_text(encoding="utf-8")
    required_snippets = (
        "## Status\n\npassed",
        "## Config Path",
        "configs/experiments/single_body_physical_pendulum.yaml",
        "configs/experiments/paper_experiment_matrix.yaml",
        "## Repository",
        "base commit: `81785e0`",
        "phase34-physical-pendulum-mabd-lane",
        "2026-05-17-mabd-phase34-world-anchor-physical-pendulum-mabd.md",
        "2026-05-17-phase34-world-anchor-physical-pendulum-mabd-design.md",
        "## Vendored Newton",
        "96713fa965463b69c229a4d30582c733ff3526bb",
        "local patch status: Phase 34 modifies vendored Newton M-ABD CPU oracle code",
        "vendor/newton/newton/_src/solvers/mabd/step_oracle.py",
        "vendor/newton/newton/_src/solvers/mabd/__init__.py",
        "vendor/newton/newton/tests/test_mabd_phase4_solver_step.py",
        "## Paper Source",
        "arXiv ID: `2603.08079`",
        "arXiv version: `v2`",
        "PDF SHA256:",
        "/tmp/mabd-paper/source/sections/experiment.tex:77-91",
        "fixed pivot",
        "joint-force waveform comparison",
        "implicit RBD baseline comparison",
        "## Environment",
        "mabd-newton-py310",
        "physics-primitive-newton-py310",
        "smoke_passed",
        "mutates_reference_environment=false",
        "uses_reference_python=false",
        "uses_ambient_python=false",
        "## Newton World Anchor Evidence",
        "MABDCPUOracleWorldConstraint",
        "MABDCPUOracleConfig.world_constraints",
        "point_jacobian(rest_point)",
        "topology='dense'",
        "malformed rest/world vectors are rejected",
        "newton.tests.test_mabd_phase4_solver_step",
        "## Physical Pendulum M-ABD Diagnostic Evidence",
        "src/mabd_reproduction/physical_pendulum_mabd.py",
        "src/mabd_reproduction/physical_pendulum_reports.py",
        "load_physical_pendulum_config",
        "validate_physical_pendulum_config_against_matrix",
        "run_physical_pendulum_mabd_development",
        "--lane physical_pendulum_mabd_development",
        "mabd_cpu_oracle_physical_pendulum_development",
        "cpu_numpy_newton_only",
        "report lane: `physical_pendulum_mabd_development_diagnostic`",
        "lane_status = development_diagnostic_generated",
        "top-level report status: `incomplete`",
        "reports/experiment_matrix/single_body_physical_pendulum_mabd_development.json",
        "paper pendulum geometry remains unknown",
        "no implicit RBD baseline",
        "no joint-force waveform comparison",
        "required `mabd_newton` experiment lane remains listed as missing",
        "## Metrics And Thresholds",
        "random seed: not applicable deterministic config-driven CPU oracle rollout",
        "time_step_s: `0.01`",
        "step_count: `16`",
        "compact sample count: `5`",
        "max_pivot_residual_m <= 1.0e-10",
        "max_pivot_residual_m = 0.0",
        "max_constraint_residual_norm <= 1.0e-10",
        "max_constraint_residual_norm = 0.0",
        "max_abs_angle_error_rad <= 2.0",
        "max_abs_angle_error_rad = 0.007130697850637885",
        "threshold status: `passed`",
        "sample steps: `[0, 4, 8, 12, 16]`",
        "## TDD Evidence",
        "MABDCPUOracleWorldConstraint",
        "missing `mabd_development` config parsing",
        "invalid CLI choice `physical_pendulum_mabd_development`",
        "Ran 22 tests",
        "Ran 17 tests",
        "Ran 38 tests",
        "## Claim Impact",
        "No `experiment.*` claim is passed.",
        "`experiment.single_body.physical_pendulum` remains not passed.",
        "Newton-only M-ABD development diagnostic lane",
        "required physical-pendulum `mabd_newton` experiment lane remains missing",
        "RBD implicit baseline remains missing",
        "Joint-force waveform agreement remains missing",
        "Paper-faithful pendulum geometry remains missing",
        "`pendulum_geometry_unknown` remains a blocker",
        "## Verification Commands",
        "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_mabd_phase4_solver_step",
        "PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest newton.tests.test_mabd_phase4_solver_step",
        "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_run_configs tests.test_experiment_runner",
        "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_phase0_bootstrap",
        "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py",
        "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .",
        "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests",
        "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/env/readiness_check.py",
        'PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"',
        "git diff --check",
    )
    for snippet in required_snippets:
        if snippet not in text:
            fail(f"Phase 34 record missing required evidence field: {snippet}")
    for placeholder in ("TO_BE_BACKFILLED_PHASE34", "pending branch-local"):
        if placeholder in text:
            fail("Phase 34 record contains stale placeholder")

    lower_text = text.lower()
    for snippet in (
        "passed physical-pendulum experiment",
        "physical-pendulum experiment passed",
        "physical pendulum experiment passed",
        "full reproduction complete",
        "paper timing verified",
        "paper timing result",
        "joint-force agreement passed",
        "joint-force agreement result",
        "rbd baseline passed",
        "rbd baseline result",
        "paper-faithful pendulum geometry passed",
        "paper-faithful pendulum geometry result",
    ):
        if snippet in lower_text:
            fail(f"Phase 34 record overclaims unsupported evidence: {snippet}")

    try:
        config = load_physical_pendulum_config(
            ROOT / "configs/experiments/single_body_physical_pendulum.yaml"
        )
        matrix = load_experiment_matrix(ROOT / "configs/experiments/paper_experiment_matrix.yaml")
        validate_physical_pendulum_config_against_matrix(config, matrix)
    except (ExperimentRunConfigError, ExperimentMatrixError) as exc:
        fail(f"Phase 34 physical-pendulum config validation failed: {exc}")
    lane = config.mabd_development
    if config.baseline_lane != "analytic_reference":
        fail("Phase 34 config must keep analytic_reference as the config baseline lane")
    if config.report_status.value != "incomplete":
        fail("Phase 34 physical-pendulum report status must remain incomplete")
    if config.required_missing_lanes != ("mabd_newton",):
        fail("current physical-pendulum missing lanes must keep only mabd_newton")
    if lane.output_report != "reports/experiment_matrix/single_body_physical_pendulum_mabd_development.json":
        fail("Phase 34 M-ABD diagnostic output report changed")
    if lane.step_count != 16 or lane.sample_count != 5:
        fail("Phase 34 M-ABD diagnostic rollout size changed")
    if not np.isclose(lane.time_step_s, 0.01, rtol=0.0, atol=1.0e-15):
        fail("Phase 34 M-ABD diagnostic timestep changed")
    if lane.rest_points_m.shape != (4, 3) or lane.masses_kg.shape != (4,):
        fail("Phase 34 M-ABD diagnostic procedural point set changed shape")
    if not np.allclose(lane.pivot_rest_point_m, [0.0, 0.0, 0.0], rtol=0.0, atol=1.0e-15):
        fail("Phase 34 M-ABD diagnostic pivot rest point changed")
    if not np.allclose(lane.pivot_world_point_m, [0.0, 0.0, 0.0], rtol=0.0, atol=1.0e-15):
        fail("Phase 34 M-ABD diagnostic pivot world point changed")
    if not np.allclose(lane.gravity_m_s2, [0.0, -9.81, 0.0], rtol=0.0, atol=1.0e-15):
        fail("Phase 34 M-ABD diagnostic gravity changed")
    for key in (
        "max_pivot_residual_m",
        "max_constraint_residual_norm",
        "max_abs_angle_error_rad",
    ):
        if key not in lane.thresholds:
            fail(f"Phase 34 M-ABD diagnostic threshold missing: {key}")

    report = load_claim_report(ROOT / lane.output_report)
    if report.claim_id != config.claim_id:
        fail("Phase 34 report claim_id does not match config")
    if report.scene_id != config.scene_id:
        fail("Phase 34 report scene_id does not match config")
    if report.status.value != "incomplete":
        fail("Phase 34 report must remain incomplete")
    if report.baseline_lane != "physical_pendulum_mabd_development_diagnostic":
        fail("Phase 34 report must use the diagnostic baseline lane id")
    if report.solver_mode != "mabd_cpu_oracle_physical_pendulum_development":
        fail("Phase 34 report solver mode changed")
    observed = report.observed
    if observed.get("lane_status") != "development_diagnostic_generated":
        fail("Phase 34 report lane_status changed")
    if observed.get("full_experiment_claim_passed") is not False:
        fail("Phase 34 report must not pass the full experiment claim")
    if observed.get("required_missing_lanes") != ["mabd_newton"]:
        fail("Phase 34 report required missing lanes changed")
    if observed.get("threshold_violations") != []:
        fail("Phase 34 report threshold violations must remain empty")
    if not np.isclose(float(observed.get("max_pivot_residual_m")), 0.0, rtol=0.0, atol=1.0e-15):
        fail("Phase 34 report pivot residual changed")
    if not np.isclose(float(observed.get("max_constraint_residual_norm")), 0.0, rtol=0.0, atol=1.0e-15):
        fail("Phase 34 report constraint residual changed")
    if not np.isclose(
        float(observed.get("max_abs_angle_error_rad")),
        0.007130697850637885,
        rtol=0.0,
        atol=1.0e-15,
    ):
        fail("Phase 34 report max angle error changed")
    samples = observed.get("angle_samples_rad")
    if not isinstance(samples, list) or len(samples) != 5:
        fail("Phase 34 report must contain five compact angle samples")

    claims = read_yaml(ROOT / "docs/reference/paper-claims.yaml").get("claims")
    if not isinstance(claims, list):
        fail("paper-claims.yaml missing claims list")
    for claim in claims:
        if isinstance(claim, dict) and str(claim.get("claim_id", "")).startswith("experiment."):
            if claim.get("reproduction_status") == "passed":
                fail("Phase 34 must not pass experiment.* claims")


def validate_phase35_record() -> None:
    record_path = ROOT / "docs/records/2026-05-17-phase35-physical-pendulum-rbd-baseline.md"
    text = record_path.read_text(encoding="utf-8")
    required_snippets = (
        "## Status\n\npassed",
        "## Config Path",
        "configs/experiments/single_body_physical_pendulum.yaml",
        "configs/experiments/paper_experiment_matrix.yaml",
        "## Repository",
        "base commit: `7778469`",
        "phase35-physical-pendulum-rbd-baseline",
        "2026-05-17-mabd-phase35-physical-pendulum-rbd-baseline.md",
        "2026-05-17-phase35-physical-pendulum-rbd-baseline-design.md",
        "## Vendored Newton",
        "96713fa965463b69c229a4d30582c733ff3526bb",
        "local patch status: Phase 35 does not modify vendored Newton",
        "## Paper Source",
        "arXiv ID: `2603.08079`",
        "arXiv version: `v2`",
        "/tmp/mabd-paper/source/sections/experiment.tex:77-91",
        "implicit RBD baseline against the analytic solution",
        "## Environment",
        "mabd-newton-py310",
        "physics-primitive-newton-py310",
        "smoke_passed",
        "mutates_reference_environment=false",
        "uses_reference_python=false",
        "uses_ambient_python=false",
        "## Physical Pendulum RBD Evidence",
        "src/mabd_reproduction/physical_pendulum_rbd.py",
        "run_physical_pendulum_rbd_baseline",
        "--lane rbd_implicit_baseline",
        "physical_pendulum_scalar_implicit_rbd_development",
        "cpu_numpy_newton_only",
        "baseline lane: `rbd_implicit_baseline`",
        "lane_status = development_diagnostic_generated",
        "top-level report status: `incomplete`",
        "required_missing_lanes = [`mabd_newton`]",
        "reports/experiment_matrix/single_body_physical_pendulum_rbd_baseline.json",
        "joint-force magnitude is diagnostic only",
        "## Metrics And Thresholds",
        "random seed: not applicable deterministic scalar implicit RBD rollout",
        "time_step_s: `0.01`",
        "step_count: `16`",
        "compact sample count: `5`",
        "max_abs_angle_error_rad <= 2.0",
        "max_abs_angle_error_rad = 0.0078024877841559315",
        "max_phase_drift_rad <= 2.0",
        "max_phase_drift_rad = 0.0078024877841559315",
        "max_implicit_residual <= 1.0e-12",
        "max_implicit_residual = 6.245004513516506e-16",
        "max_length_constraint_error_m <= 1.0e-12",
        "max_length_constraint_error_m = 1.1102230246251565e-16",
        "max_joint_force_magnitude_n = 3.7570647135963737",
        "threshold status: `passed`",
        "sample steps: `[0, 4, 8, 12, 16]`",
        "## TDD Evidence",
        "tests.test_physical_pendulum_rbd",
        "run_physical_pendulum_rbd_baseline",
        "--lane rbd_implicit_baseline",
        "Ran 3 tests",
        "Ran 16 tests",
        "Ran 25 tests",
        "## Claim Impact",
        "No `experiment.*` claim is passed.",
        "`experiment.single_body.physical_pendulum` remains not passed.",
        "required physical-pendulum `mabd_newton` experiment lane remains missing",
        "RBD implicit baseline diagnostic is now present",
        "Joint-force waveform agreement remains missing",
        "Paper-faithful pendulum geometry remains missing",
        "`pendulum_geometry_unknown` remains a blocker",
        "paper timing remains missing",
        "## Verification Commands",
        "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_physical_pendulum_rbd tests.test_experiment_run_configs tests.test_experiment_runner",
        "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_phase0_bootstrap",
        "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py",
        "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .",
        "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests",
        "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/env/readiness_check.py",
        'PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"',
        "git diff --check",
    )
    for snippet in required_snippets:
        if snippet not in text:
            fail(f"Phase 35 record missing required evidence field: {snippet}")
    for placeholder in ("TO_BE_BACKFILLED_PHASE35", "pending branch-local"):
        if placeholder in text:
            fail("Phase 35 record contains stale placeholder")

    lower_text = text.lower()
    for snippet in (
        "passed physical-pendulum experiment",
        "physical-pendulum experiment passed",
        "physical pendulum experiment passed",
        "full reproduction complete",
        "paper timing verified",
        "paper timing result",
        "joint-force agreement passed",
        "joint-force agreement result",
        "m-abd dynamics result",
        "m-abd physical-pendulum dynamics passed",
        "paper-faithful pendulum geometry passed",
        "paper-faithful pendulum geometry result",
    ):
        if snippet in lower_text:
            fail(f"Phase 35 record overclaims unsupported evidence: {snippet}")

    try:
        config = load_physical_pendulum_config(
            ROOT / "configs/experiments/single_body_physical_pendulum.yaml"
        )
        matrix = load_experiment_matrix(ROOT / "configs/experiments/paper_experiment_matrix.yaml")
        validate_physical_pendulum_config_against_matrix(config, matrix)
    except (ExperimentRunConfigError, ExperimentMatrixError) as exc:
        fail(f"Phase 35 physical-pendulum config validation failed: {exc}")
    lane = config.rbd_baseline
    if config.baseline_lane != "analytic_reference":
        fail("Phase 35 config must keep analytic_reference as the config baseline lane")
    if config.report_status.value != "incomplete":
        fail("Phase 35 physical-pendulum report status must remain incomplete")
    if config.required_missing_lanes != ("mabd_newton",):
        fail("Phase 35 config required missing lanes changed")
    if lane.output_report != "reports/experiment_matrix/single_body_physical_pendulum_rbd_baseline.json":
        fail("Phase 35 RBD diagnostic output report changed")
    if lane.step_count != 16 or lane.sample_count != 5:
        fail("Phase 35 RBD diagnostic rollout size changed")
    if not np.isclose(lane.time_step_s, 0.01, rtol=0.0, atol=1.0e-15):
        fail("Phase 35 RBD diagnostic timestep changed")
    if not np.isclose(lane.length_m, 1.0, rtol=0.0, atol=1.0e-15):
        fail("Phase 35 RBD diagnostic length changed")
    if not np.isclose(lane.mass_kg, 1.0, rtol=0.0, atol=1.0e-15):
        fail("Phase 35 RBD diagnostic mass changed")
    if not np.allclose(lane.gravity_m_s2, [0.0, -9.81, 0.0], rtol=0.0, atol=1.0e-15):
        fail("Phase 35 RBD diagnostic gravity changed")
    for key in (
        "max_abs_angle_error_rad",
        "max_phase_drift_rad",
        "max_implicit_residual",
        "max_length_constraint_error_m",
        "max_abs_joint_force_error_n",
    ):
        if key not in lane.thresholds:
            fail(f"Phase 35 RBD diagnostic threshold missing: {key}")

    report = load_claim_report(ROOT / lane.output_report)
    if report.claim_id != config.claim_id:
        fail("Phase 35 report claim_id does not match config")
    if report.scene_id != config.scene_id:
        fail("Phase 35 report scene_id does not match config")
    if report.status.value != "incomplete":
        fail("Phase 35 report must remain incomplete")
    if report.baseline_lane != "rbd_implicit_baseline":
        fail("Phase 35 report must use rbd_implicit_baseline")
    if report.solver_mode != "physical_pendulum_scalar_implicit_rbd_development":
        fail("Phase 35 report solver mode changed")
    if report.backend != "cpu_numpy_newton_only":
        fail("Phase 35 report backend changed")
    if report.source_commit in {"phase35-working-tree", "pending branch-local"}:
        fail("Phase 35 report source_commit must name the implementation commit")
    expected = report.expected
    if expected.get("full_experiment_claim_passed") is not False:
        fail("Phase 35 report expected.full_experiment_claim_passed must be false")
    paper_claim_status = str(expected.get("paper_claim_status", "")).lower()
    if "diagnostic only" not in paper_claim_status or "incomplete" not in paper_claim_status:
        fail("Phase 35 report expected.paper_claim_status must stay diagnostic-only")
    nonclaim_limitations = expected.get("nonclaim_limitations")
    if not isinstance(nonclaim_limitations, list):
        fail("Phase 35 report expected.nonclaim_limitations must be a list")
    for limitation in (
        "procedural scalar pendulum is not the paper's undisclosed rigid geometry",
        "scalar joint-force reference is diagnostic and not paper geometry",
        "no M-ABD comparison pass is generated",
        "no rendered figure or timing distribution is generated",
    ):
        if limitation not in nonclaim_limitations:
            fail(f"Phase 35 report expected.nonclaim_limitations missing: {limitation}")
    observed = report.observed
    if observed.get("lane_status") != "development_diagnostic_generated":
        fail("Phase 35 report lane_status changed")
    if observed.get("full_experiment_claim_passed") is not False:
        fail("Phase 35 report must not pass the full experiment claim")
    if observed.get("required_missing_lanes") != ["mabd_newton"]:
        fail("Phase 35 report required missing lanes changed")
    if observed.get("threshold_violations") != []:
        fail("Phase 35 report threshold violations must remain empty")
    if observed.get("sample_count") != 5:
        fail("Phase 35 report must contain five compact samples")
    for observed_key, threshold_key in (
        ("max_abs_angle_error_rad", "max_abs_angle_error_rad"),
        ("max_phase_drift_rad", "max_phase_drift_rad"),
        ("max_implicit_residual", "max_implicit_residual"),
        ("max_length_constraint_error_m", "max_length_constraint_error_m"),
        ("max_abs_joint_force_error_n", "max_abs_joint_force_error_n"),
    ):
        if float(observed.get(observed_key)) > float(report.threshold[threshold_key]):
            fail(f"Phase 35 report threshold exceeded: {observed_key}")
    blockers = observed.get("blocking_reasons", [])
    if "pendulum_geometry_unknown" not in blockers:
        fail("Phase 35 report must retain pendulum_geometry_unknown blocker")
    if "joint_force_waveform_agreement_missing" in blockers:
        fail("Phase 35 report must not retain obsolete joint-force waveform blocker")
    samples = observed.get("angle_samples_rad")
    if not isinstance(samples, list) or len(samples) != 5:
        fail("Phase 35 report must contain five compact angle samples")
    if [sample.get("step") for sample in samples] != [0, 4, 8, 12, 16]:
        fail("Phase 35 report sample steps changed")

    claims = read_yaml(ROOT / "docs/reference/paper-claims.yaml").get("claims")
    if not isinstance(claims, list):
        fail("paper-claims.yaml missing claims list")
    for claim in claims:
        if isinstance(claim, dict) and str(claim.get("claim_id", "")).startswith("experiment."):
            if claim.get("reproduction_status") == "passed":
                fail("Phase 35 must not pass experiment.* claims")


def validate_phase36_record() -> None:
    record_path = ROOT / "docs/records/2026-05-17-phase36-physical-pendulum-comparison-protocol.md"
    text = record_path.read_text(encoding="utf-8")
    required_snippets = (
        "## Status\n\npassed",
        "## Config Path",
        "configs/experiments/single_body_physical_pendulum.yaml",
        "configs/experiments/paper_experiment_matrix.yaml",
        "## Repository",
        "implementation commit: `a2a9374`",
        "phase36-physical-pendulum-comparison-protocol",
        "2026-05-17-mabd-phase36-physical-pendulum-comparison-protocol.md",
        "2026-05-17-phase36-physical-pendulum-comparison-protocol-design.md",
        "## Vendored Newton",
        VENDORED_NEWTON_COMMIT,
        "local patch status: Phase 36 does not modify vendored Newton",
        "## Paper Source",
        "arXiv ID: `2603.08079`",
        "arXiv version: `v2`",
        "/tmp/mabd-paper/source/sections/experiment.tex:77-91",
        "## Environment",
        "mabd-newton-py310",
        "physics-primitive-newton-py310",
        "smoke_passed",
        "mutates_reference_environment=false",
        "uses_reference_python=false",
        "uses_ambient_python=false",
        "## Physical Pendulum Comparison Evidence",
        "write_physical_pendulum_comparison_report",
        "run_physical_pendulum_comparison",
        "--lane physical_pendulum_comparison",
        "physical_pendulum_multilane_comparison_development",
        "report_protocol",
        "baseline lane: `physical_pendulum_comparison_protocol`",
        "top-level report status: `incomplete`",
        "input_report_provenance",
        "paper_metric_statuses",
        "reports/experiment_matrix/single_body_physical_pendulum_analytic_reference.json",
        "reports/experiment_matrix/single_body_physical_pendulum_comparison.json",
        "analytic report source_commit:",
        "comparison report source_commit:",
        "## Metrics And Thresholds",
        "required_missing_lanes = [`mabd_newton`]",
        "matched_sample_count = `5`",
        "max_mabd_rbd_abs_angle_delta_rad = 0.0006717899335180466",
        "joint_force_error status = `missing_waveform_not_max_magnitude`",
        "## TDD Evidence",
        "tests.test_physical_pendulum_comparison_reports",
        "run_physical_pendulum_comparison",
        "--analytic-report",
        "Ran 22 tests",
        "Ran 5 tests",
        "Ran 33 tests",
        "## Claim Impact",
        "No `experiment.*` claim is passed.",
        "`experiment.single_body.physical_pendulum` remains intended.",
        "required physical-pendulum `mabd_newton` experiment lane remains missing",
        "Joint-force waveform agreement remains missing",
        "Paper-faithful pendulum geometry remains missing",
        "paper timing remains missing",
        "## Verification Commands",
        "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_run_configs tests.test_physical_pendulum_comparison_reports tests.test_experiment_runner",
        "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py",
        "git diff --check",
    )
    for snippet in required_snippets:
        if snippet not in text:
            fail(f"Phase 36 record missing required evidence field: {snippet}")
    for placeholder in ("TO_BE_BACKFILLED_PHASE36", "pending branch-local", "<implementation-commit>"):
        if placeholder in text:
            fail("Phase 36 record contains stale placeholder")

    lower_text = text.lower()
    for snippet in (
        "passed physical-pendulum experiment",
        "physical-pendulum experiment passed",
        "m-abd lane pass achieved",
        "joint-force waveform agreement passed",
        "paper geometry result",
        "paper timing result",
        "full reproduction complete",
    ):
        if snippet in lower_text:
            fail(f"Phase 36 record overclaims unsupported evidence: {snippet}")

    try:
        config = load_physical_pendulum_config(
            ROOT / "configs/experiments/single_body_physical_pendulum.yaml"
        )
        matrix = load_experiment_matrix(ROOT / "configs/experiments/paper_experiment_matrix.yaml")
        validate_physical_pendulum_config_against_matrix(config, matrix)
    except (ExperimentRunConfigError, ExperimentMatrixError) as exc:
        fail(f"Phase 36 physical-pendulum config validation failed: {exc}")
    if config.comparison.output_report != (
        "reports/experiment_matrix/single_body_physical_pendulum_comparison.json"
    ):
        fail("Phase 36 comparison output report changed")
    if config.comparison.required_lanes != (
        "mabd_newton",
        "analytic_reference",
        "rbd_implicit_baseline",
    ):
        fail("Phase 36 comparison required lanes changed")
    if config.comparison.required_metrics != (
        "pendulum_angle_error",
        "joint_force_error",
        "phase_drift",
    ):
        fail("Phase 36 comparison required metrics changed")

    claims = read_yaml(ROOT / "docs/reference/paper-claims.yaml").get("claims")
    if not isinstance(claims, list):
        fail("paper-claims.yaml missing claims list")
    found_physical_pendulum = False
    for claim in claims:
        if not isinstance(claim, dict):
            continue
        claim_id = str(claim.get("claim_id", ""))
        if claim_id == "experiment.single_body.physical_pendulum":
            found_physical_pendulum = True
            if claim.get("reproduction_status") != "intended":
                fail("Phase 36 must keep physical-pendulum experiment status intended")
        if claim_id.startswith("experiment.") and claim.get("reproduction_status") == "passed":
            fail("Phase 36 must not pass experiment.* claims")
    if not found_physical_pendulum:
        fail("paper-claims.yaml missing physical-pendulum claim")


def validate_phase37_record() -> None:
    record_path = ROOT / "docs/records/2026-05-17-phase37-physical-pendulum-mabd-newton-lane.md"
    text = record_path.read_text(encoding="utf-8")
    required_snippets = (
        "## Status\n\npassed",
        "## Config Path",
        "configs/experiments/single_body_physical_pendulum.yaml",
        "configs/experiments/paper_experiment_matrix.yaml",
        "## Repository",
        "implementation commit: `cf45239`",
        "phase37-mabd-solver-core",
        "2026-05-17-mabd-phase37-physical-pendulum-mabd-newton-lane.md",
        "2026-05-17-phase37-physical-pendulum-mabd-newton-lane-design.md",
        "## Vendored Newton",
        VENDORED_NEWTON_COMMIT,
        "local patch status: Phase 37 does not modify vendored Newton",
        "## Paper Source",
        "arXiv ID: `2603.08079`",
        "arXiv version: `v2`",
        "/tmp/mabd-paper/source/sections/experiment.tex:77-91",
        "## Environment",
        "mabd-newton-py310",
        "physics-primitive-newton-py310",
        "smoke_passed",
        "mutates_reference_environment=false",
        "uses_reference_python=false",
        "uses_ambient_python=false",
        "## Physical Pendulum MABD Newton Evidence",
        "write_physical_pendulum_mabd_newton_report",
        "run_physical_pendulum_mabd_newton",
        "--lane physical_pendulum_mabd_newton",
        "mabd_cpu_oracle_physical_pendulum_newton_lane",
        "baseline lane: `mabd_newton`",
        "lane_status: `incomplete_diagnostic_generated`",
        "reports/experiment_matrix/single_body_physical_pendulum_mabd_newton.json",
        "report source_commit:",
        "world_anchor_reaction_vector_n",
        "## Regenerated Comparison Evidence",
        "write_physical_pendulum_comparison_report",
        "run_physical_pendulum_comparison",
        "--lane physical_pendulum_comparison",
        "physical_pendulum_multilane_comparison_development",
        "baseline lane: `physical_pendulum_comparison_protocol`",
        "reports/experiment_matrix/single_body_physical_pendulum_comparison.json",
        "comparison report source_commit:",
        "input report provenance lanes: `analytic_reference`, `mabd_newton`,",
        "missing_required_lanes = `[]`",
        "missing_paper_metrics = [`joint_force_error:paper_waveform_agreement`]",
        "paper_metric_statuses.phase_drift.status = `diagnostic_available`",
        "paper_metric_statuses.joint_force_error.status =",
        "`diagnostic_reaction_not_paper_waveform`",
        "## Metrics And Thresholds",
        "max_abs_angle_error_rad = `0.007130697850637885`",
        "max_phase_drift_rad = `0.007130697850637885`",
        "max_world_anchor_reaction_magnitude_n = `0.00981000000001586`",
        "matched_sample_count = `5`",
        "max_mabd_rbd_abs_angle_delta_rad = `0.0006717899335180466`",
        "## TDD Evidence",
        "tests.test_physical_pendulum_mabd",
        "tests.test_physical_pendulum_comparison_reports tests.test_experiment_runner",
        "Ran 36 tests",
        "## Claim Impact",
        "No `experiment.*` claim is passed.",
        "`experiment.single_body.physical_pendulum` remains intended.",
        "formal but incomplete physical-pendulum `mabd_newton` report artifact",
        "Joint-force waveform agreement remains missing",
        "Paper-faithful pendulum geometry remains missing",
        "paper timing remains missing",
        "## Verification Commands",
        "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_physical_pendulum_comparison_reports tests.test_experiment_runner",
        "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py",
        "git diff --check",
    )
    for snippet in required_snippets:
        if snippet not in text:
            fail(f"Phase 37 record missing required evidence field: {snippet}")
    for placeholder in ("TO_BE_BACKFILLED_PHASE37", "phase37-working-tree", "<implementation-commit>"):
        if placeholder in text:
            fail("Phase 37 record contains stale placeholder")

    lower_text = text.lower()
    for snippet in (
        "passed physical-pendulum experiment",
        "physical-pendulum experiment passed",
        "joint-force waveform agreement passed",
        "paper geometry result",
        "paper timing result",
        "full reproduction complete",
    ):
        if snippet in lower_text:
            fail(f"Phase 37 record overclaims unsupported evidence: {snippet}")

    try:
        config = load_physical_pendulum_config(
            ROOT / "configs/experiments/single_body_physical_pendulum.yaml"
        )
        matrix = load_experiment_matrix(ROOT / "configs/experiments/paper_experiment_matrix.yaml")
        validate_physical_pendulum_config_against_matrix(config, matrix)
    except (ExperimentRunConfigError, ExperimentMatrixError) as exc:
        fail(f"Phase 37 physical-pendulum config validation failed: {exc}")
    if config.mabd_newton.output_report != (
        "reports/experiment_matrix/single_body_physical_pendulum_mabd_newton.json"
    ):
        fail("Phase 37 MABD Newton output report changed")

    mabd = load_claim_report(ROOT / config.mabd_newton.output_report)
    comparison = load_claim_report(ROOT / config.comparison.output_report)
    for report_name, report in (("MABD Newton", mabd), ("comparison", comparison)):
        if report.source_commit in PLACEHOLDER_SOURCE_COMMITS:
            fail(f"Phase 37 {report_name} report source_commit must name the implementation commit")
        if report.vendored_newton_commit != VENDORED_NEWTON_COMMIT:
            fail(f"Phase 37 {report_name} report vendored Newton commit changed")
        if report.claim_id != config.claim_id:
            fail(f"Phase 37 {report_name} report claim_id does not match config")
        if report.scene_id != config.scene_id:
            fail(f"Phase 37 {report_name} report scene_id does not match config")
        if report.status.value != "incomplete":
            fail(f"Phase 37 {report_name} report must remain incomplete")

    if mabd.baseline_lane != "mabd_newton":
        fail("Phase 37 MABD Newton report lane changed")
    if mabd.solver_mode != "mabd_cpu_oracle_physical_pendulum_newton_lane":
        fail("Phase 37 MABD Newton report solver mode changed")
    if mabd.backend != "cpu_numpy_newton_only":
        fail("Phase 37 MABD Newton report backend changed")
    mabd_observed = mabd.observed
    if mabd_observed.get("lane_status") != "incomplete_diagnostic_generated":
        fail("Phase 37 MABD Newton lane_status changed")
    if mabd_observed.get("full_experiment_claim_passed") is not False:
        fail("Phase 37 MABD Newton report must not pass full experiment claim")
    if mabd_observed.get("threshold_violations") != []:
        fail("Phase 37 MABD Newton report threshold violations changed")
    for metric in (
        "max_abs_angle_error_rad",
        "max_phase_drift_rad",
        "max_pivot_residual_m",
        "max_constraint_residual_norm",
        "max_world_anchor_reaction_magnitude_n",
    ):
        if metric not in mabd_observed:
            fail(f"Phase 37 MABD Newton metric missing: {metric}")
        if float(mabd_observed[metric]) > float(mabd.threshold[metric]):
            fail(f"Phase 37 MABD Newton metric exceeds threshold: {metric}")
    samples = mabd_observed.get("angle_samples_rad")
    if not isinstance(samples, list) or not samples:
        fail("Phase 37 MABD Newton samples missing")
    if "world_anchor_reaction_vector_n" not in samples[-1]:
        fail("Phase 37 MABD Newton samples missing reaction vector")

    if comparison.baseline_lane != "physical_pendulum_comparison_protocol":
        fail("Phase 37 comparison report lane changed")
    if comparison.solver_mode != "physical_pendulum_multilane_comparison_development":
        fail("Phase 37 comparison report solver mode changed")
    if comparison.backend != "report_protocol":
        fail("Phase 37 comparison report backend changed")
    observed = comparison.observed
    if observed.get("full_experiment_claim_passed") is not False:
        fail("Phase 37 comparison report must not pass full experiment claim")
    if observed.get("missing_required_lanes") != []:
        fail("Phase 37 comparison missing_required_lanes changed")
    if observed.get("missing_paper_metrics") != ["joint_force_error:paper_geometry_unknown"]:
        fail("Phase 37 comparison missing_paper_metrics changed")
    blockers = observed.get("blocking_reasons")
    if not isinstance(blockers, list):
        fail("Phase 37 comparison blockers must be a list")
    for blocker in (
        "pendulum_geometry_unknown",
        "physical_pendulum_comparison_pass_gate_not_enabled",
    ):
        if blocker not in blockers:
            fail(f"Phase 37 comparison blocker missing: {blocker}")
    if "joint_force_waveform_agreement_missing" in blockers:
        fail("Phase 37 comparison must not retain obsolete joint-force blocker")
    if "mabd_newton_missing" in blockers:
        fail("Phase 37 comparison must not retain mabd_newton_missing blocker")
    metric_statuses = observed.get("paper_metric_statuses")
    if not isinstance(metric_statuses, dict):
        fail("Phase 37 comparison paper_metric_statuses must be a mapping")
    if metric_statuses.get("phase_drift", {}).get("status") != "diagnostic_available":
        fail("Phase 37 phase_drift metric status changed")
    if metric_statuses.get("joint_force_error", {}).get("status") != (
        "diagnostic_scalar_reference_not_paper_geometry"
    ):
        fail("Phase 37 joint_force_error metric status changed")
    if int(observed.get("matched_sample_count", 0)) <= 0:
        fail("Phase 37 comparison must retain matched sample coverage")
    if observed.get("unmatched_mabd_samples") != [] or observed.get("unmatched_rbd_samples") != []:
        fail("Phase 37 comparison sample alignment changed")
    if float(observed.get("max_mabd_rbd_abs_angle_delta_rad", 999.0)) > float(
        comparison.threshold["max_mabd_rbd_abs_angle_delta_rad"]
    ):
        fail("Phase 37 comparison angle delta exceeds threshold")
    provenance = observed.get("input_report_provenance")
    if not isinstance(provenance, dict):
        fail("Phase 37 comparison input_report_provenance must be a mapping")
    expected_lanes = {
        "analytic_reference": "reports/experiment_matrix/single_body_physical_pendulum_analytic_reference.json",
        "mabd_newton": "reports/experiment_matrix/single_body_physical_pendulum_mabd_newton.json",
        "rbd_implicit_baseline": "reports/experiment_matrix/single_body_physical_pendulum_rbd_baseline.json",
    }
    for lane, expected_path in expected_lanes.items():
        lane_provenance = provenance.get(lane)
        if not isinstance(lane_provenance, dict):
            fail(f"Phase 37 input report provenance missing lane: {lane}")
        if lane_provenance.get("path") != expected_path:
            fail(f"Phase 37 input report path changed: {lane}")
        if lane_provenance.get("vendored_newton_commit") != VENDORED_NEWTON_COMMIT:
            fail(f"Phase 37 input report vendored Newton commit changed: {lane}")
        actual_sha256 = sha256_file(ROOT / expected_path)
        if lane_provenance.get("sha256") != actual_sha256:
            fail(f"Phase 37 input report sha256 mismatch: {lane}")
        if lane_provenance.get("source_commit") in PLACEHOLDER_SOURCE_COMMITS:
            fail(f"Phase 37 input report source_commit placeholder: {lane}")

    claims = read_yaml(ROOT / "docs/reference/paper-claims.yaml").get("claims")
    if not isinstance(claims, list):
        fail("paper-claims.yaml missing claims list")
    found_physical_pendulum = False
    for claim in claims:
        if not isinstance(claim, dict):
            continue
        claim_id = str(claim.get("claim_id", ""))
        if claim_id == "experiment.single_body.physical_pendulum":
            found_physical_pendulum = True
            if claim.get("reproduction_status") != "intended":
                fail("Phase 37 must keep physical-pendulum experiment status intended")
        if claim_id.startswith("experiment.") and claim.get("reproduction_status") == "passed":
            fail("Phase 37 must not pass experiment.* claims")
    if not found_physical_pendulum:
        fail("paper-claims.yaml missing physical-pendulum claim")


def validate_phase38_record() -> None:
    text = (ROOT / "docs/records/2026-05-17-phase38-constrained-rotated-kkt.md").read_text(
        encoding="utf-8"
    )
    required_snippets = (
        "## Status\n\npassed",
        "## Config Path",
        "configs/experiments/single_body_physical_pendulum.yaml",
        "## Repository",
        "implementation commit: `0b93ee1`",
        "phase38-constrained-rotated-kkt",
        "2026-05-17-mabd-phase38-constrained-rotated-kkt.md",
        "2026-05-17-phase38-constrained-rotated-kkt-design.md",
        "## Vendored Newton",
        VENDORED_NEWTON_COMMIT,
        "dense constrained polar CPU KKT support",
        "## Environment",
        "mabd-newton-py310",
        "physics-primitive-newton-py310",
        "mutates_reference_environment=false",
        "uses_reference_python=false",
        "uses_ambient_python=false",
        "## Solver Evidence",
        "np.kron(np.eye(4), polar_rotation(A))",
        "J_world @ increment_map",
        "constrained `no_polar` remains unsupported",
        "rotated non-dense topology paths require `topology='dense'`",
        "test_constrained_cpu_step_supports_polar_world_anchor",
        "test_constrained_cpu_step_rejects_no_polar_because_map_is_nonlinear",
        "test_constrained_cpu_step_rejects_polar_non_dense_topology_until_tested",
        "newton.tests.test_mabd_phase4_solver_step",
        "## Physical Pendulum Evidence",
        "mabd_newton.rotation_mode = polar",
        "mabd_rotation_mode = `polar`",
        "reports/experiment_matrix/single_body_physical_pendulum_mabd_newton.json",
        "report source_commit: `0b93ee1`",
        "## Regenerated Comparison Evidence",
        "reports/experiment_matrix/single_body_physical_pendulum_comparison.json",
        "comparison report source_commit: `0b93ee1`",
        "missing_required_lanes = `[]`",
        "missing_paper_metrics = [`joint_force_error:paper_waveform_agreement`]",
        "`diagnostic_reaction_not_paper_waveform`",
        "physical_pendulum_comparison_pass_gate_not_enabled",
        "## Claim Impact",
        "No `experiment.*` claim is passed.",
        "`experiment.single_body.physical_pendulum` remains intended.",
        "Constrained `no_polar` KKT remains explicitly unsupported.",
        "Rotated non-dense topology KKT remains explicitly unsupported.",
        "Joint-force waveform agreement remains missing",
        "paper timing remains missing",
        "## Verification Commands",
        "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py",
        "git diff --check",
    )
    for snippet in required_snippets:
        if snippet not in text:
            fail(f"Phase 38 record missing required evidence field: {snippet}")
    for placeholder in ("TO_BE_BACKFILLED_PHASE38", "phase38-working-tree", "<implementation-commit>"):
        if placeholder in text:
            fail("Phase 38 record contains stale placeholder")

    lower_text = text.lower()
    for snippet in (
        "passed physical-pendulum experiment",
        "physical-pendulum experiment passed",
        "constrained `no_polar` kkt support exists",
        "joint-force waveform agreement passed",
        "paper geometry result",
        "paper timing result",
        "full reproduction complete",
    ):
        if snippet in lower_text:
            fail(f"Phase 38 record overclaims unsupported evidence: {snippet}")

    boundary_text = (ROOT / "docs/reference/claim-boundaries.md").read_text(encoding="utf-8")
    for snippet in (
        "This repository contains Phase 38 dense constrained polar CPU KKT evidence",
        "Phase 38 verifies dense constrained `rotation_mode = polar`",
        "explicit constrained `no_polar`",
        "mabd_rotation_mode = polar",
        "Phase 38 does not verify constrained `no_polar` KKT",
        "rotated chain/tree/loop",
        "Phase 38 constrained polar CPU KKT support",
    ):
        if snippet not in boundary_text:
            fail(f"Phase 38 claim boundary missing: {snippet}")

    try:
        config = load_physical_pendulum_config(
            ROOT / "configs/experiments/single_body_physical_pendulum.yaml"
        )
        matrix = load_experiment_matrix(ROOT / "configs/experiments/paper_experiment_matrix.yaml")
        validate_physical_pendulum_config_against_matrix(config, matrix)
    except (ExperimentRunConfigError, ExperimentMatrixError) as exc:
        fail(f"Phase 38 physical-pendulum config validation failed: {exc}")
    if config.mabd_newton.rotation_mode != "polar":
        fail("Phase 38 physical-pendulum mabd_newton.rotation_mode must be polar")

    mabd = load_claim_report(ROOT / config.mabd_newton.output_report)
    comparison = load_claim_report(ROOT / config.comparison.output_report)
    for report_name, report in (("MABD Newton", mabd), ("comparison", comparison)):
        if report.source_commit in PLACEHOLDER_SOURCE_COMMITS:
            fail(f"Phase 38 {report_name} report source_commit must name the implementation commit")
        if report.vendored_newton_commit != VENDORED_NEWTON_COMMIT:
            fail(f"Phase 38 {report_name} report vendored Newton commit changed")
        if report.claim_id != config.claim_id:
            fail(f"Phase 38 {report_name} report claim_id does not match config")
        if report.scene_id != config.scene_id:
            fail(f"Phase 38 {report_name} report scene_id does not match config")
        if report.status.value != "incomplete":
            fail(f"Phase 38 {report_name} report must remain incomplete")

    if mabd.baseline_lane != "mabd_newton":
        fail("Phase 38 MABD Newton report lane changed")
    if mabd.solver_mode != "mabd_cpu_oracle_physical_pendulum_newton_lane":
        fail("Phase 38 MABD Newton report solver mode changed")
    if mabd.backend != "cpu_numpy_newton_only":
        fail("Phase 38 MABD Newton report backend changed")
    mabd_observed = mabd.observed
    if mabd_observed.get("lane_status") != "incomplete_diagnostic_generated":
        fail("Phase 38 MABD Newton lane_status changed")
    if mabd_observed.get("mabd_rotation_mode") != "polar":
        fail("Phase 38 MABD Newton report must record mabd_rotation_mode=polar")
    if mabd.expected.get("mabd_rotation_mode") != "polar":
        fail("Phase 38 MABD Newton expected record must keep mabd_rotation_mode=polar")
    if mabd_observed.get("full_experiment_claim_passed") is not False:
        fail("Phase 38 MABD Newton report must not pass full experiment claim")
    if mabd_observed.get("threshold_violations") != []:
        fail("Phase 38 MABD Newton report threshold violations changed")
    mabd_blockers = mabd_observed.get("blocking_reasons", [])
    if "pendulum_geometry_unknown" not in mabd_blockers:
        fail("Phase 38 MABD Newton blocker missing: pendulum_geometry_unknown")
    if "joint_force_waveform_agreement_missing" in mabd_blockers:
        fail("Phase 38 MABD Newton must not retain obsolete joint-force blocker")

    if comparison.baseline_lane != "physical_pendulum_comparison_protocol":
        fail("Phase 38 comparison report lane changed")
    if comparison.solver_mode != "physical_pendulum_multilane_comparison_development":
        fail("Phase 38 comparison report solver mode changed")
    if comparison.backend != "report_protocol":
        fail("Phase 38 comparison report backend changed")
    observed = comparison.observed
    if observed.get("full_experiment_claim_passed") is not False:
        fail("Phase 38 comparison report must not pass full experiment claim")
    if observed.get("missing_required_lanes") != []:
        fail("Phase 38 comparison missing_required_lanes changed")
    if observed.get("missing_paper_metrics") != ["joint_force_error:paper_geometry_unknown"]:
        fail("Phase 38 comparison missing_paper_metrics changed")
    blockers = observed.get("blocking_reasons")
    if not isinstance(blockers, list):
        fail("Phase 38 comparison blockers must be a list")
    for blocker in (
        "pendulum_geometry_unknown",
        "physical_pendulum_comparison_pass_gate_not_enabled",
    ):
        if blocker not in blockers:
            fail(f"Phase 38 comparison blocker missing: {blocker}")
    if "joint_force_waveform_agreement_missing" in blockers:
        fail("Phase 38 comparison must not retain obsolete joint-force blocker")
    if "mabd_newton_missing" in blockers:
        fail("Phase 38 comparison must not retain mabd_newton_missing blocker")
    metric_statuses = observed.get("paper_metric_statuses")
    if not isinstance(metric_statuses, dict):
        fail("Phase 38 comparison paper_metric_statuses must be a mapping")
    if metric_statuses.get("phase_drift", {}).get("status") != "diagnostic_available":
        fail("Phase 38 phase_drift metric status changed")
    if metric_statuses.get("joint_force_error", {}).get("status") != (
        "diagnostic_scalar_reference_not_paper_geometry"
    ):
        fail("Phase 38 joint_force_error metric status changed")
    if int(observed.get("matched_sample_count", 0)) <= 0:
        fail("Phase 38 comparison must retain matched sample coverage")

    provenance = observed.get("input_report_provenance")
    if not isinstance(provenance, dict):
        fail("Phase 38 comparison input_report_provenance must be a mapping")
    expected_lanes = {
        "analytic_reference": "reports/experiment_matrix/single_body_physical_pendulum_analytic_reference.json",
        "mabd_newton": "reports/experiment_matrix/single_body_physical_pendulum_mabd_newton.json",
        "rbd_implicit_baseline": "reports/experiment_matrix/single_body_physical_pendulum_rbd_baseline.json",
    }
    for lane, expected_path in expected_lanes.items():
        lane_provenance = provenance.get(lane)
        if not isinstance(lane_provenance, dict):
            fail(f"Phase 38 input report provenance missing lane: {lane}")
        if lane_provenance.get("path") != expected_path:
            fail(f"Phase 38 input report path changed: {lane}")
        if lane_provenance.get("vendored_newton_commit") != VENDORED_NEWTON_COMMIT:
            fail(f"Phase 38 input report vendored Newton commit changed: {lane}")
        actual_sha256 = sha256_file(ROOT / expected_path)
        if lane_provenance.get("sha256") != actual_sha256:
            fail(f"Phase 38 input report sha256 mismatch: {lane}")
        if lane_provenance.get("source_commit") in PLACEHOLDER_SOURCE_COMMITS:
            fail(f"Phase 38 input report source_commit placeholder: {lane}")
    if provenance["mabd_newton"].get("source_commit") != mabd.source_commit:
        fail("Phase 38 comparison must consume the regenerated MABD Newton report")

    claims = read_yaml(ROOT / "docs/reference/paper-claims.yaml").get("claims")
    if not isinstance(claims, list):
        fail("paper-claims.yaml missing claims list")
    found_physical_pendulum = False
    for claim in claims:
        if not isinstance(claim, dict):
            continue
        claim_id = str(claim.get("claim_id", ""))
        if claim_id == "experiment.single_body.physical_pendulum":
            found_physical_pendulum = True
            if claim.get("reproduction_status") != "intended":
                fail("Phase 38 must keep physical-pendulum experiment status intended")
        if claim_id.startswith("experiment.") and claim.get("reproduction_status") == "passed":
            fail("Phase 38 must not pass experiment.* claims")
    if not found_physical_pendulum:
        fail("paper-claims.yaml missing physical-pendulum claim")


def validate_phase39_record() -> None:
    text = (
        ROOT / "docs/records/2026-05-17-phase39-physical-pendulum-timing-source-audit.md"
    ).read_text(encoding="utf-8")
    required_snippets = (
        "## Status\n\npassed",
        "## Config Path",
        "configs/experiments/single_body_physical_pendulum.yaml",
        "## Repository",
        "phase39-physical-pendulum-timing",
        "## Paper Source Audit",
        "/tmp/mabd-paper/source/sections/experiment.tex:77-91",
        "runtime_timing_claim_present = `false`",
        "required_metric = `false`",
        PHYSICAL_PENDULUM_TIMING_AUDIT_STATUS,
        "## Report Evidence",
        "paper_timing_source_audit",
        "removed blocker: `paper_timing_missing`",
        "retained blocker: `joint_force_waveform_agreement_missing`",
        "retained blocker: `pendulum_geometry_unknown`",
        "retained blocker: `physical_pendulum_comparison_pass_gate_not_enabled`",
        "reports/experiment_matrix/single_body_physical_pendulum_mabd_newton.json",
        "reports/experiment_matrix/single_body_physical_pendulum_rbd_baseline.json",
        "reports/experiment_matrix/single_body_physical_pendulum_comparison.json",
        "## Claim Impact",
        "No `experiment.*` claim is passed.",
        "`experiment.single_body.physical_pendulum` remains intended.",
        "## Verification Commands",
        "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py",
        "git diff --check",
    )
    for snippet in required_snippets:
        if snippet not in text:
            fail(f"Phase 39 record missing required evidence field: {snippet}")
    for placeholder in ("TO_BE_BACKFILLED_PHASE39", "phase39-working-tree", "<implementation-commit>"):
        if placeholder in text:
            fail("Phase 39 record contains stale placeholder")

    lower_text = text.lower()
    for snippet in (
        "physical-pendulum experiment passed",
        "joint-force waveform agreement passed",
        "paper geometry result",
        "paper timing result",
        "runtime timing reproduced",
        "runtime performance reproduced",
        "full reproduction complete",
    ):
        if snippet in lower_text:
            fail(f"Phase 39 record overclaims unsupported evidence: {snippet}")

    boundary_text = (ROOT / "docs/reference/claim-boundaries.md").read_text(encoding="utf-8")
    normalized_boundary_text = " ".join(boundary_text.split())
    for snippet in (
        "This repository contains Phase 39 physical-pendulum timing source-audit evidence",
        "Phase 39 verifies `paper_timing_source_audit`",
        "runtime_timing_claim_present = false",
        "required_metric = false",
        "removal of `paper_timing_missing`",
        "Phase 39 does not verify runtime performance",
        "Phase 39 physical-pendulum timing source audit",
    ):
        if snippet not in normalized_boundary_text:
            fail(f"Phase 39 claim boundary missing: {snippet}")

    try:
        config = load_physical_pendulum_config(
            ROOT / "configs/experiments/single_body_physical_pendulum.yaml"
        )
        matrix = load_experiment_matrix(ROOT / "configs/experiments/paper_experiment_matrix.yaml")
        validate_physical_pendulum_config_against_matrix(config, matrix)
    except (ExperimentRunConfigError, ExperimentMatrixError) as exc:
        fail(f"Phase 39 physical-pendulum config validation failed: {exc}")

    report_paths = {
        "analytic_reference": "reports/experiment_matrix/single_body_physical_pendulum_analytic_reference.json",
        "mabd_development": config.mabd_development.output_report,
        "mabd_newton": config.mabd_newton.output_report,
        "rbd_implicit_baseline": config.rbd_baseline.output_report,
        "comparison": config.comparison.output_report,
    }
    reports = {
        name: load_claim_report(ROOT / path)
        for name, path in report_paths.items()
    }
    for name, report in reports.items():
        if report.source_commit in PLACEHOLDER_SOURCE_COMMITS:
            fail(f"Phase 39 {name} report source_commit must name the implementation commit")
        if report.vendored_newton_commit != VENDORED_NEWTON_COMMIT:
            fail(f"Phase 39 {name} report vendored Newton commit changed")
        if report.claim_id != config.claim_id:
            fail(f"Phase 39 {name} report claim_id does not match config")
        if report.scene_id != config.scene_id:
            fail(f"Phase 39 {name} report scene_id does not match config")
        if report.status.value != "incomplete":
            fail(f"Phase 39 {name} report must remain incomplete")
        if report.observed.get("full_experiment_claim_passed") is not False:
            fail(f"Phase 39 {name} report must not pass full experiment claim")
        validate_physical_pendulum_timing_source_audit(
            report.observed.get("paper_timing_source_audit"),
            f"Phase 39 {name} observed",
        )
        validate_physical_pendulum_timing_source_audit(
            report.expected.get("paper_timing_source_audit"),
            f"Phase 39 {name} expected",
        )
        if report.timing_distribution.get("scope") != "not_timed":
            fail(f"Phase 39 {name} report must remain not_timed")
        blockers = report.observed.get("blocking_reasons", [])
        if isinstance(blockers, list) and "paper_timing_missing" in blockers:
            fail(f"Phase 39 {name} report must not retain paper_timing_missing blocker")

    mabd_blockers = reports["mabd_newton"].observed.get("blocking_reasons", [])
    if "pendulum_geometry_unknown" not in mabd_blockers:
        fail("Phase 39 MABD Newton blocker missing: pendulum_geometry_unknown")
    if "joint_force_waveform_agreement_missing" in mabd_blockers:
        fail("Phase 39 MABD Newton must not retain obsolete joint-force blocker")

    rbd_blockers = reports["rbd_implicit_baseline"].observed.get("blocking_reasons", [])
    for blocker in (
        "mabd_newton_missing",
        "pendulum_geometry_unknown",
    ):
        if blocker not in rbd_blockers:
            fail(f"Phase 39 RBD baseline blocker missing: {blocker}")
    if "joint_force_waveform_agreement_missing" in rbd_blockers:
        fail("Phase 39 RBD baseline must not retain obsolete joint-force blocker")

    comparison = reports["comparison"]
    if comparison.baseline_lane != "physical_pendulum_comparison_protocol":
        fail("Phase 39 comparison report lane changed")
    if comparison.solver_mode != "physical_pendulum_multilane_comparison_development":
        fail("Phase 39 comparison report solver mode changed")
    observed = comparison.observed
    if observed.get("missing_required_lanes") != []:
        fail("Phase 39 comparison missing_required_lanes changed")
    if observed.get("missing_paper_metrics") != ["joint_force_error:paper_geometry_unknown"]:
        fail("Phase 39 comparison missing_paper_metrics changed")
    blockers = observed.get("blocking_reasons")
    if not isinstance(blockers, list):
        fail("Phase 39 comparison blockers must be a list")
    for blocker in (
        "pendulum_geometry_unknown",
        "physical_pendulum_comparison_pass_gate_not_enabled",
    ):
        if blocker not in blockers:
            fail(f"Phase 39 comparison blocker missing: {blocker}")
    if "joint_force_waveform_agreement_missing" in blockers:
        fail("Phase 39 comparison must not retain obsolete joint-force blocker")
    if "paper_timing_missing" in blockers:
        fail("Phase 39 comparison must not retain paper_timing_missing blocker")

    claims = read_yaml(ROOT / "docs/reference/paper-claims.yaml").get("claims")
    if not isinstance(claims, list):
        fail("paper-claims.yaml missing claims list")
    found_physical_pendulum = False
    for claim in claims:
        if not isinstance(claim, dict):
            continue
        claim_id = str(claim.get("claim_id", ""))
        if claim_id == "experiment.single_body.physical_pendulum":
            found_physical_pendulum = True
            if claim.get("reproduction_status") != "intended":
                fail("Phase 39 must keep physical-pendulum experiment status intended")
        if claim_id.startswith("experiment.") and claim.get("reproduction_status") == "passed":
            fail("Phase 39 must not pass experiment.* claims")
    if not found_physical_pendulum:
        fail("paper-claims.yaml missing physical-pendulum claim")


def validate_phase40_record() -> None:
    text = (
        ROOT / "docs/records/2026-05-17-phase40-physical-pendulum-joint-force-reference.md"
    ).read_text(encoding="utf-8")
    required_snippets = (
        "## Status\n\npassed",
        "## Config Path",
        "configs/experiments/single_body_physical_pendulum.yaml",
        "## Repository",
        "phase40-physical-pendulum-joint-force-reference",
        "## Scalar Joint-Force Reference Evidence",
        "physical_pendulum_angular_velocity_reference",
        "physical_pendulum_joint_force_reference",
        "joint_force_samples_n",
        "scalar_point_pendulum_radial_reaction",
        "## Lane Report Evidence",
        "max_abs_joint_force_error_n",
        "reference_joint_force_magnitude_n",
        "abs_joint_force_error_n",
        "removed blocker: `joint_force_waveform_agreement_missing`",
        "retained blocker: `pendulum_geometry_unknown`",
        "## Comparison Evidence",
        "joint_force_waveform_diagnostics",
        "missing_paper_metrics = [`joint_force_error:paper_geometry_unknown`]",
        "paper_metric_statuses.joint_force_error.status =",
        "`diagnostic_scalar_reference_not_paper_geometry`",
        "matched_sample_count = `5`",
        "## Claim Impact",
        "No `experiment.*` claim is passed.",
        "`experiment.single_body.physical_pendulum` remains intended.",
        "scalar/procedural diagnostic, not paper geometry",
        "## Verification Commands",
        "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py",
        "git diff --check",
    )
    for snippet in required_snippets:
        if snippet not in text:
            fail(f"Phase 40 record missing required evidence field: {snippet}")
    for placeholder in ("TO_BE_BACKFILLED_PHASE40", "phase40-working-tree", "<implementation-commit>"):
        if placeholder in text:
            fail("Phase 40 record contains stale placeholder")

    lower_text = text.lower()
    for snippet in (
        "physical-pendulum experiment passed",
        "paper geometry result",
        "paper joint-force waveform reproduced",
        "runtime performance reproduced",
        "full reproduction complete",
    ):
        if snippet in lower_text:
            fail(f"Phase 40 record overclaims unsupported evidence: {snippet}")

    boundary_text = (ROOT / "docs/reference/claim-boundaries.md").read_text(encoding="utf-8")
    normalized_boundary_text = " ".join(boundary_text.split())
    for snippet in (
        "This repository contains Phase 40 scalar physical-pendulum joint-force reference",
        "Phase 40 verifies `physical_pendulum_angular_velocity_reference`",
        "`physical_pendulum_joint_force_reference`",
        "`max_abs_joint_force_error_n`",
        "`joint_force_waveform_diagnostics`",
        "Phase 40 does not verify the paper's exact physical-pendulum geometry",
        "Phase 40 physical-pendulum scalar joint-force diagnostics",
    ):
        if snippet not in normalized_boundary_text:
            fail(f"Phase 40 claim boundary missing: {snippet}")

    try:
        config = load_physical_pendulum_config(
            ROOT / "configs/experiments/single_body_physical_pendulum.yaml"
        )
        matrix = load_experiment_matrix(ROOT / "configs/experiments/paper_experiment_matrix.yaml")
        validate_physical_pendulum_config_against_matrix(config, matrix)
    except (ExperimentRunConfigError, ExperimentMatrixError) as exc:
        fail(f"Phase 40 physical-pendulum config validation failed: {exc}")

    report_paths = {
        "analytic_reference": config.output_report,
        "mabd_newton": config.mabd_newton.output_report,
        "rbd_implicit_baseline": config.rbd_baseline.output_report,
        "comparison": config.comparison.output_report,
    }
    reports = {
        name: load_claim_report(ROOT / path)
        for name, path in report_paths.items()
    }
    for name, report in reports.items():
        if report.source_commit in PLACEHOLDER_SOURCE_COMMITS:
            fail(f"Phase 40 {name} report source_commit must name the implementation commit")
        if report.vendored_newton_commit != VENDORED_NEWTON_COMMIT:
            fail(f"Phase 40 {name} report vendored Newton commit changed")
        if report.claim_id != config.claim_id:
            fail(f"Phase 40 {name} report claim_id does not match config")
        if report.scene_id != config.scene_id:
            fail(f"Phase 40 {name} report scene_id does not match config")
        if report.status.value != "incomplete":
            fail(f"Phase 40 {name} report must remain incomplete")
        if report.observed.get("full_experiment_claim_passed") is not False:
            fail(f"Phase 40 {name} report must not pass full experiment claim")

    analytic = reports["analytic_reference"]
    if analytic.expected.get("joint_force_reference_model") != (
        "scalar_point_pendulum_radial_reaction"
    ):
        fail("Phase 40 analytic report missing scalar joint-force reference model")
    force_samples = analytic.observed.get("joint_force_samples_n")
    if not isinstance(force_samples, list) or len(force_samples) != config.reference.sample_count:
        fail("Phase 40 analytic report joint_force_samples_n changed")
    if force_samples[0].get("joint_force_magnitude_n") != 0.0:
        fail("Phase 40 analytic report first joint-force sample must be zero")
    if float(analytic.observed.get("max_joint_force_magnitude_n", 0.0)) <= 0.0:
        fail("Phase 40 analytic report max joint-force magnitude must be positive")

    mabd = reports["mabd_newton"]
    rbd = reports["rbd_implicit_baseline"]
    for report_name, report in (("MABD Newton", mabd), ("RBD baseline", rbd)):
        observed = report.observed
        metric = observed.get("max_abs_joint_force_error_n")
        if not isinstance(metric, int | float) or not np.isfinite(float(metric)):
            fail(f"Phase 40 {report_name} missing finite max_abs_joint_force_error_n")
        if float(metric) > float(report.threshold["max_abs_joint_force_error_n"]):
            fail(f"Phase 40 {report_name} joint-force error exceeds threshold")
        blockers = observed.get("blocking_reasons")
        if not isinstance(blockers, list):
            fail(f"Phase 40 {report_name} blockers must be a list")
        if "pendulum_geometry_unknown" not in blockers:
            fail(f"Phase 40 {report_name} must retain pendulum_geometry_unknown")
        if "joint_force_waveform_agreement_missing" in blockers:
            fail(f"Phase 40 {report_name} must not retain obsolete joint-force blocker")
        samples = observed.get("angle_samples_rad")
        if not isinstance(samples, list) or not samples:
            fail(f"Phase 40 {report_name} samples missing")
        last_sample = samples[-1]
        if not isinstance(last_sample, dict):
            fail(f"Phase 40 {report_name} sample rows must be mappings")
        for field in ("reference_joint_force_magnitude_n", "abs_joint_force_error_n"):
            if field not in last_sample:
                fail(f"Phase 40 {report_name} sample missing {field}")

    comparison = reports["comparison"]
    observed = comparison.observed
    if observed.get("missing_paper_metrics") != ["joint_force_error:paper_geometry_unknown"]:
        fail("Phase 40 comparison missing_paper_metrics changed")
    blockers = observed.get("blocking_reasons")
    if not isinstance(blockers, list):
        fail("Phase 40 comparison blockers must be a list")
    for blocker in (
        "pendulum_geometry_unknown",
        "physical_pendulum_comparison_pass_gate_not_enabled",
    ):
        if blocker not in blockers:
            fail(f"Phase 40 comparison blocker missing: {blocker}")
    if "joint_force_waveform_agreement_missing" in blockers:
        fail("Phase 40 comparison must not retain obsolete joint-force blocker")
    metric_statuses = observed.get("paper_metric_statuses")
    if not isinstance(metric_statuses, dict):
        fail("Phase 40 comparison paper_metric_statuses must be a mapping")
    if metric_statuses.get("joint_force_error", {}).get("status") != (
        "diagnostic_scalar_reference_not_paper_geometry"
    ):
        fail("Phase 40 joint_force_error metric status changed")
    diagnostics = observed.get("joint_force_waveform_diagnostics")
    if not isinstance(diagnostics, dict):
        fail("Phase 40 comparison joint_force_waveform_diagnostics missing")
    if diagnostics.get("reference_model") != "scalar_point_pendulum_radial_reaction":
        fail("Phase 40 comparison joint-force reference model changed")
    if diagnostics.get("matched_sample_count") != 5:
        fail("Phase 40 comparison joint-force matched sample count changed")
    rows = diagnostics.get("joint_force_sample_differences_n")
    if not isinstance(rows, list) or len(rows) != 5:
        fail("Phase 40 comparison joint-force sample rows changed")
    for key in ("max_mabd_abs_joint_force_error_n", "max_rbd_abs_joint_force_error_n"):
        value = diagnostics.get(key)
        if not isinstance(value, int | float) or not np.isfinite(float(value)):
            fail(f"Phase 40 comparison diagnostic missing finite {key}")

    claims = read_yaml(ROOT / "docs/reference/paper-claims.yaml").get("claims")
    if not isinstance(claims, list):
        fail("paper-claims.yaml missing claims list")
    found_physical_pendulum = False
    for claim in claims:
        if not isinstance(claim, dict):
            continue
        claim_id = str(claim.get("claim_id", ""))
        if claim_id == "experiment.single_body.physical_pendulum":
            found_physical_pendulum = True
            if claim.get("reproduction_status") != "intended":
                fail("Phase 40 must keep physical-pendulum experiment status intended")
        if claim_id.startswith("experiment.") and claim.get("reproduction_status") == "passed":
            fail("Phase 40 must not pass experiment.* claims")
    if not found_physical_pendulum:
        fail("paper-claims.yaml missing physical-pendulum claim")


def validate_phase41_record() -> None:
    text = (
        ROOT / "docs/records/2026-05-17-phase41-physical-pendulum-geometry-source-audit.md"
    ).read_text(encoding="utf-8")
    required_snippets = (
        "## Status\n\npassed",
        "## Repository",
        "phase41-physical-pendulum-geometry-source-audit",
        "## Paper Source Audit",
        "physical_pendulum_geometry_source_audit",
        "source_assets_found_geometry_parameters_missing",
        "sections/experiment.tex",
        "images/simple_pendulum/simple_pendulum.pdf",
        "4b198ace42ff08d32dc266f1eca710987a2b6335d75878ee01b60498fed945cf",
        "source_tree_path_count",
        "scanned_tex_paths",
        "sections_a/multiabd.tex",
        "absence_findings.physical_pendulum_geometry_parameter_search.status",
        "no_paper_faithful_physical_pendulum_geometry_parameters_found",
        "physical_pendulum_geometry_parameters_missing_from_public_source_assets",
        "raw_physical_pendulum_curve_data_missing_from_public_source_assets",
        "physical_pendulum_private_author_assets_not_audited",
        "retained blocker: `pendulum_geometry_unknown`",
        "missing_paper_metrics = [`joint_force_error:paper_geometry_unknown`]",
        "## Claim Impact",
        "No `experiment.*` claim is passed.",
        "`experiment.single_body.physical_pendulum` remains intended.",
        "does not reconstruct paper-faithful physical-pendulum geometry",
        "## Verification Commands",
        "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_physical_pendulum_source_audit tests.test_phase0_bootstrap",
        "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py",
        "git diff --check",
    )
    for snippet in required_snippets:
        if snippet not in text:
            fail(f"Phase 41 record missing required evidence field: {snippet}")
    for placeholder in ("TO_BE_BACKFILLED_PHASE41", "phase41-working-tree", "<implementation-commit>"):
        if placeholder in text:
            fail("Phase 41 record contains stale placeholder")

    lower_text = text.lower()
    for snippet in (
        "physical-pendulum experiment passed",
        "paper geometry reconstructed",
        "paper-faithful physical-pendulum geometry implemented",
        "joint-force waveform agreement passed",
        "runtime performance reproduced",
        "full reproduction complete",
    ):
        if snippet in lower_text:
            fail(f"Phase 41 record overclaims unsupported evidence: {snippet}")

    boundary_text = (ROOT / "docs/reference/claim-boundaries.md").read_text(encoding="utf-8")
    normalized_boundary_text = " ".join(boundary_text.split())
    for snippet in (
        "This repository contains Phase 41 physical-pendulum geometry source-asset audit",
        "Phase 41 verifies `physical_pendulum_geometry_source_audit`",
        "`source_tree_paths`",
        "`scanned_tex_paths`",
        "`absence_findings`",
        "source_assets_found_geometry_parameters_missing",
        "Phase 41 does not verify private author assets",
        "paper-faithful physical-pendulum geometry",
        "Phase 41 physical-pendulum source-asset audit",
    ):
        if snippet not in normalized_boundary_text:
            fail(f"Phase 41 claim boundary missing: {snippet}")

    audit = physical_pendulum_geometry_source_audit(PAPER_SOURCE_ROOT)
    if audit.status != "source_assets_found_geometry_parameters_missing":
        fail(f"Phase 41 geometry source audit status changed: {audit.status}")
    expected_hashes = {
        "sections/experiment.tex": (
            "c5927183fe4e3f1c1c1617e5b10b7e9006da6a9eac537e891cb1dac03d58dd0f"
        ),
        "images/simple_pendulum/simple_pendulum.pdf": (
            "4b198ace42ff08d32dc266f1eca710987a2b6335d75878ee01b60498fed945cf"
        ),
    }
    for relative_path, expected_hash in expected_hashes.items():
        if audit.file_hashes.get(relative_path) != expected_hash:
            fail(f"Phase 41 source hash changed: {relative_path}")
    if len(audit.source_tree_paths) < 30:
        fail("Phase 41 source-tree inventory is unexpectedly small")
    for relative_path in (
        "sections/experiment.tex",
        "sections_a/multiabd.tex",
        "ref.bib",
        "images/simple_pendulum/simple_pendulum.pdf",
    ):
        if relative_path not in audit.source_tree_paths:
            fail(f"Phase 41 source-tree inventory missing: {relative_path}")
    for relative_path in ("sections/experiment.tex", "sections_a/multiabd.tex"):
        if relative_path not in audit.scanned_tex_paths:
            fail(f"Phase 41 scanned_tex_paths missing: {relative_path}")
    for key in (
        "fixed_pivot",
        "horizontal_release_zero_initial_velocity",
        "elliptic_angle_reference",
        "joint_force_magnitude_plot",
    ):
        finding = audit.positive_findings.get(key)
        if not isinstance(finding, dict) or finding.get("present") is not True:
            fail(f"Phase 41 positive source finding missing: {key}")
        if finding.get("path") != "sections/experiment.tex":
            fail(f"Phase 41 positive source finding path changed: {key}")
        if finding.get("line_start") != 77 or finding.get("line_end") != 91:
            fail(f"Phase 41 positive source finding window changed: {key}")
    figure_paths = audit.figure_pdf.get("embedded_image_paths")
    if not isinstance(figure_paths, list) or not any("pendulum15.png" in path for path in figure_paths):
        fail("Phase 41 figure PDF embedded image paths changed")
    absence = audit.absence_findings.get("physical_pendulum_geometry_parameter_search")
    if not isinstance(absence, dict):
        fail("Phase 41 missing geometry absence finding")
    if absence.get("status") != "no_paper_faithful_physical_pendulum_geometry_parameters_found":
        fail("Phase 41 geometry absence finding status changed")
    if absence.get("usable_parameter_disclosures") != []:
        fail("Phase 41 geometry absence finding found usable parameter disclosures")
    if int(absence.get("searched_source_path_count", 0)) != len(audit.source_tree_paths):
        fail("Phase 41 source-tree search count changed")
    for term in ("body geometry", "mass distribution", "inertia tensor"):
        if term not in absence.get("query_terms", []):
            fail(f"Phase 41 geometry absence query term missing: {term}")
    context_hits = absence.get("context_hits")
    if not isinstance(context_hits, list) or not any("physical pendulum" in str(hit) for hit in context_hits):
        fail("Phase 41 geometry absence context hits changed")
    for parameter in (
        "body_geometry",
        "mass_distribution",
        "inertia_tensor",
        "raw_joint_force_curve_data",
    ):
        if parameter not in audit.missing_parameters:
            fail(f"Phase 41 missing parameter changed: {parameter}")
    for blocker in (
        "physical_pendulum_geometry_parameters_missing_from_public_source_assets",
        "raw_physical_pendulum_curve_data_missing_from_public_source_assets",
        "physical_pendulum_private_author_assets_not_audited",
    ):
        if blocker not in audit.blockers:
            fail(f"Phase 41 source audit blocker missing: {blocker}")

    try:
        config = load_physical_pendulum_config(
            ROOT / "configs/experiments/single_body_physical_pendulum.yaml"
        )
        matrix = load_experiment_matrix(ROOT / "configs/experiments/paper_experiment_matrix.yaml")
        validate_physical_pendulum_config_against_matrix(config, matrix)
    except (ExperimentRunConfigError, ExperimentMatrixError) as exc:
        fail(f"Phase 41 physical-pendulum config validation failed: {exc}")

    matrix_claim = next(
        (
            experiment
            for experiment in matrix.experiments
            if experiment.claim_id == "experiment.single_body.physical_pendulum"
        ),
        None,
    )
    if matrix_claim is None:
        fail("Phase 41 matrix missing physical-pendulum experiment")
    if "pendulum_geometry_unknown" not in matrix_claim.blocking_reasons:
        fail("Phase 41 matrix must retain pendulum_geometry_unknown")
    if "pendulum_geometry_unknown" not in config.failure_reason:
        fail("Phase 41 analytic config report must retain geometry failure reason")

    report_paths = {
        "analytic_reference": config.output_report,
        "mabd_development": config.mabd_development.output_report,
        "mabd_newton": config.mabd_newton.output_report,
        "rbd_implicit_baseline": config.rbd_baseline.output_report,
        "comparison": config.comparison.output_report,
    }
    reports = {
        name: load_claim_report(ROOT / path)
        for name, path in report_paths.items()
    }
    for name, report in reports.items():
        if report.status.value != "incomplete":
            fail(f"Phase 41 {name} report must remain incomplete")
        if report.observed.get("full_experiment_claim_passed") is not False:
            fail(f"Phase 41 {name} report must not pass full experiment claim")
        blockers = report.observed.get("blocking_reasons")
        if not isinstance(blockers, list):
            fail(f"Phase 41 {name} blockers must be a list")
        if "pendulum_geometry_unknown" not in blockers:
            fail(f"Phase 41 {name} must retain pendulum_geometry_unknown")

    comparison = reports["comparison"]
    if comparison.observed.get("missing_paper_metrics") != [
        "joint_force_error:paper_geometry_unknown"
    ]:
        fail("Phase 41 comparison missing_paper_metrics changed")
    if "physical_pendulum_comparison_pass_gate_not_enabled" not in comparison.observed.get(
        "blocking_reasons", []
    ):
        fail("Phase 41 comparison pass gate blocker missing")

    claims = read_yaml(ROOT / "docs/reference/paper-claims.yaml").get("claims")
    if not isinstance(claims, list):
        fail("paper-claims.yaml missing claims list")
    found_physical_pendulum = False
    for claim in claims:
        if not isinstance(claim, dict):
            continue
        claim_id = str(claim.get("claim_id", ""))
        if claim_id == "experiment.single_body.physical_pendulum":
            found_physical_pendulum = True
            if claim.get("reproduction_status") != "intended":
                fail("Phase 41 must keep physical-pendulum experiment status intended")
        if claim_id.startswith("experiment.") and claim.get("reproduction_status") == "passed":
            fail("Phase 41 must not pass experiment.* claims")
    if not found_physical_pendulum:
        fail("paper-claims.yaml missing physical-pendulum claim")


def _require_finite_scalar(value: Any, context: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        fail(f"{context} must be a finite scalar")
    result = float(value)
    if not np.isfinite(result):
        fail(f"{context} must be finite")
    return result


def _require_finite_vector3(value: Any, context: str) -> list[float]:
    if not isinstance(value, list | tuple) or len(value) != 3:
        fail(f"{context} must be a length-3 vector")
    return [
        _require_finite_scalar(component, f"{context}[{index}]")
        for index, component in enumerate(value)
    ]


def _record_sha256_for_artifact(text: str, artifact_path: str) -> str:
    lines = text.splitlines()
    target = f"- `{artifact_path}`"
    for start_index, line in enumerate(lines):
        if line.strip() != target:
            continue
        for block_line in lines[start_index + 1:]:
            if block_line.startswith("- `reports/experiment_matrix/"):
                break
            tokens = block_line.split("`")
            for token in tokens[1::2]:
                if len(token) == 64 and all(character in "0123456789abcdef" for character in token):
                    return token
        fail(f"Phase 42 record missing sha256 below {artifact_path}")
    fail(f"Phase 42 record missing artifact path: {artifact_path}")


def validate_phase42_record() -> None:
    text = (
        ROOT / "docs/records/2026-05-17-phase42-spinning-box-report-artifacts.md"
    ).read_text(encoding="utf-8")
    required_snippets = (
        "## Status\n\npassed",
        "## Repository",
        "phase42-spinning-box-report-artifacts",
        "## Report Artifacts",
        "reports/experiment_matrix/single_body_spinning_box.json",
        "reports/experiment_matrix/single_body_spinning_box_paper_horizon.json",
        "reports/experiment_matrix/single_body_spinning_box_rbd_baseline.json",
        "reports/experiment_matrix/single_body_spinning_box_comparison.json",
        "mabd_cpu_oracle_development",
        "mabd_cpu_oracle_paper_horizon_diagnostic",
        "paper_faithful_implicit_rbd",
        "spinning_box_multilane_comparison_development",
        "rbd_implicit_baseline lane_gate_status = `passed`",
        "mabd_newton lane_gate_status = `incomplete`",
        "mabd_paper_horizon_diagnostic_thresholds_violated",
        "mabd_kinematic_feasibility_blocker_recorded",
        "mabd_newton_report_incomplete",
        "spinning_box_comparison_pass_gate_not_enabled",
        "## Claim Impact",
        "No `experiment.*` claim is passed.",
        "`experiment.single_body.spinning_box` remains blocked_by_baselines",
        "does not pass the spinning-box experiment",
        "## Verification Commands",
        "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests -p 'test_spinning_box_report_artifacts.py'",
        "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py",
        "git diff --check",
    )
    for snippet in required_snippets:
        if snippet not in text:
            fail(f"Phase 42 record missing required evidence field: {snippet}")
    for placeholder in ("TO_BE_BACKFILLED_PHASE42", "phase42-working-tree", "<implementation-commit>"):
        if placeholder in text:
            fail("Phase 42 record contains stale placeholder")

    lower_text = text.lower()
    for snippet in (
        "spinning-box experiment passed",
        "passed spinning-box experiment",
        "m-abd lane passed",
        "mabd_newton lane passed",
        "comparison pass gate enabled",
        "runtime performance reproduced",
        "full reproduction complete",
    ):
        if snippet in lower_text:
            fail(f"Phase 42 record overclaims unsupported evidence: {snippet}")

    boundary_text = (ROOT / "docs/reference/claim-boundaries.md").read_text(encoding="utf-8")
    normalized_boundary_text = " ".join(boundary_text.split())
    for snippet in (
        "This repository contains Phase 42 spinning-box report-artifact evidence",
        "Phase 42 verifies committed compact JSON reports",
        "`rbd_implicit_baseline` lane gate status: `passed`",
        "`mabd_newton` lane gate status: `incomplete`",
        "`mabd_paper_horizon_diagnostic_thresholds_violated`",
        "`mabd_kinematic_feasibility_blocker_recorded`",
        "`spinning_box_comparison_pass_gate_not_enabled`",
        "Phase 42 does not verify a passed spinning-box experiment",
        "Phase 42 spinning-box report artifacts",
    ):
        if snippet not in normalized_boundary_text:
            fail(f"Phase 42 claim boundary missing: {snippet}")

    try:
        config = load_spinning_box_config(ROOT / "configs/experiments/single_body_spinning_box.yaml")
        matrix = load_experiment_matrix(ROOT / "configs/experiments/paper_experiment_matrix.yaml")
        validate_spinning_box_config_against_matrix(config, matrix)
    except (ExperimentRunConfigError, ExperimentMatrixError) as exc:
        fail(f"Phase 42 spinning-box config validation failed: {exc}")

    report_paths = {
        "mabd": "reports/experiment_matrix/single_body_spinning_box.json",
        "paper_horizon": "reports/experiment_matrix/single_body_spinning_box_paper_horizon.json",
        "rbd": "reports/experiment_matrix/single_body_spinning_box_rbd_baseline.json",
        "comparison": "reports/experiment_matrix/single_body_spinning_box_comparison.json",
    }
    reports = {
        name: load_claim_report(ROOT / path)
        for name, path in report_paths.items()
    }
    source_commits = {report.source_commit for report in reports.values()}
    if len(source_commits) != 1:
        fail("Phase 42 reports must share the same source_commit")
    report_source_commit = next(iter(source_commits))
    if report_source_commit in PLACEHOLDER_SOURCE_COMMITS:
        fail("Phase 42 report source_commit must not be a placeholder")
    if report_source_commit not in text:
        fail("Phase 42 record must list the report source_commit")
    for name, report in reports.items():
        if report.vendored_newton_commit != VENDORED_NEWTON_COMMIT:
            fail(f"Phase 42 {name} report vendored Newton commit changed")
        if report.claim_id != config.claim_id:
            fail(f"Phase 42 {name} report claim_id does not match config")
        if report.scene_id != config.scene_id:
            fail(f"Phase 42 {name} report scene_id does not match config")
        if report.status.value != "incomplete":
            fail(f"Phase 42 {name} report must remain incomplete")
        actual_hash = sha256_file(ROOT / report_paths[name])
        record_hash = _record_sha256_for_artifact(text, report_paths[name])
        if record_hash != actual_hash:
            fail(f"Phase 42 {name} report sha256 mismatch")

    mabd = reports["mabd"]
    if mabd.baseline_lane != "mabd_newton":
        fail("Phase 42 MABD report lane changed")
    if mabd.solver_mode != "mabd_cpu_oracle_development":
        fail("Phase 42 MABD report solver mode changed")
    if mabd.backend != "cpu_numpy":
        fail("Phase 42 MABD report backend changed")
    if "mabd_newton lane pass" not in mabd.failure_reason:
        fail("Phase 42 MABD report must retain incomplete lane-pass failure reason")
    for metric in (
        "linear_momentum_error",
        "angular_momentum_error",
        "energy_drift",
        "relative_energy_drift",
        "generalized_momentum_delta_norm",
    ):
        _require_finite_scalar(mabd.observed.get(metric), f"Phase 42 MABD {metric}")
    for vector_metric in ("initial_position_m", "final_position_m"):
        _require_finite_vector3(mabd.observed.get(vector_metric), f"Phase 42 MABD {vector_metric}")
    if mabd.observed.get("mabd_rotation_mode") != "polar":
        fail("Phase 42 MABD report must retain polar rotation mode")
    if "lane_gate_status" in mabd.observed:
        fail("Phase 42 MABD report must not expose a passed lane gate")

    paper_horizon = reports["paper_horizon"]
    if paper_horizon.baseline_lane != "mabd_newton":
        fail("Phase 42 paper-horizon report lane changed")
    if paper_horizon.solver_mode != "mabd_cpu_oracle_paper_horizon_diagnostic":
        fail("Phase 42 paper-horizon solver mode changed")
    observed = paper_horizon.observed
    if observed.get("mabd_paper_horizon_status") != "development_gap_observed":
        fail("Phase 42 paper-horizon diagnostic status changed")
    if observed.get("mabd_kinematic_feasibility_status") != (
        "paper_momentum_requires_affine_stretch_under_q_delta_over_h"
    ):
        fail("Phase 42 paper-horizon feasibility status changed")
    if "lane_gate_status" in observed:
        fail("Phase 42 paper-horizon report must not expose a passed lane gate")
    blockers = observed.get("blocking_reasons")
    if not isinstance(blockers, list):
        fail("Phase 42 paper-horizon blockers must be a list")
    for blocker in (
        "mabd_newton_report_incomplete",
        "mabd_paper_horizon_diagnostic_thresholds_violated",
        "mabd_kinematic_feasibility_blocker_recorded",
    ):
        if blocker not in blockers:
            fail(f"Phase 42 paper-horizon blocker missing: {blocker}")
    violations = observed.get("threshold_violations")
    if not isinstance(violations, list):
        fail("Phase 42 paper-horizon threshold_violations must be a list")
    for violation in (
        "max_abs_det_minus_one",
        "max_affine_orthogonality_error",
        "max_relative_kinetic_energy_drift",
        "max_relative_total_energy_drift",
        "max_singular_value",
    ):
        if violation not in violations:
            fail(f"Phase 42 paper-horizon threshold violation missing: {violation}")
    if _require_finite_scalar(observed.get("energy_drift"), "Phase 42 paper-horizon energy_drift") <= 0.0:
        fail("Phase 42 paper-horizon energy drift must remain positive diagnostic gap")

    rbd = reports["rbd"]
    if rbd.baseline_lane != "rbd_implicit_baseline":
        fail("Phase 42 RBD report lane changed")
    if rbd.solver_mode != "paper_faithful_implicit_rbd":
        fail("Phase 42 RBD solver mode changed")
    if rbd.backend != "cpu_numpy_newton_only":
        fail("Phase 42 RBD backend changed")
    if rbd.observed.get("lane_gate_status") != "passed":
        fail("Phase 42 RBD lane gate must remain passed")
    lane_gate = rbd.observed.get("lane_pass_gate")
    if not isinstance(lane_gate, dict) or lane_gate.get("thresholds_met") is not True:
        fail("Phase 42 RBD lane pass gate must keep thresholds_met=true")
    if lane_gate.get("full_experiment_claim_passed") is not False:
        fail("Phase 42 RBD lane gate must not pass the full experiment")
    for metric in ("linear_momentum_error", "angular_momentum_error", "energy_drift"):
        if _require_finite_scalar(rbd.observed.get(metric), f"Phase 42 RBD {metric}") != 0.0:
            fail(f"Phase 42 RBD {metric} changed")

    comparison = reports["comparison"]
    if comparison.baseline_lane != "spinning_box_comparison_protocol":
        fail("Phase 42 comparison lane changed")
    if comparison.solver_mode != "spinning_box_multilane_comparison_development":
        fail("Phase 42 comparison solver mode changed")
    if comparison.backend != "report_protocol":
        fail("Phase 42 comparison backend changed")
    observed = comparison.observed
    if observed.get("lane_gate_statuses", {}).get("mabd_newton") != "incomplete":
        fail("Phase 42 comparison MABD lane gate status must remain incomplete")
    if observed.get("lane_gate_statuses", {}).get("rbd_implicit_baseline") != "passed":
        fail("Phase 42 comparison RBD lane gate status must remain passed")
    for key in (
        "missing_required_metrics",
        "invalid_required_metrics",
        "missing_required_vector_metrics",
        "invalid_required_vector_metrics",
    ):
        if observed.get(key) != []:
            fail(f"Phase 42 comparison {key} changed")
    blockers = observed.get("blocking_reasons")
    if not isinstance(blockers, list):
        fail("Phase 42 comparison blockers must be a list")
    for blocker in (
        "mabd_newton_report_incomplete",
        "spinning_box_comparison_pass_gate_not_enabled",
    ):
        if blocker not in blockers:
            fail(f"Phase 42 comparison blocker missing: {blocker}")
    if "rbd_implicit_baseline_report_incomplete" in blockers:
        fail("Phase 42 comparison must not mark the RBD lane gate incomplete")
    if "rbd_implicit_baseline_not_paper_faithful" in blockers:
        fail("Phase 42 comparison must keep the paper-faithful RBD solver identity")
    if comparison.raw_outputs.get("mabd_report") != report_paths["mabd"]:
        fail("Phase 42 comparison must consume committed MABD report path")
    if comparison.raw_outputs.get("rbd_report") != report_paths["rbd"]:
        fail("Phase 42 comparison must consume committed RBD report path")
    lane_metrics = observed.get("lane_metrics")
    if not isinstance(lane_metrics, dict):
        fail("Phase 42 comparison lane_metrics must be a mapping")
    lane_vector_metrics = observed.get("lane_vector_metrics")
    if not isinstance(lane_vector_metrics, dict):
        fail("Phase 42 comparison lane_vector_metrics must be a mapping")
    required_metrics = ("linear_momentum_error", "angular_momentum_error", "energy_drift")
    required_vector_metrics = ("initial_position_m", "final_position_m")
    for lane, report in (("mabd_newton", mabd), ("rbd_implicit_baseline", rbd)):
        metric_snapshot = lane_metrics.get(lane)
        if not isinstance(metric_snapshot, dict):
            fail(f"Phase 42 comparison lane_metrics missing lane: {lane}")
        for metric in required_metrics:
            actual = _require_finite_scalar(report.observed.get(metric), f"Phase 42 {lane} source {metric}")
            snapshot = _require_finite_scalar(
                metric_snapshot.get(metric),
                f"Phase 42 comparison {lane} {metric}",
            )
            if snapshot != actual:
                fail(f"Phase 42 comparison lane metric mismatch: {lane}:{metric}")
        vector_snapshot = lane_vector_metrics.get(lane)
        if not isinstance(vector_snapshot, dict):
            fail(f"Phase 42 comparison lane_vector_metrics missing lane: {lane}")
        for metric in required_vector_metrics:
            actual_vector = _require_finite_vector3(
                report.observed.get(metric),
                f"Phase 42 {lane} source {metric}",
            )
            snapshot_vector = _require_finite_vector3(
                vector_snapshot.get(metric),
                f"Phase 42 comparison {lane} {metric}",
            )
            if snapshot_vector != actual_vector:
                fail(f"Phase 42 comparison lane vector metric mismatch: {lane}:{metric}")
    lane_differences = observed.get("lane_metric_differences")
    if not isinstance(lane_differences, dict):
        fail("Phase 42 comparison lane_metric_differences must be a mapping")
    scalar_differences = lane_differences.get("mabd_newton_minus_rbd_implicit_baseline")
    if not isinstance(scalar_differences, dict):
        fail("Phase 42 comparison scalar lane differences missing")
    for metric in required_metrics:
        expected_difference = float(mabd.observed[metric]) - float(rbd.observed[metric])
        observed_difference = _require_finite_scalar(
            scalar_differences.get(metric),
            f"Phase 42 comparison difference {metric}",
        )
        if observed_difference != expected_difference:
            fail(f"Phase 42 comparison lane metric difference mismatch: {metric}")
    lane_vector_differences = observed.get("lane_vector_metric_differences")
    if not isinstance(lane_vector_differences, dict):
        fail("Phase 42 comparison lane_vector_metric_differences must be a mapping")
    vector_differences = lane_vector_differences.get("mabd_newton_minus_rbd_implicit_baseline")
    if not isinstance(vector_differences, dict):
        fail("Phase 42 comparison vector lane differences missing")
    for metric in required_vector_metrics:
        mabd_vector = [float(value) for value in mabd.observed[metric]]
        rbd_vector = [float(value) for value in rbd.observed[metric]]
        expected_vector_difference = [
            mabd_component - rbd_component
            for mabd_component, rbd_component in zip(mabd_vector, rbd_vector, strict=True)
        ]
        observed_vector_difference = _require_finite_vector3(
            vector_differences.get(metric),
            f"Phase 42 comparison vector difference {metric}",
        )
        if observed_vector_difference != expected_vector_difference:
            fail(f"Phase 42 comparison lane vector metric difference mismatch: {metric}")

    claims = read_yaml(ROOT / "docs/reference/paper-claims.yaml").get("claims")
    if not isinstance(claims, list):
        fail("paper-claims.yaml missing claims list")
    found_spinning_box = False
    for claim in claims:
        if not isinstance(claim, dict):
            continue
        claim_id = str(claim.get("claim_id", ""))
        if claim_id == "experiment.single_body.spinning_box":
            found_spinning_box = True
            if claim.get("reproduction_status") != "intended":
                fail("Phase 42 must keep paper-claims spinning-box experiment status intended")
        if claim_id.startswith("experiment.") and claim.get("reproduction_status") == "passed":
            fail("Phase 42 must not pass experiment.* claims")
    if not found_spinning_box:
        fail("paper-claims.yaml missing spinning-box claim")

    matrix = read_yaml(ROOT / "configs/experiments/paper_experiment_matrix.yaml")
    experiments = matrix.get("experiments")
    if not isinstance(experiments, list):
        fail("Phase 42 experiment matrix missing experiments")
    matrix_entry = next(
        (
            item
            for item in experiments
            if isinstance(item, dict)
            and item.get("claim_id") == "experiment.single_body.spinning_box"
        ),
        None,
    )
    if matrix_entry is None:
        fail("Phase 42 matrix missing spinning-box experiment")
    if matrix_entry.get("reproduction_status") != "blocked_by_baselines":
        fail("Phase 42 matrix must keep spinning-box blocked_by_baselines")
    matrix_blockers = matrix_entry.get("blocking_reasons")
    if not isinstance(matrix_blockers, list):
        fail("Phase 42 matrix spinning-box blockers must be a list")
    for blocker in (
        "mabd_newton_report_incomplete",
        "spinning_box_comparison_report_incomplete",
    ):
        if blocker not in matrix_blockers:
            fail(f"Phase 42 matrix blocker missing: {blocker}")


def validate_phase43_record() -> None:
    text = (
        ROOT / "docs/records/2026-05-18-phase43-t-handle-rk4-reference.md"
    ).read_text(encoding="utf-8")
    required_snippets = (
        "## Status\n\npassed",
        "## Repository",
        "phase43-t-handle-reference",
        "## Paper Source",
        "experiment.tex:57-75",
        "images/T-handle/T-handle.pdf",
        "5ae6464fd7e7e6fd471ad56e67cdbead6014736cb731a232ce29d80630a72c1c",
        "## Report Artifact",
        "reports/experiment_matrix/single_body_t_handle_rk4_reference.json",
        "t_handle_torque_free_rk4_reference",
        "rbd_rk4_reference",
        "diagnostic_generated",
        "exact_t_handle_geometry_unknown",
        "raw_t_handle_reference_curve_data_missing",
        "mabd_newton_report_missing",
        "t_handle_comparison_report_missing",
        "## Claim Impact",
        "No `experiment.*` claim is passed.",
        "`experiment.single_body.t_handle` remains intended",
        "does not implement a paper-faithful T-handle geometry",
        "## Verification Commands",
        "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_t_handle_reference tests.test_experiment_run_configs tests.test_experiment_runner tests.test_phase0_bootstrap",
        "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py",
        "git diff --check",
    )
    for snippet in required_snippets:
        if snippet not in text:
            fail(f"Phase 43 record missing required evidence field: {snippet}")
    for placeholder in ("TO_BE_BACKFILLED_PHASE43", "phase43-working-tree", "<implementation-commit>"):
        if placeholder in text:
            fail("Phase 43 record contains stale placeholder")

    lower_text = text.lower()
    for snippet in (
        "t-handle experiment passed",
        "passed t-handle experiment",
        "m-abd t-handle lane passed",
        "mabd_newton lane passed",
        "paper-faithful t-handle geometry reconstructed",
        "raw curve agreement passed",
        "runtime performance reproduced",
        "full reproduction complete",
    ):
        if snippet in lower_text:
            fail(f"Phase 43 record overclaims unsupported evidence: {snippet}")

    boundary_text = (ROOT / "docs/reference/claim-boundaries.md").read_text(encoding="utf-8")
    normalized_boundary_text = " ".join(boundary_text.split())
    for snippet in (
        "This repository contains Phase 43 T-handle RK4 reference diagnostic lane",
        "Phase 43 verifies a source-backed `rbd_rk4_reference` diagnostic lane",
        "`raw_t_handle_reference_curve_data_missing`",
        "`mabd_newton_report_missing`",
        "`t_handle_comparison_report_missing`",
        "Phase 43 does not verify a passed T-handle experiment",
        "Phase 43 T-handle RK4 reference",
    ):
        if snippet not in normalized_boundary_text:
            fail(f"Phase 43 claim boundary missing: {snippet}")

    try:
        config = load_t_handle_config(ROOT / "configs/experiments/single_body_t_handle.yaml")
        matrix = load_experiment_matrix(ROOT / "configs/experiments/paper_experiment_matrix.yaml")
        validate_t_handle_config_against_matrix(config, matrix)
    except (ExperimentRunConfigError, ExperimentMatrixError) as exc:
        fail(f"Phase 43 T-handle config validation failed: {exc}")

    report_path = "reports/experiment_matrix/single_body_t_handle_rk4_reference.json"
    report = load_claim_report(ROOT / report_path)
    if report.source_commit in PLACEHOLDER_SOURCE_COMMITS:
        fail("Phase 43 report source_commit must not be a placeholder")
    if report.source_commit not in text:
        fail("Phase 43 record must list the report source_commit")
    if report.vendored_newton_commit != VENDORED_NEWTON_COMMIT:
        fail("Phase 43 report vendored Newton commit changed")
    if report.claim_id != config.claim_id:
        fail("Phase 43 report claim_id does not match config")
    if report.scene_id != config.scene_id:
        fail("Phase 43 report scene_id does not match config")
    if report.asset_hashes.get("t_handle_procedural") != "not_applicable_procedural":
        fail("Phase 43 T-handle asset hash must match manifest checksum")
    if report.status.value != "incomplete":
        fail("Phase 43 T-handle report must remain incomplete")
    actual_hash = sha256_file(ROOT / report_path)
    record_hash = _record_sha256_for_artifact(text, report_path)
    if record_hash != actual_hash:
        fail("Phase 43 T-handle report sha256 mismatch")

    if report.baseline_lane != "rbd_rk4_reference":
        fail("Phase 43 T-handle report lane changed")
    if report.solver_mode != "t_handle_torque_free_rk4_reference":
        fail("Phase 43 T-handle report solver mode changed")
    if report.backend != "cpu_numpy":
        fail("Phase 43 T-handle report backend changed")
    observed = report.observed
    trajectory = roll_out_t_handle_rk4_reference(config)
    if observed.get("lane_status") != "diagnostic_generated":
        fail("Phase 43 T-handle diagnostic status changed")
    if "lane_gate_status" in observed:
        fail("Phase 43 T-handle report must not expose a passed lane gate")
    if observed.get("full_experiment_claim_passed") is not False:
        fail("Phase 43 T-handle report must not pass full experiment claim")
    if observed.get("reference_not_paper_geometry") is not True:
        fail("Phase 43 T-handle report must mark reference_not_paper_geometry")
    blockers = observed.get("blocking_reasons")
    if not isinstance(blockers, list):
        fail("Phase 43 T-handle blockers must be a list")
    for blocker in (
        "exact_t_handle_geometry_unknown",
        "raw_t_handle_reference_curve_data_missing",
        "mabd_newton_report_missing",
        "t_handle_comparison_report_missing",
        "t_handle_timing_evidence_missing",
    ):
        if blocker not in blockers:
            fail(f"Phase 43 T-handle blocker missing: {blocker}")
    if observed.get("required_missing_lanes") != ["mabd_newton"]:
        fail("Phase 43 T-handle required_missing_lanes changed")
    if _require_finite_scalar(observed.get("time_step_s"), "Phase 43 T-handle time_step_s") != 1.0e-4:
        fail("Phase 43 T-handle RK4 step changed")
    if _require_finite_scalar(observed.get("duration_s"), "Phase 43 T-handle duration_s") != 4.0:
        fail("Phase 43 T-handle diagnostic duration changed")
    if abs(
        _require_finite_scalar(
            observed.get("relative_energy_drift"),
            "Phase 43 T-handle relative_energy_drift",
        )
    ) > config.reference.thresholds["max_relative_energy_drift"]:
        fail("Phase 43 T-handle relative energy drift exceeded threshold")
    if abs(
        _require_finite_scalar(
            observed.get("angular_momentum_norm_drift"),
            "Phase 43 T-handle angular_momentum_norm_drift",
        )
    ) > config.reference.thresholds["max_angular_momentum_norm_drift"]:
        fail("Phase 43 T-handle angular momentum norm drift exceeded threshold")
    if _require_finite_scalar(
        observed.get("intermediate_axis_sign_flips"),
        "Phase 43 T-handle intermediate_axis_sign_flips",
    ) < config.reference.thresholds["min_intermediate_axis_sign_flips"]:
        fail("Phase 43 T-handle sign-flip count below threshold")
    if (
        int(observed.get("intermediate_axis_sign_flips", -1))
        != trajectory.intermediate_axis_sign_flips
    ):
        fail("Phase 43 T-handle sign-flip count does not match recomputed RK4 rollout")
    for key, expected in (
        ("energy_initial", trajectory.energy_initial),
        ("energy_final", trajectory.energy_final),
        ("relative_energy_drift", trajectory.relative_energy_drift),
        ("angular_momentum_norm_initial", trajectory.angular_momentum_norm_initial),
        ("angular_momentum_norm_final", trajectory.angular_momentum_norm_final),
        ("angular_momentum_norm_drift", trajectory.angular_momentum_norm_drift),
    ):
        actual = _require_finite_scalar(observed.get(key), f"Phase 43 T-handle {key}")
        if not np.isclose(actual, expected, rtol=0.0, atol=1.0e-15):
            fail(f"Phase 43 T-handle {key} does not match recomputed RK4 rollout")
    _require_finite_vector3(
        observed.get("principal_inertia_kg_m2"),
        "Phase 43 T-handle principal_inertia_kg_m2",
    )
    if not np.allclose(
        observed.get("principal_inertia_kg_m2"),
        config.reference.principal_inertia_kg_m2.tolist(),
        rtol=0.0,
        atol=1.0e-15,
    ):
        fail("Phase 43 T-handle inertia does not match config")
    _require_finite_vector3(
        observed.get("initial_angular_velocity_rad_s"),
        "Phase 43 T-handle initial_angular_velocity_rad_s",
    )
    if not np.allclose(
        observed.get("initial_angular_velocity_rad_s"),
        config.reference.initial_angular_velocity_rad_s.tolist(),
        rtol=0.0,
        atol=1.0e-15,
    ):
        fail("Phase 43 T-handle initial angular velocity does not match config")
    gravity = _require_finite_vector3(observed.get("gravity_m_s2"), "Phase 43 T-handle gravity_m_s2")
    if gravity != [0.0, 0.0, 0.0]:
        fail("Phase 43 T-handle gravity must remain zero")
    samples = observed.get("angular_velocity_samples")
    if not isinstance(samples, list) or len(samples) != config.reference.sample_count:
        fail("Phase 43 T-handle angular_velocity_samples changed")
    for index, sample in enumerate(samples):
        if not isinstance(sample, dict):
            fail("Phase 43 T-handle sample must be a mapping")
        if sample.get("sample_index") != index:
            fail("Phase 43 T-handle sample_index changed")
        for key in ("time_s", "omega_x_rad_s", "omega_y_rad_s", "omega_z_rad_s"):
            _require_finite_scalar(sample.get(key), f"Phase 43 T-handle sample {index} {key}")
        expected_row = trajectory.samples[index]
        for key, expected in (
            ("time_s", expected_row[0]),
            ("omega_x_rad_s", expected_row[1]),
            ("omega_y_rad_s", expected_row[2]),
            ("omega_z_rad_s", expected_row[3]),
        ):
            actual = float(sample[key])
            if not np.isclose(actual, float(expected), rtol=0.0, atol=1.0e-14):
                fail(f"Phase 43 T-handle sample {index} {key} does not match recomputed RK4 rollout")
    if observed.get("threshold_violations") != []:
        fail("Phase 43 T-handle threshold_violations changed")
    if report.expected.get("source_lines") != list(config.source_lines):
        fail("Phase 43 T-handle expected source_lines changed")
    if report.expected.get("figure_pdf_sha256") != config.reference.figure_pdf_sha256:
        fail("Phase 43 T-handle expected figure hash changed")
    if report.expected.get("matrix_claim_report") != "reports/experiment_matrix/single_body_t_handle.json":
        fail("Phase 43 T-handle matrix claim report binding changed")
    if report.expected.get("lane_report") != config.reference.output_report:
        fail("Phase 43 T-handle lane report binding changed")

    claims = read_yaml(ROOT / "docs/reference/paper-claims.yaml").get("claims")
    if not isinstance(claims, list):
        fail("paper-claims.yaml missing claims list")
    found_t_handle = False
    for claim in claims:
        if not isinstance(claim, dict):
            continue
        claim_id = str(claim.get("claim_id", ""))
        if claim_id == "experiment.single_body.t_handle":
            found_t_handle = True
            if claim.get("reproduction_status") != "intended":
                fail("Phase 43 must keep T-handle experiment status intended")
            conflict_note = str(claim.get("conflict_note", ""))
            if "exact_t_handle_geometry_unknown" not in conflict_note:
                fail("Phase 43 T-handle conflict_note missing geometry blocker")
            if "raw_t_handle_reference_curve_data_missing" not in conflict_note:
                fail("Phase 43 T-handle conflict_note missing raw-curve blocker")
        if claim_id.startswith("experiment.") and claim.get("reproduction_status") == "passed":
            fail("Phase 43 must not pass experiment.* claims")
    if not found_t_handle:
        fail("paper-claims.yaml missing T-handle claim")

    matrix_data = read_yaml(ROOT / "configs/experiments/paper_experiment_matrix.yaml")
    experiments = matrix_data.get("experiments")
    if not isinstance(experiments, list):
        fail("Phase 43 experiment matrix missing experiments")
    matrix_entry = next(
        (
            item
            for item in experiments
            if isinstance(item, dict)
            and item.get("claim_id") == "experiment.single_body.t_handle"
        ),
        None,
    )
    if matrix_entry is None:
        fail("Phase 43 matrix missing T-handle experiment")
    if matrix_entry.get("reproduction_status") != "planned":
        fail("Phase 43 matrix must keep T-handle planned")
    matrix_blockers = matrix_entry.get("blocking_reasons")
    if not isinstance(matrix_blockers, list):
        fail("Phase 43 matrix T-handle blockers must be a list")
    for blocker in (
        "exact_t_handle_geometry_unknown",
        "raw_t_handle_reference_curve_data_missing",
        "mabd_newton_report_missing",
        "t_handle_comparison_report_missing",
    ):
        if blocker not in matrix_blockers:
            fail(f"Phase 43 matrix blocker missing: {blocker}")


def _pip_freeze_parts(python: Path, context: str) -> tuple[list[str], list[str]]:
    result = subprocess.run(
        [str(python), "-m", "pip", "freeze", "--local"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        fail(f"{context} pip freeze failed: {result.stderr.strip()}")
    lines = sorted(line.strip() for line in result.stdout.splitlines() if line.strip())
    editable = [line for line in lines if line.startswith("-e ")]
    non_editable = [line for line in lines if not line.startswith("-e ")]
    return non_editable, editable


def _editable_lines_by_egg(lines: list[str]) -> dict[str, str]:
    eggs: dict[str, str] = {}
    for line in lines:
        marker = "#egg="
        if marker not in line:
            continue
        egg = line.split(marker, 1)[1].split("&", 1)[0]
        eggs[egg] = line
    return eggs


def _require_freeze_pin(lines: list[str], package: str, context: str) -> str:
    prefix = f"{package}=="
    matches = [line for line in lines if line.startswith(prefix)]
    if len(matches) != 1:
        fail(f"{context} must contain one {package} version pin")
    return matches[0]


def validate_phase44_environment_clone() -> None:
    if not PHASE44_REFERENCE_PYTHON.exists():
        fail("Phase 44 reference physics-primitive-agent Python is missing")
    if not MABD_PYTHON.exists():
        fail("Phase 44 canonical mabd-newton Python is missing")

    reference_packages, reference_editable = _pip_freeze_parts(
        PHASE44_REFERENCE_PYTHON,
        "Phase 44 reference env",
    )
    current_packages, current_editable = _pip_freeze_parts(MABD_PYTHON, "Phase 44 current env")

    reference_eggs = _editable_lines_by_egg(reference_editable)
    current_eggs = _editable_lines_by_egg(current_editable)
    if "primitive_collision_compiler" not in reference_eggs:
        fail("Phase 44 reference env missing primitive_collision_compiler editable root")
    if "mabd_newton" not in current_eggs:
        fail("Phase 44 current env missing mabd_newton editable root")

    for context, eggs in (
        ("Phase 44 reference env", reference_eggs),
        ("Phase 44 current env", current_eggs),
    ):
        newton_line = eggs.get("newton")
        if newton_line is None:
            fail(f"{context} missing editable Newton source")
        if "https://github.com/newton-physics/newton.git" not in newton_line:
            fail(f"{context} Newton editable source changed")
        if VENDORED_NEWTON_COMMIT not in newton_line:
            fail(f"{context} Newton editable commit changed")

    for package in PHASE44_CORE_ENV_PACKAGES:
        reference_pin = _require_freeze_pin(reference_packages, package, "Phase 44 reference env")
        current_pin = _require_freeze_pin(current_packages, package, "Phase 44 current env")
        if reference_pin != current_pin:
            fail(f"Phase 44 environment core package drift: {reference_pin} != {current_pin}")


def validate_phase44_model_path_smoke() -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = f"{ROOT / 'src'}:{ROOT / 'vendor/newton'}"
    code = r"""
import numpy as np
import warp as wp

import newton
from newton.solvers import SolverMABD

builder = newton.ModelBuilder()
SolverMABD.register_custom_attributes(builder)
body_id = builder.add_body()
builder.add_custom_values(
    **{
        "mabd:body_index": body_id,
        "mabd:young_modulus": 1.0,
        "mabd:poisson_ratio": 0.25,
        "mabd:density": 1.0,
        "mabd:polar_mode": 0,
        "mabd:rest_point0": wp.vec3(0.0, 0.0, 0.0),
        "mabd:rest_point1": wp.vec3(1.0, 0.0, 0.0),
        "mabd:rest_point2": wp.vec3(0.0, 1.0, 0.0),
        "mabd:rest_point3": wp.vec3(0.0, 0.0, 1.0),
        "mabd:point_mass0": -1.0,
        "mabd:point_mass1": -1.0,
        "mabd:point_mass2": -1.0,
        "mabd:point_mass3": -1.0,
        "mabd:volume": -1.0,
    }
)
model = builder.finalize()
state_in = model.state()
state_out = model.state()
solver = SolverMABD(model)
solver.step(state_in, state_out, None, None, 0.01)
if solver.cpu_oracle_config is not None:
    raise SystemExit("manual config unexpectedly populated")
if solver.model_cpu_oracle_config is None:
    raise SystemExit("model-derived config was not cached")
if solver.last_step_result is None:
    raise SystemExit("missing last_step_result")
if solver.last_step_result.topology != "unconstrained":
    raise SystemExit(f"unexpected topology {solver.last_step_result.topology}")
if len(solver.model_cpu_oracle_config.bodies) != 1:
    raise SystemExit("model-derived config body count changed")
if not np.isclose(float(solver.model_cpu_oracle_config.bodies[0].precompute.masses.sum()), 1.0 / 6.0):
    raise SystemExit("model-derived tetrahedron density mass changed")
solver.notify_model_changed(0)
if solver.model_cpu_oracle_config is not None:
    raise SystemExit("notify_model_changed did not clear model config cache")
"""
    result = subprocess.run(
        [str(MABD_PYTHON), "-c", code],
        cwd=ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        fail("Phase 44 model-derived SolverMABD smoke failed: " + result.stderr.strip())


def validate_phase44_record() -> None:
    text = (
        ROOT / "docs/records/2026-05-18-phase44-solver-model-config.md"
    ).read_text(encoding="utf-8")
    required_snippets = (
        "## Status\n\npassed_for_solver_model_config_slice",
        "## Repository",
        "phase44-solver-model-config",
        "ddd2696fbbc958b5f313dd40ee49b27e9b89b454",
        "0e506bf9a0e53d74a06eb55d8c093909e3a72f8d",
        "60a957a4f3d02d14d0f025bc4bdb373cfbe686ec",
        "## Vendored Newton",
        "https://github.com/newton-physics/newton.git",
        "96713fa965463b69c229a4d30582c733ff3526bb",
        "Local patch status",
        "locally patched",
        "## Environment",
        "/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python",
        "/cpfs/user/zhuzihou/conda-managed/envs/physics-primitive-newton-py310/bin/python",
        "same package set except editable project root",
        "validator rechecks core package parity and editable roots",
        "primitive_collision_compiler",
        "mabd_newton",
        "## Implementation Evidence",
        "model-derived `SolverMABD.step()`",
        "`mabd:rest_point0`",
        "`mabd:point_mass0`",
        "`mabd:volume`",
        "`mabd:control` rows",
        "`mabd:constraint` rows are rejected",
        "manual `configure_cpu_oracle(...)`",
        "`notify_model_changed()`",
        "## Verification Commands",
        "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_mabd_phase4_solver_step tests.test_mabd_single_body tests.test_mabd_control_forces tests.test_mabd_phase2_joints_kkt tests.test_mabd_phase3_topology_solvers",
        "Ran 82 tests",
        "OK",
        "## Claim Impact",
        "No `experiment.*` claim is passed.",
        "not a full paper reproduction",
    )
    for snippet in required_snippets:
        if snippet not in text:
            fail(f"Phase 44 record missing required evidence field: {snippet}")
    for placeholder in (
        "TO_BE_BACKFILLED_PHASE44",
        "phase44-working-tree",
        "<implementation-commit>",
    ):
        if placeholder in text:
            fail("Phase 44 record contains stale placeholder")

    lower_text = text.lower()
    for snippet in (
        "full paper reproduction complete",
        "experiment.* claim is passed",
        "paper experiment passed",
        "model-derived constraints are implemented",
        "contacts are implemented",
        "gpu solver passed",
        "warp solver passed",
        "runtime performance reproduced",
    ):
        if snippet in lower_text:
            fail(f"Phase 44 record overclaims unsupported evidence: {snippet}")

    boundary_text = (ROOT / "docs/reference/claim-boundaries.md").read_text(encoding="utf-8")
    normalized_boundary_text = " ".join(boundary_text.split())
    for snippet in (
        "This repository contains Phase 44 SolverMABD model-derived CPU body-config",
        "Phase 44 verifies model-derived `SolverMABD.step()` CPU oracle configuration",
        "`mabd:rest_point0`",
        "`mabd:point_mass0`",
        "`mabd:volume`",
        "model `mabd:control` rows",
        "manual `configure_cpu_oracle(...)` support",
        "`notify_model_changed()`",
        "Phase 44 does not verify model-derived `mabd:constraint` rows",
        "Newton `Control` input",
        "GPU/Warp kernels",
        "any passed `experiment.*` claim",
        "Phase 44 model-derived SolverMABD CPU config",
    ):
        if snippet not in normalized_boundary_text:
            fail(f"Phase 44 claim boundary missing: {snippet}")

    validate_phase44_environment_clone()
    validate_phase44_model_path_smoke()


def validate_phase45_model_constraint_smoke() -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = f"{ROOT / 'src'}:{ROOT / 'vendor/newton'}"
    code = r"""
import numpy as np
import warp as wp

import newton
from newton.solvers import SolverMABD, mabd


def add_body_row(builder):
    body_id = builder.add_body()
    builder.add_custom_values(
        **{
            "mabd:body_index": body_id,
            "mabd:young_modulus": 1.0,
            "mabd:poisson_ratio": 0.25,
            "mabd:density": 1.0,
            "mabd:polar_mode": 0,
            "mabd:rest_point0": wp.vec3(0.0, 0.0, 0.0),
            "mabd:rest_point1": wp.vec3(1.0, 0.0, 0.0),
            "mabd:rest_point2": wp.vec3(0.0, 1.0, 0.0),
            "mabd:rest_point3": wp.vec3(0.0, 0.0, 1.0),
            "mabd:point_mass0": -1.0,
            "mabd:point_mass1": -1.0,
            "mabd:point_mass2": -1.0,
            "mabd:point_mass3": -1.0,
            "mabd:volume": -1.0,
        }
    )


def assign_state(state, q, qd):
    q_arr = np.asarray(q, dtype=float)
    qd_arr = np.asarray(qd, dtype=float)
    state.mabd.q0.assign(q_arr[:, 0:3].astype(np.float32))
    state.mabd.q1.assign(q_arr[:, 3:6].astype(np.float32))
    state.mabd.q2.assign(q_arr[:, 6:9].astype(np.float32))
    state.mabd.t.assign(q_arr[:, 9:12].astype(np.float32))
    state.mabd.qd0.assign(qd_arr[:, 0:3].astype(np.float32))
    state.mabd.qd1.assign(qd_arr[:, 3:6].astype(np.float32))
    state.mabd.qd2.assign(qd_arr[:, 6:9].astype(np.float32))
    state.mabd.td.assign(qd_arr[:, 9:12].astype(np.float32))


builder = newton.ModelBuilder()
SolverMABD.register_custom_attributes(builder)
add_body_row(builder)
add_body_row(builder)
builder.add_custom_values(
    **{
        "mabd:constraint_type": 2,
        "mabd:body_a": 0,
        "mabd:body_b": 1,
        "mabd:rank": 3,
        "mabd:gradient_mode": 0,
        "mabd:axis0": wp.vec3(0.0, 1.0, 0.0),
        "mabd:axis1": wp.vec3(0.0, 0.0, 1.0),
        "mabd:cp_index": 1,
    }
)
model = builder.finalize()
state = model.state()
q = [
    mabd.pack_q(np.eye(3), np.array([0.2, 0.0, 0.0])),
    mabd.pack_q(np.eye(3), np.zeros(3)),
]
qd = [np.zeros(12), np.zeros(12)]
assign_state(state, q, qd)
solver = SolverMABD(model)
solver.step(state, state, None, None, 0.1)
config = solver.model_cpu_oracle_config
if solver.cpu_oracle_config is not None:
    raise SystemExit("manual config unexpectedly populated")
if config is None:
    raise SystemExit("model-derived config was not cached")
if len(config.constraints) != 1:
    raise SystemExit("model-derived constraint count changed")
if config.constraints[0].spec.cp_index != 1:
    raise SystemExit("model-derived cp_index changed")
if solver.last_step_result.topology != "dense":
    raise SystemExit(f"unexpected topology {solver.last_step_result.topology}")
if solver.last_step_result.constraint_residual_norm > 1.0e-10:
    raise SystemExit("model-derived joint residual is too large")
"""
    result = subprocess.run(
        [str(MABD_PYTHON), "-c", code],
        cwd=ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        fail("Phase 45 model-derived constraint smoke failed: " + result.stderr.strip())


def validate_phase45_record() -> None:
    text = (
        ROOT / "docs/records/2026-05-18-phase45-model-constraint-config.md"
    ).read_text(encoding="utf-8")
    required_snippets = (
        "## Status\n\npassed_for_solver_model_constraint_config_slice",
        "## Repository",
        "phase45-model-constraint-config",
        "00e54159fcc18cd02f7c2cff74426d276b4f2e11",
        "83534a45b9ec1be456b3eaf9512a0a06b6639402",
        "ca8c8a100471ff0b7a5a42adbb795f64f16a90a6",
        "2eb5e39126b12d4609aa51309c9a78d6a9016fbc",
        "bb4b416341adace4db145df51efcc148409b6363",
        "## Vendored Newton",
        "https://github.com/newton-physics/newton.git",
        "96713fa965463b69c229a4d30582c733ff3526bb",
        "Local patch status",
        "locally patched",
        "## Environment",
        "/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python",
        "validator rechecks editable roots and core package parity",
        "## Implementation Evidence",
        "model-derived `mabd:constraint` rows",
        "`MABDCPUOracleConstraint`",
        "`ball_joint(...)`",
        "`hinge_joint(...)`",
        "`universal_joint(...)`",
        "`prismatic_joint(...)`",
        "`mabd:cp_index`",
        "manual `configure_cpu_oracle(...)`",
        "## RED Evidence",
        "Custom attribute 'mabd:cp_index' is not defined",
        "FAILED (errors=7)",
        "## GREEN Evidence",
        "Ran 80 tests",
        "OK",
        "## Claim Impact",
        "No `experiment.*` claim is passed.",
        "not a full paper reproduction",
        "paper timing",
        "comparative baselines",
        "rendered output",
        "raw simulation logs",
    )
    for snippet in required_snippets:
        if snippet not in text:
            fail(f"Phase 45 record missing required evidence field: {snippet}")
    for placeholder in (
        "TO_BE_BACKFILLED_PHASE45",
        "phase45-working-tree",
        "<implementation-commit>",
    ):
        if placeholder in text:
            fail("Phase 45 record contains stale placeholder")

    lower_text = text.lower()
    for snippet in (
        "full paper reproduction complete",
        "experiment.* claim is passed",
        "paper experiment passed",
        "contacts are implemented",
        "gpu solver passed",
        "warp solver passed",
        "runtime performance reproduced",
    ):
        if snippet in lower_text:
            fail(f"Phase 45 record overclaims unsupported evidence: {snippet}")

    boundary_text = (ROOT / "docs/reference/claim-boundaries.md").read_text(encoding="utf-8")
    normalized_boundary_text = " ".join(boundary_text.split())
    for snippet in (
        "This repository contains Phase 45 SolverMABD model-derived CPU joint-constraint",
        "Phase 45 verifies model-derived `mabd:constraint` rows",
        "`MABDCPUOracleConstraint`",
        "ball, hinge, and universal joint specs",
        "`mabd:cp_index`",
        "rank validation",
        "manual `configure_cpu_oracle(...)` precedence",
        "Phase 45 does not verify model-derived world constraints",
        "Newton `Contacts`",
        "Newton `Control` input",
        "GPU/Warp kernels",
        "paper timing",
        "comparative baselines",
        "rendered output",
        "raw simulation logs",
        "a full paper reproduction",
        "any passed `experiment.*` claim",
        "Phase 45 model-derived SolverMABD joint constraints",
    ):
        if snippet not in normalized_boundary_text:
            fail(f"Phase 45 claim boundary missing: {snippet}")

    validate_phase44_environment_clone()
    validate_phase45_model_constraint_smoke()


def validate_phase46_model_world_constraint_smoke() -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = f"{ROOT / 'src'}:{ROOT / 'vendor/newton'}"
    code = r"""
import numpy as np
import warp as wp

import newton
from newton.solvers import SolverMABD, mabd


def add_body_row(builder):
    body_id = builder.add_body()
    builder.add_custom_values(
        **{
            "mabd:body_index": body_id,
            "mabd:young_modulus": 1.0,
            "mabd:poisson_ratio": 0.25,
            "mabd:density": 1.0,
            "mabd:polar_mode": 0,
            "mabd:rest_point0": wp.vec3(0.0, 0.0, 0.0),
            "mabd:rest_point1": wp.vec3(1.0, 0.0, 0.0),
            "mabd:rest_point2": wp.vec3(0.0, 1.0, 0.0),
            "mabd:rest_point3": wp.vec3(0.0, 0.0, 1.0),
            "mabd:point_mass0": -1.0,
            "mabd:point_mass1": -1.0,
            "mabd:point_mass2": -1.0,
            "mabd:point_mass3": -1.0,
            "mabd:volume": -1.0,
        }
    )


def assign_state(state, q, qd):
    q_arr = np.asarray(q, dtype=float)
    qd_arr = np.asarray(qd, dtype=float)
    state.mabd.q0.assign(q_arr[:, 0:3].astype(np.float32))
    state.mabd.q1.assign(q_arr[:, 3:6].astype(np.float32))
    state.mabd.q2.assign(q_arr[:, 6:9].astype(np.float32))
    state.mabd.t.assign(q_arr[:, 9:12].astype(np.float32))
    state.mabd.qd0.assign(qd_arr[:, 0:3].astype(np.float32))
    state.mabd.qd1.assign(qd_arr[:, 3:6].astype(np.float32))
    state.mabd.qd2.assign(qd_arr[:, 6:9].astype(np.float32))
    state.mabd.td.assign(qd_arr[:, 9:12].astype(np.float32))


builder = newton.ModelBuilder()
SolverMABD.register_custom_attributes(builder)
add_body_row(builder)
builder.add_custom_values(
    **{
        "mabd:world_body": 0,
        "mabd:world_rest_point": wp.vec3(1.0, 0.0, 0.0),
        "mabd:world_point": wp.vec3(1.25, 0.0, 0.0),
    }
)
model = builder.finalize()
state = model.state()
q = [mabd.pack_q(np.eye(3), np.zeros(3))]
qd = [np.zeros(12)]
assign_state(state, q, qd)
solver = SolverMABD(model)
solver.step(state, state, None, None, 0.05)
config = solver.model_cpu_oracle_config
if config is None:
    raise SystemExit("model-derived config was not cached")
if len(config.world_constraints) != 1:
    raise SystemExit("model-derived world constraint count changed")
constraint = config.world_constraints[0]
if int(constraint.body) != 0:
    raise SystemExit("model-derived world_body changed")
if not np.allclose(constraint.rest_point, np.array([1.0, 0.0, 0.0])):
    raise SystemExit("model-derived world_rest_point changed")
if not np.allclose(constraint.world_point, np.array([1.25, 0.0, 0.0])):
    raise SystemExit("model-derived world_point changed")
if solver.last_step_result.topology != "dense":
    raise SystemExit(f"unexpected topology {solver.last_step_result.topology}")
if solver.last_step_result.constraint_residual_norm > 1.0e-10:
    raise SystemExit("model-derived world residual is too large")
if solver.last_step_result.dlambda.shape != (3,):
    raise SystemExit("model-derived world reaction vector shape changed")
q_next = np.concatenate(
    [
        state.mabd.q0.numpy(),
        state.mabd.q1.numpy(),
        state.mabd.q2.numpy(),
        state.mabd.t.numpy(),
    ],
    axis=1,
)[0]
pinned = mabd.point_jacobian(np.array([1.0, 0.0, 0.0], dtype=float)) @ q_next
if not np.allclose(pinned, np.array([1.25, 0.0, 0.0]), atol=1.0e-10):
    raise SystemExit("model-derived world anchor did not pin the point")
"""
    result = subprocess.run(
        [str(MABD_PYTHON), "-c", code],
        cwd=ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        fail("Phase 46 model-derived world constraint smoke failed: " + result.stderr.strip())


def validate_phase46_record() -> None:
    text = (
        ROOT / "docs/records/2026-05-18-phase46-model-world-constraints.md"
    ).read_text(encoding="utf-8")
    required_snippets = (
        "## Status\n\npassed_for_solver_model_world_constraint_config_slice",
        "## Repository",
        "phase46-model-world-constraints",
        "aa9d8c6ca586d7d4faa15fda19be17a138cb8307",
        "a7d95d4ec069afd333de2582f9b198a62189ad73",
        "e53e842877b3ddd7bcaca8d56d584074601d40f7",
        "da38183ca7090fc2ceb8a6f635a7aaf4c6bd02e4",
        "Evidence record commit",
        "76ba6acba4b208b66e4088a08434a354ed3fd186",
        "Review hardening commit",
        "47b3d63f63103ae1a81747fe7635975814b3f626",
        "## Vendored Newton",
        "https://github.com/newton-physics/newton.git",
        "96713fa965463b69c229a4d30582c733ff3526bb",
        "Local patch status",
        "locally patched",
        "## Environment",
        "/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python",
        "validator rechecks editable roots and core package parity",
        "## Implementation Evidence",
        "`mabd:world_constraint`",
        "`mabd:world_body`",
        "`mabd:world_rest_point`",
        "`mabd:world_point`",
        "`MABDCPUOracleWorldConstraint`",
        "`dlambda`",
        "manual `configure_cpu_oracle(...)`",
        "## RED Evidence",
        "Custom attribute 'mabd:world_body' is not defined",
        "FAILED (errors=3)",
        "## GREEN Evidence",
        "Ran 37 tests",
        "OK",
        "## Verification Commands",
        "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .",
        "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests",
        "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py",
        "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/env/readiness_check.py",
        'PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"',
        "git diff --check",
        "## Claim Impact",
        "No `experiment.*` claim is passed.",
        "not a full paper reproduction",
        "Newton `Contacts`",
        "Newton `Control` input",
        "paper timing",
        "comparative baselines",
        "rendered output",
        "raw simulation logs",
    )
    for snippet in required_snippets:
        if snippet not in text:
            fail(f"Phase 46 record missing required evidence field: {snippet}")
    for placeholder in (
        "TO_BE_BACKFILLED_PHASE46",
        "phase46-working-tree",
        "<implementation-commit>",
    ):
        if placeholder in text:
            fail("Phase 46 record contains stale placeholder")

    lower_text = text.lower()
    for snippet in (
        "full paper reproduction complete",
        "experiment.* claim is passed",
        "paper experiment passed",
        "contacts are implemented",
        "control input is implemented",
        "gpu solver passed",
        "warp solver passed",
        "runtime performance reproduced",
    ):
        if snippet in lower_text:
            fail(f"Phase 46 record overclaims unsupported evidence: {snippet}")

    boundary_text = (ROOT / "docs/reference/claim-boundaries.md").read_text(encoding="utf-8")
    normalized_boundary_text = " ".join(boundary_text.split())
    for snippet in (
        "This repository contains Phase 46 SolverMABD model-derived CPU world-constraint",
        "Phase 46 verifies model-derived `mabd:world_constraint` rows",
        "`MABDCPUOracleWorldConstraint`",
        "`mabd:world_body`",
        "`mabd:world_rest_point`",
        "`mabd:world_point`",
        "body-index validation",
        "reaction-vector availability through `dlambda`",
        "manual `configure_cpu_oracle(...)` precedence",
        "Phase 46 does not verify Newton `Contacts`",
        "Newton `Control` input",
        "GPU/Warp kernels",
        "paper timing",
        "comparative baselines",
        "rendered output",
        "raw simulation logs",
        "a full paper reproduction",
        "any passed `experiment.*` claim",
        "Phase 46 model-derived SolverMABD world constraints",
    ):
        if snippet not in normalized_boundary_text:
            fail(f"Phase 46 claim boundary missing: {snippet}")

    spec_text = (
        ROOT / "docs/superpowers/specs/2026-05-18-phase46-model-world-constraints-design.md"
    ).read_text(encoding="utf-8")
    plan_text = (
        ROOT / "docs/superpowers/plans/2026-05-18-mabd-phase46-model-world-constraints.md"
    ).read_text(encoding="utf-8")
    for snippet in (
        "Phase 46 Solver Model World Constraint Config Design",
        "`mabd:world_constraint`",
        "`mabd:world_body`",
        "`mabd:world_rest_point`",
        "`mabd:world_point`",
        "dense CPU world-anchor constraints only",
        "This is still not a paper experiment pass",
        "Phase 46 does not implement Newton `Contacts`",
    ):
        if snippet not in spec_text:
            fail(f"Phase 46 spec missing required boundary text: {snippet}")
    for snippet in (
        "Phase 46 Model World Constraints Implementation Plan",
        "Let `SolverMABD.step()` build CPU oracle world-anchor constraints",
        "`MABDCPUOracleWorldConstraint`",
        "manual `configure_cpu_oracle(...)` remains authoritative",
        "registered custom attribute",
        "claim impact saying no `experiment.*` claim is passed",
    ):
        if snippet not in plan_text:
            fail(f"Phase 46 plan missing required boundary text: {snippet}")
    for stale in (
        "Phase 45 Model Constraint Config Implementation Plan",
        "passed_for_solver_model_constraint_config_slice",
        "model-derived `mabd:constraint` rows are verified",
        "Phase 46 does not verify model-derived world constraints",
    ):
        if stale in spec_text or stale in plan_text:
            fail(f"Phase 46 spec/plan contains stale copied language: {stale}")

    validate_phase44_environment_clone()
    validate_phase46_model_world_constraint_smoke()


def validate_phase47_model_gravity_smoke() -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = f"{ROOT / 'src'}:{ROOT / 'vendor/newton'}"
    code = r"""
import numpy as np
import warp as wp

import newton
from newton.solvers import SolverMABD, mabd


def add_body_row(builder):
    body_id = builder.add_body()
    builder.add_custom_values(
        **{
            "mabd:body_index": body_id,
            "mabd:young_modulus": 1.0,
            "mabd:poisson_ratio": 0.25,
            "mabd:density": 1.0,
            "mabd:polar_mode": 0,
            "mabd:rest_point0": wp.vec3(0.0, 0.0, 0.0),
            "mabd:rest_point1": wp.vec3(1.0, 0.0, 0.0),
            "mabd:rest_point2": wp.vec3(0.0, 1.0, 0.0),
            "mabd:rest_point3": wp.vec3(0.0, 0.0, 1.0),
            "mabd:point_mass0": -1.0,
            "mabd:point_mass1": -1.0,
            "mabd:point_mass2": -1.0,
            "mabd:point_mass3": -1.0,
            "mabd:volume": -1.0,
        }
    )


def assign_state(state, q, qd):
    q_arr = np.asarray(q, dtype=float)
    qd_arr = np.asarray(qd, dtype=float)
    state.mabd.q0.assign(q_arr[:, 0:3].astype(np.float32))
    state.mabd.q1.assign(q_arr[:, 3:6].astype(np.float32))
    state.mabd.q2.assign(q_arr[:, 6:9].astype(np.float32))
    state.mabd.t.assign(q_arr[:, 9:12].astype(np.float32))
    state.mabd.qd0.assign(qd_arr[:, 0:3].astype(np.float32))
    state.mabd.qd1.assign(qd_arr[:, 3:6].astype(np.float32))
    state.mabd.qd2.assign(qd_arr[:, 6:9].astype(np.float32))
    state.mabd.td.assign(qd_arr[:, 9:12].astype(np.float32))


def read_state(state):
    q = np.concatenate(
        [
            state.mabd.q0.numpy(),
            state.mabd.q1.numpy(),
            state.mabd.q2.numpy(),
            state.mabd.t.numpy(),
        ],
        axis=1,
    )
    qd = np.concatenate(
        [
            state.mabd.qd0.numpy(),
            state.mabd.qd1.numpy(),
            state.mabd.qd2.numpy(),
            state.mabd.td.numpy(),
        ],
        axis=1,
    )
    return q, qd


rest_points = np.array(
    [
        [0.0, 0.0, 0.0],
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0],
    ],
    dtype=float,
)
gravity = np.array([0.0, -9.81, 1.25], dtype=float)
q_initial = mabd.pack_q(np.eye(3), np.array([0.1, 0.2, -0.3], dtype=float))
qd_initial = np.zeros(12, dtype=float)
dt = 0.02

builder = newton.ModelBuilder()
SolverMABD.register_custom_attributes(builder)
add_body_row(builder)
builder.add_custom_values(
    **{
        "mabd:gravity_enabled": 1,
        "mabd:gravity_vector": wp.vec3(*gravity),
    }
)
model = builder.finalize()
state = model.state()
assign_state(state, [q_initial], [qd_initial])
solver = SolverMABD(model)
solver.step(state, state, None, None, dt)
config = solver.model_cpu_oracle_config
if config is None:
    raise SystemExit("model-derived config was not cached")
if config.gravity is None or not np.allclose(config.gravity, gravity):
    raise SystemExit("model-derived gravity vector changed")

volume = mabd.tetra_volume(rest_points)
masses = np.full(4, volume / 4.0, dtype=float)
expected = mabd.solve_cpu_oracle_step(
    q=[q_initial],
    qd=[qd_initial],
    dt=dt,
    config=mabd.MABDCPUOracleConfig(
        bodies=[
            mabd.MABDCPUOracleBody(
                precompute=mabd.SingleBodyABDPrecompute.from_linear_elastic_points(
                    rest_points,
                    masses,
                    young_modulus=1.0,
                    poisson_ratio=0.25,
                    volume=volume,
                ),
                rest_q=mabd.pack_q(np.eye(3), np.zeros(3)),
                rotation_mode="none",
            )
        ],
        gravity=gravity,
    ),
)
q_next, qd_next = read_state(state)
if not np.allclose(q_next[0], expected.q[0], atol=1.0e-7):
    raise SystemExit("model-derived gravity q did not match explicit CPU oracle gravity")
if not np.allclose(qd_next[0], expected.qd[0], atol=1.0e-7):
    raise SystemExit("model-derived gravity qd did not match explicit CPU oracle gravity")
"""
    result = subprocess.run(
        [str(MABD_PYTHON), "-c", code],
        cwd=ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        fail("Phase 47 model-derived gravity smoke failed: " + result.stderr.strip())


def validate_phase47_record() -> None:
    text = (
        ROOT / "docs/records/2026-05-18-phase47-model-gravity-config.md"
    ).read_text(encoding="utf-8")
    required_snippets = (
        "## Status\n\npassed_for_solver_model_gravity_config_slice",
        "## Repository",
        "phase47-model-gravity-config",
        "2d03449f079fb853dae64c672686edffae9b078b",
        "b6abb83f5ec70f7d8b02e1e450ef05f871c4e659",
        "804d8ea37e3adb2140bde10823e65dd4aa96c75d",
        "f393c43831e7c5dd0a665a7b9e8f4d4ff49f81b4",
        "Evidence record commit",
        "c265d0098c75a46f2d2bf471ecb3acf7350b9987",
        "Evidence pin commit",
        "f0a9b57a0f5aa44f52397042405c9e7090730fc3",
        "Review hardening commit",
        "94559a01f220a2546273870c994a8eff333c2bba",
        "Mixed-row coverage commit",
        "32e2270761115eae53c1b901c03bb42e9f82f5a3",
        "## Vendored Newton",
        "https://github.com/newton-physics/newton.git",
        "96713fa965463b69c229a4d30582c733ff3526bb",
        "Local patch status",
        "locally patched",
        "## Environment",
        "/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python",
        "does not mutate the shared Newton environment",
        "## Implementation Evidence",
        "`mabd:gravity`",
        "`mabd:gravity_enabled`",
        "`mabd:gravity_vector`",
        "`MABDCPUOracleConfig.gravity`",
        "Multiple enabled rows raise",
        "One enabled row plus one disabled row remains accepted",
        "manual `configure_cpu_oracle(...)` precedence",
        "explicit no-gravity manual oracle",
        "## RED Evidence",
        "Custom attribute 'mabd:gravity_enabled' is not defined",
        "FAILED (errors=4)",
        "## GREEN Evidence",
        "Ran 41 tests",
        "OK",
        "## Review Hardening Evidence",
        "manual-precedence coverage could false-positive",
        "Ran 42 tests",
        "## Verification Commands",
        "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .",
        "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests",
        "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py",
        "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/env/readiness_check.py",
        'PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"',
        "git diff --check",
        "## Claim Impact",
        "No `experiment.*` claim is passed",
        "heavy-top reproduction",
        "physical-pendulum scene",
        "Newton `Contacts`",
        "runtime Newton `Control`",
        "GPU/Warp solver",
        "paper timing",
        "comparative baselines",
        "rendered output",
        "raw simulation logs",
        "full paper reproduction",
    )
    for snippet in required_snippets:
        if snippet not in text:
            fail(f"Phase 47 record missing required evidence field: {snippet}")
    for placeholder in (
        "TO_BE_BACKFILLED_PHASE47",
        "phase47-working-tree",
        "<implementation-commit>",
    ):
        if placeholder in text:
            fail("Phase 47 record contains stale placeholder")

    lower_text = text.lower()
    for snippet in (
        "full paper reproduction complete",
        "experiment.* claim is passed",
        "paper experiment passed",
        "contacts are implemented",
        "control input is implemented",
        "gpu solver passed",
        "warp solver passed",
        "runtime performance reproduced",
    ):
        if snippet in lower_text:
            fail(f"Phase 47 record overclaims unsupported evidence: {snippet}")

    boundary_text = (ROOT / "docs/reference/claim-boundaries.md").read_text(encoding="utf-8")
    normalized_boundary_text = " ".join(boundary_text.split())
    for snippet in (
        "This repository contains Phase 47 SolverMABD model-derived CPU gravity-config",
        "Phase 47 verifies model-derived `mabd:gravity` rows",
        "`MABDCPUOracleConfig.gravity`",
        "`mabd:gravity_enabled`",
        "`mabd:gravity_vector`",
        "disabled-row filtering",
        "multiple-enabled-row validation",
        "manual `configure_cpu_oracle(...)` precedence",
        "Phase 47 does not verify heavy-top reproduction",
        "physical-pendulum scene reproduction",
        "Newton `Contacts`",
        "Newton `Control` input",
        "GPU/Warp kernels",
        "paper timing",
        "comparative baselines",
        "rendered output",
        "raw simulation logs",
        "a full paper reproduction",
        "any passed `experiment.*` claim",
        "Phase 47 model-derived SolverMABD gravity config",
    ):
        if snippet not in normalized_boundary_text:
            fail(f"Phase 47 claim boundary missing: {snippet}")

    spec_text = (
        ROOT / "docs/superpowers/specs/2026-05-18-phase47-model-gravity-config-design.md"
    ).read_text(encoding="utf-8")
    plan_text = (
        ROOT / "docs/superpowers/plans/2026-05-18-mabd-phase47-model-gravity-config.md"
    ).read_text(encoding="utf-8")
    for snippet in (
        "Phase 47 Solver Model Gravity Config Design",
        "`mabd:gravity`",
        "`mabd:gravity_enabled`",
        "`mabd:gravity_vector`",
        "more than one enabled row is rejected",
        "This is still not a paper experiment pass",
        "Phase 47 does not implement heavy-top reproduction",
    ):
        if snippet not in spec_text:
            fail(f"Phase 47 spec missing required boundary text: {snippet}")
    for snippet in (
        "Phase 47 Model Gravity Config Implementation Plan",
        "Let `SolverMABD.step()` build `MABDCPUOracleConfig.gravity`",
        "`MABDCPUOracleConfig.gravity`",
        "manual `configure_cpu_oracle(...)` remains authoritative",
        "registered custom attribute",
        "No `experiment.*` claim is passed",
    ):
        if snippet not in plan_text:
            fail(f"Phase 47 plan missing required boundary text: {snippet}")
    for stale in (
        "Phase 46 Model World Constraints Implementation Plan",
        "passed_for_solver_model_world_constraint_config_slice",
        "model-derived `mabd:world_constraint` rows are verified",
        "Phase 47 does not verify model-derived gravity",
    ):
        if stale in spec_text or stale in plan_text:
            fail(f"Phase 47 spec/plan contains stale copied language: {stale}")

    validate_phase44_environment_clone()
    validate_phase47_model_gravity_smoke()


def validate_phase48_record() -> None:
    text = (
        ROOT / "docs/records/2026-05-18-phase48-physical-pendulum-model-lane.md"
    ).read_text(encoding="utf-8")
    required_snippets = (
        "## Status\n\npassed_for_physical_pendulum_model_derived_lane_slice",
        "## Repository",
        "phase48-physical-pendulum-model-lane",
        "7735a3357a2660a4b014aa6e37d3bc38f9039916",
        "42f8674",
        "f642f69",
        "d102194",
        "Evidence record commit",
        "0200a67f22dc38b4af20db1215202cd838379766",
        "Review hardening commit",
        "1280ac4a3e15a6b5d9c8ffade2cb16980ab2d54c",
        "## Vendored Newton",
        "https://github.com/newton-physics/newton.git",
        VENDORED_NEWTON_COMMIT,
        "Local patch status: locally patched",
        "mabd:zero_stiffness_diagnostic",
        "zero stiffness requires explicit diagnostic opt-in",
        "young_modulus == 0.0",
        "Default `young_modulus == 0.0` without the diagnostic opt-in still raises",
        "## Environment",
        "/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python",
        "does not mutate the shared Newton/reference environment",
        "## Implementation Evidence",
        "manual_cpu_oracle_config",
        "newton_model_derived",
        "`mabd:body`",
        "`mabd:world_constraint`",
        "`mabd:gravity`",
        "SolverMABD.step(state, state, None, None, dt)",
        "solver_model_config_source = newton_model_derived",
        "full_experiment_claim_passed = false",
        "## RED Evidence",
        "roll_out_physical_pendulum_mabd_model_derived",
        "KeyError: 'solver_model_config_source'",
        "FAILED (errors=2)",
        "ValueError: young_modulus must be positive",
        "FAILED (errors=1)",
        "AssertionError: ValueError not raised",
        "FAILED (failures=1)",
        "## GREEN Evidence",
        "Ran 38 tests",
        "test_solver_step_model_body_rejects_zero_young_modulus_without_diagnostic_opt_in",
        "test_solver_step_model_body_allows_zero_young_modulus_with_diagnostic_opt_in",
        "the formal physical-pendulum lane calls `SolverMABD.step()`",
        "OK",
        "## Report Artifacts",
        "single_body_physical_pendulum_mabd_newton.json",
        "single_body_physical_pendulum_comparison.json",
        "source_commit = 1280ac4",
        "blocking_reasons = [pendulum_geometry_unknown]",
        "## Verification Commands",
        "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .",
        "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests",
        "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py",
        "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/env/readiness_check.py",
        'PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"',
        "npm --prefix site run validate",
        "git diff --check",
        "## Claim Impact",
        "No `experiment.*` claim is passed",
        "Paper-faithful physical-pendulum geometry remains missing",
        "Newton `Contacts` remain unimplemented",
        "Runtime Newton `Control` remains unverified",
        "Zero stiffness remains an explicit diagnostic opt-in",
        "GPU/Warp kernels remain unverified",
        "full paper reproduction remain incomplete",
    )
    for snippet in required_snippets:
        if snippet not in text:
            fail(f"Phase 48 record missing required evidence field: {snippet}")
    for placeholder in (
        "TO_BE_BACKFILLED_PHASE48",
        "phase48-working-tree",
        "<implementation-commit>",
        "PHASE48_EVIDENCE_RECORD_COMMIT_TO_PIN",
    ):
        if placeholder in text:
            fail("Phase 48 record contains stale placeholder")

    lower_text = text.lower()
    for snippet in (
        "passed physical-pendulum experiment",
        "physical-pendulum experiment passed",
        "paper-faithful physical-pendulum geometry is verified",
        "contacts are implemented",
        "control input is implemented",
        "gpu solver passed",
        "warp solver passed",
        "full paper reproduction complete",
    ):
        if snippet in lower_text:
            fail(f"Phase 48 record overclaims unsupported evidence: {snippet}")

    boundary_text = (ROOT / "docs/reference/claim-boundaries.md").read_text(encoding="utf-8")
    normalized_boundary_text = " ".join(boundary_text.split())
    for snippet in (
        "This repository contains Phase 48 physical-pendulum `mabd_newton`",
        "Phase 48 verifies the formal physical-pendulum `mabd_newton` report lane uses",
        "Newton model-derived `SolverMABD.step()`",
        "`mabd:body`",
        "`mabd:world_constraint`",
        "`mabd:gravity`",
        "solver_model_config_source = newton_model_derived",
        "full_experiment_claim_passed = false",
        "Phase 48 does not verify paper-faithful physical-pendulum geometry",
        "physical-pendulum experiment pass",
        "Newton `Contacts`",
        "runtime Newton `Control`",
        "GPU/Warp kernels",
        "rendered output",
        "paper timing",
        "comparative pass gates",
        "raw simulation logs",
        "a full paper reproduction",
        "any passed `experiment.*` claim",
        "Phase 48 physical-pendulum model-derived `mabd_newton` lane",
    ):
        if snippet not in normalized_boundary_text:
            fail(f"Phase 48 claim boundary missing: {snippet}")

    spec_text = (
        ROOT / "docs/superpowers/specs/2026-05-18-phase48-physical-pendulum-model-lane-design.md"
    ).read_text(encoding="utf-8")
    plan_text = (
        ROOT / "docs/superpowers/plans/2026-05-18-mabd-phase48-physical-pendulum-model-lane.md"
    ).read_text(encoding="utf-8")
    for snippet in (
        "Phase 48 Physical Pendulum Model-Derived MABD Lane Design",
        "`mabd_newton` lane",
        "`SolverMABD.step()`",
        "`mabd:body`",
        "`mabd:world_constraint`",
        "`mabd:gravity`",
        "solver_model_config_source",
        "newton_model_derived",
        "This is still not a passed physical-pendulum paper experiment",
    ):
        if snippet not in spec_text:
            fail(f"Phase 48 spec missing required boundary text: {snippet}")
    for snippet in (
        "Phase 48 Physical Pendulum Model-Derived Lane Implementation Plan",
        "Make the physical-pendulum `mabd_newton` report lane step through Newton model-derived `SolverMABD.step()`",
        "roll_out_physical_pendulum_mabd_model_derived",
        "solver_model_config_source",
        "newton_model_derived",
        "No `experiment.*` claim is passed",
    ):
        if snippet not in plan_text:
            fail(f"Phase 48 plan missing required boundary text: {snippet}")
    for stale in (
        "Phase 47 Model Gravity Config Implementation Plan",
        "passed_for_solver_model_gravity_config_slice",
        "Phase 48 does not verify model-derived physical pendulum",
    ):
        if stale in spec_text or stale in plan_text:
            fail(f"Phase 48 spec/plan contains stale copied language: {stale}")

    try:
        config = load_physical_pendulum_config(
            ROOT / "configs/experiments/single_body_physical_pendulum.yaml"
        )
        matrix = load_experiment_matrix(ROOT / "configs/experiments/paper_experiment_matrix.yaml")
        validate_physical_pendulum_config_against_matrix(config, matrix)
    except (ExperimentRunConfigError, ExperimentMatrixError) as exc:
        fail(f"Phase 48 physical-pendulum config validation failed: {exc}")

    mabd = load_claim_report(ROOT / config.mabd_newton.output_report)
    comparison = load_claim_report(ROOT / config.comparison.output_report)
    for report_name, report in (("MABD Newton", mabd), ("comparison", comparison)):
        if report.source_commit in PLACEHOLDER_SOURCE_COMMITS:
            fail(f"Phase 48 {report_name} report source_commit must name the implementation commit")
        if report.vendored_newton_commit != VENDORED_NEWTON_COMMIT:
            fail(f"Phase 48 {report_name} report vendored Newton commit changed")
        if report.claim_id != config.claim_id:
            fail(f"Phase 48 {report_name} report claim_id does not match config")
        if report.scene_id != config.scene_id:
            fail(f"Phase 48 {report_name} report scene_id does not match config")
        if report.status.value != "incomplete":
            fail(f"Phase 48 {report_name} report must remain incomplete")

    if mabd.source_commit != "1280ac4":
        fail("Phase 48 MABD Newton report source_commit must pin review hardening commit 1280ac4")
    if comparison.source_commit != "1280ac4":
        fail("Phase 48 comparison report source_commit must pin review hardening commit 1280ac4")
    if mabd.baseline_lane != "mabd_newton":
        fail("Phase 48 MABD Newton report lane changed")
    if mabd.solver_mode != "mabd_cpu_oracle_physical_pendulum_newton_lane":
        fail("Phase 48 MABD Newton report solver mode changed")
    if mabd.backend != "cpu_numpy_newton_only":
        fail("Phase 48 MABD Newton report backend changed")
    mabd_observed = mabd.observed
    if mabd_observed.get("lane_status") != "incomplete_diagnostic_generated":
        fail("Phase 48 MABD Newton lane_status changed")
    if mabd_observed.get("solver_model_config_source") != "newton_model_derived":
        fail("Phase 48 MABD Newton report must record model-derived solver source")
    if mabd.expected.get("solver_model_config_source") != "newton_model_derived":
        fail("Phase 48 MABD Newton expected record must record model-derived solver source")
    expected_frequencies = ["mabd:body", "mabd:world_constraint", "mabd:gravity"]
    if mabd_observed.get("newton_model_derived_custom_frequencies") != expected_frequencies:
        fail("Phase 48 MABD Newton observed custom frequencies changed")
    if mabd.expected.get("newton_model_derived_custom_frequencies") != expected_frequencies:
        fail("Phase 48 MABD Newton expected custom frequencies changed")
    if mabd_observed.get("full_experiment_claim_passed") is not False:
        fail("Phase 48 MABD Newton report must not pass full experiment claim")
    if mabd_observed.get("threshold_violations") != []:
        fail("Phase 48 MABD Newton report threshold violations changed")
    if mabd_observed.get("blocking_reasons") != ["pendulum_geometry_unknown"]:
        fail("Phase 48 MABD Newton blockers changed")

    if comparison.baseline_lane != "physical_pendulum_comparison_protocol":
        fail("Phase 48 comparison report lane changed")
    if comparison.solver_mode != "physical_pendulum_multilane_comparison_development":
        fail("Phase 48 comparison report solver mode changed")
    observed = comparison.observed
    if observed.get("full_experiment_claim_passed") is not False:
        fail("Phase 48 comparison report must not pass full experiment claim")
    if observed.get("missing_required_lanes") != []:
        fail("Phase 48 comparison missing_required_lanes changed")
    if observed.get("missing_paper_metrics") != ["joint_force_error:paper_geometry_unknown"]:
        fail("Phase 48 comparison missing_paper_metrics changed")
    blockers = observed.get("blocking_reasons")
    if not isinstance(blockers, list):
        fail("Phase 48 comparison blockers must be a list")
    for blocker in (
        "pendulum_geometry_unknown",
        "physical_pendulum_comparison_pass_gate_not_enabled",
    ):
        if blocker not in blockers:
            fail(f"Phase 48 comparison blocker missing: {blocker}")
    provenance = observed.get("input_report_provenance")
    if not isinstance(provenance, dict):
        fail("Phase 48 comparison input_report_provenance must be a mapping")
    mabd_provenance = provenance.get("mabd_newton")
    if not isinstance(mabd_provenance, dict):
        fail("Phase 48 comparison missing mabd_newton input provenance")
    if mabd_provenance.get("path") != config.mabd_newton.output_report:
        fail("Phase 48 comparison MABD input path changed")
    if mabd_provenance.get("source_commit") != mabd.source_commit:
        fail("Phase 48 comparison must consume the regenerated MABD Newton report")
    if mabd_provenance.get("sha256") != sha256_file(ROOT / config.mabd_newton.output_report):
        fail("Phase 48 comparison MABD input sha256 mismatch")

    claims = read_yaml(ROOT / "docs/reference/paper-claims.yaml").get("claims")
    if not isinstance(claims, list):
        fail("paper-claims.yaml missing claims list")
    for claim in claims:
        if not isinstance(claim, dict):
            continue
        claim_id = str(claim.get("claim_id", ""))
        if claim_id == "experiment.single_body.physical_pendulum":
            if claim.get("reproduction_status") != "intended":
                fail("Phase 48 must keep physical-pendulum experiment status intended")
        if claim_id.startswith("experiment.") and claim.get("reproduction_status") == "passed":
            fail("Phase 48 must not pass experiment.* claims")


def validate_phase49_record() -> None:
    text = (
        ROOT / "docs/records/2026-05-18-phase49-heavy-top-rk4-reference.md"
    ).read_text(encoding="utf-8")
    required_snippets = (
        "## Status\n\npassed_for_heavy_top_reference_diagnostic_lane",
        "## Repository",
        "phase49-heavy-top-reference",
        "6d90ccf7d3faf9e79b84b01da815dd8c861df341",
        "ef53522077c53b4842f5198938dd5c24190e7863",
        VENDORED_NEWTON_COMMIT,
        "## Paper Source",
        "experiment.tex:65-75",
        "images/spinning_top/spinning_top.pdf",
        "c8f5e206415b9feb3578ee32aa3b7284e2695bdd84eeb0200f3b4aa01cf3422d",
        "## Report Artifact",
        "reports/experiment_matrix/single_body_heavy_top_rk4_reference.json",
        "heavy_top_rk4_reference_diagnostic",
        "rbd_rk4_reference",
        "diagnostic_generated",
        "exact_heavy_top_inertia_unknown",
        "exact_heavy_top_geometry_unknown",
        "raw_heavy_top_reference_curve_data_missing",
        "mabd_newton_report_incomplete",
        "heavy_top_comparison_report_incomplete",
        "heavy_top_timing_evidence_missing",
        "## Claim Impact",
        "No `experiment.*` claim is passed.",
        "`experiment.single_body.heavy_top` remains intended",
        "does not implement paper-faithful heavy-top inertia",
        "## Verification Commands",
        "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_heavy_top_reference tests.test_experiment_run_configs tests.test_experiment_runner tests.test_phase0_bootstrap",
        "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py",
        "git diff --check",
    )
    for snippet in required_snippets:
        if snippet not in text:
            fail(f"Phase 49 record missing required evidence field: {snippet}")
    for placeholder in (
        "TO_BE_BACKFILLED_PHASE49",
        "phase49-working-tree",
        "<implementation-commit>",
    ):
        if placeholder in text:
            fail("Phase 49 record contains stale placeholder")

    lower_text = text.lower()
    for snippet in (
        "passed heavy-top experiment",
        "heavy-top experiment passed",
        "paper-faithful heavy-top inertia is verified",
        "m-abd heavy-top dynamics passed",
        "raw curve agreement passed",
        "runtime performance reproduced",
        "full reproduction complete",
    ):
        if snippet in lower_text:
            fail(f"Phase 49 record overclaims unsupported evidence: {snippet}")

    boundary_text = (ROOT / "docs/reference/claim-boundaries.md").read_text(encoding="utf-8")
    normalized_boundary_text = " ".join(boundary_text.split())
    for snippet in (
        "This repository contains Phase 49 heavy-top RK4 reference diagnostic lane",
        "Phase 49 verifies a source-backed `rbd_rk4_reference` diagnostic lane",
        "`exact_heavy_top_geometry_unknown`",
        "`raw_heavy_top_reference_curve_data_missing`",
        "`mabd_newton_report_incomplete`",
        "`heavy_top_comparison_report_incomplete`",
        "`heavy_top_timing_evidence_missing`",
        "Phase 49 does not verify a passed heavy-top experiment",
        "paper-faithful heavy-top inertia",
        "M-ABD heavy-top dynamics",
        "Phase 49 heavy-top RK4 reference",
    ):
        if snippet not in normalized_boundary_text:
            fail(f"Phase 49 claim boundary missing: {snippet}")

    try:
        config = load_heavy_top_config(ROOT / "configs/experiments/single_body_heavy_top.yaml")
        matrix = load_experiment_matrix(ROOT / "configs/experiments/paper_experiment_matrix.yaml")
        validate_heavy_top_config_against_matrix(config, matrix)
    except (ExperimentRunConfigError, ExperimentMatrixError) as exc:
        fail(f"Phase 49 heavy-top config validation failed: {exc}")

    report_path = "reports/experiment_matrix/single_body_heavy_top_rk4_reference.json"
    report = load_claim_report(ROOT / report_path)
    if report.source_commit in PLACEHOLDER_SOURCE_COMMITS:
        fail("Phase 49 report source_commit must not be a placeholder")
    if report.source_commit not in text:
        fail("Phase 49 record must list the report source_commit")
    if report.vendored_newton_commit != VENDORED_NEWTON_COMMIT:
        fail("Phase 49 report vendored Newton commit changed")
    if report.claim_id != config.claim_id:
        fail("Phase 49 report claim_id does not match config")
    if report.scene_id != config.scene_id:
        fail("Phase 49 report scene_id does not match config")
    if report.asset_hashes.get("heavy_top_procedural") != "not_applicable_procedural":
        fail("Phase 49 heavy-top asset hash must remain procedural")
    if report.status.value != "incomplete":
        fail("Phase 49 heavy-top report must remain incomplete")
    actual_hash = sha256_file(ROOT / report_path)
    record_hash = _record_sha256_for_artifact(text, report_path)
    if record_hash != actual_hash:
        fail("Phase 49 heavy-top report sha256 mismatch")

    if report.baseline_lane != "rbd_rk4_reference":
        fail("Phase 49 heavy-top report lane changed")
    if report.solver_mode != "heavy_top_rk4_reference_diagnostic":
        fail("Phase 49 heavy-top report solver mode changed")
    if report.backend != "cpu_numpy":
        fail("Phase 49 heavy-top report backend changed")
    observed = report.observed
    trajectory = roll_out_heavy_top_rk4_reference(config)
    if observed.get("lane_status") != "diagnostic_generated":
        fail("Phase 49 heavy-top diagnostic status changed")
    if "lane_gate_status" in observed:
        fail("Phase 49 heavy-top report must not expose a passed lane gate")
    if observed.get("full_experiment_claim_passed") is not False:
        fail("Phase 49 heavy-top report must not pass full experiment claim")
    if observed.get("reference_not_paper_inertia") is not True:
        fail("Phase 49 heavy-top report must mark reference_not_paper_inertia")
    if observed.get("reference_not_paper_geometry") is not True:
        fail("Phase 49 heavy-top report must mark reference_not_paper_geometry")
    blockers = observed.get("blocking_reasons")
    if not isinstance(blockers, list):
        fail("Phase 49 heavy-top blockers must be a list")
    for blocker in (
        "exact_heavy_top_inertia_unknown",
        "exact_heavy_top_geometry_unknown",
        "raw_heavy_top_reference_curve_data_missing",
        "mabd_newton_report_incomplete",
        "heavy_top_comparison_report_incomplete",
        "heavy_top_timing_evidence_missing",
    ):
        if blocker not in blockers:
            fail(f"Phase 49 heavy-top blocker missing: {blocker}")
    if observed.get("required_missing_lanes") != []:
        fail("Phase 49 heavy-top required_missing_lanes changed")
    if (
        _require_finite_scalar(observed.get("time_step_s"), "Phase 49 heavy-top time_step_s")
        != 1.0e-4
    ):
        fail("Phase 49 heavy-top RK4 step changed")
    if (
        _require_finite_scalar(observed.get("duration_s"), "Phase 49 heavy-top duration_s")
        != 10.0
    ):
        fail("Phase 49 heavy-top diagnostic duration changed")
    if abs(
        _require_finite_scalar(
            observed.get("relative_energy_drift"),
            "Phase 49 heavy-top relative_energy_drift",
        )
    ) > config.reference.thresholds["max_relative_energy_drift"]:
        fail("Phase 49 heavy-top relative energy drift exceeded threshold")
    nutation_range = _require_finite_scalar(
        observed.get("max_nutation_angle_deg"),
        "Phase 49 heavy-top max_nutation_angle_deg",
    ) - _require_finite_scalar(
        observed.get("min_nutation_angle_deg"),
        "Phase 49 heavy-top min_nutation_angle_deg",
    )
    if nutation_range < config.reference.thresholds["min_nutation_angle_range_deg"]:
        fail("Phase 49 heavy-top nutation range below threshold")
    if (
        _require_finite_scalar(
            observed.get("max_abs_precession_velocity_rad_s"),
            "Phase 49 heavy-top max_abs_precession_velocity_rad_s",
        )
        < config.reference.thresholds["min_abs_precession_velocity_rad_s"]
    ):
        fail("Phase 49 heavy-top precession velocity below threshold")
    for key, expected in (
        ("energy_initial", trajectory.energy_initial),
        ("energy_final", trajectory.energy_final),
        ("relative_energy_drift", trajectory.relative_energy_drift),
        ("min_nutation_angle_deg", trajectory.min_nutation_angle_deg),
        ("max_nutation_angle_deg", trajectory.max_nutation_angle_deg),
        ("max_abs_precession_velocity_rad_s", trajectory.max_abs_precession_velocity_rad_s),
    ):
        actual = _require_finite_scalar(observed.get(key), f"Phase 49 heavy-top {key}")
        if not np.isclose(actual, expected, rtol=0.0, atol=1.0e-14):
            fail(f"Phase 49 heavy-top {key} does not match recomputed RK4 rollout")
    if not np.allclose(
        observed.get("principal_inertia_kg_m2"),
        config.reference.principal_inertia_kg_m2.tolist(),
        rtol=0.0,
        atol=1.0e-15,
    ):
        fail("Phase 49 heavy-top inertia does not match config")
    if not np.allclose(
        observed.get("pivot_to_com_m"),
        config.reference.pivot_to_com_m.tolist(),
        rtol=0.0,
        atol=1.0e-15,
    ):
        fail("Phase 49 heavy-top pivot_to_com_m does not match config")
    gravity = _require_finite_vector3(observed.get("gravity_m_s2"), "Phase 49 heavy-top gravity")
    if gravity != [0.0, -9.81, 0.0]:
        fail("Phase 49 heavy-top gravity changed")
    samples = observed.get("precession_nutation_samples")
    if not isinstance(samples, list) or len(samples) != config.reference.sample_count:
        fail("Phase 49 heavy-top precession_nutation_samples changed")
    for index, sample in enumerate(samples):
        if not isinstance(sample, dict):
            fail("Phase 49 heavy-top sample must be a mapping")
        if sample.get("sample_index") != index:
            fail("Phase 49 heavy-top sample_index changed")
        expected_row = trajectory.samples[index]
        for key, expected in (
            ("time_s", expected_row[0]),
            ("nutation_angle_deg", expected_row[1]),
            ("precession_angle_rad", expected_row[2]),
            ("precession_velocity_rad_s", expected_row[3]),
        ):
            actual = _require_finite_scalar(sample.get(key), f"Phase 49 sample {index} {key}")
            if not np.isclose(actual, float(expected), rtol=0.0, atol=1.0e-14):
                fail(f"Phase 49 heavy-top sample {index} {key} changed")
    if observed.get("threshold_violations") != []:
        fail("Phase 49 heavy-top threshold_violations changed")
    if report.expected.get("source_lines") != list(config.source_lines):
        fail("Phase 49 heavy-top expected source_lines changed")
    if report.expected.get("figure_pdf_sha256") != config.reference.figure_pdf_sha256:
        fail("Phase 49 heavy-top expected figure hash changed")
    if report.expected.get("matrix_claim_report") != (
        "reports/experiment_matrix/single_body_heavy_top.json"
    ):
        fail("Phase 49 heavy-top matrix claim report binding changed")
    if report.expected.get("lane_report") != config.reference.output_report:
        fail("Phase 49 heavy-top lane report binding changed")

    claims = read_yaml(ROOT / "docs/reference/paper-claims.yaml").get("claims")
    if not isinstance(claims, list):
        fail("paper-claims.yaml missing claims list")
    found_heavy_top = False
    for claim in claims:
        if not isinstance(claim, dict):
            continue
        claim_id = str(claim.get("claim_id", ""))
        if claim_id == "experiment.single_body.heavy_top":
            found_heavy_top = True
            if claim.get("reproduction_status") != "intended":
                fail("Phase 49 must keep heavy-top experiment status intended")
            conflict_note = str(claim.get("conflict_note", ""))
            for blocker in (
                "exact_heavy_top_inertia_unknown",
                "exact_heavy_top_geometry_unknown",
                "raw_heavy_top_reference_curve_data_missing",
                "mabd_newton_report_incomplete",
                "heavy_top_comparison_report_incomplete",
            ):
                if blocker not in conflict_note:
                    fail(f"Phase 49 heavy-top conflict_note missing {blocker}")
            if "mabd_newton_report_missing" in conflict_note:
                fail("Phase 49 current heavy-top conflict_note must use mabd_newton_report_incomplete")
        if claim_id.startswith("experiment.") and claim.get("reproduction_status") == "passed":
            fail("Phase 49 must not pass experiment.* claims")
    if not found_heavy_top:
        fail("paper-claims.yaml missing heavy-top claim")

    matrix_data = read_yaml(ROOT / "configs/experiments/paper_experiment_matrix.yaml")
    experiments = matrix_data.get("experiments")
    if not isinstance(experiments, list):
        fail("Phase 49 experiment matrix missing experiments")
    matrix_entry = next(
        (
            item
            for item in experiments
            if isinstance(item, dict)
            and item.get("claim_id") == "experiment.single_body.heavy_top"
        ),
        None,
    )
    if matrix_entry is None:
        fail("Phase 49 matrix missing heavy-top experiment")
    if matrix_entry.get("reproduction_status") != "planned":
        fail("Phase 49 matrix must keep heavy-top planned")
    matrix_blockers = matrix_entry.get("blocking_reasons")
    if not isinstance(matrix_blockers, list):
        fail("Phase 49 matrix heavy-top blockers must be a list")
    for blocker in (
        "exact_heavy_top_inertia_unknown",
        "exact_heavy_top_geometry_unknown",
        "raw_heavy_top_reference_curve_data_missing",
        "mabd_newton_report_incomplete",
        "heavy_top_comparison_report_incomplete",
    ):
        if blocker not in matrix_blockers:
            fail(f"Phase 49 matrix blocker missing: {blocker}")
    if "mabd_newton_report_missing" in matrix_blockers:
        fail("Phase 49 current matrix must use mabd_newton_report_incomplete")


def validate_phase50_record() -> None:
    text = (
        ROOT / "docs/records/2026-05-18-phase50-heavy-top-mabd-newton-lane.md"
    ).read_text(encoding="utf-8")
    required_snippets = (
        "## Status\n\npassed_for_heavy_top_mabd_newton_diagnostic_lane",
        "phase50-heavy-top-mabd-lane",
        "45bef31db663b2d13d9385ef64a8445cbac9b613",
        "ef53522077c53b4842f5198938dd5c24190e7863",
        VENDORED_NEWTON_COMMIT,
        "reports/experiment_matrix/single_body_heavy_top_mabd_newton.json",
        "9342374ffde72071308b6aa5c117815392f71f4db1e07d9817ac61e4847bf324",
        "mabd_cpu_oracle_heavy_top_newton_lane",
        "mabd_newton",
        "cpu_numpy_newton_only",
        "newton_model_derived",
        "mabd:body",
        "mabd:world_constraint",
        "mabd:gravity",
        "incomplete_diagnostic_generated",
        "mabd_newton_report_incomplete",
        "exact_heavy_top_inertia_unknown",
        "exact_heavy_top_geometry_unknown",
        "raw_heavy_top_reference_curve_data_missing",
        "heavy_top_comparison_report_incomplete",
        "heavy_top_timing_evidence_missing",
        "diagnostic relative energy drift",
        "No `experiment.*` claim is passed.",
        "`experiment.single_body.heavy_top` remains intended",
        "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_heavy_top_mabd tests.test_experiment_run_configs tests.test_experiment_runner tests.test_phase0_bootstrap",
        "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py",
        "git diff --check",
    )
    for snippet in required_snippets:
        if snippet not in text:
            fail(f"Phase 50 record missing required evidence field: {snippet}")
    for placeholder in (
        "TO_BE_BACKFILLED_PHASE50",
        "phase50-working-tree",
        "<implementation-commit>",
    ):
        if placeholder in text:
            fail("Phase 50 record contains stale placeholder")

    lower_text = text.lower()
    for snippet in (
        "passed heavy-top experiment",
        "heavy-top experiment passed",
        "paper-faithful heavy-top inertia is verified",
        "raw curve agreement passed",
        "abd-vs-rbd comparison passed",
        "runtime performance reproduced",
        "full reproduction complete",
    ):
        if snippet in lower_text:
            fail(f"Phase 50 record overclaims unsupported evidence: {snippet}")

    boundary_text = (ROOT / "docs/reference/claim-boundaries.md").read_text(encoding="utf-8")
    normalized_boundary_text = " ".join(boundary_text.split())
    for snippet in (
        "This repository contains Phase 50 heavy-top `mabd_newton` diagnostic lane",
        "Phase 50 verifies the formal heavy-top `mabd_newton` diagnostic lane",
        "model-derived `SolverMABD.step()`",
        "`mabd:body`",
        "`mabd:world_constraint`",
        "`mabd:gravity`",
        "`mabd_newton_report_incomplete`",
        "Phase 50 does not verify a passed heavy-top experiment",
        "paper-faithful heavy-top inertia",
        "ABD-vs-RBD comparison",
        "Phase 50 heavy-top MABD Newton lane",
    ):
        if snippet not in normalized_boundary_text:
            fail(f"Phase 50 claim boundary missing: {snippet}")

    try:
        config = load_heavy_top_config(ROOT / "configs/experiments/single_body_heavy_top.yaml")
        matrix = load_experiment_matrix(ROOT / "configs/experiments/paper_experiment_matrix.yaml")
        validate_heavy_top_config_against_matrix(config, matrix)
    except (ExperimentRunConfigError, ExperimentMatrixError) as exc:
        fail(f"Phase 50 heavy-top config validation failed: {exc}")

    if config.required_missing_lanes != ():
        fail("Phase 50 heavy-top config must have no missing mabd_newton lane")
    if "mabd_newton_report_incomplete" not in config.failure_reason:
        fail("Phase 50 heavy-top config failure_reason must mention mabd_newton_report_incomplete")
    if "mabd_newton_report_missing" in config.failure_reason:
        fail("Phase 50 heavy-top config failure_reason must not mention mabd_newton_report_missing")
    if config.mabd_newton.output_report != (
        "reports/experiment_matrix/single_body_heavy_top_mabd_newton.json"
    ):
        fail("Phase 50 MABD output report binding changed")

    report_path = "reports/experiment_matrix/single_body_heavy_top_mabd_newton.json"
    report = load_claim_report(ROOT / report_path)
    if report.source_commit in PLACEHOLDER_SOURCE_COMMITS:
        fail("Phase 50 report source_commit must not be a placeholder")
    if report.source_commit not in text:
        fail("Phase 50 record must list the report source_commit")
    if report.vendored_newton_commit != VENDORED_NEWTON_COMMIT:
        fail("Phase 50 report vendored Newton commit changed")
    if report.claim_id != config.claim_id:
        fail("Phase 50 report claim_id does not match config")
    if report.scene_id != config.scene_id:
        fail("Phase 50 report scene_id does not match config")
    if report.asset_hashes.get("heavy_top_procedural") != "not_applicable_procedural":
        fail("Phase 50 heavy-top asset hash must remain procedural")
    if report.status.value != "incomplete":
        fail("Phase 50 heavy-top report must remain incomplete")
    actual_hash = sha256_file(ROOT / report_path)
    record_hash = _record_sha256_for_artifact(text, report_path)
    if record_hash != actual_hash:
        fail("Phase 50 heavy-top report sha256 mismatch")
    if report.baseline_lane != "mabd_newton":
        fail("Phase 50 heavy-top report lane changed")
    if report.solver_mode != "mabd_cpu_oracle_heavy_top_newton_lane":
        fail("Phase 50 heavy-top report solver mode changed")
    if report.backend != "cpu_numpy_newton_only":
        fail("Phase 50 heavy-top report backend changed")

    observed = report.observed
    rollout = roll_out_heavy_top_mabd_model_derived(config)
    if observed.get("lane_status") != "incomplete_diagnostic_generated":
        fail("Phase 50 heavy-top diagnostic status changed")
    if "lane_gate_status" in observed:
        fail("Phase 50 heavy-top report must not expose a passed lane gate")
    if observed.get("full_experiment_claim_passed") is not False:
        fail("Phase 50 heavy-top report must not pass full experiment claim")
    if observed.get("solver_model_config_source") != NEWTON_MODEL_DERIVED_CONFIG_SOURCE:
        fail("Phase 50 solver_model_config_source changed")
    if observed.get("newton_model_derived_custom_frequencies") != list(
        NEWTON_MODEL_DERIVED_CUSTOM_FREQUENCIES
    ):
        fail("Phase 50 Newton custom-frequency list changed")
    if report.expected.get("solver_model_config_source") != NEWTON_MODEL_DERIVED_CONFIG_SOURCE:
        fail("Phase 50 expected solver_model_config_source changed")
    if report.expected.get("full_experiment_claim_passed") is not False:
        fail("Phase 50 expected full_experiment_claim_passed must remain false")
    if report.expected.get("lane_report") != config.mabd_newton.output_report:
        fail("Phase 50 lane report binding changed")
    if observed.get("required_missing_lanes") != []:
        fail("Phase 50 heavy-top required_missing_lanes must be empty")

    blockers = observed.get("blocking_reasons")
    if not isinstance(blockers, list):
        fail("Phase 50 heavy-top blockers must be a list")
    for blocker in (
        "exact_heavy_top_inertia_unknown",
        "exact_heavy_top_geometry_unknown",
        "raw_heavy_top_reference_curve_data_missing",
        "mabd_newton_report_incomplete",
        "heavy_top_comparison_report_incomplete",
        "heavy_top_timing_evidence_missing",
    ):
        if blocker not in blockers:
            fail(f"Phase 50 heavy-top blocker missing: {blocker}")
    if "mabd_newton_report_missing" in blockers:
        fail("Phase 50 heavy-top report must not keep mabd_newton_report_missing")

    if observed.get("threshold_violations") != []:
        fail("Phase 50 heavy-top threshold_violations changed")
    scalar_checks = (
        ("step_count", rollout.step_count, 0.0),
        ("sample_count", rollout.sample_count, 0.0),
        ("time_step_s", rollout.time_step_s, 0.0),
        ("energy_initial", rollout.energy_initial, 1.0e-12),
        ("energy_final", rollout.energy_final, 1.0e-12),
        ("relative_energy_drift", rollout.relative_energy_drift, 1.0e-14),
        ("min_nutation_angle_deg", rollout.min_nutation_angle_deg, 1.0e-12),
        ("max_nutation_angle_deg", rollout.max_nutation_angle_deg, 1.0e-12),
        ("max_abs_precession_velocity_rad_s", rollout.max_abs_precession_velocity_rad_s, 1.0e-12),
        ("max_pivot_residual_m", rollout.max_pivot_residual_m, 1.0e-14),
        ("max_constraint_residual_norm", rollout.max_constraint_residual_norm, 1.0e-14),
        ("max_affine_shape_spread_m", rollout.max_affine_shape_spread_m, 1.0e-12),
        (
            "max_world_anchor_reaction_magnitude_n",
            rollout.max_world_anchor_reaction_magnitude_n,
            1.0e-12,
        ),
    )
    for key, expected, atol in scalar_checks:
        actual = _require_finite_scalar(observed.get(key), f"Phase 50 heavy-top {key}")
        if not np.isclose(actual, float(expected), rtol=0.0, atol=atol):
            fail(f"Phase 50 heavy-top {key} does not match recomputed rollout")

    if observed.get("mabd_rotation_mode") != config.mabd_newton.rotation_mode:
        fail("Phase 50 heavy-top rotation mode changed")
    if not np.allclose(
        observed.get("rest_points_m"),
        config.mabd_newton.rest_points_m.tolist(),
        rtol=0.0,
        atol=1.0e-15,
    ):
        fail("Phase 50 heavy-top rest_points_m changed")
    if not np.allclose(
        observed.get("point_masses_kg"),
        config.mabd_newton.point_masses_kg.tolist(),
        rtol=0.0,
        atol=1.0e-15,
    ):
        fail("Phase 50 heavy-top point masses changed")
    if _require_finite_vector3(observed.get("gravity_m_s2"), "Phase 50 gravity") != [
        0.0,
        -9.81,
        0.0,
    ]:
        fail("Phase 50 heavy-top gravity changed")
    if (
        observed["max_nutation_angle_deg"] - observed["min_nutation_angle_deg"]
        < config.mabd_newton.thresholds["min_nutation_angle_range_deg"]
    ):
        fail("Phase 50 heavy-top nutation range below threshold")
    if observed["max_pivot_residual_m"] > config.mabd_newton.thresholds["max_pivot_residual_m"]:
        fail("Phase 50 heavy-top pivot residual exceeded threshold")
    if (
        observed["max_constraint_residual_norm"]
        > config.mabd_newton.thresholds["max_constraint_residual_norm"]
    ):
        fail("Phase 50 heavy-top constraint residual exceeded threshold")
    if (
        observed["max_affine_shape_spread_m"]
        > config.mabd_newton.thresholds["max_affine_shape_spread_m"]
    ):
        fail("Phase 50 heavy-top affine shape spread exceeded threshold")

    samples = observed.get("precession_nutation_samples")
    if not isinstance(samples, list) or len(samples) != config.mabd_newton.sample_count:
        fail("Phase 50 heavy-top precession_nutation_samples changed")
    for index, sample in enumerate(samples):
        if not isinstance(sample, dict):
            fail("Phase 50 heavy-top sample must be a mapping")
        if sample.get("sample_index") != index:
            fail("Phase 50 heavy-top sample_index changed")
        expected_sample = rollout.samples[index]
        for key, expected in (
            ("step", expected_sample.step),
            ("time_s", expected_sample.time_s),
            ("nutation_angle_deg", expected_sample.nutation_angle_deg),
            ("precession_angle_rad", expected_sample.precession_angle_rad),
            ("precession_velocity_rad_s", expected_sample.precession_velocity_rad_s),
            ("pivot_residual_m", expected_sample.pivot_residual_m),
            ("constraint_residual_norm", expected_sample.constraint_residual_norm),
            ("affine_shape_spread_m", expected_sample.affine_shape_spread_m),
            ("world_anchor_reaction_magnitude_n", expected_sample.world_anchor_reaction_magnitude_n),
        ):
            actual = _require_finite_scalar(sample.get(key), f"Phase 50 sample {index} {key}")
            if not np.isclose(actual, float(expected), rtol=0.0, atol=1.0e-12):
                fail(f"Phase 50 heavy-top sample {index} {key} changed")

    claims = read_yaml(ROOT / "docs/reference/paper-claims.yaml").get("claims")
    if not isinstance(claims, list):
        fail("paper-claims.yaml missing claims list")
    found_heavy_top = False
    for claim in claims:
        if not isinstance(claim, dict):
            continue
        claim_id = str(claim.get("claim_id", ""))
        if claim_id == "experiment.single_body.heavy_top":
            found_heavy_top = True
            if claim.get("reproduction_status") != "intended":
                fail("Phase 50 must keep heavy-top experiment status intended")
            conflict_note = str(claim.get("conflict_note", ""))
            if "mabd_newton_report_incomplete" not in conflict_note:
                fail("Phase 50 heavy-top conflict_note missing mabd_newton_report_incomplete")
            if "mabd_newton_report_missing" in conflict_note:
                fail("Phase 50 heavy-top conflict_note must not keep mabd_newton_report_missing")
        if claim_id.startswith("experiment.") and claim.get("reproduction_status") == "passed":
            fail("Phase 50 must not pass experiment.* claims")
    if not found_heavy_top:
        fail("paper-claims.yaml missing heavy-top claim")

    matrix_data = read_yaml(ROOT / "configs/experiments/paper_experiment_matrix.yaml")
    experiments = matrix_data.get("experiments")
    if not isinstance(experiments, list):
        fail("Phase 50 experiment matrix missing experiments")
    matrix_entry = next(
        (
            item
            for item in experiments
            if isinstance(item, dict)
            and item.get("claim_id") == "experiment.single_body.heavy_top"
        ),
        None,
    )
    if matrix_entry is None:
        fail("Phase 50 matrix missing heavy-top experiment")
    if matrix_entry.get("reproduction_status") != "planned":
        fail("Phase 50 matrix must keep heavy-top planned")
    matrix_blockers = matrix_entry.get("blocking_reasons")
    if not isinstance(matrix_blockers, list):
        fail("Phase 50 matrix heavy-top blockers must be a list")
    if "mabd_newton_report_incomplete" not in matrix_blockers:
        fail("Phase 50 matrix blocker missing mabd_newton_report_incomplete")
    if "mabd_newton_report_missing" in matrix_blockers:
        fail("Phase 50 matrix must not keep mabd_newton_report_missing")


def validate_phase51_record() -> None:
    text = (
        ROOT / "docs/records/2026-05-18-phase51-heavy-top-comparison-protocol.md"
    ).read_text(encoding="utf-8")
    required_snippets = (
        "## Status\n\npassed_for_heavy_top_comparison_protocol",
        "phase51-heavy-top-comparison-protocol",
        "ef53522077c53b4842f5198938dd5c24190e7863",
        VENDORED_NEWTON_COMMIT,
        "reports/experiment_matrix/single_body_heavy_top_comparison.json",
        "522d0dbea2eacbe1f334400dbcba4bd885ba26cecd50d239463048f7e24ec8de",
        "reports/experiment_matrix/single_body_heavy_top_rk4_reference.json",
        "41418e964dd9e7fba1516f420fa97ced8cfaf9157d552d9072f85fcbb08f564c",
        "reports/experiment_matrix/single_body_heavy_top_mabd_newton.json",
        "9342374ffde72071308b6aa5c117815392f71f4db1e07d9817ac61e4847bf324",
        "heavy_top_multilane_comparison_development",
        "heavy_top_comparison_protocol",
        "report_protocol",
        "mabd_newton_report_incomplete",
        "heavy_top_comparison_report_incomplete",
        "heavy_top_comparison_pass_gate_not_enabled",
        "sample_time_grid_mismatch",
        "nutation_angle_error:paper_reference_curve_missing",
        "MABD precession velocity status: `diagnostic_available`",
        "MABD energy drift status: `diagnostic_available`",
        "No `experiment.*` claim is passed.",
        "`experiment.single_body.heavy_top` remains intended",
        "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_run_configs tests.test_heavy_top_comparison_reports tests.test_experiment_runner",
        "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py",
        "git diff --check",
    )
    for snippet in required_snippets:
        if snippet not in text:
            fail(f"Phase 51 record missing required evidence field: {snippet}")
    for placeholder in (
        "TO_BE_BACKFILLED_PHASE51",
        "phase51-working-tree",
        "<implementation-commit>",
    ):
        if placeholder in text:
            fail("Phase 51 record contains stale placeholder")

    lower_text = text.lower()
    for snippet in (
        "passed heavy-top experiment",
        "heavy-top experiment passed",
        "paper-faithful heavy-top inertia is verified",
        "raw curve agreement passed",
        "abd-vs-rbd comparison passed",
        "runtime performance reproduced",
        "full reproduction complete",
    ):
        if snippet in lower_text:
            fail(f"Phase 51 record overclaims unsupported evidence: {snippet}")

    boundary_text = (ROOT / "docs/reference/claim-boundaries.md").read_text(encoding="utf-8")
    normalized_boundary_text = " ".join(boundary_text.split())
    for snippet in (
        "This repository contains Phase 51 heavy-top comparison protocol evidence",
        "Phase 51 verifies an executable `heavy_top_comparison_protocol` report",
        "input report provenance and sha256 hashes",
        "sample time-grid mismatch",
        "`heavy_top_comparison_report_incomplete`",
        "Phase 51 does not verify a passed heavy-top experiment",
        "comparison pass gate",
        "Phase 51 heavy-top comparison protocol",
    ):
        if snippet not in normalized_boundary_text:
            fail(f"Phase 51 claim boundary missing: {snippet}")

    try:
        config = load_heavy_top_config(ROOT / "configs/experiments/single_body_heavy_top.yaml")
        matrix = load_experiment_matrix(ROOT / "configs/experiments/paper_experiment_matrix.yaml")
        validate_heavy_top_config_against_matrix(config, matrix)
    except (ExperimentRunConfigError, ExperimentMatrixError) as exc:
        fail(f"Phase 51 heavy-top config validation failed: {exc}")

    comparison_path = "reports/experiment_matrix/single_body_heavy_top_comparison.json"
    rk4_path = "reports/experiment_matrix/single_body_heavy_top_rk4_reference.json"
    mabd_path = "reports/experiment_matrix/single_body_heavy_top_mabd_newton.json"
    report = load_claim_report(ROOT / comparison_path)
    rk4_report = load_claim_report(ROOT / rk4_path)
    mabd_report = load_claim_report(ROOT / mabd_path)
    observed = report.observed
    digitized_figure_available = observed.get("digitized_figure_reference_available") is True
    if report.source_commit in PLACEHOLDER_SOURCE_COMMITS:
        fail("Phase 51 report source_commit must not be a placeholder")
    if report.source_commit not in text and not digitized_figure_available:
        fail("Phase 51 record must list the report source_commit")
    if report.vendored_newton_commit != VENDORED_NEWTON_COMMIT:
        fail("Phase 51 report vendored Newton commit changed")
    if report.claim_id != config.claim_id or report.scene_id != config.scene_id:
        fail("Phase 51 report identity does not match config")
    if report.asset_hashes.get("heavy_top_procedural") != "not_applicable_procedural":
        fail("Phase 51 heavy-top asset hash must remain procedural")
    if report.status.value != "incomplete":
        fail("Phase 51 heavy-top comparison report must remain incomplete")
    if (
        _record_sha256_for_artifact(text, comparison_path) != sha256_file(ROOT / comparison_path)
        and not digitized_figure_available
    ):
        fail("Phase 51 heavy-top comparison report sha256 mismatch")
    if report.baseline_lane != "heavy_top_comparison_protocol":
        fail("Phase 51 heavy-top comparison lane changed")
    if report.solver_mode != "heavy_top_multilane_comparison_development":
        fail("Phase 51 heavy-top comparison solver mode changed")
    if report.backend != "report_protocol":
        fail("Phase 51 heavy-top comparison backend changed")

    if observed.get("full_experiment_claim_passed") is not False:
        fail("Phase 51 heavy-top comparison must not pass full experiment claim")
    if observed.get("missing_required_lanes") != []:
        fail("Phase 51 heavy-top comparison missing lanes changed")
    expected_missing_metrics = ["nutation_angle_error:paper_reference_curve_missing"]
    expected_digitized_missing_metrics = [
        "nutation_angle_error:paper_figure_digitized_curve_agreement_not_passed"
    ]
    if observed.get("missing_paper_metrics") not in (
        expected_missing_metrics,
        expected_digitized_missing_metrics,
    ):
        fail("Phase 51 heavy-top comparison missing paper metrics changed")
    paper_metric_statuses = observed.get("paper_metric_statuses")
    if not isinstance(paper_metric_statuses, dict):
        fail("Phase 51 heavy-top paper_metric_statuses must be a mapping")
    if (
        paper_metric_statuses.get("precession_velocity_error", {}).get("status")
        != "diagnostic_available"
    ):
        fail("Phase 51 heavy-top precession metric status must be diagnostic_available")
    if paper_metric_statuses.get("energy_drift", {}).get("status") != "diagnostic_available":
        fail("Phase 51 heavy-top energy metric status must be diagnostic_available")
    blockers = observed.get("blocking_reasons")
    if not isinstance(blockers, list):
        fail("Phase 51 heavy-top comparison blockers must be a list")
    for blocker in (
        "exact_heavy_top_inertia_unknown",
        "exact_heavy_top_geometry_unknown",
        "raw_heavy_top_reference_curve_data_missing",
        "mabd_newton_report_incomplete",
        "heavy_top_comparison_report_incomplete",
        "heavy_top_timing_evidence_missing",
        "heavy_top_comparison_pass_gate_not_enabled",
        "sample_time_grid_mismatch",
    ):
        if blocker not in blockers:
            fail(f"Phase 51 heavy-top comparison blocker missing: {blocker}")
    if (
        digitized_figure_available
        and "heavy_top_digitized_figure_curve_agreement_not_passed" not in blockers
    ):
        fail("Phase 51 heavy-top comparison missing digitized-figure agreement blocker")
    if observed.get("time_grid_mismatch") is not True:
        fail("Phase 51 heavy-top comparison must record sample time-grid mismatch")
    if observed.get("sample_nonfinite") is not False:
        fail("Phase 51 heavy-top comparison sample_nonfinite changed")
    if _require_finite_scalar(
        observed.get("matched_sample_index_count"),
        "Phase 51 matched_sample_index_count",
    ) < 1:
        fail("Phase 51 heavy-top comparison must retain matched samples")
    if _require_finite_scalar(
        observed.get("max_sample_time_delta_s"),
        "Phase 51 max_sample_time_delta_s",
    ) <= config.comparison.thresholds["max_sample_time_delta_s"]:
        fail("Phase 51 heavy-top comparison expected a time-grid mismatch")

    provenance = observed.get("input_report_provenance")
    if not isinstance(provenance, dict):
        fail("Phase 51 comparison missing input_report_provenance")
    for lane, path, lane_report in (
        ("rbd_rk4_reference", rk4_path, rk4_report),
        ("mabd_newton", mabd_path, mabd_report),
    ):
        lane_provenance = provenance.get(lane)
        if not isinstance(lane_provenance, dict):
            fail(f"Phase 51 comparison missing {lane} input provenance")
        if lane_provenance.get("path") != path:
            fail(f"Phase 51 {lane} input path changed")
        if lane_provenance.get("sha256") != sha256_file(ROOT / path):
            fail(f"Phase 51 {lane} input sha256 mismatch")
        if lane_provenance.get("source_commit") != lane_report.source_commit:
            fail(f"Phase 51 {lane} source_commit provenance mismatch")
        if not digitized_figure_available and lane_report.source_commit != report.source_commit:
            fail(f"Phase 51 {lane} report must be regenerated with comparison source_commit")
        if lane_report.status.value != "incomplete":
            fail(f"Phase 51 {lane} input report must remain incomplete")

    claims = read_yaml(ROOT / "docs/reference/paper-claims.yaml").get("claims")
    if not isinstance(claims, list):
        fail("paper-claims.yaml missing claims list")
    for claim in claims:
        if not isinstance(claim, dict):
            continue
        claim_id = str(claim.get("claim_id", ""))
        if claim_id == "experiment.single_body.heavy_top":
            if claim.get("reproduction_status") != "intended":
                fail("Phase 51 must keep heavy-top experiment status intended")
            conflict_note = str(claim.get("conflict_note", ""))
            if "heavy_top_comparison_report_incomplete" not in conflict_note:
                fail("Phase 51 heavy-top conflict_note missing comparison blocker")
            if "heavy_top_comparison_report_missing" in conflict_note:
                fail("Phase 51 heavy-top conflict_note must not keep missing comparison blocker")
        if claim_id.startswith("experiment.") and claim.get("reproduction_status") == "passed":
            fail("Phase 51 must not pass experiment.* claims")


def validate_phase52_record() -> None:
    text = (
        ROOT / "docs/records/2026-05-18-phase52-heavy-top-mabd-metrics.md"
    ).read_text(encoding="utf-8")
    required_snippets = (
        "## Status\n\npassed_for_heavy_top_mabd_metric_diagnostics",
        "phase52-heavy-top-mabd-metrics",
        "ef53522077c53b4842f5198938dd5c24190e7863",
        VENDORED_NEWTON_COMMIT,
        "reports/experiment_matrix/single_body_heavy_top_mabd_newton.json",
        "9342374ffde72071308b6aa5c117815392f71f4db1e07d9817ac61e4847bf324",
        "reports/experiment_matrix/single_body_heavy_top_comparison.json",
        "522d0dbea2eacbe1f334400dbcba4bd885ba26cecd50d239463048f7e24ec8de",
        "reports/experiment_matrix/single_body_heavy_top_rk4_reference.json",
        "41418e964dd9e7fba1516f420fa97ced8cfaf9157d552d9072f85fcbb08f564c",
        "mabd_cpu_oracle_heavy_top_newton_lane",
        "heavy_top_multilane_comparison_development",
        "precession_velocity_rad_s",
        "diagnostic relative energy drift: `-0.0014033729823068706`",
        "MABD precession velocity status: `diagnostic_available`",
        "MABD energy drift status: `diagnostic_available`",
        "nutation_angle_error:paper_reference_curve_missing",
        "sample_time_grid_mismatch",
        "No `experiment.*` claim is passed.",
        "`experiment.single_body.heavy_top` remains intended",
        "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_heavy_top_mabd tests.test_heavy_top_comparison_reports",
        "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests",
        "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py",
        "PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c \"import newton; print(newton.__file__)\"",
        "/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .",
        "git diff --check",
    )
    for snippet in required_snippets:
        if snippet not in text:
            fail(f"Phase 52 record missing required evidence field: {snippet}")
    for placeholder in (
        "TO_BE_BACKFILLED_PHASE52",
        "phase52-working-tree",
        "<implementation-commit>",
    ):
        if placeholder in text:
            fail("Phase 52 record contains stale placeholder")

    lower_text = text.lower()
    for snippet in (
        "passed heavy-top experiment",
        "heavy-top experiment passed",
        "paper-faithful heavy-top inertia is verified",
        "raw curve agreement passed",
        "abd-vs-rbd comparison passed",
        "runtime performance reproduced",
        "full reproduction complete",
    ):
        if snippet in lower_text:
            fail(f"Phase 52 record overclaims unsupported evidence: {snippet}")

    boundary_text = (ROOT / "docs/reference/claim-boundaries.md").read_text(encoding="utf-8")
    normalized_boundary_text = " ".join(boundary_text.split())
    for snippet in (
        "This repository contains Phase 52 heavy-top MABD diagnostic metric evidence",
        "Phase 52 verifies that the heavy-top `mabd_newton` diagnostic report records",
        "finite per-sample `precession_velocity_rad_s`",
        "`energy_initial`, `energy_final`, and `relative_energy_drift`",
        "no longer marks MABD precession velocity or MABD energy drift as missing",
        "`nutation_angle_error:paper_reference_curve_missing`",
        "Phase 52 does not verify a passed heavy-top experiment",
        "Phase 52 heavy-top MABD metrics",
    ):
        if snippet not in normalized_boundary_text:
            fail(f"Phase 52 claim boundary missing: {snippet}")

    try:
        config = load_heavy_top_config(ROOT / "configs/experiments/single_body_heavy_top.yaml")
        matrix = load_experiment_matrix(ROOT / "configs/experiments/paper_experiment_matrix.yaml")
        validate_heavy_top_config_against_matrix(config, matrix)
    except (ExperimentRunConfigError, ExperimentMatrixError) as exc:
        fail(f"Phase 52 heavy-top config validation failed: {exc}")

    mabd_path = "reports/experiment_matrix/single_body_heavy_top_mabd_newton.json"
    comparison_path = "reports/experiment_matrix/single_body_heavy_top_comparison.json"
    rk4_path = "reports/experiment_matrix/single_body_heavy_top_rk4_reference.json"
    mabd_report = load_claim_report(ROOT / mabd_path)
    comparison_report = load_claim_report(ROOT / comparison_path)
    rk4_report = load_claim_report(ROOT / rk4_path)
    comparison_observed = comparison_report.observed
    digitized_figure_available = (
        comparison_observed.get("digitized_figure_reference_available") is True
    )

    for label, path, report in (
        ("MABD", mabd_path, mabd_report),
        ("comparison", comparison_path, comparison_report),
        ("RK4", rk4_path, rk4_report),
    ):
        if report.source_commit in PLACEHOLDER_SOURCE_COMMITS:
            fail(f"Phase 52 {label} report source_commit must not be a placeholder")
        if report.source_commit not in text and not (label == "comparison" and digitized_figure_available):
            fail(f"Phase 52 record must list {label} report source_commit")
        if report.vendored_newton_commit != VENDORED_NEWTON_COMMIT:
            fail(f"Phase 52 {label} report vendored Newton commit changed")
        if report.status.value != "incomplete":
            fail(f"Phase 52 {label} report must remain incomplete")
        if (
            _record_sha256_for_artifact(text, path) != sha256_file(ROOT / path)
            and not (label == "comparison" and digitized_figure_available)
        ):
            fail(f"Phase 52 {label} report sha256 mismatch")
        if report.observed.get("full_experiment_claim_passed") is not False:
            fail(f"Phase 52 {label} report must not pass full experiment claim")

    if mabd_report.claim_id != config.claim_id or mabd_report.scene_id != config.scene_id:
        fail("Phase 52 MABD report identity does not match config")
    if comparison_report.claim_id != config.claim_id or comparison_report.scene_id != config.scene_id:
        fail("Phase 52 comparison report identity does not match config")
    if mabd_report.baseline_lane != "mabd_newton":
        fail("Phase 52 MABD baseline lane changed")
    if comparison_report.baseline_lane != "heavy_top_comparison_protocol":
        fail("Phase 52 comparison baseline lane changed")
    if mabd_report.solver_mode != "mabd_cpu_oracle_heavy_top_newton_lane":
        fail("Phase 52 MABD solver mode changed")
    if comparison_report.solver_mode != "heavy_top_multilane_comparison_development":
        fail("Phase 52 comparison solver mode changed")

    rollout = roll_out_heavy_top_mabd_model_derived(config)
    observed = mabd_report.observed
    for key, expected, atol in (
        ("energy_initial", rollout.energy_initial, 1.0e-12),
        ("energy_final", rollout.energy_final, 1.0e-12),
        ("relative_energy_drift", rollout.relative_energy_drift, 1.0e-14),
        ("max_abs_precession_velocity_rad_s", rollout.max_abs_precession_velocity_rad_s, 1.0e-12),
    ):
        actual = _require_finite_scalar(observed.get(key), f"Phase 52 MABD {key}")
        if not np.isclose(actual, float(expected), rtol=0.0, atol=atol):
            fail(f"Phase 52 MABD {key} does not match recomputed rollout")
    if observed.get("threshold_violations") != []:
        fail("Phase 52 MABD threshold_violations changed")

    samples = observed.get("precession_nutation_samples")
    if not isinstance(samples, list) or len(samples) != config.mabd_newton.sample_count:
        fail("Phase 52 MABD samples changed")
    for index, sample in enumerate(samples):
        if not isinstance(sample, dict):
            fail("Phase 52 MABD sample must be a mapping")
        expected_sample = rollout.samples[index]
        actual_velocity = _require_finite_scalar(
            sample.get("precession_velocity_rad_s"),
            f"Phase 52 sample {index} precession_velocity_rad_s",
        )
        if not np.isclose(
            actual_velocity,
            expected_sample.precession_velocity_rad_s,
            rtol=0.0,
            atol=1.0e-12,
        ):
            fail(f"Phase 52 MABD sample {index} precession velocity changed")

    if comparison_observed.get("missing_paper_metrics") not in (
        ["nutation_angle_error:paper_reference_curve_missing"],
        ["nutation_angle_error:paper_figure_digitized_curve_agreement_not_passed"],
    ):
        fail("Phase 52 comparison missing_paper_metrics changed")
    metric_statuses = comparison_observed.get("paper_metric_statuses")
    if not isinstance(metric_statuses, dict):
        fail("Phase 52 comparison paper_metric_statuses must be a mapping")
    if metric_statuses.get("precession_velocity_error", {}).get("status") != "diagnostic_available":
        fail("Phase 52 comparison precession velocity status changed")
    if metric_statuses.get("energy_drift", {}).get("status") != "diagnostic_available":
        fail("Phase 52 comparison energy status changed")
    lane_metrics = comparison_observed.get("lane_metrics")
    if not isinstance(lane_metrics, dict):
        fail("Phase 52 comparison lane_metrics must be a mapping")
    if _require_finite_scalar(
        lane_metrics.get("mabd_newton", {}).get("energy_drift"),
        "Phase 52 comparison MABD energy_drift",
    ) != _require_finite_scalar(
        observed.get("relative_energy_drift"),
        "Phase 52 MABD relative_energy_drift",
    ):
        fail("Phase 52 comparison MABD energy_drift does not mirror MABD report")
    for blocker in (
        "exact_heavy_top_inertia_unknown",
        "exact_heavy_top_geometry_unknown",
        "raw_heavy_top_reference_curve_data_missing",
        "mabd_newton_report_incomplete",
        "heavy_top_comparison_report_incomplete",
        "heavy_top_timing_evidence_missing",
        "heavy_top_comparison_pass_gate_not_enabled",
        "sample_time_grid_mismatch",
    ):
        if blocker not in comparison_observed.get("blocking_reasons", []):
            fail(f"Phase 52 comparison blocker missing: {blocker}")
    if digitized_figure_available and (
        "heavy_top_digitized_figure_curve_agreement_not_passed"
        not in comparison_observed.get("blocking_reasons", [])
    ):
        fail("Phase 52 comparison missing digitized-figure agreement blocker")

    provenance = comparison_observed.get("input_report_provenance")
    if not isinstance(provenance, dict):
        fail("Phase 52 comparison input_report_provenance must be a mapping")
    for lane, path, report in (
        ("rbd_rk4_reference", rk4_path, rk4_report),
        ("mabd_newton", mabd_path, mabd_report),
    ):
        lane_provenance = provenance.get(lane)
        if not isinstance(lane_provenance, dict):
            fail(f"Phase 52 comparison missing {lane} provenance")
        if lane_provenance.get("sha256") != sha256_file(ROOT / path):
            fail(f"Phase 52 comparison {lane} provenance sha256 mismatch")
        if lane_provenance.get("source_commit") != report.source_commit:
            fail(f"Phase 52 comparison {lane} provenance source_commit mismatch")

    claims = read_yaml(ROOT / "docs/reference/paper-claims.yaml").get("claims")
    if not isinstance(claims, list):
        fail("paper-claims.yaml missing claims list")
    for claim in claims:
        if not isinstance(claim, dict):
            continue
        claim_id = str(claim.get("claim_id", ""))
        if claim_id == "experiment.single_body.heavy_top":
            if claim.get("reproduction_status") != "intended":
                fail("Phase 52 must keep heavy-top experiment status intended")
        if claim_id.startswith("experiment.") and claim.get("reproduction_status") == "passed":
            fail("Phase 52 must not pass experiment.* claims")


def validate_phase53_record() -> None:
    text = (
        ROOT / "docs/records/2026-05-18-phase53-heavy-top-figure-curves.md"
    ).read_text(encoding="utf-8")
    figure_path = "reports/experiment_matrix/single_body_heavy_top_figure_curves.json"
    comparison_path = "reports/experiment_matrix/single_body_heavy_top_comparison.json"
    rk4_path = "reports/experiment_matrix/single_body_heavy_top_rk4_reference.json"
    mabd_path = "reports/experiment_matrix/single_body_heavy_top_mabd_newton.json"
    required_snippets = (
        "## Status\n\npassed_for_heavy_top_figure_curve_digitization_lane",
        "phase53-heavy-top-figure-curves",
        "24d3858a8b1d7eca346aec80c13e68652099b600",
        VENDORED_NEWTON_COMMIT,
        str(HEAVY_TOP_FIGURE_PDF),
        HEAVY_TOP_FIGURE_PDF_SHA256,
        "pdftocairo 22.02.0",
        "3179 x 1924",
        "paper_figure_reference_family_only",
        "not_authors_raw_data",
        "no_blue_orange_line_style_split",
        figure_path,
        "1fc15336ba81146554bd26e7be6b33a13f84b36bd0ae3d0b672b46e72742ced1",
        comparison_path,
        "ef8c3fd21ac1159798f8102c18834e0b75655e6d0e396f69e8d4fdd738f7d87f",
        "paper_figure_digitization",
        "heavy_top_paper_figure_digitization",
        "pdftocairo_pillow",
        "paper_figure_digitized_reference_available",
        "nutation_angle_error:paper_figure_digitized_curve_agreement_not_passed",
        "raw_heavy_top_reference_curve_data_missing",
        "heavy_top_digitized_figure_curve_agreement_not_passed",
        "No `experiment.*` claim is passed.",
        "`experiment.single_body.heavy_top` remains intended",
        "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests",
        "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py",
        "PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c \"import newton; print(newton.__file__)\"",
        "/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .",
        "git diff --check",
    )
    for snippet in required_snippets:
        if snippet not in text:
            fail(f"Phase 53 record missing required evidence field: {snippet}")
    for placeholder in (
        "TO_BE_BACKFILLED_PHASE53",
        "phase53-working-tree",
        "<implementation-commit>",
    ):
        if placeholder in text:
            fail("Phase 53 record contains stale placeholder")

    lower_text = text.lower()
    for snippet in (
        "passed heavy-top experiment",
        "heavy-top experiment passed",
        "authors' raw simulation data is available",
        "blue/orange solid and dashed paper curves separated",
        "heavy-top curve agreement passed",
        "paper-faithful heavy-top inertia is verified",
        "abd-vs-rbd comparison passed",
        "runtime performance reproduced",
        "full reproduction complete",
    ):
        if snippet in lower_text:
            fail(f"Phase 53 record overclaims unsupported evidence: {snippet}")

    boundary_text = (ROOT / "docs/reference/claim-boundaries.md").read_text(encoding="utf-8")
    current = claim_boundary_bullet(boundary_text, "This repository contains Phase 53")
    verified = claim_boundary_bullet(boundary_text, "Phase 53 verifies")
    non_claim = claim_boundary_bullet(boundary_text, "Phase 53 does not verify")
    forbidden = claim_boundary_bullet(
        boundary_text, "Phase 53 heavy-top paper-figure digitization"
    )
    for snippet in (
        "heavy-top paper-figure digitization evidence",
        "Phase 53 record",
    ):
        if snippet not in current:
            fail(f"Phase 53 current boundary missing: {snippet}")
    for snippet in (
        "digitized paper-figure reference-family samples",
        "recorded `spinning_top.pdf`",
        "pdftocairo 22.02.0",
        "3179 x 1924",
        "compact numeric JSON samples",
        "figure_curve_report_path",
        "paper_figure_digitized_reference_available",
        "raw author curve data remains unavailable",
        "raw_heavy_top_reference_curve_data_missing",
    ):
        if snippet not in verified:
            fail(f"Phase 53 verified boundary missing: {snippet}")
    for snippet in (
        "passed heavy-top experiment",
        "authors' raw simulation data",
        "blue/orange solid and dashed paper curves",
        "heavy-top curve agreement",
        "paper-faithful heavy-top inertia or geometry",
        "paper timing",
        "rendered output",
        "full paper reproduction",
        "any passed `experiment.*` claim",
    ):
        if snippet not in non_claim:
            fail(f"Phase 53 non-claim boundary missing: {snippet}")
        if snippet not in forbidden:
            fail(f"Phase 53 forbidden boundary missing: {snippet}")

    try:
        config = load_heavy_top_config(ROOT / "configs/experiments/single_body_heavy_top.yaml")
        matrix = load_experiment_matrix(ROOT / "configs/experiments/paper_experiment_matrix.yaml")
        validate_heavy_top_config_against_matrix(config, matrix)
    except (ExperimentRunConfigError, ExperimentMatrixError) as exc:
        fail(f"Phase 53 heavy-top config validation failed: {exc}")

    figure_report = load_claim_report(ROOT / figure_path)
    comparison_report = load_claim_report(ROOT / comparison_path)
    rk4_report = load_claim_report(ROOT / rk4_path)
    mabd_report = load_claim_report(ROOT / mabd_path)

    for label, path, report in (
        ("figure", figure_path, figure_report),
        ("comparison", comparison_path, comparison_report),
        ("RK4", rk4_path, rk4_report),
        ("MABD", mabd_path, mabd_report),
    ):
        if report.source_commit in PLACEHOLDER_SOURCE_COMMITS:
            fail(f"Phase 53 {label} report source_commit must not be a placeholder")
        if report.vendored_newton_commit != VENDORED_NEWTON_COMMIT:
            fail(f"Phase 53 {label} report vendored Newton commit changed")
        if report.status.value != "incomplete":
            fail(f"Phase 53 {label} report must remain incomplete")
        if report.observed.get("full_experiment_claim_passed") is not False:
            fail(f"Phase 53 {label} report must not pass full experiment claim")
        if label in {"figure", "comparison"} and report.source_commit not in text:
            fail(f"Phase 53 record must list {label} report source_commit")
        if label in {"figure", "comparison"}:
            if _record_sha256_for_artifact(text, path) != sha256_file(ROOT / path):
                fail(f"Phase 53 {label} report sha256 mismatch")

    if figure_report.claim_id != config.claim_id or figure_report.scene_id != config.scene_id:
        fail("Phase 53 figure report identity does not match config")
    if (
        comparison_report.claim_id != config.claim_id
        or comparison_report.scene_id != config.scene_id
    ):
        fail("Phase 53 comparison report identity does not match config")
    if figure_report.asset_hashes.get("spinning_top_pdf") != HEAVY_TOP_FIGURE_PDF_SHA256:
        fail("Phase 53 figure report source PDF asset hash changed")
    if figure_report.baseline_lane != "paper_figure_digitization":
        fail("Phase 53 figure report baseline lane changed")
    if figure_report.solver_mode != "heavy_top_paper_figure_digitization":
        fail("Phase 53 figure report solver mode changed")
    if figure_report.backend != "pdftocairo_pillow":
        fail("Phase 53 figure report backend changed")

    observed = figure_report.observed
    if observed.get("lane_status") != "reference_curves_digitized":
        fail("Phase 53 figure lane status changed")
    if observed.get("reference_curve_available") is not True:
        fail("Phase 53 figure report must expose available reference curves")
    if observed.get("source_pdf_path") != str(HEAVY_TOP_FIGURE_PDF):
        fail("Phase 53 figure report source PDF path changed")
    if observed.get("source_pdf_sha256") != HEAVY_TOP_FIGURE_PDF_SHA256:
        fail("Phase 53 figure report source PDF sha256 changed")
    if observed.get("renderer_version") != "pdftocairo 22.02.0":
        fail("Phase 53 figure report renderer version changed")
    if observed.get("render_dpi") != RENDER_DPI:
        fail("Phase 53 figure report render DPI changed")
    if observed.get("rendered_size_px") != list(EXPECTED_RENDERED_SIZE_PX):
        fail("Phase 53 figure report rendered size changed")
    limitations = observed.get("limitations")
    if not isinstance(limitations, list):
        fail("Phase 53 figure limitations must be a list")
    for limitation in (
        "not_authors_raw_data",
        "no_blue_orange_line_style_split",
        "no_curve_agreement_gate",
        "no_runtime_timing_evidence",
    ):
        if limitation not in limitations:
            fail(f"Phase 53 figure limitation missing: {limitation}")
    raw_outputs_text = str(figure_report.raw_outputs).lower()
    for forbidden_payload in (".png", ".svg", ".pdf", "base64"):
        if forbidden_payload in raw_outputs_text:
            fail(f"Phase 53 figure raw_outputs must not vendor {forbidden_payload} payloads")
    if figure_report.raw_outputs != {"reference_samples": "compact_numeric_samples_only"}:
        fail("Phase 53 figure raw_outputs changed")

    reference_curves = observed.get("reference_curves")
    if not isinstance(reference_curves, dict):
        fail("Phase 53 figure report missing reference_curves")
    for curve_name in ("reference_precession", "reference_nutation"):
        curve = reference_curves.get(curve_name)
        if not isinstance(curve, dict):
            fail(f"Phase 53 figure report missing {curve_name}")
        if curve.get("extraction_success") is not True:
            fail(f"Phase 53 {curve_name} extraction must succeed")
        if _require_finite_scalar(curve.get("sample_coverage"), curve_name) <= 0.80:
            fail(f"Phase 53 {curve_name} coverage below threshold")
        samples = curve.get("samples")
        if not isinstance(samples, list) or len(samples) < 51:
            fail(f"Phase 53 {curve_name} samples changed")
        for index, sample in enumerate(samples):
            if not isinstance(sample, dict):
                fail(f"Phase 53 {curve_name} sample must be a mapping")
            _require_finite_scalar(sample.get("time_s"), f"Phase 53 {curve_name} time {index}")
            _require_finite_scalar(sample.get("value"), f"Phase 53 {curve_name} value {index}")

    comparison_observed = comparison_report.observed
    metric_statuses = comparison_observed.get("paper_metric_statuses")
    if not isinstance(metric_statuses, dict):
        fail("Phase 53 comparison paper_metric_statuses must be a mapping")
    if (
        metric_statuses.get("nutation_angle_error", {}).get("status")
        != "paper_figure_digitized_reference_available"
    ):
        fail("Phase 53 comparison nutation metric status changed")
    if comparison_observed.get("missing_paper_metrics") != [
        "nutation_angle_error:paper_figure_digitized_curve_agreement_not_passed"
    ]:
        fail("Phase 53 comparison missing_paper_metrics changed")
    if comparison_observed.get("digitized_figure_reference_available") is not True:
        fail("Phase 53 comparison must record digitized figure availability")
    blockers = comparison_observed.get("blocking_reasons")
    if not isinstance(blockers, list):
        fail("Phase 53 comparison blockers must be a list")
    for blocker in (
        "exact_heavy_top_inertia_unknown",
        "exact_heavy_top_geometry_unknown",
        "raw_heavy_top_reference_curve_data_missing",
        "mabd_newton_report_incomplete",
        "heavy_top_comparison_report_incomplete",
        "heavy_top_timing_evidence_missing",
        "heavy_top_comparison_pass_gate_not_enabled",
        "heavy_top_digitized_figure_curve_agreement_not_passed",
        "sample_time_grid_mismatch",
    ):
        if blocker not in blockers:
            fail(f"Phase 53 comparison blocker missing: {blocker}")
    provenance = comparison_observed.get("input_report_provenance")
    if not isinstance(provenance, dict):
        fail("Phase 53 comparison input_report_provenance must be a mapping")
    expected_provenance = (
        ("paper_figure_curves", figure_path, figure_report),
        ("rbd_rk4_reference", rk4_path, rk4_report),
        ("mabd_newton", mabd_path, mabd_report),
    )
    for lane, path, report in expected_provenance:
        lane_provenance = provenance.get(lane)
        if not isinstance(lane_provenance, dict):
            fail(f"Phase 53 comparison missing {lane} provenance")
        if lane_provenance.get("path") != path:
            fail(f"Phase 53 comparison {lane} provenance path changed")
        if lane_provenance.get("sha256") != sha256_file(ROOT / path):
            fail(f"Phase 53 comparison {lane} provenance sha256 mismatch")
        if lane_provenance.get("source_commit") != report.source_commit:
            fail(f"Phase 53 comparison {lane} provenance source_commit mismatch")
        if lane_provenance.get("status") != report.status.value:
            fail(f"Phase 53 comparison {lane} provenance status mismatch")
    if comparison_report.raw_outputs.get("figure_curve_report") != figure_path:
        fail("Phase 53 comparison raw_outputs missing figure report binding")

    claims = read_yaml(ROOT / "docs/reference/paper-claims.yaml").get("claims")
    if not isinstance(claims, list):
        fail("paper-claims.yaml missing claims list")
    found_heavy_top = False
    for claim in claims:
        if not isinstance(claim, dict):
            continue
        claim_id = str(claim.get("claim_id", ""))
        if claim_id == "experiment.single_body.heavy_top":
            found_heavy_top = True
            if claim.get("reproduction_status") != "intended":
                fail("Phase 53 must keep heavy-top experiment status intended")
            conflict_note = str(claim.get("conflict_note", ""))
            if "raw_heavy_top_reference_curve_data_missing" not in conflict_note:
                fail("Phase 53 heavy-top conflict_note missing raw-data blocker")
        if claim_id.startswith("experiment.") and claim.get("reproduction_status") == "passed":
            fail("Phase 53 must not pass experiment.* claims")
    if not found_heavy_top:
        fail("paper-claims.yaml missing heavy-top claim")


def validate_phase54_record() -> None:
    text = (
        ROOT / "docs/records/2026-05-18-phase54-environment-clone-contract.md"
    ).read_text(encoding="utf-8")
    required_snippets = (
        "## Status\n\npassed_for_environment_clone_contract",
        "phase54-environment-clone-contract",
        "75eb19423f5b7a3be1129bf44341fb19901c4276",
        VENDORED_NEWTON_COMMIT,
        "/cpfs/user/zhuzihou/conda-managed/envs/physics-primitive-newton-py310",
        "/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310",
        "scripts/env/clone_from_reference.py",
        "src/mabd_reproduction/environment_clone.py",
        "tests/test_environment_clone.py",
        "target_exists",
        "ready_to_clone",
        "ready_to_sync_existing",
        "conda create -y -p",
        "rsync -a --delete",
        "mutates_reference_environment=false",
        "uses_reference_python=false",
        "uses_ambient_python=false",
        "No `experiment.*` claim is passed.",
        "does not prove dependency freshness",
        "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_environment_clone tests.test_environment_readiness",
        "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/env/clone_from_reference.py --dry-run",
        "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/env/readiness_check.py",
        "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py",
        "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests",
        "PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c \"import newton; print(newton.__file__)\"",
        "/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .",
        "git diff --check",
    )
    for snippet in required_snippets:
        if snippet not in text:
            fail(f"Phase 54 record missing required evidence field: {snippet}")
    for placeholder in (
        "TO_BE_BACKFILLED_PHASE54",
        "phase54-working-tree",
        "<implementation-commit>",
    ):
        if placeholder in text:
            fail("Phase 54 record contains stale placeholder")

    lower_text = text.lower()
    for snippet in (
        "dependency freshness is verified",
        "solver behavior passed",
        "m-abd method correctness passed",
        "paper experiment reproduction passed",
        "full reproduction complete",
    ):
        if snippet in lower_text:
            fail(f"Phase 54 record overclaims unsupported evidence: {snippet}")

    boundary_text = (ROOT / "docs/reference/claim-boundaries.md").read_text(encoding="utf-8")
    current = claim_boundary_bullet(boundary_text, "This repository contains Phase 54")
    verified = claim_boundary_bullet(boundary_text, "Phase 54 verifies")
    non_claim = claim_boundary_bullet(boundary_text, "Phase 54 does not verify")
    forbidden = claim_boundary_bullet(boundary_text, "Phase 54 environment clone/sync scripting")
    for snippet in ("environment clone/sync contract", "Phase 54 record"):
        if snippet not in current:
            fail(f"Phase 54 current boundary missing: {snippet}")
    for snippet in (
        "scripts/env",
        "conda create -y -p",
        "--sync-existing",
        "rsync -a --delete",
        "aliasing and nesting",
        "mutates_reference_environment=false",
        "uses_reference_python=false",
        "uses_ambient_python=false",
    ):
        if snippet not in verified:
            fail(f"Phase 54 verified boundary missing: {snippet}")
    for snippet in (
        "dependency freshness",
        "solver behavior",
        "M-ABD method correctness",
        "paper experiment reproduction",
        "timing",
        "comparative baselines",
        "full paper reproduction",
        "any passed `experiment.*` claim",
    ):
        if snippet not in non_claim:
            fail(f"Phase 54 non-claim boundary missing: {snippet}")
    for snippet in (
        "dependency freshness evidence",
        "solver behavior evidence",
        "method correctness evidence",
        "paper experiment reproduction",
        "full paper reproduction",
        "any passed `experiment.*` claim",
    ):
        if snippet not in forbidden:
            fail(f"Phase 54 forbidden boundary missing: {snippet}")

    env = os.environ.copy()
    env["PYTHONPATH"] = f"{ROOT / 'src'}:{ROOT / 'vendor/newton'}"
    with tempfile.TemporaryDirectory() as temp_dir:
        base = Path(temp_dir)
        reference = base / "physics-primitive-newton-py310"
        target = base / "mabd-newton-py310"
        conda = base / "miniforge3/bin/conda"
        reference.mkdir()
        conda.parent.mkdir(parents=True)

        clone_result = subprocess.run(
            [
                str(MABD_PYTHON),
                "scripts/env/clone_from_reference.py",
                "--reference-env",
                str(reference),
                "--target-env",
                str(target),
                "--conda",
                str(conda),
                "--dry-run",
            ],
            cwd=ROOT,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if clone_result.returncode != 0:
            fail("Phase 54 clone dry-run failed: " + clone_result.stderr.strip())
        clone_payload = json.loads(clone_result.stdout)
        if clone_payload.get("status") != "ready_to_clone":
            fail("Phase 54 clone dry-run did not report ready_to_clone")
        if clone_payload.get("executed") is not False:
            fail("Phase 54 clone dry-run executed commands")
        if clone_payload.get("non_pollution", {}).get("mutates_reference_environment") is not False:
            fail("Phase 54 clone dry-run mutates reference environment")

        target.mkdir()
        target_exists_result = subprocess.run(
            [
                str(MABD_PYTHON),
                "scripts/env/clone_from_reference.py",
                "--reference-env",
                str(reference),
                "--target-env",
                str(target),
                "--dry-run",
            ],
            cwd=ROOT,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if target_exists_result.returncode != 2:
            fail("Phase 54 existing target dry-run must return 2")
        target_exists_payload = json.loads(target_exists_result.stdout)
        if target_exists_payload.get("status") != "target_exists":
            fail("Phase 54 existing target dry-run did not report target_exists")
        if target_exists_payload.get("can_execute") is not False:
            fail("Phase 54 existing target dry-run must not be executable")

        sync_result = subprocess.run(
            [
                str(MABD_PYTHON),
                "scripts/env/clone_from_reference.py",
                "--reference-env",
                str(reference),
                "--target-env",
                str(target),
                "--sync-existing",
                "--dry-run",
            ],
            cwd=ROOT,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if sync_result.returncode != 0:
            fail("Phase 54 sync dry-run failed: " + sync_result.stderr.strip())
        sync_payload = json.loads(sync_result.stdout)
        if sync_payload.get("status") != "ready_to_sync_existing":
            fail("Phase 54 sync dry-run did not report ready_to_sync_existing")
        if sync_payload.get("executed") is not False:
            fail("Phase 54 sync dry-run executed commands")


def validate_paper_claims() -> None:
    data = read_yaml(ROOT / "docs/reference/paper-claims.yaml")
    paper = data.get("paper")
    claims = data.get("claims")
    if not isinstance(paper, dict):
        fail("paper-claims.yaml missing paper mapping")
    if paper.get("arxiv_id") != "2603.08079":
        fail("paper-claims.yaml arxiv_id must be 2603.08079")
    if paper.get("arxiv_version") != "v2":
        fail("paper-claims.yaml arxiv_version must be v2")
    if not isinstance(claims, list) or len(claims) < 20:
        fail("paper-claims.yaml must contain at least 20 seeded claims")

    seen: set[str] = set()
    required_fields = {
        "claim_id",
        "source_path",
        "source_line",
        "expected_value",
        "unit",
        "conflict_note",
        "reproduction_status",
    }
    for claim in claims:
        if not isinstance(claim, dict):
            fail("each paper claim must be a mapping")
        missing = sorted(required_fields - set(claim))
        if missing:
            fail(f"{claim.get('claim_id', '<unknown>')} missing fields: {', '.join(missing)}")
        claim_id = str(claim["claim_id"])
        if claim_id in seen:
            fail(f"duplicate claim_id {claim_id}")
        seen.add(claim_id)
        status = str(claim["reproduction_status"])
        if status not in STATUS_VALUES:
            fail(f"{claim_id} has invalid reproduction_status {status}")

    for claim_id in (
        "method.single_body.affine_kinematics",
        "method.single_body.corotated_stiffness",
        "method.joints.universal",
        "method.actuation.affine_control_forces",
        "method.force_mapping.point_load_penalty_contact",
        "method.force_mapping.gravity_generalized_force",
        "method.kkt.residual_corrected_rhs",
        "method.topology.chain_block_tridiagonal",
        "method.topology.tree_traversal_dense_dual_oracle",
        "method.topology.loop_schur_complement",
        "method.topology.graph_gauss_seidel",
        "method.topology.graph_classification_reconstruction",
        "method.solver.configured_cpu_step",
        "method.joint_limits.strain_clamp_penalty",
        "experiment.ragdoll_on_net",
        "experiment.robot.franka",
        "experiment.protein_chain",
    ):
        if claim_id not in seen:
            fail(f"paper-claims.yaml missing required claim {claim_id}")

    corotated = next(c for c in claims if c["claim_id"] == "method.single_body.corotated_stiffness")
    if corotated["reproduction_status"] != "passed":
        fail("method.single_body.corotated_stiffness must pass after Phase 5 K_A_bar evidence exists")
    validate_phase9_claim(claims)
    validate_phase10_claim(claims)

    record_text = (
        (ROOT / "docs/records/2026-05-16-phase1-single-body-abd.md").read_text(encoding="utf-8")
        + "\n"
        + (ROOT / "docs/records/2026-05-16-phase2-joints-kkt.md").read_text(encoding="utf-8")
        + "\n"
        + (ROOT / "docs/records/2026-05-16-phase3-topology-solvers.md").read_text(encoding="utf-8")
        + "\n"
        + (ROOT / "docs/records/2026-05-16-phase4-configured-cpu-step.md").read_text(encoding="utf-8")
        + "\n"
        + (ROOT / "docs/records/2026-05-16-phase5-corotated-stiffness.md").read_text(encoding="utf-8")
        + "\n"
        + (ROOT / "docs/records/2026-05-16-phase7-joint-limits.md").read_text(encoding="utf-8")
        + "\n"
        + (ROOT / "docs/records/2026-05-16-phase9-point-contact-forces.md").read_text(encoding="utf-8")
        + "\n"
        + (ROOT / "docs/records/2026-05-16-phase10-actuation-forces.md").read_text(encoding="utf-8")
        + "\n"
        + (ROOT / "docs/records/2026-05-17-phase11-control-row-extraction.md").read_text(encoding="utf-8")
        + "\n"
        + (ROOT / "docs/records/2026-05-17-phase12-single-body-report-lane.md").read_text(encoding="utf-8")
        + "\n"
        + (ROOT / "docs/records/2026-05-17-phase13-configured-spinning-box.md").read_text(encoding="utf-8")
        + "\n"
        + (ROOT / "docs/records/2026-05-17-phase32-gravity-force-mapping.md").read_text(encoding="utf-8")
    )
    for claim in claims:
        if claim["reproduction_status"] == "passed" and str(claim["claim_id"]) not in record_text:
            fail(f"passed claim {claim['claim_id']} is not cited in a phase record")


def validate_experiment_contracts() -> None:
    claims = read_yaml(ROOT / "docs/reference/paper-claims.yaml")["claims"]
    try:
        matrix = load_experiment_matrix(ROOT / "configs/experiments/paper_experiment_matrix.yaml")
        manifest = load_asset_manifest(ROOT / "assets/manifests/paper_asset_sources.yaml")
        validate_experiment_matrix(matrix, claims)
    except ExperimentMatrixError as exc:
        fail(f"experiment matrix validation failed: {exc}")

    asset_ids = {asset.asset_id for asset in manifest.assets}
    missing_assets = sorted(
        {
            asset_id
            for experiment in matrix.experiments
            for asset_id in experiment.asset_ids
            if asset_id not in asset_ids
        }
    )
    if missing_assets:
        fail("experiment matrix references missing assets: " + ", ".join(missing_assets))

    experiment_claims = [claim for claim in claims if str(claim["claim_id"]).startswith("experiment.")]
    passed_experiments = [claim["claim_id"] for claim in experiment_claims if claim["reproduction_status"] == "passed"]
    if passed_experiments:
        fail("Phase 6 must not mark experiment claims passed: " + ", ".join(passed_experiments))

    spinning_box = next(
        experiment
        for experiment in matrix.experiments
        if experiment.claim_id == "experiment.single_body.spinning_box"
    )
    if "rbd_implicit_baseline_adapter_missing" in spinning_box.blocking_reasons:
        fail("Phase 15 spinning-box matrix must not keep stale RBD adapter-missing blocker")
    if "rbd_implicit_baseline_report_incomplete" in spinning_box.blocking_reasons:
        fail("Phase 27 spinning-box matrix must not keep stale incomplete RBD baseline blocker")
    if "mabd_newton_report_incomplete" not in spinning_box.blocking_reasons:
        fail("Phase 27 spinning-box matrix must record incomplete M-ABD lane blocker")
    if "paper_comparison_protocol_not_recorded" in spinning_box.blocking_reasons:
        fail("Phase 16 spinning-box matrix must not keep stale missing-comparison-protocol blocker")
    if "spinning_box_comparison_report_incomplete" not in spinning_box.blocking_reasons:
        fail("Phase 16 spinning-box matrix must record incomplete comparison report blocker")
    heavy_top = next(
        experiment
        for experiment in matrix.experiments
        if experiment.claim_id == "experiment.single_body.heavy_top"
    )
    if "mabd_newton_report_incomplete" not in heavy_top.blocking_reasons:
        fail("Phase 51 heavy-top matrix must record incomplete M-ABD lane blocker")
    if "heavy_top_comparison_report_incomplete" not in heavy_top.blocking_reasons:
        fail("Phase 51 heavy-top matrix must record incomplete comparison report blocker")
    if "mabd_newton_report_missing" in heavy_top.blocking_reasons:
        fail("Phase 51 heavy-top matrix must not keep missing M-ABD lane blocker")
    if "heavy_top_comparison_report_missing" in heavy_top.blocking_reasons:
        fail("Phase 51 heavy-top matrix must not keep missing comparison report blocker")


def validate_phase13_config(
    config_path: str | Path = ROOT / "configs/experiments/single_body_spinning_box.yaml",
    matrix_path: str | Path = ROOT / "configs/experiments/paper_experiment_matrix.yaml",
) -> None:
    try:
        config = load_spinning_box_config(config_path)
        matrix = load_experiment_matrix(matrix_path)
        validate_spinning_box_config_against_matrix(config, matrix)
    except (ExperimentRunConfigError, ExperimentMatrixError) as exc:
        fail(f"Phase 13 config validation failed: {exc}")
    expected_mass_diagonal = spinning_box_mabd_mass_diagonal(config)
    if not np.allclose(config.mass_diagonal, expected_mass_diagonal, rtol=0.0, atol=1.0e-15):
        fail("Phase 18 config validation failed: spinning-box mass_diagonal is not paper-derived")
    if config.contact_surface["type"] != "plane":
        fail("Phase 20 config validation failed: spinning-box contact surface must be a plane")
    if config.contact_surface["plane_normal"] != (0.0, 1.0, 0.0):
        fail("Phase 20 config validation failed: spinning-box contact plane normal changed")
    if config.contact_surface["stiffness"] <= 0.0:
        fail("Phase 20 config validation failed: spinning-box contact stiffness must be positive")
    if not np.isclose(config.initial_q[10], 0.05, rtol=0.0, atol=1.0e-15):
        fail("Phase 21 config validation failed: spinning-box initial translation y must be 0.05m")
    if not np.allclose(config.initial_q[:9], np.eye(3).reshape(9), rtol=0.0, atol=1.0e-15):
        fail("Phase 21 config validation failed: spinning-box affine block must remain identity")
    if not np.allclose(config.initial_q[[9, 11]], [0.0, 0.0], rtol=0.0, atol=1.0e-15):
        fail("Phase 21 config validation failed: spinning-box initial x/z translation must remain zero")
    diagnostics = spinning_box_contact_diagnostics(config, config.initial_q, config.initial_qd)
    if diagnostics.active_contact_count != 0:
        fail("Phase 21 config validation failed: spinning-box initial contacts must be nonpenetrating")
    if not np.isclose(diagnostics.min_signed_distance, 0.0, rtol=0.0, atol=1.0e-15):
        fail("Phase 21 config validation failed: spinning-box minimum signed distance must be zero")
    if not np.isclose(diagnostics.max_penetration_depth, 0.0, rtol=0.0, atol=1.0e-15):
        fail("Phase 21 config validation failed: spinning-box maximum penetration must be zero")
    if not np.allclose(diagnostics.total_normal_force, np.zeros(3), rtol=0.0, atol=1.0e-15):
        fail("Phase 21 config validation failed: spinning-box initial normal force must be zero")
    if not np.allclose(diagnostics.total_generalized_force, np.zeros(12), rtol=0.0, atol=1.0e-15):
        fail("Phase 21 config validation failed: spinning-box initial generalized contact force must be zero")
    if config.paper_horizon.duration_s != 10.0:
        fail("Phase 28 config validation failed: paper_horizon duration must be 10 seconds")
    if config.paper_horizon.time_step_grid_s != (0.01, 0.001):
        fail("Phase 28 config validation failed: paper_horizon step grid must be (0.01, 0.001)")
    if config.paper_horizon.output_report == config.output_report:
        fail("Phase 28 config validation failed: paper_horizon output must not overwrite development report")
    if (
        config.paper_horizon.figure_pdf_sha256
        != "7669b062348324a3b0090cc9f44930655c83233a87f63389db9198b88f95ae80"
    ):
        fail("Phase 28 config validation failed: spinning-box figure checksum changed")


def validate_provenance() -> None:
    text = (ROOT / "vendor/newton/PROVENANCE.md").read_text(encoding="utf-8")
    required_snippets = (
        "https://github.com/newton-physics/newton.git",
        "96713fa965463b69c229a4d30582c733ff3526bb",
        "rsync -a --delete",
        str(MABD_PYTHON),
        "vendor/newton/newton/__init__.py",
        "Local Patch Policy",
    )
    for snippet in required_snippets:
        if snippet not in text:
            fail(f"PROVENANCE.md missing {snippet}")


def validate_newton_import() -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "vendor/newton")
    result = subprocess.run(
        [str(MABD_PYTHON), "-c", "import newton; print(newton.__file__)"],
        cwd=ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        fail("vendored newton import failed: " + result.stderr.strip())
    if "vendor/newton/newton/__init__.py" not in result.stdout.replace("\\", "/"):
        fail("import newton did not resolve to vendor/newton: " + result.stdout.strip())


def main() -> int:
    require_paths()
    validate_environment_contract()
    validate_claim_boundaries()
    validate_phase9_record()
    validate_phase10_record()
    validate_phase11_record()
    validate_phase12_record()
    validate_phase13_record()
    validate_phase14_record()
    validate_phase15_record()
    validate_phase16_record()
    validate_phase17_record()
    validate_phase18_record()
    validate_phase19_record()
    validate_phase20_record()
    validate_phase21_record()
    validate_phase22_record()
    validate_phase23_record()
    validate_phase24_record()
    validate_phase25_record()
    validate_phase26_record()
    validate_phase27_record()
    validate_phase28_record()
    validate_phase29_record()
    validate_phase30_record()
    validate_phase31_record()
    validate_phase32_record()
    validate_phase33_record()
    validate_phase34_record()
    validate_phase35_record()
    validate_phase36_record()
    validate_phase37_record()
    validate_phase38_record()
    validate_phase39_record()
    validate_phase40_record()
    validate_phase41_record()
    validate_phase42_record()
    validate_phase43_record()
    validate_phase44_record()
    validate_phase45_record()
    validate_phase46_record()
    validate_phase47_record()
    validate_phase48_record()
    validate_phase49_record()
    validate_phase50_record()
    validate_phase51_record()
    validate_phase52_record()
    validate_phase53_record()
    validate_phase54_record()
    validate_paper_claims()
    validate_experiment_contracts()
    validate_phase13_config()
    validate_provenance()
    validate_newton_import()
    print(
        "Phase 0/1/2/3/4/5/6/7/8/9/10/11/12/13/14/15/16/17/18/19/20/21/22/23/24/25/26/27/28/29/30/31/32/33/34/35/36/37/38/39/40/41/42/43/44/45/46/47/48/49/50/51/52/53/54 "
        "docs/provenance validation passed"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
