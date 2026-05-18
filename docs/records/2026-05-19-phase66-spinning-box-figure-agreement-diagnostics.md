# Phase 66 Spinning-Box Figure Agreement Diagnostics Record

Date: 2026-05-19

## Status

passed_for_spinning_box_figure_agreement_diagnostics_slice

This is a diagnostic/reporting slice only. It does not pass
`experiment.single_body.spinning_box`, and it does not pass any
`experiment.*` claim.

No `experiment.*` claim is passed.

## Repository

- branch: `phase66-spinning-box-figure-agreement`
- implementation commit: `27650c74cadb5008fdb3d69f1a3faed069da2757`
- phase id: `phase66-spinning-box-figure-agreement`

## Vendored Newton

- upstream source commit: `96713fa965463b69c229a4d30582c733ff3526bb`
- local vendor path: `vendor/newton`
- local patch status: unchanged in Phase66

## Report Artifacts

- `reports/experiment_matrix/single_body_spinning_box_comparison.json`
  - sha256:
    `e8dfb25537d8a6dafd22d89ac9d7339e8f89b720c8d0b574b7b9168e34b7e5a6`
  - source_commit:
    `27650c74cadb5008fdb3d69f1a3faed069da2757`
  - status: `incomplete`
  - baseline_lane: `spinning_box_comparison_protocol`
  - solver_mode: `spinning_box_multilane_comparison_development`
- `reports/experiment_matrix/single_body_spinning_box_figure_curves.json`
  - sha256:
    `d85cc7d71f82661038727f363304742e2b76ddcee2c9ea0d94e249ed31341bdd`
  - consumed as `paper_figure_curves` input provenance

## Diagnostic Evidence

- `digitized_figure_reference_available=true`
- `digitized_figure_curve_agreement_available=true`
- `digitized_figure_curve_agreement_passed=false`
- recorded diagnostics:
  - `linear_momentum`
  - `angular_momentum`
  - `mabd_newton`
  - `rbd_implicit_baseline`
- diagnostic status:
  - `diagnostic_available_not_pass_gate`
  - `numeric_best_fit_not_legend_identity`
  - `diagnostic_only_not_curve_agreement`
- blocking reason:
  - `spinning_box_digitized_figure_curve_agreement_not_passed`

## Commands

```bash
SOURCE_COMMIT=27650c74cadb5008fdb3d69f1a3faed069da2757
VENDORED_NEWTON_COMMIT=96713fa965463b69c229a4d30582c733ff3526bb
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/run_experiment.py \
  --lane spinning_box_comparison \
  --config configs/experiments/single_body_spinning_box.yaml \
  --matrix configs/experiments/paper_experiment_matrix.yaml \
  --mabd-report reports/experiment_matrix/single_body_spinning_box.json \
  --rbd-report reports/experiment_matrix/single_body_spinning_box_rbd_baseline.json \
  --figure-report reports/experiment_matrix/single_body_spinning_box_figure_curves.json \
  --output reports/experiment_matrix/single_body_spinning_box_comparison.json \
  --source-commit "$SOURCE_COMMIT" \
  --vendored-newton-commit "$VENDORED_NEWTON_COMMIT"
```

## Verification Commands

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_spinning_box_comparison
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_runner.ExperimentRunnerTests.test_run_spinning_box_comparison_writes_explicit_output_report tests.test_experiment_runner.ExperimentRunnerTests.test_run_experiment_cli_writes_spinning_box_comparison_report
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .
git diff --check
```

## Claim Boundary

`experiment.single_body.spinning_box remains intended`. No `experiment.*`
claim is passed. The diagnostics compare lane scalar momentum errors with
digitized paper-figure color-family endpoint values, but the color families are
not paper legend-entry identities, the source is not authors' raw simulation
data, and the curve agreement gate is not passed.
