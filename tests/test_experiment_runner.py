from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import yaml

from mabd_reproduction.reporting import ClaimReport, EvidenceStatus, load_claim_report


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs/experiments/single_body_spinning_box.yaml"
HEAVY_TOP_CONFIG_PATH = ROOT / "configs/experiments/single_body_heavy_top.yaml"
PHYSICAL_PENDULUM_CONFIG_PATH = ROOT / "configs/experiments/single_body_physical_pendulum.yaml"
ROLLING_SPINNING_CONFIG_PATH = ROOT / "configs/experiments/single_body_rolling_spinning.yaml"
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

    def _write_short_spinning_box_model_plane_config(self, tmpdir: str) -> Path:
        config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
        config["paper_horizon"]["duration_s"] = 0.02
        config["paper_horizon"]["sample_count"] = 3
        path = Path(tmpdir) / "single_body_spinning_box_short_model_plane.yaml"
        path.write_text(yaml.safe_dump(config), encoding="utf-8")
        return path

    def _write_short_spinning_box_contacts_input_config(self, tmpdir: str) -> Path:
        config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
        config["paper_horizon"]["duration_s"] = 0.02
        config["paper_horizon"]["sample_count"] = 3
        path = Path(tmpdir) / "single_body_spinning_box_short_contacts_input.yaml"
        path.write_text(yaml.safe_dump(config), encoding="utf-8")
        return path

    def _write_short_spinning_box_affine_static_plane_contacts_config(self, tmpdir: str) -> Path:
        config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
        config["paper_horizon"]["duration_s"] = 0.02
        config["paper_horizon"]["sample_count"] = 3
        path = Path(tmpdir) / "single_body_spinning_box_short_affine_static_plane_contacts.yaml"
        path.write_text(yaml.safe_dump(config), encoding="utf-8")
        return path

    def _write_short_rolling_spinning_rbd_config(self, tmpdir: str) -> Path:
        config = yaml.safe_load(ROLLING_SPINNING_CONFIG_PATH.read_text(encoding="utf-8"))
        config["rbd_implicit_baseline"]["step_count"] = 4
        config["rbd_implicit_baseline"]["sample_count"] = 3
        path = Path(tmpdir) / "single_body_rolling_spinning_short_rbd.yaml"
        path.write_text(yaml.safe_dump(config), encoding="utf-8")
        return path

    def _write_short_rolling_spinning_rbd_explicit_config(self, tmpdir: str) -> Path:
        config = yaml.safe_load(ROLLING_SPINNING_CONFIG_PATH.read_text(encoding="utf-8"))
        config["rbd_explicit_baseline"] = dict(config["rbd_implicit_baseline"])
        config["rbd_explicit_baseline"]["output_report"] = (
            "reports/experiment_matrix/single_body_rolling_spinning_rbd_explicit_baseline.json"
        )
        config["rbd_explicit_baseline"]["step_count"] = 4
        config["rbd_explicit_baseline"]["sample_count"] = 3
        path = Path(tmpdir) / "single_body_rolling_spinning_short_rbd_explicit.yaml"
        path.write_text(yaml.safe_dump(config), encoding="utf-8")
        return path

    def _write_short_rolling_spinning_mabd_newton_config(self, tmpdir: str) -> Path:
        config = yaml.safe_load(ROLLING_SPINNING_CONFIG_PATH.read_text(encoding="utf-8"))
        config["mabd_newton"]["step_count"] = 4
        config["mabd_newton"]["sample_count"] = 3
        path = Path(tmpdir) / "single_body_rolling_spinning_short_mabd_newton.yaml"
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

    def _write_heavy_top_lane_inputs(self, tmpdir: str) -> tuple[Path, Path]:
        from mabd_reproduction.experiment_configs import load_heavy_top_config
        from mabd_reproduction.heavy_top_reports import (
            write_heavy_top_mabd_newton_report,
            write_heavy_top_rk4_reference_report,
        )

        config = load_heavy_top_config(HEAVY_TOP_CONFIG_PATH)
        rk4_path = Path(tmpdir) / "heavy_top_rk4.json"
        mabd_path = Path(tmpdir) / "heavy_top_mabd.json"
        write_heavy_top_rk4_reference_report(
            rk4_path,
            config=config,
            source_commit="test-source",
            vendored_newton_commit="test-newton",
        )
        write_heavy_top_mabd_newton_report(
            mabd_path,
            config=config,
            source_commit="test-source",
            vendored_newton_commit="test-newton",
        )
        return rk4_path, mabd_path

    def _write_t_handle_lane_inputs(self, tmpdir: str) -> tuple[Path, Path]:
        from mabd_reproduction.experiment_configs import load_t_handle_config
        from mabd_reproduction.t_handle_reports import (
            write_t_handle_mabd_newton_report,
            write_t_handle_rk4_reference_report,
        )

        config = load_t_handle_config(T_HANDLE_CONFIG_PATH)
        rk4_path = Path(tmpdir) / "t_handle_rk4.json"
        mabd_path = Path(tmpdir) / "t_handle_mabd.json"
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
        return rk4_path, mabd_path

    def _assert_physical_pendulum_timing_source_audit(self, payload: dict[str, object]) -> None:
        self.assertEqual(payload["source_lines"], PHYSICAL_PENDULUM_TIMING_SOURCE_LINES)
        self.assertEqual(payload["status"], "not_a_physical_pendulum_paper_metric")
        self.assertFalse(payload["runtime_timing_claim_present"])
        self.assertFalse(payload["required_metric"])

    def _fake_heavy_top_paper_horizon_report(self) -> ClaimReport:
        return ClaimReport(
            claim_id="experiment.single_body.heavy_top",
            scene_id="single_body_heavy_top",
            asset_hashes={"heavy_top_procedural": "not_applicable_procedural"},
            solver_mode="mabd_cpu_oracle_heavy_top_newton_lane",
            backend="cpu_numpy_newton_only",
            baseline_lane="mabd_newton",
            expected={"full_experiment_claim_passed": False},
            observed={
                "full_experiment_claim_passed": False,
                "lane_status": "incomplete_diagnostic_failed",
                "mabd_diagnostic_scope": "paper_horizon_sample_grid",
                "step_count": 10000,
                "sample_count": 11,
            },
            threshold={},
            unit="angle_deg",
            status=EvidenceStatus.INCOMPLETE,
            failure_reason="test fake incomplete heavy-top paper-horizon report",
            timing_distribution={"status": "not_measured"},
            raw_outputs={},
            plot_paths={},
            source_commit="test-source",
            vendored_newton_commit="test-newton",
            paper_source_version="2603.08079v2",
        )

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

    def test_run_rolling_spinning_protocol_writes_configured_report(self) -> None:
        from mabd_reproduction.experiment_runner import run_rolling_spinning_protocol

        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            result = run_rolling_spinning_protocol(
                config_path=ROLLING_SPINNING_CONFIG_PATH,
                matrix_path=MATRIX_PATH,
                output_root=root,
                source_commit="test-source",
                vendored_newton_commit="test-newton",
            )
            loaded = load_claim_report(result.report_path)

        self.assertEqual(
            result.report_path,
            root / "reports/experiment_matrix/single_body_rolling_spinning.json",
        )
        self.assertEqual(result.claim_id, "experiment.single_body.rolling_spinning")
        self.assertEqual(result.status, EvidenceStatus.INCOMPLETE)
        self.assertEqual(loaded.baseline_lane, "mabd_newton")
        self.assertEqual(loaded.solver_mode, "rolling_spinning_protocol_audit")
        self.assertEqual(loaded.backend, "report_protocol")
        self.assertFalse(loaded.observed["local_runtime_measured"])
        self.assertIn("rbd_implicit_baseline", loaded.observed["required_lanes_missing"])
        self.assertIn("rbd_explicit_baseline", loaded.observed["required_lanes_missing"])
        self.assertIn("rolling_cylinder_runtime_not_measured", loaded.observed["blocking_reasons"])
        self.assertEqual(
            loaded.observed["paper_metric_statuses"]["total_simulation_time_ms"],
            "paper_reference_recorded_no_local_runtime",
        )
        self.assertEqual(
            loaded.observed["paper_metric_statuses"]["linear_momentum_error"],
            "not_measured_by_phase73",
        )
        self.assertEqual(
            loaded.observed["paper_metric_statuses"]["angular_momentum_error"],
            "not_measured_by_phase73",
        )
        self.assertEqual(
            loaded.observed["paper_metric_statuses"]["energy_drift"],
            "not_measured_by_phase73",
        )
        self.assertEqual(loaded.timing_distribution["status"], "not_measured")
        self.assertFalse(loaded.timing_distribution["paper_comparable"])
        self.assertEqual(loaded.threshold["total_simulation_time_ms"], 0.0)

    def test_run_rolling_spinning_protocol_rejects_ambiguous_output_selection(self) -> None:
        from mabd_reproduction.experiment_runner import run_rolling_spinning_protocol

        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            with self.assertRaisesRegex(ValueError, "output_path and output_root"):
                run_rolling_spinning_protocol(
                    config_path=ROLLING_SPINNING_CONFIG_PATH,
                    matrix_path=MATRIX_PATH,
                    output_path=root / "report.json",
                    output_root=root,
                    source_commit="test-source",
                    vendored_newton_commit="test-newton",
                )

    def test_run_rolling_spinning_rbd_implicit_baseline_writes_newton_report(
        self,
    ) -> None:
        from mabd_reproduction.experiment_runner import (
            run_rolling_spinning_rbd_implicit_baseline,
        )

        with TemporaryDirectory() as tmpdir:
            config_path = self._write_short_rolling_spinning_rbd_config(tmpdir)
            output_path = Path(tmpdir) / "rolling_spinning_rbd.json"
            result = run_rolling_spinning_rbd_implicit_baseline(
                config_path=config_path,
                matrix_path=MATRIX_PATH,
                output_path=output_path,
                source_commit="test-source",
                vendored_newton_commit="test-newton",
            )
            loaded = load_claim_report(result.report_path)

        self.assertEqual(result.claim_id, "experiment.single_body.rolling_spinning")
        self.assertEqual(result.status, EvidenceStatus.INCOMPLETE)
        self.assertEqual(loaded.baseline_lane, "rbd_implicit_baseline")
        self.assertEqual(
            loaded.solver_mode,
            "newton_semimplicit_rolling_cylinder_rbd_cpu_development",
        )
        self.assertEqual(loaded.backend, "cpu_newton_warp")
        self.assertTrue(loaded.observed["local_runtime_measured"])
        self.assertFalse(loaded.observed["paper_comparable"])
        self.assertFalse(loaded.observed["full_experiment_claim_passed"])
        self.assertEqual(
            loaded.observed["required_lanes_missing"],
            ["rbd_explicit_baseline", "mabd_newton", "paper_comparable_timing"],
        )
        self.assertIn(
            "rbd_explicit_baseline_missing",
            loaded.observed["blocking_reasons"],
        )
        self.assertIn(
            "mabd_rolling_cylinder_lane_missing",
            loaded.observed["blocking_reasons"],
        )
        self.assertIn(
            "paper_comparable_timing_missing",
            loaded.observed["blocking_reasons"],
        )
        self.assertIn(
            "newton_semimplicit_not_paper_implicit_rbd_solver",
            loaded.observed["blocking_reasons"],
        )
        self.assertEqual(loaded.observed["newton_device"], "cpu")
        self.assertEqual(loaded.observed["cylinder_axis_world"], [0.0, 0.0, 1.0])
        self.assertEqual(
            set(loaded.observed["newton_api"]),
            {
                "ModelBuilder.add_shape_cylinder",
                "ModelBuilder.add_ground_plane",
                "Model.contacts",
                "Model.collide",
                "SolverSemiImplicit",
            },
        )
        self.assertEqual(loaded.observed["step_count"], 4)
        self.assertEqual(loaded.observed["time_step_s"], 0.01)
        contact_summary = loaded.observed["contact_count_summary"]
        self.assertGreaterEqual(contact_summary["max"], 1)
        for key in ("initial", "final", "min", "max"):
            self.assertIsInstance(contact_summary[key], int)
            self.assertGreaterEqual(contact_summary[key], 0)
        self.assertGreaterEqual(loaded.observed["max_center_penetration_m"], 0.0)
        self.assertEqual(
            set(loaded.observed["contact_material"]),
            {"ke", "kd", "kf", "mu", "gap"},
        )
        self.assertGreater(loaded.timing_distribution["total_wall_time_ms"], 0.0)
        self.assertFalse(loaded.timing_distribution["paper_comparable"])
        self.assertEqual(loaded.raw_outputs["time_series"], "not_written")

    def test_run_rolling_spinning_rbd_explicit_baseline_writes_newton_report(
        self,
    ) -> None:
        from mabd_reproduction.experiment_runner import (
            run_rolling_spinning_rbd_explicit_baseline,
        )

        with TemporaryDirectory() as tmpdir:
            config_path = self._write_short_rolling_spinning_rbd_explicit_config(tmpdir)
            output_path = Path(tmpdir) / "rolling_spinning_rbd_explicit.json"
            result = run_rolling_spinning_rbd_explicit_baseline(
                config_path=config_path,
                matrix_path=MATRIX_PATH,
                output_path=output_path,
                source_commit="test-source",
                vendored_newton_commit="test-newton",
            )
            loaded = load_claim_report(result.report_path)

        self.assertEqual(result.claim_id, "experiment.single_body.rolling_spinning")
        self.assertEqual(result.status, EvidenceStatus.INCOMPLETE)
        self.assertEqual(loaded.baseline_lane, "rbd_explicit_baseline")
        self.assertEqual(
            loaded.solver_mode,
            "newton_explicit_euler_rolling_cylinder_rbd_cpu_development",
        )
        self.assertEqual(loaded.backend, "cpu_newton_warp")
        self.assertTrue(loaded.observed["local_runtime_measured"])
        self.assertFalse(loaded.observed["paper_comparable"])
        self.assertFalse(loaded.observed["full_experiment_claim_passed"])
        self.assertEqual(
            loaded.observed["required_lanes_missing"],
            ["mabd_newton", "paper_comparable_timing"],
        )
        self.assertIn(
            "mabd_rolling_cylinder_lane_missing",
            loaded.observed["blocking_reasons"],
        )
        self.assertIn(
            "paper_comparable_timing_missing",
            loaded.observed["blocking_reasons"],
        )
        self.assertIn(
            "newton_explicit_euler_not_paper_explicit_rbd_solver",
            loaded.observed["blocking_reasons"],
        )
        self.assertEqual(loaded.observed["newton_device"], "cpu")
        self.assertIn("SolverExplicitEuler", loaded.observed["newton_api"])
        self.assertEqual(loaded.observed["step_count"], 4)
        self.assertEqual(loaded.observed["time_step_s"], 0.01)
        self.assertEqual(
            set(loaded.observed["contact_material"]),
            {"ke", "kd", "kf", "mu", "gap"},
        )
        self.assertGreater(loaded.timing_distribution["total_wall_time_ms"], 0.0)
        self.assertFalse(loaded.timing_distribution["paper_comparable"])
        self.assertEqual(loaded.raw_outputs["time_series"], "not_written")

    def test_run_rolling_spinning_mabd_newton_writes_diagnostic_report(
        self,
    ) -> None:
        from mabd_reproduction.experiment_runner import run_rolling_spinning_mabd_newton

        with TemporaryDirectory() as tmpdir:
            config_path = self._write_short_rolling_spinning_mabd_newton_config(tmpdir)
            output_path = Path(tmpdir) / "rolling_spinning_mabd_newton.json"
            result = run_rolling_spinning_mabd_newton(
                config_path=config_path,
                matrix_path=MATRIX_PATH,
                output_path=output_path,
                source_commit="test-source",
                vendored_newton_commit="test-newton",
            )
            loaded = load_claim_report(result.report_path)

        self.assertEqual(result.claim_id, "experiment.single_body.rolling_spinning")
        self.assertEqual(result.status, EvidenceStatus.INCOMPLETE)
        self.assertEqual(loaded.baseline_lane, "mabd_newton")
        self.assertEqual(
            loaded.solver_mode,
            "mabd_cpu_oracle_rolling_cylinder_newton_lane",
        )
        self.assertEqual(loaded.backend, "cpu_numpy_newton_solver_mabd_static_plane_contacts")
        self.assertTrue(loaded.observed["local_runtime_measured"])
        self.assertFalse(loaded.observed["paper_comparable"])
        self.assertFalse(loaded.observed["full_experiment_claim_passed"])
        self.assertEqual(loaded.observed["required_lanes_missing"], ["paper_comparable_timing"])
        self.assertIn(
            "mabd_rolling_cylinder_report_incomplete",
            loaded.observed["blocking_reasons"],
        )
        self.assertIn(
            "paper_faithful_mabd_collision_missing",
            loaded.observed["blocking_reasons"],
        )
        self.assertIn(
            "paper_faithful_explicit_rbd_baseline_missing",
            loaded.observed["blocking_reasons"],
        )
        self.assertIn(
            "paper_comparable_timing_missing",
            loaded.observed["blocking_reasons"],
        )
        self.assertEqual(loaded.observed["newton_device"], "cpu")
        self.assertEqual(
            loaded.observed["solver_scope"],
            "mabd_affine_cylinder_static_plane_diagnostic_not_paper_faithful",
        )
        self.assertEqual(loaded.observed["step_count"], 4)
        self.assertEqual(loaded.observed["time_step_s"], 0.01)
        contact_summary = loaded.observed["contact_count_summary"]
        self.assertGreaterEqual(contact_summary["max"], 1)
        for key in ("initial", "final", "min", "max"):
            self.assertIsInstance(contact_summary[key], int)
            self.assertGreaterEqual(contact_summary[key], 0)
        self.assertEqual(
            loaded.observed["static_plane_collision_policy"],
            "mabd_affine_cylinder_static_plane_support_diagnostic",
        )
        self.assertEqual(loaded.observed["static_plane_cylinder_shape_count"], 1)
        self.assertGreaterEqual(loaded.observed["max_affine_shape_spread_m"], 0.0)
        self.assertGreater(loaded.timing_distribution["total_wall_time_ms"], 0.0)
        self.assertFalse(loaded.timing_distribution["paper_comparable"])
        self.assertEqual(loaded.raw_outputs["time_series"], "not_written")

    def test_run_experiment_cli_runs_rolling_spinning_protocol_lane(self) -> None:
        import json
        import subprocess
        import sys

        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "rolling_spinning.json"
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/run_experiment.py",
                    "--lane",
                    "rolling_spinning_protocol",
                    "--config",
                    str(ROLLING_SPINNING_CONFIG_PATH),
                    "--matrix",
                    str(MATRIX_PATH),
                    "--output",
                    str(output_path),
                    "--source-commit",
                    "test-source",
                    "--vendored-newton-commit",
                    "test-newton",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["claim_id"], "experiment.single_body.rolling_spinning")
        self.assertEqual(payload["status"], "incomplete")
        self.assertEqual(payload["baseline_lane"], "mabd_newton")

    def test_run_experiment_cli_runs_rolling_spinning_rbd_implicit_baseline_lane(
        self,
    ) -> None:
        import json
        import subprocess
        import sys

        with TemporaryDirectory() as tmpdir:
            config_path = self._write_short_rolling_spinning_rbd_config(tmpdir)
            output_path = Path(tmpdir) / "rolling_spinning_rbd.json"
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/run_experiment.py",
                    "--lane",
                    "rolling_spinning_rbd_implicit_baseline",
                    "--config",
                    str(config_path),
                    "--matrix",
                    str(MATRIX_PATH),
                    "--output",
                    str(output_path),
                    "--source-commit",
                    "test-source",
                    "--vendored-newton-commit",
                    "test-newton",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["claim_id"], "experiment.single_body.rolling_spinning")
        self.assertEqual(payload["status"], "incomplete")
        self.assertEqual(payload["baseline_lane"], "rbd_implicit_baseline")

    def test_run_experiment_cli_runs_rolling_spinning_rbd_explicit_baseline_lane(
        self,
    ) -> None:
        import json
        import subprocess
        import sys

        with TemporaryDirectory() as tmpdir:
            config_path = self._write_short_rolling_spinning_rbd_explicit_config(tmpdir)
            output_path = Path(tmpdir) / "rolling_spinning_rbd_explicit.json"
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/run_experiment.py",
                    "--lane",
                    "rolling_spinning_rbd_explicit_baseline",
                    "--config",
                    str(config_path),
                    "--matrix",
                    str(MATRIX_PATH),
                    "--output",
                    str(output_path),
                    "--source-commit",
                    "test-source",
                    "--vendored-newton-commit",
                    "test-newton",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["claim_id"], "experiment.single_body.rolling_spinning")
        self.assertEqual(payload["status"], "incomplete")
        self.assertEqual(payload["baseline_lane"], "rbd_explicit_baseline")

    def test_run_experiment_cli_runs_rolling_spinning_mabd_newton_lane(
        self,
    ) -> None:
        import json
        import subprocess
        import sys

        with TemporaryDirectory() as tmpdir:
            config_path = self._write_short_rolling_spinning_mabd_newton_config(tmpdir)
            output_path = Path(tmpdir) / "rolling_spinning_mabd_newton.json"
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/run_experiment.py",
                    "--lane",
                    "rolling_spinning_mabd_newton",
                    "--config",
                    str(config_path),
                    "--matrix",
                    str(MATRIX_PATH),
                    "--output",
                    str(output_path),
                    "--source-commit",
                    "test-source",
                    "--vendored-newton-commit",
                    "test-newton",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["claim_id"], "experiment.single_body.rolling_spinning")
        self.assertEqual(payload["status"], "incomplete")
        self.assertEqual(payload["baseline_lane"], "mabd_newton")

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

    def test_run_spinning_box_contact_response_writes_explicit_output_report(self) -> None:
        from mabd_reproduction.experiment_runner import run_spinning_box_contact_response

        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "contact_response.json"
            result = run_spinning_box_contact_response(
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
        self.assertEqual(loaded.solver_mode, "mabd_cpu_oracle_contact_response_diagnostic")
        self.assertEqual(
            loaded.observed["contact_response_policy"],
            "explicit_current_state_penalty_force_as_external_force_next_step",
        )
        self.assertNotIn("lane_gate_status", loaded.observed)

    def test_run_spinning_box_contact_response_requires_explicit_output(self) -> None:
        from mabd_reproduction.experiment_runner import run_spinning_box_contact_response

        with TemporaryDirectory() as tmpdir:
            with self.assertRaisesRegex(ValueError, "spinning_box_contact_response requires --output"):
                run_spinning_box_contact_response(
                    config_path=CONFIG_PATH,
                    matrix_path=MATRIX_PATH,
                    output_root=Path(tmpdir),
                    source_commit="test-source",
                    vendored_newton_commit="test-newton",
                )

    def test_run_spinning_box_normal_constraint_writes_explicit_output_report(self) -> None:
        from mabd_reproduction.experiment_runner import run_spinning_box_normal_constraint

        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "normal_constraint.json"
            result = run_spinning_box_normal_constraint(
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
        self.assertEqual(
            loaded.solver_mode,
            "mabd_cpu_oracle_point_plane_normal_constraint_diagnostic",
        )
        self.assertEqual(
            loaded.observed["contact_constraint_policy"],
            "free_predict_then_active_point_plane_normal_constraints",
        )
        self.assertNotIn("lane_gate_status", loaded.observed)

    def test_run_spinning_box_normal_constraint_requires_explicit_output(self) -> None:
        from mabd_reproduction.experiment_runner import run_spinning_box_normal_constraint

        with TemporaryDirectory() as tmpdir:
            with self.assertRaisesRegex(ValueError, "spinning_box_normal_constraint requires --output"):
                run_spinning_box_normal_constraint(
                    config_path=CONFIG_PATH,
                    matrix_path=MATRIX_PATH,
                    output_root=Path(tmpdir),
                    source_commit="test-source",
                    vendored_newton_commit="test-newton",
                )

    def test_run_spinning_box_model_plane_constraint_writes_explicit_output_report(self) -> None:
        from mabd_reproduction.experiment_runner import run_spinning_box_model_plane_constraint

        with TemporaryDirectory() as tmpdir:
            config_path = self._write_short_spinning_box_model_plane_config(tmpdir)
            output_path = Path(tmpdir) / "model_plane_constraint.json"
            result = run_spinning_box_model_plane_constraint(
                config_path=config_path,
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
        self.assertEqual(loaded.source_commit, "test-source")
        self.assertEqual(loaded.vendored_newton_commit, "test-newton")
        self.assertEqual(loaded.solver_mode, "solver_mabd_model_plane_constraint_diagnostic")
        self.assertEqual(loaded.backend, "cpu_numpy_newton_solver_mabd_model_rows")
        self.assertEqual(
            loaded.observed["model_plane_constraint_config_source"],
            "mabd:plane_constraint_custom_rows",
        )
        self.assertNotIn("lane_gate_status", loaded.observed)

    def test_run_spinning_box_model_plane_constraint_requires_explicit_output(self) -> None:
        from mabd_reproduction.experiment_runner import run_spinning_box_model_plane_constraint

        with TemporaryDirectory() as tmpdir:
            config_path = self._write_short_spinning_box_model_plane_config(tmpdir)
            with self.assertRaisesRegex(
                ValueError,
                "spinning_box_model_plane_constraint requires --output",
            ):
                run_spinning_box_model_plane_constraint(
                    config_path=config_path,
                    matrix_path=MATRIX_PATH,
                    output_root=Path(tmpdir),
                    source_commit="test-source",
                    vendored_newton_commit="test-newton",
                )

    def test_run_spinning_box_contacts_input_writes_explicit_output_report(self) -> None:
        from mabd_reproduction.experiment_runner import run_spinning_box_contacts_input

        with TemporaryDirectory() as tmpdir:
            config_path = self._write_short_spinning_box_contacts_input_config(tmpdir)
            output_path = Path(tmpdir) / "contacts_input.json"
            result = run_spinning_box_contacts_input(
                config_path=config_path,
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
        self.assertEqual(loaded.source_commit, "test-source")
        self.assertEqual(loaded.vendored_newton_commit, "test-newton")
        self.assertEqual(loaded.solver_mode, "solver_mabd_contacts_input_diagnostic")
        self.assertEqual(
            loaded.backend,
            "cpu_numpy_newton_solver_mabd_contacts_input_diagnostic",
        )
        self.assertEqual(
            loaded.observed["contacts_input_source"],
            "newton.Contacts.rigid_contact_static_plane_rows_from_diagnostic_corners",
        )
        self.assertEqual(
            loaded.observed["contacts_input_summary_source"],
            "last_contacts_input_summary",
        )
        self.assertIn(
            "spinning_box_contacts_input_not_paper_faithful",
            loaded.observed["blocking_reasons"],
        )
        self.assertNotIn("lane_gate_status", loaded.observed)

    def test_run_spinning_box_contacts_input_requires_explicit_output(self) -> None:
        from mabd_reproduction.experiment_runner import run_spinning_box_contacts_input

        with TemporaryDirectory() as tmpdir:
            config_path = self._write_short_spinning_box_contacts_input_config(tmpdir)
            with self.assertRaisesRegex(
                ValueError,
                "spinning_box_contacts_input requires --output",
            ):
                run_spinning_box_contacts_input(
                    config_path=config_path,
                    matrix_path=MATRIX_PATH,
                    output_root=Path(tmpdir),
                    source_commit="test-source",
                    vendored_newton_commit="test-newton",
                )

    def test_run_spinning_box_affine_static_plane_contacts_writes_explicit_output_report(self) -> None:
        from mabd_reproduction.experiment_runner import (
            run_spinning_box_affine_static_plane_contacts,
        )

        with TemporaryDirectory() as tmpdir:
            config_path = self._write_short_spinning_box_affine_static_plane_contacts_config(tmpdir)
            output_path = Path(tmpdir) / "affine_static_plane_contacts.json"
            result = run_spinning_box_affine_static_plane_contacts(
                config_path=config_path,
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
        self.assertEqual(loaded.source_commit, "test-source")
        self.assertEqual(loaded.vendored_newton_commit, "test-newton")
        self.assertEqual(
            loaded.solver_mode,
            "solver_mabd_affine_static_plane_contacts_diagnostic",
        )
        self.assertEqual(
            loaded.backend,
            "cpu_numpy_newton_solver_mabd_affine_static_plane_contacts_diagnostic",
        )
        self.assertEqual(
            loaded.observed["affine_static_plane_contact_source"],
            "SolverMABD.detect_static_plane_contacts",
        )
        self.assertNotIn("lane_gate_status", loaded.observed)

    def test_run_spinning_box_affine_static_plane_contacts_requires_explicit_output(self) -> None:
        from mabd_reproduction.experiment_runner import (
            run_spinning_box_affine_static_plane_contacts,
        )

        with TemporaryDirectory() as tmpdir:
            config_path = self._write_short_spinning_box_affine_static_plane_contacts_config(tmpdir)
            with self.assertRaisesRegex(
                ValueError,
                "spinning_box_affine_static_plane_contacts requires --output",
            ):
                run_spinning_box_affine_static_plane_contacts(
                    config_path=config_path,
                    matrix_path=MATRIX_PATH,
                    output_root=Path(tmpdir),
                    source_commit="test-source",
                    vendored_newton_commit="test-newton",
                )

    def test_run_spinning_box_decoupled_twist_writes_explicit_output_report(self) -> None:
        from mabd_reproduction.experiment_runner import run_spinning_box_decoupled_twist

        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "decoupled_twist.json"
            result = run_spinning_box_decoupled_twist(
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
        self.assertEqual(
            loaded.solver_mode,
            "decoupled_twist_rigid_reconstruction_diagnostic",
        )
        self.assertEqual(
            loaded.observed["velocity_semantics_policy"],
            "decoupled_spatial_twist_with_exponential_rigid_update",
        )
        self.assertNotIn("lane_gate_status", loaded.observed)

    def test_run_spinning_box_decoupled_twist_requires_explicit_output(self) -> None:
        from mabd_reproduction.experiment_runner import run_spinning_box_decoupled_twist

        with TemporaryDirectory() as tmpdir:
            with self.assertRaisesRegex(ValueError, "spinning_box_decoupled_twist requires --output"):
                run_spinning_box_decoupled_twist(
                    config_path=CONFIG_PATH,
                    matrix_path=MATRIX_PATH,
                    output_root=Path(tmpdir),
                    source_commit="test-source",
                    vendored_newton_commit="test-newton",
                )

    def test_run_spinning_box_figure_curves_writes_explicit_output_report(self) -> None:
        from mabd_reproduction.experiment_runner import run_spinning_box_figure_curves

        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "figure_curves.json"
            result = run_spinning_box_figure_curves(
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
        self.assertEqual(result.report.baseline_lane, "paper_figure_digitization")
        self.assertEqual(loaded.baseline_lane, "paper_figure_digitization")
        self.assertEqual(loaded.solver_mode, "spinning_box_paper_figure_curve_digitization")
        self.assertEqual(loaded.backend, "paper_pdf_digitization")
        self.assertTrue(loaded.observed["color_family_curve_available"])
        self.assertFalse(loaded.observed["paper_reference_legend_identity_available"])
        self.assertNotIn("lane_gate_status", loaded.observed)

    def test_run_spinning_box_figure_curves_requires_explicit_output(self) -> None:
        from mabd_reproduction.experiment_runner import run_spinning_box_figure_curves

        with TemporaryDirectory() as tmpdir:
            with self.assertRaisesRegex(ValueError, "spinning_box_figure_curves requires --output"):
                run_spinning_box_figure_curves(
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
        from mabd_reproduction.experiment_configs import load_spinning_box_config
        from mabd_reproduction.experiment_runner import run_spinning_box_comparison
        from mabd_reproduction.spinning_box_digitization import (
            write_spinning_box_figure_curve_report,
        )

        with TemporaryDirectory() as tmpdir:
            mabd_path, rbd_path = self._write_spinning_box_lane_inputs(tmpdir)
            config = load_spinning_box_config(CONFIG_PATH)
            figure_path = Path(tmpdir) / "figure_curves.json"
            write_spinning_box_figure_curve_report(
                figure_path,
                config=config,
                source_commit="test-source",
                vendored_newton_commit="test-newton",
            )
            output_path = Path(tmpdir) / "comparison.json"
            result = run_spinning_box_comparison(
                config_path=CONFIG_PATH,
                matrix_path=MATRIX_PATH,
                mabd_report_path=mabd_path,
                rbd_report_path=rbd_path,
                figure_curve_report_path=figure_path,
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
        self.assertTrue(loaded.observed["digitized_figure_reference_available"])
        self.assertEqual(loaded.raw_outputs["figure_curve_report"], figure_path.as_posix())

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
        self.assertIn("mabd_newton_report_incomplete", loaded.observed["blocking_reasons"])
        self.assertNotIn("mabd_newton_report_missing", loaded.observed["blocking_reasons"])
        self.assertIn("t_handle_comparison_report_incomplete", loaded.observed["blocking_reasons"])
        self.assertEqual(loaded.observed["required_missing_lanes"], [])
        self.assertNotIn("lane_gate_status", loaded.observed)

    def test_run_t_handle_mabd_newton_writes_incomplete_newton_diagnostic_report(self) -> None:
        from mabd_reproduction.experiment_runner import run_t_handle_mabd_newton

        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "t_handle_mabd_newton.json"
            result = run_t_handle_mabd_newton(
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
        self.assertEqual(loaded.solver_mode, "mabd_cpu_oracle_t_handle_newton_lane")
        self.assertEqual(loaded.backend, "cpu_numpy_newton_only")
        self.assertEqual(loaded.baseline_lane, "mabd_newton")
        self.assertEqual(loaded.observed["solver_model_config_source"], "newton_model_derived")
        self.assertEqual(
            loaded.observed["newton_model_derived_custom_frequencies"],
            ["mabd:body", "mabd:gravity"],
        )
        self.assertEqual(loaded.observed["step_count"], 4000)
        self.assertEqual(loaded.observed["sample_count"], 9)
        self.assertFalse(loaded.observed["full_experiment_claim_passed"])
        self.assertIn("exact_t_handle_geometry_unknown", loaded.observed["blocking_reasons"])
        self.assertIn(
            "raw_t_handle_reference_curve_data_missing",
            loaded.observed["blocking_reasons"],
        )
        self.assertIn("mabd_newton_report_incomplete", loaded.observed["blocking_reasons"])
        self.assertNotIn("mabd_newton_report_missing", loaded.observed["blocking_reasons"])
        self.assertIn("t_handle_comparison_report_incomplete", loaded.observed["blocking_reasons"])
        self.assertEqual(loaded.observed["required_missing_lanes"], [])
        self.assertNotIn("lane_gate_status", loaded.observed)

    def test_run_t_handle_figure_curves_writes_digitized_report(self) -> None:
        from mabd_reproduction.experiment_runner import run_t_handle_figure_curves

        with TemporaryDirectory() as tmpdir:
            result = run_t_handle_figure_curves(
                config_path=T_HANDLE_CONFIG_PATH,
                matrix_path=MATRIX_PATH,
                output_root=tmpdir,
                source_commit="test-source",
                vendored_newton_commit="test-newton",
            )
            loaded = load_claim_report(result.report_path)

        self.assertEqual(
            result.report_path,
            Path(tmpdir) / "reports/experiment_matrix/single_body_t_handle_figure_curves.json",
        )
        self.assertEqual(result.claim_id, "experiment.single_body.t_handle")
        self.assertEqual(result.status, EvidenceStatus.INCOMPLETE)
        self.assertEqual(result.report.baseline_lane, "paper_figure_digitization")
        self.assertEqual(loaded.baseline_lane, "paper_figure_digitization")
        self.assertEqual(loaded.solver_mode, "t_handle_paper_figure_digitization")
        self.assertEqual(loaded.backend, "pdftocairo_pillow")
        self.assertEqual(loaded.observed["lane_status"], "figure_color_families_digitized")
        self.assertFalse(loaded.observed["full_experiment_claim_passed"])
        self.assertTrue(loaded.observed["reference_curve_available"])

    def test_run_t_handle_comparison_writes_incomplete_protocol_report(self) -> None:
        from mabd_reproduction.experiment_runner import run_t_handle_comparison

        with TemporaryDirectory() as tmpdir:
            rk4_path, mabd_path = self._write_t_handle_lane_inputs(tmpdir)
            output_path = Path(tmpdir) / "t_handle_comparison.json"
            result = run_t_handle_comparison(
                config_path=T_HANDLE_CONFIG_PATH,
                matrix_path=MATRIX_PATH,
                rk4_report_path=rk4_path,
                mabd_report_path=mabd_path,
                output_path=output_path,
                source_commit="test-source",
                vendored_newton_commit="test-newton",
            )
            loaded = load_claim_report(output_path)

        self.assertEqual(result.report_path, output_path)
        self.assertEqual(result.claim_id, "experiment.single_body.t_handle")
        self.assertEqual(result.status, EvidenceStatus.INCOMPLETE)
        self.assertEqual(result.report.baseline_lane, "t_handle_comparison_protocol")
        self.assertEqual(loaded.solver_mode, "t_handle_multilane_comparison_development")
        self.assertEqual(loaded.backend, "report_protocol")
        self.assertIn(
            "t_handle_comparison_report_incomplete",
            loaded.observed["blocking_reasons"],
        )
        self.assertFalse(loaded.observed["full_experiment_claim_passed"])

    def test_run_t_handle_comparison_uses_configured_output_under_output_root(self) -> None:
        from mabd_reproduction.experiment_runner import run_t_handle_comparison

        with TemporaryDirectory() as tmpdir:
            rk4_path, mabd_path = self._write_t_handle_lane_inputs(tmpdir)
            output_root = Path(tmpdir) / "root"
            result = run_t_handle_comparison(
                config_path=T_HANDLE_CONFIG_PATH,
                matrix_path=MATRIX_PATH,
                rk4_report_path=rk4_path,
                mabd_report_path=mabd_path,
                output_root=output_root,
                source_commit="test-source",
                vendored_newton_commit="test-newton",
            )
            loaded = load_claim_report(result.report_path)

        self.assertEqual(
            result.report_path,
            output_root / "reports/experiment_matrix/single_body_t_handle_comparison.json",
        )
        self.assertEqual(loaded.baseline_lane, "t_handle_comparison_protocol")

    def test_run_t_handle_comparison_requires_lane_inputs(self) -> None:
        from mabd_reproduction.experiment_runner import run_t_handle_comparison

        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "t_handle_comparison.json"
            with self.assertRaisesRegex(
                ValueError,
                "t_handle_comparison requires --mabd-report and --rbd-report",
            ):
                run_t_handle_comparison(
                    config_path=T_HANDLE_CONFIG_PATH,
                    matrix_path=MATRIX_PATH,
                    output_path=output_path,
                    source_commit="test-source",
                    vendored_newton_commit="test-newton",
                )
            self.assertFalse(output_path.exists())

    def test_t_handle_mabd_report_rejects_nonfinite_rollout(self) -> None:
        from dataclasses import replace

        from mabd_reproduction.experiment_configs import load_t_handle_config
        from mabd_reproduction.t_handle_mabd import roll_out_t_handle_mabd_model_derived
        from mabd_reproduction.t_handle_reports import write_t_handle_mabd_newton_report

        config = load_t_handle_config(T_HANDLE_CONFIG_PATH)
        finite_rollout = roll_out_t_handle_mabd_model_derived(config)
        nonfinite_rollout = replace(
            finite_rollout,
            finite=False,
            relative_energy_drift=float("nan"),
        )

        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "t_handle_mabd_newton.json"
            with patch(
                "mabd_reproduction.t_handle_reports.roll_out_t_handle_mabd_model_derived",
                return_value=nonfinite_rollout,
            ):
                with self.assertRaisesRegex(ValueError, "finite"):
                    write_t_handle_mabd_newton_report(
                        output_path,
                        config=config,
                        source_commit="test-source",
                        vendored_newton_commit="test-newton",
                    )
            self.assertFalse(output_path.exists())

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
        self.assertIn("mabd_newton_report_incomplete", loaded.observed["blocking_reasons"])
        self.assertNotIn("mabd_newton_report_missing", loaded.observed["blocking_reasons"])
        self.assertIn("heavy_top_comparison_report_incomplete", loaded.observed["blocking_reasons"])
        self.assertIn("exact_heavy_top_geometry_unknown", loaded.observed["blocking_reasons"])
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

    def test_run_heavy_top_mabd_newton_writes_incomplete_model_derived_report(self) -> None:
        from mabd_reproduction.experiment_runner import run_heavy_top_mabd_newton

        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "heavy_top_mabd_newton.json"
            result = run_heavy_top_mabd_newton(
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
        self.assertEqual(loaded.baseline_lane, "mabd_newton")
        self.assertEqual(loaded.solver_mode, "mabd_cpu_oracle_heavy_top_newton_lane")
        self.assertEqual(loaded.backend, "cpu_numpy_newton_only")
        self.assertEqual(loaded.observed["lane_status"], "incomplete_diagnostic_generated")
        self.assertEqual(
            loaded.observed["solver_model_config_source"],
            "newton_model_derived",
        )
        self.assertEqual(
            loaded.observed["newton_model_derived_custom_frequencies"],
            ["mabd:body", "mabd:world_constraint", "mabd:gravity"],
        )
        self.assertFalse(loaded.observed["full_experiment_claim_passed"])
        self.assertNotIn("lane_gate_status", loaded.observed)
        self.assertIn("mabd_newton_report_incomplete", loaded.observed["blocking_reasons"])
        self.assertIn("exact_heavy_top_geometry_unknown", loaded.observed["blocking_reasons"])
        self.assertIn("heavy_top_comparison_report_incomplete", loaded.observed["blocking_reasons"])
        self.assertGreater(
            loaded.observed["max_nutation_angle_deg"] - loaded.observed["min_nutation_angle_deg"],
            0.0,
        )

    def test_run_heavy_top_mabd_paper_horizon_dispatches_configured_report(self) -> None:
        from mabd_reproduction import experiment_runner

        fake_report = self._fake_heavy_top_paper_horizon_report()
        with TemporaryDirectory() as tmpdir:
            with patch.object(
                experiment_runner,
                "write_heavy_top_mabd_paper_horizon_report",
                return_value=fake_report,
            ) as writer:
                result = experiment_runner.run_heavy_top_mabd_paper_horizon(
                    config_path=HEAVY_TOP_CONFIG_PATH,
                    matrix_path=MATRIX_PATH,
                    output_root=tmpdir,
                    source_commit="test-source",
                    vendored_newton_commit="test-newton",
                )

        self.assertEqual(
            result.report_path,
            Path(tmpdir)
            / "reports/experiment_matrix/single_body_heavy_top_mabd_paper_horizon.json",
        )
        self.assertEqual(result.claim_id, "experiment.single_body.heavy_top")
        self.assertEqual(result.status, EvidenceStatus.INCOMPLETE)
        self.assertEqual(result.report.observed["mabd_diagnostic_scope"], "paper_horizon_sample_grid")
        writer.assert_called_once()
        called_config = writer.call_args.kwargs["config"]
        self.assertEqual(called_config.mabd_paper_horizon.step_count, 10000)
        self.assertEqual(called_config.mabd_paper_horizon.sample_count, 11)

    def test_run_heavy_top_figure_curves_writes_digitized_report(self) -> None:
        from mabd_reproduction.experiment_runner import run_heavy_top_figure_curves

        with TemporaryDirectory() as tmpdir:
            result = run_heavy_top_figure_curves(
                config_path=HEAVY_TOP_CONFIG_PATH,
                matrix_path=MATRIX_PATH,
                output_root=tmpdir,
                source_commit="test-source",
                vendored_newton_commit="test-newton",
            )
            loaded = load_claim_report(result.report_path)

        self.assertEqual(
            result.report_path,
            Path(tmpdir) / "reports/experiment_matrix/single_body_heavy_top_figure_curves.json",
        )
        self.assertEqual(result.claim_id, "experiment.single_body.heavy_top")
        self.assertEqual(result.status, EvidenceStatus.INCOMPLETE)
        self.assertEqual(result.report.baseline_lane, "paper_figure_digitization")
        self.assertEqual(loaded.baseline_lane, "paper_figure_digitization")
        self.assertEqual(loaded.solver_mode, "heavy_top_paper_figure_digitization")
        self.assertEqual(loaded.backend, "pdftocairo_pillow")
        self.assertEqual(loaded.observed["lane_status"], "reference_curves_digitized")
        self.assertFalse(loaded.observed["full_experiment_claim_passed"])
        self.assertTrue(loaded.observed["reference_curve_available"])

    def test_run_heavy_top_comparison_writes_report(self) -> None:
        from mabd_reproduction.experiment_runner import run_heavy_top_comparison

        with TemporaryDirectory() as tmpdir:
            rk4_path, mabd_path = self._write_heavy_top_lane_inputs(tmpdir)
            result = run_heavy_top_comparison(
                config_path=HEAVY_TOP_CONFIG_PATH,
                matrix_path=MATRIX_PATH,
                rk4_report_path=rk4_path,
                mabd_report_path=mabd_path,
                output_root=tmpdir,
                source_commit="test-source",
                vendored_newton_commit="test-newton",
            )
            loaded = load_claim_report(result.report_path)

        self.assertEqual(
            result.report_path,
            Path(tmpdir) / "reports/experiment_matrix/single_body_heavy_top_comparison.json",
        )
        self.assertEqual(result.claim_id, "experiment.single_body.heavy_top")
        self.assertEqual(result.status, EvidenceStatus.INCOMPLETE)
        self.assertEqual(result.report.baseline_lane, "heavy_top_comparison_protocol")
        self.assertEqual(loaded.baseline_lane, "heavy_top_comparison_protocol")
        self.assertEqual(loaded.solver_mode, "heavy_top_multilane_comparison_development")
        self.assertEqual(loaded.observed["missing_required_lanes"], [])
        self.assertIn("input_report_provenance", loaded.observed)
        self.assertIn("sample_time_grid_mismatch", loaded.observed["blocking_reasons"])
        self.assertIn(
            "heavy_top_comparison_pass_gate_not_enabled",
            loaded.observed["blocking_reasons"],
        )
        self.assertEqual(
            loaded.observed["missing_paper_metrics"],
            ["nutation_angle_error:paper_reference_curve_missing"],
        )
        self.assertEqual(
            loaded.observed["paper_metric_statuses"]["precession_velocity_error"]["status"],
            "diagnostic_available",
        )
        self.assertEqual(
            loaded.observed["paper_metric_statuses"]["energy_drift"]["status"],
            "diagnostic_available",
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

    def test_run_experiment_cli_writes_spinning_box_contact_response_report(self) -> None:
        import json
        import os
        import subprocess
        import sys

        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "contact_response_cli_report.json"
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/run_experiment.py",
                    "--lane",
                    "spinning_box_contact_response",
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
        self.assertEqual(loaded.solver_mode, "mabd_cpu_oracle_contact_response_diagnostic")
        self.assertEqual(
            loaded.observed["contact_response_policy"],
            "explicit_current_state_penalty_force_as_external_force_next_step",
        )
        self.assertNotIn("lane_gate_status", loaded.observed)

    def test_run_experiment_cli_writes_spinning_box_normal_constraint_report(self) -> None:
        import json
        import os
        import subprocess
        import sys

        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "normal_constraint_cli_report.json"
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/run_experiment.py",
                    "--lane",
                    "spinning_box_normal_constraint",
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
        self.assertEqual(
            loaded.solver_mode,
            "mabd_cpu_oracle_point_plane_normal_constraint_diagnostic",
        )
        self.assertEqual(
            loaded.observed["contact_constraint_policy"],
            "free_predict_then_active_point_plane_normal_constraints",
        )
        self.assertNotIn("lane_gate_status", loaded.observed)

    def test_run_experiment_cli_writes_spinning_box_model_plane_constraint_report(self) -> None:
        import json
        import os
        import subprocess
        import sys

        with TemporaryDirectory() as tmpdir:
            config_path = self._write_short_spinning_box_model_plane_config(tmpdir)
            output_path = Path(tmpdir) / "model_plane_constraint_cli_report.json"
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/run_experiment.py",
                    "--lane",
                    "spinning_box_model_plane_constraint",
                    "--config",
                    str(config_path),
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
        self.assertEqual(loaded.source_commit, "cli-source")
        self.assertEqual(loaded.vendored_newton_commit, "cli-newton")
        self.assertEqual(loaded.solver_mode, "solver_mabd_model_plane_constraint_diagnostic")
        self.assertEqual(loaded.backend, "cpu_numpy_newton_solver_mabd_model_rows")
        self.assertNotIn("lane_gate_status", loaded.observed)

    def test_run_experiment_cli_rejects_model_plane_constraint_output_root(self) -> None:
        import os
        import subprocess
        import sys

        with TemporaryDirectory() as tmpdir:
            config_path = self._write_short_spinning_box_model_plane_config(tmpdir)
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/run_experiment.py",
                    "--lane",
                    "spinning_box_model_plane_constraint",
                    "--config",
                    str(config_path),
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
        self.assertIn("spinning_box_model_plane_constraint", result.stderr)
        self.assertIn("--output", result.stderr)

    def test_run_experiment_cli_writes_spinning_box_contacts_input_report(self) -> None:
        import json
        import os
        import subprocess
        import sys

        with TemporaryDirectory() as tmpdir:
            config_path = self._write_short_spinning_box_contacts_input_config(tmpdir)
            output_path = Path(tmpdir) / "contacts_input_cli_report.json"
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/run_experiment.py",
                    "--lane",
                    "spinning_box_contacts_input",
                    "--config",
                    str(config_path),
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
        self.assertEqual(loaded.source_commit, "cli-source")
        self.assertEqual(loaded.vendored_newton_commit, "cli-newton")
        self.assertEqual(loaded.solver_mode, "solver_mabd_contacts_input_diagnostic")
        self.assertEqual(
            loaded.backend,
            "cpu_numpy_newton_solver_mabd_contacts_input_diagnostic",
        )
        self.assertEqual(
            loaded.observed["contacts_input_policy"],
            "solver_mabd_contacts_input_free_predict_then_static_plane_constraints",
        )
        self.assertNotIn("lane_gate_status", loaded.observed)

    def test_run_experiment_cli_rejects_contacts_input_output_root(self) -> None:
        import os
        import subprocess
        import sys

        with TemporaryDirectory() as tmpdir:
            config_path = self._write_short_spinning_box_contacts_input_config(tmpdir)
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/run_experiment.py",
                    "--lane",
                    "spinning_box_contacts_input",
                    "--config",
                    str(config_path),
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
        self.assertIn("spinning_box_contacts_input", result.stderr)
        self.assertIn("--output", result.stderr)

    def test_run_experiment_cli_writes_spinning_box_affine_static_plane_contacts_report(self) -> None:
        import json
        import os
        import subprocess
        import sys

        with TemporaryDirectory() as tmpdir:
            config_path = self._write_short_spinning_box_affine_static_plane_contacts_config(tmpdir)
            output_path = Path(tmpdir) / "affine_static_plane_contacts_cli_report.json"
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/run_experiment.py",
                    "--lane",
                    "spinning_box_affine_static_plane_contacts",
                    "--config",
                    str(config_path),
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
        self.assertEqual(loaded.source_commit, "cli-source")
        self.assertEqual(loaded.vendored_newton_commit, "cli-newton")
        self.assertEqual(
            loaded.solver_mode,
            "solver_mabd_affine_static_plane_contacts_diagnostic",
        )
        self.assertEqual(
            loaded.observed["affine_static_plane_contact_source"],
            "SolverMABD.detect_static_plane_contacts",
        )
        self.assertNotIn("lane_gate_status", loaded.observed)

    def test_run_experiment_cli_rejects_affine_static_plane_contacts_output_root(self) -> None:
        import os
        import subprocess
        import sys

        with TemporaryDirectory() as tmpdir:
            config_path = self._write_short_spinning_box_affine_static_plane_contacts_config(tmpdir)
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/run_experiment.py",
                    "--lane",
                    "spinning_box_affine_static_plane_contacts",
                    "--config",
                    str(config_path),
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
        self.assertIn("spinning_box_affine_static_plane_contacts", result.stderr)
        self.assertIn("--output", result.stderr)

    def test_run_experiment_cli_writes_spinning_box_decoupled_twist_report(self) -> None:
        import json
        import os
        import subprocess
        import sys

        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "decoupled_twist_cli_report.json"
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/run_experiment.py",
                    "--lane",
                    "spinning_box_decoupled_twist",
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
        self.assertEqual(
            loaded.solver_mode,
            "decoupled_twist_rigid_reconstruction_diagnostic",
        )
        self.assertEqual(
            loaded.observed["velocity_semantics_policy"],
            "decoupled_spatial_twist_with_exponential_rigid_update",
        )
        self.assertNotIn("lane_gate_status", loaded.observed)

    def test_run_experiment_cli_writes_spinning_box_figure_curve_report(self) -> None:
        import json
        import os
        import subprocess
        import sys

        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "figure_curves_cli_report.json"
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/run_experiment.py",
                    "--lane",
                    "spinning_box_figure_curves",
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
        self.assertEqual(summary["baseline_lane"], "paper_figure_digitization")
        self.assertEqual(summary["output_report"], output_path.as_posix())
        self.assertEqual(loaded.solver_mode, "spinning_box_paper_figure_curve_digitization")
        self.assertEqual(loaded.backend, "paper_pdf_digitization")
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

    def test_run_experiment_cli_writes_t_handle_mabd_newton_report(self) -> None:
        import json
        import os
        import subprocess
        import sys

        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "t_handle_mabd_newton_cli.json"
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/run_experiment.py",
                    "--lane",
                    "t_handle_mabd_newton",
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
        self.assertEqual(summary["baseline_lane"], "mabd_newton")
        self.assertEqual(summary["output_report"], output_path.as_posix())
        self.assertEqual(loaded.solver_mode, "mabd_cpu_oracle_t_handle_newton_lane")
        self.assertEqual(loaded.observed["solver_model_config_source"], "newton_model_derived")

    def test_run_experiment_cli_writes_t_handle_figure_curve_report(self) -> None:
        import json
        import os
        import subprocess
        import sys

        with TemporaryDirectory() as tmpdir:
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/run_experiment.py",
                    "--lane",
                    "t_handle_figure_curves",
                    "--config",
                    str(T_HANDLE_CONFIG_PATH),
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

            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            summary = json.loads(result.stdout)
            output_path = (
                Path(tmpdir) / "reports/experiment_matrix/single_body_t_handle_figure_curves.json"
            )
            loaded = load_claim_report(output_path)

        self.assertEqual(summary["claim_id"], "experiment.single_body.t_handle")
        self.assertEqual(summary["status"], "incomplete")
        self.assertEqual(summary["baseline_lane"], "paper_figure_digitization")
        self.assertEqual(summary["output_report"], output_path.as_posix())
        self.assertEqual(loaded.source_commit, "cli-source")
        self.assertEqual(loaded.vendored_newton_commit, "cli-newton")
        self.assertEqual(loaded.observed["lane_status"], "figure_color_families_digitized")

    def test_run_experiment_cli_writes_t_handle_comparison_report(self) -> None:
        import json
        import os
        import subprocess
        import sys

        from mabd_reproduction.experiment_configs import load_t_handle_config
        from mabd_reproduction.t_handle_digitization import write_t_handle_figure_curve_report

        with TemporaryDirectory() as tmpdir:
            rk4_path, mabd_path = self._write_t_handle_lane_inputs(tmpdir)
            figure_path = Path(tmpdir) / "t_handle_figure_curves.json"
            config = load_t_handle_config(T_HANDLE_CONFIG_PATH)
            write_t_handle_figure_curve_report(
                figure_path,
                config=config,
                source_commit="test-source",
                vendored_newton_commit="test-newton",
                sample_count=51,
            )
            output_path = Path(tmpdir) / "t_handle_comparison_cli.json"
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/run_experiment.py",
                    "--lane",
                    "t_handle_comparison",
                    "--config",
                    str(T_HANDLE_CONFIG_PATH),
                    "--matrix",
                    str(MATRIX_PATH),
                    "--rbd-report",
                    str(rk4_path),
                    "--mabd-report",
                    str(mabd_path),
                    "--figure-report",
                    str(figure_path),
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
        self.assertEqual(summary["baseline_lane"], "t_handle_comparison_protocol")
        self.assertEqual(summary["output_report"], output_path.as_posix())
        self.assertEqual(loaded.solver_mode, "t_handle_multilane_comparison_development")
        self.assertIn("paper_figure_curves", loaded.observed["input_report_provenance"])
        self.assertEqual(
            loaded.observed["paper_metric_statuses"]["energy_loss"]["status"],
            "paper_figure_digitized_energy_loss_error_diagnostic_available_not_agreement",
        )
        self.assertTrue(loaded.observed["digitized_figure_curve_agreement_available"])

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

    def test_run_experiment_main_dispatches_heavy_top_mabd_paper_horizon_lane(self) -> None:
        import importlib.util
        import io
        import json
        from contextlib import redirect_stdout

        class FakeResult:
            def to_summary(self) -> dict[str, str]:
                return {
                    "claim_id": "experiment.single_body.heavy_top",
                    "scene_id": "single_body_heavy_top",
                    "status": "incomplete",
                    "output_report": "fake.json",
                    "baseline_lane": "mabd_newton",
                }

        script_path = ROOT / "scripts/run_experiment.py"
        spec = importlib.util.spec_from_file_location(
            "run_experiment_phase55_test",
            script_path,
        )
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with patch.object(
            module,
            "run_heavy_top_mabd_paper_horizon",
            return_value=FakeResult(),
        ) as runner:
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                code = module.main(
                    [
                        "--lane",
                        "heavy_top_mabd_paper_horizon",
                        "--config",
                        str(HEAVY_TOP_CONFIG_PATH),
                        "--matrix",
                        str(MATRIX_PATH),
                        "--output-root",
                        "unused-root",
                        "--source-commit",
                        "cli-source",
                        "--vendored-newton-commit",
                        "cli-newton",
                    ]
                )

        self.assertEqual(code, 0)
        summary = json.loads(stdout.getvalue())
        self.assertEqual(summary["claim_id"], "experiment.single_body.heavy_top")
        self.assertEqual(summary["baseline_lane"], "mabd_newton")
        runner.assert_called_once()
        self.assertEqual(
            runner.call_args.kwargs["output_root"],
            Path("unused-root"),
        )

    def test_run_experiment_cli_writes_heavy_top_figure_curve_report(self) -> None:
        import json
        import os
        import subprocess
        import sys

        with TemporaryDirectory() as tmpdir:
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/run_experiment.py",
                    "--lane",
                    "heavy_top_figure_curves",
                    "--config",
                    str(HEAVY_TOP_CONFIG_PATH),
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

            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            summary = json.loads(result.stdout)
            output_path = (
                Path(tmpdir) / "reports/experiment_matrix/single_body_heavy_top_figure_curves.json"
            )
            loaded = load_claim_report(output_path)

        self.assertEqual(summary["claim_id"], "experiment.single_body.heavy_top")
        self.assertEqual(summary["status"], "incomplete")
        self.assertEqual(summary["baseline_lane"], "paper_figure_digitization")
        self.assertEqual(summary["output_report"], output_path.as_posix())
        self.assertEqual(loaded.source_commit, "cli-source")
        self.assertEqual(loaded.vendored_newton_commit, "cli-newton")
        self.assertEqual(loaded.observed["lane_status"], "reference_curves_digitized")

    def test_run_experiment_cli_writes_heavy_top_comparison_report(self) -> None:
        import json
        import os
        import subprocess
        import sys

        with TemporaryDirectory() as tmpdir:
            rk4_path, mabd_path = self._write_heavy_top_lane_inputs(tmpdir)
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/run_experiment.py",
                    "--lane",
                    "heavy_top_comparison",
                    "--config",
                    str(HEAVY_TOP_CONFIG_PATH),
                    "--matrix",
                    str(MATRIX_PATH),
                    "--mabd-report",
                    str(mabd_path),
                    "--rbd-report",
                    str(rk4_path),
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

            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            summary = json.loads(result.stdout)
            output_path = (
                Path(tmpdir) / "reports/experiment_matrix/single_body_heavy_top_comparison.json"
            )
            loaded = load_claim_report(output_path)

        self.assertEqual(summary["claim_id"], "experiment.single_body.heavy_top")
        self.assertEqual(summary["status"], "incomplete")
        self.assertEqual(summary["baseline_lane"], "heavy_top_comparison_protocol")
        self.assertEqual(summary["output_report"], output_path.as_posix())
        self.assertEqual(loaded.source_commit, "cli-source")
        self.assertEqual(loaded.vendored_newton_commit, "cli-newton")
        self.assertEqual(
            loaded.observed["input_report_provenance"]["rbd_rk4_reference"]["source_commit"],
            "test-source",
        )

    def test_run_experiment_cli_heavy_top_comparison_accepts_figure_report(self) -> None:
        import json
        import os
        import subprocess
        import sys

        from mabd_reproduction.experiment_configs import load_heavy_top_config
        from mabd_reproduction.heavy_top_digitization import write_heavy_top_figure_curve_report

        with TemporaryDirectory() as tmpdir:
            rk4_path, mabd_path = self._write_heavy_top_lane_inputs(tmpdir)
            config = load_heavy_top_config(HEAVY_TOP_CONFIG_PATH)
            figure_path = Path(tmpdir) / "heavy_top_figure_curves.json"
            write_heavy_top_figure_curve_report(
                figure_path,
                config=config,
                source_commit="test-source",
                vendored_newton_commit="test-newton",
                sample_count=51,
            )
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/run_experiment.py",
                    "--lane",
                    "heavy_top_comparison",
                    "--config",
                    str(HEAVY_TOP_CONFIG_PATH),
                    "--matrix",
                    str(MATRIX_PATH),
                    "--mabd-report",
                    str(mabd_path),
                    "--rbd-report",
                    str(rk4_path),
                    "--figure-report",
                    str(figure_path),
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

            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            summary = json.loads(result.stdout)
            output_path = (
                Path(tmpdir) / "reports/experiment_matrix/single_body_heavy_top_comparison.json"
            )
            loaded = load_claim_report(output_path)

        self.assertEqual(summary["baseline_lane"], "heavy_top_comparison_protocol")
        self.assertEqual(
            loaded.observed["paper_metric_statuses"]["nutation_angle_error"]["status"],
            "paper_figure_digitized_reference_available",
        )
        self.assertIn("paper_figure_curves", loaded.observed["input_report_provenance"])

    def test_run_experiment_cli_heavy_top_comparison_requires_input_reports(self) -> None:
        import os
        import subprocess
        import sys

        with TemporaryDirectory() as tmpdir:
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/run_experiment.py",
                    "--lane",
                    "heavy_top_comparison",
                    "--config",
                    str(HEAVY_TOP_CONFIG_PATH),
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
        self.assertIn(
            "heavy_top_comparison requires --mabd-report and --rbd-report",
            result.stderr,
        )

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

        from mabd_reproduction.experiment_configs import load_spinning_box_config
        from mabd_reproduction.spinning_box_digitization import (
            write_spinning_box_figure_curve_report,
        )

        with TemporaryDirectory() as tmpdir:
            mabd_path, rbd_path = self._write_spinning_box_lane_inputs(tmpdir)
            config = load_spinning_box_config(CONFIG_PATH)
            figure_path = Path(tmpdir) / "figure_curves.json"
            write_spinning_box_figure_curve_report(
                figure_path,
                config=config,
                source_commit="test-source",
                vendored_newton_commit="test-newton",
            )
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
                    "--figure-report",
                    str(figure_path),
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
        self.assertTrue(loaded.observed["digitized_figure_reference_available"])
        self.assertEqual(loaded.raw_outputs["figure_curve_report"], figure_path.as_posix())

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
