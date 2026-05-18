# Phase 61 Spinning-Box Contact Diagnostics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> superpowers:subagent-driven-development or superpowers:executing-plans to
> implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for
> tracking.

**Goal:** Add contact diagnostics to the paper-horizon M-ABD lane so the
spinning-box report records the current missing contact-response blocker without
claiming a solver pass.

**Architecture:** Reuse the existing procedural spinning-box contact diagnostic
function. Evaluate it from each current M-ABD state in the paper-horizon rollout,
record compact extrema and sample fields, and keep the contact force diagnostic
not applied to the implicit step.

**Tech Stack:** Python 3.10, NumPy, vendored Newton `SolverMABD` CPU oracle,
`unittest`, existing JSON claim-report schema, isolated
`mabd-newton-py310` environment.

---

### Task 1: Add Failing Report Tests

**Files:**
- Modify: `tests/test_single_body_report_lane.py`
- Modify: `tests/test_spinning_box_report_artifacts.py`

- [ ] Require `spinning_box_contact_response_missing` in the paper-horizon
  report blockers.
- [ ] Require top-level and per-step `contact_diagnostic_policy =
  evaluated_from_current_mabd_states_not_applied_to_step`.
- [ ] Require observed positive contact active count, penetration, normal force,
  and generalized force diagnostics.

Expected red result: tests fail because the paper-horizon report does not yet
record contact-response-missing fields.

### Task 2: Implement Paper-Horizon Diagnostics

**Files:**
- Modify: `src/mabd_reproduction/single_body_reports.py`

- [ ] Evaluate `spinning_box_contact_diagnostics(config, q, qd)` in
  `_paper_horizon_state_metrics`.
- [ ] Include finite contact scalar fields in compact trajectory samples.
- [ ] Track contact extrema in each paper-horizon step-size summary.
- [ ] Add `spinning_box_contact_response_missing` only when penetration is
  observed.
- [ ] Keep the diagnostic force not applied to the implicit step.

### Task 3: Regenerate Report And Evidence

**Files:**
- Modify: `reports/experiment_matrix/single_body_spinning_box_paper_horizon.json`
- Modify: `docs/reference/reproduction-gap-audit.yaml`
- Create: `docs/records/2026-05-18-phase61-spinning-box-contact-diagnostics.md`
- Create: `docs/superpowers/specs/2026-05-18-phase61-spinning-box-contact-diagnostics-design.md`
- Create: `docs/superpowers/plans/2026-05-18-mabd-phase61-spinning-box-contact-diagnostics.md`
- Modify: `docs/reference/claim-boundaries.md`

- [ ] Regenerate `single_body_spinning_box_paper_horizon.json` with the
  implementation commit as `source_commit`.
- [ ] Update `docs/reference/reproduction-gap-audit.yaml` so the current
  evidence hash matches the regenerated report.
- [ ] Record the report sha256, observed contact fields, retained blockers, and
  non-claims in the Phase 61 record.
- [ ] Preserve Phase 42 history by making validator acceptance explicit for the
  Phase 61-upgraded current paper-horizon report.

### Task 4: Validate And Review

- [ ] Run focused tests:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_single_body_report_lane tests.test_spinning_box_report_artifacts
```

- [ ] Run full validation:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"
git diff --check
```

Expected final state: all commands pass. No `experiment.*` claim is passed.
