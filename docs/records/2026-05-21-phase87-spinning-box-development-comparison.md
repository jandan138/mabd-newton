# Phase 87 Spinning-Box Development Comparison

## Status

incomplete_development_comparison_recorded

## Environment

- canonical python:
  `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python`
- source commit: `ce0c5bd`
- vendored Newton commit:
  `96713fa965463b69c229a4d30582c733ff3526bb`
- mutates_reference_environment=false
- uses_reference_python=false
- uses_ambient_python=false

## Evidence

Phase 87 records a development-only internal comparison for
`experiment.single_body.spinning_box`.

- lane: `spinning_box_development_comparison`
- output:
  `reports/experiment_matrix/single_body_spinning_box_development_comparison.json`
- report SHA256:
  `37d5dec0c0dbecf66c538ed0662cb19741af9cc22dea8f90ea7ecbdc749cca22`
- backend: `cpu_newton_warp`
- baseline lane: `spinning_box_development_comparison`
- solver mode: `spinning_box_newton_mabd_rbd_development_comparison`
- status = incomplete
- comparison_scope = development_only
- comparison_status = development_comparison_recorded
- paper_faithful = false
- full_experiment_claim_passed = false
- duration_s = 10.0
- time_step_s = 0.01
- step_count = 1000
- sample_count = 101
- M-ABD solver: `newton.solvers.SolverMABD`
- RBD solver: `newton.solvers.SolverSemiImplicit`
- trajectory = embedded compact samples
- energy_curve = embedded energy curve samples
- timing_distribution.scope = local_cpu_wall_clock_not_paper_comparable
- timing_distribution.paper_comparable = false

The comparison metrics recorded by the report include:

- `final_position_delta_m = 2.9598184619306317e-16`
- `max_position_delta_m = 1.0178080243105681e-15`
- `final_energy_delta_j = 0.07684916188036828`
- `max_energy_delta_j = 0.07687721962834809`
- `final_linear_momentum_delta_norm = 5.117682011268654e-16`
- `max_linear_momentum_delta_norm = 6.007268835001826e-16`
- `final_angular_momentum_delta_norm = 5.72693793099259e-07`
- `max_angular_momentum_delta_norm = 5.72693793099259e-07`

## Claim Boundary

This record is a development comparison only. It does not prove a
paper-faithful M-ABD spinning-box lane, does not prove a paper-faithful RBD
baseline, does not enable a comparison pass gate, and does not pass
`experiment.single_body.spinning_box`.

No experiment.* claim is passed. No `experiment.*` claim is passed by this
phase.

The committed report remains incomplete because it uses reasonable local
defaults, embeds compact samples rather than paper assets, and deliberately
sets `paper_faithful = false`.

## Verification

RED tests failed before implementation because
`development_comparison`, `run_spinning_box_development_comparison`, and CLI
lane `spinning_box_development_comparison` were absent.

GREEN Phase87 contract tests:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_run_configs.ExperimentRunConfigTests.test_spinning_box_config_is_machine_checkable tests.test_experiment_run_configs.ExperimentRunConfigTests.test_spinning_box_development_comparison_config_is_development_only tests.test_experiment_runner.ExperimentRunnerTests.test_run_spinning_box_development_comparison_writes_report tests.test_experiment_runner.ExperimentRunnerTests.test_run_experiment_cli_writes_spinning_box_development_comparison_report tests.test_spinning_box_report_artifacts.SpinningBoxReportArtifactTests.test_development_comparison_report_records_10s_newton_mabd_rbd_internal_comparison tests.test_phase0_bootstrap.Phase0BootstrapTests.test_phase87_spinning_box_development_comparison_artifact tests.test_phase0_bootstrap.Phase0BootstrapTests.test_docs_validator_accepts_phase0_contract
```

Result:

```text
Ran 7 tests in 60.988s

OK
```

Docs and provenance validation:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
```

Result:

```text
Phase 0/1/2/3/4/5/6/7/8/9/10/11/12/13/14/15/16/17/18/19/20/21/22/23/24/25/26/27/28/29/30/31/32/33/34/35/36/37/38/39/40/41/42/43/44/45/46/47/48/49/50/51/52/53/54/55/56/57/58/59/60/61/62/63/64/65/66/67/68/69/70/71/72/73/74/75/76/77/78/79/80/81/82/83/84/85/86/87 docs/provenance validation passed
```

Full unit test suite:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
```

Result:

```text
Ran 664 tests in 668.767s

OK
```

Whitespace and vendored Newton import checks:

```bash
git diff --check
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"
```

The import resolved to:

```text
/cpfs/user/zhuzihou/dev/mabd-newton/.worktrees/phase87-spinning-box-dev-comparison/vendor/newton/newton/__init__.py
```
