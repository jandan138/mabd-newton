# Phase 69 Contacts Input Plane Constraints

## Status

passed_for_solver_mabd_contacts_input_plumbing

## Repository

- branch: `phase68-model-plane-report-lane`
- implementation commit:
  `674064f7558527da92be0f186361df4a7c71d4f7`
- local patch files:
  - `vendor/newton/newton/_src/solvers/mabd/solver_mabd.py`
  - `vendor/newton/newton/tests/test_mabd_phase4_solver_step.py`
  - `tests/test_mabd_phase4_solver_step.py`

## Vendored Newton

- vendored Newton upstream commit:
  `96713fa965463b69c229a4d30582c733ff3526bb`
- local patch status:
  `Phase69 modifies vendored Newton inside this repository; unmodified Newton
  support is not claimed.`

## Environment

- Python:
  `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python`
- reference environment:
  `/cpfs/user/zhuzihou/conda-managed/envs/physics-primitive-newton-py310`
- target environment:
  `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310`
- environment non-pollution:
  `mutates_reference_environment=false`, `uses_reference_python=false`,
  `uses_ambient_python=false`

## Evidence

Phase 69 lets `SolverMABD.step(..., contacts=...)` consume a bounded subset of
precomputed Newton rigid contact rows and append generated point-plane rows to
the existing CPU oracle config. The supported path is static-geometry
plane-constraint plumbing only:

- API: `SolverMABD.step(..., contacts=...)`
- summary type: `MABDContactsInputSummary`
- summary field: `last_contacts_input_summary`
- conversion source: `newton.Contacts.rigid_contact_*`
- policy: `rigid_contacts_to_point_plane_constraints_diagnostic`
- scope: `diagnostic_only_static_geometry_plane_constraints`
- helper: `_cpu_oracle_config_with_contacts`
- duplicate mapping guard:
  `duplicate mabd:body_index mapping for Newton body`
- bounded-count fields:
  `rigid_contact_count`, `rigid_contact_capacity`,
  `rigid_contact_overflow_count`, `rigid_contact_rows_read`,
  `generated_plane_constraint_count`, and `skipped_contact_count`
- supported row shape:
  exactly one rigid contact side maps through `model.shape_body` to a Newton
  body id and then through `mabd:body_index` to one M-ABD body row
- unsupported rows:
  invalid shapes, rows with neither side mapped, rows with both sides mapped,
  and rows beyond `rigid_contact_max` are skipped and counted
- normal convention:
  shape 0 mapped to M-ABD uses `rigid_contact_normal`; shape 1 mapped to M-ABD
  flips the normal

Control input remains unsupported. `Control input remains unsupported` is part
of this phase boundary.

## Tests

Phase 69 adds mirrored tests in the vendored Newton and repository lanes:

- `test_solver_step_consumes_newton_contacts_as_plane_constraints`
- `test_solver_step_flips_contact_normal_when_mabd_body_is_shape1`
- `test_solver_step_records_skipped_and_overflow_contact_rows`
- `test_solver_step_rejects_duplicate_mabd_body_index_mapping_for_contacts`
- `test_solver_step_clears_contacts_summary_when_contacts_none`

Focused implementation checks observed on this branch:

- `PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest newton.tests.test_mabd_phase4_solver_step.MABDPhase4InternalTests.test_solver_step_consumes_newton_contacts_as_plane_constraints`
  - red result before implementation:
    `NotImplementedError: SolverMABD Phase 4 CPU oracle step does not support Contacts input`
- `PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest newton.tests.test_mabd_phase4_solver_step.MABDPhase4InternalTests.test_solver_step_consumes_newton_contacts_as_plane_constraints newton.tests.test_mabd_phase4_solver_step.MABDPhase4InternalTests.test_solver_step_flips_contact_normal_when_mabd_body_is_shape1 newton.tests.test_mabd_phase4_solver_step.MABDPhase4InternalTests.test_solver_step_records_skipped_and_overflow_contact_rows newton.tests.test_mabd_phase4_solver_step.MABDPhase4InternalTests.test_solver_step_rejects_duplicate_mabd_body_index_mapping_for_contacts newton.tests.test_mabd_phase4_solver_step.MABDPhase4InternalTests.test_solver_step_clears_contacts_summary_when_contacts_none`
  - result: `Ran 5 tests ... OK`
- `PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest newton.tests.test_mabd_phase4_solver_step`
  - result: `Ran 34 tests ... OK`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_mabd_phase4_solver_step`
  - result: `Ran 59 tests ... OK`

## Claim Boundary

No `experiment.*` claim is passed. `paper-claims.yaml` is unchanged.

This is not collision detection, not contact solver behavior, not a contact
solver, not broadphase or narrowphase correctness, not active-set generation
inside Newton, not IPC, not friction, not complementarity, not continuous
collision detection, not body-body affine contact, not generic
inequality-constrained M-ABD KKT, not paper-faithful affine collision/contact,
not paper-faithful M-ABD stepping, not a report-lane pass gate, not rendered
output agreement, not runtime performance evidence, not a passed experiment,
and not full paper reproduction.

Boundary keywords: not collision detection; not contact solver; not
paper-faithful affine collision/contact; not full paper reproduction.

## Verification Commands

- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_phase0_bootstrap`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/env/readiness_check.py`
- `PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"`
- `git diff --check`
