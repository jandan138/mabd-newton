# Phase 19 Spinning-Box Comparison Finite Metrics Record

Date: 2026-05-17

## Status

passed

## Scope

Phase 19 hardens the spinning-box comparison protocol so required metrics must
be finite scalar numbers, not merely present keys. The comparison report now
separates `missing_required_metrics` from `invalid_required_metrics`, appends
invalid metric blocking reasons, and records finite-only
`lane_metric_differences` for M-ABD minus RBD development lanes.

This phase does not verify the paper spinning-box experiment, paper-faithful
implicit RBD baseline, paper-faithful affine collision, paper timing, rendered
output, paper trajectory agreement, committed generated report artifacts, or
any passed `experiment.*` claim. The comparison report remains `incomplete`.

## Config Path

- `configs/experiments/single_body_spinning_box.yaml`
- matrix: `configs/experiments/paper_experiment_matrix.yaml`

## Repository

- worktree:
  `/cpfs/user/zhuzihou/dev/mabd-newton/.worktrees/phase19-spinning-box-comparison-finite-metrics`
- branch: `phase19-spinning-box-comparison-finite-metrics`
- base commit: `cd85b64`
- plan commit: `5af27323947b296b3ebf1956a5799d0906dfea03`
- implementation commit: `947bbfa4ba1e3f5ed805585d41ba3a562039441a`
- docs/provenance commit: pending exact commit hash follow-up after this
  record is first committed.

## Vendored Newton

- vendored path: `vendor/newton`
- upstream commit: `96713fa965463b69c229a4d30582c733ff3526bb`
- local patch status: Phase 19 adds no vendored Newton source changes.

## Paper Source

- arXiv ID: `2603.08079`
- arXiv version: `v2`
- PDF SHA256:
  `a594e79093673c60fc59ad14f9b71f29a8f7f8e7b1c3d9c73efe6f5814cc6ec0`
- TeX source SHA256:
  `73ec398956c606dec2f8f40f0d38b9d5370e11b27830775e1b3765fe0efc563f`
- cited source lines: `experiment.tex:40-55`

## Environment

- Python: `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python`
- reference clone source:
  `/cpfs/user/zhuzihou/conda-managed/envs/physics-primitive-newton-py310`
- Backend: `report_protocol` for the comparison report.
- readiness check:
  `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/env/readiness_check.py`
- readiness status: `smoke_passed`
- non-pollution result: `mutates_reference_environment=false`,
  `uses_reference_python=false`, `uses_ambient_python=false`

## Metrics And Thresholds

- random seed: not applicable; comparison report generation is deterministic.
- required metrics:
  `linear_momentum_error`, `angular_momentum_error`, `energy_drift`
- missing metric field: `missing_required_metrics`
- invalid metric field: `invalid_required_metrics`
- invalid metric blocker example: `mabd_newton:energy_drift_invalid`
- finite difference field: `lane_metric_differences`
- finite difference key:
  `mabd_newton_minus_rbd_implicit_baseline`
- generated comparison reports remain `incomplete` because the lane reports are
  still incomplete and the RBD baseline is not paper-faithful.

## Artifacts

- committed comparison protocol:
  `src/mabd_reproduction/comparison_reports.py`
- committed tests: `tests/test_spinning_box_comparison.py`,
  `tests/test_phase0_bootstrap.py`
- docs validator: `scripts/validate_docs.py`
- generated reports: not committed; tests write JSON reports to temporary
  directories only
- No `experiment.*` claim is passed in this phase.

## TDD Evidence

RED result:

```text
comparison tests:
  KeyError for missing `invalid_required_metrics`
  KeyError for missing `lane_metric_differences`
docs tests:
  Phase 19 boundary text missing
  Phase 19 record file missing
  validator output still ended at Phase 18
```

GREEN result:

```text
comparison tests: Ran 3 tests, OK
phase bootstrap docs tests: expected to pass after Phase 19 docs/validator
are committed with this record.
```

## Claim Impact

No `experiment.*` claim is passed in this phase.
