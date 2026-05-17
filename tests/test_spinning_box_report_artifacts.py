from __future__ import annotations

import math
import unittest
from pathlib import Path

import yaml

from mabd_reproduction.reporting import EvidenceStatus, load_claim_report


ROOT = Path(__file__).resolve().parents[1]
VENDORED_NEWTON_COMMIT = "96713fa965463b69c229a4d30582c733ff3526bb"
PLACEHOLDER_SOURCE_COMMITS = {
    "",
    "unknown",
    "test-source",
    "working-tree",
    "pending branch-local",
    "<implementation-commit>",
    "phase42-working-tree",
    "TO_BE_BACKFILLED_PHASE42",
}
REPORTS = {
    "mabd": ROOT / "reports/experiment_matrix/single_body_spinning_box.json",
    "paper_horizon": ROOT
    / "reports/experiment_matrix/single_body_spinning_box_paper_horizon.json",
    "rbd": ROOT / "reports/experiment_matrix/single_body_spinning_box_rbd_baseline.json",
    "comparison": ROOT
    / "reports/experiment_matrix/single_body_spinning_box_comparison.json",
}


def _finite_scalar(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise AssertionError(f"value is not a scalar number: {value!r}")
    result = float(value)
    if not math.isfinite(result):
        raise AssertionError(f"value is not finite: {value!r}")
    return result


def _finite_vector3(value: object) -> list[float]:
    if not isinstance(value, list | tuple) or len(value) != 3:
        raise AssertionError(f"value is not a length-3 vector: {value!r}")
    return [_finite_scalar(component) for component in value]


class SpinningBoxReportArtifactTests(unittest.TestCase):
    def _load_reports(self):
        return {
            name: load_claim_report(path)
            for name, path in REPORTS.items()
        }

    def test_committed_spinning_box_reports_exist_and_share_identity(self) -> None:
        for name, path in REPORTS.items():
            with self.subTest(name=name):
                self.assertTrue(path.exists(), f"missing report artifact: {path}")

        reports = self._load_reports()
        for name, report in reports.items():
            with self.subTest(name=name):
                self.assertEqual(report.claim_id, "experiment.single_body.spinning_box")
                self.assertEqual(report.scene_id, "single_body_spinning_box")
                self.assertEqual(report.status, EvidenceStatus.INCOMPLETE)
                self.assertEqual(report.vendored_newton_commit, VENDORED_NEWTON_COMMIT)
                self.assertNotIn(report.source_commit, PLACEHOLDER_SOURCE_COMMITS)
                self.assertEqual(report.paper_source_version, "2603.08079v2")

    def test_mabd_diagnostic_report_remains_incomplete_with_required_metrics(self) -> None:
        mabd = self._load_reports()["mabd"]

        self.assertEqual(mabd.baseline_lane, "mabd_newton")
        self.assertEqual(mabd.solver_mode, "mabd_cpu_oracle_development")
        self.assertEqual(mabd.backend, "cpu_numpy")
        self.assertIn("mabd_newton lane pass", mabd.failure_reason)
        for metric in (
            "linear_momentum_error",
            "angular_momentum_error",
            "energy_drift",
            "relative_energy_drift",
            "generalized_momentum_delta_norm",
        ):
            _finite_scalar(mabd.observed[metric])
        for vector_metric in ("initial_position_m", "final_position_m"):
            _finite_vector3(mabd.observed[vector_metric])
        self.assertEqual(mabd.observed["mabd_rotation_mode"], "polar")
        self.assertEqual(mabd.observed["affine_shape_diagnostic_status"], "development_gap_observed")
        self.assertEqual(mabd.raw_outputs["time_series"], "not_written")

    def test_paper_horizon_report_records_diagnostic_blockers(self) -> None:
        paper_horizon = self._load_reports()["paper_horizon"]

        self.assertEqual(paper_horizon.baseline_lane, "mabd_newton")
        self.assertEqual(paper_horizon.solver_mode, "mabd_cpu_oracle_paper_horizon_diagnostic")
        self.assertEqual(paper_horizon.backend, "cpu_numpy")
        self.assertEqual(
            paper_horizon.observed["mabd_paper_horizon_status"],
            "development_gap_observed",
        )
        self.assertEqual(
            paper_horizon.observed["mabd_kinematic_feasibility_status"],
            "paper_momentum_requires_affine_stretch_under_q_delta_over_h",
        )
        self.assertNotIn("lane_gate_status", paper_horizon.observed)
        blockers = paper_horizon.observed["blocking_reasons"]
        self.assertIn("mabd_newton_report_incomplete", blockers)
        self.assertIn("mabd_paper_horizon_diagnostic_thresholds_violated", blockers)
        self.assertIn("mabd_kinematic_feasibility_blocker_recorded", blockers)
        for violation in (
            "max_abs_det_minus_one",
            "max_affine_orthogonality_error",
            "max_relative_kinetic_energy_drift",
            "max_relative_total_energy_drift",
            "max_singular_value",
        ):
            self.assertIn(violation, paper_horizon.observed["threshold_violations"])
        self.assertGreater(
            _finite_scalar(paper_horizon.observed["energy_drift"]),
            0.0,
        )
        self.assertEqual(paper_horizon.raw_outputs["time_series"], "compact_samples_only")

    def test_rbd_report_records_paper_faithful_lane_gate_only(self) -> None:
        rbd = self._load_reports()["rbd"]

        self.assertEqual(rbd.baseline_lane, "rbd_implicit_baseline")
        self.assertEqual(rbd.solver_mode, "paper_faithful_implicit_rbd")
        self.assertEqual(rbd.backend, "cpu_numpy_newton_only")
        self.assertEqual(rbd.observed["lane_gate_status"], "passed")
        self.assertIs(rbd.observed["lane_pass_gate"]["thresholds_met"], True)
        self.assertIs(rbd.observed["lane_pass_gate"]["full_experiment_claim_passed"], False)
        self.assertIn("mabd_newton lane", rbd.failure_reason)
        self.assertEqual(_finite_scalar(rbd.observed["linear_momentum_error"]), 0.0)
        self.assertEqual(_finite_scalar(rbd.observed["angular_momentum_error"]), 0.0)
        self.assertEqual(_finite_scalar(rbd.observed["energy_drift"]), 0.0)
        _finite_vector3(rbd.observed["initial_position_m"])
        _finite_vector3(rbd.observed["final_position_m"])

    def test_comparison_report_consumes_committed_lanes_without_claiming_pass(self) -> None:
        reports = self._load_reports()
        comparison = reports["comparison"]

        self.assertEqual(comparison.baseline_lane, "spinning_box_comparison_protocol")
        self.assertEqual(comparison.solver_mode, "spinning_box_multilane_comparison_development")
        self.assertEqual(comparison.backend, "report_protocol")
        self.assertEqual(comparison.observed["lane_statuses"]["mabd_newton"], "incomplete")
        self.assertEqual(
            comparison.observed["lane_gate_statuses"]["mabd_newton"],
            "incomplete",
        )
        self.assertEqual(
            comparison.observed["lane_gate_statuses"]["rbd_implicit_baseline"],
            "passed",
        )
        self.assertEqual(comparison.observed["missing_required_metrics"], [])
        self.assertEqual(comparison.observed["invalid_required_metrics"], [])
        self.assertEqual(comparison.observed["missing_required_vector_metrics"], [])
        self.assertEqual(comparison.observed["invalid_required_vector_metrics"], [])
        blockers = comparison.observed["blocking_reasons"]
        self.assertIn("mabd_newton_report_incomplete", blockers)
        self.assertIn("spinning_box_comparison_pass_gate_not_enabled", blockers)
        self.assertNotIn("rbd_implicit_baseline_report_incomplete", blockers)
        self.assertNotIn("rbd_implicit_baseline_not_paper_faithful", blockers)
        self.assertEqual(
            comparison.raw_outputs["mabd_report"],
            "reports/experiment_matrix/single_body_spinning_box.json",
        )
        self.assertEqual(
            comparison.raw_outputs["rbd_report"],
            "reports/experiment_matrix/single_body_spinning_box_rbd_baseline.json",
        )
        self.assertEqual(
            comparison.observed["lane_solver_modes"]["mabd_newton"],
            reports["mabd"].solver_mode,
        )
        self.assertEqual(
            comparison.observed["lane_solver_modes"]["rbd_implicit_baseline"],
            reports["rbd"].solver_mode,
        )
        for lane, report in (
            ("mabd_newton", reports["mabd"]),
            ("rbd_implicit_baseline", reports["rbd"]),
        ):
            for metric in ("linear_momentum_error", "angular_momentum_error", "energy_drift"):
                self.assertEqual(
                    comparison.observed["lane_metrics"][lane][metric],
                    report.observed[metric],
                )
            for metric in ("initial_position_m", "final_position_m"):
                self.assertEqual(
                    comparison.observed["lane_vector_metrics"][lane][metric],
                    report.observed[metric],
                )

    def test_matrix_retains_spinning_box_blocked_status(self) -> None:
        matrix = yaml.safe_load(
            (ROOT / "configs/experiments/paper_experiment_matrix.yaml").read_text()
        )
        spinning_box = next(
            item
            for item in matrix["experiments"]
            if item["claim_id"] == "experiment.single_body.spinning_box"
        )

        self.assertEqual(spinning_box["reproduction_status"], "blocked_by_baselines")
        self.assertIn("mabd_newton_report_incomplete", spinning_box["blocking_reasons"])
        self.assertIn(
            "spinning_box_comparison_report_incomplete",
            spinning_box["blocking_reasons"],
        )
        self.assertEqual(
            spinning_box["output_report"],
            "reports/experiment_matrix/single_body_spinning_box.json",
        )
        for claim in matrix["experiments"]:
            self.assertNotEqual(claim["reproduction_status"], "passed")


if __name__ == "__main__":
    unittest.main()
