# Phase 57 T-Handle Comparison Protocol

## Status

passed_for_t_handle_comparison_protocol

## Scope

- branch: `phase57-t-handle-comparison`
- worktree:
  `/cpfs/user/zhuzihou/dev/mabd-newton/.worktrees/phase57-t-handle-comparison`
- source commit used for comparison report:
  `5ad17151f1e70172b922fda4d96da8144cd60774`
- vendored Newton upstream commit: `96713fa965463b69c229a4d30582c733ff3526bb`
- paper source version: `2603.08079v2`
- Python: `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python`
- environment isolation: `mabd-newton-py310` remains separate from the
  reference `physics-primitive-agent` environment and the ambient DSW Python.

## Evidence

Phase 57 adds a T-handle multi-lane comparison protocol report:

- claim: `experiment.single_body.t_handle`
- config: `configs/experiments/single_body_t_handle.yaml`
- matrix: `configs/experiments/paper_experiment_matrix.yaml`
- `reports/experiment_matrix/single_body_t_handle_comparison.json`
  - sha256:
    `258a56e8c0530a14c86268b9a9f7e08a801b0fe026db133e579e283d2263861e`
  - solver mode: `t_handle_multilane_comparison_development`
  - baseline lane: `t_handle_comparison_protocol`
  - backend: `report_protocol`
  - top-level evidence status: `incomplete`
- input `reports/experiment_matrix/single_body_t_handle_rk4_reference.json`
  - input report sha256:
    `a0153e2bd4f0e20aa5271ecbaaec726661e352b6b4baebe96dcfc76dddd25b67`
  - provenance scope:
    `torque_free_principal_axis_rk4_diagnostic`
- input `reports/experiment_matrix/single_body_t_handle_mabd_newton.json`
  - input report sha256:
    `969e8aa66516af3b846bf64699cc2339df66dfaa6a22c851fee4a9957744e55b`
  - provenance scope: `t_handle_model_derived_proxy`
  - solver model config source: `newton_model_derived`
- matched sample index count: `9`
- finite matched sample count: `9`
- time-aligned sample count: `9`
- max sample time delta: `0.0`
- `time_grid_mismatch`: `false`
- `sample_nonfinite`: `false`
- intermediate-axis waveform RMSE diagnostic:
  `2.21913405945304`
- max absolute angular-velocity delta diagnostic:
  `2.992369356563783`
- sample-grid flip timing status:
  `sample_grid_flip_delta_unavailable`
- paper metric status for flip timing:
  `sample_grid_diagnostic_not_paper_timing`
- paper metric status for intermediate-axis waveform:
  `diagnostic_available_not_paper_curve`
- paper metric status for energy loss:
  `signed_energy_drift_diagnostic_not_paper_loss`
- missing paper metric:
  `flip_timing_error:raw_paper_timing_missing`
- missing paper metric:
  `intermediate_axis_angular_velocity_waveform:raw_paper_curve_missing`
- missing paper metric:
  `energy_loss:paper_energy_loss_metric_unavailable`

The T-handle matrix now records `t_handle_comparison_report_incomplete` instead
of `t_handle_comparison_report_missing`.

## Retained Blockers

The T-handle experiment remains incomplete. Phase 57 retains:

- `exact_t_handle_geometry_unknown`
- `raw_t_handle_reference_curve_data_missing`
- `mabd_newton_report_incomplete`
- `t_handle_comparison_report_incomplete`
- `t_handle_timing_evidence_missing`
- `t_handle_comparison_pass_gate_not_enabled`

## Result Boundary

No `experiment.*` claim is passed. `experiment.single_body.t_handle` remains intended,
not passed.

Phase 57 records a comparison protocol and current input-report provenance only.
It does not prove a passed T-handle experiment, a passed T-handle MABD lane,
paper-faithful T-handle geometry or inertia, raw waveform agreement, paper
energy loss, ABD-vs-RBD comparison pass, paper timing, rendered output,
generated videos, runtime performance, comparative baseline pass-gate results,
or a full paper reproduction.

## Commands

- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_run_configs tests.test_t_handle_comparison_reports tests.test_reporting_contracts tests.test_experiment_runner`
- `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check src/mabd_reproduction/comparison_reports.py src/mabd_reproduction/experiment_configs.py src/mabd_reproduction/experiment_runner.py scripts/run_experiment.py tests/test_t_handle_comparison_reports.py tests/test_experiment_runner.py tests/test_experiment_run_configs.py tests/test_reporting_contracts.py`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/run_experiment.py --lane t_handle_comparison --config configs/experiments/single_body_t_handle.yaml --matrix configs/experiments/paper_experiment_matrix.yaml --rbd-report reports/experiment_matrix/single_body_t_handle_rk4_reference.json --mabd-report reports/experiment_matrix/single_body_t_handle_mabd_newton.json --source-commit 5ad17151f1e70172b922fda4d96da8144cd60774 --vendored-newton-commit 96713fa965463b69c229a4d30582c733ff3526bb`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests`
- `PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"`
- `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .`
- `git diff --check`
