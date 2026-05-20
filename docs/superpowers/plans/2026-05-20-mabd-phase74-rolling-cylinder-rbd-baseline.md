# Phase 74 Rolling Cylinder RBD Baseline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> superpowers:test-driven-development and superpowers:executing-plans to execute
> this plan. Keep each task small, run the listed red/green checks, and do not
> relax claim boundaries.

**Goal:** Add a real Newton CPU `rbd_implicit_baseline` report lane for the
rolling-cylinder part of `experiment.single_body.rolling_spinning`, while
keeping the full paper claim incomplete.

No `experiment.*` claim is passed by this phase.

**Architecture:** Extend the rolling/spinning config with an
`rbd_implicit_baseline` section, build and step a procedural cylinder on a Y-up
ground plane through vendored Newton, write a separate incomplete `ClaimReport`,
then validate the committed report and docs record.

**Tech Stack:** Python 3.10, `unittest`, PyYAML, NumPy, vendored Newton/Warp CPU.

---

### Task 1: Red Tests For Config Extension

**Files:**
- Modify: `tests/test_experiment_run_configs.py`
- Modify: `src/mabd_reproduction/experiment_configs.py`
- Modify: `configs/experiments/single_body_rolling_spinning.yaml`

- [ ] Add assertions that `load_rolling_spinning_config()` exposes
  `config.rbd_implicit_baseline`.
- [ ] Assert these config values:
  `output_report =
  reports/experiment_matrix/single_body_rolling_spinning_rbd_implicit_baseline.json`,
  `radius_m = 0.5`, `half_height_m = 0.5`, `density_kg_m3 = 1000.0`,
  `time_step_s = 0.01`, `step_count = 10000`, `sample_count = 7`,
  `initial_position_m = [0.0, 0.5, 0.0]`,
  `initial_linear_velocity_m_s = [1.0, 0.0, 0.0]`,
  `initial_angular_velocity_rad_s = [0.0, 0.0, -2.0]`,
  `gravity_m_s2 = [0.0, -9.81, 0.0]`.
- [ ] Assert contact material keys include `ke`, `kd`, `kf`, `mu`, `gap`, and
  that thresholds include `max_no_slip_residual_m_s`,
  `max_relative_energy_drift`, `min_contact_count`, and
  `max_runtime_wall_time_ms`.
- [ ] Add a validation test that rejects a mismatched
  `rbd_implicit_baseline.output_report`.
- [ ] Include invalid absolute paths, paths outside `reports/experiment_matrix/`,
  `.txt` paths, and reuse of the Phase 73 protocol report path.
- [ ] Run the targeted tests and confirm they fail because the dataclass and
  loader fields do not exist:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_run_configs.ExperimentRunConfigTests.test_rolling_spinning_config_is_machine_checkable tests.test_experiment_run_configs.ExperimentRunConfigTests.test_rolling_spinning_rbd_implicit_baseline_report_path_must_be_lane_specific
```

- [ ] Add `RollingSpinningRBDBaselineConfig` and parse the YAML section.
- [ ] Add report-path validation for the lane-specific JSON path.
- [ ] Run the targeted tests and confirm they pass.

### Task 2: Red Tests For Newton RBD Baseline Report

**Files:**
- Modify: `tests/test_experiment_runner.py`
- Modify: `src/mabd_reproduction/rolling_spinning_reports.py`
- Modify: `src/mabd_reproduction/experiment_runner.py`
- Modify: `scripts/run_experiment.py`

- [ ] Add a helper that writes a short rolling/spinning config with
  `rbd_implicit_baseline.step_count = 4` and a temporary output path.
- [ ] Add a unit test for `write_rolling_spinning_rbd_implicit_baseline_report`
  or the runner that verifies:
  `status = incomplete`,
  `baseline_lane = rbd_implicit_baseline`,
  `solver_mode =
  newton_semimplicit_rolling_cylinder_rbd_cpu_development`,
  `backend = cpu_newton_warp`,
  `observed.local_runtime_measured = true`,
  `observed.contact_count_summary.max >= 1`,
  finite integer `observed.contact_count_summary.initial/final/min/max`,
  `observed.newton_device = cpu`,
  `observed.cylinder_axis_world = [0.0, 0.0, 1.0]`,
  `observed.contact_material` matching config,
  finite `observed.max_center_penetration_m`,
  `observed.paper_comparable = false`, and
  `timing_distribution.paper_comparable = false`.
- [ ] Verify the report has
  `observed.full_experiment_claim_passed = false`,
  exact `observed.required_lanes_missing =
  ["rbd_explicit_baseline", "mabd_newton", "paper_comparable_timing"]`,
  and blockers for missing explicit RBD, missing M-ABD rolling cylinder,
  missing paper-comparable timing, and SemiImplicit not being the paper-exact
  implicit RBD solver.
- [ ] Add a CLI smoke test for
  `--lane rolling_spinning_rbd_implicit_baseline`.
- [ ] Run the targeted tests and confirm they fail because the lane does not
  exist.
- [ ] Implement `RollingCylinderRBDBaselineResult`, scene construction, sampling,
  metrics, report writer, runner function, and CLI branch.
- [ ] Build Newton with `builder.add_body(...)`,
  `builder.add_shape_cylinder(body, cfg=ModelBuilder.ShapeConfig(...))`,
  `builder.add_ground_plane(...)`, `builder.finalize(device="cpu")`,
  `contacts = model.contacts()`, and `model.collide(state, contacts)`.
- [ ] Keep the cylinder body orientation at identity so the local Z cylinder
  axis is world Z and the no-slip residual uses `v_x + omega_z * radius`.
- [ ] Keep the writer redirecting Newton/Warp stdout to stderr to preserve JSON
  CLI stdout.
- [ ] Run the targeted tests and confirm they pass.

### Task 3: Generate Full-Horizon Report

**Files:**
- Add:
  `reports/experiment_matrix/single_body_rolling_spinning_rbd_implicit_baseline.json`

- [ ] Capture source commit and vendored Newton commit.
- [ ] Run the full configured lane:

```bash
SOURCE_COMMIT=$(git rev-parse HEAD)
VENDORED_NEWTON_COMMIT=96713fa965463b69c229a4d30582c733ff3526bb
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/run_experiment.py --lane rolling_spinning_rbd_implicit_baseline --config configs/experiments/single_body_rolling_spinning.yaml --matrix configs/experiments/paper_experiment_matrix.yaml --output reports/experiment_matrix/single_body_rolling_spinning_rbd_implicit_baseline.json --source-commit "$SOURCE_COMMIT" --vendored-newton-commit "$VENDORED_NEWTON_COMMIT"
```

- [ ] Inspect the report and confirm it remains `incomplete` and
  `paper_comparable = false`.
- [ ] Confirm the report includes source lines, source/vendored commits,
  paper source version, canonical Python path, non-passing flags, blockers, and
  the exact remaining missing lane list.
- [ ] Record the report SHA256 for docs validation.

### Task 4: Docs And Validation Gate

**Files:**
- Modify: `docs/reference/claim-boundaries.md`
- Modify: `docs/reference/reproduction-gap-audit.yaml`
- Add: `docs/records/2026-05-20-phase74-rolling-cylinder-rbd-baseline.md`
- Modify: `scripts/validate_docs.py`
- Modify: `tests/test_phase0_bootstrap.py`

- [ ] Add Phase 74 boundary bullets:
  current claim, verified evidence, non-claims, and forbidden interpretations.
- [ ] Update the gap audit rolling/spinning entry so it references the new
  implicit RBD baseline report and still records the overall experiment as
  incomplete.
- [ ] Add a dated record with source commit, implementation commit, report SHA,
  exact commands, and explicit non-claims.
- [ ] Extend `scripts/validate_docs.py` with `validate_phase74_record()`.
- [ ] Add bootstrap tests that call the new validation function and inspect the
  committed report fields.
- [ ] Run targeted docs tests and fix issues.

### Task 5: Final Verification And Commits

- [ ] Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_run_configs tests.test_experiment_runner tests.test_phase0_bootstrap
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .
git diff --check
scripts/env/readiness_check.py
scripts/env/clone_from_reference.py --dry-run
scripts/env/clone_from_reference.py --dry-run --sync-existing
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"
```

- [ ] Commit plan/spec changes after review fixes.
- [ ] Commit implementation and tests.
- [ ] Commit generated report and docs record.
