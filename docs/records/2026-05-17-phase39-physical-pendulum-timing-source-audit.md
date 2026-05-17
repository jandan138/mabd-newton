# Phase 39 Physical Pendulum Timing Source Audit

## Status

passed

## Config Path

- `configs/experiments/single_body_physical_pendulum.yaml`
- `configs/experiments/paper_experiment_matrix.yaml`

## Repository

- branch: `phase39-physical-pendulum-timing`
- implementation commit: `d1985dc`
- spec: `docs/superpowers/specs/2026-05-17-phase39-physical-pendulum-timing-source-audit-design.md`
- plan: `docs/superpowers/plans/2026-05-17-mabd-phase39-physical-pendulum-timing-source-audit.md`

## Vendored Newton

- source commit: `96713fa965463b69c229a4d30582c733ff3526bb`
- local patch status: Phase 39 does not modify vendored Newton.

## Environment

- Python: `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python`
- reference environment: `/cpfs/user/zhuzihou/conda-managed/envs/physics-primitive-newton-py310`
- `mutates_reference_environment=false`
- `uses_reference_python=false`
- `uses_ambient_python=false`

## Paper Source Audit

- source lines: `/tmp/mabd-paper/source/sections/experiment.tex:77-91`
- source version: `2603.08079v2`
- audit status: `not_a_physical_pendulum_paper_metric`
- runtime_timing_claim_present = `false`
- required_metric = `false`
- finding: the cited physical-pendulum source lines specify angle trajectory, joint-force waveform behavior, phase drift, horizontal release, zero initial velocity, gravity, and an elliptic reference, but no runtime timing or performance value.

## Report Evidence

- `paper_timing_source_audit` is recorded in expected and observed payloads for:
  - `reports/experiment_matrix/single_body_physical_pendulum_analytic_reference.json`
  - `reports/experiment_matrix/single_body_physical_pendulum_mabd_development.json`
  - `reports/experiment_matrix/single_body_physical_pendulum_mabd_newton.json`
  - `reports/experiment_matrix/single_body_physical_pendulum_rbd_baseline.json`
  - `reports/experiment_matrix/single_body_physical_pendulum_comparison.json`
- report source_commit: `d1985dc`
- comparison report source_commit: `d1985dc`
- removed blocker: `paper_timing_missing`
- retained blocker: `joint_force_waveform_agreement_missing`
- retained blocker: `pendulum_geometry_unknown`
- retained blocker: `physical_pendulum_comparison_pass_gate_not_enabled`
- missing_paper_metrics = [`joint_force_error:paper_waveform_agreement`]
- matched_sample_count = `5`
- max_mabd_rbd_abs_angle_delta_rad = `0.0006717899335178523`
- top-level report status: `incomplete`
- timing_distribution.scope = `not_timed`

## Claim Impact

- No `experiment.*` claim is passed.
- `experiment.single_body.physical_pendulum` remains intended.
- Joint-force waveform agreement remains missing.
- Paper-faithful pendulum geometry remains missing.
- Physical-pendulum comparison pass gate remains disabled.
- This record is a source-audit correction only and is not runtime performance reproduction.

## Verification Commands

- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_runner`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_phase0_bootstrap`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py`
- `git diff --check`
