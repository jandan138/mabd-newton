# Phase 10 Actuation Forces Record

Date: 2026-05-16

## Status

passed

## Scope

Phase 10 adds CPU oracle helpers that assemble scene-script affine target,
damping, and feedforward controls into M-ABD generalized forces. It also adds
`mabd:control` custom storage rows for later scene import.

This phase verifies force assembly only. It does not verify Newton `Control`
object ingestion, robot inverse kinematics, Franka pick-and-place,
contact-rich grasping, wind/aerodynamic scene dynamics, closed-loop
controllers, GPU/Warp control kernels, timing, paper scenes, or comparative
baselines.

## Source And Environment

- repo base commit: `042d451`
- plan commit: `236b9bf`
- implementation commit: `e87bb72`
- paper source version: arXiv `2603.08079v2`
- paper source paths:
  - `/tmp/mabd-paper/source/sections/singleabd.tex`
  - `/tmp/mabd-paper/source/sections/experiment.tex`
- source basis:
  - `singleabd.tex:23-26`: affine DOF `x_i = J_i q`
  - `experiment.tex:51`: external wrenches map to ABD generalized forces
  - `experiment.tex:184`: wind/aerodynamic loads accumulate as external forces
  - `experiment.tex:224`: Franka scene motivates actuation plus contact
- canonical Python:
  `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python`
- backend: CPU NumPy oracle, with existing Newton/Warp imports in test setup

## Config Path

No experiment config is used in Phase 10. The tested actuation-force behavior
is encoded in:

- `tests/test_mabd_control_forces.py`
- `tests/test_mabd_phase4_solver_step.py`
- `vendor/newton/newton/tests/test_mabd_control_forces.py`

## Repository

- worktree:
  `/cpfs/user/zhuzihou/dev/mabd-newton/.worktrees/phase10-actuation-forces`
- branch: `phase10-actuation-forces`
- base commit: `042d451`
- plan commit: `236b9bf`
- implementation commit: `e87bb72`

## Vendored Newton

- vendored path: `vendor/newton`
- upstream commit: `96713fa965463b69c229a4d30582c733ff3526bb`
- local patch status: Phase 10 adds affine actuation force helper APIs,
  configured CPU oracle force summation, `mabd:control` custom storage, exports,
  and Newton-internal tests on top of the existing M-ABD oracle patch stack.

## Paper Source

- arXiv ID: `2603.08079`
- arXiv version: `v2`
- local PDF: `/tmp/mabd-paper/mabd.pdf`
- local TeX source: `/tmp/mabd-paper/source`
- PDF SHA256:
  `a594e79093673c60fc59ad14f9b71f29a8f7f8e7b1c3d9c73efe6f5814cc6ec0`
- TeX source SHA256:
  `73ec398956c606dec2f8f40f0d38b9d5370e11b27830775e1b3765fe0efc563f`
- affine DOF source: `/tmp/mabd-paper/source/sections/singleabd.tex`
- external force and actuation scene source:
  `/tmp/mabd-paper/source/sections/experiment.tex`
- cited source lines: `singleabd.tex:23-26`, `experiment.tex:51`,
  `experiment.tex:184`, `experiment.tex:224`

## Environment

- Python: `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python`
- Isolation: dependency set cloned from
  `/cpfs/user/zhuzihou/conda-managed/envs/physics-primitive-newton-py310`,
  with the current repo installed editable as `mabd-newton` and the reference
  `primitive-collision-compiler` editable package removed from this env
- Backend: CPU NumPy oracle; Warp imports initialize available CPU/CUDA devices
  for Newton state storage but Phase 10 kernels are not implemented.

## Metrics And Thresholds

- random seed: not applicable; tests use deterministic arrays only
- metrics: 12-DOF position error, velocity error, feedforward force,
  generalized force, per-body summed control force, configured CPU oracle
  external-force update, invalid shape/body/gain errors, custom-frequency count,
  and custom control attribute round trip
- thresholds: `numpy.allclose` defaults for vector checks,
  `unittest.assertAlmostEqual` defaults for scalar checks, and `atol=1.0e-12`
  for the configured CPU oracle state update

## Artifacts

- committed source:
  `vendor/newton/newton/_src/solvers/mabd/control_forces.py`
- committed integration:
  `vendor/newton/newton/_src/solvers/mabd/step_oracle.py`
- committed storage registration:
  `vendor/newton/newton/_src/solvers/mabd/solver_mabd.py`
- committed exports:
  `vendor/newton/newton/_src/solvers/mabd/__init__.py`
- committed tests: `tests/test_mabd_control_forces.py`,
  `tests/test_mabd_phase4_solver_step.py`, and
  `vendor/newton/newton/tests/test_mabd_control_forces.py`
- committed evidence record:
  `docs/records/2026-05-16-phase10-actuation-forces.md`
- raw artifacts: not applicable; no generated run directories, videos, or raw
  logs are committed in this phase

## TDD Evidence

RED commands:

```bash
PYTHONPATH=src:vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  -m unittest tests.test_mabd_control_forces

PYTHONPATH=vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  -m unittest vendor.newton.newton.tests.test_mabd_control_forces

PYTHONPATH=src:vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  -m unittest \
  tests.test_mabd_phase4_solver_step.MABDPhase4SolverStepTests.test_dense_cpu_step_adds_actuation_forces_to_external_forces
```

RED result:

```text
AttributeError: module 'newton._src.solvers.mabd' has no attribute
'MABDActuationSpec'
AttributeError: module 'newton._src.solvers.mabd' has no attribute
'assemble_control_generalized_forces'
AttributeError: Custom attribute 'mabd:control_body' is not defined.
ImportError: cannot import name 'MABDActuationSpec'
```

GREEN commands:

```bash
PYTHONPATH=src:vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  -m unittest tests.test_mabd_control_forces

PYTHONPATH=vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  -m unittest vendor.newton.newton.tests.test_mabd_control_forces

PYTHONPATH=src:vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  -m unittest tests.test_mabd_control_forces tests.test_mabd_phase4_solver_step
```

GREEN result:

```text
public control force tests: Ran 5 tests, OK
vendored internal tests: Ran 3 tests, OK
public focused Phase 4/10 tests: Ran 14 tests, OK
```

## Verified Behavior

- `evaluate_affine_pd_control(...)` returns
  `stiffness * (target_q - q) + damping * (target_qd - qd) + feedforward`.
- Feedforward-only controls are valid and leave missing target errors at zero.
- Scalar and per-DOF nonnegative stiffness/damping gains are accepted.
- Bad body IDs, bad 12-vector shapes, and negative gains raise `ValueError`.
- `assemble_control_generalized_forces(...)` sums multiple controls per body
  and adds them to optional existing external forces.
- `MABDCPUOracleConfig.actuations` contributes to the same configured CPU
  oracle external-force RHS path as other generalized forces.
- `SolverMABD.register_custom_attributes(...)` registers `mabd:control`
  custom-frequency rows and target/damping/feedforward control attributes.

## Final Verification

Final verification commands:

```bash
/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_mabd_control_forces tests.test_mabd_phase4_solver_step tests.test_phase0_bootstrap
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest vendor.newton.newton.tests.test_mabd_control_forces
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"
git diff --check
```

Final verification result:

```text
ruff: All checks passed!
docs: Phase 0/1/2/3/4/5/6/7/8/9/10 docs/provenance validation passed
focused public tests: Ran 29 tests, OK
vendored internal tests: Ran 3 tests, OK
full public tests: Ran 86 tests, OK
vendored Newton import: vendor/newton/newton/__init__.py
git diff --check: clean
```

## Claim Impact

New passed method claim:

- `method.actuation.affine_control_forces`

No `experiment.*` claim is passed in this phase.
