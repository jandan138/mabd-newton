# Phase 11 Control Row Extraction Record

Date: 2026-05-17

## Status

passed

## Scope

Phase 11 strengthens `method.actuation.affine_control_forces` by proving that
stored Newton `mabd:control` rows can be converted into CPU-oracle actuation
specs.

This phase does not verify Newton `Control` object ingestion, time-varying
controller updates, robot inverse kinematics, Franka pick-and-place,
contact-rich grasping, paper scenes, timing, or comparative baselines.

## Source And Environment

- repo base commit: `0d2d15a`
- plan commit: `8d2ca19`
- implementation commit: `06fb7b3`
- paper source version: arXiv `2603.08079v2`
- paper source paths:
  - `/tmp/mabd-paper/source/sections/singleabd.tex`
  - `/tmp/mabd-paper/source/sections/experiment.tex`
- source basis:
  - `singleabd.tex:23-26`: affine DOF `x_i = J_i q`
  - `experiment.tex:224`: Franka scene motivates actuation plus contact
- canonical Python:
  `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python`
- backend: CPU NumPy oracle, with existing Newton/Warp imports in test setup

## Config Path

No experiment config is used in Phase 11. The tested control-row extraction
behavior is encoded in:

- `tests/test_mabd_control_forces.py`
- `vendor/newton/newton/tests/test_mabd_control_forces.py`

## Repository

- worktree:
  `/cpfs/user/zhuzihou/dev/mabd-newton/.worktrees/phase11-control-row-extraction`
- branch: `phase11-control-row-extraction`
- base commit: `0d2d15a`
- plan commit: `8d2ca19`
- implementation commit: `06fb7b3`

## Vendored Newton

- vendored path: `vendor/newton`
- upstream commit: `96713fa965463b69c229a4d30582c733ff3526bb`
- local patch status: Phase 11 adds extraction of Newton `mabd:control`
  custom model rows into `MABDActuationSpec` values on top of the existing
  M-ABD oracle patch stack.

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
- actuation scene source: `/tmp/mabd-paper/source/sections/experiment.tex`
- cited source lines: `singleabd.tex:23-26`, `experiment.tex:224`

## Environment

- Python: `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python`
- Isolation: dependency set cloned from
  `/cpfs/user/zhuzihou/conda-managed/envs/physics-primitive-newton-py310`,
  with the current repo installed editable as `mabd-newton`
- Backend: CPU NumPy oracle; Warp imports initialize available CPU/CUDA devices
  for Newton model storage but Phase 11 kernels are not implemented.

## Metrics And Thresholds

- random seed: not applicable; tests use deterministic arrays only
- metrics: enabled control row count, disabled row filtering, body id,
  stiffness, damping, target affine state, target affine velocity, feedforward
  force, bad body-reference error, and configured CPU oracle state update from
  extracted specs
- thresholds: exact integer equality for counts/body ids, `numpy.allclose`
  defaults for vector checks, `unittest.assertAlmostEqual` defaults for scalar
  checks, and `atol=1.0e-12` for the configured CPU oracle state update

## Artifacts

- committed source:
  `vendor/newton/newton/_src/solvers/mabd/control_forces.py`
- committed exports:
  `vendor/newton/newton/_src/solvers/mabd/__init__.py`
- committed tests: `tests/test_mabd_control_forces.py` and
  `vendor/newton/newton/tests/test_mabd_control_forces.py`
- committed evidence record:
  `docs/records/2026-05-17-phase11-control-row-extraction.md`
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
```

RED result:

```text
AttributeError: module 'newton._src.solvers.mabd' has no attribute
'actuation_specs_from_model'
ImportError: cannot import name 'actuation_specs_from_model'
```

GREEN commands:

```bash
PYTHONPATH=src:vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  -m unittest tests.test_mabd_control_forces

PYTHONPATH=vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  -m unittest vendor.newton.newton.tests.test_mabd_control_forces
```

GREEN result:

```text
public control force tests: Ran 9 tests, OK
vendored internal tests: Ran 4 tests, OK
```

## Verified Behavior

- `actuation_specs_from_model(model)` extracts enabled `mabd:control` rows into
  `MABDActuationSpec` values.
- The helper packs target affine state, target affine velocity, and feedforward
  `vec3` rows into 12-DOF arrays.
- Disabled control rows are skipped by default and included when
  `enabled_only=False`.
- Enabled rows with body ids outside the registered `mabd:body` range raise
  `ValueError`.
- Extracted specs can be passed to `MABDCPUOracleConfig.actuations` and affect
  the configured CPU oracle RHS.

## Final Verification

Final verification commands:

```bash
/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_mabd_control_forces tests.test_phase0_bootstrap
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest vendor.newton.newton.tests.test_mabd_control_forces
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"
git diff --check
```

Final verification result:

```text
ruff: All checks passed!
docs: Phase 0/1/2/3/4/5/6/7/8/9/10/11 docs/provenance validation passed
focused public tests: Ran 26 tests, OK
vendored internal tests: Ran 4 tests, OK
full public tests: Ran 93 tests, OK
vendored Newton import: vendor/newton/newton/__init__.py
git diff --check: clean
```

## Claim Impact

Strengthened existing method claim:

- `method.actuation.affine_control_forces`

No `experiment.*` claim is passed in this phase.
