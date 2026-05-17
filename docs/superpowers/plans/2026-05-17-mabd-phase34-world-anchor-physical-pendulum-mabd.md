# Phase 34 World-Anchor Physical Pendulum M-ABD Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a bounded physical-pendulum M-ABD development lane backed by a vendored Newton dense CPU-oracle world-anchor ball constraint.

**Architecture:** Vendored Newton owns the world-anchor constraint primitive and dense KKT integration. The reproduction package owns config parsing, procedural scene setup, report generation, runner/CLI dispatch, and claim-boundary documentation. All evidence remains incomplete at the experiment level. The generated physical-pendulum report uses a distinct diagnostic lane id; the required paper `mabd_newton` lane remains missing.

**Tech Stack:** Python 3.10, NumPy, SciPy, PyYAML, vendored Newton M-ABD CPU oracle, `unittest`, ruff.

---

### Task 1: World-Anchor Constraint Tests

**Files:**
- Modify: `tests/test_mabd_phase4_solver_step.py`
- Modify: `vendor/newton/newton/tests/test_mabd_phase4_solver_step.py`
- Modify: `vendor/newton/newton/_src/solvers/mabd/step_oracle.py`
- Modify: `vendor/newton/newton/_src/solvers/mabd/__init__.py`

- [x] **Step 1: Write failing repo and vendored tests**

Add tests that instantiate `mabd.MABDCPUOracleWorldConstraint(body=0, rest_point=[0,0,0], world_point=[0,0,0])`, run one dense CPU-oracle step from a translated body, and assert the pinned point residual is near zero after the step. Add rejection tests for non-dense topology and bad vector shapes.

- [x] **Step 2: Run RED**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_mabd_phase4_solver_step
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest newton.tests.test_mabd_phase4_solver_step
```

Expected: failures mention missing `MABDCPUOracleWorldConstraint`.

- [x] **Step 3: Implement vendored Newton support**

Add `MABDCPUOracleWorldConstraint`, validate its body/rest/world fields, assemble world rows into dense KKT, compute post-step residuals, reject world constraints for `chain`, `tree`, `single_loop`, `general_graph`, or `auto`, and export the dataclass from `mabd.__init__`.

- [x] **Step 4: Run GREEN**

Run the same two commands. Expected: both pass.

### Task 2: Physical-Pendulum Config And Report Tests

**Files:**
- Modify: `configs/experiments/single_body_physical_pendulum.yaml`
- Modify: `src/mabd_reproduction/experiment_configs.py`
- Create: `src/mabd_reproduction/physical_pendulum_mabd.py`
- Modify: `src/mabd_reproduction/physical_pendulum_reports.py`
- Modify: `tests/test_experiment_run_configs.py`
- Modify: `tests/test_experiment_runner.py`

- [x] **Step 1: Write failing config/report tests**

Add tests requiring `mabd_development` fields, finite nondegenerate rest points,
positive masses, distinct output report path, thresholds, and report fields:
`solver_mode = mabd_cpu_oracle_physical_pendulum_development`,
`baseline_lane = physical_pendulum_mabd_development_diagnostic`, `lane_status =
development_diagnostic_generated`, `pivot_residual_max`, compact angle samples,
and top-level status `incomplete`.

- [x] **Step 2: Run RED**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_run_configs tests.test_experiment_runner
```

Expected: missing config fields and runner/report symbols.

- [x] **Step 3: Implement config and report lane**

Add dataclasses for `PhysicalPendulumMABDDevelopmentConfig`, parse the config
block, validate geometry/thresholds, implement a short CPU-oracle rollout with
world-anchor constraint and gravity, compute angle samples and analytic
diagnostics, and write an incomplete claim report.

- [x] **Step 4: Run GREEN**

Run the same command. Expected: pass.

### Task 3: Runner And CLI Dispatch

**Files:**
- Modify: `src/mabd_reproduction/experiment_runner.py`
- Modify: `scripts/run_experiment.py`
- Modify: `tests/test_experiment_runner.py`

- [x] **Step 1: Write failing CLI test**

Add a subprocess test for:

```bash
scripts/run_experiment.py --lane physical_pendulum_mabd_development \
  --config configs/experiments/single_body_physical_pendulum.yaml \
  --matrix configs/experiments/paper_experiment_matrix.yaml \
  --output /tmp/physical_pendulum_mabd.json \
  --source-commit cli-source \
  --vendored-newton-commit cli-newton
```

Expected summary: claim id physical pendulum, status incomplete, baseline lane
`physical_pendulum_mabd_development_diagnostic`.

- [x] **Step 2: Implement runner/CLI**

Add `run_physical_pendulum_mabd_development` and dispatch it from CLI.

- [x] **Step 3: Run GREEN**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_runner
```

Expected: pass.

### Task 4: Docs, Record, And Validators

**Files:**
- Modify: `docs/reference/claim-boundaries.md`
- Create: `docs/records/2026-05-17-phase34-world-anchor-physical-pendulum-mabd.md`
- Modify: `scripts/validate_docs.py`
- Modify: `tests/test_phase0_bootstrap.py`

- [x] **Step 1: Write failing docs tests**

Add Phase 34 boundary and record checks. Require explicit non-claims for
paper-faithful physical-pendulum reproduction, RBD baseline, joint-force
waveform, geometry, contact, timing, and passed `experiment.*` claims.

- [x] **Step 2: Run RED**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_phase0_bootstrap
```

Expected: missing Phase 34 record/boundaries.

- [x] **Step 3: Implement docs and validator updates**

Add Phase 34 record with seed, metrics, thresholds, commands, environment,
paper source checksums, vendored Newton patch status, and claim impact.
Update validator required paths and final Phase 0-34 message.

- [x] **Step 4: Run GREEN**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_phase0_bootstrap
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
```

Expected: both pass.

### Task 5: Final Gates And Review

**Files:**
- All changed files.

- [x] **Step 1: Run full gates**

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/env/readiness_check.py
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"
git diff --check
```

- [x] **Step 2: Request review**

Ask for code/spec review focused on claim boundaries, world-anchor KKT
correctness, and report non-overclaiming. Fix any valid findings and rerun
affected gates.

- [ ] **Step 3: Commit, merge, push**

Commit Phase 34, fast-forward `main`, push `origin/main`, and remove the
temporary worktree/branch after confirming `main` and `origin/main` contain the
commit.
