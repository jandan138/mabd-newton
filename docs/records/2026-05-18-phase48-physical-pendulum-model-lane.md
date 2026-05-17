# Phase 48 Physical Pendulum Model-Derived Lane Record

## Status

passed_for_physical_pendulum_model_derived_lane_slice

## Repository

- Worktree: `/cpfs/user/zhuzihou/dev/mabd-newton/.worktrees/phase48-physical-pendulum-model-lane`
- Branch: `phase48-physical-pendulum-model-lane`
- Base commit: `7735a3357a2660a4b014aa6e37d3bc38f9039916`
- Plan/spec commit: `42f8674`
- RED test commit: `f642f69`
- Implementation commit: `d102194`
- Evidence record commit: `0200a67f22dc38b4af20db1215202cd838379766`
- Review hardening commit: `1280ac4a3e15a6b5d9c8ffade2cb16980ab2d54c`
- Spec: `docs/superpowers/specs/2026-05-18-phase48-physical-pendulum-model-lane-design.md`
- Plan: `docs/superpowers/plans/2026-05-18-mabd-phase48-physical-pendulum-model-lane.md`

## Vendored Newton

- Source: `https://github.com/newton-physics/newton.git`
- Imported upstream commit: `96713fa965463b69c229a4d30582c733ff3526bb`
- Local patch status: locally patched
- Phase 48 local patch: `SolverMABD.register_custom_attributes(...)` registers
  `mabd:zero_stiffness_diagnostic` on body rows.
- Model-row zero stiffness requires explicit diagnostic opt-in:
  `young_modulus == 0.0` is accepted only when
  `mabd:zero_stiffness_diagnostic != 0`.
- Default `young_modulus == 0.0` without the diagnostic opt-in still raises
  through the positive-Young-modulus validation path.

## Environment

- Python:
  `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python`
- Environment role: `mabd-newton-clone`
- The validation commands use `PYTHONPATH=src:vendor/newton` or
  `PYTHONPATH=vendor/newton`.
- Routine validation does not mutate the shared Newton/reference environment.

## Implementation Evidence

- `src/mabd_reproduction/physical_pendulum_mabd.py` now has two explicit
  rollout sources:
  - `manual_cpu_oracle_config`
  - `newton_model_derived`
- `roll_out_physical_pendulum_mabd_development(...)` remains on the manual
  `MABDCPUOracleConfig` diagnostic path.
- `roll_out_physical_pendulum_mabd_model_derived(...)` builds a Newton
  `ModelBuilder` model with:
  - `mabd:body`
  - `mabd:world_constraint`
  - `mabd:gravity`
  - `mabd:zero_stiffness_diagnostic`
- The model-derived path advances the procedural physical pendulum through
  `SolverMABD.step(state, state, None, None, dt)`.
- The formal `write_physical_pendulum_mabd_newton_report(...)` lane now uses
  `roll_out_physical_pendulum_mabd_model_derived(...)`.
- The generated `mabd_newton` report records
  `solver_model_config_source = newton_model_derived`.
- The generated `mabd_newton` report records
  `newton_model_derived_custom_frequencies = [mabd:body,
  mabd:world_constraint, mabd:gravity]`.
- The regenerated reports remain `status = incomplete` and
  `full_experiment_claim_passed = false`.

## RED Evidence

Command:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_physical_pendulum_mabd tests.test_experiment_runner
```

Observed failure before implementation:

- `ImportError: cannot import name 'roll_out_physical_pendulum_mabd_model_derived'`
- `KeyError: 'solver_model_config_source'`
- `Ran 34 tests`
- `FAILED (errors=2)`

Additional focused Newton RED after root-cause investigation:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_mabd_phase4_solver_step.MABDPhase4SolverStepTests.test_solver_step_model_body_allows_zero_young_modulus_with_diagnostic_opt_in
```

Observed failure:

- `ValueError: young_modulus must be positive`
- `Ran 1 test`
- `FAILED (errors=1)`

Review hardening RED for the over-broad zero-stiffness patch:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_mabd_phase4_solver_step.MABDPhase4SolverStepTests.test_solver_step_model_body_rejects_zero_young_modulus_without_diagnostic_opt_in
```

Observed failure before the explicit model-row diagnostic gate:

- `AssertionError: ValueError not raised`
- `Ran 1 test`
- `FAILED (failures=1)`

## GREEN Evidence

Focused Newton zero-stiffness test:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_mabd_phase4_solver_step.MABDPhase4SolverStepTests.test_solver_step_model_body_allows_zero_young_modulus_with_diagnostic_opt_in
```

Result:

- `Ran 1 test`
- `OK`

Targeted Phase48 suite:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_mabd_phase4_solver_step.MABDPhase4SolverStepTests.test_solver_step_model_body_rejects_zero_young_modulus_without_diagnostic_opt_in tests.test_mabd_phase4_solver_step.MABDPhase4SolverStepTests.test_solver_step_model_body_allows_zero_young_modulus_with_diagnostic_opt_in tests.test_physical_pendulum_mabd tests.test_experiment_runner
```

Result:

- `Ran 38 tests`
- `OK`

Review hardening coverage now verifies:

- the default model-derived body row rejects `young_modulus == 0.0` without
  `mabd:zero_stiffness_diagnostic`;
- the explicit diagnostic opt-in permits the zero-stiffness physical-pendulum
  body row;
- the formal physical-pendulum lane calls `SolverMABD.step()`;
- the generated reports assert the model-derived custom frequencies.

CLI stdout regression test:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_runner.ExperimentRunnerTests.test_run_experiment_cli_writes_physical_pendulum_mabd_newton_report
```

Result:

- `Ran 1 test`
- `OK`

Style check:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check src/mabd_reproduction/physical_pendulum_mabd.py src/mabd_reproduction/physical_pendulum_reports.py tests/test_mabd_phase4_solver_step.py
```

Result:

- `All checks passed!`

## Report Artifacts

Regenerated reports:

- `reports/experiment_matrix/single_body_physical_pendulum_mabd_newton.json`
- `reports/experiment_matrix/single_body_physical_pendulum_comparison.json`

Generation commands:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/run_experiment.py --lane physical_pendulum_mabd_newton --config configs/experiments/single_body_physical_pendulum.yaml --matrix configs/experiments/paper_experiment_matrix.yaml --output reports/experiment_matrix/single_body_physical_pendulum_mabd_newton.json --source-commit 1280ac4 --vendored-newton-commit 96713fa965463b69c229a4d30582c733ff3526bb
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/run_experiment.py --lane physical_pendulum_comparison --config configs/experiments/single_body_physical_pendulum.yaml --matrix configs/experiments/paper_experiment_matrix.yaml --analytic-report reports/experiment_matrix/single_body_physical_pendulum_analytic_reference.json --mabd-report reports/experiment_matrix/single_body_physical_pendulum_mabd_newton.json --rbd-report reports/experiment_matrix/single_body_physical_pendulum_rbd_baseline.json --output reports/experiment_matrix/single_body_physical_pendulum_comparison.json --source-commit 1280ac4 --vendored-newton-commit 96713fa965463b69c229a4d30582c733ff3526bb
```

Observed report invariants:

- `status = incomplete`
- `source_commit = 1280ac4`
- `vendored_newton_commit = 96713fa965463b69c229a4d30582c733ff3526bb`
- `solver_model_config_source = newton_model_derived`
- `newton_model_derived_custom_frequencies = [mabd:body,
  mabd:world_constraint, mabd:gravity]`
- `blocking_reasons = [pendulum_geometry_unknown]` for the `mabd_newton`
  report
- comparison blockers remain `pendulum_geometry_unknown` and
  `physical_pendulum_comparison_pass_gate_not_enabled`

## Verification Commands

The final Phase48 gate set is:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/env/readiness_check.py
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"
npm --prefix site run validate
git diff --check
```

## Claim Impact

- No `experiment.*` claim is passed.
- The physical-pendulum `mabd_newton` report lane is now model-derived through
  `SolverMABD.step()` for the procedural diagnostic pendulum.
- Paper-faithful physical-pendulum geometry remains missing.
- The physical-pendulum comparison pass gate remains not enabled.
- Zero stiffness remains an explicit diagnostic opt-in, not a general material
  model change.
- Newton `Contacts` remain unimplemented for the reproduction.
- Runtime Newton `Control` remains unverified for this lane.
- GPU/Warp kernels remain unverified.
- Rendered output, generated videos, raw simulation logs, paper timing, and
  full paper reproduction remain incomplete.
