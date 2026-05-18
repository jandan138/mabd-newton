from __future__ import annotations

import unittest
from math import isfinite
from pathlib import Path
from tempfile import TemporaryDirectory

from mabd_reproduction.experiment_configs import load_t_handle_config
from mabd_reproduction.reporting import EvidenceStatus, load_claim_report
from mabd_reproduction.t_handle_digitization import (
    EXPECTED_RENDERED_SIZE_PX,
    RENDER_DPI,
    T_HANDLE_FIGURE_PDF,
    T_HANDLE_FIGURE_PDF_SHA256,
    digitize_t_handle_figure_curves,
    write_t_handle_figure_curve_report,
)


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs/experiments/single_body_t_handle.yaml"


class THandleDigitizationTests(unittest.TestCase):
    def test_digitizes_color_families_from_recorded_pdf(self) -> None:
        curves = digitize_t_handle_figure_curves(sample_count=51)

        self.assertEqual(curves.source_pdf_path, T_HANDLE_FIGURE_PDF.as_posix())
        self.assertEqual(curves.source_pdf_sha256, T_HANDLE_FIGURE_PDF_SHA256)
        self.assertEqual(curves.render_dpi, RENDER_DPI)
        self.assertEqual(curves.rendered_size_px, EXPECTED_RENDERED_SIZE_PX)
        self.assertEqual(curves.renderer_version, "pdftocairo 22.02.0")
        self.assertEqual(curves.sample_count, 51)
        self.assertEqual(curves.figure_curve_scope, "color_family_digitization_only")
        self.assertEqual(set(curves.angular_velocity_curves), {"blue", "orange", "green"})
        self.assertEqual(set(curves.energy_loss_curves), {"blue", "orange", "green"})
        for curve in (*curves.angular_velocity_curves.values(), *curves.energy_loss_curves.values()):
            self.assertTrue(curve.extraction_success)
            self.assertGreater(curve.sample_coverage, 0.80)
            self.assertEqual(curve.curve_identity_status, "color_family_not_legend_entry")
            self.assertAlmostEqual(curve.samples[0]["time_s"], 0.0)
            self.assertAlmostEqual(curve.samples[-1]["time_s"], 100.0)
            self.assertTrue(all(isfinite(sample["value"]) for sample in curve.samples))
        self.assertTrue(
            all(-2.0 <= sample["value"] <= 6.0 for sample in curves.angular_velocity_curves["green"].samples)
        )
        self.assertTrue(
            all(0.0 <= sample["value"] <= 0.25 for sample in curves.energy_loss_curves["blue"].samples)
        )

    def test_writes_incomplete_report_without_vendoring_raw_assets(self) -> None:
        config = load_t_handle_config(CONFIG_PATH)
        self.assertEqual(
            config.figure_curves.output_report,
            "reports/experiment_matrix/single_body_t_handle_figure_curves.json",
        )
        with TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "figure_curves.json"
            report = write_t_handle_figure_curve_report(
                output,
                config=config,
                source_commit="test-source",
                vendored_newton_commit="test-newton",
            )
            loaded = load_claim_report(output)

        self.assertEqual(report.status, EvidenceStatus.INCOMPLETE)
        self.assertEqual(loaded.baseline_lane, "paper_figure_digitization")
        self.assertEqual(loaded.solver_mode, "t_handle_paper_figure_digitization")
        self.assertEqual(loaded.backend, "pdftocairo_pillow")
        self.assertFalse(loaded.observed["full_experiment_claim_passed"])
        self.assertEqual(loaded.observed["lane_status"], "figure_color_families_digitized")
        self.assertTrue(loaded.observed["reference_curve_available"])
        self.assertEqual(loaded.observed["source_pdf_sha256"], T_HANDLE_FIGURE_PDF_SHA256)
        self.assertEqual(loaded.observed["rendered_size_px"], list(EXPECTED_RENDERED_SIZE_PX))
        self.assertIn("not_authors_raw_data", loaded.observed["limitations"])
        self.assertIn("no_solid_dashed_line_style_split", loaded.observed["limitations"])
        self.assertNotIn(".png", str(loaded.raw_outputs))
        self.assertNotIn(".pdf", str(loaded.raw_outputs))
        self.assertNotIn("base64", str(loaded.observed))


if __name__ == "__main__":
    unittest.main()
