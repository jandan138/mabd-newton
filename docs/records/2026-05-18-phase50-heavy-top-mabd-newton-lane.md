# Phase 50 Heavy-Top MABD Newton Diagnostic Lane

## Status

passed_for_heavy_top_mabd_newton_diagnostic_lane

## Scope

- worktree: `/cpfs/user/zhuzihou/dev/mabd-newton/.worktrees/phase50-heavy-top-mabd-lane`
- source commit: `45bef31db663b2d13d9385ef64a8445cbac9b613`
- current artifact regeneration source commit:
  `ef53522077c53b4842f5198938dd5c24190e7863`
- vendored Newton upstream commit: `96713fa965463b69c229a4d30582c733ff3526bb`
- paper source version: `2603.08079v2`
- Python: `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python`
- environment isolation: no install was made into the ambient DSW Python or the
  reference `physics-primitive-agent` environment.

## Evidence

- claim: `experiment.single_body.heavy_top`
- config: `configs/experiments/single_body_heavy_top.yaml`
- matrix: `configs/experiments/paper_experiment_matrix.yaml`
- `reports/experiment_matrix/single_body_heavy_top_mabd_newton.json`
- lane report sha256:
  `9342374ffde72071308b6aa5c117815392f71f4db1e07d9817ac61e4847bf324`
- solver mode: `mabd_cpu_oracle_heavy_top_newton_lane`
- baseline lane: `mabd_newton`
- backend: `cpu_numpy_newton_only`
- solver model config source: `newton_model_derived`
- custom frequencies: `mabd:body`, `mabd:world_constraint`, `mabd:gravity`
- lane status: `incomplete_diagnostic_generated`
- top-level evidence status: `incomplete`
- diagnostic energy initial: `8.562042497067562`
- diagnostic energy final: `8.550026757953814`
- diagnostic relative energy drift: `-0.0014033729823068706`
- retained blocker: `mabd_newton_report_incomplete`
- retained blocker: `exact_heavy_top_inertia_unknown`
- retained blocker: `exact_heavy_top_geometry_unknown`
- retained blocker: `raw_heavy_top_reference_curve_data_missing`
- retained blocker: `heavy_top_comparison_report_incomplete`
- retained blocker: `heavy_top_timing_evidence_missing`

## Result Boundary

No `experiment.*` claim is passed.

`experiment.single_body.heavy_top` remains intended. The Phase 50 lane records a
Newton-derived M-ABD diagnostic rollout only. It does not prove paper-faithful
heavy-top inertia or geometry, raw curve agreement, ABD-vs-RBD comparison,
rendered output, paper timing, or a full paper reproduction.

## Commands

- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_heavy_top_mabd tests.test_experiment_run_configs tests.test_experiment_runner tests.test_phase0_bootstrap`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py`
- `git diff --check`
