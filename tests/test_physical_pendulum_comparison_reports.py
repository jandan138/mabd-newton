from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from mabd_reproduction.experiment_configs import load_physical_pendulum_config
from mabd_reproduction.physical_pendulum_reports import (
    write_physical_pendulum_analytic_reference_report,
    write_physical_pendulum_mabd_development_report,
    write_physical_pendulum_rbd_baseline_report,
)
from mabd_reproduction.reporting import EvidenceStatus


ROOT = Path(__file__).resolve().parents[1]
PHYSICAL_PENDULUM_CONFIG_PATH = ROOT / "configs/experiments/single_body_physical_pendulum.yaml"


class PhysicalPendulumComparisonReportTests(unittest.TestCase):
    def _write_lane_reports(self, tmpdir: str) -> tuple[object, Path, Path, Path]:
        config = load_physical_pendulum_config(PHYSICAL_PENDULUM_CONFIG_PATH)
        root = Path(tmpdir)
        analytic_path = root / "analytic.json"
        mabd_path = root / "mabd.json"
        rbd_path = root / "rbd.json"
        write_physical_pendulum_analytic_reference_report(
            analytic_path,
            config=config,
            source_commit="test-source",
            vendored_newton_commit="test-newton",
        )
        write_physical_pendulum_mabd_development_report(
            mabd_path,
            config=config,
            source_commit="test-source",
            vendored_newton_commit="test-newton",
        )
        write_physical_pendulum_rbd_baseline_report(
            rbd_path,
            config=config,
            source_commit="test-source",
            vendored_newton_commit="test-newton",
        )
        return config, analytic_path, mabd_path, rbd_path

    def _write_comparison(
        self,
        *,
        output_path: Path,
        config: object,
        analytic_path: Path,
        mabd_path: Path,
        rbd_path: Path,
    ):
        from mabd_reproduction.comparison_reports import (
            write_physical_pendulum_comparison_report,
        )

        return write_physical_pendulum_comparison_report(
            output_path,
            config=config,
            analytic_report_path=analytic_path,
            mabd_report_path=mabd_path,
            rbd_report_path=rbd_path,
            source_commit="test-source",
            vendored_newton_commit="test-newton",
        )

    def _mutate_report(self, path: Path, *keys: str, value: object) -> None:
        payload = json.loads(path.read_text(encoding="utf-8"))
        target = payload
        for key in keys[:-1]:
            target = target[key]
        target[keys[-1]] = value
        path.write_text(json.dumps(payload), encoding="utf-8")

    def test_physical_pendulum_comparison_report_records_bounded_protocol(self) -> None:
        with TemporaryDirectory() as tmpdir:
            config, analytic_path, mabd_path, rbd_path = self._write_lane_reports(tmpdir)
            output_path = Path(tmpdir) / "comparison.json"
            report = self._write_comparison(
                output_path=output_path,
                config=config,
                analytic_path=analytic_path,
                mabd_path=mabd_path,
                rbd_path=rbd_path,
            )

        self.assertEqual(report.baseline_lane, "physical_pendulum_comparison_protocol")
        self.assertEqual(report.solver_mode, "physical_pendulum_multilane_comparison_development")
        self.assertEqual(report.backend, "report_protocol")
        self.assertEqual(report.status, EvidenceStatus.INCOMPLETE)
        self.assertFalse(report.observed["full_experiment_claim_passed"])
        self.assertEqual(report.observed["missing_required_lanes"], ["mabd_newton"])
        self.assertIn("joint_force_waveform_agreement_missing", report.observed["blocking_reasons"])
        self.assertEqual(report.observed["matched_sample_count"], 5)
        self.assertEqual(report.observed["mabd_sample_count"], 5)
        self.assertEqual(report.observed["rbd_sample_count"], 5)
        self.assertEqual(report.observed["unmatched_mabd_samples"], [])
        self.assertEqual(report.observed["unmatched_rbd_samples"], [])
        self.assertIn("max_mabd_rbd_abs_angle_delta_rad", report.observed)
        self.assertGreater(len(report.observed["angle_sample_differences_rad"]), 0)
        self.assertEqual(
            report.observed["paper_metric_statuses"]["joint_force_error"]["status"],
            "missing_waveform_not_max_magnitude",
        )
        self.assertEqual(
            report.observed["input_report_provenance"]["rbd_implicit_baseline"]["source_commit"],
            "test-source",
        )
        self.assertIn("sha256", report.observed["input_report_provenance"]["analytic_reference"])

    def test_physical_pendulum_comparison_rejects_wrong_lane_identity(self) -> None:
        cases = (
            ("analytic", "claim_id", "wrong.claim", "analytic_reference report claim_id"),
            ("mabd", "scene_id", "wrong_scene", "physical_pendulum_mabd_development_diagnostic report scene_id"),
            ("rbd", "baseline_lane", "wrong_lane", "rbd_implicit_baseline report must have baseline_lane"),
        )
        for lane_name, key, value, pattern in cases:
            with self.subTest(lane=lane_name, key=key):
                with TemporaryDirectory() as tmpdir:
                    config, analytic_path, mabd_path, rbd_path = self._write_lane_reports(tmpdir)
                    lane_paths = {"analytic": analytic_path, "mabd": mabd_path, "rbd": rbd_path}
                    self._mutate_report(lane_paths[lane_name], key, value=value)
                    output_path = Path(tmpdir) / "comparison.json"

                    with self.assertRaisesRegex(ValueError, pattern):
                        self._write_comparison(
                            output_path=output_path,
                            config=config,
                            analytic_path=analytic_path,
                            mabd_path=mabd_path,
                            rbd_path=rbd_path,
                        )
                    self.assertFalse(output_path.exists())

    def test_physical_pendulum_comparison_rejects_wrong_protocol_identity(self) -> None:
        cases = (
            ("analytic", "solver_mode", "wrong_solver", "analytic_reference report solver_mode"),
            ("mabd", "backend", "wrong_backend", "physical_pendulum_mabd_development_diagnostic report backend"),
            ("rbd", "status", "failed", "rbd_implicit_baseline report status"),
        )
        for lane_name, key, value, pattern in cases:
            with self.subTest(lane=lane_name, key=key):
                with TemporaryDirectory() as tmpdir:
                    config, analytic_path, mabd_path, rbd_path = self._write_lane_reports(tmpdir)
                    lane_paths = {"analytic": analytic_path, "mabd": mabd_path, "rbd": rbd_path}
                    self._mutate_report(lane_paths[lane_name], key, value=value)
                    output_path = Path(tmpdir) / "comparison.json"

                    with self.assertRaisesRegex(ValueError, pattern):
                        self._write_comparison(
                            output_path=output_path,
                            config=config,
                            analytic_path=analytic_path,
                            mabd_path=mabd_path,
                            rbd_path=rbd_path,
                        )
                    self.assertFalse(output_path.exists())

    def test_physical_pendulum_comparison_blocks_zero_matched_samples(self) -> None:
        with TemporaryDirectory() as tmpdir:
            config, analytic_path, mabd_path, rbd_path = self._write_lane_reports(tmpdir)
            payload = json.loads(rbd_path.read_text(encoding="utf-8"))
            for row in payload["observed"]["angle_samples_rad"]:
                row["step"] += 1000
            rbd_path.write_text(json.dumps(payload), encoding="utf-8")
            output_path = Path(tmpdir) / "comparison.json"
            report = self._write_comparison(
                output_path=output_path,
                config=config,
                analytic_path=analytic_path,
                mabd_path=mabd_path,
                rbd_path=rbd_path,
            )

        self.assertEqual(report.observed["matched_sample_count"], 0)
        self.assertIn("angle_sample_alignment_missing", report.observed["blocking_reasons"])
        self.assertEqual(report.observed["angle_sample_differences_rad"], [])
        self.assertEqual(len(report.observed["unmatched_rbd_samples"]), 5)

    def test_physical_pendulum_comparison_blocks_nonfinite_samples_without_nan_json(self) -> None:
        with TemporaryDirectory() as tmpdir:
            config, analytic_path, mabd_path, rbd_path = self._write_lane_reports(tmpdir)
            payload = json.loads(mabd_path.read_text(encoding="utf-8"))
            payload["observed"]["angle_samples_rad"][1]["angle_rad"] = float("nan")
            mabd_path.write_text(json.dumps(payload), encoding="utf-8")
            output_path = Path(tmpdir) / "comparison.json"
            report = self._write_comparison(
                output_path=output_path,
                config=config,
                analytic_path=analytic_path,
                mabd_path=mabd_path,
                rbd_path=rbd_path,
            )
            raw_output = output_path.read_text(encoding="utf-8")

        self.assertIn("angle_sample_nonfinite", report.observed["blocking_reasons"])
        self.assertEqual(report.observed["matched_sample_count"], 5)
        self.assertEqual(len(report.observed["angle_sample_differences_rad"]), 4)
        self.assertNotIn("NaN", raw_output)
        self.assertNotIn("Infinity", raw_output)


if __name__ == "__main__":
    unittest.main()
