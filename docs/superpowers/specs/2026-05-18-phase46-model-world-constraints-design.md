# Phase 46 Solver Model World Constraint Config Design

## Purpose

Phase 46 removes the Phase 45 solver integration blocker for Newton model
world-anchor rows: `SolverMABD.step()` should build CPU oracle world
constraints from registered `mabd:world_constraint` rows when no manual
`configure_cpu_oracle(...)` config is supplied.

This is still not a paper experiment pass. It is a model-schema-to-CPU-oracle
integration slice for dense CPU world-anchor constraints only.

## Completion Audit

The full objective remains incomplete after Phase 45:

- No `experiment.*` claim is passed.
- Physical-pendulum diagnostics still use explicit `MABDCPUOracleWorldConstraint`
  wiring rather than Newton model storage.
- Newton `Contacts`, runtime `Control`, GPU/Warp kernels, paper scene assets,
  paper timing, external comparative baselines, rendered outputs, videos, and
  raw simulation logs remain outside verified scope.

Phase 46 targets only the second bullet.

## Design

`SolverMABD` will register a `mabd:world_constraint` custom frequency and
translate each row into an `MABDCPUOracleWorldConstraint` in the model-derived
CPU oracle config path.

For each world-constraint row:

- `mabd:world_body` selects one `mabd:body` row.
- `mabd:world_rest_point` is the body-space point pinned by the constraint.
- `mabd:world_point` is the target world-space point.
- The existing dense CPU oracle computes the point Jacobian, residual, and
  reaction multiplier.

Manual `configure_cpu_oracle(...)` remains higher priority than the model path,
including when the model contains world-anchor rows. This keeps explicit oracle
tests and existing diagnostics stable.

## Guardrails

Phase 46 validates unsupported or ambiguous rows before handing them to the
oracle:

- invalid `mabd:world_body` indices are rejected;
- malformed vector shapes continue to be rejected by the existing CPU oracle;
- world constraints keep the existing CPU-oracle limitation that topology must
  be `dense`;
- no Newton `Contacts`, runtime `Control`, GPU/Warp kernel, paper scene, timing,
  or pass-gate behavior changes.

## Evidence

Phase 46 evidence must include:

- RED tests showing model-derived world-anchor rows fail before registration and
  translation.
- GREEN tests showing `SolverMABD.step()` consumes a model-derived world anchor,
  caches it, pins the selected point, and exposes a dense reaction vector.
- GREEN tests showing manual `configure_cpu_oracle(...)` still bypasses model
  world-anchor rows.
- GREEN tests showing invalid world-anchor body references fail with clear
  messages.
- Updated claim boundaries, record, and docs validator that explicitly avoid
  claiming a paper experiment pass.

## Non-Goals

Phase 46 does not implement Newton `Contacts`, Newton runtime `Control`
ingestion, GPU/Warp kernels, scene loaders, paper assets, paper timing,
comparative baselines, rendering, videos, raw logs, or any passed
`experiment.*` claim.
