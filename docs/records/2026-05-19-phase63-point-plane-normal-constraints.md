# Phase 63 Point-Plane Normal Constraints

## Status

passed_for_spinning_box_normal_constraint_diagnostic_slice

## Scope

- branch: `phase63-point-plane-normal-constraints`
- implementation commit:
  `ea33e90cd7613212aad4440b9dcf0ac758e07c61`
- vendored Newton upstream commit:
  `96713fa965463b69c229a4d30582c733ff3526bb`
- paper source version: `2603.08079v2`
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

Phase 63 adds `MABDCPUOraclePlaneConstraint` to the Newton CPU oracle and a
separate spinning-box diagnostic lane:

- report lane: `spinning_box_normal_constraint`
- solver mode: `mabd_cpu_oracle_point_plane_normal_constraint_diagnostic`
- backend: `cpu_numpy`
- status: `incomplete`
- contact_constraint_policy =
  `free_predict_then_active_point_plane_normal_constraints`
- rank filter policy: `increment_map_row_rank_filter`
- blocker recorded: `spinning_box_normal_constraint_not_paper_faithful`
- max_free_predicted_contact_penetration_m = `0.001041191335932834`
- max_constrained_contact_penetration_m = `2.081690722340676e-20`
- max_requested_plane_constraint_count = `4`
- max_accepted_plane_constraint_count = `3`
- max_skipped_plane_constraint_count = `1`
- normal_constraint_residual_norm = `1.3877787807814457e-17`
- reduced free-predicted penetration:
  `normal_constraint_reduced_free_predicted_penetration=true`

## Artifacts

- `reports/experiment_matrix/single_body_spinning_box_normal_constraint.json`
  - sha256:
    `5f710498e8651a8ad22dcbcadc5ac1212410100eb36ef5733c721b6cba566394`

## Result Boundary

No `experiment.*` claim is passed. This diagnostic does not pass the
spinning-box experiment, does not pass the M-ABD lane, does not implement a
contact solver, does not verify collision detection, does not implement IPC,
does not implement generic inequality-constrained M-ABD KKT, does not verify
paper-faithful affine collision, does not enable a comparison pass gate, does
not provide rendered-output evidence, does not provide runtime-performance
evidence, and does not establish full paper reproduction.

This diagnostic does not implement a contact solver and does not verify
paper-faithful affine collision.

The observed penetration reduction is only a comparison between this lane's
free-predicted step and this lane's constrained rerun. It is not a global
contact guarantee and it is not a paper-faithful affine collision result.

## Verification Commands

- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_mabd_phase4_solver_step`
- `PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest newton.tests.test_mabd_phase4_solver_step`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_run_configs tests.test_single_body_report_lane tests.test_experiment_runner`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/run_experiment.py --lane spinning_box_normal_constraint --config configs/experiments/single_body_spinning_box.yaml --matrix configs/experiments/paper_experiment_matrix.yaml --output reports/experiment_matrix/single_body_spinning_box_normal_constraint.json --source-commit ea33e90cd7613212aad4440b9dcf0ac758e07c61 --vendored-newton-commit 96713fa965463b69c229a4d30582c733ff3526bb`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_phase0_bootstrap`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/env/readiness_check.py`
- `PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"`
- `git diff --check`
