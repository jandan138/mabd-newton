# ABD Learning Site Illustrations Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add one precise SVG teaching diagram to each existing ABD/M-ABD learning-site lesson and validate figure quality, provenance, and deployment-safe paths.

**Architecture:** Keep diagrams as small authored SVG assets under `site/src/assets/diagrams/`. Render all figures through one `Figure.astro` component so captions, alt text, lazy loading, and claim-boundary metadata stay consistent. Extend the existing Node validator to require figure metadata and prevent broken or unsafe asset usage.

**Tech Stack:** Astro 6, MDX, authored SVG, TypeScript-flavored Astro components, Node validation script, GitHub Pages.

---

## File Structure

- Create: `site/src/components/Figure.astro` for all lesson figures.
- Create: `site/src/assets/diagrams/learning-roadmap.svg`.
- Create: `site/src/assets/diagrams/modeling-spectrum.svg`.
- Create: `site/src/assets/diagrams/matrix-grid-transform.svg`.
- Create: `site/src/assets/diagrams/affine-state-map.svg`.
- Create: `site/src/assets/diagrams/polar-decomposition.svg`.
- Create: `site/src/assets/diagrams/rigid-vs-affine-dof.svg`.
- Create: `site/src/assets/diagrams/jacobian-force-map.svg`.
- Create: `site/src/assets/diagrams/implicit-residual-loop.svg`.
- Create: `site/src/assets/diagrams/kkt-block-system.svg`.
- Create: `site/src/assets/diagrams/single-abd-pipeline.svg`.
- Create: `site/src/assets/diagrams/mabd-topology-solver-map.svg`.
- Create: `site/src/assets/diagrams/evidence-funnel.svg`.
- Modify: `site/src/styles/learn.css` for figure panel styling.
- Modify: `site/scripts/validate-learning-site.mjs` for figure validation.
- Modify all 12 files under `site/src/content/lessons/*.mdx` to import and render one diagram each.

## Task 1: Figure Component And Validator Red Test

**Files:**
- Create: `site/src/components/Figure.astro`
- Modify: `site/src/styles/learn.css`
- Modify: `site/scripts/validate-learning-site.mjs`

- [ ] **Step 1: Add validator requirement before adding figures**

Modify `site/scripts/validate-learning-site.mjs` so every MDX lesson must contain `<Figure` and every `Figure` call must include these string props:

```text
alt=
caption=
kind="diagram"
provenance="authored-svg"
claimStatus=
```

Also require each MDX file that uses `Figure` to import SVG assets only from `../../assets/diagrams/*.svg`, and reject forbidden asset extensions under `site/src/assets/`.

- [ ] **Step 2: Run validator and confirm RED**

Run: `npm --prefix site run validate`

Expected: FAIL with messages that existing lessons are missing `<Figure`.

- [ ] **Step 3: Create `site/src/components/Figure.astro`**

Use this implementation shape:

```astro
---
interface Props {
  src: ImageMetadata;
  alt: string;
  caption: string;
  kind: "diagram";
  provenance: "authored-svg";
  claimStatus: "conceptual" | "not_evidence";
}

const { src, alt, caption, kind, provenance, claimStatus } = Astro.props;
---

<figure
  class="lesson-figure"
  data-figure-kind={kind}
  data-provenance={provenance}
  data-claim-status={claimStatus}
>
  <img src={src.src} width={src.width} height={src.height} alt={alt} loading="lazy" decoding="async" />
  <figcaption>{caption}</figcaption>
</figure>
```

- [ ] **Step 4: Add figure CSS**

Append styles to `site/src/styles/learn.css`:

```css
.lesson-figure {
  background: #fffaf3;
  border: 1px solid #ead5bc;
  border-radius: 18px;
  box-shadow: 0 16px 36px rgba(57, 32, 16, 0.08);
  margin: 28px 0;
  overflow: hidden;
}

.lesson-figure img {
  display: block;
  height: auto;
  width: 100%;
}

.lesson-figure figcaption {
  border-top: 1px solid #ead5bc;
  color: #6f5a49;
  font-size: 14px;
  line-height: 1.6;
  padding: 12px 16px;
}
```

- [ ] **Step 5: Run validator again**

Run: `npm --prefix site run validate`

Expected: still FAIL because lessons do not yet render figures.

## Task 2: Add First Six SVG Diagrams And Lesson Wiring

**Files:**
- Create six SVG files for lessons 1-6.
- Modify first six MDX lesson files.

- [ ] **Step 1: Create first six authored SVGs**

Create these files, each as a standalone `<svg width="960" height="540" viewBox="0 0 960 540" role="img" xmlns="http://www.w3.org/2000/svg">` with warm background, concise labels, and no external assets:

- `site/src/assets/diagrams/learning-roadmap.svg`
- `site/src/assets/diagrams/modeling-spectrum.svg`
- `site/src/assets/diagrams/matrix-grid-transform.svg`
- `site/src/assets/diagrams/affine-state-map.svg`
- `site/src/assets/diagrams/polar-decomposition.svg`
- `site/src/assets/diagrams/rigid-vs-affine-dof.svg`

Use only inline SVG elements: `rect`, `circle`, `line`, `path`, `polygon`, `text`, `marker`, and `g`. Keep text labels short.

- [ ] **Step 2: Wire `start-here.mdx`**

Add imports:

```mdx
import Figure from "../../components/Figure.astro";
import learningRoadmap from "../../assets/diagrams/learning-roadmap.svg";
```

Add near the top after `ProblemCard`:

```mdx
<Figure
  src={learningRoadmap}
  alt="Concept, formula, code, and evidence connected as a learning path with a claim-boundary checkpoint"
  caption="Conceptual learning map: diagrams guide understanding, while repository records define what is actually verified."
  kind="diagram"
  provenance="authored-svg"
  claimStatus="conceptual"
/>
```

- [ ] **Step 3: Wire lessons 2-6**

Repeat the same import pattern for each lesson:

- `why-affine-bodies.mdx` imports `modelingSpectrum` and captions the modeling spectrum as conceptual.
- `vectors-matrices-transforms.mdx` imports `matrixGridTransform` and captions matrix columns/basis vectors.
- `affine-state.mdx` imports `affineStateMap` and captions `x_world = A x_rest + t` and `q in R12` as conceptual.
- `svd-polar-rotation.mdx` imports `polarDecomposition` and captions rotation/stretch separation.
- `rigid-body-basics.mdx` imports `rigidVsAffineDof` and captions 6 DOF versus 12 DOF.

- [ ] **Step 4: Run validator and build**

Run: `npm --prefix site run validate`

Expected: FAIL only for lessons 7-12 missing figures.

Run: `npm --prefix site run build`

Expected: PASS.

## Task 3: Add Last Six SVG Diagrams And Lesson Wiring

**Files:**
- Create six SVG files for lessons 7-12.
- Modify last six MDX lesson files.

- [ ] **Step 1: Create last six authored SVGs**

Create these files using the same SVG dimensions and style vocabulary:

- `site/src/assets/diagrams/jacobian-force-map.svg`
- `site/src/assets/diagrams/implicit-residual-loop.svg`
- `site/src/assets/diagrams/kkt-block-system.svg`
- `site/src/assets/diagrams/single-abd-pipeline.svg`
- `site/src/assets/diagrams/mabd-topology-solver-map.svg`
- `site/src/assets/diagrams/evidence-funnel.svg`

- [ ] **Step 2: Wire lessons 7-12**

Add `Figure` imports and diagram imports to:

- `generalized-coordinates-forces.mdx`
- `implicit-time-stepping.mdx`
- `newton-hessian-kkt.mdx`
- `single-body-abd.mdx`
- `multi-body-mabd.mdx`
- `repo-evidence-map.mdx`

Every caption must include either `Conceptual` or `概念图`, and must not claim paper reproduction or solver completion.

- [ ] **Step 3: Run full site checks**

Run: `npm --prefix site run validate`

Expected: `learning site validation passed`.

Run: `npm --prefix site run build`

Expected: Astro build succeeds and still builds 17 pages.

Run: `git diff --check`

Expected: no output.

## Task 4: Review, Commit, Merge, And Deploy

**Files:**
- All changed files from Tasks 1-3.

- [ ] **Step 1: Dispatch final reviews**

Request three reviews:

- Diagram accuracy review: check mathematical arrows, labels, and topology diagrams.
- Claim-boundary review: check captions and diagrams do not imply paper results.
- Site/deploy review: check imported assets build under `/mabd-newton` and validator covers figure risks.

- [ ] **Step 2: Apply review fixes**

Use `apply_patch` for any targeted fixes. Do not change unrelated files.

- [ ] **Step 3: Run final verification**

Run:

```bash
npm --prefix site run validate
npm --prefix site run build
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
```

Expected: all pass.

- [ ] **Step 4: Commit and push feature branch**

Commit message:

```text
feat: add learning site diagrams
```

Push branch and create PR to `main`.

- [ ] **Step 5: Merge and verify deployed site**

Merge PR after checks pass. Wait for `Deploy Learning Site` to finish. Verify:

```text
https://jandan138.github.io/mabd-newton/learn/
```

Expected: public page includes lesson diagrams and returns non-404 content.

## Self-Review Notes

- Spec coverage: figure component, 12 SVG assets, MDX wiring, validator rules,
  claim boundaries, and deployment verification are covered.
- Scope: raster image generation is intentionally excluded from this first pass.
- Type consistency: `Figure.astro` props match validator-required MDX props.
- Placeholder scan: plan contains no unresolved placeholders for required work.
