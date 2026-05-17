# Phase 42 Spinning Box Report Artifacts

Date: 2026-05-17

## Status

passed

## Repository

- branch: `phase42-spinning-box-report-artifacts`
- report source_commit: `75a676791084ca0f77fe16fc1902814a5bb8d148`
- plan: `docs/superpowers/plans/2026-05-17-mabd-phase42-spinning-box-report-artifacts.md`
- spec: `docs/superpowers/specs/2026-05-17-phase42-spinning-box-report-artifacts-design.md`

## Environment

- interpreter:
  `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python`
- environment role: `mabd-newton-clone`
- reference environment: `physics-primitive-newton-py310`
- mutates_reference_environment=false
- uses_reference_python=false
- uses_ambient_python=false
- vendored Newton commit:
  `96713fa965463b69c229a4d30582c733ff3526bb`

## Report Artifacts

All report artifacts are compact JSON summaries under `reports/experiment_matrix/`.
No raw simulation directories, videos, or large logs are committed.

- `reports/experiment_matrix/single_body_spinning_box.json`
  - sha256:
    `fa487e5b2d5141d32e24764f52788d247ffe84a433e65196aae4a3b084b0f87c`
  - baseline lane: `mabd_newton`
  - solver mode: `mabd_cpu_oracle_development`
  - status: `incomplete`
- `reports/experiment_matrix/single_body_spinning_box_paper_horizon.json`
  - sha256:
    `f6835a95c89bf7d017dae0bd5001e39ad3c4d1436c46af23c21243334c650957`
  - baseline lane: `mabd_newton`
  - solver mode: `mabd_cpu_oracle_paper_horizon_diagnostic`
  - status: `incomplete`
  - retained blocker: `mabd_paper_horizon_diagnostic_thresholds_violated`
  - retained blocker: `mabd_kinematic_feasibility_blocker_recorded`
- `reports/experiment_matrix/single_body_spinning_box_rbd_baseline.json`
  - sha256:
    `64e7fda65ed0a25f2e9e2d4fbcbddaed1a75c7f0aba5aa56f79517db6e507836`
  - baseline lane: `rbd_implicit_baseline`
  - solver mode: `paper_faithful_implicit_rbd`
  - status: `incomplete`
  - rbd_implicit_baseline lane_gate_status = `passed`
- `reports/experiment_matrix/single_body_spinning_box_comparison.json`
  - sha256:
    `357676246e8d9fb1297966f2a698d6031610bb3fab9e814e51ddb671a04ad5b9`
  - baseline lane: `spinning_box_comparison_protocol`
  - solver mode: `spinning_box_multilane_comparison_development`
  - status: `incomplete`
  - mabd_newton lane_gate_status = `incomplete`
  - rbd_implicit_baseline lane_gate_status = `passed`
  - missing_required_metrics = `[]`
  - invalid_required_metrics = `[]`
  - missing_required_vector_metrics = `[]`
  - invalid_required_vector_metrics = `[]`
  - retained blocker: `mabd_newton_report_incomplete`
  - retained blocker: `spinning_box_comparison_pass_gate_not_enabled`

## Runner Commands

The reports were generated with the existing config-driven runner and the
isolated M-ABD Newton Python environment:

- `scripts/run_experiment.py --lane mabd_newton`
- `scripts/run_experiment.py --lane mabd_paper_horizon`
- `scripts/run_experiment.py --lane rbd_implicit_baseline`
- `scripts/run_experiment.py --lane spinning_box_comparison`

All four commands used:

- config: `configs/experiments/single_body_spinning_box.yaml`
- matrix: `configs/experiments/paper_experiment_matrix.yaml`
- fixed report source commit:
  `75a676791084ca0f77fe16fc1902814a5bb8d148`
- vendored Newton commit:
  `96713fa965463b69c229a4d30582c733ff3526bb`

## Claim Impact

No `experiment.*` claim is passed.
`experiment.single_body.spinning_box` remains blocked_by_baselines in the paper
experiment matrix and remains intended in `docs/reference/paper-claims.yaml`.
Phase 42 does not pass the spinning-box experiment. It commits replayable
spinning-box report artifacts, and it also does not pass the M-ABD lane,
paper-horizon diagnostic, comparison pass gate, rendered output, runtime
performance, generated videos, or raw simulation logs.

## Verification Commands

- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests -p 'test_spinning_box_report_artifacts.py'`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_phase0_bootstrap`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py`
- `PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"`
- `git diff --check`
