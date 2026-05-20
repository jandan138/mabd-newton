# Phase 79 Rolling Cylinder No-Slip Reference

## Status

incomplete_no_slip_reference_recorded

## Scope

Phase 79 records a fail-closed analytic no-slip rolling-cylinder reference for
`experiment.single_body.rolling_spinning`.

This is a deterministic closed-form reference for the current configured
rolling cylinder state:

- lane: `rolling_spinning_rbd_no_slip_reference`
- report:
  `reports/experiment_matrix/single_body_rolling_spinning_rbd_no_slip_reference.json`
- report sha256:
  `e9c959b15054659cc27a2f1c81eeda2bba81a30265f5fedb6e1d350de27ff032`
- source commit: `72be0f998f46f52cf0ca67d1c8c19fd94769436c`
- vendored Newton commit: `96713fa965463b69c229a4d30582c733ff3526bb`
- paper source version: `2603.08079v2`
- Python: `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python`
- backend: `cpu_numpy_closed_form`
- solver mode: `analytic_no_slip_rolling_cylinder_reference`
- status = incomplete
- paper_comparable = false
- full_experiment_claim_passed = false
- local_runtime_measured = false
- timing_distribution.status = not_measured
- deterministic report hash = true

The generated report records final center position `[100.0, 0.5, 0.0]`, final
linear velocity `[1.0, 0.0, 0.0]`, final angular velocity `[0.0, 0.0, -2.0]`,
zero no-slip residual, zero center-height drift, and zero relative energy drift
for 10K steps at `h = 0.01`.

The report intentionally does not store wall-clock timing. It is a deterministic
closed-form reference artifact, not a runtime benchmark, so paper-comparable
timing remains blocked.

## Blocking Reasons

The report intentionally keeps these blockers:

- `paper_faithful_explicit_rbd_baseline_missing`
- `paper_faithful_implicit_rbd_baseline_missing`
- `paper_faithful_mabd_collision_missing`
- `paper_comparable_timing_missing`
- `paper_rbd_solver_details_missing`

It preserves the living gap-audit vocabulary:

- `paper_faithful_explicit_rbd_baseline`
- `paper_faithful_implicit_rbd_baseline`
- `paper_faithful_mabd_rolling_cylinder`
- `paper_comparable_timing`

This phase does not prove paper-faithful RBD, paper-faithful M-ABD
rolling-cylinder collision/friction, paper-comparable timing, or any passed
`experiment.*` claim. It must not be used as evidence for any passed
`experiment.*` claim.

No `experiment.*` claim is passed; there is no evidence for any passed `experiment.*` claim.

## Environment Isolation

- mutates_reference_environment=false
- uses_reference_python=false
- uses_ambient_python=false
- canonical environment:
  `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310`
- reference environment:
  `/cpfs/user/zhuzihou/conda-managed/envs/physics-primitive-newton-py310`

## Commands

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_run_configs
```

Result: `Ran 67 tests in 4.364s OK`.

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_runner
```

Result: `Ran 93 tests in 318.038s OK`.

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/run_experiment.py --lane rolling_spinning_rbd_no_slip_reference --config configs/experiments/single_body_rolling_spinning.yaml --matrix configs/experiments/paper_experiment_matrix.yaml --source-commit 72be0f998f46f52cf0ca67d1c8c19fd94769436c --vendored-newton-commit 96713fa965463b69c229a4d30582c733ff3526bb
```

Result:

```json
{"baseline_lane": "rbd_no_slip_reference", "claim_id": "experiment.single_body.rolling_spinning", "output_report": "reports/experiment_matrix/single_body_rolling_spinning_rbd_no_slip_reference.json", "scene_id": "single_body_rolling_spinning", "status": "incomplete"}
```

```bash
sha256sum reports/experiment_matrix/single_body_rolling_spinning_rbd_no_slip_reference.json
```

Result:

```text
e9c959b15054659cc27a2f1c81eeda2bba81a30265f5fedb6e1d350de27ff032  reports/experiment_matrix/single_body_rolling_spinning_rbd_no_slip_reference.json
```
