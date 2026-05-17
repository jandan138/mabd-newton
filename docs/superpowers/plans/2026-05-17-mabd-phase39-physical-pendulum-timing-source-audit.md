# Phase 39 Physical Pendulum Timing Source Audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove the false `paper_timing_missing` physical-pendulum blocker and record source-audit evidence that the cited paper lines do not state a runtime timing metric for this experiment.

**Architecture:** Keep report status incomplete and leave timing distributions as `not_timed`. Add a small shared source-audit payload to physical-pendulum report writers and comparison reports, update validators/docs, and regenerate only the small JSON reports.

**Tech Stack:** Python 3.10, `unittest`, JSON claim reports, Markdown records, canonical `mabd-newton-py310` environment.

---

## File Map

- Modify `src/mabd_reproduction/physical_pendulum_reports.py`: add a shared timing source-audit payload and include it in MABD/RBD/analytic physical-pendulum reports where appropriate.
- Modify `src/mabd_reproduction/comparison_reports.py`: remove `paper_timing_missing` from physical-pendulum comparison blockers and include the audit payload in expected/observed.
- Modify `tests/test_experiment_runner.py`: add RED tests for generated reports.
- Modify `tests/test_phase0_bootstrap.py`: add Phase39 boundary/record/validator tests and update current report artifact expectations.
- Modify `scripts/validate_docs.py`: add `validate_phase39_record()` and relax Phase37/38 current-report timing blocker checks.
- Modify `docs/reference/claim-boundaries.md`: add Phase39 current/verified/non-claim bullets and forbidden claim.
- Add `docs/records/2026-05-17-phase39-physical-pendulum-timing-source-audit.md`.
- Regenerate `reports/experiment_matrix/single_body_physical_pendulum_mabd_newton.json`, `reports/experiment_matrix/single_body_physical_pendulum_rbd_baseline.json`, `reports/experiment_matrix/single_body_physical_pendulum_analytic_reference.json`, and `reports/experiment_matrix/single_body_physical_pendulum_comparison.json`.

## Task 1: RED Tests

- [ ] **Step 1: Add report-writer expectations**

In `tests/test_experiment_runner.py`, update physical-pendulum MABD, RBD, and comparison tests:

```python
self.assertNotIn("paper_timing_missing", loaded.observed["blocking_reasons"])
self.assertEqual(
    loaded.observed["paper_timing_source_audit"]["status"],
    "not_a_physical_pendulum_paper_metric",
)
```

For comparison, also assert:

```python
self.assertEqual(
    loaded.expected["paper_timing_source_audit"]["status"],
    "not_a_physical_pendulum_paper_metric",
)
```

- [ ] **Step 2: Run RED**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_runner
```

Expected: fail because generated reports still contain `paper_timing_missing` or lack `paper_timing_source_audit`.

## Task 2: Report Implementation

- [ ] **Step 1: Add source-audit helper**

In `src/mabd_reproduction/physical_pendulum_reports.py`, add:

```python
PHYSICAL_PENDULUM_TIMING_SOURCE_AUDIT = {
    "source_lines": ["/tmp/mabd-paper/source/sections/experiment.tex:77-91"],
    "status": "not_a_physical_pendulum_paper_metric",
    "finding": (
        "No runtime timing or performance value is stated in the cited "
        "physical-pendulum source lines."
    ),
}
```

- [ ] **Step 2: Include audit in physical-pendulum reports**

Add `"paper_timing_source_audit": dict(PHYSICAL_PENDULUM_TIMING_SOURCE_AUDIT)` to `observed` and `expected` for analytic, MABD Newton, and RBD baseline physical-pendulum reports.

- [ ] **Step 3: Remove report-level timing blocker**

Remove `paper_timing_missing` from MABD Newton and RBD baseline physical-pendulum `blocking_reasons` lists. Keep `timing_distribution={"scope": "not_timed", ...}` unchanged.

- [ ] **Step 4: Update comparison report**

In `src/mabd_reproduction/comparison_reports.py`, import the audit constant, remove `paper_timing_missing` from physical-pendulum comparison `blocking_reasons`, add audit payload to `expected` and `observed`, and change failure reason text from "geometry, and timing evidence remain required" to "geometry remains required; runtime timing is not a cited physical-pendulum metric".

- [ ] **Step 5: Run GREEN**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_runner
```

Expected: pass.

## Task 3: Docs, Validator, And Reports

- [ ] **Step 1: Add Phase39 docs tests**

In `tests/test_phase0_bootstrap.py`, add tests for Phase39 claim boundaries, record snippets, and validator rejection if `paper_timing_missing` returns to comparison blockers.

- [ ] **Step 2: Add validator**

Add `validate_phase39_record()` in `scripts/validate_docs.py`. It must require the audit payload in current reports, reject `paper_timing_missing` in physical-pendulum blockers, keep joint-force/geometry/pass-gate blockers, and keep all `experiment.*` paper claims non-passed.

- [ ] **Step 3: Update claim boundaries and record**

Add Phase39 boundary text and `docs/records/2026-05-17-phase39-physical-pendulum-timing-source-audit.md` with source lines, report paths, blockers removed/retained, and verification commands.

- [ ] **Step 4: Regenerate reports after code commit**

Commit code/tests/docs first, then regenerate physical-pendulum lane reports and comparison using the actual commit SHA:

```bash
SOURCE_COMMIT=$(git rev-parse --short HEAD)
VENDORED_NEWTON_COMMIT=96713fa965463b69c229a4d30582c733ff3526bb
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/run_experiment.py --lane physical_pendulum_analytic_reference --config configs/experiments/single_body_physical_pendulum.yaml --matrix configs/experiments/paper_experiment_matrix.yaml --output reports/experiment_matrix/single_body_physical_pendulum_analytic_reference.json --source-commit "$SOURCE_COMMIT" --vendored-newton-commit "$VENDORED_NEWTON_COMMIT"
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/run_experiment.py --lane physical_pendulum_mabd_newton --config configs/experiments/single_body_physical_pendulum.yaml --matrix configs/experiments/paper_experiment_matrix.yaml --output reports/experiment_matrix/single_body_physical_pendulum_mabd_newton.json --source-commit "$SOURCE_COMMIT" --vendored-newton-commit "$VENDORED_NEWTON_COMMIT"
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/run_experiment.py --lane physical_pendulum_rbd_baseline --config configs/experiments/single_body_physical_pendulum.yaml --matrix configs/experiments/paper_experiment_matrix.yaml --output reports/experiment_matrix/single_body_physical_pendulum_rbd_baseline.json --source-commit "$SOURCE_COMMIT" --vendored-newton-commit "$VENDORED_NEWTON_COMMIT"
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/run_experiment.py --lane physical_pendulum_comparison --config configs/experiments/single_body_physical_pendulum.yaml --matrix configs/experiments/paper_experiment_matrix.yaml --output reports/experiment_matrix/single_body_physical_pendulum_comparison.json --analytic-report reports/experiment_matrix/single_body_physical_pendulum_analytic_reference.json --mabd-report reports/experiment_matrix/single_body_physical_pendulum_mabd_newton.json --rbd-report reports/experiment_matrix/single_body_physical_pendulum_rbd_baseline.json --source-commit "$SOURCE_COMMIT" --vendored-newton-commit "$VENDORED_NEWTON_COMMIT"
```

- [ ] **Step 5: Final gates**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/env/readiness_check.py
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"
git diff --check
```

Expected: all pass.
