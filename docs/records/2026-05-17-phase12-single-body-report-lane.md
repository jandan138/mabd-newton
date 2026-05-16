# Phase 12 Single-Body Report Lane Record

Date: 2026-05-17

## Status

passed

## Scope

Phase 12 adds full-schema `ClaimReport` JSON validation and a deterministic
single-body spinning-box M-ABD development report lane.

This phase does not verify the paper spinning-box experiment, paper timing,
RK4/RBD/analytic baselines, rendered output, paper trajectory agreement, or any
passed `experiment.*` claim. The generated development report intentionally
uses `EvidenceStatus.INCOMPLETE` because full paper evidence still requires
baseline lanes.

## Source And Environment

- repo base commit: `ebf3c3d`
- plan commit: `f9df80e`
- implementation commits: `bf3e0fc`, `6d484da`
- paper source version: arXiv `2603.08079v2`
- paper source paths:
  - `/tmp/mabd-paper/source/sections/experiment.tex`
- source basis:
  - `experiment.tex:40-55`: spinning-box momentum and energy diagnostic text
- canonical Python:
  `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python`
- backend: CPU NumPy oracle through vendored Newton imports

## Config Path

No experiment config is used in Phase 12. The tested development report lane is
encoded in:

- `tests/test_reporting_contracts.py`
- `tests/test_single_body_report_lane.py`

## Repository

- worktree:
  `/cpfs/user/zhuzihou/dev/mabd-newton/.worktrees/phase12-single-body-report-lane`
- branch: `phase12-single-body-report-lane`
- base commit: `ebf3c3d`
- plan commit: `f9df80e`
- implementation commits: `bf3e0fc`, `6d484da`

## Vendored Newton

- vendored path: `vendor/newton`
- upstream commit: `96713fa965463b69c229a4d30582c733ff3526bb`
- local patch status: Phase 12 adds no vendored Newton source changes; it uses
  the existing M-ABD CPU oracle to generate a development report.

## Paper Source

- arXiv ID: `2603.08079`
- arXiv version: `v2`
- local PDF: `/tmp/mabd-paper/mabd.pdf`
- local TeX source: `/tmp/mabd-paper/source`
- PDF SHA256:
  `a594e79093673c60fc59ad14f9b71f29a8f7f8e7b1c3d9c73efe6f5814cc6ec0`
- TeX source SHA256:
  `73ec398956c606dec2f8f40f0d38b9d5370e11b27830775e1b3765fe0efc563f`
- cited source lines: `experiment.tex:40-55`

## Environment

- Python: `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python`
- Isolation: dependency set cloned from
  `/cpfs/user/zhuzihou/conda-managed/envs/physics-primitive-newton-py310`,
  with the current repo installed editable as `mabd-newton`
- Backend: CPU NumPy oracle; Warp imports are available through vendored Newton
  but this phase does not add kernels.

## Metrics And Thresholds

- random seed: not applicable; tests use deterministic arrays only
- metrics: full-schema report required keys, invalid status rejection, JSON
  round trip, deterministic step count, energy drift, generalized momentum
  delta norm, and incomplete report status
- thresholds: exact key/status equality, `energy_drift <= 1.0e-12`, and
  `generalized_momentum_delta_norm <= 1.0e-12`

## Artifacts

- committed source:
  `src/mabd_reproduction/reporting.py`
- committed development lane:
  `src/mabd_reproduction/single_body_reports.py`
- committed tests: `tests/test_reporting_contracts.py` and
  `tests/test_single_body_report_lane.py`
- committed evidence record:
  `docs/records/2026-05-17-phase12-single-body-report-lane.md`
- generated reports: not committed; tests write JSON reports to temporary
  directories only
- raw artifacts: not applicable; no generated run directories, videos, or raw
  logs are committed in this phase

## TDD Evidence

RED commands:

```bash
PYTHONPATH=src:vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  -m unittest tests.test_reporting_contracts

PYTHONPATH=src:vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  -m unittest tests.test_single_body_report_lane
```

RED result:

```text
ImportError: cannot import name 'load_claim_report'
ModuleNotFoundError: No module named 'mabd_reproduction.single_body_reports'
```

GREEN commands:

```bash
PYTHONPATH=src:vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  -m unittest tests.test_reporting_contracts tests.test_phase0_bootstrap

PYTHONPATH=src:vendor/newton \
  /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  -m unittest tests.test_single_body_report_lane tests.test_reporting_contracts
```

GREEN result:

```text
reporting contracts plus bootstrap: Ran 20 tests, OK
single-body report lane plus reporting contracts: Ran 4 tests, OK
```

## Verified Behavior

- Full-schema `ClaimReport` JSON round trips preserve required fields.
- Report validation rejects missing schema keys and unknown statuses.
- `write_spinning_box_development_report` writes a machine-checkable report for
  `experiment.single_body.spinning_box`.
- The development report records `baseline_lane=mabd_newton` and
  `EvidenceStatus.INCOMPLETE`.
- The report explicitly cites missing `rbd_implicit_baseline` evidence rather
  than marking the experiment claim passed.

## Final Verification

Final verification commands:

```bash
/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_reporting_contracts tests.test_single_body_report_lane tests.test_phase0_bootstrap
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"
git diff --check
```

Final verification result:

```text
ruff: All checks passed!
docs: Phase 0/1/2/3/4/5/6/7/8/9/10/11/12 docs/provenance validation passed
focused public tests: Ran 23 tests, OK
full public tests: Ran 99 tests, OK
vendored Newton import:
  /cpfs/user/zhuzihou/dev/mabd-newton/.worktrees/phase12-single-body-report-lane/vendor/newton/newton/__init__.py
git diff --check: clean
```

## Claim Impact

No `experiment.*` claim is passed in this phase.
