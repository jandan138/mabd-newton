# Phase 22 RBD Plane Placement Record

Date: 2026-05-17

## Status

passed

## Scope

Phase 22 aligns the Newton `rbd_implicit_baseline` development lane with the
configured spinning-box initial translation. The RBD body is initialized from
`config.initial_q[9:12]`, so it starts at `initial_position_m = [0.0, 0.05,
0.0]` instead of the origin. After four 10 ms free-body steps at the paper
linear velocity of 100 m/s, the RBD lane reports `final_position_m = [4.0,
0.05, 0.0]` up to float32 storage precision.

This phase does not verify the paper spinning-box experiment,
paper-faithful implicit RBD baseline, paper-faithful affine collision,
collision detection, continuous collision detection, friction, implicit contact
solve, gravity, rendered output, paper timing, paper trajectory agreement,
committed generated report artifacts, or any passed `experiment.*` claim. The
RBD report remains `incomplete`.

## Config Path

- `configs/experiments/single_body_spinning_box.yaml`
- matrix: `configs/experiments/paper_experiment_matrix.yaml`

## Repository

- worktree:
  `/cpfs/user/zhuzihou/dev/mabd-newton/.worktrees/phase22-rbd-plane-placement`
- branch: `phase22-rbd-plane-placement`
- base commit: `cdb1f46c427ad7bea6e223efce515f4895498882`
- plan commit: `50816b9ba11c80e9993d067bfbbdcc579e2c5fa3`
- implementation commit: `c7a22b1a0fb400da47c2a715b9ac32333aed67d2`
- docs/provenance commit: pending until this record is committed
- independent review: pending

## Vendored Newton

- vendored path: `vendor/newton`
- upstream commit: `96713fa965463b69c229a4d30582c733ff3526bb`
- local patch status: Phase 22 adds no vendored Newton source changes.

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
- readiness check:
  `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/env/readiness_check.py`
- readiness status: `smoke_passed`
- clone drift check: `pip freeze` differs from
  `physics-primitive-newton-py310` only by the editable project line,
  `primitive_collision_compiler` versus `mabd_newton`.
- non-pollution result: `mutates_reference_environment=false`,
  `uses_reference_python=false`, `uses_ambient_python=false`

## Metrics And Thresholds

- random seed: not applicable; the RBD free-body lane is deterministic.
- baseline lane: `rbd_implicit_baseline`
- solver mode in report: `newton_semimplicit_rbd_cpu_development`
- backend in report: `cpu_newton_warp`
- solver name: `newton.solvers.SolverSemiImplicit`
- Newton step count: `4`
- time step: `0.01s`
- initial_position_m = [0.0, 0.05, 0.0]
- final_position_m = [4.0, 0.05, 0.0]
- final_position_m raw y from Warp float32 snapshot:
  `0.05000000074505806`
- report status: `incomplete`
- no passed `experiment.*` claim is created in this phase.

## Artifacts

- committed code: `src/mabd_reproduction/rigid_baselines.py`
- committed tests: `tests/test_rigid_baselines.py`,
  `tests/test_phase0_bootstrap.py`
- docs validator: `scripts/validate_docs.py`
- generated reports: not committed; tests write JSON reports to temporary
  directories only
- No `experiment.*` claim is passed in this phase.

## TDD Evidence

RBD code RED result:

```text
AttributeError: 'SpinningBoxRBDBaselineResult' object has no attribute 'initial_position_m'
KeyError: 'initial_position_m'
```

RBD GREEN result:

```text
RBD tests: Ran 5 tests, OK
ruff: All checks passed!
git diff --check: exit 0
```

Docs RED result:

```text
missing claim boundary bullet: This repository contains Phase 22
record file missing:
  docs/records/2026-05-17-phase22-rbd-plane-placement.md
validator output still ended at Phase 21
```

Expected docs GREEN evidence for this record:

```text
phase bootstrap docs tests: Ran 39 tests, OK
docs validator: Phase 0/1/2/3/4/5/6/7/8/9/10/11/12/13/14/15/16/17/18/19/20/21/22 docs/provenance validation passed
```

## Claim Impact

No `experiment.*` claim is passed in this phase.
