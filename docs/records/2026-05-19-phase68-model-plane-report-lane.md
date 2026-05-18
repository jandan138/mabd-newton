# Phase 68 Model Plane Report Lane

## Status

passed_for_solver_mabd_model_plane_report_diagnostic

## Scope

- branch: `phase68-model-plane-report-lane`
- implementation source_commit =
  `c2088d012e51d2b901c075c6b88790c347915089`
- vendored Newton upstream commit:
  `96713fa965463b69c229a4d30582c733ff3526bb`
- paper source version: `2603.08079v2`
- report artifact:
  `reports/experiment_matrix/single_body_spinning_box_model_plane_constraint.json`
- report sha256:
  `0dcaef75c93437c95fbb7bd39d126a6f25f18ad4e30ee6c46002d81ea3d346b8`
- Python:
  `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python`
- reference environment:
  `/cpfs/user/zhuzihou/conda-managed/envs/physics-primitive-newton-py310`
- target environment:
  `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310`
- environment non-pollution:
  `mutates_reference_environment=false`, `uses_reference_python=false`,
  `uses_ambient_python=false`

## Evidence

Phase 68 adds a separate spinning-box diagnostic lane that exercises the Phase
67 `SolverMABD.step()` model-derived `mabd:plane_constraint` path through the
experiment runner and CLI:

- config field:
  `paper_horizon.model_plane_constraint_output_report`
- runner: `run_spinning_box_model_plane_constraint`
- CLI lane: `spinning_box_model_plane_constraint`
- writer: `write_spinning_box_model_plane_constraint_report`
- helper: `_run_spinning_box_solver_mabd_model_step`
- transient Newton rows: `mabd:body` and `mabd:plane_constraint`
- CPU row type reached through SolverMABD:
  `MABDCPUOraclePlaneConstraint`
- policy:
  `solver_mabd_model_rows_free_predict_then_active_plane_constraints`
- contact constraint policy:
  `free_predict_then_active_point_plane_normal_constraints`
- config source:
  `model_plane_constraint_config_source = mabd:plane_constraint_custom_rows`
- rank filter policy: `increment_map_row_rank_filter`
- report status: `incomplete`
- solver mode: `solver_mabd_model_plane_constraint_diagnostic`
- backend: `cpu_numpy_newton_solver_mabd_model_rows`
- no `lane_gate_status` is written

The committed report records:

- `max_free_predicted_contact_penetration_m =
  0.001041191071271902`
- `max_constrained_contact_penetration_m =
  2.2351741846282636e-09`
- `model_plane_constraint_reduced_free_predicted_penetration = true`
- `max_requested_plane_constraint_count = 4`
- `max_accepted_plane_constraint_count = 3`
- `max_skipped_plane_constraint_count = 1`
- `max_model_plane_constraint_residual_norm =
  1.3877787807814457e-17`
- blocking reasons include `mabd_newton_report_incomplete`,
  `mabd_paper_horizon_diagnostic_thresholds_violated`,
  `spinning_box_model_plane_constraint_not_paper_faithful`,
  `spinning_box_comparison_pass_gate_not_enabled`, and
  `mabd_kinematic_feasibility_blocker_recorded`

## Environment

The project environment is a cloned local runtime, not the shared reference
environment. `scripts/env/clone_from_reference.py --dry-run` reports
`target_exists` on this machine. `scripts/env/readiness_check.py` reports
`smoke_passed`, imports `warp==1.13.0` and `PyYAML==6.0.3` from
`/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310`, and imports
`newton` from this repository's `vendor/newton` tree.

## Result Boundary

Phase 68 is diagnostic report-lane evidence only. It is not a contact solver,
not Newton `Contacts` ingestion, not collision detection, not active-set
generation inside Newton, not IPC, not friction or complementarity, not
paper-faithful affine collision/contact, not paper-faithful M-ABD stepping, not
unmodified Newton M-ABD contact support, not rendered-output agreement, not
runtime performance evidence, and not full paper reproduction.

Boundary keywords: not Newton `Contacts` ingestion; not paper-faithful affine collision/contact; not full paper reproduction.

No `experiment.*` claim is passed. `paper-claims.yaml` is unchanged.

## Commands

- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_run_configs`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_single_body_report_lane`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_runner`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/run_experiment.py --lane spinning_box_model_plane_constraint --config configs/experiments/single_body_spinning_box.yaml --matrix configs/experiments/paper_experiment_matrix.yaml --output reports/experiment_matrix/single_body_spinning_box_model_plane_constraint.json --source-commit c2088d012e51d2b901c075c6b88790c347915089 --vendored-newton-commit 96713fa965463b69c229a4d30582c733ff3526bb`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/env/clone_from_reference.py --dry-run`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/env/readiness_check.py`
- `PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"`
- `git diff --check`
