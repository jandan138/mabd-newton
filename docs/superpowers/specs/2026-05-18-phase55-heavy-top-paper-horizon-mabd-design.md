# Phase55 Heavy-Top Paper-Horizon MABD Diagnostic Design

## Goal

Phase55 extends the heavy-top `mabd_newton` diagnostic lane to a paper-horizon
variant that runs on the same 0 to 10 second sample grid as the existing RK4
reference report. The immediate goal is to remove the comparison-report
`sample_time_grid_mismatch` blocker by comparing aligned samples, while keeping
all unresolved paper-faithfulness blockers explicit.

This phase does not make the configured heavy-top geometry, inertia, or curve
agreement paper-faithful. It only replaces the short 0.25 second development
MABD input to the heavy-top comparison report with a 10 second, 11 sample,
Newton-backed diagnostic report.

## Current Evidence

The heavy-top reference lane already records:

- RK4 step size `h = 0.0001 s`;
- duration `10.0 s`;
- `11` samples on the paper figure horizon;
- the public `spinning_top.pdf` source hash and figure digitization evidence.

The current MABD heavy-top lane records:

- Newton `SolverMABD.step()` execution through the model-derived
  `mabd:body`, `mabd:world_constraint`, and `mabd:gravity` rows;
- step size `0.001 s`;
- `250` steps and `6` samples, ending at `0.25 s`;
- finite precession velocity and relative energy drift diagnostics.

Because the comparison report matches samples by sample index, the existing
0.25 second MABD lane cannot be compared to the 10 second RK4 reference without
recording a time-grid mismatch.

## Design

Add a second heavy-top MABD diagnostic config section:

```yaml
mabd_paper_horizon:
  time_step_s: 0.001
  step_count: 10000
  sample_count: 11
  output_report: reports/experiment_matrix/single_body_heavy_top_mabd_paper_horizon.json
```

The rest points, masses, pivot, gravity, rotation mode, and diagnostic
thresholds mirror `mabd_newton`. This keeps the only intended behavioral
difference in Phase55 the diagnostic horizon and sample grid.

The implementation will:

- parse `mabd_paper_horizon` as a `HeavyTopMABDNewtonConfig`;
- validate that the paper-horizon lane:
  - has a lane-specific output report;
  - is distinct from the short MABD, RK4, comparison, and figure reports;
  - has `sample_count == reference.sample_count`;
  - has `step_count * time_step_s` equal to `reference.duration_s` within a
    strict numeric tolerance;
  - has a sample stride that divides `step_count` evenly;
  - uses the same point-mass sum and gravity as the reference;
  - mirrors the short `mabd_newton` lane's rest points, masses, pivot points,
    angle probe, gravity, rotation mode, and thresholds so the only intended
    config difference is horizon and sample count;
- allow the MABD rollout and report writer to receive an explicit heavy-top
  MABD lane config instead of always using `config.mabd_newton`;
- add `write_heavy_top_mabd_paper_horizon_report`;
- add `run_heavy_top_mabd_paper_horizon` and CLI lane
  `heavy_top_mabd_paper_horizon`;
- regenerate:
  - `reports/experiment_matrix/single_body_heavy_top_mabd_paper_horizon.json`;
  - `reports/experiment_matrix/single_body_heavy_top_comparison.json` using
    the paper-horizon MABD input and the existing RK4 and figure reports.

The report identity remains `baseline_lane="mabd_newton"` and
`solver_mode="mabd_cpu_oracle_heavy_top_newton_lane"` so the comparison
protocol still consumes the required MABD lane. The report will expose a
diagnostic scope field such as `mabd_diagnostic_scope =
paper_horizon_sample_grid`, `duration_s`, `solver_model_config_source =
newton_model_derived`, and Newton custom-frequency provenance. The current
paper-horizon rollout may record threshold violations such as affine-shape
spread growth; those violations are evidence against treating the lane as
passed.

## Comparison Integration

The heavy-top comparison report will continue to require explicit RK4, MABD,
and optional paper-figure report paths. Phase55 changes the generated evidence
record and validation to use:

```text
--mabd-report reports/experiment_matrix/single_body_heavy_top_mabd_paper_horizon.json
```

Expected comparison effects:

- `mabd_sample_count == 11`;
- `rk4_sample_count == 11`;
- `matched_sample_index_count == 11`;
- `time_grid_mismatch == false`;
- `max_sample_time_delta_s <= 1e-12`;
- `sample_time_grid_mismatch` is absent from current comparison blockers.
- `input_report_provenance["mabd_newton"]["mabd_diagnostic_scope"]` records
  `paper_horizon_sample_grid`.

The comparison must retain:

- `exact_heavy_top_inertia_unknown`;
- `exact_heavy_top_geometry_unknown`;
- `raw_heavy_top_reference_curve_data_missing`;
- `mabd_newton_report_incomplete`;
- `heavy_top_comparison_report_incomplete`;
- `heavy_top_timing_evidence_missing`;
- `heavy_top_comparison_pass_gate_not_enabled`;
- `heavy_top_digitized_figure_curve_agreement_not_passed` when figure curves
  are supplied.

## Claim Boundaries

Phase55 may claim:

- a Newton-backed heavy-top MABD diagnostic report covers the 0 to 10 second
  paper figure horizon;
- the MABD and RK4 diagnostic sample grids are aligned in the current
  comparison report;
- the previous `sample_time_grid_mismatch` blocker is removed from current
  heavy-top comparison evidence.

Phase55 must not claim:

- a passed heavy-top experiment;
- a passed heavy-top MABD lane;
- paper-horizon MABD stability or accuracy;
- paper-faithful heavy-top MABD dynamics;
- paper-faithful heavy-top inertia, geometry, or contact/collision modeling;
- raw author simulation curve access;
- digitized curve agreement;
- ABD-vs-RBD comparison pass;
- runtime performance reproduction;
- rendered output or generated videos;
- full paper reproduction;
- any passed `experiment.*` claim.

## Validation

Required checks:

- RED/GREEN tests for config parsing and validation of `mabd_paper_horizon`;
- RED/GREEN tests for `roll_out_heavy_top_mabd_model_derived(...,
  mabd_config=config.mabd_paper_horizon)`;
- RED/GREEN tests for report writer, runner, and CLI lane;
- RED/GREEN tests proving comparison consumes the paper-horizon report without
  `sample_time_grid_mismatch`;
- regenerate the paper-horizon MABD report and heavy-top comparison report;
- update claim boundaries and dated Phase55 record;
- update docs validation so older Phase51-53 checks tolerate newer aligned-grid
  evidence while Phase55 requires it, and update Phase51/52 boundary wording so
  their `sample_time_grid_mismatch` statements are clearly historical after
  Phase55;
- commit implementation code before regenerating final JSON reports, then
  stamp generated reports with that implementation commit as `source_commit`;
- run:
  - `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests`;
  - `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py`;
  - `PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"`;
  - `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .`;
  - `git diff --check`.
