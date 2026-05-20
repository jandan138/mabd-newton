# Phase 71 Affine Box Static-Plane Active Set Design

## Purpose

Phase 70 still synthesizes `newton.Contacts` rows in the report layer from
diagnostic corner/plane checks. Phase 71 moves that bounded active-set
generation into vendored/local Newton so `SolverMABD` can produce a
`newton.Contacts` buffer from M-ABD affine state and model shapes.

This is a narrow solver-plumbing step toward contact support. It is not a
paper-faithful collision pipeline or experiment pass.

## Objective Audit

The active thread goal is full M-ABD reproduction. Current evidence does not
meet that goal:

- `docs/reference/paper-claims.yaml` records 19 method claims as `passed` and
  all 15 `experiment.*` claims as `intended`;
- `docs/reference/reproduction-gap-audit.yaml` records
  `full_reproduction_complete: false`;
- Phase 70 records `collision_detection_not_enabled_for_contacts_input` and
  `spinning_box_contacts_input_not_paper_faithful` blockers;
- `docs/reference/claim-boundaries.md` forbids claiming a passed spinning-box
  experiment, contact solver, paper-faithful affine collision/contact, or full
  paper reproduction from Phase 70 evidence.

Phase 71 addresses only the first blocker above for a single supported
shape-pair subset.

## Approach Options

1. Recommended: add `SolverMABD.detect_static_plane_contacts(state, ...)` for
   M-ABD box shapes against world-static infinite planes. It owns active-set
   generation inside Newton, returns ordinary `newton.Contacts`, and lets the
   existing Phase 69 contacts ingestion path perform the step.
2. Call `model.collide(...)` after copying affine state into rigid `body_q`.
   This would use Newton's existing collision pipeline, but it would be a rigid
   proxy and violate the existing claim boundary for affine collision.
3. Implement full Newton broadphase/narrowphase for affine bodies now. This is
   the long-term direction, but it is too broad for one verifiable phase because
   it mixes generic geometry, active-set persistence, body-body contact, and
   solver response.

We use option 1.

## Scope

Phase 71 adds:

- `MABDStaticPlaneCollisionSummary` on `SolverMABD`;
- `SolverMABD.detect_static_plane_contacts(state, max_contacts=None)`;
- support for Newton `GeoType.BOX` shapes attached to a Newton body mapped by
  `mabd:body_index`;
- support for world-static `GeoType.PLANE` shapes with `shape_body == -1` and
  infinite extents (`shape_scale[:2] == 0`);
- affine-corner signed-distance checks using M-ABD `q`, not rigid `body_q`;
- generated `newton.Contacts.rigid_contact_*` rows whose M-ABD side point is a
  body-space rest corner and whose plane side point lies on the static plane;
- a report lane that uses this solver-generated active set before calling
  `SolverMABD.step(..., contacts=contacts)`;
- committed diagnostic report and Phase71 claim-boundary/validator evidence.

The supported active-set scope is explicitly affine box corners against static
infinite planes.

## Non-Scope

Phase 71 does not implement or verify:

- broadphase, generic narrowphase, finite-plane clipping, mesh/SDF collision,
  sphere/capsule/cylinder contact, or body-body affine contact;
- friction, complementarity, IPC, continuous collision detection, contact
  persistence, or a generic inequality KKT contact solve;
- unmodified Newton support for affine-body dynamics;
- paper-faithful affine collision/contact;
- comparison pass gate, rendered agreement, runtime performance, any passed
  `experiment.*` claim, or full paper reproduction.

## Active-Set Algorithm

For each M-ABD box shape and static infinite plane shape:

1. Read the M-ABD body row mapped to the box shape's Newton body.
2. Read affine state `q = [A columns, t]` from `state.mabd`.
3. Build the eight local box corners from `shape_scale`.
4. Apply the box `shape_transform` to each corner into the M-ABD body/rest
   coordinate frame.
5. Evaluate each rest corner's world position by `A r + t`.
6. Compute signed distance with the static plane convention
   `normal dot x >= plane_offset`.
7. Emit one rigid contact row for each corner with negative signed distance,
   bounded by `max_contacts` if provided.

The contact row uses:

- `shape0 = box_shape`, `shape1 = plane_shape`;
- `point0 = rest_corner` in M-ABD body coordinates;
- `point1 = normal * plane_offset`;
- `normal = plane_normal`.

This matches the existing Phase 69 conversion path, which interprets the M-ABD
side point as a rest point for `MABDCPUOraclePlaneConstraint`.

## Report Contract

The new diagnostic lane is written by
`write_spinning_box_affine_static_plane_contacts_report`, emits
`reports/experiment_matrix/single_body_spinning_box_affine_static_plane_contacts.json`,
and calls `SolverMABD.step(..., contacts=contacts)` with the
solver-generated `newton.Contacts` buffer. It records:

```text
solver_mode = solver_mabd_affine_static_plane_contacts_diagnostic
backend = cpu_numpy_newton_solver_mabd_affine_static_plane_contacts_diagnostic
status = incomplete
baseline_lane = mabd_newton
```

Top-level `observed` includes:

- `affine_static_plane_contact_policy =
  solver_mabd_detect_affine_box_static_plane_contacts`;
- `affine_static_plane_contact_scope =
  diagnostic_affine_box_corners_vs_static_infinite_planes_no_lane_gate`;
- `affine_static_plane_contact_source =
  SolverMABD.detect_static_plane_contacts`;
- `contacts_input_summary_source = last_contacts_input_summary`;
- max generated/read/skipped/overflow/contact residual metrics;
- `blocking_reasons` containing
  `spinning_box_affine_static_plane_contacts_not_paper_faithful`.

The report does not contain `lane_gate_status`.

## Tests

New tests cover:

- generated contacts for a penetrating affine box against a static plane;
- no generated contacts when affine state is separated from the plane;
- `max_contacts` capacity truncation and overflow accounting;
- parity between `detect_static_plane_contacts(...)+step(...)` and an
  equivalent explicit `MABDCPUOraclePlaneConstraint` solve;
- report writer, runner, CLI, committed artifact, and docs validator contract.

All checks use the project environment:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
```
