# Phase 80 Rolling Explicit No-Slip Candidate

## Status

incomplete_explicit_no_slip_candidate_recorded

## Scope

Phase 80 records a fail-closed local explicit no-slip rolling-cylinder
candidate for `experiment.single_body.rolling_spinning`.

This lane is a CPU NumPy projected no-slip candidate for the current configured
rolling cylinder state:

- lane: `rolling_spinning_rbd_explicit_no_slip_candidate`
- report:
  `reports/experiment_matrix/single_body_rolling_spinning_rbd_explicit_no_slip_candidate.json`
- report sha256:
  `6bf5707e67a98e2e4e79871d36968fc4aac34ac9cbe512978a324ea1ed5e93f3`
- source commit: `5c137ceae88affcef8c9774ebea7cbecfe9177bf`
- vendored Newton commit: `96713fa965463b69c229a4d30582c733ff3526bb`
- paper source version: `2603.08079v2`
- Python: `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python`
- backend: `cpu_numpy_projected_no_slip`
- solver mode: `newton_explicit_no_slip_rolling_cylinder_candidate`
- status = incomplete
- paper_comparable = false
- full_experiment_claim_passed = false
- local_runtime_measured = true
- timing_distribution.scope = local_no_slip_projection_not_paper_timing
- timing_distribution.paper_explicit_rbd_total_simulation_time_ms = 32.0

The generated report records final center position approximately
`[100.0, 0.5, 0.0]`, final linear velocity `[1.0, 0.0, 0.0]`, final angular
velocity `[0.0, 0.0, -2.0]`, zero no-slip residual, zero center-height drift,
and zero relative energy drift for 10K local explicit projection steps at
`h = 0.01`.

The report intentionally records local wall-clock timing only as local evidence.
It is not paper-comparable timing and is not compared against the paper's
explicit RBD `32 ms` result.

## Blocking Reasons

The report intentionally keeps these blockers:

- `newton_explicit_no_slip_candidate_not_paper_explicit_rbd_solver`
- `paper_rbd_solver_details_missing`
- `paper_no_slip_condition_inferred`
- `no_slip_projection_not_contact_dynamics`
- `paper_faithful_explicit_rbd_baseline_missing`
- `paper_faithful_implicit_rbd_baseline_missing`
- `paper_faithful_mabd_collision_missing`
- `paper_comparable_timing_missing`

It preserves the living gap-audit vocabulary:

- `paper_faithful_explicit_rbd_baseline`
- `paper_faithful_implicit_rbd_baseline`
- `paper_faithful_mabd_rolling_cylinder`
- `paper_comparable_timing`

This phase does not prove paper-faithful explicit RBD, paper-faithful implicit
RBD, paper-faithful M-ABD rolling-cylinder collision/friction, contact-dynamics
no-slip, paper-comparable timing, or any passed `experiment.*` claim.

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
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_run_configs.ExperimentRunConfigTests.test_rolling_spinning_rbd_explicit_no_slip_candidate_is_fail_closed
```

Result: `Ran 1 test in 0.103s OK`.

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_runner.ExperimentRunnerTests.test_run_rolling_spinning_rbd_explicit_no_slip_candidate_writes_report
```

Result: `Ran 1 test in 3.968s OK`.

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_runner.ExperimentRunnerTests.test_run_experiment_cli_runs_rolling_spinning_rbd_explicit_no_slip_candidate_lane
```

Result: `Ran 1 test in 4.099s OK`.

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/run_experiment.py --lane rolling_spinning_rbd_explicit_no_slip_candidate --config configs/experiments/single_body_rolling_spinning.yaml --matrix configs/experiments/paper_experiment_matrix.yaml --source-commit 5c137ceae88affcef8c9774ebea7cbecfe9177bf --vendored-newton-commit 96713fa965463b69c229a4d30582c733ff3526bb
```

Result:

```json
{"baseline_lane": "rbd_explicit_no_slip_candidate", "claim_id": "experiment.single_body.rolling_spinning", "output_report": "reports/experiment_matrix/single_body_rolling_spinning_rbd_explicit_no_slip_candidate.json", "scene_id": "single_body_rolling_spinning", "status": "incomplete"}
```

```bash
sha256sum reports/experiment_matrix/single_body_rolling_spinning_rbd_explicit_no_slip_candidate.json
```

Result:

```text
6bf5707e67a98e2e4e79871d36968fc4aac34ac9cbe512978a324ea1ed5e93f3  reports/experiment_matrix/single_body_rolling_spinning_rbd_explicit_no_slip_candidate.json
```

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
```

Result:
`Phase 0/1/2/3/4/5/6/7/8/9/10/11/12/13/14/15/16/17/18/19/20/21/22/23/24/25/26/27/28/29/30/31/32/33/34/35/36/37/38/39/40/41/42/43/44/45/46/47/48/49/50/51/52/53/54/55/56/57/58/59/60/61/62/63/64/65/66/67/68/69/70/71/72/73/74/75/76/77/78/79/80 docs/provenance validation passed`.

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
```

Result: `Ran 626 tests in 604.163s OK`.

```bash
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"
```

Result:
`/cpfs/user/zhuzihou/dev/mabd-newton/.worktrees/phase80-rolling-explicit-no-slip-candidate/vendor/newton/newton/__init__.py`.

```bash
git diff --check
```

Result: passed with no output.
