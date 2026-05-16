# M-ABD Newton-Only Full Reproduction Design

Date: 2026-05-16

## Decision

This repository will reproduce "M-ABD: Scalable, Efficient, and Robust
Multi-Affine-Body Dynamics" using a Newton-only implementation path. The project
will vendor the local Newton source tree, modify it inside this repository, and
add M-ABD as a first-class Newton solver instead of building an independent
Eigen/MKL simulator.

The reproduction target is both method-complete and experiment-complete:

- Implement the M-ABD method: co-rotated single-body ABD, control-point joint
  constraints, dual-space KKT, and topology-specialized solvers for chains,
  trees, loops, and dense graphs.
- Reproduce the paper experiments and reported metrics, including the single-body
  benchmarks, multibody robustness tests, and Table 1 scale/timing scenes.

## Source Material

Primary sources:

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
- Paper TeX source archive: `/tmp/mabd-paper/mabd-source.tar`
- Extracted TeX source: `/tmp/mabd-paper/source/`
- Local Newton source: `/cpfs/user/zhuzihou/dev/newton`
- Reference project style: `/cpfs/user/zhuzihou/dev/physics-primitive-agent`

## Claim Boundary

The primary claim is: this repo implements and evaluates an M-ABD reproduction
inside a vendored Newton fork.

The repo must not claim:

- That unmodified Newton already supports M-ABD.
- That existing Newton rigid-body solvers are equivalent to M-ABD.
- That generic inequality constraints are solved by M-ABD KKT. The paper itself
  lists inequality constraints as a limitation.
- That MuJoCo, Bullet, PhysX, or VQ baselines have been reproduced unless their
  adapters are installed, run, and recorded with versioned reports.
- That CPU timing is directly comparable to the paper if the implementation runs
  on a different Newton/Warp execution backend.

## Repository Layout

The project will use a small, evidence-oriented structure:

- `vendor/newton/`: copied Newton source from `/cpfs/user/zhuzihou/dev/newton`.
- `src/mabd_reproduction/`: Python orchestration, configs, report contracts, and
  experiment runners that use the vendored Newton package.
- `configs/experiments/`: one configuration per paper experiment or benchmark
  family.
- `tests/`: unit and regression tests for formulas, solver invariants, and
  experiment contracts.
- `docs/reference/`: paper notes, equation maps, and implementation boundary
  notes.
- `docs/records/`: dated reproduction records with command, environment, seed,
  source hash, metrics, and artifact paths.
- `reports/`: generated tables, figures, and machine-readable run summaries.

The repo will copy the useful project discipline from
`physics-primitive-agent`: claim boundaries, config-driven runs, dataclass report
contracts, focused tests, and dated records. It will not copy its long single
CLI style or its accumulated one-off experiment switches.

## Newton Integration

M-ABD will be implemented inside the vendored Newton tree:

- Internal module:
  `vendor/newton/newton/_src/solvers/mabd/`
- Public solver export:
  `vendor/newton/newton/solvers.py`
- Public class:
  `newton.solvers.SolverMABD`

Examples, tests, and reproduction code must import public Newton APIs only. They
must not import from `newton._src`, matching Newton's local `AGENTS.md`.

The solver will extend Newton rather than wrap an external engine. Newton will
provide model construction, world grouping, shape/contact infrastructure, viewer
support, USD utilities where useful, and test conventions. M-ABD will provide
its own affine state, joint residuals, dual variables, and solver path.

## M-ABD State Model

Each affine body stores:

- Affine coordinate `q in R12`, stacking the three columns of `A` and translation
  `t`.
- Affine velocity `qd in R12`.
- Generalized mass matrix `M_A`.
- Rest generalized stiffness matrix `K_A_bar`.
- Pre-factorized per-body Hessian `H_A_bar = M_A / h^2 + K_A_bar`.
- Control tetrahedron transform `T` and inverse `T^-1`.
- Material parameters: density, Young's modulus, Poisson ratio, and damping
  options needed by the reproduction scenes.
- Runtime diagnostics: residual norm, energy, momentum, constraint violation,
  iteration count, and per-step timing.

The existing Newton `body_q` transform is not the source of truth for M-ABD. It
is a rendering/contact bridge derived from the affine state when needed.

## Core Solver Components

Single-body ABD:

- Implement ABD kinematics `x_i = A xbar_i + t`.
- Implement co-rotated stiffness and the constant pre-factorized solve.
- Support both polar-decomposition and no-polar length-normalized paths.
- Map spatial wrenches to affine forces and affine increments back to diagnostic
  rigid transforms.

Joint constraints:

- Implement control-point coordinate mapping.
- Implement ball, hinge, universal, and prismatic joints.
- Support paper-faithful minimal-rank nonlinear constraints:
  ball rank 3, hinge rank 5, universal rank 4, prismatic rank 5.
- Keep implementation-friendly linear variants where needed for validation, but
  mark them as validation paths when not used in paper-faithful experiments.

Dual KKT:

- Implement global dual-space Schur solve.
- Implement chain block-tridiagonal solve.
- Implement tree ABD-ABA condensation and downward local KKT solve.
- Implement loop handling via low-rank Schur complement around loop breakers.
- Implement dense graph multidirectional block Gauss-Seidel.

Contact and inequality handling:

- Reuse Newton contact generation where practical.
- Convert contact impulses or penalty forces to affine generalized forces.
- Implement the paper's experiment-level implicit penalty/contact behavior.
- Report generic inequality KKT as outside the reproduced method scope.

## Experiment Reproduction Scope

The experiment harness must reproduce:

- Rolling/spinning single body comparison, including the ABD vs RBD timing modes.
- Spinning box momentum and energy diagnostics.
- T-handle intermediate-axis instability.
- Heavy top precession and nutation.
- Physical pendulum angle and joint-force comparison to analytic reference.
- Heavy-end chain robustness test.
- Ball-joint nets: hanging net, net with cylinder, and scaling to 20x20, 50x50,
  and 100x100.
- Pulley system and huge pulley stress test.
- Willow and pear tree hierarchy tests.
- Net cloak scene.
- Armadillo coupling scene at the level supported by Newton assets/contact path.
- Ragdoll-on-net scene.
- Falling mixed joints scene with ball, universal, hinge, and prismatic pairs.
- Franka pick-and-place M-ABD scene.
- Protein chain reconstruction scene.

Table 1 targets from the paper source will be encoded as expected experiment
metadata, including link count, constraint count, time step, residual tolerance,
iteration count, Young's modulus, and reported per-step timing.

## Baseline Policy

The M-ABD lane is mandatory and Newton-only.

External baseline lanes are optional and separately labeled:

- MuJoCo, Bullet, PhysX, and VQ comparisons may be implemented as adapters only
  when their dependencies are available.
- Missing baseline dependencies produce a `not_verified` report entry.
- No baseline result may be inferred from the paper figures or text.

Newton's existing Featherstone, XPBD, VBD, MuJoCo, and SemiImplicit solvers may
be used for internal comparison, debugging, or Newton-native baselines. They do
not count as reproducing the paper's MuJoCo/Bullet/PhysX/VQ baselines unless the
corresponding external backend is actually run.

## Data Flow

1. A config file selects a paper experiment, solver mode, scale, backend device,
   random seed, material values, and output paths.
2. The experiment builder creates a Newton model plus M-ABD custom attributes or
   M-ABD-specific model buffers.
3. `SolverMABD` advances the affine state and writes diagnostics.
4. Optional Newton collision/viewer systems consume derived body transforms.
5. The runner writes JSON and Markdown reports under `reports/` and
   `docs/records/`.
6. Plot scripts generate paper-aligned figures from recorded run outputs.

## Error Handling

Runs must fail loudly when:

- Required paper metadata is missing from a config.
- A scene requests a joint type not supported by `SolverMABD`.
- The affine Hessian factorization fails.
- Constraint residuals exceed the configured tolerance after the configured
  iteration budget.
- Contact buffers overflow.
- A requested external baseline backend is unavailable.

Reports must distinguish:

- `passed`: run completed and met configured residual/metric thresholds.
- `failed`: run completed but violated thresholds.
- `not_verified`: dependency, asset, or backend was unavailable.
- `unsupported`: requested scope is outside the paper-faithful implementation
  boundary.

## Testing Strategy

Use Newton's `unittest` style for vendored Newton tests and focused Python tests
for orchestration.

Required tests:

- ABD kinematics and Jacobian consistency.
- Co-rotation identities and polar/no-polar force rotation sanity checks.
- Mass and stiffness symmetry/positive-definiteness checks.
- Control tetrahedron `q <-> y` bijection.
- Joint residual and Jacobian finite-difference checks.
- Global dual KKT vs direct primal KKT on small systems.
- Chain block-Thomas vs dense dual solve.
- Tree ABD-ABA vs dense dual solve on small trees.
- Loop Schur complement vs dense solve on small loop systems.
- Graph Gauss-Seidel residual monotonicity on controlled fixtures.
- Single-body benchmark invariants: linear momentum, angular momentum trend, and
  energy diagnostics.
- Experiment config schema and report schema tests.

Large-scale performance tests are not ordinary unit tests. They run through
explicit benchmark commands and write dated records.

## Verification Records

Every reproduction run must record:

- Git commit or source hash for this repo and vendored Newton.
- Paper source version: arXiv `2603.08079v2`.
- Command and config path.
- Python, Warp, CUDA/GPU, CPU, and OS information.
- Backend device and threading settings.
- Random seed.
- Scene scale and paper target row.
- Residual tolerance and achieved residual.
- Iteration count and timing summary.
- Output artifact paths.

## Risks

The largest risk is performance comparability. The paper reports a single-thread
CPU Eigen/MKL implementation, while Newton is GPU/Warp-first. A Newton-only
solver can faithfully reproduce the method and physics, but timing claims must
be labeled by backend. If strict CPU timing is required, the vendored Newton fork
will need a CPU-oriented path using Newton-compatible APIs or Warp CPU kernels,
and the report must compare against the actual local CPU.

The second risk is scene asset availability. The paper TeX source includes
figures but not necessarily all simulation assets. Scene generators must
procedurally rebuild the reported structures where possible, and unavailable
artist assets must be recorded as reconstructed approximations rather than
silent substitutes.

The third risk is contact coupling. The paper's M-ABD contribution focuses on
equality joint constraints, while contact and inequality constraints are a
known limitation. The reproduction will implement the contact behavior required
by reported scenes but will not claim a general inequality-constrained M-ABD
solver.

## Approval State

The user approved the Newton-only, fork-first design direction on 2026-05-16.
Implementation must wait for the written spec review gate before the detailed
implementation plan is created.
