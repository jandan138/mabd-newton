# Phase 85 Rolling MABD Source Gate

## Status

incomplete_mabd_source_gate_recorded

## Environment

- canonical python:
  `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python`
- source commit: `fadd6ad`
- vendored Newton commit:
  `96713fa965463b69c229a4d30582c733ff3526bb`
- mutates_reference_environment=false
- uses_reference_python=false
- uses_ambient_python=false

## Evidence

Phase 85 adds a fail-closed source-audit report lane for the
`paper_faithful_mabd_rolling_cylinder` gate of
`experiment.single_body.rolling_spinning`.

- lane: `rolling_spinning_mabd_source_gate`
- output:
  `reports/experiment_matrix/single_body_rolling_spinning_mabd_source_gate.json`
- report SHA256:
  `36b468396aa8a768fc66006cbf2a190ceef1e9dcc807c4bd7b8e317a2d7deb4f`
- backend: `paper_source_audit`
- baseline lane: `mabd_source_gate`
- solver mode: `rolling_spinning_mabd_source_gate`
- status = incomplete
- source_audit_status = mabd_source_requirements_incomplete
- paper_faithful_gate_passed = false
- paper_comparable = false
- full_experiment_claim_passed = false
- timing_distribution.status = not_measured
- timing_distribution.scope = source_gate_no_runtime

The missing required source parameters are:

- `rolling_cylinder_geometry`
- `rolling_cylinder_mass_or_density`
- `rolling_cylinder_initial_state`
- `mabd_affine_body_discretization`
- `mabd_rolling_contact_friction_model`
- `mabd_collision_parameters`

The blocking reasons include:

- `rolling_cylinder_geometry_parameters_missing_from_public_source`
- `rolling_cylinder_initial_state_missing_from_public_source`
- `paper_mabd_affine_discretization_missing_from_public_source`
- `paper_mabd_rolling_contact_friction_missing_from_public_source`
- `paper_mabd_collision_parameters_missing_from_public_source`
- `paper_faithful_mabd_collision_missing`
- `paper_faithful_explicit_rbd_baseline_missing`
- `paper_faithful_implicit_rbd_baseline_missing`
- `paper_comparable_timing_missing`

## Claim Boundary

This record does not prove paper-faithful M-ABD rolling-cylinder behavior. It
only records that the public paper source does not provide enough
rolling-cylinder M-ABD affine body, contact, friction, and collision setup
details to pass the M-ABD source gate.

No experiment.* claim is passed. No `experiment.*` claim is passed by this
phase.

The remaining rolling/spinning reproduction gaps are still:

- `paper_faithful_explicit_rbd_baseline`
- `paper_faithful_implicit_rbd_baseline`
- `paper_faithful_mabd_rolling_cylinder`
- `paper_comparable_timing`

## Verification

RED tests failed before implementation because
`rolling_spinning_mabd_source_audit`, `mabd_source_gate`,
`run_rolling_spinning_mabd_source_gate`, and the CLI lane were absent.

GREEN targeted tests:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_paper_source_audit.PaperSourceAuditTests.test_rolling_spinning_mabd_source_audit_is_fail_closed tests.test_paper_source_audit.PaperSourceAuditTests.test_rolling_spinning_mabd_source_disclosure_triggers_manual_review tests.test_experiment_run_configs.ExperimentRunConfigTests.test_rolling_spinning_mabd_source_gate_is_fail_closed tests.test_experiment_runner.ExperimentRunnerTests.test_run_rolling_spinning_mabd_source_gate_writes_report tests.test_experiment_runner.ExperimentRunnerTests.test_run_experiment_cli_runs_rolling_spinning_mabd_source_gate_lane
```

Result:

```text
Ran 5 tests in 8.811s

OK
```

GREEN Phase85 contract tests:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_paper_source_audit.PaperSourceAuditTests.test_rolling_spinning_mabd_source_audit_is_fail_closed tests.test_paper_source_audit.PaperSourceAuditTests.test_rolling_spinning_mabd_source_disclosure_triggers_manual_review tests.test_experiment_run_configs.ExperimentRunConfigTests.test_rolling_spinning_mabd_source_gate_is_fail_closed tests.test_experiment_runner.ExperimentRunnerTests.test_run_rolling_spinning_mabd_source_gate_writes_report tests.test_experiment_runner.ExperimentRunnerTests.test_run_experiment_cli_runs_rolling_spinning_mabd_source_gate_lane tests.test_phase0_bootstrap.Phase0BootstrapTests.test_phase85_rolling_mabd_source_gate_artifact tests.test_phase0_bootstrap.Phase0BootstrapTests.test_docs_validator_accepts_phase0_contract
```

Result:

```text
Ran 7 tests in 55.893s

OK
```

Docs and provenance validation:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
```

Result:

```text
Phase 0/1/2/3/4/5/6/7/8/9/10/11/12/13/14/15/16/17/18/19/20/21/22/23/24/25/26/27/28/29/30/31/32/33/34/35/36/37/38/39/40/41/42/43/44/45/46/47/48/49/50/51/52/53/54/55/56/57/58/59/60/61/62/63/64/65/66/67/68/69/70/71/72/73/74/75/76/77/78/79/80/81/82/83/84/85 docs/provenance validation passed
```

Full unit test suite:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
```

Result:

```text
Ran 653 tests in 646.678s

OK
```

Whitespace and vendored Newton import checks:

```bash
git diff --check
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"
```

The import resolved to:

```text
/cpfs/user/zhuzihou/dev/mabd-newton/.worktrees/phase83-rolling-explicit-rbd-source-gate/vendor/newton/newton/__init__.py
```
