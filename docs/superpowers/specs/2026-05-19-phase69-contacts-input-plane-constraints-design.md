# Phase 69 Contacts Input Plane Constraints Design

Date: 2026-05-19

## Objective

Phase 69 lets vendored Newton `SolverMABD.step(..., contacts=...)` consume
precomputed Newton rigid contact rows and translate a narrow supported subset
into existing M-ABD point-plane normal constraint rows.

This is a solver input-plumbing slice. It removes the unconditional
`Contacts input` rejection for a bounded CPU diagnostic path. It does not add
collision detection, contact generation, active-set generation inside Newton,
friction, complementarity, IPC, continuous collision detection, body-body
affine contact, paper-faithful affine collision/contact, a report lane gate, or
any passed `experiment.*` claim.

## Current Gap

Phase 67 added explicit `mabd:plane_constraint` model rows.
Phase 68 proved those rows can drive a spinning-box diagnostic report lane.
However, `SolverMABD.step()` still rejects any non-`None` `contacts` argument,
so a Newton collision pipeline cannot even hand existing contact rows to the
M-ABD solver.

The Newton contact buffer already stores rigid contact count, shape ids,
body-frame contact points, and contact normals. Phase 69 consumes that data
only after another caller has produced it.

## Scope

Supported conversion:

- read `Contacts.rigid_contact_count` and rigid contact arrays on CPU through
  `.numpy()`;
- cap reads at `Contacts.rigid_contact_max` and record overflow count when the
  reported count exceeds capacity;
- map Newton shape ids to Newton body ids through `model.shape_body`;
- map Newton body ids to M-ABD body rows through `mabd:body_index`;
- convert a contact row only when exactly one side maps to an M-ABD body row;
- use the mapped side's body-frame contact point as the M-ABD rest point;
- use the opposite side's contact point to define the plane offset;
- flip the contact normal when the mapped M-ABD body is shape 1 rather than
  shape 0;
- append generated plane rows to the existing explicit/model-derived
  `MABDCPUOracleConfig.plane_constraints`;
- keep the existing dense CPU oracle rank filter and residual diagnostics;
- record a `last_contacts_input_summary` on `SolverMABD`.

Unsupported contact rows are skipped, not guessed:

- rows with invalid shape ids;
- rows where neither side maps to an M-ABD body;
- rows where both sides map to M-ABD bodies;
- rows requiring shape-transform reconstruction beyond the stored contact
  point buffers.

`Control` input remains unsupported in this phase.

## Semantics

For each consumed rigid contact, let `n` be Newton's
`rigid_contact_normal`, pointing from shape 0 toward shape 1.

If shape 0 maps to M-ABD body row `b`, Phase 69 creates:

```text
body = b
rest_point = rigid_contact_point0
plane_normal = n
plane_offset = dot(n, rigid_contact_point1)
```

If shape 1 maps to M-ABD body row `b`, Phase 69 creates:

```text
body = b
rest_point = rigid_contact_point1
plane_normal = -n
plane_offset = dot(-n, rigid_contact_point0)
```

This convention preserves the already tested `MABDCPUOraclePlaneConstraint`
normalization behavior. It is diagnostic contact-row ingestion, not a general
or paper-faithful contact model.

## Summary Contract

`SolverMABD.last_contacts_input_summary` is `None` when `contacts is None`.
When contacts are supplied it records:

- `policy = "rigid_contacts_to_point_plane_constraints_diagnostic"`;
- `rigid_contact_count`;
- `rigid_contact_capacity`;
- `rigid_contact_overflow_count`;
- `rigid_contact_rows_read`;
- `generated_plane_constraint_count`;
- `skipped_contact_count`;
- `source = "newton.Contacts.rigid_contact_*"`;
- `scope = "diagnostic_only_static_geometry_plane_constraints"`.

The summary is intentionally not a pass gate. It exists so reports can later
prove whether Newton `Contacts` were actually consumed.

## Claim Boundaries

Phase 69 may verify only bounded `Contacts` input plumbing for
`SolverMABD.step()`.

It must not modify `docs/reference/paper-claims.yaml`. All `experiment.*`
claims remain `intended`, and the existing contact method claim remains bounded
to CPU-oracle force/row mapping evidence.

Phase 69 does not verify:

- collision detection;
- broadphase or narrowphase correctness;
- active-set generation inside Newton;
- contact solver behavior;
- friction;
- complementarity;
- IPC;
- continuous collision detection;
- body-body affine contact;
- paper-faithful affine collision/contact;
- generic inequality-constrained M-ABD KKT;
- comparison pass gates;
- rendered-output agreement;
- runtime performance;
- any passed `experiment.*` claim;
- full paper reproduction.

Forbidden wording includes claiming that Phase 69 implements paper-faithful
M-ABD contact, that unmodified Newton supports M-ABD contact, that the
spinning-box experiment passes, or that full paper reproduction is complete.

## Tests

Phase 69 requires test-first coverage for:

- `SolverMABD.step()` consuming a manual Newton `Contacts` buffer for a contact
  between one M-ABD shape and one static shape;
- generated contact plane constraints matching the explicit
  `MABDCPUOracleConfig(plane_constraints=[...])` result;
- normal flipping when the M-ABD body is on shape 1;
- skipping unsupported rows and recording counts;
- detecting duplicate `mabd:body_index` rows as an ambiguous mapping;
- preserving `contacts=None` behavior and `Control` rejection;
- docs/record/validator checks for the spec, plan, record, claim boundaries,
  contact-summary contract, paper-claim status preservation, and overclaim
  rejection.

## Verification

Focused commands:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_mabd_phase4_solver_step
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest newton.tests.test_mabd_phase4_solver_step
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_phase0_bootstrap
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
```

Final gates:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest newton.tests.test_mabd_phase4_solver_step
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/env/readiness_check.py
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"
git diff --check
```
