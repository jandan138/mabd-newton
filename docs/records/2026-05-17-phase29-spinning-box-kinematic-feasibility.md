# Phase 29 Spinning-Box Kinematic Feasibility Record

Date: 2026-05-17

## Status

passed

## Scope

Phase 29 adds a bounded kinematic feasibility diagnostic for the single-body
spinning-box M-ABD paper-horizon report. It records whether the paper angular
momentum can be represented by an orthogonal finite-difference update under the
current velocity relation `qd_next=(q_next-q_n)/h`.

The diagnostic report remains `status=incomplete`; it records
`mabd_kinematic_feasibility_status =
paper_momentum_requires_affine_stretch_under_q_delta_over_h` and no
`lane_gate_status`. This phase does not pass the M-ABD lane, the comparison
protocol, or the paper spinning-box experiment.

## Config Path

- `configs/experiments/single_body_spinning_box.yaml`
- `configs/experiments/paper_experiment_matrix.yaml`

## Repository

- worktree:
  `/cpfs/user/zhuzihou/dev/mabd-newton/.worktrees/phase29-spinning-box-mabd-momentum-gate`
- branch: `phase29-spinning-box-mabd-momentum-gate`
- base commit: `df9ff5f`
- design commit: `68a95b6`
- plan commit: `d18942c`
- helper implementation commit: `7cec405`
- report implementation commit: `061f916`
- docs/record commit: `0c38c44`
- independent review: paper/claim review required no M-ABD lane pass, no
  comparison pass, and no `paper-claims.yaml` pass-state change. Solver/numerics
  review identified the finite-difference velocity relation as the key blocker:
  orthogonal updates at paper step sizes cannot represent the paper angular
  momentum without affine stretch or a different velocity semantics.

## Vendored Newton

- vendored path: `vendor/newton`
- upstream commit: `96713fa965463b69c229a4d30582c733ff3526bb`
- local patch status: Phase 29 does not modify vendored Newton.

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

## Environment

- Python: `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python`
- reference clone source:
  `/cpfs/user/zhuzihou/conda-managed/envs/physics-primitive-newton-py310`
- readiness status: `smoke_passed`
- readiness JSON output: branch-gate stdout, not committed.
- non-pollution result: `mutates_reference_environment=false`,
  `uses_reference_python=false`, `uses_ambient_python=false`
- clone drift observation: the current `mabd-newton-py310` package set matches
  the reference `physics-primitive-newton-py310` dependency line except the
  editable project package is `mabd_newton` instead of
  `primitive_collision_compiler`.

## Metrics And Diagnostics

- random seed: not applicable; the diagnostic is deterministic.
- baseline_lane = mabd_newton
- solver_mode = mabd_cpu_oracle_paper_horizon_diagnostic
- backend = cpu_numpy
- report status: `incomplete`
- mabd_kinematic_feasibility_status =
  paper_momentum_requires_affine_stretch_under_q_delta_over_h
- velocity_update_relation = `qd_next=(q_next-q_n)/h`
- no `lane_gate_status`
- paper_angular_speed_rad_s = 60000.0
- paper_angular_momentum_norm_kg_m2_s = 100.0
- h = 0.01 orthogonal_update_angular_speed_bound_rad_s = 100.0
- h = 0.01 orthogonal_update_angular_momentum_bound_kg_m2_s = 0.16666666666666666
- h = 0.01 required_speed_to_bound_ratio = 600.0
- h = 0.001 orthogonal_update_angular_speed_bound_rad_s = 1000.0
- h = 0.001 orthogonal_update_angular_momentum_bound_kg_m2_s = 1.6666666666666667
- h = 0.001 required_speed_to_bound_ratio = 60.0
- comparison blocker retained: `mabd_newton_report_incomplete`
- matrix blocker retained: `mabd_newton_report_incomplete`
- matrix blocker retained: `spinning_box_comparison_report_incomplete`
- No `experiment.*` claim is passed in this phase.

## Artifacts

- committed project code:
  `src/mabd_reproduction/spinning_box_physics.py`,
  `src/mabd_reproduction/single_body_reports.py`
- committed tests:
  `tests/test_rigid_baselines.py`,
  `tests/test_single_body_report_lane.py`,
  `tests/test_phase0_bootstrap.py`
- docs validator: `scripts/validate_docs.py`
- generated reports: not committed; tests write JSON reports to temporary
  directories only
- raw artifacts: temporary unittest output and branch-gate stdout only

## Verification Commands

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_rigid_baselines
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_single_body_report_lane
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_phase0_bootstrap
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
git diff --check
```

## TDD Evidence

Helper RED result:

```text
ImportError: cannot import name 'spinning_box_kinematic_feasibility'
```

Helper GREEN result:

```text
Ran 8 tests, OK
```

Report RED result:

```text
KeyError: 'mabd_kinematic_feasibility_status'
```

Report GREEN result:

```text
Ran 3 tests, OK
```

Docs RED result:

```text
missing claim boundary bullet: This repository contains Phase 29
FileNotFoundError: docs/records/2026-05-17-phase29-spinning-box-kinematic-feasibility.md
```

## Claim Impact

No `experiment.*` claim is passed in this phase. The single-body spinning-box
matrix still lists `mabd_newton_report_incomplete` and
`spinning_box_comparison_report_incomplete`. The Phase 27
`rbd_implicit_baseline` lane gate is unchanged.
