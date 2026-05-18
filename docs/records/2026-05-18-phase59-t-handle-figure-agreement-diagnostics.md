# Phase59 T-Handle Figure Agreement Diagnostics Record

## Status

passed_for_t_handle_digitized_figure_agreement_diagnostic_lane

## Provenance

- branch: `phase59-t-handle-figure-agreement`
- worktree:
  `/cpfs/user/zhuzihou/dev/mabd-newton/.worktrees/phase59-t-handle-figure-agreement`
- implementation commit:
  `5d8a0079876d17568464a87c320c53be2d898089`
- vendored Newton upstream commit:
  `96713fa965463b69c229a4d30582c733ff3526bb`
- paper source version: `2603.08079v2`
- environment:
  `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python`
- backend: `cpu_numpy`, `cpu_numpy_newton_only`, and `report_protocol`
- seed: `not_applicable_deterministic_no_random_sampling`
- config:
  `configs/experiments/single_body_t_handle.yaml`
- matrix:
  `configs/experiments/paper_experiment_matrix.yaml`

## Evidence

Phase 59 adds numeric diagnostics comparing current T-handle diagnostic-lane
samples to the Phase 58 digitized T-handle paper-figure color-family curves.

The comparison report now records:

- `digitized_figure_curve_agreement_available`: `true`
- `digitized_figure_curve_agreement_passed`: `false`
- normalized-time mapping:
  `lane_time_s / diagnostic_duration_s * 100`
- normalized-time claim status:
  `normalized_figure_time_not_paper_raw_time`
- best-color-family claim status:
  `numeric_best_fit_not_legend_identity`
- agreement claim status:
  `diagnostic_only_not_curve_agreement`
- paper metric status for intermediate-axis waveform:
  `paper_figure_digitized_color_family_error_diagnostic_available_not_agreement`
- paper metric status for energy loss:
  `paper_figure_digitized_energy_loss_error_diagnostic_available_not_agreement`

Committed report artifacts:

- `reports/experiment_matrix/single_body_t_handle_rk4_reference.json`
  - sha256:
    `0a0f1be3ffbfced0dd4ef463ee3419c119775a46ddde17807748d1b957c5b1b3`
  - sample field added: `relative_energy_loss`
  - top-level evidence status: `incomplete`
- `reports/experiment_matrix/single_body_t_handle_mabd_newton.json`
  - sha256:
    `a04556cdf375fa63d9a9a927ac3fa9732351a07be3aa26c82e617a492f198199`
  - sample field added: `relative_energy_loss`
  - top-level evidence status: `incomplete`
- `reports/experiment_matrix/single_body_t_handle_comparison.json`
  - sha256:
    `a3b0a8acb993d99d842027fab7c10a8df7deffd903d1507b2851fbcd35fd3766`
  - baseline lane: `t_handle_comparison_protocol`
  - solver mode: `t_handle_multilane_comparison_development`
  - backend: `report_protocol`
  - top-level evidence status: `incomplete`
  - input provenance includes `paper_figure_curves`
- `reports/experiment_matrix/single_body_t_handle_figure_curves.json`
  - sha256:
    `975f1e1fc27d76073145a6981a9f8e87907fac908333d8303a4386f5a5e743c6`
  - reused Phase 58 digitized color-family source

Observed best-color diagnostics in the committed comparison report:

- `intermediate_axis_angular_velocity_waveform.rbd_rk4_reference`
  - best color family: `blue`
  - RMSE: `2.825187073627759`
  - max absolute error: `4.896470588235294`
  - matched samples: `9`
- `intermediate_axis_angular_velocity_waveform.mabd_newton`
  - best color family: `blue`
  - RMSE: `2.049181746364472`
  - max absolute error: `4.896470588235294`
  - matched samples: `9`
- `energy_loss.rbd_rk4_reference`
  - best color family: `orange`
  - RMSE: `0.029111399489891207`
  - max absolute error: `0.07218309859153116`
  - matched samples: `9`
- `energy_loss.mabd_newton`
  - best color family: `orange`
  - RMSE: `0.029111399488363488`
  - max absolute error: `0.07218309858931408`
  - matched samples: `9`

Thresholds:

- comparison `max_sample_time_delta_s`: `1.0e-12`
- figure x-axis range: `[0.0, 100.0]`
- no curve-agreement threshold or pass gate is enabled

Raw artifacts:

- committed artifacts are compact JSON reports only
- no rendered PNG, PDF, SVG, base64 payload, generated video, or raw simulation
  run directory is committed

## Retained Blockers

The T-handle experiment remains incomplete. Phase 59 retains:

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

Phase 59 records normalized-time numeric diagnostics against digitized
paper-figure color-family curves only. It does not prove authors' raw
simulation data, authors' raw curve data, exact curve identity, solid/dashed
line-style separation, paper raw-time alignment, paper-faithful T-handle
geometry or inertia, raw waveform agreement, paper energy-loss agreement,
ABD-vs-RBD comparison pass, paper timing, runtime performance, generated
videos, rendered output, or a full paper reproduction.

## Commands

- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_t_handle_comparison_reports.THandleComparisonReportTests.test_t_handle_lane_reports_record_relative_energy_loss_samples`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_t_handle_comparison_reports`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_t_handle_reference tests.test_t_handle_comparison_reports tests.test_t_handle_digitization tests.test_experiment_runner`
- `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check src/mabd_reproduction/comparison_reports.py src/mabd_reproduction/t_handle_reports.py tests/test_t_handle_comparison_reports.py tests/test_experiment_runner.py`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/run_experiment.py --lane t_handle_rk4_reference --config configs/experiments/single_body_t_handle.yaml --matrix configs/experiments/paper_experiment_matrix.yaml --source-commit 5d8a0079876d17568464a87c320c53be2d898089 --vendored-newton-commit 96713fa965463b69c229a4d30582c733ff3526bb`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/run_experiment.py --lane t_handle_mabd_newton --config configs/experiments/single_body_t_handle.yaml --matrix configs/experiments/paper_experiment_matrix.yaml --source-commit 5d8a0079876d17568464a87c320c53be2d898089 --vendored-newton-commit 96713fa965463b69c229a4d30582c733ff3526bb`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/run_experiment.py --lane t_handle_comparison --config configs/experiments/single_body_t_handle.yaml --matrix configs/experiments/paper_experiment_matrix.yaml --rbd-report reports/experiment_matrix/single_body_t_handle_rk4_reference.json --mabd-report reports/experiment_matrix/single_body_t_handle_mabd_newton.json --figure-report reports/experiment_matrix/single_body_t_handle_figure_curves.json --source-commit 5d8a0079876d17568464a87c320c53be2d898089 --vendored-newton-commit 96713fa965463b69c229a4d30582c733ff3526bb`
- `git diff --check`
