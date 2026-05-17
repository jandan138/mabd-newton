# Phase 25 Spinning-Box No-Polar Material Lane Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> superpowers:subagent-driven-development (recommended) or
> superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enable the unconstrained M-ABD CPU oracle's no-polar single-body path
and wire paper material stiffness into the configured spinning-box M-ABD report
lane.

**Architecture:** Keep the implementation Newton-first. Modify only the
vendored Newton CPU oracle routing and the project report/physics helpers. Keep
constrained KKT/topology solves on `rotation_mode = "none"` until their rotated
Hessian/RHS assembly is explicitly implemented and tested.

**Tech Stack:** Python 3.10, NumPy, vendored Newton/Warp, `unittest`, Markdown
records, `scripts/validate_docs.py`.

---

### Task 1: CPU Oracle No-Polar Routing

**Files:**
- Modify: `vendor/newton/newton/_src/solvers/mabd/step_oracle.py`
- Modify: `tests/test_mabd_phase4_solver_step.py`
- Modify: `vendor/newton/newton/tests/test_mabd_phase4_solver_step.py`

- [ ] **Step 1: Write failing tests**

Add focused tests requiring:

- an unconstrained single-body CPU oracle with `rotation_mode="no_polar"` runs
  without raising `NotImplementedError`;
- the no-polar result matches `mabd.solve_single_body_delta(...)` using the
  current affine matrix `A`;
- a constrained CPU oracle with a no-polar body raises a clear
  `NotImplementedError`.

- [ ] **Step 2: Run RED**

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_mabd_phase4_solver_step
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest newton.tests.test_mabd_phase4_solver_step
```

Expected: the unconstrained no-polar test fails because `_validate_config`
currently rejects non-`none` rotation modes.

- [ ] **Step 3: Implement no-polar routing**

Update `step_oracle.py` to:

- allow body `rotation_mode` values in `{"none", "no_polar"}`;
- keep unsupported modes rejected with a clear message;
- pass bodies into `_unconstrained_step`;
- use `mabd.unpack_q(body_q)` to obtain `A` and call
  `solve_single_body_delta` for no-polar body solves;
- reject non-`none` body rotation modes before constrained KKT assembly.

- [ ] **Step 4: Run GREEN**

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_mabd_phase4_solver_step
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest newton.tests.test_mabd_phase4_solver_step
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check vendor/newton/newton/_src/solvers/mabd/step_oracle.py tests/test_mabd_phase4_solver_step.py vendor/newton/newton/tests/test_mabd_phase4_solver_step.py
git diff --check
```

- [ ] **Step 5: Commit**

```bash
git add vendor/newton/newton/_src/solvers/mabd/step_oracle.py tests/test_mabd_phase4_solver_step.py vendor/newton/newton/tests/test_mabd_phase4_solver_step.py
git commit -m "feat: enable no-polar M-ABD CPU oracle steps"
```

### Task 2: Paper Material Stiffness In Spinning-Box Lane

**Files:**
- Modify: `src/mabd_reproduction/spinning_box_physics.py`
- Modify: `src/mabd_reproduction/single_body_reports.py`
- Modify: `tests/test_single_body_report_lane.py`

- [ ] **Step 1: Write failing tests**

Extend the configured spinning-box report test to require:

- `mabd_rotation_mode == "no_polar"`;
- `material_model == "paper_linear_elastic_no_polar_development"`;
- `material_young_modulus_pa == 1.0e9`;
- `material_poisson_ratio == 0.3`;
- `material_volume_m3 == 0.001`;
- positive finite `material_stiffness_trace`;
- positive `material_stiffness_rank`;
- finite final affine diagnostics.

- [ ] **Step 2: Run RED**

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_single_body_report_lane
```

Expected: missing material/no-polar observed fields.

- [ ] **Step 3: Implement material helper and report wiring**

Add `spinning_box_mabd_material_stiffness(config)` to
`spinning_box_physics.py`, validating paper `material_E`, `poisson`, and cube
volume before calling `mabd.rest_generalized_stiffness_matrix`.

Update `_oracle_body(config)` in `single_body_reports.py` to:

- use the configured mass diagonal;
- use paper material stiffness when `config is not None`;
- set `rest_q` to identity affine plus the configured initial translation;
- set `rotation_mode="no_polar"` for the configured spinning-box lane.

Promote the material and rotation observed fields into the report.

- [ ] **Step 4: Run GREEN**

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_single_body_report_lane
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check src/mabd_reproduction/spinning_box_physics.py src/mabd_reproduction/single_body_reports.py tests/test_single_body_report_lane.py
git diff --check
```

- [ ] **Step 5: Commit**

```bash
git add src/mabd_reproduction/spinning_box_physics.py src/mabd_reproduction/single_body_reports.py tests/test_single_body_report_lane.py
git commit -m "feat: use paper material stiffness in spinning box M-ABD lane"
```

### Task 3: Phase 25 Docs And Gates

**Files:**
- Modify: `docs/reference/claim-boundaries.md`
- Create: `docs/records/2026-05-17-phase25-spinning-box-no-polar-material-lane.md`
- Modify: `scripts/validate_docs.py`
- Modify: `tests/test_phase0_bootstrap.py`

- [ ] **Step 1: Write failing docs tests**

Add Phase 25 bootstrap tests requiring claim-boundary and record snippets for:

- no-polar unconstrained CPU oracle routing;
- paper material constants and stiffness fields;
- constrained no-polar KKT remains unsupported;
- isolated cloned environment evidence;
- explicit non-claims for paper trajectory agreement, timing, affine collision,
  and passed `experiment.*` claims.

- [ ] **Step 2: Run RED**

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_phase0_bootstrap
```

Expected: missing Phase 25 boundary, record, and validator output.

- [ ] **Step 3: Add docs, record, and validator checks**

Update claim boundaries, add the Phase 25 record, and extend
`scripts/validate_docs.py` to require the new record and print `/25`.

- [ ] **Step 4: Run docs GREEN**

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_phase0_bootstrap
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check scripts/validate_docs.py tests/test_phase0_bootstrap.py
git diff --check
```

- [ ] **Step 5: Commit and harden provenance**

Commit the docs record, then backfill the docs/provenance commit hash into the
record, validator, and test. Re-run focused docs checks and commit the
hardening change.

### Task 4: Review, Full Verification, Merge

**Files:**
- No code changes expected unless review finds a defect.

- [ ] **Step 1: Run full gates**

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/env/readiness_check.py
git diff --check
```

- [ ] **Step 2: Request review**

Use independent review for:

- Newton no-polar routing and constrained-path boundary;
- report/material/claim-boundary provenance.

- [ ] **Step 3: Address findings**

Fix only validated defects, rerun focused checks, and commit the disposition.

- [ ] **Step 4: Merge and push**

After all gates pass, merge Phase 25 to `main`, push to origin, remove the
worktree, and verify `main` remains clean and aligned with `origin/main`.
