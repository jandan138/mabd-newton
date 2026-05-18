# Phase 60 Reproduction Gap Audit

## Status

passed_for_reproduction_gap_audit

## Scope

Phase 60 records the current distance from the requested A+B paper
reproduction in a machine-checkable audit. It does not add a solver path,
scene lane, baseline adapter, contact implementation, timing result, or paper
experiment pass.

The structured audit is:

- `docs/reference/reproduction-gap-audit.yaml`

## Repository

- branch: `phase60-reproduction-gap-audit`
- implementation commit: `f83889adbec6402e0baa1b4c55db5962a224808d`
- vendored Newton commit: `96713fa965463b69c229a4d30582c733ff3526bb`
- paper: `2603.08079v2`
- canonical Python:
  `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python`

## Audit Summary

- remaining_experiment_claims: `15`
- experiment_claims_passed: `0`
- full_reproduction_complete: `false`
- method_claims_passed: `19`
- No `experiment.*` claim is passed.

The audit covers every remaining `experiment.*` claim from
`docs/reference/paper-claims.yaml` and matches each claim to
`configs/experiments/paper_experiment_matrix.yaml`. For each claim it records
the matrix status, blocking reasons, matrix output report path, committed
report status when present, and the next evidence action.

## Remaining Claim Coverage

| Claim | Matrix status | Key blockers |
| --- | --- | --- |
| `experiment.single_body.rolling_spinning` | `blocked_by_baselines` | `rbd_baseline_adapter_missing`, `benchmark_protocol_not_recorded` |
| `experiment.single_body.spinning_box` | `blocked_by_baselines` | `mabd_newton_report_incomplete`, `spinning_box_comparison_report_incomplete` |
| `experiment.single_body.t_handle` | `planned` | `exact_t_handle_geometry_unknown`, `raw_t_handle_reference_curve_data_missing`, `mabd_newton_report_incomplete`, `t_handle_comparison_report_incomplete` |
| `experiment.single_body.heavy_top` | `planned` | `exact_heavy_top_inertia_unknown`, `exact_heavy_top_geometry_unknown`, `raw_heavy_top_reference_curve_data_missing`, `mabd_newton_report_incomplete`, `heavy_top_comparison_report_incomplete` |
| `experiment.single_body.physical_pendulum` | `planned` | `pendulum_geometry_unknown` |
| `experiment.joints.heavy_end_chain` | `blocked_by_baselines` | `external_baseline_adapters_missing`, `exact_chain_geometry_unknown` |
| `experiment.joints.ball_joint_nets` | `blocked_by_baselines` | `external_baseline_adapters_missing`, `contact_lane_missing` |
| `experiment.joints.pulley` | `blocked_by_baselines` | `external_baseline_adapters_missing`, `exact_pulley_drive_cycle_unknown` |
| `experiment.hierarchy.trees` | `blocked_by_assets` | `tree_geometry_and_skeleton_source_missing` |
| `experiment.cloak` | `blocked_by_assets` | `avatar_motion_and_cloak_asset_missing`, `contact_lane_missing`, `external_baseline_adapters_missing` |
| `experiment.armadillo_coupling` | `blocked_by_assets` | `armadillo_mesh_and_fem_discretization_missing`, `fem_coupling_lane_missing` |
| `experiment.ragdoll_on_net` | `planned` | `contact_lane_missing`, `table_text_timing_conflict_requires_separate_report` |
| `experiment.mixed_joints.falling` | `planned` | `contact_lane_missing` |
| `experiment.robot.franka` | `blocked_by_assets` | `franka_asset_and_motion_plan_missing`, `actuation_mapping_missing`, `contact_lane_missing` |
| `experiment.protein_chain` | `blocked_by_assets` | `exact_marker_sequence_missing`, `ik_keyframe_lane_missing` |

## Current Compact Report Evidence

The audit records the current sha256 for every committed compact report under
`reports/experiment_matrix/`. All listed reports remain `incomplete`; the
spinning-box RBD report records only a lane gate, not a paper experiment pass.

Representative hashes:

- `reports/experiment_matrix/single_body_spinning_box.json`:
  `fa487e5b2d5141d32e24764f52788d247ffe84a433e65196aae4a3b084b0f87c`
- `reports/experiment_matrix/single_body_spinning_box_rbd_baseline.json`:
  `64e7fda65ed0a25f2e9e2d4fbcbddaed1a75c7f0aba5aa56f79517db6e507836`
- `reports/experiment_matrix/single_body_t_handle_comparison.json`:
  `a3b0a8acb993d99d842027fab7c10a8df7deffd903d1507b2851fbcd35fd3766`
- `reports/experiment_matrix/single_body_heavy_top_comparison.json`:
  `b7b006f8a86cf7a259ac641395e1011e7a08e10db41e7a42137221e5c5e705d9`
- `reports/experiment_matrix/single_body_physical_pendulum_comparison.json`:
  `1c9f7ef97e45977beef9682c296130e23d51e537619a8d7fcd2da8ec10545875`

## Environment Boundary

The audit keeps the Newton environment isolated:

- `canonical_python`:
  `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python`
- `reference_python`:
  `/cpfs/user/zhuzihou/conda-managed/envs/physics-primitive-newton-py310/bin/python`
- `mutates_reference_environment`: `false`
- `uses_reference_python`: `false`
- `uses_ambient_python`: `false`

## Next Phase Recommendation

The next recommended technical slice is `phase61-spinning-box-contact-mabd-lane`
for `experiment.single_body.spinning_box`. The reason is practical: the scene
already has explicit paper values, a committed M-ABD diagnostic, a committed
RBD lane gate, and a comparison protocol. It is still blocked by an incomplete
Newton-only contact/MABD lane and incomplete comparison pass gate, so Phase 61
should address that gap before any claim pass is considered.

## Non-Claims

Phase 60 does not verify:

- a passed paper experiment;
- a solver fix;
- a contact or collision implementation;
- a comparative baseline result;
- a runtime timing result;
- rendered-output agreement;
- any `experiment.*` claim.

## Verification

Commands run with the isolated environment:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_phase0_bootstrap.Phase0BootstrapTests.test_phase60_reproduction_gap_audit_is_bounded
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"
git diff --check
```
