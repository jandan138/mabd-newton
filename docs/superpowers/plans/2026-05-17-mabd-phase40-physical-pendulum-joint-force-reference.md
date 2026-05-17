# Phase 40 Physical Pendulum Joint-Force Reference Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add scalar/procedural analytic joint-force reference diagnostics for the physical-pendulum lane without claiming paper-faithful geometry or passing the experiment.

**Architecture:** Extend the existing physical-pendulum analytic reference module with angular-velocity and scalar radial-reaction helpers, then thread those values through MABD, RBD, analytic, and comparison reports. Keep claim-boundary records and validators as the enforcement layer that this is diagnostic evidence only.

**Tech Stack:** Python 3.10, NumPy/SciPy, `unittest`, JSON claim reports, canonical `mabd-newton-py310` environment.

---

## File Map

- Modify `src/mabd_reproduction/physical_pendulum_reference.py`: add analytic angular-velocity and joint-force reference helpers.
- Modify `src/mabd_reproduction/physical_pendulum_rbd.py`: add reference joint-force/error fields to samples and rollout max metric.
- Modify `src/mabd_reproduction/physical_pendulum_mabd.py`: add reference joint-force/error fields to samples and rollout max metric.
- Modify `src/mabd_reproduction/physical_pendulum_reports.py`: serialize new metrics in analytic, MABD, and RBD reports, and update blockers/status text.
- Modify `src/mabd_reproduction/comparison_reports.py`: add joint-force waveform diagnostics and update physical-pendulum metric status.
- Modify `configs/experiments/single_body_physical_pendulum.yaml`: add thresholds for max joint-force errors in the relevant lanes.
- Modify `tests/test_physical_pendulum_reference.py`, `tests/test_physical_pendulum_rbd.py`, `tests/test_physical_pendulum_mabd.py`, and `tests/test_experiment_runner.py`: RED/GREEN coverage for new fields.
- Modify `tests/test_phase0_bootstrap.py` and `scripts/validate_docs.py`: Phase40 record, claim boundaries, and report contract gates.
- Modify `docs/reference/claim-boundaries.md`: add Phase40 bounded claim language.
- Add `docs/records/2026-05-17-phase40-physical-pendulum-joint-force-reference.md`.
- Regenerate physical-pendulum reports under `reports/experiment_matrix/`.

## Task 1: RED Tests For Reference Helpers

- [ ] **Step 1: Add failing reference tests**

In `tests/test_physical_pendulum_reference.py`, add tests:

```python
def test_physical_pendulum_angular_velocity_reference_matches_release_and_quarter_period(self) -> None:
    from mabd_reproduction.physical_pendulum_reference import (
        physical_pendulum_angular_velocity_reference,
        physical_pendulum_complete_elliptic_k,
    )

    kappa = 2.0 ** -0.5
    omega_lin = 3.132091952673165
    complete = physical_pendulum_complete_elliptic_k(kappa)
    values = physical_pendulum_angular_velocity_reference(
        [0.0, complete / omega_lin],
        kappa=kappa,
        omega_lin=omega_lin,
    )

    self.assertAlmostEqual(values[0], 0.0, places=12)
    self.assertAlmostEqual(values[1], (2.0 * 9.81) ** 0.5, places=12)


def test_physical_pendulum_joint_force_reference_uses_scalar_radial_reaction(self) -> None:
    from mabd_reproduction.physical_pendulum_reference import (
        physical_pendulum_complete_elliptic_k,
        physical_pendulum_joint_force_reference,
    )

    kappa = 2.0 ** -0.5
    omega_lin = 3.132091952673165
    complete = physical_pendulum_complete_elliptic_k(kappa)
    values = physical_pendulum_joint_force_reference(
        [0.0, complete / omega_lin],
        kappa=kappa,
        omega_lin=omega_lin,
        mass_kg=1.0,
        length_m=1.0,
        gravity_magnitude=9.81,
    )

    self.assertAlmostEqual(values[0], 0.0, places=12)
    self.assertAlmostEqual(values[1], 29.43, places=10)
```

- [ ] **Step 2: Run RED**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_physical_pendulum_reference
```

Expected: fail with missing helper imports.

## Task 2: Implement Reference Helpers

- [ ] **Step 1: Add helpers in `physical_pendulum_reference.py`**

Add functions:

```python
def _validate_positive_scalar(value: float, *, name: str) -> float:
    if not isinstance(value, Real) or isinstance(value, bool):
        raise ValueError(f"{name} must be finite and positive")
    result = float(value)
    if not isfinite(result) or result <= 0.0:
        raise ValueError(f"{name} must be finite and positive")
    return result


def physical_pendulum_angular_velocity_reference(
    times: Iterable[float],
    *,
    kappa: float,
    omega_lin: float,
) -> np.ndarray:
    angles = physical_pendulum_angle_reference(times, kappa=kappa, omega_lin=omega_lin)
    omega_value = _validate_omega_lin(omega_lin)
    velocities = 2.0 * omega_value * np.sqrt(np.maximum(0.0, np.sin(angles)))
    return np.asarray(velocities, dtype=float)


def physical_pendulum_joint_force_reference(
    times: Iterable[float],
    *,
    kappa: float,
    omega_lin: float,
    mass_kg: float,
    length_m: float,
    gravity_magnitude: float,
) -> np.ndarray:
    mass = _validate_positive_scalar(mass_kg, name="mass_kg")
    length = _validate_positive_scalar(length_m, name="length_m")
    gravity = _validate_positive_scalar(gravity_magnitude, name="gravity_magnitude")
    angles = physical_pendulum_angle_reference(times, kappa=kappa, omega_lin=omega_lin)
    velocities = physical_pendulum_angular_velocity_reference(
        times,
        kappa=kappa,
        omega_lin=omega_lin,
    )
    return np.asarray(mass * np.abs(length * velocities * velocities + gravity * np.sin(angles)), dtype=float)
```

Update `__all__`.

- [ ] **Step 2: Run GREEN**

Run the same reference test command. Expected: pass.

## Task 3: RED Tests For RBD And MABD Rollouts

- [ ] **Step 1: Add failing rollout tests**

In `tests/test_physical_pendulum_rbd.py`, add assertions to the existing rollout test:

```python
self.assertGreaterEqual(rollout.max_abs_joint_force_error_n, 0.0)
self.assertTrue(np.isfinite(rollout.max_abs_joint_force_error_n))
self.assertIn("reference_joint_force_magnitude_n", rollout.samples[-1].__dataclass_fields__)
self.assertIn("abs_joint_force_error_n", rollout.samples[-1].__dataclass_fields__)
```

In `tests/test_physical_pendulum_mabd.py`, add matching assertions for `PhysicalPendulumMABDRollout`.

- [ ] **Step 2: Run RED**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_physical_pendulum_rbd tests.test_physical_pendulum_mabd
```

Expected: fail with missing dataclass fields.

## Task 4: Implement Rollout Metrics

- [ ] **Step 1: Update RBD dataclasses and rollout**

In `src/mabd_reproduction/physical_pendulum_rbd.py`:

- Import `physical_pendulum_joint_force_reference`.
- Add `reference_joint_force_magnitude_n` and `abs_joint_force_error_n` to `PhysicalPendulumRBDSample`.
- Add `max_abs_joint_force_error_n` to `PhysicalPendulumRBDRollout`.
- Compute reference force at every step using `lane.length_m`, `lane.mass_kg`, and `gravity_magnitude`.
- Track max absolute joint-force error and serialize sample fields.

- [ ] **Step 2: Update MABD dataclasses and rollout**

In `src/mabd_reproduction/physical_pendulum_mabd.py`:

- Import `physical_pendulum_joint_force_reference`.
- Add `reference_joint_force_magnitude_n` and `abs_joint_force_error_n` to `PhysicalPendulumMABDSample`.
- Add `max_abs_joint_force_error_n` to `PhysicalPendulumMABDRollout`.
- Compute reference force at every step using `config.rbd_baseline` scalar parameters so the diagnostic uses the same scalar model as RBD.
- Track max absolute joint-force error and serialize sample fields.

- [ ] **Step 3: Run GREEN**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_physical_pendulum_rbd tests.test_physical_pendulum_mabd
```

Expected: pass.

## Task 5: RED Tests For Reports And Comparison

- [ ] **Step 1: Add report tests**

In `tests/test_experiment_runner.py`:

- For analytic reference, assert `joint_force_samples_n` exists and first sample force is `0.0`.
- For MABD and RBD reports, assert `max_abs_joint_force_error_n` exists and sample rows include `reference_joint_force_magnitude_n`.
- For MABD and RBD reports, assert `joint_force_waveform_agreement_missing` is absent from `blocking_reasons`.
- For comparison, assert `joint_force_waveform_diagnostics` exists, `missing_paper_metrics` is `["joint_force_error:paper_geometry_unknown"]`, and `paper_metric_statuses.joint_force_error.status` is `diagnostic_scalar_reference_not_paper_geometry`.

- [ ] **Step 2: Run RED**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_runner
```

Expected: fail because reports do not yet serialize the new fields.

## Task 6: Implement Reports And Comparison

- [ ] **Step 1: Update analytic report serialization**

In `src/mabd_reproduction/physical_pendulum_reports.py`:

- Add helper rows for analytic joint-force samples using config `rbd_baseline` mass/length/gravity.
- Add observed `joint_force_samples_n`, `max_joint_force_magnitude_n`, and expected `joint_force_reference_model`.

- [ ] **Step 2: Update MABD/RBD report serialization**

In `src/mabd_reproduction/physical_pendulum_reports.py`:

- Add sample-row fields `reference_joint_force_magnitude_n` and `abs_joint_force_error_n`.
- Add observed `max_abs_joint_force_error_n`.
- Remove `joint_force_waveform_agreement_missing` from MABD and RBD blockers.
- Replace expected limitation wording with `scalar joint-force reference is diagnostic and not paper geometry`.

- [ ] **Step 3: Update comparison diagnostics**

In `src/mabd_reproduction/comparison_reports.py`:

- Add `_physical_joint_force_waveform_diagnostics(analytic_report, mabd_report, rbd_report)`.
- Match rows by `(step, time_s)` for MABD/RBD and by `time_s` for analytic.
- Report per-sample MABD/RBD reference errors and maximum absolute errors.
- Change `_physical_pendulum_paper_metric_statuses()["joint_force_error"]["status"]` to `diagnostic_scalar_reference_not_paper_geometry`.
- Change `missing_paper_metrics` to `["joint_force_error:paper_geometry_unknown"]`.
- Remove `joint_force_waveform_agreement_missing` from comparison blockers.

- [ ] **Step 4: Run GREEN**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_runner
```

Expected: pass.

## Task 7: Docs, Validators, Reports

- [ ] **Step 1: Add Phase40 validator tests**

In `tests/test_phase0_bootstrap.py`, add tests that Phase40:

- Has claim-boundary bullets.
- Has a dated record file.
- Rejects returned `joint_force_waveform_agreement_missing` in current MABD/RBD/comparison blockers.
- Requires `joint_force_waveform_diagnostics` in current comparison report.
- Keeps every `experiment.*` claim non-passed.

- [ ] **Step 2: Update `scripts/validate_docs.py`**

Add `validate_phase40_record()` and call it after Phase39. It must check:

- Phase40 record snippets.
- Current physical-pendulum reports include joint-force reference fields.
- Current comparison report includes `joint_force_waveform_diagnostics`.
- Current `missing_paper_metrics` is `["joint_force_error:paper_geometry_unknown"]`.
- Current blockers do not include `joint_force_waveform_agreement_missing`.
- `pendulum_geometry_unknown` remains.
- Physical-pendulum claim remains `intended`.

- [ ] **Step 3: Update claim boundaries and record**

Update `docs/reference/claim-boundaries.md` and add
`docs/records/2026-05-17-phase40-physical-pendulum-joint-force-reference.md`.

- [ ] **Step 4: Commit implementation before regenerating reports**

Run focused tests and commit source/tests/docs before report regeneration:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_physical_pendulum_reference tests.test_physical_pendulum_rbd tests.test_physical_pendulum_mabd tests.test_experiment_runner tests.test_phase0_bootstrap
git add .
git commit -m "Add physical-pendulum joint-force reference diagnostics"
```

- [ ] **Step 5: Regenerate reports using the actual implementation commit**

Use `SOURCE_COMMIT=$(git rev-parse --short HEAD)` and run:

```bash
VENDORED_NEWTON_COMMIT=96713fa965463b69c229a4d30582c733ff3526bb
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/run_experiment.py --lane analytic_reference --config configs/experiments/single_body_physical_pendulum.yaml --matrix configs/experiments/paper_experiment_matrix.yaml --output reports/experiment_matrix/single_body_physical_pendulum_analytic_reference.json --source-commit "$SOURCE_COMMIT" --vendored-newton-commit "$VENDORED_NEWTON_COMMIT"
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/run_experiment.py --lane physical_pendulum_mabd_development --config configs/experiments/single_body_physical_pendulum.yaml --matrix configs/experiments/paper_experiment_matrix.yaml --output reports/experiment_matrix/single_body_physical_pendulum_mabd_development.json --source-commit "$SOURCE_COMMIT" --vendored-newton-commit "$VENDORED_NEWTON_COMMIT"
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/run_experiment.py --lane physical_pendulum_mabd_newton --config configs/experiments/single_body_physical_pendulum.yaml --matrix configs/experiments/paper_experiment_matrix.yaml --output reports/experiment_matrix/single_body_physical_pendulum_mabd_newton.json --source-commit "$SOURCE_COMMIT" --vendored-newton-commit "$VENDORED_NEWTON_COMMIT"
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/run_experiment.py --lane rbd_implicit_baseline --config configs/experiments/single_body_physical_pendulum.yaml --matrix configs/experiments/paper_experiment_matrix.yaml --output reports/experiment_matrix/single_body_physical_pendulum_rbd_baseline.json --source-commit "$SOURCE_COMMIT" --vendored-newton-commit "$VENDORED_NEWTON_COMMIT"
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/run_experiment.py --lane physical_pendulum_comparison --config configs/experiments/single_body_physical_pendulum.yaml --matrix configs/experiments/paper_experiment_matrix.yaml --output reports/experiment_matrix/single_body_physical_pendulum_comparison.json --analytic-report reports/experiment_matrix/single_body_physical_pendulum_analytic_reference.json --mabd-report reports/experiment_matrix/single_body_physical_pendulum_mabd_newton.json --rbd-report reports/experiment_matrix/single_body_physical_pendulum_rbd_baseline.json --source-commit "$SOURCE_COMMIT" --vendored-newton-commit "$VENDORED_NEWTON_COMMIT"
```

- [ ] **Step 6: Final gates**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/env/readiness_check.py
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"
git diff --check
```

Expected: all pass.
