# Phase 13 Configured Spinning-Box Lane Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the Phase 12 hard-coded spinning-box development lane with a machine-checkable per-scene config that drives the M-ABD Newton CPU-oracle report while keeping the experiment claim incomplete.

**Architecture:** Add a narrow config loader for `experiment.single_body.spinning_box`, validate it against `configs/experiments/paper_experiment_matrix.yaml`, then make the report writer consume that config. This creates the first concrete paper-scene config path without adding baseline adapters or changing any `experiment.*` claim status.

**Tech Stack:** Python dataclasses, PyYAML, `unittest`, vendored Newton M-ABD CPU oracle, existing `ClaimReport` JSON contract.

---

### Task 1: Add Config Contract And Fixture

**Files:**
- Create: `configs/experiments/single_body_spinning_box.yaml`
- Create: `src/mabd_reproduction/experiment_configs.py`
- Create: `tests/test_experiment_run_configs.py`

- [ ] **Step 1: Write the failing config-loader test**

Create `tests/test_experiment_run_configs.py` with:

```python
from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import yaml

from mabd_reproduction.experiment_configs import (
    ExperimentRunConfigError,
    load_spinning_box_config,
    validate_spinning_box_config_against_matrix,
)
from mabd_reproduction.experiment_contracts import load_experiment_matrix
from mabd_reproduction.reporting import EvidenceStatus


ROOT = Path(__file__).resolve().parents[1]


class ExperimentRunConfigTests(unittest.TestCase):
    def test_spinning_box_config_is_machine_checkable(self) -> None:
        config = load_spinning_box_config(ROOT / "configs/experiments/single_body_spinning_box.yaml")

        self.assertEqual(config.schema_version, 1)
        self.assertEqual(config.claim_id, "experiment.single_body.spinning_box")
        self.assertEqual(config.scene_id, "single_body_spinning_box")
        self.assertEqual(config.asset_ids, ("primitive_cube",))
        self.assertEqual(config.baseline_lane, "mabd_newton")
        self.assertEqual(config.report_status, EvidenceStatus.INCOMPLETE)
        self.assertIn("rbd_implicit_baseline", config.failure_reason)
        self.assertEqual(config.time_step_s, 0.01)
        self.assertEqual(config.step_count, 4)
        self.assertEqual(config.initial_qd.shape, (12,))
        self.assertEqual(config.mass_diagonal.shape, (12,))
        self.assertIn("energy_drift", config.thresholds)
        self.assertIn("generalized_momentum_delta_norm", config.thresholds)

    def test_spinning_box_config_matches_experiment_matrix(self) -> None:
        config = load_spinning_box_config(ROOT / "configs/experiments/single_body_spinning_box.yaml")
        matrix = load_experiment_matrix(ROOT / "configs/experiments/paper_experiment_matrix.yaml")

        validate_spinning_box_config_against_matrix(config, matrix)

    def test_spinning_box_config_rejects_passed_experiment_status(self) -> None:
        with TemporaryDirectory() as tmpdir:
            source = yaml.safe_load((ROOT / "configs/experiments/single_body_spinning_box.yaml").read_text())
            source["report"]["status"] = "passed"
            path = Path(tmpdir) / "bad.yaml"
            path.write_text(yaml.safe_dump(source), encoding="utf-8")

            with self.assertRaisesRegex(ExperimentRunConfigError, "passed experiment"):
                load_spinning_box_config(path)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the failing test**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_run_configs
```

Expected: fail with `ModuleNotFoundError: No module named 'mabd_reproduction.experiment_configs'`.

- [ ] **Step 3: Add the YAML fixture**

Create `configs/experiments/single_body_spinning_box.yaml`:

```yaml
schema_version: 1
claim_id: experiment.single_body.spinning_box
scene_id: single_body_spinning_box
source_lines:
  - /tmp/mabd-paper/source/sections/experiment.tex:40-55
asset_ids:
  - primitive_cube
baseline_lane: mabd_newton
required_missing_lanes:
  - rbd_implicit_baseline
paper_values:
  cube_size_m: 0.1
  density: "1E3 kg/m^3"
  material_E: "1E9 Pa"
  poisson_ratio: 0.3
  p0: [100, 0, 0]
  L0: [0, 100, 0]
simulation:
  time_step_s: 0.01
  step_count: 4
  initial_q:
    - 1.0
    - 0.0
    - 0.0
    - 0.0
    - 1.0
    - 0.0
    - 0.0
    - 0.0
    - 1.0
    - 0.0
    - 0.0
    - 0.0
  initial_qd:
    - -0.2
    - -0.1590909090909091
    - -0.1181818181818182
    - -0.07727272727272727
    - -0.03636363636363636
    - 0.004545454545454547
    - 0.04545454545454547
    - 0.08636363636363636
    - 0.1272727272727273
    - 0.16818181818181818
    - 0.2090909090909091
    - 0.25
  mass_diagonal:
    - 1.0
    - 1.0
    - 1.0
    - 1.0
    - 1.0
    - 1.0
    - 1.0
    - 1.0
    - 1.0
    - 1.0
    - 1.0
    - 1.0
report:
  status: incomplete
  failure_reason: full paper claim still requires rbd_implicit_baseline
  output_report: reports/experiment_matrix/single_body_spinning_box.json
  thresholds:
    energy_drift: 1.0e-12
    generalized_momentum_delta_norm: 1.0e-12
```

- [ ] **Step 4: Add the loader implementation**

Create `src/mabd_reproduction/experiment_configs.py` with:

```python
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import yaml

from .experiment_contracts import ExperimentMatrix
from .reporting import EvidenceStatus


class ExperimentRunConfigError(ValueError):
    """Raised when a per-scene run config is incomplete or unsafe."""


@dataclass(frozen=True)
class SpinningBoxRunConfig:
    schema_version: int
    claim_id: str
    scene_id: str
    source_lines: tuple[str, ...]
    asset_ids: tuple[str, ...]
    baseline_lane: str
    required_missing_lanes: tuple[str, ...]
    paper_values: dict[str, Any]
    time_step_s: float
    step_count: int
    initial_q: np.ndarray
    initial_qd: np.ndarray
    mass_diagonal: np.ndarray
    report_status: EvidenceStatus
    failure_reason: str
    output_report: str
    thresholds: dict[str, float]


def _read_mapping(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ExperimentRunConfigError(f"{path} must contain a YAML mapping")
    return data


def _require_str(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value:
        raise ExperimentRunConfigError(f"{key} must be a non-empty string")
    return value


def _require_str_tuple(data: dict[str, Any], key: str) -> tuple[str, ...]:
    value = data.get(key)
    if not isinstance(value, list) or not value or not all(isinstance(item, str) and item for item in value):
        raise ExperimentRunConfigError(f"{key} must be a non-empty list of strings")
    return tuple(value)


def _require_mapping(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = data.get(key)
    if not isinstance(value, dict) or not value:
        raise ExperimentRunConfigError(f"{key} must be a non-empty mapping")
    return dict(value)


def _require_float_mapping(data: dict[str, Any], key: str) -> dict[str, float]:
    mapping = _require_mapping(data, key)
    result: dict[str, float] = {}
    for item_key, item_value in mapping.items():
        if not isinstance(item_key, str):
            raise ExperimentRunConfigError(f"{key} keys must be strings")
        result[item_key] = float(item_value)
    return result


def _require_vector(data: dict[str, Any], key: str) -> np.ndarray:
    value = data.get(key)
    vector = np.asarray(value, dtype=float)
    if vector.shape != (12,):
        raise ExperimentRunConfigError(f"{key} must contain 12 numeric values")
    return vector


def load_spinning_box_config(path: str | Path) -> SpinningBoxRunConfig:
    config_path = Path(path)
    data = _read_mapping(config_path)
    if data.get("schema_version") != 1:
        raise ExperimentRunConfigError("schema_version must be 1")
    if _require_str(data, "claim_id") != "experiment.single_body.spinning_box":
        raise ExperimentRunConfigError("spinning-box config must target experiment.single_body.spinning_box")
    simulation = _require_mapping(data, "simulation")
    report = _require_mapping(data, "report")
    status = EvidenceStatus(_require_str(report, "status"))
    if status == EvidenceStatus.PASSED:
        raise ExperimentRunConfigError("passed experiment configs require a dedicated evidence gate")
    return SpinningBoxRunConfig(
        schema_version=1,
        claim_id=_require_str(data, "claim_id"),
        scene_id=_require_str(data, "scene_id"),
        source_lines=_require_str_tuple(data, "source_lines"),
        asset_ids=_require_str_tuple(data, "asset_ids"),
        baseline_lane=_require_str(data, "baseline_lane"),
        required_missing_lanes=_require_str_tuple(data, "required_missing_lanes"),
        paper_values=_require_mapping(data, "paper_values"),
        time_step_s=float(simulation.get("time_step_s")),
        step_count=int(simulation.get("step_count")),
        initial_q=_require_vector(simulation, "initial_q"),
        initial_qd=_require_vector(simulation, "initial_qd"),
        mass_diagonal=_require_vector(simulation, "mass_diagonal"),
        report_status=status,
        failure_reason=_require_str(report, "failure_reason"),
        output_report=_require_str(report, "output_report"),
        thresholds=_require_float_mapping(report, "thresholds"),
    )


def validate_spinning_box_config_against_matrix(
    config: SpinningBoxRunConfig, matrix: ExperimentMatrix
) -> None:
    matches = [entry for entry in matrix.experiments if entry.claim_id == config.claim_id]
    if len(matches) != 1:
        raise ExperimentRunConfigError(f"{config.claim_id} must have exactly one matrix entry")
    entry = matches[0]
    if config.scene_id != entry.scene_id:
        raise ExperimentRunConfigError("scene_id must match experiment matrix")
    if config.source_lines != entry.source_lines:
        raise ExperimentRunConfigError("source_lines must match experiment matrix")
    if config.asset_ids != entry.asset_ids:
        raise ExperimentRunConfigError("asset_ids must match experiment matrix")
    if config.output_report != entry.output_report:
        raise ExperimentRunConfigError("output_report must match experiment matrix")
    if config.baseline_lane not in entry.required_lanes:
        raise ExperimentRunConfigError("baseline_lane must be listed in required_lanes")
    missing = set(config.required_missing_lanes) - set(entry.required_lanes)
    if missing:
        raise ExperimentRunConfigError("required_missing_lanes must be listed in required_lanes")


__all__ = [
    "ExperimentRunConfigError",
    "SpinningBoxRunConfig",
    "load_spinning_box_config",
    "validate_spinning_box_config_against_matrix",
]
```

- [ ] **Step 5: Run tests and commit**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_run_configs
/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check src/mabd_reproduction/experiment_configs.py tests/test_experiment_run_configs.py
```

Expected: `Ran 3 tests, OK` and `All checks passed!`.

Commit:

```bash
git add configs/experiments/single_body_spinning_box.yaml src/mabd_reproduction/experiment_configs.py tests/test_experiment_run_configs.py
git commit -m "feat: add configured spinning-box experiment lane"
```

### Task 2: Make Report Generation Config-Driven

**Files:**
- Modify: `src/mabd_reproduction/single_body_reports.py`
- Modify: `tests/test_single_body_report_lane.py`

- [ ] **Step 1: Write the failing report integration test**

Append to `tests/test_single_body_report_lane.py`:

```python
    def test_spinning_box_report_uses_run_config(self) -> None:
        from mabd_reproduction.experiment_configs import load_spinning_box_config

        root = Path(__file__).resolve().parents[1]
        config = load_spinning_box_config(root / "configs/experiments/single_body_spinning_box.yaml")
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "single_body_spinning_box.json"
            report = write_spinning_box_development_report(
                path,
                config=config,
                source_commit="test-source",
                vendored_newton_commit="test-newton",
            )
            loaded = load_claim_report(path)

        self.assertEqual(report.scene_id, config.scene_id)
        self.assertEqual(report.asset_hashes, {"primitive_cube": "not_applicable_procedural"})
        self.assertEqual(loaded.observed["step_count"], config.step_count)
        self.assertEqual(loaded.observed["time_step_s"], config.time_step_s)
        self.assertEqual(loaded.threshold, config.thresholds)
        self.assertEqual(loaded.status, config.report_status)
        self.assertEqual(loaded.failure_reason, config.failure_reason)
```

- [ ] **Step 2: Run the failing test**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_single_body_report_lane
```

Expected: fail with `TypeError` because `write_spinning_box_development_report()` has no `config` argument.

- [ ] **Step 3: Update report writer**

Modify `src/mabd_reproduction/single_body_reports.py`:

```python
from .experiment_configs import SpinningBoxRunConfig
```

Change `_oracle_body()` to accept the config:

```python
def _oracle_body(config: SpinningBoxRunConfig | None = None) -> mabd.MABDCPUOracleBody:
    mass_matrix = np.eye(12)
    if config is not None:
        mass_matrix = np.diag(config.mass_diagonal)
    return mabd.MABDCPUOracleBody(
        precompute=mabd.SingleBodyABDPrecompute(
            rest_points=np.zeros((4, 3), dtype=float),
            masses=np.ones(4, dtype=float),
            mass_matrix=mass_matrix,
            stiffness_matrix=np.zeros((12, 12), dtype=float),
        )
    )
```

Change the writer signature and setup:

```python
def write_spinning_box_development_report(
    path: str | Path,
    *,
    source_commit: str,
    vendored_newton_commit: str,
    paper_source_version: str = "2603.08079v2",
    config: SpinningBoxRunConfig | None = None,
) -> ClaimReport:
    dt = 0.01 if config is None else config.time_step_s
    step_count = 4 if config is None else config.step_count
    q = mabd.pack_q(np.eye(3), np.zeros(3)) if config is None else config.initial_q.copy()
    qd = np.linspace(-0.2, 0.25, 12) if config is None else config.initial_qd.copy()
    initial_momentum = qd.copy()
    initial_energy = _kinetic_energy(qd)
    oracle_config = mabd.MABDCPUOracleConfig(bodies=[_oracle_body(config)])
```

Use config-backed report fields:

```python
    report = ClaimReport(
        claim_id="experiment.single_body.spinning_box",
        scene_id="single_body_spinning_box" if config is None else config.scene_id,
        asset_hashes={"primitive_cube": "not_applicable_procedural"},
        solver_mode="mabd_cpu_oracle_development",
        backend="cpu_numpy",
        baseline_lane="mabd_newton" if config is None else config.baseline_lane,
        expected={"paper_claim_status": "requires comparative baseline lanes before pass"},
        observed={
            "step_count": step_count,
            "time_step_s": dt,
            "energy_drift": energy_drift,
            "generalized_momentum_delta_norm": momentum_delta,
        },
        threshold={
            "energy_drift": 1.0e-12,
            "generalized_momentum_delta_norm": 1.0e-12,
        }
        if config is None
        else config.thresholds,
        unit="json_report",
        status=EvidenceStatus.INCOMPLETE if config is None else config.report_status,
        failure_reason="full paper claim still requires rbd_implicit_baseline"
        if config is None
        else config.failure_reason,
        timing_distribution={"step_count": step_count, "scope": "not_timed"},
        raw_outputs={"time_series": "not_written"},
        plot_paths={},
        source_commit=source_commit,
        vendored_newton_commit=vendored_newton_commit,
        paper_source_version=paper_source_version,
    )
```

- [ ] **Step 4: Run tests and commit**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_single_body_report_lane tests.test_experiment_run_configs tests.test_reporting_contracts
/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check src/mabd_reproduction/single_body_reports.py tests/test_single_body_report_lane.py
```

Expected: `Ran 9 tests, OK` and `All checks passed!`.

Commit:

```bash
git add src/mabd_reproduction/single_body_reports.py tests/test_single_body_report_lane.py
git commit -m "feat: drive spinning-box report from config"
```

### Task 3: Record Phase 13 Evidence And Guard Claim Boundaries

**Files:**
- Modify: `docs/reference/claim-boundaries.md`
- Modify: `scripts/validate_docs.py`
- Modify: `tests/test_phase0_bootstrap.py`
- Create: `docs/records/2026-05-17-phase13-configured-spinning-box.md`

- [ ] **Step 1: Write boundary and validator tests**

Add tests to `tests/test_phase0_bootstrap.py` requiring:

```python
    def test_phase13_configured_spinning_box_lane_is_bounded(self) -> None:
        text = (ROOT / "docs/reference/claim-boundaries.md").read_text()
        normalized_text = " ".join(text.split())

        self.assertIn("Phase 13 verifies a config-driven single-body spinning-box", text)
        self.assertIn("per-scene config schema", normalized_text)
        self.assertIn("report remains `incomplete`", normalized_text)
        self.assertIn("Phase 13 does not verify the paper spinning-box experiment", text)
        self.assertIn("RBD baselines", normalized_text)
        self.assertIn("any passed `experiment.*` claim", normalized_text)

    def test_phase13_record_has_required_evidence_fields(self) -> None:
        text = (ROOT / "docs/records/2026-05-17-phase13-configured-spinning-box.md").read_text()

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
            "## Metrics And Thresholds",
            "Report validation rejects `status=passed`",
            "No `experiment.*` claim is passed in this phase.",
        ):
            self.assertIn(snippet, text)
```

- [ ] **Step 2: Run the failing tests**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_phase0_bootstrap
```

Expected: fail because Phase 13 boundary and record do not exist yet.

- [ ] **Step 3: Update docs and validator**

Update `docs/reference/claim-boundaries.md`:

- Add Current bullet for Phase 13 config-driven spinning-box lane.
- Add Verified bullets stating Phase 13 verifies only the per-scene config schema, matrix alignment, and config-driven M-ABD development report that remains `incomplete`.
- Add non-claim bullet excluding paper spinning-box experiment, RBD baselines, timing, rendered output, trajectory agreement, and passed `experiment.*`.

Create `docs/records/2026-05-17-phase13-configured-spinning-box.md` with the same record sections used by Phase 12, including config path, commits, paper checksums, environment, metrics, TDD RED/GREEN, final verification, and claim impact.

Update `scripts/validate_docs.py`:

- Add Phase 13 record to `REQUIRED_PATHS`.
- Add `validate_phase13_record()` requiring the snippets from the bootstrap test and forbidding overclaims.
- Include Phase 13 record in passed-claim citation text.
- Update stdout to `Phase 0/1/2/3/4/5/6/7/8/9/10/11/12/13 docs/provenance validation passed`.

- [ ] **Step 4: Run validation and commit docs**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_phase0_bootstrap
git diff --check
```

Expected: docs validator prints Phase 0 through Phase 13, bootstrap tests pass, whitespace check is clean.

Commit:

```bash
git add docs/reference/claim-boundaries.md scripts/validate_docs.py tests/test_phase0_bootstrap.py docs/records/2026-05-17-phase13-configured-spinning-box.md
git commit -m "docs: record Phase 13 configured spinning-box lane"
```

### Task 4: Final Verification, Review, Merge, Push

**Files:**
- No new source files unless review finds a defect.

- [ ] **Step 1: Run full branch verification**

Run:

```bash
/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_run_configs tests.test_single_body_report_lane tests.test_reporting_contracts tests.test_phase0_bootstrap
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"
git diff --check
```

- [ ] **Step 2: Refresh record with actual counts**

Edit `docs/records/2026-05-17-phase13-configured-spinning-box.md` so final verification lists the actual command outputs and test counts from Step 1.

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
git diff --check
```

Commit:

```bash
git add docs/records/2026-05-17-phase13-configured-spinning-box.md
git commit -m "docs: refresh Phase 13 verification evidence"
```

- [ ] **Step 3: Request review**

Request two reviews:

- Implementation review of `experiment_configs.py`, `single_body_reports.py`, and tests.
- Docs/provenance review of Phase 13 boundary, record, and validator.

Fix Critical or Medium findings with TDD where applicable, then re-run the focused and full gates.

- [ ] **Step 4: Merge and push**

From `/cpfs/user/zhuzihou/dev/mabd-newton`:

```bash
git fetch git@github.com:jandan138/mabd-newton.git main
git merge --ff-only phase13-configured-spinning-box
/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"
git diff --check
GIT_TERMINAL_PROMPT=0 git push git@github.com:jandan138/mabd-newton.git main
git ls-remote git@github.com:jandan138/mabd-newton.git refs/heads/main
```

Expected: pushed remote `main` equals local `HEAD`.

---

## Self-Review

- Spec coverage: This plan advances the full reproduction design by adding the first per-scene experiment config and config-driven M-ABD lane evidence while preserving the no-experiment-passed boundary.
- Placeholder scan: No placeholder markers or unspecified implementation steps remain.
- Type consistency: `SpinningBoxRunConfig`, `ExperimentRunConfigError`, `load_spinning_box_config`, and `validate_spinning_box_config_against_matrix` are defined before later tasks use them.
