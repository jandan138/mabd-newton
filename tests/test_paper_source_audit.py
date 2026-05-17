from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from mabd_reproduction.paper_source_audit import velocity_semantics_source_audit


def _line_filled_text(line_map: dict[int, str], *, total_lines: int = 260) -> str:
    lines = [""] * total_lines
    for line_number, text in line_map.items():
        lines[line_number - 1] = text
    return "\n".join(lines)


def _write_source_fixture(root: Path, *, omitted_file_text: str) -> None:
    (root / "sections").mkdir(parents=True)
    (root / "sections_a").mkdir(parents=True)
    (root / "images/cube").mkdir(parents=True)
    (root / "arxiv.tex").write_text("% root\n", encoding="utf-8")
    (root / "sections/singleabd.tex").write_text(
        _line_filled_text(
            {
                34: (
                    "E_I(\\bm{x}) with implicit Euler and "
                    "h\\dot{\\bm{x}}^n source evidence"
                )
            }
        ),
        encoding="utf-8",
    )
    (root / "sections/solver.tex").write_text(
        _line_filled_text(
            {
                219: (
                    "spatial twist source evidence "
                    "\\bm V^j = \\bm{G}\\dot{\\bm q}^j"
                ),
                238: (
                    "G(\\bm A^j)^\\top maps a wrench and "
                    "\\frac{1}{h}\\bm M_{A}^j\\dot{\\bm q}^j appears"
                ),
            }
        ),
        encoding="utf-8",
    )
    (root / "sections/experiment.tex").write_text(
        _line_filled_text(
            {
                40: (
                    "\\bm p_0=[100, 0, 0] and \\bm L_0=[0, 100, 0] "
                    "with \\bm V_0 map it to ABD generalized velocities"
                )
            }
        ),
        encoding="utf-8",
    )
    (root / "sections_a/multiabd.tex").write_text(omitted_file_text, encoding="utf-8")
    (root / "images/cube/roll_cube.pdf").write_bytes(b"%PDF-fixture\n")


class PaperSourceAuditTests(unittest.TestCase):
    def test_velocity_semantics_audit_records_source_basis(self) -> None:
        audit = velocity_semantics_source_audit()

        self.assertEqual(
            audit.status,
            "source_does_not_prove_decoupled_velocity_semantics",
        )
        self.assertEqual(audit.source_root, "/tmp/mabd-paper/source")
        self.assertEqual(
            audit.file_hashes["sections/singleabd.tex"],
            "0f18165cba13d358a07c67a652e728170abecd7372b5ba905ff2b4a5950a3e8d",
        )
        self.assertEqual(
            audit.file_hashes["sections/solver.tex"],
            "871dbd7ae7f5544b95c6c4dc0940cb6a0e73eca48415b1abed2e3599db90c97e",
        )
        self.assertEqual(
            audit.file_hashes["sections/experiment.tex"],
            "c5927183fe4e3f1c1c1617e5b10b7e9006da6a9eac537e891cb1dac03d58dd0f",
        )
        self.assertEqual(
            audit.file_hashes["images/cube/roll_cube.pdf"],
            "7669b062348324a3b0090cc9f44930655c83233a87f63389db9198b88f95ae80",
        )
        self.assertIn("arxiv.tex", audit.scanned_tex_paths)
        self.assertIn("sections/singleabd.tex", audit.scanned_tex_paths)
        self.assertIn("sections/solver.tex", audit.scanned_tex_paths)
        self.assertIn("sections/experiment.tex", audit.scanned_tex_paths)
        self.assertIn("sections_a/multiabd.tex", audit.scanned_tex_paths)

        findings = {finding.key: finding for finding in audit.findings}
        self.assertTrue(findings["implicit_euler_inertia_potential"].present)
        self.assertEqual(findings["implicit_euler_inertia_potential"].path, "sections/singleabd.tex")
        self.assertEqual(findings["implicit_euler_inertia_potential"].line_start, 34)
        self.assertIn("implicit Euler", findings["implicit_euler_inertia_potential"].evidence_text)
        self.assertIn("h\\dot{\\bm{x}}^n", findings["implicit_euler_inertia_potential"].evidence_text)

        self.assertTrue(findings["g_map_twist_velocity"].present)
        self.assertEqual(findings["g_map_twist_velocity"].path, "sections/solver.tex")
        self.assertEqual(findings["g_map_twist_velocity"].line_start, 219)
        self.assertIn("spatial twist", findings["g_map_twist_velocity"].evidence_text)
        self.assertIn("\\bm V^j = \\bm{G}\\dot{\\bm q}^j", findings["g_map_twist_velocity"].evidence_text)

        self.assertTrue(findings["wrench_map_generalized_force"].present)
        self.assertIn("G(\\bm A^j)^\\top", findings["wrench_map_generalized_force"].evidence_text)
        self.assertIn("\\frac{1}{h}\\bm M_{A}^j\\dot{\\bm q}^j", findings["wrench_map_generalized_force"].evidence_text)

        self.assertTrue(findings["spinning_box_twist_initialization"].present)
        self.assertEqual(findings["spinning_box_twist_initialization"].path, "sections/experiment.tex")
        self.assertIn("\\bm V_0", findings["spinning_box_twist_initialization"].evidence_text)
        self.assertIn("map it to ABD generalized velocities", findings["spinning_box_twist_initialization"].evidence_text)

        self.assertFalse(findings["decoupled_velocity_semantics"].present)
        self.assertIn("no matching uncommented source line", findings["decoupled_velocity_semantics"].evidence_text)
        self.assertFalse(findings["alternative_momentum_extraction"].present)
        self.assertIn(
            "source_does_not_specify_alternative_momentum_extraction",
            audit.blockers,
        )
        self.assertIn("source_does_not_specify_decoupled_velocity_semantics", audit.blockers)

    def test_velocity_semantics_audit_report_is_json_ready(self) -> None:
        report = velocity_semantics_source_audit().to_report()

        self.assertEqual(
            report["status"],
            "source_does_not_prove_decoupled_velocity_semantics",
        )
        self.assertEqual(report["source_root"], "/tmp/mabd-paper/source")
        self.assertIn("file_hashes", report)
        self.assertIn("scanned_tex_paths", report)
        self.assertIn("sections_a/multiabd.tex", report["scanned_tex_paths"])
        self.assertIn("findings", report)
        self.assertIn("blockers", report)
        self.assertIn(
            "source_does_not_specify_decoupled_velocity_semantics",
            report["blockers"],
        )

    def test_negative_scan_covers_all_tex_files_and_conditionally_reports_blockers(self) -> None:
        with TemporaryDirectory() as tmpdir:
            source_root = Path(tmpdir) / "source"
            _write_source_fixture(
                source_root,
                omitted_file_text=(
                    "The private note mentions decoupled velocity semantics and "
                    "alternative momentum extraction.\n"
                ),
            )

            audit = velocity_semantics_source_audit(source_root)

        findings = {finding.key: finding for finding in audit.findings}
        self.assertIn("sections_a/multiabd.tex", audit.scanned_tex_paths)
        self.assertTrue(findings["decoupled_velocity_semantics"].present)
        self.assertIn("sections_a/multiabd.tex", findings["decoupled_velocity_semantics"].path)
        self.assertTrue(findings["alternative_momentum_extraction"].present)
        self.assertNotIn("source_does_not_specify_decoupled_velocity_semantics", audit.blockers)
        self.assertNotIn("source_does_not_specify_alternative_momentum_extraction", audit.blockers)
        self.assertEqual(
            audit.status,
            "source_mentions_velocity_semantics_requiring_manual_review",
        )


if __name__ == "__main__":
    unittest.main()
