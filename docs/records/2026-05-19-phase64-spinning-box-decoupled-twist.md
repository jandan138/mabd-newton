# Phase 64 Spinning-Box Decoupled Twist Diagnostic

## Status

passed_for_spinning_box_decoupled_twist_diagnostic_slice

## Scope

- branch: `phase64-spinning-box-velocity-semantics`
- implementation commit:
  `8c00873c9e85ca8a85d518f02f7bbf415f946d91`
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

Phase 64 adds a separate spinning-box diagnostic lane that reconstructs the
paper horizon from a decoupled spatial twist and an SO(3) exponential rigid
update:

- report lane: `spinning_box_decoupled_twist`
- solver mode: `decoupled_twist_rigid_reconstruction_diagnostic`
- backend: `cpu_numpy`
- status: `incomplete`
- velocity semantics policy:
  `decoupled_spatial_twist_with_exponential_rigid_update`
- velocity semantics scope: `diagnostic_only_no_lane_gate`
- solver step policy: `no_solver_step_rigid_reconstruction_diagnostic`
- solver residual status: `not_evaluated_no_kkt_solve`
- blocker recorded: `spinning_box_decoupled_twist_not_paper_faithful`
- blocker retained: `mabd_kinematic_feasibility_blocker_recorded`
- threshold_violations = `[]`
- shape_thresholds_met_by_decoupled_twist = `true`
- energy_thresholds_met_by_decoupled_twist = `true`
- max_velocity_state_inconsistency_norm = `85328.56614876063`
- max_finite_difference_twist_error = `60304.81062110217`
- max_contact_penetration_m = `0.0`

## Artifacts

- `reports/experiment_matrix/single_body_spinning_box_decoupled_twist.json`
  - sha256:
    `748e83d4f670222a861c9eb1c38d3c1a21469d046c9be60ee7b0609a8e84242d`

## Result Boundary

No `experiment.*` claim is passed. This diagnostic does not pass the
spinning-box experiment, does not pass the M-ABD lane, does not prove paper
velocity semantics, does not perform a paper-faithful M-ABD solve, does not
implement a contact solver, does not verify paper-faithful affine collision,
does not enable a comparison pass gate, does not provide rendered-output
evidence, does not provide runtime-performance evidence, and does not
establish full paper reproduction.

The positive finite-difference inconsistency metrics record the gap between
this decoupled twist reconstruction and the existing `qd_next=(q_next-q_n)/h`
state relation. They are diagnostic evidence only.

This record does not prove paper velocity semantics.

## Verification Commands

- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_rigid_baselines`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_run_configs tests.test_single_body_report_lane tests.test_experiment_runner`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check src/mabd_reproduction/single_body_reports.py src/mabd_reproduction/experiment_configs.py src/mabd_reproduction/experiment_runner.py scripts/run_experiment.py tests/test_experiment_run_configs.py tests/test_single_body_report_lane.py tests/test_experiment_runner.py`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/run_experiment.py --lane spinning_box_decoupled_twist --config configs/experiments/single_body_spinning_box.yaml --matrix configs/experiments/paper_experiment_matrix.yaml --output reports/experiment_matrix/single_body_spinning_box_decoupled_twist.json --source-commit 8c00873c9e85ca8a85d518f02f7bbf415f946d91 --vendored-newton-commit 96713fa965463b69c229a4d30582c733ff3526bb`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_phase0_bootstrap`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/env/readiness_check.py`
- `PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"`
- `git diff --check`
