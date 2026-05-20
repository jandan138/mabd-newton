# Phase 73 Rolling-Spinning Report Lane Design

## Problem

`experiment.single_body.rolling_spinning` is listed in
`configs/experiments/paper_experiment_matrix.yaml`, but the configured output
report `reports/experiment_matrix/single_body_rolling_spinning.json` is absent.
The reproduction gap audit therefore has a fully missing experiment surface for
the rolling-cylinder performance figure and the related single-body
rolling/spinning entry.

The paper source gives two bounded requirements for this claim:

- `/tmp/mabd-paper/source/sections/singleabd.tex:162-172` reports a rolling
  cylinder performance comparison over 10K steps at `h = 0.01 sec`.
- `/tmp/mabd-paper/source/sections/experiment.tex:48-55` records the
  single-body spinning-box momentum comparison context already covered by the
  separate spinning-box lane.

## Scope

- Add a machine-checkable config for
  `experiment.single_body.rolling_spinning`.
- Add a report writer that emits
  `reports/experiment_matrix/single_body_rolling_spinning.json`.
- Add a `rolling_spinning_protocol` runner lane to `scripts/run_experiment.py`.
- Keep the report status `incomplete`.
- Record the exact paper timing values as expected evidence:
  `vanilla_implicit_abd = 161 ms`, `implicit_rbd = 44 ms`,
  `explicit_rbd = 32 ms`, `corotated_abd_with_polar = 34 ms`,
  `corotated_abd_without_polar = 27 ms`.
- Record the paper timing context `i7 CPU, single thread`.
- Record per-matrix-metric status for `total_simulation_time_ms`,
  `linear_momentum_error`, `angular_momentum_error`, and `energy_drift`, so the
  combined matrix claim cannot be mistaken as covered by a timing-only protocol
  record.
- Record that no local runtime benchmark, RBD baseline adapter, or paper-faithful
  rolling-cylinder Newton simulation has been executed in this phase.
- Keep `experiment.single_body.rolling_spinning` at `intended`.

## Non-Scope

- No runtime-performance pass.
- No implicit RBD or explicit RBD baseline adapter.
- No rolling cylinder dynamics simulation.
- No claim that the spinning-box lane completes the rolling-cylinder timing
  claim.
- No spinning-box momentum or energy agreement for this combined
  rolling/spinning matrix claim.
- No comparative baseline results.
- No passed `experiment.*` claim.
- No full paper reproduction claim.
- No environment refresh or package installation.

## Architecture

The implementation follows the existing config/report/runner pattern:

- `configs/experiments/single_body_rolling_spinning.yaml` stores the paper
  source lines, matrix-matching paper values, missing required lanes, timing
  protocol fields, and report thresholds.
- `src/mabd_reproduction/experiment_configs.py` defines
  `RollingSpinningRunConfig` and validates the config against the matrix entry.
- `src/mabd_reproduction/rolling_spinning_reports.py` writes a `ClaimReport`
  with `solver_mode = rolling_spinning_protocol_audit`,
  `backend = report_protocol`, and `status = incomplete`.
- `src/mabd_reproduction/experiment_runner.py` exposes
  `run_rolling_spinning_protocol`.
- `scripts/run_experiment.py --lane rolling_spinning_protocol` writes the report
  through the same CLI path used by the other experiment lanes.

The report is intentionally a protocol/evidence-surface record, not a solver
result. It reduces the gap from "missing report" to "incomplete, blocked by
specific baseline and benchmark requirements" without relaxing any claim
boundary.

## Report Contract

The JSON report must include:

- `claim_id = experiment.single_body.rolling_spinning`
- `scene_id = single_body_rolling_spinning`
- `asset_hashes` for `primitive_cylinder` and `primitive_cube`, both marked
  `not_applicable_procedural`
- `baseline_lane = mabd_newton`
- `status = incomplete`
- `expected.paper_total_simulation_time_ms` with all five paper timing values
- `expected.paper_hardware_context = i7 CPU, single thread`
- `expected.benchmark_step_count = 10000`
- `expected.time_step_s = 0.01`
- `observed.local_runtime_measured = false`
- `observed.paper_metric_statuses.total_simulation_time_ms =
  paper_reference_recorded_no_local_runtime`
- `observed.paper_metric_statuses.linear_momentum_error =
  not_measured_by_phase73`
- `observed.paper_metric_statuses.angular_momentum_error =
  not_measured_by_phase73`
- `observed.paper_metric_statuses.energy_drift = not_measured_by_phase73`
- `observed.required_lanes_missing` containing
  `rbd_implicit_baseline` and `rbd_explicit_baseline`
- `observed.blocking_reasons` containing
  `rbd_baseline_adapter_missing`, `benchmark_protocol_not_recorded`, and
  `rolling_cylinder_runtime_not_measured`
- `timing_distribution.status = not_measured`
- `timing_distribution.paper_comparable = false`
- top-level `threshold` entries for every matrix metric

## Acceptance Criteria

- `tests.test_experiment_run_configs` loads and validates the new config against
  the matrix.
- `tests.test_experiment_runner` writes and reloads the rolling/spinning
  protocol report through `run_rolling_spinning_protocol`.
- `scripts/run_experiment.py --lane rolling_spinning_protocol` produces the
  committed report path.
- `scripts/run_experiment.py --lane rolling_spinning_protocol` is covered by a
  CLI smoke test so argparse choices and branch placement cannot regress.
- `scripts/validate_docs.py` requires the config, report, Phase 73 record, claim
  boundary text, status `incomplete`, and the non-passing blocker fields.
- `scripts/validate_docs.py` checks the report SHA256, source/vendored commits,
  paper source version, config-vs-matrix validation, five paper timing values,
  per-metric statuses, and `full_experiment_claim_passed = false`.
- `docs/reference/claim-boundaries.md` states that Phase 73 only adds a
  protocol/report lane and does not pass the rolling/spinning experiment.
