# Phase 52 Heavy-Top MABD Metrics

## Status

passed_for_heavy_top_mabd_metric_diagnostics

## Scope

- worktree:
  `/cpfs/user/zhuzihou/dev/mabd-newton/.worktrees/phase52-heavy-top-mabd-metrics`
- source commit used for regenerated reports:
  `ef53522077c53b4842f5198938dd5c24190e7863`
- vendored Newton upstream commit: `96713fa965463b69c229a4d30582c733ff3526bb`
- paper source version: `2603.08079v2`
- Python: `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python`
- environment isolation: `mabd-newton-py310` remains a clone of
  `physics-primitive-newton-py310`; no install was made into the ambient DSW
  Python or the reference `physics-primitive-agent` environment.

## Evidence

- claim: `experiment.single_body.heavy_top`
- config: `configs/experiments/single_body_heavy_top.yaml`
- matrix: `configs/experiments/paper_experiment_matrix.yaml`
- `reports/experiment_matrix/single_body_heavy_top_mabd_newton.json`
  - sha256:
    `9342374ffde72071308b6aa5c117815392f71f4db1e07d9817ac61e4847bf324`
  - solver mode: `mabd_cpu_oracle_heavy_top_newton_lane`
  - baseline lane: `mabd_newton`
  - backend: `cpu_numpy_newton_only`
  - top-level evidence status: `incomplete`
  - diagnostic energy initial: `8.562042497067562`
  - diagnostic energy final: `8.550026757953814`
  - diagnostic relative energy drift: `-0.0014033729823068706`
  - per-sample field: `precession_velocity_rad_s`
- `reports/experiment_matrix/single_body_heavy_top_comparison.json`
  - sha256:
    `522d0dbea2eacbe1f334400dbcba4bd885ba26cecd50d239463048f7e24ec8de`
  - solver mode: `heavy_top_multilane_comparison_development`
  - baseline lane: `heavy_top_comparison_protocol`
  - backend: `report_protocol`
  - top-level evidence status: `incomplete`
  - missing paper metric: `nutation_angle_error:paper_reference_curve_missing`
  - MABD precession velocity status: `diagnostic_available`
  - MABD energy drift status: `diagnostic_available`
- `reports/experiment_matrix/single_body_heavy_top_rk4_reference.json`
  - input report sha256:
    `41418e964dd9e7fba1516f420fa97ced8cfaf9157d552d9072f85fcbb08f564c`
- retained blocker: `mabd_newton_report_incomplete`
- retained blocker: `heavy_top_comparison_report_incomplete`
- retained blocker: `exact_heavy_top_inertia_unknown`
- retained blocker: `exact_heavy_top_geometry_unknown`
- retained blocker: `raw_heavy_top_reference_curve_data_missing`
- retained blocker: `heavy_top_timing_evidence_missing`
- retained blocker: `heavy_top_comparison_pass_gate_not_enabled`
- retained blocker: `sample_time_grid_mismatch`

## Result Boundary

No `experiment.*` claim is passed.

`experiment.single_body.heavy_top` remains intended. Phase 52 records
MABD-side diagnostic precession-velocity and point-mass energy metrics only. It
does not prove paper-faithful heavy-top inertia or geometry, raw curve
agreement, ABD-vs-RBD pass-gate agreement, rendered output, paper timing,
runtime performance, generated video evidence, or a full paper reproduction.

## Commands

- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_heavy_top_mabd tests.test_heavy_top_comparison_reports`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py`
- `PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"`
- `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .`
- `git diff --check`
