# Phase 65 Spinning-Box Figure Curve Digitization Record

Date: 2026-05-19

## Status

passed_for_spinning_box_figure_curve_digitization_slice

## Scope

Phase 65 adds a paper-PDF digitization lane for
`/tmp/mabd-paper/source/images/cube/roll_cube.pdf`. The lane records
color-family momentum curves from the paper figure only.

## Evidence

- Branch: `phase65-spinning-box-figure-curves`
- Spec:
  `docs/superpowers/specs/2026-05-19-phase65-spinning-box-figure-curves-design.md`
- Plan:
  `docs/superpowers/plans/2026-05-19-mabd-phase65-spinning-box-figure-curves.md`
- Config: `configs/experiments/single_body_spinning_box.yaml`
- Report:
  `reports/experiment_matrix/single_body_spinning_box_figure_curves.json`
- `reports/experiment_matrix/single_body_spinning_box_figure_curves.json`
  - SHA256:
    `d85cc7d71f82661038727f363304742e2b76ddcee2c9ea0d94e249ed31341bdd`
- Report SHA256:
  `d85cc7d71f82661038727f363304742e2b76ddcee2c9ea0d94e249ed31341bdd`
- Source commit: `8cfbb4647742cdf032706c03e16bcb37d8dbbc28`
- Vendored Newton commit: `96713fa965463b69c229a4d30582c733ff3526bb`
- Paper source version: `2603.08079v2`
- Canonical Python:
  `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python`
- Backend: `paper_pdf_digitization`
- Solver mode: `spinning_box_paper_figure_curve_digitization`
- Status: `incomplete`
- Paper PDF SHA256:
  `7669b062348324a3b0090cc9f44930655c83233a87f63389db9198b88f95ae80`
- Render command:
  `pdftocairo -png -singlefile -r 300 /tmp/mabd-paper/source/images/cube/roll_cube.pdf temporary_output_prefix`
- Rendered image SHA256:
  `936750053ee318cc3929b850673125a6160cb15e97dd5d605491cf4a0ef13376`

## Metrics

- `figure_curve_scope = paper_roll_cube_color_family_digitization`
- `color_assignment_policy = nearest_color_family_within_threshold`
- `color_family_curve_available = true`
- `paper_reference_legend_identity_available = false`
- `curve_identity_status = color_family_not_legend_entry`
- `curve_agreement_status = not_evaluated`
- `sample_count = 101`
- `min_sample_coverage = 0.8712871287128713`
- `rendered_size_px = [3570, 2187]`
- `render_dpi = 300`
- `angular_momentum_curves = [blue, brown, gray, green, orange]`
- `linear_momentum_curves = [blue, brown, gray, green, orange]`
- `blocking_reasons = [spinning_box_figure_curve_agreement_not_evaluated, spinning_box_reference_legend_identity_not_evaluated, spinning_box_line_style_split_not_evaluated, mabd_newton_report_incomplete, spinning_box_comparison_pass_gate_not_enabled]`

## Command

```bash
SOURCE_COMMIT=$(git rev-parse HEAD)
VENDORED_NEWTON_COMMIT=96713fa965463b69c229a4d30582c733ff3526bb
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/run_experiment.py \
  --lane spinning_box_figure_curves \
  --config configs/experiments/single_body_spinning_box.yaml \
  --matrix configs/experiments/paper_experiment_matrix.yaml \
  --output reports/experiment_matrix/single_body_spinning_box_figure_curves.json \
  --source-commit "$SOURCE_COMMIT" \
  --vendored-newton-commit "$VENDORED_NEWTON_COMMIT"
```

## Claim Boundary

This phase does not pass `experiment.single_body.spinning_box` and does not
change `docs/reference/paper-claims.yaml`. Curve identity, solid/dashed line
style split, curve agreement, solver agreement, runtime timing, rendered-output
inspection, and the comparison pass gate remain unevaluated.

No `experiment.*` claim is passed.

## Verification

- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_spinning_box_digitization tests.test_experiment_run_configs`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_runner.ExperimentRunnerTests.test_run_spinning_box_figure_curves_writes_explicit_output_report tests.test_experiment_runner.ExperimentRunnerTests.test_run_spinning_box_figure_curves_requires_explicit_output tests.test_experiment_runner.ExperimentRunnerTests.test_run_experiment_cli_writes_spinning_box_figure_curve_report`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check src/mabd_reproduction/spinning_box_digitization.py tests/test_spinning_box_digitization.py tests/test_experiment_run_configs.py`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check src/mabd_reproduction/experiment_runner.py scripts/run_experiment.py tests/test_experiment_runner.py`
- `git diff --check`
