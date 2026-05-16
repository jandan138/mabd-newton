# Phase 13 Configured Spinning-Box Lane Record

Date: 2026-05-17

## Status

passed

## Scope

Phase 13 adds a per-scene config for the single-body spinning-box development
lane and makes the M-ABD Newton CPU-oracle report consume that config.

This phase does not verify the paper spinning-box experiment, RBD baselines,
paper timing, rendered output, paper trajectory agreement, or any passed
`experiment.*` claim. The generated report remains `incomplete` because full
paper evidence still requires at least the `rbd_implicit_baseline` lane.

## Source And Environment

- repo base commit: `eaaba80`
- plan commit: `7f68fd7`
- implementation commits: `9dd5d10`, `bbb4836`
- paper source version: arXiv `2603.08079v2`
- paper source paths:
  - `/tmp/mabd-paper/source/sections/experiment.tex`
- source basis:
  - `experiment.tex:40-55`: spinning-box momentum and energy diagnostic text
- canonical Python:
  `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python`
- backend: CPU NumPy oracle through vendored Newton imports

## Config Path

The Phase 13 per-scene config is:

- `configs/experiments/single_body_spinning_box.yaml`

The config is validated against:

- `configs/experiments/paper_experiment_matrix.yaml`

## Repository

- worktree:
  `/cpfs/user/zhuzihou/dev/mabd-newton/.worktrees/phase13-configured-spinning-box`
- branch: `phase13-configured-spinning-box`
- base commit: `eaaba80`
- plan commit: `7f68fd7`
- implementation commits: `9dd5d10`, `bbb4836`

## Vendored Newton

- vendored path: `vendor/newton`
- upstream commit: `96713fa965463b69c229a4d30582c733ff3526bb`
- local patch status: Phase 13 adds no vendored Newton source changes; it uses
  the existing M-ABD CPU oracle to generate the configured development report.

## Paper Source

- arXiv ID: `2603.08079`
- arXiv version: `v2`
- local PDF: `/tmp/mabd-paper/mabd.pdf`
- local TeX source: `/tmp/mabd-paper/source`
- PDF SHA256:
  `a594e79093673c60fc59ad14f9b71f29a8f7f8e7b1c3d9c73efe6f5814cc6ec0`
- TeX source SHA256:
  `73ec398956c606dec2f8f40f0d38b9d5370e11b27830775e1b3765fe0efc563f`
- cited source lines: `experiment.tex:40-55`

## Environment

- Python: `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python`
- Isolation: dependency set cloned from
  `/cpfs/user/zhuzihou/conda-managed/envs/physics-primitive-newton-py310`,
  with the current repo installed editable as `mabd-newton`
- Backend: CPU NumPy oracle; Warp imports are available through vendored Newton
  but this phase does not add kernels.

## Metrics And Thresholds

- random seed: not applicable; tests use deterministic arrays only
- metrics: per-scene config required keys, experiment matrix alignment,
  invalid passed experiment config rejection, deterministic step count, energy
  drift, generalized momentum delta norm, incomplete report status, and
  config-backed report field propagation
- thresholds: exact key/status equality, `energy_drift <= 1.0e-12`, and
  `generalized_momentum_delta_norm <= 1.0e-12`
- Report validation rejects `status=passed` for experiment configs and reports
  until a dedicated evidence gate exists.

## Artifacts

- committed config:
  `configs/experiments/single_body_spinning_box.yaml`
- committed source:
  `src/mabd_reproduction/experiment_configs.py`
- committed development lane:
  `src/mabd_reproduction/single_body_reports.py`
- committed tests:
  `tests/test_experiment_run_configs.py` and
  `tests/test_single_body_report_lane.py`
- committed evidence record:
  `docs/records/2026-05-17-phase13-configured-spinning-box.md`
- generated reports: not committed; tests write JSON reports to temporary
  directories only
- raw artifacts: not applicable; no generated run directories, videos, or raw
  logs are committed in this phase
- `load_spinning_box_config` loads the per-scene config.
- `validate_spinning_box_config_against_matrix` checks matrix alignment.
- `write_spinning_box_development_report` consumes the loaded config.

## TDD Evidence

RED commands:

```bash
PYTHONPATH=src:vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  -m unittest tests.test_experiment_run_configs

PYTHONPATH=src:vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  -m unittest tests.test_single_body_report_lane

PYTHONPATH=src:vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  -m unittest tests.test_phase0_bootstrap
```

RED result:

```text
ModuleNotFoundError: No module named 'mabd_reproduction.experiment_configs'
TypeError: write_spinning_box_development_report() got an unexpected keyword argument 'config'
Phase 13 boundary and record assertions failed because the record did not exist.
```

GREEN commands:

```bash
PYTHONPATH=src:vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  -m unittest tests.test_experiment_run_configs

PYTHONPATH=src:vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  -m unittest tests.test_single_body_report_lane tests.test_experiment_run_configs tests.test_reporting_contracts
```

GREEN result:

```text
experiment run configs: Ran 3 tests, OK
single-body report lane plus config/reporting contracts: Ran 9 tests, OK
```

## Verified Behavior

- `load_spinning_box_config` loads the per-scene spinning-box config into a
  typed object with deterministic 12-DOF initial state, step count, thresholds,
  and incomplete report status.
- `validate_spinning_box_config_against_matrix` requires the config claim,
  scene id, source lines, assets, output report, and lanes to match the
  experiment matrix entry.
- Config loading rejects `status=passed` for experiment configs.
- `write_spinning_box_development_report(..., config=config)` propagates config
  scene id, timestep, step count, thresholds, status, and failure reason into
  the generated `ClaimReport`.
- The report still cites missing `rbd_implicit_baseline` evidence instead of
  marking the experiment claim passed.

## Final Verification

Final verification commands:

```bash
/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_run_configs tests.test_single_body_report_lane tests.test_reporting_contracts tests.test_phase0_bootstrap
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"
git diff --check
```

Final verification result:

```text
ruff: All checks passed!
docs: Phase 0/1/2/3/4/5/6/7/8/9/10/11/12/13 docs/provenance validation passed
focused public tests: Ran 30 tests, OK
full public tests: Ran 106 tests, OK
vendored Newton import:
  /cpfs/user/zhuzihou/dev/mabd-newton/.worktrees/phase13-configured-spinning-box/vendor/newton/newton/__init__.py
git diff --check: clean
```

## Claim Impact

No `experiment.*` claim is passed in this phase.
