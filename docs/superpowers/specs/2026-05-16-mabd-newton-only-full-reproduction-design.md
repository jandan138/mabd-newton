# M-ABD Newton-Only Full Reproduction Design

Date: 2026-05-16

## Decision

This repository will reproduce "M-ABD: Scalable, Efficient, and Robust
Multi-Affine-Body Dynamics" with a Newton-first implementation. The primary
physics implementation will vendor the local Newton source tree, modify it
inside this repository, and add M-ABD as a first-class Newton solver.

The project target remains A+B:

- A: implement the paper method without reducing the algorithmic scope.
- B: reproduce the paper evidence without silently dropping experiments,
  baselines, assets, metrics, or timing claims.

The phrase "full reproduction" is a final verified status, not a current repo
claim.

## Evidence Levels

The project has two evidence layers:

1. `mabd_only_physics_reproduction`: the Newton fork implements the M-ABD method
   and validates it against method-level oracles and paper scenes using the
   M-ABD lane.
2. `full_paper_evidence_reproduction`: every paper claim that depends on an
   external baseline, asset, timing number, or qualitative failure mode is
   reproduced or explicitly marked incomplete with evidence.

The primary M-ABD implementation is Newton-only. External MuJoCo, Bullet, PhysX,
and VQ lanes are not part of the M-ABD implementation, but they are required to
verify the paper's comparative evidence. If those baselines are disallowed or
unavailable, the affected full-paper claims must be `incomplete`, not `passed`.

## Source Material

Primary paper sources:

- SIGGRAPH 2026 schedule page:
  https://s2026.conference-schedule.org/presentation/?id=papers_116&sess=sess102
- arXiv abstract page:
  https://arxiv.org/abs/2603.08079
- arXiv PDF:
  https://arxiv.org/pdf/2603.08079
- arXiv TeX source:
  https://arxiv.org/e-print/2603.08079

Local source copies used during design review:

- Paper PDF: `/tmp/mabd-paper/mabd.pdf`
- Paper PDF sha256:
  `a594e79093673c60fc59ad14f9b71f29a8f7f8e7b1c3d9c73efe6f5814cc6ec0`
- Paper TeX source archive: `/tmp/mabd-paper/mabd-source.tar`
- Paper TeX source sha256:
  `73ec398956c606dec2f8f40f0d38b9d5370e11b27830775e1b3765fe0efc563f`
- Extracted TeX source: `/tmp/mabd-paper/source/`
- Local Newton source: `/cpfs/user/zhuzihou/dev/newton`
- Local Newton source commit:
  `96713fa965463b69c229a4d30582c733ff3526bb`
- Local Newton source status at review time: clean against `origin/main`
- Reference project style: `/cpfs/user/zhuzihou/dev/physics-primitive-agent`

The durable repo must create `docs/reference/paper-claims.yaml` before
experiment implementation. It must map every figure, table, and text claim to
source path, source line, expected value, unit, conflict note, and reproduction
status. Known example: the ragdoll timing differs between Table 1 and the
experiment text, so both claims must be represented separately.

## License And Provenance

The project must add a root license before code implementation.

Vendored Newton requirements:

- Copy Newton's Apache-2.0 license files and third-party license inventory.
- Add `vendor/newton/PROVENANCE.md` with upstream URL, source commit, source
  dirty status, copy date, copy command, local patch policy, license inventory,
  and a command showing `import newton` resolves to `vendor/newton`.
- Preserve required copyright and license notices.
- Add prominent modified-file notices where Apache-2.0 requires them.

Paper source requirements:

- Do not vendor arXiv PDF, TeX text, figures, or rendered assets unless the
  license permits it and the copied files are listed in a manifest.
- Store paper checksums and source URLs in docs and records.
- Use short quotations only where needed; implementation docs should paraphrase
  paper methods and cite source paths/line numbers.

## Claim Boundary

The repo must split claims into three states:

- `current`: what exists in the repository today.
- `intended`: planned work from this spec.
- `verified`: results backed by a dated record, command, config, source hash,
  artifact path, and metric threshold.

Current claim:

- This repository contains a reviewed design for a Newton-first M-ABD
  reproduction.

Intended claim:

- This repository will vendor Newton and implement a paper-faithful `SolverMABD`
  plus reproduction harnesses.

No verified method or experiment claim exists until the corresponding record is
created. The repo must add `docs/reference/claim-boundaries.md` as the source of
truth before implementation.

The repo must not claim:

- That unmodified Newton already supports M-ABD.
- That existing Newton rigid-body solvers are equivalent to M-ABD.
- That a derived rigid `body_q` proxy is paper-faithful affine collision.
- That generic inequality constraints are solved by M-ABD KKT.
- That comparative paper baselines are verified unless their adapters are
  installed, run, and recorded.
- That CPU timing is comparable to the paper unless the benchmark protocol and
  hardware/threading status match the claim being made.

## Phase Gates

Implementation must proceed through explicit gates:

- Phase 0: repo bootstrap, license/provenance, vendored Newton import isolation,
  docs validator, claim-boundary doc, and source manifests.
- Phase 1: single-body ABD with dense CPU oracles, co-rotated solve, polar and
  no-polar modes, and invariant tests.
- Phase 2: control-point joints, paper-faithful joint gradient mode, and dense
  primal/dual KKT oracle on small systems.
- Phase 3: topology solvers: chain block tridiagonal, tree ABD-ABA, loop Schur
  complement, and graph reconstruction with direct dense validation.
- Phase 4: selected paper scenes with complete configs, assets, metrics, and
  M-ABD lane evidence.
- Phase 5: full paper evidence matrix, including required external baseline
  lanes or explicit `incomplete` statuses for unavailable comparative claims.

Each phase needs exit criteria, commands, records, and a commit before the next
phase starts.

## Repository Layout

Planned structure:

- `vendor/newton/`: copied Newton source from `/cpfs/user/zhuzihou/dev/newton`.
- `src/mabd_reproduction/`: Python orchestration, config loading, report
  contracts, paper claim tools, and experiment runners.
- `configs/experiments/`: one config per figure/table claim or claim family.
- `assets/manifests/`: asset source, license, checksum, and reconstruction
  manifests.
- `tests/`: orchestration tests and report/config schema tests.
- `vendor/newton/newton/tests/`: vendored Newton `unittest` tests for low-level
  M-ABD solver and kernel invariants.
- `docs/reference/`: claim boundaries, paper equation maps, source claim maps,
  and implementation boundary notes.
- `docs/records/`: dated records with command, environment, seed, source hash,
  metrics, and artifact paths.
- `reports/`: generated tables, figures, JSON summaries, and raw time series.

Initial bootstrap files before solver implementation:

- `AGENTS.md`
- `.gitignore`
- `pyproject.toml`
- `docs/reference/claim-boundaries.md`
- `docs/reference/paper-claims.yaml`
- `docs/records/README.md`
- `reports/README.md`
- `scripts/validate_docs.py`
- `vendor/newton/PROVENANCE.md`

The project will reuse the useful discipline from
`physics-primitive-agent`: claim boundaries, config-driven runs, dataclass report
contracts, focused tests, docs validation, and dated records. It will not reuse
its long single-CLI pattern or accumulated one-off experiment switches.

## Newton Integration

M-ABD will be implemented inside the vendored Newton tree:

- Internal module: `vendor/newton/newton/_src/solvers/mabd/`
- Internal package export: `vendor/newton/newton/_src/solvers/__init__.py`
- Public solver export: `vendor/newton/newton/solvers.py`
- Public class: `newton.solvers.SolverMABD`
- API docs update path: `vendor/newton/docs/generate_api.py`
- Solver support table update: `vendor/newton/newton/solvers.py`

Examples, docs, and reproduction code must use public Newton APIs. Vendored
Newton unit tests may import `newton._src` for low-level kernel and solver
invariant coverage, matching existing Newton test practice.

`SolverMABD.register_custom_attributes(builder)` is required before adding
M-ABD entities or finalizing a model. The detailed attribute table must be added
during Phase 0 and include namespace, assignment, frequency, dtype, shape, and
default. Required namespaces:

- `mabd:body`: affine body material and static model parameters.
- `mabd:state`: affine coordinates, velocities, residuals, and diagnostics.
- `mabd:constraint`: solver-owned joint/graph edges. This is independent of
  Newton articulation trees and supports loops and dense graphs.
- `mabd:control`: affine generalized forces, target parameters, and actuation.
- `mabd:contact`: optional force reporting produced by `SolverMABD`.

Newton articulations may be used for import convenience or rigid baselines, but
M-ABD topology is owned by `mabd:constraint`.

## M-ABD State And Caches

Each affine body state stores:

- Affine coordinate `q in R12`, stacking the three columns of `A` and
  translation `t`.
- Affine velocity `qd in R12`.
- Runtime diagnostics: residual norm, energy, momentum, constraint violation,
  iteration count, and per-step timing.

Static model data stores:

- Generalized mass matrix `M_A`.
- Rest generalized stiffness matrix `K_A_bar`.
- Control tetrahedron transform `T` and inverse `T^-1`.
- Material parameters: density, Young's modulus, Poisson ratio, damping, and
  scene-specific penalty parameters.

`H_A_bar = M_A / dt^2 + K_A_bar` is not a static body attribute. It is a
`SolverMABD` cache keyed by `dt`, material state, device/backend, and model
version. The cache must rebuild on `dt` changes and on `notify_model_changed()`.

The existing Newton `State.body_q` is not the M-ABD source of truth. It is a
derived rigid proxy only. The spec requires an explicit lane choice per scene:

- `rigid_proxy`: derive a rigid transform from affine state for Newton
  rendering/collision. This is an approximation and must be labeled as such.
- `affine_kernel`: implement M-ABD-specific affine render/contact kernels for
  paper-faithful affine geometry handling.

If `rigid_proxy` is used, the runner must sync `mabd.q -> state.body_q` before
`model.collide()` and after `SolverMABD.step()`.

## Core Solver Components

Single-body ABD requirements:

- ABD kinematics `x_i = A xbar_i + t`.
- Constant rest-shape coordinate Jacobian `J`.
- Co-rotated stiffness using rest generalized stiffness `K_A_bar`.
- RHS assembly through the volume-weighted `Jbar^T f` map.
- Linear-elastic `dPsi/dA` using Lame parameters derived from Young's modulus
  and Poisson ratio.
- Polar-decomposition rotation mode.
- No-polar length-normalized per-block mode matching the paper algorithm.
- Twist-wrench maps `G(A)` and `E(A)`.
- Virtual-work mapping from spatial wrench to affine force.
- `f_A = f_A_ext + (1 / dt) M_A qd`.
- Tests for `G(A) E(A) = I`, virtual work consistency, and the paper's no
  explicit gyroscopic term cancellation.

Joint constraints:

- Control-point coordinate mapping `y = T q` and `q = T^-1 y`.
- Ball, hinge, universal, and prismatic joints.
- Paper-faithful minimal-rank nonlinear constraints:
  ball rank 3, hinge rank 5, universal rank 4, prismatic rank 5.
- Linear higher-rank variants only as validation or fallback paths.
- Universal joint note: the equation/source matrix uses rank 4, while the paper
  figure caption appears inconsistent. The reproduction follows the equation and
  records the inconsistency in `paper-claims.yaml`.

Joint gradient modes:

- `paper_faithful`: use `R_H`, `R_U`, and `R_P`; include `dC/dR_joint`; use the
  `R ~= A` semi-linearized rotation-gradient approximation; apply the
  skew-symmetrization rule; keep the reduced rotation-gradient entries specified
  by the paper.
- `finite_difference_oracle`: validation-only mode for small tests.

Dual KKT:

- Global dual-space Schur solve.
- Support both the paper-simplified lower RHS and the residual-corrected lower
  RHS `-C(q_n)`. Each run records which mode is used.
- Chain block-tridiagonal solve.
- Tree ABD-ABA condensation and downward local KKT solve.
- Loop handling via low-rank Schur complement around loop breakers.
- Dense graph multidirectional block Gauss-Seidel as an inferred
  reconstruction, with schedule, chain decomposition, stopping criteria, and
  tolerance recorded. Small and moderate graph cases must compare against direct
  dense dual solves.

Joint limits and compliance:

- Implement the paper's strain-limiting clamp for out-of-range joint DOFs.
- Add the explicit dual-space penalty RHS term for clamped limits.
- Store stiffness, damping, and range parameters per scene.
- Keep this separate from generic contact inequalities.

Contact and inequality handling:

- Newton `Contacts` geometry may be consumed, but `Contacts` does not provide
  impulses from collision generation.
- `SolverMABD` computes experiment-specific penalty/contact generalized forces.
- `SolverMABD.update_contacts()` writes force reports only when requested.
- Contact buffer overflow must be checked after collision generation.
- Scene contact is paper-faithful only when source parameters are known;
  otherwise it is a recorded reconstruction.
- The project must not claim a general inequality-constrained M-ABD KKT solver.

Actuation:

- `SolverMABD` must define how `Control.joint_f`, joint targets, drives, and
  scene scripts map into affine generalized forces.
- Franka, ragdoll, and robot-like scenes cannot be marked verified until this
  mapping exists and is tested.

## Experiment Reproduction Contracts

Every figure/table/text claim needs a config and a claim entry.

Experiment config schema must include:

- `claim_ids`
- `geometry`
- `asset_manifest`
- `materials`
- `joints`
- `initial_state`
- `forces`
- `actuation`
- `contact`
- `duration`
- `time_step_grid`
- `solver_budget`
- `backend`
- `random_seed`
- `metrics`
- `paper_claims`
- `output_paths`

Asset manifests must include:

- source URI or local path
- license
- checksum
- geometry counts or skeleton counts
- reconstruction script and seed if procedural
- status: `paper_asset`, `procedural_reconstruction`, `approximation`,
  `missing`
- whether the asset can count toward full paper evidence

Approximations may support development, but they cannot verify a paper scene.

Required scene families:

- ABD vs RBD rolling/spinning body timing modes.
- Spinning box momentum and energy diagnostics.
- T-handle intermediate-axis instability.
- Heavy top precession and nutation.
- Physical pendulum angle and joint-force comparison to analytic reference.
- Heavy-end chain robustness test.
- Hanging ball-joint net, net with cylinder, and scaling to 20x20, 50x50, and
  100x100.
- Pulley system and huge pulley stress test.
- Willow and pear tree hierarchy tests.
- Net cloak scene.
- Armadillo coupling scene.
- Ragdoll-on-net scene.
- Falling mixed joints with ball, universal, hinge, and prismatic pairs.
- Franka pick-and-place M-ABD scene.
- Protein chain reconstruction scene.

Table 1 metadata is necessary but insufficient. Single-body and qualitative
experiments must also encode initial conditions, references, boundary
conditions, scene duration, and metric thresholds. Paper-missing values must be
represented as `not_applicable` or `unknown_in_source`, not invented.

## Baseline Policy

The M-ABD implementation lane is mandatory and Newton-only.

Full paper evidence requires the comparative baselines that the paper uses for
each claim:

- ABD/RBD/RK4/analytic single-body references where applicable.
- MuJoCo equality and articulated configurations where applicable.
- Bullet configurations where applicable.
- PhysX configurations where applicable.
- VQ configurations where applicable.

Baseline lane schema:

- engine name and version
- model construction path
- solver options
- time step
- iteration count
- warmup policy
- termination and failure criteria
- raw logs
- output metrics and artifacts

If a baseline dependency is missing during normal M-ABD work, the affected
baseline claim is `incomplete`. If a run is invoked with `--require-baseline`,
missing dependencies are command failures.

## Metrics And Acceptance Thresholds

Each claim must define expected metrics before it can be verified.

Required metric families:

- Momentum drift.
- Energy loss or energy drift.
- Angle or trajectory RMSE.
- Phase error against analytic or RK4 reference.
- Precession/nutation curve error.
- T-handle flip timing and angular-velocity waveform error.
- Max and RMS constraint residual.
- Max joint gap.
- Max penetration or contact violation where contact is part of the claim.
- NaN/divergence/crash criteria.
- Solver iteration count.
- Per-step timing distribution.
- Required plot and raw time-series artifacts.

Qualitative paper claims must be converted into measurable thresholds where
possible. Where this is impossible, the report must mark the claim as
`qualitative_reconstruction` and include the basis for review.

## Timing Protocol

Timing claims must record:

- solver-only vs end-to-end scope
- warmup and JIT exclusion
- measured step count
- mean, median, standard deviation, min, max, and p95
- CPU model, core affinity, thread count, and BLAS/Warp/CUDA settings
- GPU model and driver when GPU is used
- render and I/O inclusion or exclusion
- backend: CPU, Warp CPU, CUDA, or other
- comparability status: `paper_comparable`, `backend_comparable`,
  `not_comparable`, or `development_only`

Paper CPU timings cannot be claimed as reproduced by a GPU or different backend
without a `not_comparable` or `backend_comparable` label.

## Report Schema And Statuses

Machine-readable reports must include:

- `claim_id`
- `scene_id`
- `asset_hashes`
- `solver_mode`
- `backend`
- `baseline_lane`
- `expected`
- `observed`
- `threshold`
- `unit`
- `status`
- `failure_reason`
- `timing_distribution`
- `raw_outputs`
- `plot_paths`
- `source_commit`
- `vendored_newton_commit`
- `paper_source_version`

Statuses:

- `passed`: required lane ran and met thresholds.
- `failed`: required lane ran and violated thresholds.
- `incomplete`: required evidence is missing, including unavailable required
  baselines or assets for full paper evidence.
- `not_verified`: optional development lane was skipped or unavailable.
- `unsupported`: requested scope is outside the paper-faithful implementation
  boundary.
- `qualitative_reconstruction`: qualitative evidence was reconstructed but does
  not meet the bar for numeric verification.

Mandatory M-ABD lane errors fail the command. Optional development lanes may
produce `not_verified`. Full evidence claims use `incomplete` for missing
required assets or baselines.

## Data Flow

1. A paper claim entry selects a figure/table/text claim and source lines.
2. A config file selects the scene, solver mode, backend, seed, material values,
   contact policy, baseline lanes, and output paths.
3. The builder calls `SolverMABD.register_custom_attributes(builder)`.
4. The builder creates Newton bodies plus M-ABD body and constraint attributes.
5. The runner synchronizes derived rigid proxies if the scene uses
   `rigid_proxy` contact/render.
6. `SolverMABD` advances affine state and writes diagnostics.
7. Optional baseline lanes run with their own recorded configs.
8. The runner writes JSON, raw time series, plots, and a dated record.

## Error Handling

Runs fail when:

- Required paper metadata is missing from a config.
- A scene requests an unsupported M-ABD joint or solver feature.
- M-ABD graph data is inconsistent.
- Hessian factorization fails.
- Constraint residuals exceed configured thresholds.
- Contact buffers overflow.
- A required baseline is missing under `--require-baseline`.
- A required asset for full paper evidence is missing.

Runs do not fail merely because optional development baselines are unavailable;
they produce `not_verified` for that optional lane.

## Testing Strategy

Use Newton's `unittest` style for vendored Newton tests and focused Python tests
for orchestration. Low-level vendored tests may import `newton._src`; examples,
docs, and reproduction runners must use public APIs.

Required tests:

- ABD kinematics and Jacobian consistency.
- Co-rotation identities.
- `Jbar^T f` RHS assembly checks.
- Lame-parameter linear elasticity checks.
- Polar and no-polar force rotation checks.
- `G(A) E(A) = I`.
- Virtual-work force mapping.
- No explicit gyroscopic term cancellation.
- Mass and stiffness symmetry/positive-definiteness.
- Control tetrahedron `q <-> y` bijection.
- Paper-faithful joint residual and gradient checks.
- Finite-difference oracle comparisons for small joints.
- Residual-corrected KKT lower RHS.
- Global dual KKT vs direct primal KKT on small systems.
- Chain block-Thomas vs dense dual solve.
- Tree ABD-ABA vs dense dual solve on small trees.
- Loop Schur complement vs dense solve on small loop systems.
- Graph Gauss-Seidel vs dense dual solve on controlled fixtures.
- Joint limit clamp and dual penalty RHS.
- Contact force mapping in scenes that use contact.
- Actuation mapping for robot-like scenes.
- Experiment config schema.
- Asset manifest schema.
- Paper claim manifest schema.
- Report schema.

Large-scale performance tests are benchmark commands, not normal unit tests.
They must write dated records.

Planned verification commands after bootstrap:

- `python scripts/validate_docs.py`
- `python -m unittest discover -s tests`
- `PYTHONPATH=vendor/newton python -m newton.tests -k mabd`
- benchmark commands only through explicit experiment runners

CPU/GPU tolerances must be defined per metric before a test can claim
verification.

## Verification Records

Every reproduction run must record:

- Git commit for this repo.
- Vendored Newton source commit and local patch status.
- Paper source version: arXiv `2603.08079v2`.
- Command and config path.
- Python, Warp, CUDA/GPU, CPU, and OS information.
- Backend device and threading settings.
- Random seed.
- Scene scale and paper target row.
- Asset manifest status and checksums.
- Baseline lane statuses.
- Residual tolerance and achieved residual.
- Iteration count and timing distribution.
- Output artifact paths.

## Risks

Performance comparability remains the largest risk. The paper reports a
single-thread CPU Eigen/MKL implementation, while Newton is GPU/Warp-first. A
Newton-only solver can reproduce method behavior, but timing claims must be
labeled by backend. Strict CPU timing requires a CPU-oriented path and a matching
benchmark protocol.

Scene asset availability is the second risk. The paper TeX source includes
rendered figures but not necessarily all simulation assets or trajectories.
Procedural reconstructions must be labeled as such and cannot verify paper
asset claims unless the manifest proves equivalence.

Contact coupling is the third risk. The paper focuses on equality joint
constraints and lists general inequality constraints as future work. The
reproduction will implement experiment-specific contact behavior but will not
claim a general inequality-constrained M-ABD solver.

Graph solver fidelity is a fourth risk. The paper describes dense graph
Gauss-Seidel at a high level. The implementation must record inferred schedule
choices and validate small cases against direct dense solves.

## Approval State

The user approved the Newton-only, fork-first design direction on 2026-05-16.
After multi-agent review, this revision tightens the spec so implementation
cannot proceed by silently narrowing the A+B reproduction target.
