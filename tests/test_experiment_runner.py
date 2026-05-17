from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import yaml

from mabd_reproduction.reporting import EvidenceStatus, load_claim_report


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs/experiments/single_body_spinning_box.yaml"
HEAVY_TOP_CONFIG_PATH = ROOT / "configs/experiments/single_body_heavy_top.yaml"
PHYSICAL_PENDULUM_CONFIG_PATH = ROOT / "configs/experiments/single_body_physical_pendulum.yaml"
T_HANDLE_CONFIG_PATH = ROOT / "configs/experiments/single_body_t_handle.yaml"
MATRIX_PATH = ROOT / "configs/experiments/paper_experiment_matrix.yaml"
PHYSICAL_PENDULUM_TIMING_SOURCE_LINES = [
    "/tmp/mabd-paper/source/sections/experiment.tex:77-91"
]


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

    def _write_physical_pendulum_lane_inputs(self, tmpdir: str) -> tuple[Path, Path, Path]:
        from mabd_reproduction.experiment_configs import load_physical_pendulum_config
        from mabd_reproduction.physical_pendulum_reports import (
            write_physical_pendulum_analytic_reference_report,
            write_physical_pendulum_mabd_newton_report,
            write_physical_pendulum_rbd_baseline_report,
        )

        config = load_physical_pendulum_config(PHYSICAL_PENDULUM_CONFIG_PATH)
        analytic_path = Path(tmpdir) / "physical_pendulum_analytic.json"
        mabd_path = Path(tmpdir) / "physical_pendulum_mabd.json"
        rbd_path = Path(tmpdir) / "physical_pendulum_rbd.json"
        write_physical_pendulum_analytic_reference_report(
            analytic_path,
            config=config,
            source_commit="test-source",
            vendored_newton_commit="test-newton",
        )
        write_physical_pendulum_mabd_newton_report(
            mabd_path,
            config=config,
            source_commit="test-source",
            vendored_newton_commit="test-newton",
        )
        write_physical_pendulum_rbd_baseline_report(
            rbd_path,
            config=config,
            source_commit="test-source",
            vendored_newton_commit="test-newton",
        )
        return analytic_path, mabd_path, rbd_path

    def _assert_physical_pendulum_timing_source_audit(self, payload: dict[str, object]) -> None:
        self.assertEqual(payload["source_lines"], PHYSICAL_PENDULUM_TIMING_SOURCE_LINES)
        self.assertEqual(payload["status"], "not_a_physical_pendulum_paper_metric")
        self.assertFalse(payload["runtime_timing_claim_present"])
        self.assertFalse(payload["required_metric"])

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

    def test_run_spinning_box_paper_horizon_writes_explicit_output_report(self) -> None:
        from mabd_reproduction.experiment_runner import run_spinning_box_paper_horizon

        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "mabd_paper_horizon.json"
            result = run_spinning_box_paper_horizon(
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
        self.assertEqual(result.report.baseline_lane, "mabd_newton")
        self.assertEqual(loaded.baseline_lane, "mabd_newton")
        self.assertEqual(loaded.solver_mode, "mabd_cpu_oracle_paper_horizon_diagnostic")
        self.assertNotIn("lane_gate_status", loaded.observed)
        self.assertEqual(loaded.source_commit, "test-source")
        self.assertEqual(loaded.vendored_newton_commit, "test-newton")

    def test_run_spinning_box_paper_horizon_requires_explicit_output(self) -> None:
        from mabd_reproduction.experiment_runner import run_spinning_box_paper_horizon

        with TemporaryDirectory() as tmpdir:
            with self.assertRaisesRegex(ValueError, "mabd_paper_horizon requires --output"):
                run_spinning_box_paper_horizon(
                    config_path=CONFIG_PATH,
                    matrix_path=MATRIX_PATH,
                    output_root=Path(tmpdir),
                    source_commit="test-source",
                    vendored_newton_commit="test-newton",
                )

    def test_run_physical_pendulum_analytic_reference_writes_report(self) -> None:
        from mabd_reproduction.experiment_runner import (
            run_physical_pendulum_analytic_reference,
        )

        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "physical_pendulum_reference.json"
            result = run_physical_pendulum_analytic_reference(
                config_path=PHYSICAL_PENDULUM_CONFIG_PATH,
                matrix_path=MATRIX_PATH,
                output_path=output_path,
                source_commit="test-source",
                vendored_newton_commit="test-newton",
            )
            loaded = load_claim_report(output_path)

        self.assertEqual(result.report_path, output_path)
        self.assertEqual(result.claim_id, "experiment.single_body.physical_pendulum")
        self.assertEqual(result.status, EvidenceStatus.INCOMPLETE)
        self.assertEqual(result.report.baseline_lane, "analytic_reference")
        self.assertEqual(loaded.solver_mode, "analytic_elliptic_reference")
        self.assertEqual(loaded.backend, "cpu_scipy_reference")
        self.assertEqual(loaded.observed["lane_status"], "passed")
        self.assertEqual(loaded.observed["sample_count"], 9)
        self.assertEqual(loaded.observed["angle_samples_rad"][0]["angle_rad"], 0.0)
        self.assertEqual(
            loaded.expected["joint_force_reference_model"],
            "scalar_point_pendulum_radial_reaction",
        )
        self.assertIn("joint_force_samples_n", loaded.observed)
        self.assertEqual(loaded.observed["joint_force_samples_n"][0]["joint_force_magnitude_n"], 0.0)
        self.assertGreater(loaded.observed["max_joint_force_magnitude_n"], 0.0)
        self.assertIn("pendulum_geometry_unknown", loaded.failure_reason)
        self.assertEqual(loaded.source_commit, "test-source")
        self.assertEqual(loaded.vendored_newton_commit, "test-newton")

    def test_run_physical_pendulum_analytic_reference_requires_incomplete_status(self) -> None:
        from mabd_reproduction.experiment_runner import (
            run_physical_pendulum_analytic_reference,
        )

        with TemporaryDirectory() as tmpdir:
            source = yaml.safe_load(PHYSICAL_PENDULUM_CONFIG_PATH.read_text(encoding="utf-8"))
            source["report"]["status"] = "failed"
            config_path = Path(tmpdir) / "single_body_physical_pendulum.yaml"
            config_path.write_text(yaml.safe_dump(source), encoding="utf-8")
            output_path = Path(tmpdir) / "physical_pendulum_reference.json"

            with self.assertRaisesRegex(ValueError, "incomplete"):
                run_physical_pendulum_analytic_reference(
                    config_path=config_path,
                    matrix_path=MATRIX_PATH,
                    output_path=output_path,
                    source_commit="test-source",
                    vendored_newton_commit="test-newton",
                )
            self.assertFalse(output_path.exists())

    def test_run_physical_pendulum_analytic_reference_reports_failed_lane_on_threshold_violation(
        self,
    ) -> None:
        from mabd_reproduction.experiment_runner import (
            run_physical_pendulum_analytic_reference,
        )

        with TemporaryDirectory() as tmpdir:
            source = yaml.safe_load(PHYSICAL_PENDULUM_CONFIG_PATH.read_text(encoding="utf-8"))
            source["report"]["thresholds"]["max_abs_reference_identity_error"] = 1.0e-18
            config_path = Path(tmpdir) / "single_body_physical_pendulum.yaml"
            config_path.write_text(yaml.safe_dump(source), encoding="utf-8")
            output_path = Path(tmpdir) / "physical_pendulum_reference.json"

            result = run_physical_pendulum_analytic_reference(
                config_path=config_path,
                matrix_path=MATRIX_PATH,
                output_path=output_path,
                source_commit="test-source",
                vendored_newton_commit="test-newton",
            )
            loaded = load_claim_report(output_path)

        self.assertEqual(result.status, EvidenceStatus.INCOMPLETE)
        self.assertEqual(loaded.observed["lane_status"], "failed")
        self.assertEqual(
            loaded.observed["threshold_violations"],
            ["max_abs_reference_identity_error"],
        )

    def test_run_physical_pendulum_mabd_development_writes_report(self) -> None:
        from mabd_reproduction.experiment_runner import (
            run_physical_pendulum_mabd_development,
        )

        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "physical_pendulum_mabd.json"
            result = run_physical_pendulum_mabd_development(
                config_path=PHYSICAL_PENDULUM_CONFIG_PATH,
                matrix_path=MATRIX_PATH,
                output_path=output_path,
                source_commit="test-source",
                vendored_newton_commit="test-newton",
            )
            loaded = load_claim_report(output_path)

        self.assertEqual(result.report_path, output_path)
        self.assertEqual(result.claim_id, "experiment.single_body.physical_pendulum")
        self.assertEqual(result.status, EvidenceStatus.INCOMPLETE)
        self.assertEqual(
            result.report.baseline_lane,
            "physical_pendulum_mabd_development_diagnostic",
        )
        self.assertIn("mabd_newton", loaded.observed["required_missing_lanes"])
        self.assertEqual(loaded.solver_mode, "mabd_cpu_oracle_physical_pendulum_development")
        self.assertEqual(loaded.backend, "cpu_numpy_newton_only")
        self.assertEqual(loaded.observed["lane_status"], "development_diagnostic_generated")
        self.assertEqual(loaded.observed["required_missing_lanes"], ["mabd_newton"])
        self.assertEqual(loaded.observed["step_count"], 16)
        self.assertEqual(loaded.observed["sample_count"], 5)
        self.assertLessEqual(
            loaded.observed["max_pivot_residual_m"],
            loaded.threshold["max_pivot_residual_m"],
        )
        self.assertEqual(loaded.observed["angle_samples_rad"][0]["angle_rad"], 0.0)
        self.assertIn("pendulum_geometry_unknown", loaded.failure_reason)
        self.assertNotIn("rbd_implicit_baseline", loaded.failure_reason)
        self.assertEqual(loaded.source_commit, "test-source")
        self.assertEqual(loaded.vendored_newton_commit, "test-newton")

    def test_run_physical_pendulum_mabd_newton_writes_required_lane_report(self) -> None:
        from mabd_reproduction.experiment_runner import (
            run_physical_pendulum_mabd_newton,
        )

        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "physical_pendulum_mabd_newton.json"
            result = run_physical_pendulum_mabd_newton(
                config_path=PHYSICAL_PENDULUM_CONFIG_PATH,
                matrix_path=MATRIX_PATH,
                output_path=output_path,
                source_commit="test-source",
                vendored_newton_commit="test-newton",
            )
            loaded = load_claim_report(output_path)

        self.assertEqual(result.report_path, output_path)
        self.assertEqual(result.claim_id, "experiment.single_body.physical_pendulum")
        self.assertEqual(result.status, EvidenceStatus.INCOMPLETE)
        self.assertEqual(result.report.baseline_lane, "mabd_newton")
        self.assertEqual(loaded.baseline_lane, "mabd_newton")
        self.assertEqual(loaded.solver_mode, "mabd_cpu_oracle_physical_pendulum_newton_lane")
        self.assertEqual(loaded.backend, "cpu_numpy_newton_only")
        self.assertEqual(loaded.observed["lane_status"], "incomplete_diagnostic_generated")
        self.assertFalse(loaded.observed["full_experiment_claim_passed"])
        self.assertEqual(loaded.observed["mabd_rotation_mode"], "polar")
        self.assertEqual(
            loaded.observed["solver_model_config_source"],
            "newton_model_derived",
        )
        self.assertEqual(
            loaded.expected["solver_model_config_source"],
            "newton_model_derived",
        )
        expected_frequencies = ["mabd:body", "mabd:world_constraint", "mabd:gravity"]
        self.assertEqual(
            loaded.observed["newton_model_derived_custom_frequencies"],
            expected_frequencies,
        )
        self.assertEqual(
            loaded.expected["newton_model_derived_custom_frequencies"],
            expected_frequencies,
        )
        self.assertIn("max_phase_drift_rad", loaded.observed)
        self.assertIn("max_world_anchor_reaction_magnitude_n", loaded.observed)
        self.assertIn("max_abs_joint_force_error_n", loaded.observed)
        self.assertIn("world_anchor_reaction_vector_n", loaded.observed["angle_samples_rad"][-1])
        self.assertIn(
            "reference_joint_force_magnitude_n",
            loaded.observed["angle_samples_rad"][-1],
        )
        self.assertIn("abs_joint_force_error_n", loaded.observed["angle_samples_rad"][-1])
        self.assertNotIn(
            "joint_force_waveform_agreement_missing",
            loaded.observed["blocking_reasons"],
        )
        self.assertNotIn("paper_timing_missing", loaded.observed["blocking_reasons"])
        self._assert_physical_pendulum_timing_source_audit(
            loaded.observed["paper_timing_source_audit"]
        )
        self._assert_physical_pendulum_timing_source_audit(
            loaded.expected["paper_timing_source_audit"]
        )
        self.assertIn("pendulum_geometry_unknown", loaded.failure_reason)
        self.assertNotIn("paper timing", loaded.failure_reason)
        self.assertEqual(loaded.source_commit, "test-source")
        self.assertEqual(loaded.vendored_newton_commit, "test-newton")

    def test_run_physical_pendulum_rbd_baseline_writes_report(self) -> None:
        from mabd_reproduction.experiment_runner import (
            run_physical_pendulum_rbd_baseline,
        )

        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "physical_pendulum_rbd.json"
            result = run_physical_pendulum_rbd_baseline(
                config_path=PHYSICAL_PENDULUM_CONFIG_PATH,
                matrix_path=MATRIX_PATH,
                output_path=output_path,
                source_commit="test-source",
                vendored_newton_commit="test-newton",
            )
            loaded = load_claim_report(output_path)

        self.assertEqual(result.report_path, output_path)
        self.assertEqual(result.claim_id, "experiment.single_body.physical_pendulum")
        self.assertEqual(result.status, EvidenceStatus.INCOMPLETE)
        self.assertEqual(result.report.baseline_lane, "rbd_implicit_baseline")
        self.assertEqual(loaded.baseline_lane, "rbd_implicit_baseline")
        self.assertEqual(loaded.solver_mode, "physical_pendulum_scalar_implicit_rbd_development")
        self.assertEqual(loaded.backend, "cpu_numpy_newton_only")
        self.assertEqual(loaded.observed["lane_status"], "development_diagnostic_generated")
        self.assertEqual(loaded.observed["required_missing_lanes"], ["mabd_newton"])
        self.assertFalse(loaded.observed["full_experiment_claim_passed"])
        self.assertEqual(loaded.observed["sample_count"], 5)
        self.assertLessEqual(
            loaded.observed["max_implicit_residual"],
            loaded.threshold["max_implicit_residual"],
        )
        self.assertIn("max_abs_joint_force_error_n", loaded.observed)
        self.assertIn(
            "reference_joint_force_magnitude_n",
            loaded.observed["angle_samples_rad"][-1],
        )
        self.assertIn("abs_joint_force_error_n", loaded.observed["angle_samples_rad"][-1])
        self.assertNotIn(
            "joint_force_waveform_agreement_missing",
            loaded.observed["blocking_reasons"],
        )
        self.assertNotIn("paper_timing_missing", loaded.observed["blocking_reasons"])
        self._assert_physical_pendulum_timing_source_audit(
            loaded.observed["paper_timing_source_audit"]
        )
        self._assert_physical_pendulum_timing_source_audit(
            loaded.expected["paper_timing_source_audit"]
        )
        self.assertIn("pendulum_geometry_unknown", loaded.failure_reason)
        self.assertNotIn("paper timing", loaded.failure_reason)
        self.assertNotIn("full experiment passed", loaded.failure_reason)
        self.assertEqual(loaded.source_commit, "test-source")
        self.assertEqual(loaded.vendored_newton_commit, "test-newton")

    def test_run_physical_pendulum_comparison_writes_report(self) -> None:
        from mabd_reproduction.experiment_runner import run_physical_pendulum_comparison

        with TemporaryDirectory() as tmpdir:
            analytic_path, mabd_path, rbd_path = self._write_physical_pendulum_lane_inputs(tmpdir)
            output_path = Path(tmpdir) / "physical_pendulum_comparison.json"
            result = run_physical_pendulum_comparison(
                config_path=PHYSICAL_PENDULUM_CONFIG_PATH,
                matrix_path=MATRIX_PATH,
                analytic_report_path=analytic_path,
                mabd_report_path=mabd_path,
                rbd_report_path=rbd_path,
                output_path=output_path,
                source_commit="test-source",
                vendored_newton_commit="test-newton",
            )
            loaded = load_claim_report(output_path)

        self.assertEqual(result.report_path, output_path)
        self.assertEqual(result.claim_id, "experiment.single_body.physical_pendulum")
        self.assertEqual(result.status, EvidenceStatus.INCOMPLETE)
        self.assertEqual(result.report.baseline_lane, "physical_pendulum_comparison_protocol")
        self.assertEqual(loaded.baseline_lane, "physical_pendulum_comparison_protocol")
        self.assertEqual(loaded.solver_mode, "physical_pendulum_multilane_comparison_development")
        self.assertEqual(loaded.observed["missing_required_lanes"], [])
        self.assertEqual(loaded.observed["matched_sample_count"], 5)
        self.assertIn("input_report_provenance", loaded.observed)
        self.assertNotIn("paper_timing_missing", loaded.observed["blocking_reasons"])
        self.assertNotIn(
            "joint_force_waveform_agreement_missing",
            loaded.observed["blocking_reasons"],
        )
        self.assertEqual(
            loaded.observed["missing_paper_metrics"],
            ["joint_force_error:paper_geometry_unknown"],
        )
        self.assertEqual(
            loaded.observed["paper_metric_statuses"]["joint_force_error"]["status"],
            "diagnostic_scalar_reference_not_paper_geometry",
        )
        self.assertIn("joint_force_waveform_diagnostics", loaded.observed)
        self.assertEqual(
            loaded.observed["joint_force_waveform_diagnostics"]["matched_sample_count"],
            5,
        )
        self.assertIn("pendulum_geometry_unknown", loaded.observed["blocking_reasons"])
        self.assertIn(
            "physical_pendulum_comparison_pass_gate_not_enabled",
            loaded.observed["blocking_reasons"],
        )
        self._assert_physical_pendulum_timing_source_audit(
            loaded.observed["paper_timing_source_audit"]
        )
        self._assert_physical_pendulum_timing_source_audit(
            loaded.expected["paper_timing_source_audit"]
        )
        self.assertNotIn("paper timing", loaded.failure_reason)

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

    def test_run_t_handle_rk4_reference_writes_bounded_diagnostic_report(self) -> None:
        from mabd_reproduction.experiment_runner import run_t_handle_rk4_reference

        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "t_handle_rk4_reference.json"
            result = run_t_handle_rk4_reference(
                config_path=T_HANDLE_CONFIG_PATH,
                matrix_path=MATRIX_PATH,
                output_path=output_path,
                source_commit="test-source",
                vendored_newton_commit="test-newton",
            )
            loaded = load_claim_report(output_path)

        self.assertEqual(result.report_path, output_path)
        self.assertEqual(result.claim_id, "experiment.single_body.t_handle")
        self.assertEqual(result.status, EvidenceStatus.INCOMPLETE)
        self.assertEqual(result.report.baseline_lane, "rbd_rk4_reference")
        self.assertEqual(loaded.solver_mode, "t_handle_torque_free_rk4_reference")
        self.assertEqual(loaded.backend, "cpu_numpy")
        self.assertEqual(loaded.observed["lane_status"], "diagnostic_generated")
        self.assertFalse(loaded.observed["full_experiment_claim_passed"])
        self.assertGreaterEqual(loaded.observed["intermediate_axis_sign_flips"], 1)
        self.assertLessEqual(abs(loaded.observed["relative_energy_drift"]), 1.0e-8)
        self.assertIn("exact_t_handle_geometry_unknown", loaded.observed["blocking_reasons"])
        self.assertIn(
            "raw_t_handle_reference_curve_data_missing",
            loaded.observed["blocking_reasons"],
        )
        self.assertIn("mabd_newton_report_missing", loaded.observed["blocking_reasons"])
        self.assertIn("t_handle_comparison_report_missing", loaded.observed["blocking_reasons"])
        self.assertNotIn("lane_gate_status", loaded.observed)

    def test_run_t_handle_rk4_reference_requires_incomplete_status(self) -> None:
        from mabd_reproduction.experiment_runner import run_t_handle_rk4_reference

        with TemporaryDirectory() as tmpdir:
            source = yaml.safe_load(T_HANDLE_CONFIG_PATH.read_text(encoding="utf-8"))
            source["report"]["status"] = "failed"
            config_path = Path(tmpdir) / "single_body_t_handle.yaml"
            config_path.write_text(yaml.safe_dump(source), encoding="utf-8")
            output_path = Path(tmpdir) / "t_handle_rk4_reference.json"

            with self.assertRaisesRegex(ValueError, "incomplete"):
                run_t_handle_rk4_reference(
                    config_path=config_path,
                    matrix_path=MATRIX_PATH,
                    output_path=output_path,
                    source_commit="test-source",
                    vendored_newton_commit="test-newton",
                )
            self.assertFalse(output_path.exists())

    def test_run_heavy_top_rk4_reference_writes_bounded_diagnostic_report(self) -> None:
        from mabd_reproduction.experiment_runner import run_heavy_top_rk4_reference

        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "heavy_top_rk4_reference.json"
            result = run_heavy_top_rk4_reference(
                config_path=HEAVY_TOP_CONFIG_PATH,
                matrix_path=MATRIX_PATH,
                output_path=output_path,
                source_commit="test-source",
                vendored_newton_commit="test-newton",
            )
            loaded = load_claim_report(output_path)

        self.assertEqual(result.report_path, output_path)
        self.assertEqual(result.claim_id, "experiment.single_body.heavy_top")
        self.assertEqual(result.status, EvidenceStatus.INCOMPLETE)
        self.assertEqual(result.report.baseline_lane, "rbd_rk4_reference")
        self.assertEqual(loaded.solver_mode, "heavy_top_rk4_reference_diagnostic")
        self.assertEqual(loaded.backend, "cpu_numpy")
        self.assertEqual(loaded.observed["lane_status"], "diagnostic_generated")
        self.assertFalse(loaded.observed["full_experiment_claim_passed"])
        self.assertGreater(loaded.observed["max_abs_precession_velocity_rad_s"], 0.0)
        self.assertGreater(
            loaded.observed["max_nutation_angle_deg"] - loaded.observed["min_nutation_angle_deg"],
            0.0,
        )
        self.assertIn("exact_heavy_top_inertia_unknown", loaded.observed["blocking_reasons"])
        self.assertIn(
            "raw_heavy_top_reference_curve_data_missing",
            loaded.observed["blocking_reasons"],
        )
        self.assertIn("mabd_newton_report_missing", loaded.observed["blocking_reasons"])
        self.assertIn("heavy_top_comparison_report_missing", loaded.observed["blocking_reasons"])
        self.assertNotIn("lane_gate_status", loaded.observed)

    def test_run_heavy_top_rk4_reference_requires_incomplete_status(self) -> None:
        from mabd_reproduction.experiment_runner import run_heavy_top_rk4_reference

        with TemporaryDirectory() as tmpdir:
            source = yaml.safe_load(HEAVY_TOP_CONFIG_PATH.read_text(encoding="utf-8"))
            source["report"]["status"] = "failed"
            config_path = Path(tmpdir) / "single_body_heavy_top.yaml"
            config_path.write_text(yaml.safe_dump(source), encoding="utf-8")
            output_path = Path(tmpdir) / "heavy_top_rk4_reference.json"

            with self.assertRaisesRegex(ValueError, "incomplete"):
                run_heavy_top_rk4_reference(
                    config_path=config_path,
                    matrix_path=MATRIX_PATH,
                    output_path=output_path,
                    source_commit="test-source",
                    vendored_newton_commit="test-newton",
                )
            self.assertFalse(output_path.exists())

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

    def test_run_experiment_cli_writes_mabd_paper_horizon_report(self) -> None:
        import json
        import os
        import subprocess
        import sys

        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "mabd_horizon_cli_report.json"
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/run_experiment.py",
                    "--lane",
                    "mabd_paper_horizon",
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
        self.assertEqual(summary["baseline_lane"], "mabd_newton")
        self.assertEqual(summary["output_report"], output_path.as_posix())
        self.assertEqual(loaded.solver_mode, "mabd_cpu_oracle_paper_horizon_diagnostic")
        self.assertNotIn("lane_gate_status", loaded.observed)

    def test_run_experiment_cli_writes_physical_pendulum_analytic_reference_report(self) -> None:
        import json
        import os
        import subprocess
        import sys

        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "physical_pendulum_cli.json"
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/run_experiment.py",
                    "--lane",
                    "analytic_reference",
                    "--config",
                    str(PHYSICAL_PENDULUM_CONFIG_PATH),
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

        self.assertEqual(summary["claim_id"], "experiment.single_body.physical_pendulum")
        self.assertEqual(summary["status"], "incomplete")
        self.assertEqual(summary["baseline_lane"], "analytic_reference")
        self.assertEqual(loaded.solver_mode, "analytic_elliptic_reference")
        self.assertEqual(loaded.observed["lane_status"], "passed")

    def test_run_experiment_cli_writes_physical_pendulum_mabd_development_report(self) -> None:
        import json
        import os
        import subprocess
        import sys

        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "physical_pendulum_mabd_cli.json"
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/run_experiment.py",
                    "--lane",
                    "physical_pendulum_mabd_development",
                    "--config",
                    str(PHYSICAL_PENDULUM_CONFIG_PATH),
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

        self.assertEqual(summary["claim_id"], "experiment.single_body.physical_pendulum")
        self.assertEqual(summary["status"], "incomplete")
        self.assertEqual(
            summary["baseline_lane"],
            "physical_pendulum_mabd_development_diagnostic",
        )
        self.assertEqual(loaded.solver_mode, "mabd_cpu_oracle_physical_pendulum_development")
        self.assertEqual(loaded.observed["lane_status"], "development_diagnostic_generated")
        self.assertEqual(loaded.observed["required_missing_lanes"], ["mabd_newton"])

    def test_run_experiment_cli_writes_physical_pendulum_mabd_newton_report(self) -> None:
        import json
        import os
        import subprocess
        import sys

        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "physical_pendulum_mabd_newton_cli.json"
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/run_experiment.py",
                    "--lane",
                    "physical_pendulum_mabd_newton",
                    "--config",
                    str(PHYSICAL_PENDULUM_CONFIG_PATH),
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

        self.assertEqual(summary["claim_id"], "experiment.single_body.physical_pendulum")
        self.assertEqual(summary["status"], "incomplete")
        self.assertEqual(summary["baseline_lane"], "mabd_newton")
        self.assertEqual(summary["output_report"], output_path.as_posix())
        self.assertEqual(loaded.solver_mode, "mabd_cpu_oracle_physical_pendulum_newton_lane")
        self.assertIn("max_phase_drift_rad", loaded.observed)
        self.assertIn("max_world_anchor_reaction_magnitude_n", loaded.observed)

    def test_run_experiment_cli_writes_physical_pendulum_rbd_baseline_report(self) -> None:
        import json
        import os
        import subprocess
        import sys

        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "physical_pendulum_rbd_cli.json"
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/run_experiment.py",
                    "--lane",
                    "rbd_implicit_baseline",
                    "--config",
                    str(PHYSICAL_PENDULUM_CONFIG_PATH),
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

        self.assertEqual(summary["claim_id"], "experiment.single_body.physical_pendulum")
        self.assertEqual(summary["status"], "incomplete")
        self.assertEqual(summary["baseline_lane"], "rbd_implicit_baseline")
        self.assertEqual(summary["output_report"], output_path.as_posix())
        self.assertEqual(loaded.solver_mode, "physical_pendulum_scalar_implicit_rbd_development")
        self.assertEqual(loaded.observed["required_missing_lanes"], ["mabd_newton"])

    def test_run_experiment_cli_writes_physical_pendulum_comparison_report(self) -> None:
        import json
        import os
        import subprocess
        import sys

        with TemporaryDirectory() as tmpdir:
            analytic_path, mabd_path, rbd_path = self._write_physical_pendulum_lane_inputs(tmpdir)
            output_path = Path(tmpdir) / "physical_pendulum_comparison_cli.json"
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/run_experiment.py",
                    "--lane",
                    "physical_pendulum_comparison",
                    "--config",
                    str(PHYSICAL_PENDULUM_CONFIG_PATH),
                    "--matrix",
                    str(MATRIX_PATH),
                    "--analytic-report",
                    str(analytic_path),
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

        self.assertEqual(summary["claim_id"], "experiment.single_body.physical_pendulum")
        self.assertEqual(summary["status"], "incomplete")
        self.assertEqual(summary["baseline_lane"], "physical_pendulum_comparison_protocol")
        self.assertEqual(summary["output_report"], output_path.as_posix())
        self.assertEqual(loaded.source_commit, "cli-source")
        self.assertEqual(loaded.vendored_newton_commit, "cli-newton")
        self.assertEqual(
            loaded.observed["input_report_provenance"]["analytic_reference"]["source_commit"],
            "test-source",
        )

    def test_run_experiment_cli_writes_t_handle_rk4_reference_report(self) -> None:
        import json
        import os
        import subprocess
        import sys

        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "t_handle_rk4_reference_cli.json"
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/run_experiment.py",
                    "--lane",
                    "t_handle_rk4_reference",
                    "--config",
                    str(T_HANDLE_CONFIG_PATH),
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

        self.assertEqual(summary["claim_id"], "experiment.single_body.t_handle")
        self.assertEqual(summary["status"], "incomplete")
        self.assertEqual(summary["baseline_lane"], "rbd_rk4_reference")
        self.assertEqual(summary["output_report"], output_path.as_posix())
        self.assertEqual(loaded.solver_mode, "t_handle_torque_free_rk4_reference")
        self.assertEqual(loaded.observed["lane_status"], "diagnostic_generated")

    def test_run_experiment_cli_writes_heavy_top_rk4_reference_report(self) -> None:
        import json
        import os
        import subprocess
        import sys

        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "heavy_top_rk4_reference_cli.json"
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/run_experiment.py",
                    "--lane",
                    "heavy_top_rk4_reference",
                    "--config",
                    str(HEAVY_TOP_CONFIG_PATH),
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

        self.assertEqual(summary["claim_id"], "experiment.single_body.heavy_top")
        self.assertEqual(summary["status"], "incomplete")
        self.assertEqual(summary["baseline_lane"], "rbd_rk4_reference")
        self.assertEqual(summary["output_report"], output_path.as_posix())
        self.assertEqual(loaded.solver_mode, "heavy_top_rk4_reference_diagnostic")
        self.assertEqual(loaded.observed["lane_status"], "diagnostic_generated")

    def test_run_experiment_cli_physical_pendulum_comparison_requires_input_reports(self) -> None:
        import os
        import subprocess
        import sys

        with TemporaryDirectory() as tmpdir:
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/run_experiment.py",
                    "--lane",
                    "physical_pendulum_comparison",
                    "--config",
                    str(PHYSICAL_PENDULUM_CONFIG_PATH),
                    "--matrix",
                    str(MATRIX_PATH),
                    "--output",
                    str(Path(tmpdir) / "physical_pendulum_comparison.json"),
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
        self.assertIn(
            "physical_pendulum_comparison requires --analytic-report, --mabd-report, and --rbd-report",
            result.stderr,
        )

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
