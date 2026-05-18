# Phase 56 T-Handle MABD Newton Diagnostic

## Status

passed_for_t_handle_mabd_newton_diagnostic

## Scope

- branch: `phase56-t-handle-mabd-newton`
- worktree:
  `/cpfs/user/zhuzihou/dev/mabd-newton/.worktrees/phase56-t-handle-mabd-newton`
- base source commit: `00d864edd79e5f7073828534bdb3b9f74943d5d7`
- implementation source commit:
  `51745677bd115a0b98294dd8bbf9132e94fc4f3a`
- vendored Newton upstream commit: `96713fa965463b69c229a4d30582c733ff3526bb`
- paper source version: `2603.08079v2`
- Python: `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python`

## Evidence

Phase 56 adds a T-handle MABD Newton diagnostic lane:

- config: `configs/experiments/single_body_t_handle.yaml`
- lane config: `mabd_newton`
- `reports/experiment_matrix/single_body_t_handle_mabd_newton.json`
  - sha256:
    `969e8aa66516af3b846bf64699cc2339df66dfaa6a22c851fee4a9957744e55b`
- report `source_commit`:
  `51745677bd115a0b98294dd8bbf9132e94fc4f3a`
- solver mode: `mabd_cpu_oracle_t_handle_newton_lane`
- backend: `cpu_numpy_newton_only`
- baseline lane: `mabd_newton`
- diagnostic scope: `t_handle_model_derived_proxy`
- `solver_model_config_source`: `newton_model_derived`
- Newton custom frequencies: `mabd:body`, `mabd:gravity`
- step count: `4000`
- sample count: `9`
- duration: `4.0`
- lane status: `incomplete_diagnostic_failed`
- current threshold violation: `max_affine_shape_spread_m`
- required missing lanes in this MABD report: `[]`
- relative energy drift: `-2.2352228624317797e-12`
- angular momentum norm drift: `-6.166533408032632e-13`
- maximum proxy inertia relative error: `0.00010000000000021103`

The T-handle matrix now records `mabd_newton_report_incomplete` instead of
`mabd_newton_report_missing`.

## Retained Blockers

The T-handle experiment remains incomplete. Phase 56 retains:

- `exact_t_handle_geometry_unknown`
- `raw_t_handle_reference_curve_data_missing`
- `mabd_newton_report_incomplete`
- `t_handle_comparison_report_missing`
- `t_handle_timing_evidence_missing`

## Result Boundary

No `experiment.*` claim is passed. `experiment.single_body.t_handle` remains intended,
not passed.

Phase 56 does not prove a passed T-handle experiment, a passed T-handle MABD
lane, paper-faithful T-handle geometry or inertia, raw waveform agreement, an
ABD-vs-RBD comparison pass, paper timing, rendered output, generated videos,
runtime performance, comparative baseline results beyond the generated RK4 and
MABD diagnostic reports, or a full paper reproduction.

## Commands

- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_run_configs tests.test_t_handle_reference tests.test_experiment_runner`
- `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check src/mabd_reproduction/t_handle_mabd.py src/mabd_reproduction/t_handle_reports.py src/mabd_reproduction/experiment_configs.py src/mabd_reproduction/experiment_runner.py scripts/run_experiment.py tests/test_experiment_run_configs.py tests/test_t_handle_reference.py tests/test_experiment_runner.py`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/run_experiment.py --lane t_handle_mabd_newton --config configs/experiments/single_body_t_handle.yaml --matrix configs/experiments/paper_experiment_matrix.yaml --source-commit 51745677bd115a0b98294dd8bbf9132e94fc4f3a --vendored-newton-commit 96713fa965463b69c229a4d30582c733ff3526bb`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests`
- `PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"`
- `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .`
- `git diff --check`
