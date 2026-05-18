from __future__ import annotations

import json
import shutil
import unittest
from math import isfinite
from pathlib import Path
from tempfile import TemporaryDirectory

from mabd_reproduction.experiment_configs import load_t_handle_config
from mabd_reproduction.reporting import EvidenceStatus, load_claim_report
from mabd_reproduction.t_handle_reports import (
    write_t_handle_mabd_newton_report,
    write_t_handle_rk4_reference_report,
)


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs/experiments/single_body_t_handle.yaml"


class THandleComparisonReportTests(unittest.TestCase):
    def _write_lane_reports(self, tmpdir: str) -> tuple[object, Path, Path]:
        config = load_t_handle_config(CONFIG_PATH)
        root = Path(tmpdir)
        rk4_path = root / "rk4.json"
        mabd_path = root / "mabd.json"
        write_t_handle_rk4_reference_report(
            rk4_path,
            config=config,
            source_commit="test-source",
            vendored_newton_commit="test-newton",
        )
        write_t_handle_mabd_newton_report(
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
        from mabd_reproduction.comparison_reports import write_t_handle_comparison_report

        return write_t_handle_comparison_report(
            output_path,
            config=config,
            rk4_report_path=rk4_path,
            mabd_report_path=mabd_path,
            source_commit="test-source",
            vendored_newton_commit="test-newton",
        )

    def _mutate_report(self, path: Path, *keys: object, value: object) -> None:
        payload = json.loads(path.read_text(encoding="utf-8"))
        target = payload
        for key in keys[:-1]:
            target = target[key]
        target[keys[-1]] = value
        path.write_text(json.dumps(payload, allow_nan=True), encoding="utf-8")

    def test_t_handle_comparison_report_records_bounded_protocol(self) -> None:
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

        self.assertEqual(report.claim_id, "experiment.single_body.t_handle")
        self.assertEqual(loaded.baseline_lane, "t_handle_comparison_protocol")
        self.assertEqual(loaded.solver_mode, "t_handle_multilane_comparison_development")
        self.assertEqual(loaded.backend, "report_protocol")
        self.assertEqual(loaded.status, EvidenceStatus.INCOMPLETE)
        self.assertFalse(loaded.observed["full_experiment_claim_passed"])
        self.assertEqual(loaded.observed["missing_required_lanes"], [])
        self.assertEqual(
            loaded.observed["lane_observed_statuses"]["rbd_rk4_reference"],
            "diagnostic_generated",
        )
        self.assertEqual(
            loaded.observed["lane_observed_statuses"]["mabd_newton"],
            "incomplete_diagnostic_failed",
        )
        provenance = loaded.observed["input_report_provenance"]
        self.assertEqual(provenance["rbd_rk4_reference"]["source_commit"], "test-source")
        self.assertEqual(provenance["mabd_newton"]["baseline_lane"], "mabd_newton")
        self.assertEqual(
            provenance["mabd_newton"]["mabd_diagnostic_scope"],
            "t_handle_model_derived_proxy",
        )
        self.assertIn("sha256", provenance["rbd_rk4_reference"])
        self.assertIn("sample_index_differences", loaded.observed)
        self.assertGreater(loaded.observed["matched_sample_index_count"], 0)
        self.assertGreater(loaded.observed["time_aligned_sample_count"], 0)
        self.assertLessEqual(
            loaded.observed["max_sample_time_delta_s"],
            loaded.threshold["max_sample_time_delta_s"],
        )
        self.assertIsNotNone(loaded.observed["intermediate_axis_waveform_rmse_rad_s"])
        self.assertTrue(isfinite(loaded.observed["intermediate_axis_waveform_rmse_rad_s"]))
        self.assertIsNotNone(loaded.observed["max_abs_angular_velocity_delta_rad_s"])
        self.assertTrue(isfinite(loaded.observed["max_abs_angular_velocity_delta_rad_s"]))
        self.assertIn("flip_timing_diagnostics", loaded.observed)
        self.assertEqual(
            loaded.observed["flip_timing_diagnostics"]["method"],
            "sample_grid_linear_interpolation",
        )
        self.assertIn("energy_drift_diagnostics", loaded.observed)
        self.assertIsNotNone(
            loaded.observed["energy_drift_diagnostics"][
                "mabd_minus_rk4_relative_energy_drift"
            ]
        )
        self.assertEqual(
            loaded.observed["paper_metric_statuses"]["intermediate_axis_angular_velocity_waveform"][
                "status"
            ],
            "diagnostic_available_not_paper_curve",
        )
        self.assertEqual(
            loaded.observed["paper_metric_statuses"]["flip_timing_error"]["status"],
            "sample_grid_diagnostic_not_paper_timing",
        )
        self.assertEqual(
            loaded.observed["paper_metric_statuses"]["energy_loss"]["status"],
            "signed_energy_drift_diagnostic_not_paper_loss",
        )
        blockers = loaded.observed["blocking_reasons"]
        self.assertIn("exact_t_handle_geometry_unknown", blockers)
        self.assertIn("raw_t_handle_reference_curve_data_missing", blockers)
        self.assertIn("mabd_newton_report_incomplete", blockers)
        self.assertIn("t_handle_comparison_report_incomplete", blockers)
        self.assertIn("t_handle_comparison_pass_gate_not_enabled", blockers)
        self.assertIn("t_handle_timing_evidence_missing", blockers)
        self.assertNotIn("t_handle_comparison_report_missing", blockers)

    def test_t_handle_comparison_rejects_wrong_input_identity(self) -> None:
        cases = (
            ("claim_id", ("claim_id",), "experiment.single_body.heavy_top", "claim_id"),
            ("scene_id", ("scene_id",), "wrong_scene", "scene_id"),
            ("baseline_lane", ("baseline_lane",), "mabd_newton", "baseline_lane"),
            ("solver_mode", ("solver_mode",), "wrong_solver", "solver_mode"),
            ("backend", ("backend",), "wrong_backend", "backend"),
            ("status", ("status",), "failed", "status"),
            (
                "asset_hash",
                ("asset_hashes", "t_handle_procedural"),
                "wrong_asset",
                "t_handle_procedural",
            ),
            (
                "full_experiment_claim_passed",
                ("observed", "full_experiment_claim_passed"),
                True,
                "full experiment",
            ),
            (
                "reference_scope",
                ("observed", "reference_scope"),
                "paper_faithful_t_handle",
                "reference_scope",
            ),
        )
        with TemporaryDirectory() as tmpdir:
            config, rk4_path, mabd_path = self._write_lane_reports(tmpdir)
            for name, keys, value, error in cases:
                mutated_rk4 = Path(tmpdir) / f"rk4_{name}.json"
                shutil.copyfile(rk4_path, mutated_rk4)
                self._mutate_report(mutated_rk4, *keys, value=value)
                output_path = Path(tmpdir) / f"comparison_{name}.json"
                with self.subTest(name=name), self.assertRaisesRegex(ValueError, error):
                    self._write_comparison(
                        output_path=output_path,
                        config=config,
                        rk4_path=mutated_rk4,
                        mabd_path=mabd_path,
                    )

    def test_t_handle_comparison_rejects_wrong_mabd_semantic_scope(self) -> None:
        cases = (
            (
                "mabd_diagnostic_scope",
                ("observed", "mabd_diagnostic_scope"),
                "paper_faithful_t_handle",
                "mabd_diagnostic_scope",
            ),
            (
                "solver_model_config_source",
                ("observed", "solver_model_config_source"),
                "manual_test_fixture",
                "solver_model_config_source",
            ),
        )
        with TemporaryDirectory() as tmpdir:
            config, rk4_path, mabd_path = self._write_lane_reports(tmpdir)
            for name, keys, value, error in cases:
                mutated_mabd = Path(tmpdir) / f"mabd_{name}.json"
                shutil.copyfile(mabd_path, mutated_mabd)
                self._mutate_report(mutated_mabd, *keys, value=value)
                output_path = Path(tmpdir) / f"comparison_{name}.json"
                with self.subTest(name=name), self.assertRaisesRegex(ValueError, error):
                    self._write_comparison(
                        output_path=output_path,
                        config=config,
                        rk4_path=rk4_path,
                        mabd_path=mutated_mabd,
                    )

    def test_t_handle_comparison_blocks_nonfinite_samples_without_nan_json(self) -> None:
        with TemporaryDirectory() as tmpdir:
            config, rk4_path, mabd_path = self._write_lane_reports(tmpdir)
            self._mutate_report(
                mabd_path,
                "observed",
                "angular_velocity_samples",
                1,
                "omega_y_rad_s",
                value=float("nan"),
            )
            output_path = Path(tmpdir) / "comparison.json"
            report = self._write_comparison(
                output_path=output_path,
                config=config,
                rk4_path=rk4_path,
                mabd_path=mabd_path,
            )
            raw_output = output_path.read_text(encoding="utf-8")

        self.assertEqual(report.status, EvidenceStatus.INCOMPLETE)
        self.assertTrue(report.observed["sample_nonfinite"])
        self.assertIn("nonfinite_sample_values", report.observed["blocking_reasons"])
        self.assertNotIn("NaN", raw_output)
        self.assertNotIn("Infinity", raw_output)


if __name__ == "__main__":
    unittest.main()
