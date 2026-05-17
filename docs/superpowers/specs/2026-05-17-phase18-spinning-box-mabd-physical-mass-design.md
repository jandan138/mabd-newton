# Phase 18 Spinning-Box MABD Physical Mass Design

## Goal

Replace the single-body spinning-box M-ABD development lane's synthetic identity
mass diagonal with the paper cube's continuous affine mass diagonal, and record
physical kinetic-energy diagnostics without claiming the paper experiment is
passed.

## Source Facts

The paper spinning-box setup uses a cube with side length `0.1 m`, density
`1E3 kg/m^3`, initial linear momentum `[100, 0, 0] kg m/s`, and initial angular
momentum `[0, 100, 0] kg m^2/s`. The current Phase 17 lane already maps these
paper momenta to ABD generalized velocity. Its remaining synthetic piece is the
configured `mass_diagonal`, which is still twelve identity entries.

Newton's local M-ABD state packs `q = [A[:,0], A[:,1], A[:,2], t]`. For affine
kinematics `x = A r + t`, the continuous mass matrix is
`M = integral rho * J(r)^T * J(r) dV`. A centered uniform cube has zero mixed
second moments and identical diagonal second moments:

- `mass = density * side_length^3 = 1.0 kg`
- `int rho * x^2 dV = int rho * y^2 dV = int rho * z^2 dV = mass * side_length^2 / 12 = 1/1200 kg m^2`
- M-ABD diagonal: nine affine entries of `1/1200`, then three translation entries of `1.0`

This makes the Phase 17 paper velocity produce physical initial energy
`3,005,000 J`: `3,000,000 J` rotational and `5,000 J` translational.

## Implementation

Add `spinning_box_mabd_mass_diagonal(config)` to
`src/mabd_reproduction/spinning_box_physics.py`. The helper derives its values
from parsed paper values, not hard-coded config literals, and returns a
12-vector matching Newton's local `pack_q` order.

Update `configs/experiments/single_body_spinning_box.yaml` so
`simulation.mass_diagonal` contains the physical diagonal. Keep the lane status
`incomplete` and keep `rbd_implicit_baseline` as a required missing lane.

Update `write_spinning_box_development_report` to publish physical mass and
energy evidence:

- `mass_kg`
- `mabd_mass_diagonal`
- `mass_diagonal_source`
- `initial_energy_j`
- `final_energy_j`
- `relative_energy_drift`

The existing absolute `energy_drift` remains for compatibility with earlier
comparison/report code.

## Validation

Add tests that fail against Phase 17:

- the helper returns `[1/1200] * 9 + [1.0] * 3`
- the configured spinning-box mass diagonal equals the helper output
- the configured paper velocity has `3,005,000 J` initial kinetic energy
- the generated M-ABD report contains physical mass/energy diagnostics
- docs validator requires the Phase 18 record and boundary language

## Claim Boundaries

Phase 18 verifies only the physical mass-diagonal and kinetic-energy diagnostic
plumbing for the M-ABD single-body spinning-box development lane. It still does
not verify:

- the paper spinning-box experiment
- paper-faithful implicit RBD comparison
- paper-faithful affine collision/contact
- paper timing or trajectory agreement
- generated reports as committed evidence
- any passed `experiment.*` claim
