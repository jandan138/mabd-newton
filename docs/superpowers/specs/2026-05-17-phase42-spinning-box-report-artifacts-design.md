# Phase 42 Spinning Box Report Artifacts Design

Date: 2026-05-17

## Purpose

Phase 42 makes the current spinning-box evidence replayable from committed
small JSON reports. Earlier phases added the spinning-box M-ABD diagnostic
lane, paper-horizon diagnostic lane, paper-faithful RBD lane gate, and
comparison protocol, but the repository still does not commit the corresponding
`reports/experiment_matrix/` artifacts. This phase closes that provenance gap
without changing the solver claim.

## Scope

In scope:

- Generate and commit these small report artifacts:
  - `reports/experiment_matrix/single_body_spinning_box.json`
  - `reports/experiment_matrix/single_body_spinning_box_paper_horizon.json`
  - `reports/experiment_matrix/single_body_spinning_box_rbd_baseline.json`
  - `reports/experiment_matrix/single_body_spinning_box_comparison.json`
- Record the generating repository source commit and vendored Newton source
  commit in every report.
- Validate that the M-ABD diagnostic report remains `status = incomplete` and
  `solver_mode = mabd_cpu_oracle_development`.
- Validate that the M-ABD paper-horizon diagnostic remains `status =
  incomplete`, records threshold violations, and retains the kinematic
  feasibility blocker.
- Validate that the RBD baseline report uses `solver_mode =
  paper_faithful_implicit_rbd` and records `lane_gate_status = passed`.
- Validate that the comparison report has no missing required scalar metrics,
  no invalid required scalar metrics, consumes the committed M-ABD and RBD
  reports, and remains `status = incomplete` with blockers
  `mabd_newton_report_incomplete` and
  `spinning_box_comparison_pass_gate_not_enabled`.
- Keep `experiment.single_body.spinning_box` at
  `reproduction_status = blocked_by_baselines`.

Out of scope:

- Passing the spinning-box experiment.
- Enabling the spinning-box comparison pass gate.
- Claiming M-ABD lane pass status.
- Removing the M-ABD paper-horizon shape, energy, or kinematic blockers.
- Changing Newton solver behavior or report-generation physics.
- Committing raw simulation directories, videos, or large logs.

## Approach

The implementation uses the existing config-driven runner and report contracts.
No new solver path is added. The only generated artifacts are compact JSON
claim reports already written by repository code. Tests and
`scripts/validate_docs.py` become the gate that proves the artifacts are
present, source-stamped, internally consistent, and bounded by current claim
limitations.

## Alternatives Considered

1. Commit no reports and rely on runner tests only.
   This keeps the tree small but leaves no durable machine-checkable evidence
   for the current spinning-box lanes.
2. Treat current M-ABD diagnostics as a passed lane.
   This overclaims because the report status is incomplete and paper-horizon
   diagnostics still violate shape and energy thresholds.
3. Commit compact reports and keep blockers.
   This is the selected option because it advances reproducibility while
   preserving claim boundaries.

## Report Contract

All four reports must be JSON `ClaimReport` artifacts with:

- `claim_id = experiment.single_body.spinning_box`
- `scene_id = single_body_spinning_box`
- `vendored_newton_commit =
  96713fa965463b69c229a4d30582c733ff3526bb`
- non-placeholder `source_commit`
- `status = incomplete`

Additional lane requirements:

- MABD diagnostic: `baseline_lane = mabd_newton`, `solver_mode =
  mabd_cpu_oracle_development`, finite `linear_momentum_error`,
  `angular_momentum_error`, `energy_drift`, `initial_position_m`, and
  `final_position_m`.
- MABD paper horizon: `baseline_lane = mabd_newton`, `solver_mode =
  mabd_cpu_oracle_paper_horizon_diagnostic`, `mabd_paper_horizon_status =
  development_gap_observed`, and blockers including
  `mabd_paper_horizon_diagnostic_thresholds_violated` and
  `mabd_kinematic_feasibility_blocker_recorded`.
- RBD baseline: `baseline_lane = rbd_implicit_baseline`, `solver_mode =
  paper_faithful_implicit_rbd`, and `observed.lane_gate_status = passed`.
- Comparison: `baseline_lane = spinning_box_comparison_protocol`,
  `solver_mode = spinning_box_multilane_comparison_development`, no missing or
  invalid required scalar/vector metrics, RBD lane gate passed, MABD lane gate
  incomplete, and blockers preserving the incomplete comparison gate.

## Claim Boundary

Phase 42 verifies that the current spinning-box report artifacts are committed
and machine-checkable. It does not verify a passed spinning-box paper result,
does not enable a passed M-ABD lane, and does not complete any `experiment.*`
claim.

## Tests

- `tests.test_spinning_box_report_artifacts` verifies committed report paths,
  per-lane identities, source stamps, finite required metrics, retained
  blockers, and comparison input paths.
- `tests.test_phase0_bootstrap` verifies Phase42 claim-boundary and record
  text.
- `scripts/validate_docs.py` verifies Phase42 docs, report contracts, report
  hashes, non-overclaim text, and that all `experiment.*` claims remain
  unpassed.
