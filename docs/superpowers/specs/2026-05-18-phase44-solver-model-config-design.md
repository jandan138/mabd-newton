# Phase 44 Solver Model Config Design

## Purpose

Phase 44 removes one core solver integration blocker: `SolverMABD.step()` should
be able to run a deterministic CPU M-ABD step from Newton `mabd:body` model rows
without requiring a test-only `configure_cpu_oracle(...)` call.

This is still not a paper experiment pass. The implementation remains a CPU
body-config path with explicit unsupported boundaries for model constraint rows,
Newton `Control`, `Contacts`, GPU/Warp kernels, paper scene assets, timings, and
comparative baselines.

## Current Gap

`SolverMABD.step()` currently raises unless `configure_cpu_oracle(...)` is called
manually. That proves state I/O and the CPU oracle, but not that a normal Newton
model carrying `mabd:body` rows can drive the solver.

Existing `mabd:body` rows store material constants and rotation mode, but they
do not store the body rest tetrahedron, point masses, or material volume needed
to construct `SingleBodyABDPrecompute` from the model.

## Design

Add model-side body data:

- `mabd:rest_point0`, `mabd:rest_point1`, `mabd:rest_point2`,
  `mabd:rest_point3`: four rest control points for the affine body.
- `mabd:point_mass0`, `mabd:point_mass1`, `mabd:point_mass2`,
  `mabd:point_mass3`: optional explicit lumped point masses. The default value
  is `-1.0`, meaning "derive uniform point masses from density and volume".
- `mabd:volume`: optional material volume. The default value is `-1.0`, meaning
  "derive the tetrahedron volume from the four rest points".

`SolverMABD` will build a cached `MABDCPUOracleConfig` from model rows when no
manual CPU oracle config is supplied. For each body row it will:

- read the four rest points;
- derive volume from `mabd:volume` or `tetra_volume(rest_points)`;
- use explicit point masses if all four point masses are nonnegative;
- otherwise derive uniform masses as `density * volume / 4`;
- build `SingleBodyABDPrecompute.from_linear_elastic_points(...)`;
- map `polar_mode`: `0 -> none`, `1 -> polar`, `2 -> no_polar`;
- use `rest_q = pack_q(identity, zero)`;
- include enabled `mabd:control` rows through `actuation_specs_from_model(model)`.

The cached model-derived config is invalidated by `notify_model_changed()`.

## Guardrails

The automatic model-derived path rejects model `mabd:constraint` rows in Phase
44 because the model schema does not yet store per-constraint control
tetrahedra. Users must still supply a manual `MABDCPUOracleConfig` when testing
constraint systems.

The path also keeps current rejections for Newton runtime `Control` and
`Contacts` arguments. Contact force mapping and model control-row force
assembly remain CPU diagnostics, not paper-faithful scene contact or robot
control reproduction.

## Evidence

Phase 44 evidence must include:

- RED tests showing unconfigured `SolverMABD.step()` fails before the change.
- GREEN tests showing unconfigured `SolverMABD.step()` advances single-body and
  multi-body custom state from model-derived rest points, masses, materials, and
  rotation mode.
- GREEN tests showing enabled model control rows are consumed by the
  model-derived path.
- GREEN tests showing constraint rows are explicitly rejected with a clear
  message in the automatic path.
- Updated claim boundaries and validation record that do not claim any
  `experiment.*` pass.

## Non-Goals

Phase 44 does not implement automatic model-derived joint specs, tree/chain
scene solving from model rows, `Contacts` ingestion, Newton `Control` ingestion,
GPU/Warp kernels, rendered outputs, timings, or any paper experiment pass.
