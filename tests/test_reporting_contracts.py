from __future__ import annotations

import unittest
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory

from mabd_reproduction.reporting import (
    ClaimReport,
    EvidenceStatus,
    load_claim_report,
    validate_claim_report_mapping,
    write_claim_report,
)


def _report() -> ClaimReport:
    return ClaimReport(
        claim_id="experiment.single_body.spinning_box",
        scene_id="single_body_spinning_box",
        asset_hashes={"primitive_cube": "not_applicable_procedural"},
        solver_mode="mabd_cpu_oracle_development",
        backend="cpu_numpy",
        baseline_lane="mabd_newton",
        expected={"energy_drift_max": 1.0e-12},
        observed={"energy_drift": 0.0},
        threshold={"energy_drift": 1.0e-12},
        unit="json_report",
        status=EvidenceStatus.INCOMPLETE,
        failure_reason="full paper claim still requires rbd_implicit_baseline",
        timing_distribution={"step_count": 4},
        raw_outputs={"time_series": "not_written"},
        plot_paths={},
        source_commit="abc123",
        vendored_newton_commit="96713fa965463b69c229a4d30582c733ff3526bb",
        paper_source_version="2603.08079v2",
    )


def _lane_pass_gate(
    *,
    baseline_lane: str = "rbd_implicit_baseline",
    full_experiment_claim_passed: bool = False,
) -> dict[str, object]:
    return {
        "gate_version": "required_lane_v1",
        "claim_id": "experiment.single_body.spinning_box",
        "baseline_lane": baseline_lane,
        "solver_mode": "paper_faithful_implicit_rbd",
        "backend": "cpu_numpy_newton_only",
        "scope": "required_lane_only",
        "full_experiment_claim_passed": full_experiment_claim_passed,
    }


def _gated_rbd_lane_report(
    *,
    baseline_lane: str = "rbd_implicit_baseline",
    full_experiment_claim_passed: bool = False,
) -> ClaimReport:
    gate = _lane_pass_gate(
        baseline_lane=baseline_lane,
        full_experiment_claim_passed=full_experiment_claim_passed,
    )
    return replace(
        _report(),
        baseline_lane="rbd_implicit_baseline",
        solver_mode="paper_faithful_implicit_rbd",
        backend="cpu_numpy_newton_only",
        expected={"lane_pass_gate": gate},
        observed={
            "linear_momentum_error": 0.0,
            "angular_momentum_error": 0.0,
            "energy_drift": 0.0,
            "lane_gate_status": "passed",
            "lane_pass_gate": {**gate, "thresholds_met": True},
        },
        threshold={
            "linear_momentum_error": 1.0e-12,
            "angular_momentum_error": 1.0e-12,
            "energy_drift": 1.0e-12,
        },
        status=EvidenceStatus.INCOMPLETE,
        failure_reason="full paper claim still requires mabd_newton lane and comparison pass gate",
    )


class ReportingContractTests(unittest.TestCase):
    def test_claim_report_json_round_trips_required_fields(self) -> None:
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "report.json"
            write_claim_report(_report(), path)

            loaded = load_claim_report(path)

        self.assertEqual(loaded.claim_id, "experiment.single_body.spinning_box")
        self.assertEqual(loaded.status, EvidenceStatus.INCOMPLETE)
        self.assertEqual(loaded.asset_hashes["primitive_cube"], "not_applicable_procedural")
        self.assertEqual(loaded.timing_distribution["step_count"], 4)

    def test_report_validation_rejects_missing_full_schema_keys(self) -> None:
        mapping = _report().to_mapping()
        mapping.pop("asset_hashes")

        with self.assertRaisesRegex(ValueError, "asset_hashes"):
            validate_claim_report_mapping(mapping)

    def test_report_validation_rejects_unknown_status(self) -> None:
        mapping = _report().to_mapping()
        mapping["status"] = "almost_passed"

        with self.assertRaisesRegex(ValueError, "status"):
            validate_claim_report_mapping(mapping)

    def test_report_validation_rejects_passed_experiment_claims(self) -> None:
        mapping = _report().to_mapping()
        mapping["status"] = EvidenceStatus.PASSED.value

        with self.assertRaisesRegex(ValueError, "passed experiment"):
            validate_claim_report_mapping(mapping)

    def test_report_writer_rejects_passed_experiment_claims(self) -> None:
        report = replace(_report(), status=EvidenceStatus.PASSED)

        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "report.json"

            with self.assertRaisesRegex(ValueError, "passed experiment"):
                write_claim_report(report, path)
            self.assertFalse(path.exists())

    def test_report_writer_rejects_nonfinite_json_constants(self) -> None:
        report = replace(_report(), observed={"energy_drift": float("nan")})

        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "report.json"

            with self.assertRaisesRegex(ValueError, "JSON"):
                write_claim_report(report, path)
            self.assertFalse(path.exists())

    def test_report_validation_accepts_experiment_required_lane_gate(self) -> None:
        report = _gated_rbd_lane_report()

        loaded = validate_claim_report_mapping(report.to_mapping())

        self.assertEqual(loaded.status, EvidenceStatus.INCOMPLETE)
        self.assertEqual(loaded.baseline_lane, "rbd_implicit_baseline")
        self.assertEqual(loaded.observed["lane_gate_status"], "passed")
        self.assertFalse(loaded.observed["lane_pass_gate"]["full_experiment_claim_passed"])

    def test_report_writer_accepts_experiment_required_lane_gate(self) -> None:
        report = _gated_rbd_lane_report()

        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "rbd_lane_gate.json"
            write_claim_report(report, path)
            loaded = load_claim_report(path)

        self.assertEqual(loaded.status, EvidenceStatus.INCOMPLETE)
        self.assertEqual(loaded.observed["lane_gate_status"], "passed")
        self.assertEqual(loaded.solver_mode, "paper_faithful_implicit_rbd")

    def test_report_validation_still_rejects_passed_experiment_even_with_lane_gate(self) -> None:
        report = replace(_gated_rbd_lane_report(), status=EvidenceStatus.PASSED)

        with self.assertRaisesRegex(ValueError, "passed experiment"):
            validate_claim_report_mapping(report.to_mapping())

    def test_report_validation_rejects_lane_gate_claiming_full_experiment_pass(self) -> None:
        report = _gated_rbd_lane_report(full_experiment_claim_passed=True)

        with self.assertRaisesRegex(ValueError, "full_experiment_claim_passed"):
            validate_claim_report_mapping(report.to_mapping())

    def test_report_validation_rejects_passed_lane_gate_without_threshold_confirmation(self) -> None:
        report = _gated_rbd_lane_report()
        mapping = report.to_mapping()
        mapping["observed"]["lane_pass_gate"]["thresholds_met"] = False

        with self.assertRaisesRegex(ValueError, "thresholds_met"):
            validate_claim_report_mapping(mapping)

    def test_report_validation_rejects_lane_gate_not_bound_to_top_level_lane(self) -> None:
        report = _gated_rbd_lane_report(baseline_lane="mabd_newton")

        with self.assertRaisesRegex(ValueError, "baseline_lane"):
            validate_claim_report_mapping(report.to_mapping())

    def test_report_validation_rejects_lane_gate_for_unallowlisted_solver_mode(self) -> None:
        report = replace(
            _gated_rbd_lane_report(),
            solver_mode="newton_semimplicit_rbd_cpu_development",
        )

        with self.assertRaisesRegex(ValueError, "paper_faithful_implicit_rbd"):
            validate_claim_report_mapping(report.to_mapping())


if __name__ == "__main__":
    unittest.main()
