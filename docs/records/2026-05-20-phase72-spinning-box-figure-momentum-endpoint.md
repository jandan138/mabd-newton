# Phase 72 Spinning-Box Figure Momentum Endpoint Diagnostic

## Status

passed_for_spinning_box_figure_momentum_endpoint_diagnostic

## Repository

- branch/worktree: `phase68-model-plane-report-lane`
- source commit: `721cf0f9c059d0fbe7852d9ba0c86e015e7ed5c9`
- vendored Newton commit: `96713fa965463b69c229a4d30582c733ff3526bb`
- Python: `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python`
- paper source version: `2603.08079v2`
- config path: `configs/experiments/single_body_spinning_box.yaml`
- matrix path: `configs/experiments/paper_experiment_matrix.yaml`
- random seed: `not applicable`
- backend: `report_protocol`

## Scope

Phase 72 corrects only the spinning-box digitized paper-figure endpoint
diagnostic value source. The diagnostic now compares the digitized
`roll_cube.pdf` endpoint momentum values against lane endpoint momentum
magnitudes:

- `final_linear_momentum_norm`
- `final_angular_momentum_norm`

The previous diagnostic compared those paper momentum values against
`linear_momentum_error` and `angular_momentum_error`, which are error fields
relative to the paper initial momenta rather than the plotted momentum values.

For M-ABD reports, endpoint magnitudes are read from
`final_linear_momentum_kg_m_s` and `final_angular_momentum_kg_m2_s` when
available. For the RBD baseline report, endpoint magnitudes are derived from
`mass_kg * linear_velocity_m_s` and
`inertia_diag_kg_m2 * angular_velocity_rad_s`.

`digitized_figure_curve_agreement_passed = false` remains unchanged, and the
comparison pass gate remains disabled.

## Report Artifact

- `reports/experiment_matrix/single_body_spinning_box_comparison.json`
  - sha256:
    `1b8d2ab68f97c4e0035132fd8077271c4c2a68e40fa96f06fc9ba11983ea2e0f`
- report path:
  `reports/experiment_matrix/single_body_spinning_box_comparison.json`
- report sha256:
  `1b8d2ab68f97c4e0035132fd8077271c4c2a68e40fa96f06fc9ba11983ea2e0f`
- figure report path:
  `reports/experiment_matrix/single_body_spinning_box_figure_curves.json`
- figure report sha256:
  `d85cc7d71f82661038727f363304742e2b76ddcee2c9ea0d94e249ed31341bdd`
- solver mode: `spinning_box_multilane_comparison_development`
- baseline lane: `spinning_box_comparison_protocol`
- status: `incomplete`
- blocking reason retained:
  `spinning_box_digitized_figure_curve_agreement_not_passed`

Endpoint diagnostic values:

- linear M-ABD: `lane_value_source = final_linear_momentum_norm`,
  `lane_value = 99.99999999999993`, `best_abs_error = 0.48347613219087293`
- linear RBD: `lane_value_source = final_linear_momentum_norm`,
  `lane_value = 100.0`, `best_abs_error = 0.483476132190944`
- angular M-ABD: `lane_value_source = final_angular_momentum_norm`,
  `lane_value = 100.00000000147234`, `best_abs_error = 0.6731946159154347`
- angular RBD: `lane_value_source = final_angular_momentum_norm`,
  `lane_value = 100.0`, `best_abs_error = 0.6731946144430907`

The comparison report still records lane error metrics including
`linear_momentum_error` and `angular_momentum_error`; those fields are no
longer used as the paper-figure endpoint momentum values.

raw artifacts: no videos, run directories, raw logs, or raw paper assets are
committed. The committed artifact is the small JSON report above.

## Commands

TDD red check:

```bash
PYTHONPATH=src:vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  -m unittest \
  tests.test_spinning_box_comparison.SpinningBoxComparisonTests.test_spinning_box_comparison_consumes_valid_figure_curve_report
```

Observed before implementation: failed because `lane_value_source` was
`linear_momentum_error`.

Report regeneration:

```bash
PYTHONPATH=src:vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  scripts/run_experiment.py \
  --lane spinning_box_comparison \
  --config configs/experiments/single_body_spinning_box.yaml \
  --matrix configs/experiments/paper_experiment_matrix.yaml \
  --mabd-report reports/experiment_matrix/single_body_spinning_box.json \
  --rbd-report reports/experiment_matrix/single_body_spinning_box_rbd_baseline.json \
  --figure-report reports/experiment_matrix/single_body_spinning_box_figure_curves.json \
  --output reports/experiment_matrix/single_body_spinning_box_comparison.json \
  --source-commit 721cf0f9c059d0fbe7852d9ba0c86e015e7ed5c9 \
  --vendored-newton-commit 96713fa965463b69c229a4d30582c733ff3526bb
```

Result summary:

```json
{"baseline_lane": "spinning_box_comparison_protocol", "claim_id": "experiment.single_body.spinning_box", "output_report": "reports/experiment_matrix/single_body_spinning_box_comparison.json", "scene_id": "single_body_spinning_box", "status": "incomplete"}
```

Focused verification:

```bash
PYTHONPATH=src:vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  -m unittest tests.test_spinning_box_comparison
```

Repository validation commands:

```bash
PYTHONPATH=src:vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  -m unittest \
  tests.test_spinning_box_comparison \
  tests.test_experiment_runner \
  tests.test_phase0_bootstrap

PYTHONPATH=src:vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  scripts/validate_docs.py

git diff --check
```

Environment isolation commands:

```bash
PYTHONPATH=src:vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  scripts/env/clone_from_reference.py --dry-run

PYTHONPATH=src:vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  scripts/env/clone_from_reference.py --dry-run --sync-existing
```

Observed statuses:

- `target_exists` for the non-sync dry-run
- `ready_to_sync_existing` and `can_execute=true` for the explicit sync dry-run

Non-pollution fields:

- `mutates_reference_environment=false`
- `uses_reference_python=false`
- `uses_ambient_python=false`

## Claim Boundaries

No `experiment.*` claim is passed.

`paper-claims.yaml` is unchanged.

This record is:

- not experiment-pass evidence for the spinning-box scene;
- not an M-ABD lane pass;
- not paper reference legend-entry identity evidence;
- not solid/dashed line-style split evidence;
- not Newton-vs-paper curve agreement evidence;
- not comparison pass gate evidence;
- not rendered-output inspection evidence;
- not runtime performance evidence;
- not full paper reproduction.
