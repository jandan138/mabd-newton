# Phase 70 Contacts Input Report Lane

## Status

passed_for_solver_mabd_contacts_input_report_diagnostic

## Repository

- branch/worktree: `phase68-model-plane-report-lane`
- source commit: `493cc1ac9cb0eb11faac89b1540813b3dab4bcd1`
- vendored Newton commit: `96713fa965463b69c229a4d30582c733ff3526bb`
- Python: `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python`
- paper source version: `2603.08079v2`
- config path: `configs/experiments/single_body_spinning_box.yaml`
- random seed: `not applicable`
- backend: `cpu_numpy_newton_solver_mabd_contacts_input_diagnostic`

## Scope

Phase 70 adds a single-body spinning-box report lane that exercises
`SolverMABD.step(..., contacts=...)` through bounded `newton.Contacts` input
rows. It is a diagnostic report lane, not collision detection and not contact
solver evidence.

The lane is configured by
`paper_horizon.contacts_input_output_report` and exposed through
`run_spinning_box_contacts_input` / CLI lane `spinning_box_contacts_input`.
The report writer is `write_spinning_box_contacts_input_report`; its helper is
`_run_spinning_box_solver_mabd_contacts_input_step`.

The helper builds a transient Newton model with one M-ABD body, one box shape,
and one static plane shape, then writes
`newton.Contacts.rigid_contact_static_plane_rows_from_diagnostic_corners` rows
from the existing diagnostic corner/plane penetration check. The report records
`last_contacts_input_summary` when contacts are provided and
`contacts_none_no_active_diagnostic_contacts` for the no-active-contact branch.

## Report Artifact

- report path:
  `reports/experiment_matrix/single_body_spinning_box_contacts_input.json`
- report sha256:
  `a9076b8df0eff7d5f98b042f9a6d6d293ae772181b41ed0f23c80a3627e5160d`
- solver mode: `solver_mabd_contacts_input_diagnostic`
- contacts input policy:
  `solver_mabd_contacts_input_free_predict_then_static_plane_constraints`
- contacts input source:
  `newton.Contacts.rigid_contact_static_plane_rows_from_diagnostic_corners`
- contacts input scope:
  `diagnostic_only_static_geometry_plane_constraints_no_lane_gate`
- contacts_input_summary_source = last_contacts_input_summary
- max_contacts_input_rigid_contact_count = 4
- max_contacts_input_rows_read = 4
- max_contacts_input_generated_plane_constraint_count = 4
- max_contacts_input_skipped_contact_count = 0
- max_contacts_input_overflow_count = 0
- status: `incomplete`

Recorded blockers include:

- `mabd_newton_report_incomplete`
- `mabd_paper_horizon_diagnostic_thresholds_violated`
- `spinning_box_contacts_input_not_paper_faithful`
- `collision_detection_not_enabled_for_contacts_input`
- `spinning_box_comparison_pass_gate_not_enabled`
- `mabd_kinematic_feasibility_blocker_recorded`

raw artifacts: no videos, run directories, or large logs are committed. The
committed artifact is the small JSON report above.

## Commands

```bash
PYTHONPATH=src:vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  scripts/run_experiment.py \
  --lane spinning_box_contacts_input \
  --config configs/experiments/single_body_spinning_box.yaml \
  --matrix configs/experiments/paper_experiment_matrix.yaml \
  --output reports/experiment_matrix/single_body_spinning_box_contacts_input.json \
  --source-commit 493cc1ac9cb0eb11faac89b1540813b3dab4bcd1 \
  --vendored-newton-commit 96713fa965463b69c229a4d30582c733ff3526bb
```

Result summary:

```json
{"baseline_lane": "mabd_newton", "claim_id": "experiment.single_body.spinning_box", "output_report": "reports/experiment_matrix/single_body_spinning_box_contacts_input.json", "scene_id": "single_body_spinning_box", "status": "incomplete"}
```

Focused verification:

```bash
PYTHONPATH=src:vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  -m unittest \
  tests.test_experiment_run_configs.ExperimentRunConfigTests.test_spinning_box_config_is_machine_checkable \
  tests.test_experiment_run_configs.ExperimentRunConfigTests.test_spinning_box_contacts_input_report_path_must_be_lane_specific

PYTHONPATH=src:vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  -m unittest \
  tests.test_single_body_report_lane.SingleBodyReportLaneTests.test_solver_mabd_contacts_input_step_records_static_plane_summary \
  tests.test_single_body_report_lane.SingleBodyReportLaneTests.test_solver_mabd_contacts_input_step_records_contacts_none_when_no_active_rows \
  tests.test_single_body_report_lane.SingleBodyReportLaneTests.test_spinning_box_contacts_input_report_records_newton_contacts_lane

PYTHONPATH=src:vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  -m unittest \
  tests.test_experiment_runner.ExperimentRunnerTests.test_run_spinning_box_contacts_input_writes_explicit_output_report \
  tests.test_experiment_runner.ExperimentRunnerTests.test_run_spinning_box_contacts_input_requires_explicit_output \
  tests.test_experiment_runner.ExperimentRunnerTests.test_run_experiment_cli_writes_spinning_box_contacts_input_report \
  tests.test_experiment_runner.ExperimentRunnerTests.test_run_experiment_cli_rejects_contacts_input_output_root

PYTHONPATH=src:vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  -m unittest \
  tests.test_spinning_box_report_artifacts.SpinningBoxReportArtifactTests.test_contacts_input_report_records_newton_contacts_lane_only \
  tests.test_phase0_bootstrap.Phase0BootstrapTests.test_phase70_contacts_input_report_lane_is_bounded
```

Repository validation commands:

```bash
PYTHONPATH=src:vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  scripts/validate_docs.py

PYTHONPATH=src:vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  -m unittest discover -s tests

PYTHONPATH=src:vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  -m ruff check .

PYTHONPATH=src:vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  scripts/env/readiness_check.py

PYTHONPATH=vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  -c "import newton; print(newton.__file__)"

git diff --check
```

Environment clone dry-run:

```bash
PYTHONPATH=src:vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  scripts/env/clone_from_reference.py --dry-run
```

Observed statuses:

- clone dry-run: `target_exists`
- readiness check: `smoke_passed`
- non-pollution fields:
  `mutates_reference_environment=false`, `uses_reference_python=false`,
  `uses_ambient_python=false`

## Claim Boundaries

No `experiment.*` claim is passed.

`paper-claims.yaml` is unchanged.

This record is:

- not collision detection;
- not contact solver evidence;
- not generic inequality-constrained M-ABD KKT evidence;
- not paper-faithful affine collision/contact;
- not paper-faithful M-ABD stepping;
- not rendered-output agreement;
- not runtime performance evidence;
- not full paper reproduction.
