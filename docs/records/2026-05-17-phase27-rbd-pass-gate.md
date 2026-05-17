# Phase 27 RBD Pass Gate Record

Date: 2026-05-17

## Status

passed

## Scope

Phase 27 adds a bounded required-lane gate for the single-body spinning-box
`rbd_implicit_baseline`. The RBD lane report remains a top-level
`experiment.single_body.spinning_box` report with `status=incomplete`; it uses
`observed["lane_gate_status"] = "passed"` and a `lane_pass_gate` payload to
record that only the required RBD lane has met its narrow conservation and
closed-form trajectory checks.

This phase does not pass the paper spinning-box experiment, the M-ABD lane, or
the spinning-box comparison. It does not implement paper-faithful affine
collision, collision detection, implicit contact solve, gravity, rendered
agreement, timing, external baselines, or any passed `experiment.*` claim.

## Config Path

- `configs/experiments/single_body_spinning_box.yaml`
- `configs/experiments/paper_experiment_matrix.yaml`

## Repository

- worktree:
  `/cpfs/user/zhuzihou/dev/mabd-newton/.worktrees/phase27-rbd-pass-gate`
- branch: `phase27-rbd-pass-gate`
- base commit: `b371dd13de321b98cc56b09e416715b5c61b42c7`
- plan commit: `423313d`
- design hardening commit: `55d23c8`
- report gate validation commit: `28a6d1e`
- paper RBD baseline commit: `d2c4c51`
- runner/comparison commit: `84dceb5`
- docs/record commit: `b8e9b8e`
- independent review: claim/provenance review required that top-level
  experiment reports must remain incomplete and that the record include config
  path, repo commit, vendored Newton provenance, paper source version, backend,
  seed policy, raw artifacts, and explicit non-claims. Numerics/comparison
  review required the lane gate to be bound to claim id, lane, solver mode,
  backend, strict thresholds, exact quaternion samples, and comparison blocker
  semantics.
- review disposition: top-level experiment reports must remain incomplete.

## Vendored Newton

- vendored path: `vendor/newton`
- upstream commit: `96713fa965463b69c229a4d30582c733ff3526bb`
- local patch status: Phase 27 does not modify vendored Newton.

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
- readiness status: `smoke_passed`
- readiness JSON output: branch-gate stdout, not committed.
- non-pollution result: `mutates_reference_environment=false`,
  `uses_reference_python=false`, `uses_ambient_python=false`

## Metrics And Diagnostics

- random seed: not applicable; the closed-form RBD lane is deterministic.
- baseline_lane = rbd_implicit_baseline
- solver_mode = paper_faithful_implicit_rbd
- backend = cpu_numpy_newton_only
- lane_gate_status = passed
- report status: `incomplete`
- full_experiment_claim_passed = false
- gate_version = required_lane_v1
- scope = required_lane_only
- step count: `4`
- time step: `0.01s`
- initial_position_m = `[0.0, 0.05, 0.0]`
- final_position_m = `[4.0, 0.05, 0.0]`
- final_rotation_xyzw = [0.0, -0.08827860647172615, 0.0, 0.9960958225188027]
- linear_momentum_error <= 1.0e-12
- angular_momentum_error <= 1.0e-12
- energy_drift <= 1.0e-12
- relative_energy_drift <= 1.0e-12
- comparison blocker retained: `mabd_newton_report_incomplete`
- comparison blocker retained: `spinning_box_comparison_pass_gate_not_enabled`
- comparison blocker removed: `rbd_implicit_baseline_report_incomplete`
- matrix blocker retained: `spinning_box_comparison_report_incomplete`
- matrix blocker retained: `mabd_newton_report_incomplete`
- No `experiment.*` claim is passed in this phase.

## Artifacts

- committed project code:
  `src/mabd_reproduction/reporting.py`,
  `src/mabd_reproduction/rigid_baselines.py`,
  `src/mabd_reproduction/experiment_runner.py`,
  `src/mabd_reproduction/comparison_reports.py`,
  `src/mabd_reproduction/experiment_configs.py`
- committed configs:
  `configs/experiments/single_body_spinning_box.yaml`,
  `configs/experiments/paper_experiment_matrix.yaml`
- committed tests:
  `tests/test_reporting_contracts.py`,
  `tests/test_rigid_baselines.py`,
  `tests/test_experiment_runner.py`,
  `tests/test_spinning_box_comparison.py`,
  `tests/test_experiment_run_configs.py`,
  `tests/test_phase0_bootstrap.py`
- docs validator: `scripts/validate_docs.py`
- generated reports: not committed; tests write JSON reports to temporary
  directories only
- raw artifacts: temporary unittest output and branch-gate stdout only

## Verification Commands

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_reporting_contracts
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_rigid_baselines
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_runner tests.test_spinning_box_comparison
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_run_configs tests.test_phase0_bootstrap
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/env/readiness_check.py
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"
git diff --check
```

## TDD Evidence

Reporting RED result:

```text
FAILED (failures=4)
```

Reporting GREEN result:

```text
Ran 12 tests, OK
```

RBD baseline RED result:

```text
ImportError: cannot import name 'run_spinning_box_paper_rbd_baseline'
ImportError: cannot import name 'write_spinning_box_paper_rbd_baseline_report'
```

RBD baseline GREEN result:

```text
Ran 7 tests, OK
```

Runner/comparison RED result:

```text
FAILED (failures=2, errors=2)
```

Runner/comparison GREEN result:

```text
Ran 19 tests, OK
```

Docs RED result:

```text
missing claim boundary bullet: This repository contains Phase 27
record file missing: docs/records/2026-05-17-phase27-rbd-pass-gate.md
```

Docs GREEN result:

```text
docs validator: Phase 0/1/2/3/4/5/6/7/8/9/10/11/12/13/14/15/16/17/18/19/20/21/22/23/24/25/26/27 docs/provenance validation passed
```

## Claim Impact

No `experiment.*` claim is passed in this phase. The single-body spinning-box
matrix no longer lists `rbd_implicit_baseline_report_incomplete`, but the paper
claim remains blocked by `mabd_newton_report_incomplete` and
`spinning_box_comparison_report_incomplete`.
