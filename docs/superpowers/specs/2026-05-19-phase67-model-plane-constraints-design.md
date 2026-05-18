# Phase 67 Model Plane Constraints Design

Date: 2026-05-19

## Objective

Phase 67 connects the vendored/local Newton M-ABD CPU-oracle point-plane normal
constraint primitive to the `SolverMABD.step()` model-derived path. The goal is
to let a Newton `ModelBuilder` carry explicit `mabd:plane_constraint` rows that
become `MABDCPUOraclePlaneConstraint` entries when `SolverMABD` builds its
cached `MABDCPUOracleConfig`.

This is a solver plumbing capability slice. It does not add collision
detection, active-set generation, friction, IPC, complementarity, continuous
collision detection, paper-faithful affine contact, or any passed experiment
claim.

## Current Gap

Phase 63 added `MABDCPUOraclePlaneConstraint` and diagnostic report usage, but
that support is available only through an explicit `MABDCPUOracleConfig`.
`SolverMABD.step()` can currently derive these model-backed CPU-oracle fields:

- `mabd:body`;
- `mabd:constraint`;
- `mabd:world_constraint`;
- `mabd:gravity`;
- `mabd:control`.

It cannot derive explicit point-plane rows from the Newton model. That means
scene-like tests must bypass the model storage layer to exercise the normal
constraint primitive.

## Scope

Phase 67 adds:

- `SolverMABD.MABD_PLANE_CONSTRAINT_FREQUENCY = "mabd:plane_constraint"`;
- registration of the `mabd:plane_constraint` custom frequency;
- model attributes:
  - `mabd:plane_body`;
  - `mabd:plane_rest_point`;
  - `mabd:plane_normal`;
  - `mabd:plane_offset`;
  - `mabd:plane_active`;
- `_plane_constraint_from_model_row(row, body_count)`;
- `_cpu_oracle_config_from_model()` extraction into
  `MABDCPUOracleConfig(plane_constraints=...)`;
- mirrored TDD coverage in `tests/test_mabd_phase4_solver_step.py` and
  `vendor/newton/newton/tests/test_mabd_phase4_solver_step.py`;
- Phase 67 claim-boundary text, record, and validator gates.

Manual `configure_cpu_oracle(...)` precedence remains unchanged: an explicit
manual config ignores model-derived plane rows and leaves
`model_cpu_oracle_config` unset.

The existing `contacts` argument to `SolverMABD.step()` remains unsupported and
continues to raise `NotImplementedError`.

## Model Attribute Semantics

Each `mabd:plane_constraint` row stores a single explicit point-plane normal
constraint:

```text
unit_normal dot (J(rest_point) q_next) = normalized_offset
```

The row maps to `MABDCPUOraclePlaneConstraint` as:

- `mabd:plane_body`: integer index into `mabd:body` rows, default `-1`;
- `mabd:plane_rest_point`: material point, default `(0, 0, 0)`;
- `mabd:plane_normal`: world-space plane normal, default `(0, 1, 0)`;
- `mabd:plane_offset`: signed plane offset using the Phase 63 convention,
  default `0.0`;
- `mabd:plane_active`: integer active flag, default `1`.

`_plane_constraint_from_model_row` validates the body index before constructing
the dataclass. Normal shape and zero-normal validation remain in the CPU
oracle's existing `MABDCPUOraclePlaneConstraint` path, so zero normals still
raise a `ValueError` containing `plane_normal`. Phase 67 does not broaden the
CPU-oracle primitive to add NaN/Inf normal validation.

## Claim Boundaries

Phase 67 verifies only that explicit model rows are extracted into the
vendored/local Newton CPU-oracle plane-constraint data structure and used by
`SolverMABD.step`.

Phase 67 must not modify `docs/reference/paper-claims.yaml`: all currently
passed method claims stay unchanged, all `experiment.*` claims stay
`intended`, and no contact-related method claim is widened beyond its existing
conflict note. In particular, Phase 67 does not widen
`method.force_mapping.point_load_penalty_contact`, which remains CPU-oracle
force/row mapping evidence only and not collision detection or a full contact
solver.

Phase 67 does not verify:

- collision detection;
- broadphase or narrowphase;
- active-set generation;
- inequality-constrained contact;
- Newton `Contacts` ingestion;
- complementarity;
- friction;
- IPC;
- continuous collision detection;
- paper-faithful affine collision or contact;
- paper-faithful M-ABD stepping;
- comparison pass gates;
- rendered agreement;
- runtime performance;
- external baselines;
- any `experiment.*` pass;
- full paper reproduction.

Forbidden wording includes claiming that unmodified Newton supports M-ABD
point-plane contact, that rigid `body_q` proxy collision is paper-faithful
affine collision, that Phase 67 implements a contact solver, or that full paper
reproduction is complete.

## Tests

Phase 67 requires test-first coverage for:

- model-derived plane rows matching an explicit
  `MABDCPUOracleConfig(plane_constraints=[...], topology="dense")` result;
- non-unit normals and nonzero offsets preserving the Phase 63 normalized
  offset convention;
- inactive `mabd:plane_active = 0` rows being ignored by the CPU oracle result;
- inactive rows still being extracted into `model_cpu_oracle_config` with
  `active=False`;
- out-of-range `mabd:plane_body` raising `ValueError`;
- zero `mabd:plane_normal` raising `ValueError`;
- manual `configure_cpu_oracle(...)` on a fresh solver taking precedence over
  model plane rows without building `model_cpu_oracle_config`;
- `contacts` input remaining unsupported and raising `NotImplementedError`;
- docs/provenance validation requiring this spec, plan, record, claim-boundary
  text, a model-path smoke, exact paper-claim status boundaries, and unchanged
  contact/method claim boundaries.

The model-path numerical test must include nonzero tangent motion, assert a
finite post-step point-plane residual, compare state against the explicit
config path, and assert `last_step_result` plane-row counters.

## Verification

Required focused commands:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_mabd_phase4_solver_step
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest newton.tests.test_mabd_phase4_solver_step
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_phase0_bootstrap
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
```

Required final gates:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest newton.tests.test_mabd_phase4_solver_step
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/env/readiness_check.py
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"
git diff --check
```
