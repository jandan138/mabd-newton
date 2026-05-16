#!/usr/bin/env python3
"""Validate Phase 0/1/2/3/4/5/6/7 documentation, provenance, and claim manifests."""

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
    "reports/README.md",
    "assets/manifests/README.md",
    "assets/manifests/paper_asset_sources.yaml",
    "configs/experiments/README.md",
    "configs/experiments/paper_experiment_matrix.yaml",
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
    ):
        if snippet not in text:
            fail(f"environment.md missing {snippet}")


def validate_claim_boundaries() -> None:
    text = (ROOT / "docs/reference/claim-boundaries.md").read_text(encoding="utf-8")
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
    validate_paper_claims()
    validate_experiment_contracts()
    validate_provenance()
    validate_newton_import()
    print("Phase 0/1/2/3/4/5/6/7 docs/provenance validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
