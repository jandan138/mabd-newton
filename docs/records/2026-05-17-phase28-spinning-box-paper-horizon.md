# Phase 28 Spinning-Box Paper Horizon Record

Date: 2026-05-17

## Status

passed

## Scope

Phase 28 adds a bounded paper-horizon M-ABD diagnostic report for the
single-body spinning-box claim. The diagnostic runs the current Newton M-ABD
CPU oracle for the 10 second figure horizon at `h = 1e-2` and `h = 1e-3`,
scans every integration step for extrema and threshold violations, and stores
compact trajectory samples for review.

The diagnostic report remains `status=incomplete`; it records
`mabd_paper_horizon_status = development_gap_observed` and no
`lane_gate_status`. This phase does not pass the M-ABD lane, the comparison
protocol, or the paper spinning-box experiment.

## Config Path

- `configs/experiments/single_body_spinning_box.yaml`
- `configs/experiments/paper_experiment_matrix.yaml`

## Repository

- worktree:
  `/cpfs/user/zhuzihou/dev/mabd-newton/.worktrees/phase28-spinning-box-paper-horizon`
- branch: `phase28-spinning-box-paper-horizon`
- base commit: `2d626033c8b6d4300084bb5092d5e470dd545b9f`
- design commit: `c0b2acc`
- plan commit: `458c586`
- config commit: `0f0fb4f`
- report implementation commit: `6d78c2e`
- runner/comparison commit: `3347542`
- docs/record commit: `b20817d`
- independent review: claim/provenance review required removing
  `lane_gate_status` from the M-ABD diagnostic, preserving
  `paper-claims.yaml`, and adding distinct output/provenance fields.
  Numerics review required every-step extrema scanning, named thresholds,
  kinetic/elastic/total energy separation, explicit threshold violations, and
  figure/PDF text provenance.

## Vendored Newton

- vendored path: `vendor/newton`
- upstream commit: `96713fa965463b69c229a4d30582c733ff3526bb`
- local patch status: Phase 28 does not modify vendored Newton.

## Paper Source

- arXiv ID: `2603.08079`
- arXiv version: `v2`
- PDF SHA256:
  `a594e79093673c60fc59ad14f9b71f29a8f7f8e7b1c3d9c73efe6f5814cc6ec0`
- TeX source SHA256:
  `73ec398956c606dec2f8f40f0d38b9d5370e11b27830775e1b3765fe0efc563f`
- cited source lines: `experiment.tex:40-55`
- figure path: `/tmp/mabd-paper/source/images/cube/roll_cube.pdf`
- figure PDF SHA256:
  `7669b062348324a3b0090cc9f44930655c83233a87f63389db9198b88f95ae80`
- figure text extraction:
  `pdftotext /tmp/mabd-paper/source/images/cube/roll_cube.pdf -`
- extracted figure labels include `Co-rotated ABD, h=10-2`,
  `Co-rotated ABD, h=10-3`, and `Time (s)` with axis labels through `10`.

## Environment

- Python: `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python`
- reference clone source:
  `/cpfs/user/zhuzihou/conda-managed/envs/physics-primitive-newton-py310`
- readiness status: `smoke_passed`
- readiness JSON output: branch-gate stdout, not committed.
- non-pollution result: `mutates_reference_environment=false`,
  `uses_reference_python=false`, `uses_ambient_python=false`

## Metrics And Diagnostics

- random seed: not applicable; the diagnostic is deterministic.
- baseline_lane = mabd_newton
- solver_mode = mabd_cpu_oracle_paper_horizon_diagnostic
- backend = cpu_numpy
- report status: `incomplete`
- mabd_paper_horizon_status = development_gap_observed
- no `lane_gate_status`
- paper_horizon_duration_s = 10.0
- paper_step_sizes_s = [0.01, 0.001]
- threshold_violations:
  `max_abs_det_minus_one`, `max_affine_orthogonality_error`,
  `max_relative_kinetic_energy_drift`, `max_relative_total_energy_drift`,
  `max_singular_value`
- h = 0.01 steps_completed = 1000 / 1000
- h = 0.01 max_relative_total_energy_drift = 229618.58334568472
- h = 0.01 max_abs_det_minus_one = 360000.00000263675
- h = 0.01 max_affine_orthogonality_error = 509116.8824580432
- h = 0.01 max_singular_value = 600.0008333349521
- h = 0.001 steps_completed = 10000 / 10000
- h = 0.001 max_relative_total_energy_drift = 2228.3267211638477
- h = 0.001 max_abs_det_minus_one = 3600.0000000000528
- h = 0.001 max_affine_orthogonality_error = 5091.168824543211
- h = 0.001 max_singular_value = 60.0083327547104
- top-level linear_momentum_error = 3.749445450725338e-11
- top-level angular_momentum_error = 3.662254641883743e-07
- top-level energy_drift = 690003842953.7826
- comparison blocker retained: `mabd_newton_report_incomplete`
- comparison blocker retained: `spinning_box_comparison_pass_gate_not_enabled`
- matrix blocker retained: `mabd_newton_report_incomplete`
- matrix blocker retained: `spinning_box_comparison_report_incomplete`
- No `experiment.*` claim is passed in this phase.

## Artifacts

- committed project code:
  `src/mabd_reproduction/experiment_configs.py`,
  `src/mabd_reproduction/single_body_reports.py`,
  `src/mabd_reproduction/experiment_runner.py`,
  `scripts/run_experiment.py`
- committed config:
  `configs/experiments/single_body_spinning_box.yaml`
- committed tests:
  `tests/test_experiment_run_configs.py`,
  `tests/test_single_body_report_lane.py`,
  `tests/test_experiment_runner.py`,
  `tests/test_spinning_box_comparison.py`,
  `tests/test_phase0_bootstrap.py`
- docs validator: `scripts/validate_docs.py`
- generated reports: not committed; tests write JSON reports to temporary
  directories only
- raw artifacts: temporary unittest output and branch-gate stdout only

## Verification Commands

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_run_configs
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_single_body_report_lane
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_runner tests.test_spinning_box_comparison
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_phase0_bootstrap
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
git diff --check
```

## TDD Evidence

Config RED result:

```text
FAILED (errors=2)
```

Config GREEN result:

```text
Ran 9 tests, OK
```

Paper-horizon report RED result:

```text
ImportError: cannot import name 'write_spinning_box_paper_horizon_report'
```

Paper-horizon report GREEN result:

```text
Ran 3 tests, OK
```

Runner/comparison RED result:

```text
FAILED (failures=1, errors=2)
```

Runner/comparison GREEN result:

```text
Ran 23 tests, OK
```

Docs RED result:

```text
missing claim boundary bullet: This repository contains Phase 28
record file missing: docs/records/2026-05-17-phase28-spinning-box-paper-horizon.md
```

## Claim Impact

No `experiment.*` claim is passed in this phase. The single-body spinning-box
matrix still lists `mabd_newton_report_incomplete` and
`spinning_box_comparison_report_incomplete`. The Phase 27
`rbd_implicit_baseline` lane gate is unchanged.
