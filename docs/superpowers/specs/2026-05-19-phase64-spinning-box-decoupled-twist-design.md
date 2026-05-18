# Phase 64 Spinning-Box Decoupled Twist Diagnostic Design

Date: 2026-05-19

## Objective

Phase 64 adds a bounded spinning-box diagnostic lane that integrates the paper
spatial twist as an independent rigid velocity and advances the affine matrix
with an exponential rotation update. The purpose is to separate the Phase 29
finite-difference velocity blocker from the rest of the spinning-box scene
evidence.

This phase is a velocity-semantics reconstruction diagnostic. It does not claim
the paper uses decoupled velocity state, does not replace the Newton M-ABD CPU
oracle step, does not pass `experiment.single_body.spinning_box`, and does not
claim full paper reproduction.

## Current Gap

Phase 63 shows that scalar point-plane normal KKT rows can reduce the
spinning-box contact penetration diagnostic to numerical zero. The remaining
paper-horizon blockers include shape, energy, and momentum/velocity-semantics
failures that are consistent with interpreting the paper angular momentum
through the current relation:

```text
qd_next = (q_next - q_n) / h
```

With the paper angular speed of `60000 rad/s`, an orthogonal finite-difference
update at `h = 0.01` is bounded by `100 rad/s`, and at `h = 0.001` by
`1000 rad/s`. The existing M-ABD lane therefore represents the paper momentum
by large affine stretch. Phase 30 audited the paper source and found support
for target spatial twist initialization and `G(A)`/`G(A)^T` maps, but no public
source proof of decoupled velocity semantics.

Phase 64 records a reconstruction experiment: keep the paper spatial twist as
the diagnostic velocity state, update orientation by `exp([omega] h)`, update
translation by `v h`, then map the twist back to ABD generalized velocity for
measurement through the existing Newton `E(A)` and `G(A)` helpers. The lane
tests whether the configured stretch and energy thresholds are absent under
this reconstruction; it does not prove paper solver semantics.

## Design

### Rigid Exponential Diagnostic

Add small helpers under `spinning_box_physics.py`:

- build a skew matrix for a 3-vector;
- compute `SO(3)` exponential updates from angular velocity and time step;
- validate finite positive time steps;
- produce a decoupled ABD diagnostic state:
  `q = pack_q(A, t)` and `qd = rigid_embedding_E(A) @ V_paper`.

The integration update is:

```text
A_{n+1} = exp([omega] h) A_n
t_{n+1} = t_n + v h
qd_diag,n+1 = E(A_{n+1}) V_paper
```

The diagnostic uses the same paper mass, inertia, cube corners, plane, momentum
diagnostics, contact diagnostics, and threshold keys as the current
paper-horizon lane. It records the velocity relation as:

```text
decoupled_spatial_twist_with_exponential_rigid_update
```

and records the Phase 29 finite-difference relation as the blocker it is
testing against, not as a solved paper claim.

### Report Lane

Add:

```text
reports/experiment_matrix/single_body_spinning_box_decoupled_twist.json
```

The report uses:

```text
solver_mode = decoupled_twist_rigid_reconstruction_diagnostic
status = incomplete
baseline_lane = mabd_newton
```

The observed payload records:

- `velocity_semantics_policy =
  "decoupled_spatial_twist_with_exponential_rigid_update"`;
- `velocity_semantics_scope = "diagnostic_only_no_lane_gate"`;
- one result per configured paper step size;
- maximum momentum errors, relative kinetic/total energy drift, determinant
  error, singular-value extrema, affine orthogonality error, contact
  penetration, finite-difference inconsistency, and residual applicability;
- `threshold_violations` for the decoupled lane;
- `shape_thresholds_met_by_decoupled_twist` and
  `energy_thresholds_met_by_decoupled_twist`;
- `max_velocity_state_inconsistency_norm`;
- `max_finite_difference_twist_error`;
- `solver_step_policy = "no_solver_step_rigid_reconstruction_diagnostic"`;
- `solver_residual_status = "not_evaluated_no_kkt_solve"`;
- Phase 29 finite-difference feasibility status and required ratios;
- blockers retaining `mabd_newton_report_incomplete`,
  `spinning_box_decoupled_twist_not_paper_faithful`,
  `spinning_box_comparison_pass_gate_not_enabled`, and
  `mabd_kinematic_feasibility_blocker_recorded`.

If thresholds are met, the report may say
`decoupled_twist_thresholds_met_no_lane_gate`; it must still be
`status = incomplete`, must not include `lane_gate_status`, and must not change
`paper-claims.yaml`.

### Config, Runner, And CLI

Add `decoupled_twist_output_report` to the existing spinning-box
`paper_horizon` config block and expose a runner lane:

```text
--lane spinning_box_decoupled_twist
```

This lane requires an explicit `--output`, like other side-lane diagnostics, so
historical reports remain separate.

## Tests

Phase 64 requires test-first coverage for:

- `spinning_box_so3_exp_from_angular_velocity` returning rotations with
  determinant near one and orthogonality error near zero;
- `spinning_box_decoupled_twist_state` preserving the paper momentum when
  measured by `G(A) @ qd`;
- config parsing of `decoupled_twist_output_report`;
- `write_spinning_box_decoupled_twist_report` producing finite per-step JSON,
  `status = incomplete`, no `lane_gate_status`, and the exact non-pass
  blockers;
- the decoupled report showing no affine stretch thresholds violated for the
  spinning-box paper horizon while retaining non-pass claim boundaries;
- experiment runner and CLI support for `spinning_box_decoupled_twist`;
- `scripts/validate_docs.py` checking the committed report, record, claim
  boundary bullets, sha256, status, solver mode, backend, exact blocker list,
  no `lane_gate_status`, non-temporary `source_commit`, vendored Newton
  commit, paper source version, config path, environment non-pollution fields,
  exact report path, exact velocity semantics policy/scope/status, result
  count matching `time_step_grid_s`, finite metric values, top-level maxima
  matching per-step results, and unchanged experiment claim statuses.

## Claim Boundaries

Phase 64 verifies only that the configured stretch thresholds are absent under
a decoupled spatial-twist reconstruction for the configured spinning-box scene.
It does not verify:

- the paper solver's private velocity semantics;
- paper-faithful M-ABD stepping;
- contact, friction, collision detection, or IPC;
- rendered agreement;
- timing;
- external baselines;
- the spinning-box experiment claim;
- full paper reproduction.

`docs/reference/paper-claims.yaml` must keep
`experiment.single_body.spinning_box` at `intended`.
