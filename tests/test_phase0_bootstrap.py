from __future__ import annotations

import os
import math
import subprocess
import sys
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import yaml

from mabd_reproduction.reporting import EvidenceStatus, REQUIRED_REPORT_KEYS, load_claim_report


ROOT = Path(__file__).resolve().parents[1]
PHYSICAL_PENDULUM_TIMING_SOURCE_LINES = [
    "/tmp/mabd-paper/source/sections/experiment.tex:77-91"
]


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
        raise AssertionError(f"missing claim boundary bullet: {starts_with}")
    return " ".join(parts)


class Phase0BootstrapTests(unittest.TestCase):
    def assert_physical_pendulum_timing_source_audit(self, payload: dict[str, object]) -> None:
        self.assertEqual(payload["source_lines"], PHYSICAL_PENDULUM_TIMING_SOURCE_LINES)
        self.assertEqual(payload["status"], "not_a_physical_pendulum_paper_metric")
        self.assertFalse(payload["runtime_timing_claim_present"])
        self.assertFalse(payload["required_metric"])

    def test_report_status_vocabulary_matches_spec(self) -> None:
        self.assertEqual(
            {status.value for status in EvidenceStatus},
            {
                "passed",
                "failed",
                "incomplete",
                "not_verified",
                "unsupported",
                "qualitative_reconstruction",
            },
        )
        self.assertIn("claim_id", REQUIRED_REPORT_KEYS)
        self.assertIn("vendored_newton_commit", REQUIRED_REPORT_KEYS)

    def test_claim_manifest_has_required_source_material(self) -> None:
        data = yaml.safe_load((ROOT / "docs/reference/paper-claims.yaml").read_text())
        self.assertEqual(data["paper"]["arxiv_id"], "2603.08079")
        self.assertEqual(data["paper"]["arxiv_version"], "v2")
        self.assertGreaterEqual(len(data["claims"]), 20)
        claim_ids = {claim["claim_id"] for claim in data["claims"]}
        self.assertIn("method.joints.universal", claim_ids)
        self.assertIn("experiment.ragdoll_on_net", claim_ids)
        universal = next(c for c in data["claims"] if c["claim_id"] == "method.joints.universal")
        self.assertIn("inconsistent", universal["conflict_note"])
        corotated = next(c for c in data["claims"] if c["claim_id"] == "method.single_body.corotated_stiffness")
        self.assertEqual(corotated["reproduction_status"], "passed")
        ball = next(c for c in data["claims"] if c["claim_id"] == "method.joints.ball")
        universal = next(c for c in data["claims"] if c["claim_id"] == "method.joints.universal")
        kkt = next(c for c in data["claims"] if c["claim_id"] == "method.kkt.residual_corrected_rhs")
        control = next(c for c in data["claims"] if c["claim_id"] == "method.actuation.affine_control_forces")
        gravity = next(c for c in data["claims"] if c["claim_id"] == "method.force_mapping.gravity_generalized_force")
        self.assertEqual(ball["reproduction_status"], "passed")
        self.assertEqual(universal["reproduction_status"], "passed")
        self.assertEqual(kkt["reproduction_status"], "passed")
        self.assertEqual(control["reproduction_status"], "passed")
        self.assertEqual(gravity["reproduction_status"], "passed")
        self.assertIn("J_i^T m_i g", gravity["expected_value"])
        self.assertIn("singleabd.tex:23-26,42,55-58", gravity["source_line"])
        self.assertIn("solver.tex:238-242", gravity["source_line"])
        self.assertNotIn("experiment.tex:67-75", gravity["source_line"])
        self.assertNotIn("experiment.tex:80-91", gravity["source_line"])
        self.assertIn("not heavy-top", gravity["conflict_note"])

    def test_claim_boundaries_refuse_method_claims_at_phase0(self) -> None:
        text = (ROOT / "docs/reference/claim-boundaries.md").read_text()
        self.assertIn("## Current", text)
        self.assertIn("## Intended", text)
        self.assertIn("## Verified", text)
        self.assertIn("No method-level M-ABD result is verified at Phase 0.", text)
        self.assertIn("Phase 2 verifies control tetrahedron", text)
        self.assertIn("skew-symmetrized joint-gradient", text)
        self.assertIn("performance path", text)

    def test_phase3_topology_claims_are_in_manifest_and_records(self) -> None:
        data = yaml.safe_load((ROOT / "docs/reference/paper-claims.yaml").read_text())
        claims = {claim["claim_id"]: claim for claim in data["claims"]}
        for claim_id in (
            "method.topology.chain_block_tridiagonal",
            "method.topology.tree_traversal_dense_dual_oracle",
            "method.topology.loop_schur_complement",
            "method.topology.graph_gauss_seidel",
            "method.topology.graph_classification_reconstruction",
        ):
            self.assertIn(claim_id, claims)
            self.assertEqual(claims[claim_id]["reproduction_status"], "passed")

        text = (ROOT / "docs/reference/claim-boundaries.md").read_text()
        self.assertIn("Phase 3 verifies chain block-tridiagonal", text)
        self.assertIn("tree parent/postorder", text)
        self.assertIn("traversal metadata", text)
        self.assertIn("paper tree elimination", text)
        self.assertIn("loop Schur complement", text)
        self.assertIn("graph Gauss-Seidel", text)
        self.assertIn("Phase 3 does not verify `SolverMABD.step()`", text)

    def test_phase4_configured_step_claim_is_in_manifest_and_records(self) -> None:
        data = yaml.safe_load((ROOT / "docs/reference/paper-claims.yaml").read_text())
        claims = {claim["claim_id"]: claim for claim in data["claims"]}
        claim = claims["method.solver.configured_cpu_step"]

        self.assertEqual(claim["reproduction_status"], "passed")
        self.assertIn("configured CPU", claim["expected_value"])
        self.assertIn("not an unconfigured production step", claim["conflict_note"])

        text = (ROOT / "docs/reference/claim-boundaries.md").read_text()
        self.assertIn("Phase 4 verifies explicitly configured CPU oracle", text)
        self.assertIn("unconfigured production `SolverMABD.step()`", text)
        self.assertIn("Warp kernels", text)

    def test_phase5_corotated_stiffness_claim_is_in_manifest_and_records(self) -> None:
        data = yaml.safe_load((ROOT / "docs/reference/paper-claims.yaml").read_text())
        claims = {claim["claim_id"]: claim for claim in data["claims"]}
        claim = claims["method.single_body.corotated_stiffness"]

        self.assertEqual(claim["reproduction_status"], "passed")
        self.assertIn("K_A_bar", claim["expected_value"])

        text = (ROOT / "docs/reference/claim-boundaries.md").read_text()
        self.assertIn("Phase 5 verifies linear-elastic rest generalized stiffness", text)
        self.assertIn("co-rotated affine elastic force", text)
        self.assertIn("Phase 5 does not verify unconfigured production `SolverMABD.step()`", text)

    def test_phase6_experiment_matrix_keeps_scene_claims_unpassed(self) -> None:
        data = yaml.safe_load((ROOT / "docs/reference/paper-claims.yaml").read_text())
        experiment_claims = [
            claim for claim in data["claims"] if str(claim["claim_id"]).startswith("experiment.")
        ]

        self.assertGreaterEqual(len(experiment_claims), 15)
        self.assertNotIn("passed", {claim["reproduction_status"] for claim in experiment_claims})

        text = (ROOT / "docs/reference/claim-boundaries.md").read_text()
        self.assertIn("Phase 6 verifies only that every `experiment.*` paper claim", text)
        self.assertIn("does not verify any scene dynamics", text)
        self.assertIn("external baseline run", text)

    def test_phase7_joint_limit_claim_is_in_manifest_and_records(self) -> None:
        data = yaml.safe_load((ROOT / "docs/reference/paper-claims.yaml").read_text())
        claims = {claim["claim_id"]: claim for claim in data["claims"]}
        claim = claims["method.joint_limits.strain_clamp_penalty"]

        self.assertEqual(claim["reproduction_status"], "passed")
        self.assertIn("theta clamp", claim["expected_value"])
        self.assertIn("not a generic inequality-constrained KKT solver", claim["conflict_note"])

        text = (ROOT / "docs/reference/claim-boundaries.md").read_text()
        self.assertIn("Phase 7 verifies scalar joint-limit strain clamping", text)
        self.assertIn("generic inequality-constrained M-ABD KKT", text)
        self.assertIn("joint-limit parameter extraction from scenes", text)

    def test_phase8_environment_readiness_is_bounded(self) -> None:
        text = (ROOT / "docs/reference/claim-boundaries.md").read_text()
        self.assertIn("Phase 8 verifies the cloned M-ABD Newton environment contract", text)
        self.assertIn("vendored Newton import resolution", text)
        self.assertIn("Phase 8 does not verify solver behavior", text)
        self.assertIn("paper experiments", text)

        environment_text = (ROOT / "docs/operations/environment.md").read_text()
        self.assertIn("scripts/env/readiness_check.py", environment_text)
        self.assertIn("reports/generated/environment-readiness/local/readiness.json", environment_text)
        self.assertIn("smoke_passed", environment_text)

    def test_phase54_environment_clone_contract_is_bounded(self) -> None:
        text = (ROOT / "docs/reference/claim-boundaries.md").read_text()
        current = claim_boundary_bullet(text, "This repository contains Phase 54")
        verified = claim_boundary_bullet(text, "Phase 54 verifies")
        non_claim = claim_boundary_bullet(text, "Phase 54 does not verify")
        forbidden = claim_boundary_bullet(text, "Phase 54 environment clone/sync scripting")

        self.assertIn("environment clone/sync contract", current)
        self.assertIn("scripts/env", verified)
        self.assertIn("conda create -y -p", verified)
        self.assertIn("--sync-existing", verified)
        self.assertIn("mutates_reference_environment=false", verified)
        self.assertIn("solver behavior", non_claim)
        self.assertIn("paper experiment reproduction", non_claim)
        self.assertIn("full paper reproduction", forbidden)

        environment_text = (ROOT / "docs/operations/environment.md").read_text()
        self.assertIn("scripts/env/clone_from_reference.py --dry-run", environment_text)
        self.assertIn("target_exists", environment_text)
        self.assertIn("ready_to_clone", environment_text)
        self.assertIn("rsync -a --delete", environment_text)

        record_text = (
            ROOT / "docs/records/2026-05-18-phase54-environment-clone-contract.md"
        ).read_text()
        for snippet in (
            "passed_for_environment_clone_contract",
            "scripts/env/clone_from_reference.py",
            "src/mabd_reproduction/environment_clone.py",
            "tests/test_environment_clone.py",
            "target_exists",
            "ready_to_clone",
            "ready_to_sync_existing",
            "mutates_reference_environment=false",
            "No `experiment.*` claim is passed.",
        ):
            self.assertIn(snippet, record_text)

    def test_phase9_point_contact_force_claim_is_bounded(self) -> None:
        data = yaml.safe_load((ROOT / "docs/reference/paper-claims.yaml").read_text())
        claims = {claim["claim_id"]: claim for claim in data["claims"]}
        claim = claims["method.force_mapping.point_load_penalty_contact"]

        self.assertEqual(claim["reproduction_status"], "passed")
        self.assertIn("point load J^T f", claim["expected_value"])
        self.assertIn("not collision detection", claim["conflict_note"])

        text = (ROOT / "docs/reference/claim-boundaries.md").read_text()
        normalized_text = " ".join(text.split())
        self.assertIn("Phase 9 verifies point-load affine generalized force mapping", text)
        self.assertIn("inward-only contact damping", normalized_text)
        self.assertIn("Phase 9 does not verify collision detection", text)
        self.assertIn("full contact handling", text)

    def test_phase9_point_contact_record_has_required_evidence_fields(self) -> None:
        text = (ROOT / "docs/records/2026-05-16-phase9-point-contact-forces.md").read_text()

        for snippet in (
            "## Status",
            "passed",
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
        ):
            self.assertIn(snippet, text)

    def test_phase10_actuation_force_claim_is_bounded(self) -> None:
        data = yaml.safe_load((ROOT / "docs/reference/paper-claims.yaml").read_text())
        claims = {claim["claim_id"]: claim for claim in data["claims"]}
        claim = claims["method.actuation.affine_control_forces"]

        self.assertEqual(claim["reproduction_status"], "passed")
        self.assertIn("feedforward controls", claim["expected_value"])
        self.assertIn("not Newton Control object ingestion", claim["conflict_note"])

        text = (ROOT / "docs/reference/claim-boundaries.md").read_text()
        normalized_text = " ".join(text.split())
        self.assertIn("Phase 10 verifies scene-script affine target", text)
        self.assertIn("mabd:control", text)
        self.assertIn("Phase 10 does not verify Newton `Control` object ingestion", text)
        self.assertIn("Franka pick-and-place", normalized_text)
        self.assertIn("closed-loop controllers", normalized_text)

    def test_phase10_actuation_force_record_has_required_evidence_fields(self) -> None:
        text = (ROOT / "docs/records/2026-05-16-phase10-actuation-forces.md").read_text()

        for snippet in (
            "## Status",
            "passed",
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
        ):
            self.assertIn(snippet, text)

    def test_phase11_control_row_extraction_is_bounded(self) -> None:
        text = (ROOT / "docs/reference/claim-boundaries.md").read_text()
        normalized_text = " ".join(text.split())

        self.assertIn("Phase 11 verifies extraction of enabled Newton `mabd:control` model rows", text)
        self.assertIn("disabled-row filtering", normalized_text)
        self.assertIn("bad body-reference validation", normalized_text)
        self.assertIn("Phase 11 does not verify Newton `Control` object ingestion", text)
        self.assertIn("time-varying controller updates", normalized_text)
        self.assertIn("Franka pick-and-place", normalized_text)

    def test_phase11_control_row_extraction_record_has_required_evidence_fields(self) -> None:
        text = (ROOT / "docs/records/2026-05-17-phase11-control-row-extraction.md").read_text()

        for snippet in (
            "## Status",
            "passed",
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
        ):
            self.assertIn(snippet, text)

    def test_phase12_single_body_report_lane_is_bounded(self) -> None:
        text = (ROOT / "docs/reference/claim-boundaries.md").read_text()
        normalized_text = " ".join(text.split())

        self.assertIn("Phase 12 verifies full-schema `ClaimReport` JSON round trips", text)
        self.assertIn("single-body spinning-box M-ABD development report", normalized_text)
        self.assertIn("remains `incomplete`", normalized_text)
        self.assertIn("Phase 12 does not verify the paper spinning-box experiment", text)
        self.assertIn("RK4/RBD/analytic baselines", normalized_text)
        self.assertIn("any passed `experiment.*` claim", normalized_text)

    def test_phase12_single_body_report_lane_record_has_required_evidence_fields(self) -> None:
        text = (ROOT / "docs/records/2026-05-17-phase12-single-body-report-lane.md").read_text()

        for snippet in (
            "## Status",
            "passed",
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
        ):
            self.assertIn(snippet, text)

    def test_phase13_configured_spinning_box_lane_is_bounded(self) -> None:
        text = (ROOT / "docs/reference/claim-boundaries.md").read_text()
        normalized_text = " ".join(text.split())

        self.assertIn("Phase 13 verifies a config-driven single-body spinning-box", text)
        self.assertIn("per-scene config schema", normalized_text)
        self.assertIn("report remains `incomplete`", normalized_text)
        self.assertIn("Phase 13 does not verify the paper spinning-box experiment", text)
        self.assertIn("RBD baselines", normalized_text)
        self.assertIn("any passed `experiment.*` claim", normalized_text)

    def test_phase13_record_has_required_evidence_fields(self) -> None:
        text = (ROOT / "docs/records/2026-05-17-phase13-configured-spinning-box.md").read_text()

        for snippet in (
            "## Status",
            "passed",
            "## Config Path",
            "configs/experiments/single_body_spinning_box.yaml",
            "## Repository",
            "plan commit:",
            "implementation commits:",
            "docs/provenance commit:",
            "verification evidence commit:",
            "review hardening commit:",
            "## Vendored Newton",
            "96713fa965463b69c229a4d30582c733ff3526bb",
            "## Paper Source",
            "PDF SHA256:",
            "TeX source SHA256:",
            "experiment.tex:40-55",
            "## Metrics And Thresholds",
            "Report validation rejects `status=passed`",
            "No `experiment.*` claim is passed in this phase.",
        ):
            self.assertIn(snippet, text)

    def test_phase14_experiment_runner_lane_is_bounded(self) -> None:
        text = (ROOT / "docs/reference/claim-boundaries.md").read_text()
        normalized_text = " ".join(text.split())

        self.assertIn("Phase 14 verifies an executable config-driven experiment runner", text)
        self.assertIn("single-body spinning-box development report", normalized_text)
        self.assertIn("Phase 14 does not verify the paper spinning-box experiment", text)
        self.assertIn("generated report artifacts as committed evidence", normalized_text)
        self.assertIn("any passed `experiment.*` claim", normalized_text)

    def test_phase14_record_has_required_evidence_fields(self) -> None:
        text = (ROOT / "docs/records/2026-05-17-phase14-experiment-runner.md").read_text()

        for snippet in (
            "## Status",
            "passed",
            "## Config Path",
            "configs/experiments/single_body_spinning_box.yaml",
            "## Repository",
            "plan commit:",
            "implementation commits:",
            "verification evidence commit:",
            "review hardening commit:",
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
        ):
            self.assertIn(snippet, text)

    def test_phase15_rbd_baseline_lane_is_bounded(self) -> None:
        text = (ROOT / "docs/reference/claim-boundaries.md").read_text()
        normalized_text = " ".join(text.split())

        self.assertIn("Phase 15 verifies a Newton `SolverSemiImplicit` CPU free-rigid", text)
        self.assertIn("deterministic cube mass and inertia", normalized_text)
        self.assertIn("--lane rbd_implicit_baseline", normalized_text)
        self.assertIn("Phase 15 does not verify the paper spinning-box experiment", text)
        self.assertIn("paper-faithful implicit RBD baseline", normalized_text)
        self.assertIn("paper-faithful affine collision", normalized_text)
        self.assertIn("any passed `experiment.*` claim", normalized_text)

    def test_phase15_record_has_required_evidence_fields(self) -> None:
        text = (ROOT / "docs/records/2026-05-17-phase15-rbd-baseline-lane.md").read_text()

        for snippet in (
            "## Status",
            "passed",
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
        ):
            self.assertIn(snippet, text)

    def test_phase16_spinning_box_comparison_protocol_is_bounded(self) -> None:
        text = (ROOT / "docs/reference/claim-boundaries.md").read_text()
        normalized_text = " ".join(text.split())

        self.assertIn("Phase 16 verifies a machine-checkable spinning-box comparison protocol", text)
        self.assertIn("spinning_box_comparison_protocol", normalized_text)
        self.assertIn("mabd_newton", normalized_text)
        self.assertIn("rbd_implicit_baseline", normalized_text)
        self.assertIn("Phase 16 does not verify the paper spinning-box experiment", text)
        self.assertIn("paper-faithful implicit RBD baseline", normalized_text)
        self.assertIn("paper timing", normalized_text)
        self.assertIn("any passed `experiment.*` claim", normalized_text)

    def test_phase16_record_has_required_evidence_fields(self) -> None:
        text = (
            ROOT / "docs/records/2026-05-17-phase16-spinning-box-comparison-protocol.md"
        ).read_text()

        for snippet in (
            "## Status",
            "passed",
            "## Config Path",
            "configs/experiments/single_body_spinning_box.yaml",
            "configs/experiments/paper_experiment_matrix.yaml",
            "## Repository",
            "plan commit:",
            "implementation commits:",
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
        ):
            self.assertIn(snippet, text)

    def test_phase17_spinning_box_mabd_paper_metrics_are_bounded(self) -> None:
        text = (ROOT / "docs/reference/claim-boundaries.md").read_text()
        normalized_text = " ".join(text.split())

        self.assertIn("Phase 17 verifies paper-value momentum metric reporting", text)
        self.assertIn("M-ABD spinning-box development lane", normalized_text)
        self.assertIn("paper p0/L0", normalized_text)
        self.assertIn("Phase 17 does not verify the paper spinning-box experiment", text)
        self.assertIn("paper-faithful implicit RBD baseline", normalized_text)
        self.assertIn("paper timing", normalized_text)
        self.assertIn("any passed `experiment.*` claim", normalized_text)

    def test_phase17_record_has_required_evidence_fields(self) -> None:
        text = (
            ROOT / "docs/records/2026-05-17-phase17-spinning-box-mabd-paper-metrics.md"
        ).read_text()

        for snippet in (
            "## Status",
            "passed",
            "## Config Path",
            "configs/experiments/single_body_spinning_box.yaml",
            "## Repository",
            "plan commit:",
            "implementation commits:",
            "docs/provenance commit: `d25e3bd3b7b60655285d3d077e600c438737cd48`",
            "## Paper Source",
            "experiment.tex:40-55",
            "## Environment",
            "mabd-newton-py310",
            "## Metrics And Thresholds",
            "paper_spatial_twist",
            "linear_momentum_error",
            "angular_momentum_error",
            "spinning_box_comparison_report_incomplete",
            "## Artifacts",
            "`src/mabd_reproduction/spinning_box_physics.py`",
            "`write_spinning_box_development_report`",
            "No `experiment.*` claim is passed in this phase.",
        ):
            self.assertIn(snippet, text)

    def test_phase18_spinning_box_mabd_physical_mass_is_bounded(self) -> None:
        text = (ROOT / "docs/reference/claim-boundaries.md").read_text()
        normalized_text = " ".join(text.split())

        self.assertIn("Phase 18 verifies physical affine mass-diagonal reporting", text)
        self.assertIn("paper uniform centered cube", normalized_text)
        self.assertIn("m*s^2/12", normalized_text)
        self.assertIn("relative_energy_drift", text)
        self.assertIn("Phase 18 does not verify the paper spinning-box experiment", text)
        self.assertIn("paper-faithful implicit RBD baseline", text)
        self.assertIn("any passed `experiment.*` claim", text)

    def test_phase18_record_has_required_evidence_fields(self) -> None:
        text = (
            ROOT / "docs/records/2026-05-17-phase18-spinning-box-mabd-physical-mass.md"
        ).read_text()

        for snippet in (
            "## Status\n\npassed",
            "## Config Path",
            "configs/experiments/single_body_spinning_box.yaml",
            "## Repository",
            "plan commit:",
            "implementation commit:",
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
        ):
            self.assertIn(snippet, text)

    def test_phase19_spinning_box_comparison_finite_metrics_is_bounded(self) -> None:
        text = (ROOT / "docs/reference/claim-boundaries.md").read_text()
        normalized_text = " ".join(text.split())

        self.assertIn("Phase 19 verifies finite required-metric validation", text)
        self.assertIn("invalid_required_metrics", normalized_text)
        self.assertIn("lane_metric_differences", normalized_text)
        self.assertIn("Phase 19 does not verify the paper spinning-box experiment", text)
        self.assertIn("paper-faithful implicit RBD baseline", text)
        self.assertIn("any passed `experiment.*` claim", text)

    def test_phase19_record_has_required_evidence_fields(self) -> None:
        text = (
            ROOT / "docs/records/2026-05-17-phase19-spinning-box-comparison-finite-metrics.md"
        ).read_text()

        for snippet in (
            "## Status\n\npassed",
            "## Config Path",
            "configs/experiments/single_body_spinning_box.yaml",
            "## Repository",
            "plan commit:",
            "implementation commit:",
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
        ):
            self.assertIn(snippet, text)

    def test_phase20_spinning_box_contact_diagnostics_is_bounded(self) -> None:
        text = (ROOT / "docs/reference/claim-boundaries.md").read_text()
        verified = claim_boundary_bullet(text, "Phase 20 verifies")
        non_claim = claim_boundary_bullet(text, "Phase 20 does not verify")

        self.assertIn("Phase 20 verifies procedural spinning-box cube corner derivation", verified)
        self.assertIn("configured frictionless plane metadata", verified)
        self.assertIn("point-plane normal penalty contact diagnostics", verified)
        self.assertIn("finite contact diagnostic fields", verified)
        self.assertIn("the paper spinning-box experiment", non_claim)
        self.assertIn("collision detection", non_claim)
        self.assertIn("implicit contact solve", non_claim)
        self.assertIn("any passed `experiment.*` claim", non_claim)

    def test_phase20_record_has_required_evidence_fields(self) -> None:
        text = (
            ROOT / "docs/records/2026-05-17-phase20-spinning-box-contact-diagnostics.md"
        ).read_text()

        for snippet in (
            "## Status\n\npassed",
            "## Config Path",
            "configs/experiments/single_body_spinning_box.yaml",
            "## Repository",
            "plan commit:",
            "config commit:",
            "implementation commit:",
            "report commit:",
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
        ):
            self.assertIn(snippet, text)

    def test_phase21_spinning_box_plane_placement_is_bounded(self) -> None:
        text = (ROOT / "docs/reference/claim-boundaries.md").read_text()
        current = claim_boundary_bullet(text, "This repository contains Phase 21")
        verified = claim_boundary_bullet(text, "Phase 21 verifies")
        non_claim = claim_boundary_bullet(text, "Phase 21 does not verify")

        self.assertIn("spinning-box plane-aligned initial placement", current)
        self.assertIn("configured spinning-box resting pose", verified)
        self.assertIn("cube side length 0.1m", verified)
        self.assertIn("initial translation y=0.05m", verified)
        self.assertIn("zero initial penetration", verified)
        self.assertIn("zero point-plane penalty contact force fields", verified)
        self.assertIn("the paper spinning-box experiment", non_claim)
        self.assertIn("collision detection", non_claim)
        self.assertIn("implicit contact solve", non_claim)
        self.assertIn("any passed `experiment.*` claim", non_claim)

    def test_phase21_record_has_required_evidence_fields(self) -> None:
        text = (
            ROOT / "docs/records/2026-05-17-phase21-spinning-box-plane-placement.md"
        ).read_text()

        for snippet in (
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
            "generated reports: not committed",
            "No `experiment.*` claim is passed in this phase.",
            "config/report tests: Ran 10 tests, OK",
        ):
            self.assertIn(snippet, text)

    def test_phase22_rbd_plane_placement_is_bounded(self) -> None:
        text = (ROOT / "docs/reference/claim-boundaries.md").read_text()
        current = claim_boundary_bullet(text, "This repository contains Phase 22")
        verified = claim_boundary_bullet(text, "Phase 22 verifies")
        non_claim = claim_boundary_bullet(text, "Phase 22 does not verify")

        self.assertIn("RBD development baseline configured initial placement", current)
        self.assertIn("RBD development baseline consumes the configured spinning-box", verified)
        self.assertIn("initial_position_m = [0.0, 0.05, 0.0]", verified)
        self.assertIn("final_position_m = [4.0, 0.05, 0.0]", verified)
        self.assertIn("report propagation for the RBD lane", verified)
        self.assertIn("the paper spinning-box experiment", non_claim)
        self.assertIn("paper-faithful implicit RBD baseline", non_claim)
        self.assertIn("paper-faithful affine collision", non_claim)
        self.assertIn("any passed `experiment.*` claim", non_claim)

    def test_phase22_record_has_required_evidence_fields(self) -> None:
        text = (
            ROOT / "docs/records/2026-05-17-phase22-rbd-plane-placement.md"
        ).read_text()

        for snippet in (
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
            "## Metrics And Thresholds",
            "initial_position_m = [0.0, 0.05, 0.0]",
            "final_position_m = [4.0, 0.05, 0.0]",
            "newton_semimplicit_rbd_cpu_development",
            "newton.solvers.SolverSemiImplicit",
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
        ):
            self.assertIn(snippet, text)

    def test_phase23_spinning_box_position_comparison_is_bounded(self) -> None:
        text = (ROOT / "docs/reference/claim-boundaries.md").read_text()
        current = claim_boundary_bullet(text, "This repository contains Phase 23")
        verified = claim_boundary_bullet(text, "Phase 23 verifies")
        non_claim = claim_boundary_bullet(text, "Phase 23 does not verify")

        self.assertIn("spinning-box position comparison metrics", current)
        self.assertIn("initial_position_m", verified)
        self.assertIn("final_position_m", verified)
        self.assertIn("lane_vector_metrics", verified)
        self.assertIn("lane_vector_metric_differences", verified)
        self.assertIn("finite length-three vector validation", verified)
        self.assertIn("the paper spinning-box experiment", non_claim)
        self.assertIn("paper-faithful implicit RBD baseline", non_claim)
        self.assertIn("paper-faithful affine collision", non_claim)
        self.assertIn("paper timing", non_claim)
        self.assertIn("paper trajectory agreement", non_claim)
        self.assertIn("any passed `experiment.*` claim", non_claim)

    def test_phase23_record_has_required_evidence_fields(self) -> None:
        text = (
            ROOT
            / "docs/records/2026-05-17-phase23-spinning-box-position-comparison.md"
        ).read_text()

        for snippet in (
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
            "mutates_reference_environment=false",
            "uses_reference_python=false",
            "uses_ambient_python=false",
            "## Metrics And Thresholds",
            "initial_position_m = [0.0, 0.05, 0.0]",
            "final_position_m = [4.0, 0.05, 0.0]",
            "lane_vector_metrics",
            "lane_vector_metric_differences",
            "invalid_required_vector_metrics",
            "mabd_newton:final_position_m_invalid",
            "spinning_box_comparison_report_incomplete",
            "## Artifacts",
            "`src/mabd_reproduction/single_body_reports.py`",
            "`src/mabd_reproduction/comparison_reports.py`",
            "generated reports: not committed",
            "No `experiment.*` claim is passed in this phase.",
            "M-ABD report tests: Ran 2 tests, OK",
            "comparison tests: Ran 5 tests, OK",
            "AssertionError: 'Infinity' unexpectedly found",
        ):
            self.assertIn(snippet, text)

    def test_phase24_spinning_box_trajectory_shape_diagnostics_is_bounded(self) -> None:
        text = (ROOT / "docs/reference/claim-boundaries.md").read_text()
        current = claim_boundary_bullet(text, "This repository contains Phase 24")
        verified = claim_boundary_bullet(text, "Phase 24 verifies")
        non_claim = claim_boundary_bullet(text, "Phase 24 does not verify")

        self.assertIn("trajectory samples", current)
        self.assertIn("affine shape diagnostics", current)
        self.assertIn("trajectory_samples", verified)
        self.assertIn("affine_orthogonality_error", verified)
        self.assertIn("affine_shape_diagnostic_status", verified)
        self.assertIn("development_gap_observed", verified)
        self.assertIn("RBD `rotation_xyzw`", verified)
        self.assertIn("the paper spinning-box experiment", non_claim)
        self.assertIn("paper-faithful implicit RBD baseline", non_claim)
        self.assertIn("paper-faithful affine collision", non_claim)
        self.assertIn("paper timing", non_claim)
        self.assertIn("paper trajectory agreement", non_claim)
        self.assertIn("any passed `experiment.*` claim", non_claim)

    def test_phase24_record_has_required_evidence_fields(self) -> None:
        text = (
            ROOT
            / "docs/records/2026-05-17-phase24-spinning-box-trajectory-shape-diagnostics.md"
        ).read_text()

        for snippet in (
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
        ):
            self.assertIn(snippet, text)
        self.assertNotIn("independent review: pending", text)
        self.assertNotIn("TO_BE_BACKFILLED_PHASE24_DOCS_COMMIT", text)

    def test_phase25_spinning_box_no_polar_material_lane_is_bounded(self) -> None:
        text = (ROOT / "docs/reference/claim-boundaries.md").read_text()
        current = claim_boundary_bullet(text, "This repository contains Phase 25")
        verified = claim_boundary_bullet(text, "Phase 25 verifies")
        non_claim = claim_boundary_bullet(text, "Phase 25 does not verify")

        self.assertIn("no-polar", current)
        self.assertIn("paper material stiffness", current)
        self.assertIn("unconstrained CPU oracle", verified)
        self.assertIn("rotation_mode = no_polar", verified)
        self.assertIn("mabd_rotation_mode", verified)
        self.assertIn("material_model", verified)
        self.assertIn("material_young_modulus_pa", verified)
        self.assertIn("material_poisson_ratio", verified)
        self.assertIn("material_volume_m3", verified)
        self.assertIn("material_stiffness_trace", verified)
        self.assertIn("material_stiffness_rank", verified)
        self.assertIn("constrained", verified)
        self.assertIn("rotation_mode = none", verified)
        self.assertIn("angular momentum", verified)
        self.assertIn("energy", verified)
        self.assertIn("development gap", verified)
        self.assertIn("the paper spinning-box experiment", non_claim)
        self.assertIn("multi-body no-polar constraints", non_claim)
        self.assertIn("paper-faithful implicit RBD baseline", non_claim)
        self.assertIn("paper-faithful affine collision", non_claim)
        self.assertIn("paper timing", non_claim)
        self.assertIn("paper trajectory agreement", non_claim)
        self.assertIn("any passed `experiment.*` claim", non_claim)

    def test_phase25_record_has_required_evidence_fields(self) -> None:
        text = (
            ROOT / "docs/records/2026-05-17-phase25-spinning-box-no-polar-material-lane.md"
        ).read_text()

        for snippet in (
            "## Status\n\npassed",
            "## Config Path",
            "configs/experiments/single_body_spinning_box.yaml",
            "## Repository",
            "plan commit: `9cff8b74521ec3ae2395bb5ceac42651cb1f2a40`",
            "CPU oracle no-polar implementation commit: `80a32a1e2f5a1a3ab80bec2460562cbcfd54c0bf`",
            "spinning-box material lane implementation commit: `c0cef676e5265c659ca2bd9bd58165f357d8b1fa`",
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
        ):
            self.assertIn(snippet, text)
        self.assertNotIn("TO_BE_BACKFILLED_PHASE25_DOCS_COMMIT", text)
        self.assertNotIn("TO_BE_BACKFILLED_PHASE25_REVIEW_DISPOSITION_COMMIT", text)

    def test_phase26_corotated_material_rhs_is_bounded(self) -> None:
        text = (ROOT / "docs/reference/claim-boundaries.md").read_text()
        current = claim_boundary_bullet(text, "This repository contains Phase 26")
        verified = claim_boundary_bullet(text, "Phase 26 verifies")
        non_claim = claim_boundary_bullet(text, "Phase 26 does not verify")

        self.assertIn("co-rotated material RHS", current)
        self.assertIn("rotation_mode = polar", current)
        self.assertIn("unconstrained CPU oracle", verified)
        self.assertIn("rotation_mode = polar", verified)
        self.assertIn("material_rhs_frame = corotated_local_all_blocks", verified)
        self.assertIn("translation_frame = corotated_polar_all_blocks", verified)
        self.assertIn("report status: `incomplete`", verified)
        self.assertIn("the paper spinning-box experiment", non_claim)
        self.assertIn("paper-faithful implicit RBD baseline", non_claim)
        self.assertIn("paper-faithful affine collision", non_claim)
        self.assertIn("unconfigured production `SolverMABD.step()`", non_claim)
        self.assertIn("Warp/CUDA/GPU paths", non_claim)
        self.assertIn("paper timing", non_claim)
        self.assertIn("paper trajectory agreement", non_claim)
        self.assertIn("any passed `experiment.*` claim", non_claim)

    def test_phase26_record_has_required_evidence_fields(self) -> None:
        text = (ROOT / "docs/records/2026-05-17-phase26-corotated-material-rhs.md").read_text()

        for snippet in (
            "## Status\n\npassed",
            "## Config Path",
            "configs/experiments/single_body_spinning_box.yaml",
            "## Repository",
            "plan commit: `96509da",
            "polar CPU oracle implementation commit: `d2ddb2a",
            "spinning-box polar report lane implementation commit: `a5755ba",
            "docs/record creation commit: `982ebaa60907e1666e3acc6f3cf8ffdabc1d207a`",
            "review disposition record commit: `aa18dda3111de820e617d1b6515d1d547445efa5`",
            "provenance hardening commit: `d500f97cee6f66a2a5a4aae23275d09ac4dd0df3`",
            "verification-command hardening commit: `aa18dda3111de820e617d1b6515d1d547445efa5`",
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
        ):
            self.assertIn(snippet, text)
        self.assertNotIn("TO_BE_BACKFILLED_PHASE26_DOCS_COMMIT", text)
        self.assertNotIn("TO_BE_BACKFILLED_PHASE26_REVIEW_DISPOSITION_COMMIT", text)
        self.assertNotIn("pending branch-local", text)

    def test_phase27_rbd_lane_gate_is_bounded(self) -> None:
        data = yaml.safe_load((ROOT / "docs/reference/paper-claims.yaml").read_text())
        experiment_statuses = {
            claim["claim_id"]: claim["reproduction_status"]
            for claim in data["claims"]
            if str(claim["claim_id"]).startswith("experiment.")
        }
        self.assertNotIn("passed", set(experiment_statuses.values()))

        text = (ROOT / "docs/reference/claim-boundaries.md").read_text()
        current = claim_boundary_bullet(text, "This repository contains Phase 27")
        verified = claim_boundary_bullet(text, "Phase 27 verifies")
        non_claim = claim_boundary_bullet(text, "Phase 27 does not verify")

        self.assertIn("paper-scoped RBD lane gate", current)
        self.assertIn("required single-body spinning-box", current)
        self.assertIn("top-level report remains `incomplete`", verified)
        self.assertIn("lane_gate_status = passed", verified)
        self.assertIn("paper_faithful_implicit_rbd", verified)
        self.assertIn("cpu_numpy_newton_only", verified)
        self.assertIn("closed-form xyzw quaternion", verified)
        self.assertIn("comparison protocol consumes the RBD lane gate", verified)
        self.assertIn("the paper spinning-box experiment", non_claim)
        self.assertIn("M-ABD lane pass", non_claim)
        self.assertIn("spinning-box comparison pass", non_claim)
        self.assertIn("any passed `experiment.*` claim", non_claim)

    def test_phase27_record_has_required_evidence_fields(self) -> None:
        text = (ROOT / "docs/records/2026-05-17-phase27-rbd-pass-gate.md").read_text()

        for snippet in (
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
        ):
            self.assertIn(snippet, text)
        self.assertNotIn("TO_BE_BACKFILLED_PHASE27_DOCS_COMMIT", text)
        self.assertNotIn("pending branch-local", text)

    def test_phase28_spinning_box_paper_horizon_is_bounded(self) -> None:
        data = yaml.safe_load((ROOT / "docs/reference/paper-claims.yaml").read_text())
        experiment_statuses = {
            claim["claim_id"]: claim["reproduction_status"]
            for claim in data["claims"]
            if str(claim["claim_id"]).startswith("experiment.")
        }
        self.assertNotIn("passed", set(experiment_statuses.values()))

        text = (ROOT / "docs/reference/claim-boundaries.md").read_text()
        current = claim_boundary_bullet(text, "This repository contains Phase 28")
        verified = claim_boundary_bullet(text, "Phase 28 verifies")
        non_claim = claim_boundary_bullet(text, "Phase 28 does not verify")

        self.assertIn("paper-horizon M-ABD diagnostic", current)
        self.assertIn("10 second", current)
        self.assertIn("h = 1e-2", current)
        self.assertIn("h = 1e-3", current)
        self.assertIn("mabd_cpu_oracle_paper_horizon_diagnostic", verified)
        self.assertIn("every-step extrema", verified)
        self.assertIn("threshold_violations", verified)
        self.assertIn("mabd_paper_horizon_status = development_gap_observed", verified)
        self.assertIn("no `lane_gate_status`", verified)
        self.assertIn("report status: `incomplete`", verified)
        self.assertIn("M-ABD lane pass", non_claim)
        self.assertIn("spinning-box comparison pass", non_claim)
        self.assertIn("paper-faithful affine collision", non_claim)
        self.assertIn("paper timing", non_claim)
        self.assertIn("any passed `experiment.*` claim", non_claim)

    def test_phase28_record_has_required_evidence_fields(self) -> None:
        text = (
            ROOT / "docs/records/2026-05-17-phase28-spinning-box-paper-horizon.md"
        ).read_text()

        for snippet in (
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
        ):
            self.assertIn(snippet, text)
        self.assertNotIn("TO_BE_BACKFILLED_PHASE28_DOCS_COMMIT", text)
        self.assertNotIn("pending branch-local", text)

    def test_phase29_spinning_box_kinematic_feasibility_is_bounded(self) -> None:
        data = yaml.safe_load((ROOT / "docs/reference/paper-claims.yaml").read_text())
        experiment_statuses = {
            claim["claim_id"]: claim["reproduction_status"]
            for claim in data["claims"]
            if str(claim["claim_id"]).startswith("experiment.")
        }
        self.assertNotIn("passed", set(experiment_statuses.values()))

        text = (ROOT / "docs/reference/claim-boundaries.md").read_text()
        current = claim_boundary_bullet(text, "This repository contains Phase 29")
        verified = claim_boundary_bullet(text, "Phase 29 verifies")
        non_claim = claim_boundary_bullet(text, "Phase 29 does not verify")

        self.assertIn("spinning-box kinematic feasibility diagnostics", current)
        self.assertIn("paper angular speed 60000", verified)
        self.assertIn("orthogonal finite-difference bounds 100 and 1000 rad/s", verified)
        self.assertIn("momentum bounds 1/6 and 10/6", verified)
        self.assertIn("ratios 600 and 60", verified)
        self.assertIn("paper_momentum_requires_affine_stretch_under_q_delta_over_h", verified)
        self.assertIn("qd_next=(q_next-q_n)/h", verified)
        self.assertIn("the paper spinning-box experiment", non_claim)
        self.assertIn("M-ABD lane pass", non_claim)
        self.assertIn("spinning-box comparison pass", non_claim)
        self.assertIn("solver fix", non_claim)
        self.assertIn("decoupled velocity semantics", non_claim)
        self.assertIn("any passed `experiment.*` claim", non_claim)

    def test_phase29_record_has_required_evidence_fields(self) -> None:
        text = (
            ROOT / "docs/records/2026-05-17-phase29-spinning-box-kinematic-feasibility.md"
        ).read_text()

        for snippet in (
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
            "h = 0.01 orthogonal_update_angular_speed_bound_rad_s = 100.0",
            "h = 0.01 orthogonal_update_angular_momentum_bound_kg_m2_s = 0.16666666666666666",
            "h = 0.01 required_speed_to_bound_ratio = 600.0",
            "h = 0.001 orthogonal_update_angular_speed_bound_rad_s = 1000.0",
            "h = 0.001 orthogonal_update_angular_momentum_bound_kg_m2_s = 1.6666666666666667",
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
        ):
            self.assertIn(snippet, text)
        self.assertNotIn("TO_BE_BACKFILLED_PHASE29_DOCS_COMMIT", text)
        self.assertNotIn("pending branch-local", text)

    def test_phase30_velocity_semantics_source_audit_is_bounded(self) -> None:
        data = yaml.safe_load((ROOT / "docs/reference/paper-claims.yaml").read_text())
        experiment_statuses = {
            claim["claim_id"]: claim["reproduction_status"]
            for claim in data["claims"]
            if str(claim["claim_id"]).startswith("experiment.")
        }
        self.assertNotIn("passed", set(experiment_statuses.values()))

        text = (ROOT / "docs/reference/claim-boundaries.md").read_text()
        current = claim_boundary_bullet(text, "This repository contains Phase 30")
        verified = claim_boundary_bullet(text, "Phase 30 verifies")
        non_claim = claim_boundary_bullet(text, "Phase 30 does not verify")

        self.assertIn("velocity semantics source audit", current)
        self.assertIn("source_does_not_prove_decoupled_velocity_semantics", current)
        self.assertIn("implicit Euler inertia potential", verified)
        self.assertIn("`G(A)` twist mapping", verified)
        self.assertIn("`G(A)^T` wrench mapping", verified)
        self.assertIn("spinning-box twist initialization", verified)
        self.assertIn("source_does_not_specify_decoupled_velocity_semantics", verified)
        self.assertIn("source_does_not_specify_alternative_momentum_extraction", verified)
        self.assertIn("Newton solver modification", non_claim)
        self.assertIn("decoupled velocity semantics", non_claim)
        self.assertIn("M-ABD lane pass", non_claim)
        self.assertIn("any passed `experiment.*` claim", non_claim)

    def test_phase30_record_has_required_evidence_fields(self) -> None:
        text = (
            ROOT / "docs/records/2026-05-17-phase30-velocity-semantics-source-audit.md"
        ).read_text()

        for snippet in (
            "## Status\n\npassed",
            "## Config Path",
            "configs/experiments/single_body_spinning_box.yaml",
            "configs/experiments/paper_experiment_matrix.yaml",
            "## Repository",
            "base commit: `6683d92`",
            "design/plan commit: `c97ee49`",
            "source-audit implementation commit:",
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
        ):
            self.assertIn(snippet, text)
        self.assertNotIn("TO_BE_BACKFILLED_PHASE30_DOCS_COMMIT", text)
        self.assertNotIn("to be recorded after the Phase 30 docs commit", text)
        self.assertNotIn("pending branch-local", text)

    def test_phase31_official_artifact_audit_is_bounded(self) -> None:
        data = yaml.safe_load((ROOT / "docs/reference/paper-claims.yaml").read_text())
        experiment_statuses = {
            claim["claim_id"]: claim["reproduction_status"]
            for claim in data["claims"]
            if str(claim["claim_id"]).startswith("experiment.")
        }
        self.assertNotIn("passed", set(experiment_statuses.values()))

        text = (ROOT / "docs/reference/claim-boundaries.md").read_text()
        current = claim_boundary_bullet(text, "This repository contains Phase 31")
        verified = claim_boundary_bullet(text, "Phase 31 verifies")
        non_claim = claim_boundary_bullet(text, "Phase 31 does not verify")

        self.assertIn("official artifact availability audit", current)
        self.assertIn(
            "official_project_and_video_found_implementation_code_coming_soon_as_of_2026-05-17",
            current,
        )
        self.assertIn("arXiv", verified)
        self.assertIn("SIGGRAPH 2026 schedule", verified)
        self.assertIn("Minghao Guo", verified)
        self.assertIn("first-author project page", verified)
        self.assertIn("MINSUGLLY/mabd", verified)
        self.assertIn("supplementary video were found", verified)
        self.assertIn("Code (coming soon)", verified)
        self.assertIn("Yin Yang", verified)
        self.assertIn("GitHub repository search", verified)
        self.assertIn("private author-code absence", non_claim)
        self.assertIn("paper experiment pass", non_claim)
        self.assertIn("Newton solver modification", non_claim)
        self.assertIn("any passed `experiment.*` claim", non_claim)

    def test_phase31_record_has_required_evidence_fields(self) -> None:
        text = (
            ROOT / "docs/records/2026-05-17-phase31-official-artifact-availability.md"
        ).read_text()

        for snippet in (
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
            "official_implementation_code_marked_coming_soon",
            "official_implementation_code_not_found_in_audited_public_sources",
            "not proof of private author-code absence",
            "No `experiment.*` claim is passed in this phase.",
            "## Artifacts",
            "raw web pages: not committed",
            "generated reports: not committed",
            "## Verification Commands",
            "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_official_artifact_audit",
            "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py",
            "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/env/readiness_check.py",
            "git diff --check",
        ):
            self.assertIn(snippet, text)
        self.assertNotIn("TO_BE_BACKFILLED_PHASE31_DOCS_COMMIT", text)
        self.assertNotIn("pending branch-local", text)
        self.assertNotIn("official_project_page_url_missing", text)
        self.assertNotIn("official_supplementary_video_url_missing", text)

    def test_phase32_gravity_force_mapping_is_bounded(self) -> None:
        data = yaml.safe_load((ROOT / "docs/reference/paper-claims.yaml").read_text())
        claims = {claim["claim_id"]: claim for claim in data["claims"]}
        self.assertEqual(
            claims["method.force_mapping.gravity_generalized_force"]["reproduction_status"],
            "passed",
        )
        experiment_statuses = {
            claim["claim_id"]: claim["reproduction_status"]
            for claim in data["claims"]
            if str(claim["claim_id"]).startswith("experiment.")
        }
        self.assertNotIn("passed", set(experiment_statuses.values()))

        text = (ROOT / "docs/reference/claim-boundaries.md").read_text()
        current = claim_boundary_bullet(text, "This repository contains Phase 32")
        verified = claim_boundary_bullet(text, "Phase 32 verifies")
        non_claim = claim_boundary_bullet(text, "Phase 32 does not verify")

        self.assertIn("uniform gravity generalized-force CPU oracle support", current)
        self.assertIn("gravity_generalized_force", verified)
        self.assertIn("J_i^T m_i g", verified)
        self.assertIn("MABDCPUOracleConfig", verified)
        self.assertIn("gravity input", verified)
        self.assertIn("malformed gravity-vector rejection", verified)
        self.assertIn("heavy-top scene reproduction", non_claim)
        self.assertIn("physical-pendulum scene reproduction", non_claim)
        self.assertIn("analytic or RK4 reference agreement", non_claim)
        self.assertIn("contact", non_claim)
        self.assertIn("any passed `experiment.*` claim", non_claim)

    def test_phase32_record_has_required_evidence_fields(self) -> None:
        text = (
            ROOT / "docs/records/2026-05-17-phase32-gravity-force-mapping.md"
        ).read_text()

        for snippet in (
            "## Status\n\npassed",
            "## Config Path",
            "No experiment config is changed in Phase 32.",
            "## Repository",
            "base commit: `f8d36da`",
            "## Vendored Newton",
            "local patch status: Phase 32 modifies vendored Newton M-ABD CPU oracle code",
            "vendor/newton/newton/_src/solvers/mabd/affine_math.py",
            "vendor/newton/newton/_src/solvers/mabd/__init__.py",
            "vendor/newton/newton/_src/solvers/mabd/step_oracle.py",
            "vendor/newton/newton/tests/test_mabd_single_body.py",
            "vendor/newton/newton/tests/test_mabd_phase4_solver_step.py",
            "## Paper Source",
            "/tmp/mabd-paper/source/sections/singleabd.tex:23-26",
            "/tmp/mabd-paper/source/sections/singleabd.tex:42",
            "/tmp/mabd-paper/source/sections/singleabd.tex:55-58",
            "/tmp/mabd-paper/source/sections/solver.tex:238-242",
            "non-claim experiment motivation, not passed evidence",
            "/tmp/mabd-paper/source/sections/experiment.tex:67-75",
            "/tmp/mabd-paper/source/sections/experiment.tex:80-91",
            "## Environment",
            "mabd-newton-py310",
            "smoke_passed",
            "mutates_reference_environment=false",
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
            "git diff --check",
        ):
            self.assertIn(snippet, text)
        self.assertNotIn("TO_BE_BACKFILLED_PHASE32", text)
        self.assertNotIn("pending branch-local", text)

    def test_phase33_physical_pendulum_analytic_reference_is_bounded(self) -> None:
        data = yaml.safe_load((ROOT / "docs/reference/paper-claims.yaml").read_text())
        experiment_statuses = {
            claim["claim_id"]: claim["reproduction_status"]
            for claim in data["claims"]
            if str(claim["claim_id"]).startswith("experiment.")
        }
        self.assertNotIn("passed", set(experiment_statuses.values()))

        text = (ROOT / "docs/reference/claim-boundaries.md").read_text()
        current = claim_boundary_bullet(text, "This repository contains Phase 33")
        verified = claim_boundary_bullet(text, "Phase 33 verifies")
        non_claim = claim_boundary_bullet(text, "Phase 33 does not verify")

        self.assertIn("physical-pendulum analytic-reference lane", current)
        self.assertIn("elliptic-reference formula", verified)
        self.assertIn("physical_pendulum_angle_reference", verified)
        self.assertIn("experiment-matrix validation", verified)
        self.assertIn("`analytic_reference` CLI dispatch", verified)
        self.assertIn("`lane_status = passed`", verified)
        self.assertIn("top-level report status: `incomplete`", verified)
        self.assertIn("M-ABD physical-pendulum dynamics", non_claim)
        self.assertIn("RBD implicit baseline dynamics", non_claim)
        self.assertIn("joint-force waveform agreement", non_claim)
        self.assertIn("full physical-pendulum experiment", non_claim)
        self.assertIn("any passed `experiment.*` claim", non_claim)

    def test_phase33_record_has_required_evidence_fields(self) -> None:
        text = (
            ROOT / "docs/records/2026-05-17-phase33-physical-pendulum-analytic-reference.md"
        ).read_text()

        for snippet in (
            "## Status\n\npassed",
            "## Config Path",
            "configs/experiments/single_body_physical_pendulum.yaml",
            "## Repository",
            "base commit: `52fa600`",
            "phase33-physical-pendulum-reference",
            "## Vendored Newton",
            "local patch status: Phase 33 does not modify vendored Newton",
            "## Paper Source",
            "/tmp/mabd-paper/source/sections/experiment.tex:77-91",
            "theta(t)=pi/2 - 2 asin(kappa * sn(K(kappa) - omega_lin * t, kappa))",
            "## Environment",
            "mabd-newton-py310",
            "physics-primitive-newton-py310",
            "smoke_passed",
            "mutates_reference_environment=false",
            "## Analytic Reference Evidence",
            "physical_pendulum_angle_reference",
            "m = kappa**2",
            "theta(K/omega_lin)=pi/2",
            "lane_status = passed",
            "top-level report status: `incomplete`",
            "reports/experiment_matrix/single_body_physical_pendulum_analytic_reference.json",
            "review hardening:",
            "`lane_status` is derived from threshold violations",
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
            "## TDD Evidence",
            "FAILED (failures=1, errors=5)",
            "Ran 37 tests",
            "## Claim Impact",
            "No `experiment.*` claim is passed.",
            "`experiment.single_body.physical_pendulum` remains not passed.",
            "M-ABD simulation lane remains missing",
            "RBD implicit baseline remains missing",
            "Joint-force waveform agreement remains missing",
            "`pendulum_geometry_unknown` remains a blocker",
            "## Verification Commands",
            "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_physical_pendulum_reference tests.test_experiment_run_configs tests.test_experiment_runner",
            "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py",
            "git diff --check",
        ):
            self.assertIn(snippet, text)
        self.assertNotIn("TO_BE_BACKFILLED_PHASE33", text)
        self.assertNotIn("pending branch-local", text)

    def test_phase34_world_anchor_physical_pendulum_mabd_is_bounded(self) -> None:
        data = yaml.safe_load((ROOT / "docs/reference/paper-claims.yaml").read_text())
        experiment_statuses = {
            claim["claim_id"]: claim["reproduction_status"]
            for claim in data["claims"]
            if str(claim["claim_id"]).startswith("experiment.")
        }
        self.assertNotIn("passed", set(experiment_statuses.values()))

        text = (ROOT / "docs/reference/claim-boundaries.md").read_text()
        current = claim_boundary_bullet(text, "This repository contains Phase 34")
        verified = claim_boundary_bullet(text, "Phase 34 verifies")
        non_claim = claim_boundary_bullet(text, "Phase 34 does not verify")

        self.assertIn("world-anchor CPU-oracle support", current)
        self.assertIn("physical-pendulum M-ABD development diagnostic lane", current)
        self.assertIn("MABDCPUOracleWorldConstraint", verified)
        self.assertIn("dense-only topology gating", verified)
        self.assertIn("mabd_development", verified)
        self.assertIn("`physical_pendulum_mabd_development` CLI dispatch", verified)
        self.assertIn("`physical_pendulum_mabd_development_diagnostic` report lane id", verified)
        self.assertIn("`lane_status = development_diagnostic_generated`", verified)
        self.assertIn("top-level report status: `incomplete`", verified)
        self.assertIn("full physical-pendulum experiment", non_claim)
        self.assertIn("paper-faithful pendulum geometry", non_claim)
        self.assertIn("RBD implicit baseline dynamics", non_claim)
        self.assertIn("joint-force waveform agreement", non_claim)
        self.assertIn("paper timing", non_claim)
        self.assertIn("any passed `experiment.*` claim", non_claim)

    def test_phase34_record_has_required_evidence_fields(self) -> None:
        text = (
            ROOT / "docs/records/2026-05-17-phase34-world-anchor-physical-pendulum-mabd.md"
        ).read_text()

        for snippet in (
            "## Status\n\npassed",
            "## Config Path",
            "configs/experiments/single_body_physical_pendulum.yaml",
            "configs/experiments/paper_experiment_matrix.yaml",
            "## Repository",
            "base commit: `81785e0`",
            "phase34-physical-pendulum-mabd-lane",
            "## Vendored Newton",
            "local patch status: Phase 34 modifies vendored Newton M-ABD CPU oracle code",
            "vendor/newton/newton/_src/solvers/mabd/step_oracle.py",
            "vendor/newton/newton/tests/test_mabd_phase4_solver_step.py",
            "## Paper Source",
            "/tmp/mabd-paper/source/sections/experiment.tex:77-91",
            "fixed pivot",
            "joint-force waveform comparison",
            "implicit RBD baseline comparison",
            "## Environment",
            "mabd-newton-py310",
            "physics-primitive-newton-py310",
            "smoke_passed",
            "mutates_reference_environment=false",
            "## Newton World Anchor Evidence",
            "MABDCPUOracleWorldConstraint",
            "MABDCPUOracleConfig.world_constraints",
            "point_jacobian(rest_point)",
            "topology='dense'",
            "malformed rest/world vectors are rejected",
            "## Physical Pendulum M-ABD Diagnostic Evidence",
            "src/mabd_reproduction/physical_pendulum_mabd.py",
            "run_physical_pendulum_mabd_development",
            "--lane physical_pendulum_mabd_development",
            "mabd_cpu_oracle_physical_pendulum_development",
            "report lane: `physical_pendulum_mabd_development_diagnostic`",
            "lane_status = development_diagnostic_generated",
            "top-level report status: `incomplete`",
            "reports/experiment_matrix/single_body_physical_pendulum_mabd_development.json",
            "paper pendulum geometry remains unknown",
            "no implicit RBD baseline",
            "no joint-force waveform comparison",
            "required `mabd_newton` experiment lane remains listed as missing",
            "## Metrics And Thresholds",
            "time_step_s: `0.01`",
            "step_count: `16`",
            "compact sample count: `5`",
            "max_pivot_residual_m = 0.0",
            "max_constraint_residual_norm = 0.0",
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
            "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py",
            "git diff --check",
        ):
            self.assertIn(snippet, text)
        self.assertNotIn("TO_BE_BACKFILLED_PHASE34", text)
        self.assertNotIn("pending branch-local", text)

    def test_phase34_mabd_report_artifact_tracks_current_missing_lanes(self) -> None:
        report = load_claim_report(
            ROOT / "reports/experiment_matrix/single_body_physical_pendulum_mabd_development.json"
        )

        self.assertEqual(report.observed["required_missing_lanes"], ["mabd_newton"])
        self.assertFalse(report.observed["full_experiment_claim_passed"])
        self.assertNotIn("rbd_implicit_baseline", report.failure_reason)

    def test_phase35_physical_pendulum_rbd_baseline_is_bounded(self) -> None:
        data = yaml.safe_load((ROOT / "docs/reference/paper-claims.yaml").read_text())
        experiment_statuses = {
            claim["claim_id"]: claim["reproduction_status"]
            for claim in data["claims"]
            if str(claim["claim_id"]).startswith("experiment.")
        }
        self.assertNotIn("passed", set(experiment_statuses.values()))

        text = (ROOT / "docs/reference/claim-boundaries.md").read_text()
        current = claim_boundary_bullet(text, "This repository contains Phase 35")
        verified = claim_boundary_bullet(text, "Phase 35 verifies")
        non_claim = claim_boundary_bullet(text, "Phase 35 does not verify")

        self.assertIn("physical-pendulum RBD implicit baseline diagnostic lane", current)
        self.assertIn("rbd_baseline", verified)
        self.assertIn("`rbd_implicit_baseline` CLI dispatch", verified)
        self.assertIn("`physical_pendulum_scalar_implicit_rbd_development`", verified)
        self.assertIn("`required_missing_lanes = [mabd_newton]`", verified)
        self.assertIn("top-level report status: `incomplete`", verified)
        self.assertIn("full physical-pendulum experiment", non_claim)
        self.assertIn("paper-faithful pendulum geometry", non_claim)
        self.assertIn("joint-force waveform agreement", non_claim)
        self.assertIn("paper timing", non_claim)
        self.assertIn("any passed `experiment.*` claim", non_claim)

    def test_phase35_record_has_required_evidence_fields(self) -> None:
        text = (
            ROOT / "docs/records/2026-05-17-phase35-physical-pendulum-rbd-baseline.md"
        ).read_text()

        for snippet in (
            "## Status\n\npassed",
            "## Config Path",
            "configs/experiments/single_body_physical_pendulum.yaml",
            "configs/experiments/paper_experiment_matrix.yaml",
            "## Repository",
            "base commit: `7778469`",
            "phase35-physical-pendulum-rbd-baseline",
            "## Vendored Newton",
            "local patch status: Phase 35 does not modify vendored Newton",
            "## Paper Source",
            "/tmp/mabd-paper/source/sections/experiment.tex:77-91",
            "implicit RBD baseline against the analytic solution",
            "## Environment",
            "mabd-newton-py310",
            "physics-primitive-newton-py310",
            "smoke_passed",
            "mutates_reference_environment=false",
            "## Physical Pendulum RBD Evidence",
            "src/mabd_reproduction/physical_pendulum_rbd.py",
            "run_physical_pendulum_rbd_baseline",
            "--lane rbd_implicit_baseline",
            "physical_pendulum_scalar_implicit_rbd_development",
            "baseline lane: `rbd_implicit_baseline`",
            "lane_status = development_diagnostic_generated",
            "top-level report status: `incomplete`",
            "required_missing_lanes = [`mabd_newton`]",
            "reports/experiment_matrix/single_body_physical_pendulum_rbd_baseline.json",
            "joint-force magnitude is diagnostic only",
            "## Metrics And Thresholds",
            "time_step_s: `0.01`",
            "step_count: `16`",
            "compact sample count: `5`",
            "max_implicit_residual",
            "max_length_constraint_error_m",
            "threshold status: `passed`",
            "## Claim Impact",
            "No `experiment.*` claim is passed.",
            "`experiment.single_body.physical_pendulum` remains not passed.",
            "required physical-pendulum `mabd_newton` experiment lane remains missing",
            "RBD implicit baseline diagnostic is now present",
            "Joint-force waveform agreement remains missing",
            "Paper-faithful pendulum geometry remains missing",
            "`pendulum_geometry_unknown` remains a blocker",
            "## Verification Commands",
            "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_physical_pendulum_rbd tests.test_experiment_run_configs tests.test_experiment_runner",
            "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py",
            "git diff --check",
        ):
            self.assertIn(snippet, text)
        self.assertNotIn("TO_BE_BACKFILLED_PHASE35", text)
        self.assertNotIn("pending branch-local", text)

    def test_phase35_rbd_report_artifact_is_machine_checkable(self) -> None:
        report = load_claim_report(
            ROOT / "reports/experiment_matrix/single_body_physical_pendulum_rbd_baseline.json"
        )

        self.assertEqual(report.claim_id, "experiment.single_body.physical_pendulum")
        self.assertEqual(report.scene_id, "single_body_physical_pendulum")
        self.assertEqual(report.status.value, "incomplete")
        self.assertEqual(report.baseline_lane, "rbd_implicit_baseline")
        self.assertEqual(report.solver_mode, "physical_pendulum_scalar_implicit_rbd_development")
        self.assertEqual(report.backend, "cpu_numpy_newton_only")
        self.assertNotEqual(report.source_commit, "phase35-working-tree")
        self.assertEqual(report.observed["lane_status"], "development_diagnostic_generated")
        self.assertEqual(report.observed["required_missing_lanes"], ["mabd_newton"])
        self.assertFalse(report.observed["full_experiment_claim_passed"])
        self.assertFalse(report.expected["full_experiment_claim_passed"])
        self.assertIn("diagnostic only", report.expected["paper_claim_status"])
        self.assertIn("full experiment incomplete", report.expected["paper_claim_status"])
        self.assertIn(
            "scalar joint-force reference is diagnostic and not paper geometry",
            report.expected["nonclaim_limitations"],
        )
        self.assertEqual(report.observed["sample_count"], 5)
        self.assertEqual(report.observed["threshold_violations"], [])
        self.assertLessEqual(
            report.observed["max_implicit_residual"],
            report.threshold["max_implicit_residual"],
        )
        self.assertIn("pendulum_geometry_unknown", report.observed["blocking_reasons"])
        self.assertNotIn(
            "joint_force_waveform_agreement_missing",
            report.observed["blocking_reasons"],
        )

    def test_phase35_validator_rejects_placeholder_report_source_commit(self) -> None:
        import scripts.validate_docs as validate_docs

        actual = load_claim_report(
            ROOT / "reports/experiment_matrix/single_body_physical_pendulum_rbd_baseline.json"
        )
        stale = replace(actual, source_commit="phase35-working-tree")

        with patch.object(validate_docs, "load_claim_report", return_value=stale):
            with self.assertRaises(SystemExit) as context:
                validate_docs.validate_phase35_record()

        self.assertIn("source_commit", str(context.exception))

    def test_phase35_validator_rejects_expected_overclaim(self) -> None:
        import scripts.validate_docs as validate_docs

        actual = load_claim_report(
            ROOT / "reports/experiment_matrix/single_body_physical_pendulum_rbd_baseline.json"
        )
        overclaimed = replace(
            actual,
            expected={
                **actual.expected,
                "paper_claim_status": "physical pendulum experiment passed",
                "full_experiment_claim_passed": True,
                "nonclaim_limitations": [],
            },
        )

        with patch.object(validate_docs, "load_claim_report", return_value=overclaimed):
            with self.assertRaises(SystemExit) as context:
                validate_docs.validate_phase35_record()

        self.assertIn("expected", str(context.exception))

    def test_phase36_physical_pendulum_comparison_protocol_is_bounded(self) -> None:
        data = yaml.safe_load((ROOT / "docs/reference/paper-claims.yaml").read_text())
        physical_pendulum = next(
            claim for claim in data["claims"] if claim["claim_id"] == "experiment.single_body.physical_pendulum"
        )
        self.assertEqual(physical_pendulum["reproduction_status"], "intended")

        text = (ROOT / "docs/reference/claim-boundaries.md").read_text()
        current = claim_boundary_bullet(text, "This repository contains Phase 36")
        verified = claim_boundary_bullet(text, "Phase 36 verifies")
        non_claim = claim_boundary_bullet(text, "Phase 36 does not verify")
        forbidden = claim_boundary_bullet(
            text,
            "Phase 36 physical-pendulum comparison protocol",
        )

        self.assertIn("physical-pendulum comparison protocol", current)
        self.assertIn("input report provenance", verified)
        self.assertIn("matched/unmatched sample coverage", verified)
        self.assertIn("paper_metric_statuses", verified)
        self.assertIn("full physical-pendulum experiment", non_claim)
        self.assertIn("M-ABD lane pass", non_claim)
        self.assertIn("joint-force waveform agreement", non_claim)
        self.assertIn("paper geometry", non_claim)
        self.assertIn("paper timing", non_claim)
        self.assertIn("any passed `experiment.*` claim", forbidden)

    def test_phase36_record_has_required_evidence_fields(self) -> None:
        text = (
            ROOT / "docs/records/2026-05-17-phase36-physical-pendulum-comparison-protocol.md"
        ).read_text()

        for snippet in (
            "## Status\n\npassed",
            "## Config Path",
            "configs/experiments/single_body_physical_pendulum.yaml",
            "configs/experiments/paper_experiment_matrix.yaml",
            "## Repository",
            "phase36-physical-pendulum-comparison-protocol",
            "## Vendored Newton",
            "96713fa965463b69c229a4d30582c733ff3526bb",
            "local patch status: Phase 36 does not modify vendored Newton",
            "## Physical Pendulum Comparison Evidence",
            "run_physical_pendulum_comparison",
            "--lane physical_pendulum_comparison",
            "physical_pendulum_multilane_comparison_development",
            "baseline lane: `physical_pendulum_comparison_protocol`",
            "top-level report status: `incomplete`",
            "input_report_provenance",
            "paper_metric_statuses",
            "matched_sample_count",
            "reports/experiment_matrix/single_body_physical_pendulum_analytic_reference.json",
            "reports/experiment_matrix/single_body_physical_pendulum_comparison.json",
            "analytic report source_commit:",
            "comparison report source_commit:",
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
        ):
            self.assertIn(snippet, text)
        self.assertNotIn("TO_BE_BACKFILLED_PHASE36", text)
        self.assertNotIn("pending branch-local", text)

    def test_phase36_report_artifacts_are_machine_checkable(self) -> None:
        analytic = load_claim_report(
            ROOT / "reports/experiment_matrix/single_body_physical_pendulum_analytic_reference.json"
        )
        mabd = load_claim_report(
            ROOT / "reports/experiment_matrix/single_body_physical_pendulum_mabd_newton.json"
        )
        comparison = load_claim_report(
            ROOT / "reports/experiment_matrix/single_body_physical_pendulum_comparison.json"
        )

        self.assertEqual(analytic.baseline_lane, "analytic_reference")
        self.assertEqual(analytic.status.value, "incomplete")
        self.assertNotIn(analytic.source_commit, {"phase37-working-tree", "pending branch-local", "<implementation-commit>"})
        self.assertEqual(
            analytic.vendored_newton_commit,
            "96713fa965463b69c229a4d30582c733ff3526bb",
        )
        self.assertEqual(mabd.baseline_lane, "mabd_newton")
        self.assertEqual(mabd.solver_mode, "mabd_cpu_oracle_physical_pendulum_newton_lane")
        self.assertEqual(mabd.observed["lane_status"], "incomplete_diagnostic_generated")
        self.assertIn("max_phase_drift_rad", mabd.observed)
        self.assertIn("max_world_anchor_reaction_magnitude_n", mabd.observed)
        self.assertEqual(comparison.baseline_lane, "physical_pendulum_comparison_protocol")
        self.assertEqual(comparison.status.value, "incomplete")
        self.assertEqual(comparison.solver_mode, "physical_pendulum_multilane_comparison_development")
        self.assertFalse(comparison.observed["full_experiment_claim_passed"])
        self.assertEqual(comparison.observed["missing_required_lanes"], [])
        self.assertEqual(
            comparison.observed["missing_paper_metrics"],
            ["joint_force_error:paper_geometry_unknown"],
        )
        self.assertIn("joint_force_waveform_diagnostics", comparison.observed)
        self.assertNotIn(
            "joint_force_waveform_agreement_missing",
            comparison.observed["blocking_reasons"],
        )
        self.assertNotIn("mabd_newton_missing", comparison.observed["blocking_reasons"])
        self.assertGreater(comparison.observed["matched_sample_count"], 0)
        self.assertEqual(
            comparison.observed["paper_metric_statuses"]["joint_force_error"]["status"],
            "diagnostic_scalar_reference_not_paper_geometry",
        )
        self.assertEqual(
            comparison.observed["paper_metric_statuses"]["phase_drift"]["status"],
            "diagnostic_available",
        )
        self.assertEqual(
            comparison.observed["input_report_provenance"]["analytic_reference"]["source_commit"],
            analytic.source_commit,
        )
        self.assertEqual(
            comparison.observed["input_report_provenance"]["mabd_newton"]["source_commit"],
            mabd.source_commit,
        )
        self.assertEqual(
            comparison.vendored_newton_commit,
            "96713fa965463b69c229a4d30582c733ff3526bb",
        )

    def test_phase37_physical_pendulum_mabd_newton_lane_is_bounded(self) -> None:
        data = yaml.safe_load((ROOT / "docs/reference/paper-claims.yaml").read_text())
        physical_pendulum = next(
            claim for claim in data["claims"] if claim["claim_id"] == "experiment.single_body.physical_pendulum"
        )
        self.assertEqual(physical_pendulum["reproduction_status"], "intended")

        text = (ROOT / "docs/reference/claim-boundaries.md").read_text()
        current = claim_boundary_bullet(text, "This repository contains Phase 37")
        verified = claim_boundary_bullet(text, "Phase 37 verifies")
        non_claim = claim_boundary_bullet(text, "Phase 37 does not verify")
        forbidden = claim_boundary_bullet(
            text,
            "Phase 37 physical-pendulum `mabd_newton` lane",
        )

        self.assertIn("formal physical-pendulum `mabd_newton` lane", current)
        self.assertIn("run_physical_pendulum_mabd_newton", verified)
        self.assertIn("world_anchor_reaction_vector_n", verified)
        self.assertIn("missing_required_lanes = []", verified)
        self.assertIn("diagnostic_reaction_not_paper_waveform", verified)
        self.assertIn("full physical-pendulum experiment", non_claim)
        self.assertIn("paper-faithful pendulum geometry", non_claim)
        self.assertIn("joint-force waveform agreement", non_claim)
        self.assertIn("paper timing", non_claim)
        self.assertIn("any passed `experiment.*` claim", forbidden)

    def test_phase37_record_has_required_evidence_fields(self) -> None:
        text = (
            ROOT / "docs/records/2026-05-17-phase37-physical-pendulum-mabd-newton-lane.md"
        ).read_text()

        for snippet in (
            "## Status\n\npassed",
            "## Config Path",
            "configs/experiments/single_body_physical_pendulum.yaml",
            "## Repository",
            "phase37-mabd-solver-core",
            "implementation commit: `cf45239`",
            "## Physical Pendulum MABD Newton Evidence",
            "run_physical_pendulum_mabd_newton",
            "--lane physical_pendulum_mabd_newton",
            "mabd_cpu_oracle_physical_pendulum_newton_lane",
            "baseline lane: `mabd_newton`",
            "world_anchor_reaction_vector_n",
            "reports/experiment_matrix/single_body_physical_pendulum_mabd_newton.json",
            "## Regenerated Comparison Evidence",
            "missing_required_lanes = `[]`",
            "diagnostic_reaction_not_paper_waveform",
            "## Claim Impact",
            "No `experiment.*` claim is passed.",
            "`experiment.single_body.physical_pendulum` remains intended.",
            "Joint-force waveform agreement remains missing",
            "paper timing remains missing",
            "## Verification Commands",
            "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py",
            "git diff --check",
        ):
            self.assertIn(snippet, text)
        self.assertNotIn("TO_BE_BACKFILLED_PHASE37", text)
        self.assertNotIn("phase37-working-tree", text)

    def test_phase37_validator_rejects_placeholder_report_source_commit(self) -> None:
        import scripts.validate_docs as validate_docs

        actual = load_claim_report(
            ROOT / "reports/experiment_matrix/single_body_physical_pendulum_comparison.json"
        )
        stale = replace(actual, source_commit="phase37-working-tree")

        with patch.object(validate_docs, "load_claim_report", return_value=stale):
            with self.assertRaises(SystemExit) as context:
                validate_docs.validate_phase37_record()

        self.assertIn("source_commit", str(context.exception))

    def test_phase37_validator_rejects_missing_metric_status(self) -> None:
        import scripts.validate_docs as validate_docs

        actual = load_claim_report(
            ROOT / "reports/experiment_matrix/single_body_physical_pendulum_comparison.json"
        )
        overclaimed = replace(
            actual,
            observed={
                **actual.observed,
                "paper_metric_statuses": {
                    **actual.observed["paper_metric_statuses"],
                    "joint_force_error": {"status": "passed"},
                },
            },
        )

        def fake_load_claim_report(path):
            if str(path).endswith("single_body_physical_pendulum_comparison.json"):
                return overclaimed
            return load_claim_report(path)

        with patch.object(validate_docs, "load_claim_report", side_effect=fake_load_claim_report):
            with self.assertRaises(SystemExit) as context:
                validate_docs.validate_phase37_record()

        self.assertIn("joint_force_error", str(context.exception))

    def test_phase37_validator_rejects_stale_input_report_sha256(self) -> None:
        import scripts.validate_docs as validate_docs

        comparison = load_claim_report(
            ROOT / "reports/experiment_matrix/single_body_physical_pendulum_comparison.json"
        )
        provenance = {
            lane: dict(details)
            for lane, details in comparison.observed["input_report_provenance"].items()
        }
        provenance["analytic_reference"]["sha256"] = "0" * 64
        stale = replace(
            comparison,
            observed={
                **comparison.observed,
                "input_report_provenance": provenance,
            },
        )

        def fake_load_claim_report(path):
            if str(path).endswith("single_body_physical_pendulum_comparison.json"):
                return stale
            return load_claim_report(path)

        with patch.object(validate_docs, "load_claim_report", side_effect=fake_load_claim_report):
            with self.assertRaises(SystemExit) as context:
                validate_docs.validate_phase37_record()

        self.assertIn("sha256", str(context.exception))

    def test_phase38_constrained_rotated_kkt_is_bounded(self) -> None:
        data = yaml.safe_load((ROOT / "docs/reference/paper-claims.yaml").read_text())
        physical_pendulum = next(
            claim for claim in data["claims"] if claim["claim_id"] == "experiment.single_body.physical_pendulum"
        )
        self.assertEqual(physical_pendulum["reproduction_status"], "intended")

        text = (ROOT / "docs/reference/claim-boundaries.md").read_text()
        current = claim_boundary_bullet(text, "This repository contains Phase 38")
        verified = claim_boundary_bullet(text, "Phase 38 verifies")
        non_claim = claim_boundary_bullet(text, "Phase 38 does not verify")
        forbidden = claim_boundary_bullet(
            text,
            "Phase 38 constrained polar CPU KKT support",
        )

        self.assertIn("dense constrained polar CPU KKT evidence", current)
        self.assertIn("dense constrained `rotation_mode = polar`", verified)
        self.assertIn("explicit constrained `no_polar` rejection", verified)
        self.assertIn("mabd_rotation_mode = polar", verified)
        self.assertIn("diagnostic_reaction_not_paper_waveform", verified)
        self.assertIn("constrained `no_polar` KKT", non_claim)
        self.assertIn("rotated chain/tree/loop", non_claim)
        self.assertIn("full physical-pendulum experiment", non_claim)
        self.assertIn("any passed `experiment.*` claim", forbidden)

    def test_phase38_record_has_required_evidence_fields(self) -> None:
        text = (ROOT / "docs/records/2026-05-17-phase38-constrained-rotated-kkt.md").read_text()

        for snippet in (
            "## Status\n\npassed",
            "## Config Path",
            "configs/experiments/single_body_physical_pendulum.yaml",
            "## Repository",
            "phase38-constrained-rotated-kkt",
            "implementation commit: `0b93ee1`",
            "## Solver Evidence",
            "np.kron(np.eye(4), polar_rotation(A))",
            "J_world @ increment_map",
            "constrained `no_polar` remains unsupported",
            "test_constrained_cpu_step_supports_polar_world_anchor",
            "test_constrained_cpu_step_rejects_no_polar_because_map_is_nonlinear",
            "## Physical Pendulum Evidence",
            "mabd_newton.rotation_mode = polar",
            "mabd_rotation_mode = `polar`",
            "reports/experiment_matrix/single_body_physical_pendulum_mabd_newton.json",
            "report source_commit: `0b93ee1`",
            "## Regenerated Comparison Evidence",
            "comparison report source_commit: `0b93ee1`",
            "missing_required_lanes = `[]`",
            "diagnostic_reaction_not_paper_waveform",
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
        ):
            self.assertIn(snippet, text)
        self.assertNotIn("TO_BE_BACKFILLED_PHASE38", text)
        self.assertNotIn("phase38-working-tree", text)

    def test_phase38_validator_rejects_missing_rotation_mode(self) -> None:
        import scripts.validate_docs as validate_docs

        actual = load_claim_report(
            ROOT / "reports/experiment_matrix/single_body_physical_pendulum_mabd_newton.json"
        )
        stale = replace(
            actual,
            observed={**actual.observed, "mabd_rotation_mode": "none"},
        )

        def fake_load_claim_report(path):
            if str(path).endswith("single_body_physical_pendulum_mabd_newton.json"):
                return stale
            return load_claim_report(path)

        with patch.object(validate_docs, "load_claim_report", side_effect=fake_load_claim_report):
            with self.assertRaises(SystemExit) as context:
                validate_docs.validate_phase38_record()

        self.assertIn("mabd_rotation_mode", str(context.exception))

    def test_phase38_validator_rejects_comparison_pass_overclaim(self) -> None:
        import scripts.validate_docs as validate_docs

        actual = load_claim_report(
            ROOT / "reports/experiment_matrix/single_body_physical_pendulum_comparison.json"
        )
        overclaimed = replace(
            actual,
            observed={**actual.observed, "full_experiment_claim_passed": True},
        )

        def fake_load_claim_report(path):
            if str(path).endswith("single_body_physical_pendulum_comparison.json"):
                return overclaimed
            return load_claim_report(path)

        with patch.object(validate_docs, "load_claim_report", side_effect=fake_load_claim_report):
            with self.assertRaises(SystemExit) as context:
                validate_docs.validate_phase38_record()

        self.assertIn("full experiment", str(context.exception))

    def test_phase39_physical_pendulum_timing_source_audit_is_bounded(self) -> None:
        data = yaml.safe_load((ROOT / "docs/reference/paper-claims.yaml").read_text())
        physical_pendulum = next(
            claim for claim in data["claims"] if claim["claim_id"] == "experiment.single_body.physical_pendulum"
        )
        self.assertEqual(physical_pendulum["reproduction_status"], "intended")

        text = (ROOT / "docs/reference/claim-boundaries.md").read_text()
        current = claim_boundary_bullet(text, "This repository contains Phase 39")
        verified = claim_boundary_bullet(text, "Phase 39 verifies")
        non_claim = claim_boundary_bullet(text, "Phase 39 does not verify")
        forbidden = claim_boundary_bullet(
            text,
            "Phase 39 physical-pendulum timing source audit",
        )

        self.assertIn("physical-pendulum timing source-audit evidence", current)
        self.assertIn("paper_timing_source_audit", verified)
        self.assertIn("runtime_timing_claim_present = false", verified)
        self.assertIn("paper_timing_missing", verified)
        self.assertIn("joint-force waveform agreement", non_claim)
        self.assertIn("paper-faithful pendulum geometry", non_claim)
        self.assertIn("runtime performance", non_claim)
        self.assertIn("passed physical-pendulum experiment", forbidden)

    def test_phase39_record_has_required_evidence_fields(self) -> None:
        text = (
            ROOT / "docs/records/2026-05-17-phase39-physical-pendulum-timing-source-audit.md"
        ).read_text()

        for snippet in (
            "## Status\n\npassed",
            "## Config Path",
            "configs/experiments/single_body_physical_pendulum.yaml",
            "## Repository",
            "phase39-physical-pendulum-timing",
            "## Paper Source Audit",
            "/tmp/mabd-paper/source/sections/experiment.tex:77-91",
            "runtime_timing_claim_present = `false`",
            "required_metric = `false`",
            "not_a_physical_pendulum_paper_metric",
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
        ):
            self.assertIn(snippet, text)
        self.assertNotIn("TO_BE_BACKFILLED_PHASE39", text)
        self.assertNotIn("phase39-working-tree", text)

    def test_phase39_current_physical_pendulum_reports_record_timing_source_audit(
        self,
    ) -> None:
        report_paths = (
            ROOT / "reports/experiment_matrix/single_body_physical_pendulum_analytic_reference.json",
            ROOT / "reports/experiment_matrix/single_body_physical_pendulum_mabd_newton.json",
            ROOT / "reports/experiment_matrix/single_body_physical_pendulum_rbd_baseline.json",
            ROOT / "reports/experiment_matrix/single_body_physical_pendulum_comparison.json",
        )

        reports = [load_claim_report(path) for path in report_paths]
        for report in reports:
            self.assertEqual(report.status.value, "incomplete")
            self.assertFalse(report.observed["full_experiment_claim_passed"])
            self.assert_physical_pendulum_timing_source_audit(
                report.observed["paper_timing_source_audit"]
            )
            self.assert_physical_pendulum_timing_source_audit(
                report.expected["paper_timing_source_audit"]
            )
            self.assertEqual(report.timing_distribution["scope"], "not_timed")
            self.assertNotIn("paper_timing_missing", report.observed.get("blocking_reasons", []))

        comparison = reports[-1]
        blockers = comparison.observed["blocking_reasons"]
        self.assertNotIn("joint_force_waveform_agreement_missing", blockers)
        self.assertIn("pendulum_geometry_unknown", blockers)
        self.assertIn("physical_pendulum_comparison_pass_gate_not_enabled", blockers)
        self.assertEqual(
            comparison.observed["missing_paper_metrics"],
            ["joint_force_error:paper_geometry_unknown"],
        )
        self.assertIn("joint_force_waveform_diagnostics", comparison.observed)

    def test_phase39_validator_rejects_returned_physical_pendulum_timing_blocker(
        self,
    ) -> None:
        import scripts.validate_docs as validate_docs

        actual = load_claim_report(
            ROOT / "reports/experiment_matrix/single_body_physical_pendulum_comparison.json"
        )
        overblocked = replace(
            actual,
            observed={
                **actual.observed,
                "blocking_reasons": [
                    *actual.observed["blocking_reasons"],
                    "paper_timing_missing",
                ],
            },
        )

        def fake_load_claim_report(path):
            if str(path).endswith("single_body_physical_pendulum_comparison.json"):
                return overblocked
            return load_claim_report(path)

        with patch.object(validate_docs, "load_claim_report", side_effect=fake_load_claim_report):
            with self.assertRaises(SystemExit) as context:
                validate_docs.validate_phase39_record()

        self.assertIn("paper_timing_missing", str(context.exception))

    def test_phase40_physical_pendulum_joint_force_reference_is_bounded(self) -> None:
        data = yaml.safe_load((ROOT / "docs/reference/paper-claims.yaml").read_text())
        physical_pendulum = next(
            claim for claim in data["claims"] if claim["claim_id"] == "experiment.single_body.physical_pendulum"
        )
        self.assertEqual(physical_pendulum["reproduction_status"], "intended")

        text = (ROOT / "docs/reference/claim-boundaries.md").read_text()
        current = claim_boundary_bullet(text, "This repository contains Phase 40")
        verified = claim_boundary_bullet(text, "Phase 40 verifies")
        non_claim = claim_boundary_bullet(text, "Phase 40 does not verify")
        forbidden = claim_boundary_bullet(
            text,
            "Phase 40 physical-pendulum scalar joint-force diagnostics",
        )

        self.assertIn("scalar physical-pendulum joint-force reference", current)
        self.assertIn("physical_pendulum_angular_velocity_reference", verified)
        self.assertIn("physical_pendulum_joint_force_reference", verified)
        self.assertIn("max_abs_joint_force_error_n", verified)
        self.assertIn("joint_force_waveform_diagnostics", verified)
        self.assertIn("paper's exact physical-pendulum geometry", non_claim)
        self.assertIn("paper joint-force waveform", non_claim)
        self.assertIn("passed physical-pendulum experiment", forbidden)
        self.assertIn("any passed `experiment.*` claim", forbidden)

    def test_phase40_record_has_required_evidence_fields(self) -> None:
        text = (
            ROOT / "docs/records/2026-05-17-phase40-physical-pendulum-joint-force-reference.md"
        ).read_text()

        for snippet in (
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
            "diagnostic_scalar_reference_not_paper_geometry",
            "matched_sample_count = `5`",
            "## Claim Impact",
            "No `experiment.*` claim is passed.",
            "`experiment.single_body.physical_pendulum` remains intended.",
            "scalar/procedural diagnostic, not paper geometry",
            "## Verification Commands",
            "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py",
            "git diff --check",
        ):
            self.assertIn(snippet, text)
        self.assertNotIn("TO_BE_BACKFILLED_PHASE40", text)
        self.assertNotIn("phase40-working-tree", text)

    def test_phase40_current_physical_pendulum_reports_record_joint_force_diagnostic(
        self,
    ) -> None:
        analytic = load_claim_report(
            ROOT / "reports/experiment_matrix/single_body_physical_pendulum_analytic_reference.json"
        )
        mabd = load_claim_report(
            ROOT / "reports/experiment_matrix/single_body_physical_pendulum_mabd_newton.json"
        )
        rbd = load_claim_report(
            ROOT / "reports/experiment_matrix/single_body_physical_pendulum_rbd_baseline.json"
        )
        comparison = load_claim_report(
            ROOT / "reports/experiment_matrix/single_body_physical_pendulum_comparison.json"
        )

        self.assertEqual(
            analytic.expected["joint_force_reference_model"],
            "scalar_point_pendulum_radial_reaction",
        )
        self.assertEqual(analytic.observed["joint_force_samples_n"][0]["joint_force_magnitude_n"], 0.0)
        self.assertGreater(analytic.observed["max_joint_force_magnitude_n"], 0.0)
        for report in (mabd, rbd):
            self.assertIn("max_abs_joint_force_error_n", report.observed)
            self.assertLessEqual(
                report.observed["max_abs_joint_force_error_n"],
                report.threshold["max_abs_joint_force_error_n"],
            )
            self.assertIn(
                "reference_joint_force_magnitude_n",
                report.observed["angle_samples_rad"][-1],
            )
            self.assertIn("abs_joint_force_error_n", report.observed["angle_samples_rad"][-1])
            self.assertIn("pendulum_geometry_unknown", report.observed["blocking_reasons"])
            self.assertNotIn(
                "joint_force_waveform_agreement_missing",
                report.observed["blocking_reasons"],
            )
        self.assertEqual(
            comparison.observed["missing_paper_metrics"],
            ["joint_force_error:paper_geometry_unknown"],
        )
        self.assertEqual(
            comparison.observed["paper_metric_statuses"]["joint_force_error"]["status"],
            "diagnostic_scalar_reference_not_paper_geometry",
        )
        diagnostics = comparison.observed["joint_force_waveform_diagnostics"]
        self.assertEqual(diagnostics["matched_sample_count"], 5)
        self.assertEqual(diagnostics["reference_model"], "scalar_point_pendulum_radial_reaction")
        self.assertEqual(len(diagnostics["joint_force_sample_differences_n"]), 5)

    def test_phase40_validator_rejects_returned_joint_force_blocker(self) -> None:
        import scripts.validate_docs as validate_docs

        actual = load_claim_report(
            ROOT / "reports/experiment_matrix/single_body_physical_pendulum_comparison.json"
        )
        overblocked = replace(
            actual,
            observed={
                **actual.observed,
                "blocking_reasons": [
                    *actual.observed["blocking_reasons"],
                    "joint_force_waveform_agreement_missing",
                ],
            },
        )

        def fake_load_claim_report(path):
            if str(path).endswith("single_body_physical_pendulum_comparison.json"):
                return overblocked
            return load_claim_report(path)

        with patch.object(validate_docs, "load_claim_report", side_effect=fake_load_claim_report):
            with self.assertRaises(SystemExit) as context:
                validate_docs.validate_phase40_record()

        self.assertIn("joint-force blocker", str(context.exception))

    def test_phase41_physical_pendulum_geometry_source_audit_is_bounded(self) -> None:
        data = yaml.safe_load((ROOT / "docs/reference/paper-claims.yaml").read_text())
        physical_pendulum = next(
            claim for claim in data["claims"] if claim["claim_id"] == "experiment.single_body.physical_pendulum"
        )
        self.assertEqual(physical_pendulum["reproduction_status"], "intended")

        text = (ROOT / "docs/reference/claim-boundaries.md").read_text()
        current = claim_boundary_bullet(text, "This repository contains Phase 41")
        verified = claim_boundary_bullet(text, "Phase 41 verifies")
        non_claim = claim_boundary_bullet(text, "Phase 41 does not verify")
        forbidden = claim_boundary_bullet(
            text,
            "Phase 41 physical-pendulum source-asset audit",
        )

        self.assertIn("physical-pendulum geometry source-asset audit", current)
        self.assertIn("physical_pendulum_geometry_source_audit", verified)
        self.assertIn("source_tree_paths", verified)
        self.assertIn("scanned_tex_paths", verified)
        self.assertIn("absence_findings", verified)
        self.assertIn("source_assets_found_geometry_parameters_missing", verified)
        self.assertIn("private author assets", non_claim)
        self.assertIn("paper-faithful physical-pendulum geometry", non_claim)
        self.assertIn("passed physical-pendulum experiment", forbidden)
        self.assertIn("any passed `experiment.*` claim", forbidden)

    def test_phase41_record_has_required_evidence_fields(self) -> None:
        text = (
            ROOT / "docs/records/2026-05-17-phase41-physical-pendulum-geometry-source-audit.md"
        ).read_text()

        for snippet in (
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
        ):
            self.assertIn(snippet, text)
        self.assertNotIn("TO_BE_BACKFILLED_PHASE41", text)
        self.assertNotIn("phase41-working-tree", text)

    def test_phase41_current_physical_pendulum_reports_retain_geometry_blocker(
        self,
    ) -> None:
        config = yaml.safe_load(
            (ROOT / "configs/experiments/single_body_physical_pendulum.yaml").read_text()
        )
        matrix = yaml.safe_load(
            (ROOT / "configs/experiments/paper_experiment_matrix.yaml").read_text()
        )
        experiment = next(
            item for item in matrix["experiments"] if item["claim_id"] == "experiment.single_body.physical_pendulum"
        )
        self.assertIn("pendulum_geometry_unknown", experiment["blocking_reasons"])
        self.assertIn("pendulum_geometry_unknown", config["report"]["failure_reason"])

        for report_path in (
            ROOT / "reports/experiment_matrix/single_body_physical_pendulum_analytic_reference.json",
            ROOT / "reports/experiment_matrix/single_body_physical_pendulum_mabd_development.json",
            ROOT / "reports/experiment_matrix/single_body_physical_pendulum_mabd_newton.json",
            ROOT / "reports/experiment_matrix/single_body_physical_pendulum_rbd_baseline.json",
            ROOT / "reports/experiment_matrix/single_body_physical_pendulum_comparison.json",
        ):
            report = load_claim_report(report_path)
            self.assertEqual(report.status.value, "incomplete")
            self.assertIs(report.observed["full_experiment_claim_passed"], False)
            self.assertIn("pendulum_geometry_unknown", report.observed["blocking_reasons"])
        comparison = load_claim_report(
            ROOT / "reports/experiment_matrix/single_body_physical_pendulum_comparison.json"
        )
        self.assertEqual(
            comparison.observed["missing_paper_metrics"],
            ["joint_force_error:paper_geometry_unknown"],
        )

    def test_phase41_validator_rejects_geometry_reconstructed_status(self) -> None:
        import scripts.validate_docs as validate_docs
        from mabd_reproduction.paper_source_audit import physical_pendulum_geometry_source_audit

        actual = physical_pendulum_geometry_source_audit()
        overclaimed = replace(
            actual,
            status="geometry_reconstructed",
            missing_parameters=(),
            blockers=(),
        )

        with patch.object(
            validate_docs,
            "physical_pendulum_geometry_source_audit",
            return_value=overclaimed,
        ):
            with self.assertRaises(SystemExit) as context:
                validate_docs.validate_phase41_record()

        self.assertIn("geometry source audit status", str(context.exception))

    def test_phase42_spinning_box_report_artifacts_are_bounded(self) -> None:
        data = yaml.safe_load((ROOT / "docs/reference/paper-claims.yaml").read_text())
        spinning_box = next(
            claim for claim in data["claims"] if claim["claim_id"] == "experiment.single_body.spinning_box"
        )
        self.assertEqual(spinning_box["reproduction_status"], "intended")

        matrix = yaml.safe_load((ROOT / "configs/experiments/paper_experiment_matrix.yaml").read_text())
        matrix_entry = next(
            item for item in matrix["experiments"] if item["claim_id"] == "experiment.single_body.spinning_box"
        )
        self.assertEqual(matrix_entry["reproduction_status"], "blocked_by_baselines")
        self.assertIn("mabd_newton_report_incomplete", matrix_entry["blocking_reasons"])
        self.assertIn("spinning_box_comparison_report_incomplete", matrix_entry["blocking_reasons"])

        text = (ROOT / "docs/reference/claim-boundaries.md").read_text()
        current = claim_boundary_bullet(text, "This repository contains Phase 42")
        verified = claim_boundary_bullet(text, "Phase 42 verifies")
        non_claim = claim_boundary_bullet(text, "Phase 42 does not verify")
        forbidden = claim_boundary_bullet(text, "Phase 42 spinning-box report artifacts")

        self.assertIn("spinning-box report-artifact evidence", current)
        self.assertIn("committed compact JSON reports", verified)
        self.assertIn("rbd_implicit_baseline` lane gate status: `passed", verified)
        self.assertIn("mabd_newton` lane gate status: `incomplete", verified)
        self.assertIn("mabd_paper_horizon_diagnostic_thresholds_violated", verified)
        self.assertIn("mabd_kinematic_feasibility_blocker_recorded", verified)
        self.assertIn("spinning_box_comparison_pass_gate_not_enabled", verified)
        self.assertIn("passed spinning-box experiment", non_claim)
        self.assertIn("M-ABD lane pass", non_claim)
        self.assertIn("any passed `experiment.*` claim", non_claim)
        self.assertIn("not a passed spinning-box experiment", forbidden)
        self.assertIn("any passed `experiment.*` claim", forbidden)

    def test_phase42_record_has_required_evidence_fields(self) -> None:
        text = (
            ROOT / "docs/records/2026-05-17-phase42-spinning-box-report-artifacts.md"
        ).read_text()

        for snippet in (
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
        ):
            self.assertIn(snippet, text)
        self.assertNotIn("TO_BE_BACKFILLED_PHASE42", text)
        self.assertNotIn("phase42-working-tree", text)

    def test_phase42_validator_rejects_spinning_box_mabd_lane_gate_pass(self) -> None:
        import scripts.validate_docs as validate_docs

        actual = load_claim_report(
            ROOT / "reports/experiment_matrix/single_body_spinning_box_comparison.json"
        )
        overclaimed = replace(
            actual,
            observed={
                **actual.observed,
                "lane_gate_statuses": {
                    **actual.observed["lane_gate_statuses"],
                    "mabd_newton": "passed",
                },
                "blocking_reasons": ["spinning_box_comparison_pass_gate_not_enabled"],
            },
        )

        def fake_load_claim_report(path):
            if str(path).endswith("single_body_spinning_box_comparison.json"):
                return overclaimed
            return load_claim_report(path)

        with patch.object(validate_docs, "load_claim_report", side_effect=fake_load_claim_report):
            with self.assertRaises(SystemExit) as context:
                validate_docs.validate_phase42_record()

        self.assertIn("MABD lane gate status", str(context.exception))

    def test_phase42_validator_rejects_spinning_box_paper_horizon_lane_gate_pass(self) -> None:
        import scripts.validate_docs as validate_docs

        actual = load_claim_report(
            ROOT / "reports/experiment_matrix/single_body_spinning_box_paper_horizon.json"
        )
        overclaimed = replace(
            actual,
            observed={
                **actual.observed,
                "lane_gate_status": "passed",
            },
        )

        def fake_load_claim_report(path):
            if str(path).endswith("single_body_spinning_box_paper_horizon.json"):
                return overclaimed
            return load_claim_report(path)

        with patch.object(validate_docs, "load_claim_report", side_effect=fake_load_claim_report):
            with self.assertRaises(SystemExit) as context:
                validate_docs.validate_phase42_record()

        self.assertIn("paper-horizon report", str(context.exception))

    def test_phase42_validator_rejects_stale_spinning_box_comparison_metrics(self) -> None:
        import scripts.validate_docs as validate_docs

        actual = load_claim_report(
            ROOT / "reports/experiment_matrix/single_body_spinning_box_comparison.json"
        )
        stale = replace(
            actual,
            observed={
                **actual.observed,
                "lane_metrics": {
                    **actual.observed["lane_metrics"],
                    "mabd_newton": {
                        **actual.observed["lane_metrics"]["mabd_newton"],
                        "energy_drift": 0.0,
                    },
                },
            },
        )

        def fake_load_claim_report(path):
            if str(path).endswith("single_body_spinning_box_comparison.json"):
                return stale
            return load_claim_report(path)

        with patch.object(validate_docs, "load_claim_report", side_effect=fake_load_claim_report):
            with self.assertRaises(SystemExit) as context:
                validate_docs.validate_phase42_record()

        self.assertIn("lane metric mismatch", str(context.exception))

    def test_phase42_validator_rejects_record_hash_mismatch(self) -> None:
        import scripts.validate_docs as validate_docs

        actual_sha256_file = validate_docs.sha256_file

        def fake_sha256_file(path):
            if str(path).endswith("single_body_spinning_box.json"):
                return "0" * 64
            return actual_sha256_file(path)

        with patch.object(validate_docs, "sha256_file", side_effect=fake_sha256_file):
            with self.assertRaises(SystemExit) as context:
                validate_docs.validate_phase42_record()

        self.assertIn("sha256 mismatch", str(context.exception))

    def test_phase43_t_handle_rk4_reference_is_bounded(self) -> None:
        data = yaml.safe_load((ROOT / "docs/reference/paper-claims.yaml").read_text())
        t_handle_claim = next(
            claim for claim in data["claims"] if claim["claim_id"] == "experiment.single_body.t_handle"
        )
        self.assertEqual(t_handle_claim["reproduction_status"], "intended")
        self.assertIn("exact_t_handle_geometry_unknown", t_handle_claim["conflict_note"])
        self.assertIn("raw_t_handle_reference_curve_data_missing", t_handle_claim["conflict_note"])

        matrix = yaml.safe_load((ROOT / "configs/experiments/paper_experiment_matrix.yaml").read_text())
        matrix_entry = next(
            item for item in matrix["experiments"] if item["claim_id"] == "experiment.single_body.t_handle"
        )
        self.assertEqual(matrix_entry["reproduction_status"], "planned")
        self.assertIn("exact_t_handle_geometry_unknown", matrix_entry["blocking_reasons"])
        self.assertIn("raw_t_handle_reference_curve_data_missing", matrix_entry["blocking_reasons"])

        text = (ROOT / "docs/reference/claim-boundaries.md").read_text()
        current = claim_boundary_bullet(text, "This repository contains Phase 43")
        verified = claim_boundary_bullet(text, "Phase 43 verifies")
        non_claim = claim_boundary_bullet(text, "Phase 43 does not verify")
        forbidden = claim_boundary_bullet(text, "Phase 43 T-handle RK4 reference")

        self.assertIn("T-handle RK4 reference diagnostic lane", current)
        self.assertIn("rbd_rk4_reference", verified)
        self.assertIn("source-backed", verified)
        self.assertIn("raw_t_handle_reference_curve_data_missing", verified)
        self.assertIn("passed T-handle experiment", non_claim)
        self.assertIn("paper-faithful T-handle geometry", non_claim)
        self.assertIn("M-ABD T-handle lane pass", non_claim)
        self.assertIn("not a passed T-handle experiment", forbidden)
        self.assertIn("any passed `experiment.*` claim", forbidden)

    def test_phase43_record_has_required_evidence_fields(self) -> None:
        text = (ROOT / "docs/records/2026-05-18-phase43-t-handle-rk4-reference.md").read_text()

        for snippet in (
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
        ):
            self.assertIn(snippet, text)
        self.assertNotIn("TO_BE_BACKFILLED_PHASE43", text)
        self.assertNotIn("phase43-working-tree", text)

    def test_phase43_validator_rejects_t_handle_lane_gate_pass(self) -> None:
        import scripts.validate_docs as validate_docs

        actual = load_claim_report(
            ROOT / "reports/experiment_matrix/single_body_t_handle_rk4_reference.json"
        )
        overclaimed = replace(
            actual,
            observed={
                **actual.observed,
                "lane_gate_status": "passed",
                "full_experiment_claim_passed": True,
            },
        )

        def fake_load_claim_report(path):
            if str(path).endswith("single_body_t_handle_rk4_reference.json"):
                return overclaimed
            return load_claim_report(path)

        with patch.object(validate_docs, "load_claim_report", side_effect=fake_load_claim_report):
            with self.assertRaises(SystemExit) as context:
                validate_docs.validate_phase43_record()

        self.assertIn("must not expose a passed lane gate", str(context.exception))

    def test_phase43_validator_rejects_t_handle_record_hash_mismatch(self) -> None:
        import scripts.validate_docs as validate_docs

        actual_sha256_file = validate_docs.sha256_file
        actual = load_claim_report(
            ROOT / "reports/experiment_matrix/single_body_t_handle_rk4_reference.json"
        )
        legacy_report = replace(
            actual,
            source_commit="d741e6f5b1d85f7c02afb520f55b8bb273947604",
        )

        def fake_load_claim_report(path):
            if str(path).endswith("single_body_t_handle_rk4_reference.json"):
                return legacy_report
            return load_claim_report(path)

        def fake_sha256_file(path):
            if str(path).endswith("single_body_t_handle_rk4_reference.json"):
                return "0" * 64
            return actual_sha256_file(path)

        with patch.object(validate_docs, "load_claim_report", side_effect=fake_load_claim_report):
            with patch.object(validate_docs, "sha256_file", side_effect=fake_sha256_file):
                with self.assertRaises(SystemExit) as context:
                    validate_docs.validate_phase43_record()

        self.assertIn("sha256 mismatch", str(context.exception))

    def test_phase43_validator_accepts_phase59_relative_energy_loss_report_upgrade(self) -> None:
        import scripts.validate_docs as validate_docs

        actual_sha256_file = validate_docs.sha256_file

        def fake_sha256_file(path):
            if str(path).endswith("single_body_t_handle_rk4_reference.json"):
                return "0" * 64
            return actual_sha256_file(path)

        with patch.object(validate_docs, "sha256_file", side_effect=fake_sha256_file):
            validate_docs.validate_phase43_record()

    def test_phase43_validator_rejects_phase59_upgrade_without_relative_energy_loss(self) -> None:
        import scripts.validate_docs as validate_docs

        actual = load_claim_report(
            ROOT / "reports/experiment_matrix/single_body_t_handle_rk4_reference.json"
        )
        samples = [
            {key: value for key, value in sample.items() if key != "relative_energy_loss"}
            for sample in actual.observed["angular_velocity_samples"]
        ]
        without_energy_loss = replace(
            actual,
            observed={**actual.observed, "angular_velocity_samples": samples},
        )

        def fake_load_claim_report(path):
            if str(path).endswith("single_body_t_handle_rk4_reference.json"):
                return without_energy_loss
            return load_claim_report(path)

        with patch.object(validate_docs, "load_claim_report", side_effect=fake_load_claim_report):
            with self.assertRaises(SystemExit) as context:
                validate_docs.validate_phase43_record()

        self.assertIn("must list the report source_commit", str(context.exception))

    def test_phase57_t_handle_comparison_protocol_is_bounded(self) -> None:
        data = yaml.safe_load((ROOT / "docs/reference/paper-claims.yaml").read_text())
        t_handle_claim = next(
            claim for claim in data["claims"] if claim["claim_id"] == "experiment.single_body.t_handle"
        )
        self.assertEqual(t_handle_claim["reproduction_status"], "intended")
        self.assertIn("t_handle_comparison_report_incomplete", t_handle_claim["conflict_note"])
        self.assertNotIn("t_handle_comparison_report_missing", t_handle_claim["conflict_note"])

        matrix = yaml.safe_load((ROOT / "configs/experiments/paper_experiment_matrix.yaml").read_text())
        matrix_entry = next(
            item for item in matrix["experiments"] if item["claim_id"] == "experiment.single_body.t_handle"
        )
        self.assertEqual(matrix_entry["reproduction_status"], "planned")
        self.assertIn("t_handle_comparison_report_incomplete", matrix_entry["blocking_reasons"])
        self.assertNotIn("t_handle_comparison_report_missing", matrix_entry["blocking_reasons"])

        text = (ROOT / "docs/reference/claim-boundaries.md").read_text()
        current = claim_boundary_bullet(text, "This repository contains Phase 57")
        verified = claim_boundary_bullet(text, "Phase 57 verifies")
        non_claim = claim_boundary_bullet(text, "Phase 57 does not verify")
        forbidden = claim_boundary_bullet(text, "Phase 57 T-handle comparison protocol")

        self.assertIn("T-handle comparison protocol", current)
        self.assertIn("t_handle_comparison_protocol", verified)
        self.assertIn("input report provenance and sha256 hashes", verified)
        self.assertIn("reference_not_paper_geometry = true", verified)
        self.assertIn("finite aligned-sample RMSE", verified)
        self.assertIn("sample_grid_flip_delta_unavailable", verified)
        self.assertIn("duplicate sample-index guard fields", verified)
        self.assertIn("energy_loss", verified)
        self.assertIn("passed T-handle experiment", non_claim)
        self.assertIn("paper-faithful T-handle geometry", non_claim)
        self.assertIn("raw waveform agreement", non_claim)
        self.assertIn("must not be described as a passed T-handle experiment", forbidden)
        self.assertIn("any passed `experiment.*` claim", forbidden)

        report = load_claim_report(
            ROOT / "reports/experiment_matrix/single_body_t_handle_comparison.json"
        )
        self.assertEqual(report.status.value, "incomplete")
        self.assertEqual(report.baseline_lane, "t_handle_comparison_protocol")
        self.assertEqual(report.solver_mode, "t_handle_multilane_comparison_development")
        self.assertFalse(report.observed["full_experiment_claim_passed"])
        self.assertEqual(report.observed["missing_required_lanes"], [])
        self.assertEqual(report.observed["matched_sample_index_count"], 9)
        self.assertEqual(report.observed["finite_matched_sample_count"], 9)
        self.assertEqual(report.observed["time_aligned_sample_count"], 9)
        self.assertFalse(report.observed["time_grid_mismatch"])
        self.assertFalse(report.observed["sample_nonfinite"])
        self.assertFalse(report.observed["sample_index_duplicate"])
        self.assertEqual(report.observed["duplicate_rk4_sample_indices"], [])
        self.assertEqual(report.observed["duplicate_mabd_sample_indices"], [])
        self.assertIn("t_handle_comparison_report_incomplete", report.observed["blocking_reasons"])
        self.assertIn("sample_grid_flip_delta_unavailable", report.observed["blocking_reasons"])
        self.assertNotIn("t_handle_comparison_report_missing", report.observed["blocking_reasons"])
        provenance = report.observed["input_report_provenance"]
        self.assertTrue(provenance["rbd_rk4_reference"]["reference_not_paper_geometry"])
        self.assertTrue(provenance["mabd_newton"]["reference_not_paper_geometry"])

        metric_statuses = report.observed["paper_metric_statuses"]
        self.assertEqual(
            metric_statuses["flip_timing_error"]["status"],
            "sample_grid_flip_delta_unavailable_not_paper_timing",
        )
        self.assertEqual(
            metric_statuses["intermediate_axis_angular_velocity_waveform"]["status"],
            "paper_figure_digitized_color_family_error_diagnostic_available_not_agreement"
            if report.observed.get("digitized_figure_curve_agreement_available") is True
            else (
                "paper_figure_digitized_color_family_available_not_curve_agreement"
                if report.observed.get("digitized_figure_reference_available") is True
                else "diagnostic_available_not_paper_curve"
            ),
        )
        self.assertEqual(
            metric_statuses["energy_loss"]["status"],
            "paper_figure_digitized_energy_loss_error_diagnostic_available_not_agreement"
            if report.observed.get("digitized_figure_curve_agreement_available") is True
            else (
                "paper_figure_digitized_color_family_available_not_energy_agreement"
                if report.observed.get("digitized_figure_reference_available") is True
                else "signed_energy_drift_diagnostic_not_paper_loss"
            ),
        )

        record_text = (
            ROOT / "docs/records/2026-05-18-phase57-t-handle-comparison-protocol.md"
        ).read_text()
        for snippet in (
            "passed_for_t_handle_comparison_protocol",
            "reports/experiment_matrix/single_body_t_handle_comparison.json",
            "608fa8676a1849bea67c6c9c3c4de999d2662ed68f6ac346d140211ebc33c6e2",
            "t_handle_multilane_comparison_development",
            "t_handle_comparison_protocol",
            "sample_grid_flip_delta_unavailable_not_paper_timing",
            "diagnostic_available_not_paper_curve",
            "signed_energy_drift_diagnostic_not_paper_loss",
            "No `experiment.*` claim is passed.",
        ):
            self.assertIn(snippet, record_text)

    def test_phase57_validator_rejects_t_handle_comparison_pass(self) -> None:
        import scripts.validate_docs as validate_docs

        actual = load_claim_report(
            ROOT / "reports/experiment_matrix/single_body_t_handle_comparison.json"
        )
        overclaimed = replace(
            actual,
            observed={
                **actual.observed,
                "full_experiment_claim_passed": True,
            },
        )

        def fake_load_claim_report(path):
            if str(path).endswith("single_body_t_handle_comparison.json"):
                return overclaimed
            return load_claim_report(path)

        with patch.object(validate_docs, "load_claim_report", side_effect=fake_load_claim_report):
            with self.assertRaises(SystemExit) as context:
                validate_docs.validate_phase57_record()

        self.assertIn("must not pass full experiment claim", str(context.exception))

    def test_phase58_t_handle_figure_curve_digitization_is_bounded(self) -> None:
        data = yaml.safe_load((ROOT / "docs/reference/paper-claims.yaml").read_text())
        t_handle_claim = next(
            claim for claim in data["claims"] if claim["claim_id"] == "experiment.single_body.t_handle"
        )
        self.assertEqual(t_handle_claim["reproduction_status"], "intended")
        self.assertIn("raw_t_handle_reference_curve_data_missing", t_handle_claim["conflict_note"])

        text = (ROOT / "docs/reference/claim-boundaries.md").read_text()
        current = claim_boundary_bullet(text, "This repository contains Phase 58")
        verified = claim_boundary_bullet(text, "Phase 58 verifies")
        non_claim = claim_boundary_bullet(text, "Phase 58 does not verify")
        forbidden = claim_boundary_bullet(text, "Phase 58 T-handle paper-figure digitization")

        self.assertIn("paper-figure color-family digitization", current)
        self.assertIn("pdftocairo 22.02.0", verified)
        self.assertIn("T-handle.pdf", verified)
        self.assertIn("blue/orange/green color-family samples", verified)
        self.assertIn("paper_figure_curves", verified)
        self.assertIn("without any curve or energy-loss agreement pass", verified)
        self.assertIn("authors' raw simulation data", non_claim)
        self.assertIn("solid/dashed line-style separation", non_claim)
        self.assertIn("specific legend-entry curve identity", non_claim)
        self.assertIn("must not be described as", forbidden)
        self.assertIn("any passed `experiment.*` claim", forbidden)

        figure_report = load_claim_report(
            ROOT / "reports/experiment_matrix/single_body_t_handle_figure_curves.json"
        )
        self.assertEqual(figure_report.status, EvidenceStatus.INCOMPLETE)
        self.assertEqual(figure_report.baseline_lane, "paper_figure_digitization")
        self.assertEqual(figure_report.solver_mode, "t_handle_paper_figure_digitization")
        self.assertEqual(figure_report.backend, "pdftocairo_pillow")
        self.assertEqual(figure_report.observed["lane_status"], "figure_color_families_digitized")
        self.assertEqual(figure_report.observed["figure_curve_scope"], "color_family_digitization_only")
        self.assertTrue(figure_report.observed["reference_curve_available"])
        self.assertFalse(figure_report.observed["full_experiment_claim_passed"])
        self.assertEqual(figure_report.raw_outputs, {"figure_samples": "compact_numeric_samples_only"})

        comparison_report = load_claim_report(
            ROOT / "reports/experiment_matrix/single_body_t_handle_comparison.json"
        )
        self.assertTrue(comparison_report.observed["digitized_figure_reference_available"])
        self.assertIn("paper_figure_curves", comparison_report.observed["input_report_provenance"])
        self.assertEqual(
            comparison_report.observed["paper_metric_statuses"][
                "intermediate_axis_angular_velocity_waveform"
            ]["status"],
            "paper_figure_digitized_color_family_error_diagnostic_available_not_agreement",
        )
        self.assertEqual(
            comparison_report.observed["paper_metric_statuses"]["energy_loss"]["status"],
            "paper_figure_digitized_energy_loss_error_diagnostic_available_not_agreement",
        )
        self.assertIn(
            "t_handle_digitized_figure_curve_agreement_not_passed",
            comparison_report.observed["blocking_reasons"],
        )
        self.assertFalse(comparison_report.observed["full_experiment_claim_passed"])

        record_text = (
            ROOT / "docs/records/2026-05-18-phase58-t-handle-figure-curves.md"
        ).read_text()
        for snippet in (
            "passed_for_t_handle_figure_curve_digitization_lane",
            "reports/experiment_matrix/single_body_t_handle_figure_curves.json",
            "975f1e1fc27d76073145a6981a9f8e87907fac908333d8303a4386f5a5e743c6",
            "reports/experiment_matrix/single_body_t_handle_comparison.json",
            "80b5ac9bc0782f3ad51314945a35a7f6cc0505f2e916abbc2898bbf3c00ab6d2",
            "t_handle_paper_figure_digitization",
            "paper_figure_digitized_color_family_available_not_curve_agreement",
            "paper_figure_digitized_color_family_available_not_energy_agreement",
            "No `experiment.*` claim is passed.",
        ):
            self.assertIn(snippet, record_text)

    def test_phase59_t_handle_figure_agreement_diagnostics_is_bounded(self) -> None:
        text = (ROOT / "docs/reference/claim-boundaries.md").read_text()
        current = claim_boundary_bullet(text, "This repository contains Phase 59")
        verified = claim_boundary_bullet(text, "Phase 59 verifies")
        non_claim = claim_boundary_bullet(text, "Phase 59 does not verify")
        forbidden = claim_boundary_bullet(
            text, "Phase 59 T-handle digitized-figure agreement"
        )

        self.assertIn("digitized-figure agreement diagnostic evidence", current)
        self.assertIn("normalized-time numeric error diagnostics", verified)
        self.assertIn("relative-energy-loss RMSE/max-error diagnostics", verified)
        self.assertIn("normalized_figure_time_not_paper_raw_time", verified)
        self.assertIn("numeric_best_fit_not_legend_identity", verified)
        self.assertIn("diagnostic_only_not_curve_agreement", verified)
        self.assertIn("digitized_figure_curve_agreement_passed = false", verified)
        self.assertIn("authors' raw simulation data", non_claim)
        self.assertIn("paper raw-time alignment", non_claim)
        self.assertIn("paper energy-loss agreement", non_claim)
        self.assertIn("comparison pass gate", forbidden)
        self.assertIn("any passed `experiment.*` claim", forbidden)

        rk4_report = load_claim_report(
            ROOT / "reports/experiment_matrix/single_body_t_handle_rk4_reference.json"
        )
        mabd_report = load_claim_report(
            ROOT / "reports/experiment_matrix/single_body_t_handle_mabd_newton.json"
        )
        for report in (rk4_report, mabd_report):
            self.assertEqual(report.source_commit, "5d8a0079876d17568464a87c320c53be2d898089")
            self.assertEqual(report.status, EvidenceStatus.INCOMPLETE)
            samples = report.observed["angular_velocity_samples"]
            self.assertEqual(len(samples), 9)
            self.assertEqual(samples[0]["relative_energy_loss"], 0.0)
            for sample in samples:
                self.assertTrue(math.isfinite(float(sample["relative_energy_loss"])))

        comparison_report = load_claim_report(
            ROOT / "reports/experiment_matrix/single_body_t_handle_comparison.json"
        )
        self.assertEqual(
            comparison_report.source_commit,
            "5d8a0079876d17568464a87c320c53be2d898089",
        )
        self.assertEqual(comparison_report.status, EvidenceStatus.INCOMPLETE)
        observed = comparison_report.observed
        self.assertTrue(observed["digitized_figure_reference_available"])
        self.assertTrue(observed["digitized_figure_curve_agreement_available"])
        self.assertFalse(observed["digitized_figure_curve_agreement_passed"])
        self.assertIn("paper_figure_curves", observed["input_report_provenance"])
        self.assertEqual(
            observed["paper_metric_statuses"]["intermediate_axis_angular_velocity_waveform"][
                "status"
            ],
            "paper_figure_digitized_color_family_error_diagnostic_available_not_agreement",
        )
        self.assertEqual(
            observed["paper_metric_statuses"]["energy_loss"]["status"],
            "paper_figure_digitized_energy_loss_error_diagnostic_available_not_agreement",
        )
        for blocker in (
            "exact_t_handle_geometry_unknown",
            "raw_t_handle_reference_curve_data_missing",
            "mabd_newton_report_incomplete",
            "t_handle_comparison_report_incomplete",
            "t_handle_timing_evidence_missing",
            "t_handle_comparison_pass_gate_not_enabled",
            "sample_grid_flip_delta_unavailable",
            "t_handle_digitized_figure_curve_agreement_not_passed",
        ):
            self.assertIn(blocker, observed["blocking_reasons"])

        diagnostics = observed["digitized_figure_curve_agreement_diagnostics"]
        self.assertEqual(
            set(diagnostics),
            {"intermediate_axis_angular_velocity_waveform", "energy_loss"},
        )
        for metric, lanes in diagnostics.items():
            self.assertEqual(set(lanes), {"rbd_rk4_reference", "mabd_newton"})
            for lane, diagnostic in lanes.items():
                self.assertEqual(diagnostic["metric"], metric)
                self.assertEqual(diagnostic["lane"], lane)
                self.assertEqual(diagnostic["status"], "diagnostic_available_not_pass_gate")
                self.assertGreater(diagnostic["matched_sample_count"], 0)
                self.assertIn(diagnostic["best_color_family"], {"blue", "orange", "green"})
                self.assertTrue(math.isfinite(float(diagnostic["best_rmse"])))
                self.assertTrue(math.isfinite(float(diagnostic["best_max_abs_error"])))
                self.assertEqual(
                    diagnostic["best_color_family_claim_status"],
                    "numeric_best_fit_not_legend_identity",
                )
                self.assertEqual(
                    diagnostic["agreement_claim_status"],
                    "diagnostic_only_not_curve_agreement",
                )
                normalization = diagnostic["time_normalization"]
                self.assertEqual(
                    normalization["claim_status"],
                    "normalized_figure_time_not_paper_raw_time",
                )
                self.assertEqual(
                    normalization["mapping"],
                    "lane_time_s / diagnostic_duration_s * 100",
                )
                self.assertEqual(normalization["duration_source"], "lane_report_observed_duration_s")
                self.assertEqual(normalization["figure_time_range"], [0.0, 100.0])
                self.assertEqual(set(diagnostic["all_color_family_errors"]), {"blue", "orange", "green"})
                for errors in diagnostic["all_color_family_errors"].values():
                    self.assertGreater(errors["matched_sample_count"], 0)
                    self.assertTrue(math.isfinite(float(errors["rmse"])))
                    self.assertTrue(math.isfinite(float(errors["max_abs_error"])))
                    self.assertTrue(math.isfinite(float(errors["mean_error"])))

        record_text = (
            ROOT
            / "docs/records/2026-05-18-phase59-t-handle-figure-agreement-diagnostics.md"
        ).read_text()
        for snippet in (
            "passed_for_t_handle_digitized_figure_agreement_diagnostic_lane",
            "5d8a0079876d17568464a87c320c53be2d898089",
            "reports/experiment_matrix/single_body_t_handle_rk4_reference.json",
            "0a0f1be3ffbfced0dd4ef463ee3419c119775a46ddde17807748d1b957c5b1b3",
            "reports/experiment_matrix/single_body_t_handle_mabd_newton.json",
            "a04556cdf375fa63d9a9a927ac3fa9732351a07be3aa26c82e617a492f198199",
            "reports/experiment_matrix/single_body_t_handle_comparison.json",
            "a3b0a8acb993d99d842027fab7c10a8df7deffd903d1507b2851fbcd35fd3766",
            "normalized_figure_time_not_paper_raw_time",
            "numeric_best_fit_not_legend_identity",
            "diagnostic_only_not_curve_agreement",
            "sample_grid_flip_delta_unavailable",
            "No `experiment.*` claim is passed.",
        ):
            self.assertIn(snippet, record_text)
        self.assertNotIn("TO_BE_BACKFILLED_PHASE59", record_text)
        self.assertNotIn("phase59-working-tree", record_text)

    def test_phase60_reproduction_gap_audit_is_bounded(self) -> None:
        text = (ROOT / "docs/reference/claim-boundaries.md").read_text()
        current = claim_boundary_bullet(text, "This repository contains Phase 60")
        verified = claim_boundary_bullet(text, "Phase 60 verifies")
        non_claim = claim_boundary_bullet(text, "Phase 60 does not verify")
        forbidden = claim_boundary_bullet(text, "Phase 60 reproduction gap audit")

        self.assertIn("machine-checkable reproduction gap audit", current)
        self.assertIn("all 15 remaining `experiment.*` paper claims", verified)
        self.assertIn("full_reproduction_complete = false", verified)
        self.assertIn("experiment_claims_passed = 0", verified)
        self.assertIn("Newton-only continuation path", verified)
        self.assertIn("passed paper experiment", non_claim)
        self.assertIn("solver fix", non_claim)
        self.assertIn("comparative baseline result", forbidden)
        self.assertIn("full paper reproduction", forbidden)

        audit = yaml.safe_load((ROOT / "docs/reference/reproduction-gap-audit.yaml").read_text())
        claims = yaml.safe_load((ROOT / "docs/reference/paper-claims.yaml").read_text())["claims"]
        matrix = yaml.safe_load(
            (ROOT / "configs/experiments/paper_experiment_matrix.yaml").read_text()
        )["experiments"]
        experiment_claims = {
            claim["claim_id"]: claim
            for claim in claims
            if str(claim["claim_id"]).startswith("experiment.")
        }
        incomplete_claim_ids = [
            claim_id
            for claim_id, claim in experiment_claims.items()
            if claim["reproduction_status"] != "passed"
        ]
        matrix_by_claim = {entry["claim_id"]: entry for entry in matrix}
        entries = {entry["claim_id"]: entry for entry in audit["remaining_experiment_claims"]}

        self.assertEqual(audit["schema_version"], 1)
        self.assertEqual(audit["audit_id"], "phase60_reproduction_gap_audit")
        self.assertFalse(audit["global_status"]["full_reproduction_complete"])
        self.assertEqual(audit["global_status"]["experiment_claims_passed"], 0)
        self.assertEqual(audit["global_status"]["remaining_experiment_claims"], 15)
        self.assertEqual(set(entries), set(incomplete_claim_ids))
        self.assertEqual(set(entries), set(matrix_by_claim))
        self.assertEqual(
            audit["environment"]["canonical_python"],
            "/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python",
        )
        self.assertFalse(audit["environment"]["mutates_reference_environment"])
        self.assertFalse(audit["environment"]["uses_ambient_python"])

        for claim_id, entry in entries.items():
            matrix_entry = matrix_by_claim[claim_id]
            self.assertEqual(entry["claim_status"], experiment_claims[claim_id]["reproduction_status"])
            self.assertEqual(entry["matrix_status"], matrix_entry["reproduction_status"])
            self.assertEqual(entry["matrix_blocking_reasons"], matrix_entry["blocking_reasons"])
            self.assertEqual(entry["matrix_output_report"], matrix_entry["output_report"])
            report_path = ROOT / entry["matrix_output_report"]
            if report_path.exists():
                report = load_claim_report(report_path)
                self.assertEqual(entry["committed_report_status"], report.status.value)
                self.assertNotEqual(entry["committed_report_status"], "passed")
                if "full_experiment_claim_passed" in report.observed:
                    self.assertFalse(report.observed["full_experiment_claim_passed"])
            else:
                self.assertEqual(entry["committed_report_status"], "missing")

        recommended = audit["next_recommended_phase"]
        self.assertEqual(recommended["claim_id"], "experiment.single_body.spinning_box")
        self.assertIn("contact", recommended["phase_id"])
        self.assertIn("Newton-only", recommended["rationale"])

        record_text = (
            ROOT / "docs/records/2026-05-18-phase60-reproduction-gap-audit.md"
        ).read_text()
        for snippet in (
            "passed_for_reproduction_gap_audit",
            "docs/reference/reproduction-gap-audit.yaml",
            "remaining_experiment_claims: `15`",
            "experiment_claims_passed: `0`",
            "full_reproduction_complete: `false`",
            "single_body_spinning_box",
            "contact/MABD lane",
            "No `experiment.*` claim is passed.",
        ):
            self.assertIn(snippet, record_text)
        self.assertNotIn("TO_BE_BACKFILLED_PHASE60", record_text)
        self.assertNotIn("full reproduction complete", record_text.lower())

    def test_phase61_spinning_box_contact_diagnostics_are_bounded(self) -> None:
        text = (ROOT / "docs/reference/claim-boundaries.md").read_text()
        current = claim_boundary_bullet(text, "This repository contains Phase 61")
        verified = claim_boundary_bullet(text, "Phase 61 verifies")
        non_claim = claim_boundary_bullet(text, "Phase 61 does not verify")
        forbidden = claim_boundary_bullet(text, "Phase 61 spinning-box contact")

        self.assertIn("spinning-box paper-horizon contact diagnostic gap evidence", current)
        self.assertIn(
            "contact_diagnostic_policy = evaluated_from_current_mabd_states_not_applied_to_step",
            verified,
        )
        self.assertIn("contact_penetration_observed_without_response", verified)
        self.assertIn("spinning_box_contact_response_missing", verified)
        self.assertIn(
            "records the report policy that contact diagnostics are not applied to the step",
            verified,
        )
        self.assertIn("passed spinning-box experiment", non_claim)
        self.assertIn("contact solver", non_claim)
        self.assertIn("paper-faithful affine collision", non_claim)
        self.assertIn("full paper reproduction", forbidden)

        report_path = ROOT / "reports/experiment_matrix/single_body_spinning_box_paper_horizon.json"
        report = load_claim_report(report_path)
        self.assertEqual(report.status.value, "incomplete")
        self.assertNotIn("lane_gate_status", report.observed)
        self.assertEqual(
            report.observed["contact_diagnostic_policy"],
            "evaluated_from_current_mabd_states_not_applied_to_step",
        )
        self.assertEqual(
            report.observed["contact_diagnostic_status"],
            "contact_penetration_observed_without_response",
        )
        self.assertIn("spinning_box_contact_response_missing", report.observed["blocking_reasons"])
        self.assertGreaterEqual(report.observed["max_contact_active_count"], 4)
        self.assertGreater(report.observed["max_contact_penetration_m"], 0.0)
        self.assertGreater(report.observed["max_contact_normal_force_n"], 0.0)
        self.assertGreater(report.observed["max_contact_generalized_force_norm"], 0.0)
        for result in report.observed["paper_horizon_results"]:
            self.assertEqual(
                result["contact_diagnostic_policy"],
                "evaluated_from_current_mabd_states_not_applied_to_step",
            )
            self.assertEqual(
                result["contact_diagnostic_status"],
                "contact_penetration_observed_without_response",
            )
            self.assertGreater(result["max_contact_penetration_m"], 0.0)

        audit = yaml.safe_load((ROOT / "docs/reference/reproduction-gap-audit.yaml").read_text())
        audit_entry = next(
            item
            for item in audit["current_evidence_reports"]
            if item["path"] == "reports/experiment_matrix/single_body_spinning_box_paper_horizon.json"
        )
        import scripts.validate_docs as validate_docs

        self.assertEqual(audit_entry["status"], report.status.value)
        self.assertEqual(
            audit_entry["sha256"],
            validate_docs.PHASE60_SPINNING_BOX_PAPER_HORIZON_SHA256,
        )
        self.assertNotEqual(audit_entry["sha256"], validate_docs.sha256_file(report_path))
        self.assertEqual(report.source_commit, validate_docs.PHASE61_SPINNING_BOX_CONTACT_COMMIT)
        self.assertNotIn(report.source_commit, validate_docs.PLACEHOLDER_SOURCE_COMMITS)

    def test_phase61_record_has_required_evidence_fields(self) -> None:
        text = (
            ROOT / "docs/records/2026-05-18-phase61-spinning-box-contact-diagnostics.md"
        ).read_text()
        import scripts.validate_docs as validate_docs

        for snippet in (
            "## Status\n\npassed_for_spinning_box_contact_diagnostic_gap_slice",
            "phase61-spinning-box-contact-mabd-lane",
            validate_docs.PHASE61_SPINNING_BOX_CONTACT_COMMIT,
            "96713fa965463b69c229a4d30582c733ff3526bb",
            "reports/experiment_matrix/single_body_spinning_box_paper_horizon.json",
            "contact_diagnostic_policy = `evaluated_from_current_mabd_states_not_applied_to_step`",
            "contact_diagnostic_status = `contact_penetration_observed_without_response`",
            "spinning_box_contact_response_missing",
            "max_contact_active_count = `4`",
            "No `experiment.*` claim is passed.",
            "does not implement a contact solver",
            "does not pass the spinning-box experiment",
        ):
            self.assertIn(snippet, text)
        self.assertNotIn("TO_BE_BACKFILLED_PHASE61", text)
        self.assertNotIn("phase61-working-tree", text)

    def test_phase61_validator_rejects_fractional_contact_count(self) -> None:
        import scripts.validate_docs as validate_docs

        actual = load_claim_report(
            ROOT / "reports/experiment_matrix/single_body_spinning_box_paper_horizon.json"
        )
        corrupted = replace(
            actual,
            observed={
                **actual.observed,
                "max_contact_active_count": 4.5,
            },
        )

        def fake_load_claim_report(path):
            if str(path).endswith(validate_docs.SPINNING_BOX_PAPER_HORIZON_REPORT_PATH):
                return corrupted
            return load_claim_report(path)

        with patch.object(validate_docs, "load_claim_report", side_effect=fake_load_claim_report):
            with self.assertRaises(SystemExit) as context:
                validate_docs.validate_phase61_record()

        self.assertIn("integer count", str(context.exception))

    def test_phase61_validator_rejects_nonfinite_per_step_contact_extrema(self) -> None:
        import scripts.validate_docs as validate_docs

        actual = load_claim_report(
            ROOT / "reports/experiment_matrix/single_body_spinning_box_paper_horizon.json"
        )
        results = [dict(result) for result in actual.observed["paper_horizon_results"]]
        results[0]["max_contact_normal_force_n"] = math.nan
        corrupted = replace(
            actual,
            observed={
                **actual.observed,
                "paper_horizon_results": results,
            },
        )

        def fake_load_claim_report(path):
            if str(path).endswith(validate_docs.SPINNING_BOX_PAPER_HORIZON_REPORT_PATH):
                return corrupted
            return load_claim_report(path)

        with patch.object(validate_docs, "load_claim_report", side_effect=fake_load_claim_report):
            with self.assertRaises(SystemExit) as context:
                validate_docs.validate_phase61_record()

        self.assertIn("result normal force", str(context.exception))

    def test_phase61_validator_rejects_inconsistent_top_level_contact_extrema(self) -> None:
        import scripts.validate_docs as validate_docs

        actual = load_claim_report(
            ROOT / "reports/experiment_matrix/single_body_spinning_box_paper_horizon.json"
        )
        corrupted = replace(
            actual,
            observed={
                **actual.observed,
                "max_contact_normal_force_n": actual.observed["max_contact_normal_force_n"] * 0.5,
            },
        )

        def fake_load_claim_report(path):
            if str(path).endswith(validate_docs.SPINNING_BOX_PAPER_HORIZON_REPORT_PATH):
                return corrupted
            return load_claim_report(path)

        with patch.object(validate_docs, "load_claim_report", side_effect=fake_load_claim_report):
            with self.assertRaises(SystemExit) as context:
                validate_docs.validate_phase61_record()

        self.assertIn("top-level contact normal force", str(context.exception))

    def test_phase62_spinning_box_contact_response_is_bounded(self) -> None:
        text = (ROOT / "docs/reference/claim-boundaries.md").read_text()
        current = claim_boundary_bullet(text, "This repository contains Phase 62")
        verified = claim_boundary_bullet(text, "Phase 62 verifies")
        non_claim = claim_boundary_bullet(text, "Phase 62 does not verify")
        forbidden = claim_boundary_bullet(text, "Phase 62 spinning-box contact-response")

        self.assertIn("spinning-box explicit contact-response diagnostic evidence", current)
        self.assertIn("external_forces", verified)
        self.assertIn(
            "explicit_current_state_penalty_force_as_external_force_next_step",
            verified,
        )
        self.assertIn("spinning_box_contact_response_not_paper_faithful", verified)
        self.assertIn("contact_response_does_not_reduce_penetration", verified)
        self.assertIn("positive applied contact force", verified)
        self.assertIn("no lane gate", verified)
        self.assertIn("passed spinning-box experiment", non_claim)
        self.assertIn("contact solver", non_claim)
        self.assertIn("implicit contact solve", non_claim)
        self.assertIn("paper-faithful affine collision", non_claim)
        self.assertIn("full paper reproduction", forbidden)

        report_path = ROOT / "reports/experiment_matrix/single_body_spinning_box_contact_response.json"
        report = load_claim_report(report_path)
        self.assertEqual(report.status.value, "incomplete")
        self.assertNotIn("lane_gate_status", report.observed)
        self.assertEqual(report.solver_mode, "mabd_cpu_oracle_contact_response_diagnostic")
        self.assertEqual(
            report.observed["contact_response_policy"],
            "explicit_current_state_penalty_force_as_external_force_next_step",
        )
        self.assertEqual(report.observed["contact_response_scope"], "diagnostic_only_no_lane_gate")
        self.assertIn(
            "spinning_box_contact_response_not_paper_faithful",
            report.observed["blocking_reasons"],
        )
        self.assertIn(
            "contact_response_does_not_reduce_penetration",
            report.observed["blocking_reasons"],
        )
        self.assertGreaterEqual(report.observed["response_max_contact_active_count"], 4)
        self.assertGreater(report.observed["response_max_contact_penetration_m"], 0.0)
        self.assertGreater(report.observed["response_max_applied_contact_force_norm"], 0.0)
        self.assertGreater(report.observed["no_response_max_contact_penetration_m"], 0.0)
        self.assertEqual(report.observed["penetration_delta_vs_no_response_m"], 0.0)
        self.assertEqual(len(report.observed["contact_response_results"]), 2)

        import scripts.validate_docs as validate_docs

        self.assertEqual(
            report.source_commit,
            validate_docs.PHASE62_SPINNING_BOX_CONTACT_RESPONSE_COMMIT,
        )
        self.assertNotIn(report.source_commit, validate_docs.PLACEHOLDER_SOURCE_COMMITS)
        self.assertEqual(
            validate_docs.sha256_file(report_path),
            validate_docs.PHASE62_SPINNING_BOX_CONTACT_RESPONSE_SHA256,
        )

    def test_phase62_record_has_required_evidence_fields(self) -> None:
        text = (
            ROOT / "docs/records/2026-05-18-phase62-spinning-box-contact-response.md"
        ).read_text()
        import scripts.validate_docs as validate_docs

        for snippet in (
            "## Status\n\npassed_for_spinning_box_contact_response_diagnostic_slice",
            "phase62-spinning-box-contact-response",
            validate_docs.PHASE62_SPINNING_BOX_CONTACT_RESPONSE_COMMIT,
            "96713fa965463b69c229a4d30582c733ff3526bb",
            "reports/experiment_matrix/single_body_spinning_box_contact_response.json",
            "0dac0d45baeccbab0120059112268453b59ceb4af025d123ce1979ecb4c91942",
            "explicit_current_state_penalty_force_as_external_force_next_step",
            "spinning_box_contact_response_not_paper_faithful",
            "contact_response_does_not_reduce_penetration",
            "response_max_applied_contact_force_norm = `5776.765458377781`",
            "No `experiment.*` claim is passed.",
            "does not implement a contact solver",
            "paper-faithful affine collision",
        ):
            self.assertIn(snippet, text)
        self.assertNotIn("TO_BE_BACKFILLED_PHASE62", text)
        self.assertNotIn("phase62-working-tree", text)

    def test_phase62_validator_rejects_nonfinite_applied_contact_force(self) -> None:
        import scripts.validate_docs as validate_docs

        actual = load_claim_report(
            ROOT / "reports/experiment_matrix/single_body_spinning_box_contact_response.json"
        )
        corrupted = replace(
            actual,
            observed={
                **actual.observed,
                "response_max_applied_contact_force_norm": math.nan,
            },
        )

        def fake_load_claim_report(path):
            if str(path).endswith(validate_docs.SPINNING_BOX_CONTACT_RESPONSE_REPORT_PATH):
                return corrupted
            return load_claim_report(path)

        with patch.object(validate_docs, "load_claim_report", side_effect=fake_load_claim_report):
            with self.assertRaises(SystemExit) as context:
                validate_docs.validate_phase62_record()

        self.assertIn("applied contact force", str(context.exception))

    def test_phase62_validator_rejects_inconsistent_response_penetration(self) -> None:
        import scripts.validate_docs as validate_docs

        actual = load_claim_report(
            ROOT / "reports/experiment_matrix/single_body_spinning_box_contact_response.json"
        )
        corrupted = replace(
            actual,
            observed={
                **actual.observed,
                "response_max_contact_penetration_m": (
                    actual.observed["response_max_contact_penetration_m"] * 0.5
                ),
            },
        )

        def fake_load_claim_report(path):
            if str(path).endswith(validate_docs.SPINNING_BOX_CONTACT_RESPONSE_REPORT_PATH):
                return corrupted
            return load_claim_report(path)

        with patch.object(validate_docs, "load_claim_report", side_effect=fake_load_claim_report):
            with self.assertRaises(SystemExit) as context:
                validate_docs.validate_phase62_record()

        self.assertIn("top-level penetration", str(context.exception))

    def test_phase63_spinning_box_normal_constraint_is_bounded(self) -> None:
        text = (ROOT / "docs/reference/claim-boundaries.md").read_text()
        current = claim_boundary_bullet(text, "This repository contains Phase 63")
        verified = claim_boundary_bullet(text, "Phase 63 verifies")
        non_claim = claim_boundary_bullet(text, "Phase 63 does not verify")
        forbidden = claim_boundary_bullet(text, "Phase 63 spinning-box normal-constraint")

        self.assertIn("point-plane normal-constraint diagnostic evidence", current)
        self.assertIn("free_predict_then_active_point_plane_normal_constraints", verified)
        self.assertIn("increment_map_row_rank_filter", verified)
        self.assertIn("reduced free-predicted penetration", verified)
        self.assertIn("no lane gate", verified)
        self.assertIn("passed spinning-box experiment", non_claim)
        self.assertIn("contact solver", non_claim)
        self.assertIn("paper-faithful affine collision", non_claim)
        self.assertIn("IPC", non_claim)
        self.assertIn("full paper reproduction", forbidden)

        import scripts.validate_docs as validate_docs

        report_path = ROOT / validate_docs.SPINNING_BOX_NORMAL_CONSTRAINT_REPORT_PATH
        report = load_claim_report(report_path)
        self.assertEqual(report.status.value, "incomplete")
        self.assertNotIn("lane_gate_status", report.observed)
        self.assertEqual(
            report.solver_mode,
            "mabd_cpu_oracle_point_plane_normal_constraint_diagnostic",
        )
        self.assertEqual(
            report.observed["contact_constraint_policy"],
            "free_predict_then_active_point_plane_normal_constraints",
        )
        self.assertEqual(report.observed["contact_constraint_scope"], "diagnostic_only_no_lane_gate")
        self.assertEqual(report.observed["rank_filter_policy"], "increment_map_row_rank_filter")
        self.assertIn(
            "spinning_box_normal_constraint_not_paper_faithful",
            report.observed["blocking_reasons"],
        )
        self.assertGreater(report.observed["max_free_predicted_contact_penetration_m"], 0.0)
        self.assertGreaterEqual(report.observed["max_requested_plane_constraint_count"], 1)
        self.assertGreaterEqual(report.observed["max_accepted_plane_constraint_count"], 1)
        self.assertGreaterEqual(report.observed["max_skipped_plane_constraint_count"], 0)
        self.assertLess(
            report.observed["max_constrained_contact_penetration_m"],
            report.observed["max_free_predicted_contact_penetration_m"],
        )
        self.assertTrue(report.observed["normal_constraint_reduced_free_predicted_penetration"])
        self.assertEqual(len(report.observed["normal_constraint_results"]), 2)
        self.assertEqual(
            report.source_commit,
            validate_docs.PHASE63_POINT_PLANE_NORMAL_CONSTRAINT_COMMIT,
        )
        self.assertNotIn(report.source_commit, validate_docs.PLACEHOLDER_SOURCE_COMMITS)
        self.assertEqual(
            validate_docs.sha256_file(report_path),
            validate_docs.PHASE63_SPINNING_BOX_NORMAL_CONSTRAINT_SHA256,
        )

    def test_phase63_record_has_required_evidence_fields(self) -> None:
        text = (
            ROOT / "docs/records/2026-05-19-phase63-point-plane-normal-constraints.md"
        ).read_text()
        import scripts.validate_docs as validate_docs

        for snippet in (
            "## Status\n\npassed_for_spinning_box_normal_constraint_diagnostic_slice",
            "phase63-point-plane-normal-constraints",
            validate_docs.PHASE63_POINT_PLANE_NORMAL_CONSTRAINT_COMMIT,
            "96713fa965463b69c229a4d30582c733ff3526bb",
            "reports/experiment_matrix/single_body_spinning_box_normal_constraint.json",
            validate_docs.PHASE63_SPINNING_BOX_NORMAL_CONSTRAINT_SHA256,
            "free_predict_then_active_point_plane_normal_constraints",
            "increment_map_row_rank_filter",
            "spinning_box_normal_constraint_not_paper_faithful",
            "max_free_predicted_contact_penetration_m = `0.001041191335932834`",
            "max_constrained_contact_penetration_m = `2.081690722340676e-20`",
            "normal_constraint_residual_norm = `1.3877787807814457e-17`",
            "No `experiment.*` claim is passed.",
            "does not implement a contact solver",
            "paper-faithful affine collision",
        ):
            self.assertIn(snippet, text)
        self.assertNotIn("TO_BE_BACKFILLED_PHASE63", text)
        self.assertNotIn("phase63-working-tree", text)

    def test_phase63_validator_rejects_nonfinite_normal_constraint_residual(self) -> None:
        import scripts.validate_docs as validate_docs

        actual = load_claim_report(
            ROOT / "reports/experiment_matrix/single_body_spinning_box_normal_constraint.json"
        )
        corrupted = replace(
            actual,
            observed={
                **actual.observed,
                "normal_constraint_residual_norm": math.nan,
            },
        )

        def fake_load_claim_report(path):
            if str(path).endswith(validate_docs.SPINNING_BOX_NORMAL_CONSTRAINT_REPORT_PATH):
                return corrupted
            return load_claim_report(path)

        with patch.object(validate_docs, "load_claim_report", side_effect=fake_load_claim_report):
            with self.assertRaises(SystemExit) as context:
                validate_docs.validate_phase63_record()

        self.assertIn("normal constraint residual", str(context.exception))

    def test_phase63_validator_rejects_inconsistent_constrained_penetration(self) -> None:
        import scripts.validate_docs as validate_docs

        actual = load_claim_report(
            ROOT / "reports/experiment_matrix/single_body_spinning_box_normal_constraint.json"
        )
        corrupted = replace(
            actual,
            observed={
                **actual.observed,
                "max_constrained_contact_penetration_m": 1.0e-10,
            },
        )

        def fake_load_claim_report(path):
            if str(path).endswith(validate_docs.SPINNING_BOX_NORMAL_CONSTRAINT_REPORT_PATH):
                return corrupted
            return load_claim_report(path)

        with patch.object(validate_docs, "load_claim_report", side_effect=fake_load_claim_report):
            with self.assertRaises(SystemExit) as context:
                validate_docs.validate_phase63_record()

        self.assertIn("top-level constrained penetration", str(context.exception))

    def test_phase64_spinning_box_decoupled_twist_is_bounded(self) -> None:
        text = (ROOT / "docs/reference/claim-boundaries.md").read_text()
        current = claim_boundary_bullet(text, "This repository contains Phase 64")
        verified = claim_boundary_bullet(text, "Phase 64 verifies")
        non_claim = claim_boundary_bullet(text, "Phase 64 does not verify")
        forbidden = claim_boundary_bullet(text, "Phase 64 spinning-box decoupled")

        self.assertIn("decoupled spatial-twist rigid reconstruction diagnostic evidence", current)
        self.assertIn("decoupled_spatial_twist_with_exponential_rigid_update", verified)
        self.assertIn("decoupled_twist_rigid_reconstruction_diagnostic", verified)
        self.assertIn("not_evaluated_no_kkt_solve", verified)
        self.assertIn("finite-difference velocity inconsistency", verified)
        self.assertIn("no lane gate", verified)
        self.assertIn("passed spinning-box experiment", non_claim)
        self.assertIn("paper solver's private velocity semantics", non_claim)
        self.assertIn("paper-faithful M-ABD stepping", non_claim)
        self.assertIn("full paper reproduction", forbidden)

        import scripts.validate_docs as validate_docs

        report_path = ROOT / validate_docs.SPINNING_BOX_DECOUPLED_TWIST_REPORT_PATH
        report = load_claim_report(report_path)
        self.assertEqual(report.status.value, "incomplete")
        self.assertNotIn("lane_gate_status", report.observed)
        self.assertEqual(
            report.solver_mode,
            "decoupled_twist_rigid_reconstruction_diagnostic",
        )
        self.assertEqual(
            report.observed["velocity_semantics_policy"],
            "decoupled_spatial_twist_with_exponential_rigid_update",
        )
        self.assertEqual(report.observed["solver_residual_status"], "not_evaluated_no_kkt_solve")
        self.assertEqual(report.observed["threshold_violations"], [])
        self.assertTrue(report.observed["shape_thresholds_met_by_decoupled_twist"])
        self.assertTrue(report.observed["energy_thresholds_met_by_decoupled_twist"])
        self.assertIn(
            "spinning_box_decoupled_twist_not_paper_faithful",
            report.observed["blocking_reasons"],
        )
        self.assertGreater(report.observed["max_velocity_state_inconsistency_norm"], 0.0)
        self.assertGreater(report.observed["max_finite_difference_twist_error"], 0.0)
        self.assertEqual(report.observed["max_contact_penetration_m"], 0.0)
        self.assertEqual(len(report.observed["decoupled_twist_results"]), 2)
        self.assertEqual(
            report.source_commit,
            validate_docs.PHASE64_SPINNING_BOX_DECOUPLED_TWIST_COMMIT,
        )
        self.assertNotIn(report.source_commit, validate_docs.PLACEHOLDER_SOURCE_COMMITS)
        self.assertEqual(
            validate_docs.sha256_file(report_path),
            validate_docs.PHASE64_SPINNING_BOX_DECOUPLED_TWIST_SHA256,
        )

    def test_phase64_record_has_required_evidence_fields(self) -> None:
        text = (
            ROOT / "docs/records/2026-05-19-phase64-spinning-box-decoupled-twist.md"
        ).read_text()
        import scripts.validate_docs as validate_docs

        for snippet in (
            "## Status\n\npassed_for_spinning_box_decoupled_twist_diagnostic_slice",
            "phase64-spinning-box-velocity-semantics",
            validate_docs.PHASE64_SPINNING_BOX_DECOUPLED_TWIST_COMMIT,
            "96713fa965463b69c229a4d30582c733ff3526bb",
            "reports/experiment_matrix/single_body_spinning_box_decoupled_twist.json",
            validate_docs.PHASE64_SPINNING_BOX_DECOUPLED_TWIST_SHA256,
            "decoupled_twist_rigid_reconstruction_diagnostic",
            "decoupled_spatial_twist_with_exponential_rigid_update",
            "not_evaluated_no_kkt_solve",
            "spinning_box_decoupled_twist_not_paper_faithful",
            "max_velocity_state_inconsistency_norm = `85328.56614876063`",
            "max_finite_difference_twist_error = `60304.81062110217`",
            "threshold_violations = `[]`",
            "No `experiment.*` claim is passed.",
            "does not prove paper velocity semantics",
        ):
            self.assertIn(snippet, text)
        self.assertNotIn("TO_BE_BACKFILLED_PHASE64", text)
        self.assertNotIn("phase64-working-tree", text)

    def test_phase64_validator_rejects_missing_residual_status(self) -> None:
        import scripts.validate_docs as validate_docs

        actual = load_claim_report(
            ROOT / "reports/experiment_matrix/single_body_spinning_box_decoupled_twist.json"
        )
        corrupted = replace(
            actual,
            observed={
                **actual.observed,
                "solver_residual_status": "0.0",
            },
        )

        def fake_load_claim_report(path):
            if str(path).endswith(validate_docs.SPINNING_BOX_DECOUPLED_TWIST_REPORT_PATH):
                return corrupted
            return load_claim_report(path)

        with patch.object(validate_docs, "load_claim_report", side_effect=fake_load_claim_report):
            with self.assertRaises(SystemExit) as context:
                validate_docs.validate_phase64_record()

        self.assertIn("solver residual status", str(context.exception))

    def test_phase64_validator_rejects_inconsistent_velocity_inconsistency(self) -> None:
        import scripts.validate_docs as validate_docs

        actual = load_claim_report(
            ROOT / "reports/experiment_matrix/single_body_spinning_box_decoupled_twist.json"
        )
        corrupted = replace(
            actual,
            observed={
                **actual.observed,
                "max_velocity_state_inconsistency_norm": (
                    actual.observed["max_velocity_state_inconsistency_norm"] * 0.5
                ),
            },
        )

        def fake_load_claim_report(path):
            if str(path).endswith(validate_docs.SPINNING_BOX_DECOUPLED_TWIST_REPORT_PATH):
                return corrupted
            return load_claim_report(path)

        with patch.object(validate_docs, "load_claim_report", side_effect=fake_load_claim_report):
            with self.assertRaises(SystemExit) as context:
                validate_docs.validate_phase64_record()

        self.assertIn("top-level velocity inconsistency", str(context.exception))

    def test_phase65_spinning_box_figure_curves_is_bounded(self) -> None:
        import scripts.validate_docs as validate_docs

        text = (ROOT / "docs/reference/claim-boundaries.md").read_text()
        current = claim_boundary_bullet(text, "This repository contains Phase 65")
        verified = claim_boundary_bullet(text, "Phase 65 verifies")
        non_claim = claim_boundary_bullet(text, "Phase 65 does not verify")
        forbidden = claim_boundary_bullet(text, "Phase 65 spinning-box paper-figure digitization")

        self.assertIn("paper-figure color-family digitization evidence", current)
        self.assertIn("Phase 65 record", current)
        self.assertIn("roll_cube.pdf", verified)
        self.assertIn("nearest_color_family_within_threshold", verified)
        self.assertIn("color_family_curve_available = true", verified)
        self.assertIn("paper_reference_legend_identity_available = false", verified)
        self.assertIn("color_family_not_legend_entry", verified)
        self.assertIn("not_evaluated", verified)
        self.assertIn("incomplete", verified)
        self.assertIn("no lane gate", verified)
        for snippet in (
            "passed spinning-box experiment",
            "M-ABD lane pass",
            "paper reference legend-entry identity",
            "solid/dashed line-style split",
            "Newton-vs-paper curve agreement",
            "comparison pass gate",
            "rendered output inspection",
            "runtime performance",
            "full paper reproduction",
            "any passed `experiment.*` claim",
        ):
            self.assertIn(snippet, non_claim)
            self.assertIn(snippet, forbidden)

        report = load_claim_report(ROOT / validate_docs.SPINNING_BOX_FIGURE_CURVES_REPORT_PATH)
        self.assertEqual(report.source_commit, validate_docs.PHASE65_SPINNING_BOX_FIGURE_CURVES_COMMIT)
        self.assertEqual(report.vendored_newton_commit, "96713fa965463b69c229a4d30582c733ff3526bb")
        self.assertEqual(report.claim_id, "experiment.single_body.spinning_box")
        self.assertEqual(report.scene_id, "single_body_spinning_box")
        self.assertEqual(report.baseline_lane, "paper_figure_digitization")
        self.assertEqual(report.solver_mode, "spinning_box_paper_figure_curve_digitization")
        self.assertEqual(report.backend, "paper_pdf_digitization")
        self.assertEqual(report.status.value, "incomplete")
        self.assertFalse(report.expected["full_experiment_claim_passed"])

        observed = report.observed
        self.assertNotIn("lane_gate_status", observed)
        self.assertNotIn("reference_curve_available", observed)
        self.assertEqual(observed["figure_curve_scope"], "paper_roll_cube_color_family_digitization")
        self.assertEqual(observed["source_pdf_path"], "/tmp/mabd-paper/source/images/cube/roll_cube.pdf")
        self.assertEqual(
            observed["source_pdf_sha256"],
            "7669b062348324a3b0090cc9f44930655c83233a87f63389db9198b88f95ae80",
        )
        self.assertEqual(
            observed["render_command"],
            [
                "pdftocairo",
                "-png",
                "-singlefile",
                "-r",
                "300",
                "/tmp/mabd-paper/source/images/cube/roll_cube.pdf",
                "temporary_output_prefix",
            ],
        )
        self.assertEqual(observed["renderer_version"], "pdftocairo 22.02.0")
        self.assertEqual(observed["render_dpi"], 300)
        self.assertEqual(observed["rendered_size_px"], [3570, 2187])
        self.assertEqual(
            observed["rendered_image_sha256"],
            validate_docs.PHASE65_SPINNING_BOX_RENDERED_IMAGE_SHA256,
        )
        self.assertEqual(observed["sample_count"], 101)
        self.assertTrue(observed["color_family_curve_available"])
        self.assertFalse(observed["paper_reference_legend_identity_available"])
        self.assertEqual(observed["color_assignment_policy"], "nearest_color_family_within_threshold")
        self.assertEqual(observed["curve_identity_status"], "color_family_not_legend_entry")
        self.assertEqual(observed["curve_agreement_status"], "not_evaluated")
        self.assertEqual(
            observed["blocking_reasons"],
            [
                "spinning_box_figure_curve_agreement_not_evaluated",
                "spinning_box_reference_legend_identity_not_evaluated",
                "spinning_box_line_style_split_not_evaluated",
                "mabd_newton_report_incomplete",
                "spinning_box_comparison_pass_gate_not_enabled",
            ],
        )
        expected_colors = {"blue", "brown", "gray", "green", "orange"}
        for group_key, metric, plot_box in (
            ("angular_momentum_curves", "angular_momentum", [394, 1139, 1751, 1956]),
            ("linear_momentum_curves", "linear_momentum", [2142, 1139, 3528, 1956]),
        ):
            self.assertEqual(set(observed[group_key]), expected_colors)
            for color_family, curve in observed[group_key].items():
                self.assertEqual(curve["metric"], metric)
                self.assertEqual(curve["color_family"], color_family)
                self.assertEqual(curve["unit"], "paper_plot_units")
                self.assertEqual(curve["plot_box_px"], plot_box)
                self.assertEqual(curve["axis_range"], [95.0, 100.0])
                self.assertTrue(curve["extraction_success"])
                self.assertGreaterEqual(curve["sample_coverage"], 0.80)
                self.assertGreater(curve["matched_sample_count"], 0)
                self.assertGreater(curve["source_pixel_count"], 0)
                self.assertEqual(curve["curve_identity_status"], "color_family_not_legend_entry")
                self.assertEqual(len(curve["samples"]), 101)
                self.assertTrue(math.isclose(curve["samples"][0]["time_s"], 0.0, abs_tol=1.0e-12))
                self.assertTrue(math.isclose(curve["samples"][-1]["time_s"], 10.0, abs_tol=1.0e-12))

        actual_sha = validate_docs.sha256_file(
            ROOT / validate_docs.SPINNING_BOX_FIGURE_CURVES_REPORT_PATH
        )
        self.assertEqual(actual_sha, validate_docs.PHASE65_SPINNING_BOX_FIGURE_CURVES_SHA256)

        data = yaml.safe_load((ROOT / "docs/reference/paper-claims.yaml").read_text())
        spinning_box = next(
            claim
            for claim in data["claims"]
            if claim["claim_id"] == "experiment.single_body.spinning_box"
        )
        self.assertEqual(spinning_box["reproduction_status"], "intended")
        self.assertFalse(
            any(
                claim["claim_id"].startswith("experiment.")
                and claim["reproduction_status"] == "passed"
                for claim in data["claims"]
            )
        )

    def test_phase65_record_has_required_evidence_fields(self) -> None:
        import scripts.validate_docs as validate_docs

        text = (
            ROOT / "docs/records/2026-05-19-phase65-spinning-box-figure-curves.md"
        ).read_text()

        for snippet in (
            "## Status\n\npassed_for_spinning_box_figure_curve_digitization_slice",
            "phase65-spinning-box-figure-curves",
            validate_docs.PHASE65_SPINNING_BOX_FIGURE_CURVES_COMMIT,
            "96713fa965463b69c229a4d30582c733ff3526bb",
            "reports/experiment_matrix/single_body_spinning_box_figure_curves.json",
            validate_docs.PHASE65_SPINNING_BOX_FIGURE_CURVES_SHA256,
            validate_docs.PHASE65_SPINNING_BOX_RENDERED_IMAGE_SHA256,
            "paper_pdf_digitization",
            "spinning_box_paper_figure_curve_digitization",
            "paper_roll_cube_color_family_digitization",
            "nearest_color_family_within_threshold",
            "color_family_not_legend_entry",
            "not_evaluated",
            "spinning_box_figure_curve_agreement_not_evaluated",
            "spinning_box_reference_legend_identity_not_evaluated",
            "spinning_box_line_style_split_not_evaluated",
            "spinning_box_comparison_pass_gate_not_enabled",
            "No `experiment.*` claim is passed.",
        ):
            self.assertIn(snippet, text)
        self.assertNotIn("TO_BE_BACKFILLED_PHASE65", text)
        self.assertNotIn("phase65-working-tree", text)

    def test_phase65_validator_rejects_verified_reference_legend_identity(self) -> None:
        import scripts.validate_docs as validate_docs

        actual = load_claim_report(ROOT / validate_docs.SPINNING_BOX_FIGURE_CURVES_REPORT_PATH)
        corrupted = replace(
            actual,
            observed={
                **actual.observed,
                "paper_reference_legend_identity_available": True,
            },
        )

        def fake_load_claim_report(path):
            if str(path).endswith(validate_docs.SPINNING_BOX_FIGURE_CURVES_REPORT_PATH):
                return corrupted
            return load_claim_report(path)

        with patch.object(validate_docs, "load_claim_report", side_effect=fake_load_claim_report):
            with self.assertRaises(SystemExit) as context:
                validate_docs.validate_phase65_record()

        self.assertIn("reference legend identity", str(context.exception))

    def test_phase66_spinning_box_figure_agreement_diagnostics_are_bounded(self) -> None:
        import scripts.validate_docs as validate_docs

        text = (ROOT / "docs/reference/claim-boundaries.md").read_text()
        current = claim_boundary_bullet(text, "This repository contains Phase 66")
        verified = claim_boundary_bullet(text, "Phase 66 verifies")
        non_claim = claim_boundary_bullet(text, "Phase 66 does not verify")
        forbidden = claim_boundary_bullet(
            text,
            "Phase 66 spinning-box figure agreement diagnostics",
        )

        self.assertIn("paper-figure agreement diagnostic evidence", current)
        self.assertIn("Phase 65 paper-figure color-family digitization report", verified)
        self.assertIn("digitized_figure_reference_available = true", verified)
        self.assertIn("digitized_figure_curve_agreement_available = true", verified)
        self.assertIn("digitized_figure_curve_agreement_passed = false", verified)
        self.assertIn("endpoint best-fit diagnostics", verified)
        self.assertIn("paper_figure_curves", verified)
        self.assertIn("spinning_box_digitized_figure_curve_agreement_not_passed", verified)
        for snippet in (
            "passed spinning-box experiment",
            "M-ABD lane pass",
            "paper reference legend-entry identity",
            "solid/dashed line-style split",
            "Newton-vs-paper curve agreement",
            "comparison pass gate",
            "rendered output inspection",
            "runtime performance",
            "full paper reproduction",
            "any passed `experiment.*` claim",
        ):
            self.assertIn(snippet, non_claim)
            self.assertIn(snippet, forbidden)

        report = load_claim_report(ROOT / validate_docs.SPINNING_BOX_COMPARISON_REPORT_PATH)
        self.assertIn(
            report.source_commit,
            {
                validate_docs.PHASE66_SPINNING_BOX_FIGURE_AGREEMENT_COMMIT,
                validate_docs.PHASE72_SPINNING_BOX_FIGURE_MOMENTUM_ENDPOINT_COMMIT,
            },
        )
        self.assertEqual(report.vendored_newton_commit, "96713fa965463b69c229a4d30582c733ff3526bb")
        self.assertEqual(report.claim_id, "experiment.single_body.spinning_box")
        self.assertEqual(report.scene_id, "single_body_spinning_box")
        self.assertEqual(report.baseline_lane, "spinning_box_comparison_protocol")
        self.assertEqual(report.solver_mode, "spinning_box_multilane_comparison_development")
        self.assertEqual(report.backend, "report_protocol")
        self.assertEqual(report.status.value, "incomplete")

        observed = report.observed
        self.assertFalse(observed["full_experiment_claim_passed"])
        self.assertTrue(observed["digitized_figure_reference_available"])
        self.assertTrue(observed["digitized_figure_curve_agreement_available"])
        self.assertFalse(observed["digitized_figure_curve_agreement_passed"])
        self.assertEqual(
            report.raw_outputs["figure_curve_report"],
            validate_docs.SPINNING_BOX_FIGURE_CURVES_REPORT_PATH,
        )
        self.assertIn("paper_figure_curves", observed["input_report_provenance"])
        self.assertEqual(
            observed["input_report_provenance"]["paper_figure_curves"]["sha256"],
            validate_docs.PHASE65_SPINNING_BOX_FIGURE_CURVES_SHA256,
        )
        self.assertIn(
            "spinning_box_digitized_figure_curve_agreement_not_passed",
            observed["blocking_reasons"],
        )
        diagnostics = observed["digitized_figure_curve_agreement_diagnostics"]
        self.assertEqual(
            diagnostics["linear_momentum"]["mabd_newton"]["status"],
            "diagnostic_available_not_pass_gate",
        )
        self.assertEqual(
            diagnostics["linear_momentum"]["mabd_newton"]["lane_value_source"],
            (
                "linear_momentum_error"
                if report.source_commit
                == validate_docs.PHASE66_SPINNING_BOX_FIGURE_AGREEMENT_COMMIT
                else "final_linear_momentum_norm"
            ),
        )
        self.assertEqual(
            diagnostics["linear_momentum"]["mabd_newton"]["agreement_claim_status"],
            "diagnostic_only_not_curve_agreement",
        )
        self.assertEqual(
            observed["digitized_figure_reference_samples"]["linear_momentum_color_families"]["blue"],
            101,
        )
        actual_sha = validate_docs.sha256_file(ROOT / validate_docs.SPINNING_BOX_COMPARISON_REPORT_PATH)
        self.assertIn(
            actual_sha,
            {
                validate_docs.PHASE66_SPINNING_BOX_COMPARISON_SHA256,
                validate_docs.PHASE72_SPINNING_BOX_COMPARISON_SHA256,
            },
        )

        data = yaml.safe_load((ROOT / "docs/reference/paper-claims.yaml").read_text())
        spinning_box = next(
            claim
            for claim in data["claims"]
            if claim["claim_id"] == "experiment.single_body.spinning_box"
        )
        self.assertEqual(spinning_box["reproduction_status"], "intended")
        self.assertFalse(
            any(
                claim["claim_id"].startswith("experiment.")
                and claim["reproduction_status"] == "passed"
                for claim in data["claims"]
            )
        )
        validate_docs.validate_phase66_record()

    def test_phase66_record_has_required_evidence_fields(self) -> None:
        import scripts.validate_docs as validate_docs

        text = (
            ROOT / "docs/records/2026-05-19-phase66-spinning-box-figure-agreement-diagnostics.md"
        ).read_text()

        for snippet in (
            "## Status\n\npassed_for_spinning_box_figure_agreement_diagnostics_slice",
            "phase66-spinning-box-figure-agreement",
            validate_docs.PHASE66_SPINNING_BOX_FIGURE_AGREEMENT_COMMIT,
            "96713fa965463b69c229a4d30582c733ff3526bb",
            "reports/experiment_matrix/single_body_spinning_box_comparison.json",
            validate_docs.PHASE66_SPINNING_BOX_COMPARISON_SHA256,
            "reports/experiment_matrix/single_body_spinning_box_figure_curves.json",
            validate_docs.PHASE65_SPINNING_BOX_FIGURE_CURVES_SHA256,
            "digitized_figure_reference_available=true",
            "digitized_figure_curve_agreement_available=true",
            "digitized_figure_curve_agreement_passed=false",
            "spinning_box_digitized_figure_curve_agreement_not_passed",
            "experiment.single_body.spinning_box remains intended",
            "No `experiment.*` claim is passed.",
        ):
            self.assertIn(snippet, text)
        self.assertNotIn("TO_BE_BACKFILLED_PHASE66", text)
        self.assertNotIn("phase66-working-tree", text)

    def test_phase72_spinning_box_figure_momentum_endpoint_artifact(self) -> None:
        import scripts.validate_docs as validate_docs

        boundary_text = (ROOT / "docs/reference/claim-boundaries.md").read_text()
        current = validate_docs.claim_boundary_bullet(
            boundary_text,
            "This repository contains Phase 72",
        )
        verified = validate_docs.claim_boundary_bullet(boundary_text, "Phase 72 verifies")
        non_claim = validate_docs.claim_boundary_bullet(
            boundary_text,
            "Phase 72 does not verify",
        )
        forbidden = validate_docs.claim_boundary_bullet(
            boundary_text,
            "Phase 72 spinning-box figure momentum endpoint diagnostics",
        )

        self.assertIn("spinning-box paper-figure momentum endpoint diagnostic evidence", current)
        self.assertIn("final_linear_momentum_norm", verified)
        self.assertIn("final_angular_momentum_norm", verified)
        self.assertIn("not `linear_momentum_error` or `angular_momentum_error`", verified)
        self.assertIn("digitized_figure_curve_agreement_passed = false", verified)
        self.assertIn("comparison pass gate remains disabled", verified)
        for snippet in (
            "passed spinning-box experiment",
            "M-ABD lane pass",
            "paper reference legend-entry identity",
            "solid/dashed line-style split",
            "Newton-vs-paper curve agreement",
            "comparison pass gate",
            "rendered output inspection",
            "runtime performance",
            "full paper reproduction",
            "any passed `experiment.*` claim",
        ):
            self.assertIn(snippet, non_claim)
            self.assertIn(snippet, forbidden)

        report = load_claim_report(ROOT / validate_docs.SPINNING_BOX_COMPARISON_REPORT_PATH)
        self.assertEqual(
            report.source_commit,
            validate_docs.PHASE72_SPINNING_BOX_FIGURE_MOMENTUM_ENDPOINT_COMMIT,
        )
        self.assertEqual(report.vendored_newton_commit, "96713fa965463b69c229a4d30582c733ff3526bb")
        self.assertEqual(report.claim_id, "experiment.single_body.spinning_box")
        self.assertEqual(report.scene_id, "single_body_spinning_box")
        self.assertEqual(report.baseline_lane, "spinning_box_comparison_protocol")
        self.assertEqual(report.status.value, "incomplete")

        observed = report.observed
        self.assertFalse(observed["full_experiment_claim_passed"])
        self.assertFalse(observed["digitized_figure_curve_agreement_passed"])
        self.assertIn(
            "spinning_box_digitized_figure_curve_agreement_not_passed",
            observed["blocking_reasons"],
        )
        diagnostics = observed["digitized_figure_curve_agreement_diagnostics"]
        linear_mabd = diagnostics["linear_momentum"]["mabd_newton"]
        self.assertEqual(linear_mabd["lane_value_source"], "final_linear_momentum_norm")
        self.assertGreater(linear_mabd["lane_value"], 99.0)
        self.assertLess(linear_mabd["lane_value"], 101.0)
        self.assertLess(linear_mabd["best_abs_error"], 5.0)
        angular_mabd = diagnostics["angular_momentum"]["mabd_newton"]
        self.assertEqual(angular_mabd["lane_value_source"], "final_angular_momentum_norm")
        self.assertGreater(angular_mabd["lane_value"], 99.0)
        self.assertLess(angular_mabd["lane_value"], 101.0)
        self.assertLess(angular_mabd["best_abs_error"], 5.0)
        self.assertIn("linear_momentum_error", observed["lane_metrics"]["mabd_newton"])
        self.assertIn("angular_momentum_error", observed["lane_metrics"]["mabd_newton"])

        actual_sha = validate_docs.sha256_file(ROOT / validate_docs.SPINNING_BOX_COMPARISON_REPORT_PATH)
        self.assertEqual(actual_sha, validate_docs.PHASE72_SPINNING_BOX_COMPARISON_SHA256)

        data = yaml.safe_load((ROOT / "docs/reference/paper-claims.yaml").read_text())
        spinning_box = next(
            claim
            for claim in data["claims"]
            if claim["claim_id"] == "experiment.single_body.spinning_box"
        )
        self.assertEqual(spinning_box["reproduction_status"], "intended")
        self.assertFalse(
            any(
                claim["claim_id"].startswith("experiment.")
                and claim["reproduction_status"] == "passed"
                for claim in data["claims"]
            )
        )
        validate_docs.validate_phase72_record()

    def test_phase72_record_has_required_evidence_fields(self) -> None:
        import scripts.validate_docs as validate_docs

        text = (
            ROOT
            / "docs/records/2026-05-20-phase72-spinning-box-figure-momentum-endpoint.md"
        ).read_text()

        for snippet in (
            "## Status\n\npassed_for_spinning_box_figure_momentum_endpoint_diagnostic",
            validate_docs.PHASE72_SPINNING_BOX_FIGURE_MOMENTUM_ENDPOINT_COMMIT,
            "96713fa965463b69c229a4d30582c733ff3526bb",
            "reports/experiment_matrix/single_body_spinning_box_comparison.json",
            validate_docs.PHASE72_SPINNING_BOX_COMPARISON_SHA256,
            "final_linear_momentum_norm",
            "final_angular_momentum_norm",
            "linear_momentum_error",
            "angular_momentum_error",
            "digitized_figure_curve_agreement_passed = false",
            "spinning_box_digitized_figure_curve_agreement_not_passed",
            "comparison pass gate remains disabled",
            "No `experiment.*` claim is passed.",
            "mutates_reference_environment=false",
            "uses_reference_python=false",
            "uses_ambient_python=false",
        ):
            self.assertIn(snippet, text)
        self.assertNotIn("TO_BE_BACKFILLED_PHASE72", text)
        self.assertNotIn("phase72-working-tree", text)

    def test_phase73_rolling_spinning_report_lane_artifact(self) -> None:
        import scripts.validate_docs as validate_docs

        boundary_text = (ROOT / "docs/reference/claim-boundaries.md").read_text()
        current = validate_docs.claim_boundary_bullet(
            boundary_text,
            "This repository contains Phase 73",
        )
        verified = validate_docs.claim_boundary_bullet(boundary_text, "Phase 73 verifies")
        non_claim = validate_docs.claim_boundary_bullet(
            boundary_text,
            "Phase 73 does not verify",
        )
        forbidden = validate_docs.claim_boundary_bullet(
            boundary_text,
            "Phase 73 rolling/spinning protocol report lane evidence",
        )

        self.assertIn("rolling/spinning protocol report lane evidence", current)
        self.assertIn("single_body_rolling_spinning.json", verified)
        self.assertIn("i7 CPU, single thread", verified)
        self.assertIn("paper_metric_statuses", verified)
        self.assertIn("backend: `report_protocol`", verified)
        self.assertIn("no experiment claim passed", verified)
        for snippet in (
            "rolling-cylinder dynamics",
            "local runtime timing",
            "implicit/explicit RBD baselines",
            "comparative baseline results",
            "rendered output",
            "full paper reproduction",
            "any passed `experiment.*` claim",
        ):
            self.assertIn(snippet, non_claim)
            self.assertIn(snippet, forbidden)

        report = load_claim_report(ROOT / validate_docs.ROLLING_SPINNING_REPORT_PATH)
        self.assertEqual(report.source_commit, validate_docs.PHASE73_ROLLING_SPINNING_REPORT_LANE_COMMIT)
        self.assertEqual(report.vendored_newton_commit, "96713fa965463b69c229a4d30582c733ff3526bb")
        self.assertEqual(report.claim_id, "experiment.single_body.rolling_spinning")
        self.assertEqual(report.scene_id, "single_body_rolling_spinning")
        self.assertEqual(report.baseline_lane, "mabd_newton")
        self.assertEqual(report.solver_mode, "rolling_spinning_protocol_audit")
        self.assertEqual(report.backend, "report_protocol")
        self.assertEqual(report.status.value, "incomplete")
        self.assertFalse(report.expected["full_experiment_claim_passed"])
        self.assertFalse(report.observed["full_experiment_claim_passed"])
        self.assertFalse(report.observed["local_runtime_measured"])
        self.assertEqual(report.expected["benchmark_step_count"], 10000)
        self.assertEqual(report.expected["time_step_s"], 0.01)
        self.assertEqual(report.expected["paper_hardware_context"], "i7 CPU, single thread")
        self.assertIn("rbd_implicit_baseline", report.observed["required_lanes_missing"])
        self.assertIn("rbd_explicit_baseline", report.observed["required_lanes_missing"])
        self.assertIn("rolling_cylinder_runtime_not_measured", report.observed["blocking_reasons"])
        self.assertEqual(
            report.observed["paper_metric_statuses"]["total_simulation_time_ms"],
            "paper_reference_recorded_no_local_runtime",
        )
        self.assertEqual(report.timing_distribution["status"], "not_measured")
        self.assertFalse(report.timing_distribution["paper_comparable"])

        actual_sha = validate_docs.sha256_file(ROOT / validate_docs.ROLLING_SPINNING_REPORT_PATH)
        self.assertEqual(actual_sha, validate_docs.PHASE73_ROLLING_SPINNING_REPORT_SHA256)

        data = yaml.safe_load((ROOT / "docs/reference/paper-claims.yaml").read_text())
        rolling = next(
            claim
            for claim in data["claims"]
            if claim["claim_id"] == "experiment.single_body.rolling_spinning"
        )
        self.assertEqual(rolling["reproduction_status"], "intended")
        self.assertFalse(
            any(
                claim["claim_id"].startswith("experiment.")
                and claim["reproduction_status"] == "passed"
                for claim in data["claims"]
            )
        )
        validate_docs.validate_phase73_record()

    def test_phase73_record_has_required_evidence_fields(self) -> None:
        import scripts.validate_docs as validate_docs

        text = (
            ROOT
            / "docs/records/2026-05-20-phase73-rolling-spinning-report-lane.md"
        ).read_text()

        for snippet in (
            "## Status\n\npassed_for_rolling_spinning_report_lane",
            validate_docs.PHASE73_ROLLING_SPINNING_REPORT_LANE_COMMIT,
            "96713fa965463b69c229a4d30582c733ff3526bb",
            "configs/experiments/single_body_rolling_spinning.yaml",
            "reports/experiment_matrix/single_body_rolling_spinning.json",
            validate_docs.PHASE73_ROLLING_SPINNING_REPORT_SHA256,
            "backend: `report_protocol`",
            "status: `incomplete`",
            "paper_text_timing_only_no_local_runtime_measurement",
            "local_runtime_measured=false",
            "full_experiment_claim_passed=false",
            "target_exists",
            "ready_to_sync_existing",
            "smoke_passed",
            "mutates_reference_environment=false",
            "uses_reference_python=false",
            "uses_ambient_python=false",
            "No `experiment.*` claim is passed.",
        ):
            self.assertIn(snippet, text)
        self.assertNotIn("TO_BE_BACKFILLED_PHASE73", text)
        self.assertNotIn("phase73-working-tree", text)

    def test_phase74_rolling_cylinder_rbd_baseline_artifact(self) -> None:
        import scripts.validate_docs as validate_docs

        boundary_text = (ROOT / "docs/reference/claim-boundaries.md").read_text()
        current = validate_docs.claim_boundary_bullet(
            boundary_text,
            "This repository contains Phase 74",
        )
        verified = validate_docs.claim_boundary_bullet(boundary_text, "Phase 74 verifies")
        non_claim = validate_docs.claim_boundary_bullet(
            boundary_text,
            "Phase 74 does not verify",
        )
        forbidden = validate_docs.claim_boundary_bullet(
            boundary_text,
            "Phase 74 rolling-cylinder Newton RBD development baseline evidence",
        )

        self.assertIn("rolling-cylinder Newton RBD development baseline evidence", current)
        self.assertIn("single_body_rolling_spinning_rbd_implicit_baseline.json", verified)
        self.assertIn("SolverSemiImplicit", verified)
        self.assertIn("builder.finalize(device=\"cpu\")", verified)
        self.assertIn("required_lanes_missing", verified)
        self.assertIn("no experiment claim passed", verified)
        for snippet in (
            "paper-faithful implicit RBD",
            "explicit RBD",
            "M-ABD rolling-cylinder dynamics",
            "co-rotated ABD timing",
            "paper-comparable performance",
            "completed rolling/spinning reproduction",
            "full paper reproduction",
            "any passed `experiment.*` claim",
        ):
            self.assertIn(snippet, non_claim)
        for snippet in (
            "paper-faithful implicit RBD result",
            "explicit RBD result",
            "M-ABD rolling-cylinder result",
            "paper-comparable timing result",
            "comparative baseline pass",
            "full paper reproduction",
        ):
            self.assertIn(snippet, forbidden)

        report = load_claim_report(
            ROOT / validate_docs.ROLLING_SPINNING_RBD_IMPLICIT_BASELINE_REPORT_PATH
        )
        self.assertEqual(
            report.source_commit,
            validate_docs.PHASE74_ROLLING_CYLINDER_RBD_BASELINE_COMMIT,
        )
        self.assertEqual(report.vendored_newton_commit, "96713fa965463b69c229a4d30582c733ff3526bb")
        self.assertEqual(report.claim_id, "experiment.single_body.rolling_spinning")
        self.assertEqual(report.scene_id, "single_body_rolling_spinning")
        self.assertEqual(report.baseline_lane, "rbd_implicit_baseline")
        self.assertEqual(
            report.solver_mode,
            "newton_semimplicit_rolling_cylinder_rbd_cpu_development",
        )
        self.assertEqual(report.backend, "cpu_newton_warp")
        self.assertEqual(report.status.value, "incomplete")
        self.assertFalse(report.expected["full_experiment_claim_passed"])
        self.assertFalse(report.expected["paper_comparable"])
        self.assertFalse(report.observed["full_experiment_claim_passed"])
        self.assertFalse(report.observed["paper_comparable"])
        self.assertTrue(report.observed["local_runtime_measured"])
        self.assertEqual(report.observed["newton_device"], "cpu")
        self.assertEqual(report.observed["cylinder_axis_world"], [0.0, 0.0, 1.0])
        self.assertEqual(report.observed["step_count"], 10000)
        self.assertEqual(report.observed["time_step_s"], 0.01)
        self.assertEqual(
            report.observed["required_lanes_missing"],
            ["rbd_explicit_baseline", "mabd_newton", "paper_comparable_timing"],
        )
        self.assertIn(
            "newton_semimplicit_not_paper_implicit_rbd_solver",
            report.observed["blocking_reasons"],
        )
        contact_summary = report.observed["contact_count_summary"]
        for key in ("initial", "final", "min", "max"):
            self.assertIsInstance(contact_summary[key], int)
            self.assertGreaterEqual(contact_summary[key], 0)
        self.assertGreaterEqual(contact_summary["max"], 1)
        self.assertGreaterEqual(report.observed["max_center_penetration_m"], 0.0)
        self.assertTrue(math.isfinite(report.observed["no_slip_residual_m_s"]))
        self.assertFalse(report.timing_distribution["paper_comparable"])
        self.assertGreater(report.timing_distribution["total_wall_time_ms"], 0.0)
        self.assertEqual(report.raw_outputs, {"time_series": "not_written"})
        self.assertEqual(report.plot_paths, {})

        actual_sha = validate_docs.sha256_file(
            ROOT / validate_docs.ROLLING_SPINNING_RBD_IMPLICIT_BASELINE_REPORT_PATH
        )
        self.assertEqual(
            actual_sha,
            validate_docs.PHASE74_ROLLING_SPINNING_RBD_IMPLICIT_BASELINE_SHA256,
        )

        data = yaml.safe_load((ROOT / "docs/reference/paper-claims.yaml").read_text())
        rolling = next(
            claim
            for claim in data["claims"]
            if claim["claim_id"] == "experiment.single_body.rolling_spinning"
        )
        self.assertEqual(rolling["reproduction_status"], "intended")
        self.assertFalse(
            any(
                claim["claim_id"].startswith("experiment.")
                and claim["reproduction_status"] == "passed"
                for claim in data["claims"]
            )
        )
        validate_docs.validate_phase74_record()

    def test_phase74_record_has_required_evidence_fields(self) -> None:
        import scripts.validate_docs as validate_docs

        text = (
            ROOT
            / "docs/records/2026-05-20-phase74-rolling-cylinder-rbd-baseline.md"
        ).read_text()

        for snippet in (
            "## Status\n\npassed_for_rolling_cylinder_rbd_development_baseline_lane",
            validate_docs.PHASE74_ROLLING_CYLINDER_RBD_BASELINE_COMMIT,
            "96713fa965463b69c229a4d30582c733ff3526bb",
            "configs/experiments/single_body_rolling_spinning.yaml",
            "reports/experiment_matrix/single_body_rolling_spinning_rbd_implicit_baseline.json",
            validate_docs.PHASE74_ROLLING_SPINNING_RBD_IMPLICIT_BASELINE_SHA256,
            "backend: `cpu_newton_warp`",
            "status: `incomplete`",
            "newton_semimplicit_rolling_cylinder_rbd_cpu_development",
            "builder.finalize(device=\"cpu\")",
            "ModelBuilder.ShapeConfig",
            "Model.contacts",
            "Model.collide",
            "contact_count_summary",
            "max_center_penetration_m",
            "no_slip_residual_m_s",
            "rbd_explicit_baseline_missing",
            "mabd_rolling_cylinder_lane_missing",
            "paper_comparable_timing_missing",
            "newton_semimplicit_not_paper_implicit_rbd_solver",
            "paper_comparable=false",
            "full_experiment_claim_passed=false",
            "No `experiment.*` claim is passed.",
            "mutates_reference_environment=false",
            "uses_reference_python=false",
            "uses_ambient_python=false",
        ):
            self.assertIn(snippet, text)
        self.assertNotIn("TO_BE_BACKFILLED_PHASE74", text)
        self.assertNotIn("phase74-working-tree", text)

    def test_phase75_rolling_cylinder_explicit_rbd_baseline_artifact(self) -> None:
        import scripts.validate_docs as validate_docs

        boundary_text = (ROOT / "docs/reference/claim-boundaries.md").read_text()
        current = validate_docs.claim_boundary_bullet(
            boundary_text,
            "This repository contains Phase 75",
        )
        verified = validate_docs.claim_boundary_bullet(boundary_text, "Phase 75 verifies")
        non_claim = validate_docs.claim_boundary_bullet(
            boundary_text,
            "Phase 75 does not verify",
        )
        forbidden = validate_docs.claim_boundary_bullet(
            boundary_text,
            "Phase 75 rolling-cylinder Newton ExplicitEuler development baseline evidence",
        )

        self.assertIn("rolling-cylinder Newton ExplicitEuler development baseline evidence", current)
        self.assertIn("single_body_rolling_spinning_rbd_explicit_baseline.json", verified)
        self.assertIn("SolverExplicitEuler", verified)
        self.assertIn("required_lanes_missing", verified)
        self.assertIn("no experiment claim passed", verified)
        for snippet in (
            "paper-faithful explicit RBD",
            "M-ABD rolling-cylinder dynamics",
            "co-rotated ABD timing",
            "paper-comparable performance",
            "completed rolling/spinning reproduction",
            "full paper reproduction",
            "any passed `experiment.*` claim",
        ):
            self.assertIn(snippet, non_claim)
        for snippet in (
            "paper-faithful explicit RBD result",
            "M-ABD rolling-cylinder result",
            "paper-comparable timing result",
            "comparative baseline pass",
            "full paper reproduction",
        ):
            self.assertIn(snippet, forbidden)

        report = load_claim_report(
            ROOT / validate_docs.ROLLING_SPINNING_RBD_EXPLICIT_BASELINE_REPORT_PATH
        )
        self.assertEqual(
            report.source_commit,
            validate_docs.PHASE75_ROLLING_CYLINDER_RBD_EXPLICIT_BASELINE_COMMIT,
        )
        self.assertEqual(report.vendored_newton_commit, "96713fa965463b69c229a4d30582c733ff3526bb")
        self.assertEqual(report.claim_id, "experiment.single_body.rolling_spinning")
        self.assertEqual(report.scene_id, "single_body_rolling_spinning")
        self.assertEqual(report.baseline_lane, "rbd_explicit_baseline")
        self.assertEqual(
            report.solver_mode,
            "newton_explicit_euler_rolling_cylinder_rbd_cpu_development",
        )
        self.assertEqual(report.backend, "cpu_newton_warp")
        self.assertEqual(report.status.value, "incomplete")
        self.assertFalse(report.expected["full_experiment_claim_passed"])
        self.assertFalse(report.expected["paper_comparable"])
        self.assertFalse(report.observed["full_experiment_claim_passed"])
        self.assertFalse(report.observed["paper_comparable"])
        self.assertTrue(report.observed["local_runtime_measured"])
        self.assertEqual(report.observed["newton_device"], "cpu")
        self.assertEqual(report.observed["cylinder_axis_world"], [0.0, 0.0, 1.0])
        self.assertEqual(report.observed["step_count"], 10000)
        self.assertEqual(report.observed["time_step_s"], 0.01)
        self.assertEqual(
            report.observed["required_lanes_missing"],
            ["mabd_newton", "paper_comparable_timing"],
        )
        self.assertIn(
            "newton_explicit_euler_not_paper_explicit_rbd_solver",
            report.observed["blocking_reasons"],
        )
        self.assertIn("SolverExplicitEuler", report.observed["newton_api"])
        contact_summary = report.observed["contact_count_summary"]
        for key in ("initial", "final", "min", "max"):
            self.assertIsInstance(contact_summary[key], int)
            self.assertGreaterEqual(contact_summary[key], 0)
        self.assertGreaterEqual(contact_summary["max"], 1)
        self.assertGreaterEqual(report.observed["max_center_penetration_m"], 0.0)
        self.assertTrue(math.isfinite(report.observed["no_slip_residual_m_s"]))
        self.assertFalse(report.timing_distribution["paper_comparable"])
        self.assertGreater(report.timing_distribution["total_wall_time_ms"], 0.0)
        self.assertEqual(report.raw_outputs, {"time_series": "not_written"})
        self.assertEqual(report.plot_paths, {})

        actual_sha = validate_docs.sha256_file(
            ROOT / validate_docs.ROLLING_SPINNING_RBD_EXPLICIT_BASELINE_REPORT_PATH
        )
        self.assertEqual(
            actual_sha,
            validate_docs.PHASE75_ROLLING_SPINNING_RBD_EXPLICIT_BASELINE_SHA256,
        )

        data = yaml.safe_load((ROOT / "docs/reference/paper-claims.yaml").read_text())
        rolling = next(
            claim
            for claim in data["claims"]
            if claim["claim_id"] == "experiment.single_body.rolling_spinning"
        )
        self.assertEqual(rolling["reproduction_status"], "intended")
        audit = yaml.safe_load((ROOT / "docs/reference/reproduction-gap-audit.yaml").read_text())
        gap_entry = next(
            entry
            for entry in audit["remaining_experiment_claims"]
            if entry["claim_id"] == "experiment.single_body.rolling_spinning"
        )
        self.assertEqual(
            gap_entry["remaining_report_artifacts_missing_after_phase75"],
            ["mabd_newton", "paper_comparable_timing"],
        )
        self.assertEqual(
            gap_entry["remaining_reproduction_gaps_after_phase75"],
            [
                "paper_faithful_explicit_rbd_baseline",
                "mabd_newton",
                "paper_comparable_timing",
            ],
        )
        self.assertFalse(
            any(
                claim["claim_id"].startswith("experiment.")
                and claim["reproduction_status"] == "passed"
                for claim in data["claims"]
            )
        )
        validate_docs.validate_phase75_record()

    def test_phase75_record_has_required_evidence_fields(self) -> None:
        import scripts.validate_docs as validate_docs

        text = (
            ROOT
            / "docs/records/2026-05-20-phase75-newton-explicit-rbd-baseline.md"
        ).read_text()

        for snippet in (
            "## Status\n\npassed_for_rolling_cylinder_explicit_rbd_development_baseline_lane",
            validate_docs.PHASE75_NEWTON_EXPLICIT_EULER_SOLVER_COMMIT,
            validate_docs.PHASE75_ROLLING_CYLINDER_RBD_EXPLICIT_BASELINE_COMMIT,
            "96713fa965463b69c229a4d30582c733ff3526bb",
            "configs/experiments/single_body_rolling_spinning.yaml",
            "reports/experiment_matrix/single_body_rolling_spinning_rbd_explicit_baseline.json",
            validate_docs.PHASE75_ROLLING_SPINNING_RBD_EXPLICIT_BASELINE_SHA256,
            "vendor/newton/newton/_src/solvers/explicit_euler/solver_explicit_euler.py",
            "backend: `cpu_newton_warp`",
            "status: `incomplete`",
            "newton_explicit_euler_rolling_cylinder_rbd_cpu_development",
            "newton_development_baseline_not_paper_faithful_explicit_rbd",
            "builder.finalize(device=\"cpu\")",
            "ModelBuilder.ShapeConfig",
            "Model.contacts",
            "Model.collide",
            "SolverExplicitEuler",
            "contact_count_summary",
            "max_center_penetration_m",
            "no_slip_residual_m_s",
            "mabd_rolling_cylinder_lane_missing",
            "paper_comparable_timing_missing",
            "newton_explicit_euler_not_paper_explicit_rbd_solver",
            "paper_faithful_explicit_rbd_baseline",
            "remaining_reproduction_gaps_after_phase75",
            "-m unittest discover -s tests",
            "Ran 591 tests",
            "Phase 0/1/2/3/4/5/6/7/8/9/10/11/12/13/14/15/16/17/18/19/20/21/22/23/24/25/26/27/28/29/30/31/32/33/34/35/36/37/38/39/40/41/42/43/44/45/46/47/48/49/50/51/52/53/54/55/56/57/58/59/60/61/62/63/64/65/66/67/68/69/70/71/72/73/74/75 docs/provenance validation passed",
            "-m ruff check .",
            "git diff --check",
            "smoke_passed",
            "target_exists",
            "ready_to_sync_existing",
            "paper_comparable=false",
            "full_experiment_claim_passed=false",
            "No `experiment.*` claim is passed.",
            "mutates_reference_environment=false",
            "uses_reference_python=false",
            "uses_ambient_python=false",
        ):
            self.assertIn(snippet, text)
        self.assertNotIn("TO_BE_BACKFILLED_PHASE75", text)
        self.assertNotIn("phase75-working-tree", text)

    def test_phase76_rolling_cylinder_mabd_newton_artifact(self) -> None:
        import scripts.validate_docs as validate_docs

        boundary_text = (ROOT / "docs/reference/claim-boundaries.md").read_text()
        current = validate_docs.claim_boundary_bullet(
            boundary_text,
            "This repository contains Phase 76",
        )
        verified = validate_docs.claim_boundary_bullet(boundary_text, "Phase 76 verifies")
        non_claim = validate_docs.claim_boundary_bullet(
            boundary_text,
            "Phase 76 does not verify",
        )
        forbidden = validate_docs.claim_boundary_bullet(
            boundary_text,
            "Phase 76 rolling-cylinder SolverMABD diagnostic evidence",
        )

        self.assertIn("rolling-cylinder SolverMABD diagnostic evidence", current)
        self.assertIn("single_body_rolling_spinning_mabd_newton.json", verified)
        self.assertIn("SolverMABD.detect_static_plane_contacts", verified)
        self.assertIn("required_lanes_missing", verified)
        self.assertIn("no experiment claim passed", verified)
        for snippet in (
            "paper-faithful M-ABD rolling-cylinder collision",
            "paper-faithful rolling friction/no-slip dynamics",
            "paper-faithful explicit RBD",
            "paper-comparable performance",
            "completed rolling/spinning reproduction",
            "full paper reproduction",
            "any passed `experiment.*` claim",
        ):
            self.assertIn(snippet, non_claim)
        for snippet in (
            "paper-faithful M-ABD rolling-cylinder result",
            "paper-faithful collision result",
            "paper-comparable timing result",
            "comparative baseline pass",
            "full paper reproduction",
        ):
            self.assertIn(snippet, forbidden)

        report = load_claim_report(ROOT / validate_docs.ROLLING_SPINNING_MABD_NEWTON_REPORT_PATH)
        self.assertEqual(
            report.source_commit,
            validate_docs.PHASE76_ROLLING_CYLINDER_MABD_NEWTON_COMMIT,
        )
        self.assertEqual(report.vendored_newton_commit, "96713fa965463b69c229a4d30582c733ff3526bb")
        self.assertEqual(report.claim_id, "experiment.single_body.rolling_spinning")
        self.assertEqual(report.scene_id, "single_body_rolling_spinning")
        self.assertEqual(report.baseline_lane, "mabd_newton")
        self.assertEqual(report.solver_mode, "mabd_cpu_oracle_rolling_cylinder_newton_lane")
        self.assertEqual(report.backend, "cpu_numpy_newton_solver_mabd_static_plane_contacts")
        self.assertEqual(report.status.value, "incomplete")
        self.assertFalse(report.expected["full_experiment_claim_passed"])
        self.assertFalse(report.expected["paper_comparable"])
        self.assertFalse(report.observed["full_experiment_claim_passed"])
        self.assertFalse(report.observed["paper_comparable"])
        self.assertTrue(report.observed["local_runtime_measured"])
        self.assertEqual(report.observed["newton_device"], "cpu")
        self.assertEqual(report.observed["step_count"], 10000)
        self.assertEqual(report.observed["time_step_s"], 0.01)
        self.assertEqual(report.observed["required_lanes_missing"], ["paper_comparable_timing"])
        self.assertIn("paper_faithful_mabd_collision_missing", report.observed["blocking_reasons"])
        self.assertIn("SolverMABD.detect_static_plane_contacts", report.observed["newton_api"])
        self.assertEqual(
            report.observed["static_plane_collision_policy"],
            "mabd_affine_cylinder_static_plane_support_diagnostic",
        )
        self.assertEqual(report.observed["static_plane_cylinder_shape_count"], 1)
        contact_summary = report.observed["contact_count_summary"]
        for key in ("initial", "final", "min", "max"):
            self.assertIsInstance(contact_summary[key], int)
            self.assertGreaterEqual(contact_summary[key], 0)
        self.assertGreaterEqual(contact_summary["max"], 1)
        self.assertGreaterEqual(report.observed["max_support_penetration_m"], 0.0)
        self.assertTrue(math.isfinite(report.observed["no_slip_residual_m_s"]))
        self.assertTrue(math.isfinite(report.observed["max_affine_shape_spread_m"]))
        self.assertEqual(
            report.observed["threshold_violations"],
            [
                "max_no_slip_residual_m_s",
                "max_affine_shape_spread_m",
                "max_runtime_wall_time_ms",
            ],
        )
        self.assertFalse(report.timing_distribution["paper_comparable"])
        self.assertGreater(report.timing_distribution["total_wall_time_ms"], 0.0)
        self.assertEqual(report.raw_outputs, {"time_series": "not_written"})
        self.assertEqual(report.plot_paths, {})

        actual_sha = validate_docs.sha256_file(
            ROOT / validate_docs.ROLLING_SPINNING_MABD_NEWTON_REPORT_PATH
        )
        self.assertEqual(actual_sha, validate_docs.PHASE76_ROLLING_SPINNING_MABD_NEWTON_SHA256)

        data = yaml.safe_load((ROOT / "docs/reference/paper-claims.yaml").read_text())
        rolling = next(
            claim
            for claim in data["claims"]
            if claim["claim_id"] == "experiment.single_body.rolling_spinning"
        )
        self.assertEqual(rolling["reproduction_status"], "intended")
        audit = yaml.safe_load((ROOT / "docs/reference/reproduction-gap-audit.yaml").read_text())
        gap_entry = next(
            entry
            for entry in audit["remaining_experiment_claims"]
            if entry["claim_id"] == "experiment.single_body.rolling_spinning"
        )
        self.assertEqual(
            gap_entry["remaining_report_artifacts_missing_after_phase76"],
            ["paper_comparable_timing"],
        )
        self.assertEqual(
            gap_entry["remaining_reproduction_gaps_after_phase76"],
            [
                "paper_faithful_explicit_rbd_baseline",
                "paper_faithful_mabd_rolling_cylinder",
                "paper_comparable_timing",
            ],
        )
        self.assertFalse(
            any(
                claim["claim_id"].startswith("experiment.")
                and claim["reproduction_status"] == "passed"
                for claim in data["claims"]
            )
        )
        validate_docs.validate_phase76_record()

    def test_phase76_record_has_required_evidence_fields(self) -> None:
        import scripts.validate_docs as validate_docs

        text = (
            ROOT
            / "docs/records/2026-05-20-phase76-rolling-cylinder-mabd-newton.md"
        ).read_text()

        for snippet in (
            "## Status\n\npassed_for_rolling_cylinder_mabd_newton_diagnostic_lane",
            validate_docs.PHASE76_ROLLING_CYLINDER_MABD_NEWTON_COMMIT,
            "96713fa965463b69c229a4d30582c733ff3526bb",
            "configs/experiments/single_body_rolling_spinning.yaml",
            "reports/experiment_matrix/single_body_rolling_spinning_mabd_newton.json",
            validate_docs.PHASE76_ROLLING_SPINNING_MABD_NEWTON_SHA256,
            "backend: `cpu_numpy_newton_solver_mabd_static_plane_contacts`",
            "status: `incomplete`",
            "mabd_cpu_oracle_rolling_cylinder_newton_lane",
            "mabd_affine_cylinder_static_plane_diagnostic_not_paper_faithful",
            "builder.finalize(device=\"cpu\")",
            "SolverMABD.detect_static_plane_contacts",
            "SolverMABD.step",
            "mabd_affine_cylinder_static_plane_support_diagnostic",
            "contact_count_summary",
            "max_support_penetration_m",
            "no_slip_residual_m_s",
            "max_affine_shape_spread_m",
            "max_runtime_wall_time_ms",
            "mabd_rolling_cylinder_report_incomplete",
            "paper_faithful_mabd_collision_missing",
            "paper_faithful_explicit_rbd_baseline_missing",
            "paper_comparable_timing_missing",
            "paper_faithful_mabd_rolling_cylinder",
            "remaining_reproduction_gaps_after_phase76",
            "Ran 10 tests",
            "paper_comparable=false",
            "full_experiment_claim_passed=false",
            "No `experiment.*` claim is passed.",
            "mutates_reference_environment=false",
            "uses_reference_python=false",
            "uses_ambient_python=false",
        ):
            self.assertIn(snippet, text)
        self.assertNotIn("TO_BE_BACKFILLED_PHASE76", text)
        self.assertNotIn("phase76-working-tree", text)

    def test_phase66_validator_rejects_passed_digitized_figure_agreement(self) -> None:
        import scripts.validate_docs as validate_docs

        actual = load_claim_report(ROOT / validate_docs.SPINNING_BOX_COMPARISON_REPORT_PATH)
        corrupted = replace(
            actual,
            observed={
                **actual.observed,
                "digitized_figure_curve_agreement_passed": True,
            },
        )

        def fake_load_claim_report(path):
            if str(path).endswith(validate_docs.SPINNING_BOX_COMPARISON_REPORT_PATH):
                return corrupted
            return load_claim_report(path)

        with patch.object(validate_docs, "load_claim_report", side_effect=fake_load_claim_report):
            with self.assertRaises(SystemExit) as context:
                validate_docs.validate_phase66_record()

        self.assertIn("agreement", str(context.exception))

    def test_phase67_model_plane_constraints_are_bounded(self) -> None:
        import scripts.validate_docs as validate_docs

        text = (ROOT / "docs/reference/claim-boundaries.md").read_text()
        current = claim_boundary_bullet(text, "This repository contains Phase 67")
        verified = claim_boundary_bullet(text, "Phase 67 verifies")
        non_claim = claim_boundary_bullet(text, "Phase 67 does not verify")
        forbidden = claim_boundary_bullet(
            text,
            "Phase 67 model-derived point-plane normal constraint",
        )

        self.assertIn("model-derived point-plane normal constraint row extraction evidence", current)
        self.assertIn("mabd:plane_constraint", verified)
        self.assertIn("mabd:plane_body", verified)
        self.assertIn("mabd:plane_rest_point", verified)
        self.assertIn("mabd:plane_normal", verified)
        self.assertIn("mabd:plane_offset", verified)
        self.assertIn("mabd:plane_active", verified)
        self.assertIn("vendored/local Newton CPU oracle config", verified)
        self.assertIn("SolverMABD.step()", verified)
        for snippet in (
            "contact solver",
            "Newton `Contacts` ingestion",
            "collision detection",
            "active-set generation",
            "IPC",
            "generic inequality-constrained M-ABD KKT",
            "paper-faithful affine contact",
            "paper-faithful M-ABD stepping",
            "comparison pass gate",
            "runtime performance",
            "any passed `experiment.*` claim",
            "full paper reproduction",
        ):
            self.assertIn(snippet, non_claim)
        for snippet in (
            "unmodified Newton M-ABD support",
            "paper-faithful affine collision/contact",
            "contact solver",
            "full paper reproduction",
        ):
            self.assertIn(snippet, forbidden)

        data = yaml.safe_load((ROOT / "docs/reference/paper-claims.yaml").read_text())
        self.assertFalse(
            any(
                claim["claim_id"].startswith("experiment.")
                and claim["reproduction_status"] == "passed"
                for claim in data["claims"]
            )
        )
        contact_claim = next(
            claim
            for claim in data["claims"]
            if claim["claim_id"] == "method.force_mapping.point_load_penalty_contact"
        )
        self.assertEqual(
            contact_claim["conflict_note"],
            "CPU oracle force mapping only; not collision detection, friction, broadphase, or a full contact solver",
        )
        validate_docs.validate_phase67_record()

    def test_phase67_record_has_required_evidence_fields(self) -> None:
        import scripts.validate_docs as validate_docs

        text = (
            ROOT / "docs/records/2026-05-19-phase67-model-plane-constraints.md"
        ).read_text()

        for snippet in (
            "## Status\n\npassed_for_solver_model_plane_constraint_config_slice",
            "phase67-model-plane-constraints",
            validate_docs.PHASE67_MODEL_PLANE_CONSTRAINT_COMMIT,
            "96713fa965463b69c229a4d30582c733ff3526bb",
            "local patch files:",
            "vendor/newton/newton/_src/solvers/mabd/solver_mabd.py",
            "tests/test_mabd_phase4_solver_step.py",
            "vendor/newton/newton/tests/test_mabd_phase4_solver_step.py",
            "Phase67 modifies vendored Newton inside this repository; unmodified Newton support is not claimed.",
            "mutates_reference_environment=false",
            "uses_ambient_python=false",
            "mabd:plane_constraint",
            "mabd:plane_body",
            "mabd:plane_rest_point",
            "mabd:plane_normal",
            "mabd:plane_offset",
            "mabd:plane_active",
            "requested=1",
            "accepted=1",
            "skipped=0",
            "manual-config precedence smoke",
            "NotImplementedError",
            "No `experiment.*` claim is passed.",
            "`paper-claims.yaml` is unchanged.",
            "not a contact solver",
            "not Newton `Contacts` ingestion",
            "not paper-faithful affine collision/contact",
            "not unmodified Newton M-ABD support",
            "not full paper reproduction",
            "PYTHONPATH=vendor/newton",
            "scripts/env/readiness_check.py",
            "git diff --check",
        ):
            self.assertIn(snippet, text)
        self.assertNotIn("TO_BE_BACKFILLED_PHASE67", text)
        self.assertNotIn("phase67-working-tree", text)

    def test_phase67_validator_rejects_missing_local_patch_provenance(self) -> None:
        import scripts.validate_docs as validate_docs

        record_path = validate_docs.ROOT / "docs/records/2026-05-19-phase67-model-plane-constraints.md"
        original_read_text = Path.read_text

        def fake_read_text(path, *args, **kwargs):
            text = original_read_text(path, *args, **kwargs)
            if Path(path) == record_path:
                text = text.replace(
                    "- local patch files:\n"
                    "  - `vendor/newton/newton/_src/solvers/mabd/solver_mabd.py`\n"
                    "  - `tests/test_mabd_phase4_solver_step.py`\n"
                    "  - `vendor/newton/newton/tests/test_mabd_phase4_solver_step.py`\n",
                    "",
                )
            return text

        with patch.object(Path, "read_text", fake_read_text):
            with self.assertRaises(SystemExit) as context:
                validate_docs.validate_phase67_record()

        self.assertIn("local patch files", str(context.exception))

    def test_phase67_validator_rejects_record_overclaims(self) -> None:
        import scripts.validate_docs as validate_docs

        record_path = validate_docs.ROOT / "docs/records/2026-05-19-phase67-model-plane-constraints.md"
        original_read_text = Path.read_text

        def fake_read_text(path, *args, **kwargs):
            text = original_read_text(path, *args, **kwargs)
            if Path(path) == record_path:
                return f"{text}\ncontact solver implemented\n"
            return text

        with patch.object(Path, "read_text", fake_read_text):
            with self.assertRaises(SystemExit) as context:
                validate_docs.validate_phase67_record()

        self.assertIn("overclaims unsupported evidence", str(context.exception))

    def test_phase67_validator_rejects_passed_experiment_claim(self) -> None:
        import scripts.validate_docs as validate_docs

        data = yaml.safe_load((ROOT / "docs/reference/paper-claims.yaml").read_text())
        corrupted = {
            **data,
            "claims": [
                {
                    **claim,
                    "reproduction_status": (
                        "passed"
                        if claim["claim_id"] == "experiment.single_body.spinning_box"
                        else claim["reproduction_status"]
                    ),
                }
                for claim in data["claims"]
            ],
        }

        def fake_read_yaml(path):
            if str(path).endswith("paper-claims.yaml"):
                return corrupted
            return validate_docs.read_yaml(path)

        with patch.object(validate_docs, "read_yaml", side_effect=fake_read_yaml):
            with self.assertRaises(SystemExit) as context:
                validate_docs.validate_phase67_record()

        self.assertIn("experiment claim status", str(context.exception))

    def test_phase67_validator_rejects_failed_model_plane_smoke(self) -> None:
        import scripts.validate_docs as validate_docs

        with patch.object(
            validate_docs,
            "_phase67_model_plane_constraint_smoke",
            side_effect=SystemExit("validate_docs.py: Phase 67 smoke residual exceeded tolerance"),
        ):
            with self.assertRaises(SystemExit) as context:
                validate_docs.validate_phase67_record()

        self.assertIn("Phase 67 smoke residual", str(context.exception))

    def test_phase68_model_plane_report_lane_is_bounded(self) -> None:
        import scripts.validate_docs as validate_docs

        text = (ROOT / "docs/reference/claim-boundaries.md").read_text()
        current = claim_boundary_bullet(text, "This repository contains Phase 68")
        verified = claim_boundary_bullet(text, "Phase 68 verifies")
        non_claim = claim_boundary_bullet(text, "Phase 68 does not verify")
        forbidden = claim_boundary_bullet(
            text,
            "Phase 68 SolverMABD model-plane report lane evidence",
        )

        self.assertIn("SolverMABD model-plane spinning-box diagnostic report lane evidence", current)
        self.assertIn("SolverMABD.step()", verified)
        self.assertIn("mabd:body", verified)
        self.assertIn("mabd:plane_constraint", verified)
        self.assertIn("free-predict/active point-plane normal constraint policy", verified)
        self.assertIn(validate_docs.SPINNING_BOX_MODEL_PLANE_CONSTRAINT_REPORT_PATH, verified)
        self.assertIn("model_plane_constraint_config_source", verified)
        self.assertIn("reduced free-predicted penetration", verified)
        for snippet in (
            "contact solver",
            "Newton `Contacts` ingestion",
            "collision detection",
            "broadphase or narrowphase",
            "active-set generation inside Newton",
            "IPC",
            "friction",
            "complementarity",
            "continuous collision detection",
            "generic inequality-constrained M-ABD KKT",
            "paper-faithful affine contact",
            "paper-faithful M-ABD stepping",
            "comparison pass gate",
            "rendered-output agreement",
            "runtime performance",
            "any passed `experiment.*` claim",
            "full paper reproduction",
        ):
            self.assertIn(snippet, non_claim)
        for snippet in (
            "unmodified Newton M-ABD contact support",
            "paper-faithful affine collision/contact",
            "contact solver",
            "passed spinning-box experiment",
            "full paper reproduction",
        ):
            self.assertIn(snippet, forbidden)

        report = load_claim_report(ROOT / validate_docs.SPINNING_BOX_MODEL_PLANE_CONSTRAINT_REPORT_PATH)
        self.assertEqual(report.source_commit, validate_docs.PHASE68_MODEL_PLANE_REPORT_LANE_COMMIT)
        self.assertEqual(report.vendored_newton_commit, "96713fa965463b69c229a4d30582c733ff3526bb")
        self.assertEqual(report.claim_id, "experiment.single_body.spinning_box")
        self.assertEqual(report.scene_id, "single_body_spinning_box")
        self.assertEqual(report.status.value, "incomplete")
        self.assertEqual(report.baseline_lane, "mabd_newton")
        self.assertEqual(report.solver_mode, "solver_mabd_model_plane_constraint_diagnostic")
        self.assertEqual(report.backend, "cpu_numpy_newton_solver_mabd_model_rows")
        observed = report.observed
        self.assertNotIn("lane_gate_status", observed)
        self.assertEqual(
            observed["model_plane_constraint_policy"],
            "solver_mabd_model_rows_free_predict_then_active_plane_constraints",
        )
        self.assertEqual(observed["model_plane_constraint_scope"], "diagnostic_only_no_lane_gate")
        self.assertEqual(
            observed["model_plane_constraint_config_source"],
            "mabd:plane_constraint_custom_rows",
        )
        self.assertTrue(observed["model_plane_constraint_reduced_free_predicted_penetration"])
        self.assertGreater(
            observed["max_free_predicted_contact_penetration_m"],
            observed["max_constrained_contact_penetration_m"],
        )
        self.assertEqual(observed["max_requested_plane_constraint_count"], 4)
        self.assertEqual(observed["max_accepted_plane_constraint_count"], 3)
        self.assertEqual(observed["max_skipped_plane_constraint_count"], 1)
        self.assertLess(observed["max_model_plane_constraint_residual_norm"], 1.0e-12)
        self.assertEqual(len(observed["model_plane_constraint_results"]), 2)
        for result in observed["model_plane_constraint_results"]:
            self.assertNotEqual(
                result["contact_diagnostic_status"],
                "contact_penetration_observed_without_response",
            )
        self.assertEqual(
            validate_docs.sha256_file(ROOT / validate_docs.SPINNING_BOX_MODEL_PLANE_CONSTRAINT_REPORT_PATH),
            validate_docs.PHASE68_SPINNING_BOX_MODEL_PLANE_CONSTRAINT_SHA256,
        )

        data = yaml.safe_load((ROOT / "docs/reference/paper-claims.yaml").read_text())
        self.assertFalse(
            any(
                claim["claim_id"].startswith("experiment.")
                and claim["reproduction_status"] == "passed"
                for claim in data["claims"]
            )
        )
        validate_docs.validate_phase68_record()

    def test_phase68_record_has_required_evidence_fields(self) -> None:
        import scripts.validate_docs as validate_docs

        text = (
            ROOT / "docs/records/2026-05-19-phase68-model-plane-report-lane.md"
        ).read_text()

        for snippet in (
            "## Status\n\npassed_for_solver_mabd_model_plane_report_diagnostic",
            "phase68-model-plane-report-lane",
            validate_docs.PHASE68_MODEL_PLANE_REPORT_LANE_COMMIT,
            "96713fa965463b69c229a4d30582c733ff3526bb",
            validate_docs.SPINNING_BOX_MODEL_PLANE_CONSTRAINT_REPORT_PATH,
            validate_docs.PHASE68_SPINNING_BOX_MODEL_PLANE_CONSTRAINT_SHA256,
            "paper_horizon.model_plane_constraint_output_report",
            "run_spinning_box_model_plane_constraint",
            "write_spinning_box_model_plane_constraint_report",
            "_run_spinning_box_solver_mabd_model_step",
            "SolverMABD.step()",
            "mabd:plane_constraint",
            "MABDCPUOraclePlaneConstraint",
            "solver_mabd_model_rows_free_predict_then_active_plane_constraints",
            "model_plane_constraint_config_source = mabd:plane_constraint_custom_rows",
            "max_requested_plane_constraint_count = 4",
            "max_accepted_plane_constraint_count = 3",
            "max_skipped_plane_constraint_count = 1",
            "contact_penetration_observed_after_normal_constraint",
            "spinning_box_model_plane_constraint_not_paper_faithful",
            "target_exists",
            "smoke_passed",
            "mutates_reference_environment=false",
            "uses_reference_python=false",
            "uses_ambient_python=false",
            "No `experiment.*` claim is passed.",
            "`paper-claims.yaml` is unchanged.",
            "not Newton `Contacts` ingestion",
            "not paper-faithful affine collision/contact",
            "not full paper reproduction",
            "scripts/env/readiness_check.py",
            "PYTHONPATH=vendor/newton",
            "git diff --check",
        ):
            self.assertIn(snippet, text)
        self.assertNotIn("TO_BE_BACKFILLED_PHASE68", text)
        self.assertNotIn("phase68-working-tree", text)

    def test_phase68_validator_rejects_lane_gate_overclaim(self) -> None:
        import scripts.validate_docs as validate_docs

        actual = load_claim_report(ROOT / validate_docs.SPINNING_BOX_MODEL_PLANE_CONSTRAINT_REPORT_PATH)
        corrupted = replace(
            actual,
            observed={
                **actual.observed,
                "lane_gate_status": "passed",
            },
        )

        def fake_load_claim_report(path):
            if str(path).endswith(validate_docs.SPINNING_BOX_MODEL_PLANE_CONSTRAINT_REPORT_PATH):
                return corrupted
            return load_claim_report(path)

        with patch.object(validate_docs, "load_claim_report", side_effect=fake_load_claim_report):
            with self.assertRaises(SystemExit) as context:
                validate_docs.validate_phase68_record()

        self.assertIn("lane_gate_status", str(context.exception))

    def test_phase68_validator_rejects_timestep_grid_mismatch(self) -> None:
        import scripts.validate_docs as validate_docs

        actual = load_claim_report(ROOT / validate_docs.SPINNING_BOX_MODEL_PLANE_CONSTRAINT_REPORT_PATH)
        corrupted = replace(
            actual,
            expected={
                **actual.expected,
                "paper_step_sizes_s": [0.01, 0.01],
            },
        )

        def fake_load_claim_report(path):
            if str(path).endswith(validate_docs.SPINNING_BOX_MODEL_PLANE_CONSTRAINT_REPORT_PATH):
                return corrupted
            return load_claim_report(path)

        with patch.object(validate_docs, "load_claim_report", side_effect=fake_load_claim_report):
            with self.assertRaises(SystemExit) as context:
                validate_docs.validate_phase68_record()

        self.assertIn("timestep grid", str(context.exception))

    def test_phase68_validator_rejects_stale_plane_count_aggregates(self) -> None:
        import scripts.validate_docs as validate_docs

        actual = load_claim_report(ROOT / validate_docs.SPINNING_BOX_MODEL_PLANE_CONSTRAINT_REPORT_PATH)
        corrupted_results = [
            {
                **result,
                "max_requested_plane_constraint_count": 1,
                "max_accepted_plane_constraint_count": 1,
                "max_skipped_plane_constraint_count": 0,
            }
            for result in actual.observed["model_plane_constraint_results"]
        ]
        corrupted = replace(
            actual,
            observed={
                **actual.observed,
                "model_plane_constraint_results": corrupted_results,
            },
        )

        def fake_load_claim_report(path):
            if str(path).endswith(validate_docs.SPINNING_BOX_MODEL_PLANE_CONSTRAINT_REPORT_PATH):
                return corrupted
            return load_claim_report(path)

        with patch.object(validate_docs, "load_claim_report", side_effect=fake_load_claim_report):
            with self.assertRaises(SystemExit) as context:
                validate_docs.validate_phase68_record()

        self.assertIn("aggregate", str(context.exception))

    def test_phase68_validator_rejects_passed_experiment_claim(self) -> None:
        import scripts.validate_docs as validate_docs

        data = yaml.safe_load((ROOT / "docs/reference/paper-claims.yaml").read_text())
        corrupted = {
            **data,
            "claims": [
                {
                    **claim,
                    "reproduction_status": (
                        "passed"
                        if claim["claim_id"] == "experiment.single_body.spinning_box"
                        else claim["reproduction_status"]
                    ),
                }
                for claim in data["claims"]
            ],
        }

        def fake_read_yaml(path):
            if str(path).endswith("paper-claims.yaml"):
                return corrupted
            return validate_docs.read_yaml(path)

        with patch.object(validate_docs, "read_yaml", side_effect=fake_read_yaml):
            with self.assertRaises(SystemExit) as context:
                validate_docs.validate_phase68_record()

        self.assertIn("experiment claim status", str(context.exception))

    def test_phase69_contacts_input_plane_constraints_are_bounded(self) -> None:
        import scripts.validate_docs as validate_docs

        phase69_commit = "674064f7558527da92be0f186361df4a7c71d4f7"
        self.assertEqual(validate_docs.PHASE69_CONTACTS_INPUT_COMMIT, phase69_commit)
        self.assertEqual(
            validate_docs.PHASE69_STATIC_CONTACT_REVIEW_FIX_COMMIT,
            "4659b13662df287a406d1cc1c4a652d2eb156ab7",
        )

        text = (ROOT / "docs/reference/claim-boundaries.md").read_text()
        current = claim_boundary_bullet(text, "This repository contains Phase 69")
        verified = claim_boundary_bullet(text, "Phase 69 verifies")
        non_claim = claim_boundary_bullet(text, "Phase 69 does not verify")
        forbidden = claim_boundary_bullet(
            text,
            "Phase 69 SolverMABD Contacts input evidence",
        )

        self.assertIn("SolverMABD Contacts input plane-constraint plumbing evidence", current)
        self.assertIn("SolverMABD.step(..., contacts=...)", verified)
        self.assertIn("newton.Contacts.rigid_contact_*", verified)
        self.assertIn("shape_body == -1", verified)
        self.assertIn("rigid_contacts_to_point_plane_constraints_diagnostic", verified)
        self.assertIn("diagnostic_only_static_geometry_plane_constraints", verified)
        self.assertIn("last_contacts_input_summary", verified)
        self.assertIn("no experiment claim passed", verified)
        for snippet in (
            "contact solver",
            "collision detection",
            "broadphase or narrowphase",
            "active-set generation inside Newton",
            "IPC",
            "friction",
            "complementarity",
            "continuous collision detection",
            "body-body affine contact",
            "dynamic non-M-ABD body contact",
            "generic inequality-constrained M-ABD KKT",
            "paper-faithful affine collision/contact",
            "paper-faithful M-ABD stepping",
            "comparison pass gate",
            "rendered-output agreement",
            "runtime performance",
            "any passed `experiment.*` claim",
            "full paper reproduction",
        ):
            self.assertIn(snippet, non_claim)
        for snippet in (
            "contact solver",
            "collision detection",
            "paper-faithful affine collision/contact",
            "generic inequality-constrained M-ABD KKT",
            "passed experiment",
            "full paper reproduction",
        ):
            self.assertIn(snippet, forbidden)

        solver_source = (
            ROOT / "vendor/newton/newton/_src/solvers/mabd/solver_mabd.py"
        ).read_text()
        for snippet in (
            "MABDContactsInputSummary",
            "last_contacts_input_summary",
            "_cpu_oracle_config_with_contacts",
            "rigid_contacts_to_point_plane_constraints_diagnostic",
            "newton.Contacts.rigid_contact_*",
            "diagnostic_only_static_geometry_plane_constraints",
            "newton_body1 != -1",
            "newton_body0 != -1",
            "duplicate mabd:body_index mapping for Newton body",
        ):
            self.assertIn(snippet, solver_source)

        test_source = (
            ROOT / "vendor/newton/newton/tests/test_mabd_phase4_solver_step.py"
        ).read_text()
        repo_test_source = (ROOT / "tests/test_mabd_phase4_solver_step.py").read_text()
        for snippet in (
            "test_solver_step_consumes_newton_contacts_as_plane_constraints",
            "test_solver_step_flips_contact_normal_when_mabd_body_is_shape1",
            "test_solver_step_records_skipped_and_overflow_contact_rows",
            "test_solver_step_skips_dynamic_non_mabd_contact_rows",
            "test_solver_step_rejects_duplicate_mabd_body_index_mapping_for_contacts",
            "test_solver_step_clears_contacts_summary_when_contacts_none",
        ):
            self.assertIn(snippet, test_source)
            self.assertIn(snippet, repo_test_source)

        data = yaml.safe_load((ROOT / "docs/reference/paper-claims.yaml").read_text())
        spinning_box = next(
            claim for claim in data["claims"] if claim["claim_id"] == "experiment.single_body.spinning_box"
        )
        self.assertEqual(spinning_box["reproduction_status"], "intended")
        contact_claim = next(
            claim
            for claim in data["claims"]
            if claim["claim_id"] == "method.force_mapping.point_load_penalty_contact"
        )
        self.assertEqual(contact_claim["reproduction_status"], "passed")
        self.assertIn("not collision detection", contact_claim["conflict_note"])

        validate_docs.validate_phase69_record()

    def test_phase69_record_has_required_evidence_fields(self) -> None:
        import scripts.validate_docs as validate_docs

        text = (
            ROOT / "docs/records/2026-05-19-phase69-contacts-input-plane-constraints.md"
        ).read_text()

        for snippet in (
            "## Status\n\npassed_for_solver_mabd_contacts_input_plumbing",
            "phase68-model-plane-report-lane",
            validate_docs.PHASE69_CONTACTS_INPUT_COMMIT,
            validate_docs.PHASE69_STATIC_CONTACT_REVIEW_FIX_COMMIT,
            "1df81a6",
            "96713fa965463b69c229a4d30582c733ff3526bb",
            "paper source version: `2603.08079v2`",
            "config path: `not applicable; unit-test ModelBuilder fixtures only`",
            "backend: `cpu_numpy_newton_solver_mabd_contacts_input_diagnostic`",
            "random seed: `not applicable`",
            "SolverMABD.step(..., contacts=...)",
            "MABDContactsInputSummary",
            "last_contacts_input_summary",
            "rigid_contacts_to_point_plane_constraints_diagnostic",
            "newton.Contacts.rigid_contact_*",
            "diagnostic_only_static_geometry_plane_constraints",
            "shape_body == -1",
            "dynamic non-M-ABD contact rows are skipped",
            "rigid_contact_overflow_count",
            "generated_plane_constraint_count",
            "skipped_contact_count",
            "dynamic non-M-ABD generated plane constraints",
            "dynamic non-M-ABD skipped contacts",
            "raw artifacts:",
            "Control input remains unsupported",
            "mutates_reference_environment=false",
            "uses_reference_python=false",
            "uses_ambient_python=false",
            "No `experiment.*` claim is passed.",
            "`paper-claims.yaml` is unchanged.",
            "not collision detection",
            "not contact solver",
            "not paper-faithful affine collision/contact",
            "not full paper reproduction",
            "PYTHONPATH=vendor/newton",
            "scripts/env/readiness_check.py",
            "git diff --check",
        ):
            self.assertIn(snippet, text)
        self.assertNotIn("TO_BE_BACKFILLED_PHASE69", text)
        self.assertNotIn("phase69-working-tree", text)

    def test_phase69_validator_rejects_missing_summary_contract(self) -> None:
        import scripts.validate_docs as validate_docs

        actual_record = (
            ROOT / "docs/records/2026-05-19-phase69-contacts-input-plane-constraints.md"
        ).read_text()
        corrupted_record = actual_record.replace("last_contacts_input_summary", "missing_summary")

        original_read_text = Path.read_text

        def fake_read_text(path, *args, **kwargs):
            if str(path).endswith("2026-05-19-phase69-contacts-input-plane-constraints.md"):
                return corrupted_record
            return original_read_text(path, *args, **kwargs)

        with patch.object(Path, "read_text", fake_read_text):
            with self.assertRaises(SystemExit) as context:
                validate_docs.validate_phase69_record()

        self.assertIn("last_contacts_input_summary", str(context.exception))

    def test_phase69_validator_rejects_passed_experiment_claim(self) -> None:
        import scripts.validate_docs as validate_docs

        data = yaml.safe_load((ROOT / "docs/reference/paper-claims.yaml").read_text())
        corrupted = {
            **data,
            "claims": [
                {
                    **claim,
                    "reproduction_status": (
                        "passed"
                        if claim["claim_id"] == "experiment.single_body.spinning_box"
                        else claim["reproduction_status"]
                    ),
                }
                for claim in data["claims"]
            ],
        }

        def fake_read_yaml(path):
            if str(path).endswith("paper-claims.yaml"):
                return corrupted
            return validate_docs.read_yaml(path)

        with patch.object(validate_docs, "read_yaml", side_effect=fake_read_yaml):
            with self.assertRaises(SystemExit) as context:
                validate_docs.validate_phase69_record()

        self.assertIn("experiment claim status", str(context.exception))

    def test_phase70_contacts_input_report_lane_is_bounded(self) -> None:
        import scripts.validate_docs as validate_docs

        self.assertEqual(
            validate_docs.PHASE70_CONTACTS_INPUT_REPORT_LANE_COMMIT,
            "493cc1ac9cb0eb11faac89b1540813b3dab4bcd1",
        )
        self.assertEqual(
            validate_docs.PHASE70_SPINNING_BOX_CONTACTS_INPUT_SHA256,
            "a9076b8df0eff7d5f98b042f9a6d6d293ae772181b41ed0f23c80a3627e5160d",
        )

        text = (ROOT / "docs/reference/claim-boundaries.md").read_text()
        current = claim_boundary_bullet(text, "This repository contains Phase 70")
        verified = claim_boundary_bullet(text, "Phase 70 verifies")
        non_claim = claim_boundary_bullet(text, "Phase 70 does not verify")
        forbidden = claim_boundary_bullet(
            text,
            "Phase 70 SolverMABD Contacts input report lane evidence",
        )

        self.assertIn("Contacts input spinning-box diagnostic report lane evidence", current)
        self.assertIn("SolverMABD.step(..., contacts=...)", verified)
        self.assertIn("newton.Contacts", verified)
        self.assertIn("rigid_contact_static_plane_rows_from_diagnostic_corners", verified)
        self.assertIn("shape_body == -1", verified)
        self.assertIn("contacts_input_summary_source = last_contacts_input_summary", verified)
        self.assertIn(validate_docs.SPINNING_BOX_CONTACTS_INPUT_REPORT_PATH, verified)
        self.assertIn("reduced free-predicted penetration", verified)
        for snippet in (
            "contact solver",
            "collision detection",
            "broadphase or narrowphase",
            "active-set generation inside Newton",
            "IPC",
            "friction",
            "complementarity",
            "continuous collision detection",
            "body-body affine contact",
            "dynamic non-M-ABD body contact",
            "generic inequality-constrained M-ABD KKT",
            "paper-faithful affine collision/contact",
            "paper-faithful M-ABD stepping",
            "comparison pass gate",
            "rendered-output agreement",
            "runtime performance",
            "any passed `experiment.*` claim",
            "full paper reproduction",
        ):
            self.assertIn(snippet, non_claim)
        for snippet in (
            "contact solver",
            "collision detection",
            "paper-faithful affine collision/contact",
            "generic inequality-constrained M-ABD KKT",
            "passed experiment",
            "full paper reproduction",
        ):
            self.assertIn(snippet, forbidden)

        report = load_claim_report(ROOT / validate_docs.SPINNING_BOX_CONTACTS_INPUT_REPORT_PATH)
        self.assertEqual(report.source_commit, validate_docs.PHASE70_CONTACTS_INPUT_REPORT_LANE_COMMIT)
        self.assertEqual(report.vendored_newton_commit, "96713fa965463b69c229a4d30582c733ff3526bb")
        self.assertEqual(report.claim_id, "experiment.single_body.spinning_box")
        self.assertEqual(report.scene_id, "single_body_spinning_box")
        self.assertEqual(report.status.value, "incomplete")
        self.assertEqual(report.baseline_lane, "mabd_newton")
        self.assertEqual(report.solver_mode, "solver_mabd_contacts_input_diagnostic")
        self.assertEqual(report.backend, "cpu_numpy_newton_solver_mabd_contacts_input_diagnostic")
        observed = report.observed
        self.assertNotIn("lane_gate_status", observed)
        self.assertEqual(
            observed["contacts_input_policy"],
            "solver_mabd_contacts_input_free_predict_then_static_plane_constraints",
        )
        self.assertEqual(
            observed["contacts_input_source"],
            "newton.Contacts.rigid_contact_static_plane_rows_from_diagnostic_corners",
        )
        self.assertEqual(observed["contacts_input_summary_source"], "last_contacts_input_summary")
        self.assertEqual(
            observed["contacts_input_scope"],
            "diagnostic_only_static_geometry_plane_constraints_no_lane_gate",
        )
        self.assertTrue(observed["contacts_input_reduced_free_predicted_penetration"])
        self.assertGreater(
            observed["max_free_predicted_contact_penetration_m"],
            observed["max_constrained_contact_penetration_m"],
        )
        self.assertEqual(observed["max_contacts_input_rigid_contact_count"], 4)
        self.assertEqual(observed["max_contacts_input_rows_read"], 4.0)
        self.assertEqual(observed["max_contacts_input_generated_plane_constraint_count"], 4)
        self.assertEqual(observed["max_contacts_input_skipped_contact_count"], 0)
        self.assertEqual(observed["max_contacts_input_overflow_count"], 0)
        self.assertLess(observed["max_contacts_input_constraint_residual_norm"], 1.0e-12)
        self.assertEqual(len(observed["contacts_input_results"]), 2)
        for result in observed["contacts_input_results"]:
            self.assertEqual(
                result["contacts_input_source"],
                "newton.Contacts.rigid_contact_static_plane_rows_from_diagnostic_corners",
            )
            self.assertEqual(result["contacts_input_summary_source"], "last_contacts_input_summary")
            self.assertEqual(
                result["contacts_input_scope"],
                "diagnostic_only_static_geometry_plane_constraints_no_lane_gate",
            )
            self.assertEqual(result["contacts_input_overflow_count"], 0)
            self.assertGreaterEqual(result["contacts_input_generated_plane_constraint_count"], 0)
            self.assertTrue(math.isfinite(result["max_contacts_input_constraint_residual_norm"]))
        blockers = observed["blocking_reasons"]
        self.assertIn("spinning_box_contacts_input_not_paper_faithful", blockers)
        self.assertIn("collision_detection_not_enabled_for_contacts_input", blockers)
        self.assertEqual(
            validate_docs.sha256_file(ROOT / validate_docs.SPINNING_BOX_CONTACTS_INPUT_REPORT_PATH),
            validate_docs.PHASE70_SPINNING_BOX_CONTACTS_INPUT_SHA256,
        )

        data = yaml.safe_load((ROOT / "docs/reference/paper-claims.yaml").read_text())
        self.assertFalse(
            any(
                claim["claim_id"].startswith("experiment.")
                and claim["reproduction_status"] == "passed"
                for claim in data["claims"]
            )
        )
        validate_docs.validate_phase70_record()

    def test_phase71_affine_static_plane_contacts_report_lane_is_bounded(self) -> None:
        import scripts.validate_docs as validate_docs

        self.assertEqual(
            validate_docs.PHASE71_AFFINE_STATIC_PLANE_CONTACTS_COMMIT,
            "de79f7a5da8a62064dc463ecd0a3ed874d43bf0e",
        )
        self.assertEqual(
            validate_docs.PHASE71_SPINNING_BOX_AFFINE_STATIC_PLANE_CONTACTS_SHA256,
            "e5f6babcf0c78c217757e13dd7afadc9963048226745528221d38213d2c7477d",
        )

        text = (ROOT / "docs/reference/claim-boundaries.md").read_text()
        current = claim_boundary_bullet(text, "This repository contains Phase 71")
        verified = claim_boundary_bullet(text, "Phase 71 verifies")
        non_claim = claim_boundary_bullet(text, "Phase 71 does not verify")
        forbidden = claim_boundary_bullet(
            text,
            "Phase 71 affine static-plane contact report lane evidence",
        )

        self.assertIn("affine static-plane active-set diagnostic report lane", current)
        self.assertIn("SolverMABD.detect_static_plane_contacts", verified)
        self.assertIn("affine box corners", verified)
        self.assertIn("static infinite planes", verified)
        self.assertIn("paper_horizon.affine_static_plane_contacts_output_report", verified)
        self.assertIn(validate_docs.SPINNING_BOX_AFFINE_STATIC_PLANE_CONTACTS_REPORT_PATH, verified)
        self.assertIn("contacts_input_summary_source = last_contacts_input_summary", verified)
        self.assertIn("reduced free-predicted penetration", verified)
        for snippet in (
            "generic collision detection",
            "broadphase or narrowphase",
            "body-body affine contact",
            "finite-plane clipping",
            "contact solver",
            "IPC",
            "friction",
            "complementarity",
            "continuous collision detection",
            "generic inequality-constrained M-ABD KKT",
            "paper-faithful affine collision/contact",
            "comparison pass gate",
            "rendered-output agreement",
            "runtime performance",
            "any passed `experiment.*` claim",
            "full paper reproduction",
        ):
            self.assertIn(snippet, non_claim)
        for snippet in (
            "generic collision detection",
            "contact solver",
            "paper-faithful affine collision/contact",
            "passed experiment",
            "full paper reproduction",
        ):
            self.assertIn(snippet, forbidden)

        report = load_claim_report(
            ROOT / validate_docs.SPINNING_BOX_AFFINE_STATIC_PLANE_CONTACTS_REPORT_PATH
        )
        self.assertEqual(report.source_commit, validate_docs.PHASE71_AFFINE_STATIC_PLANE_CONTACTS_COMMIT)
        self.assertEqual(report.vendored_newton_commit, "96713fa965463b69c229a4d30582c733ff3526bb")
        self.assertEqual(report.claim_id, "experiment.single_body.spinning_box")
        self.assertEqual(report.scene_id, "single_body_spinning_box")
        self.assertEqual(report.status.value, "incomplete")
        self.assertEqual(report.baseline_lane, "mabd_newton")
        self.assertEqual(
            report.solver_mode,
            "solver_mabd_affine_static_plane_contacts_diagnostic",
        )
        self.assertEqual(
            report.backend,
            "cpu_numpy_newton_solver_mabd_affine_static_plane_contacts_diagnostic",
        )
        observed = report.observed
        self.assertNotIn("lane_gate_status", observed)
        self.assertEqual(
            observed["affine_static_plane_contact_policy"],
            "solver_mabd_detect_affine_box_static_plane_contacts",
        )
        self.assertEqual(
            observed["affine_static_plane_contact_source"],
            "SolverMABD.detect_static_plane_contacts",
        )
        self.assertEqual(observed["contacts_input_summary_source"], "last_contacts_input_summary")
        self.assertTrue(observed["affine_static_plane_contacts_reduced_free_predicted_penetration"])
        self.assertGreater(
            observed["max_free_predicted_contact_penetration_m"],
            observed["max_constrained_contact_penetration_m"],
        )
        self.assertEqual(observed["max_affine_static_plane_candidate_contact_count"], 4)
        self.assertEqual(observed["max_affine_static_plane_rows_written"], 4)
        self.assertEqual(observed["max_contacts_input_generated_plane_constraint_count"], 4)
        self.assertEqual(observed["max_contacts_input_overflow_count"], 0)
        self.assertLess(observed["max_contacts_input_constraint_residual_norm"], 1.0e-12)
        self.assertEqual(len(observed["affine_static_plane_contacts_results"]), 2)
        for result in observed["affine_static_plane_contacts_results"]:
            self.assertEqual(
                result["affine_static_plane_contact_source"],
                "SolverMABD.detect_static_plane_contacts",
            )
            self.assertEqual(result["contacts_input_summary_source"], "last_contacts_input_summary")
            self.assertEqual(result["contacts_input_overflow_count"], 0)
            self.assertGreaterEqual(result["affine_static_plane_candidate_contact_count"], 0)
            self.assertGreaterEqual(result["contacts_input_generated_plane_constraint_count"], 0)
            self.assertTrue(math.isfinite(result["max_contacts_input_constraint_residual_norm"]))
        blockers = observed["blocking_reasons"]
        self.assertIn("spinning_box_affine_static_plane_contacts_not_paper_faithful", blockers)
        self.assertNotIn("collision_detection_not_enabled_for_contacts_input", blockers)
        self.assertEqual(
            validate_docs.sha256_file(
                ROOT / validate_docs.SPINNING_BOX_AFFINE_STATIC_PLANE_CONTACTS_REPORT_PATH
            ),
            validate_docs.PHASE71_SPINNING_BOX_AFFINE_STATIC_PLANE_CONTACTS_SHA256,
        )

        data = yaml.safe_load((ROOT / "docs/reference/paper-claims.yaml").read_text())
        self.assertFalse(
            any(
                claim["claim_id"].startswith("experiment.")
                and claim["reproduction_status"] == "passed"
                for claim in data["claims"]
            )
        )
        validate_docs.validate_phase71_record()

    def test_phase49_heavy_top_rk4_reference_is_bounded(self) -> None:
        data = yaml.safe_load((ROOT / "docs/reference/paper-claims.yaml").read_text())
        heavy_top_claim = next(
            claim for claim in data["claims"] if claim["claim_id"] == "experiment.single_body.heavy_top"
        )
        self.assertEqual(heavy_top_claim["reproduction_status"], "intended")
        self.assertIn("exact_heavy_top_inertia_unknown", heavy_top_claim["conflict_note"])
        self.assertIn("exact_heavy_top_geometry_unknown", heavy_top_claim["conflict_note"])

        matrix = yaml.safe_load((ROOT / "configs/experiments/paper_experiment_matrix.yaml").read_text())
        matrix_entry = next(
            item for item in matrix["experiments"] if item["claim_id"] == "experiment.single_body.heavy_top"
        )
        self.assertEqual(matrix_entry["reproduction_status"], "planned")
        self.assertIn("exact_heavy_top_inertia_unknown", matrix_entry["blocking_reasons"])
        self.assertIn("exact_heavy_top_geometry_unknown", matrix_entry["blocking_reasons"])

        text = (ROOT / "docs/reference/claim-boundaries.md").read_text()
        current = claim_boundary_bullet(text, "This repository contains Phase 49")
        verified = claim_boundary_bullet(text, "Phase 49 verifies")
        non_claim = claim_boundary_bullet(text, "Phase 49 does not verify")
        forbidden = claim_boundary_bullet(text, "Phase 49 heavy-top RK4 reference")

        self.assertIn("heavy-top RK4 reference diagnostic lane", current)
        self.assertIn("rbd_rk4_reference", verified)
        self.assertIn("source-backed", verified)
        self.assertIn("raw_heavy_top_reference_curve_data_missing", verified)
        self.assertIn("heavy_top_timing_evidence_missing", verified)
        self.assertIn("passed heavy-top experiment", non_claim)
        self.assertIn("paper-faithful heavy-top inertia", non_claim)
        self.assertIn("M-ABD heavy-top dynamics", non_claim)
        self.assertIn("not a passed heavy-top experiment", forbidden)
        self.assertIn("any passed `experiment.*` claim", forbidden)

    def test_phase49_record_has_required_evidence_fields(self) -> None:
        text = (ROOT / "docs/records/2026-05-18-phase49-heavy-top-rk4-reference.md").read_text()

        for snippet in (
            "## Status\n\npassed_for_heavy_top_reference_diagnostic_lane",
            "## Repository",
            "phase49-heavy-top-reference",
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
        ):
            self.assertIn(snippet, text)
        self.assertNotIn("TO_BE_BACKFILLED_PHASE49", text)
        self.assertNotIn("phase49-working-tree", text)

    def test_phase50_heavy_top_mabd_newton_lane_is_bounded(self) -> None:
        data = yaml.safe_load((ROOT / "docs/reference/paper-claims.yaml").read_text())
        heavy_top_claim = next(
            claim for claim in data["claims"] if claim["claim_id"] == "experiment.single_body.heavy_top"
        )
        self.assertEqual(heavy_top_claim["reproduction_status"], "intended")
        self.assertIn("mabd_newton_report_incomplete", heavy_top_claim["conflict_note"])
        self.assertNotIn("mabd_newton_report_missing", heavy_top_claim["conflict_note"])

        matrix = yaml.safe_load((ROOT / "configs/experiments/paper_experiment_matrix.yaml").read_text())
        matrix_entry = next(
            item for item in matrix["experiments"] if item["claim_id"] == "experiment.single_body.heavy_top"
        )
        self.assertEqual(matrix_entry["reproduction_status"], "planned")
        self.assertIn("mabd_newton_report_incomplete", matrix_entry["blocking_reasons"])
        self.assertNotIn("mabd_newton_report_missing", matrix_entry["blocking_reasons"])

        text = (ROOT / "docs/reference/claim-boundaries.md").read_text()
        current = claim_boundary_bullet(text, "This repository contains Phase 50")
        verified = claim_boundary_bullet(text, "Phase 50 verifies")
        non_claim = claim_boundary_bullet(text, "Phase 50 does not verify")
        forbidden = claim_boundary_bullet(text, "Phase 50 heavy-top MABD Newton lane")

        self.assertIn("heavy-top `mabd_newton` diagnostic lane", current)
        self.assertIn("model-derived `SolverMABD.step()`", verified)
        self.assertIn("`mabd:body`", verified)
        self.assertIn("`mabd:world_constraint`", verified)
        self.assertIn("`mabd:gravity`", verified)
        self.assertIn("paper-faithful heavy-top inertia", non_claim)
        self.assertIn("ABD-vs-RBD comparison", non_claim)
        self.assertIn("not a passed heavy-top experiment", forbidden)
        self.assertIn("any passed `experiment.*` claim", forbidden)

    def test_phase50_record_has_required_evidence_fields(self) -> None:
        text = (ROOT / "docs/records/2026-05-18-phase50-heavy-top-mabd-newton-lane.md").read_text()

        for snippet in (
            "## Status\n\npassed_for_heavy_top_mabd_newton_diagnostic_lane",
            "phase50-heavy-top-mabd-lane",
            "reports/experiment_matrix/single_body_heavy_top_mabd_newton.json",
            "mabd_cpu_oracle_heavy_top_newton_lane",
            "mabd_newton",
            "newton_model_derived",
            "mabd_newton_report_incomplete",
            "exact_heavy_top_inertia_unknown",
            "exact_heavy_top_geometry_unknown",
            "heavy_top_comparison_report_incomplete",
            "No `experiment.*` claim is passed.",
            "`experiment.single_body.heavy_top` remains intended",
            "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_heavy_top_mabd tests.test_experiment_run_configs tests.test_experiment_runner tests.test_phase0_bootstrap",
            "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py",
            "git diff --check",
        ):
            self.assertIn(snippet, text)
        self.assertNotIn("TO_BE_BACKFILLED_PHASE50", text)
        self.assertNotIn("phase50-working-tree", text)

    def test_phase51_heavy_top_comparison_protocol_is_bounded(self) -> None:
        data = yaml.safe_load((ROOT / "docs/reference/paper-claims.yaml").read_text())
        heavy_top_claim = next(
            claim for claim in data["claims"] if claim["claim_id"] == "experiment.single_body.heavy_top"
        )
        self.assertEqual(heavy_top_claim["reproduction_status"], "intended")
        self.assertIn("heavy_top_comparison_report_incomplete", heavy_top_claim["conflict_note"])
        self.assertNotIn("heavy_top_comparison_report_missing", heavy_top_claim["conflict_note"])

        matrix = yaml.safe_load((ROOT / "configs/experiments/paper_experiment_matrix.yaml").read_text())
        matrix_entry = next(
            item for item in matrix["experiments"] if item["claim_id"] == "experiment.single_body.heavy_top"
        )
        self.assertEqual(matrix_entry["reproduction_status"], "planned")
        self.assertIn("heavy_top_comparison_report_incomplete", matrix_entry["blocking_reasons"])
        self.assertNotIn("heavy_top_comparison_report_missing", matrix_entry["blocking_reasons"])

        text = (ROOT / "docs/reference/claim-boundaries.md").read_text()
        current = claim_boundary_bullet(text, "This repository contains Phase 51")
        verified = claim_boundary_bullet(text, "Phase 51 verifies")
        non_claim = claim_boundary_bullet(text, "Phase 51 does not verify")
        forbidden = claim_boundary_bullet(text, "Phase 51 heavy-top comparison protocol")

        self.assertIn("heavy-top comparison protocol evidence", current)
        self.assertIn("heavy_top_comparison_protocol", verified)
        self.assertIn("input report provenance", verified)
        self.assertIn("sample time-grid mismatch", verified)
        self.assertIn("passed heavy-top experiment", non_claim)
        self.assertIn("comparison pass gate", non_claim)
        self.assertIn("not a passed heavy-top experiment", forbidden)
        self.assertIn("any passed `experiment.*` claim", forbidden)

    def test_phase51_record_has_required_evidence_fields(self) -> None:
        text = (
            ROOT / "docs/records/2026-05-18-phase51-heavy-top-comparison-protocol.md"
        ).read_text()

        for snippet in (
            "## Status\n\npassed_for_heavy_top_comparison_protocol",
            "phase51-heavy-top-comparison-protocol",
            "reports/experiment_matrix/single_body_heavy_top_comparison.json",
            "522d0dbea2eacbe1f334400dbcba4bd885ba26cecd50d239463048f7e24ec8de",
            "heavy_top_multilane_comparison_development",
            "heavy_top_comparison_protocol",
            "report_protocol",
            "mabd_newton_report_incomplete",
            "heavy_top_comparison_report_incomplete",
            "sample_time_grid_mismatch",
            "nutation_angle_error:paper_reference_curve_missing",
            "MABD precession velocity status: `diagnostic_available`",
            "MABD energy drift status: `diagnostic_available`",
            "No `experiment.*` claim is passed.",
            "`experiment.single_body.heavy_top` remains intended",
            "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_run_configs tests.test_heavy_top_comparison_reports tests.test_experiment_runner",
            "PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py",
            "git diff --check",
        ):
            self.assertIn(snippet, text)
        self.assertNotIn("TO_BE_BACKFILLED_PHASE51", text)
        self.assertNotIn("phase51-working-tree", text)

    def test_phase53_heavy_top_figure_curve_digitization_is_bounded(self) -> None:
        figure_report = load_claim_report(
            ROOT / "reports/experiment_matrix/single_body_heavy_top_figure_curves.json"
        )
        comparison_report = load_claim_report(
            ROOT / "reports/experiment_matrix/single_body_heavy_top_comparison.json"
        )

        self.assertEqual(figure_report.status, EvidenceStatus.INCOMPLETE)
        self.assertEqual(figure_report.baseline_lane, "paper_figure_digitization")
        self.assertEqual(figure_report.solver_mode, "heavy_top_paper_figure_digitization")
        self.assertEqual(figure_report.backend, "pdftocairo_pillow")
        self.assertFalse(figure_report.observed["full_experiment_claim_passed"])
        self.assertEqual(figure_report.observed["lane_status"], "reference_curves_digitized")
        self.assertTrue(figure_report.observed["reference_curve_available"])
        self.assertEqual(figure_report.observed["renderer_version"], "pdftocairo 22.02.0")
        self.assertEqual(figure_report.observed["rendered_size_px"], [3179, 1924])
        self.assertIn("not_authors_raw_data", figure_report.observed["limitations"])
        self.assertIn(
            "no_blue_orange_line_style_split",
            figure_report.observed["limitations"],
        )
        self.assertEqual(
            comparison_report.observed["paper_metric_statuses"]["nutation_angle_error"]["status"],
            "paper_figure_digitized_reference_available",
        )
        self.assertEqual(
            comparison_report.observed["missing_paper_metrics"],
            ["nutation_angle_error:paper_figure_digitized_curve_agreement_not_passed"],
        )
        self.assertIn(
            "raw_heavy_top_reference_curve_data_missing",
            comparison_report.observed["blocking_reasons"],
        )
        self.assertIn(
            "heavy_top_digitized_figure_curve_agreement_not_passed",
            comparison_report.observed["blocking_reasons"],
        )
        self.assertIn(
            "paper_figure_curves",
            comparison_report.observed["input_report_provenance"],
        )

        claims = yaml.safe_load((ROOT / "docs/reference/paper-claims.yaml").read_text())
        heavy_top_claim = next(
            claim for claim in claims["claims"] if claim["claim_id"] == "experiment.single_body.heavy_top"
        )
        self.assertEqual(heavy_top_claim["reproduction_status"], "intended")
        self.assertIn(
            "raw_heavy_top_reference_curve_data_missing",
            heavy_top_claim["conflict_note"],
        )

        boundary_text = (ROOT / "docs/reference/claim-boundaries.md").read_text()
        current = claim_boundary_bullet(boundary_text, "This repository contains Phase 53")
        verified = claim_boundary_bullet(boundary_text, "Phase 53 verifies")
        non_claim = claim_boundary_bullet(boundary_text, "Phase 53 does not verify")
        self.assertIn("heavy-top paper-figure digitization evidence", current)
        self.assertIn("digitized paper-figure reference-family samples", verified)
        self.assertIn("raw author curve data remains unavailable", verified)
        self.assertIn("passed heavy-top experiment", non_claim)
        self.assertIn("authors' raw simulation data", non_claim)
        self.assertIn("blue/orange solid and dashed paper curves", non_claim)

        record_text = (
            ROOT / "docs/records/2026-05-18-phase53-heavy-top-figure-curves.md"
        ).read_text()
        for snippet in (
            "## Status\n\npassed_for_heavy_top_figure_curve_digitization_lane",
            "reports/experiment_matrix/single_body_heavy_top_figure_curves.json",
            "pdftocairo 22.02.0",
            "3179 x 1924",
            "not_authors_raw_data",
            "paper_figure_digitized_reference_available",
            "raw_heavy_top_reference_curve_data_missing",
            "No `experiment.*` claim is passed.",
            "`experiment.single_body.heavy_top` remains intended",
        ):
            self.assertIn(snippet, record_text)
        self.assertNotIn("TO_BE_BACKFILLED_PHASE53", record_text)

    def test_phase44_solver_model_config_is_bounded(self) -> None:
        text = (ROOT / "docs/reference/claim-boundaries.md").read_text()
        current = claim_boundary_bullet(text, "This repository contains Phase 44")
        verified = claim_boundary_bullet(text, "Phase 44 verifies")
        non_claim = claim_boundary_bullet(text, "Phase 44 does not verify")
        forbidden = claim_boundary_bullet(text, "Phase 44 model-derived SolverMABD CPU config")

        self.assertIn("SolverMABD model-derived CPU body-config integration", current)
        self.assertIn("model-derived `SolverMABD.step()`", verified)
        self.assertIn("registered `mabd:body` rows", verified)
        self.assertIn("`mabd:rest_point0`", verified)
        self.assertIn("model `mabd:control` rows", verified)
        self.assertIn("manual `configure_cpu_oracle(...)`", verified)
        self.assertIn("`notify_model_changed()`", verified)
        self.assertIn("model-derived `mabd:constraint` rows", non_claim)
        self.assertIn("Newton `Control` input", non_claim)
        self.assertIn("GPU/Warp kernels", non_claim)
        self.assertIn("any passed `experiment.*` claim", non_claim)
        self.assertIn("not a passed paper experiment", forbidden)
        self.assertIn("not a model-derived joint/constraint implementation", forbidden)
        self.assertIn("not a GPU/Warp solver", forbidden)

    def test_phase44_record_has_required_evidence_fields(self) -> None:
        text = (ROOT / "docs/records/2026-05-18-phase44-solver-model-config.md").read_text()

        for snippet in (
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
        ):
            self.assertIn(snippet, text)
        self.assertNotIn("TO_BE_BACKFILLED_PHASE44", text)
        self.assertNotIn("phase44-working-tree", text)

    def test_phase45_solver_model_constraint_config_is_bounded(self) -> None:
        text = (ROOT / "docs/reference/claim-boundaries.md").read_text()
        current = claim_boundary_bullet(text, "This repository contains Phase 45")
        verified = claim_boundary_bullet(text, "Phase 45 verifies")
        non_claim = claim_boundary_bullet(text, "Phase 45 does not verify")
        forbidden = claim_boundary_bullet(text, "Phase 45 model-derived SolverMABD joint constraints")

        self.assertIn("SolverMABD model-derived CPU joint-constraint config integration", current)
        self.assertIn("model-derived `mabd:constraint` rows", verified)
        self.assertIn("`MABDCPUOracleConstraint`", verified)
        self.assertIn("ball, hinge, and universal", verified)
        self.assertIn("`mabd:cp_index`", verified)
        self.assertIn("manual `configure_cpu_oracle(...)`", verified)
        self.assertIn("model-derived world constraints", non_claim)
        self.assertIn("Newton `Contacts`", non_claim)
        self.assertIn("Newton `Control` input", non_claim)
        self.assertIn("GPU/Warp kernels", non_claim)
        self.assertIn("paper timing", non_claim)
        self.assertIn("comparative baselines", non_claim)
        self.assertIn("rendered output", non_claim)
        self.assertIn("raw simulation", non_claim)
        self.assertIn("full paper reproduction", non_claim)
        self.assertIn("any passed `experiment.*` claim", non_claim)
        self.assertIn("not a passed paper experiment", forbidden)
        self.assertIn("not a contact implementation", forbidden)
        self.assertIn("not a GPU/Warp solver", forbidden)

    def test_phase45_record_has_required_evidence_fields(self) -> None:
        text = (ROOT / "docs/records/2026-05-18-phase45-model-constraint-config.md").read_text()

        for snippet in (
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
            "## Implementation Evidence",
            "model-derived `mabd:constraint` rows",
            "`MABDCPUOracleConstraint`",
            "`ball_joint(...)`",
            "`hinge_joint(...)`",
            "`universal_joint(...)`",
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
        ):
            self.assertIn(snippet, text)
        self.assertNotIn("TO_BE_BACKFILLED_PHASE45", text)
        self.assertNotIn("phase45-working-tree", text)

    def test_phase46_solver_model_world_constraint_config_is_bounded(self) -> None:
        text = (ROOT / "docs/reference/claim-boundaries.md").read_text()
        current = claim_boundary_bullet(text, "This repository contains Phase 46")
        verified = claim_boundary_bullet(text, "Phase 46 verifies")
        non_claim = claim_boundary_bullet(text, "Phase 46 does not verify")
        forbidden = claim_boundary_bullet(text, "Phase 46 model-derived SolverMABD world constraints")

        self.assertIn("SolverMABD model-derived CPU world-constraint config integration", current)
        self.assertIn("model-derived `mabd:world_constraint` rows", verified)
        self.assertIn("`MABDCPUOracleWorldConstraint`", verified)
        self.assertIn("`mabd:world_body`", verified)
        self.assertIn("`mabd:world_rest_point`", verified)
        self.assertIn("`mabd:world_point`", verified)
        self.assertIn("body-index validation", verified)
        self.assertIn("reaction-vector availability through `dlambda`", verified)
        self.assertIn("manual `configure_cpu_oracle(...)`", verified)
        self.assertIn("Newton `Contacts`", non_claim)
        self.assertIn("Newton `Control` input", non_claim)
        self.assertIn("GPU/Warp kernels", non_claim)
        self.assertIn("paper timing", non_claim)
        self.assertIn("comparative baselines", non_claim)
        self.assertIn("rendered output", non_claim)
        self.assertIn("raw simulation", non_claim)
        self.assertIn("full paper reproduction", non_claim)
        self.assertIn("any passed `experiment.*` claim", non_claim)
        self.assertIn("not a passed paper experiment", forbidden)
        self.assertIn("not a contact implementation", forbidden)
        self.assertIn("not a Newton `Control` input implementation", forbidden)
        self.assertIn("not a GPU/Warp solver", forbidden)

    def test_phase46_record_has_required_evidence_fields(self) -> None:
        text = (ROOT / "docs/records/2026-05-18-phase46-model-world-constraints.md").read_text()

        for snippet in (
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
        ):
            self.assertIn(snippet, text)
        self.assertNotIn("TO_BE_BACKFILLED_PHASE46", text)
        self.assertNotIn("phase46-working-tree", text)

    def test_phase46_spec_and_plan_have_world_constraint_guardrails(self) -> None:
        spec = (
            ROOT / "docs/superpowers/specs/2026-05-18-phase46-model-world-constraints-design.md"
        ).read_text()
        plan = (
            ROOT / "docs/superpowers/plans/2026-05-18-mabd-phase46-model-world-constraints.md"
        ).read_text()

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
            self.assertIn(snippet, spec)
        for snippet in (
            "Phase 46 Model World Constraints Implementation Plan",
            "Let `SolverMABD.step()` build CPU oracle world-anchor constraints",
            "`MABDCPUOracleWorldConstraint`",
            "manual `configure_cpu_oracle(...)` remains authoritative",
            "registered custom attribute",
            "claim impact saying no `experiment.*` claim is passed",
        ):
            self.assertIn(snippet, plan)
        for stale in (
            "Phase 45 Model Constraint Config Implementation Plan",
            "passed_for_solver_model_constraint_config_slice",
            "model-derived `mabd:constraint` rows are verified",
            "Phase 46 does not verify model-derived world constraints",
        ):
            self.assertNotIn(stale, spec)
            self.assertNotIn(stale, plan)

    def test_phase47_solver_model_gravity_config_is_bounded(self) -> None:
        text = (ROOT / "docs/reference/claim-boundaries.md").read_text()
        current = claim_boundary_bullet(text, "This repository contains Phase 47")
        verified = claim_boundary_bullet(text, "Phase 47 verifies")
        non_claim = claim_boundary_bullet(text, "Phase 47 does not verify")
        forbidden = claim_boundary_bullet(text, "Phase 47 model-derived SolverMABD gravity config")

        self.assertIn("SolverMABD model-derived CPU gravity-config integration", current)
        self.assertIn("model-derived `mabd:gravity` rows", verified)
        self.assertIn("`MABDCPUOracleConfig.gravity`", verified)
        self.assertIn("`mabd:gravity_enabled`", verified)
        self.assertIn("`mabd:gravity_vector`", verified)
        self.assertIn("disabled-row filtering", verified)
        self.assertIn("multiple-enabled-row validation", verified)
        self.assertIn("manual `configure_cpu_oracle(...)`", verified)
        self.assertIn("heavy-top reproduction", non_claim)
        self.assertIn("physical-pendulum scene reproduction", non_claim)
        self.assertIn("Newton `Contacts`", non_claim)
        self.assertIn("Newton `Control` input", non_claim)
        self.assertIn("GPU/Warp kernels", non_claim)
        self.assertIn("paper timing", non_claim)
        self.assertIn("comparative baselines", non_claim)
        self.assertIn("rendered output", non_claim)
        self.assertIn("raw simulation", non_claim)
        self.assertIn("full paper reproduction", non_claim)
        self.assertIn("any passed `experiment.*` claim", non_claim)
        self.assertIn("not a passed paper experiment", forbidden)
        self.assertIn("not a heavy-top reproduction", forbidden)
        self.assertIn("not a physical-pendulum scene reproduction", forbidden)
        self.assertIn("not a contact implementation", forbidden)
        self.assertIn("not a Newton `Control` input implementation", forbidden)
        self.assertIn("not a GPU/Warp solver", forbidden)

    def test_phase47_record_has_required_evidence_fields(self) -> None:
        text = (ROOT / "docs/records/2026-05-18-phase47-model-gravity-config.md").read_text()

        for snippet in (
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
        ):
            self.assertIn(snippet, text)
        self.assertNotIn("TO_BE_BACKFILLED_PHASE47", text)
        self.assertNotIn("phase47-working-tree", text)

    def test_phase47_spec_and_plan_have_gravity_guardrails(self) -> None:
        spec = (
            ROOT / "docs/superpowers/specs/2026-05-18-phase47-model-gravity-config-design.md"
        ).read_text()
        plan = (
            ROOT / "docs/superpowers/plans/2026-05-18-mabd-phase47-model-gravity-config.md"
        ).read_text()

        for snippet in (
            "Phase 47 Solver Model Gravity Config Design",
            "`mabd:gravity`",
            "`mabd:gravity_enabled`",
            "`mabd:gravity_vector`",
            "more than one enabled row is rejected",
            "This is still not a paper experiment pass",
            "Phase 47 does not implement heavy-top reproduction",
        ):
            self.assertIn(snippet, spec)
        for snippet in (
            "Phase 47 Model Gravity Config Implementation Plan",
            "Let `SolverMABD.step()` build `MABDCPUOracleConfig.gravity`",
            "`MABDCPUOracleConfig.gravity`",
            "manual `configure_cpu_oracle(...)` remains authoritative",
            "registered custom attribute",
            "No `experiment.*` claim is passed",
        ):
            self.assertIn(snippet, plan)
        for stale in (
            "Phase 46 Model World Constraints Implementation Plan",
            "passed_for_solver_model_world_constraint_config_slice",
            "model-derived `mabd:world_constraint` rows are verified",
            "Phase 47 does not verify model-derived gravity",
        ):
            self.assertNotIn(stale, spec)
            self.assertNotIn(stale, plan)

    def test_phase48_physical_pendulum_model_derived_lane_is_bounded(self) -> None:
        text = (ROOT / "docs/reference/claim-boundaries.md").read_text()
        current = claim_boundary_bullet(text, "This repository contains Phase 48")
        verified = claim_boundary_bullet(text, "Phase 48 verifies")
        non_claim = claim_boundary_bullet(text, "Phase 48 does not verify")
        forbidden = claim_boundary_bullet(text, "Phase 48 physical-pendulum model-derived")

        self.assertIn("physical-pendulum `mabd_newton`", current)
        self.assertIn("model-derived SolverMABD", current)
        self.assertIn("Newton model-derived `SolverMABD.step()`", verified)
        self.assertIn("`mabd:body`", verified)
        self.assertIn("`mabd:world_constraint`", verified)
        self.assertIn("`mabd:gravity`", verified)
        self.assertIn("solver_model_config_source = newton_model_derived", verified)
        self.assertIn("full_experiment_claim_passed = false", verified)
        self.assertIn("paper-faithful physical-pendulum geometry", non_claim)
        self.assertIn("physical-pendulum experiment pass", non_claim)
        self.assertIn("Newton `Contacts`", non_claim)
        self.assertIn("runtime Newton `Control`", non_claim)
        self.assertIn("GPU/Warp kernels", non_claim)
        self.assertIn("rendered output", non_claim)
        self.assertIn("paper timing", non_claim)
        self.assertIn("comparative pass gates", non_claim)
        self.assertIn("raw simulation logs", non_claim)
        self.assertIn("full paper reproduction", non_claim)
        self.assertIn("any passed `experiment.*` claim", non_claim)
        self.assertIn("not a passed physical-pendulum experiment", forbidden)
        self.assertIn("not paper-faithful pendulum geometry", forbidden)
        self.assertIn("not a contact implementation", forbidden)
        self.assertIn("not a runtime Newton `Control` implementation", forbidden)
        self.assertIn("not a GPU/Warp solver", forbidden)
        self.assertIn("not a comparative pass gate", forbidden)

    def test_phase48_record_has_required_evidence_fields(self) -> None:
        text = (
            ROOT / "docs/records/2026-05-18-phase48-physical-pendulum-model-lane.md"
        ).read_text()

        for snippet in (
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
            "96713fa965463b69c229a4d30582c733ff3526bb",
            "Local patch status: locally patched",
            "mabd:zero_stiffness_diagnostic",
            "zero stiffness requires explicit diagnostic opt-in",
            "young_modulus == 0.0",
            "Default `young_modulus == 0.0` without the diagnostic opt-in still raises",
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
            "ValueError: young_modulus must be positive",
            "AssertionError: ValueError not raised",
            "## GREEN Evidence",
            "Ran 38 tests",
            "test_solver_step_model_body_rejects_zero_young_modulus_without_diagnostic_opt_in",
            "test_solver_step_model_body_allows_zero_young_modulus_with_diagnostic_opt_in",
            "the formal physical-pendulum lane calls `SolverMABD.step()`",
            "## Report Artifacts",
            "single_body_physical_pendulum_mabd_newton.json",
            "single_body_physical_pendulum_comparison.json",
            "source_commit = 1280ac4",
            "## Claim Impact",
            "No `experiment.*` claim is passed",
            "Paper-faithful physical-pendulum geometry remains missing",
            "Zero stiffness remains an explicit diagnostic opt-in",
            "Newton `Contacts` remain unimplemented",
            "Runtime Newton `Control` remains unverified",
            "GPU/Warp kernels remain unverified",
        ):
            self.assertIn(snippet, text)
        self.assertNotIn("TO_BE_BACKFILLED_PHASE48", text)
        self.assertNotIn("phase48-working-tree", text)
        self.assertNotIn("PHASE48_EVIDENCE_RECORD_COMMIT_TO_PIN", text)

    def test_phase48_spec_and_plan_have_model_lane_guardrails(self) -> None:
        spec = (
            ROOT
            / "docs/superpowers/specs/2026-05-18-phase48-physical-pendulum-model-lane-design.md"
        ).read_text()
        plan = (
            ROOT
            / "docs/superpowers/plans/2026-05-18-mabd-phase48-physical-pendulum-model-lane.md"
        ).read_text()

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
            self.assertIn(snippet, spec)
        for snippet in (
            "Phase 48 Physical Pendulum Model-Derived Lane Implementation Plan",
            "Make the physical-pendulum `mabd_newton` report lane step through Newton model-derived `SolverMABD.step()`",
            "roll_out_physical_pendulum_mabd_model_derived",
            "solver_model_config_source",
            "newton_model_derived",
            "No `experiment.*` claim is passed",
        ):
            self.assertIn(snippet, plan)
        for stale in (
            "Phase 47 Model Gravity Config Implementation Plan",
            "passed_for_solver_model_gravity_config_slice",
            "Phase 48 does not verify model-derived physical pendulum",
        ):
            self.assertNotIn(stale, spec)
            self.assertNotIn(stale, plan)

    def test_phase48_mabd_newton_report_records_model_derived_solver_source(self) -> None:
        report = load_claim_report(
            ROOT / "reports/experiment_matrix/single_body_physical_pendulum_mabd_newton.json"
        )

        self.assertEqual(report.source_commit, "1280ac4")
        self.assertEqual(report.status.value, "incomplete")
        self.assertEqual(report.observed["solver_model_config_source"], "newton_model_derived")
        self.assertEqual(report.expected["solver_model_config_source"], "newton_model_derived")
        self.assertEqual(
            report.observed["newton_model_derived_custom_frequencies"],
            ["mabd:body", "mabd:world_constraint", "mabd:gravity"],
        )
        self.assertFalse(report.observed["full_experiment_claim_passed"])
        self.assertEqual(report.observed["blocking_reasons"], ["pendulum_geometry_unknown"])

    def test_vendored_newton_import_resolves_inside_repo(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "import newton; print(newton.__file__)",
            ],
            cwd=ROOT,
            env={**os.environ, "PYTHONPATH": str(ROOT / "vendor/newton")},
            text=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.assertIn("vendor/newton/newton/__init__.py", result.stdout.replace("\\", "/"))

    def test_docs_validator_accepts_phase0_contract(self) -> None:
        result = subprocess.run(
            [sys.executable, "scripts/validate_docs.py"],
            cwd=ROOT,
            env={
                **os.environ,
                "PYTHONPATH": f"{ROOT / 'src'}:{ROOT / 'vendor/newton'}",
            },
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertIn(
            (
                "Phase 0/1/2/3/4/5/6/7/8/9/10/11/12/13/14/15/16/17/18/19/20/21/22/23/24/25/26/27/28/29/30/31/32/33/34/35/36/37/38/39/40/41/42/43/44/45/46/47/48/49/50/51/52/53/54/55/56/57/58/59/60/61/62/63/64/65/66/67/68/69/70/71/72/73/74"
                "/75/76 docs/provenance validation passed"
            ),
            result.stdout,
        )


if __name__ == "__main__":
    unittest.main()
