from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from mabd_reproduction.experiment_configs import load_spinning_box_config
from mabd_reproduction.reporting import EvidenceStatus, load_claim_report
from mabd_reproduction.rigid_baselines import write_spinning_box_rbd_baseline_report
from mabd_reproduction.single_body_reports import write_spinning_box_development_report


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs/experiments/single_body_spinning_box.yaml"


class SpinningBoxComparisonTests(unittest.TestCase):
    def _write_lane_reports(self, tmpdir: str) -> tuple[Path, Path]:
        config = load_spinning_box_config(CONFIG_PATH)
        mabd_path = Path(tmpdir) / "mabd.json"
        rbd_path = Path(tmpdir) / "rbd.json"
        write_spinning_box_development_report(
            mabd_path,
            config=config,
            source_commit="test-source",
            vendored_newton_commit="test-newton",
        )
        write_spinning_box_rbd_baseline_report(
            rbd_path,
            config=config,
            source_commit="test-source",
            vendored_newton_commit="test-newton",
        )
        return mabd_path, rbd_path

    def test_write_spinning_box_comparison_report_records_incomplete_protocol(self) -> None:
        from mabd_reproduction.comparison_reports import write_spinning_box_comparison_report

        config = load_spinning_box_config(CONFIG_PATH)
        with TemporaryDirectory() as tmpdir:
            mabd_path, rbd_path = self._write_lane_reports(tmpdir)
            output_path = Path(tmpdir) / "comparison.json"
            report = write_spinning_box_comparison_report(
                output_path,
                config=config,
                mabd_report_path=mabd_path,
                rbd_report_path=rbd_path,
                source_commit="test-source",
                vendored_newton_commit="test-newton",
            )
            loaded = load_claim_report(output_path)

        self.assertEqual(report.claim_id, "experiment.single_body.spinning_box")
        self.assertEqual(loaded.baseline_lane, "spinning_box_comparison_protocol")
        self.assertEqual(loaded.status, EvidenceStatus.INCOMPLETE)
        self.assertEqual(loaded.solver_mode, "spinning_box_multilane_comparison_development")
        self.assertEqual(loaded.backend, "report_protocol")
        self.assertEqual(loaded.observed["lane_statuses"]["mabd_newton"], "incomplete")
        self.assertEqual(loaded.observed["lane_statuses"]["rbd_implicit_baseline"], "incomplete")
        self.assertNotIn("mabd_newton:linear_momentum_error", loaded.observed["missing_required_metrics"])
        self.assertNotIn("mabd_newton:angular_momentum_error", loaded.observed["missing_required_metrics"])
        self.assertNotIn("mabd_newton:energy_drift", loaded.observed["missing_required_metrics"])
        self.assertLessEqual(
            loaded.observed["lane_metrics"]["mabd_newton"]["linear_momentum_error"],
            1.0e-9,
        )
        self.assertLessEqual(
            loaded.observed["lane_metrics"]["mabd_newton"]["angular_momentum_error"],
            1.0e-9,
        )
        self.assertIn("required lane reports remain incomplete", loaded.failure_reason)
        self.assertEqual(loaded.threshold["required_lane_status"], "passed")

    def test_spinning_box_comparison_rejects_wrong_lane_inputs(self) -> None:
        from mabd_reproduction.comparison_reports import write_spinning_box_comparison_report

        config = load_spinning_box_config(CONFIG_PATH)
        with TemporaryDirectory() as tmpdir:
            mabd_path, _rbd_path = self._write_lane_reports(tmpdir)
            output_path = Path(tmpdir) / "comparison.json"
            with self.assertRaisesRegex(ValueError, "rbd_implicit_baseline"):
                write_spinning_box_comparison_report(
                    output_path,
                    config=config,
                    mabd_report_path=mabd_path,
                    rbd_report_path=mabd_path,
                    source_commit="test-source",
                    vendored_newton_commit="test-newton",
                )
            self.assertFalse(output_path.exists())


if __name__ == "__main__":
    unittest.main()
