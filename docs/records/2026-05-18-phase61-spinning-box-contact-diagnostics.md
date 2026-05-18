# Phase 61 Spinning-Box Contact Diagnostics

## Status

passed_for_spinning_box_contact_diagnostic_gap_slice

## Scope

Phase 61 records contact penetration and normal-force diagnostics for the
current spinning-box paper-horizon M-ABD diagnostic lane. It does not implement
a contact solver, does not apply contact response to the implicit step, and
does not pass the spinning-box experiment.

## Repository

- branch: `phase61-spinning-box-contact-mabd-lane`
- implementation commit: `TO_BE_BACKFILLED_PHASE61`
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
    `TO_BE_BACKFILLED_PHASE61_REPORT_SHA256`
  - source_commit:
    `TO_BE_BACKFILLED_PHASE61`
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
- max_contact_penetration_m = `TO_BE_BACKFILLED_PHASE61_MAX_PENETRATION`
- max_contact_normal_force_n = `TO_BE_BACKFILLED_PHASE61_MAX_NORMAL_FORCE`
- max_contact_generalized_force_norm =
  `TO_BE_BACKFILLED_PHASE61_MAX_GENERALIZED_FORCE`

The diagnostic policy means contact force is evaluated from current M-ABD
states for evidence only. It is not applied to the step, so the positive
penetration is recorded as a missing contact-response blocker.

## Claim Impact

No `experiment.*` claim is passed. `experiment.single_body.spinning_box`
remains intended in `docs/reference/paper-claims.yaml` and
blocked_by_baselines in the experiment matrix. Phase 61 does not pass the
spinning-box experiment, M-ABD lane, contact solver, collision implementation,
paper-faithful affine collision, comparison pass gate, rendered result, runtime
performance, generated video, raw simulation log, or full paper reproduction.

## Verification Commands

- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_single_body_report_lane tests.test_spinning_box_report_artifacts`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/run_experiment.py --lane mabd_paper_horizon --config configs/experiments/single_body_spinning_box.yaml --output reports/experiment_matrix/single_body_spinning_box_paper_horizon.json --source-commit TO_BE_BACKFILLED_PHASE61 --vendored-newton-commit 96713fa965463b69c229a4d30582c733ff3526bb`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .`
- `PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"`
- `git diff --check`
