# Phase 89 Spinning-Box Unilateral Contact Gate Candidate

## Status

incomplete_unilateral_contact_collision_gate_candidate_recorded

No experiment.* claim is passed.
No `experiment.*` claim is passed.

## Environment

- source_commit = 2b9d6e6
- vendored_newton_commit = 96713fa965463b69c229a4d30582c733ff3526bb
- python = /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python
- mutates_reference_environment=false
- uses_reference_python=false
- uses_ambient_python=false

## Evidence

Phase 89 records a development-only unilateral static-plane contact/collision
gate candidate for the single-body spinning box. This is still fail-closed and
is not a paper-faithful affine collision solver.

- lane: `spinning_box_contact_collision_gate_candidate`
- report:
  `reports/experiment_matrix/single_body_spinning_box_contact_collision_gate_candidate.json`
- report_sha256:
  `14b44280dcb8abcd6c33271d6a9ecb844197dccb23983ae5501e824e2f85b8ff`
- phase88_rollout_candidate_sha256 = 04b6057cfc02df5c690785645d3e3ee95821153796931a4c39ce3c434a29c4a2
- backend: `cpu_newton_solver_mabd_unilateral_static_plane_contact_gate_candidate`
- solver mode: `solver_mabd_unilateral_static_plane_contact_gate_candidate`
- status = incomplete
- gate_scope = single_body_spinning_box_contact_collision_candidate
- candidate_status = contact_collision_gate_candidate_recorded
- contact_constraint_mode = unilateral_plane
- unilateral_contact_policy = dense_cpu_active_set_drop_tensile_plane_rows
- paper_faithful = false
- paper_comparable = false
- full_experiment_claim_passed = false
- comparison_pass_gate_enabled = false
- duration_s = 10.0
- time_step_s = 0.01
- step_count = 1000
- sample_count = 101
- max_unilateral_plane_requested_count = 4
- max_unilateral_plane_accepted_count = 3
- max_unilateral_plane_rejected_count = 0
- max_unilateral_plane_skipped_count = 1
- threshold_violations = [`max_relative_total_energy_drift`]

## Boundaries

This evidence verifies only that Newton `SolverMABD` has an opt-in
`unilateral_plane` diagnostic path for affine box vs static infinite-plane
contacts and that the spinning-box candidate records it.

It does not verify paper-faithful affine contact/collision, finite-plane
clipping, body-body affine contact, generic contact solving, friction,
restitution, CCD, paper-faithful M-ABD dynamics, RBD baselines, comparison pass
gates, paper-comparable timing, or full reproduction.

## Commands

```text
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_mabd_phase4_solver_step tests.test_experiment_run_configs.ExperimentRunConfigTests.test_spinning_box_config_is_machine_checkable tests.test_experiment_run_configs.ExperimentRunConfigTests.test_spinning_box_affine_static_plane_contacts_rollout_candidate_config_is_development_only tests.test_experiment_run_configs.ExperimentRunConfigTests.test_spinning_box_contact_collision_gate_candidate_config_is_fail_closed tests.test_experiment_runner.ExperimentRunnerTests.test_run_spinning_box_affine_static_plane_contacts_rollout_candidate_writes_report tests.test_experiment_runner.ExperimentRunnerTests.test_run_spinning_box_contact_collision_gate_candidate_writes_report tests.test_experiment_runner.ExperimentRunnerTests.test_run_experiment_cli_writes_spinning_box_affine_static_plane_contacts_rollout_candidate_report tests.test_experiment_runner.ExperimentRunnerTests.test_run_experiment_cli_writes_spinning_box_contact_collision_gate_candidate_report
```

Result:

```text
Ran 79 tests in 11.520s
OK
```

```text
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/run_experiment.py --lane spinning_box_contact_collision_gate_candidate --config configs/experiments/single_body_spinning_box.yaml --matrix configs/experiments/paper_experiment_matrix.yaml --source-commit 2b9d6e6 --vendored-newton-commit 96713fa965463b69c229a4d30582c733ff3526bb
```

Result:

```json
{"baseline_lane": "spinning_box_contact_collision_gate_candidate", "claim_id": "experiment.single_body.spinning_box", "output_report": "reports/experiment_matrix/single_body_spinning_box_contact_collision_gate_candidate.json", "scene_id": "single_body_spinning_box", "status": "incomplete"}
```
