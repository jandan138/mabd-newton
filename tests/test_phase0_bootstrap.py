from __future__ import annotations

import os
import subprocess
import sys
import unittest
from pathlib import Path

import yaml

from mabd_reproduction.reporting import EvidenceStatus, REQUIRED_REPORT_KEYS


ROOT = Path(__file__).resolve().parents[1]


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
                "Phase 0/1/2/3/4/5/6/7/8/9/10/11/12/13/14/15/16/17/18/19/20/21/22/23/24/25/26/27/28/29/30/31/32/33 "
                "docs/provenance validation passed"
            ),
            result.stdout,
        )


if __name__ == "__main__":
    unittest.main()
