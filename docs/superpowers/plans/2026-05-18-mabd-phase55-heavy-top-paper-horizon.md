# Phase55 Heavy-Top Paper-Horizon MABD Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> superpowers:subagent-driven-development or superpowers:executing-plans to
> implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for
> tracking.

**Goal:** Add a 10 second heavy-top MABD diagnostic lane that aligns with the
RK4 reference sample grid, then regenerate the comparison report without the
`sample_time_grid_mismatch` blocker.

**Architecture:** Reuse the existing heavy-top MABD rollout/report pipeline by
parameterizing it with an explicit `HeavyTopMABDNewtonConfig`. Add a
`mabd_paper_horizon` config section, a report writer, a runner/CLI lane, and a
Phase55 docs validator.

**Tech Stack:** Python 3.10, NumPy, vendored Newton, JSON `ClaimReport`,
`unittest`, existing docs validator.

---

### Task 1: RED Tests For Paper-Horizon Config And Rollout

**Files:**
- Modify: `tests/test_experiment_run_configs.py`
- Modify: `tests/test_heavy_top_mabd.py`

- [ ] **Step 1: Add config expectations**

Extend the heavy-top config test to require:

- `config.mabd_paper_horizon.output_report ==
  "reports/experiment_matrix/single_body_heavy_top_mabd_paper_horizon.json"`;
- `step_count == 10000`;
- `sample_count == config.reference.sample_count == 11`;
- `time_step_s == 0.001`;
- `step_count * time_step_s == config.reference.duration_s`;
- rest points, masses, pivot, angle probe, gravity, rotation mode, and
  thresholds match `config.mabd_newton`.

- [ ] **Step 2: Add rollout expectations**

Add a targeted rollout test:

```python
rollout = roll_out_heavy_top_mabd_model_derived(
    config,
    mabd_config=config.mabd_paper_horizon,
)
self.assertEqual(rollout.step_count, 10000)
self.assertEqual(rollout.sample_count, 11)
self.assertAlmostEqual(rollout.samples[-1].time_s, 10.0)
self.assertTrue(rollout.finite)
```

Also assert all sample times match the RK4/reference grid within `1e-12`.

- [ ] **Step 3: Run tests and verify RED**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_run_configs tests.test_heavy_top_mabd
```

Expected: fail because `mabd_paper_horizon` and rollout override do not exist.

### Task 2: GREEN Config And Rollout Parameterization

**Files:**
- Modify: `configs/experiments/single_body_heavy_top.yaml`
- Modify: `src/mabd_reproduction/experiment_configs.py`
- Modify: `src/mabd_reproduction/heavy_top_mabd.py`

- [ ] **Step 1: Add config section**

Add `mabd_paper_horizon` to the heavy-top YAML by copying the short
`mabd_newton` diagnostic config and changing only `step_count`, `sample_count`,
and `output_report`.

- [ ] **Step 2: Parse and validate config**

Reuse the `HeavyTopMABDNewtonConfig` dataclass. Refactor the parser helper so it
can parse either `mabd_newton` or `mabd_paper_horizon` while producing key-aware
error messages.

Add validation that the paper-horizon lane:

- is output-report distinct;
- aligns to reference duration and sample count;
- has a sample stride that divides `step_count` evenly;
- mirrors short-lane geometry, mass distribution, pivot points, angle probe,
  gravity, rotation mode, and thresholds;
- uses the same point-mass sum and gravity constraints already required for the
  short MABD lane.

- [ ] **Step 3: Parameterize rollout**

Change:

```python
roll_out_heavy_top_mabd_model_derived(config)
```

to accept:

```python
roll_out_heavy_top_mabd_model_derived(config, *, mabd_config=None)
```

When `mabd_config` is supplied, use `dataclasses.replace(config,
mabd_newton=mabd_config)` internally so existing private helpers remain
localized and behavior stays unchanged for the default lane.

- [ ] **Step 4: Run GREEN tests**

Run the same targeted tests. They should pass.

### Task 3: RED Tests For Report Writer, Runner, CLI, And Comparison

**Files:**
- Modify: `tests/test_heavy_top_comparison_reports.py`
- Modify: `tests/test_experiment_runner.py`

- [ ] **Step 1: Add paper-horizon report writer expectations**

Add a helper that writes RK4 plus paper-horizon MABD lane reports. Assert the
MABD paper-horizon report has:

- `baseline_lane == "mabd_newton"`;
- `solver_mode == "mabd_cpu_oracle_heavy_top_newton_lane"`;
- `observed["mabd_diagnostic_scope"] == "paper_horizon_sample_grid"`;
- `observed["solver_model_config_source"] == "newton_model_derived"`;
- `observed["newton_model_derived_custom_frequencies"] == ["mabd:body",
  "mabd:world_constraint", "mabd:gravity"]`;
- `observed["step_count"] == 10000`;
- `observed["sample_count"] == 11`;
- `observed["duration_s"] == 10.0`;
- last sample time `10.0`;
- status `incomplete`;
- `full_experiment_claim_passed == false`.

The current diagnostic may record `lane_status =
incomplete_diagnostic_failed` and `max_affine_shape_spread_m` threshold
violations. That must be recorded as a non-pass, not hidden by Phase55.

- [ ] **Step 2: Add comparison expectations**

When the comparison consumes paper-horizon MABD input plus the figure report,
assert:

- `time_grid_mismatch is False`;
- `sample_time_grid_mismatch` is not in `blocking_reasons`;
- `matched_sample_index_count == 11`;
- `max_sample_time_delta_s <= threshold`;
- `input_report_provenance["mabd_newton"]["path"]` points to the
  paper-horizon report.
- `input_report_provenance["mabd_newton"]["mabd_diagnostic_scope"] ==
  "paper_horizon_sample_grid"`;
- comparison report status remains `incomplete`;
- `full_experiment_claim_passed == false`.

Retain checks for geometry, inertia, raw-curve,
`mabd_newton_report_incomplete`, `heavy_top_comparison_report_incomplete`,
timing, comparison pass gate, and figure-agreement blockers.

- [ ] **Step 3: Add runner and CLI expectations**

Add tests for:

- `run_heavy_top_mabd_paper_horizon(...)`;
- `scripts/run_experiment.py --lane heavy_top_mabd_paper_horizon`.

- [ ] **Step 4: Run tests and verify RED**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_heavy_top_comparison_reports tests.test_experiment_runner
```

Expected: fail because writer/runner/CLI do not exist.

### Task 4: GREEN Report Writer, Runner, CLI, And Artifacts

**Files:**
- Modify: `src/mabd_reproduction/heavy_top_reports.py`
- Modify: `src/mabd_reproduction/experiment_runner.py`
- Modify: `scripts/run_experiment.py`
- Add generated JSON report:
  `reports/experiment_matrix/single_body_heavy_top_mabd_paper_horizon.json`
- Modify generated JSON report:
  `reports/experiment_matrix/single_body_heavy_top_comparison.json`

- [ ] **Step 1: Add report writer**

Refactor the existing heavy-top MABD report writer into a private helper that
takes the lane config and a diagnostic scope string. Keep
`write_heavy_top_mabd_newton_report` behavior unchanged, and add
`write_heavy_top_mabd_paper_horizon_report`.

- [ ] **Step 2: Add runner and CLI lane**

Add `run_heavy_top_mabd_paper_horizon` and expose CLI choice
`heavy_top_mabd_paper_horizon`. Use the configured output report by default and
support `--output`/`--output-root` like the other heavy-top lanes.

- [ ] **Step 3: Regenerate reports**

After the implementation code is ready, make an implementation commit first.
Use that implementation commit hash, not a dirty worktree hash, as
`--source-commit` when regenerating reports. Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/run_experiment.py --lane heavy_top_mabd_paper_horizon --config configs/experiments/single_body_heavy_top.yaml --matrix configs/experiments/paper_experiment_matrix.yaml --source-commit "$(git rev-parse HEAD)" --vendored-newton-commit 96713fa965463b69c229a4d30582c733ff3526bb
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/run_experiment.py --lane heavy_top_comparison --config configs/experiments/single_body_heavy_top.yaml --matrix configs/experiments/paper_experiment_matrix.yaml --rbd-report reports/experiment_matrix/single_body_heavy_top_rk4_reference.json --mabd-report reports/experiment_matrix/single_body_heavy_top_mabd_paper_horizon.json --figure-report reports/experiment_matrix/single_body_heavy_top_figure_curves.json --source-commit "$(git rev-parse HEAD)" --vendored-newton-commit 96713fa965463b69c229a4d30582c733ff3526bb
```

- [ ] **Step 4: Run GREEN tests**

Run targeted tests from Task 3.

### Task 5: Docs, Record, Validator, And Final Verification

**Files:**
- Modify: `docs/reference/claim-boundaries.md`
- Add: `docs/records/2026-05-18-phase55-heavy-top-paper-horizon-mabd.md`
- Modify: `scripts/validate_docs.py`

- [ ] **Step 1: Update claim boundaries**

Add Phase55 bullets that state:

- current evidence includes a heavy-top 10 second MABD diagnostic report;
- comparison sample grids are aligned;
- `sample_time_grid_mismatch` is removed from current evidence;
- all paper-faithfulness and pass-gate non-claims remain.

- [ ] **Step 2: Add record**

Record:

- branch/worktree;
- base source commit;
- implementation commit after commit is created;
- vendored Newton commit;
- Python path;
- report paths and sha256 values;
- comparison sample counts and max time delta;
- retained blockers and explicit non-claims;
- validation commands.

- [ ] **Step 3: Update docs validator**

Add required paths and `validate_phase55_record()`.

Loosen Phase51-53 historical validators only enough to accept newer aligned
comparison evidence, then make Phase55 require:

- paper-horizon MABD report exists;
- comparison MABD provenance points to it;
- comparison MABD provenance records `paper_horizon_sample_grid`;
- no `sample_time_grid_mismatch`;
- `time_grid_mismatch is False`;
- aligned 11/11 samples;
- status remains `incomplete` and `full_experiment_claim_passed` remains false;
- the paper-horizon report records any current affine-shape threshold
  violation as a non-pass;
- no passed `experiment.*` claims.

- [ ] **Step 4: Full verification**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"
/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .
git diff --check
```

- [ ] **Step 5: Review, merge, push**

Request multi-angle review of the spec/implementation, fix confirmed issues,
commit, merge to `main`, push to `origin/main`, then remove the Phase55
worktree and branch after successful merge.
