from __future__ import annotations

import os
import subprocess
import sys
import unittest
from pathlib import Path

import yaml

from mabd_reproduction.reporting import EvidenceStatus, REQUIRED_REPORT_KEYS


ROOT = Path(__file__).resolve().parents[1]


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
        self.assertEqual(ball["reproduction_status"], "passed")
        self.assertEqual(universal["reproduction_status"], "passed")
        self.assertEqual(kkt["reproduction_status"], "passed")
        self.assertEqual(control["reproduction_status"], "passed")

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
            "## Metrics And Thresholds",
            "newton_semimplicit_rbd_cpu_development",
            "newton.solvers.SolverSemiImplicit",
            "Newton step count: `4`",
            "linear_momentum_error",
            "angular_momentum_error",
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
            "Phase 0/1/2/3/4/5/6/7/8/9/10/11/12/13/14/15 docs/provenance validation passed",
            result.stdout,
        )


if __name__ == "__main__":
    unittest.main()
