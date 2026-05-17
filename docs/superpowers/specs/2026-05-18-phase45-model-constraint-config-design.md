# Phase 45 Solver Model Constraint Config Design

## Purpose

Phase 45 removes the Phase 44 solver integration blocker for Newton model
constraint rows: `SolverMABD.step()` should build CPU oracle joint constraints
from registered `mabd:constraint` rows when no manual `configure_cpu_oracle(...)`
config is supplied.

This is still not a paper experiment pass. It is a model-schema-to-CPU-oracle
integration slice for dense CPU joint constraints only.

## Completion Audit

The full objective remains incomplete after Phase 44:

- No `experiment.*` claim is passed.
- `SolverMABD.step()` still rejects model-derived `mabd:constraint` rows.
- Newton `Contacts`, runtime `Control`, GPU/Warp kernels, paper scene assets,
  paper timing, external comparative baselines, rendered outputs, videos, and
  raw simulation logs remain outside verified scope.

Phase 45 targets only the second bullet.

## Design

`SolverMABD` will translate each model `mabd:constraint` row into an
`MABDCPUOracleConstraint` and pass those constraints into the existing
`solve_cpu_oracle_step(...)` path.

For each constraint row:

- `mabd:body_a` and `mabd:body_b` select the two `mabd:body` rows.
- The control tetrahedron for each side is the selected body row's
  `mabd:rest_point0` through `mabd:rest_point3`.
- `mabd:rank` and `mabd:constraint_type` select the joint spec:
  - rank `3` or explicit ball type: `ball_joint(...)`;
  - rank `5` or explicit hinge type: `hinge_joint(..., axis0)`;
  - rank `4` or explicit universal type:
    `universal_joint(..., axis0, axis1)`;
  - explicit prismatic type: `prismatic_joint(..., axis0)`.
- `mabd:cp_index` selects the ball-joint control point and defaults to `0`.
- `mabd:gradient_mode` maps to the existing CPU oracle modes:
  `0 -> finite_difference_oracle`, `1 -> paper_faithful`.

Manual `configure_cpu_oracle(...)` remains higher priority than the model path,
including when the model contains constraint rows. This keeps existing explicit
oracle tests and diagnostics stable.

## Guardrails

Phase 45 validates unsupported or ambiguous rows before handing them to the
oracle:

- invalid body indices are rejected;
- unknown `constraint_type` values are rejected;
- `mabd:rank` must match the derived joint rank;
- non-ball paper-faithful gradient mode may still be rejected by the existing
  CPU oracle because those nonlinear paper gradients are not implemented.

World-anchor constraints are not model-derived in this phase because there is
no registered `mabd:world_constraint` model frequency. Newton `Contacts`,
runtime `Control`, GPU/Warp kernels, paper scenes, timing, and pass gates remain
unchanged.

## Evidence

Phase 45 evidence must include:

- RED tests showing model-derived `mabd:constraint` rows fail before the
  change.
- GREEN tests showing `SolverMABD.step()` consumes model-derived ball, hinge,
  and universal constraints and matches explicit `MABDCPUOracleConfig`
  behavior.
- GREEN tests showing manual `configure_cpu_oracle(...)` still bypasses model
  constraint rows.
- GREEN tests showing invalid model constraint rows fail with clear messages.
- Updated claim boundaries, record, and docs validator that explicitly avoid
  claiming a paper experiment pass.

## Non-Goals

Phase 45 does not implement model-derived world constraints, contact ingestion,
Newton runtime `Control` ingestion, GPU/Warp kernels, scene loaders, paper
assets, paper timing, comparative baselines, rendering, videos, raw logs, or any
passed `experiment.*` claim.
