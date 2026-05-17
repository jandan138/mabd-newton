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
- This repository contains Phase 14 executable config-driven single-body
  spinning-box development report runner after the Phase 14 record is created.
- This repository contains Phase 15 Newton `SolverSemiImplicit` CPU
  free-rigid development baseline lane for the required
  `rbd_implicit_baseline` single-body spinning-box lane and CLI dispatch after
  the Phase 15 record is created.
- This repository contains Phase 16 machine-checkable spinning-box comparison
  protocol report generation for the existing `mabd_newton` and
  `rbd_implicit_baseline` incomplete lanes after the Phase 16 record is
  created.
- This repository contains Phase 17 paper-value momentum metric reporting for
  the M-ABD single-body spinning-box development lane after the Phase 17
  record is created.
- This repository contains Phase 18 physical affine mass-diagonal reporting
  and kinetic-energy diagnostics for the M-ABD single-body spinning-box
  development lane after the Phase 18 record is created.
- This repository contains Phase 19 finite required-metric validation and
  lane metric-difference reporting for the spinning-box comparison protocol
  after the Phase 19 record is created.
- This repository contains Phase 20 contact-surface config parsing, procedural
  spinning-box cube-corner derivation, and contact diagnostic reporting for
  the M-ABD development lane after the Phase 20 record is created.
- This repository contains Phase 21 spinning-box plane-aligned initial
  placement checks and reporting after the Phase 21 record is created.
- This repository contains Phase 22 RBD development baseline configured
  initial placement checks and reporting after the Phase 22 record is created.
- This repository contains Phase 23 spinning-box position comparison metrics
  and finite vector validation for the existing development lanes after the
  Phase 23 record is created.
- This repository contains Phase 24 report-level trajectory samples for the
  M-ABD and RBD spinning-box development lanes plus affine shape diagnostics
  for the M-ABD lane after the Phase 24 record is created.

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
- Phase 14 verifies an executable config-driven experiment runner for the
  single-body spinning-box development report, including CLI output override,
  config-output-root resolution, report summary JSON, and config/matrix
  validation before writing.
- Phase 14 does not verify the paper spinning-box experiment, RBD baselines,
  paper timing, rendered output, paper trajectory agreement, generated report
  artifacts as committed evidence, or any passed `experiment.*` claim.
- Phase 15 verifies a Newton `SolverSemiImplicit` CPU free-rigid development
  baseline for the required single-body spinning-box `rbd_implicit_baseline`
  lane, including deterministic cube mass and inertia from the paper values,
  real vendored-Newton stepping, final pose/velocity capture, conservation
  diagnostics, incomplete claim report writing, and explicit CLI dispatch
  through `--lane rbd_implicit_baseline`.
- Phase 15 does not verify the paper spinning-box experiment,
  paper-faithful implicit RBD baseline, paper-faithful affine collision, RK4
  or analytic baselines, rendered output, paper trajectory agreement, paper
  timing, generated report artifacts as committed evidence, or any passed
  `experiment.*` claim.
- Phase 16 verifies a machine-checkable spinning-box comparison protocol that
  consumes the existing `mabd_newton` and `rbd_implicit_baseline` lane reports,
  validates lane identity, records lane status and missing paper comparison
  metrics, writes an incomplete `spinning_box_comparison_protocol` report, and
  exposes explicit runner and CLI dispatch.
- Phase 16 does not verify the paper spinning-box experiment,
  paper-faithful implicit RBD baseline, paper-faithful affine collision, paper
  timing, rendered output, paper trajectory agreement, generated report
  artifacts as committed evidence, or any passed `experiment.*` claim.
- Phase 17 verifies paper-value momentum metric reporting for the M-ABD
  spinning-box development lane: paper p0/L0 parsing, ABD generalized
  velocity initialization via the rigid embedding map, final spatial twist
  extraction via the paper twist map, and `linear_momentum_error` /
  `angular_momentum_error` fields consumed by the comparison protocol.
- Phase 17 does not verify the paper spinning-box experiment,
  paper-faithful implicit RBD baseline, paper-faithful affine collision, paper
  timing, rendered output, paper trajectory agreement, generated report
  artifacts as committed evidence, or any passed `experiment.*` claim.
- Phase 18 verifies physical affine mass-diagonal reporting for the M-ABD
  single-body spinning-box development lane: paper uniform centered cube mass
  derivation, Newton affine packing order, `mass_diagonal = [m*s^2/12] * 9 +
  [m] * 3`, `initial_energy_j`, `final_energy_j`, and
  `relative_energy_drift` report fields.
- Phase 18 does not verify the paper spinning-box experiment,
  paper-faithful implicit RBD baseline, paper-faithful affine collision, paper
  timing, rendered output, paper trajectory agreement, generated report
  artifacts as committed evidence, or any passed `experiment.*` claim.
- Phase 19 verifies finite required-metric validation for the spinning-box
  comparison protocol, including `invalid_required_metrics` reporting,
  finite-only `lane_metric_differences`, and invalid metric blocking reasons.
- Phase 19 does not verify the paper spinning-box experiment,
  paper-faithful implicit RBD baseline, paper-faithful affine collision, paper
  timing, rendered output, paper trajectory agreement, generated report
  artifacts as committed evidence, or any passed `experiment.*` claim.
- Phase 20 verifies procedural spinning-box cube corner derivation, configured
  frictionless plane metadata, point-plane normal penalty contact diagnostics,
  and finite contact diagnostic fields in the M-ABD development lane report.
- Phase 20 does not verify the paper spinning-box experiment, collision
  detection, continuous collision detection, friction, implicit contact solve,
  paper-faithful affine collision, paper-faithful implicit RBD baseline, paper
  timing, rendered output, paper trajectory agreement, generated report
  artifacts as committed evidence, or any passed `experiment.*` claim.
- Phase 21 verifies the configured spinning-box resting pose on the
  frictionless plane: paper cube side length 0.1m, plane normal [0, 1, 0],
  plane offset 0, initial translation y=0.05m, zero initial penetration, and
  zero point-plane penalty contact force fields in the M-ABD development lane
  report.
- Phase 21 does not verify the paper spinning-box experiment, collision
  detection, continuous collision detection, friction, implicit contact solve,
  gravity, paper-faithful affine collision, paper-faithful implicit RBD
  baseline, paper timing, rendered output, paper trajectory agreement,
  generated report artifacts as committed evidence, or any passed
  `experiment.*` claim.
- Phase 22 verifies that the Newton `rbd_implicit_baseline` RBD development
  baseline consumes the configured spinning-box initial translation:
  `initial_position_m = [0.0, 0.05, 0.0]`, `final_position_m = [4.0, 0.05,
  0.0]` after four 10 ms free-body steps at 100 m/s, and report propagation
  for the RBD lane.
- Phase 22 does not verify the paper spinning-box experiment,
  paper-faithful implicit RBD baseline, paper-faithful affine collision,
  collision detection, continuous collision detection, friction, implicit
  contact solve, gravity, rendered output, paper timing, paper trajectory
  agreement, generated report artifacts as committed evidence, or any passed
  `experiment.*` claim.
- Phase 23 verifies report-level `initial_position_m` and `final_position_m`
  propagation for the M-ABD spinning-box development lane and finite
  length-three vector validation/differencing in the comparison protocol via
  `lane_vector_metrics`, `invalid_required_vector_metrics`, and
  `lane_vector_metric_differences`.
- Phase 23 does not verify the paper spinning-box experiment,
  paper-faithful implicit RBD baseline, paper-faithful affine collision,
  collision detection, continuous collision detection, friction, implicit
  contact solve, gravity, rendered output, paper timing, paper trajectory
  agreement, generated report artifacts as committed evidence, or any passed
  `experiment.*` claim.
- Phase 24 verifies report-level `trajectory_samples` for the M-ABD and RBD
  spinning-box development lanes. M-ABD samples include affine matrix,
  determinant, singular values, and `affine_orthogonality_error`; the M-ABD
  report also exposes `affine_shape_diagnostic_status =
  development_gap_observed`. RBD `rotation_xyzw` samples are recorded.
- Phase 24 does not verify the paper spinning-box experiment,
  paper-faithful implicit RBD baseline, paper-faithful affine collision,
  collision detection, continuous collision detection, friction, implicit
  contact solve, gravity, rendered output, paper timing, paper trajectory
  agreement, generated report artifacts as committed evidence, or any passed
  `experiment.*` claim.
- This repository contains Phase 25 no-polar spinning-box material-lane
  evidence. It wires paper material stiffness into the M-ABD development report
  lane and enables unconstrained CPU oracle no-polar body steps.
- Phase 25 verifies unconstrained CPU oracle `rotation_mode = no_polar`
  routing, report fields `mabd_rotation_mode`, `material_model`,
  `material_young_modulus_pa`, `material_poisson_ratio`,
  `material_volume_m3`, `material_stiffness_trace`, and
  `material_stiffness_rank`; it also verifies constrained CPU oracle KKT still
  requires `rotation_mode = none`. Final angular momentum and energy remain a
  development gap, recorded under incomplete report status.
- Phase 25 does not verify the paper spinning-box experiment, full M-ABD
  dynamics, multi-body no-polar constraints, paper-faithful implicit RBD
  baseline, paper-faithful affine collision, collision detection, continuous
  collision detection, friction, implicit contact solve, gravity, rendered
  output, paper timing, paper trajectory agreement, generated report artifacts
  as committed evidence, or any passed `experiment.*` claim.
- This repository contains Phase 26 co-rotated material RHS evidence for the
  spinning-box M-ABD development lane. It adds unconstrained CPU oracle
  `rotation_mode = polar` and records a polar co-rotated all-block material RHS
  report lane.
- Phase 26 verifies unconstrained CPU oracle `rotation_mode = polar` routing,
  pure-rotation zero material strain, consistency with the co-rotated material
  force helper for a small deformation, constrained CPU oracle polar rejection,
  report fields `mabd_rotation_mode = polar`,
  `material_model = paper_linear_elastic_corotated_development`,
  `material_rhs_frame = corotated_local_all_blocks`, and
  `translation_frame = corotated_polar_all_blocks`. The spinning-box
  report status: `incomplete`; angular momentum, relative energy drift, and
  affine shape remain development diagnostics.
- Phase 26 does not verify the paper spinning-box experiment, full M-ABD
  dynamics, multi-body polar or no-polar constraints, unconfigured production
  `SolverMABD.step()`, Warp/CUDA/GPU paths, paper ABD-ABA performance,
  paper-faithful implicit RBD baseline, paper-faithful affine collision,
  collision detection, continuous collision detection, friction, implicit
  contact solve, gravity, rendered output, paper timing, paper trajectory
  agreement, generated report artifacts as committed evidence, or any passed
  `experiment.*` claim.
- This repository contains Phase 27 paper-scoped RBD lane gate evidence for
  the required single-body spinning-box `rbd_implicit_baseline` lane.
- Phase 27 verifies that the RBD lane top-level report remains `incomplete`
  while `lane_gate_status = passed`, `solver_mode =
  paper_faithful_implicit_rbd`, and `backend = cpu_numpy_newton_only` are
  recorded for the closed-form xyzw quaternion free-body path. It also verifies
  strict conservation thresholds and that the comparison protocol consumes the
  RBD lane gate while keeping the full comparison incomplete.
- Phase 27 does not verify the paper spinning-box experiment, M-ABD lane pass,
  spinning-box comparison pass, full M-ABD dynamics, paper-faithful affine
  collision, collision detection, continuous collision detection, friction,
  implicit contact solve, gravity, rendered output, paper timing, paper
  trajectory agreement, generated report artifacts as committed evidence, or
  any passed `experiment.*` claim.
- This repository contains Phase 28 paper-horizon M-ABD diagnostic evidence for
  the single-body spinning-box claim. It runs the Newton M-ABD CPU oracle over
  the 10 second figure horizon for `h = 1e-2` and `h = 1e-3`.
- Phase 28 verifies `mabd_cpu_oracle_paper_horizon_diagnostic` report
  generation, every-step extrema scanning, compact trajectory samples,
  kinetic/elastic/total energy separation, finite metric snapshots,
  `threshold_violations`, comparison-compatible scalar fields,
  `mabd_paper_horizon_status = development_gap_observed`, no
  `lane_gate_status`, and report status: `incomplete`.
- Phase 28 does not verify the paper spinning-box experiment, M-ABD lane pass,
  spinning-box comparison pass, full M-ABD dynamics, paper-faithful affine
  collision, collision detection, continuous collision detection, friction,
  implicit contact solve, gravity, rendered output, paper timing, paper
  trajectory agreement, generated report artifacts as committed evidence, or
  any passed `experiment.*` claim.
- This repository contains Phase 29 spinning-box kinematic feasibility
  diagnostics for the M-ABD paper-horizon report.
- Phase 29 verifies paper angular speed 60000 rad/s, orthogonal
  finite-difference bounds 100 and 1000 rad/s for `h = 0.01` and
  `h = 0.001`, momentum bounds 1/6 and 10/6 kg m^2/s, ratios 600 and 60,
  `paper_momentum_requires_affine_stretch_under_q_delta_over_h`, and
  `qd_next=(q_next-q_n)/h` reporting.
- Phase 29 does not verify the paper spinning-box experiment, M-ABD lane pass,
  spinning-box comparison pass, full M-ABD dynamics, solver fix, projection
  fix, decoupled velocity semantics, paper-faithful affine collision, contact
  solve, timing, generated report artifacts as committed evidence, or any
  passed `experiment.*` claim.
- This repository contains Phase 30 velocity semantics source audit evidence
  for the single-body spinning-box claim, with
  `source_does_not_prove_decoupled_velocity_semantics` as the audit status.
- Phase 30 verifies paper-source presence of the implicit Euler inertia
  potential, `G(A)` twist mapping, `G(A)^T` wrench mapping, and spinning-box
  twist initialization, while recording
  `source_does_not_specify_decoupled_velocity_semantics` and
  `source_does_not_specify_alternative_momentum_extraction`.
- Phase 30 does not verify the paper spinning-box experiment, any Newton solver
  modification, decoupled velocity semantics, alternative momentum extraction,
  M-ABD lane pass, spinning-box comparison pass, paper timing, paper trajectory
  agreement, generated report artifacts as committed evidence, or any passed
  `experiment.*` claim.
- This repository contains Phase 31 official artifact availability audit
  evidence, with
  `official_project_and_video_found_implementation_code_coming_soon_as_of_2026-05-17`
  as the scoped public-source status.
- Phase 31 verifies a dated public-source audit of the arXiv page, SIGGRAPH
  2026 schedule page, Minghao Guo author page, first-author homepage data,
  first-author project page, first-author `MINSUGLLY/mabd` GitHub Pages
  repository, Yin Yang author page, local arXiv TeX source tree, and GitHub
  repository search. The official project page and supplementary video were
  found, while implementation code is marked `Code (coming soon)` and no
  released implementation-code URL is recorded in the audited public sources.
- Phase 31 does not verify private author-code absence, unpublished
  implementation-code absence, a paper experiment pass, any Newton solver
  modification, M-ABD lane pass, spinning-box comparison pass, paper timing,
  paper trajectory agreement, generated report artifacts as committed evidence,
  or any passed `experiment.*` claim.
- This repository contains Phase 32 uniform gravity generalized-force CPU
  oracle support after the Phase 32 record is created.
- Phase 32 verifies `gravity_generalized_force(rest_points, masses, gravity)`
  as point-mass `J_i^T m_i g` virtual-work assembly, `MABDCPUOracleConfig`
  gravity input, configured unconstrained CPU oracle step use, and malformed
  gravity-vector rejection through repo and vendored Newton unit tests.
- Phase 32 does not verify heavy-top scene reproduction, physical-pendulum
  scene reproduction, analytic or RK4 reference agreement, joints under
  gravity, contact, collision, friction, implicit contact solve, Warp/CUDA/GPU
  paths, paper timing, rendered output, generated report artifacts as committed
  evidence, or any passed `experiment.*` claim.
- This repository contains Phase 33 physical-pendulum analytic-reference lane
  evidence after the Phase 33 record is created.
- Phase 33 verifies only the paper physical-pendulum elliptic-reference formula
  as a SciPy CPU analytic lane: `physical_pendulum_angle_reference`, config
  and experiment-matrix validation, `analytic_reference` CLI dispatch, compact
  angle samples, `lane_status = passed`, and top-level report status:
  `incomplete`.
- Phase 33 does not verify M-ABD physical-pendulum dynamics, RBD implicit
  baseline dynamics, joint-force waveform agreement, pendulum geometry,
  contact, collision, rendered output, paper timing, generated report artifacts
  as committed evidence, the full physical-pendulum experiment, or any passed
  `experiment.*` claim.
- This repository contains Phase 34 world-anchor CPU-oracle support and a
  physical-pendulum M-ABD development diagnostic lane after the Phase 34 record
  is created.
- Phase 34 verifies vendored Newton dense CPU-oracle world-anchor constraints
  for `MABDCPUOracleWorldConstraint`, dense-only topology gating, malformed
  vector rejection, physical-pendulum `mabd_development` config validation,
  `physical_pendulum_mabd_development` CLI dispatch, the distinct
  `physical_pendulum_mabd_development_diagnostic` report lane id, compact
  angle samples, `lane_status = development_diagnostic_generated`, and
  top-level report status: `incomplete`.
- Phase 34 does not verify the full physical-pendulum experiment,
  paper-faithful pendulum geometry, RBD implicit baseline dynamics,
  joint-force waveform agreement, rendered output, paper timing, topology
  solvers for world anchors beyond dense CPU oracle, generated report artifacts
  as committed evidence, or any passed `experiment.*` claim.
- This repository contains Phase 35 physical-pendulum RBD implicit baseline
  diagnostic lane evidence after the Phase 35 record is created.
- Phase 35 verifies physical-pendulum `rbd_baseline` config validation,
  scalar implicit-RBD CPU rollout generation, `rbd_implicit_baseline` CLI
  dispatch, the `physical_pendulum_scalar_implicit_rbd_development` report
  solver mode, compact angle samples, finite implicit residual and length
  constraint diagnostics, `lane_status = development_diagnostic_generated`,
  `required_missing_lanes = [mabd_newton]`, and top-level report status:
  `incomplete`.
- Phase 35 does not verify the full physical-pendulum experiment,
  paper-faithful pendulum geometry, M-ABD physical-pendulum experiment lane,
  joint-force waveform agreement, rendered output, paper timing, paper
  trajectory agreement, generated videos or raw simulation logs, or any passed
  `experiment.*` claim.

## Forbidden Claims

- Unmodified Newton already supports M-ABD.
- Existing Newton rigid-body solvers are equivalent to the M-ABD method.
- A Newton `SolverSemiImplicit` free-rigid development lane is a paper-faithful
  implicit RBD baseline.
- A rigid `body_q` proxy is paper-faithful affine collision.
- A spinning-box comparison protocol report is a passed paper experiment.
- Phase 20 point-plane contact diagnostics are a paper-faithful collision or
  contact solve.
- A nonpenetrating spinning-box initial pose is a paper-faithful contact solve.
- An RBD baseline that consumes the configured initial translation is a
  paper-faithful implicit RBD baseline.
- Matching development-lane position vectors are paper trajectory agreement.
- Development-lane trajectory samples or affine shape diagnostics are paper
  trajectory agreement.
- Phase 29 kinematic feasibility diagnostics are an M-ABD lane pass or solver
  fix.
- Phase 30 source-audit absence findings are proof of private author-code
  behavior, a Newton solver modification, or a paper experiment pass.
- Phase 31 project-page/video availability or `Code (coming soon)` status is
  proof that private author code, unpublished implementation code, or
  author-owned solver artifacts do not exist.
- Phase 32 gravity generalized-force mapping is a passed heavy-top,
  physical-pendulum, contact, or paper experiment reproduction.
- Phase 33 analytic-reference lane status is a passed physical-pendulum
  experiment, M-ABD dynamics result, RBD baseline result, or joint-force
  agreement result.
- Phase 34 physical-pendulum M-ABD development diagnostic is a passed
  physical-pendulum experiment, paper-faithful pendulum geometry result, RBD
  baseline result, joint-force agreement result, or paper timing result.
- Phase 35 physical-pendulum RBD diagnostic is a passed physical-pendulum
  experiment, paper-faithful pendulum geometry result, M-ABD dynamics result,
  joint-force agreement result, or paper timing result.
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
