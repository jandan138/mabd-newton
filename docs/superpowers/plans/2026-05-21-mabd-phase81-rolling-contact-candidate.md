# Phase 81 MABD Rolling Contact Candidate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a fail-closed rolling-cylinder M-ABD contact candidate lane using existing `SolverMABD` world-constraint contact plumbing.

**Architecture:** Extend the rolling/spinning M-ABD config with a lane-specific `mabd_rolling_contact_candidate` section and `contact_constraint_mode` field. Reuse the current affine-cylinder/static-plane model, but configure the CPU oracle with `contact_constraint_mode="world"` for this lane, record contact conversion summaries, and keep all paper-faithful blockers open.

**Tech Stack:** Python 3.10, `unittest`, PyYAML, NumPy, vendored Newton `SolverMABD`, existing `ClaimReport`, canonical `mabd-newton-py310` environment.

No `experiment.*` claim is passed by this phase.

---

### Task 1: Candidate Config Contract

**Files:**
- Modify: `src/mabd_reproduction/experiment_configs.py`
- Modify: `configs/experiments/single_body_rolling_spinning.yaml`
- Test: `tests/test_experiment_run_configs.py`

- [ ] **Step 1: Write the failing config test**

Add `test_rolling_spinning_mabd_rolling_contact_candidate_is_fail_closed`.
It must load `single_body_rolling_spinning.yaml` and assert:

```python
config = load_rolling_spinning_config(ROLLING_SPINNING_CONFIG_PATH)
lane = config.mabd_rolling_contact_candidate
self.assertEqual(
    lane.output_report,
    "reports/experiment_matrix/single_body_rolling_spinning_mabd_rolling_contact_candidate.json",
)
self.assertEqual(lane.contact_constraint_mode, "world")
self.assertEqual(lane.young_modulus_pa, 1.0e9)
self.assertEqual(lane.poisson_ratio, 0.3)
self.assertFalse(lane.zero_stiffness_diagnostic)
self.assertEqual(lane.time_step_s, 0.01)
self.assertEqual(lane.step_count, 10000)
self.assertEqual(config.required_missing_lanes, ("rbd_implicit_baseline", "rbd_explicit_baseline"))
```

- [ ] **Step 2: Run the test and verify it fails**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_run_configs.ExperimentRunConfigTests.test_rolling_spinning_mabd_rolling_contact_candidate_is_fail_closed
```

Expected: fail because `RollingSpinningRunConfig` has no
`mabd_rolling_contact_candidate` field.

- [ ] **Step 3: Implement minimal config support**

Add:

```python
ROLLING_SPINNING_MABD_ROLLING_CONTACT_CANDIDATE_OUTPUT_REPORT = (
    "reports/experiment_matrix/"
    "single_body_rolling_spinning_mabd_rolling_contact_candidate.json"
)
```

Add `contact_constraint_mode: str = "plane"` to
`RollingSpinningMABDNewtonConfig`. Parse it in `_require_rolling_spinning_mabd_newton`
with:

```python
contact_constraint_mode = str(section.get("contact_constraint_mode", "plane"))
if contact_constraint_mode not in {"plane", "world"}:
    raise ExperimentRunConfigError(f"{key}.contact_constraint_mode must be plane or world")
```

Add `mabd_rolling_contact_candidate` to `RollingSpinningRunConfig`, parse it via
`_require_rolling_spinning_mabd_newton(...)`, and add YAML copied from
`mabd_material_preflight` with the new output path and
`contact_constraint_mode: world`.

- [ ] **Step 4: Add validation and negative tests**

Add a negative test that replaces `config.mabd_rolling_contact_candidate` with:

```python
replace(config.mabd_rolling_contact_candidate, contact_constraint_mode="plane")
```

and expects `ExperimentRunConfigError` containing `contact_constraint_mode`.

In `validate_rolling_spinning_config_against_matrix`, enforce the candidate:

- output path equals the new lane-specific report path
- output path is distinct from all existing rolling/spinning reports
- finite material settings match `mabd_material_preflight`
- `zero_stiffness_diagnostic is False`
- `contact_constraint_mode == "world"`
- `step_count == config.performance.step_count`
- `time_step_s == config.performance.time_step_s`

- [ ] **Step 5: Run config tests**

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

- [ ] **Step 1: Write the failing runner test**

Add `test_run_rolling_spinning_mabd_rolling_contact_candidate_writes_report`.
It must call `run_rolling_spinning_mabd_rolling_contact_candidate(...)` with a
temporary output path and assert:

```python
self.assertEqual(loaded.baseline_lane, "mabd_rolling_contact_candidate")
self.assertEqual(
    loaded.solver_mode,
    "newton_mabd_rolling_contact_world_constraint_candidate",
)
self.assertEqual(loaded.backend, "cpu_newton_mabd_world_constraints")
self.assertEqual(loaded.observed["contact_constraint_mode"], "world")
self.assertTrue(loaded.observed["local_runtime_measured"])
self.assertFalse(loaded.observed["paper_comparable"])
self.assertFalse(loaded.observed["full_experiment_claim_passed"])
self.assertIn(
    "mabd_rolling_contact_candidate_not_paper_faithful",
    loaded.observed["blocking_reasons"],
)
self.assertIn("generated_world_constraint_count_summary", loaded.observed)
self.assertGreaterEqual(
    loaded.observed["generated_world_constraint_count_summary"]["max"],
    1,
)
self.assertGreater(loaded.timing_distribution["total_wall_time_ms"], 0.0)
```

- [ ] **Step 2: Run the test and verify it fails**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_runner.ExperimentRunnerTests.test_run_rolling_spinning_mabd_rolling_contact_candidate_writes_report
```

Expected: import or attribute failure because the runner does not exist.

- [ ] **Step 3: Implement world-constraint candidate execution**

Add a helper in `rolling_spinning_reports.py`:

```python
def run_rolling_cylinder_mabd_rolling_contact_candidate(
    config: RollingSpinningMABDNewtonConfig,
) -> RollingCylinderMABDNewtonResult:
    return _run_rolling_cylinder_mabd_with_contact_mode(
        config,
        contact_constraint_mode="world",
    )
```

Refactor the current `run_rolling_cylinder_mabd_newton` body into a shared
private helper that accepts `contact_constraint_mode`. For `"world"`, after
building the model and solver, configure the CPU oracle:

```python
solver.configure_cpu_oracle(
    mabd.MABDCPUOracleConfig(
        bodies=[solver._body_precompute_from_model_row(0)],
        gravity=config.gravity_m_s2,
        contact_constraint_mode="world",
        topology="dense",
    )
)
```

Collect `generated_world_constraint_count` and
`generated_plane_constraint_count` from `solver.last_contacts_input_summary`
after every solver step and return min/max/initial/final summaries in
`RollingCylinderMABDNewtonResult`.

- [ ] **Step 4: Add report writer and Python runner**

Add `write_rolling_spinning_mabd_rolling_contact_candidate_report(...)` and
`run_rolling_spinning_mabd_rolling_contact_candidate(...)`.

The report must set:

```python
baseline_lane="mabd_rolling_contact_candidate"
solver_mode="newton_mabd_rolling_contact_world_constraint_candidate"
backend="cpu_newton_mabd_world_constraints"
status=EvidenceStatus.INCOMPLETE
observed["contact_constraint_mode"] = "world"
observed["blocking_reasons"] = [
    "mabd_rolling_contact_candidate_not_paper_faithful",
    "diagnostic_world_constraints_not_paper_friction_law",
    "paper_affine_rolling_contact_details_missing",
    "paper_faithful_explicit_rbd_baseline_missing",
    "paper_faithful_implicit_rbd_baseline_missing",
    "paper_comparable_timing_missing",
]
```

- [ ] **Step 5: Add CLI lane and CLI test**

Add CLI choice and dispatch branch:

```text
rolling_spinning_mabd_rolling_contact_candidate
```

Add a subprocess test that runs this lane and verifies the output JSON summary
has `baseline_lane == "mabd_rolling_contact_candidate"`.

- [ ] **Step 6: Run runner tests**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_runner
```

Expected: all runner tests pass.

### Task 3: Evidence, Claim Boundaries, And Validation

**Files:**
- Add: `reports/experiment_matrix/single_body_rolling_spinning_mabd_rolling_contact_candidate.json`
- Add: `docs/records/2026-05-21-phase81-mabd-rolling-contact-candidate.md`
- Modify: `docs/reference/claim-boundaries.md`
- Modify: `docs/reference/reproduction-gap-audit.yaml`
- Modify: `scripts/validate_docs.py`
- Test: `tests/test_phase0_bootstrap.py`

- [ ] **Step 1: Generate the candidate report**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/run_experiment.py --lane rolling_spinning_mabd_rolling_contact_candidate --config configs/experiments/single_body_rolling_spinning.yaml --matrix configs/experiments/paper_experiment_matrix.yaml --source-commit 03733a3 --vendored-newton-commit 96713fa965463b69c229a4d30582c733ff3526bb
```

Record the report SHA256 with:

```bash
sha256sum reports/experiment_matrix/single_body_rolling_spinning_mabd_rolling_contact_candidate.json
```

- [ ] **Step 2: Update docs and gap audit**

Record Phase81 in:

- `docs/records/2026-05-21-phase81-mabd-rolling-contact-candidate.md`
- `docs/reference/claim-boundaries.md`
- `docs/reference/reproduction-gap-audit.yaml`

The gap audit must add the candidate report path and SHA, update
`latest_update.phase_id` to `phase81_mabd_rolling_contact_candidate`, and keep
`remaining_reproduction_gaps_after_phase81` equal to:

```yaml
- paper_faithful_explicit_rbd_baseline
- paper_faithful_implicit_rbd_baseline
- paper_faithful_mabd_rolling_cylinder
- paper_comparable_timing
```

- [ ] **Step 3: Add bootstrap/docs validation**

Add `validate_phase81_record()` to `scripts/validate_docs.py` and bootstrap
tests requiring:

- spec/plan/record paths exist
- report path exists and hash matches
- `baseline_lane = mabd_rolling_contact_candidate`
- `solver_mode = newton_mabd_rolling_contact_world_constraint_candidate`
- `backend = cpu_newton_mabd_world_constraints`
- `observed.contact_constraint_mode = world`
- all Phase81 blockers are present
- no `experiment.*` claim is passed

- [ ] **Step 4: Run final validation**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"
git diff --check
```

Expected: all commands pass.
