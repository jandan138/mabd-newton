# Phase 36 Physical Pendulum Comparison Protocol Design

## Objective

Add a bounded, machine-checkable comparison protocol for
`experiment.single_body.physical_pendulum`.

The protocol combines the current analytic reference, Phase 34 M-ABD
development diagnostic, and Phase 35 scalar implicit RBD diagnostic into one
summary report. It records what can be compared now, records which paper metrics
remain unavailable, and keeps the paper experiment incomplete.

## Current Evidence Gap

The current `main` state has:

- an analytic reference runner and output contract, but no committed analytic
  reference JSON artifact
- a committed M-ABD development diagnostic JSON report
- a committed RBD implicit baseline diagnostic JSON report
- no single report that compares the physical-pendulum lanes or explains why
  the paper experiment still cannot pass

This phase closes only the protocol gap. It does not introduce a paper-faithful
`mabd_newton` lane, a force-waveform comparison, paper pendulum geometry,
rendered output, or timing evidence.

## Selected Design

Extend the existing comparison-report layer with a physical-pendulum comparison
writer:

```python
write_physical_pendulum_comparison_report(
    path,
    config=config,
    analytic_report_path=analytic_report_path,
    mabd_report_path=mabd_report_path,
    rbd_report_path=rbd_report_path,
    source_commit=source_commit,
    vendored_newton_commit=vendored_newton_commit,
)
```

The writer loads and validates three lane reports:

- `analytic_reference`
- `physical_pendulum_mabd_development_diagnostic`
- `rbd_implicit_baseline`

It emits a `ClaimReport` with:

- `baseline_lane = physical_pendulum_comparison_protocol`
- `solver_mode = physical_pendulum_multilane_comparison_development`
- `backend = report_protocol`
- `status = incomplete`
- `observed.full_experiment_claim_passed = False`
- `observed.missing_required_lanes = ["mabd_newton"]`
- `observed.input_report_provenance`, keyed by lane, with each input report's
  configured path, SHA256, source commit, vendored Newton commit, solver mode,
  backend, baseline lane, and status
- explicit blockers for the missing paper-faithful M-ABD lane, joint-force
  waveform agreement, paper geometry, and paper timing

The config gains a `comparison` block with an output report path, the paper
required lanes, the currently available diagnostic lanes, required paper
metrics, and a bounded diagnostic threshold for M-ABD-vs-RBD angle differences.
The configured `required_lanes` must match the experiment-matrix required lanes
as an unordered set; display order is report-local.

## Comparison Fields

The report records:

- top-level status and lane-status snapshots for all input reports
- solver modes for every lane report
- per-lane input report provenance, including report SHA256 and source commit
- compact scalar metric snapshots:
  - analytic reference identity error
  - M-ABD development angle and pivot/constraint residuals
  - RBD angle error, phase drift, implicit residual, length error, and
    diagnostic joint-force magnitude
- matched M-ABD/RBD compact angle samples, aligned by `(step, time_s)`
- `matched_sample_count`, `mabd_sample_count`, `rbd_sample_count`,
  `unmatched_mabd_samples`, and `unmatched_rbd_samples`; zero matched samples
  is a comparison blocker
- `max_mabd_rbd_abs_angle_delta_rad`
- `paper_metric_statuses`, mapping canonical paper metric names to currently
  available report fields or explicit missing reasons:
  - `pendulum_angle_error -> max_abs_angle_error_rad`
  - `phase_drift -> max_phase_drift_rad`
  - `joint_force_error -> missing_waveform_not_max_magnitude`
- missing paper metrics:
  - `mabd_newton:pendulum_angle_error`
  - `mabd_newton:joint_force_error`
  - `mabd_newton:phase_drift`
  - `physical_pendulum_mabd_development_diagnostic:joint_force_error`
  - `physical_pendulum_mabd_development_diagnostic:phase_drift`
  - `rbd_implicit_baseline:joint_force_error`

The writer validates every input report against expected claim id, scene id,
baseline lane, solver mode, backend, incomplete top-level status,
`observed.full_experiment_claim_passed is False`, and
`asset_hashes.physical_pendulum_procedural`.

The writer must not emit JSON containing `NaN` or `Infinity`. Invalid scalar
sample fields are omitted from diagnostic differences and recorded in blockers
instead of being serialized as non-finite JSON tokens.

## Runner And CLI

Add `run_physical_pendulum_comparison` to `experiment_runner.py`.

Add CLI support:

```bash
scripts/run_experiment.py --lane physical_pendulum_comparison \
  --config configs/experiments/single_body_physical_pendulum.yaml \
  --matrix configs/experiments/paper_experiment_matrix.yaml \
  --analytic-report reports/experiment_matrix/single_body_physical_pendulum_analytic_reference.json \
  --mabd-report reports/experiment_matrix/single_body_physical_pendulum_mabd_development.json \
  --rbd-report reports/experiment_matrix/single_body_physical_pendulum_rbd_baseline.json \
  --output reports/experiment_matrix/single_body_physical_pendulum_comparison.json
```

For this phase, `--analytic-report`, `--mabd-report`, and `--rbd-report` are
explicit inputs. The CLI parser must define all three arguments. This keeps
provenance clear and avoids silently regenerating or mixing lane evidence.

## Validation

Tests must prove:

- the `comparison` config block is parsed and validated
- invalid comparison output paths are rejected
- the comparison writer rejects reports with wrong claim, scene, or lane id
- the comparison writer rejects wrong solver mode/backend/status/procedural
  asset identity
- the comparison writer records matched/unmatched sample counts and blocks zero
  matched samples
- the comparison writer records `paper_metric_statuses` using canonical matrix
  metric names
- corrupted non-finite sample values are blocked without writing `NaN` or
  `Infinity`
- the generated comparison report is schema-valid and incomplete
- the generated comparison report records missing required `mabd_newton`
  evidence and force-waveform blockers
- CLI dispatch for `--lane physical_pendulum_comparison` requires all three
  report inputs and writes the expected report
- docs/provenance validators require the Phase 36 record and comparison report
- docs/provenance validators reject placeholder source commits, require
  per-lane input report provenance, require the vendored Newton commit to match
  `96713fa965463b69c229a4d30582c733ff3526bb`, and require
  `experiment.single_body.physical_pendulum` to remain unpassed

## Claim Boundaries

Allowed Phase 36 claims:

- a physical-pendulum comparison protocol exists
- the protocol compares current analytic, M-ABD development diagnostic, and
  RBD diagnostic reports
- the protocol records missing paper-lane and missing paper-metric blockers

Forbidden Phase 36 claims:

- the physical-pendulum paper experiment is passed
- the M-ABD development diagnostic is the required `mabd_newton` experiment
  lane
- the RBD diagnostic is paper-faithful for all paper purposes
- diagnostic joint-force magnitude is joint-force waveform agreement
- paper geometry, rendering, or timing is verified
- any `experiment.*` paper claim is passed
