# Phase 63 Point-Plane Normal Constraints Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a Newton-only scalar point-plane normal constraint row and a bounded spinning-box diagnostic report lane that remains explicitly non-passing.

**Architecture:** Extend the vendored Newton M-ABD CPU oracle with `MABDCPUOraclePlaneConstraint` rows that are normalized, residual-corrected, rank-filtered, and accepted only in dense topology. Add a separate spinning-box report lane that free-predicts each step, reruns with active rank-filtered plane rows only when needed, records diagnostics, and preserves all claim boundaries.

**Tech Stack:** Python 3.10, NumPy, vendored Newton `newton.solvers.mabd`, `unittest`, repo reporting/config helpers, `scripts/validate_docs.py`.

**Claim Impact:** No `experiment.*` claim is passed.

---

## File Structure

- Modify `vendor/newton/newton/_src/solvers/mabd/step_oracle.py` for the new dataclass, config field, normalized plane-row assembly, rank filtering, and result diagnostics.
- Modify `vendor/newton/newton/_src/solvers/mabd/__init__.py` to export `MABDCPUOraclePlaneConstraint`.
- Modify `tests/test_mabd_phase4_solver_step.py` and `vendor/newton/newton/tests/test_mabd_phase4_solver_step.py` with mirrored TDD coverage for the oracle row.
- Modify `src/mabd_reproduction/experiment_configs.py` and `configs/experiments/single_body_spinning_box.yaml` for `normal_constraint_output_report`.
- Modify `src/mabd_reproduction/single_body_reports.py` for the active-set diagnostic and report writer.
- Modify `src/mabd_reproduction/experiment_runner.py` and `scripts/run_experiment.py` for the new lane.
- Modify `tests/test_experiment_run_configs.py`, `tests/test_single_body_report_lane.py`, and `tests/test_experiment_runner.py` for config/report/runner/CLI coverage.
- Create `reports/experiment_matrix/single_body_spinning_box_normal_constraint.json`.
- Modify `docs/reference/claim-boundaries.md`, `scripts/validate_docs.py`, and `tests/test_phase0_bootstrap.py` for Phase 63 provenance gates.
- Create `docs/records/2026-05-19-phase63-point-plane-normal-constraints.md`.

## Task 1: Newton Plane Constraint Oracle

- [ ] **Step 1: Write failing mirrored solver tests**

Add tests to both `tests/test_mabd_phase4_solver_step.py` and `vendor/newton/newton/tests/test_mabd_phase4_solver_step.py`:

```python
def test_dense_cpu_step_plane_constraint_preserves_tangent_motion(self) -> None:
    q = _identity_q((0.2, -0.3, 0.1))
    qd = np.zeros(12)
    qd[9:12] = np.array([2.0, 3.0, -1.0])
    dt = 0.05
    rest_point = np.array([0.3, -0.2, 0.1])
    normal = np.array([0.0, 2.0, 2.0])
    normal_norm = float(np.linalg.norm(normal))
    free = mabd.solve_cpu_oracle_step(
        q=[q],
        qd=[qd],
        dt=dt,
        config=mabd.MABDCPUOracleConfig(bodies=[_body()]),
    )
    J = mabd.point_jacobian(rest_point)
    free_point = J @ free.q[0]
    offset = float(normal @ free_point + 0.1 * normal_norm)

    result = mabd.solve_cpu_oracle_step(
        q=[q],
        qd=[qd],
        dt=dt,
        config=mabd.MABDCPUOracleConfig(
            bodies=[_body()],
            plane_constraints=[
                mabd.MABDCPUOraclePlaneConstraint(
                    body=0,
                    rest_point=rest_point,
                    plane_normal=normal,
                    plane_offset=offset,
                )
            ],
            topology="dense",
        ),
    )

    unit_normal = normal / normal_norm
    constrained_point = J @ result.q[0]
    np.testing.assert_allclose(unit_normal @ constrained_point, offset / normal_norm, atol=1.0e-10)
    free_tangent = free_point - unit_normal * float(unit_normal @ free_point)
    constrained_tangent = constrained_point - unit_normal * float(unit_normal @ constrained_point)
    np.testing.assert_allclose(constrained_tangent, free_tangent, atol=1.0e-10)
    self.assertEqual(result.dlambda.shape, (1,))
    self.assertEqual(result.plane_constraint_requested_count, 1)
    self.assertEqual(result.plane_constraint_accepted_count, 1)
    self.assertEqual(result.plane_constraint_skipped_count, 0)
```

Also add tests for polar mode, inactive rows, invalid body/normal/vector shapes, and four dependent coplanar rows producing `accepted_count == 3`, `skipped_count == 1`, and finite output.

- [ ] **Step 2: Verify RED**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_mabd_phase4_solver_step
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest newton.tests.test_mabd_phase4_solver_step
```

Expected: fail because `MABDCPUOraclePlaneConstraint` and `plane_constraints` do not exist.

- [ ] **Step 3: Implement Newton oracle support**

Implement the dataclass, config field, normalization, `_plane_constraint_blocks`, rank-filtered dense row assembly, topology guard, `constraint_residual_norm` inclusion, and result counters. Export the class in `vendor/newton/newton/_src/solvers/mabd/__init__.py`.

- [ ] **Step 4: Verify GREEN**

Run both mirrored solver test commands again. Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add vendor/newton/newton/_src/solvers/mabd/step_oracle.py vendor/newton/newton/_src/solvers/mabd/__init__.py tests/test_mabd_phase4_solver_step.py vendor/newton/newton/tests/test_mabd_phase4_solver_step.py
git commit -m "feat: add MABD point-plane normal constraints"
```

## Task 2: Spinning-Box Normal Constraint Lane

- [ ] **Step 1: Write failing config/report/runner tests**

Add config tests for `normal_constraint_output_report`. Add report tests that assert solver mode, status, no lane gate, finite top-level/per-step fields, rank-filter policy, blocker list, and no global monotonic assertion. Add control-flow tests using a patched `mabd.solve_cpu_oracle_step`: nonpenetrating free prediction makes one solve call; penetrating free prediction makes two calls and the second config contains `MABDCPUOraclePlaneConstraint` rows.

- [ ] **Step 2: Verify RED**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_run_configs tests.test_single_body_report_lane tests.test_experiment_runner
```

Expected: fail because the config field, writer, runner, and CLI lane do not exist.

- [ ] **Step 3: Implement config, writer, runner, and CLI**

Add `normal_constraint_output_report`, `write_spinning_box_normal_constraint_report`, `run_spinning_box_normal_constraint`, and the `spinning_box_normal_constraint` CLI lane. The writer must run the paper-horizon grid, record free/constrained penetration and rank-filter counts, and keep `EvidenceStatus.INCOMPLETE`.

- [ ] **Step 4: Verify GREEN**

Run the same config/report/runner tests. Expected: pass.

- [ ] **Step 5: Generate committed report**

Use the current implementation commit SHA as `source_commit`:

```bash
SOURCE_COMMIT=$(git rev-parse HEAD)
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/run_experiment.py --lane spinning_box_normal_constraint --config configs/experiments/single_body_spinning_box.yaml --matrix configs/experiments/paper_experiment_matrix.yaml --output reports/experiment_matrix/single_body_spinning_box_normal_constraint.json --source-commit "$SOURCE_COMMIT" --vendored-newton-commit 96713fa965463b69c229a4d30582c733ff3526bb
```

- [ ] **Step 6: Commit**

```bash
git add src/mabd_reproduction/experiment_configs.py src/mabd_reproduction/single_body_reports.py src/mabd_reproduction/experiment_runner.py scripts/run_experiment.py configs/experiments/single_body_spinning_box.yaml tests/test_experiment_run_configs.py tests/test_single_body_report_lane.py tests/test_experiment_runner.py reports/experiment_matrix/single_body_spinning_box_normal_constraint.json
git commit -m "feat: add spinning-box normal constraint diagnostic"
```

## Task 3: Provenance, Validator, And Final Gates

- [ ] **Step 1: Write failing docs/provenance tests**

Update `tests/test_phase0_bootstrap.py` to require Phase 63 claim-boundary bullets, record text, validator rejection of invalid report status or inconsistent maxima, and unchanged `paper-claims.yaml` experiment statuses.

- [ ] **Step 2: Verify RED**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_phase0_bootstrap
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
```

Expected: fail because Phase 63 record, claim boundaries, and validator checks do not exist.

- [ ] **Step 3: Implement validator and docs**

Add Phase 63 required docs lists, report exclusion/evidence handling, `validate_phase63_record`, claim-boundary bullets, and `docs/records/2026-05-19-phase63-point-plane-normal-constraints.md` with the generated report sha256.

- [ ] **Step 4: Verify docs GREEN**

Run the same docs/provenance tests. Expected: pass.

- [ ] **Step 5: Run final verification**

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/env/readiness_check.py
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"
git diff --check
```

- [ ] **Step 6: Commit docs/provenance**

```bash
git add docs/reference/claim-boundaries.md scripts/validate_docs.py tests/test_phase0_bootstrap.py docs/records/2026-05-19-phase63-point-plane-normal-constraints.md docs/superpowers/plans/2026-05-19-mabd-phase63-point-plane-normal-constraints.md
git commit -m "docs: record Phase63 normal constraint diagnostics"
```

## Self-Review

- Spec coverage: covers Newton oracle row, rank filtering, report lane, config/runner/CLI, tests, validator, records, and claim boundaries.
- Placeholder scan: no placeholder source commit may remain in committed reports or records.
- Type consistency: use `MABDCPUOraclePlaneConstraint`, `plane_constraints`, `normal_constraint_output_report`, `write_spinning_box_normal_constraint_report`, `run_spinning_box_normal_constraint`, and CLI lane `spinning_box_normal_constraint` consistently.
