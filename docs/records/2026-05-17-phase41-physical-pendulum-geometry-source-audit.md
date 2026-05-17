# Phase 41 Physical Pendulum Geometry Source Audit

Date: 2026-05-17

## Status

passed

## Repository

- branch: `phase41-physical-pendulum-geometry-source-audit`
- implementation commit: `cdceafe`
- plan: `docs/superpowers/plans/2026-05-17-mabd-phase41-physical-pendulum-geometry-source-audit.md`
- spec: `docs/superpowers/specs/2026-05-17-phase41-physical-pendulum-geometry-source-audit-design.md`

## Paper Source Audit

- audit helper: `physical_pendulum_geometry_source_audit`
- source root: `/tmp/mabd-paper/source`
- status: `source_assets_found_geometry_parameters_missing`
- `sections/experiment.tex` sha256:
  `c5927183fe4e3f1c1c1617e5b10b7e9006da6a9eac537e891cb1dac03d58dd0f`
- `images/simple_pendulum/simple_pendulum.pdf` sha256:
  `4b198ace42ff08d32dc266f1eca710987a2b6335d75878ee01b60498fed945cf`
- source_tree_path_count = `37`
- scanned_text_path_count = `12`
- scanned_tex_path_count = `8`
- scanned_tex_paths include `sections/experiment.tex` and `sections_a/multiabd.tex`
- embedded figure metadata includes `pendulum15.png`
- absence_findings.physical_pendulum_geometry_parameter_search.status =
  `no_paper_faithful_physical_pendulum_geometry_parameters_found`
- usable parameter disclosures = `[]`
- missing parameters include `body_geometry`, `mass_distribution`,
  `inertia_tensor`, and `raw_joint_force_curve_data`
- blocker: `physical_pendulum_geometry_parameters_missing_from_public_source_assets`
- blocker: `raw_physical_pendulum_curve_data_missing_from_public_source_assets`
- blocker: `physical_pendulum_private_author_assets_not_audited`

## Positive Source Facts

The audit records positive findings from `/tmp/mabd-paper/source/sections/experiment.tex:77-91`:

- `fixed_pivot`
- `horizontal_release_zero_initial_velocity`
- `elliptic_angle_reference`
- `joint_force_magnitude_plot`
- `phase_drift`
- `abd_rbd_comparison`

## Report And Config Boundaries

- retained blocker: `pendulum_geometry_unknown`
- retained comparison blocker: `physical_pendulum_comparison_pass_gate_not_enabled`
- missing_paper_metrics = [`joint_force_error:paper_geometry_unknown`]
- physical-pendulum analytic, M-ABD development, M-ABD Newton, RBD baseline,
  and comparison reports remain `incomplete`
- every current physical-pendulum report has `full_experiment_claim_passed = false`

## Claim Impact

No `experiment.*` claim is passed.
`experiment.single_body.physical_pendulum` remains intended.
This audit records public source availability and missing-parameter evidence. It
does not reconstruct paper-faithful physical-pendulum geometry, raw curves,
rendered output, paper timing, runtime performance, or full experiment results.

## Verification Commands

- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_physical_pendulum_source_audit tests.test_phase0_bootstrap`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py`
- `PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"`
- `git diff --check`
