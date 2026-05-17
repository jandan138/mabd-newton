# Phase 40 Physical Pendulum Joint-Force Reference Design

Date: 2026-05-17

## Purpose

Phase 40 closes one concrete physical-pendulum evidence gap: the current reports
record M-ABD and RBD joint-force magnitudes, but the analytic lane contains only
the paper angle reference. The paper source lines
`/tmp/mabd-paper/source/sections/experiment.tex:77-91` state that the
physical-pendulum figure plots joint-force magnitude and that the joint-force
waveform should better match the reference as the time step decreases.

This phase adds a scalar/procedural analytic joint-force reference using the
same simple-pendulum assumptions already used by the current RBD lane. It is a
diagnostic reference for this repository's configured scalar/procedural
physical-pendulum lane, not a paper-faithful geometry claim.

## Scope

In scope:

- Add analytic angular-velocity and joint-force magnitude reference helpers for
  the configured scalar pendulum:
  `force = mass * abs(length * angular_velocity**2 + |gravity| * sin(angle))`.
- Add compact analytic joint-force samples to the analytic-reference report.
- Add MABD/RBD joint-force reference errors to their lane reports.
- Add comparison-level joint-force waveform diagnostics against the analytic
  reference for matched sample times.
- Replace the report blocker `joint_force_waveform_agreement_missing` with
  `paper_geometry_unknown_for_joint_force_claim` only where an analytic
  diagnostic is actually available.
- Keep `pendulum_geometry_unknown` and top-level report status `incomplete`.
- Keep `experiment.single_body.physical_pendulum` as `intended`.

Out of scope:

- Claiming paper-faithful physical-pendulum geometry.
- Claiming physical-pendulum experiment pass.
- Claiming the paper's undisclosed rigid geometry, mass distribution, or joint
  force is reconstructed.
- Rendering the paper figure.
- Benchmarking runtime performance.

## Reference Model

The current physical-pendulum RBD lane already models a scalar point pendulum
with length `L`, mass `m`, and gravity magnitude `g`. For the paper angle
reference `theta(t)`, the scalar angular velocity is computed by the derivative
of the existing elliptic-reference formula. For the configured release from
horizontal with zero velocity, this is equivalent to the energy relation:

```text
omega_ref(theta) = sqrt(max(0, 2 * g / L * sin(theta)))
```

The joint-force reference uses the same radial reaction convention as the
existing RBD diagnostic:

```text
joint_force_ref = m * abs(L * omega_ref**2 + g * sin(theta))
```

Because the paper does not disclose the exact rigid pendulum geometry and mass
distribution, this reference is only valid for the repository's scalar
procedural lane. Reports must state this limitation explicitly.

## Report Contract

Analytic-reference report:

- Adds `joint_force_samples_n`, each with `sample_index`, `time_s`,
  `angle_rad`, `angular_velocity_rad_s`, and `joint_force_magnitude_n`.
- Adds `max_joint_force_magnitude_n`.
- Adds expected `joint_force_reference_model =
  scalar_point_pendulum_radial_reaction`.

MABD and RBD reports:

- Add per-sample `reference_joint_force_magnitude_n` and
  `abs_joint_force_error_n`.
- Add `max_abs_joint_force_error_n`.
- Keep `pendulum_geometry_unknown`.
- Remove `joint_force_waveform_agreement_missing` only after the analytic
  waveform diagnostic exists.

Comparison report:

- Adds `joint_force_waveform_diagnostics` with matched sample count, per-lane
  maximum absolute joint-force error, and compact per-sample rows.
- Keeps `missing_paper_metrics = ["joint_force_error:paper_geometry_unknown"]`.
- Keeps `paper_metric_statuses.joint_force_error.status =
  diagnostic_scalar_reference_not_paper_geometry`.

## Claim Boundary

Phase 40 verifies scalar/procedural joint-force waveform diagnostics for the
configured physical-pendulum lane. It does not verify paper-faithful geometry,
the paper's exact joint-force waveform, a rendered figure, runtime timing, or
any passed `experiment.*` claim.

## Tests

- `tests.test_physical_pendulum_reference` verifies angular velocity and
  joint-force reference values at release and quarter-period samples.
- `tests.test_physical_pendulum_rbd` verifies RBD force samples include
  reference force and error fields.
- `tests.test_physical_pendulum_mabd` verifies MABD force samples include
  reference force and error fields.
- `tests.test_experiment_runner` verifies generated lane and comparison reports
  include joint-force waveform diagnostics and do not retain
  `joint_force_waveform_agreement_missing`.
- `tests.test_phase0_bootstrap` and `scripts/validate_docs.py` verify Phase40
  records, boundaries, reports, and non-overclaim constraints.
