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
- This repository contains Phase 4 configured CPU `SolverMABD.step()` oracle
  tests after the Phase 4 record is created.
- This repository contains Phase 5 rest generalized stiffness and co-rotated
  single-body material oracle tests after the Phase 5 record is created.
- This repository contains Phase 6 machine-checkable experiment and asset
  matrices after the Phase 6 record is created.
- This repository contains Phase 7 joint-limit clamp and explicit dual RHS CPU
  oracle tests after the Phase 7 record is created.
- This repository contains Phase 8 cloned-environment readiness checks after
  the Phase 8 record is created.
- This repository contains Phase 9 point-load and point-plane penalty contact
  force-mapping CPU oracle tests after the Phase 9 record is created.
- This repository contains Phase 10 affine actuation/control force CPU oracle
  tests and `mabd:control` storage after the Phase 10 record is created.
- This repository contains Phase 11 `mabd:control` model-row extraction tests
  after the Phase 11 record is created.
- This repository contains Phase 12 full-schema claim report JSON validation
  and a single-body spinning-box M-ABD development report lane after the Phase
  12 record is created.
- This repository contains Phase 13 config-driven single-body spinning-box
  per-scene config validation and M-ABD development report generation after the
  Phase 13 record is created.

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
- Phase 4 verifies explicitly configured CPU oracle `SolverMABD.step()` state
  I/O, one small-system implicit-Euler/Newton affine update, dense dual KKT with
  residual-corrected lower RHS, rest-stiffness RHS sign, and guarded
  two-body/in-place state writes through unit tests.
- Phase 4 does not verify unconfigured production `SolverMABD.step()`, contact,
  collision, joint limits, actuation, robot controls, Warp kernels, GPU paths,
  multi-step paper scenes, convergence/timing claims, paper ABD-ABA performance,
  paper graph schedules, external baselines, or comparative reports.
- Phase 5 verifies linear-elastic rest generalized stiffness `K_A_bar`,
  finite-difference energy curvature agreement, co-rotated affine elastic force
  vanishing on pure rotations, block-rotated generalized stiffness, and
  `SingleBodyABDPrecompute.from_linear_elastic_points(...)` wiring through CPU
  oracle tests.
- Phase 5 does not verify unconfigured production `SolverMABD.step()`, contact,
  collision, joint limits, actuation, robot controls, Warp kernels, GPU paths,
  multi-step paper scenes, convergence/timing claims, paper ABD-ABA performance,
  external baselines, or comparative reports.
- Phase 6 verifies only that every `experiment.*` paper claim has a
  machine-checkable experiment matrix entry, required lane list, asset source
  reference, metric list, blocking reason, and output report contract.
- Phase 6 does not verify any scene dynamics, rendered image/video result,
  contact behavior, actuation behavior, external baseline run, timing number,
  paper visual match, or comparative report.
- Phase 7 verifies scalar joint-limit strain clamping, nearest-range
  `theta_hat` selection, explicit `k(theta - theta_hat)` dual RHS composition,
  and dense KKT lower-RHS effect through CPU oracle tests.
- Phase 7 does not verify generic inequality-constrained M-ABD KKT, contact,
  collision, production stepping, joint-limit parameter extraction from scenes,
  actuation, paper experiments, timing, or comparative baselines.
- Phase 8 verifies the cloned M-ABD Newton environment contract, interpreter
  isolation from the reference `physics-primitive-agent` environment and
  ambient DSW Python, vendored Newton import resolution, required runtime
  package imports, and readiness JSON writing through diagnostic tests.
- Phase 8 does not verify solver behavior, method correctness, scene dynamics,
  rendered output, timing, comparative baselines, dependency freshness, or
  paper experiments.
- Phase 9 verifies point-load affine generalized force mapping via `J^T f`,
  simple frictionless point-plane normal penalty force mapping, inward-only
  contact damping, and use of the resulting generalized force through the
  configured CPU oracle external-force path.
- Phase 9 does not verify collision detection, broadphase, narrowphase,
  friction, full contact handling, general inequality constraints, production
  `SolverMABD.step()` contact input, actuation/controller behavior, paper
  scenes, timing, or comparative baselines.
- Phase 10 verifies scene-script affine target, damping, and feedforward
  control-force assembly into M-ABD generalized forces, summation with existing
  external forces in the configured CPU oracle path, validation of bad control
  specs, and Newton `mabd:control` custom storage rows.
- Phase 10 does not verify Newton `Control` object ingestion, robot inverse
  kinematics, Franka pick-and-place, contact-rich grasping, wind/aerodynamic
  scene dynamics, closed-loop controllers, GPU/Warp control kernels, timing,
  paper scenes, or comparative baselines.
- Phase 11 verifies extraction of enabled Newton `mabd:control` model rows into
  `MABDActuationSpec` values, disabled-row filtering, bad body-reference
  validation, and use of extracted specs in the configured CPU oracle actuation
  path.
- Phase 11 does not verify Newton `Control` object ingestion, time-varying
  controller updates, robot inverse kinematics, Franka pick-and-place,
  contact-rich grasping, paper scenes, timing, or comparative baselines.
- Phase 12 verifies full-schema `ClaimReport` JSON round trips, required-key
  validation, invalid-status rejection, and a deterministic single-body
  spinning-box M-ABD development report that remains `incomplete`.
- Phase 12 does not verify the paper spinning-box experiment, paper timing,
  RK4/RBD/analytic baselines, rendered output, paper trajectory agreement, or
  any passed `experiment.*` claim.
- Phase 13 verifies a config-driven single-body spinning-box M-ABD development
  lane, per-scene config schema validation, experiment-matrix alignment, and
  config-backed report generation. The report remains `incomplete`.
- Phase 13 does not verify the paper spinning-box experiment, RBD baselines,
  paper timing, rendered output, paper trajectory agreement, or any passed
  `experiment.*` claim.

## Forbidden Claims

- Unmodified Newton already supports M-ABD.
- Existing Newton rigid-body solvers are equivalent to the M-ABD method.
- A rigid `body_q` proxy is paper-faithful affine collision.
- The project implements generic inequality-constrained M-ABD KKT.
- Scene-script affine control force assembly is a full robot-control or
  closed-loop actuation reproduction.
- Comparative baselines are reproduced before their adapters, configs, raw logs,
  and reports exist.
- CPU timings are paper-comparable without matching benchmark protocol and
  recorded hardware/threading conditions.

## Evidence Record Requirements

Each verified claim needs a dated record with the command, config path, repo
commit, vendored Newton source commit, paper source version, environment,
backend, seed, metrics, thresholds, raw artifacts, and status.
