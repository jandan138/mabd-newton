# Phase 21 Spinning-Box Plane Placement Record

Date: 2026-05-17

## Status

passed

## Scope

Phase 21 fixes the configured single-body spinning-box M-ABD development
initial pose so the paper cube rests on the frictionless plane without initial
penetration. The affine block remains identity and the translation is
`[0.0, 0.05, 0.0]`, matching a cube of side length 0.1m above a plane with
normal `[0.0, 1.0, 0.0]` and offset 0.

This phase does not verify the paper spinning-box experiment, collision
detection, continuous collision detection, friction, implicit contact solve,
gravity, paper-faithful affine collision, paper-faithful implicit RBD baseline,
paper timing, rendered output, paper trajectory agreement, committed generated
report artifacts, or any passed `experiment.*` claim. The M-ABD report remains
`incomplete`.

## Config Path

- `configs/experiments/single_body_spinning_box.yaml`
- matrix: `configs/experiments/paper_experiment_matrix.yaml`

## Repository

- worktree:
  `/cpfs/user/zhuzihou/dev/mabd-newton/.worktrees/phase21-spinning-box-plane-placement`
- branch: `phase21-spinning-box-plane-placement`
- base commit: `5d696860b2dc43c727dac405ed20a578d66ebde5`
- plan commit: `d6c2265ea9f23b867cd88a0881f0275aa341c4da`
- implementation commit: `29a210d28446d2f5dd0fa816a35dde894aa7b639`
- docs/provenance commit: `630a60b18e85d6481944abadc743da28655dcc09`
- review hardening commit: `9c099e5788fb3d29f541f90eab45a877b2d7650b`
- independent review: physics/config/report review found no findings. Claim
  boundary/provenance review found the Phase 21 record did not list the final
  hardening commit and still said independent review was pending; this review
  disposition records the review result and the hardening commit.

## Vendored Newton

- vendored path: `vendor/newton`
- upstream commit: `96713fa965463b69c229a4d30582c733ff3526bb`
- local patch status: Phase 21 adds no vendored Newton source changes.

## Paper Source

- arXiv ID: `2603.08079`
- arXiv version: `v2`
- PDF SHA256:
  `a594e79093673c60fc59ad14f9b71f29a8f7f8e7b1c3d9c73efe6f5814cc6ec0`
- TeX source SHA256:
  `73ec398956c606dec2f8f40f0d38b9d5370e11b27830775e1b3765fe0efc563f`
- cited source lines: `experiment.tex:40-55`

## Environment

- Python: `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python`
- reference clone source:
  `/cpfs/user/zhuzihou/conda-managed/envs/physics-primitive-newton-py310`
- Backend: `cpu_numpy` for the M-ABD development report.
- readiness check:
  `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/env/readiness_check.py`
- readiness status: `smoke_passed` in the inherited Phase 20 main gate.
- non-pollution result: `mutates_reference_environment=false`,
  `uses_reference_python=false`, `uses_ambient_python=false`

## Metrics And Thresholds

- random seed: not applicable; the M-ABD CPU oracle lane and contact
  diagnostic snapshot are deterministic.
- initial affine block: identity
- initial translation: `[0.0, 0.05, 0.0]`
- initial_q[10] = 0.05
- contact surface type: `contact_surface_type = plane`
- cube side length: `0.1m`
- contact corner count: `contact_corner_count = 8`
- contact signed distances:
  `contact_corner_signed_distances_m = [0.0, 0.0, 0.1, 0.1, 0.0, 0.0, 0.1, 0.1]`
- contact_min_signed_distance_m = 0.0
- contact_max_penetration_m = 0.0
- contact_active_count = 0
- contact_total_normal_force_n = [0.0, 0.0, 0.0]
- contact_total_generalized_force = [0.0] * 12
- generated M-ABD reports remain `incomplete` because the paper comparison
  lanes, contact solve, and benchmark evidence are still incomplete.

## Artifacts

- committed config:
  `configs/experiments/single_body_spinning_box.yaml`
- committed tests: `tests/test_experiment_run_configs.py`,
  `tests/test_single_body_report_lane.py`, `tests/test_phase0_bootstrap.py`
- docs validator: `scripts/validate_docs.py`
- generated reports: not committed; tests write JSON reports to temporary
  directories only
- No `experiment.*` claim is passed in this phase.

## TDD Evidence

RED result:

```text
config/report tests:
  Ran 10 tests
  FAILED (failures=2)
  config.initial_q[10] was 0.0 instead of 0.05
  diagnostics.active_contact_count was 4 instead of 0

phase bootstrap docs tests:
  missing claim boundary bullet: This repository contains Phase 21
  record file missing:
    docs/records/2026-05-17-phase21-spinning-box-plane-placement.md
  validator output still ended at Phase 20
```

GREEN result:

```text
config/report tests: Ran 10 tests, OK
phase bootstrap docs tests: Ran 37 tests, OK
docs validator: Phase 0/1/2/3/4/5/6/7/8/9/10/11/12/13/14/15/16/17/18/19/20/21 docs/provenance validation passed
```

## Claim Impact

No `experiment.*` claim is passed in this phase.
