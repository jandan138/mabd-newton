# Phase 81 MABD Rolling Contact Candidate

## Status

incomplete_mabd_rolling_contact_candidate_recorded

## Scope

Phase 81 records a fail-closed Newton `SolverMABD` world-constraint contact
candidate for `experiment.single_body.rolling_spinning`.

This lane is a Newton-local M-ABD diagnostic for the configured rolling cylinder:

- lane: `rolling_spinning_mabd_rolling_contact_candidate`
- report:
  `reports/experiment_matrix/single_body_rolling_spinning_mabd_rolling_contact_candidate.json`
- report sha256:
  `bfe53115cf544e66510305653adb098655b8fd24b45b78ffee5088303031b448`
- source commit: `03733a3`
- vendored Newton commit: `96713fa965463b69c229a4d30582c733ff3526bb`
- paper source version: `2603.08079v2`
- Python: `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python`
- backend: `cpu_newton_mabd_world_constraints`
- solver mode: `newton_mabd_rolling_contact_world_constraint_candidate`
- status = incomplete
- contact_constraint_mode = world
- contacts_input_summary_source = last_contacts_input_summary
- local_runtime_measured = true
- paper_comparable = false
- full_experiment_claim_passed = false

The generated report records 10000 local M-ABD steps at `h = 0.01`, finite
material parameters `young_modulus_pa = 1.0e9` and `poisson_ratio = 0.3`,
`zero_stiffness_diagnostic = false`,
`generated_world_constraint_count_summary.max = 1`, and
`generated_plane_constraint_count_summary.max = 0`.

The report intentionally records local wall-clock timing only as local evidence.
It is not paper-comparable timing and is not compared against the paper's
rolling-cylinder timing table.

## Blocking Reasons

The report intentionally keeps these blockers:

- `mabd_rolling_contact_candidate_not_paper_faithful`
- `diagnostic_world_constraints_not_paper_friction_law`
- `paper_affine_rolling_contact_details_missing`
- `paper_faithful_explicit_rbd_baseline_missing`
- `paper_faithful_implicit_rbd_baseline_missing`
- `paper_comparable_timing_missing`

It preserves the living gap-audit vocabulary:

- `paper_faithful_explicit_rbd_baseline`
- `paper_faithful_implicit_rbd_baseline`
- `paper_faithful_mabd_rolling_cylinder`
- `paper_comparable_timing`

This phase does not prove paper-faithful affine rolling contact/friction,
paper-faithful explicit RBD, paper-faithful implicit RBD, paper-comparable
timing, or any passed `experiment.*` claim.

No `experiment.*` claim is passed; there is no evidence for any passed
`experiment.*` claim.

## Environment Isolation

- mutates_reference_environment=false
- uses_reference_python=false
- uses_ambient_python=false
- canonical environment:
  `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310`
- reference environment:
  `/cpfs/user/zhuzihou/conda-managed/envs/physics-primitive-newton-py310`

## Commands

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_run_configs.ExperimentRunConfigTests.test_rolling_spinning_mabd_rolling_contact_candidate_is_fail_closed
```

Initial result: failed with
`AttributeError: 'RollingSpinningRunConfig' object has no attribute 'mabd_rolling_contact_candidate'`.

Final result: covered in the targeted config bundle below.

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_run_configs.ExperimentRunConfigTests.test_rolling_spinning_mabd_rolling_contact_candidate_is_fail_closed tests.test_experiment_run_configs.ExperimentRunConfigTests.test_rolling_spinning_config_is_machine_checkable tests.test_experiment_run_configs.ExperimentRunConfigTests.test_rolling_spinning_config_matches_matrix
```

Result: `Ran 3 tests in 0.119s OK`.

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_runner.ExperimentRunnerTests.test_run_rolling_spinning_mabd_rolling_contact_candidate_writes_report tests.test_experiment_runner.ExperimentRunnerTests.test_run_experiment_cli_runs_rolling_spinning_mabd_rolling_contact_candidate_lane
```

Initial result: failed because
`run_rolling_spinning_mabd_rolling_contact_candidate` and CLI choice
`rolling_spinning_mabd_rolling_contact_candidate` did not exist.

Final result: `Ran 2 tests in 9.646s OK`.

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/run_experiment.py --lane rolling_spinning_mabd_rolling_contact_candidate --config configs/experiments/single_body_rolling_spinning.yaml --matrix configs/experiments/paper_experiment_matrix.yaml --source-commit 03733a3 --vendored-newton-commit 96713fa965463b69c229a4d30582c733ff3526bb
```

Result:

```json
{"baseline_lane": "mabd_rolling_contact_candidate", "claim_id": "experiment.single_body.rolling_spinning", "output_report": "reports/experiment_matrix/single_body_rolling_spinning_mabd_rolling_contact_candidate.json", "scene_id": "single_body_rolling_spinning", "status": "incomplete"}
```

```bash
sha256sum reports/experiment_matrix/single_body_rolling_spinning_mabd_rolling_contact_candidate.json
```

Result:

```text
bfe53115cf544e66510305653adb098655b8fd24b45b78ffee5088303031b448  reports/experiment_matrix/single_body_rolling_spinning_mabd_rolling_contact_candidate.json
```

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
```

Result:
`Phase 0/1/2/3/4/5/6/7/8/9/10/11/12/13/14/15/16/17/18/19/20/21/22/23/24/25/26/27/28/29/30/31/32/33/34/35/36/37/38/39/40/41/42/43/44/45/46/47/48/49/50/51/52/53/54/55/56/57/58/59/60/61/62/63/64/65/66/67/68/69/70/71/72/73/74/75/76/77/78/79/80/81 docs/provenance validation passed`.

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
```

Result: `Ran 630 tests in 638.932s OK`.

```bash
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"
```

Result:
`/cpfs/user/zhuzihou/dev/mabd-newton/.worktrees/phase81-mabd-rolling-contact-candidate/vendor/newton/newton/__init__.py`.

```bash
git diff --check
```

Result: passed with no output.
