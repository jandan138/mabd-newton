# ABD/M-ABD Learning Site Design

Date: 2026-05-17

## Decision

Build a public Astro static course site for ABD and M-ABD foundations inside
`site/`. The site is an original learning guide for developers with programming
experience who are new to affine-body dynamics and physics simulation. It is not
a paper companion, not a paper-claim result, and not evidence that this
repository has completed a full M-ABD implementation or full paper reproduction.

The first implementation should deliver a deployable course skeleton plus a
high-quality first batch of complete lessons. The course must be structured to
expand to 30+ lessons without changing its information architecture.

## Goals

- Teach the prerequisites needed to understand ABD and M-ABD: linear algebra,
  affine maps, rigid-body dynamics, implicit integration, Newton solves, KKT
  systems, constraints, and topology-aware solvers.
- Use a teacherly style with analogies, examples, pseudocode, step cards, and
  warning cards instead of dense textbook prose.
- Reuse the successful site pattern from
  `/cpfs/user/zhuzihou/dev/physics-primitive-agent/site`: Astro, MDX,
  hand-written components, static output, README directory contract, and a
  GitHub Pages workflow.
- Preserve this repository's claim boundaries by making educational content
  visibly separate from verified reproduction evidence.
- Provide a clear route from basic concepts to the current `mabd-newton`
  records, configs, tests, and future Newton-first implementation work.

## Non-Goals

- Do not create a line-by-line paper translation site.
- Do not vendor raw paper PDFs, TeX source, paper figures, videos, or large
  generated media as part of the first site pass.
- Do not claim that unmodified Newton supports affine-body dynamics.
- Do not claim this repository has completed paper-faithful M-ABD scene dynamics,
  comparative baselines, timing results, or full paper reproduction unless a
  dated record and claim entry support the exact statement.
- Do not introduce React, Vue, Svelte, Tailwind, or a component-library
  dependency in the first pass.

## Audience

Primary audience:

- Developers who can program and read array-heavy code.
- Readers who know basic vectors and functions but have not studied physics
  simulation, FEM, rigid-body dynamics, or constrained optimization deeply.
- Project contributors who need to understand why the current reproduction has
  phases, oracle tests, claim records, and incomplete experiment lanes.

Assumed background:

- Python or TypeScript-level programming literacy.
- Basic vectors, matrices, functions, loops, and tests.
- Basic physical intuition for mass, velocity, force, springs, and energy.

The course should fill gaps rather than assume advanced mechanics or numerical
optimization knowledge.

## Site Architecture

Use a self-contained Astro site:

- `site/package.json`: Astro 6, MDX integration, and scripts for `dev`, `build`,
  and `validate`.
- `site/astro.config.mjs`: static output with `site: "https://jandan138.github.io"`
  and `base: "/mabd-newton"`.
- `site/src/layouts/LearnLayout.astro`: page shell with navigation, claim banner,
  and responsive content width.
- `site/src/pages/learn/index.astro`: course home and learning-map entry point.
- `site/src/pages/learn/[slug].astro`: dynamic lesson route from MDX content.
- `site/src/pages/learn/glossary.astro`: glossary landing page.
- `site/src/pages/learn/roadmap.astro`: role-based learning paths.
- `site/src/pages/learn/reproduction-map.astro`: map from concepts to repo
  records, configs, tests, and claim statuses.
- `site/src/content/lessons/*.mdx`: lesson source.
- `site/src/data/lessons.ts`: ordered lesson metadata used by navigation and
  index pages.
- `site/src/data/glossary.ts`: tooltip and glossary terms.
- `site/src/components/`: reusable educational blocks.
- `site/src/styles/learn.css`: site-specific CSS.
- `site/scripts/validate-learning-site.mjs`: site claim/content guard.
- `.github/workflows/deploy-learning-site.yml`: GitHub Pages deployment.

The site is isolated from Python runtime, solver code, experiments, and reports.
It can reference repository records and claim IDs, but it must not mutate or
replace the machine-checkable reproduction pipeline.

## Page Model

Every lesson should follow the learning-guide structure requested by the user:

1. One sentence explaining the problem the lesson solves.
2. Core concepts, each with definition, analogy, and example.
3. Workflow, architecture, or derivation as step cards or a timeline when
   applicable.
4. Practical use cases and comparisons to known techniques.
5. Expanded explanations for details that papers usually mention too quickly,
   including pseudocode where useful.
6. A short "what to remember" summary.
7. Optional exercises or code-reading prompts.

Lesson frontmatter should include:

- `title`
- `description`
- `module`
- `order`
- `status`, initially `complete` for first-batch pages and `planned` for future
  stubs if stubs are added later.
- `claimStatus`, with values such as `conceptual`, `passed`, `incomplete`,
  `not_verified`, or `unsupported`.
- `repoEvidence`, either `none` or paths to dated records and claim IDs.

## Educational Components

Create small, reusable Astro components rather than one-off markup:

- `ConceptCard`: definition, analogy, example.
- `ProblemCard`: one-sentence motivation and why the reader should care.
- `StepFlow`: ordered step cards for algorithms and workflows.
- `CompareGrid`: side-by-side comparisons such as RBD vs FEM vs ABD.
- `PseudoCode`: readable pseudocode block with a short caption.
- `PitfallCard`: common mistakes and claim-boundary warnings.
- `RememberBox`: lesson summary.
- `Term`: wraps important terms with `<abbr>` tooltip text from glossary data.
- `RepoEvidenceCard`: links a concept to `docs/records/` and
  `docs/reference/paper-claims.yaml` without overclaiming.

CSS should use cards, color bands, icons or text glyphs, and clear typography to
avoid a text wall. The design should remain lightweight, responsive, and usable
on desktop and mobile.

## First-Batch Lessons

The first pass should fully write these lessons:

1. `start-here`: course scope, prerequisites, how to read the site, and claim
   boundaries.
2. `why-affine-bodies`: what ABD solves compared with particles, rigid bodies,
   and FEM.
3. `vectors-matrices-transforms`: vectors, matrices, basis changes, and point
   transforms.
4. `affine-state`: `x = A xbar + t`, 12 generalized coordinates, and point
   mapping pseudocode.
5. `svd-polar-rotation`: SVD, polar decomposition, and extracting rotation from
   deformation.
6. `rigid-body-basics`: 6 DOF, rotation, angular velocity, inertia, momentum,
   and why rigid solvers are nonlinear.
7. `generalized-coordinates-forces`: `q`, `qd`, Jacobians, virtual work, and
   `J^T f` force mapping.
8. `implicit-time-stepping`: explicit vs implicit Euler, stability intuition,
   and why robust simulation solves equations.
9. `newton-hessian-kkt`: Newton iteration, Hessians, constraints, Lagrange
   multipliers, and dense KKT intuition.
10. `single-body-abd`: single-body ABD solve, affine mass, co-rotated stiffness,
    polar/no-polar modes, and pseudocode.
11. `multi-body-mabd`: control-point joints, joint ranks, topology cases, and
    why M-ABD needs specialized solvers.
12. `repo-evidence-map`: how the current repository records method oracles,
    incomplete experiment lanes, and claim boundaries.

These 12 pages form a complete minimum course. They also establish component and
writing patterns for later expansion.

## 30+ Lesson Expansion Path

Future lessons should extend the same architecture:

- Affine deformation modes: rotation, scale, shear.
- Coordinate packing and indexing in Newton-facing code.
- Positive definiteness, Cholesky, and stable linear solves.
- Co-rotated elasticity by analogy and by formula.
- Finite-difference oracle checks.
- Dense KKT derivation step by step.
- Residual-corrected lower RHS and paper ambiguity.
- Ball joint worked example.
- Hinge joint worked example.
- Universal joint worked example.
- Prismatic joint worked example.
- Joint limits and clamp penalties.
- Chain block-tridiagonal solve intuition.
- Tree traversal and ABD-ABA motivation.
- Loop Schur complement intuition.
- Graph Gauss-Seidel reconstruction.
- Contact force mapping details.
- Actuation and affine target forces.
- Spinning-box diagnostics.
- RBD baseline caveats.
- Experiment matrices and report schemas.
- Asset/provenance discipline.
- How to add a new verified claim.
- How to add a new experiment lane.
- Common implementation bugs.
- Glossary of symbols.
- Further reading and paper map.

## Claim-Boundary Design

The site must include a persistent banner:

> This site teaches concepts from affine-body dynamics and tracks a Newton-first
> reproduction effort. It is not evidence of a completed full M-ABD
> implementation or full paper reproduction.

Use these wording rules:

- Prefer "conceptual explanation", "development oracle", "incomplete lane",
  "verified by local unit tests only", and "Newton-first reproduction effort".
- Avoid "M-ABD is implemented", "paper-faithful solver", "reproduces the paper",
  "Newton supports affine-body dynamics", "matches paper results", or
  "baseline comparison passed" unless the exact statement links to a dated
  record and claim ID.
- Keep method-unit evidence separate from experiment evidence.
- Treat examples and diagrams as tutorial illustrations unless explicitly tied
  to a record.

The validator should fail on high-risk phrases unless they appear in an approved
boundary-warning context. It should also check that required pages exist, lesson
metadata is complete, and hardcoded deployment paths do not use the wrong base.

## Deployment

Follow the `physics-primitive-agent` GitHub Pages pattern with repository-specific
values:

- Workflow name: `Deploy Learning Site`.
- Trigger on pushes to `main` affecting `.github/workflows/deploy-learning-site.yml`
  or `site/**`, plus `workflow_dispatch`.
- Node version: 22.
- Install with `npm ci` in `site/`.
- Build with `npm run build` in `site/`.
- Upload `site/dist` using `actions/upload-pages-artifact`.
- Deploy with `actions/deploy-pages`.

Document local commands in `site/README.md`:

```bash
npm --prefix site install
npm --prefix site run validate
npm --prefix site run build
npm --prefix site run preview -- --host 127.0.0.1 --port 4321
```

The existing repository gates remain separate:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
git diff --check
```

## Validation And Review

Minimum validation for the first implementation:

- `npm --prefix site run validate`
- `npm --prefix site run build`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py`
- `git diff --check`

Use subagents for review checkpoints when useful:

- Curriculum review: check sequence, missing prerequisites, and whether pages
  are understandable to developers.
- Claim-boundary review: check overclaims and misleading wording.
- Site-architecture review: check Astro structure, deployment base path, and
  validation coverage.

## Open Decisions Resolved

- Delivery format: Astro static site, not a single self-contained HTML file.
- Content scope: complete introductory course, not only a quick reading guide.
- First milestone: 12 complete lessons plus scalable course infrastructure.
- Public visibility: public deployment, with repository claim boundaries still
  enforced.
- User-review checkpoints: replaced by recommended defaults and subagent review
  loops per user instruction to continue without stopping for questions.
