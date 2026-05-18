from __future__ import annotations

import unittest
from math import isfinite
from pathlib import Path
from tempfile import TemporaryDirectory

from mabd_reproduction.experiment_configs import load_heavy_top_config
from mabd_reproduction.heavy_top_digitization import (
    EXPECTED_RENDERED_SIZE_PX,
    HEAVY_TOP_FIGURE_PDF,
    HEAVY_TOP_FIGURE_PDF_SHA256,
    RENDER_DPI,
    digitize_heavy_top_reference_curves,
    write_heavy_top_figure_curve_report,
)
from mabd_reproduction.reporting import EvidenceStatus, load_claim_report


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs/experiments/single_body_heavy_top.yaml"


class HeavyTopDigitizationTests(unittest.TestCase):
    def test_digitizes_green_reference_family_from_recorded_pdf(self) -> None:
        curves = digitize_heavy_top_reference_curves(sample_count=51)

        self.assertEqual(curves.source_pdf_path, HEAVY_TOP_FIGURE_PDF.as_posix())
        self.assertEqual(curves.source_pdf_sha256, HEAVY_TOP_FIGURE_PDF_SHA256)
        self.assertEqual(curves.render_dpi, RENDER_DPI)
        self.assertEqual(curves.rendered_size_px, EXPECTED_RENDERED_SIZE_PX)
        self.assertEqual(curves.renderer_version, "pdftocairo 22.02.0")
        self.assertEqual(curves.sample_count, 51)
        self.assertTrue(curves.reference_precession.extraction_success)
        self.assertTrue(curves.reference_nutation.extraction_success)
        self.assertGreater(curves.reference_precession.sample_coverage, 0.80)
        self.assertGreater(curves.reference_nutation.sample_coverage, 0.80)
        self.assertEqual(curves.reference_precession.metric, "precession_velocity_rad_s")
        self.assertEqual(curves.reference_precession.unit, "rad/s")
        self.assertEqual(curves.reference_nutation.metric, "nutation_angle_deg")
        self.assertEqual(curves.reference_nutation.unit, "deg")
        self.assertAlmostEqual(curves.reference_precession.samples[0]["time_s"], 0.0)
        self.assertAlmostEqual(curves.reference_precession.samples[-1]["time_s"], 10.0)
        self.assertAlmostEqual(curves.reference_nutation.samples[0]["time_s"], 0.0)
        self.assertAlmostEqual(curves.reference_nutation.samples[-1]["time_s"], 10.0)
        self.assertTrue(
            all(
                isfinite(sample["value"])
                for sample in (
                    curves.reference_precession.samples
                    + curves.reference_nutation.samples
                )
            )
        )
        self.assertTrue(
            all(0.0 <= sample["value"] <= 8.0 for sample in curves.reference_precession.samples)
        )
        self.assertTrue(
            all(5.0 <= sample["value"] <= 30.0 for sample in curves.reference_nutation.samples)
        )
        self.assertEqual(curves.non_reference_curve_status, "color_family_counts_only")
        self.assertGreater(curves.non_reference_color_counts["blue"], 0)
        self.assertGreater(curves.non_reference_color_counts["orange"], 0)

    def test_writes_incomplete_claim_report_without_vendoring_raw_assets(self) -> None:
        config = load_heavy_top_config(CONFIG_PATH)
        self.assertEqual(
            config.figure_curves.output_report,
            "reports/experiment_matrix/single_body_heavy_top_figure_curves.json",
        )

        with TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "figure_curves.json"
            report = write_heavy_top_figure_curve_report(
                output,
                config=config,
                source_commit="test-source",
                vendored_newton_commit="test-newton",
            )
            loaded = load_claim_report(output)

        self.assertEqual(report.status, EvidenceStatus.INCOMPLETE)
        self.assertEqual(loaded.baseline_lane, "paper_figure_digitization")
        self.assertEqual(loaded.solver_mode, "heavy_top_paper_figure_digitization")
        self.assertEqual(loaded.backend, "pdftocairo_pillow")
        self.assertFalse(loaded.observed["full_experiment_claim_passed"])
        self.assertEqual(loaded.observed["lane_status"], "reference_curves_digitized")
        self.assertTrue(loaded.observed["reference_curve_available"])
        self.assertEqual(loaded.observed["source_pdf_sha256"], HEAVY_TOP_FIGURE_PDF_SHA256)
        self.assertEqual(loaded.observed["rendered_size_px"], list(EXPECTED_RENDERED_SIZE_PX))
        self.assertIn("not_authors_raw_data", loaded.observed["limitations"])
        self.assertIn("no_blue_orange_line_style_split", loaded.observed["limitations"])
        self.assertNotIn(".png", str(loaded.raw_outputs))
        self.assertNotIn(".pdf", str(loaded.raw_outputs))
        self.assertNotIn("base64", str(loaded.observed))
        self.assertIn("reference_precession", loaded.observed["reference_curves"])
        self.assertIn("reference_nutation", loaded.observed["reference_curves"])


if __name__ == "__main__":
    unittest.main()
