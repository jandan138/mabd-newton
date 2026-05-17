from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from mabd_reproduction.paper_source_audit import (
    physical_pendulum_geometry_source_audit,
)


def _line_filled_text(line_map: dict[int, str], *, total_lines: int = 100) -> str:
    lines = [""] * total_lines
    for line_number, text in line_map.items():
        lines[line_number - 1] = text
    return "\n".join(lines)


def _write_physical_pendulum_fixture(root: Path, *, extra_text: str = "") -> None:
    (root / "sections").mkdir(parents=True)
    (root / "sections_a").mkdir(parents=True)
    (root / "images/simple_pendulum").mkdir(parents=True)
    (root / "ref.bib").write_text(extra_text, encoding="utf-8")
    (root / "sections_a/multiabd.tex").write_text(extra_text, encoding="utf-8")
    (root / "sections/experiment.tex").write_text(
        _line_filled_text(
            {
                77: "\\begin{figure}",
                78: "\\centering",
                79: "\\includegraphics[width=\\linewidth]{images/simple_pendulum/simple_pendulum.pdf}",
                80: "\\caption{\\textbf{Physical pendulum.}",
                81: (
                    "We simulate a physical pendulum with a fixed pivot, released from a "
                    "horizontal configuration with zero initial velocity under gravity. "
                    "Top: We plot the pendulum angle over time, where the reference curve "
                    "is from the elliptic-integral (Eq.~\\ref{eq:elliptic}). Bottom: We "
                    "plot the magnitude of the joint force over time, which varies "
                    "periodically and peaks near the turning points of the swing. As the "
                    "time step decreases, both the angle trajectory and the joint-force "
                    "waveform produced by ABD better match the reference. Larger time "
                    "steps lead to accumulated phase drift.}"
                ),
                86: (
                    "In Fig.~\\ref{fig:pendulum}, we simulate a physical pendulum starting "
                    "from a horizontal position. The pendulum swings freely under gravity, "
                    "and we compare our ABD method and an implicit RBD baseline against the "
                    "analytic solution based on elliptic integrals of:"
                ),
                88: (
                    "\\theta(t)=\\frac{\\pi}{2}-2\\,\\arcsin\\!\\Big(\\kappa\\,"
                    "\\mathrm{sn}\\!\\big(K(\\kappa)-\\omega_{\\mathrm{lin}} t,"
                    "\\kappa\\big)\\Big),"
                ),
                91: (
                    "Our method tracks the analytic reference more closely than the "
                    "implicit RBD baseline and provides more stable results for both the "
                    "motion and joint forces."
                ),
                95: extra_text,
            }
        ),
        encoding="utf-8",
    )
    (root / "images/simple_pendulum/simple_pendulum.pdf").write_bytes(
        (
            b"%PDF-fixture\n<stRef:filePath>/tmp/test/pendulum15.png"
            b"</stRef:filePath>\n"
        )
    )


class PhysicalPendulumSourceAuditTests(unittest.TestCase):
    def test_audit_records_figure_source_and_missing_geometry(self) -> None:
        audit = physical_pendulum_geometry_source_audit()
        report = audit.to_report()

        self.assertEqual(audit.status, "source_assets_found_geometry_parameters_missing")
        self.assertEqual(
            audit.figure_pdf["path"],
            "images/simple_pendulum/simple_pendulum.pdf",
        )
        self.assertEqual(
            audit.file_hashes["sections/experiment.tex"],
            "c5927183fe4e3f1c1c1617e5b10b7e9006da6a9eac537e891cb1dac03d58dd0f",
        )
        self.assertEqual(
            audit.file_hashes["images/simple_pendulum/simple_pendulum.pdf"],
            "4b198ace42ff08d32dc266f1eca710987a2b6335d75878ee01b60498fed945cf",
        )
        for key, snippet in (
            ("fixed_pivot", "fixed pivot"),
            ("horizontal_release_zero_initial_velocity", "zero initial velocity"),
            ("elliptic_angle_reference", "\\theta(t)"),
            ("joint_force_magnitude_plot", "magnitude of the joint force"),
        ):
            finding = audit.positive_findings[key]
            self.assertIs(finding["present"], True)
            self.assertEqual(finding["path"], "sections/experiment.tex")
            self.assertEqual(finding["line_start"], 77)
            self.assertEqual(finding["line_end"], 91)
            self.assertIn(snippet, finding["evidence_text"])
        self.assertIn("body_geometry", audit.missing_parameters)
        self.assertIn("mass_distribution", audit.missing_parameters)
        self.assertIn("inertia_tensor", audit.missing_parameters)
        self.assertIn("raw_joint_force_curve_data", audit.missing_parameters)
        self.assertIn(
            "physical_pendulum_geometry_parameters_missing_from_public_source_assets",
            audit.blockers,
        )
        self.assertIn("pendulum15.png", "\n".join(audit.figure_pdf["embedded_image_paths"]))
        self.assertEqual(report["status"], audit.status)

    def test_audit_inventories_and_searches_source_tree(self) -> None:
        audit = physical_pendulum_geometry_source_audit()
        report = audit.to_report()

        self.assertIn("sections_a/multiabd.tex", audit.scanned_tex_paths)
        self.assertIn("ref.bib", audit.scanned_text_paths)
        self.assertIn("images/T-handle/T-handle.pdf", audit.source_tree_paths)
        self.assertIn("images/simple_pendulum/simple_pendulum.pdf", audit.source_tree_paths)
        self.assertGreaterEqual(len(audit.source_tree_paths), 30)

        absence = audit.absence_findings["physical_pendulum_geometry_parameter_search"]
        self.assertEqual(
            absence["status"],
            "no_paper_faithful_physical_pendulum_geometry_parameters_found",
        )
        self.assertEqual(absence["searched_source_path_count"], len(audit.source_tree_paths))
        self.assertIn("body geometry", absence["query_terms"])
        self.assertIn("mass distribution", absence["query_terms"])
        self.assertIn("inertia tensor", absence["query_terms"])
        self.assertEqual(absence["usable_parameter_disclosures"], [])
        self.assertIn("physical pendulum", "\n".join(absence["context_hits"]))
        self.assertIn("source_tree_paths", report)
        self.assertIn("absence_findings", report)

    def test_geometry_disclosure_triggers_manual_review_instead_of_absence_blocker(self) -> None:
        with TemporaryDirectory() as tmpdir:
            source_root = Path(tmpdir) / "source"
            _write_physical_pendulum_fixture(
                source_root,
                extra_text=(
                    "For the physical pendulum body geometry we use a rectangular bar; "
                    "physical pendulum length scale = 2.0 m; physical pendulum mass "
                    "distribution is uniform; physical pendulum inertia tensor is diagonal; "
                    "raw joint force curve data are stored in pendulum_force.csv."
                ),
            )

            audit = physical_pendulum_geometry_source_audit(source_root)

        absence = audit.absence_findings["physical_pendulum_geometry_parameter_search"]
        self.assertEqual(
            audit.status,
            "source_mentions_physical_pendulum_geometry_parameters_requiring_manual_review",
        )
        self.assertNotIn(
            "physical_pendulum_geometry_parameters_missing_from_public_source_assets",
            audit.blockers,
        )
        self.assertIn(
            "physical_pendulum_geometry_parameter_disclosure_found",
            audit.blockers,
        )
        self.assertGreater(len(absence["usable_parameter_disclosures"]), 0)

    def test_audit_requires_source_root(self) -> None:
        missing = Path("/tmp/mabd-paper/source-does-not-exist")
        with self.assertRaisesRegex(FileNotFoundError, "paper source root does not exist"):
            physical_pendulum_geometry_source_audit(missing)

    def test_audit_requires_experiment_tex_and_figure_pdf(self) -> None:
        with TemporaryDirectory() as tmpdir:
            source_root = Path(tmpdir) / "source"
            (source_root / "images/simple_pendulum").mkdir(parents=True)
            (source_root / "images/simple_pendulum/simple_pendulum.pdf").write_bytes(b"%PDF\n")
            with self.assertRaisesRegex(FileNotFoundError, "sections/experiment.tex"):
                physical_pendulum_geometry_source_audit(source_root)

        with TemporaryDirectory() as tmpdir:
            source_root = Path(tmpdir) / "source"
            (source_root / "sections").mkdir(parents=True)
            (source_root / "sections/experiment.tex").write_text("", encoding="utf-8")
            with self.assertRaisesRegex(
                FileNotFoundError,
                "images/simple_pendulum/simple_pendulum.pdf",
            ):
                physical_pendulum_geometry_source_audit(source_root)


if __name__ == "__main__":
    unittest.main()
