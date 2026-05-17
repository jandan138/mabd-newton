# Phase 51 Heavy-Top Comparison Protocol

## Status

passed_for_heavy_top_comparison_protocol

## Scope

- worktree: `/cpfs/user/zhuzihou/dev/mabd-newton/.worktrees/phase51-heavy-top-comparison-protocol`
- source commit used for regenerated reports:
  `6c4eab14b2cc4b96ab150b3bbab818c539d6aa6a`
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
- `reports/experiment_matrix/single_body_heavy_top_comparison.json`
  - sha256:
    `4525c71a24f841cfee98332c1bfb68d3365065df82dedc54a31713f0a9438ec9`
  - solver mode: `heavy_top_multilane_comparison_development`
  - baseline lane: `heavy_top_comparison_protocol`
  - backend: `report_protocol`
  - top-level evidence status: `incomplete`
- `reports/experiment_matrix/single_body_heavy_top_rk4_reference.json`
  - input report sha256:
    `2359c0108d10bccbeaeac9ba99896c5d02ac8e0b392c6145597e63f2b3a07156`
- `reports/experiment_matrix/single_body_heavy_top_mabd_newton.json`
  - input report sha256:
    `b71b71fdd06d5daed97efae29eb6428dd1a9e000662329e7b05b4c004512f149`
- retained blocker: `mabd_newton_report_incomplete`
- retained blocker: `heavy_top_comparison_report_incomplete`
- retained blocker: `exact_heavy_top_inertia_unknown`
- retained blocker: `exact_heavy_top_geometry_unknown`
- retained blocker: `raw_heavy_top_reference_curve_data_missing`
- retained blocker: `heavy_top_timing_evidence_missing`
- retained blocker: `heavy_top_comparison_pass_gate_not_enabled`
- retained blocker: `sample_time_grid_mismatch`
- missing paper metric:
  `precession_velocity_error:mabd_precession_velocity_samples_missing`
- missing paper metric:
  `nutation_angle_error:paper_reference_curve_missing`
- missing paper metric: `energy_drift:mabd_energy_drift_missing`

## Result Boundary

No `experiment.*` claim is passed.

`experiment.single_body.heavy_top` remains intended. Phase 51 records an
executable comparison protocol and current input-report provenance only. It
does not prove paper-faithful heavy-top inertia or geometry, raw curve
agreement, M-ABD energy/precession metric agreement, ABD-vs-RBD pass-gate
agreement, rendered output, paper timing, or a full paper reproduction.

## Commands

- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_run_configs tests.test_heavy_top_comparison_reports tests.test_experiment_runner`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/env/readiness_check.py`
- `git diff --check`
