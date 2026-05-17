# Phase 28 Spinning-Box Paper Horizon Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a paper-horizon M-ABD diagnostic report for the single-body spinning-box claim without passing the M-ABD lane or the full paper experiment.

**Architecture:** Keep the existing four-step `mabd_newton` development report unchanged. Add a nested paper-horizon config and a separate report writer that scans every simulation step for extrema and threshold violations while storing compact samples. Expose the diagnostic through a distinct runner/CLI lane, and keep comparison semantics incomplete because Phase 28 does not emit `lane_gate_status`.

**Tech Stack:** Python 3.10, NumPy, vendored Newton M-ABD CPU oracle, existing `ClaimReport` JSON schema, YAML config parsing, unittest.

---

### Task 1: Paper-Horizon Config Contract

**Files:**
- Modify: `configs/experiments/single_body_spinning_box.yaml`
- Modify: `src/mabd_reproduction/experiment_configs.py`
- Modify: `tests/test_experiment_run_configs.py`

- [ ] **Step 1: Write failing config tests**

Add assertions to `test_spinning_box_config_is_machine_checkable`:

```python
self.assertEqual(config.paper_horizon.duration_s, 10.0)
self.assertEqual(config.paper_horizon.time_step_grid_s, (0.01, 0.001))
self.assertEqual(config.paper_horizon.sample_count, 11)
self.assertEqual(
    config.paper_horizon.output_report,
    "reports/experiment_matrix/single_body_spinning_box_paper_horizon.json",
)
self.assertEqual(
    config.paper_horizon.figure_pdf_sha256,
    "7669b062348324a3b0090cc9f44930655c83233a87f63389db9198b88f95ae80",
)
for key in (
    "max_linear_momentum_error",
    "max_angular_momentum_error",
    "max_relative_kinetic_energy_drift",
    "max_relative_total_energy_drift",
    "max_abs_det_minus_one",
    "min_singular_value",
    "max_singular_value",
    "max_affine_orthogonality_error",
    "max_residual_norm",
):
    self.assertIn(key, config.paper_horizon.thresholds)
```

Add a rejection test:

```python
def test_spinning_box_config_rejects_bad_paper_horizon_grid(self) -> None:
    source = self._config_mapping()
    source["paper_horizon"]["time_step_grid_s"] = [0.01, "0.001"]
    with TemporaryDirectory() as tmpdir:
        path = self._write_config(tmpdir, source)
        with self.assertRaisesRegex(ExperimentRunConfigError, "time_step_grid_s"):
            load_spinning_box_config(path)
```

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_run_configs
```

Expected before implementation: attribute or key failure because `paper_horizon` is not parsed.

- [ ] **Step 2: Implement config parsing**

Add:

```python
@dataclass(frozen=True)
class SpinningBoxPaperHorizonConfig:
    duration_s: float
    time_step_grid_s: tuple[float, ...]
    sample_count: int
    output_report: str
    figure_pdf_sha256: str
    figure_text_source: str
    thresholds: dict[str, float]
```

Add `paper_horizon: SpinningBoxPaperHorizonConfig` to `SpinningBoxRunConfig`.
Parse `paper_horizon` with positive numeric duration, positive finite numeric
step grid, positive integer sample count, non-empty output report, non-empty
figure provenance strings, and the required threshold keys listed above.

- [ ] **Step 3: Add YAML config section**

Add:

```yaml
paper_horizon:
  duration_s: 10.0
  time_step_grid_s: [0.01, 0.001]
  sample_count: 11
  output_report: reports/experiment_matrix/single_body_spinning_box_paper_horizon.json
  figure_pdf_sha256: 7669b062348324a3b0090cc9f44930655c83233a87f63389db9198b88f95ae80
  figure_text_source: "pdftotext /tmp/mabd-paper/source/images/cube/roll_cube.pdf -"
  thresholds:
    max_linear_momentum_error: 1.0e-6
    max_angular_momentum_error: 1.0e-6
    max_relative_kinetic_energy_drift: 1.0e-1
    max_relative_total_energy_drift: 1.0e-1
    max_abs_det_minus_one: 1.0e-1
    min_singular_value: 0.9
    max_singular_value: 1.1
    max_affine_orthogonality_error: 1.0e-1
    max_residual_norm: 1.0e-6
```

- [ ] **Step 4: Run focused test and commit**

Run the command from Step 1. Expected: all config tests pass.

Commit:

```bash
git add configs/experiments/single_body_spinning_box.yaml src/mabd_reproduction/experiment_configs.py tests/test_experiment_run_configs.py
git commit -m "feat: add spinning-box paper horizon config"
```

### Task 2: M-ABD Paper-Horizon Diagnostic Report

**Files:**
- Modify: `src/mabd_reproduction/single_body_reports.py`
- Modify: `tests/test_single_body_report_lane.py`

- [ ] **Step 1: Write failing report tests**

Add a test that writes `write_spinning_box_paper_horizon_report(...)` and asserts:

```python
self.assertEqual(loaded.status, EvidenceStatus.INCOMPLETE)
self.assertEqual(loaded.baseline_lane, "mabd_newton")
self.assertEqual(loaded.solver_mode, "mabd_cpu_oracle_paper_horizon_diagnostic")
self.assertNotIn("lane_gate_status", loaded.observed)
self.assertEqual(loaded.observed["paper_horizon_duration_s"], 10.0)
self.assertEqual(loaded.observed["paper_step_sizes_s"], [0.01, 0.001])
self.assertEqual(
    loaded.observed["mabd_paper_horizon_status"],
    "development_gap_observed",
)
self.assertIn("mabd_newton_report_incomplete", loaded.observed["blocking_reasons"])
self.assertEqual(len(loaded.observed["paper_horizon_results"]), 2)
```

For every result entry, assert:

```python
self.assertIn("steps_attempted", entry)
self.assertIn("steps_completed", entry)
self.assertIn("first_nonfinite_step", entry)
self.assertIn("threshold_violations", entry)
self.assertIn("trajectory_samples", entry)
self.assertLessEqual(len(entry["trajectory_samples"]), config.paper_horizon.sample_count)
self.assertIn("max_affine_orthogonality_error", entry)
self.assertIn("max_affine_orthogonality_error_step_index", entry)
self.assertIn("kinetic_energy_initial_j", entry)
self.assertIn("elastic_energy_initial_j", entry)
self.assertIn("total_energy_initial_j", entry)
self.assertIn("max_relative_total_energy_drift", entry)
self.assertIn("max_abs_det_minus_one", entry["threshold_violations"])
self.assertIn("max_relative_total_energy_drift", entry["threshold_violations"])
```

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_single_body_report_lane
```

Expected before implementation: import failure for the new writer.

- [ ] **Step 2: Implement every-step scanner**

Add helpers that:

- compute `steps = round(duration_s / dt)` and require exact round-trip within `1e-12`;
- compute compact sample indices with `np.linspace(0, steps, sample_count)`;
- run `mabd.solve_cpu_oracle_step(...)` for every step;
- compute kinetic, elastic, and total energy at every step;
- compute momentum and affine shape diagnostics at every step;
- update extrema and step indices from every step, including step 0;
- stop on non-finite state and record `first_nonfinite_step`.

- [ ] **Step 3: Implement threshold aggregation and report writer**

Add `write_spinning_box_paper_horizon_report(...)`. Top-level `observed`
must include finite comparison-compatible fields:

```python
"linear_momentum_error": max(result["max_linear_momentum_error"] for result in results),
"angular_momentum_error": max(result["max_angular_momentum_error"] for result in results),
"energy_drift": max(result["max_total_energy_drift_j"] for result in results),
"initial_position_m": config.initial_q[9:12].tolist(),
"final_position_m": results[0]["final_position_m"],
```

Set `status=EvidenceStatus.INCOMPLETE`, no `lane_gate_status`, and
`failure_reason` naming M-ABD paper-horizon diagnostic violations.

- [ ] **Step 4: Run focused test and commit**

Run the command from Step 1. Expected: all single-body report tests pass.

Commit:

```bash
git add src/mabd_reproduction/single_body_reports.py tests/test_single_body_report_lane.py
git commit -m "feat: add spinning-box MABD paper horizon report"
```

### Task 3: Runner, CLI, And Comparison Guard

**Files:**
- Modify: `src/mabd_reproduction/experiment_runner.py`
- Modify: `scripts/run_experiment.py`
- Modify: `tests/test_experiment_runner.py`
- Modify: `tests/test_spinning_box_comparison.py`

- [ ] **Step 1: Write failing runner tests**

Add `run_spinning_box_paper_horizon(...)` tests that require an explicit output
path and write the new report. Assert the summary still has
`baseline_lane = "mabd_newton"` and `status = "incomplete"`.

Add CLI coverage for:

```bash
--lane mabd_paper_horizon
```

Add comparison guard coverage using the Phase 28 M-ABD report plus the Phase 27
RBD report:

```python
self.assertEqual(loaded.observed["lane_gate_statuses"]["mabd_newton"], "incomplete")
self.assertIn("mabd_newton_report_incomplete", loaded.observed["blocking_reasons"])
self.assertNotIn("lane_gate_status", load_claim_report(mabd_path).observed)
```

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_runner tests.test_spinning_box_comparison
```

Expected before implementation: import/CLI choice failures.

- [ ] **Step 2: Wire runner and CLI**

Import `write_spinning_box_paper_horizon_report`, add
`run_spinning_box_paper_horizon(...)`, and add `"mabd_paper_horizon"` to
`scripts/run_experiment.py --lane` choices. Require `--output` for this lane so
it cannot overwrite the configured four-step development output.

- [ ] **Step 3: Run focused test and commit**

Run the command from Step 1. Expected: all runner/comparison tests pass.

Commit:

```bash
git add src/mabd_reproduction/experiment_runner.py scripts/run_experiment.py tests/test_experiment_runner.py tests/test_spinning_box_comparison.py
git commit -m "feat: expose spinning-box MABD paper horizon lane"
```

### Task 4: Claim Boundaries, Record, And Docs Validator

**Files:**
- Modify: `docs/reference/claim-boundaries.md`
- Create: `docs/records/2026-05-17-phase28-spinning-box-paper-horizon.md`
- Modify: `scripts/validate_docs.py`
- Modify: `tests/test_phase0_bootstrap.py`

- [ ] **Step 1: Write failing docs tests**

Add a Phase 28 bootstrap test requiring:

- claim-boundaries current bullet for Phase 28;
- verified boundary stating the M-ABD paper-horizon report remains incomplete;
- non-claim boundary for M-ABD lane pass, comparison pass, paper timing, affine collision/contact, and full experiment pass;
- Phase 28 record exists;
- record includes design commit, report implementation commit, runner commit, config path, vendored Newton provenance, paper source version, figure PDF checksum, no `lane_gate_status`, and focused test outputs;
- no `experiment.*` entry in `docs/reference/paper-claims.yaml` is passed.

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_phase0_bootstrap
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
```

Expected before implementation: missing Phase 28 docs/record failures.

- [ ] **Step 2: Update docs and validator**

Add a concise Phase 28 current/verified/non-claim block and a dated record with
the provenance fields required by the spec. Extend `scripts/validate_docs.py`
to validate the same required strings and record path.

- [ ] **Step 3: Run docs tests and commit**

Run the commands from Step 1. Expected: docs tests and validator pass.

Commit:

```bash
git add docs/reference/claim-boundaries.md docs/records/2026-05-17-phase28-spinning-box-paper-horizon.md scripts/validate_docs.py tests/test_phase0_bootstrap.py
git commit -m "docs: record Phase 28 spinning-box paper horizon"
```

### Task 5: Final Verification

- [ ] **Step 1: Run full gates**

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest newton.tests.test_mabd_phase4_solver_step
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/env/readiness_check.py
git diff --check
```

- [ ] **Step 2: Fix any failures**

If a gate fails, use the failure output to make the minimal correction and
rerun the failed gate before rerunning the full list.

- [ ] **Step 3: Merge and push after green gates**

Fast-forward merge the worktree branch into `main`, push to
`origin/main`, then remove the worktree.
