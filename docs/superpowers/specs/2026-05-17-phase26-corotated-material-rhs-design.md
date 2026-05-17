# Phase 26 Co-Rotated Material RHS Design

Date: 2026-05-17

## Completion Audit Snapshot

The active objective is complete Newton-only reproduction of the M-ABD paper,
with isolated environment use, durable evidence, multi-angle review, and no
overclaiming. The current repository does not yet satisfy that full objective:

- Newton source is vendored and locally patched under `vendor/newton`.
- The isolated `mabd-newton-py310` environment matches the reference
  `physics-primitive-newton-py310` package set except the editable project line.
- Method claims in `docs/reference/paper-claims.yaml` are mostly passed, but
  every `experiment.*` claim remains `intended`.
- Phase 25 records spinning-box no-polar/material development evidence, but the
  report remains `incomplete`, with angular momentum, energy, and affine shape
  still marked as development gaps. Phase 25 `no_polar` CPU-oracle translation
  handling is a Newton development variant, not a paper-equivalent all-block
  no-polar implementation.
- `docs/reference/claim-boundaries.md` forbids claiming a passed spinning-box
  experiment, paper-faithful implicit RBD baseline, paper-faithful affine
  collision/contact, paper timing, or full paper reproduction from the current
  evidence.

Phase 26 therefore advances the next concrete missing method-to-scene bridge
without changing the full reproduction claim boundary.

## Prompt-To-Artifact Checklist

- Paper source URL and arXiv source: recorded in
  `docs/reference/paper-claims.yaml` and prior records; Phase 26 cites
  `/tmp/mabd-paper/source/sections/singleabd.tex:87-125` for the co-rotated
  constant-matrix local solve, `/tmp/mabd-paper/source/sections/singleabd.tex:127-156`
  only as a no-polar boundary/non-goal, and
  `/tmp/mabd-paper/source/sections/experiment.tex:44-55`.
- A+B complete reproduction: not complete; Phase 26 keeps this as an intended
  goal and only adds bounded evidence.
- Newton-only implementation: Phase 26 modifies only vendored Newton solver code
  plus project reports/tests/docs.
- Environment cloning and non-pollution: Phase 26 uses
  `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python`; the
  readiness check must continue to show `smoke_passed`.
- Multi-agent/spec review: Phase 26 spec is suitable for independent numerical
  and claim-boundary review before merge.
- Push-to-main workflow: only after tests, docs validator, review disposition,
  and claim-boundary records pass.

## Problem

Phase 25 enabled unconstrained `rotation_mode = no_polar`, but the configured
spinning-box lane still does not use the paper's polar co-rotated
constant-matrix material RHS. The current CPU oracle assembles material force
as a world-space rest-stiffness term before any local rotation:

```text
rhs = (M_A / h) qdot + f_ext - K_A_bar (q - q_rest)
```

For a pure rigid rotation, `K_A_bar(q - q_rest)` is nonzero even though the
paper's co-rotated model treats that state as zero elastic strain. This is not
the final system in Eq. `abd_final`, where the constant prefactored Hessian is
used in a local co-rotated coordinate system.

The immediate scene symptom is that the spinning-box M-ABD development lane can
produce huge angular momentum, energy, and affine-shape gaps after Phase 25
no-polar routing. Exploratory calculations are only used to choose this next
phase; Phase 26 evidence must come from committed tests, generated reports, and
the dated Phase 26 record.

## Approaches Considered

Recommended: add a polar co-rotated local material RHS inside the CPU oracle
step. For `rotation_mode = polar`, rotate all four 3-vector blocks with
`diag_4(R^T)`, subtract `K_A_bar(local_q - rest_q)` in the local frame, solve
with the existing constant `H_A_bar`, then rotate all four increment blocks back
with `diag_4(R)`. This provides scoped single-body CPU-oracle evidence for the
paper's co-rotated constant-matrix material RHS while keeping the current dense
oracle scope.

Alternative: retrofit Phase 25 `no_polar` into the same phase. This is rejected
for Phase 26 because the existing CPU oracle intentionally preserves
world-frame translation for a non-orthogonal `A`, while the paper's no-polar
algorithm applies the shortcut to all four blocks under the near-rotation
assumption. That needs a separate phase with explicit mode naming or all-block
semantics and mass-coupling tests.

Alternative: jump straight to contact or new paper scenes. This is rejected
because the current single-body M-ABD lane still lacks the co-rotated material
RHS needed by the first experiment family.

## Design

### Solver Semantics

`MABDCPUOracleBody.rotation_mode` will support:

- `none`: existing world-coordinate linear solve, unchanged.
- `polar`: full-block co-rotated local RHS using `polar_rotation(A)`.
- `no_polar`: existing Phase 25 affine-only/world-translation development
  behavior, unchanged in Phase 26 and not claimed paper-equivalent.

For `polar`, the step assembly is:

```text
local_q = diag_4(R^T) q
local_inertial_external = diag_4(R^T) ((M_A / h) qdot + f_ext)
local_rhs = local_inertial_external - K_A_bar (local_q - q_rest)
local_delta = solve((M_A / h^2 + K_A_bar), local_rhs)
delta_q = diag_4(R) local_delta
```

The transform applies to all four 3-vector blocks, including translation, which
matches Eq. `abd_final`. For polar mode `R` is orthogonal, so free world
translation is preserved when the mass/stiffness system is rotation invariant.
The no-polar world-translation invariant from Phase 25 remains scoped to that
development mode and is not used for Phase 26 paper-facing spinning-box
diagnostics.

The local residual for polar mode is reported in the local solve system:

```text
||H_A_bar local_delta - local_rhs||
```

### Public Report Lane

The spinning-box M-ABD report will use `rotation_mode = polar` for the scoped
single-body co-rotated material RHS lane. The report will record:

- `mabd_rotation_mode = polar`
- `material_model = paper_linear_elastic_corotated_development`
- `material_rhs_frame = corotated_local_all_blocks`
- `translation_frame = corotated_polar_all_blocks`
- existing material constants and stiffness trace/rank
- existing momentum, energy, trajectory, and affine-shape diagnostics

The report remains `incomplete`. Phase 26 may improve diagnostics, but it does
not pass the paper spinning-box claim.

### Tests

TDD starts with failing tests for:

- `rotation_mode = polar` is accepted for unconstrained CPU oracle steps and
  rejected for constrained CPU oracle steps.
- A pure rigid rotation at rest produces zero internal material impulse for
  polar mode.
- Polar full-block local material RHS is consistent with the existing analytic
  co-rotated elastic force helper on a small non-rigid deformation.
- Polar mode preserves free translation under a rigid rotation.
- The spinning-box M-ABD report records polar/co-rotated local RHS metadata and
  finite diagnostics.

Docs tests and `scripts/validate_docs.py` will require the Phase 26 record,
claim-boundary text, and the continued non-claim status. The validator must add
the record path to `REQUIRED_FILES`, extend `validate_claim_boundaries()`, add
`validate_phase26_record()`, call it from `main()`, update the success string to
end at Phase 26, require `paper-claims.yaml` experiment claims remain unpassed,
and require the spinning-box experiment matrix remains blocked by incomplete
baseline/comparison reports.

The Phase 26 record must include the same concrete provenance pattern as Phase
25: worktree, branch, base commit, spec/plan commit, implementation commit,
docs/record commit, review disposition commit, vendored Newton upstream commit,
local patch summary, paper SHA256/source lines, config path, environment path,
readiness/non-pollution evidence, exact observed metrics and thresholds,
generated-report policy, TDD RED/GREEN evidence, full verification gates, and a
statement that no `experiment.*` claim is passed.

## Non-Goals

Phase 26 does not verify:

- the paper spinning-box experiment as passed;
- paper-faithful implicit RBD baseline;
- paper-faithful affine collision, CCD, friction, or implicit contact solve;
- multi-body constrained no-polar or polar KKT;
- unconfigured production `SolverMABD.step()` behavior beyond the configured
  CPU oracle path;
- Warp kernels, CUDA/GPU paths, or production Newton contact integration;
- paper ABD-ABA, large-scale topology performance, or timing claims;
- paper timing;
- generated videos or rendered trajectory agreement;
- any `experiment.*` claim.

## Verification Gates

Run from the Phase 26 worktree and again after merge:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest newton.tests.test_mabd_phase4_solver_step
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/env/readiness_check.py
git diff --check
```
