# Phase 62 Spinning-Box Contact Response

## Status

passed_for_spinning_box_contact_response_diagnostic_slice

## Scope

Phase 62 records a Newton-only explicit contact-response diagnostic for the
spinning-box paper-horizon M-ABD lane. It evaluates the existing point-plane
penalty contact generalized force from the current M-ABD state and passes that
force through the Newton CPU oracle `external_forces` hook for the next step.
It does not implement a contact solver, collision implementation,
paper-faithful affine collision, or spinning-box experiment pass.

## Repository

- branch: `phase62-spinning-box-contact-response`
- implementation commit: `98f66d7344c3bb09995d1c9187beb1830683195e`
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

- `reports/experiment_matrix/single_body_spinning_box_contact_response.json`
  - sha256:
    `0dac0d45baeccbab0120059112268453b59ceb4af025d123ce1979ecb4c91942`
  - source_commit:
    `98f66d7344c3bb09995d1c9187beb1830683195e`
  - baseline lane: `mabd_newton`
  - solver mode: `mabd_cpu_oracle_contact_response_diagnostic`
  - backend: `cpu_numpy`
  - top-level status: `incomplete`

## Evidence

The report records:

- contact_response_policy =
  `explicit_current_state_penalty_force_as_external_force_next_step`
- contact_response_scope = `diagnostic_only_no_lane_gate`
- contact_response_status = `explicit_response_diagnostic_incomplete`
- retained blocker: `mabd_newton_report_incomplete`
- retained blocker: `mabd_paper_horizon_diagnostic_thresholds_violated`
- retained blocker: `mabd_kinematic_feasibility_blocker_recorded`
- retained blocker: `spinning_box_comparison_pass_gate_not_enabled`
- new blocker: `spinning_box_contact_response_not_paper_faithful`
- new blocker: `contact_response_does_not_reduce_penetration`
- no_response_max_contact_penetration_m = `0.001041191335932834`
- response_max_contact_penetration_m = `0.001041191335932834`
- response_max_applied_contact_force_norm = `5776.765458377781`
- penetration_delta_vs_no_response_m = `0.0`

The explicit response diagnostic applies a nonzero generalized contact force,
but the committed evidence does not reduce the maximum penetration relative to
the Phase 61 no-response diagnostic. The lane therefore remains incomplete.

## Claim Impact

No `experiment.*` claim is passed. `experiment.single_body.spinning_box`
remains intended in `docs/reference/paper-claims.yaml` and blocked by the M-ABD
and comparison gates in the experiment matrix. Phase 62 does not pass the
spinning-box experiment, M-ABD lane, contact solver, collision implementation,
paper-faithful affine collision, comparison pass gate, rendered result, runtime
performance, generated video, raw simulation log, or full paper reproduction.

## Verification Commands

- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_run_configs tests.test_single_body_report_lane`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_runner`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/run_experiment.py --lane spinning_box_contact_response --config configs/experiments/single_body_spinning_box.yaml --matrix configs/experiments/paper_experiment_matrix.yaml --output reports/experiment_matrix/single_body_spinning_box_contact_response.json --source-commit 98f66d7344c3bb09995d1c9187beb1830683195e --vendored-newton-commit 96713fa965463b69c229a4d30582c733ff3526bb`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .`
- `PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/env/readiness_check.py`
- `git diff --check`
