# Phase 70 Contacts Input Report Lane Design

## Purpose

Phase 69 proved that vendored/local Newton `SolverMABD.step(..., contacts=...)`
can read bounded `newton.Contacts.rigid_contact_*` rows and convert the
supported static-geometry subset into existing M-ABD point-plane normal
constraints. Phase 70 connects that plumbing to the single-body spinning-box
diagnostic report stack so the experiment runner can exercise the `Contacts`
input path end to end.

This is a reproduction infrastructure slice. It is not a paper experiment pass.

## Approach Options

1. Recommended: add a dedicated spinning-box contacts-input diagnostic lane.
   This keeps Phase 68 `mabd:plane_constraint` evidence stable, adds a separate
   report path, and makes the distinction between model-row constraints and
   `newton.Contacts` input machine-checkable.
2. Replace the Phase 68 model-plane lane with `Contacts` input. This would
   reduce duplicate code, but it would blur existing evidence provenance and
   make it harder to audit the difference between custom model rows and runtime
   contact buffers.
3. Implement Newton collision-pipeline active-set generation now. This would
   move closer to a paper-faithful contact stack, but it is a larger subsystem
   and would mix collision correctness, report plumbing, and solver behavior in
   one phase.

We use option 1. It advances the Newton-first path while preserving claim
boundaries and leaving collision generation as a separate future phase.

## Scope

Phase 70 adds:

- config field `paper_horizon.contacts_input_output_report`;
- CLI lane `spinning_box_contacts_input`;
- runner function `run_spinning_box_contacts_input`;
- report writer `write_spinning_box_contacts_input_report`;
- transient Newton model helper that creates an M-ABD body shape and static
  plane shape, builds `newton.Contacts` rows from already-diagnostic active
  point-plane contacts, and passes them into `SolverMABD.step(..., contacts=...)`;
- committed report
  `reports/experiment_matrix/single_body_spinning_box_contacts_input.json`;
- docs, records, and validator checks proving this remains incomplete evidence.

## Non-Scope

Phase 70 does not implement or verify:

- collision detection, broadphase, narrowphase, or active-set generation inside
  Newton;
- contact solver behavior, IPC, friction, complementarity, continuous collision
  detection, or dynamic body-body M-ABD contact;
- paper-faithful affine collision/contact;
- generic inequality-constrained M-ABD KKT;
- paper-faithful M-ABD stepping;
- comparison pass gate, rendered-output agreement, runtime performance, any
  passed `experiment.*` claim, or full paper reproduction.

The contact rows are derived from the existing diagnostic corner/plane check.
The report must label this as
`newton.Contacts.rigid_contact_static_plane_rows_from_diagnostic_corners`, not
as collision detection.

## Architecture

The existing `single_body_reports.py` paper-horizon rollout already has separate
branches for no contact response, explicit contact force, direct CPU-oracle
normal constraints, and SolverMABD model-plane rows. Phase 70 adds a fifth
mutually exclusive mode:

```text
free SolverMABD model step
  -> diagnostic corner/plane penetration check
  -> Newton Contacts buffer with M-ABD box shape vs static plane shape
  -> SolverMABD.step(..., contacts=contacts)
  -> last_contacts_input_summary recorded into report metrics
```

The helper builds a transient Newton model with:

- one `mabd:body` custom row;
- one box shape attached to that Newton body;
- one world-static plane shape with `shape_body == -1`;
- no `mabd:plane_constraint` custom rows.

When no active diagnostic contacts exist, the helper calls
`SolverMABD.step(..., contacts=None)` and records no generated contact
constraints. When active rows exist, the helper creates a bounded
`newton.Contacts` buffer and lets Phase 69 `SolverMABD` plumbing generate the
point-plane constraints.

## Report Contract

The report has:

```text
solver_mode = solver_mabd_contacts_input_diagnostic
backend = cpu_numpy_newton_solver_mabd_contacts_input_diagnostic
status = incomplete
baseline_lane = mabd_newton
```

Top-level `observed` must include:

- `contacts_input_policy =
  solver_mabd_contacts_input_free_predict_then_static_plane_constraints`;
- `contacts_input_scope =
  diagnostic_only_static_geometry_plane_constraints_no_lane_gate`;
- `contacts_input_source =
  newton.Contacts.rigid_contact_static_plane_rows_from_diagnostic_corners`;
- `contacts_input_summary_source = last_contacts_input_summary`;
- `contact_constraint_policy =
  free_predict_then_active_point_plane_normal_constraints`;
- `rank_filter_policy = increment_map_row_rank_filter`;
- `max_contacts_input_rigid_contact_count`;
- `max_contacts_input_rows_read`;
- `max_contacts_input_generated_plane_constraint_count`;
- `max_contacts_input_skipped_contact_count`;
- `max_contacts_input_overflow_count`;
- `max_contacts_input_constraint_residual_norm`;
- `contacts_input_reduced_free_predicted_penetration`;
- `contacts_input_results`;
- `blocking_reasons`.

Each per-timestep result must include matching contacts-input policy/source
fields, finite residuals, and compact trajectory samples only.

The report must not contain `lane_gate_status` and must not mark the spinning-box
claim passed.

## Config And CLI

`configs/experiments/single_body_spinning_box.yaml` adds:

```yaml
paper_horizon:
  contacts_input_output_report: reports/experiment_matrix/single_body_spinning_box_contacts_input.json
```

The config validator requires this path to:

- start with the spinning-box matrix output stem;
- end in `.json`;
- be distinct from all other spinning-box lane reports.

The CLI adds:

```bash
scripts/run_experiment.py --lane spinning_box_contacts_input ...
```

Like other side lanes, it requires `--output` and rejects `--output-root`.

## Evidence Boundaries

`docs/reference/claim-boundaries.md` gains Phase 70 bullets stating that this
phase verifies only a diagnostic report lane using `newton.Contacts` static
geometry rows consumed by `SolverMABD.step(..., contacts=...)`.

`docs/reference/paper-claims.yaml` remains unchanged:

- all `experiment.*` claims stay `intended`;
- `method.force_mapping.point_load_penalty_contact` stays scoped to CPU-oracle
  force mapping, not collision detection or a contact solver.

## Tests

New and updated tests cover:

- config parsing and path validation;
- contacts-input step helper parity against equivalent explicit
  `MABDCPUOraclePlaneConstraint` solves and Phase 69
  `SolverMABD.step(..., contacts=...)` plumbing;
- the no-active-contact helper branch, which must call
  `SolverMABD.step(..., contacts=None)` and record zero generated contact
  constraints;
- report writer contract and blockers;
- runner function and CLI dispatch;
- committed report artifact contract;
- docs validator Phase 70 checks;
- unchanged `experiment.*` claim statuses.

All tests run with:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
```

and validation with:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
```
