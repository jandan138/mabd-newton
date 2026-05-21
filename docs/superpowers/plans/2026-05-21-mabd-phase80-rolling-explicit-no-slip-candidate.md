# Phase 80 Rolling Explicit No-Slip Candidate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development and superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a fail-closed local `rbd_explicit_no_slip_candidate` lane for the rolling/spinning experiment without passing any paper experiment claim.

**Architecture:** Extend the rolling/spinning config with a lane-specific candidate section that reuses the existing RBD baseline dataclass, add a deterministic no-slip projected trajectory runner and report writer, expose it through the experiment runner and CLI, then record the report in docs validation and the gap audit while preserving all paper-faithful blockers.

**Tech Stack:** Python 3.10, `unittest`, PyYAML, NumPy deterministic rolling kinematics, existing `ClaimReport`, existing `mabd-newton-py310` validation commands.

No `experiment.*` claim is passed by this phase.

---

### Task 1: Candidate Config Contract

**Files:**
- Modify: `src/mabd_reproduction/experiment_configs.py`
- Modify: `configs/experiments/single_body_rolling_spinning.yaml`
- Test: `tests/test_experiment_run_configs.py`

- [x] **Step 1: Write the failing config test**

Add `test_rolling_spinning_rbd_explicit_no_slip_candidate_is_fail_closed`.
It must assert the candidate output path is
`reports/experiment_matrix/single_body_rolling_spinning_rbd_explicit_no_slip_candidate.json`,
that the lane uses `radius_m = 0.5`, `half_height_m = 0.5`,
`density_kg_m3 = 1000.0`, `time_step_s = 0.01`, `step_count = 10000`,
and that `vx + radius_m * wz = 0`.

- [x] **Step 2: Run the test and verify it fails**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_run_configs.ExperimentRunConfigTests.test_rolling_spinning_rbd_explicit_no_slip_candidate_is_fail_closed
```

Expected: fail because `RollingSpinningRunConfig` has no
`rbd_explicit_no_slip_candidate` field.

- [x] **Step 3: Implement minimal config support**

Add `ROLLING_SPINNING_RBD_EXPLICIT_NO_SLIP_CANDIDATE_OUTPUT_REPORT`, parse the
YAML section into `RollingSpinningRBDBaselineConfig`, and validate the path,
10K horizon, `h = 0.01`, sample count, center height, zero vertical/lateral
velocity, zero off-axis angular velocity, and no-slip initial velocity. Do not
change `ROLLING_SPINNING_REQUIRED_MISSING_LANES`.

- [x] **Step 4: Run config tests**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_run_configs
```

Expected: all config tests pass.

### Task 2: Candidate Runner And Report

**Files:**
- Modify: `src/mabd_reproduction/rolling_spinning_reports.py`
- Modify: `src/mabd_reproduction/experiment_runner.py`
- Modify: `scripts/run_experiment.py`
- Test: `tests/test_experiment_runner.py`

- [x] **Step 1: Write the failing runner test**

Add
`test_run_rolling_spinning_rbd_explicit_no_slip_candidate_writes_report`.
It must run the candidate lane to a temporary output path and assert:
`status = incomplete`, `baseline_lane = rbd_explicit_no_slip_candidate`,
`solver_mode = newton_explicit_no_slip_rolling_cylinder_candidate`,
`observed.candidate_status = local_no_slip_projection_generated`,
`observed.local_runtime_measured = true`, `paper_comparable = false`,
`full_experiment_claim_passed = false`, `timing_distribution.total_wall_time_ms`
is present, and all Phase80 blocker strings are present.

- [x] **Step 2: Run the test and verify it fails**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_runner.ExperimentRunnerTests.test_run_rolling_spinning_rbd_explicit_no_slip_candidate_writes_report
```

Expected: import or attribute failure because the runner does not exist.

- [x] **Step 3: Implement the candidate trajectory**

Reuse the closed-form no-slip trajectory shape from Phase79, but measure local
wall-clock time around the deterministic projection loop. Keep contact count as
a diagnostic constant, record no-slip residual and energy drift, and keep
`status = incomplete`.

- [x] **Step 4: Add report writer, experiment runner, and CLI lane**

Add `write_rolling_spinning_rbd_explicit_no_slip_candidate_report`,
`run_rolling_spinning_rbd_explicit_no_slip_candidate`, and CLI lane
`rolling_spinning_rbd_explicit_no_slip_candidate`.

- [x] **Step 5: Run runner tests**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_runner
```

Expected: all runner tests pass.

### Task 3: Evidence And Validator

**Files:**
- Add: `reports/experiment_matrix/single_body_rolling_spinning_rbd_explicit_no_slip_candidate.json`
- Add: `docs/records/2026-05-21-phase80-rolling-explicit-no-slip-candidate.md`
- Modify: `docs/reference/claim-boundaries.md`
- Modify: `docs/reference/reproduction-gap-audit.yaml`
- Modify: `scripts/validate_docs.py`
- Test: `tests/test_phase0_bootstrap.py`

- [x] **Step 1: Generate the candidate report**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/run_experiment.py --lane rolling_spinning_rbd_explicit_no_slip_candidate --config configs/experiments/single_body_rolling_spinning.yaml --matrix configs/experiments/paper_experiment_matrix.yaml --source-commit <current-commit> --vendored-newton-commit 96713fa965463b69c229a4d30582c733ff3526bb
```

- [x] **Step 2: Add bootstrap and docs validation**

Add Phase80 bootstrap tests requiring the spec, plan, record, verified report,
report hash, `baseline_lane`, `solver_mode`, candidate blockers, local timing
scope, unchanged `paper-claims.yaml` experiment status, unchanged top-level
`required_missing_lanes`, and unchanged remaining rolling/spinning gap names.

- [x] **Step 3: Update `scripts/validate_docs.py`**

Validate the Phase80 spec, plan, record, report fields, report SHA256, gap-audit
fields, and claim-boundary text. Add the report to the expected verified-report
set without removing any Phase75, Phase78, or Phase79 checks.

- [x] **Step 4: Run final validation**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"
git diff --check
```

Expected: all commands pass.
