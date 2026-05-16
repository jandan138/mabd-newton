# Phase 4: Configured CPU Solver Step Oracle

## Scope

Implement a conservative `SolverMABD.step()` bridge for configured CPU oracle
data. This phase should make `SolverMABD.step()` executable for small
test-controlled M-ABD states while keeping full paper scenes, contact, timing,
and production Warp kernels unclaimed.

## Claim Boundary

Passed evidence may cover:

- one implicit-Euler/Newton affine increment using Eq. `singleabd` inertia and
  `solver` KKT algebra
- dense dual KKT and previously verified topology solvers as CPU oracle backends
- residual-corrected lower RHS `J dq = -C(q_n)` for linearized joint correction
- reading `state_in.mabd.{q0,q1,q2,t,qd0,qd1,qd2,td}` and writing the matching
  `state_out` arrays when CPU oracle data are explicitly configured

Not passed in this phase:

- unconfigured production `SolverMABD.step()` behavior
- paper contact, collision, joint limits, actuation, robot controls, scenes,
  external baselines, timing, single-thread scaling, or Warp kernels
- paper ABD-ABA performance or paper-identical graph schedules

## RED Tests

Add project tests:

- `test_dense_cpu_step_matches_implicit_euler_single_body_force`
- `test_dense_cpu_step_enforces_ball_joint_residual_correction`
- `test_solver_step_writes_custom_state_when_cpu_oracle_configured`
- `test_solver_step_requires_cpu_oracle_configuration`

Add Newton-internal mirrors for the single-body step and configured
`SolverMABD.step()` state write.

Expected RED failures:

- missing `MABDCPUOracleBody`
- missing `MABDCPUOracleConstraint`
- missing `MABDCPUOracleConfig`
- missing `solve_cpu_oracle_step`
- `SolverMABD` has no CPU oracle configuration and still always raises
  `NotImplementedError`

## Implementation

1. Add `step_oracle.py` under `newton._src.solvers.mabd`.
2. Define frozen dataclasses for body precompute, constraints, config, and
   result diagnostics.
3. Build body Hessians as `M_A / h^2 + K_A` and RHS as
   `M_A / h^2 * (q_n + h qd_n + h^2 M_A^{-1} f_ext - q_n)
   - K_A(q_n - q_rest)`.
4. Evaluate configured joint specs at current `q_n`, split gradients into edge
   body blocks, and use lower RHS `-C(q_n)`.
5. Route to dense dual KKT by default and to Phase 3 topology solvers when
   requested.
6. Update `SolverMABD` with `configure_cpu_oracle(...)`, state pack/unpack
   helpers, `last_step_result`, and a guarded `step()` path.
7. Export new helpers in `mabd.__init__`.
8. Update docs, claim manifest, validator, and Phase 4 evidence record.

## Verification

Use the isolated environment:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_mabd_phase4_solver_step
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest vendor.newton.newton.tests.test_mabd_phase4_solver_step
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check tests/test_mabd_phase4_solver_step.py tests/test_phase0_bootstrap.py vendor/newton/newton/_src/solvers/mabd vendor/newton/newton/tests/test_mabd_phase4_solver_step.py scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
git diff --check
```
