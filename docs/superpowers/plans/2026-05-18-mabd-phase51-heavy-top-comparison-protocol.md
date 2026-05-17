# Phase 51 Heavy-Top Comparison Protocol Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an incomplete, machine-checkable heavy-top comparison protocol that consumes the existing RK4 reference and Newton M-ABD diagnostic reports.

**Architecture:** Reuse the existing `comparison_reports.py` pattern. Extend heavy-top config parsing and runner dispatch, then generate a committed comparison report and docs/provenance evidence while preserving claim boundaries.

**Tech Stack:** Python 3.10, unittest, YAML configs, existing `ClaimReport` JSON schema, vendored Newton import through `PYTHONPATH=src:vendor/newton`.

---

### Task 1: Config Schema And Runner Contract

**Files:**
- Modify: `configs/experiments/single_body_heavy_top.yaml`
- Modify: `configs/experiments/paper_experiment_matrix.yaml`
- Modify: `docs/reference/paper-claims.yaml`
- Modify: `src/mabd_reproduction/experiment_configs.py`
- Modify: `tests/test_experiment_run_configs.py`

- [ ] **Step 1: Write failing config tests**

Add assertions to `tests/test_experiment_run_configs.py` that:

```python
config = load_heavy_top_config(ROOT / "configs/experiments/single_body_heavy_top.yaml")
self.assertEqual(config.comparison.output_report, "reports/experiment_matrix/single_body_heavy_top_comparison.json")
self.assertEqual(config.comparison.required_lanes, ("mabd_newton", "rbd_rk4_reference"))
self.assertEqual(config.comparison.required_metrics, ("precession_velocity_error", "nutation_angle_error", "energy_drift"))
self.assertIn("max_sample_time_delta_s", config.comparison.thresholds)
```

Also mutate the loaded YAML to prove validation rejects:

```python
data["comparison"]["required_lanes"] = ["mabd_newton"]
with self.assertRaisesRegex(ExperimentRunConfigError, "comparison.required_lanes"):
    _load_heavy_top_from_data(data)
```

- [ ] **Step 2: Run the config tests and verify RED**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_run_configs
```

Expected: failure because `HeavyTopRunConfig` has no `comparison` field yet.

- [ ] **Step 3: Implement config parsing**

In `src/mabd_reproduction/experiment_configs.py` add:

```python
@dataclass(frozen=True)
class HeavyTopComparisonConfig:
    output_report: str
    required_lanes: tuple[str, ...]
    required_metrics: tuple[str, ...]
    thresholds: dict[str, float]
```

Add constants:

```python
HEAVY_TOP_COMPARISON_REQUIRED_LANES = ("mabd_newton", "rbd_rk4_reference")
HEAVY_TOP_COMPARISON_REQUIRED_METRICS = (
    "precession_velocity_error",
    "nutation_angle_error",
    "energy_drift",
)
HEAVY_TOP_COMPARISON_THRESHOLD_KEYS = frozenset({"max_sample_time_delta_s"})
```

Parse `comparison` with `_require_heavy_top_comparison(...)`, attach it to
`HeavyTopRunConfig`, and validate that the comparison required metrics match
the heavy-top matrix metrics.

- [ ] **Step 4: Update YAML blockers**

In `single_body_heavy_top.yaml` add the `comparison` block from the design spec
and change the report failure text to
`heavy_top_comparison_report_incomplete`.

In `paper_experiment_matrix.yaml` and `paper-claims.yaml`, replace
`heavy_top_comparison_report_missing` with
`heavy_top_comparison_report_incomplete`.

- [ ] **Step 5: Run config tests and verify GREEN**

Run the same unittest command. Expected: all config tests pass.

### Task 2: Heavy-Top Comparison Report Writer

**Files:**
- Modify: `src/mabd_reproduction/comparison_reports.py`
- Create: `tests/test_heavy_top_comparison_reports.py`

- [ ] **Step 1: Write failing report tests**

Create `tests/test_heavy_top_comparison_reports.py` with tests that generate
temporary RK4 and M-ABD reports using existing report writers, call
`write_heavy_top_comparison_report(...)`, and assert:

```python
self.assertEqual(report.baseline_lane, "heavy_top_comparison_protocol")
self.assertEqual(report.solver_mode, "heavy_top_multilane_comparison_development")
self.assertEqual(report.backend, "report_protocol")
self.assertEqual(report.status, EvidenceStatus.INCOMPLETE)
self.assertFalse(report.observed["full_experiment_claim_passed"])
self.assertEqual(report.observed["missing_required_lanes"], [])
self.assertIn("heavy_top_comparison_pass_gate_not_enabled", report.observed["blocking_reasons"])
self.assertIn("heavy_top_comparison_report_incomplete", report.observed["blocking_reasons"])
self.assertEqual(
    report.observed["missing_paper_metrics"],
    [
        "precession_velocity_error:mabd_precession_velocity_samples_missing",
        "nutation_angle_error:paper_reference_curve_missing",
        "energy_drift:mabd_energy_drift_missing",
    ],
)
self.assertIn("input_report_provenance", report.observed)
self.assertIn("sample_index_differences", report.observed)
```

Add identity rejection tests for wrong `claim_id`, wrong `baseline_lane`,
wrong solver mode/backend/status, and nonfinite sample values.

- [ ] **Step 2: Run report tests and verify RED**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_heavy_top_comparison_reports
```

Expected: import failure because `write_heavy_top_comparison_report` does not
exist.

- [ ] **Step 3: Implement report writer**

In `comparison_reports.py`, add heavy-top constants and helper functions:

```python
HEAVY_TOP_REQUIRED_METRICS = (
    "precession_velocity_error",
    "nutation_angle_error",
    "energy_drift",
)
```

Implement strict lane report validation, finite scalar extraction, provenance
hashing, compact sample row parsing, sample-index differences, lane metric
snapshots, and `write_heavy_top_comparison_report(...)`.

The writer must:

- load both reports;
- reject wrong claim, scene, baseline lane, solver mode, backend, status, asset
  hash, or `full_experiment_claim_passed` overclaim;
- emit JSON without bare `NaN` or `Infinity`;
- always return `EvidenceStatus.INCOMPLETE`;
- include blockers for lane incompleteness, source gaps, missing paper metrics,
  time grid mismatch, and the disabled pass gate.

- [ ] **Step 4: Run report tests and verify GREEN**

Run the heavy-top comparison report unittest. Expected: all tests pass.

### Task 3: Runner And CLI Dispatch

**Files:**
- Modify: `src/mabd_reproduction/experiment_runner.py`
- Modify: `scripts/run_experiment.py`
- Modify: `tests/test_experiment_runner.py`

- [ ] **Step 1: Write failing runner tests**

Add `run_heavy_top_comparison(...)` tests that require both `--mabd-report`
and `--rbd-report`, write the configured comparison output path, and expose CLI
lane `heavy_top_comparison`.

- [ ] **Step 2: Run runner tests and verify RED**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_runner
```

Expected: failure because runner and CLI dispatch are missing.

- [ ] **Step 3: Implement runner and CLI**

Add `run_heavy_top_comparison(...)` to `experiment_runner.py`, export it from
`__all__`, import it in `scripts/run_experiment.py`, add
`"heavy_top_comparison"` to `--lane` choices, and dispatch it with
`args.mabd_report`, `args.rbd_report`, and the configured output path.

- [ ] **Step 4: Run runner tests and verify GREEN**

Run the same unittest command. Expected: all runner tests pass.

### Task 4: Artifact, Claim Boundaries, And Validator

**Files:**
- Create: `reports/experiment_matrix/single_body_heavy_top_comparison.json`
- Create: `docs/records/2026-05-18-phase51-heavy-top-comparison-protocol.md`
- Modify: `docs/reference/claim-boundaries.md`
- Modify: `scripts/validate_docs.py`
- Modify: `tests/test_phase0_bootstrap.py`

- [ ] **Step 1: Generate comparison artifact**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/run_experiment.py \
  --lane heavy_top_comparison \
  --config configs/experiments/single_body_heavy_top.yaml \
  --matrix configs/experiments/paper_experiment_matrix.yaml \
  --mabd-report reports/experiment_matrix/single_body_heavy_top_mabd_newton.json \
  --rbd-report reports/experiment_matrix/single_body_heavy_top_rk4_reference.json \
  --source-commit "$(git rev-parse --short HEAD)" \
  --vendored-newton-commit 96713fa965463b69c229a4d30582c733ff3526bb
```

Expected: summary JSON with `baseline_lane` equal
`heavy_top_comparison_protocol` and status `incomplete`.

- [ ] **Step 2: Add failing docs/bootstrap tests**

Extend `tests/test_phase0_bootstrap.py` to require Phase51 claim-boundary
bullets, record snippets, comparison report path, solver mode
`heavy_top_multilane_comparison_development`, blocker
`heavy_top_comparison_report_incomplete`, a new Forbidden Claims bullet for
the heavy-top comparison protocol, and no passed `experiment.*` claims.

- [ ] **Step 3: Update claim boundaries and validator**

Update `docs/reference/claim-boundaries.md` with Phase51 current, verified,
non-claim, and forbidden bullets. Update `scripts/validate_docs.py` to Phase
0-51, add required paths, validate the comparison report SHA256 recorded in the
record, and ensure the report remains incomplete with source-gap blockers.

- [ ] **Step 4: Run docs tests and verify GREEN**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_heavy_top_comparison_reports tests.test_experiment_run_configs tests.test_experiment_runner tests.test_phase0_bootstrap
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
```

Expected: tests and docs/provenance validation pass.

### Task 5: Final Verification And Commit

**Files:**
- All touched files.

- [ ] **Step 1: Run full verification**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/env/readiness_check.py
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"
npm --prefix site run validate
git diff --check
```

Expected: all commands exit 0.

- [ ] **Step 2: Commit Phase51**

Commit the plan/spec first if useful, then implementation and evidence with
message:

```bash
git commit -m "Add Phase51 heavy top comparison protocol"
```

No generated videos, raw logs, or raw paper assets are committed.
