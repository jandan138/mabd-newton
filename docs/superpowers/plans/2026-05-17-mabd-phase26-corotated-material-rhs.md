# Phase 26 Co-Rotated Material RHS Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move polar unconstrained CPU oracle material RHS assembly into the paper co-rotated local solve frame and record bounded spinning-box evidence.

**Architecture:** Keep `rotation_mode = none` and the Phase 25 `no_polar` development behavior unchanged. Add full `diag_4(R^T)` and `diag_4(R)` local-frame assembly in vendored Newton `step_oracle.py` for `rotation_mode = polar`. Update the spinning-box M-ABD report lane to use `polar` and record co-rotated all-block local RHS metadata while keeping the experiment report incomplete.

**Tech Stack:** Python 3.10, NumPy, vendored Newton `unittest`, project report validators, docs records under `docs/records`.

---

## File Structure

- Modify: `vendor/newton/newton/_src/solvers/mabd/step_oracle.py`
  - Accept `rotation_mode = polar`.
  - Assemble local co-rotated material RHS for `polar`.
  - Keep constrained rotated KKT unsupported.
- Modify: `tests/test_mabd_phase4_solver_step.py`
  - Public API regression tests for polar co-rotated material RHS.
- Modify: `vendor/newton/newton/tests/test_mabd_phase4_solver_step.py`
  - Vendored internal mirror tests.
- Modify: `src/mabd_reproduction/single_body_reports.py`
  - Set configured spinning-box M-ABD report lane to `polar`.
  - Record `material_rhs_frame` and `translation_frame`.
- Modify: `tests/test_single_body_report_lane.py`
  - Assert Phase 26 report fields and finite bounded diagnostics.
- Modify: `tests/test_spinning_box_comparison.py`
  - Update expected M-ABD metric ranges for the co-rotated lane.
- Modify: `docs/reference/claim-boundaries.md`
  - Add Phase 26 bounded evidence and non-claims.
- Create: `docs/records/2026-05-17-phase26-corotated-material-rhs.md`
  - New dated record.
- Modify: `scripts/validate_docs.py`
  - Require Phase 26 record and snippets.
- Modify: `tests/test_phase0_bootstrap.py`
  - Require Phase 26 boundary/record snippets.

## Task 1: CPU Oracle RED Tests

**Files:**
- Modify: `tests/test_mabd_phase4_solver_step.py`
- Modify: `vendor/newton/newton/tests/test_mabd_phase4_solver_step.py`

- [ ] **Step 1: Add public failing tests**

Add these tests after `test_no_polar_cpu_step_preserves_free_translation_in_world_frame`:

```python
    def test_polar_cpu_step_treats_pure_rotation_as_zero_material_strain(self) -> None:
        theta = 0.43
        R = np.array(
            [
                [np.cos(theta), -np.sin(theta), 0.0],
                [np.sin(theta), np.cos(theta), 0.0],
                [0.0, 0.0, 1.0],
            ],
            dtype=float,
        )
        q = mabd.pack_q(R, np.array([0.2, -0.1, 0.3]))
        rest_q = _identity_q((0.2, -0.1, 0.3))
        stiffness = mabd.rest_generalized_stiffness_matrix(80.0, 0.25, 0.35)
        dt = 0.04

        result = mabd.solve_cpu_oracle_step(
            q=[q],
            qd=[np.zeros(12)],
            dt=dt,
            config=mabd.MABDCPUOracleConfig(
                bodies=[_body_with_stiffness(stiffness, rest_q, rotation_mode="polar")]
            ),
        )

        self.assertTrue(np.allclose(result.q[0], q, atol=1.0e-12))
        self.assertTrue(np.allclose(result.qd[0], np.zeros(12), atol=1.0e-12))
        self.assertLess(result.residual_norm, 1.0e-12)

    def test_polar_cpu_step_matches_corotated_material_force_for_small_deformation(self) -> None:
        theta = 0.2
        R = np.array(
            [
                [np.cos(theta), -np.sin(theta), 0.0],
                [np.sin(theta), np.cos(theta), 0.0],
                [0.0, 0.0, 1.0],
            ],
            dtype=float,
        )
        stretch = np.diag([1.02, 0.99, 1.01])
        A = R @ stretch
        q = mabd.pack_q(A, np.array([0.2, -0.1, 0.3]))
        rest_q = _identity_q((0.2, -0.1, 0.3))
        young = 80.0
        poisson = 0.25
        volume = 0.35
        stiffness = mabd.rest_generalized_stiffness_matrix(young, poisson, volume)
        dt = 0.04

        result = mabd.solve_cpu_oracle_step(
            q=[q],
            qd=[np.zeros(12)],
            dt=dt,
            config=mabd.MABDCPUOracleConfig(
                bodies=[_body_with_stiffness(stiffness, rest_q, rotation_mode="polar")]
            ),
        )

        material_force = mabd.co_rotated_linear_elastic_affine_force(A, young, poisson, volume)
        expected_dq = np.linalg.solve(
            np.eye(12) / (dt * dt) + stiffness,
            mabd.apply_polar_rhs_rotation(A, material_force),
        )
        expected_q = q + mabd.apply_polar_increment_rotation(A, expected_dq)
        self.assertTrue(np.allclose(result.q[0], expected_q, atol=1.0e-10))
        self.assertLess(result.residual_norm, 1.0e-10)

    def test_polar_cpu_step_preserves_free_translation_under_rigid_rotation(self) -> None:
        theta = -0.37
        R = np.array(
            [
                [np.cos(theta), 0.0, np.sin(theta)],
                [0.0, 1.0, 0.0],
                [-np.sin(theta), 0.0, np.cos(theta)],
            ],
            dtype=float,
        )
        q = mabd.pack_q(R, np.array([0.2, -0.1, 0.3]))
        qd = np.zeros(12)
        qd[9:12] = np.array([1.0, 2.0, 3.0])
        dt = 0.04

        result = mabd.solve_cpu_oracle_step(
            q=[q],
            qd=[qd],
            dt=dt,
            config=mabd.MABDCPUOracleConfig(bodies=[_body(rotation_mode="polar")]),
        )

        self.assertTrue(np.allclose(result.qd[0][9:12], qd[9:12], atol=1.0e-12))
        self.assertTrue(np.allclose(result.q[0][9:12], q[9:12] + dt * qd[9:12], atol=1.0e-12))

    def test_constrained_cpu_step_rejects_polar_until_rotated_kkt_exists(self) -> None:
        config = mabd.MABDCPUOracleConfig(
            bodies=[_body(rotation_mode="polar"), _body()],
            constraints=[
                mabd.MABDCPUOracleConstraint(
                    body_a=0,
                    body_b=1,
                    spec=mabd.ball_joint(HINGE_CT, HINGE_CT),
                )
            ],
            topology="dense",
        )

        with self.assertRaisesRegex(NotImplementedError, "constrained.*rotation_mode='none'"):
            mabd.solve_cpu_oracle_step(
                q=[_identity_q((0.2, 0.0, 0.0)), _identity_q()],
                qd=[np.zeros(12), np.zeros(12)],
                dt=0.1,
                config=config,
            )
```

- [ ] **Step 2: Add vendored mirror failing tests**

Add the same tests to `vendor/newton/newton/tests/test_mabd_phase4_solver_step.py`, adapting only the existing local control-tetrahedron fixture name if needed.

- [ ] **Step 3: Run RED tests**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_mabd_phase4_solver_step
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest newton.tests.test_mabd_phase4_solver_step
```

Expected: public and vendored tests fail because `rotation_mode = polar` is rejected.

## Task 2: CPU Oracle GREEN Implementation

**Files:**
- Modify: `vendor/newton/newton/_src/solvers/mabd/step_oracle.py`

- [ ] **Step 1: Import polar rotation helpers**

Change the affine imports to include:

```python
    apply_polar_increment_rotation,
    apply_polar_rhs_rotation,
```

- [ ] **Step 2: Accept polar in config validation**

Change:

```python
if body.rotation_mode not in {"none", "no_polar"}:
    raise ValueError("rotation_mode must be one of 'none' or 'no_polar'")
```

to:

```python
if body.rotation_mode not in {"none", "polar", "no_polar"}:
    raise ValueError("rotation_mode must be one of 'none', 'polar', or 'no_polar'")
```

- [ ] **Step 3: Split step body RHS into inertial/external and material**

In `_step_body_systems`, keep `hessians` as-is but change the returned RHS blocks to:

```python
rhs.append(inv_dt * (mass @ body_qd) + force)
```

Then apply the material term in `_unconstrained_step`.

- [ ] **Step 4: Update `_unconstrained_step` branches**

For `none`, solve the old world RHS explicitly:

```python
world_rhs = f - body.precompute.stiffness_matrix @ (body_q - _body_rest_q(body))
body_dq = np.linalg.solve(H, world_rhs)
dq_blocks.append(body_dq)
residual_blocks.append(float(np.linalg.norm(H @ body_dq - world_rhs)))
```

For `polar`, use the existing full four-block helpers:

```python
A, _t = unpack_q(body_q)
local_q = apply_polar_rhs_rotation(A, body_q)
local_rhs = apply_polar_rhs_rotation(A, f) - body.precompute.stiffness_matrix @ (
    local_q - _body_rest_q(body)
)
local_delta = np.linalg.solve(H, local_rhs)
dq_blocks.append(apply_polar_increment_rotation(A, local_delta))
residual_blocks.append(float(np.linalg.norm(H @ local_delta - local_rhs)))
```

For `no_polar`, keep Phase 25 behavior by first forming the world material RHS and then applying the existing affine-only no-polar helpers:

```python
A, _t = unpack_q(body_q)
world_rhs = f - body.precompute.stiffness_matrix @ (body_q - _body_rest_q(body))
local_rhs = _affine_only_no_polar_rhs(A, world_rhs)
local_delta = np.linalg.solve(H, local_rhs)
dq_blocks.append(_affine_only_no_polar_increment(A, local_delta))
residual_blocks.append(float(np.linalg.norm(H @ local_delta - local_rhs)))
```

- [ ] **Step 5: Run GREEN CPU oracle tests**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_mabd_phase4_solver_step
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest newton.tests.test_mabd_phase4_solver_step
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check vendor/newton/newton/_src/solvers/mabd/step_oracle.py tests/test_mabd_phase4_solver_step.py vendor/newton/newton/tests/test_mabd_phase4_solver_step.py
git diff --check
```

Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add vendor/newton/newton/_src/solvers/mabd/step_oracle.py tests/test_mabd_phase4_solver_step.py vendor/newton/newton/tests/test_mabd_phase4_solver_step.py
git commit -m "feat: add polar corotated local material RHS"
```

## Task 3: Spinning-Box Report Lane

**Files:**
- Modify: `src/mabd_reproduction/single_body_reports.py`
- Modify: `tests/test_single_body_report_lane.py`
- Modify: `tests/test_spinning_box_comparison.py`

- [ ] **Step 1: Write report RED assertions**

In `test_spinning_box_report_uses_run_config`, change the report assertions to:

```python
self.assertLess(loaded.observed["relative_energy_drift"], 1.0)
self.assertGreater(loaded.observed["relative_energy_drift"], 0.1)
self.assertLess(loaded.observed["final_affine_orthogonality_error"], 10.0)
self.assertGreater(loaded.observed["final_affine_orthogonality_error"], 1.0)
self.assertEqual(loaded.observed["mabd_rotation_mode"], "polar")
self.assertEqual(
    loaded.observed["material_model"],
    "paper_linear_elastic_corotated_development",
)
self.assertEqual(
    loaded.observed["material_rhs_frame"],
    "corotated_local_all_blocks",
)
self.assertEqual(loaded.observed["translation_frame"], "corotated_polar_all_blocks")
```

Keep assertions that status is `incomplete`, linear momentum is under threshold, and angular momentum remains above the strict threshold unless implementation evidence justifies a stricter bound.

- [ ] **Step 2: Run RED report tests**

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_single_body_report_lane tests.test_spinning_box_comparison
```

Expected: fails because report still says no-polar/no-polar material and lacks the two new metadata fields.

- [ ] **Step 3: Update `_oracle_body`**

In `src/mabd_reproduction/single_body_reports.py`, change configured `rotation_mode` from `"no_polar"` to `"polar"`.

- [ ] **Step 4: Update observed report fields**

Change:

```python
"material_model": "paper_linear_elastic_no_polar_development",
```

to:

```python
"material_model": "paper_linear_elastic_corotated_development",
"material_rhs_frame": "corotated_local_all_blocks",
"translation_frame": "corotated_polar_all_blocks",
```

- [ ] **Step 5: Run report GREEN tests**

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_single_body_report_lane tests.test_spinning_box_comparison tests.test_experiment_runner
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check src/mabd_reproduction/single_body_reports.py tests/test_single_body_report_lane.py tests/test_spinning_box_comparison.py
git diff --check
```

Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add src/mabd_reproduction/single_body_reports.py tests/test_single_body_report_lane.py tests/test_spinning_box_comparison.py
git commit -m "feat: report polar corotated spinning box lane"
```

## Task 4: Phase 26 Docs And Gates

**Files:**
- Modify: `docs/reference/claim-boundaries.md`
- Create: `docs/records/2026-05-17-phase26-corotated-material-rhs.md`
- Modify: `scripts/validate_docs.py`
- Modify: `tests/test_phase0_bootstrap.py`

- [ ] **Step 1: Write docs RED tests**

Add a bootstrap test requiring:

- `This repository contains Phase 26 co-rotated material RHS evidence`
- `Phase 26 verifies unconstrained CPU oracle rotation_mode = polar`
- `material_rhs_frame = corotated_local_all_blocks`
- `translation_frame = corotated_polar_all_blocks`
- `report status: incomplete`
- `No experiment.* claim is passed in this phase`

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_phase0_bootstrap
```

Expected: fails because Phase 26 boundary and record do not exist.

- [ ] **Step 2: Extend docs validator**

Add the Phase 26 record path to `REQUIRED_FILES`, extend `validate_claim_boundaries()`, add `validate_phase26_record()`, call it from `main()`, and update the success string to end at Phase 26. Require:

- worktree, branch, base commit, spec/plan commit, implementation commit, docs/record commit, review disposition commit
- vendored Newton upstream commit and local patch summary
- paper SHA256/source lines
- environment path, readiness `smoke_passed`, and non-pollution fields
- config path, observed metrics, thresholds, and generated report policy
- `material_rhs_frame = corotated_local_all_blocks`
- `translation_frame = corotated_polar_all_blocks`
- no passed `experiment.*` claim
- `paper-claims.yaml` experiment claims remain unpassed
- spinning-box matrix remains blocked by incomplete baseline/comparison reports

Reject overclaims:

```python
"Phase 26 verifies the paper spinning-box experiment",
"Phase 26 passes experiment.single_body.spinning_box",
"Phase 26 verifies paper-faithful implicit RBD baseline",
"Phase 26 verifies paper-faithful affine collision",
"Phase 26 verifies collision detection",
"Phase 26 verifies implicit contact solve",
"Phase 26 verifies paper timing",
"Phase 26 verifies paper trajectory agreement",
```

- [ ] **Step 3: Update claim boundaries**

Append Phase 26 bullets after Phase 25. Keep non-claims at least as broad as Phase 25 and explicitly exclude unconfigured production `SolverMABD.step()`, Warp/CUDA/GPU paths, and paper performance claims.

- [ ] **Step 4: Add Phase 26 record**

Create `docs/records/2026-05-17-phase26-corotated-material-rhs.md` with:

- status: `passed` for Phase 26's bounded evidence only
- repo branch/worktree/base commit
- implementation commit placeholders to backfill after commits
- vendored Newton upstream commit
- local patch status
- paper source checksums and cited lines
- environment command and `smoke_passed`
- exact observed metrics and thresholds from generated report
- generated reports are not committed
- TDD RED/GREEN evidence
- explicit claim impact: no `experiment.*` claim passed

- [ ] **Step 5: Run docs GREEN tests**

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_phase0_bootstrap
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
git diff --check
```

Expected: docs tests and validator pass through Phase 26.

- [ ] **Step 6: Commit**

```bash
git add docs/reference/claim-boundaries.md docs/records/2026-05-17-phase26-corotated-material-rhs.md scripts/validate_docs.py tests/test_phase0_bootstrap.py
git commit -m "docs: record Phase 26 corotated material RHS"
```

## Task 5: Review, Verification, Merge

**Files:**
- Modify after review if needed.

- [ ] **Step 1: Backfill record commits**

Backfill Phase 26 implementation and docs commit hashes in the record. Reject stale placeholders in validator/tests.

- [ ] **Step 2: Run full verification in worktree**

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest newton.tests.test_mabd_phase4_solver_step
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/env/readiness_check.py
git diff --check
```

- [ ] **Step 3: Merge to main and repeat verification**

Use fast-forward merge only, repeat the same gates on main, then push `origin main`.

- [ ] **Step 4: Clean up**

Remove the Phase 26 worktree and delete the local branch only after push.

## Self-Review

- Spec coverage: The plan covers polar CPU oracle semantics, report fields, docs boundaries, provenance, review, verification, merge, and cleanup.
- Placeholder scan: The only placeholders are explicitly scoped to record commit hashes and are backfilled before merge.
- Type consistency: The plan uses existing `MABDCPUOracleBody`, `rotation_mode`, `ClaimReport.observed`, and `EvidenceStatus.INCOMPLETE` conventions.
