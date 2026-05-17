# Phase 20 Spinning-Box Contact Diagnostics Record

Date: 2026-05-17

## Status

passed

## Scope

Phase 20 adds a bounded contact-diagnostics lane for the single-body
spinning-box M-ABD development report. It parses configured frictionless plane
metadata, derives the eight paper-sized cube corners procedurally, evaluates
the existing point-plane normal penalty contact oracle at the configured
initial state, and records finite contact diagnostic fields in the M-ABD
development report.

This phase does not verify the paper spinning-box experiment, collision
detection, continuous collision detection, friction, implicit contact solve,
paper-faithful affine collision, paper-faithful implicit RBD baseline, paper
timing, rendered output, paper trajectory agreement, committed generated
report artifacts, or any passed `experiment.*` claim. The M-ABD report remains
`incomplete`.

## Config Path

- `configs/experiments/single_body_spinning_box.yaml`
- matrix: `configs/experiments/paper_experiment_matrix.yaml`

## Repository

- worktree:
  `/cpfs/user/zhuzihou/dev/mabd-newton/.worktrees/phase20-spinning-box-contact-diagnostics`
- branch: `phase20-spinning-box-contact-diagnostics`
- base commit: `06d28e8`
- plan commit: `773a0ef60c4357a3083e30918c915f08a6eb1e88`
- config commit: `d10ca0176cd678d76ed9a0c6d48339d4bdcdcf22`
- implementation commit: `6bc889a6f7f9d2c19d9a487e37b9f9286ff4cf03`
- report commit: `f4b5212cdf5543021dcf7d7a3b29731f237773c2`
- docs/provenance commit: `b24eb15a15f47fd6a0a024eebd1b815fd474c505`
- review hardening commit: `f5fe643200a510368a240459d598289ff6e499ba`
- independent review: code/physics/report review found no findings. Claim
  boundary/provenance review found committed Phase 20 plan/spec EOF whitespace
  failures under `git diff --check 06d28e8e..HEAD` and weak document-wide
  Phase 20 non-claim substring checks; the review hardening commit fixes both.

## Vendored Newton

- vendored path: `vendor/newton`
- upstream commit: `96713fa965463b69c229a4d30582c733ff3526bb`
- local patch status: Phase 20 adds no vendored Newton source changes.

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
- readiness status: `smoke_passed`
- non-pollution result: `mutates_reference_environment=false`,
  `uses_reference_python=false`, `uses_ambient_python=false`

## Metrics And Thresholds

- random seed: not applicable; the M-ABD CPU oracle lane and contact
  diagnostic snapshot are deterministic.
- config field: `contact_surface`
- contact surface type: `contact_surface_type = plane`
- contact evaluation state: `initial_configured_q_qd`
- cube corner count: `contact_corner_count = 8`
- active contact count at the configured initial state:
  `contact_active_count = 4`
- signed distance field: `contact_corner_signed_distances_m`
- minimum signed distance at the configured initial state:
  `contact_min_signed_distance_m = -0.05`
- maximum penetration at the configured initial state:
  `contact_max_penetration_m = 0.05`
- total normal force field: `contact_total_normal_force_n`
- total generalized force field: `contact_total_generalized_force`
- oracle helper:
  `mabd.evaluate_point_plane_penalty_contact`
- generated M-ABD reports remain `incomplete` because the paper comparison
  lanes, contact solve, and benchmark evidence are still incomplete.

## Artifacts

- committed config:
  `configs/experiments/single_body_spinning_box.yaml`
- committed config parser:
  `src/mabd_reproduction/experiment_configs.py`
- committed shared physics helpers:
  `src/mabd_reproduction/spinning_box_physics.py`
- committed helper APIs: `spinning_box_cube_corners`,
  `spinning_box_contact_diagnostics`
- committed M-ABD report writer:
  `src/mabd_reproduction/single_body_reports.py`
- committed tests: `tests/test_experiment_run_configs.py`,
  `tests/test_single_body_report_lane.py`, `tests/test_phase0_bootstrap.py`
- docs validator: `scripts/validate_docs.py`
- generated reports: not committed; tests write JSON reports to temporary
  directories only
- No `experiment.*` claim is passed in this phase.

## TDD Evidence

RED result:

```text
config tests:
  AttributeError: 'SpinningBoxRunConfig' object has no attribute 'contact_surface'
helper tests:
  ImportError: cannot import name 'spinning_box_contact_diagnostics'
report tests:
  KeyError: 'contact_surface_type'
docs tests:
  Phase 20 boundary text missing
  Phase 20 record file missing
  validator output still ended at Phase 19
```

GREEN result:

```text
config tests: Ran 8 tests, OK
single-body report tests: Ran 2 tests, OK
phase bootstrap docs tests: Ran 35 tests, OK
docs validator: Phase 0/1/2/3/4/5/6/7/8/9/10/11/12/13/14/15/16/17/18/19/20 docs/provenance validation passed
ruff docs/code slice: All checks passed!
```

## Claim Impact

No `experiment.*` claim is passed in this phase.
