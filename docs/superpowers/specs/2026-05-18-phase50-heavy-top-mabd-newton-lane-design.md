# Phase 50 Heavy Top MABD Newton Lane Design

## Status

design_for_heavy_top_mabd_newton_diagnostic_lane

## Objective

Add a formal, executable `mabd_newton` diagnostic lane for
`experiment.single_body.heavy_top` without claiming the paper heavy-top
experiment is reproduced.

## Source Facts

- Paper source: `/tmp/mabd-paper/source/sections/experiment.tex:65-75`.
- Phase 49 already records the public spinning-top figure hash and the
  source-backed facts: initial tilt `5 deg`, initial angular speed `10 rad/s`,
  RK4 reference step `h = 1e-4 s`, and metrics over `0..10 s`.
- Public source does not provide exact heavy-top geometry, exact inertia, raw
  plotted curve data, or paper-comparable timing.

## Claim Boundary

Phase 50 creates a formal `mabd_newton` lane artifact only. The lane must remain
`status = incomplete`, must set `full_experiment_claim_passed = false`, and
must not expose `lane_gate_status = passed`.

This phase does not prove:

- paper-faithful heavy-top inertia or geometry;
- raw figure-curve agreement;
- ABD-vs-RBD comparison pass;
- rendered output or timing;
- any passed `experiment.*` claim.

## Approach

Use the existing model-derived `SolverMABD.step()` path. A procedural four-point
heavy-top diagnostic body is pinned at a pivot with a `mabd:world_constraint`,
receives gravity through `mabd:gravity`, and uses polar mode with
`mabd:zero_stiffness_diagnostic`. The initial affine state is derived from the
same tilt and spin as the Phase 49 reference. The report records compact samples
of nutation, precession, pivot residual, affine shape spread, and finite rollout
status.

This mirrors the proven physical-pendulum model-derived lane pattern while
keeping heavy-top source gaps machine-readable.

## Artifacts

- `configs/experiments/single_body_heavy_top.yaml` gains a `mabd_newton`
  section and a lane report path.
- `src/mabd_reproduction/heavy_top_mabd.py` implements the model-derived
  rollout.
- `src/mabd_reproduction/heavy_top_reports.py` writes the new
  `mabd_newton` report.
- `src/mabd_reproduction/experiment_runner.py` and `scripts/run_experiment.py`
  expose `heavy_top_mabd_newton`.
- `reports/experiment_matrix/single_body_heavy_top_mabd_newton.json` is a
  compact committed report artifact.
- `docs/records/2026-05-18-phase50-heavy-top-mabd-newton-lane.md`,
  `docs/reference/claim-boundaries.md`, `docs/reference/paper-claims.yaml`,
  and `configs/experiments/paper_experiment_matrix.yaml` record that the missing
  M-ABD report blocker has become an incomplete diagnostic-lane blocker.

## Tests

RED tests cover:

- config parsing and matrix validation for `mabd_newton`;
- model-derived rollout uses Newton custom frequencies
  `mabd:body`, `mabd:world_constraint`, and `mabd:gravity`;
- report writer emits `baseline_lane = mabd_newton`, incomplete status,
  finite metrics, no pass gate, and retained blockers;
- CLI runner writes JSON-safe output for `heavy_top_mabd_newton`;
- docs/provenance validation records Phase 50 without overclaiming.

## Non-Goals

- No paper pass gate.
- No long-horizon or paper-curve agreement claim.
- No generated videos or raw simulation directories.
- No external baseline adapters.
