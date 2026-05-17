# Phase 18 Spinning-Box M-ABD Physical Mass Record

Date: 2026-05-17

## Status

passed

## Scope

Phase 18 replaces the M-ABD single-body spinning-box development lane's
synthetic identity mass diagonal with the paper uniform centered cube's
continuous affine mass diagonal. It also reports physical mass and
kinetic-energy diagnostics from that diagonal: `mass_kg`,
`mabd_mass_diagonal`, `mass_diagonal_source`, `initial_energy_j`,
`final_energy_j`, and `relative_energy_drift`.

This phase does not verify the paper spinning-box experiment, paper-faithful
implicit RBD baseline, paper-faithful affine collision, paper timing, rendered
output, paper trajectory agreement, committed generated report artifacts, or
any passed `experiment.*` claim. The M-ABD report and comparison protocol
remain `incomplete`.

## Config Path

- `configs/experiments/single_body_spinning_box.yaml`
- matrix: `configs/experiments/paper_experiment_matrix.yaml`

## Repository

- worktree:
  `/cpfs/user/zhuzihou/dev/mabd-newton/.worktrees/phase18-spinning-box-mabd-physical-mass`
- branch: `phase18-spinning-box-mabd-physical-mass`
- base commit: `c762c9a`
- plan commit: `5f8c3de029f20b157b9a50d624223d05e21a7720`
- implementation commit: `c7710f0f3ab6656a41968b3fe230e274d5f77f8b`
- docs/provenance commit: `632946ffa567ef7cac15868b92b8a5db936ec739`
- review hardening commit: `054d454caa55c10b9094a536ef4d0dd10047b041`
- independent review: claim/spec review found missing review-hardening
  provenance and expected-vs-observed wording in this record; code/physics
  review found no findings.

## Vendored Newton

- vendored path: `vendor/newton`
- upstream commit: `96713fa965463b69c229a4d30582c733ff3526bb`
- local patch status: Phase 18 adds no vendored Newton source changes.

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
- Backend: `cpu_numpy` for the M-ABD development report and
  `report_protocol` for the comparison report.
- readiness check:
  `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/env/readiness_check.py`
- readiness status: `smoke_passed`
- non-pollution result: `mutates_reference_environment=false`,
  `uses_reference_python=false`, `uses_ambient_python=false`

## Metrics And Thresholds

- random seed: not applicable; the M-ABD CPU oracle lane is deterministic.
- paper cube side length: `0.1 m`
- paper cube density: `1E3 kg/m^3`
- derived mass: `1.0 kg`
- affine second moment: `m*s^2/12 = 1/1200 kg m^2`
- Newton M-ABD q packing: `[A[:,0], A[:,1], A[:,2], t]`
- mass_diagonal = [1/1200] * 9 + [1.0] * 3
- mass source field:
  `mass_diagonal_source = paper_uniform_centered_cube_continuous`
- paper generalized velocity remains:
  `[0, 0, -60000, 0, 0, 0, 60000, 0, 0, 100, 0, 0]`
- initial_energy_j = 3005000.0
- `relative_energy_drift <= 1.0e-15` in the deterministic zero-force
  development lane.
- existing comparison blocker remains:
  `spinning_box_comparison_report_incomplete`
- generated M-ABD reports remain `incomplete` because the paper comparison
  lanes and benchmark evidence are still incomplete.

## Artifacts

- committed shared physics helper:
  `src/mabd_reproduction/spinning_box_physics.py`
- helper API: `spinning_box_mabd_mass_diagonal`
- committed config:
  `configs/experiments/single_body_spinning_box.yaml`
- committed M-ABD report writer:
  `write_spinning_box_development_report`
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
  ImportError for missing `spinning_box_mabd_mass_diagonal`
  KeyError for missing report `mass_diagonal_source`
docs tests:
  Phase 18 boundary text missing
  Phase 18 record file missing
```

GREEN result:

```text
config/report tests: Ran 10 tests, OK
phase bootstrap docs tests: Ran 31 tests, OK
docs validator: Phase 0/1/2/3/4/5/6/7/8/9/10/11/12/13/14/15/16/17/18 docs/provenance validation passed
ruff docs/code slice: All checks passed!
```

## Claim Impact

No `experiment.*` claim is passed in this phase.
