# Phase 49 Heavy Top RK4 Reference Diagnostic

## Status

passed_for_heavy_top_reference_diagnostic_lane

## Repository

- branch: `phase49-heavy-top-reference`
- implementation source commit:
  `cbeff81dfbadfcac3b1c96840bc96eba0e28c8bd`
- vendored Newton commit:
  `96713fa965463b69c229a4d30582c733ff3526bb`
- canonical Python:
  `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python`

## Paper Source

- claim: `experiment.single_body.heavy_top`
- source lines: `/tmp/mabd-paper/source/sections/experiment.tex:65-75`
- figure: `/tmp/mabd-paper/source/images/spinning_top/spinning_top.pdf`
- figure PDF sha256:
  `c8f5e206415b9feb3578ee32aa3b7284e2695bdd84eeb0200f3b4aa01cf3422d`
- figure text source:
  `pdftotext /tmp/mabd-paper/source/images/spinning_top/spinning_top.pdf -`

## Report Artifact

The report artifact is a compact JSON summary under `reports/experiment_matrix/`.
No raw simulation directories, videos, or large logs are committed.

- `reports/experiment_matrix/single_body_heavy_top_rk4_reference.json`
  - sha256:
    `d2d69700dfec8a5e767ba31ef487e8b9a6310b1e06b6e6a3f36f765e8a2d88e1`
  - baseline lane: `rbd_rk4_reference`
  - solver mode: `heavy_top_rk4_reference_diagnostic`
  - backend: `cpu_numpy`
  - status: `incomplete`
  - lane_status: `diagnostic_generated`
  - retained blocker: `exact_heavy_top_inertia_unknown`
  - retained blocker: `exact_heavy_top_geometry_unknown`
  - retained blocker: `raw_heavy_top_reference_curve_data_missing`
  - retained blocker: `mabd_newton_report_missing`
  - retained blocker: `heavy_top_comparison_report_missing`
  - retained blocker: `heavy_top_timing_evidence_missing`

## Claim Impact

No `experiment.*` claim is passed.
`experiment.single_body.heavy_top` remains intended.
This diagnostic lane does not implement paper-faithful heavy-top inertia,
paper-faithful heavy-top geometry, raw figure-curve agreement, M-ABD heavy-top
dynamics, rendered-output evidence, timing evidence, or a comparative pass
gate.

## Verification Commands

- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_heavy_top_reference tests.test_experiment_run_configs tests.test_experiment_runner tests.test_phase0_bootstrap`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py`
- `git diff --check`
