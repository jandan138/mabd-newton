from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from mabd_reproduction.reporting import EvidenceStatus, load_claim_report
from mabd_reproduction.single_body_reports import write_spinning_box_development_report


class SingleBodyReportLaneTests(unittest.TestCase):
    def test_spinning_box_development_report_is_machine_checkable(self) -> None:
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "single_body_spinning_box.json"
            report = write_spinning_box_development_report(
                path,
                source_commit="test-source",
                vendored_newton_commit="test-newton",
            )
            loaded = load_claim_report(path)

        self.assertEqual(report.claim_id, "experiment.single_body.spinning_box")
        self.assertEqual(loaded.status, EvidenceStatus.INCOMPLETE)
        self.assertEqual(loaded.baseline_lane, "mabd_newton")
        self.assertIn("rbd_implicit_baseline", loaded.failure_reason)
        self.assertEqual(loaded.observed["step_count"], 4)
        self.assertLessEqual(loaded.observed["energy_drift"], loaded.threshold["energy_drift"])
        self.assertLessEqual(
            loaded.observed["generalized_momentum_delta_norm"],
            loaded.threshold["generalized_momentum_delta_norm"],
        )

    def test_spinning_box_report_uses_run_config(self) -> None:
        from mabd_reproduction.experiment_configs import load_spinning_box_config

        root = Path(__file__).resolve().parents[1]
        config = load_spinning_box_config(root / "configs/experiments/single_body_spinning_box.yaml")
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "single_body_spinning_box.json"
            report = write_spinning_box_development_report(
                path,
                config=config,
                source_commit="test-source",
                vendored_newton_commit="test-newton",
            )
            loaded = load_claim_report(path)

        self.assertEqual(report.scene_id, config.scene_id)
        self.assertEqual(report.asset_hashes, {"primitive_cube": "not_applicable_procedural"})
        self.assertEqual(loaded.observed["step_count"], config.step_count)
        self.assertEqual(loaded.observed["time_step_s"], config.time_step_s)
        self.assertEqual(loaded.threshold, config.thresholds)
        self.assertEqual(loaded.status, config.report_status)
        self.assertEqual(loaded.failure_reason, config.failure_reason)


if __name__ == "__main__":
    unittest.main()
