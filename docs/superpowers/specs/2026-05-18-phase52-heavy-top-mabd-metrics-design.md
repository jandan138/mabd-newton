# Phase52 Heavy-Top MABD Metrics Design

## Goal

Phase52 adds machine-checkable heavy-top MABD diagnostic metrics that already can be derived from the Newton-backed point-mass affine rollout:

- per-sample MABD precession velocity;
- MABD point-mass energy initial/final values;
- MABD relative energy drift;
- comparison report statuses that consume those fields.

This phase does not add paper-faithful heavy-top geometry, paper inertia, raw paper curve digitization, timing evidence, rendered videos, or a comparison pass gate.

## Current Gap

Phase51 writes a heavy-top comparison report that consumes both the RK4 reference lane and the MABD Newton lane, but it still records:

- `precession_velocity_error:mabd_precession_velocity_samples_missing`;
- `energy_drift:mabd_energy_drift_missing`.

The MABD rollout already carries affine state `q` and velocity `qd`, so these two fields can be computed without changing solver semantics:

- precession velocity is derived from unwrapped sampled precession angles divided by sample time deltas;
- energy is derived from the configured MABD point masses, affine-transformed point positions, affine point velocities, and configured gravity.

## Design

`HeavyTopMABDSample` will expose `precession_velocity_rad_s`. The value is sampled consistently with existing compact rows. For sample index `i`, use a finite-difference over unwrapped precession samples:

- first sample: forward difference to sample 1;
- last sample: backward difference from the previous sample;
- interior sample: centered difference from `i - 1` to `i + 1`.

`HeavyTopMABDRollout` will expose:

- `energy_initial`;
- `energy_final`;
- `relative_energy_drift`.

Energy uses the MABD diagnostic point-mass model:

```text
world_points = affine_points(q, rest_points_m)
world_velocities = affine_points(qd, rest_points_m)
kinetic = 0.5 * sum_i m_i * dot(v_i, v_i)
potential = -sum_i m_i * dot(gravity_m_s2, world_points_i)
energy = kinetic + potential
relative_energy_drift = (energy_final - energy_initial) / energy_initial
```

If `energy_initial` is zero or non-finite, the drift is non-finite and the rollout must not report `finite = true`.

The report writer will include these values in `observed` and in each sample row. The comparison report will treat MABD precession velocity and energy drift as diagnostic-available when finite, while retaining `nutation_angle_error:paper_reference_curve_missing` and the existing source/timing/pass-gate blockers.

## Claim Boundaries

Phase52 may claim:

- heavy-top MABD diagnostic precession velocities are generated and finite;
- heavy-top MABD diagnostic point-mass energy drift is generated and finite;
- the heavy-top comparison report no longer records missing MABD-side precession velocity or energy fields.

Phase52 must not claim:

- paper-faithful heavy-top geometry or inertia;
- raw paper curve agreement;
- heavy-top experiment pass;
- ABD-vs-RBD comparison pass;
- runtime performance reproduction;
- full paper reproduction.

## Validation

Required checks:

- targeted RED/GREEN tests for `tests.test_heavy_top_mabd`;
- targeted RED/GREEN tests for `tests.test_heavy_top_comparison_reports`;
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests`;
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py`;
- `PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"`;
- `git diff --check`.
