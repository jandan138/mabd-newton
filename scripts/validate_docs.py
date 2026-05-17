#!/usr/bin/env python3
"""Validate Phase 0/1/2/3/4/5/6/7/8/9/10/11/12/13/14/15/16/17/18/19 docs."""

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
from mabd_reproduction.spinning_box_physics import spinning_box_mabd_mass_diagonal


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
        "## Artifacts",
        "`src/mabd_reproduction/comparison_reports.py`",
        "generated reports: not committed",
        "No `experiment.*` claim is passed in this phase.",
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
    validate_paper_claims()
    validate_experiment_contracts()
    validate_phase13_config()
    validate_provenance()
    validate_newton_import()
    print(
        "Phase 0/1/2/3/4/5/6/7/8/9/10/11/12/13/14/15/16/17/18/19 "
        "docs/provenance validation passed"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
