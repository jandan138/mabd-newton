from __future__ import annotations

import json
import unittest
from math import isfinite
from pathlib import Path
from tempfile import TemporaryDirectory

from mabd_reproduction.experiment_configs import load_heavy_top_config
from mabd_reproduction.heavy_top_reports import (
    write_heavy_top_mabd_newton_report,
    write_heavy_top_rk4_reference_report,
)
from mabd_reproduction.reporting import EvidenceStatus, load_claim_report


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs/experiments/single_body_heavy_top.yaml"


class HeavyTopComparisonReportTests(unittest.TestCase):
    def _write_lane_reports(self, tmpdir: str) -> tuple[object, Path, Path]:
        config = load_heavy_top_config(CONFIG_PATH)
        root = Path(tmpdir)
        rk4_path = root / "rk4.json"
        mabd_path = root / "mabd.json"
        write_heavy_top_rk4_reference_report(
            rk4_path,
            config=config,
            source_commit="test-source",
            vendored_newton_commit="test-newton",
        )
        write_heavy_top_mabd_newton_report(
            mabd_path,
            config=config,
            source_commit="test-source",
            vendored_newton_commit="test-newton",
        )
        return config, rk4_path, mabd_path

    def _write_comparison(
        self,
        *,
        output_path: Path,
        config: object,
        rk4_path: Path,
        mabd_path: Path,
    ):
        from mabd_reproduction.comparison_reports import write_heavy_top_comparison_report

        return write_heavy_top_comparison_report(
            output_path,
            config=config,
            rk4_report_path=rk4_path,
            mabd_report_path=mabd_path,
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

    def test_heavy_top_comparison_report_records_bounded_protocol(self) -> None:
        with TemporaryDirectory() as tmpdir:
            config, rk4_path, mabd_path = self._write_lane_reports(tmpdir)
            output_path = Path(tmpdir) / "comparison.json"
            report = self._write_comparison(
                output_path=output_path,
                config=config,
                rk4_path=rk4_path,
                mabd_path=mabd_path,
            )
            loaded = load_claim_report(output_path)
            mabd_loaded = load_claim_report(mabd_path)

        self.assertEqual(report.claim_id, "experiment.single_body.heavy_top")
        self.assertEqual(loaded.baseline_lane, "heavy_top_comparison_protocol")
        self.assertEqual(loaded.solver_mode, "heavy_top_multilane_comparison_development")
        self.assertEqual(loaded.backend, "report_protocol")
        self.assertEqual(loaded.status, EvidenceStatus.INCOMPLETE)
        self.assertEqual(mabd_loaded.status, EvidenceStatus.INCOMPLETE)
        self.assertFalse(loaded.observed["full_experiment_claim_passed"])
        self.assertFalse(mabd_loaded.observed["full_experiment_claim_passed"])
        self.assertEqual(loaded.observed["missing_required_lanes"], [])
        self.assertEqual(
            loaded.observed["missing_paper_metrics"],
            [
                "nutation_angle_error:paper_reference_curve_missing",
            ],
        )
        self.assertTrue(
            all(
                isfinite(sample["precession_velocity_rad_s"])
                for sample in mabd_loaded.observed["precession_nutation_samples"]
            )
        )
        self.assertTrue(isfinite(mabd_loaded.observed["energy_initial"]))
        self.assertTrue(isfinite(mabd_loaded.observed["energy_final"]))
        self.assertTrue(isfinite(mabd_loaded.observed["relative_energy_drift"]))
        self.assertIn("mabd_newton_report_incomplete", loaded.observed["blocking_reasons"])
        self.assertIn(
            "exact_heavy_top_inertia_unknown",
            loaded.observed["blocking_reasons"],
        )
        self.assertIn(
            "exact_heavy_top_geometry_unknown",
            loaded.observed["blocking_reasons"],
        )
        self.assertIn(
            "raw_heavy_top_reference_curve_data_missing",
            loaded.observed["blocking_reasons"],
        )
        self.assertIn(
            "heavy_top_timing_evidence_missing",
            loaded.observed["blocking_reasons"],
        )
        self.assertIn(
            "heavy_top_comparison_report_incomplete",
            loaded.observed["blocking_reasons"],
        )
        self.assertIn(
            "heavy_top_comparison_pass_gate_not_enabled",
            loaded.observed["blocking_reasons"],
        )
        self.assertIn("sample_time_grid_mismatch", loaded.observed["blocking_reasons"])
        self.assertEqual(
            loaded.observed["lane_observed_statuses"]["rbd_rk4_reference"],
            "diagnostic_generated",
        )
        self.assertEqual(
            loaded.observed["lane_observed_statuses"]["mabd_newton"],
            "incomplete_diagnostic_generated",
        )
        self.assertEqual(
            loaded.observed["input_report_provenance"]["mabd_newton"]["baseline_lane"],
            "mabd_newton",
        )
        self.assertEqual(
            loaded.observed["input_report_provenance"]["rbd_rk4_reference"]["source_commit"],
            "test-source",
        )
        self.assertIn("sha256", loaded.observed["input_report_provenance"]["rbd_rk4_reference"])
        self.assertGreater(loaded.observed["matched_sample_index_count"], 0)
        self.assertGreater(len(loaded.observed["sample_index_differences"]), 0)
        self.assertGreater(loaded.observed["max_sample_time_delta_s"], 0.0)
        self.assertIsNotNone(loaded.observed["lane_metrics"]["mabd_newton"]["energy_drift"])
        self.assertIsNotNone(
            loaded.observed["lane_metrics"]["rbd_rk4_reference"]["energy_drift"]
        )
        self.assertEqual(
            loaded.observed["paper_metric_statuses"]["precession_velocity_error"]["status"],
            "diagnostic_available",
        )
        self.assertEqual(
            loaded.observed["paper_metric_statuses"]["energy_drift"]["status"],
            "diagnostic_available",
        )

    def test_heavy_top_comparison_requires_per_sample_mabd_precession_velocity(self) -> None:
        with TemporaryDirectory() as tmpdir:
            config, rk4_path, mabd_path = self._write_lane_reports(tmpdir)
            payload = json.loads(mabd_path.read_text(encoding="utf-8"))
            del payload["observed"]["precession_nutation_samples"][0][
                "precession_velocity_rad_s"
            ]
            mabd_path.write_text(json.dumps(payload), encoding="utf-8")
            output_path = Path(tmpdir) / "comparison.json"
            report = self._write_comparison(
                output_path=output_path,
                config=config,
                rk4_path=rk4_path,
                mabd_path=mabd_path,
            )

        self.assertIn(
            "precession_velocity_error:mabd_precession_velocity_samples_missing",
            report.observed["missing_paper_metrics"],
        )
        self.assertEqual(
            report.observed["paper_metric_statuses"]["precession_velocity_error"]["status"],
            "missing_mabd_precession_velocity_samples",
        )

    def test_heavy_top_comparison_rejects_wrong_lane_identity(self) -> None:
        cases = (
            ("rk4", "claim_id", "wrong.claim", "rbd_rk4_reference report claim_id"),
            ("mabd", "scene_id", "wrong_scene", "mabd_newton report scene_id"),
            ("mabd", "baseline_lane", "wrong_lane", "mabd_newton report must have baseline_lane"),
        )
        for lane_name, key, value, pattern in cases:
            with self.subTest(lane=lane_name, key=key):
                with TemporaryDirectory() as tmpdir:
                    config, rk4_path, mabd_path = self._write_lane_reports(tmpdir)
                    paths = {"rk4": rk4_path, "mabd": mabd_path}
                    self._mutate_report(paths[lane_name], key, value=value)
                    output_path = Path(tmpdir) / "comparison.json"

                    with self.assertRaisesRegex(ValueError, pattern):
                        self._write_comparison(
                            output_path=output_path,
                            config=config,
                            rk4_path=rk4_path,
                            mabd_path=mabd_path,
                        )
                    self.assertFalse(output_path.exists())

    def test_heavy_top_comparison_rejects_wrong_protocol_identity(self) -> None:
        cases = (
            ("rk4", "solver_mode", "wrong_solver", "rbd_rk4_reference report solver_mode"),
            ("mabd", "backend", "wrong_backend", "mabd_newton report backend"),
            ("mabd", "status", "failed", "mabd_newton report status"),
        )
        for lane_name, key, value, pattern in cases:
            with self.subTest(lane=lane_name, key=key):
                with TemporaryDirectory() as tmpdir:
                    config, rk4_path, mabd_path = self._write_lane_reports(tmpdir)
                    paths = {"rk4": rk4_path, "mabd": mabd_path}
                    self._mutate_report(paths[lane_name], key, value=value)
                    output_path = Path(tmpdir) / "comparison.json"

                    with self.assertRaisesRegex(ValueError, pattern):
                        self._write_comparison(
                            output_path=output_path,
                            config=config,
                            rk4_path=rk4_path,
                            mabd_path=mabd_path,
                        )
                    self.assertFalse(output_path.exists())

    def test_heavy_top_comparison_flags_nonfinite_sample_without_nan_json(self) -> None:
        with TemporaryDirectory() as tmpdir:
            config, rk4_path, mabd_path = self._write_lane_reports(tmpdir)
            payload = json.loads(mabd_path.read_text(encoding="utf-8"))
            payload["observed"]["precession_nutation_samples"][1]["nutation_angle_deg"] = float("nan")
            mabd_path.write_text(json.dumps(payload), encoding="utf-8")
            output_path = Path(tmpdir) / "comparison.json"
            report = self._write_comparison(
                output_path=output_path,
                config=config,
                rk4_path=rk4_path,
                mabd_path=mabd_path,
            )
            raw_output = output_path.read_text(encoding="utf-8")

        self.assertIn("sample_nonfinite", report.observed["blocking_reasons"])
        self.assertLess(
            len(report.observed["sample_index_differences"]),
            report.observed["matched_sample_index_count"],
        )
        self.assertNotIn("NaN", raw_output)
        self.assertNotIn("Infinity", raw_output)


if __name__ == "__main__":
    unittest.main()
