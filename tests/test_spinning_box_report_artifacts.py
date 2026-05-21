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
    "model_plane_constraint": ROOT
    / "reports/experiment_matrix/single_body_spinning_box_model_plane_constraint.json",
    "contacts_input": ROOT
    / "reports/experiment_matrix/single_body_spinning_box_contacts_input.json",
    "affine_static_plane_contacts": ROOT
    / "reports/experiment_matrix/single_body_spinning_box_affine_static_plane_contacts.json",
    "development_comparison": ROOT
    / "reports/experiment_matrix/single_body_spinning_box_development_comparison.json",
    "affine_static_plane_contacts_rollout_candidate": ROOT
    / "reports/experiment_matrix/"
    "single_body_spinning_box_affine_static_plane_contacts_rollout_candidate.json",
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
        self.assertIn("spinning_box_contact_response_missing", blockers)
        self.assertEqual(
            paper_horizon.observed["contact_diagnostic_policy"],
            "evaluated_from_current_mabd_states_not_applied_to_step",
        )
        self.assertEqual(
            paper_horizon.observed["contact_diagnostic_status"],
            "contact_penetration_observed_without_response",
        )
        self.assertGreaterEqual(paper_horizon.observed["max_contact_active_count"], 4)
        self.assertGreater(paper_horizon.observed["max_contact_penetration_m"], 0.0)
        self.assertGreater(paper_horizon.observed["max_contact_normal_force_n"], 0.0)
        for result in paper_horizon.observed["paper_horizon_results"]:
            self.assertEqual(
                result["contact_diagnostic_policy"],
                "evaluated_from_current_mabd_states_not_applied_to_step",
            )
            self.assertGreaterEqual(result["max_contact_active_count"], 4)
            self.assertGreater(result["max_contact_penetration_m"], 0.0)
            self.assertGreater(result["max_contact_normal_force_n"], 0.0)
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

    def test_model_plane_constraint_report_records_solver_model_lane_only(self) -> None:
        report = self._load_reports()["model_plane_constraint"]

        self.assertEqual(report.baseline_lane, "mabd_newton")
        self.assertEqual(report.solver_mode, "solver_mabd_model_plane_constraint_diagnostic")
        self.assertEqual(report.backend, "cpu_numpy_newton_solver_mabd_model_rows")
        self.assertIn("diagnostic extraction path", report.failure_reason)
        observed = report.observed
        self.assertEqual(
            observed["model_plane_constraint_policy"],
            "solver_mabd_model_rows_free_predict_then_active_plane_constraints",
        )
        self.assertEqual(
            observed["model_plane_constraint_scope"],
            "diagnostic_only_no_lane_gate",
        )
        self.assertEqual(
            observed["model_plane_constraint_config_source"],
            "mabd:plane_constraint_custom_rows",
        )
        self.assertEqual(
            observed["contact_constraint_policy"],
            "free_predict_then_active_point_plane_normal_constraints",
        )
        self.assertEqual(observed["rank_filter_policy"], "increment_map_row_rank_filter")
        self.assertNotIn("lane_gate_status", observed)
        self.assertTrue(observed["model_plane_constraint_reduced_free_predicted_penetration"])
        self.assertGreater(
            _finite_scalar(observed["max_free_predicted_contact_penetration_m"]),
            _finite_scalar(observed["max_constrained_contact_penetration_m"]),
        )
        self.assertEqual(observed["max_requested_plane_constraint_count"], 4)
        self.assertEqual(observed["max_accepted_plane_constraint_count"], 3)
        self.assertEqual(observed["max_skipped_plane_constraint_count"], 1)
        self.assertLess(
            _finite_scalar(observed["max_model_plane_constraint_residual_norm"]),
            1.0e-12,
        )
        self.assertEqual(len(observed["model_plane_constraint_results"]), 2)
        for result in observed["model_plane_constraint_results"]:
            self.assertNotEqual(
                result["contact_diagnostic_status"],
                "contact_penetration_observed_without_response",
            )
        blockers = observed["blocking_reasons"]
        self.assertIn("mabd_newton_report_incomplete", blockers)
        self.assertIn("mabd_paper_horizon_diagnostic_thresholds_violated", blockers)
        self.assertIn("spinning_box_model_plane_constraint_not_paper_faithful", blockers)
        self.assertIn("spinning_box_comparison_pass_gate_not_enabled", blockers)
        self.assertIn("mabd_kinematic_feasibility_blocker_recorded", blockers)
        self.assertEqual(report.raw_outputs["time_series"], "compact_samples_only")

    def test_contacts_input_report_records_newton_contacts_lane_only(self) -> None:
        report = self._load_reports()["contacts_input"]

        self.assertEqual(report.baseline_lane, "mabd_newton")
        self.assertEqual(report.solver_mode, "solver_mabd_contacts_input_diagnostic")
        self.assertEqual(
            report.backend,
            "cpu_numpy_newton_solver_mabd_contacts_input_diagnostic",
        )
        self.assertIn("Contacts input rows are a diagnostic path", report.failure_reason)
        observed = report.observed
        self.assertEqual(
            observed["contacts_input_policy"],
            "solver_mabd_contacts_input_free_predict_then_static_plane_constraints",
        )
        self.assertEqual(
            observed["contacts_input_scope"],
            "diagnostic_only_static_geometry_plane_constraints_no_lane_gate",
        )
        self.assertEqual(
            observed["contacts_input_source"],
            "newton.Contacts.rigid_contact_static_plane_rows_from_diagnostic_corners",
        )
        self.assertEqual(observed["contacts_input_summary_source"], "last_contacts_input_summary")
        self.assertEqual(
            observed["contact_constraint_policy"],
            "free_predict_then_active_point_plane_normal_constraints",
        )
        self.assertEqual(observed["rank_filter_policy"], "increment_map_row_rank_filter")
        self.assertNotIn("lane_gate_status", observed)
        self.assertTrue(observed["contacts_input_reduced_free_predicted_penetration"])
        self.assertGreater(
            _finite_scalar(observed["max_free_predicted_contact_penetration_m"]),
            _finite_scalar(observed["max_constrained_contact_penetration_m"]),
        )
        self.assertEqual(observed["max_contacts_input_rigid_contact_count"], 4)
        self.assertEqual(observed["max_contacts_input_rows_read"], 4.0)
        self.assertEqual(observed["max_contacts_input_generated_plane_constraint_count"], 4)
        self.assertEqual(observed["max_contacts_input_skipped_contact_count"], 0)
        self.assertEqual(observed["max_contacts_input_overflow_count"], 0)
        self.assertLess(
            _finite_scalar(observed["max_contacts_input_constraint_residual_norm"]),
            1.0e-12,
        )
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
        self.assertIn("mabd_newton_report_incomplete", blockers)
        self.assertIn("mabd_paper_horizon_diagnostic_thresholds_violated", blockers)
        self.assertIn("spinning_box_contacts_input_not_paper_faithful", blockers)
        self.assertIn("collision_detection_not_enabled_for_contacts_input", blockers)
        self.assertIn("spinning_box_comparison_pass_gate_not_enabled", blockers)
        self.assertIn("mabd_kinematic_feasibility_blocker_recorded", blockers)
        self.assertEqual(report.raw_outputs["time_series"], "compact_samples_only")

    def test_affine_static_plane_contacts_report_records_solver_generated_active_set_only(
        self,
    ) -> None:
        report = self._load_reports()["affine_static_plane_contacts"]

        self.assertEqual(report.baseline_lane, "mabd_newton")
        self.assertEqual(
            report.solver_mode,
            "solver_mabd_affine_static_plane_contacts_diagnostic",
        )
        self.assertEqual(
            report.backend,
            "cpu_numpy_newton_solver_mabd_affine_static_plane_contacts_diagnostic",
        )
        self.assertIn("bounded diagnostic active-set path", report.failure_reason)
        observed = report.observed
        self.assertEqual(
            observed["affine_static_plane_contact_policy"],
            "solver_mabd_detect_affine_box_static_plane_contacts",
        )
        self.assertEqual(
            observed["affine_static_plane_contact_source"],
            "SolverMABD.detect_static_plane_contacts",
        )
        self.assertEqual(
            observed["affine_static_plane_contact_scope"],
            "diagnostic_affine_box_corners_vs_static_infinite_planes_no_lane_gate",
        )
        self.assertEqual(observed["contacts_input_summary_source"], "last_contacts_input_summary")
        self.assertNotIn("lane_gate_status", observed)
        self.assertTrue(observed["affine_static_plane_contacts_reduced_free_predicted_penetration"])
        self.assertGreater(
            _finite_scalar(observed["max_free_predicted_contact_penetration_m"]),
            _finite_scalar(observed["max_constrained_contact_penetration_m"]),
        )
        self.assertEqual(observed["max_affine_static_plane_box_shape_count"], 1)
        self.assertEqual(observed["max_affine_static_plane_static_plane_shape_count"], 1)
        self.assertEqual(observed["max_affine_static_plane_candidate_contact_count"], 4)
        self.assertEqual(observed["max_affine_static_plane_rows_written"], 4)
        self.assertEqual(observed["max_affine_static_plane_skipped_shape_pair_count"], 0)
        self.assertEqual(observed["max_contacts_input_generated_plane_constraint_count"], 4)
        self.assertEqual(observed["max_contacts_input_overflow_count"], 0)
        self.assertLess(
            _finite_scalar(observed["max_contacts_input_constraint_residual_norm"]),
            1.0e-12,
        )
        self.assertEqual(len(observed["affine_static_plane_contacts_results"]), 2)
        for result in observed["affine_static_plane_contacts_results"]:
            self.assertEqual(
                result["affine_static_plane_contact_source"],
                "SolverMABD.detect_static_plane_contacts",
            )
            self.assertEqual(result["contacts_input_summary_source"], "last_contacts_input_summary")
            self.assertGreaterEqual(result["affine_static_plane_candidate_contact_count"], 0)
            self.assertGreaterEqual(result["contacts_input_generated_plane_constraint_count"], 0)
            self.assertEqual(result["contacts_input_overflow_count"], 0)
            self.assertTrue(math.isfinite(result["max_contacts_input_constraint_residual_norm"]))
        blockers = observed["blocking_reasons"]
        self.assertIn("mabd_newton_report_incomplete", blockers)
        self.assertIn("mabd_paper_horizon_diagnostic_thresholds_violated", blockers)
        self.assertIn("spinning_box_affine_static_plane_contacts_not_paper_faithful", blockers)
        self.assertIn("spinning_box_comparison_pass_gate_not_enabled", blockers)
        self.assertIn("mabd_kinematic_feasibility_blocker_recorded", blockers)
        self.assertNotIn("collision_detection_not_enabled_for_contacts_input", blockers)
        self.assertEqual(report.raw_outputs["time_series"], "compact_samples_only")

    def test_development_comparison_report_records_10s_newton_mabd_rbd_internal_comparison(
        self,
    ) -> None:
        report = self._load_reports()["development_comparison"]

        self.assertEqual(report.baseline_lane, "spinning_box_development_comparison")
        self.assertEqual(
            report.solver_mode,
            "spinning_box_newton_mabd_rbd_development_comparison",
        )
        self.assertEqual(report.backend, "cpu_newton_warp")
        self.assertFalse(report.observed["paper_faithful"])
        self.assertFalse(report.observed["full_experiment_claim_passed"])
        self.assertEqual(report.observed["comparison_scope"], "development_only")
        self.assertEqual(
            report.observed["comparison_status"],
            "development_comparison_recorded",
        )
        self.assertEqual(report.observed["duration_s"], 10.0)
        self.assertEqual(report.observed["time_step_s"], 0.01)
        self.assertEqual(report.observed["step_count"], 1000)
        self.assertEqual(report.observed["sample_count"], 101)
        self.assertEqual(
            report.observed["mabd_solver_name"],
            "newton.solvers.SolverMABD",
        )
        self.assertEqual(
            report.observed["rbd_solver_name"],
            "newton.solvers.SolverSemiImplicit",
        )
        self.assertEqual(len(report.observed["trajectory_samples"]["mabd"]), 101)
        self.assertEqual(len(report.observed["trajectory_samples"]["rbd"]), 101)
        self.assertEqual(len(report.observed["energy_curve_samples"]), 101)
        self.assertEqual(report.observed["energy_curve_samples"][-1]["time_s"], 10.0)
        for metric in (
            "final_position_delta_m",
            "max_position_delta_m",
            "final_energy_delta_j",
            "max_energy_delta_j",
            "final_linear_momentum_delta_norm",
            "max_linear_momentum_delta_norm",
            "final_angular_momentum_delta_norm",
            "max_angular_momentum_delta_norm",
        ):
            _finite_scalar(report.observed["comparison_metrics"][metric])
        self.assertIn(
            "development_comparison_only",
            report.observed["blocking_reasons"],
        )
        self.assertNotIn("lane_gate_status", report.observed)
        self.assertEqual(report.raw_outputs["trajectory"], "embedded_compact_samples")
        self.assertEqual(report.raw_outputs["energy_curve"], "embedded_energy_curve_samples")
        self.assertEqual(report.plot_paths, {})

    def test_affine_static_plane_contacts_rollout_candidate_report_records_10s_persistent_contacts(
        self,
    ) -> None:
        report = self._load_reports()["affine_static_plane_contacts_rollout_candidate"]

        self.assertEqual(
            report.baseline_lane,
            "spinning_box_affine_static_plane_contacts_rollout_candidate",
        )
        self.assertEqual(
            report.solver_mode,
            "solver_mabd_affine_static_plane_contacts_rollout_candidate",
        )
        self.assertEqual(
            report.backend,
            "cpu_newton_solver_mabd_affine_static_plane_contacts_rollout_candidate",
        )
        self.assertEqual(
            report.observed["candidate_status"],
            "affine_static_plane_contacts_rollout_candidate_recorded",
        )
        self.assertFalse(report.observed["paper_faithful"])
        self.assertFalse(report.observed["paper_comparable"])
        self.assertFalse(report.observed["full_experiment_claim_passed"])
        self.assertEqual(report.observed["rollout_scope"], "development_only")
        self.assertEqual(
            report.observed["contact_constraint_policy"],
            "free_predict_detect_static_plane_contacts_then_constrained_step",
        )
        self.assertEqual(
            report.observed["contact_detection_source"],
            "SolverMABD.detect_static_plane_contacts",
        )
        self.assertEqual(
            report.observed["solver_step_api"],
            "SolverMABD.step(..., contacts=...)",
        )
        self.assertEqual(report.observed["newton_contacts_api"], "newton.Contacts")
        self.assertEqual(report.observed["contact_constraint_mode"], "plane")
        self.assertEqual(report.observed["duration_s"], 10.0)
        self.assertEqual(report.observed["time_step_s"], 0.01)
        self.assertEqual(report.observed["step_count"], 1000)
        self.assertEqual(report.observed["sample_count"], 101)
        self.assertEqual(len(report.observed["trajectory_samples"]), 101)
        self.assertGreater(
            report.observed["max_free_predicted_contact_penetration_m"],
            report.observed["max_constrained_contact_penetration_m"],
        )
        self.assertEqual(report.observed["max_affine_static_plane_candidate_contact_count"], 4)
        self.assertEqual(
            report.observed["max_contacts_input_generated_plane_constraint_count"],
            4,
        )
        _finite_scalar(report.observed["max_constraint_residual_norm"])
        self.assertIn(
            "max_relative_total_energy_drift",
            report.observed["threshold_violations"],
        )
        self.assertIn(
            "spinning_box_affine_static_plane_contacts_rollout_candidate_not_paper_faithful",
            report.observed["blocking_reasons"],
        )
        self.assertIn(
            "paper_faithful_affine_collision_missing",
            report.observed["blocking_reasons"],
        )
        self.assertNotIn("lane_gate_status", report.observed)
        self.assertFalse(report.timing_distribution["paper_comparable"])
        self.assertEqual(
            report.timing_distribution["scope"],
            "local_cpu_wall_clock_not_paper_comparable",
        )
        self.assertEqual(report.raw_outputs["trajectory"], "embedded_compact_samples")
        self.assertEqual(report.plot_paths, {})

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
