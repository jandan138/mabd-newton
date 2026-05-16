# Claim Boundaries

## Current

- This repository contains a reviewed Newton-first design for reproducing
  "M-ABD: Scalable, Efficient, and Robust Multi-Affine-Body Dynamics".
- This repository contains Phase 0 provenance, manifests, validation scripts,
  and bootstrap tests after the Phase 0 record is created.
- This repository contains Phase 1 single-body M-ABD CPU oracle tests and a
  `newton.solvers.SolverMABD` shell after the Phase 1 record is created.
- This repository contains Phase 2 control-point joint and dense KKT CPU oracle
  tests after the Phase 2 record is created.
- This repository contains Phase 3 topology solver CPU oracle tests after the
  Phase 3 record is created.

## Intended

- Vendor Newton and implement a paper-faithful `newton.solvers.SolverMABD`.
- Reproduce the paper method with affine state, equality joint constraints,
  topology solvers, contact/reporting lanes, and dense oracles.
- Reproduce paper evidence through configs, asset manifests, metrics, reports,
  and baseline lanes where required.

## Verified

- No method-level M-ABD result is verified at Phase 0.
- No experiment, timing, or comparative baseline result is verified at Phase 0.
- Phase 1 verifies single-body affine kinematics, dense generalized mass and
  Hessian helpers, volume-weighted `bar J` force mapping, polar/no-polar block
  maps, twist/wrench maps, and Hessian cache invalidation through unit tests
  only.
- Phase 1 does not verify time stepping, joints, contact, topology solvers,
  full FEM rest-stiffness precomputation, paper experiments, timing, or
  comparative baselines.
- Phase 2 verifies control tetrahedron `q <-> y` maps, minimal-rank ball,
  hinge, universal, and prismatic joint residuals, finite-difference joint
  gradient oracle checks, `mabd:constraint` custom storage, and dense primal vs
  dual KKT agreement including the residual-corrected lower RHS.
- Phase 2 does not verify `SolverMABD.step()`, chain/tree/loop/graph topology
  solvers, contact, joint limits, actuation, paper experiments, timing,
  comparative baselines, or the lightweight skew-symmetrized joint-gradient
  performance path.
- Phase 3 verifies chain block-tridiagonal dual solve, tree parent/postorder
  traversal metadata with dense-dual equivalence, loop Schur complement,
  inferred explicit-schedule graph Gauss-Seidel reconstruction, deterministic
  graph classification, and Newton custom-constraint graph reconstruction
  through CPU oracle tests against dense dual solves.
- Phase 3 does not verify `SolverMABD.step()`, paper ABD-ABA performance,
  paper tree elimination, paper graph Gauss-Seidel schedule identity, contact,
  joint limits, actuation, paper experiments, timing, or comparative baselines.

## Forbidden Claims

- Unmodified Newton already supports M-ABD.
- Existing Newton rigid-body solvers are equivalent to the M-ABD method.
- A rigid `body_q` proxy is paper-faithful affine collision.
- The project implements generic inequality-constrained M-ABD KKT.
- Comparative baselines are reproduced before their adapters, configs, raw logs,
  and reports exist.
- CPU timings are paper-comparable without matching benchmark protocol and
  recorded hardware/threading conditions.

## Evidence Record Requirements

Each verified claim needs a dated record with the command, config path, repo
commit, vendored Newton source commit, paper source version, environment,
backend, seed, metrics, thresholds, raw artifacts, and status.
