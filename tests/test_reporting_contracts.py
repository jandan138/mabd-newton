from __future__ import annotations

import unittest
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


if __name__ == "__main__":
    unittest.main()
