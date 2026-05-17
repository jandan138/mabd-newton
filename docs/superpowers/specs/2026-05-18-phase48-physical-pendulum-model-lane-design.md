# Phase 48 Physical Pendulum Model-Derived MABD Lane Design

## Purpose

Phase 48 moves the physical-pendulum `mabd_newton` lane from a hand-built
`MABDCPUOracleConfig` rollout to a Newton `ModelBuilder` plus
`SolverMABD.step()` model-derived rollout. This consumes the model-derived
body, world-constraint, and gravity storage added in Phases 44, 46, and 47.

This is still not a passed physical-pendulum paper experiment. It is a
lane-plumbing and provenance slice: the same procedural diagnostic pendulum is
stepped through Newton model rows instead of a manual CPU-oracle config.

## Completion Audit

The full reproduction objective remains incomplete after Phase 47:

- no `experiment.*` claim is passed;
- physical-pendulum paper geometry remains undisclosed and unverified;
- the physical-pendulum `mabd_newton` report exists but still uses the
  development rollout helper that manually constructs `MABDCPUOracleConfig`;
- Newton `Contacts`, runtime `Control`, GPU/Warp kernels, rendered outputs,
  paper timing, and comparative pass gates remain outside verified scope.

Phase 48 targets only the third bullet.

## Design

Add a model-derived physical-pendulum M-ABD rollout path:

- keep `roll_out_physical_pendulum_mabd_development(...)` on the existing
  manual CPU-oracle diagnostic path;
- add `roll_out_physical_pendulum_mabd_model_derived(...)` for the formal
  `mabd_newton` lane;
- build a Newton model using `SolverMABD.register_custom_attributes(...)`;
- add one `mabd:body` row with the procedural pendulum rest points and explicit
  point masses from `mabd_development`;
- set `mabd:young_modulus = 0.0` so the model-derived body matches the existing
  zero-stiffness diagnostic `SingleBodyABDPrecompute.from_points(...)` lane;
- set `mabd:polar_mode` from the requested rotation mode;
- add one `mabd:world_constraint` row for the pivot anchor;
- add one enabled `mabd:gravity` row for `gravity_m_s2`;
- use `SolverMABD(model).step(state, state, None, None, dt)` for each rollout
  step;
- record `solver_model_config_source = "newton_model_derived"` in the
  `mabd_newton` report.

The report keeps `full_experiment_claim_passed = False`, `status =
incomplete`, and `pendulum_geometry_unknown` because the model-derived plumbing
does not solve the missing paper-scene evidence.

## Guardrails

Phase 48 must not:

- claim a physical-pendulum experiment pass;
- mark any `experiment.*` claim as passed;
- change the analytic reference, RBD baseline, comparison thresholds, or pass
  gates;
- claim paper-faithful physical-pendulum geometry;
- claim Newton `Contacts`, runtime `Control`, GPU/Warp kernels, rendered
  output, raw logs, paper timing, or full paper reproduction.

## Evidence

Phase 48 evidence must include:

- RED tests showing the model-derived physical-pendulum rollout API and report
  provenance fields are missing before implementation;
- GREEN tests showing the model-derived rollout matches the existing manual
  diagnostic rollout within numerical tolerance for the procedural pendulum;
- GREEN tests showing the `mabd_newton` report records
  `solver_model_config_source = "newton_model_derived"` while staying
  incomplete;
- docs-validator and bootstrap guardrails that require the Phase48 record,
  spec, plan, model-derived report provenance, and claim-boundary text;
- no generated videos, raw logs, or run directories committed.

## Non-Goals

Phase 48 does not implement paper geometry, contact solve, runtime `Control`,
GPU/Warp kernels, rendering, videos, raw logs, paper timing, comparative pass
gates, or full paper reproduction.
