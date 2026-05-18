# Phase 68 Model Plane Report Lane Design

Date: 2026-05-19

## Objective

Phase 68 adds a spinning-box diagnostic report lane that exercises the Phase 67
`SolverMABD.step()` model-derived `mabd:plane_constraint` path from the
experiment runner. The goal is to prove that model-backed Newton rows can drive
the existing point-plane normal constraint diagnostic outside unit tests.

This is a report/provenance capability slice. It does not add collision
detection, Newton `Contacts` ingestion, active-set generation inside Newton,
friction, IPC, complementarity, continuous collision detection,
paper-faithful affine contact, a comparison pass gate, or any passed
`experiment.*` claim.

## Current Gap

Phase 63 added the CPU-oracle `MABDCPUOraclePlaneConstraint` primitive and a
spinning-box normal-constraint diagnostic lane, but that lane directly calls
`mabd.solve_cpu_oracle_step(...)` with an explicit
`MABDCPUOracleConfig(plane_constraints=...)`.

Phase 67 added `mabd:plane_constraint` extraction to `SolverMABD.step()`, but
the evidence is limited to solver-level tests and a validator smoke. No
experiment runner or committed report currently proves that the public
`SolverMABD` model path can run the spinning-box free-predict/active-plane-row
diagnostic.

## Scope

Phase 68 adds a separate side lane rather than rewriting Phase 63 evidence:

- config field:
  `paper_horizon.model_plane_constraint_output_report`;
- report path:
  `reports/experiment_matrix/single_body_spinning_box_model_plane_constraint.json`;
- runner:
  `run_spinning_box_model_plane_constraint`;
- CLI lane:
  `--lane spinning_box_model_plane_constraint`;
- report writer:
  `write_spinning_box_model_plane_constraint_report`;
- implementation helper that builds a transient Newton `ModelBuilder`, registers
  `SolverMABD` custom attributes, adds one `mabd:body` row and zero or more
  `mabd:plane_constraint` rows, calls `SolverMABD.step()`, and reads the M-ABD
  state back into the report lane;
- docs, record, claim-boundary, and validator gates.

The lane reuses the Phase 63 two-pass diagnostic policy:

1. Run a free prediction.
2. Evaluate configured cube corners against the configured plane on the free
   predicted state.
3. Build active point-plane rows for penetrating corners.
4. If no corner penetrates, accept the free prediction.
5. If rows exist, rerun the step through `SolverMABD.step()` with explicit
   model `mabd:plane_constraint` rows.
6. Record free-predicted penetration, constrained penetration, requested row
   count, accepted row count, skipped row count, residual norm, and finite
   state diagnostics.

Both the free prediction and constrained rerun must go through `SolverMABD`
with model-derived CPU oracle configuration. The report must record that the
manual `MABDCPUOracleConfig` report lane remains separate.

## Report Contract

The committed report uses:

```text
claim_id = experiment.single_body.spinning_box
status = incomplete
baseline_lane = mabd_newton
solver_mode = solver_mabd_model_plane_constraint_diagnostic
backend = cpu_numpy_newton_solver_mabd_model_rows
```

The observed payload must include:

- `model_plane_constraint_policy =
  "solver_mabd_model_rows_free_predict_then_active_plane_constraints"`;
- `model_plane_constraint_scope = "diagnostic_only_no_lane_gate"`;
- `model_plane_constraint_config_source = "mabd:plane_constraint_custom_rows"`;
- `contact_constraint_policy =
  "free_predict_then_active_point_plane_normal_constraints"`;
- `rank_filter_policy = "increment_map_row_rank_filter"`;
- `max_free_predicted_contact_penetration_m`;
- `max_constrained_contact_penetration_m`;
- `max_requested_plane_constraint_count`;
- `max_accepted_plane_constraint_count`;
- `max_skipped_plane_constraint_count`;
- `max_model_plane_constraint_residual_norm`;
- per-step paper-horizon result entries with the same count as
  `paper_horizon.time_step_grid_s`;
- `model_plane_constraint_reduced_free_predicted_penetration=true` only when
  the constrained maximum penetration is strictly smaller than the lane's own
  free-predicted maximum;
- `blocking_reasons` retaining `mabd_newton_report_incomplete`,
  `spinning_box_model_plane_constraint_not_paper_faithful`,
  `spinning_box_comparison_pass_gate_not_enabled`, and any existing
  threshold/kinematic-feasibility blockers.

The report must not include `lane_gate_status`. It must not set
`status=passed`.

## Config, Runner, And CLI

`configs/experiments/single_body_spinning_box.yaml` gains:

```yaml
paper_horizon:
  model_plane_constraint_output_report: reports/experiment_matrix/single_body_spinning_box_model_plane_constraint.json
```

`SpinningBoxPaperHorizonConfig` gains a string field with the same name.
`validate_spinning_box_config_against_matrix` must require the path to be
lane-specific, under the matrix stem, ending in `.json`, and distinct from
existing spinning-box reports:

- `output_report`;
- `contact_response_output_report`;
- `normal_constraint_output_report`;
- `decoupled_twist_output_report`;
- `figure_curve_output_report`.

The CLI adds `spinning_box_model_plane_constraint` to the `--lane` choices and
dispatch table. The lane requires explicit `--output` and rejects
`--output-root`, matching the current side-lane pattern.

## Claim Boundaries

Phase 68 verifies only that the spinning-box diagnostic can run through
`SolverMABD.step()` model rows that become `MABDCPUOraclePlaneConstraint`
entries.

Phase 68 must not modify `docs/reference/paper-claims.yaml`: all current
method claim statuses remain unchanged, all `experiment.*` claims remain
`intended`, and `method.force_mapping.point_load_penalty_contact` remains
bounded to CPU-oracle force/row mapping evidence only.

Phase 68 does not verify:

- contact solver behavior;
- Newton `Contacts` ingestion;
- collision detection;
- broadphase or narrowphase;
- active-set generation inside Newton;
- generic inequality-constrained M-ABD KKT;
- friction;
- complementarity;
- IPC;
- continuous collision detection;
- paper-faithful affine collision/contact;
- paper-faithful M-ABD stepping;
- comparison pass gates;
- rendered-output agreement;
- runtime performance;
- any passed `experiment.*` claim;
- full paper reproduction.

Forbidden wording includes claiming that Phase 68 implements a contact solver,
that rigid proxy collision is paper-faithful affine collision, that unmodified
Newton supports M-ABD contact, that the spinning-box experiment passes, or that
full paper reproduction is complete.

## Tests

Phase 68 requires test-first coverage for:

- config loading of `model_plane_constraint_output_report`;
- config validation rejecting output collisions with all existing
  spinning-box lane reports;
- a helper-level test proving a single `SolverMABD` model step with explicit
  plane rows matches the Phase 63 explicit CPU-oracle config result for one
  constrained spinning-box step;
- the report writer producing finite metrics, incomplete status, the exact
  solver/backend/policy strings, no `lane_gate_status`, and strictly reduced
  free-predicted penetration for the committed config;
- runner and CLI tests for `spinning_box_model_plane_constraint`;
- docs/provenance validator checks for the spec, plan, record, report path,
  report sha256, exact report fields, exact paper-claim statuses, claim-boundary
  snippets, environment non-pollution fields, and overclaim rejection.

The tests must not require or imply paper-faithful contact. They must keep
`experiment.single_body.spinning_box` at `reproduction_status: intended`.

## Verification

Required focused commands:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_run_configs tests.test_single_body_report_lane tests.test_experiment_runner tests.test_spinning_box_report_artifacts
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/run_experiment.py --lane spinning_box_model_plane_constraint --config configs/experiments/single_body_spinning_box.yaml --matrix configs/experiments/paper_experiment_matrix.yaml --output reports/experiment_matrix/single_body_spinning_box_model_plane_constraint.json --source-commit "$(git rev-parse HEAD)" --vendored-newton-commit 96713fa965463b69c229a4d30582c733ff3526bb
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_phase0_bootstrap
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
```

The generated report and final record must capture the exact implementation
commit used for the run before `validate_docs.py` can pass.

Required final gates:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/env/readiness_check.py
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"
git diff --check
```
