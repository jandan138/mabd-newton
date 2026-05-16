# Phase 14 Experiment Runner Record

Date: 2026-05-17

## Status

passed

## Scope

Phase 14 adds an executable config-driven runner for the single-body
spinning-box M-ABD development report lane. It exposes both a Python API and
`scripts/run_experiment.py` CLI for generating the Phase 13 report from the
committed YAML config.

This phase does not verify the paper spinning-box experiment, RBD baselines,
paper timing, rendered output, paper trajectory agreement, committed generated
report artifacts, or any passed `experiment.*` claim. The generated report
remains `incomplete`.

## Config Path

- `configs/experiments/single_body_spinning_box.yaml`
- matrix: `configs/experiments/paper_experiment_matrix.yaml`

## Repository

- worktree:
  `/cpfs/user/zhuzihou/dev/mabd-newton/.worktrees/phase14-experiment-runner`
- branch: `phase14-experiment-runner`
- base commit: `6bfaa63`
- plan commit: `b3e5d53`
- implementation commits: `a311f62`, `3029326`
- docs/provenance commit: `1de8829`
- verification evidence commit: `f4e4bd6`
- review hardening commit: `ad42baf`

## Vendored Newton

- vendored path: `vendor/newton`
- upstream commit: `96713fa965463b69c229a4d30582c733ff3526bb`
- local patch status: Phase 14 adds no vendored Newton source changes.

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
- Backend: CPU NumPy oracle through vendored Newton imports

## Metrics And Thresholds

- random seed: not applicable; runner uses deterministic config state
- metrics: API report writing, configured output-root resolution, CLI summary
  JSON, CLI failure for invalid config, incomplete report status, rejected
  non-incomplete runner status, rejected output-root path traversal, rejected
  absolute output-root target, and no report written on rejected CLI config
- thresholds: exact output path/status equality and existing Phase 13 report
  thresholds

## Artifacts

- committed runner API: `src/mabd_reproduction/experiment_runner.py`
- committed CLI: `scripts/run_experiment.py`
- committed tests: `tests/test_experiment_runner.py`
- generated reports: not committed; tests write JSON reports to temporary
  directories only
- `run_spinning_box_experiment` validates config and matrix before writing.
- `scripts/run_experiment.py` writes a report and prints JSON summary.

## TDD Evidence

RED result:

```text
runner API: ModuleNotFoundError for mabd_reproduction.experiment_runner
runner CLI: scripts/run_experiment.py missing
docs: Phase 14 boundary and record missing
```

GREEN result:

```text
experiment runner tests: Ran 5 tests, OK
docs/provenance validation: Phase 0/1/2/3/4/5/6/7/8/9/10/11/12/13/14 docs/provenance validation passed
```

Review hardening RED result:

```text
runner status lock: ValueError not raised for status=failed
output-root containment: ValueError not raised for ../escaped.json
output-root absolute target: ValueError not raised for absolute output_report
docs: Phase 14 record missing verification evidence and review hardening commits
```

Review hardening GREEN result:

```text
experiment runner tests: Ran 8 tests, OK
```

## Final Verification

Final verification commands:

```bash
/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_runner tests.test_experiment_run_configs tests.test_single_body_report_lane tests.test_reporting_contracts tests.test_phase0_bootstrap
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"
git diff --check
```

Final verification result:

```text
ruff: All checks passed!
docs: Phase 0/1/2/3/4/5/6/7/8/9/10/11/12/13/14 docs/provenance validation passed
focused public tests: Ran 46 tests, OK
full public tests: Ran 122 tests, OK
vendored Newton import:
  /cpfs/user/zhuzihou/dev/mabd-newton/.worktrees/phase14-experiment-runner/vendor/newton/newton/__init__.py
git diff --check: clean
```

## Claim Impact

No `experiment.*` claim is passed in this phase.
