# Phase 47 Solver Model Gravity Config Design

## Purpose

Phase 47 removes the model-derived solver blocker for uniform gravity:
`SolverMABD.step()` should be able to build `MABDCPUOracleConfig.gravity` from
registered Newton model rows when no manual `configure_cpu_oracle(...)` config
is supplied.

This is still not a paper experiment pass. It is a model-schema-to-CPU-oracle
integration slice for the Phase 32 gravity force mapping.

## Completion Audit

The full objective remains incomplete after Phase 46:

- No `experiment.*` claim is passed.
- Uniform gravity can be passed through explicit `MABDCPUOracleConfig.gravity`,
  but not through Newton model-derived `SolverMABD.step()`.
- Physical-pendulum and heavy-top style model paths still require hand-built
  CPU oracle configs for gravity.
- Newton `Contacts`, runtime `Control`, GPU/Warp kernels, paper scene assets,
  paper timing, external comparative baselines, rendered outputs, videos, and
  raw simulation logs remain outside verified scope.

Phase 47 targets only the second bullet.

## Design

`SolverMABD` will register a `mabd:gravity` custom frequency and translate
enabled rows into the single uniform gravity vector accepted by
`MABDCPUOracleConfig`.

For each gravity row:

- `mabd:gravity_enabled` controls whether the row participates.
- `mabd:gravity_vector` stores a world-space acceleration vector in m/s^2.
- zero enabled rows produce `gravity=None`;
- one enabled row produces that vector;
- more than one enabled row is rejected to keep the uniform-gravity contract
  unambiguous.

Manual `configure_cpu_oracle(...)` remains higher priority than the model path,
including when the model contains gravity rows.

## Guardrails

Phase 47 validates unsupported or ambiguous rows before handing them to the
oracle:

- multiple enabled gravity rows are rejected;
- malformed vector shapes continue to be rejected by the existing CPU oracle or
  custom attribute storage;
- this does not change the Phase 32 gravity force formula;
- this does not implement scene pass gates, Contacts, runtime Control, GPU/Warp
  kernels, paper timing, or rendered output.

## Evidence

Phase 47 evidence must include:

- RED tests showing model-derived gravity rows fail before registration and
  translation.
- GREEN tests showing `SolverMABD.step()` consumes one enabled model gravity row
  and matches explicit `MABDCPUOracleConfig.gravity` behavior.
- GREEN tests showing disabled gravity rows are ignored.
- GREEN tests showing multiple enabled gravity rows fail with a clear message.
- GREEN tests showing manual `configure_cpu_oracle(...)` still bypasses model
  gravity rows.
- Updated claim boundaries, record, and docs validator that explicitly avoid
  claiming a gravity-scene or paper-experiment pass.

## Non-Goals

Phase 47 does not implement heavy-top reproduction, physical-pendulum scene
pass, Newton `Contacts`, Newton runtime `Control` ingestion, GPU/Warp kernels,
scene loaders, paper assets, paper timing, comparative baselines, rendering,
videos, raw logs, or any passed `experiment.*` claim.
