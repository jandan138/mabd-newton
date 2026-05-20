# Phase 78 Rolling Spinning Timing Protocol

## Status

incomplete_timing_protocol_recorded

## Scope

- branch: `phase68-model-plane-report-lane`
- source commit recorded in report:
  `2087017f8cc9104e2ddac600aa7282e301b4f33a`
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

Phase 78 adds a separate fail-closed timing protocol lane:

- config section: `paper_timing_protocol`
- runner: `run_rolling_spinning_paper_timing_protocol`
- CLI lane: `rolling_spinning_paper_timing_protocol`
- report:
  `reports/experiment_matrix/single_body_rolling_spinning_timing_protocol.json`
- report sha256:
  `db8ca921ae393177b7df363fb0cceaa1ce9a84b72c7221f9c27793f676fc5c08`

The report records:

- `solver_mode = rolling_spinning_paper_timing_protocol_audit`
- `backend = report_protocol`
- `baseline_lane = paper_timing_protocol`
- `status = incomplete`
- `timing_protocol_status = paper_timing_protocol_incomplete`
- paper table timings for 10000 steps at `h = 0.01`
- input reports for Phase 73 through Phase 77 rolling/spinning lanes
- `full_experiment_claim_passed = false`
- `paper_comparable = false`
- `blocking_reasons` include
  `paper_comparable_timing_missing`,
  `paper_hardware_mismatch`,
  `paper_single_thread_protocol_not_enforced`,
  `paper_faithful_mabd_collision_missing`,
  `paper_faithful_explicit_rbd_baseline_missing`, and
  `paper_faithful_implicit_rbd_baseline_missing`

## Result Boundary

This phase proves only that the rolling/spinning paper timing table and the
committed local non-comparable lane timings are gathered into one
machine-checkable protocol artifact. It does not prove a paper-comparable timing result. It also does not prove same-hardware paper timing, single-thread runtime
enforcement, paper-faithful affine collision, paper-faithful explicit or
implicit RBD baselines, co-rotated ABD timing, a completed rolling/spinning
reproduction, full paper reproduction, or any passed `experiment.*` claim.

## Commands

- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_runner.ExperimentRunnerTests.test_run_rolling_spinning_paper_timing_protocol_writes_report tests.test_experiment_runner.ExperimentRunnerTests.test_run_experiment_cli_runs_rolling_spinning_paper_timing_protocol_lane`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_run_configs.ExperimentRunConfigTests.test_rolling_spinning_paper_timing_protocol_is_fail_closed tests.test_experiment_run_configs.ExperimentRunConfigTests.test_rolling_spinning_config_matches_matrix tests.test_experiment_run_configs.ExperimentRunConfigTests.test_rolling_spinning_config_is_machine_checkable tests.test_experiment_runner.ExperimentRunnerTests.test_run_rolling_spinning_protocol_writes_configured_report tests.test_experiment_runner.ExperimentRunnerTests.test_run_rolling_spinning_paper_timing_protocol_writes_report tests.test_experiment_runner.ExperimentRunnerTests.test_run_experiment_cli_runs_rolling_spinning_paper_timing_protocol_lane`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check src/mabd_reproduction/experiment_configs.py src/mabd_reproduction/rolling_spinning_reports.py src/mabd_reproduction/experiment_runner.py scripts/run_experiment.py tests/test_experiment_run_configs.py tests/test_experiment_runner.py`
- `git diff --check`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/run_experiment.py --lane rolling_spinning_paper_timing_protocol --config configs/experiments/single_body_rolling_spinning.yaml --matrix configs/experiments/paper_experiment_matrix.yaml --source-commit 2087017f8cc9104e2ddac600aa7282e301b4f33a --vendored-newton-commit 96713fa965463b69c229a4d30582c733ff3526bb`
