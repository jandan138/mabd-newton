# 2026-05-17 Phase 38 Constrained Rotated KKT

## Status

passed

## Config Path

- `configs/experiments/single_body_physical_pendulum.yaml`
- `configs/experiments/paper_experiment_matrix.yaml`

## Repository

- base commit: `328c217`
- plan commit: `ec4ebb5`
- implementation commit: `0b93ee1`
- branch: `phase38-constrained-rotated-kkt`
- plan:
  `docs/superpowers/plans/2026-05-17-mabd-phase38-constrained-rotated-kkt.md`
- spec:
  `docs/superpowers/specs/2026-05-17-phase38-constrained-rotated-kkt-design.md`

## Vendored Newton

- source commit: `96713fa965463b69c229a4d30582c733ff3526bb`
- local patch status: Phase 38 modifies vendored Newton locally for bounded
  dense constrained polar CPU KKT support.

## Environment

- project environment: `mabd-newton-py310`
- reference environment: `physics-primitive-newton-py310`
- readiness status: `smoke_passed`
- mutates_reference_environment=false
- uses_reference_python=false
- uses_ambient_python=false

## Solver Evidence

- implementation: `vendor/newton/newton/_src/solvers/mabd/step_oracle.py`
- dense constrained polar increment map:
  `np.kron(np.eye(4), polar_rotation(A))`
- dense KKT gradients use `J_world @ increment_map`.
- solved local increments are mapped back to world affine increments before
  state updates.
- constrained `no_polar` remains unsupported because the current no-polar
  normalization increment is nonlinear.
- rotated non-dense topology paths require `topology='dense'`.
- RED/GREEN test:
  `test_constrained_cpu_step_supports_polar_world_anchor`
- rejection tests:
  `test_constrained_cpu_step_rejects_no_polar_because_map_is_nonlinear`
  and `test_constrained_cpu_step_rejects_polar_non_dense_topology_until_tested`
- vendored Newton mirror tests:
  `newton.tests.test_mabd_phase4_solver_step`

## Physical Pendulum Evidence

- `mabd_newton.rotation_mode = polar`
- writer: `write_physical_pendulum_mabd_newton_report`
- runner: `run_physical_pendulum_mabd_newton`
- CLI: `--lane physical_pendulum_mabd_newton`
- solver mode: `mabd_cpu_oracle_physical_pendulum_newton_lane`
- backend: `cpu_numpy_newton_only`
- baseline lane: `mabd_newton`
- top-level report status: `incomplete`
- lane_status: `incomplete_diagnostic_generated`
- mabd_rotation_mode = `polar`
- report:
  `reports/experiment_matrix/single_body_physical_pendulum_mabd_newton.json`
- report source_commit: `0b93ee1`

## Regenerated Comparison Evidence

- writer: `write_physical_pendulum_comparison_report`
- runner: `run_physical_pendulum_comparison`
- CLI: `--lane physical_pendulum_comparison`
- solver mode: `physical_pendulum_multilane_comparison_development`
- backend: `report_protocol`
- baseline lane: `physical_pendulum_comparison_protocol`
- comparison report:
  `reports/experiment_matrix/single_body_physical_pendulum_comparison.json`
- comparison report source_commit: `0b93ee1`
- input report provenance lanes: `analytic_reference`, `mabd_newton`,
  `rbd_implicit_baseline`
- missing_required_lanes = `[]`
- missing_paper_metrics = [`joint_force_error:paper_waveform_agreement`]
- blocking_reasons include `joint_force_waveform_agreement_missing`,
  `pendulum_geometry_unknown`, `paper_timing_missing`, and
  `physical_pendulum_comparison_pass_gate_not_enabled`
- paper_metric_statuses.phase_drift.status = `diagnostic_available`
- paper_metric_statuses.joint_force_error.status =
  `diagnostic_reaction_not_paper_waveform`

## Metrics And Thresholds

- random seed: not applicable deterministic report protocol
- max_abs_angle_error_rad = `0.007130697850638079`
- max_phase_drift_rad = `0.007130697850638079`
- max_world_anchor_reaction_magnitude_n = `0.009810000000011114`
- matched_sample_count = `5`
- max_mabd_rbd_abs_angle_delta_rad = `0.0006717899335178523`
- threshold status: diagnostic thresholds are satisfied, but no full
  experiment pass gate is enabled.

## Claim Impact

- No `experiment.*` claim is passed.
- `experiment.single_body.physical_pendulum` remains intended.
- Dense constrained polar CPU KKT support exists only for the bounded CPU
  oracle path covered by Phase 38 tests.
- Constrained `no_polar` KKT remains explicitly unsupported.
- Rotated non-dense topology KKT remains explicitly unsupported.
- Joint-force waveform agreement remains missing.
- Paper-faithful pendulum geometry remains missing.
- `pendulum_geometry_unknown` remains a blocker.
- paper timing remains missing.

## Verification Commands

- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_mabd_phase4_solver_step tests.test_experiment_run_configs tests.test_physical_pendulum_mabd tests.test_experiment_runner`
- `PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest newton.tests.test_mabd_phase4_solver_step`
- `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check src/mabd_reproduction/experiment_configs.py src/mabd_reproduction/physical_pendulum_mabd.py src/mabd_reproduction/physical_pendulum_reports.py tests/test_experiment_run_configs.py tests/test_physical_pendulum_mabd.py tests/test_experiment_runner.py tests/test_mabd_phase4_solver_step.py vendor/newton/newton/_src/solvers/mabd/step_oracle.py vendor/newton/newton/tests/test_mabd_phase4_solver_step.py`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/env/readiness_check.py`
- `PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"`
- `git diff --check`
