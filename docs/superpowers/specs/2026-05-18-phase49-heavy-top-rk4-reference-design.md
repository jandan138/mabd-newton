# Phase 49 Heavy Top RK4 Reference Design

## Status

design_for_heavy_top_reference_diagnostic_lane

## Objective

Add a source-backed, executable diagnostic reference lane for
`experiment.single_body.heavy_top` without claiming the heavy-top paper
experiment is reproduced.

## Source Facts

- Paper source: `/tmp/mabd-paper/source/sections/experiment.tex:65-75`.
- Figure source: `/tmp/mabd-paper/source/images/spinning_top/spinning_top.pdf`.
- Figure PDF SHA256:
  `c8f5e206415b9feb3578ee32aa3b7284e2695bdd84eeb0200f3b4aa01cf3422d`.
- Public source facts used by this phase:
  - fixed-pivot heavy top under gravity;
  - initial tilt is `5 deg`;
  - initial angular speed is `10 rad/s`;
  - high-accuracy RK4 reference uses `h = 1e-4 s`;
  - plotted metrics are precession velocity and nutation angle over `0..10 s`;
  - slight inertia asymmetry induces nutation oscillations.

## Claim Boundary

Phase 49 is a diagnostic reference lane only. It does not prove:

- paper-faithful heavy-top inertia or geometry;
- M-ABD heavy-top dynamics;
- implicit RBD baseline parity;
- convergence to the paper figure curves;
- paper timing;
- any passed `experiment.*` claim.

The generated report must remain `status = incomplete` and
`full_experiment_claim_passed = false`.

## Approach Options

### Option A: Source-backed RK4 reference diagnostic

Implement a deterministic rigid heavy-top RK4 integrator in NumPy. Use the
paper-backed initialization facts and explicit diagnostic inertias, mass,
pivot-to-COM length, and gravity. Report precession velocity and nutation angle
samples, conservation diagnostics, source gaps, and blockers.

This is the selected approach because it follows the existing T-handle pattern,
keeps the claim boundary honest, and creates an executable reference artifact
for the heavy-top claim.

### Option B: Direct M-ABD heavy-top lane first

Build a Newton model-derived M-ABD heavy-top lane immediately. This would move
closer to the target method but would be under-anchored without a source-backed
reference artifact and would mix solver work with source-gap accounting.

### Option C: Source audit only

Record the missing inertia/geometry without runnable code. This would be safe
but weaker than a diagnostic lane and would not advance the experiment runner or
report matrix.

## Architecture

Phase 49 follows the existing T-handle lane pattern.

- `configs/experiments/single_body_heavy_top.yaml` stores source-backed paper
  values, diagnostic reference parameters, thresholds, output path, and blockers.
- `src/mabd_reproduction/experiment_configs.py` gains `HeavyTopRunConfig`,
  `HeavyTopReferenceConfig`, `load_heavy_top_config(...)`, and
  `validate_heavy_top_config_against_matrix(...)`.
- `src/mabd_reproduction/heavy_top_reference.py` integrates a fixed-pivot
  heavy-top reference with RK4. State consists of a world-from-body rotation
  matrix and body-frame angular velocity. The body torque is
  `r_body x R^T(m g)`, where `r_body` is the pivot-to-COM vector.
- `src/mabd_reproduction/heavy_top_reports.py` writes an incomplete
  `ClaimReport` for lane `rbd_rk4_reference`.
- `src/mabd_reproduction/experiment_runner.py` exposes
  `run_heavy_top_rk4_reference(...)`, and `scripts/run_experiment.py` gets a
  `heavy_top_rk4_reference` lane.
- `scripts/validate_docs.py` and `tests/test_phase0_bootstrap.py` guard the
  new config, report, record, and claim boundaries.

## Metrics

The report records:

- `nutation_angle_deg` samples, computed as the angle between the top symmetry
  axis and world up;
- `precession_angle_rad` and finite-difference `precession_velocity_rad_s`;
- energy initial/final and relative drift;
- angular momentum norm initial/final and relative drift;
- `max_nutation_angle_deg`, `min_nutation_angle_deg`, and
  `max_abs_precession_velocity_rad_s`.

Thresholds are diagnostic stability gates, not paper pass gates.

## Tests

RED tests must be added before implementation:

- config loader rejects missing or inconsistent heavy-top fields;
- matrix validation requires the existing heavy-top matrix source lines,
  asset ids, paper values, metrics, and blockers;
- RK4 reference returns finite samples over the configured `0..10 s` window,
  preserves energy within threshold, and shows nonconstant nutation;
- report writer emits `status = incomplete`,
  `baseline_lane = rbd_rk4_reference`, source metadata, blockers, samples, and
  `full_experiment_claim_passed = false`;
- CLI runner writes the configured report and returns JSON-safe stdout;
- bootstrap/doc validation records Phase 49 without overclaiming.

## Non-Goals

- No paper-faithful heavy-top pass gate.
- No M-ABD heavy-top lane in this phase.
- No implicit RBD baseline comparison in this phase.
- No generated videos or raw simulation directories.
- No external asset vendoring.
