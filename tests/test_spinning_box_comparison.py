from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np

from mabd_reproduction.experiment_configs import load_spinning_box_config
from mabd_reproduction.reporting import EvidenceStatus, load_claim_report
from mabd_reproduction.rigid_baselines import write_spinning_box_paper_rbd_baseline_report
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
        write_spinning_box_paper_rbd_baseline_report(
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
        self.assertEqual(loaded.observed["lane_gate_statuses"]["mabd_newton"], "incomplete")
        self.assertEqual(loaded.observed["lane_gate_statuses"]["rbd_implicit_baseline"], "passed")
        self.assertNotIn("mabd_newton:linear_momentum_error", loaded.observed["missing_required_metrics"])
        self.assertNotIn("mabd_newton:angular_momentum_error", loaded.observed["missing_required_metrics"])
        self.assertNotIn("mabd_newton:energy_drift", loaded.observed["missing_required_metrics"])
        self.assertEqual(loaded.observed["invalid_required_metrics"], [])
        differences = loaded.observed["lane_metric_differences"][
            "mabd_newton_minus_rbd_implicit_baseline"
        ]
        self.assertIn("linear_momentum_error", differences)
        self.assertIn("angular_momentum_error", differences)
        self.assertIn("energy_drift", differences)
        self.assertEqual(
            loaded.observed["lane_vector_metrics"]["mabd_newton"]["initial_position_m"],
            [0.0, 0.05, 0.0],
        )
        np.testing.assert_allclose(
            loaded.observed["lane_vector_metrics"]["rbd_implicit_baseline"]["final_position_m"],
            [4.0, 0.05, 0.0],
            atol=1.0e-6,
        )
        vector_differences = loaded.observed["lane_vector_metric_differences"][
            "mabd_newton_minus_rbd_implicit_baseline"
        ]
        np.testing.assert_allclose(
            vector_differences["initial_position_m"],
            [0.0, 0.0, 0.0],
        )
        np.testing.assert_allclose(
            vector_differences["final_position_m"],
            [0.0, 0.0, 0.0],
            atol=1.0e-6,
        )
        self.assertLessEqual(
            loaded.observed["lane_metrics"]["mabd_newton"]["linear_momentum_error"],
            1.0e-9,
        )
        self.assertGreater(
            loaded.observed["lane_metrics"]["mabd_newton"]["angular_momentum_error"],
            1.0e-9,
        )
        self.assertEqual(
            loaded.observed["lane_solver_modes"]["rbd_implicit_baseline"],
            "paper_faithful_implicit_rbd",
        )
        self.assertIn("mabd_newton_report_incomplete", loaded.observed["blocking_reasons"])
        self.assertIn(
            "spinning_box_comparison_pass_gate_not_enabled",
            loaded.observed["blocking_reasons"],
        )
        self.assertNotIn(
            "rbd_implicit_baseline_report_incomplete",
            loaded.observed["blocking_reasons"],
        )
        self.assertNotIn(
            "rbd_implicit_baseline_not_paper_faithful",
            loaded.observed["blocking_reasons"],
        )
        self.assertIn("comparison pass gate", loaded.failure_reason)
        self.assertEqual(loaded.threshold["required_lane_status"], "passed")
        self.assertEqual(loaded.threshold["required_lane_gate_status"], "passed")

    def test_spinning_box_comparison_keeps_mabd_horizon_diagnostic_incomplete(self) -> None:
        from mabd_reproduction.comparison_reports import write_spinning_box_comparison_report
        from mabd_reproduction.single_body_reports import (
            write_spinning_box_paper_horizon_report,
        )

        config = load_spinning_box_config(CONFIG_PATH)
        with TemporaryDirectory() as tmpdir:
            mabd_path = Path(tmpdir) / "mabd_horizon.json"
            rbd_path = Path(tmpdir) / "rbd.json"
            write_spinning_box_paper_horizon_report(
                mabd_path,
                config=config,
                source_commit="test-source",
                vendored_newton_commit="test-newton",
            )
            write_spinning_box_paper_rbd_baseline_report(
                rbd_path,
                config=config,
                source_commit="test-source",
                vendored_newton_commit="test-newton",
            )
            output_path = Path(tmpdir) / "comparison.json"

            write_spinning_box_comparison_report(
                output_path,
                config=config,
                mabd_report_path=mabd_path,
                rbd_report_path=rbd_path,
                source_commit="test-source",
                vendored_newton_commit="test-newton",
            )
            mabd_report = load_claim_report(mabd_path)
            loaded = load_claim_report(output_path)

        self.assertNotIn("lane_gate_status", mabd_report.observed)
        self.assertEqual(loaded.observed["lane_gate_statuses"]["mabd_newton"], "incomplete")
        self.assertEqual(loaded.observed["lane_gate_statuses"]["rbd_implicit_baseline"], "passed")
        self.assertIn("mabd_newton_report_incomplete", loaded.observed["blocking_reasons"])
        self.assertIn(
            "spinning_box_comparison_pass_gate_not_enabled",
            loaded.observed["blocking_reasons"],
        )

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

    def test_spinning_box_comparison_flags_invalid_required_metrics(self) -> None:
        import json

        from mabd_reproduction.comparison_reports import write_spinning_box_comparison_report

        config = load_spinning_box_config(CONFIG_PATH)
        for invalid_value, json_token in ((None, "NaN"), (float("nan"), "NaN"), (float("inf"), "Infinity")):
            with self.subTest(invalid_value=invalid_value):
                with TemporaryDirectory() as tmpdir:
                    mabd_path, rbd_path = self._write_lane_reports(tmpdir)
                    data = json.loads(mabd_path.read_text(encoding="utf-8"))
                    data["observed"]["energy_drift"] = invalid_value
                    mabd_path.write_text(json.dumps(data), encoding="utf-8")
                    output_path = Path(tmpdir) / "comparison.json"

                    write_spinning_box_comparison_report(
                        output_path,
                        config=config,
                        mabd_report_path=mabd_path,
                        rbd_report_path=rbd_path,
                        source_commit="test-source",
                        vendored_newton_commit="test-newton",
                    )
                    payload = output_path.read_text(encoding="utf-8")
                    loaded = load_claim_report(output_path)

                self.assertNotIn(json_token, payload)
                self.assertNotIn(
                    "mabd_newton:energy_drift",
                    loaded.observed["missing_required_metrics"],
                )
                self.assertIn(
                    "mabd_newton:energy_drift",
                    loaded.observed["invalid_required_metrics"],
                )
                self.assertIsNone(
                    loaded.observed["lane_metrics"]["mabd_newton"]["energy_drift"]
                )
                self.assertIn(
                    "mabd_newton:energy_drift_invalid",
                    loaded.observed["blocking_reasons"],
                )

    def test_spinning_box_comparison_flags_invalid_position_vectors(self) -> None:
        import json

        from mabd_reproduction.comparison_reports import write_spinning_box_comparison_report

        config = load_spinning_box_config(CONFIG_PATH)
        with TemporaryDirectory() as tmpdir:
            mabd_path, rbd_path = self._write_lane_reports(tmpdir)
            data = json.loads(mabd_path.read_text(encoding="utf-8"))
            data["observed"]["final_position_m"] = [0.0, float("nan"), 0.0]
            mabd_path.write_text(json.dumps(data), encoding="utf-8")
            output_path = Path(tmpdir) / "comparison.json"

            write_spinning_box_comparison_report(
                output_path,
                config=config,
                mabd_report_path=mabd_path,
                rbd_report_path=rbd_path,
                source_commit="test-source",
                vendored_newton_commit="test-newton",
            )
            payload = output_path.read_text(encoding="utf-8")
            loaded = load_claim_report(output_path)

        self.assertNotIn("NaN", payload)
        self.assertIn(
            "mabd_newton:final_position_m",
            loaded.observed["invalid_required_vector_metrics"],
        )
        self.assertNotIn(
            "mabd_newton:final_position_m",
            loaded.observed["missing_required_vector_metrics"],
        )
        self.assertIsNone(
            loaded.observed["lane_vector_metrics"]["mabd_newton"]["final_position_m"]
        )
        self.assertIn(
            "mabd_newton:final_position_m_invalid",
            loaded.observed["blocking_reasons"],
        )

    def test_spinning_box_comparison_omits_overflowed_metric_differences(self) -> None:
        import json

        from mabd_reproduction.comparison_reports import write_spinning_box_comparison_report

        config = load_spinning_box_config(CONFIG_PATH)
        with TemporaryDirectory() as tmpdir:
            mabd_path, rbd_path = self._write_lane_reports(tmpdir)
            mabd_data = json.loads(mabd_path.read_text(encoding="utf-8"))
            rbd_data = json.loads(rbd_path.read_text(encoding="utf-8"))
            mabd_data["observed"]["linear_momentum_error"] = 1.79e308
            rbd_data["observed"]["linear_momentum_error"] = -1.79e308
            mabd_data["observed"]["final_position_m"] = [1.79e308, 0.05, 0.0]
            rbd_data["observed"]["final_position_m"] = [-1.79e308, 0.05, 0.0]
            mabd_path.write_text(json.dumps(mabd_data), encoding="utf-8")
            rbd_path.write_text(json.dumps(rbd_data), encoding="utf-8")
            output_path = Path(tmpdir) / "comparison.json"

            write_spinning_box_comparison_report(
                output_path,
                config=config,
                mabd_report_path=mabd_path,
                rbd_report_path=rbd_path,
                source_commit="test-source",
                vendored_newton_commit="test-newton",
            )
            payload = output_path.read_text(encoding="utf-8")
            loaded = load_claim_report(output_path)

        self.assertNotIn("Infinity", payload)
        self.assertNotIn(
            "linear_momentum_error",
            loaded.observed["lane_metric_differences"][
                "mabd_newton_minus_rbd_implicit_baseline"
            ],
        )
        self.assertNotIn(
            "final_position_m",
            loaded.observed["lane_vector_metric_differences"][
                "mabd_newton_minus_rbd_implicit_baseline"
            ],
        )


if __name__ == "__main__":
    unittest.main()
