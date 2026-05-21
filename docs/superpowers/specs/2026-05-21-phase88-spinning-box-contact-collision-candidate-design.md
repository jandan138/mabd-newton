# Phase 88 Spinning-Box Contact/Collision Candidate Design

## Scope

Phase 88 starts the first concrete slice toward paper-faithful single affine
body contact/collision for `single_body_spinning_box`.

The slice adds a report lane that runs a persistent Newton `SolverMABD` model
for the configured spinning box on a static frictionless plane. Each time step
uses this policy:

1. copy the current M-ABD state,
2. run an unconstrained free prediction,
3. call `SolverMABD.detect_static_plane_contacts` on the free-predicted state,
4. restore the original state,
5. rerun `SolverMABD.step(..., contacts=contacts)` using the generated contact
   rows,
6. record free-predicted vs constrained penetration, contact counts, residuals,
   momentum, energy, and compact trajectory samples.

This is an affine static-plane contacts rollout candidate lane, not a pass gate
or a generic collision/contact solver.

## Claim Boundary

The paper text for the spinning-box benchmark describes a cube moving on a
frictionless surface and compares co-rotated ABD to an implicit RBD baseline.
It does not disclose enough collision/contact implementation detail in the
current local evidence to claim a paper-faithful contact law.

Therefore Phase 88 must keep:

- `paper_faithful = false`
- `full_experiment_claim_passed = false`
- `comparison_pass_gate_enabled = false`
- top-level report `status = incomplete`
- no `lane_gate_status`
- `timing_distribution.paper_comparable = false`

The report may claim only that the Newton M-ABD candidate path generated and
consumed affine box/static-plane contact rows over a persistent rollout and
measured free-predicted vs constrained penetration.

## Report Contract

New lane:

- lane: `spinning_box_affine_static_plane_contacts_rollout_candidate`
- report:
  `reports/experiment_matrix/single_body_spinning_box_affine_static_plane_contacts_rollout_candidate.json`
- backend: `cpu_newton_solver_mabd_affine_static_plane_contacts_rollout_candidate`
- solver mode: `solver_mabd_affine_static_plane_contacts_rollout_candidate`

Required observed fields:

- `candidate_status =
  affine_static_plane_contacts_rollout_candidate_recorded`
- `rollout_scope = development_only`
- `paper_faithful = false`
- `paper_comparable = false`
- `full_experiment_claim_passed = false`
- `contact_constraint_policy =
  free_predict_detect_static_plane_contacts_then_constrained_step`
- `contact_detection_source = SolverMABD.detect_static_plane_contacts`
- `contacts_input_summary_source = last_contacts_input_summary`
- `static_plane_collision_summary_source = last_static_plane_collision_summary`
- `newton_contacts_api = newton.Contacts`
- `solver_step_api = SolverMABD.step(..., contacts=...)`
- `contact_constraint_mode = plane`
- `duration_s = 10.0`
- `time_step_s = 0.01`
- `step_count = 1000`
- `sample_count = 101`
- `max_free_predicted_contact_penetration_m`
- `max_constrained_contact_penetration_m`
- `max_affine_static_plane_candidate_contact_count`
- `max_contacts_input_generated_plane_constraint_count`
- `max_constraint_residual_norm`
- `trajectory_samples`
- `blocking_reasons` includes
  `spinning_box_affine_static_plane_contacts_rollout_candidate_not_paper_faithful`

## Acceptance Criteria

- Config validation admits only the dedicated candidate report path and keeps
  the lane non-paper-faithful.
- Runner and CLI tests cover the new lane.
- The generated report is committed, machine-checkable, and incomplete.
- The candidate report records a 10 second rollout with 101 samples.
- The candidate report records contact counts, generated plane constraints,
  free-predicted penetration, constrained penetration, and residuals without
  enabling a pass gate.
- Claim boundaries, gap audit, and docs validator keep all `experiment.*`
  claims unpassed.
