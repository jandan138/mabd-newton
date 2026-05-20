# Phase 77 Rolling Cylinder Material Preflight

## Status

incomplete_material_preflight_recorded

## Scope

- branch: `phase68-model-plane-report-lane`
- source commit recorded in report:
  `825eba871eec65b37429cbc2222f170d5636160b`
- vendored Newton upstream commit:
  `96713fa965463b69c229a4d30582c733ff3526bb`
- paper source version: `2603.08079v2`
- Python:
  `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python`
- reference environment:
  `/cpfs/user/zhuzihou/conda-managed/envs/physics-primitive-newton-py310`
- target environment:
  `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310`
- non-pollution:
  `mutates_reference_environment=false`, `uses_reference_python=false`,
  `uses_ambient_python=false`

## Evidence

Phase 77 adds a separate fail-closed material preflight lane:

- config section: `mabd_material_preflight`
- runner: `run_rolling_spinning_mabd_material_preflight`
- CLI lane: `rolling_spinning_mabd_material_preflight`
- report:
  `reports/experiment_matrix/single_body_rolling_spinning_mabd_material_preflight.json`
- report sha256:
  `7bc5cba071e17a52f890ca2e808c6c6e45d3e219d481a7a544dbd6ab6c5e5a3a`

The report records:

- `solver_mode = mabd_cpu_oracle_rolling_cylinder_material_preflight`
- `backend = cpu_numpy_newton_solver_mabd_static_plane_contacts`
- `baseline_lane = mabd_newton`
- `status = incomplete`
- `young_modulus_pa = 1000000000.0`
- `poisson_ratio = 0.3`
- `zero_stiffness_diagnostic = false`
- `material_preflight_status = finite_stiffness_preflight_incomplete`
- `full_experiment_claim_passed = false`
- `paper_comparable = false`
- `blocking_reasons` include
  `mabd_material_preflight_incomplete`,
  `paper_faithful_mabd_collision_missing`,
  `paper_faithful_explicit_rbd_baseline_missing`,
  `paper_faithful_implicit_rbd_baseline_missing`, and
  `paper_comparable_timing_missing`

## Result Boundary

This phase proves only that the rolling-cylinder M-ABD Newton lane can be
configured and run with finite material stiffness values sourced from the paper
text. It does not prove paper-faithful affine collision, rolling friction,
explicit or implicit RBD baselines, co-rotated ABD timing, same-hardware paper
timing, paper-comparable performance, a completed rolling/spinning
reproduction, full paper reproduction, or any passed `experiment.*` claim.

## Commands

- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_run_configs.ExperimentRunConfigTests.test_rolling_spinning_config_is_machine_checkable tests.test_experiment_run_configs.ExperimentRunConfigTests.test_rolling_spinning_config_matches_matrix tests.test_experiment_run_configs.ExperimentRunConfigTests.test_rolling_spinning_mabd_material_preflight_is_fail_closed`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_runner.ExperimentRunnerTests.test_run_rolling_spinning_mabd_material_preflight_writes_report tests.test_experiment_runner.ExperimentRunnerTests.test_run_experiment_cli_runs_rolling_spinning_mabd_material_preflight_lane`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check scripts/run_experiment.py src/mabd_reproduction/experiment_configs.py src/mabd_reproduction/experiment_runner.py src/mabd_reproduction/rolling_spinning_reports.py tests/test_experiment_run_configs.py tests/test_experiment_runner.py`
- `git diff --check`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/run_experiment.py --lane rolling_spinning_mabd_material_preflight --config configs/experiments/single_body_rolling_spinning.yaml --matrix configs/experiments/paper_experiment_matrix.yaml --source-commit 825eba871eec65b37429cbc2222f170d5636160b --vendored-newton-commit 96713fa965463b69c229a4d30582c733ff3526bb`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_phase0_bootstrap.Phase0BootstrapTests.test_phase77_validator_requires_explicit_material_preflight_fields tests.test_phase0_bootstrap.Phase0BootstrapTests.test_phase77_validator_recomputes_threshold_violations`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/env/readiness_check.py`
- `PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests`
