# Phase 61 Spinning-Box Contact Diagnostics

## Status

passed_for_spinning_box_contact_diagnostic_gap_slice

## Scope

Phase 61 records contact penetration and normal-force diagnostics for the
current spinning-box paper-horizon M-ABD diagnostic lane. It does not implement a contact solver, records the report policy that contact response is not applied to the implicit step, and does not pass the spinning-box experiment.

## Repository

- branch: `phase61-spinning-box-contact-mabd-lane`
- implementation commit: `e11cb83163368af36a5000fa3a1338a8c6206aab`
- vendored Newton commit: `96713fa965463b69c229a4d30582c733ff3526bb`
- paper: `2603.08079v2`
- canonical Python:
  `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python`

## Environment

- environment role: `mabd-newton-clone`
- reference environment: `physics-primitive-newton-py310`
- mutates_reference_environment=false
- uses_reference_python=false
- uses_ambient_python=false
- readiness status: `smoke_passed`

## Report Artifact

- `reports/experiment_matrix/single_body_spinning_box_paper_horizon.json`
  - sha256:
    `7f538d76fb9a123db022c8f64682aceb1b55fecb74d6f8ff577fc3847b5b0fa9`
  - source_commit:
    `e11cb83163368af36a5000fa3a1338a8c6206aab`
  - baseline lane: `mabd_newton`
  - solver mode: `mabd_cpu_oracle_paper_horizon_diagnostic`
  - backend: `cpu_numpy`
  - top-level status: `incomplete`

## Evidence

The report now records:

- contact_diagnostic_policy = `evaluated_from_current_mabd_states_not_applied_to_step`
- contact_diagnostic_status = `contact_penetration_observed_without_response`
- retained blocker: `mabd_newton_report_incomplete`
- retained blocker: `mabd_paper_horizon_diagnostic_thresholds_violated`
- retained blocker: `mabd_kinematic_feasibility_blocker_recorded`
- new blocker: `spinning_box_contact_response_missing`
- max_contact_active_count = `4`
- max_contact_penetration_m = `0.001041191335932834`
- max_contact_normal_force_n = `5769.558012703554`
- max_contact_generalized_force_norm =
  `5776.765458377781`

The diagnostic policy records contact force evaluation from current M-ABD
states for evidence only, with a report policy that the diagnostic is not
applied to the step. The positive penetration is therefore recorded as a
missing contact-response blocker.

## Claim Impact

No `experiment.*` claim is passed. `experiment.single_body.spinning_box`
remains intended in `docs/reference/paper-claims.yaml` and
blocked_by_baselines in the experiment matrix. Phase 61 does not pass the
spinning-box experiment, M-ABD lane, contact solver, collision implementation,
paper-faithful affine collision, comparison pass gate, rendered result, runtime
performance, generated video, raw simulation log, or full paper reproduction.

## Verification Commands

- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_single_body_report_lane tests.test_spinning_box_report_artifacts`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/run_experiment.py --lane mabd_paper_horizon --config configs/experiments/single_body_spinning_box.yaml --output reports/experiment_matrix/single_body_spinning_box_paper_horizon.json --source-commit e11cb83163368af36a5000fa3a1338a8c6206aab --vendored-newton-commit 96713fa965463b69c229a4d30582c733ff3526bb`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .`
- `PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"`
- `git diff --check`
