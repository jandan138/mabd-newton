# Phase 23 Spinning-Box Position Comparison Record

Date: 2026-05-17

## Status

passed

## Scope

Phase 23 carries configured spinning-box position vectors through the existing
development reports. The M-ABD lane now records `initial_position_m = [0.0,
0.05, 0.0]` and `final_position_m = [4.0, 0.05, 0.0]`, and the comparison
protocol validates the `initial_position_m` and `final_position_m` fields as
finite length-three vectors before recording `lane_vector_metrics` and
`lane_vector_metric_differences`.

This phase does not verify the paper spinning-box experiment,
paper-faithful implicit RBD baseline, paper-faithful affine collision,
collision detection, continuous collision detection, friction, implicit contact
solve, gravity, rendered output, paper timing, paper trajectory agreement,
committed generated report artifacts, or any passed `experiment.*` claim. The
comparison report remains `incomplete`.

## Config Path

- `configs/experiments/single_body_spinning_box.yaml`
- matrix: `configs/experiments/paper_experiment_matrix.yaml`

## Repository

- worktree:
  `/cpfs/user/zhuzihou/dev/mabd-newton/.worktrees/phase23-spinning-box-position-comparison`
- branch: `phase23-spinning-box-position-comparison`
- base commit: `153071c2185b7f801b122096420e392e9f1126dc`
- plan commit: `080f4908c9a16f5e707a1175ceb33c4e7bda8c2d`
- implementation commit: `434bdeab71a024277311bfc0925eb9b09630bf41`
- implementation commit: `57c8365262f12fd4f026da14163f493c60a86974`
- docs/provenance commit: pending until this record is committed
- independent review: pending before merge.

## Vendored Newton

- vendored path: `vendor/newton`
- upstream commit: `96713fa965463b69c229a4d30582c733ff3526bb`
- local patch status: Phase 23 adds no vendored Newton source changes.

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
- readiness check:
  `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/env/readiness_check.py`
- readiness status: `smoke_passed`
- clone drift check: `pip freeze` differs from
  `physics-primitive-newton-py310` only by the editable project line,
  `primitive_collision_compiler` versus `mabd_newton`.
- non-pollution result: `mutates_reference_environment=false`,
  `uses_reference_python=false`, `uses_ambient_python=false`

## Metrics And Thresholds

- random seed: not applicable; both position-development lanes are
  deterministic.
- config lane: `mabd_newton`
- comparison lane: `spinning_box_comparison_protocol`
- M-ABD solver mode in report: `mabd_cpu_oracle_development`
- comparison solver mode in report:
  `spinning_box_multilane_comparison_development`
- backend in M-ABD report: `cpu_numpy`
- backend in comparison report: `report_protocol`
- Newton step count: `4`
- time step: `0.01s`
- required_vector_metrics = [`initial_position_m`, `final_position_m`]
- initial_position_m = [0.0, 0.05, 0.0]
- final_position_m = [4.0, 0.05, 0.0]
- lane_vector_metrics records finite vectors for `mabd_newton` and
  `rbd_implicit_baseline`.
- lane_vector_metric_differences records
  `mabd_newton_minus_rbd_implicit_baseline` for finite position vectors.
- invalid_required_vector_metrics records malformed or non-finite vector
  values; the regression test uses `mabd_newton:final_position_m_invalid`.
- comparison blocking reason retained:
  `spinning_box_comparison_report_incomplete`
- report status: `incomplete`
- no passed `experiment.*` claim is created in this phase.

## Artifacts

- committed code: `src/mabd_reproduction/single_body_reports.py`,
  `src/mabd_reproduction/comparison_reports.py`
- committed tests: `tests/test_single_body_report_lane.py`,
  `tests/test_spinning_box_comparison.py`, `tests/test_phase0_bootstrap.py`
- docs validator: `scripts/validate_docs.py`
- generated reports: not committed; tests write JSON reports to temporary
  directories only
- No `experiment.*` claim is passed in this phase.

## TDD Evidence

M-ABD report RED result:

```text
KeyError: 'initial_position_m'
```

M-ABD report GREEN result:

```text
M-ABD report tests: Ran 2 tests, OK
ruff: All checks passed!
git diff --check: exit 0
```

Comparison RED result:

```text
KeyError: 'lane_vector_metrics'
KeyError: 'invalid_required_vector_metrics'
```

Comparison GREEN result:

```text
comparison tests: Ran 4 tests, OK
ruff: All checks passed!
git diff --check: exit 0
```

Docs RED result:

```text
missing claim boundary bullet: This repository contains Phase 23
record file missing:
  docs/records/2026-05-17-phase23-spinning-box-position-comparison.md
validator output still ended at Phase 22
```

Docs GREEN result:

```text
phase bootstrap docs tests: Ran 41 tests, OK
docs validator: Phase 0/1/2/3/4/5/6/7/8/9/10/11/12/13/14/15/16/17/18/19/20/21/22/23 docs/provenance validation passed
```

## Claim Impact

No `experiment.*` claim is passed in this phase.
