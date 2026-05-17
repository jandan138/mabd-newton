# Phase 42 Spinning Box Report Artifacts Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Commit and validate compact spinning-box experiment-matrix report artifacts without claiming a passed paper result.

**Architecture:** Reuse the existing config-driven experiment runner to generate four JSON claim reports. Add tests and docs validation that prove the reports are committed, source-stamped, internally consistent, and still bounded by incomplete M-ABD and comparison blockers.

**Tech Stack:** Python 3.10, `unittest`, existing `scripts/run_experiment.py`, JSON `ClaimReport` artifacts, Markdown records, `scripts/validate_docs.py`.

---

## File Map

- Add `tests/test_spinning_box_report_artifacts.py`: committed report artifact contract tests.
- Modify `tests/test_phase0_bootstrap.py`: Phase42 boundary and record tests.
- Modify `scripts/validate_docs.py`: require Phase42 docs and validate report artifacts.
- Add `reports/experiment_matrix/single_body_spinning_box.json`: MABD diagnostic report.
- Add `reports/experiment_matrix/single_body_spinning_box_paper_horizon.json`: paper-horizon diagnostic report.
- Add `reports/experiment_matrix/single_body_spinning_box_rbd_baseline.json`: paper-faithful RBD lane-gate report.
- Add `reports/experiment_matrix/single_body_spinning_box_comparison.json`: comparison protocol report.
- Modify `docs/reference/claim-boundaries.md`: Phase42 claim boundary.
- Add `docs/records/2026-05-17-phase42-spinning-box-report-artifacts.md`: dated evidence record.

## Task 1: RED Artifact Tests

- [ ] **Step 1: Add failing report artifact tests**

Create `tests/test_spinning_box_report_artifacts.py` with tests that load:

```python
REPORTS = {
    "mabd": ROOT / "reports/experiment_matrix/single_body_spinning_box.json",
    "paper_horizon": ROOT / "reports/experiment_matrix/single_body_spinning_box_paper_horizon.json",
    "rbd": ROOT / "reports/experiment_matrix/single_body_spinning_box_rbd_baseline.json",
    "comparison": ROOT / "reports/experiment_matrix/single_body_spinning_box_comparison.json",
}
```

Assert every file exists, every report has
`claim_id = experiment.single_body.spinning_box`, `scene_id =
single_body_spinning_box`, `status = incomplete`, vendored Newton commit
`96713fa965463b69c229a4d30582c733ff3526bb`, and non-placeholder
`source_commit`.

Assert lane-specific behavior:

```python
self.assertEqual(mabd.baseline_lane, "mabd_newton")
self.assertEqual(mabd.solver_mode, "mabd_cpu_oracle_development")
self.assertEqual(paper_horizon.observed["mabd_paper_horizon_status"], "development_gap_observed")
self.assertIn("mabd_kinematic_feasibility_blocker_recorded", paper_horizon.observed["blocking_reasons"])
self.assertEqual(rbd.solver_mode, "paper_faithful_implicit_rbd")
self.assertEqual(rbd.observed["lane_gate_status"], "passed")
self.assertEqual(comparison.observed["missing_required_metrics"], [])
self.assertEqual(comparison.observed["invalid_required_metrics"], [])
self.assertIn("mabd_newton_report_incomplete", comparison.observed["blocking_reasons"])
self.assertIn("spinning_box_comparison_pass_gate_not_enabled", comparison.observed["blocking_reasons"])
```

- [ ] **Step 2: Run RED**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_spinning_box_report_artifacts
```

Expected: fail because the spinning-box report artifact files are missing.

## Task 2: Generate Reports

- [ ] **Step 1: Generate reports with canonical isolated Python**

Run:

```bash
PY=/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python
SRC=75a676791084ca0f77fe16fc1902814a5bb8d148
NEWTON=96713fa965463b69c229a4d30582c733ff3526bb
PYTHONPATH=src:vendor/newton "$PY" scripts/run_experiment.py --lane mabd_newton --config configs/experiments/single_body_spinning_box.yaml --matrix configs/experiments/paper_experiment_matrix.yaml --output reports/experiment_matrix/single_body_spinning_box.json --source-commit "$SRC" --vendored-newton-commit "$NEWTON"
PYTHONPATH=src:vendor/newton "$PY" scripts/run_experiment.py --lane mabd_paper_horizon --config configs/experiments/single_body_spinning_box.yaml --matrix configs/experiments/paper_experiment_matrix.yaml --output reports/experiment_matrix/single_body_spinning_box_paper_horizon.json --source-commit "$SRC" --vendored-newton-commit "$NEWTON"
PYTHONPATH=src:vendor/newton "$PY" scripts/run_experiment.py --lane rbd_implicit_baseline --config configs/experiments/single_body_spinning_box.yaml --matrix configs/experiments/paper_experiment_matrix.yaml --output reports/experiment_matrix/single_body_spinning_box_rbd_baseline.json --source-commit "$SRC" --vendored-newton-commit "$NEWTON"
PYTHONPATH=src:vendor/newton "$PY" scripts/run_experiment.py --lane spinning_box_comparison --config configs/experiments/single_body_spinning_box.yaml --matrix configs/experiments/paper_experiment_matrix.yaml --mabd-report reports/experiment_matrix/single_body_spinning_box.json --rbd-report reports/experiment_matrix/single_body_spinning_box_rbd_baseline.json --output reports/experiment_matrix/single_body_spinning_box_comparison.json --source-commit "$SRC" --vendored-newton-commit "$NEWTON"
```

- [ ] **Step 2: Run GREEN**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_spinning_box_report_artifacts
```

Expected: pass.

## Task 3: Docs And Validator

- [ ] **Step 1: Add Phase42 bootstrap tests**

In `tests/test_phase0_bootstrap.py`, add tests requiring Phase42 claim-boundary
text and record text, including retained blockers and no passed
`experiment.*` claim.

- [ ] **Step 2: Extend docs validator**

In `scripts/validate_docs.py`, update the title to Phase 0-42, require the
Phase42 spec/plan/record files, and add `validate_phase42_record()` that
enforces the report contract from the spec, report hashes, retained blockers,
and non-overclaim text.

- [ ] **Step 3: Update claim boundaries and record**

Add Phase42 bullets to `docs/reference/claim-boundaries.md` and create
`docs/records/2026-05-17-phase42-spinning-box-report-artifacts.md`.

## Task 4: Verify And Commit

- [ ] **Step 1: Run focused gates**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_spinning_box_report_artifacts tests.test_phase0_bootstrap
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
git diff --check
```

Expected: all pass.

- [ ] **Step 2: Commit**

Run:

```bash
git add tests/test_spinning_box_report_artifacts.py tests/test_phase0_bootstrap.py scripts/validate_docs.py docs/reference/claim-boundaries.md docs/records/2026-05-17-phase42-spinning-box-report-artifacts.md docs/superpowers/specs/2026-05-17-phase42-spinning-box-report-artifacts-design.md docs/superpowers/plans/2026-05-17-mabd-phase42-spinning-box-report-artifacts.md reports/experiment_matrix/single_body_spinning_box.json reports/experiment_matrix/single_body_spinning_box_paper_horizon.json reports/experiment_matrix/single_body_spinning_box_rbd_baseline.json reports/experiment_matrix/single_body_spinning_box_comparison.json
git commit -m "Record spinning box report artifacts"
```

## Task 5: Full Verification

- [ ] **Step 1: Run full gates**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/env/readiness_check.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
git diff --check
```

Expected: all pass, with Newton importing from this worktree's `vendor/newton`.
