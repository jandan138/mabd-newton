# Phase 12 Single-Body Report Lane Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a machine-checkable development report lane for the single-body spinning-box claim without marking any paper experiment claim passed.

**Architecture:** Extend the reproduction report contract to the full required schema and add JSON read/write validation. Add a deterministic single-body M-ABD development report generator that runs a tiny CPU oracle trajectory, records momentum/energy diagnostics, and writes an `incomplete` report because comparative baseline lanes are still missing.

**Tech Stack:** Python 3.10, dataclasses, JSON, NumPy, vendored Newton M-ABD CPU oracle, `unittest`, ruff, docs/provenance validator.

---

### File Structure

- Modify `src/mabd_reproduction/reporting.py`.
  Add full report schema fields, serialization, load/write helpers, and validation.
- Create `src/mabd_reproduction/single_body_reports.py`.
  Own deterministic single-body M-ABD development report generation.
- Create `tests/test_reporting_contracts.py`.
  Tests report schema validation, JSON round trip, and missing-key rejection.
- Create `tests/test_single_body_report_lane.py`.
  Tests the spinning-box development report writer using a temporary directory.
- Modify `docs/reference/claim-boundaries.md`.
  Add bounded Phase 12 report-lane evidence and non-claims.
- Modify `scripts/validate_docs.py` and `tests/test_phase0_bootstrap.py`.
  Require the Phase 12 record and boundary snippets.
- Create `docs/records/2026-05-17-phase12-single-body-report-lane.md`.
  Record commands, environment, paper source checksums, verification evidence, and non-claims.

### Task 1: RED Tests For Report Schema And JSON IO

**Files:**
- Create: `tests/test_reporting_contracts.py`

- [ ] **Step 1: Add report round-trip tests**

Create `tests/test_reporting_contracts.py`:

```python
from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from mabd_reproduction.reporting import (
    ClaimReport,
    EvidenceStatus,
    load_claim_report,
    validate_claim_report_mapping,
    write_claim_report,
)


def _report() -> ClaimReport:
    return ClaimReport(
        claim_id="experiment.single_body.spinning_box",
        scene_id="single_body_spinning_box",
        asset_hashes={"primitive_cube": "not_applicable_procedural"},
        solver_mode="mabd_cpu_oracle_development",
        backend="cpu_numpy",
        baseline_lane="mabd_newton",
        expected={"energy_drift_max": 1.0e-12},
        observed={"energy_drift": 0.0},
        threshold={"energy_drift": 1.0e-12},
        unit="json_report",
        status=EvidenceStatus.INCOMPLETE,
        failure_reason="full paper claim still requires rbd_implicit_baseline",
        timing_distribution={"step_count": 4},
        raw_outputs={"time_series": "not_written"},
        plot_paths={},
        source_commit="abc123",
        vendored_newton_commit="96713fa965463b69c229a4d30582c733ff3526bb",
        paper_source_version="2603.08079v2",
    )


class ReportingContractTests(unittest.TestCase):
    def test_claim_report_json_round_trips_required_fields(self) -> None:
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "report.json"
            write_claim_report(_report(), path)

            loaded = load_claim_report(path)

        self.assertEqual(loaded.claim_id, "experiment.single_body.spinning_box")
        self.assertEqual(loaded.status, EvidenceStatus.INCOMPLETE)
        self.assertEqual(loaded.asset_hashes["primitive_cube"], "not_applicable_procedural")
        self.assertEqual(loaded.timing_distribution["step_count"], 4)

    def test_report_validation_rejects_missing_full_schema_keys(self) -> None:
        mapping = _report().to_mapping()
        mapping.pop("asset_hashes")

        with self.assertRaisesRegex(ValueError, "asset_hashes"):
            validate_claim_report_mapping(mapping)

    def test_report_validation_rejects_unknown_status(self) -> None:
        mapping = _report().to_mapping()
        mapping["status"] = "almost_passed"

        with self.assertRaisesRegex(ValueError, "status"):
            validate_claim_report_mapping(mapping)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run RED**

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_reporting_contracts
```

Expected: fail because `load_claim_report`, `write_claim_report`, `validate_claim_report_mapping`, `ClaimReport.to_mapping`, and the new full schema fields do not exist yet.

### Task 2: Implement Full Report Schema Helpers

**Files:**
- Modify: `src/mabd_reproduction/reporting.py`

- [ ] **Step 1: Extend `ClaimReport`**

Update `ClaimReport` fields to exactly:

```python
claim_id: str
scene_id: str
asset_hashes: dict[str, str]
solver_mode: str
backend: str
baseline_lane: str
expected: dict[str, Any]
observed: dict[str, Any]
threshold: dict[str, Any]
unit: str
status: EvidenceStatus
failure_reason: str
timing_distribution: dict[str, Any]
raw_outputs: dict[str, str]
plot_paths: dict[str, str]
source_commit: str
vendored_newton_commit: str
paper_source_version: str
```

- [ ] **Step 2: Add serialization helpers**

Implement:

```python
def _require_mapping(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = data.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"{key} must be a mapping")
    return dict(value)


def _require_str_mapping(data: dict[str, Any], key: str) -> dict[str, str]:
    value = _require_mapping(data, key)
    if not all(isinstance(k, str) and isinstance(v, str) for k, v in value.items()):
        raise ValueError(f"{key} must map strings to strings")
    return {str(k): str(v) for k, v in value.items()}


def _require_str(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{key} must be a non-empty string")
    return value


def validate_claim_report_mapping(data: dict[str, Any]) -> ClaimReport:
    missing = sorted(REQUIRED_REPORT_KEYS - set(data))
    if missing:
        raise ValueError("claim report missing required keys: " + ", ".join(missing))
    try:
        status = EvidenceStatus(str(data["status"]))
    except ValueError as exc:
        raise ValueError(f"status must be one of {sorted(s.value for s in EvidenceStatus)}") from exc
    return ClaimReport(
        claim_id=_require_str(data, "claim_id"),
        scene_id=_require_str(data, "scene_id"),
        asset_hashes=_require_str_mapping(data, "asset_hashes"),
        solver_mode=_require_str(data, "solver_mode"),
        backend=_require_str(data, "backend"),
        baseline_lane=_require_str(data, "baseline_lane"),
        expected=_require_mapping(data, "expected"),
        observed=_require_mapping(data, "observed"),
        threshold=_require_mapping(data, "threshold"),
        unit=_require_str(data, "unit"),
        status=status,
        failure_reason=_require_str(data, "failure_reason"),
        timing_distribution=_require_mapping(data, "timing_distribution"),
        raw_outputs=_require_str_mapping(data, "raw_outputs"),
        plot_paths=_require_str_mapping(data, "plot_paths"),
        source_commit=_require_str(data, "source_commit"),
        vendored_newton_commit=_require_str(data, "vendored_newton_commit"),
        paper_source_version=_require_str(data, "paper_source_version"),
    )
```

Every required string must be non-empty. Mapping fields must be mappings. `asset_hashes`, `raw_outputs`, and `plot_paths` must have string keys and string values.

- [ ] **Step 3: Add JSON read/write**

Implement:

```python
def claim_report_to_mapping(report: ClaimReport) -> dict[str, Any]:
    data = asdict(report)
    data["status"] = report.status.value
    return data

def write_claim_report(report: ClaimReport, path: str | Path) -> None:
    report_path = Path(path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report.to_mapping(), indent=2, sort_keys=True) + "\n", encoding="utf-8")

def load_claim_report(path: str | Path) -> ClaimReport:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("claim report JSON must contain an object")
    return validate_claim_report_mapping(data)
```

Add `ClaimReport.to_mapping(self)` that calls `claim_report_to_mapping(self)`.

- [ ] **Step 4: Run GREEN**

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_reporting_contracts tests.test_phase0_bootstrap
```

Expected: passes after updating any bootstrap expectation for the expanded `REQUIRED_REPORT_KEYS`.

- [ ] **Step 5: Commit**

```bash
git add src/mabd_reproduction/reporting.py tests/test_reporting_contracts.py tests/test_phase0_bootstrap.py
git commit -m "feat: add full claim report JSON contract"
```

### Task 3: RED Tests For Single-Body Development Report Lane

**Files:**
- Create: `tests/test_single_body_report_lane.py`

- [ ] **Step 1: Add report lane test**

Create `tests/test_single_body_report_lane.py`:

```python
from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from mabd_reproduction.reporting import EvidenceStatus, load_claim_report
from mabd_reproduction.single_body_reports import write_spinning_box_development_report


class SingleBodyReportLaneTests(unittest.TestCase):
    def test_spinning_box_development_report_is_machine_checkable(self) -> None:
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "single_body_spinning_box.json"
            report = write_spinning_box_development_report(
                path,
                source_commit="test-source",
                vendored_newton_commit="test-newton",
            )
            loaded = load_claim_report(path)

        self.assertEqual(report.claim_id, "experiment.single_body.spinning_box")
        self.assertEqual(loaded.status, EvidenceStatus.INCOMPLETE)
        self.assertEqual(loaded.baseline_lane, "mabd_newton")
        self.assertIn("rbd_implicit_baseline", loaded.failure_reason)
        self.assertEqual(loaded.observed["step_count"], 4)
        self.assertLessEqual(loaded.observed["energy_drift"], loaded.threshold["energy_drift"])
        self.assertLessEqual(
            loaded.observed["generalized_momentum_delta_norm"],
            loaded.threshold["generalized_momentum_delta_norm"],
        )


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run RED**

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_single_body_report_lane
```

Expected: fail because `mabd_reproduction.single_body_reports` does not exist.

### Task 4: Implement Single-Body Development Report Lane

**Files:**
- Create: `src/mabd_reproduction/single_body_reports.py`
- Modify: `src/mabd_reproduction/__init__.py`

- [ ] **Step 1: Add deterministic report generator**

Create `src/mabd_reproduction/single_body_reports.py`:

```python
from __future__ import annotations

from pathlib import Path

import numpy as np

from newton.solvers import mabd

from .reporting import ClaimReport, EvidenceStatus, write_claim_report


def _oracle_body() -> mabd.MABDCPUOracleBody:
    return mabd.MABDCPUOracleBody(
        precompute=mabd.SingleBodyABDPrecompute(
            rest_points=np.zeros((4, 3), dtype=float),
            masses=np.ones(4, dtype=float),
            mass_matrix=np.eye(12),
            stiffness_matrix=np.zeros((12, 12), dtype=float),
        )
    )


def _kinetic_energy(qd: np.ndarray) -> float:
    return float(0.5 * qd @ qd)


def write_spinning_box_development_report(
    path: str | Path,
    *,
    source_commit: str,
    vendored_newton_commit: str,
    paper_source_version: str = "2603.08079v2",
) -> ClaimReport:
    dt = 0.01
    step_count = 4
    q = mabd.pack_q(np.eye(3), np.zeros(3))
    qd = np.linspace(-0.2, 0.25, 12)
    initial_momentum = qd.copy()
    initial_energy = _kinetic_energy(qd)
    config = mabd.MABDCPUOracleConfig(bodies=[_oracle_body()])
    for _step in range(step_count):
        result = mabd.solve_cpu_oracle_step(q=[q], qd=[qd], dt=dt, config=config)
        q = result.q[0]
        qd = result.qd[0]
    energy_drift = abs(_kinetic_energy(qd) - initial_energy)
    momentum_delta = float(np.linalg.norm(qd - initial_momentum))
    report = ClaimReport(
        claim_id="experiment.single_body.spinning_box",
        scene_id="single_body_spinning_box",
        asset_hashes={"primitive_cube": "not_applicable_procedural"},
        solver_mode="mabd_cpu_oracle_development",
        backend="cpu_numpy",
        baseline_lane="mabd_newton",
        expected={"paper_claim_status": "requires comparative baseline lanes before pass"},
        observed={
            "step_count": step_count,
            "time_step_s": dt,
            "energy_drift": energy_drift,
            "generalized_momentum_delta_norm": momentum_delta,
        },
        threshold={"energy_drift": 1.0e-12, "generalized_momentum_delta_norm": 1.0e-12},
        unit="json_report",
        status=EvidenceStatus.INCOMPLETE,
        failure_reason="full paper claim still requires rbd_implicit_baseline",
        timing_distribution={"step_count": step_count, "scope": "not_timed"},
        raw_outputs={"time_series": "not_written"},
        plot_paths={},
        source_commit=source_commit,
        vendored_newton_commit=vendored_newton_commit,
        paper_source_version=paper_source_version,
    )
    write_claim_report(report, path)
    return report
```

- [ ] **Step 2: Export module name**

No public import is required from `__init__.py`; keep imports explicit to avoid import-time Newton dependency for basic package import.

- [ ] **Step 3: Run GREEN**

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_single_body_report_lane tests.test_reporting_contracts
```

Expected: passes.

- [ ] **Step 4: Commit**

```bash
git add src/mabd_reproduction/single_body_reports.py tests/test_single_body_report_lane.py
git commit -m "feat: add single-body development report lane"
```

### Task 5: Documentation, Validator, And Record

**Files:**
- Modify: `docs/reference/claim-boundaries.md`
- Modify: `scripts/validate_docs.py`
- Modify: `tests/test_phase0_bootstrap.py`
- Create: `docs/records/2026-05-17-phase12-single-body-report-lane.md`

- [ ] **Step 1: Add Phase 12 boundaries**

Add to Current:

```markdown
- This repository contains Phase 12 full-schema claim report JSON validation and
  a single-body spinning-box M-ABD development report lane after the Phase 12
  record is created.
```

Add to Verified:

```markdown
- Phase 12 verifies full-schema `ClaimReport` JSON round trips, required-key
  validation, invalid-status rejection, and a deterministic single-body
  spinning-box M-ABD development report that remains `incomplete`.
- Phase 12 does not verify the paper spinning-box experiment, paper timing,
  RK4/RBD/analytic baselines, rendered output, paper trajectory agreement, or
  any passed `experiment.*` claim.
```

- [ ] **Step 2: Add validator requirements**

Update `scripts/validate_docs.py` to:

- include `docs/records/2026-05-17-phase12-single-body-report-lane.md` in `REQUIRED_PATHS`;
- require Phase 12 boundary and non-claim snippets;
- add `validate_phase12_record()` requiring status, commits, report schema, `write_spinning_box_development_report`, `EvidenceStatus.INCOMPLETE`, no passed experiment claim, and final verification snippets;
- print `Phase 0/1/2/3/4/5/6/7/8/9/10/11/12 docs/provenance validation passed`.

- [ ] **Step 3: Add bootstrap tests**

Add tests in `tests/test_phase0_bootstrap.py` that check Phase 12 boundary text, record fields, and `/12` validator output.

- [ ] **Step 4: Create record**

Create `docs/records/2026-05-17-phase12-single-body-report-lane.md` with:

- status `passed`;
- plan/implementation commits;
- explicit non-claims;
- TDD evidence;
- final verification placeholder;
- claim impact: no `experiment.*` claim passed.

- [ ] **Step 5: Run docs GREEN**

```bash
/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_phase0_bootstrap
git diff --check
```

- [ ] **Step 6: Commit**

```bash
git add docs/reference/claim-boundaries.md scripts/validate_docs.py tests/test_phase0_bootstrap.py docs/records/2026-05-17-phase12-single-body-report-lane.md
git commit -m "docs: record Phase 12 single-body report lane"
```

### Task 6: Final Verification And Merge

**Files:**
- No new files.

- [ ] **Step 1: Run final branch verification**

```bash
/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_reporting_contracts tests.test_single_body_report_lane tests.test_phase0_bootstrap
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"
git diff --check
```

- [ ] **Step 2: Request review**

Request focused review for report schema correctness, no experiment overclaiming, and deterministic report-lane behavior.

- [ ] **Step 3: Merge and push after review**

Fast-forward merge into `main`, rerun the same verification on merged `main`, push to `git@github.com:jandan138/mabd-newton.git main`, fetch back, verify `origin/main` equals local `HEAD`, and remove the Phase 12 worktree/branch.
