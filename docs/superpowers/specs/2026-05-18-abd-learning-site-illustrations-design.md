# ABD Learning Site Illustrations Design

Date: 2026-05-18

## Decision

Add a first illustration pass to the public ABD/M-ABD learning site. The first
pass will add one deterministic SVG teaching diagram to each of the 12 existing
lessons, plus a reusable figure component and validation rules for figure
quality, asset provenance, and deployment-safe paths.

The first pass will not use generated raster images. Raster images generated via
`codex-imagegen-bridge` are reserved for a later hero/atmosphere pass after the
precise teaching diagrams are in place.

## Goals

- Make every existing lesson visually teachable, not just text/card based.
- Use precise vector diagrams for math, dynamics, constraints, topology, and
  evidence structure.
- Keep diagrams original, small, reviewable, and compatible with the existing
  Astro/MDX static site.
- Preserve claim boundaries: diagrams are conceptual teaching aids unless a
  specific repository record says otherwise.
- Avoid paper-figure copying and avoid generated images that imply paper results
  or solver outputs.

## Non-Goals

- Do not copy, trace, or vendor paper figures.
- Do not generate raster images in this first pass.
- Do not add interactive simulations or animation.
- Do not claim any diagram is paper experiment evidence.
- Do not change solver, experiment, or report behavior.

## Visual System

The diagram style should match a warm technical notebook:

- Warm cream panel background.
- Dark brown geometry lines.
- Orange arrows for transforms, forces, and updates.
- Purple blocks for solver/KKT/Newton concepts.
- Blue blocks for evidence/records/claim boundaries.
- Coral warning accents only for unsupported-claim guardrails.
- Simple orthographic or isometric shapes.
- Minimal text inside SVGs; labels are short symbols such as `A`, `t`, `q`,
  `J`, `J^T f`, `H`, `G`, and `lambda`.

SVG diagrams should not contain long explanations. Every diagram must have an
`alt` text and caption in the MDX page.

## Site Architecture

Add:

- `site/src/components/Figure.astro`: the only component lessons use to render
  diagrams.
- `site/src/assets/diagrams/*.svg`: deterministic SVG source assets.

`Figure.astro` props:

- `src`: imported Astro image asset.
- `alt`: required string.
- `caption`: required string.
- `kind`: `diagram` for this first pass.
- `provenance`: `authored-svg` for this first pass.
- `claimStatus`: `conceptual` or `not_evidence`.

The component should render a `<figure>` with an optimized `<img>`, a caption,
and data attributes for validation. It should use lazy loading and avoid
root-relative paths.

## First-Pass Diagram Set

Add these 12 diagrams:

1. `learning-roadmap.svg` for `start-here.mdx`: concept -> formula -> code ->
   evidence flow, with a boundary marker that says the site is not proof.
2. `modeling-spectrum.svg` for `why-affine-bodies.mdx`: particle, rigid body,
   affine body, FEM mesh, and linked affine bodies.
3. `matrix-grid-transform.svg` for `vectors-matrices-transforms.mdx`: a 2D
   grid and colored basis arrows before and after a matrix transform.
4. `affine-state-map.svg` for `affine-state.mdx`: `x_rest` mapped by `A` and
   shifted by `t`, plus a compact `q in R12` packing strip.
5. `polar-decomposition.svg` for `svd-polar-rotation.mdx`: deformed grid split
   into extracted rotation and remaining stretch/shear.
6. `rigid-vs-affine-dof.svg` for `rigid-body-basics.mdx`: rigid 6 DOF controls
   versus affine 12 DOF controls.
7. `jacobian-force-map.svg` for `generalized-coordinates-forces.mdx`: point
   force `f` mapped through `J^T f` into generalized-coordinate knobs, with the
   reverse `J qd` velocity relation.
8. `implicit-residual-loop.svg` for `implicit-time-stepping.mdx`: explicit
   overshoot versus implicit guess, residual, correction loop.
9. `kkt-block-system.svg` for `newton-hessian-kkt.mdx`: KKT matrix blocks `H`,
   `G^T`, `G`, `0`, unknowns `dq`, `lambda`, and residual sources.
10. `single-abd-pipeline.svg` for `single-body-abd.mdx`: affine state, mass,
    material stiffness, polar/no-polar branch, dense CPU oracle, scoped evidence.
11. `mabd-topology-solver-map.svg` for `multi-body-mabd.mdx`: chain, tree,
    loop, graph topology sketches and matching sparse matrix patterns.
12. `evidence-funnel.svg` for `repo-evidence-map.mdx`: concept page, claim map,
    dated record, test/report, allowed claim, and forbidden-claim guardrail.

## Validation Rules

Extend `site/scripts/validate-learning-site.mjs` so it checks:

- Every required lesson imports and uses `Figure` at least once.
- Every `Figure` call includes `alt`, `caption`, `kind`, `provenance`, and
  `claimStatus` props.
- Every first-pass figure uses `kind="diagram"`, `provenance="authored-svg"`,
  and `claimStatus="conceptual"` or `claimStatus="not_evidence"`.
- Every diagram import resolves to `site/src/assets/diagrams/*.svg`.
- No MDX lesson uses root-relative image paths.
- No site asset under `site/src/assets/` uses forbidden raw paper extensions such
  as `.pdf`, `.tex`, `.mp4`, `.mov`, `.avi`, `.log`, `.usd`, `.usda`, `.usdc`.
- Existing claim-boundary phrase checks continue to scan captions and MDX.

## Claim Boundary Rules

- Captions must describe diagrams as conceptual unless linked to scoped evidence.
- Diagrams must not depict paper experiment output, timing, or visual matching as
  if reproduced.
- Topology diagrams may explain chain, tree, loop, and graph concepts, but must
  not imply paper ABD-ABA performance or complete graph solver equivalence.
- Single-body diagrams may show scoped CPU oracle evidence, but must not imply a
  production-ready full M-ABD solver.

## Later Raster Pass

A later pass may use `codex-imagegen-bridge` for non-mathematical hero images:

- Course hero illustration.
- Affine body intuition illustration.
- Matrix transform machine metaphor.
- Solver workshop metaphor.
- Evidence archive metaphor.

Raster prompts must require no text, no equations, no labels, no watermarks, and
no paper-figure style. Raster assets need provenance metadata before public
deployment.

## Verification

Required checks after implementation:

- `npm --prefix site run validate`
- `npm --prefix site run build`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py`
- `git diff --check`
- Public URL smoke test after merge and deploy.
