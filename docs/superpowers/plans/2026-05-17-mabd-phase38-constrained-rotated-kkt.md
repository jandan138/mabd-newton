# Phase 38 Constrained Rotated KKT Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add bounded CPU-oracle support for constrained M-ABD KKT solves with `rotation_mode = polar`, while keeping constrained `no_polar` explicitly unsupported.

**Architecture:** Assemble dense constrained KKT systems in per-body solve coordinates. Body Hessians and RHS vectors stay in local solve frames; constraint gradients are transformed as `J_world @ increment_map`; solved local increments are mapped back to world affine increments before state updates. Rotated non-dense topology paths stay unsupported until they have independent tests.

**Tech Stack:** Python 3.10, NumPy, vendored Newton M-ABD CPU oracle, YAML config parsing, `unittest`, canonical `mabd-newton-py310` environment.

---

## File Map

- Modify `vendor/newton/newton/_src/solvers/mabd/step_oracle.py`: add dense per-body polar local-frame KKT assembly and replace the broad constrained-rotation rejection with no-polar and non-dense topology-specific rejections.
- Modify `tests/test_mabd_phase4_solver_step.py`: replace rejection tests with behavioral red/green tests.
- Modify `vendor/newton/newton/tests/test_mabd_phase4_solver_step.py`: keep vendored Newton tests in sync for provenance.
- Modify `configs/experiments/single_body_physical_pendulum.yaml`: add `mabd_newton.rotation_mode: polar`.
- Modify `src/mabd_reproduction/experiment_configs.py`: parse and validate the new rotation mode field.
- Modify `src/mabd_reproduction/physical_pendulum_mabd.py`: allow the formal lane to pass `rotation_mode=polar`.
- Modify `src/mabd_reproduction/physical_pendulum_reports.py`: record `mabd_rotation_mode` in the formal report.
- Modify `tests/test_physical_pendulum_mabd.py`, `tests/test_experiment_run_configs.py`, `tests/test_experiment_runner.py`, and `tests/test_phase0_bootstrap.py`: cover the new report/config evidence.
- Modify `docs/reference/claim-boundaries.md`, `scripts/validate_docs.py`, and add a Phase 38 record after implementation evidence exists. Do not modify `docs/reference/paper-claims.yaml`; Phase 38 does not change any paper-claim status.

## Task 1: Solver Red Tests

- [ ] **Step 1: Replace the polar rejection test**

In `tests/test_mabd_phase4_solver_step.py`, replace
`test_constrained_cpu_step_rejects_polar_until_rotated_kkt_exists` with:

```python
def test_constrained_cpu_step_supports_polar_world_anchor(self) -> None:
    theta = 0.31
    R = np.array(
        [
            [np.cos(theta), -np.sin(theta), 0.0],
            [np.sin(theta), np.cos(theta), 0.0],
            [0.0, 0.0, 1.0],
        ],
        dtype=float,
    )
    q = mabd.pack_q(R, np.array([0.2, -0.1, 0.05]))
    rest_point = np.array([0.4, -0.2, 0.1], dtype=float)
    world_point = mabd.point_jacobian(rest_point) @ q
    world_point += np.array([0.03, -0.02, 0.01], dtype=float)

    result = mabd.solve_cpu_oracle_step(
        q=[q],
        qd=[np.zeros(12)],
        dt=0.05,
        config=mabd.MABDCPUOracleConfig(
            bodies=[_body(rotation_mode="polar")],
            world_constraints=[
                mabd.MABDCPUOracleWorldConstraint(
                    body=0,
                    rest_point=rest_point,
                    world_point=world_point,
                )
            ],
            topology="dense",
        ),
    )

    pinned = mabd.point_jacobian(rest_point) @ result.q[0]
    self.assertLess(result.constraint_residual_norm, 1.0e-10)
    self.assertTrue(np.allclose(pinned, world_point, atol=1.0e-10))
    self.assertEqual(result.topology, "dense")
```

- [ ] **Step 2: Keep constrained no-polar rejection explicit**

In `tests/test_mabd_phase4_solver_step.py`, replace
`test_constrained_cpu_step_rejects_no_polar_until_rotated_kkt_exists` with:

```python
def test_constrained_cpu_step_rejects_no_polar_because_map_is_nonlinear(self) -> None:
    stretch_shear = np.array(
        [
            [1.05, 0.08, 0.0],
            [0.0, 0.97, 0.03],
            [0.0, 0.0, 1.02],
        ],
        dtype=float,
    )
    config = mabd.MABDCPUOracleConfig(
        bodies=[_body(rotation_mode="no_polar"), _body(rotation_mode="polar")],
        constraints=[
            mabd.MABDCPUOracleConstraint(
                body_a=0,
                body_b=1,
                spec=mabd.ball_joint(HINGE_CT, HINGE_CT),
            )
        ],
        topology="dense",
    )

    with self.assertRaisesRegex(NotImplementedError, "constrained.*no_polar"):
        mabd.solve_cpu_oracle_step(
            q=[mabd.pack_q(stretch_shear, np.array([0.2, 0.0, 0.0])), _identity_q()],
            qd=[np.zeros(12), np.zeros(12)],
            dt=0.1,
            config=config,
        )
```

- [ ] **Step 3: Add non-dense rotated topology rejection**

Add this test to both `tests/test_mabd_phase4_solver_step.py` and
`vendor/newton/newton/tests/test_mabd_phase4_solver_step.py`:

```python
def test_constrained_cpu_step_rejects_polar_non_dense_topology_until_tested(self) -> None:
    config = mabd.MABDCPUOracleConfig(
        bodies=[_body(rotation_mode="polar"), _body()],
        constraints=[
            mabd.MABDCPUOracleConstraint(
                body_a=0,
                body_b=1,
                spec=mabd.ball_joint(HINGE_CT, HINGE_CT),
            )
        ],
        topology="chain",
    )

    with self.assertRaisesRegex(NotImplementedError, "rotated.*topology='dense'"):
        mabd.solve_cpu_oracle_step(
            q=[_identity_q((0.2, 0.0, 0.0)), _identity_q()],
            qd=[np.zeros(12), np.zeros(12)],
            dt=0.1,
            config=config,
        )
```

- [ ] **Step 4: Mirror the tests in vendored Newton**

Apply the same two test replacements in
`vendor/newton/newton/tests/test_mabd_phase4_solver_step.py`.

- [ ] **Step 5: Run RED**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_mabd_phase4_solver_step
```

Expected before implementation: failure because constrained dense polar still raises `NotImplementedError`; constrained no-polar should keep raising; polar non-dense should raise with the old broad message instead of the new topology-specific message.

## Task 2: Local-Frame KKT Implementation

- [ ] **Step 1: Add increment-map helpers**

In `vendor/newton/newton/_src/solvers/mabd/step_oracle.py`, add helpers near `_world_material_rhs`:

```python
def _polar_increment_map(A: np.ndarray) -> np.ndarray:
    return np.kron(np.eye(4), polar_rotation(A))


def _body_solve_system(
    body_q: np.ndarray,
    inertial_external_rhs: np.ndarray,
    body: MABDCPUOracleBody,
) -> tuple[np.ndarray, np.ndarray]:
    if body.rotation_mode == "none":
        return _world_material_rhs(body_q, inertial_external_rhs, body), np.eye(12)

    A, _t = unpack_q(body_q)
    if body.rotation_mode == "polar":
        local_q = apply_polar_rhs_rotation(A, body_q)
        local_rhs = apply_polar_rhs_rotation(A, inertial_external_rhs) - body.precompute.stiffness_matrix @ (
            local_q - _body_rest_q(body)
        )
        increment_map = _polar_increment_map(A)
        return local_rhs, increment_map

    if body.rotation_mode == "no_polar":
        raise NotImplementedError(
            "constrained CPU oracle no_polar KKT is unsupported because the current "
            "no-polar normalization increment is nonlinear"
        )

    raise ValueError("rotation_mode must be one of 'none', 'polar', or 'no_polar'")
```

- [ ] **Step 2: Thread increment maps through dense assembly**

Change `_assemble_dense_dual_inputs_with_world_constraints(...)` to accept
`increment_maps: tuple[np.ndarray, ...]`. When writing each constraint gradient
block, multiply the world gradient by that body's increment map:

```python
row[:, dim * body_a : dim * body_a + dim] = grad_a @ increment_maps[body_a]
row[:, dim * body_b : dim * body_b + dim] = grad_b @ increment_maps[body_b]
...
row[:, dim * body : dim * body + dim] = gradient @ increment_maps[body]
```

- [ ] **Step 3: Reject rotated non-dense topology paths**

In `_solve_constrained_step`, after resolving `topology`, reject rotated
non-dense paths before calling topology solvers:

```python
has_rotated_body = any(not np.allclose(increment_map, np.eye(12)) for increment_map in increment_maps)
if has_rotated_body and topology != "dense":
    raise NotImplementedError("constrained rotated CPU oracle steps require topology='dense'")
```

Do not thread polar gradients into chain/tree/loop/graph solvers in Phase 38;
that needs separate topology evidence.

- [ ] **Step 4: Replace the broad constrained rotation rejection**

In `solve_cpu_oracle_step`, replace:

```python
_require_constrained_none_rotation(bodies)
world_rhs = tuple(
    _world_material_rhs(body_q, body_rhs, body)
    for body_q, body_rhs, body in zip(q_blocks, rhs, bodies, strict=True)
)
return _solve_constrained_step(q_blocks, dt_float, hessians, world_rhs, config)
```

with:

```python
body_systems = tuple(
    _body_solve_system(body_q, body_rhs, body)
    for body_q, body_rhs, body in zip(q_blocks, rhs, bodies, strict=True)
)
local_rhs = tuple(system[0] for system in body_systems)
increment_maps = tuple(system[1] for system in body_systems)
return _solve_constrained_step(
    q_blocks,
    dt_float,
    hessians,
    local_rhs,
    increment_maps,
    config,
)
```

Leave `_require_constrained_none_rotation` deleted or unused only if no caller
still references it; do not keep dead rejection code.

- [ ] **Step 5: Map solved local increments back to world increments**

Change `_solve_constrained_step` to accept `increment_maps`. After `dq` is
solved in local coordinates, compute:

```python
local_dq_blocks = tuple(dq[12 * body_id : 12 * body_id + 12] for body_id in range(len(q)))
dq_blocks = tuple(
    increment_map @ local_dq
    for increment_map, local_dq in zip(increment_maps, local_dq_blocks, strict=True)
)
world_dq = np.concatenate(dq_blocks)
q_next = tuple(body_q + body_dq for body_q, body_dq in zip(q, dq_blocks, strict=True))
qd_next = tuple(body_dq / float(dt) for body_dq in dq_blocks)
```

Return `dq=world_dq` so callers continue to see world-frame increments.

- [ ] **Step 6: Run GREEN**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_mabd_phase4_solver_step
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest newton.tests.test_mabd_phase4_solver_step
```

Expected: both pass.

- [ ] **Step 7: Commit solver work**

```bash
git add vendor/newton/newton/_src/solvers/mabd/step_oracle.py tests/test_mabd_phase4_solver_step.py vendor/newton/newton/tests/test_mabd_phase4_solver_step.py
git commit -m "Support constrained rotated MABD CPU KKT"
```

## Task 3: Physical-Pendulum Formal Lane Evidence

- [ ] **Step 1: Write config/report RED tests**

Add assertions:

```python
self.assertEqual(config.mabd_newton.rotation_mode, "polar")
```

to `tests/test_experiment_run_configs.py::ExperimentRunConfigTests.test_physical_pendulum_config_is_machine_checkable`.

Add assertions to `tests/test_physical_pendulum_mabd.py`:

```python
self.assertEqual(rollout.rotation_mode, "none")
```

and add a new report test asserting:

```python
self.assertEqual(report.observed["mabd_rotation_mode"], "polar")
```

- [ ] **Step 2: Run RED**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_run_configs tests.test_physical_pendulum_mabd
```

Expected before implementation: config has no `rotation_mode` field and reports do not expose `mabd_rotation_mode`.

- [ ] **Step 3: Add config field**

In `configs/experiments/single_body_physical_pendulum.yaml`, add:

```yaml
mabd_newton:
  rotation_mode: polar
```

under the existing `mabd_newton` block.

In `src/mabd_reproduction/experiment_configs.py`, add `rotation_mode: str` to
`PhysicalPendulumMABDNewtonConfig`, validate it is one of `none`, `polar`, or
`no_polar`, and populate it in `_require_physical_pendulum_mabd_newton`.

- [ ] **Step 4: Add rollout field and formal-lane rotation**

In `src/mabd_reproduction/physical_pendulum_mabd.py`, add
`rotation_mode: str` to `PhysicalPendulumMABDRollout`, add a keyword parameter
`rotation_mode: str = "none"` to `roll_out_physical_pendulum_mabd_development`,
pass it to `MABDCPUOracleBody(rotation_mode=rotation_mode)`, and store it in
the returned rollout.

In `src/mabd_reproduction/physical_pendulum_reports.py`, call:

```python
rollout = roll_out_physical_pendulum_mabd_development(
    config,
    rotation_mode=config.mabd_newton.rotation_mode,
)
```

inside `write_physical_pendulum_mabd_newton_report`, and record:

```python
"mabd_rotation_mode": rollout.rotation_mode,
```

- [ ] **Step 5: Run GREEN**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_run_configs tests.test_physical_pendulum_mabd tests.test_experiment_runner
```

Expected: pass.

- [ ] **Step 6: Commit code/config/tests before report regeneration**

After code/config/report writers and focused tests pass, commit them before
regenerating committed reports:

```bash
git add vendor/newton/newton/_src/solvers/mabd/step_oracle.py tests/test_mabd_phase4_solver_step.py vendor/newton/newton/tests/test_mabd_phase4_solver_step.py configs/experiments/single_body_physical_pendulum.yaml src/mabd_reproduction/experiment_configs.py src/mabd_reproduction/physical_pendulum_mabd.py src/mabd_reproduction/physical_pendulum_reports.py tests/test_experiment_run_configs.py tests/test_physical_pendulum_mabd.py tests/test_experiment_runner.py
git commit -m "Support constrained polar MABD CPU KKT"
```

- [ ] **Step 7: Regenerate reports with real provenance**

Set:

```bash
SOURCE_COMMIT=$(git rev-parse --short HEAD)
VENDORED_NEWTON_COMMIT=96713fa965463b69c229a4d30582c733ff3526bb
```

Then run:

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/run_experiment.py --config configs/experiments/single_body_physical_pendulum.yaml --matrix configs/experiments/paper_experiment_matrix.yaml --lane physical_pendulum_mabd_newton --output reports/experiment_matrix/single_body_physical_pendulum_mabd_newton.json --source-commit "$SOURCE_COMMIT" --vendored-newton-commit "$VENDORED_NEWTON_COMMIT"
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/run_experiment.py --config configs/experiments/single_body_physical_pendulum.yaml --matrix configs/experiments/paper_experiment_matrix.yaml --lane physical_pendulum_comparison --output reports/experiment_matrix/single_body_physical_pendulum_comparison.json --analytic-report reports/experiment_matrix/single_body_physical_pendulum_analytic_reference.json --mabd-report reports/experiment_matrix/single_body_physical_pendulum_mabd_newton.json --rbd-report reports/experiment_matrix/single_body_physical_pendulum_rbd_baseline.json --source-commit "$SOURCE_COMMIT" --vendored-newton-commit "$VENDORED_NEWTON_COMMIT"
```

Expected: both reports are written and remain `incomplete`.

- [ ] **Step 8: Commit regenerated reports**

```bash
git add reports/experiment_matrix/single_body_physical_pendulum_mabd_newton.json reports/experiment_matrix/single_body_physical_pendulum_comparison.json
git commit -m "Regenerate physical pendulum constrained polar reports"
```

## Task 4: Phase 38 Docs And Gates

- [ ] **Step 1: Add Phase 38 boundary and record**

Add `docs/records/2026-05-17-phase38-constrained-rotated-kkt.md` with:

- worktree and branch;
- implementation commits;
- source lines from `solver.tex` and existing Phase 25/26 boundaries;
- RED failures;
- GREEN commands;
- readiness output;
- claim boundary stating reports remain incomplete.

Update `docs/reference/claim-boundaries.md` with Phase 38 current, verified,
and forbidden-claim bullets.

- [ ] **Step 2: Add validator coverage**

In `scripts/validate_docs.py`, add `validate_phase38_record()` and include it
in `main()`. Verify:

- Phase 38 record exists;
- claim boundary has the Phase 38 current/verified/non-claim text;
- physical-pendulum MABD report has `status = incomplete`;
- physical-pendulum MABD report has `observed.mabd_rotation_mode = polar`;
- physical-pendulum MABD report has `observed.full_experiment_claim_passed = false`;
- physical-pendulum MABD report has `expected.full_experiment_claim_passed = false`;
- physical-pendulum MABD report `blocking_reasons` still include
  `pendulum_geometry_unknown`, `joint_force_waveform_agreement_missing`, and
  `paper_timing_missing`;
- physical-pendulum comparison remains `status = incomplete`;
- physical-pendulum comparison
  `paper_metric_statuses.joint_force_error.status =
  diagnostic_reaction_not_paper_waveform`;
- `paper-claims.yaml` still has `experiment.single_body.physical_pendulum`
  as `intended`.

- [ ] **Step 3: Add bootstrap tests**

In `tests/test_phase0_bootstrap.py`, add a Phase 38 test that checks the same
record, boundary, report, and paper-claim conditions.

- [ ] **Step 4: Run docs RED then GREEN**

Before docs implementation:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
```

Expected: fails because Phase 38 docs are missing.

After docs implementation:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_phase0_bootstrap
```

Expected: both pass and validator prints Phase 0-38.

- [ ] **Step 5: Commit docs**

```bash
git add docs/reference/claim-boundaries.md docs/records/2026-05-17-phase38-constrained-rotated-kkt.md scripts/validate_docs.py tests/test_phase0_bootstrap.py
git commit -m "Record Phase 38 constrained rotated KKT"
```

## Task 5: Final Verification And Push

- [ ] **Step 1: Run final gates**

```bash
/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/env/readiness_check.py
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"
git diff --check
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
```

Expected: all pass.

- [ ] **Step 2: Merge and push**

If final gates pass:

```bash
git switch main
git merge --ff-only phase38-constrained-rotated-kkt
git push origin main
```

Expected: `main` fast-forwards and pushes to `origin/main`.
