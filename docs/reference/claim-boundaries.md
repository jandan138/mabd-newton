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
- This repository contains Phase 36 physical-pendulum comparison protocol
  evidence after the Phase 36 record is created.
- Phase 36 verifies `physical_pendulum_comparison` config validation,
  `run_physical_pendulum_comparison`, `--lane physical_pendulum_comparison`
  CLI dispatch, explicit `--analytic-report`/`--mabd-report`/`--rbd-report`
  inputs, input report provenance with per-lane source commits and SHA256,
  matched/unmatched sample coverage, `paper_metric_statuses` for the physical
  pendulum matrix metrics, `missing_required_lanes = [mabd_newton]`, the
  `physical_pendulum_multilane_comparison_development` report solver mode, and
  top-level report status: `incomplete`.
- Phase 36 does not verify the full physical-pendulum experiment, M-ABD lane
  pass, joint-force waveform agreement, paper geometry, rendered output, paper
  timing, paper trajectory agreement, generated videos or raw simulation logs,
  or any passed `experiment.*` claim.
- This repository contains Phase 37 formal physical-pendulum `mabd_newton`
  lane evidence and regenerated comparison evidence after the Phase 37 record
  is created.
- Phase 37 verifies physical-pendulum `mabd_newton` config validation,
  `run_physical_pendulum_mabd_newton`, `--lane physical_pendulum_mabd_newton`
  CLI dispatch, the `mabd_cpu_oracle_physical_pendulum_newton_lane` report
  solver mode, compact angle samples with `phase_drift_rad`,
  `world_anchor_reaction_vector_n`, `max_world_anchor_reaction_magnitude_n`,
  comparison acceptance of `baseline_lane = mabd_newton`,
  `missing_required_lanes = []`, `paper_metric_statuses.phase_drift.status =
  diagnostic_available`, `paper_metric_statuses.joint_force_error.status =
  diagnostic_reaction_not_paper_waveform`, and top-level report status:
  `incomplete`.
- Phase 37 does not verify the full physical-pendulum experiment,
  paper-faithful pendulum geometry, joint-force waveform agreement, paper
  timing, rendered output, paper trajectory agreement, generated videos or raw
  simulation logs, or any passed `experiment.*` claim.
- This repository contains Phase 38 dense constrained polar CPU KKT evidence
  and regenerated physical-pendulum `mabd_newton` polar-lane report evidence
  after the Phase 38 record is created.
- Phase 38 verifies dense constrained `rotation_mode = polar` CPU oracle KKT
  assembly for a world-anchor constraint, explicit constrained `no_polar`
  rejection because the current no-polar increment map is nonlinear, explicit
  rotated non-dense topology rejection, `mabd_newton.rotation_mode = polar`
  config validation, `mabd_rotation_mode = polar` in the formal
  physical-pendulum report, `missing_required_lanes = []`,
  `paper_metric_statuses.joint_force_error.status =
  diagnostic_reaction_not_paper_waveform`, and top-level report status:
  `incomplete`.
- Phase 38 does not verify constrained `no_polar` KKT, rotated chain/tree/loop
  or graph topology KKT, GPU/Warp KKT assembly, the full physical-pendulum
  experiment, paper-faithful pendulum geometry, joint-force waveform agreement,
  paper timing, rendered output, paper trajectory agreement, generated videos
  or raw simulation logs, or any passed `experiment.*` claim.
- This repository contains Phase 39 physical-pendulum timing source-audit
  evidence after the Phase 39 record is created.
- Phase 39 verifies `paper_timing_source_audit` records for the
  physical-pendulum analytic, M-ABD Newton, RBD baseline, and comparison reports:
  source lines `/tmp/mabd-paper/source/sections/experiment.tex:77-91`,
  `runtime_timing_claim_present = false`, `required_metric = false`, status
  `not_a_physical_pendulum_paper_metric`, and removal of
  `paper_timing_missing` from current physical-pendulum report blockers.
- Phase 39 does not verify runtime performance, paper timing reproduction for
  other experiments, the full physical-pendulum experiment, paper-faithful
  pendulum geometry, joint-force waveform agreement, rendered output, paper
  trajectory agreement, generated videos or raw simulation logs, or any passed
  `experiment.*` claim.
- This repository contains Phase 40 scalar physical-pendulum joint-force
  reference diagnostics after the Phase 40 record is created.
- Phase 40 verifies `physical_pendulum_angular_velocity_reference`,
  `physical_pendulum_joint_force_reference`, analytic
  `joint_force_samples_n`, lane `max_abs_joint_force_error_n` metrics,
  per-sample `reference_joint_force_magnitude_n` and
  `abs_joint_force_error_n`, comparison `joint_force_waveform_diagnostics`,
  `missing_paper_metrics = [joint_force_error:paper_geometry_unknown]`, and
  `paper_metric_statuses.joint_force_error.status =
  diagnostic_scalar_reference_not_paper_geometry`.
- Phase 40 does not verify the paper's exact physical-pendulum geometry, the
  paper joint-force waveform, the full physical-pendulum experiment, rendered
  output, runtime performance, generated videos or raw simulation logs, or any
  passed `experiment.*` claim.
- This repository contains Phase 41 physical-pendulum geometry source-asset
  audit evidence after the Phase 41 record is created.
- Phase 41 verifies `physical_pendulum_geometry_source_audit` against the local
  arXiv v2 paper source tree, including `source_tree_paths`,
  `scanned_text_paths`, `scanned_tex_paths`, source hashes for
  `sections/experiment.tex` and
  `images/simple_pendulum/simple_pendulum.pdf`, positive findings from
  `sections/experiment.tex:77-91`, embedded `pendulum*.png` figure metadata,
  the `absence_findings` report section,
  `absence_findings.physical_pendulum_geometry_parameter_search.status =
  no_paper_faithful_physical_pendulum_geometry_parameters_found`, audit status
  `source_assets_found_geometry_parameters_missing`, retained missing
  parameters such as `body_geometry`, `mass_distribution`, `inertia_tensor`,
  and `raw_joint_force_curve_data`, and retained blockers for public source
  geometry parameters, raw curve data, and private author assets.
- Phase 41 does not verify private author assets, absence of unpublished author
  code, paper-faithful physical-pendulum geometry, raw curve data, the full
  physical-pendulum experiment, rendered output, runtime performance, generated
  videos or raw simulation logs, or any passed `experiment.*` claim.
- This repository contains Phase 42 spinning-box report-artifact evidence after
  the Phase 42 record is created.
- Phase 42 verifies committed compact JSON reports for the spinning-box M-ABD
  diagnostic lane, M-ABD paper-horizon diagnostic lane, paper-faithful RBD lane
  gate, and comparison protocol; it verifies source-stamped report provenance,
  finite required comparison metrics, `rbd_implicit_baseline` lane gate status:
  `passed`, `mabd_newton` lane gate status: `incomplete`, retained
  `mabd_paper_horizon_diagnostic_thresholds_violated` and
  `mabd_kinematic_feasibility_blocker_recorded` blockers, retained
  `mabd_newton_report_incomplete` and
  `spinning_box_comparison_pass_gate_not_enabled` comparison blockers, and
  top-level report status: `incomplete`.
- Phase 42 does not verify a passed spinning-box experiment, M-ABD lane pass,
  paper-horizon M-ABD stability, shape or energy agreement, comparison pass
  gate enablement, rendered output, runtime performance, generated videos or raw
  simulation logs, or any passed `experiment.*` claim.
- This repository contains Phase 43 T-handle RK4 reference diagnostic lane
  evidence after the Phase 43 record is created.
- Phase 43 verifies a source-backed `rbd_rk4_reference` diagnostic lane for
  `experiment.single_body.t_handle`, the public T-handle figure hash, zero
  gravity, `omega_0 = 3 rad/s`, RK4 step size `h = 10^-4 s`, deterministic
  torque-free angular-velocity samples, at least one intermediate-axis sign
  flip in the configured diagnostic horizon, small relative energy and angular
  momentum norm drift, retained `exact_t_handle_geometry_unknown`,
  `raw_t_handle_reference_curve_data_missing`, `mabd_newton_report_missing`,
  and `t_handle_comparison_report_missing` blockers, and top-level report
  status: `incomplete`.
- Phase 43 does not verify a passed T-handle experiment, paper-faithful
  T-handle geometry, raw figure curve agreement, M-ABD T-handle lane pass,
  ABD-vs-RBD comparison, rendered output, runtime performance, generated videos
  or raw simulation logs, or any passed `experiment.*` claim.
- This repository contains Phase 56 T-handle MABD Newton diagnostic lane
  evidence after the Phase 56 record is created.
- Phase 56 verifies a `mabd_newton` diagnostic report for
  `experiment.single_body.t_handle` generated through vendored Newton
  `SolverMABD.step()`, model-derived `mabd:body` and disabled `mabd:gravity`
  rows, `solver_model_config_source = newton_model_derived`, a 4 second
  horizon, 9 samples aligned to the RK4 diagnostic grid, finite energy and
  angular-momentum drift diagnostics, proxy inertia mismatch diagnostics,
  current `max_affine_shape_spread_m` threshold failure, top-level report
  status: `incomplete`, and replacement of the matrix blocker with
  `mabd_newton_report_incomplete`.
- Phase 56 does not verify a passed T-handle experiment, passed T-handle MABD
  lane, paper-faithful T-handle geometry, paper-faithful inertia, raw waveform
  agreement, ABD-vs-RBD comparison pass, paper timing, rendered output, runtime
  performance, generated videos or raw simulation logs, full paper
  reproduction, or any passed `experiment.*` claim.
- Phase 56 T-handle MABD Newton diagnostic evidence must not be described as a
  passed T-handle experiment, passed M-ABD lane, paper-faithful T-handle
  geometry or inertia reconstruction, raw curve agreement, comparison pass
  gate, paper timing result, full paper reproduction, or any passed
  `experiment.*` claim.
- This repository contains Phase 57 T-handle comparison protocol evidence
  after the Phase 57 record is created.
- Phase 57 verifies an executable `t_handle_comparison_protocol` report that
  consumes the existing `rbd_rk4_reference` and `mabd_newton` T-handle
  diagnostic reports, validates input report provenance and sha256 hashes,
  requires `reference_not_paper_geometry = true`, records the MABD
  `t_handle_model_derived_proxy` scope and `newton_model_derived` config
  source, computes finite aligned-sample RMSE and max angular-velocity deltas,
  records sample-grid sign-flip timing diagnostic limits including
  `sample_grid_flip_delta_unavailable`, records duplicate sample-index guard
  fields, records that `energy_loss` remains unavailable as a paper metric, and
  replaces the current comparison blocker with
  `t_handle_comparison_report_incomplete`.
- Phase 57 does not verify a passed T-handle experiment, passed T-handle MABD
  lane, paper-faithful T-handle geometry, paper-faithful inertia, raw waveform
  agreement, paper energy loss, ABD-vs-RBD comparison pass, paper timing,
  rendered output, runtime performance, generated videos or raw simulation
  logs, comparison pass gate, full paper reproduction, or any passed
  `experiment.*` claim.
- Phase 57 T-handle comparison protocol evidence must not be described as a
  passed T-handle experiment, passed M-ABD lane, paper-faithful T-handle
  geometry or inertia reconstruction, raw curve agreement, paper energy-loss
  agreement, comparison pass gate, paper timing result, full paper
  reproduction, or any passed `experiment.*` claim.
- This repository contains Phase 58 T-handle paper-figure color-family
  digitization evidence after the Phase 58 record is created.
- Phase 58 verifies deterministic `pdftocairo 22.02.0` rendering of the
  recorded public `T-handle.pdf`, the pinned PDF sha256 and `3861 x 1541`
  rendered image size, compact numeric blue/orange/green color-family samples
  for intermediate-axis angular velocity and relative energy loss, a
  `paper_figure_digitization` report, `t_handle_figure_curves` runner/CLI
  dispatch, comparison-report `paper_figure_curves` provenance, and paper
  metric statuses that only say digitized figure color-family data is available
  without any curve or energy-loss agreement pass.
- Phase 58 does not verify a passed T-handle experiment, authors' raw
  simulation data, solid/dashed line-style separation, specific legend-entry
  curve identity, paper-faithful T-handle geometry or inertia, raw waveform
  agreement, paper energy-loss agreement, paper timing, runtime performance,
  comparison pass gate, rendered-output evidence, generated videos, full paper
  reproduction, or any passed `experiment.*` claim.
- Phase 58 T-handle paper-figure digitization evidence must not be described as
  a passed T-handle experiment, passed M-ABD lane, authors' raw simulation data
  or authors' raw curve data, paper-faithful T-handle geometry or inertia
  reconstruction, solid/dashed line-style separation, specific legend-entry
  curve identity, raw curve agreement or raw waveform agreement, paper
  energy-loss agreement, comparison pass gate, paper timing result, full paper
  reproduction, runtime performance, or any passed `experiment.*` claim.
- This repository contains Phase 59 T-handle digitized-figure agreement
  diagnostic evidence after the Phase 59 record is created.
- Phase 59 verifies normalized-time numeric error diagnostics between the
  current T-handle RK4/M-ABD diagnostic lanes and the Phase 58 digitized
  blue/orange/green paper-figure color-family curves. It records per-lane
  angular-velocity and relative-energy-loss RMSE/max-error diagnostics,
  `normalized_figure_time_not_paper_raw_time`,
  `numeric_best_fit_not_legend_identity`, and
  `diagnostic_only_not_curve_agreement` disclaimers, and keeps
  `digitized_figure_curve_agreement_passed = false`.
- Phase 59 does not verify a passed T-handle experiment, passed T-handle MABD
  lane, authors' raw simulation data, authors' raw curve data, solid/dashed
  line-style separation, specific legend-entry curve identity, paper raw-time
  alignment, paper-faithful T-handle geometry or inertia, raw waveform
  agreement, paper energy-loss agreement, paper timing, runtime performance,
  comparison pass gate, rendered-output evidence, generated videos, full paper
  reproduction, or any passed `experiment.*` claim.
- Phase 59 T-handle digitized-figure agreement diagnostic evidence must not be
  described as a passed T-handle experiment, passed M-ABD lane, authors' raw
  simulation data or authors' raw curve data, paper-faithful T-handle geometry
  or inertia reconstruction, solid/dashed line-style separation, specific
  legend-entry curve identity, paper raw-time alignment, raw curve agreement or
  raw waveform agreement, paper energy-loss agreement, comparison pass gate,
  paper timing result, full paper reproduction, runtime performance, or any
  passed `experiment.*` claim.
- This repository contains Phase 60 machine-checkable reproduction gap audit
  evidence after the Phase 60 record is created.
- Phase 60 verifies all 15 remaining `experiment.*` paper claims are covered
  by `docs/reference/reproduction-gap-audit.yaml`, that the audit matches the
  paper claim manifest and experiment matrix blockers, that committed compact
  report hashes remain non-passing, that `full_reproduction_complete = false`,
  that `experiment_claims_passed = 0`, and that the Newton-only continuation
  path is recorded as the next scoped technical direction.
- Phase 60 does not verify a passed paper experiment, solver fix, contact or
  collision implementation, comparative baseline result, runtime timing
  result, rendered-output agreement, full paper reproduction, or any passed
  `experiment.*` claim.
- Phase 60 reproduction gap audit evidence must not be described as a passed
  paper experiment, solver fix, contact or collision implementation,
  comparative baseline result, runtime timing result, rendered-output
  agreement, full paper reproduction, or any passed `experiment.*` claim.
- This repository contains Phase 61 spinning-box paper-horizon contact
  diagnostic gap evidence after the Phase 61 record is created.
- Phase 61 verifies the current spinning-box paper-horizon `mabd_newton`
  diagnostic report records contact diagnostics evaluated from current M-ABD
  states with `contact_diagnostic_policy =
  evaluated_from_current_mabd_states_not_applied_to_step`,
  `contact_penetration_observed_without_response`,
  `spinning_box_contact_response_missing`, positive penetration and normal
  force diagnostics, and top-level report status: `incomplete`. It also
  records the report policy that contact diagnostics are not applied to the
  step.
- Phase 61 does not verify a passed spinning-box experiment, M-ABD lane pass,
  contact solver, collision implementation, paper-faithful affine collision,
  comparison pass gate, rendered result, runtime performance, full paper
  reproduction, or any passed `experiment.*` claim.
- Phase 61 spinning-box contact diagnostic evidence must not be described as a
  passed spinning-box experiment, M-ABD lane pass, contact solver, collision
  implementation, paper-faithful affine collision, comparison pass gate,
  rendered result, runtime performance, full paper reproduction, or any passed
  `experiment.*` claim.
- This repository contains Phase 62 spinning-box explicit contact-response
  diagnostic evidence after the Phase 62 record is created.
- Phase 62 verifies the current spinning-box paper-horizon `mabd_newton`
  diagnostic can pass the existing point-plane penalty contact generalized
  force through the Newton CPU oracle `external_forces` hook with
  `contact_response_policy =
  explicit_current_state_penalty_force_as_external_force_next_step`, records
  `spinning_box_contact_response_not_paper_faithful`,
  `contact_response_does_not_reduce_penetration`, positive applied contact
  force, top-level report status: `incomplete`, and no lane gate.
- Phase 62 does not verify a passed spinning-box experiment, M-ABD lane pass,
  contact solver, collision implementation, implicit contact solve,
  paper-faithful affine collision, comparison pass gate, rendered result,
  runtime performance, full paper reproduction, or any passed `experiment.*`
  claim.
- Phase 62 spinning-box contact-response diagnostic evidence must not be
  described as a passed spinning-box experiment, M-ABD lane pass, contact
  solver, collision implementation, implicit contact solve, paper-faithful
  affine collision, comparison pass gate, rendered result, runtime
  performance, full paper reproduction, or any passed `experiment.*` claim.
- This repository contains Phase 63 spinning-box point-plane
  normal-constraint diagnostic evidence after the Phase 63 record is created.
- Phase 63 verifies the current spinning-box paper-horizon `mabd_newton`
  diagnostic can use `contact_constraint_policy =
  free_predict_then_active_point_plane_normal_constraints` to rerun penetrating
  free-predicted steps with active scalar point-plane normal rows in the Newton
  CPU oracle, records rank filtering with
  `rank_filter_policy = increment_map_row_rank_filter` and
  `increment_map_row_rank_filter`, records
  `spinning_box_normal_constraint_not_paper_faithful`, records reduced
  free-predicted penetration, top-level report status: `incomplete`, and no
  lane gate.
- Phase 63 does not verify a passed spinning-box experiment, M-ABD lane pass,
  contact solver, collision implementation, IPC, generic
  inequality-constrained M-ABD KKT, paper-faithful affine collision, comparison
  pass gate, rendered result, runtime performance, full paper reproduction, or
  any passed `experiment.*` claim.
- Phase 63 spinning-box normal-constraint diagnostic evidence must not be
  described as a passed spinning-box experiment, M-ABD lane pass, contact
  solver, collision implementation, IPC, generic inequality-constrained M-ABD
  KKT, paper-faithful affine collision, comparison pass gate, rendered result,
  runtime performance, full paper reproduction, or any passed `experiment.*`
  claim.
- This repository contains Phase 64 decoupled spatial-twist rigid
  reconstruction diagnostic evidence after the Phase 64 record is created.
- Phase 64 verifies the configured spinning-box paper-horizon report lane can
  use `decoupled_spatial_twist_with_exponential_rigid_update` in
  `decoupled_twist_rigid_reconstruction_diagnostic`, records
  `not_evaluated_no_kkt_solve`, records
  `spinning_box_decoupled_twist_not_paper_faithful`, records positive
  finite-difference velocity inconsistency diagnostics while shape and energy
  thresholds are met, top-level report status: `incomplete`, and no lane gate.
- Phase 64 does not verify a passed spinning-box experiment, M-ABD lane pass,
  the paper solver's private velocity semantics, paper-faithful M-ABD
  stepping, contact solver, paper-faithful affine collision, comparison pass
  gate, rendered result, runtime performance, full paper reproduction, or any
  passed `experiment.*` claim.
- Phase 64 spinning-box decoupled twist diagnostic evidence must not be
  described as a passed spinning-box experiment, M-ABD lane pass, proof of the
  paper solver's private velocity semantics, paper-faithful M-ABD stepping,
  contact solver, paper-faithful affine collision, comparison pass gate,
  rendered result, runtime performance, full paper reproduction, or any passed
  `experiment.*` claim.
- This repository contains Phase 65 spinning-box paper-figure color-family
  digitization evidence after the Phase 65 record is created.
- Phase 65 verifies the recorded `roll_cube.pdf` paper figure can be rendered
  with `pdftocairo -png -singlefile -r 300`, hashed, and sampled into finite
  angular and linear momentum color-family curves using
  `nearest_color_family_within_threshold`, records
  `color_family_curve_available = true`, records
  `paper_reference_legend_identity_available = false`, records
  `curve_identity_status = color_family_not_legend_entry`, records
  `curve_agreement_status = not_evaluated`, top-level report status:
  `incomplete`, and no lane gate.
- Phase 65 does not verify a passed spinning-box experiment, M-ABD lane pass,
  paper reference legend-entry identity, solid/dashed line-style split,
  Newton-vs-paper curve agreement, paper-faithful M-ABD stepping, contact
  solver, paper-faithful affine collision, comparison pass gate, rendered
  output inspection, runtime performance, full paper reproduction, or any
  passed `experiment.*` claim.
- Phase 65 spinning-box paper-figure digitization evidence must not be
  described as a passed spinning-box experiment, M-ABD lane pass, authors' raw
  simulation data, paper reference legend-entry identity, solid/dashed
  line-style split, Newton-vs-paper curve agreement, paper-faithful M-ABD
  stepping, contact solver, paper-faithful affine collision, comparison pass
  gate, rendered output inspection, runtime performance, full paper
  reproduction, or any passed `experiment.*` claim.
- This repository contains Phase 66 spinning-box paper-figure agreement
  diagnostic evidence after the Phase 66 record is created.
- Phase 66 verifies the spinning-box comparison report can consume the Phase
  65 paper-figure color-family digitization report, record
  `digitized_figure_reference_available = true`, record
  `digitized_figure_curve_agreement_available = true`, keep
  `digitized_figure_curve_agreement_passed = false`, record endpoint best-fit
  diagnostics for linear and angular momentum, record
  `paper_figure_curves` provenance, append
  `spinning_box_digitized_figure_curve_agreement_not_passed`, keep top-level
  report status: `incomplete`, and keep no experiment claim passed.
- Phase 66 does not verify a passed spinning-box experiment, M-ABD lane pass,
  paper reference legend-entry identity, solid/dashed line-style split,
  Newton-vs-paper curve agreement, paper-faithful M-ABD stepping, contact
  solver, paper-faithful affine collision, comparison pass gate, rendered
  output inspection, runtime performance, full paper reproduction, or any
  passed `experiment.*` claim.
- Phase 66 spinning-box figure agreement diagnostics must not be described as
  a passed spinning-box experiment, M-ABD lane pass, paper reference
  legend-entry identity, solid/dashed line-style split, Newton-vs-paper curve
  agreement, paper-faithful M-ABD stepping, contact solver, paper-faithful
  affine collision, comparison pass gate, rendered output inspection, runtime
  performance, full paper reproduction, or any passed `experiment.*` claim.
- This repository contains Phase 67 model-derived point-plane normal constraint
  row extraction evidence after the Phase 67 record is created.
- Phase 67 verifies that explicit `mabd:plane_constraint` model rows with
  `mabd:plane_body`, `mabd:plane_rest_point`, `mabd:plane_normal`,
  `mabd:plane_offset`, and `mabd:plane_active` are extracted into the
  vendored/local Newton CPU oracle config used by `SolverMABD.step()`, and
  keeps no experiment claim passed.
- Phase 67 does not verify contact solver behavior, Newton `Contacts`
  ingestion, collision detection, active-set generation, IPC, generic
  inequality-constrained M-ABD KKT, paper-faithful affine contact,
  paper-faithful M-ABD stepping, comparison pass gate, runtime performance,
  rendered output, any passed `experiment.*` claim, or full paper
  reproduction.
- Phase 67 model-derived point-plane normal constraint rows must not be
  described as unmodified Newton M-ABD support, paper-faithful affine
  collision/contact, a contact solver, a passed experiment, or full paper
  reproduction.
- This repository contains Phase 68 SolverMABD model-plane spinning-box
  diagnostic report lane evidence after the Phase 68 record is created.
- Phase 68 verifies that the spinning-box diagnostic runner can build transient
  vendored/local Newton `SolverMABD.step()` models with `mabd:body` and
  `mabd:plane_constraint` custom rows, run the free-predict/active
  point-plane normal constraint policy, emit
  `reports/experiment_matrix/single_body_spinning_box_model_plane_constraint.json`,
  record `model_plane_constraint_config_source =
  mabd:plane_constraint_custom_rows`, record reduced free-predicted
  penetration, and keep no experiment claim passed.
- Phase 68 does not verify contact solver behavior, Newton `Contacts`
  ingestion, collision detection, broadphase or narrowphase, active-set
  generation inside Newton, IPC, friction, complementarity, continuous
  collision detection, generic inequality-constrained M-ABD KKT,
  paper-faithful affine contact, paper-faithful M-ABD stepping, comparison pass
  gate, rendered-output agreement, runtime performance, any passed
  `experiment.*` claim, or full paper reproduction.
- Phase 68 SolverMABD model-plane report lane evidence must not be described
  as unmodified Newton M-ABD contact support, paper-faithful affine
  collision/contact, a contact solver, a passed spinning-box experiment, or
  full paper reproduction.
- This repository contains Phase 69 SolverMABD Contacts input
  plane-constraint plumbing evidence after the Phase 69 record is created.
- Phase 69 verifies that bounded Newton `Contacts` rows can be consumed by
  vendored/local Newton `SolverMABD.step(..., contacts=...)`, read from
  `newton.Contacts.rigid_contact_*`, mapped from shape ids through
  `mabd:body_index`, limited to contacts whose opposite side is static
  geometry with `shape_body == -1`, translated into existing point-plane
  normal constraint rows using the
  `rigid_contacts_to_point_plane_constraints_diagnostic` policy, scoped as
  `diagnostic_only_static_geometry_plane_constraints`, and summarized through
  `last_contacts_input_summary` while keeping no experiment claim passed.
- Phase 69 does not verify contact solver behavior, collision detection,
  broadphase or narrowphase correctness, active-set generation inside Newton,
  IPC, friction, complementarity, continuous collision detection, body-body
  affine contact, dynamic non-M-ABD body contact, generic
  inequality-constrained M-ABD KKT, paper-faithful affine collision/contact,
  paper-faithful M-ABD stepping, comparison pass gate, rendered-output
  agreement, runtime performance, any passed `experiment.*` claim, or full
  paper reproduction.
- Phase 69 SolverMABD Contacts input evidence must not be described as a
  contact solver, collision detection, paper-faithful affine collision/contact,
  generic inequality-constrained M-ABD KKT, a passed experiment, or full paper
  reproduction.
- This repository contains Phase 70 SolverMABD Contacts input spinning-box
  diagnostic report lane evidence after the Phase 70 record is created.
- Phase 70 verifies that the spinning-box diagnostic runner can build
  transient vendored/local Newton models with one `mabd:body`, one M-ABD box
  shape, one static plane shape with `shape_body == -1`, synthesize
  `newton.Contacts` rows from diagnostic corner/plane penetrations using
  `newton.Contacts.rigid_contact_static_plane_rows_from_diagnostic_corners`,
  call `SolverMABD.step(..., contacts=...)`, emit
  `reports/experiment_matrix/single_body_spinning_box_contacts_input.json`,
  record `contacts_input_summary_source = last_contacts_input_summary`, record
  reduced free-predicted penetration, and keep no experiment claim passed.
- Phase 70 does not verify contact solver behavior, collision detection,
  broadphase or narrowphase correctness, active-set generation inside Newton,
  IPC, friction, complementarity, continuous collision detection, body-body
  affine contact, dynamic non-M-ABD body contact, generic
  inequality-constrained M-ABD KKT, paper-faithful affine collision/contact,
  paper-faithful M-ABD stepping, comparison pass gate, rendered-output
  agreement, runtime performance, any passed `experiment.*` claim, or full
  paper reproduction.
- Phase 70 SolverMABD Contacts input report lane evidence must not be
  described as a contact solver, collision detection, paper-faithful affine
  collision/contact, generic inequality-constrained M-ABD KKT, a passed
  experiment, or full paper reproduction.
- This repository contains Phase 71 affine static-plane active-set diagnostic
  report lane evidence after the Phase 71 record is created.
- Phase 71 verifies that `SolverMABD.detect_static_plane_contacts` can
  generate a bounded active set from M-ABD affine box corners against world
  static infinite planes, feed generated `newton.Contacts` into
  `SolverMABD.step(..., contacts=...)`, record
  `paper_horizon.affine_static_plane_contacts_output_report`, emit
  `reports/experiment_matrix/single_body_spinning_box_affine_static_plane_contacts.json`,
  record `contacts_input_summary_source = last_contacts_input_summary`,
  record reduced free-predicted penetration, and keep no experiment claim
  passed.
- Phase 71 does not verify generic collision detection, broadphase or
  narrowphase correctness, finite-plane clipping, mesh/SDF/sphere/capsule/
  cylinder collision, body-body affine contact, dynamic non-M-ABD body
  contact, contact solver behavior, IPC, friction, complementarity, continuous
  collision detection, generic inequality-constrained M-ABD KKT,
  paper-faithful affine collision/contact, paper-faithful M-ABD stepping,
  comparison pass gate, rendered-output agreement, runtime performance, any
  passed `experiment.*` claim, or full paper reproduction.
- Phase 71 affine static-plane contact report lane evidence must not be
  described as generic collision detection, a contact solver, paper-faithful
  affine collision/contact, a passed experiment, or full paper reproduction.
- This repository contains Phase 72 spinning-box paper-figure momentum endpoint
  diagnostic evidence after the Phase 72 record is created.
- Phase 72 verifies that the spinning-box digitized paper-figure endpoint
  diagnostics compare paper momentum endpoint values against endpoint momentum
  magnitudes from `final_linear_momentum_norm` and
  `final_angular_momentum_norm`, not `linear_momentum_error` or
  `angular_momentum_error`; it records small diagnostic endpoint best-fit
  errors, keeps `digitized_figure_curve_agreement_passed = false`, keeps
  `spinning_box_digitized_figure_curve_agreement_not_passed`, confirms the
  comparison pass gate remains disabled, keeps top-level report status:
  `incomplete`, and keeps no experiment claim passed.
- Phase 72 does not verify a passed spinning-box experiment, M-ABD lane pass,
  paper reference legend-entry identity, solid/dashed line-style split,
  Newton-vs-paper curve agreement, comparison pass gate, rendered output
  inspection, runtime performance, full paper reproduction, or any passed
  `experiment.*` claim.
- Phase 72 spinning-box figure momentum endpoint diagnostics must not be
  described as a passed spinning-box experiment, M-ABD lane pass, paper
  reference legend-entry identity, solid/dashed line-style split,
  Newton-vs-paper curve agreement, comparison pass gate, rendered output
  inspection, runtime performance, full paper reproduction, or any passed
  `experiment.*` claim.
- This repository contains Phase 73 rolling/spinning protocol report lane
  evidence after the Phase 73 record is created.
- Phase 73 verifies that the rolling/spinning matrix output report
  `reports/experiment_matrix/single_body_rolling_spinning.json` exists as an
  incomplete protocol-only report, records paper timing values for 10K rolling
  cylinder steps at `h = 0.01 sec` on `i7 CPU, single thread`, records
  backend: `report_protocol`, records missing blockers
  `rbd_baseline_adapter_missing`, `benchmark_protocol_not_recorded`, and
  `rolling_cylinder_runtime_not_measured`, records per-metric
  `paper_metric_statuses`, records `local_runtime_measured = false`, records
  `full_experiment_claim_passed = false`, and keeps no experiment claim
  passed.
- Phase 73 does not verify rolling-cylinder dynamics, local runtime timing,
  implicit/explicit RBD baselines, spinning-box momentum/energy agreement,
  comparative baseline results, rendered output, a completed rolling/spinning
  reproduction, full paper reproduction, or any passed `experiment.*` claim.
- Phase 73 rolling/spinning protocol report lane evidence must not be
  described as a completed rolling/spinning reproduction, runtime benchmark,
  passed baseline, rolling-cylinder dynamics result, local runtime timing,
  implicit/explicit RBD baselines, comparative baseline results, rendered
  output, full paper reproduction, or any passed `experiment.*` claim.
- This repository contains Phase 74 rolling-cylinder Newton RBD development
  baseline evidence with the Phase 74 record.
- Phase 74 verifies that
  `reports/experiment_matrix/single_body_rolling_spinning_rbd_implicit_baseline.json`
  exists as an incomplete Newton CPU `SolverSemiImplicit` rolling-cylinder
  development baseline report, records `builder.finalize(device="cpu")`,
  `ModelBuilder.add_shape_cylinder`, `ModelBuilder.add_ground_plane`,
  `Model.contacts`, `Model.collide`, `SolverSemiImplicit`, 10000 steps at
  `h = 0.01 sec`, local non-paper-comparable wall-clock timing, contact count
  summary, contact material, maximum center penetration, no-slip residual,
  `required_lanes_missing = [rbd_explicit_baseline, mabd_newton,
  paper_comparable_timing]`, `full_experiment_claim_passed = false`, and keeps
  no experiment claim passed.
- Phase 74 does not verify paper-faithful implicit RBD, explicit RBD, M-ABD
  rolling-cylinder dynamics, co-rotated ABD timing, same-hardware paper timing,
  paper-comparable performance, a completed rolling/spinning reproduction, full
  paper reproduction, or any passed `experiment.*` claim.
- Phase 74 rolling-cylinder Newton RBD development baseline evidence must not
  be described as a paper-faithful implicit RBD result, explicit RBD result,
  M-ABD rolling-cylinder result, co-rotated ABD timing result,
  paper-comparable timing result, completed rolling/spinning reproduction,
  comparative baseline pass, full paper reproduction, or any passed
  `experiment.*` claim.
- This repository contains Phase 75 rolling-cylinder Newton ExplicitEuler
  development baseline evidence with the Phase 75 record.
- Phase 75 verifies that
  `reports/experiment_matrix/single_body_rolling_spinning_rbd_explicit_baseline.json`
  exists as an incomplete Newton CPU `SolverExplicitEuler` rolling-cylinder
  development baseline report, records 10000 steps at `h = 0.01 sec`, local
  non-paper-comparable wall-clock timing, contact count summary, contact
  material, maximum center penetration, no-slip residual,
  `required_lanes_missing = [mabd_newton, paper_comparable_timing]`,
  `full_experiment_claim_passed = false`, and keeps no experiment claim
  passed.
- Phase 75 does not verify paper-faithful explicit RBD, M-ABD
  rolling-cylinder dynamics, co-rotated ABD timing, same-hardware paper
  timing, paper-comparable performance, a completed rolling/spinning
  reproduction, full paper reproduction, or any passed `experiment.*` claim.
- Phase 75 rolling-cylinder Newton ExplicitEuler development baseline evidence
  must not be described as a paper-faithful explicit RBD result, M-ABD
  rolling-cylinder result, co-rotated ABD timing result, paper-comparable
  timing result, completed rolling/spinning reproduction, comparative baseline
  pass, full paper reproduction, or any passed `experiment.*` claim.
- This repository contains Phase 76 rolling-cylinder SolverMABD diagnostic
  evidence with the Phase 76 record.
- Phase 76 verifies that
  `reports/experiment_matrix/single_body_rolling_spinning_mabd_newton.json`
  exists as an incomplete Newton CPU `SolverMABD` rolling-cylinder diagnostic
  report, records 10000 steps at `h = 0.01 sec`, local non-paper-comparable
  wall-clock timing, `SolverMABD.detect_static_plane_contacts`,
  `SolverMABD.step`, the bounded affine-cylinder static-plane diagnostic
  policy, contact count summary, support penetration, no-slip residual,
  affine shape spread, `required_lanes_missing = [paper_comparable_timing]`,
  `full_experiment_claim_passed = false`, and keeps no experiment claim passed.
- Phase 76 does not verify paper-faithful M-ABD rolling-cylinder collision,
  paper-faithful rolling friction/no-slip dynamics, paper-faithful explicit
  RBD, co-rotated ABD timing, same-hardware paper timing, paper-comparable
  performance, a completed rolling/spinning reproduction, full paper
  reproduction, or any passed `experiment.*` claim.
- Phase 76 rolling-cylinder SolverMABD diagnostic evidence must not be
  described as a paper-faithful M-ABD rolling-cylinder result, paper-faithful
  collision result, rolling friction result, paper-faithful explicit RBD
  result, co-rotated ABD timing result, paper-comparable timing result,
  completed rolling/spinning reproduction, comparative baseline pass, full
  paper reproduction, or any passed `experiment.*` claim.
- This repository contains Phase 77 rolling-cylinder finite-stiffness
  SolverMABD material preflight evidence with the Phase 77 record.
- Phase 77 verifies that
  `reports/experiment_matrix/single_body_rolling_spinning_mabd_material_preflight.json`
  exists as an incomplete Newton CPU `SolverMABD` rolling-cylinder material
  preflight report, records the paper-sourced `young_modulus_pa = 1.0e9` and
  `poisson_ratio = 0.3`, keeps `zero_stiffness_diagnostic = false`, records
  local non-paper-comparable wall-clock timing, and keeps
  `full_experiment_claim_passed = false`.
- Phase 77 does not verify paper-faithful M-ABD rolling-cylinder collision,
  paper-faithful rolling friction/no-slip dynamics, paper-faithful explicit or
  implicit RBD, co-rotated ABD timing, same-hardware paper timing,
  paper-comparable performance, a completed rolling/spinning reproduction, full
  paper reproduction, or any passed `experiment.*` claim.
- Phase 77 rolling-cylinder finite-stiffness material preflight evidence must
  not be described as a paper-faithful M-ABD rolling-cylinder result,
  paper-faithful collision result, rolling friction result, paper-faithful
  explicit or implicit RBD result, co-rotated ABD timing result,
  paper-comparable timing result, completed rolling/spinning reproduction,
  comparative baseline pass, full paper reproduction, or any passed
  `experiment.*` claim.
- This repository contains Phase 78 rolling/spinning timing protocol evidence
  with the Phase 78 record.
- Phase 78 verifies that
  `reports/experiment_matrix/single_body_rolling_spinning_timing_protocol.json`
  exists as an incomplete report-protocol artifact, records the paper timing
  table for the rolling cylinder benchmark, records Phase 73 through Phase 77
  input reports, keeps `paper_comparable = false`, records
  `paper_comparable_timing_missing`, and keeps
  `full_experiment_claim_passed = false`.
- Phase 78 does not verify a paper-comparable timing result, same-hardware
  paper timing, single-thread runtime enforcement, paper-faithful M-ABD
  rolling-cylinder collision, paper-faithful rolling friction/no-slip dynamics,
  paper-faithful explicit or implicit RBD, co-rotated ABD timing, completed
  rolling/spinning reproduction, full paper reproduction, or any passed
  `experiment.*` claim.
- Phase 78 rolling/spinning timing protocol evidence must not be described as a
  paper-comparable timing result, performance pass, paper-faithful M-ABD
  rolling-cylinder result, paper-faithful explicit or implicit RBD result,
  comparative baseline pass, completed rolling/spinning reproduction, full
  paper reproduction, or any passed `experiment.*` claim.
- This repository contains Phase 79 analytic no-slip rolling-cylinder reference
  evidence with the Phase 79 record.
- Phase 79 verifies that
  `reports/experiment_matrix/single_body_rolling_spinning_rbd_no_slip_reference.json`
  exists as an incomplete closed-form CPU NumPy analytic reference, records
  zero no-slip residual, zero center-height drift, zero relative energy drift,
  `local_runtime_measured = false`, deterministic report hashing,
  `paper_comparable = false`, and `full_experiment_claim_passed = false`.
- Phase 79 does not verify paper-faithful explicit or implicit RBD,
  paper-faithful M-ABD rolling-cylinder collision, rolling friction/no-slip
  dynamics in Newton, paper-comparable timing, same-hardware paper timing,
  co-rotated ABD timing, completed rolling/spinning reproduction, full paper
  reproduction, or any passed `experiment.*` claim.
- Phase 79 analytic no-slip reference evidence must not be described as a
  paper-faithful RBD result, paper-faithful M-ABD rolling-cylinder result,
  paper-comparable timing result, performance pass, comparative baseline pass,
  completed rolling/spinning reproduction, full paper reproduction, or any
  passed `experiment.*` claim.
- This repository contains Phase 44 SolverMABD model-derived CPU body-config
  integration evidence after the Phase 44 record is created.
- Phase 44 verifies model-derived `SolverMABD.step()` CPU oracle configuration
  from registered `mabd:body` rows, including `mabd:rest_point0` through
  `mabd:rest_point3`, `mabd:point_mass0` through `mabd:point_mass3`,
  `mabd:volume`, positive density-derived mass defaults, explicit point-mass
  overrides, model `mabd:control` rows, continued manual
  `configure_cpu_oracle(...)` support, and model-cache invalidation through
  `notify_model_changed()`.
- Phase 44 does not verify model-derived `mabd:constraint` rows, Newton
  `Contacts`, Newton `Control` input, GPU/Warp kernels, paper scene assets,
  paper timing, comparative baselines, rendered output, generated videos or raw
  simulation logs, a full paper reproduction, or any passed `experiment.*`
  claim.
- This repository contains Phase 45 SolverMABD model-derived CPU
  joint-constraint config integration evidence after the Phase 45 record is
  created.
- Phase 45 verifies model-derived `mabd:constraint` rows can be translated into
  `MABDCPUOracleConstraint` entries for dense CPU oracle stepping, including
  ball, hinge, and universal joint specs, `mabd:cp_index`, explicit
  `mabd:constraint_type` values, rank validation, body-index validation,
  invalid-type rejection, and continued manual `configure_cpu_oracle(...)`
  precedence over the model-derived path.
- Phase 45 does not verify model-derived world constraints, Newton `Contacts`,
  Newton `Control` input, GPU/Warp kernels, paper scene assets, paper timing,
  comparative baselines, rendered output, generated videos or raw simulation
  logs, a full paper reproduction, or any passed `experiment.*` claim.
- This repository contains Phase 46 SolverMABD model-derived CPU
  world-constraint config integration evidence after the Phase 46 record is
  created.
- Phase 46 verifies model-derived `mabd:world_constraint` rows can be
  translated into `MABDCPUOracleWorldConstraint` entries for dense CPU oracle
  stepping, including `mabd:world_body`, `mabd:world_rest_point`,
  `mabd:world_point`, body-index validation, cached model-derived config
  behavior, dense world-anchor residual correction, reaction-vector
  availability through `dlambda`, and continued manual
  `configure_cpu_oracle(...)` precedence over the model-derived path.
- Phase 46 does not verify Newton `Contacts`, Newton `Control` input,
  GPU/Warp kernels, paper scene assets, paper timing, comparative baselines,
  rendered output, generated videos or raw simulation logs, a full paper
  reproduction, or any passed `experiment.*` claim.
- This repository contains Phase 47 SolverMABD model-derived CPU gravity-config
  integration evidence after the Phase 47 record is created.
- Phase 47 verifies model-derived `mabd:gravity` rows can be translated into
  `MABDCPUOracleConfig.gravity` for CPU oracle stepping, including
  `mabd:gravity_enabled`, `mabd:gravity_vector`, disabled-row filtering,
  multiple-enabled-row validation, cached model-derived config behavior, and
  continued manual `configure_cpu_oracle(...)` precedence over the
  model-derived path.
- Phase 47 does not verify heavy-top reproduction, physical-pendulum scene
  reproduction, Newton `Contacts`, Newton `Control` input, GPU/Warp kernels,
  paper scene assets, paper timing, comparative baselines, rendered output,
  generated videos or raw simulation logs, a full paper reproduction, or any
  passed `experiment.*` claim.
- This repository contains Phase 48 physical-pendulum `mabd_newton`
  model-derived SolverMABD lane-plumbing evidence after the Phase 48 record is
  created.
- Phase 48 verifies the formal physical-pendulum `mabd_newton` report lane uses
  Newton model-derived `SolverMABD.step()` with `mabd:body`,
  `mabd:world_constraint`, and `mabd:gravity` rows for the procedural
  diagnostic pendulum, records `solver_model_config_source =
  newton_model_derived`, matches the prior manual CPU-oracle diagnostic rollout
  within numerical tolerance, keeps the regenerated comparison report
  incomplete, and keeps `full_experiment_claim_passed = false`.
- Phase 48 does not verify paper-faithful physical-pendulum geometry, a
  physical-pendulum experiment pass, Newton `Contacts`, runtime Newton
  `Control`, GPU/Warp kernels, rendered output, generated videos, paper timing,
  comparative pass gates, raw simulation logs, a full paper reproduction, or
  any passed `experiment.*` claim.
- This repository contains Phase 49 heavy-top RK4 reference diagnostic lane
  evidence after the Phase 49 record is created.
- Phase 49 verifies a source-backed `rbd_rk4_reference` diagnostic lane for
  `experiment.single_body.heavy_top`, the public spinning-top figure hash,
  gravity along negative y, initial tilt `5 deg`, initial angular speed
  `10 rad/s`, RK4 step size `h = 10^-4 s`, deterministic precession and
  nutation samples for the configured diagnostic inertia, small relative
  energy drift, retained `exact_heavy_top_inertia_unknown`,
  `exact_heavy_top_geometry_unknown`,
  `raw_heavy_top_reference_curve_data_missing`, `mabd_newton_report_incomplete`,
  `heavy_top_comparison_report_incomplete`, and `heavy_top_timing_evidence_missing`
  blockers, and top-level report status: `incomplete`.
- Phase 49 does not verify a passed heavy-top experiment, paper-faithful
  heavy-top inertia or geometry, raw figure curve agreement, M-ABD heavy-top
  dynamics, ABD-vs-RBD comparison, rendered output, runtime performance,
  generated videos or raw simulation logs, or any passed `experiment.*` claim.
- This repository contains Phase 50 heavy-top `mabd_newton` diagnostic lane
  evidence after the Phase 50 record is created.
- Phase 50 verifies the formal heavy-top `mabd_newton` diagnostic lane uses
  model-derived `SolverMABD.step()` with Newton custom-frequency rows
  `mabd:body`, `mabd:world_constraint`, and `mabd:gravity`, records
  `solver_model_config_source = newton_model_derived`, generates compact
  precession and nutation samples, keeps `mabd_newton_report_incomplete`,
  retains unresolved heavy-top geometry/inertia/raw-curve/comparison/timing
  blockers, and keeps `full_experiment_claim_passed = false`.
- Phase 50 does not verify a passed heavy-top experiment, paper-faithful
  heavy-top inertia or geometry, raw figure curve agreement, ABD-vs-RBD
  comparison, rendered output, runtime performance, generated videos or raw
  simulation logs, a full paper reproduction, or any passed `experiment.*`
  claim.
- This repository contains Phase 51 heavy-top comparison protocol evidence
  after the Phase 51 record is created.
- Phase 51 verifies an executable `heavy_top_comparison_protocol` report that
  consumes the current `rbd_rk4_reference` and `mabd_newton` heavy-top lane
  reports, records input report provenance and sha256 hashes, maps RK4
  `relative_energy_drift` to the paper `energy_drift` diagnostic field, records
  missing M-ABD precession/energy and raw paper reference-curve gaps, detected
  the then-current sample time-grid mismatch before Phase 55 introduced an
  aligned paper-horizon MABD diagnostic, retains
  `mabd_newton_report_incomplete`, `heavy_top_comparison_report_incomplete`,
  and `heavy_top_timing_evidence_missing` blockers, and keeps
  `full_experiment_claim_passed = false`.
- Phase 51 does not verify a passed heavy-top experiment, paper-faithful
  heavy-top inertia or geometry, raw figure curve agreement, paper timing,
  rendered output, runtime performance, generated videos or raw simulation
  logs, a comparison pass gate, a full paper reproduction, or any passed
  `experiment.*` claim.
- This repository contains Phase 52 heavy-top MABD diagnostic metric evidence
  after the Phase 52 record is created.
- Phase 52 verifies that the heavy-top `mabd_newton` diagnostic report records
  finite per-sample `precession_velocity_rad_s`, point-mass `energy_initial`,
  `energy_final`, and `relative_energy_drift`, and that the heavy-top
  comparison protocol consumes those MABD-side diagnostics. The comparison
  report no longer marks MABD precession velocity or MABD energy drift as
  missing, historically retained `nutation_angle_error:paper_reference_curve_missing`,
  `mabd_newton_report_incomplete`,
  `heavy_top_comparison_report_incomplete`,
  `heavy_top_timing_evidence_missing`, and `sample_time_grid_mismatch` before
  Phase 55 aligned the current sample grid, and keeps
  `full_experiment_claim_passed = false`.
- Phase 52 does not verify a passed heavy-top experiment, paper-faithful
  heavy-top inertia or geometry, raw figure curve agreement, paper timing,
  rendered output, runtime performance, generated videos or raw simulation
  logs, a comparison pass gate, a full paper reproduction, or any passed
  `experiment.*` claim.
- This repository contains Phase 53 heavy-top paper-figure digitization evidence
  after the Phase 53 record is created.
- Phase 53 verifies digitized paper-figure reference-family samples from the
  recorded `spinning_top.pdf` source PDF, Poppler `pdftocairo 22.02.0`,
  deterministic `3179 x 1924` 300 DPI rendering, compact numeric JSON samples,
  explicit `figure_curve_report_path` comparison-report consumption,
  `paper_figure_digitized_reference_available` metric status, and that raw
  author curve data remains unavailable while the
  `raw_heavy_top_reference_curve_data_missing` blocker is retained.
- Phase 53 does not verify a passed heavy-top experiment, authors' raw
  simulation data, blue/orange solid and dashed paper curves, heavy-top curve
  agreement, paper-faithful heavy-top inertia or geometry, paper timing,
  rendered output, runtime performance, generated videos or raw simulation
  logs, a comparison pass gate, a full paper reproduction, or any passed
  `experiment.*` claim.
- This repository contains Phase 54 executable environment clone/sync contract
  evidence after the Phase 54 record is created.
- Phase 54 verifies that the reference `physics-primitive-agent` Newton
  environment clone process is represented by a tested `scripts/env`
  maintenance CLI, that missing-target clone plans use
  `conda create -y -p mabd-newton-py310 --clone physics-primitive-newton-py310`,
  that existing targets are not overwritten by default, that explicit
  `--sync-existing` plans use `rsync -a --delete`, that reference/target path
  aliasing and nesting are rejected, and that dry-run JSON records
  `mutates_reference_environment=false`, `uses_reference_python=false`, and
  `uses_ambient_python=false`.
- Phase 54 does not verify dependency freshness, solver behavior, M-ABD method
  correctness, scene dynamics, paper experiment reproduction, timing,
  comparative baselines, runtime performance, rendered output, a full paper
  reproduction, or any passed `experiment.*` claim.
- This repository contains Phase 55 heavy-top paper-horizon MABD diagnostic
  evidence after the Phase 55 record is created.
- Phase 55 verifies that a Newton-backed heavy-top `mabd_newton` diagnostic
  report with `mabd_diagnostic_scope = paper_horizon_sample_grid` covers the
  0 to 10 second paper figure horizon with 11 samples, preserves
  `solver_model_config_source = newton_model_derived` and Newton custom
  frequencies `mabd:body`, `mabd:world_constraint`, and `mabd:gravity`, records
  current `max_affine_shape_spread_m` threshold failure as
  `incomplete_diagnostic_failed`, and regenerates the heavy-top comparison so
  RK4 and MABD sample grids are aligned with `time_grid_mismatch = false` and
  no current `sample_time_grid_mismatch` blocker.
- Phase 55 does not verify a passed heavy-top experiment, a passed heavy-top
  MABD lane, paper-horizon MABD stability or accuracy, paper-faithful
  heavy-top MABD dynamics, paper-faithful inertia or geometry, raw author curve
  data, digitized curve agreement, a comparison pass gate, paper timing,
  rendered output, generated videos, a full paper reproduction, or any passed
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
- Phase 36 physical-pendulum comparison protocol is not a passed
  physical-pendulum experiment, M-ABD lane pass, joint-force waveform
  agreement, paper geometry result, paper timing result, or any passed
  `experiment.*` claim.
- Phase 37 physical-pendulum `mabd_newton` lane is not a passed
  physical-pendulum experiment, paper-faithful pendulum geometry result,
  joint-force waveform agreement, paper timing result, rendered result, or any
  passed `experiment.*` claim.
- Phase 38 constrained polar CPU KKT support is not a passed physical-pendulum
  experiment, constrained `no_polar` implementation, rotated non-dense topology
  implementation, joint-force waveform agreement, paper geometry result, paper
  timing result, or any passed `experiment.*` claim.
- Phase 39 physical-pendulum timing source audit is not a passed
  physical-pendulum experiment, runtime performance reproduction, paper timing
  result, paper-faithful pendulum geometry result, joint-force waveform
  agreement, rendered result, or any passed `experiment.*` claim.
- Phase 40 physical-pendulum scalar joint-force diagnostics are not a passed
  physical-pendulum experiment, paper-faithful pendulum geometry result, paper
  joint-force waveform reproduction, rendered result, runtime performance
  reproduction, or any passed `experiment.*` claim.
- Phase 41 physical-pendulum source-asset audit is not a passed
  physical-pendulum experiment, proof that private author assets do not exist,
  paper-faithful physical-pendulum geometry reconstruction, paper joint-force
  waveform reproduction, rendered result, runtime performance reproduction, or
  any passed `experiment.*` claim.
- Phase 42 spinning-box report artifacts are not a passed spinning-box
  experiment, M-ABD lane pass, paper-horizon stability result, comparison pass
  gate, rendered result, runtime performance reproduction, or any passed
  `experiment.*` claim.
- Phase 43 T-handle RK4 reference is not a passed T-handle experiment,
  paper-faithful T-handle geometry reconstruction, raw curve agreement, M-ABD
  lane pass, comparison pass gate, rendered result, runtime performance
  reproduction, or any passed `experiment.*` claim.
- Phase 44 model-derived SolverMABD CPU config is not a passed paper
  experiment, not a model-derived joint/constraint implementation, not a
  contact implementation, not a GPU/Warp solver, not a paper scene or timing
  reproduction, and not any passed `experiment.*` claim.
- Phase 45 model-derived SolverMABD joint constraints are not a passed paper
  experiment, not a contact implementation, not a model-derived world
  constraint implementation, not a GPU/Warp solver, not a paper scene or timing
  reproduction, not a full paper reproduction, and not any passed
  `experiment.*` claim.
- Phase 46 model-derived SolverMABD world constraints are not a passed paper
  experiment, not a contact implementation, not a Newton `Control` input
  implementation, not a GPU/Warp solver, not a paper scene or timing
  reproduction, not a full paper reproduction, and not any passed
  `experiment.*` claim.
- Phase 47 model-derived SolverMABD gravity config is not a passed paper
  experiment, not a heavy-top reproduction, not a physical-pendulum scene
  reproduction, not a contact implementation, not a Newton `Control` input
  implementation, not a GPU/Warp solver, not a paper timing reproduction, not
  rendered-output evidence, not a full paper reproduction, and not any passed
  `experiment.*` claim.
- Phase 48 physical-pendulum model-derived `mabd_newton` lane is not a passed
  physical-pendulum experiment, not paper-faithful pendulum geometry, not a
  contact implementation, not a runtime Newton `Control` implementation, not a
  GPU/Warp solver, not rendered-output evidence, not paper timing reproduction,
  not a comparative pass gate, not a full paper reproduction, and not any
  passed `experiment.*` claim.
- Phase 49 heavy-top RK4 reference is not a passed heavy-top experiment, not
  paper-faithful heavy-top inertia or geometry reconstruction, not raw curve
  agreement, not M-ABD heavy-top dynamics, not an M-ABD lane pass, not a
  comparison pass gate, not rendered-output evidence, not runtime performance
  reproduction, and not any passed `experiment.*` claim.
- Phase 50 heavy-top MABD Newton lane is not a passed heavy-top experiment,
  not paper-faithful heavy-top inertia or geometry reconstruction, not raw
  curve agreement, not an ABD-vs-RBD comparison result, not a paper timing
  result, not rendered-output evidence, not a full paper reproduction, and not
  any passed `experiment.*` claim.
- Phase 51 heavy-top comparison protocol is not a passed heavy-top experiment,
  not paper-faithful heavy-top inertia or geometry reconstruction, not raw
  curve agreement, not a comparison pass gate, not a paper timing result, not
  rendered-output evidence, not a full paper reproduction, and not any passed
  `experiment.*` claim.
- Phase 52 heavy-top MABD metrics are not a passed heavy-top experiment, not
  paper-faithful heavy-top inertia or geometry reconstruction, not raw curve
  agreement, not a comparison pass gate, not a paper timing result, not
  rendered-output evidence, not generated-video evidence, not a full paper
  reproduction, and not any passed `experiment.*` claim.
- Phase 53 heavy-top paper-figure digitization is not a passed heavy-top
  experiment, not authors' raw simulation data, not blue/orange solid and
  dashed paper curves, not heavy-top curve agreement, not
  paper-faithful heavy-top inertia or geometry reconstruction, not a comparison
  pass gate, not a paper timing result, not rendered output evidence, not
  generated-video evidence, not a full paper reproduction, and not any passed
  `experiment.*` claim.
- Phase 54 environment clone/sync scripting is not dependency freshness
  evidence, not solver behavior evidence, not method correctness evidence, not
  paper experiment reproduction, not timing evidence, not comparative baseline
  evidence, not runtime performance evidence, not a full paper reproduction,
  and not any passed `experiment.*` claim.
- Phase 55 heavy-top paper-horizon MABD diagnostic is not a passed heavy-top
  experiment, not a passed M-ABD lane, not paper-horizon stability or accuracy
  evidence, not paper-faithful heavy-top MABD dynamics, not paper-faithful
  heavy-top inertia or geometry reconstruction, not raw curve agreement, not a
  comparison pass gate, not a paper timing result, not rendered-output
  evidence, not generated-video evidence, not a full paper reproduction, and
  not any passed `experiment.*` claim.
- Phase 57 T-handle comparison protocol is not a passed T-handle experiment,
  not a passed M-ABD lane, not paper-faithful T-handle geometry or inertia
  reconstruction, not raw curve agreement, not paper energy-loss agreement, not
  a comparison pass gate, not a paper timing result, not rendered-output
  evidence, not generated-video evidence, not a full paper reproduction, and
  not any passed `experiment.*` claim.
- Phase 58 T-handle paper-figure digitization is not a passed T-handle
  experiment, not a passed M-ABD lane, not authors' raw simulation data, not
  solid/dashed line-style separation, not legend-entry curve identity, not
  paper-faithful T-handle geometry or inertia reconstruction, not raw curve
  agreement, not paper energy-loss agreement, not a comparison pass gate, not a
  paper timing result, not rendered-output evidence, not generated-video
  evidence, not a full paper reproduction, and not any passed `experiment.*`
  claim.
- Phase 61 spinning-box contact diagnostics are not a passed spinning-box
  experiment, not a passed M-ABD lane, not a contact solver, not a collision
  implementation, not paper-faithful affine collision, not a comparison pass
  gate, not a rendered result, not runtime performance evidence, not a full
  paper reproduction, and not any passed `experiment.*` claim.
- Phase 62 spinning-box contact-response diagnostics are not a passed
  spinning-box experiment, not a passed M-ABD lane, not a contact solver, not a
  collision implementation, not an implicit contact solve, not paper-faithful
  affine collision, not a comparison pass gate, not a rendered result, not
  runtime performance evidence, not a full paper reproduction, and not any
  passed `experiment.*` claim.
- Phase 63 spinning-box normal-constraint diagnostics are not a passed
  spinning-box experiment, not a passed M-ABD lane, not a contact solver, not a
  collision implementation, not IPC, not generic inequality-constrained M-ABD
  KKT, not paper-faithful affine collision, not a comparison pass gate, not a
  rendered result, not runtime performance evidence, not a full paper
  reproduction, and not any passed `experiment.*` claim.
- Phase 64 spinning-box decoupled twist diagnostics are not a passed
  spinning-box experiment, not a passed M-ABD lane, not proof of the paper
  solver's private velocity semantics, not paper-faithful M-ABD stepping, not a
  contact solver, not paper-faithful affine collision, not a comparison pass
  gate, not a rendered result, not runtime performance evidence, not a full
  paper reproduction, and not any passed `experiment.*` claim.
- Phase 65 spinning-box paper-figure digitization is not a passed spinning-box
  experiment, not a passed M-ABD lane, not authors' raw simulation data, not
  paper reference legend-entry identity, not solid/dashed line-style
  split, not Newton-vs-paper curve agreement, not paper-faithful M-ABD
  stepping, not a contact solver, not paper-faithful affine collision, not a
  comparison pass gate, not rendered-output inspection evidence, not runtime
  performance evidence, not a full paper reproduction, and not any passed
  `experiment.*` claim.
- Phase 66 spinning-box figure agreement diagnostics are not a passed
  spinning-box experiment, not a passed M-ABD lane, not paper reference
  legend-entry identity, not solid/dashed line-style split, not
  Newton-vs-paper curve agreement, not paper-faithful M-ABD stepping, not a
  contact solver, not paper-faithful affine collision, not a comparison pass
  gate, not rendered-output inspection evidence, not runtime performance
  evidence, not a full paper reproduction, and not any passed `experiment.*`
  claim.
- Phase 67 model-derived point-plane normal constraint rows are not unmodified
  Newton M-ABD support, not a contact solver, not Newton `Contacts` ingestion,
  not collision detection, not active-set generation, not IPC, not generic
  inequality-constrained M-ABD KKT, not paper-faithful affine contact, not
  paper-faithful affine collision/contact, not paper-faithful M-ABD stepping,
  not a comparison pass gate, not rendered-output evidence, not runtime
  performance evidence, not a full paper reproduction, and not any passed
  `experiment.*` claim.
- Phase 72 spinning-box figure momentum endpoint diagnostics are not a passed
  spinning-box experiment, not a passed M-ABD lane, not paper reference
  legend-entry identity, not solid/dashed line-style split, not
  Newton-vs-paper curve agreement, not a comparison pass gate, not rendered
  output inspection, not runtime performance reproduction, not full paper
  reproduction, and not any passed `experiment.*` claim.
- Phase 73 rolling/spinning protocol report lane evidence is not a completed
  rolling/spinning reproduction, not a runtime benchmark, not a passed
  baseline, not rolling-cylinder dynamics evidence, not local runtime timing,
  not implicit/explicit RBD baseline evidence, not comparative baseline
  results, not rendered-output evidence, not full paper reproduction, and not
  any passed `experiment.*` claim.
- Phase 74 rolling-cylinder Newton RBD development baseline evidence is not a
  paper-faithful implicit RBD result, not an explicit RBD result, not M-ABD
  rolling-cylinder evidence, not co-rotated ABD timing evidence, not
  paper-comparable timing evidence, not a completed rolling/spinning
  reproduction, not comparative baseline pass evidence, not full paper
  reproduction, and not any passed `experiment.*` claim.
- Phase 75 rolling-cylinder Newton ExplicitEuler development baseline evidence
  is not a paper-faithful explicit RBD result, not M-ABD rolling-cylinder
  evidence, not co-rotated ABD timing evidence, not paper-comparable timing
  evidence, not a completed rolling/spinning reproduction, not comparative
  baseline pass evidence, not full paper reproduction, and not any passed
  `experiment.*` claim.
- Phase 77 rolling-cylinder finite-stiffness material preflight evidence is not
  a paper-faithful M-ABD rolling-cylinder result, not paper-faithful affine
  collision/contact, not rolling friction/no-slip evidence, not paper-faithful
  explicit or implicit RBD evidence, not co-rotated ABD timing evidence, not
  paper-comparable timing evidence, not a completed rolling/spinning
  reproduction, not comparative baseline pass evidence, not full paper
  reproduction, and not any passed `experiment.*` claim.
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
