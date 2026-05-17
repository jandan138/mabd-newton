# Phase 27 RBD Pass Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a dedicated lane-level pass gate for the single-body spinning-box RBD baseline without passing the full paper experiment claim.

**Architecture:** Keep the existing development RBD baseline available, add a paper-scoped RBD baseline path for the uniform cube, and require an explicit lane-gate payload for the RBD required-lane evidence. Top-level `experiment.*` reports remain `status=incomplete`; the comparison protocol consumes `observed["lane_gate_status"]="passed"` for the RBD lane but remains incomplete until the M-ABD lane and comparison pass gate are implemented.

**Tech Stack:** Python 3.10, NumPy, existing `ClaimReport` JSON schema, existing experiment runner and unittest gates.

---

### Task 1: Report Pass-Gate Contract

**Files:**
- Modify: `src/mabd_reproduction/reporting.py`
- Modify: `tests/test_reporting_contracts.py`

- [ ] **Step 1: Write failing tests**

Add tests showing that a passed experiment report is rejected even when lane
gate fields are present, that an incomplete required-lane report with
`observed["lane_gate_status"]="passed"` is accepted, and that mismatched or
over-claiming lane gates are rejected.

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_reporting_contracts
```

Expected before implementation: fail because invalid lane-gate reports are
accepted without validation.

- [ ] **Step 2: Implement gate validation**

Add a helper in `reporting.py` that keeps rejecting `status=passed` for
`experiment.*`, but validates optional lane gate fields when present. Require
both `expected["lane_pass_gate"]` and `observed["lane_pass_gate"]` to be
mappings with:

- `gate_version = "required_lane_v1"`
- matching `claim_id`
- matching `baseline_lane`
- matching `solver_mode`
- matching `backend`
- `scope = "required_lane_only"`
- `full_experiment_claim_passed = false`
- observed `thresholds_met = true`

Also require the allowlisted top-level report fields:

- `claim_id = "experiment.single_body.spinning_box"`
- `baseline_lane = "rbd_implicit_baseline"`
- `solver_mode = "paper_faithful_implicit_rbd"`
- `backend = "cpu_numpy_newton_only"`
- `status = "incomplete"`

- [ ] **Step 3: Run focused test**

Run the same command and expect all reporting contract tests to pass.

- [ ] **Step 4: Commit**

```bash
git add src/mabd_reproduction/reporting.py tests/test_reporting_contracts.py
git commit -m "feat: add experiment lane gate validation"
```

### Task 2: Paper-Scoped RBD Baseline

**Files:**
- Modify: `src/mabd_reproduction/rigid_baselines.py`
- Modify: `tests/test_rigid_baselines.py`

- [ ] **Step 1: Write failing tests**

Add tests for `run_spinning_box_paper_rbd_baseline(config)` and
`write_spinning_box_paper_rbd_baseline_report(...)`:

- result/report status is `incomplete`;
- `observed["lane_gate_status"] = "passed"`;
- `baseline_lane = rbd_implicit_baseline`;
- `solver_mode = paper_faithful_implicit_rbd`;
- `backend = cpu_numpy_newton_only`;
- initial/final position is `[0, 0.05, 0]` to `[4, 0.05, 0]`;
- every sample records the expected time and position;
- final orientation matches the closed-form xyzw quaternion and every
  quaternion has unit norm;
- momentum and relative energy errors are within strict thresholds;
- the report contains the lane-gate payload.

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_rigid_baselines
```

Expected before implementation: import/name failure.

- [ ] **Step 2: Implement closed-form baseline**

Add helper code that advances the uniform cube with constant linear and angular
velocity for each configured step. Use an axis-angle quaternion exponential in
Newton xyzw order and record trajectory samples at step 0 through
`config.step_count`.

- [ ] **Step 3: Implement report writer**

Add `write_spinning_box_paper_rbd_baseline_report(...)` that writes an
incomplete top-level experiment report with lane-gate metadata and strict
finite thresholds.

- [ ] **Step 4: Run focused test**

Run the rigid baseline test command and expect it to pass.

- [ ] **Step 5: Commit**

```bash
git add src/mabd_reproduction/rigid_baselines.py tests/test_rigid_baselines.py
git commit -m "feat: add paper-scoped spinning-box RBD baseline"
```

### Task 3: Runner And Comparison Consumption

**Files:**
- Modify: `src/mabd_reproduction/experiment_runner.py`
- Modify: `scripts/run_experiment.py`
- Modify: `src/mabd_reproduction/comparison_reports.py`
- Modify: `tests/test_experiment_runner.py`
- Modify: `tests/test_spinning_box_comparison.py`

- [ ] **Step 1: Write failing tests**

Update the RBD runner/CLI tests to expect `status=incomplete`,
`observed["lane_gate_status"]="passed"`, and `paper_faithful_implicit_rbd`.
Update comparison tests so the RBD lane gate status is `passed`,
`rbd_implicit_baseline_not_paper_faithful` is absent, and the comparison
report remains `incomplete` due to `mabd_newton_report_incomplete` and an
explicit comparison pass gate blocker.

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_runner tests.test_spinning_box_comparison
```

Expected before implementation: failures around RBD status/solver mode.

- [ ] **Step 2: Wire runner**

Change `run_spinning_box_rbd_baseline(...)` and the `rbd_implicit_baseline`
CLI lane to write the paper-scoped RBD lane-gated report. Keep the old
development function exported under a distinct name if needed by tests.

- [ ] **Step 3: Let comparison load lane-gated RBD reports**

Use the updated reporting validator so comparison can load the RBD lane-gated
report. Keep report-status snapshots separate from lane-gate-status snapshots
so `status=incomplete` cannot be mistaken for a failed RBD lane gate.

- [ ] **Step 4: Run focused tests**

Run the command from Step 1 and expect it to pass.

- [ ] **Step 5: Commit**

```bash
git add src/mabd_reproduction/experiment_runner.py scripts/run_experiment.py src/mabd_reproduction/comparison_reports.py tests/test_experiment_runner.py tests/test_spinning_box_comparison.py
git commit -m "feat: consume passed spinning-box RBD lane"
```

### Task 4: Config, Matrix, And Provenance Docs

**Files:**
- Modify: `configs/experiments/single_body_spinning_box.yaml`
- Modify: `configs/experiments/paper_experiment_matrix.yaml`
- Modify: `src/mabd_reproduction/experiment_configs.py`
- Modify: `tests/test_experiment_run_configs.py`
- Modify: `docs/reference/claim-boundaries.md`
- Create: `docs/records/2026-05-17-phase27-rbd-pass-gate.md`
- Modify: `scripts/validate_docs.py`
- Modify: `tests/test_phase0_bootstrap.py`

- [ ] **Step 1: Write failing config/docs tests**

Update tests to require:

- no `rbd_implicit_baseline_report_incomplete` blocker for spinning box;
- `mabd_newton_report_incomplete` and
  `spinning_box_comparison_report_incomplete` remain;
- Phase 27 claim-boundary and record fields exist;
- no `experiment.*` claim in `paper-claims.yaml` is passed.

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_run_configs tests.test_phase0_bootstrap
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
```

Expected before implementation: failures on stale blocker/docs fields.

- [ ] **Step 2: Update config and matrix**

Allow `required_missing_lanes` to be empty, update the spinning-box config
failure reason to name the M-ABD/comparison gaps, and update matrix blockers
as described above.

- [ ] **Step 3: Add Phase 27 docs and validator requirements**

Add bounded claim-boundary bullets and a dated record with commands, commits,
config path, environment, vendored Newton provenance, paper source version,
backend, seed policy, raw artifact paths, metrics, thresholds, lane-gate
status, and non-claims.

- [ ] **Step 4: Run focused docs tests**

Run the commands from Step 1 and expect them to pass.

- [ ] **Step 5: Commit**

```bash
git add configs/experiments/single_body_spinning_box.yaml configs/experiments/paper_experiment_matrix.yaml src/mabd_reproduction/experiment_configs.py tests/test_experiment_run_configs.py docs/reference/claim-boundaries.md docs/records/2026-05-17-phase27-rbd-pass-gate.md scripts/validate_docs.py tests/test_phase0_bootstrap.py
git commit -m "docs: record Phase 27 RBD pass gate"
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

- [ ] **Step 3: Commit any verification hardening**

If docs/record commit backfills are needed, commit them separately.
