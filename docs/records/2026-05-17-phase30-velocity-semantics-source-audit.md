# Phase 30 Velocity Semantics Source Audit Record

Date: 2026-05-17

## Status

passed

## Scope

Phase 30 records a targeted paper-source audit for the single-body spinning-box
velocity and momentum semantics. The audit verifies the paper source supports
implicit-Euler inertia potential, `G(A)` twist mapping, `G(A)^T` wrench mapping,
and spinning-box initialization through a target spatial twist, while not
specifying decoupled velocity semantics or an alternative momentum extraction
rule for the figure.

The audit status is `source_does_not_prove_decoupled_velocity_semantics`. This
phase does not change Newton solver behavior and does not pass the M-ABD lane,
the spinning-box comparison, or any paper experiment.

## Config Path

- `configs/experiments/single_body_spinning_box.yaml`
- `configs/experiments/paper_experiment_matrix.yaml`

## Repository

- worktree:
  `/cpfs/user/zhuzihou/dev/mabd-newton/.worktrees/phase30-velocity-semantics-source-audit`
- branch: `phase30-velocity-semantics-source-audit`
- base commit: `6683d92`
- design/plan commit: `c97ee49`
- source-audit implementation commit: `d180e58`
- docs/record commit: `ee188d0`
- independent review: source audit is intentionally bounded to the public
  arXiv TeX/PDF figure source available locally; it does not infer private
  author-code behavior.

## Vendored Newton

- vendored path: `vendor/newton`
- upstream commit: `96713fa965463b69c229a4d30582c733ff3526bb`
- local patch status: Phase 30 does not modify vendored Newton.

## Paper Source

- arXiv ID: `2603.08079`
- arXiv version: `v2`
- source root: `/tmp/mabd-paper/source`
- source root setup: `/tmp/mabd-paper/source` must exist locally before
  running the Phase 30 source audit or docs validator.
- sections/singleabd.tex SHA256:
  `0f18165cba13d358a07c67a652e728170abecd7372b5ba905ff2b4a5950a3e8d`
- sections/solver.tex SHA256:
  `871dbd7ae7f5544b95c6c4dc0940cb6a0e73eca48415b1abed2e3599db90c97e`
- sections/experiment.tex SHA256:
  `c5927183fe4e3f1c1c1617e5b10b7e9006da6a9eac537e891cb1dac03d58dd0f`
- images/cube/roll_cube.pdf SHA256:
  `7669b062348324a3b0090cc9f44930655c83233a87f63389db9198b88f95ae80`
- cited source lines: `singleabd.tex:34-42`, `solver.tex:219-241`,
  `experiment.tex:40-55`
- scanned TeX source includes: `arxiv.tex`, `sections/singleabd.tex`, `sections/solver.tex`, `sections/experiment.tex`, `sections_a/multiabd.tex`

## Environment

- Python: `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python`
- reference clone source:
  `/cpfs/user/zhuzihou/conda-managed/envs/physics-primitive-newton-py310`
- readiness status: `smoke_passed`
- readiness JSON output: branch-gate stdout, not committed.
- non-pollution result: `mutates_reference_environment=false`,
  `uses_reference_python=false`, `uses_ambient_python=false`

## Metrics And Diagnostics

- random seed: not applicable; the audit is deterministic.
- audit_status = source_does_not_prove_decoupled_velocity_semantics
- implicit_euler_inertia_potential = present
- g_map_twist_velocity = present
- wrench_map_generalized_force = present
- spinning_box_twist_initialization = present
- blocker: `source_does_not_specify_decoupled_velocity_semantics`
- blocker: `source_does_not_specify_alternative_momentum_extraction`
- matrix blocker retained: `mabd_newton_report_incomplete`
- matrix blocker retained: `spinning_box_comparison_report_incomplete`
- No `experiment.*` claim is passed in this phase.

## Artifacts

- committed project code:
  `src/mabd_reproduction/paper_source_audit.py`
- committed tests:
  `tests/test_paper_source_audit.py`,
  `tests/test_phase0_bootstrap.py`
- docs validator: `scripts/validate_docs.py`
- raw paper assets: not committed
- generated reports: not committed
- raw artifacts: temporary unittest output and branch-gate stdout only

## Verification Commands

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_paper_source_audit
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_phase0_bootstrap
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
git diff --check
```

## TDD Evidence

Source-audit RED result:

```text
ModuleNotFoundError: No module named 'mabd_reproduction.paper_source_audit'
```

Source-audit GREEN result:

```text
Ran 2 tests, OK
```

Docs RED result:

```text
missing claim boundary bullet: This repository contains Phase 30
FileNotFoundError: docs/records/2026-05-17-phase30-velocity-semantics-source-audit.md
```

## Claim Impact

No `experiment.*` claim is passed in this phase. The single-body spinning-box
matrix still lists `mabd_newton_report_incomplete` and
`spinning_box_comparison_report_incomplete`. Phase 30 only records public-source
evidence boundaries for the next solver-semantics decision.
