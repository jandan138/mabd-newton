# AI Learning Site Diagram Replacement Design

Date: 2026-05-18

## Decision

Replace the current hand-authored SVG lesson diagrams with AI-generated raster
scientific diagrams. The diagrams should look like polished textbook or paper
teaching figures, not rough wireframes. This pass supersedes the earlier SVG-only
illustration decision for lesson figures.

The site must continue to label every diagram as conceptual teaching material,
not repository evidence of a completed M-ABD implementation or full paper
reproduction.

## Goals

- Replace all 12 low-quality SVG diagrams with higher-quality AI-generated
  scientific diagrams.
- Keep one diagram per existing lesson and preserve the current lesson flow.
- Use precise prompts with explicit formulas, labels, arrows, and composition.
- Preserve claim boundaries in captions, validator metadata, and generated-image
  prompt wording.
- Keep image provenance auditable through a committed prompt manifest.

## Non-Goals

- Do not copy, trace, or restyle any paper figure.
- Do not claim any generated diagram is simulation output, paper evidence, or a
  completed solver result.
- Do not add interactive diagrams or animation.
- Do not change solver, experiment, or report code.
- Do not retain the rough SVG diagrams as public lesson figures.

## Visual Direction

Use AI-generated scientific diagrams with these common requirements:

- 16:9 landscape composition suitable for a lesson header figure.
- Clean white or warm off-white scientific background.
- Crisp vector-like lines, arrows, labels, and formulas.
- Minimal but legible text; only short labels and formulas requested by each
  prompt.
- Consistent color language: orange arrows for transforms/forces/updates, purple
  blocks for solver/KKT/Newton concepts, blue accents for evidence and claim
  boundaries, red only for forbidden-claim guardrails.
- No watermark, logo, paper citation, author names, or decorative text.

## Asset Architecture

Generated images live under `site/src/assets/diagrams/` as PNG files:

1. `learning-roadmap.png`
2. `modeling-spectrum.png`
3. `matrix-grid-transform.png`
4. `affine-state-map.png`
5. `polar-decomposition.png`
6. `rigid-vs-affine-dof.png`
7. `jacobian-force-map.png`
8. `implicit-residual-loop.png`
9. `kkt-block-system.png`
10. `single-abd-pipeline.png`
11. `mabd-topology-solver-map.png`
12. `evidence-funnel.png`

The old SVG files with the same basenames should be deleted once the PNG
replacements are wired into MDX.

`site/src/components/Figure.astro` must accept:

- `kind="diagram"`
- `provenance="ai-generated-raster"`
- `claimStatus="conceptual"` or `claimStatus="not_evidence"`

The component continues to render Astro-imported image metadata through a lazy
`<img>` with caption and data attributes.

## Provenance Manifest

Add `site/src/assets/diagrams/ai-diagram-manifest.json` with one entry per image:

- `file`: PNG filename.
- `lesson`: lesson slug.
- `prompt`: exact prompt sent to image generation.
- `provenance`: `ai-generated-raster`.
- `claimStatus`: `conceptual`.
- `reviewNotes`: concise post-generation review result.

The manifest is a small committed text artifact. It documents generation intent
without treating generated images as scientific evidence.

## Per-Lesson Diagram Intent

1. `start-here`: concept -> formula -> code -> evidence learning path with a
   claim-boundary checkpoint.
2. `why-affine-bodies`: modeling spectrum from particle to rigid body to affine
   body to multi-affine body to FEM.
3. `vectors-matrices-transforms`: basis vectors and a grid transformed by a
   matrix.
4. `affine-state`: rest shape mapped to world shape by `x_world = A x_rest + t`
   and packed as `q in R^12`.
5. `svd-polar-rotation`: affine matrix `A` decomposed into rotation `R` and
   stretch/shear `S`.
6. `rigid-body-basics`: rigid 6 DOF compared with affine 12-number state.
7. `generalized-coordinates-forces`: `dx = J dq`, `v = J qdot`, and
   `tau = J^T f` force mapping.
8. `implicit-time-stepping`: next-state guess, residual evaluation, correction,
   convergence loop.
9. `newton-hessian-kkt`: KKT block matrix with `H`, `G^T`, `G`, `0`, `delta q`,
   `lambda`, `-r`, and `-C`.
10. `single-body-abd`: single affine-body pipeline from state to mass/material
    response to scoped CPU oracle evidence.
11. `multi-body-mabd`: chain, tree, loop, graph topology sketches plus a block
    sparsity/solver-path cue.
12. `repo-evidence-map`: claim map, dated records, test/report, boundary gate,
    allowed claim, and forbidden claim.

## Validation Rules

Extend `site/scripts/validate-learning-site.mjs` so it checks:

- Lesson figures import from `../../assets/diagrams/*.png` or `.webp`; this pass
  will use `.png`.
- Figure provenance must be `ai-generated-raster` for these generated raster
  lesson diagrams.
- Figure `claimStatus` remains `conceptual` or `not_evidence`.
- Every required lesson still has at least one `Figure` with `alt`, `caption`,
  `kind`, `provenance`, and `claimStatus`.
- The manifest exists and includes every imported AI diagram file.
- Forbidden raw paper or generated run extensions remain blocked.
- Existing unsupported-claim phrase checks continue to scan MDX and captions.

## Review Process

Use `codex-imagegen-bridge` to generate images. After each batch, run review
subagents to check:

- Text/formulas are legible enough for a lesson figure.
- Diagram content matches the lesson intent.
- No image implies paper reproduction, paper matching, complete M-ABD solver
  status, or external baseline success.
- File names, imports, captions, and manifest entries match.

If a generated image has severe formula/text errors or weak composition, retry
that image with a shorter, more explicit prompt. If a second retry still fails,
use a hybrid fallback: generated scientific background plus site caption/alt text
for the exact formula explanation.

## Verification

Required checks after implementation:

- `npm --prefix site run validate`
- `npm --prefix site run build`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py`
- `git diff --check`
- Public URL smoke test after merge and deploy.
