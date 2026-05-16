from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from mabd_reproduction.reporting import EvidenceStatus, load_claim_report


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs/experiments/single_body_spinning_box.yaml"
MATRIX_PATH = ROOT / "configs/experiments/paper_experiment_matrix.yaml"


class ExperimentRunnerTests(unittest.TestCase):
    def test_run_spinning_box_experiment_writes_override_report(self) -> None:
        from mabd_reproduction.experiment_runner import run_spinning_box_experiment

        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "custom_report.json"
            result = run_spinning_box_experiment(
                config_path=CONFIG_PATH,
                matrix_path=MATRIX_PATH,
                output_path=output_path,
                source_commit="test-source",
                vendored_newton_commit="test-newton",
            )
            loaded = load_claim_report(output_path)

        self.assertEqual(result.report_path, output_path)
        self.assertEqual(result.claim_id, "experiment.single_body.spinning_box")
        self.assertEqual(result.status, EvidenceStatus.INCOMPLETE)
        self.assertEqual(loaded.status, EvidenceStatus.INCOMPLETE)
        self.assertEqual(loaded.source_commit, "test-source")
        self.assertEqual(loaded.vendored_newton_commit, "test-newton")
        self.assertEqual(loaded.observed["step_count"], 4)

    def test_run_spinning_box_experiment_uses_configured_output_under_output_root(self) -> None:
        from mabd_reproduction.experiment_runner import run_spinning_box_experiment

        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            result = run_spinning_box_experiment(
                config_path=CONFIG_PATH,
                matrix_path=MATRIX_PATH,
                output_root=root,
                source_commit="test-source",
                vendored_newton_commit="test-newton",
            )
            loaded = load_claim_report(result.report_path)

        self.assertEqual(
            result.report_path,
            root / "reports/experiment_matrix/single_body_spinning_box.json",
        )
        self.assertEqual(loaded.claim_id, "experiment.single_body.spinning_box")
        self.assertEqual(loaded.status, EvidenceStatus.INCOMPLETE)
        self.assertIn("rbd_implicit_baseline", loaded.failure_reason)

    def test_run_spinning_box_experiment_rejects_ambiguous_output_selection(self) -> None:
        from mabd_reproduction.experiment_runner import run_spinning_box_experiment

        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            with self.assertRaisesRegex(ValueError, "output_path and output_root"):
                run_spinning_box_experiment(
                    config_path=CONFIG_PATH,
                    matrix_path=MATRIX_PATH,
                    output_path=root / "report.json",
                    output_root=root,
                    source_commit="test-source",
                    vendored_newton_commit="test-newton",
                )

    def test_run_experiment_cli_writes_report_and_summary(self) -> None:
        import json
        import os
        import subprocess
        import sys

        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "cli_report.json"
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/run_experiment.py",
                    "--config",
                    str(CONFIG_PATH),
                    "--matrix",
                    str(MATRIX_PATH),
                    "--output",
                    str(output_path),
                    "--source-commit",
                    "cli-source",
                    "--vendored-newton-commit",
                    "cli-newton",
                ],
                cwd=ROOT,
                env={**os.environ, "PYTHONPATH": f"{ROOT / 'src'}:{ROOT / 'vendor/newton'}"},
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            summary = json.loads(result.stdout)
            loaded = load_claim_report(output_path)

        self.assertEqual(summary["claim_id"], "experiment.single_body.spinning_box")
        self.assertEqual(summary["status"], "incomplete")
        self.assertEqual(summary["output_report"], output_path.as_posix())
        self.assertEqual(loaded.source_commit, "cli-source")
        self.assertEqual(loaded.vendored_newton_commit, "cli-newton")

    def test_run_experiment_cli_rejects_unknown_claim(self) -> None:
        import os
        import subprocess
        import sys

        import yaml

        with TemporaryDirectory() as tmpdir:
            bad_config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
            bad_config["claim_id"] = "experiment.unknown"
            bad_path = Path(tmpdir) / "bad.yaml"
            bad_path.write_text(yaml.safe_dump(bad_config), encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/run_experiment.py",
                    "--config",
                    str(bad_path),
                    "--matrix",
                    str(MATRIX_PATH),
                    "--output",
                    str(Path(tmpdir) / "bad_report.json"),
                    "--source-commit",
                    "cli-source",
                    "--vendored-newton-commit",
                    "cli-newton",
                ],
                cwd=ROOT,
                env={**os.environ, "PYTHONPATH": f"{ROOT / 'src'}:{ROOT / 'vendor/newton'}"},
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("experiment.single_body.spinning_box", result.stderr)


if __name__ == "__main__":
    unittest.main()
