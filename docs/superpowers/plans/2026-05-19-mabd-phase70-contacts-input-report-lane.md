# Phase 70 Contacts Input Report Lane Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a single-body spinning-box diagnostic report lane that passes bounded Newton `Contacts` rows into `SolverMABD.step(..., contacts=...)`.

**Architecture:** Reuse the Phase 68 paper-horizon rollout structure and Phase 69 contacts-input plumbing. The new lane builds transient Newton models with an M-ABD body shape and a world-static plane shape, synthesizes `newton.Contacts` rows from existing diagnostic corner/plane contacts, and records `last_contacts_input_summary` without claiming collision detection or any experiment pass.

**Tech Stack:** Python 3.10, `unittest`, vendored Newton, `newton.Contacts`, `SolverMABD`, YAML configs, JSON claim reports.

---

## File Structure

- Modify `configs/experiments/single_body_spinning_box.yaml`: add `paper_horizon.contacts_input_output_report`.
- Modify `src/mabd_reproduction/experiment_configs.py`: add config field and path validation.
- Modify `src/mabd_reproduction/single_body_reports.py`: add contacts-input constants, step helper, paper-horizon mode, and report writer.
- Modify `src/mabd_reproduction/experiment_runner.py`: expose `run_spinning_box_contacts_input`.
- Modify `scripts/run_experiment.py`: add `spinning_box_contacts_input` CLI lane.
- Modify tests:
  - `tests/test_experiment_run_configs.py`
  - `tests/test_single_body_report_lane.py`
  - `tests/test_experiment_runner.py`
  - `tests/test_spinning_box_report_artifacts.py`
  - `tests/test_phase0_bootstrap.py`
- Create `reports/experiment_matrix/single_body_spinning_box_contacts_input.json`.
- Modify `docs/reference/claim-boundaries.md`, `scripts/validate_docs.py`, and create
  `docs/records/2026-05-19-phase70-contacts-input-report-lane.md`.

## Task 1: Config Contract

**Files:**
- Modify `tests/test_experiment_run_configs.py`
- Modify `configs/experiments/single_body_spinning_box.yaml`
- Modify `src/mabd_reproduction/experiment_configs.py`

- [ ] **Step 1: Write failing config tests**

Add assertions to `test_spinning_box_config_is_machine_checkable`:

```python
self.assertEqual(
    config.paper_horizon.contacts_input_output_report,
    "reports/experiment_matrix/single_body_spinning_box_contacts_input.json",
)
```

Add a focused validation test:

```python
def test_spinning_box_contacts_input_report_path_must_be_lane_specific(self) -> None:
    matrix = load_experiment_matrix(ROOT / "configs/experiments/paper_experiment_matrix.yaml")
    config = load_spinning_box_config(ROOT / "configs/experiments/single_body_spinning_box.yaml")

    self.assertEqual(
        config.paper_horizon.contacts_input_output_report,
        "reports/experiment_matrix/single_body_spinning_box_contacts_input.json",
    )
    validate_spinning_box_config_against_matrix(config, matrix)

    invalid_paths = (
        config.output_report,
        config.paper_horizon.output_report,
        config.paper_horizon.contact_response_output_report,
        config.paper_horizon.normal_constraint_output_report,
        config.paper_horizon.model_plane_constraint_output_report,
        config.paper_horizon.decoupled_twist_output_report,
        config.paper_horizon.figure_curve_output_report,
        "reports/experiment_matrix/not_the_spinning_box_contacts_input.json",
        "reports/experiment_matrix/single_body_spinning_box_contacts_input.txt",
    )
    for invalid_path in invalid_paths:
        with self.subTest(invalid_path=invalid_path):
            invalid = replace(
                config,
                paper_horizon=replace(
                    config.paper_horizon,
                    contacts_input_output_report=invalid_path,
                ),
            )
            with self.assertRaisesRegex(
                ExperimentRunConfigError,
                "paper_horizon.contacts_input_output_report",
            ):
                validate_spinning_box_config_against_matrix(invalid, matrix)
```

- [ ] **Step 2: Verify RED**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_run_configs.ExperimentRunConfigTests.test_spinning_box_config_is_machine_checkable tests.test_experiment_run_configs.ExperimentRunConfigTests.test_spinning_box_contacts_input_report_path_must_be_lane_specific
```

Expected: FAIL because `contacts_input_output_report` does not exist.

- [ ] **Step 3: Implement config field**

Add `contacts_input_output_report: str` to `SpinningBoxPaperHorizonConfig`, parse it in `_require_paper_horizon`, and add this YAML field:

```yaml
contacts_input_output_report: reports/experiment_matrix/single_body_spinning_box_contacts_input.json
```

In `validate_spinning_box_config_against_matrix`, require the path to start with the experiment output stem, end with `.json`, and be distinct from all existing spinning-box lane paths.

- [ ] **Step 4: Verify GREEN**

Run the same unittest command. Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/test_experiment_run_configs.py configs/experiments/single_body_spinning_box.yaml src/mabd_reproduction/experiment_configs.py
git commit -m "feat: configure spinning-box contacts input lane"
```

## Task 2: Contacts-Input Solver Step Helper And Report Writer

**Files:**
- Modify `tests/test_single_body_report_lane.py`
- Modify `src/mabd_reproduction/single_body_reports.py`

- [ ] **Step 1: Write failing helper and report tests**

Import the new helper and writer:

```python
from mabd_reproduction.single_body_reports import (
    _run_spinning_box_solver_mabd_contacts_input_step,
    write_spinning_box_contacts_input_report,
)
```

Add helper parity coverage:

```python
def test_solver_mabd_contacts_input_step_records_static_plane_summary(self) -> None:
    from mabd_reproduction.experiment_configs import load_spinning_box_config
    from mabd_reproduction.single_body_reports import _oracle_body
    from mabd_reproduction.spinning_box_physics import (
        spinning_box_contact_diagnostics,
        spinning_box_cube_corners,
    )
    from newton.solvers import mabd

    root = Path(__file__).resolve().parents[1]
    config = load_spinning_box_config(root / "configs/experiments/single_body_spinning_box.yaml")
    penetrating_q = config.initial_q.copy()
    penetrating_q[10] = -0.02
    contact = spinning_box_contact_diagnostics(config, penetrating_q, config.initial_qd)
    constraints = [
        mabd.MABDCPUOraclePlaneConstraint(
            body=0,
            rest_point=corner,
            plane_normal=config.contact_surface["plane_normal"],
            plane_offset=float(config.contact_surface["plane_offset"]),
        )
        for corner, signed_distance in zip(
            spinning_box_cube_corners(config),
            contact.corner_signed_distances,
            strict=True,
        )
        if float(signed_distance) < 0.0
    ]
    self.assertGreater(len(constraints), 0)

    oracle_result = mabd.solve_cpu_oracle_step(
        q=[penetrating_q],
        qd=[config.initial_qd],
        dt=0.01,
        config=mabd.MABDCPUOracleConfig(
            bodies=[_oracle_body(config)],
            plane_constraints=constraints,
            topology="dense",
        ),
    )

    result = _run_spinning_box_solver_mabd_contacts_input_step(
        config=config,
        q=penetrating_q,
        qd=config.initial_qd,
        time_step_s=0.01,
        contact_constraints=constraints,
    )

    self.assertEqual(result.contacts_input_policy, "rigid_contacts_to_point_plane_constraints_diagnostic")
    self.assertEqual(
        result.contacts_input_source,
        "newton.Contacts.rigid_contact_static_plane_rows_from_diagnostic_corners",
    )
    self.assertEqual(result.contacts_input_summary_source, "newton.Contacts.rigid_contact_*")
    self.assertEqual(result.contacts_input_scope, "diagnostic_only_static_geometry_plane_constraints")
    self.assertEqual(result.contacts_input_rigid_contact_count, len(constraints))
    self.assertEqual(result.contacts_input_rows_read, len(constraints))
    self.assertEqual(result.contacts_input_generated_plane_constraint_count, len(constraints))
    self.assertEqual(result.contacts_input_skipped_contact_count, 0)
    self.assertEqual(result.plane_constraint_requested_count, len(constraints))
    np.testing.assert_allclose(result.q, oracle_result.q[0], rtol=1.0e-6, atol=1.0e-5)
    np.testing.assert_allclose(result.qd, oracle_result.qd[0], rtol=1.0e-6, atol=1.0e-5)
    self.assertEqual(
        result.plane_constraint_accepted_count,
        int(getattr(oracle_result, "plane_constraint_accepted_count", 0)),
    )
    self.assertEqual(
        result.plane_constraint_skipped_count,
        int(getattr(oracle_result, "plane_constraint_skipped_count", 0)),
    )
    self.assertTrue(np.all(np.isfinite(result.q)))
    self.assertTrue(np.all(np.isfinite(result.qd)))
```

Add no-active-contact branch coverage:

```python
def test_solver_mabd_contacts_input_step_records_contacts_none_when_no_active_rows(self) -> None:
    from mabd_reproduction.experiment_configs import load_spinning_box_config

    root = Path(__file__).resolve().parents[1]
    config = load_spinning_box_config(root / "configs/experiments/single_body_spinning_box.yaml")

    result = _run_spinning_box_solver_mabd_contacts_input_step(
        config=config,
        q=config.initial_q,
        qd=np.zeros(12, dtype=float),
        time_step_s=0.01,
        contact_constraints=[],
    )

    self.assertEqual(result.contacts_input_source, "newton.Contacts.rigid_contact_static_plane_rows_from_diagnostic_corners")
    self.assertEqual(result.contacts_input_summary_source, "contacts_none_no_active_diagnostic_contacts")
    self.assertEqual(result.contacts_input_rigid_contact_count, 0)
    self.assertEqual(result.contacts_input_rows_read, 0)
    self.assertEqual(result.contacts_input_generated_plane_constraint_count, 0)
    self.assertEqual(result.contacts_input_skipped_contact_count, 0)
    self.assertEqual(result.plane_constraint_requested_count, 0)
    self.assertTrue(np.all(np.isfinite(result.q)))
    self.assertTrue(np.all(np.isfinite(result.qd)))
```

Add report contract coverage:

```python
def test_spinning_box_contacts_input_report_records_newton_contacts_lane(self) -> None:
    from mabd_reproduction.experiment_configs import load_spinning_box_config

    root = Path(__file__).resolve().parents[1]
    config = load_spinning_box_config(root / "configs/experiments/single_body_spinning_box.yaml")
    short_config = replace(
        config,
        paper_horizon=replace(config.paper_horizon, duration_s=0.02, sample_count=3),
    )
    with TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "single_body_spinning_box_contacts_input.json"
        report = write_spinning_box_contacts_input_report(
            path,
            config=short_config,
            source_commit="test-source",
            vendored_newton_commit="test-newton",
        )
        loaded = load_claim_report(path)

    self.assertEqual(report.scene_id, config.scene_id)
    self.assertEqual(loaded.status, EvidenceStatus.INCOMPLETE)
    self.assertEqual(loaded.solver_mode, "solver_mabd_contacts_input_diagnostic")
    self.assertEqual(loaded.backend, "cpu_numpy_newton_solver_mabd_contacts_input_diagnostic")
    self.assertNotIn("lane_gate_status", loaded.observed)
    self.assertEqual(
        loaded.observed["contacts_input_policy"],
        "solver_mabd_contacts_input_free_predict_then_static_plane_constraints",
    )
    self.assertEqual(
        loaded.observed["contacts_input_source"],
        "newton.Contacts.rigid_contact_static_plane_rows_from_diagnostic_corners",
    )
    self.assertEqual(
        loaded.observed["contacts_input_summary_source"],
        "last_contacts_input_summary",
    )
    self.assertGreater(loaded.observed["max_contacts_input_generated_plane_constraint_count"], 0)
    self.assertEqual(loaded.observed["max_contacts_input_overflow_count"], 0)
    self.assertLess(
        loaded.observed["max_constrained_contact_penetration_m"],
        loaded.observed["max_free_predicted_contact_penetration_m"],
    )
    self.assertTrue(loaded.observed["contacts_input_reduced_free_predicted_penetration"])
    self.assertIn("spinning_box_contacts_input_not_paper_faithful", loaded.observed["blocking_reasons"])
    self.assertIn("collision_detection_not_enabled_for_contacts_input", loaded.observed["blocking_reasons"])
    for entry in loaded.observed["contacts_input_results"]:
        self.assertEqual(
            entry["contacts_input_policy"],
            "solver_mabd_contacts_input_free_predict_then_static_plane_constraints",
        )
        self.assertEqual(
            entry["contacts_input_source"],
            "newton.Contacts.rigid_contact_static_plane_rows_from_diagnostic_corners",
        )
        self.assertIn("contacts_input_summary_source", entry)
        self.assertEqual(entry["contacts_input_scope"], "diagnostic_only_static_geometry_plane_constraints_no_lane_gate")
        self.assertEqual(entry["contacts_input_overflow_count"], 0)
        self.assertGreaterEqual(entry["contacts_input_generated_plane_constraint_count"], 0)
        self.assertTrue(np.isfinite(entry["max_contacts_input_constraint_residual_norm"]))
```

- [ ] **Step 2: Verify RED**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_single_body_report_lane.SingleBodyReportLaneTests.test_solver_mabd_contacts_input_step_records_static_plane_summary tests.test_single_body_report_lane.SingleBodyReportLaneTests.test_solver_mabd_contacts_input_step_records_contacts_none_when_no_active_rows tests.test_single_body_report_lane.SingleBodyReportLaneTests.test_spinning_box_contacts_input_report_records_newton_contacts_lane
```

Expected: FAIL because the helper and writer do not exist.

- [ ] **Step 3: Implement helper and report writer**

Add constants:

```python
CONTACTS_INPUT_POLICY = "solver_mabd_contacts_input_free_predict_then_static_plane_constraints"
CONTACTS_INPUT_SCOPE = "diagnostic_only_static_geometry_plane_constraints_no_lane_gate"
CONTACTS_INPUT_SOURCE = "newton.Contacts.rigid_contact_static_plane_rows_from_diagnostic_corners"
CONTACTS_INPUT_BACKEND = "cpu_numpy_newton_solver_mabd_contacts_input_diagnostic"
```

Add a `SolverMABDContactsInputStepResult` dataclass with flat `q`/`qd` arrays, residuals, plane counts, contacts-summary fields, `contacts_input_source=CONTACTS_INPUT_SOURCE`, and `contacts_input_summary_source` copied from `solver.last_contacts_input_summary.source` when contacts are present. When `contact_constraints` is empty, call `SolverMABD.step(..., contacts=None)` and set `contacts_input_summary_source="contacts_none_no_active_diagnostic_contacts"` with zero contact counts. Implement `_run_spinning_box_solver_mabd_contacts_input_step` next to `_run_spinning_box_solver_mabd_model_step`; the helper must not add `mabd:plane_constraint` custom rows.

Extend `_run_spinning_box_paper_horizon_step_size` with a mutually exclusive `contacts_input_policy` branch and write `write_spinning_box_contacts_input_report` mirroring the Phase 68 model-plane report shape with contacts-specific keys. Because `SolverMABDContactsInputStepResult` uses flat arrays like `SolverMABDModelStepResult`, update the state assignment branch so both `model_plane_constraint_policy is not None` and `contacts_input_policy is not None` assign `q = result.q` and `qd = result.qd`; do not index `result.q[0]`/`result.qd[0]` for contacts-input results.

- [ ] **Step 4: Verify GREEN**

Run the same unittest command. Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/test_single_body_report_lane.py src/mabd_reproduction/single_body_reports.py
git commit -m "feat: add spinning-box contacts input report writer"
```

## Task 3: Runner And CLI Lane

**Files:**
- Modify `tests/test_experiment_runner.py`
- Modify `src/mabd_reproduction/experiment_runner.py`
- Modify `scripts/run_experiment.py`

- [ ] **Step 1: Write failing runner and CLI tests**

Add `test_run_spinning_box_contacts_input_writes_explicit_output_report` mirroring the model-plane runner test but expecting:

```python
loaded.solver_mode == "solver_mabd_contacts_input_diagnostic"
loaded.backend == "cpu_numpy_newton_solver_mabd_contacts_input_diagnostic"
loaded.observed["contacts_input_source"] == "newton.Contacts.rigid_contact_static_plane_rows_from_diagnostic_corners"
```

Add `test_run_spinning_box_contacts_input_requires_explicit_output` expecting:

```text
spinning_box_contacts_input requires --output
```

Add CLI dispatch test using:

```bash
--lane spinning_box_contacts_input
```

and assert the same solver mode/backend.

- [ ] **Step 2: Verify RED**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_runner.ExperimentRunnerTests.test_run_spinning_box_contacts_input_writes_explicit_output_report tests.test_experiment_runner.ExperimentRunnerTests.test_run_spinning_box_contacts_input_requires_explicit_output tests.test_experiment_runner.ExperimentRunnerTests.test_run_experiment_cli_writes_spinning_box_contacts_input_report
```

Expected: FAIL because runner and CLI lane do not exist.

- [ ] **Step 3: Implement runner and CLI**

Import `write_spinning_box_contacts_input_report`, add `run_spinning_box_contacts_input`, add CLI choice `spinning_box_contacts_input`, and dispatch it with the side-lane rule: `--output` required and `--output-root` rejected.

- [ ] **Step 4: Verify GREEN**

Run the same unittest command. Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/test_experiment_runner.py src/mabd_reproduction/experiment_runner.py scripts/run_experiment.py
git commit -m "feat: add spinning-box contacts input CLI lane"
```

## Task 4: Artifact, Docs, And Validator

**Files:**
- Create `reports/experiment_matrix/single_body_spinning_box_contacts_input.json`
- Modify `tests/test_spinning_box_report_artifacts.py`
- Modify `docs/reference/claim-boundaries.md`
- Create `docs/records/2026-05-19-phase70-contacts-input-report-lane.md`
- Modify `scripts/validate_docs.py`
- Modify `tests/test_phase0_bootstrap.py`

- [ ] **Step 1: Write failing artifact and validator tests**

Add the contacts-input report to `REPORT_PATHS` in `tests/test_spinning_box_report_artifacts.py` and add a test that asserts solver mode, backend, contacts-input policy/source/scope, reduced penetration, incomplete status, no `lane_gate_status`, and blockers.

Add a Phase70 bootstrap validator test in `tests/test_phase0_bootstrap.py` requiring:

```text
Phase 70
spinning_box_contacts_input
newton.Contacts.rigid_contact_static_plane_rows_from_diagnostic_corners
No `experiment.*` claim is passed.
```

- [ ] **Step 2: Verify RED**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_spinning_box_report_artifacts tests.test_phase0_bootstrap.Phase0BootstrapTests.test_phase70_contacts_input_report_lane_is_bounded
```

Expected: FAIL because report/docs/validator entries do not exist.

- [ ] **Step 3: Generate report artifact**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/run_experiment.py --lane spinning_box_contacts_input --config configs/experiments/single_body_spinning_box.yaml --matrix configs/experiments/paper_experiment_matrix.yaml --output reports/experiment_matrix/single_body_spinning_box_contacts_input.json --source-commit "$(git rev-parse HEAD)" --vendored-newton-commit 96713fa965463b69c229a4d30582c733ff3526bb
```

Expected: JSON summary with status `incomplete`.

- [ ] **Step 4: Implement docs validator**

Update `scripts/validate_docs.py` title, required paths, constants, and add `validate_phase70_record()`. The validator must require:

- report status `incomplete`;
- solver mode `solver_mabd_contacts_input_diagnostic`;
- backend `cpu_numpy_newton_solver_mabd_contacts_input_diagnostic`;
- source `newton.Contacts.rigid_contact_static_plane_rows_from_diagnostic_corners`;
- summary source `last_contacts_input_summary`;
- static-geometry scope;
- no `lane_gate_status`;
- `experiment.*` claims still `intended`;
- overclaim guards for collision detection, contact solver,
  generic inequality-constrained M-ABD KKT, paper-faithful contact,
  paper-faithful M-ABD stepping, comparison pass gate, rendered-output
  agreement, runtime performance, passed experiment, and full reproduction.

Add Phase70 bullets to `claim-boundaries.md` and a dated record with commands, hashes, env isolation, and non-claim language.

- [ ] **Step 5: Verify GREEN**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_spinning_box_report_artifacts tests.test_phase0_bootstrap.Phase0BootstrapTests.test_phase70_contacts_input_report_lane_is_bounded
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add reports/experiment_matrix/single_body_spinning_box_contacts_input.json tests/test_spinning_box_report_artifacts.py docs/reference/claim-boundaries.md docs/records/2026-05-19-phase70-contacts-input-report-lane.md scripts/validate_docs.py tests/test_phase0_bootstrap.py
git commit -m "docs: record Phase70 contacts input report evidence"
```

## Task 5: Full Verification

**Files:**
- No code changes unless verification exposes a real defect.

- [ ] **Step 1: Run focused and full gates**

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/env/readiness_check.py
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"
git diff --check
```

Expected: all pass; readiness reports no ambient/reference pollution.

- [ ] **Step 2: Commit verification fixes if needed**

Only commit fixes that are directly required by the gates.

```bash
git status --short
```

Expected: clean or only intentional committed changes.

## Self-Review

- Spec coverage: config, helper, report, runner, CLI, artifact, docs, and validation are covered.
- Placeholder scan: no unfinished markers or unspecified code tasks remain.
- Type consistency: names are consistent across spec and plan:
  `contacts_input_output_report`, `spinning_box_contacts_input`,
  `write_spinning_box_contacts_input_report`,
  `_run_spinning_box_solver_mabd_contacts_input_step`, and
  `solver_mabd_contacts_input_diagnostic`.
