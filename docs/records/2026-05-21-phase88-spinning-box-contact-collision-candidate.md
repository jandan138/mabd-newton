# Phase 88 Spinning-Box Affine Static-Plane Contacts Rollout Candidate

## Status

incomplete_affine_static_plane_contacts_rollout_candidate_recorded

## Environment

- canonical python:
  `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python`
- source commit: `e96ff6d726019a3b974d54dbad2fe82c0698d6d0`
- vendored Newton commit:
  `96713fa965463b69c229a4d30582c733ff3526bb`
- mutates_reference_environment=false
- uses_reference_python=false
- uses_ambient_python=false

## Evidence

Phase 88 records a development-only affine static-plane contacts rollout
candidate for `experiment.single_body.spinning_box`.

- lane: `spinning_box_affine_static_plane_contacts_rollout_candidate`
- output:
  `reports/experiment_matrix/single_body_spinning_box_affine_static_plane_contacts_rollout_candidate.json`
- report SHA256:
  `04b6057cfc02df5c690785645d3e3ee95821153796931a4c39ce3c434a29c4a2`
- backend: `cpu_newton_solver_mabd_affine_static_plane_contacts_rollout_candidate`
- solver mode: `solver_mabd_affine_static_plane_contacts_rollout_candidate`
- status = incomplete
- rollout_scope = development_only
- candidate_status = affine_static_plane_contacts_rollout_candidate_recorded
- paper_faithful = false
- paper_comparable = false
- full_experiment_claim_passed = false
- contact_constraint_policy =
  free_predict_detect_static_plane_contacts_then_constrained_step
- contact_detection_source = `SolverMABD.detect_static_plane_contacts`
- solver_step_api = `SolverMABD.step(..., contacts=...)`
- newton_contacts_api = `newton.Contacts`
- contacts_input_summary_source = `last_contacts_input_summary`
- static_plane_collision_summary_source = `last_static_plane_collision_summary`
- contact_constraint_mode = plane
- duration_s = 10.0
- time_step_s = 0.01
- step_count = 1000
- sample_count = 101
- max_free_predicted_contact_penetration_m = 0.000999997556209567
- max_constrained_contact_penetration_m = 1.490116135094592e-09
- max_affine_static_plane_candidate_contact_count = 4
- max_contacts_input_generated_plane_constraint_count = 4
- max_constraint_residual_norm = 8.735868072852438e-20
- relative_total_energy_drift = 2.5358934683284238
- threshold_violations = [`max_relative_total_energy_drift`]
- trajectory = embedded compact samples
- timing_distribution.scope = local_cpu_wall_clock_not_paper_comparable
- timing_distribution.paper_comparable = false

## Claim Boundary

This record is a development-only rollout candidate. It does not prove
paper-faithful affine contact/collision, does not prove a contact solver, does
not prove finite-plane clipping, does not prove body-body affine collision, does
not prove complementarity, barriers, CCD, or friction, does not enable a
comparison pass gate, and does not pass
`experiment.single_body.spinning_box`.

No experiment.* claim is passed. No `experiment.*` claim is passed by this
phase.

The committed report remains incomplete because it is a static infinite-plane
candidate path, records a total-energy threshold violation, and deliberately
sets `paper_faithful = false`.

## Verification

RED tests failed before implementation because the config dataclass field,
runner, YAML section, and CLI lane were absent.

GREEN Phase88 contract tests:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_run_configs.ExperimentRunConfigTests.test_spinning_box_config_is_machine_checkable tests.test_experiment_run_configs.ExperimentRunConfigTests.test_spinning_box_affine_static_plane_contacts_rollout_candidate_config_is_development_only tests.test_experiment_runner.ExperimentRunnerTests.test_run_spinning_box_affine_static_plane_contacts_rollout_candidate_writes_report tests.test_experiment_runner.ExperimentRunnerTests.test_run_experiment_cli_writes_spinning_box_affine_static_plane_contacts_rollout_candidate_report
```

Result:

```text
Ran 4 tests in 8.849s

OK
```

Report generation:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/run_experiment.py --lane spinning_box_affine_static_plane_contacts_rollout_candidate --config configs/experiments/single_body_spinning_box.yaml --matrix configs/experiments/paper_experiment_matrix.yaml --source-commit e96ff6d726019a3b974d54dbad2fe82c0698d6d0 --vendored-newton-commit 96713fa965463b69c229a4d30582c733ff3526bb
```

Result:

```json
{"baseline_lane": "spinning_box_affine_static_plane_contacts_rollout_candidate", "claim_id": "experiment.single_body.spinning_box", "output_report": "reports/experiment_matrix/single_body_spinning_box_affine_static_plane_contacts_rollout_candidate.json", "scene_id": "single_body_spinning_box", "status": "incomplete"}
```

Artifact/docs tests after report generation:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_spinning_box_report_artifacts.SpinningBoxReportArtifactTests.test_affine_static_plane_contacts_rollout_candidate_report_records_10s_persistent_contacts tests.test_phase0_bootstrap.Phase0BootstrapTests.test_phase88_spinning_box_affine_static_plane_contacts_rollout_candidate_artifact
```

Result:

```text
Ran 2 tests in 3.245s

OK
```

Final targeted verification:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_run_configs.ExperimentRunConfigTests.test_spinning_box_config_is_machine_checkable tests.test_experiment_run_configs.ExperimentRunConfigTests.test_spinning_box_affine_static_plane_contacts_rollout_candidate_config_is_development_only tests.test_experiment_runner.ExperimentRunnerTests.test_run_spinning_box_affine_static_plane_contacts_rollout_candidate_writes_report tests.test_experiment_runner.ExperimentRunnerTests.test_run_experiment_cli_writes_spinning_box_affine_static_plane_contacts_rollout_candidate_report tests.test_spinning_box_report_artifacts.SpinningBoxReportArtifactTests.test_affine_static_plane_contacts_rollout_candidate_report_records_10s_persistent_contacts tests.test_phase0_bootstrap.Phase0BootstrapTests.test_phase88_spinning_box_affine_static_plane_contacts_rollout_candidate_artifact tests.test_phase0_bootstrap.Phase0BootstrapTests.test_docs_validator_accepts_phase0_contract
```

Result:

```text
Ran 7 tests in 57.482s

OK
```

Full regression verification:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
```

Result:

```text
Ran 669 tests in 673.753s

OK
```

Docs/provenance validation:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
```

Result:

```text
Phase 0/1/2/3/4/5/6/7/8/9/10/11/12/13/14/15/16/17/18/19/20/21/22/23/24/25/26/27/28/29/30/31/32/33/34/35/36/37/38/39/40/41/42/43/44/45/46/47/48/49/50/51/52/53/54/55/56/57/58/59/60/61/62/63/64/65/66/67/68/69/70/71/72/73/74/75/76/77/78/79/80/81/82/83/84/85/86/87/88 docs/provenance validation passed
```

Vendored Newton import check:

```bash
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"
```

Result:

```text
/cpfs/user/zhuzihou/dev/mabd-newton/.worktrees/phase88-spinning-box-contact-collision/vendor/newton/newton/__init__.py
```

Whitespace check:

```bash
git diff --check
```

Result: no output, exit 0.
