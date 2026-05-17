# Phase 43 T-Handle RK4 Reference

Date: 2026-05-18

## Status

passed

## Repository

- branch: `phase43-t-handle-reference`
- report source_commit: `d741e6f5b1d85f7c02afb520f55b8bb273947604`
- plan: `docs/superpowers/plans/2026-05-18-mabd-phase43-t-handle-rk4-reference.md`
- spec: `docs/superpowers/specs/2026-05-18-phase43-t-handle-rk4-reference-design.md`

## Environment

- interpreter:
  `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python`
- environment role: `mabd-newton-clone`
- reference environment: `physics-primitive-newton-py310`
- mutates_reference_environment=false
- uses_reference_python=false
- uses_ambient_python=false
- vendored Newton commit:
  `96713fa965463b69c229a4d30582c733ff3526bb`

## Paper Source

- source lines: `/tmp/mabd-paper/source/sections/experiment.tex:57-75`
- figure asset: `/tmp/mabd-paper/source/images/T-handle/T-handle.pdf`
- figure PDF sha256:
  `5ae6464fd7e7e6fd471ad56e67cdbead6014736cb731a232ce29d80630a72c1c`
- paper values recorded in config:
  - zero gravity
  - `omega_0 = 3 rad/s`
  - implicit RBD RK4 reference with `h = 10^-4 s`
  - subtle asymmetry

The public paper source does not disclose the exact T-handle geometry,
principal inertias, subtle asymmetry magnitude, mesh, or raw plotted reference
curve data.

## Report Artifact

The report artifact is a compact JSON summary under `reports/experiment_matrix/`.
No raw simulation directories, videos, or large logs are committed.

- `reports/experiment_matrix/single_body_t_handle_rk4_reference.json`
  - sha256:
    `a0153e2bd4f0e20aa5271ecbaaec726661e352b6b4baebe96dcfc76dddd25b67`
  - baseline lane: `rbd_rk4_reference`
  - solver mode: `t_handle_torque_free_rk4_reference`
  - backend: `cpu_numpy`
  - status: `incomplete`
  - lane_status: `diagnostic_generated`
  - retained blocker: `exact_t_handle_geometry_unknown`
  - retained blocker: `raw_t_handle_reference_curve_data_missing`
  - retained blocker: `mabd_newton_report_missing`
  - retained blocker: `t_handle_comparison_report_missing`
  - retained blocker: `t_handle_timing_evidence_missing`
  - `intermediate_axis_sign_flips = 1`
  - `relative_energy_drift = -1.2828602409992419e-14`
  - `angular_momentum_norm_drift = -5.329003906068249e-15`

## Runner Command

The report was generated with the config-driven runner and the isolated
M-ABD Newton Python environment:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/run_experiment.py \
  --lane t_handle_rk4_reference \
  --config configs/experiments/single_body_t_handle.yaml \
  --matrix configs/experiments/paper_experiment_matrix.yaml \
  --source-commit d741e6f5b1d85f7c02afb520f55b8bb273947604 \
  --vendored-newton-commit 96713fa965463b69c229a4d30582c733ff3526bb \
  --output reports/experiment_matrix/single_body_t_handle_rk4_reference.json
```

## Claim Impact

No `experiment.*` claim is passed.
`experiment.single_body.t_handle` remains intended in
`docs/reference/paper-claims.yaml` and planned in
`configs/experiments/paper_experiment_matrix.yaml`.
Phase 43 does not implement a paper-faithful T-handle geometry, raw figure curve
agreement, M-ABD T-handle dynamics, ABD-vs-RBD comparison, rendered output,
runtime performance, generated videos, or raw simulation logs.

## Verification Commands

- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_t_handle_reference tests.test_experiment_run_configs tests.test_experiment_runner tests.test_phase0_bootstrap`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/env/readiness_check.py`
- `PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"`
- `git diff --check`
