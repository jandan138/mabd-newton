# Phase 17 Spinning-Box M-ABD Paper Momentum Metrics Record

Date: 2026-05-17

## Status

passed

## Scope

Phase 17 adds paper-value momentum metric reporting to the M-ABD
single-body spinning-box development lane. The lane now parses the paper
p0/L0 values, maps them to an ABD generalized velocity through Newton's rigid
embedding map, reports `paper_spatial_twist`, `linear_momentum_error`, and
`angular_momentum_error`, and lets the spinning-box comparison protocol consume
those M-ABD metrics.

This phase does not verify the paper spinning-box experiment, paper-faithful
implicit RBD baseline, paper-faithful affine collision, paper timing, rendered
output, paper trajectory agreement, committed generated report artifacts, or
any passed `experiment.*` claim. The M-ABD report and the comparison protocol
remain `incomplete`.

## Config Path

- `configs/experiments/single_body_spinning_box.yaml`
- matrix: `configs/experiments/paper_experiment_matrix.yaml`

## Repository

- worktree:
  `/cpfs/user/zhuzihou/dev/mabd-newton/.worktrees/phase17-spinning-box-mabd-paper-metrics`
- branch: `phase17-spinning-box-mabd-paper-metrics`
- base commit: `12be437`
- plan commit: `5cc171a`
- implementation commits: `ebf7d86`, `da56334`, `ff24a68`
- docs/provenance commit: `d25e3bd3b7b60655285d3d077e600c438737cd48`
- independent review: claim/spec review found missing exact
  docs/provenance commit and no overclaims; code/physics review found no
  findings.
- review hardening commit: records the exact Phase 17 docs/provenance commit
  required by the claim/spec review.

## Vendored Newton

- vendored path: `vendor/newton`
- upstream commit: `96713fa965463b69c229a4d30582c733ff3526bb`
- local patch status: Phase 17 adds no vendored Newton source changes.

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
- Backend: `cpu_numpy` for the M-ABD development report and
  `report_protocol` for the comparison report.
- readiness check:
  `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/env/readiness_check.py`
- readiness status: `smoke_passed`
- non-pollution result: `mutates_reference_environment=false`,
  `uses_reference_python=false`, `uses_ambient_python=false`

## Metrics And Thresholds

- random seed: not applicable; the M-ABD CPU oracle lane is deterministic.
- paper p0/L0: `p0=[100, 0, 0]`, `L0=[0, 100, 0]`
- derived mass: `1.0 kg`
- derived inertia diagonal: `[1/600, 1/600, 1/600] kg m^2`
- paper_spatial_twist: `[0, 60000, 0, 100, 0, 0]`
- ABD generalized velocity in
  `configs/experiments/single_body_spinning_box.yaml`:
  `[0, 0, -60000, 0, 0, 0, 60000, 0, 0, 100, 0, 0]`
- `linear_momentum_error <= 1.0e-9`
- `angular_momentum_error <= 1.0e-9`
- existing comparison blocker remains:
  `spinning_box_comparison_report_incomplete`
- generated M-ABD reports remain `incomplete` because the paper comparison
  lanes and benchmark evidence are still incomplete.

## Artifacts

- committed shared physics helpers:
  `src/mabd_reproduction/spinning_box_physics.py`
- helper API:
  `spinning_box_physical_properties`,
  `abd_generalized_velocity_from_paper_momenta`, and
  `mabd_momentum_diagnostics`
- committed M-ABD report writer:
  `write_spinning_box_development_report`
- committed tests: `tests/test_rigid_baselines.py`,
  `tests/test_single_body_report_lane.py`,
  `tests/test_spinning_box_comparison.py`,
  `tests/test_experiment_runner.py`, `tests/test_experiment_run_configs.py`,
  `tests/test_phase0_bootstrap.py`
- generated reports: not committed; tests write JSON reports to temporary
  directories only
- No `experiment.*` claim is passed in this phase.

## TDD Evidence

RED result:

```text
shared physics helper: ModuleNotFoundError for mabd_reproduction.spinning_box_physics
config/report tests: synthetic initial_qd and missing M-ABD momentum metrics
comparison tests: old expectation still reported M-ABD metric-missing blockers
docs tests: Phase 17 boundary, record, and /17 validator output missing
```

GREEN result:

```text
shared helper/RBD tests: Ran 5 tests, OK
config/report tests: Ran 10 tests, OK
comparison/runner tests: Ran 16 tests, OK
```

## Verification

Verification commands for the docs/provenance commit:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_phase0_bootstrap
/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check scripts/validate_docs.py tests/test_phase0_bootstrap.py
git diff --check
```

Expected result after this record is committed:

```text
docs: Phase 0/1/2/3/4/5/6/7/8/9/10/11/12/13/14/15/16/17 docs/provenance validation passed
phase0 bootstrap tests: OK
ruff: All checks passed!
git diff --check: clean
```

## Claim Impact

No `experiment.*` claim is passed in this phase.
