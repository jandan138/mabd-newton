from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import yaml

from mabd_reproduction.reporting import EvidenceStatus, load_claim_report


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs/experiments/single_body_spinning_box.yaml"
MATRIX_PATH = ROOT / "configs/experiments/paper_experiment_matrix.yaml"


class ExperimentRunnerTests(unittest.TestCase):
    def _write_config_with(self, tmpdir: str, **updates: object) -> Path:
        config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
        report_updates = updates.pop("report", None)
        config.update(updates)
        if isinstance(report_updates, dict):
            config["report"].update(report_updates)
        path = Path(tmpdir) / "single_body_spinning_box.yaml"
        path.write_text(yaml.safe_dump(config), encoding="utf-8")
        return path

    def _write_matrix_with_output_report(self, tmpdir: str, output_report: str) -> Path:
        matrix = yaml.safe_load(MATRIX_PATH.read_text(encoding="utf-8"))
        for entry in matrix["experiments"]:
            if entry["claim_id"] == "experiment.single_body.spinning_box":
                entry["output_report"] = output_report
                break
        path = Path(tmpdir) / "paper_experiment_matrix.yaml"
        path.write_text(yaml.safe_dump(matrix), encoding="utf-8")
        return path

    def _write_spinning_box_lane_inputs(self, tmpdir: str) -> tuple[Path, Path]:
        from mabd_reproduction.experiment_configs import load_spinning_box_config
        from mabd_reproduction.rigid_baselines import (
            write_spinning_box_paper_rbd_baseline_report,
        )
        from mabd_reproduction.single_body_reports import write_spinning_box_development_report

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
        self.assertIn("mabd_newton", loaded.failure_reason)
        self.assertIn("comparison", loaded.failure_reason)

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

    def test_run_spinning_box_experiment_requires_incomplete_status(self) -> None:
        from mabd_reproduction.experiment_runner import run_spinning_box_experiment

        with TemporaryDirectory() as tmpdir:
            report_path = Path(tmpdir) / "failed_report.json"
            config_path = self._write_config_with(tmpdir, report={"status": "failed"})

            with self.assertRaisesRegex(ValueError, "incomplete"):
                run_spinning_box_experiment(
                    config_path=config_path,
                    matrix_path=MATRIX_PATH,
                    output_path=report_path,
                    source_commit="test-source",
                    vendored_newton_commit="test-newton",
                )
            self.assertFalse(report_path.exists())

    def test_run_spinning_box_experiment_rejects_output_root_escape(self) -> None:
        from mabd_reproduction.experiment_runner import run_spinning_box_experiment

        with TemporaryDirectory() as tmpdir:
            output_root = Path(tmpdir) / "root"
            output_report = "../escaped.json"
            config_path = self._write_config_with(tmpdir, report={"output_report": output_report})
            matrix_path = self._write_matrix_with_output_report(tmpdir, output_report)

            with self.assertRaisesRegex(ValueError, "output_report"):
                run_spinning_box_experiment(
                    config_path=config_path,
                    matrix_path=matrix_path,
                    output_root=output_root,
                    source_commit="test-source",
                    vendored_newton_commit="test-newton",
                )
            self.assertFalse((Path(tmpdir) / "escaped.json").exists())

    def test_run_spinning_box_experiment_rejects_absolute_output_root_target(self) -> None:
        from mabd_reproduction.experiment_runner import run_spinning_box_experiment

        with TemporaryDirectory() as tmpdir:
            output_root = Path(tmpdir) / "root"
            output_report = (Path(tmpdir) / "absolute_report.json").as_posix()
            config_path = self._write_config_with(tmpdir, report={"output_report": output_report})
            matrix_path = self._write_matrix_with_output_report(tmpdir, output_report)

            with self.assertRaisesRegex(ValueError, "output_report"):
                run_spinning_box_experiment(
                    config_path=config_path,
                    matrix_path=matrix_path,
                    output_root=output_root,
                    source_commit="test-source",
                    vendored_newton_commit="test-newton",
                )
            self.assertFalse(Path(output_report).exists())

    def test_run_spinning_box_rbd_baseline_writes_explicit_output_report(self) -> None:
        from mabd_reproduction.experiment_runner import run_spinning_box_rbd_baseline

        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "rbd_baseline.json"
            result = run_spinning_box_rbd_baseline(
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
        self.assertEqual(result.report.baseline_lane, "rbd_implicit_baseline")
        self.assertEqual(loaded.baseline_lane, "rbd_implicit_baseline")
        self.assertEqual(loaded.solver_mode, "paper_faithful_implicit_rbd")
        self.assertEqual(loaded.backend, "cpu_numpy_newton_only")
        self.assertEqual(loaded.observed["lane_gate_status"], "passed")
        self.assertEqual(loaded.source_commit, "test-source")
        self.assertEqual(loaded.vendored_newton_commit, "test-newton")
        self.assertIn("comparison pass gate", loaded.failure_reason)

    def test_run_spinning_box_comparison_writes_explicit_output_report(self) -> None:
        from mabd_reproduction.experiment_runner import run_spinning_box_comparison

        with TemporaryDirectory() as tmpdir:
            mabd_path, rbd_path = self._write_spinning_box_lane_inputs(tmpdir)
            output_path = Path(tmpdir) / "comparison.json"
            result = run_spinning_box_comparison(
                config_path=CONFIG_PATH,
                matrix_path=MATRIX_PATH,
                mabd_report_path=mabd_path,
                rbd_report_path=rbd_path,
                output_path=output_path,
                source_commit="test-source",
                vendored_newton_commit="test-newton",
            )
            loaded = load_claim_report(output_path)

        self.assertEqual(result.report_path, output_path)
        self.assertEqual(result.status, EvidenceStatus.INCOMPLETE)
        self.assertEqual(result.report.baseline_lane, "spinning_box_comparison_protocol")
        self.assertEqual(loaded.baseline_lane, "spinning_box_comparison_protocol")
        self.assertNotIn("mabd_newton:linear_momentum_error", loaded.observed["missing_required_metrics"])
        self.assertNotIn("mabd_newton:angular_momentum_error", loaded.observed["missing_required_metrics"])
        self.assertEqual(
            loaded.observed["lane_gate_statuses"]["rbd_implicit_baseline"],
            "passed",
        )
        self.assertNotIn(
            "rbd_implicit_baseline_report_incomplete",
            loaded.observed["blocking_reasons"],
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

    def test_run_experiment_cli_writes_rbd_baseline_lane_report(self) -> None:
        import json
        import os
        import subprocess
        import sys

        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "rbd_cli_report.json"
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/run_experiment.py",
                    "--lane",
                    "rbd_implicit_baseline",
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
        self.assertEqual(summary["baseline_lane"], "rbd_implicit_baseline")
        self.assertEqual(summary["output_report"], output_path.as_posix())
        self.assertEqual(loaded.baseline_lane, "rbd_implicit_baseline")
        self.assertEqual(loaded.solver_mode, "paper_faithful_implicit_rbd")
        self.assertEqual(loaded.backend, "cpu_numpy_newton_only")
        self.assertEqual(loaded.observed["lane_gate_status"], "passed")
        self.assertEqual(loaded.source_commit, "cli-source")
        self.assertEqual(loaded.vendored_newton_commit, "cli-newton")

    def test_run_experiment_cli_rbd_baseline_requires_explicit_output(self) -> None:
        import os
        import subprocess
        import sys

        with TemporaryDirectory() as tmpdir:
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/run_experiment.py",
                    "--lane",
                    "rbd_implicit_baseline",
                    "--config",
                    str(CONFIG_PATH),
                    "--matrix",
                    str(MATRIX_PATH),
                    "--output-root",
                    tmpdir,
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
        self.assertIn("rbd_implicit_baseline requires --output", result.stderr)

    def test_run_experiment_cli_writes_spinning_box_comparison_report(self) -> None:
        import json
        import os
        import subprocess
        import sys

        with TemporaryDirectory() as tmpdir:
            mabd_path, rbd_path = self._write_spinning_box_lane_inputs(tmpdir)
            output_path = Path(tmpdir) / "comparison_cli.json"
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/run_experiment.py",
                    "--lane",
                    "spinning_box_comparison",
                    "--config",
                    str(CONFIG_PATH),
                    "--matrix",
                    str(MATRIX_PATH),
                    "--mabd-report",
                    str(mabd_path),
                    "--rbd-report",
                    str(rbd_path),
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

        self.assertEqual(summary["baseline_lane"], "spinning_box_comparison_protocol")
        self.assertEqual(summary["status"], "incomplete")
        self.assertEqual(loaded.source_commit, "cli-source")

    def test_run_experiment_cli_comparison_requires_input_reports(self) -> None:
        import os
        import subprocess
        import sys

        with TemporaryDirectory() as tmpdir:
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/run_experiment.py",
                    "--lane",
                    "spinning_box_comparison",
                    "--config",
                    str(CONFIG_PATH),
                    "--matrix",
                    str(MATRIX_PATH),
                    "--output",
                    str(Path(tmpdir) / "comparison.json"),
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
        self.assertIn("spinning_box_comparison requires --mabd-report and --rbd-report", result.stderr)

    def test_run_experiment_cli_rejects_unknown_claim(self) -> None:
        import os
        import subprocess
        import sys

        with TemporaryDirectory() as tmpdir:
            bad_config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
            bad_config["claim_id"] = "experiment.unknown"
            bad_path = Path(tmpdir) / "bad.yaml"
            bad_path.write_text(yaml.safe_dump(bad_config), encoding="utf-8")
            output_path = Path(tmpdir) / "bad_report.json"
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/run_experiment.py",
                    "--config",
                    str(bad_path),
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

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("experiment.single_body.spinning_box", result.stderr)
        self.assertFalse(output_path.exists())


if __name__ == "__main__":
    unittest.main()
