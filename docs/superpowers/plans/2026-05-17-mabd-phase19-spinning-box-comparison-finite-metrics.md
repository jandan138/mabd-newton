# Phase 19 Spinning-Box Comparison Finite Metrics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the spinning-box comparison protocol reject invalid required metrics and report finite cross-lane metric differences.

**Architecture:** Keep lane report generation unchanged. Strengthen `comparison_reports.py` by separating missing metric keys from invalid metric values and by computing M-ABD-minus-RBD differences only when both values are finite scalar numbers.

**Tech Stack:** Python 3.10, standard `math.isfinite`, JSON claim reports, `unittest`, Markdown/YAML provenance records.

---

## File Structure

- Modify `src/mabd_reproduction/comparison_reports.py`: finite metric validation and difference helpers.
- Modify `tests/test_spinning_box_comparison.py`: RED/GREEN tests for invalid metric handling and difference output.
- Modify `docs/reference/claim-boundaries.md`: Phase 19 bounded evidence text.
- Modify `scripts/validate_docs.py`: require Phase 19 record and boundary text.
- Modify `tests/test_phase0_bootstrap.py`: Phase 19 record/boundary assertions.
- Create `docs/records/2026-05-17-phase19-spinning-box-comparison-finite-metrics.md`: dated evidence record.

---

### Task 1: Plan And Spec Commit

**Files:**
- Create: `docs/superpowers/specs/2026-05-17-phase19-spinning-box-comparison-finite-metrics-design.md`
- Create: `docs/superpowers/plans/2026-05-17-mabd-phase19-spinning-box-comparison-finite-metrics.md`

- [ ] **Step 1: Confirm planning files exist**

Run:

```bash
test -f docs/superpowers/specs/2026-05-17-phase19-spinning-box-comparison-finite-metrics-design.md
test -f docs/superpowers/plans/2026-05-17-mabd-phase19-spinning-box-comparison-finite-metrics.md
```

Expected: both commands exit `0`.

- [ ] **Step 2: Commit planning artifacts**

Run:

```bash
git add docs/superpowers/specs/2026-05-17-phase19-spinning-box-comparison-finite-metrics-design.md docs/superpowers/plans/2026-05-17-mabd-phase19-spinning-box-comparison-finite-metrics.md
git commit -m "docs: plan Phase 19 spinning-box finite metrics"
```

Expected: commit succeeds and touches only the two planning files.

---

### Task 2: Add Failing Comparison Tests

**Files:**
- Modify: `tests/test_spinning_box_comparison.py`

- [ ] **Step 1: Add finite-difference assertions to the happy path**

In `test_write_spinning_box_comparison_report_records_incomplete_protocol`, add:

```python
        self.assertEqual(loaded.observed["invalid_required_metrics"], [])
        differences = loaded.observed["lane_metric_differences"][
            "mabd_newton_minus_rbd_implicit_baseline"
        ]
        self.assertIn("linear_momentum_error", differences)
        self.assertIn("angular_momentum_error", differences)
        self.assertIn("energy_drift", differences)
```

Expected initial failure: `invalid_required_metrics` and
`lane_metric_differences` are missing.

- [ ] **Step 2: Add invalid metric test**

Add this test:

```python
    def test_spinning_box_comparison_flags_invalid_required_metrics(self) -> None:
        import json

        from mabd_reproduction.comparison_reports import write_spinning_box_comparison_report

        config = load_spinning_box_config(CONFIG_PATH)
        with TemporaryDirectory() as tmpdir:
            mabd_path, rbd_path = self._write_lane_reports(tmpdir)
            data = json.loads(mabd_path.read_text(encoding="utf-8"))
            data["observed"]["energy_drift"] = None
            mabd_path.write_text(json.dumps(data), encoding="utf-8")
            output_path = Path(tmpdir) / "comparison.json"

            write_spinning_box_comparison_report(
                output_path,
                config=config,
                mabd_report_path=mabd_path,
                rbd_report_path=rbd_path,
                source_commit="test-source",
                vendored_newton_commit="test-newton",
            )
            loaded = load_claim_report(output_path)

        self.assertNotIn("mabd_newton:energy_drift", loaded.observed["missing_required_metrics"])
        self.assertIn("mabd_newton:energy_drift", loaded.observed["invalid_required_metrics"])
        self.assertIn(
            "mabd_newton:energy_drift_invalid",
            loaded.observed["blocking_reasons"],
        )
```

Expected initial failure: invalid metrics are not reported.

- [ ] **Step 3: Verify RED**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_spinning_box_comparison
```

Expected: FAIL due missing invalid metric fields.

---

### Task 3: Implement Finite Metric Validation

**Files:**
- Modify: `src/mabd_reproduction/comparison_reports.py`

- [ ] **Step 1: Add helpers**

Add:

```python
from math import isfinite


def _finite_scalar(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    result = float(value)
    return result if isfinite(result) else None
```

Add `_invalid_metrics(lane, report)` and `_lane_metric_differences(mabd_report, rbd_report)` using `_finite_scalar`.

- [ ] **Step 2: Use helpers in report output**

In `write_spinning_box_comparison_report`, compute:

```python
    invalid_required_metrics = _invalid_metrics("mabd_newton", mabd_report) + _invalid_metrics(
        "rbd_implicit_baseline",
        rbd_report,
    )
    metric_differences = _lane_metric_differences(mabd_report, rbd_report)
```

Include both in `observed`, and append invalid blocking reasons:

```python
        *(f"{metric}_invalid" for metric in invalid_required_metrics),
```

- [ ] **Step 3: Verify GREEN**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_spinning_box_comparison
```

Expected: comparison tests pass.

- [ ] **Step 4: Commit implementation**

Run:

```bash
git add src/mabd_reproduction/comparison_reports.py tests/test_spinning_box_comparison.py
git commit -m "feat: validate finite spinning-box comparison metrics"
```

Expected: commit succeeds.

---

### Task 4: Add Phase 19 Provenance Gates

**Files:**
- Modify: `docs/reference/claim-boundaries.md`
- Modify: `scripts/validate_docs.py`
- Modify: `tests/test_phase0_bootstrap.py`
- Create: `docs/records/2026-05-17-phase19-spinning-box-comparison-finite-metrics.md`

- [ ] **Step 1: Add RED docs tests**

Add Phase 19 boundary and record assertions to `tests/test_phase0_bootstrap.py`, requiring the snippets:

```text
Phase 19 verifies finite required-metric validation
invalid_required_metrics
lane_metric_differences
Phase 19 does not verify the paper spinning-box experiment
No `experiment.*` claim is passed in this phase.
```

- [ ] **Step 2: Verify RED**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_phase0_bootstrap
```

Expected: FAIL because Phase 19 docs are missing.

- [ ] **Step 3: Implement docs, record, and validator**

Update `claim-boundaries.md`, `validate_docs.py`, and create the Phase 19 record. Keep the record status `passed` for the phase evidence but explicitly state the comparison report remains `incomplete`.

- [ ] **Step 4: Verify GREEN**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_phase0_bootstrap
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
```

Expected: both pass.

- [ ] **Step 5: Commit docs/provenance**

Run:

```bash
git add docs/reference/claim-boundaries.md docs/records/2026-05-17-phase19-spinning-box-comparison-finite-metrics.md scripts/validate_docs.py tests/test_phase0_bootstrap.py
git commit -m "docs: record Phase 19 finite comparison metrics"
```

Expected: commit succeeds.

---

### Task 5: Verification, Review, Merge, Push

**Files:**
- No planned file edits unless review finds a concrete issue.

- [ ] **Step 1: Run full gates**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"
git diff --check
```

Expected: all pass, tests report all tests OK, and vendored Newton resolves inside the worktree.

- [ ] **Step 2: Request multi-angle review**

Dispatch two read-only reviewers:

- claim/spec reviewer for overclaims and provenance
- code/protocol reviewer for finite metric classification and comparison output

Expected: no high-severity findings, or fixes committed and gates rerun.

- [ ] **Step 3: Merge, push, cleanup**

Fast-forward `main`, rerun main gates, push `main`, and remove the Phase 19 worktree and local branch.
