# Phase 63 Point-Plane Normal Constraints Design

Date: 2026-05-19

## Objective

Phase 63 adds a Newton-only CPU oracle constraint for scalar point-plane normal
projection rows and uses it in a spinning-box diagnostic lane. The goal is to
replace the Phase 62 explicit penalty-force response diagnostic with a bounded
KKT contact slice that can enforce selected active point normal equalities while
preserving tangential freedom.

This phase is a diagnostic contact-row capability slice. It does not claim
Incremental Potential Contact, generic inequality-constrained M-ABD KKT,
broadphase, narrowphase, friction, continuous collision, paper-faithful affine
collision, or a passed spinning-box experiment.

## Current Gap

The current M-ABD CPU oracle supports:

- unconstrained affine body steps;
- body-body joint constraints;
- 3D world anchor constraints for pinning an affine point to a full world
  position;
- point-plane penalty-force diagnostics and a Phase 62 explicit external-force
  response lane.

The spinning-box paper scene uses a frictionless surface. A 3D world anchor is
too restrictive because it pins tangential point coordinates. A penalty force is
too weak as a solver artifact because it does not enforce the nonpenetration
condition in the KKT solve and Phase 62 showed no reduction in the recorded
maximum penetration. The missing minimal primitive is a scalar row:

```text
n^T (J(rest_point) q_next) = plane_offset
```

for active point-plane contacts.

## Design

### Newton CPU Oracle Constraint

Add `MABDCPUOraclePlaneConstraint` to the vendored Newton M-ABD CPU oracle. Each
constraint stores:

- `body`: constrained body index;
- `rest_point`: affine-body material point;
- `plane_normal`: world-space normal;
- `plane_offset`: scalar plane offset using the signed-distance convention
  `unit_normal dot x - normalized_offset`;
- `active`: boolean, so inactive rows can be represented without changing
  higher-level lane code.

The oracle normalizes `plane_normal` and rescales `plane_offset` to match the
existing penalty-contact convention. Active rows enter the dense KKT system as
one scalar row per accepted constraint:

```text
J_plane = unit_normal^T J(rest_point)
lower_rhs = -(unit_normal^T J(rest_point) q_n - normalized_offset)
```

With the existing residual-corrected KKT convention this enforces the accepted
active point's post-step normal coordinate exactly at the plane. The row is
multiplied by the same body increment map used for polar rotated bodies, so the
constraint works with existing `rotation_mode="polar"` CPU oracle bodies.

Inactive rows are ignored. Bad body indices, bad vector shapes, and zero plane
normals raise `ValueError`.

Multiple point-plane rows can be linearly dependent, especially four cube
corners on one face against one plane. To keep the diagnostic dense dual solve
well-posed, active rows are filtered in assembly order by numerical row rank
after applying the body's increment map. Rows that do not increase rank are
skipped and counted in diagnostics. Phase 63 records this as rank filtering,
not as a paper contact algorithm.

### Spinning-Box Active-Set Diagnostic

Add a new report lane that runs each paper-horizon step with a two-pass active
set:

1. Run the existing unconstrained M-ABD CPU oracle step.
2. Evaluate all configured cube corners against the plane on the free predicted
   state.
3. If no corner penetrates, accept the free step.
4. If one or more corners penetrate, rerun the same step with active scalar
   plane constraints for those penetrating corners after rank filtering.
5. Record free-predicted penetration, constrained post-step penetration,
   requested row count, accepted row count, skipped row count, residual norm,
   and threshold status.

This policy is intentionally diagnostic. It is not a nonlinear complementarity
solver; it does not add friction; it does not iterate until active-set
convergence; it does not guarantee all inactive points remain outside the
plane; it does not do continuous collision detection. It is still a better
Newton-only contact primitive than Phase 62 because accepted contact rows enter
the KKT system instead of being applied as an explicit force in the next step.

### Report Contract

Add a separate output report so Phase 61/62 evidence stays auditable:

```text
reports/experiment_matrix/single_body_spinning_box_normal_constraint.json
```

The report uses:

```text
solver_mode = mabd_cpu_oracle_point_plane_normal_constraint_diagnostic
status = incomplete
baseline_lane = mabd_newton
```

The observed payload records:

- `contact_constraint_policy =
  "free_predict_then_active_point_plane_normal_constraints"`;
- `contact_constraint_scope = "diagnostic_only_no_lane_gate"`;
- one result per configured paper step size;
- `max_free_predicted_contact_penetration_m`;
- `max_constrained_contact_penetration_m`;
- `max_requested_plane_constraint_count`;
- `max_accepted_plane_constraint_count`;
- `max_skipped_plane_constraint_count`;
- `normal_constraint_residual_norm`;
- `rank_filter_policy = "increment_map_row_rank_filter"`;
- retained shape, momentum, energy, kinematic-feasibility, and threshold
  diagnostics;
- `blocking_reasons` that retain `mabd_newton_report_incomplete` and
  `spinning_box_comparison_pass_gate_not_enabled`.

The report must not rewrite Phase 61/62 historical evidence. It may record
`normal_constraint_reduced_free_predicted_penetration=true` inside the new
diagnostic report only when the constrained post-step maximum penetration is
strictly smaller than this lane's free-predicted maximum. It must still retain
non-pass blockers for paper-faithful contact, threshold violations, comparison
gates, and kinematic feasibility when present.

The record for this phase must include `source_commit`, `vendored_newton_commit`,
canonical Python, reference environment, environment non-pollution flags, the
report sha256, generated-report provenance, and the exact verification
commands. The committed JSON report must carry `source_commit`,
`vendored_newton_commit`, `backend = cpu_numpy`, and `status = incomplete`.

## Config, Runner, And CLI

The lane must be machine-addressable through the same path as existing
spinning-box side lanes:

- add `normal_constraint_output_report` to the spinning-box paper-horizon config
  schema and YAML;
- add `write_spinning_box_normal_constraint_report`;
- add `run_spinning_box_normal_constraint`;
- add `--lane spinning_box_normal_constraint`;
- add loader, runner, and CLI tests for the explicit output path.

## Tests

Phase 63 requires test-first coverage for:

- `MABDCPUOraclePlaneConstraint` exported through `newton.solvers.mabd`;
- mirrored coverage in `tests/test_mabd_phase4_solver_step.py` and
  `vendor/newton/newton/tests/test_mabd_phase4_solver_step.py`;
- one scalar plane row constraining only the normal component while preserving
  tangential freedom. The regression must compare against the free predicted
  step, use nonzero tangent motion, assert `unit_normal dot point ==
  normalized_offset`, assert tangent projection matches the free prediction,
  and assert `dlambda.shape == (accepted_row_count,)`;
- active plane constraints working with `rotation_mode="polar"`;
- inactive constraints being ignored;
- invalid normal/body/shape validation;
- dependent active rows being rank-filtered instead of causing a singular dense
  dual solve;
- nonpenetrating free steps avoiding the constrained rerun;
- penetrating free steps producing matching active plane rows in the constrained
  rerun;
- the spinning-box active-set diagnostic producing finite JSON fields;
- the diagnostic recording free-predicted and constrained penetration without
  asserting a global monotonic guarantee;
- `scripts/validate_docs.py` checking exact solver/backend/status, blocker
  list, finite scalar types, per-step result coverage, top-level maxima
  consistency, report sha256, record text, claim-boundary text, and no
  `experiment.*` pass;
- the report remaining `status=incomplete` with no `lane_gate_status` and no
  `experiment.*` claim marked passed;
- docs/provenance validation including a Phase 63 record and
  `docs/reference/claim-boundaries.md` current, verified, and non-claim bullets.

## Claim Boundaries

Phase 63 verifies a scalar point-plane normal KKT row in the Newton CPU oracle
and records a spinning-box diagnostic that uses it. It does not verify:

- full contact handling;
- generic inequality-constrained M-ABD KKT;
- IPC;
- broadphase or narrowphase;
- friction;
- collision detection;
- continuous collision detection;
- paper-faithful affine collision;
- rendered agreement;
- timing;
- external baselines;
- the spinning-box experiment claim;
- full paper reproduction.

`docs/reference/paper-claims.yaml` must remain unchanged for
`experiment.single_body.spinning_box`.
