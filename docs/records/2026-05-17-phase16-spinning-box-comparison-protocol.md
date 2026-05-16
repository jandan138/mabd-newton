# Phase 16 Spinning-Box Comparison Protocol Record

Date: 2026-05-17

## Status

passed

## Scope

Phase 16 adds a machine-checkable comparison protocol report for the
single-body spinning-box lanes already present in this repository. The protocol
loads the existing incomplete `mabd_newton` and `rbd_implicit_baseline` reports,
validates claim, scene, and lane identity, records lane status and missing paper
comparison metrics, writes an incomplete `spinning_box_comparison_protocol`
report, and exposes explicit runner and CLI dispatch through
`--lane spinning_box_comparison`.

This phase does not verify the paper spinning-box experiment, paper-faithful
implicit RBD baseline, paper-faithful affine collision, paper timing, rendered
output, paper trajectory agreement, committed generated report artifacts, or
any passed `experiment.*` claim. The generated comparison protocol report
remains `incomplete`.

## Config Path

- `configs/experiments/single_body_spinning_box.yaml`
- matrix: `configs/experiments/paper_experiment_matrix.yaml`

## Repository

- worktree:
  `/cpfs/user/zhuzihou/dev/mabd-newton/.worktrees/phase16-spinning-box-comparison-protocol`
- branch: `phase16-spinning-box-comparison-protocol`
- base commit: `1459afa`
- plan commit: `a3a722a`
- implementation commits: `30ede4d`, `ec2a39c`
- docs/provenance commit: recorded by this Phase 16 docs commit
- review hardening commit: pending independent review

## Vendored Newton

- vendored path: `vendor/newton`
- upstream commit: `96713fa965463b69c229a4d30582c733ff3526bb`
- local patch status: Phase 16 adds no vendored Newton source changes.

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
- Backend: `report_protocol`, comparing committed report schemas and temporary
  generated JSON reports without mutating either environment
- readiness check:
  `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/env/readiness_check.py`
- readiness status: `smoke_passed`
- non-pollution result: `mutates_reference_environment=false`,
  `uses_reference_python=false`, `uses_ambient_python=false`

## Metrics And Thresholds

- random seed: not applicable; comparison protocol is deterministic report
  validation
- baseline lane: `spinning_box_comparison_protocol`
- solver mode: `spinning_box_multilane_comparison_development`
- backend: `report_protocol`
- required input lanes: `mabd_newton`, `rbd_implicit_baseline`
- required paper comparison metrics: `linear_momentum_error`,
  `angular_momentum_error`, `energy_drift`
- matrix blocker advanced from `paper_comparison_protocol_not_recorded` to
  `spinning_box_comparison_report_incomplete`
- report remains incomplete because required lane reports remain incomplete and
  the M-ABD development lane is still missing paper comparison metrics.

## Artifacts

- committed comparison report implementation:
  `src/mabd_reproduction/comparison_reports.py`
- committed runner API: `src/mabd_reproduction/experiment_runner.py`
- committed CLI: `scripts/run_experiment.py`
- committed tests: `tests/test_spinning_box_comparison.py`,
  `tests/test_experiment_runner.py`, `tests/test_experiment_run_configs.py`,
  `tests/test_phase0_bootstrap.py`
- generated reports: not committed; tests write JSON reports to temporary
  directories only
- `run_spinning_box_comparison` requires explicit `--output`,
  `--mabd-report`, and `--rbd-report`.
- `scripts/run_experiment.py --lane spinning_box_comparison` validates the
  config and matrix before writing an incomplete
  `spinning_box_multilane_comparison_development` report.
- No `experiment.*` claim is passed in this phase.

## TDD Evidence

RED result:

```text
comparison report tests: ModuleNotFoundError for mabd_reproduction.comparison_reports
runner API: ImportError for run_spinning_box_comparison
runner CLI: unrecognized --lane spinning_box_comparison
docs/matrix: stale paper_comparison_protocol_not_recorded blocker and Phase 16 record missing
```

GREEN result:

```text
comparison report tests: Ran 2 tests, OK
runner and comparison tests: Ran 16 tests, OK
```

## Final Verification

Final verification commands:

```bash
/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_spinning_box_comparison tests.test_experiment_runner tests.test_experiment_run_configs tests.test_phase0_bootstrap
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"
git diff --check
```

Final verification result:

```text
pending final Phase 16 verification after independent review
```

## Claim Impact

No `experiment.*` claim is passed in this phase.
