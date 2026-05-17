# Phase 40 Physical Pendulum Joint-Force Reference

## Status

passed

## Config Path

- `configs/experiments/single_body_physical_pendulum.yaml`
- `configs/experiments/paper_experiment_matrix.yaml`

## Repository

- branch: `phase40-physical-pendulum-joint-force-reference`
- implementation commit: `1937d40`
- spec: `docs/superpowers/specs/2026-05-17-phase40-physical-pendulum-joint-force-reference-design.md`
- plan: `docs/superpowers/plans/2026-05-17-mabd-phase40-physical-pendulum-joint-force-reference.md`

## Vendored Newton

- source commit: `96713fa965463b69c229a4d30582c733ff3526bb`
- local patch status: Phase 40 does not modify vendored Newton.

## Environment

- Python: `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python`
- reference environment: `/cpfs/user/zhuzihou/conda-managed/envs/physics-primitive-newton-py310`
- `mutates_reference_environment=false`
- `uses_reference_python=false`
- `uses_ambient_python=false`

## Paper Source

- source lines: `/tmp/mabd-paper/source/sections/experiment.tex:77-91`
- source version: `2603.08079v2`
- scoped gap addressed: the paper source states that joint-force magnitude is
  plotted and should better match the reference as the timestep decreases.

## Scalar Joint-Force Reference Evidence

- `physical_pendulum_angular_velocity_reference` computes the analytic
  derivative of the elliptic angle reference.
- `physical_pendulum_joint_force_reference` computes the scalar radial reaction
  diagnostic for the configured procedural pendulum.
- analytic report field: `joint_force_samples_n`
- analytic reference model: `scalar_point_pendulum_radial_reaction`
- analytic max_joint_force_magnitude_n = `29.43`
- first analytic joint_force_samples_n value is `0.0`

## Lane Report Evidence

- report source_commit: `1937d40`
- `reports/experiment_matrix/single_body_physical_pendulum_mabd_newton.json`
- `reports/experiment_matrix/single_body_physical_pendulum_rbd_baseline.json`
- MABD max_abs_joint_force_error_n = `3.674027173124528`
- RBD max_abs_joint_force_error_n = `0.07322754047186475`
- per-sample field: `reference_joint_force_magnitude_n`
- per-sample field: `abs_joint_force_error_n`
- removed blocker: `joint_force_waveform_agreement_missing`
- retained blocker: `pendulum_geometry_unknown`
- top-level report status: `incomplete`

## Comparison Evidence

- `reports/experiment_matrix/single_body_physical_pendulum_comparison.json`
- comparison report source_commit: `1937d40`
- `joint_force_waveform_diagnostics`
- missing_paper_metrics = [`joint_force_error:paper_geometry_unknown`]
- paper_metric_statuses.joint_force_error.status =
  `diagnostic_scalar_reference_not_paper_geometry`
- matched_sample_count = `5`
- joint_force_waveform_diagnostics.matched_sample_count = `5`
- max_mabd_abs_joint_force_error_n = `3.674027173124528`
- max_rbd_abs_joint_force_error_n = `0.07322754047186475`
- retained blocker: `physical_pendulum_comparison_pass_gate_not_enabled`

## Claim Impact

- No `experiment.*` claim is passed.
- `experiment.single_body.physical_pendulum` remains intended.
- This is a scalar/procedural diagnostic, not paper geometry.
- Paper-faithful physical-pendulum geometry remains missing.
- The paper joint-force waveform is not reconstructed.
- Physical-pendulum comparison pass gate remains disabled.

## Verification Commands

- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_physical_pendulum_reference tests.test_physical_pendulum_rbd tests.test_physical_pendulum_mabd tests.test_experiment_runner`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests`
- `git diff --check`
