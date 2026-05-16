#!/usr/bin/env python3
"""Validate Phase 0/1/2/3/4/5/6/7/8/9/10/11/12/13 docs, provenance, and claims."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any

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
    "reports/README.md",
    "assets/manifests/README.md",
    "assets/manifests/paper_asset_sources.yaml",
    "configs/experiments/README.md",
    "configs/experiments/paper_experiment_matrix.yaml",
    "configs/experiments/single_body_spinning_box.yaml",
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
        "any passed `experiment.*` claim",
    )
    for snippet in phase13_non_claims:
        if snippet not in normalized_text:
            fail(f"claim-boundaries.md must bound Phase 13 configured-lane evidence: {snippet}")


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
    validate_paper_claims()
    validate_experiment_contracts()
    validate_phase13_config()
    validate_provenance()
    validate_newton_import()
    print("Phase 0/1/2/3/4/5/6/7/8/9/10/11/12/13 docs/provenance validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
