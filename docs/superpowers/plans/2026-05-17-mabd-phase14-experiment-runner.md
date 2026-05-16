# M-ABD Phase 14 Experiment Runner Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an executable, config-driven runner for the Phase 13 single-body spinning-box M-ABD development lane.

**Architecture:** Keep the runner in `src/mabd_reproduction/experiment_runner.py` so tests and CLI share one implementation. Add `scripts/run_experiment.py` as a thin argparse wrapper that loads the YAML config, validates it against the experiment matrix, writes a `ClaimReport`, and prints a small JSON summary. The runner must keep `experiment.single_body.spinning_box` incomplete until required baseline lanes exist.

**Tech Stack:** Python dataclasses, argparse, JSON, `unittest`, PyYAML-backed config loader, existing `ClaimReport`, vendored Newton M-ABD CPU oracle.

---

## Files

- Create `src/mabd_reproduction/experiment_runner.py`: orchestration API for config-driven experiment report generation.
- Create `scripts/run_experiment.py`: command-line entrypoint for one configured experiment.
- Create `tests/test_experiment_runner.py`: runner API and CLI tests.
- Modify `docs/reference/claim-boundaries.md`: Phase 14 claim boundary.
- Modify `scripts/validate_docs.py`: require Phase 14 runner, record, and snippets.
- Modify `tests/test_phase0_bootstrap.py`: bootstrap tests for Phase 14 boundary and record.
- Create `docs/records/2026-05-17-phase14-experiment-runner.md`: dated evidence record.

## Task 1: Runner API

**Files:**
- Create: `tests/test_experiment_runner.py`
- Create: `src/mabd_reproduction/experiment_runner.py`

- [ ] **Step 1: Write the failing API tests**

Create `tests/test_experiment_runner.py` with:

```python
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


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run API tests to verify RED**

Run:

```bash
PYTHONPATH=src:vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  -m unittest tests.test_experiment_runner
```

Expected: fail with `ModuleNotFoundError: No module named 'mabd_reproduction.experiment_runner'`.

- [ ] **Step 3: Implement the runner API**

Create `src/mabd_reproduction/experiment_runner.py` with:

```python
"""Config-driven experiment report runners for M-ABD reproduction."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .experiment_configs import (
    load_spinning_box_config,
    validate_spinning_box_config_against_matrix,
)
from .experiment_contracts import load_experiment_matrix
from .reporting import ClaimReport, EvidenceStatus
from .single_body_reports import write_spinning_box_development_report


@dataclass(frozen=True)
class ExperimentRunResult:
    claim_id: str
    scene_id: str
    status: EvidenceStatus
    report_path: Path
    report: ClaimReport

    def to_summary(self) -> dict[str, str]:
        return {
            "claim_id": self.claim_id,
            "scene_id": self.scene_id,
            "status": self.status.value,
            "output_report": self.report_path.as_posix(),
            "baseline_lane": self.report.baseline_lane,
        }


def _resolve_output_path(
    configured_output_report: str,
    *,
    output_path: str | Path | None,
    output_root: str | Path | None,
) -> Path:
    if output_path is not None and output_root is not None:
        raise ValueError("output_path and output_root are mutually exclusive")
    if output_path is not None:
        return Path(output_path)
    configured = Path(configured_output_report)
    if output_root is not None:
        return Path(output_root) / configured
    return configured


def run_spinning_box_experiment(
    *,
    config_path: str | Path,
    matrix_path: str | Path,
    source_commit: str,
    vendored_newton_commit: str,
    output_path: str | Path | None = None,
    output_root: str | Path | None = None,
    paper_source_version: str = "2603.08079v2",
) -> ExperimentRunResult:
    config = load_spinning_box_config(config_path)
    matrix = load_experiment_matrix(matrix_path)
    validate_spinning_box_config_against_matrix(config, matrix)
    report_path = _resolve_output_path(
        config.output_report,
        output_path=output_path,
        output_root=output_root,
    )
    report = write_spinning_box_development_report(
        report_path,
        config=config,
        source_commit=source_commit,
        vendored_newton_commit=vendored_newton_commit,
        paper_source_version=paper_source_version,
    )
    return ExperimentRunResult(
        claim_id=report.claim_id,
        scene_id=report.scene_id,
        status=report.status,
        report_path=report_path,
        report=report,
    )


__all__ = ["ExperimentRunResult", "run_spinning_box_experiment"]
```

- [ ] **Step 4: Run API tests to verify GREEN**

Run:

```bash
PYTHONPATH=src:vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  -m unittest tests.test_experiment_runner
```

Expected: `Ran 3 tests`, `OK`.

- [ ] **Step 5: Run focused lint**

Run:

```bash
/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  -m ruff check src/mabd_reproduction/experiment_runner.py tests/test_experiment_runner.py
```

Expected: `All checks passed!`.

- [ ] **Step 6: Commit Task 1**

Run:

```bash
git add src/mabd_reproduction/experiment_runner.py tests/test_experiment_runner.py
git commit -m "feat: add configured experiment runner"
```

## Task 2: CLI Entrypoint

**Files:**
- Modify: `tests/test_experiment_runner.py`
- Create: `scripts/run_experiment.py`

- [ ] **Step 1: Write the failing CLI tests**

Append these tests to `ExperimentRunnerTests` in `tests/test_experiment_runner.py`:

```python
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
```

- [ ] **Step 2: Run CLI tests to verify RED**

Run:

```bash
PYTHONPATH=src:vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  -m unittest tests.test_experiment_runner
```

Expected: fail because `scripts/run_experiment.py` does not exist.

- [ ] **Step 3: Implement CLI**

Create `scripts/run_experiment.py` with:

```python
#!/usr/bin/env python3
"""Run one configured M-ABD reproduction experiment lane."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from mabd_reproduction.experiment_runner import run_spinning_box_experiment


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run one configured M-ABD experiment lane.")
    parser.add_argument("--config", required=True, help="Experiment config YAML path.")
    parser.add_argument(
        "--matrix",
        default="configs/experiments/paper_experiment_matrix.yaml",
        help="Paper experiment matrix YAML path.",
    )
    parser.add_argument("--output", help="Override report output path.")
    parser.add_argument("--output-root", help="Root under which the config output_report path is written.")
    parser.add_argument("--source-commit", required=True, help="Repository source commit recorded in the report.")
    parser.add_argument(
        "--vendored-newton-commit",
        required=True,
        help="Vendored Newton source commit recorded in the report.",
    )
    parser.add_argument("--paper-source-version", default="2603.08079v2")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        result = run_spinning_box_experiment(
            config_path=Path(args.config),
            matrix_path=Path(args.matrix),
            output_path=Path(args.output) if args.output else None,
            output_root=Path(args.output_root) if args.output_root else None,
            source_commit=args.source_commit,
            vendored_newton_commit=args.vendored_newton_commit,
            paper_source_version=args.paper_source_version,
        )
    except Exception as exc:
        print(f"run_experiment.py: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result.to_summary(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run CLI tests to verify GREEN**

Run:

```bash
PYTHONPATH=src:vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  -m unittest tests.test_experiment_runner
```

Expected: `Ran 5 tests`, `OK`.

- [ ] **Step 5: Run focused lint**

Run:

```bash
/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  -m ruff check scripts/run_experiment.py tests/test_experiment_runner.py
```

Expected: `All checks passed!`.

- [ ] **Step 6: Commit Task 2**

Run:

```bash
git add scripts/run_experiment.py tests/test_experiment_runner.py
git commit -m "feat: add experiment runner cli"
```

## Task 3: Phase 14 Docs And Evidence

**Files:**
- Modify: `docs/reference/claim-boundaries.md`
- Modify: `scripts/validate_docs.py`
- Modify: `tests/test_phase0_bootstrap.py`
- Create: `docs/records/2026-05-17-phase14-experiment-runner.md`

- [ ] **Step 1: Write failing docs tests**

In `tests/test_phase0_bootstrap.py`, add:

```python
    def test_phase14_experiment_runner_lane_is_bounded(self) -> None:
        text = (ROOT / "docs/reference/claim-boundaries.md").read_text()
        normalized_text = " ".join(text.split())

        self.assertIn("Phase 14 verifies an executable config-driven experiment runner", text)
        self.assertIn("single-body spinning-box development report", normalized_text)
        self.assertIn("Phase 14 does not verify the paper spinning-box experiment", text)
        self.assertIn("any passed `experiment.*` claim", normalized_text)

    def test_phase14_record_has_required_evidence_fields(self) -> None:
        text = (ROOT / "docs/records/2026-05-17-phase14-experiment-runner.md").read_text()

        for snippet in (
            "## Status",
            "passed",
            "## Config Path",
            "configs/experiments/single_body_spinning_box.yaml",
            "## Repository",
            "plan commit:",
            "implementation commits:",
            "## Vendored Newton",
            "96713fa965463b69c229a4d30582c733ff3526bb",
            "## Paper Source",
            "PDF SHA256:",
            "TeX source SHA256:",
            "experiment.tex:40-55",
            "## Artifacts",
            "`scripts/run_experiment.py`",
            "`run_spinning_box_experiment`",
            "No `experiment.*` claim is passed in this phase.",
        ):
            self.assertIn(snippet, text)
```

In `scripts/validate_docs.py`:

- Add `docs/records/2026-05-17-phase14-experiment-runner.md` and `scripts/run_experiment.py` to `REQUIRED_PATHS`.
- Update the module docstring and final print from `/13` to `/14`.
- Add Phase 14 snippets to `validate_claim_boundaries()`.
- Add a `validate_phase14_record()` function mirroring the test snippets.
- Call `validate_phase14_record()` in `main()`.

- [ ] **Step 2: Run docs tests to verify RED**

Run:

```bash
PYTHONPATH=src:vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  -m unittest tests.test_phase0_bootstrap

PYTHONPATH=src:vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  scripts/validate_docs.py
```

Expected: fail because Phase 14 boundary and record do not exist.

- [ ] **Step 3: Update claim boundaries**

In `docs/reference/claim-boundaries.md`, add to `## Current`:

```markdown
- This repository contains Phase 14 executable config-driven single-body
  spinning-box development report runner after the Phase 14 record is created.
```

Add to `## Verified`:

```markdown
- Phase 14 verifies an executable config-driven experiment runner for the
  single-body spinning-box development report, including CLI output override,
  config-output-root resolution, report summary JSON, and config/matrix
  validation before writing.
- Phase 14 does not verify the paper spinning-box experiment, RBD baselines,
  paper timing, rendered output, paper trajectory agreement, generated report
  artifacts as committed evidence, or any passed `experiment.*` claim.
```

- [ ] **Step 4: Create Phase 14 record**

Create `docs/records/2026-05-17-phase14-experiment-runner.md` with:

```markdown
# Phase 14 Experiment Runner Record

Date: 2026-05-17

## Status

passed

## Scope

Phase 14 adds an executable config-driven runner for the single-body
spinning-box M-ABD development report lane. It exposes both a Python API and
`scripts/run_experiment.py` CLI for generating the Phase 13 report from the
committed YAML config.

This phase does not verify the paper spinning-box experiment, RBD baselines,
paper timing, rendered output, paper trajectory agreement, committed generated
report artifacts, or any passed `experiment.*` claim. The generated report
remains `incomplete`.

## Config Path

- `configs/experiments/single_body_spinning_box.yaml`
- matrix: `configs/experiments/paper_experiment_matrix.yaml`

## Repository

- worktree: `/cpfs/user/zhuzihou/dev/mabd-newton/.worktrees/phase14-experiment-runner`
- branch: `phase14-experiment-runner`
- base commit: `6bfaa63`
- plan commit: recorded after the plan commit exists
- implementation commits: recorded after runner implementation commits exist

## Vendored Newton

- vendored path: `vendor/newton`
- upstream commit: `96713fa965463b69c229a4d30582c733ff3526bb`
- local patch status: Phase 14 adds no vendored Newton source changes.

## Paper Source

- arXiv ID: `2603.08079`
- arXiv version: `v2`
- PDF SHA256:
  `a594e79093673c60fc59ad14f9b71f29a8f7f8e7b1c3d9c73efe6f5814cc6ec0`
- TeX source SHA256:
  `73ec398956c606dec2f8f40f0d38b9d5370e11b27830775e1b3765fe0efc563f`
- cited source lines: `experiment.tex:40-55`

## Environment

- Python: `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python`
- Backend: CPU NumPy oracle through vendored Newton imports

## Metrics And Thresholds

- random seed: not applicable; runner uses deterministic config state
- metrics: API report writing, configured output-root resolution, CLI summary
  JSON, CLI failure for invalid config, incomplete report status
- thresholds: exact output path/status equality and existing Phase 13 report
  thresholds

## Artifacts

- committed runner API: `src/mabd_reproduction/experiment_runner.py`
- committed CLI: `scripts/run_experiment.py`
- committed tests: `tests/test_experiment_runner.py`
- generated reports: not committed; tests write JSON reports to temporary
  directories only
- `run_spinning_box_experiment` validates config and matrix before writing.
- `scripts/run_experiment.py` writes a report and prints JSON summary.

## TDD Evidence

RED result:

```text
runner API: ModuleNotFoundError for mabd_reproduction.experiment_runner
runner CLI: scripts/run_experiment.py missing
docs: Phase 14 boundary and record missing
```

GREEN result:

```text
experiment runner tests: Ran 5 tests, OK
docs/provenance validation: Phase 0/1/2/3/4/5/6/7/8/9/10/11/12/13/14 docs/provenance validation passed
```

## Final Verification

Final verification commands:

```bash
/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_runner tests.test_experiment_run_configs tests.test_single_body_report_lane tests.test_reporting_contracts tests.test_phase0_bootstrap
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"
git diff --check
```

Final verification result:

```text
This section is refreshed in Task 4 after final verification commands run.
```

## Claim Impact

No `experiment.*` claim is passed in this phase.
```

- [ ] **Step 5: Implement docs validator updates**

Update `scripts/validate_docs.py` exactly enough to require:

- `docs/records/2026-05-17-phase14-experiment-runner.md`
- `scripts/run_experiment.py`
- Phase 14 claim-boundary snippets listed above
- Phase 14 record snippets listed above
- final success text `Phase 0/1/2/3/4/5/6/7/8/9/10/11/12/13/14 docs/provenance validation passed`

- [ ] **Step 6: Run docs tests to verify GREEN**

Run:

```bash
PYTHONPATH=src:vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  -m unittest tests.test_phase0_bootstrap

PYTHONPATH=src:vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  scripts/validate_docs.py
```

Expected: `tests.test_phase0_bootstrap` passes and docs validation prints `/14`.

- [ ] **Step 7: Commit Task 3**

Run:

```bash
git add docs/reference/claim-boundaries.md docs/records/2026-05-17-phase14-experiment-runner.md scripts/validate_docs.py tests/test_phase0_bootstrap.py
git commit -m "docs: record Phase 14 experiment runner"
```

## Task 4: Final Verification And Record Refresh

**Files:**
- Modify: `docs/records/2026-05-17-phase14-experiment-runner.md`

- [ ] **Step 1: Run full branch verification**

Run:

```bash
/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_runner tests.test_experiment_run_configs tests.test_single_body_report_lane tests.test_reporting_contracts tests.test_phase0_bootstrap
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"
git diff --check
```

Expected:

- ruff: `All checks passed!`
- docs: `/14 docs/provenance validation passed`
- focused tests: pass
- full public tests: pass
- vendored import path resolves inside this worktree
- `git diff --check`: clean

- [ ] **Step 2: Refresh Phase 14 record**

Replace the temporary commit-trail text with actual short commit hashes from `git log --oneline`. Replace the temporary final-verification sentence with the observed final verification output and test counts.

- [ ] **Step 3: Run record validation**

Run:

```bash
PYTHONPATH=src:vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  scripts/validate_docs.py
git diff --check
```

Expected: docs validation passes and whitespace check is clean.

- [ ] **Step 4: Commit record refresh**

Run:

```bash
git add docs/records/2026-05-17-phase14-experiment-runner.md
git commit -m "docs: refresh Phase 14 verification evidence"
```

## Final Review

- Request read-only code review for implementation/API/CLI behavior.
- Request read-only docs/provenance review for Phase 14 claim boundaries.
- Fix Critical and Important feedback with TDD.
- Re-run full verification on the branch.
- Merge to `main`, re-run full verification on `main`, push to `git@github.com:jandan138/mabd-newton.git main`, verify remote head, then remove the worktree and delete the local feature branch.

## Self-Review

- Spec coverage: This plan implements the existing approved design's config-to-runner data flow for one scene without claiming full paper evidence.
- Placeholder scan: The plan has no `TBD` or `TODO` markers; Task 4 explicitly replaces temporary record text after real commit hashes and verification output exist.
- Type consistency: `ExperimentRunResult`, `run_spinning_box_experiment`, `report_path`, and `to_summary()` are defined before use by CLI/tests.
- Claim boundary: No task marks `experiment.*` passed; all generated reports remain temporary test artifacts or user-run outputs.
