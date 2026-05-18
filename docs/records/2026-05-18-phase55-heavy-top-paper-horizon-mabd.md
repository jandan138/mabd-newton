# Phase 55 Heavy-Top Paper-Horizon MABD

## Status

passed_for_heavy_top_paper_horizon_mabd_diagnostic

## Scope

- branch: `phase55-heavy-top-paper-horizon`
- worktree:
  `/cpfs/user/zhuzihou/dev/mabd-newton/.worktrees/phase55-heavy-top-paper-horizon`
- base source commit: `8021cb0d86b6eff269a073a6e2fb4f1fbe0845ff`
- implementation source commit:
  `db5347a1ff5c46f0cdb695bce842273428c4a1af`
- vendored Newton upstream commit: `96713fa965463b69c229a4d30582c733ff3526bb`
- paper source version: `2603.08079v2`
- Python: `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python`

## Evidence

Phase 55 adds a heavy-top MABD diagnostic lane on the paper figure horizon:

- config: `configs/experiments/single_body_heavy_top.yaml`
- lane config: `mabd_paper_horizon`
- `reports/experiment_matrix/single_body_heavy_top_mabd_paper_horizon.json`
  - sha256:
    `605f7056cabd29869ce4074ee880839ff26c3d7a6b8f16bb95f18be0afdf076c`
- report `source_commit`:
  `db5347a1ff5c46f0cdb695bce842273428c4a1af`
- solver mode: `mabd_cpu_oracle_heavy_top_newton_lane`
- backend: `cpu_numpy_newton_only`
- baseline lane: `mabd_newton`
- diagnostic scope: `paper_horizon_sample_grid`
- `solver_model_config_source`: `newton_model_derived`
- Newton custom frequencies: `mabd:body`, `mabd:world_constraint`,
  `mabd:gravity`
- step count: `10000`
- sample count: `11`
- duration: `10.0`
- lane status: `incomplete_diagnostic_failed`
- current threshold violation: `max_affine_shape_spread_m`

The regenerated heavy-top comparison report consumes that paper-horizon MABD
report:

- `reports/experiment_matrix/single_body_heavy_top_comparison.json`
  - sha256:
    `b7b006f8a86cf7a259ac641395e1011e7a08e10db41e7a42137221e5c5e705d9`
- comparison report `source_commit`:
  `db5347a1ff5c46f0cdb695bce842273428c4a1af`
- comparison solver mode: `heavy_top_multilane_comparison_development`
- comparison baseline lane: `heavy_top_comparison_protocol`
- RK4 sample count: `11`
- MABD sample count: `11`
- matched sample index count: `11`
- max sample time delta: `0.0`
- `time_grid_mismatch`: `false`
- current blocker removed: `sample_time_grid_mismatch`
- MABD input provenance path:
  `reports/experiment_matrix/single_body_heavy_top_mabd_paper_horizon.json`
- MABD input provenance diagnostic scope: `paper_horizon_sample_grid`

## Retained Blockers

The heavy-top experiment remains incomplete. Phase 55 retains:

- `exact_heavy_top_inertia_unknown`
- `exact_heavy_top_geometry_unknown`
- `raw_heavy_top_reference_curve_data_missing`
- `mabd_newton_report_incomplete`
- `heavy_top_comparison_report_incomplete`
- `heavy_top_timing_evidence_missing`
- `heavy_top_comparison_pass_gate_not_enabled`
- `heavy_top_digitized_figure_curve_agreement_not_passed`

## Result Boundary

No `experiment.*` claim is passed. `experiment.single_body.heavy_top` remains intended,
not passed.

Phase 55 does not prove a passed heavy-top experiment, a passed heavy-top MABD
lane, paper-horizon MABD stability or accuracy, paper-faithful heavy-top MABD
dynamics, paper-faithful inertia or geometry, raw author curve data, digitized
curve agreement, a comparison pass gate, paper timing, rendered output,
generated videos, runtime performance, comparative baseline results, or a full
paper reproduction.

## Commands

- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_run_configs tests.test_heavy_top_mabd tests.test_heavy_top_comparison_reports tests.test_experiment_runner`
- `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check src/mabd_reproduction/heavy_top_mabd.py src/mabd_reproduction/heavy_top_reports.py src/mabd_reproduction/experiment_configs.py src/mabd_reproduction/experiment_runner.py src/mabd_reproduction/comparison_reports.py scripts/run_experiment.py tests/test_experiment_run_configs.py tests/test_heavy_top_mabd.py tests/test_heavy_top_comparison_reports.py tests/test_experiment_runner.py`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/run_experiment.py --lane heavy_top_mabd_paper_horizon --config configs/experiments/single_body_heavy_top.yaml --matrix configs/experiments/paper_experiment_matrix.yaml --source-commit db5347a1ff5c46f0cdb695bce842273428c4a1af --vendored-newton-commit 96713fa965463b69c229a4d30582c733ff3526bb`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/run_experiment.py --lane heavy_top_comparison --config configs/experiments/single_body_heavy_top.yaml --matrix configs/experiments/paper_experiment_matrix.yaml --rbd-report reports/experiment_matrix/single_body_heavy_top_rk4_reference.json --mabd-report reports/experiment_matrix/single_body_heavy_top_mabd_paper_horizon.json --figure-report reports/experiment_matrix/single_body_heavy_top_figure_curves.json --source-commit db5347a1ff5c46f0cdb695bce842273428c4a1af --vendored-newton-commit 96713fa965463b69c229a4d30582c733ff3526bb`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests`
- `PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"`
- `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .`
- `git diff --check`
