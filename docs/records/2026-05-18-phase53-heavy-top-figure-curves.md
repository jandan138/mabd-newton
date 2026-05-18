# Phase 53 Heavy-Top Figure Curves

## Status

passed_for_heavy_top_figure_curve_digitization_lane

## Scope

- worktree:
  `/cpfs/user/zhuzihou/dev/mabd-newton/.worktrees/phase53-heavy-top-figure-curves`
- source commit used for regenerated reports:
  `24d3858a8b1d7eca346aec80c13e68652099b600`
- vendored Newton upstream commit: `96713fa965463b69c229a4d30582c733ff3526bb`
- paper source version: `2603.08079v2`
- Python: `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python`
- environment isolation: `mabd-newton-py310` remains a clone of
  `physics-primitive-newton-py310`; no install was made into the ambient DSW
  Python or the reference `physics-primitive-agent` environment.

## Evidence

- claim: `experiment.single_body.heavy_top`
- config: `configs/experiments/single_body_heavy_top.yaml`
- matrix: `configs/experiments/paper_experiment_matrix.yaml`
- source PDF:
  `/tmp/mabd-paper/source/images/spinning_top/spinning_top.pdf`
- source PDF sha256:
  `c8f5e206415b9feb3578ee32aa3b7284e2695bdd84eeb0200f3b4aa01cf3422d`
- renderer: `pdftocairo 22.02.0`
- render command:
  `pdftocairo -png -singlefile -r 300 /tmp/mabd-paper/source/images/spinning_top/spinning_top.pdf <temporary-prefix>`
- rendered size: `3179 x 1924`
- source scope: `paper_figure_reference_family_only`
- retained limitation: `not_authors_raw_data`
- retained limitation: `no_blue_orange_line_style_split`
- retained limitation: `no_curve_agreement_gate`
- `reports/experiment_matrix/single_body_heavy_top_figure_curves.json`
  - sha256:
    `1fc15336ba81146554bd26e7be6b33a13f84b36bd0ae3d0b672b46e72742ced1`
  - solver mode: `heavy_top_paper_figure_digitization`
  - baseline lane: `paper_figure_digitization`
  - backend: `pdftocairo_pillow`
  - top-level evidence status: `incomplete`
  - reference precession samples: `101`
  - reference precession coverage: `0.9900990099009901`
  - reference nutation samples: `101`
  - reference nutation coverage: `0.9900990099009901`
- `reports/experiment_matrix/single_body_heavy_top_comparison.json`
  - sha256:
    `ef8c3fd21ac1159798f8102c18834e0b75655e6d0e396f69e8d4fdd738f7d87f`
  - solver mode: `heavy_top_multilane_comparison_development`
  - baseline lane: `heavy_top_comparison_protocol`
  - backend: `report_protocol`
  - top-level evidence status: `incomplete`
  - nutation metric status: `paper_figure_digitized_reference_available`
  - missing paper metric:
    `nutation_angle_error:paper_figure_digitized_curve_agreement_not_passed`
- input report provenance:
  - `paper_figure_curves` sha256:
    `1fc15336ba81146554bd26e7be6b33a13f84b36bd0ae3d0b672b46e72742ced1`
  - `rbd_rk4_reference` sha256:
    `41418e964dd9e7fba1516f420fa97ced8cfaf9157d552d9072f85fcbb08f564c`
  - `mabd_newton` sha256:
    `9342374ffde72071308b6aa5c117815392f71f4db1e07d9817ac61e4847bf324`
- retained blocker: `raw_heavy_top_reference_curve_data_missing`
- retained blocker: `heavy_top_digitized_figure_curve_agreement_not_passed`
- retained blocker: `mabd_newton_report_incomplete`
- retained blocker: `heavy_top_comparison_report_incomplete`
- retained blocker: `heavy_top_timing_evidence_missing`
- retained blocker: `heavy_top_comparison_pass_gate_not_enabled`
- retained blocker: `sample_time_grid_mismatch`

## Result Boundary

No `experiment.*` claim is passed.

`experiment.single_body.heavy_top` remains intended. Phase 53 records
digitized paper-figure reference-family samples and comparison-report awareness
of those samples only. It does not prove authors' raw simulation data,
blue/orange solid and dashed paper-curve separation, heavy-top curve agreement,
paper-faithful heavy-top inertia or geometry, ABD-vs-RBD pass-gate agreement,
rendered output, paper timing, runtime performance, generated video evidence,
or a full paper reproduction.

## Commands

- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/run_experiment.py --lane heavy_top_figure_curves --config configs/experiments/single_body_heavy_top.yaml --matrix configs/experiments/paper_experiment_matrix.yaml --source-commit 24d3858a8b1d7eca346aec80c13e68652099b600 --vendored-newton-commit 96713fa965463b69c229a4d30582c733ff3526bb`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/run_experiment.py --lane heavy_top_comparison --config configs/experiments/single_body_heavy_top.yaml --matrix configs/experiments/paper_experiment_matrix.yaml --rbd-report reports/experiment_matrix/single_body_heavy_top_rk4_reference.json --mabd-report reports/experiment_matrix/single_body_heavy_top_mabd_newton.json --figure-report reports/experiment_matrix/single_body_heavy_top_figure_curves.json --source-commit 24d3858a8b1d7eca346aec80c13e68652099b600 --vendored-newton-commit 96713fa965463b69c229a4d30582c733ff3526bb`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_heavy_top_digitization tests.test_heavy_top_comparison_reports tests.test_experiment_runner tests.test_phase0_bootstrap`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py`
- `PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"`
- `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .`
- `git diff --check`
