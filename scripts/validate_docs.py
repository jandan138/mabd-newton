#!/usr/bin/env python3
"""Validate Phase 0/1/2/3/4/5/6/7/8/9/10/11/12/13/14/15/16/17/18/19/20/21/22/23/24/25 docs."""

from __future__ import annotations

import os
import subprocess
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
    load_spinning_box_config,
    validate_spinning_box_config_against_matrix,
)
from mabd_reproduction.spinning_box_physics import (
    spinning_box_contact_diagnostics,
    spinning_box_mabd_mass_diagonal,
)


ROOT = Path(__file__).resolve().parents[1]
MABD_PYTHON = Path("/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python")
REQUIRED_PATHS = (
    "AGENTS.md",
    "LICENSE.md",
    "pyproject.toml",
    "docs/operations/environment.md",
    "docs/reference/claim-boundaries.md",
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
    "reports/README.md",
    "assets/manifests/README.md",
    "assets/manifests/paper_asset_sources.yaml",
    "configs/experiments/README.md",
    "configs/experiments/paper_experiment_matrix.yaml",
    "configs/experiments/single_body_spinning_box.yaml",
    "scripts/run_experiment.py",
    "scripts/env/readiness_check.py",
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


def fail(message: str) -> None:
    raise SystemExit(f"validate_docs.py: {message}")


def read_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        fail(f"{path} must contain a YAML mapping")
    return data


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
    ):
        if snippet not in text:
            fail(f"environment.md missing {snippet}")


def validate_claim_boundaries() -> None:
    text = (ROOT / "docs/reference/claim-boundaries.md").read_text(encoding="utf-8")
    normalized_text = " ".join(text.split())
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
        "docs/record creation commit:",
        "TO_BE_BACKFILLED_PHASE25_DOCS_COMMIT",
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
        "CPU oracle tests: Ran 12 tests, OK",
        "vendored CPU oracle tests: Ran 6 tests, OK",
        "M-ABD report tests: Ran 2 tests, OK",
        "comparison and runner tests: Ran 21 tests, OK",
        "phase bootstrap docs tests:",
        (
            "docs validator: Phase "
            "0/1/2/3/4/5/6/7/8/9/10/11/12/13/14/15/16/17/18/19/20/21/22/23/24/25 "
            "docs/provenance validation passed"
        ),
    )
    for snippet in required_snippets:
        if snippet not in text:
            fail(f"Phase 25 record missing required evidence field: {snippet}")
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
    if "rbd_implicit_baseline_report_incomplete" not in spinning_box.blocking_reasons:
        fail("Phase 15 spinning-box matrix must record incomplete RBD baseline report blocker")
    if "paper_comparison_protocol_not_recorded" in spinning_box.blocking_reasons:
        fail("Phase 16 spinning-box matrix must not keep stale missing-comparison-protocol blocker")
    if "spinning_box_comparison_report_incomplete" not in spinning_box.blocking_reasons:
        fail("Phase 16 spinning-box matrix must record incomplete comparison report blocker")


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
    validate_paper_claims()
    validate_experiment_contracts()
    validate_phase13_config()
    validate_provenance()
    validate_newton_import()
    print(
        "Phase 0/1/2/3/4/5/6/7/8/9/10/11/12/13/14/15/16/17/18/19/20/21/22/23/24/25 "
        "docs/provenance validation passed"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
