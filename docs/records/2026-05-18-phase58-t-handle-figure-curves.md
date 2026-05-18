# Phase 58 T-Handle Figure Curves

## Status

passed_for_t_handle_figure_curve_digitization_lane

## Scope

- branch: `phase58-t-handle-figure-curves`
- worktree:
  `/cpfs/user/zhuzihou/dev/mabd-newton/.worktrees/phase58-t-handle-figure-curves`
- source commit used for regenerated reports:
  `892896b330ecd380656c01638bccf742accc4b28`
- vendored Newton upstream commit: `96713fa965463b69c229a4d30582c733ff3526bb`
- paper source version: `2603.08079v2`
- Python: `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python`
- environment isolation: `mabd-newton-py310` remains separate from the
  reference `physics-primitive-agent` environment and the ambient DSW Python.

## Evidence

Phase 58 adds a T-handle public paper-figure color-family digitization lane:

- source figure: `/tmp/mabd-paper/source/images/T-handle/T-handle.pdf`
- source figure sha256:
  `5ae6464fd7e7e6fd471ad56e67cdbead6014736cb731a232ce29d80630a72c1c`
- renderer: `pdftocairo 22.02.0`
- render DPI: `300`
- rendered size: `3861 x 1541`
- figure curve scope: `color_family_digitization_only`
- digitized color families: `blue`, `orange`, `green`
- angular-velocity sample counts:
  `{"blue": 101, "green": 101, "orange": 101}`
- energy-loss sample counts:
  `{"blue": 101, "green": 101, "orange": 101}`
- limitations:
  - `not_authors_raw_data`
  - `no_solid_dashed_line_style_split`
  - `no_curve_identity_claim`
  - `no_curve_agreement_gate`
  - `no_runtime_timing_evidence`

Committed report artifacts:

- `reports/experiment_matrix/single_body_t_handle_figure_curves.json`
  - sha256:
    `975f1e1fc27d76073145a6981a9f8e87907fac908333d8303a4386f5a5e743c6`
  - baseline lane: `paper_figure_digitization`
  - solver mode: `t_handle_paper_figure_digitization`
  - backend: `pdftocairo_pillow`
  - top-level evidence status: `incomplete`
  - lane status: `figure_color_families_digitized`
  - raw outputs: `compact_numeric_samples_only`
- `reports/experiment_matrix/single_body_t_handle_comparison.json`
  - sha256:
    `80b5ac9bc0782f3ad51314945a35a7f6cc0505f2e916abbc2898bbf3c00ab6d2`
  - baseline lane: `t_handle_comparison_protocol`
  - solver mode: `t_handle_multilane_comparison_development`
  - backend: `report_protocol`
  - top-level evidence status: `incomplete`
  - input provenance now includes `paper_figure_curves`
  - `digitized_figure_reference_available`: `true`
  - paper metric status for intermediate-axis waveform:
    `paper_figure_digitized_color_family_available_not_curve_agreement`
  - paper metric status for energy loss:
    `paper_figure_digitized_color_family_available_not_energy_agreement`

No rendered PNG, PDF, SVG, base64 payload, raw paper asset, generated video, or
raw simulation run directory is committed.

## Retained Blockers

The T-handle experiment remains incomplete. Phase 58 retains or adds:

- `exact_t_handle_geometry_unknown`
- `raw_t_handle_reference_curve_data_missing`
- `mabd_newton_report_incomplete`
- `t_handle_comparison_report_incomplete`
- `t_handle_timing_evidence_missing`
- `t_handle_comparison_pass_gate_not_enabled`
- `sample_grid_flip_delta_unavailable`
- `t_handle_digitized_figure_curve_agreement_not_passed`

## Result Boundary

No `experiment.*` claim is passed. `experiment.single_body.t_handle` remains
intended, not passed.

Phase 58 records public figure color-family samples and comparison provenance
only. It does not prove authors' raw simulation data, exact curve identity,
solid/dashed line-style separation, paper-faithful T-handle geometry or
inertia, raw waveform agreement, paper energy-loss agreement, ABD-vs-RBD
comparison pass, paper timing, runtime performance, generated videos, or a full
paper reproduction.

## Commands

- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_t_handle_digitization tests.test_experiment_run_configs`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_t_handle_digitization tests.test_t_handle_comparison_reports tests.test_experiment_runner`
- `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check src/mabd_reproduction/t_handle_digitization.py src/mabd_reproduction/experiment_configs.py tests/test_t_handle_digitization.py tests/test_experiment_run_configs.py`
- `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check src/mabd_reproduction/comparison_reports.py src/mabd_reproduction/experiment_runner.py scripts/run_experiment.py tests/test_t_handle_comparison_reports.py tests/test_experiment_runner.py`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/run_experiment.py --lane t_handle_figure_curves --config configs/experiments/single_body_t_handle.yaml --matrix configs/experiments/paper_experiment_matrix.yaml --source-commit 892896b330ecd380656c01638bccf742accc4b28 --vendored-newton-commit 96713fa965463b69c229a4d30582c733ff3526bb`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/run_experiment.py --lane t_handle_comparison --config configs/experiments/single_body_t_handle.yaml --matrix configs/experiments/paper_experiment_matrix.yaml --rbd-report reports/experiment_matrix/single_body_t_handle_rk4_reference.json --mabd-report reports/experiment_matrix/single_body_t_handle_mabd_newton.json --figure-report reports/experiment_matrix/single_body_t_handle_figure_curves.json --source-commit 892896b330ecd380656c01638bccf742accc4b28 --vendored-newton-commit 96713fa965463b69c229a4d30582c733ff3526bb`
- `git diff --check`
