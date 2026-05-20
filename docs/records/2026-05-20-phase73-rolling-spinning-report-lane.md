# Phase 73 Rolling-Spinning Report Lane

## Status

passed_for_rolling_spinning_report_lane

## Repository

- branch/worktree: `phase68-model-plane-report-lane`
- source commit: `b7969bce4a9cd0d11979c58a4d325aa6eda55ef4`
- vendored Newton commit: `96713fa965463b69c229a4d30582c733ff3526bb`
- Python: `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python`
- paper source version: `2603.08079v2`
- config path: `configs/experiments/single_body_rolling_spinning.yaml`
- matrix path: `configs/experiments/paper_experiment_matrix.yaml`
- report path: `reports/experiment_matrix/single_body_rolling_spinning.json`
- random seed: `not applicable`
- backend: `report_protocol`

## Scope

Phase 73 adds a protocol-only report lane for
`experiment.single_body.rolling_spinning`. The lane records the paper text
timing references for the rolling cylinder figure, keeps the matrix blockers
visible, and makes the previously missing matrix output auditable.

The report status is intentionally incomplete:

- status: `incomplete`
- backend: `report_protocol`
- solver mode: `rolling_spinning_protocol_audit`
- baseline lane: `mabd_newton`
- protocol status: `paper_text_timing_only_no_local_runtime_measurement`
- local_runtime_measured=false
- full_experiment_claim_passed=false

Paper timing references recorded from
`/tmp/mabd-paper/source/sections/singleabd.tex:162-172`:

- rolling cylinder steps: `10000`
- time step: `0.01`
- hardware context: `i7 CPU, single thread`
- vanilla implicit ABD: `161.0 ms`
- implicit RBD: `44.0 ms`
- explicit RBD: `32.0 ms`
- co-rotated ABD with polar decomposition: `34.0 ms`
- co-rotated ABD without polar decomposition: `27.0 ms`

The report records `paper_metric_statuses`:

- `total_simulation_time_ms`: `paper_reference_recorded_no_local_runtime`
- `linear_momentum_error`: `not_measured_by_phase73`
- `angular_momentum_error`: `not_measured_by_phase73`
- `energy_drift`: `not_measured_by_phase73`

Retained blockers:

- `rbd_baseline_adapter_missing`
- `benchmark_protocol_not_recorded`
- `rolling_cylinder_runtime_not_measured`

## Report Artifact

- `reports/experiment_matrix/single_body_rolling_spinning.json`
  - sha256:
    `63eec910b5bf7e451a43ce104131bc3bad5c8734d625a0e2ad913c31fcb676f9`

Result summary:

```json
{"baseline_lane": "mabd_newton", "claim_id": "experiment.single_body.rolling_spinning", "output_report": "reports/experiment_matrix/single_body_rolling_spinning.json", "scene_id": "single_body_rolling_spinning", "status": "incomplete"}
```

`docs/reference/reproduction-gap-audit.yaml` now records the rolling/spinning
matrix output as committed incomplete evidence with the same SHA256 above.
`paper-claims.yaml` is unchanged.

raw artifacts: no videos, run directories, raw logs, or raw paper assets are
committed. The committed artifact is the small JSON report above.

## Commands

TDD red checks:

```bash
PYTHONPATH=src:vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  -m unittest \
  tests.test_experiment_run_configs.ExperimentRunConfigTests.test_rolling_spinning_config_is_machine_checkable \
  tests.test_experiment_run_configs.ExperimentRunConfigTests.test_rolling_spinning_config_matches_matrix

PYTHONPATH=src:vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  -m unittest \
  tests.test_experiment_runner.ExperimentRunnerTests.test_run_rolling_spinning_protocol_writes_configured_report \
  tests.test_experiment_runner.ExperimentRunnerTests.test_run_rolling_spinning_protocol_rejects_ambiguous_output_selection \
  tests.test_experiment_runner.ExperimentRunnerTests.test_run_experiment_cli_runs_rolling_spinning_protocol_lane

PYTHONPATH=src:vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  -m unittest \
  tests.test_phase0_bootstrap.Phase0BootstrapTests.test_phase73_rolling_spinning_report_lane_artifact \
  tests.test_phase0_bootstrap.Phase0BootstrapTests.test_phase73_record_has_required_evidence_fields
```

Observed before implementation: config tests failed because
`load_rolling_spinning_config` was absent; runner tests failed because
`run_rolling_spinning_protocol` and CLI dispatch were absent; bootstrap tests
failed because the Phase 73 boundary and record were absent.

Report generation:

```bash
PYTHONPATH=src:vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  scripts/run_experiment.py \
  --lane rolling_spinning_protocol \
  --config configs/experiments/single_body_rolling_spinning.yaml \
  --matrix configs/experiments/paper_experiment_matrix.yaml \
  --output reports/experiment_matrix/single_body_rolling_spinning.json \
  --source-commit b7969bce4a9cd0d11979c58a4d325aa6eda55ef4 \
  --vendored-newton-commit 96713fa965463b69c229a4d30582c733ff3526bb
```

Focused implementation verification:

```bash
PYTHONPATH=src:vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  -m unittest tests.test_experiment_run_configs tests.test_experiment_runner
```

Observed: `Ran 141 tests in 295.853s`, `OK`.

Repository validation commands:

```bash
PYTHONPATH=src:vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  -m unittest tests.test_experiment_run_configs tests.test_experiment_runner \
  tests.test_phase0_bootstrap

PYTHONPATH=src:vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  scripts/validate_docs.py

PYTHONPATH=src:vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  -m ruff check .

git diff --check
```

Environment isolation commands:

```bash
PYTHONPATH=src:vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  scripts/env/readiness_check.py

PYTHONPATH=src:vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  scripts/env/clone_from_reference.py --dry-run

PYTHONPATH=src:vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  scripts/env/clone_from_reference.py --dry-run --sync-existing

PYTHONPATH=vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  -c "import newton; print(newton.__file__)"
```

Observed statuses:

- readiness: `smoke_passed`
- clone dry-run: `target_exists`
- explicit sync dry-run: `ready_to_sync_existing`, `can_execute=true`
- vendored import:
  `/cpfs/user/zhuzihou/dev/mabd-newton/.worktrees/phase68-model-plane-report-lane/vendor/newton/newton/__init__.py`

Non-pollution fields:

- `mutates_reference_environment=false`
- `uses_reference_python=false`
- `uses_ambient_python=false`

## Claim Boundaries

No `experiment.*` claim is passed.

This record is:

- not a completed rolling/spinning reproduction;
- not a rolling-cylinder dynamics result;
- not a local timing benchmark;
- not implicit or explicit RBD baseline evidence;
- not spinning-box momentum or energy agreement evidence;
- not comparative baseline evidence;
- not rendered-output evidence;
- not full paper reproduction.
