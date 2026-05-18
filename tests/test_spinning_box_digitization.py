from __future__ import annotations

import unittest
from math import isfinite
from pathlib import Path
from tempfile import TemporaryDirectory

from mabd_reproduction.experiment_configs import load_spinning_box_config
from mabd_reproduction.reporting import EvidenceStatus, load_claim_report
from mabd_reproduction.spinning_box_digitization import (
    ANGULAR_MOMENTUM_BOX_PX,
    EXPECTED_RENDERED_SIZE_PX,
    LINEAR_MOMENTUM_BOX_PX,
    RENDER_DPI,
    SPINNING_BOX_FIGURE_PDF,
    SPINNING_BOX_FIGURE_PDF_SHA256,
    digitize_spinning_box_figure_curves,
    write_spinning_box_figure_curve_report,
)


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs/experiments/single_body_spinning_box.yaml"


class SpinningBoxDigitizationTests(unittest.TestCase):
    def test_digitizer_rejects_bad_sample_count(self) -> None:
        for sample_count in (1, 0, -3):
            with self.subTest(sample_count=sample_count):
                with self.assertRaisesRegex(ValueError, "sample_count must be at least 2"):
                    digitize_spinning_box_figure_curves(sample_count=sample_count)

    def test_digitizes_color_families_from_recorded_pdf(self) -> None:
        curves = digitize_spinning_box_figure_curves(sample_count=31)

        self.assertEqual(curves.source_pdf_path, SPINNING_BOX_FIGURE_PDF.as_posix())
        self.assertEqual(curves.source_pdf_sha256, SPINNING_BOX_FIGURE_PDF_SHA256)
        self.assertEqual(curves.render_dpi, RENDER_DPI)
        self.assertEqual(curves.rendered_size_px, EXPECTED_RENDERED_SIZE_PX)
        self.assertRegex(curves.rendered_image_sha256, r"^[0-9a-f]{64}$")
        self.assertEqual(curves.renderer_version, "pdftocairo 22.02.0")
        self.assertEqual(curves.sample_count, 31)
        self.assertEqual(curves.figure_curve_scope, "paper_roll_cube_color_family_digitization")
        self.assertEqual(curves.color_assignment_policy, "nearest_color_family_within_threshold")
        self.assertEqual(curves.curve_identity_status, "color_family_not_legend_entry")
        self.assertEqual(curves.curve_agreement_status, "not_evaluated")
        self.assertTrue(curves.color_family_curve_available)
        self.assertFalse(curves.paper_reference_legend_identity_available)
        self.assertEqual(set(curves.angular_momentum_curves), {"blue", "orange", "green", "gray", "brown"})
        self.assertEqual(set(curves.linear_momentum_curves), {"blue", "orange", "green", "gray", "brown"})

        for curve in (*curves.angular_momentum_curves.values(), *curves.linear_momentum_curves.values()):
            self.assertTrue(curve.extraction_success)
            self.assertGreaterEqual(curve.sample_coverage, 0.80)
            self.assertGreaterEqual(curve.matched_sample_count, 25)
            self.assertLessEqual(curve.interpolated_sample_count, 6)
            self.assertLessEqual(curve.longest_missing_run, 5)
            self.assertGreater(curve.source_pixel_count, 0)
            self.assertEqual(curve.curve_identity_status, "color_family_not_legend_entry")
            self.assertEqual(curve.axis_range, (95.0, 100.0))
            self.assertAlmostEqual(curve.samples[0]["time_s"], 0.0)
            self.assertAlmostEqual(curve.samples[-1]["time_s"], 10.0)
            self.assertEqual(len(curve.samples), 31)
            self.assertTrue(all(isfinite(sample["value"]) for sample in curve.samples))
            self.assertTrue(all(95.0 <= sample["value"] <= 100.0 for sample in curve.samples))

        self.assertEqual(curves.angular_momentum_curves["blue"].plot_box_px, ANGULAR_MOMENTUM_BOX_PX)
        self.assertEqual(curves.linear_momentum_curves["blue"].plot_box_px, LINEAR_MOMENTUM_BOX_PX)

    def test_writes_incomplete_report_without_lane_gate_status(self) -> None:
        config = load_spinning_box_config(CONFIG_PATH)
        self.assertEqual(
            config.paper_horizon.figure_curve_output_report,
            "reports/experiment_matrix/single_body_spinning_box_figure_curves.json",
        )
        with TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "figure_curves.json"
            report = write_spinning_box_figure_curve_report(
                output,
                config=config,
                source_commit="test-source",
                vendored_newton_commit="test-newton",
                sample_count=31,
            )
            loaded = load_claim_report(output)

        self.assertEqual(report.status, EvidenceStatus.INCOMPLETE)
        self.assertEqual(loaded.claim_id, "experiment.single_body.spinning_box")
        self.assertEqual(loaded.baseline_lane, "paper_figure_digitization")
        self.assertEqual(loaded.solver_mode, "spinning_box_paper_figure_curve_digitization")
        self.assertEqual(loaded.backend, "paper_pdf_digitization")
        self.assertEqual(loaded.observed["figure_curve_scope"], "paper_roll_cube_color_family_digitization")
        self.assertEqual(loaded.observed["source_pdf_sha256"], SPINNING_BOX_FIGURE_PDF_SHA256)
        self.assertEqual(loaded.observed["rendered_size_px"], list(EXPECTED_RENDERED_SIZE_PX))
        self.assertRegex(loaded.observed["rendered_image_sha256"], r"^[0-9a-f]{64}$")
        self.assertTrue(loaded.observed["color_family_curve_available"])
        self.assertFalse(loaded.observed["paper_reference_legend_identity_available"])
        self.assertEqual(loaded.observed["color_assignment_policy"], "nearest_color_family_within_threshold")
        self.assertEqual(loaded.observed["curve_identity_status"], "color_family_not_legend_entry")
        self.assertEqual(loaded.observed["curve_agreement_status"], "not_evaluated")
        self.assertEqual(
            loaded.observed["blocking_reasons"],
            [
                "spinning_box_figure_curve_agreement_not_evaluated",
                "spinning_box_reference_legend_identity_not_evaluated",
                "spinning_box_line_style_split_not_evaluated",
                "mabd_newton_report_incomplete",
                "spinning_box_comparison_pass_gate_not_enabled",
            ],
        )
        self.assertNotIn("reference_curve_available", loaded.observed)
        self.assertNotIn("lane_gate_status", loaded.observed)
        self.assertNotIn(".png", str(loaded.raw_outputs))
        self.assertNotIn(".pdf", str(loaded.raw_outputs))
        self.assertNotIn("base64", str(loaded.observed))
