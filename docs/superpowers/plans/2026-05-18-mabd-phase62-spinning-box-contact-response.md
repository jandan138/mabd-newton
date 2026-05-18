# Phase 62 Spinning-Box Contact Response Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a Newton-only explicit contact-response diagnostic report for the spinning-box paper-horizon lane without claiming an experiment pass.

**Architecture:** Reuse the existing `spinning_box_contact_diagnostics` force vector and the existing CPU oracle `external_forces` hook. Keep Phase 61 no-response reporting unchanged, and write a separate Phase 62 report artifact, runner lane, record, and validator gate.

**Tech Stack:** Python 3.10, `unittest`, NumPy, vendored Newton M-ABD CPU oracle, project JSON claim reports.

---

### Task 1: Config Contract

**Files:**
- Modify: `configs/experiments/single_body_spinning_box.yaml`
- Modify: `src/mabd_reproduction/experiment_configs.py`
- Modify: `tests/test_experiment_run_configs.py`

- [ ] Add `paper_horizon.contact_response_output_report` with value `reports/experiment_matrix/single_body_spinning_box_contact_response.json`.
- [ ] Extend `SpinningBoxPaperHorizonConfig` with `contact_response_output_report: str`.
- [ ] Parse the field in `_require_paper_horizon`.
- [ ] Add a failing test assertion, then implementation, then run:
  `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_run_configs`

### Task 2: Report Lane

**Files:**
- Modify: `src/mabd_reproduction/single_body_reports.py`
- Modify: `tests/test_single_body_report_lane.py`

- [ ] Add a failing test for `write_spinning_box_contact_response_report`.
- [ ] Implement `_run_spinning_box_contact_response_step_size` by evaluating contact diagnostics from current state and passing `external_forces=[contact.total_generalized_force]` to `mabd.solve_cpu_oracle_step`.
- [ ] Record per-step-size response extrema, applied force extrema, no-response comparison, blockers, and `EvidenceStatus.INCOMPLETE`.
- [ ] Export `write_spinning_box_contact_response_report`.
- [ ] Run:
  `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_single_body_report_lane`

### Task 3: Runner Lane

**Files:**
- Modify: `src/mabd_reproduction/experiment_runner.py`
- Modify: `scripts/run_experiment.py`
- Modify: `tests/test_experiment_runner.py`

- [ ] Add `run_spinning_box_contact_response`.
- [ ] Add `spinning_box_contact_response` to CLI choices and dispatch.
- [ ] Require `--output` and reject `--output-root`.
- [ ] Add runner and CLI tests.
- [ ] Run:
  `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_runner`

### Task 4: Artifact And Provenance

**Files:**
- Create: `reports/experiment_matrix/single_body_spinning_box_contact_response.json`
- Create: `docs/records/2026-05-18-phase62-spinning-box-contact-response.md`
- Modify: `docs/reference/claim-boundaries.md`
- Modify: `scripts/validate_docs.py`
- Modify: `tests/test_phase0_bootstrap.py`

- [ ] Generate the report through `scripts/run_experiment.py --lane spinning_box_contact_response`.
- [ ] Record source commit, vendored Newton commit, report sha256, observed policy, observed blockers, and validation commands.
- [ ] Add Phase 62 claim-boundary bullets.
- [ ] Add `validate_phase62_record()` and include the new required paths.
- [ ] Add bootstrap tests proving Phase 62 boundaries and validator rejection behavior.
- [ ] Run:
  `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py`
  and
  `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_phase0_bootstrap`

### Task 5: Final Verification

**Files:**
- Verify all changed source, tests, docs, and report files.

- [ ] Run:
  `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests`
- [ ] Run:
  `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .`
- [ ] Run:
  `PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"`
- [ ] Run:
  `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/env/readiness_check.py`
- [ ] Run:
  `git diff --check`
- [ ] Request multi-agent review before merging.
