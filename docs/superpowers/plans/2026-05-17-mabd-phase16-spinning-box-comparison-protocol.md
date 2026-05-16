# M-ABD Phase 16 Spinning-Box Comparison Protocol Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a machine-checkable spinning-box multi-lane comparison protocol that records why the paper comparison remains incomplete instead of leaving the protocol unrecorded.

**Architecture:** Keep comparison assembly in a new `src/mabd_reproduction/comparison_reports.py` module that consumes existing `ClaimReport` JSON files for the `mabd_newton` and `rbd_implicit_baseline` lanes. The comparison writer emits another full-schema `ClaimReport` with `baseline_lane="spinning_box_comparison_protocol"` and `status=incomplete` until required lane reports are paper-complete and required paper metrics exist. Runner/CLI dispatch will require explicit input report paths and explicit output to avoid accidental generated artifact churn.

**Tech Stack:** Python dataclasses, existing `ClaimReport` JSON schema, existing config/matrix loaders, `unittest`, `scripts/run_experiment.py`.

---

## Files

- Create `src/mabd_reproduction/comparison_reports.py`: lane validation, metric extraction, incomplete comparison report writer.
- Create `tests/test_spinning_box_comparison.py`: focused comparison report tests.
- Modify `src/mabd_reproduction/experiment_runner.py`: add `run_spinning_box_comparison(...)`.
- Modify `scripts/run_experiment.py`: add `spinning_box_comparison` lane plus `--mabd-report` and `--rbd-report`.
- Modify `tests/test_experiment_runner.py`: API and CLI dispatch tests for the comparison lane.
- Modify `configs/experiments/paper_experiment_matrix.yaml`: replace `paper_comparison_protocol_not_recorded` with `spinning_box_comparison_report_incomplete`.
- Modify `src/mabd_reproduction/experiment_configs.py`, `scripts/validate_docs.py`, `tests/test_experiment_run_configs.py`, and `tests/test_phase0_bootstrap.py`: validate the new blocker and Phase 16 boundaries.
- Create `docs/records/2026-05-17-phase16-spinning-box-comparison-protocol.md`: dated evidence record.
- Modify `docs/reference/claim-boundaries.md`: add Phase 16 current/verified/nonclaim text.

## Task 1: Comparison Report Protocol

**Files:**
- Create: `tests/test_spinning_box_comparison.py`
- Create: `src/mabd_reproduction/comparison_reports.py`

- [ ] **Step 1: Write failing comparison tests**

Create `tests/test_spinning_box_comparison.py` with tests that first generate temporary M-ABD and RBD lane reports, then require the comparison report:

```python
from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from mabd_reproduction.experiment_configs import load_spinning_box_config
from mabd_reproduction.reporting import EvidenceStatus, load_claim_report
from mabd_reproduction.rigid_baselines import write_spinning_box_rbd_baseline_report
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
        write_spinning_box_rbd_baseline_report(
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
        self.assertIn("mabd_newton:linear_momentum_error", loaded.observed["missing_required_metrics"])
        self.assertIn("mabd_newton:angular_momentum_error", loaded.observed["missing_required_metrics"])
        self.assertIn("required lane reports remain incomplete", loaded.failure_reason)
        self.assertEqual(loaded.threshold["required_lane_status"], "passed")

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


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run RED**

```bash
PYTHONPATH=src:vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  -m unittest tests.test_spinning_box_comparison
```

Expected: `ModuleNotFoundError: No module named 'mabd_reproduction.comparison_reports'`.

- [ ] **Step 3: Implement comparison report writer**

Create `src/mabd_reproduction/comparison_reports.py`:

```python
"""Multi-lane comparison reports for paper experiment claims."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .experiment_configs import SpinningBoxRunConfig
from .reporting import ClaimReport, EvidenceStatus, load_claim_report, write_claim_report


SPINNING_BOX_REQUIRED_METRICS = (
    "linear_momentum_error",
    "angular_momentum_error",
    "energy_drift",
)


def _require_lane_report(
    path: str | Path,
    *,
    config: SpinningBoxRunConfig,
    lane: str,
) -> ClaimReport:
    report = load_claim_report(path)
    if report.claim_id != config.claim_id:
        raise ValueError(f"{lane} report claim_id must be {config.claim_id}")
    if report.scene_id != config.scene_id:
        raise ValueError(f"{lane} report scene_id must be {config.scene_id}")
    if report.baseline_lane != lane:
        raise ValueError(f"{lane} report must have baseline_lane={lane}")
    return report


def _lane_metric_snapshot(report: ClaimReport) -> dict[str, Any]:
    return {metric: report.observed.get(metric) for metric in SPINNING_BOX_REQUIRED_METRICS}


def _missing_metrics(lane: str, report: ClaimReport) -> list[str]:
    return [
        f"{lane}:{metric}"
        for metric in SPINNING_BOX_REQUIRED_METRICS
        if metric not in report.observed
    ]


def write_spinning_box_comparison_report(
    path: str | Path,
    *,
    config: SpinningBoxRunConfig,
    mabd_report_path: str | Path,
    rbd_report_path: str | Path,
    source_commit: str,
    vendored_newton_commit: str,
    paper_source_version: str = "2603.08079v2",
) -> ClaimReport:
    mabd_report = _require_lane_report(mabd_report_path, config=config, lane="mabd_newton")
    rbd_report = _require_lane_report(rbd_report_path, config=config, lane="rbd_implicit_baseline")
    lane_statuses = {
        "mabd_newton": mabd_report.status.value,
        "rbd_implicit_baseline": rbd_report.status.value,
    }
    missing_required_metrics = _missing_metrics("mabd_newton", mabd_report) + _missing_metrics(
        "rbd_implicit_baseline",
        rbd_report,
    )
    incomplete_lanes = [
        lane for lane, status in lane_statuses.items() if status != EvidenceStatus.PASSED.value
    ]
    blocking_reasons = [
        *(f"{lane}_report_{lane_statuses[lane]}" for lane in incomplete_lanes),
        *(f"{metric}_missing" for metric in missing_required_metrics),
    ]
    if rbd_report.solver_mode != "paper_faithful_implicit_rbd":
        blocking_reasons.append("rbd_implicit_baseline_not_paper_faithful")
    if not blocking_reasons:
        blocking_reasons.append("experiment_pass_gate_not_enabled")

    report = ClaimReport(
        claim_id=config.claim_id,
        scene_id=config.scene_id,
        asset_hashes={"primitive_cube": "not_applicable_procedural"},
        solver_mode="spinning_box_multilane_comparison_development",
        backend="report_protocol",
        baseline_lane="spinning_box_comparison_protocol",
        expected={
            "paper_claim_status": "requires passed M-ABD and paper-faithful implicit RBD lanes",
            "required_lanes": ["mabd_newton", "rbd_implicit_baseline"],
            "required_metrics": list(SPINNING_BOX_REQUIRED_METRICS),
            "source_lines": list(config.source_lines),
        },
        observed={
            "lane_statuses": lane_statuses,
            "lane_solver_modes": {
                "mabd_newton": mabd_report.solver_mode,
                "rbd_implicit_baseline": rbd_report.solver_mode,
            },
            "lane_metrics": {
                "mabd_newton": _lane_metric_snapshot(mabd_report),
                "rbd_implicit_baseline": _lane_metric_snapshot(rbd_report),
            },
            "missing_required_metrics": missing_required_metrics,
            "blocking_reasons": blocking_reasons,
        },
        threshold={
            "required_lane_status": EvidenceStatus.PASSED.value,
            "required_metrics": list(SPINNING_BOX_REQUIRED_METRICS),
            "paper_faithful_rbd_solver_mode": "paper_faithful_implicit_rbd",
        },
        unit="json_report",
        status=EvidenceStatus.INCOMPLETE,
        failure_reason="required lane reports remain incomplete or missing paper comparison metrics",
        timing_distribution={"scope": "not_timed"},
        raw_outputs={
            "mabd_report": Path(mabd_report_path).as_posix(),
            "rbd_report": Path(rbd_report_path).as_posix(),
        },
        plot_paths={},
        source_commit=source_commit,
        vendored_newton_commit=vendored_newton_commit,
        paper_source_version=paper_source_version,
    )
    write_claim_report(report, path)
    return report


__all__ = ["SPINNING_BOX_REQUIRED_METRICS", "write_spinning_box_comparison_report"]
```

- [ ] **Step 4: Run GREEN and lint**

```bash
PYTHONPATH=src:vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  -m unittest tests.test_spinning_box_comparison

/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  -m ruff check src/mabd_reproduction/comparison_reports.py tests/test_spinning_box_comparison.py
```

Expected: `Ran 2 tests, OK` and `All checks passed!`.

- [ ] **Step 5: Commit**

```bash
git add src/mabd_reproduction/comparison_reports.py tests/test_spinning_box_comparison.py
git commit -m "feat: add spinning-box comparison protocol report"
```

## Task 2: Runner And CLI Dispatch

**Files:**
- Modify: `src/mabd_reproduction/experiment_runner.py`
- Modify: `scripts/run_experiment.py`
- Modify: `tests/test_experiment_runner.py`

- [ ] **Step 1: Add failing runner and CLI tests**

Append tests to `tests/test_experiment_runner.py` that generate two input lane reports in a temp dir, then call both API and CLI:

```python
    def _write_spinning_box_lane_inputs(self, tmpdir: str) -> tuple[Path, Path]:
        from mabd_reproduction.experiment_configs import load_spinning_box_config
        from mabd_reproduction.rigid_baselines import write_spinning_box_rbd_baseline_report
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
        write_spinning_box_rbd_baseline_report(
            rbd_path,
            config=config,
            source_commit="test-source",
            vendored_newton_commit="test-newton",
        )
        return mabd_path, rbd_path

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
```

- [ ] **Step 2: Run RED**

```bash
PYTHONPATH=src:vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  -m unittest tests.test_experiment_runner
```

Expected: import/argparse failures for `run_spinning_box_comparison`, `--lane spinning_box_comparison`, `--mabd-report`, and `--rbd-report`.

- [ ] **Step 3: Implement dispatch**

In `src/mabd_reproduction/experiment_runner.py`:

- import `write_spinning_box_comparison_report`;
- add optional `mabd_report_path` and `rbd_report_path` fields only to the new runner signature;
- validate config and matrix through existing loaders;
- require explicit `output_path`;
- reject `output_root`;
- require both input report paths;
- return `ExperimentRunResult`.

In `scripts/run_experiment.py`:

- add lane choice `spinning_box_comparison`;
- add args `--mabd-report` and `--rbd-report`;
- route to `run_spinning_box_comparison`;
- pass input paths only for comparison lane.

- [ ] **Step 4: Run GREEN and lint**

```bash
PYTHONPATH=src:vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  -m unittest tests.test_experiment_runner tests.test_spinning_box_comparison

/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  -m ruff check src/mabd_reproduction/experiment_runner.py scripts/run_experiment.py tests/test_experiment_runner.py
```

- [ ] **Step 5: Commit**

```bash
git add src/mabd_reproduction/experiment_runner.py scripts/run_experiment.py tests/test_experiment_runner.py
git commit -m "feat: dispatch spinning-box comparison protocol"
```

## Task 3: Matrix, Boundaries, And Phase Record

**Files:**
- Modify: `configs/experiments/paper_experiment_matrix.yaml`
- Modify: `src/mabd_reproduction/experiment_configs.py`
- Modify: `scripts/validate_docs.py`
- Modify: `tests/test_experiment_run_configs.py`
- Modify: `tests/test_phase0_bootstrap.py`
- Modify: `docs/reference/claim-boundaries.md`
- Create: `docs/records/2026-05-17-phase16-spinning-box-comparison-protocol.md`

- [ ] **Step 1: Write failing validation tests**

Update `tests/test_experiment_run_configs.py` so the spinning-box matrix check requires:

```python
self.assertIn("spinning_box_comparison_report_incomplete", entry.blocking_reasons)
self.assertNotIn("paper_comparison_protocol_not_recorded", entry.blocking_reasons)
```

Update `tests/test_phase0_bootstrap.py` with Phase 16 boundary assertions:

```python
def test_phase16_spinning_box_comparison_protocol_is_bounded(self) -> None:
    text = (ROOT / "docs/reference/claim-boundaries.md").read_text()
    normalized_text = " ".join(text.split())
    self.assertIn("Phase 16 verifies a machine-checkable spinning-box comparison protocol", text)
    self.assertIn("spinning_box_comparison_protocol", normalized_text)
    self.assertIn("Phase 16 does not verify the paper spinning-box experiment", text)
    self.assertIn("any passed `experiment.*` claim", normalized_text)
```

And record snippets:

```python
for snippet in (
    "## Status",
    "passed",
    "spinning_box_comparison_protocol",
    "spinning_box_comparison_report_incomplete",
    "`src/mabd_reproduction/comparison_reports.py`",
    "`--lane spinning_box_comparison`",
    "No `experiment.*` claim is passed in this phase.",
):
    self.assertIn(snippet, text)
```

- [ ] **Step 2: Run RED**

```bash
PYTHONPATH=src:vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  -m unittest tests.test_experiment_run_configs tests.test_phase0_bootstrap

PYTHONPATH=src:vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  scripts/validate_docs.py
```

Expected: failures for stale matrix blocker and missing Phase 16 docs/record.

- [ ] **Step 3: Implement matrix and docs**

In `configs/experiments/paper_experiment_matrix.yaml`, replace:

```yaml
- paper_comparison_protocol_not_recorded
```

with:

```yaml
- spinning_box_comparison_report_incomplete
```

In `src/mabd_reproduction/experiment_configs.py`, update the blocker match rule for `required_missing_lanes` to continue allowing lane-specific report blockers and leave comparison blockers independent.

In `scripts/validate_docs.py`, add:

- `PHASE_RECORDS` entry for `docs/records/2026-05-17-phase16-spinning-box-comparison-protocol.md`;
- claim-boundary checks for Phase 16;
- `validate_phase16_record()`;
- experiment matrix checks forbidding `paper_comparison_protocol_not_recorded` and requiring `spinning_box_comparison_report_incomplete`;
- final message `Phase 0/.../16 docs/provenance validation passed`.

In `docs/reference/claim-boundaries.md`, add current/verified/nonclaim Phase 16 bullets.

Create `docs/records/2026-05-17-phase16-spinning-box-comparison-protocol.md` with concrete provenance, paper source lines, environment, comparison protocol fields, TDD evidence, final verification placeholders to update after running final gates, and explicit no-pass claim impact.

- [ ] **Step 4: Run GREEN and lint**

```bash
PYTHONPATH=src:vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  scripts/validate_docs.py

PYTHONPATH=src:vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  -m unittest tests.test_experiment_run_configs tests.test_phase0_bootstrap

/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  -m ruff check scripts/validate_docs.py tests/test_experiment_run_configs.py tests/test_phase0_bootstrap.py
```

- [ ] **Step 5: Commit**

```bash
git add configs/experiments/paper_experiment_matrix.yaml src/mabd_reproduction/experiment_configs.py scripts/validate_docs.py tests/test_experiment_run_configs.py tests/test_phase0_bootstrap.py docs/reference/claim-boundaries.md docs/records/2026-05-17-phase16-spinning-box-comparison-protocol.md
git commit -m "docs: record Phase 16 comparison protocol"
```

## Task 4: Final Verification, Review, Merge, Push

**Files:**
- Modify: `docs/records/2026-05-17-phase16-spinning-box-comparison-protocol.md` if final test counts differ.

- [ ] **Step 1: Run final verification**

```bash
/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_spinning_box_comparison tests.test_experiment_runner tests.test_experiment_run_configs tests.test_phase0_bootstrap
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"
git diff --check
```

- [ ] **Step 2: Refresh record if needed**

If focused/full test counts differ from the record, update the Phase 16 record final verification block and rerun:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
git diff --check
```

- [ ] **Step 3: Request review**

Ask two independent reviewers to inspect Phase 16:

- claim/spec review: matrix blockers, claim boundaries, record, overclaim risk;
- code-quality review: comparison report validation, CLI dispatch, missing metric handling, JSON stdout behavior.

Fix Critical and Important findings, rerun relevant tests, and commit.

- [ ] **Step 4: Merge and push**

```bash
cd /cpfs/user/zhuzihou/dev/mabd-newton
git merge --ff-only phase16-spinning-box-comparison-protocol
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
GIT_SSH_COMMAND='ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=accept-new' git push git@github.com:jandan138/mabd-newton.git main
git worktree remove /cpfs/user/zhuzihou/dev/mabd-newton/.worktrees/phase16-spinning-box-comparison-protocol
git branch -d phase16-spinning-box-comparison-protocol
```

Expected: local and remote `main` point to the final Phase 16 commit.
