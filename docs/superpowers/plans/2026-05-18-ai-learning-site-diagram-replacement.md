# AI Learning Site Diagram Replacement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the 12 rough SVG lesson figures with AI-generated scientific PNG diagrams while preserving claim boundaries and deployability.

**Architecture:** The site keeps the existing `Figure.astro` component pattern, but lesson figures move from `authored-svg` assets to `ai-generated-raster` PNG assets. The validator becomes the gate for PNG/WebP diagram imports, AI provenance metadata, and manifest coverage. A committed manifest records prompts and review notes for every generated image.

**Tech Stack:** Astro, MDX, Node validation script, imported static image assets, `codex-imagegen-bridge` via Codex CLI `$imagegen`.

---

## File Map

- Modify `site/src/components/Figure.astro`: allow `provenance="ai-generated-raster"`.
- Modify `site/scripts/validate-learning-site.mjs`: allow PNG/WebP diagram imports, require generated-raster provenance, validate manifest coverage.
- Modify `site/src/content/lessons/*.mdx`: switch imports from `.svg` to `.png` and `provenance="ai-generated-raster"`.
- Delete `site/src/assets/diagrams/*.svg`: remove low-quality hand-authored diagrams from public lesson use.
- Create `site/src/assets/diagrams/*.png`: 12 AI-generated scientific diagrams.
- Create `site/src/assets/diagrams/ai-diagram-manifest.json`: generation prompt/provenance manifest.

---

## Shared Image Prompt Requirements

Every Codex `$imagegen` request must include this common text:

```text
Create a polished scientific textbook diagram for an ABD/M-ABD learning website. Use a 16:9 landscape composition, clean warm off-white background, crisp vector-like arrows, short legible labels, precise formulas, and professional typography. Use orange arrows for transforms/forces/updates, purple solver blocks, blue evidence/boundary accents, and red only for forbidden-claim guardrails. Do not copy or imitate any paper figure. Do not show simulation screenshots or paper result plots. Do not imply a completed M-ABD solver or full paper reproduction. No watermark, logo, citation, author name, or decorative extra text.
```

Use the installed Codex CLI form:

```bash
codex exec \
  -C "$PWD" \
  --skip-git-repo-check \
  --sandbox workspace-write \
  -o "site/src/assets/diagrams/<name>.png.transcript.txt" \
  - <<'EOF'
Use $imagegen in default built-in tool mode.

Generate one raster image from this prompt:
<PROMPT>

Save or copy the final selected image to this exact path:
site/src/assets/diagrams/<name>.png

Constraints:
- Use the built-in image_gen tool through $imagegen.
- Do not use scripts/image_gen.py.
- Do not use imagegen CLI fallback mode.
- Do not require OPENAI_API_KEY.
- Do not leave the only usable output under CODEX_HOME.
- After saving, report the final path.
EOF
```

After each generated image, run:

```bash
test -s "site/src/assets/diagrams/<name>.png"
```

Do not commit transcript files.

---

### Task 1: Validator And Component Support

**Files:**
- Modify: `site/src/components/Figure.astro`
- Modify: `site/scripts/validate-learning-site.mjs`

- [ ] **Step 1: Verify current validator rejects generated-raster metadata**

Temporarily change one lesson import and provenance in the working tree only:

```diff
-import learningRoadmap from "../../assets/diagrams/learning-roadmap.svg";
+import learningRoadmap from "../../assets/diagrams/learning-roadmap.png";
...
-  provenance="authored-svg"
+  provenance="ai-generated-raster"
```

Run:

```bash
npm --prefix site run validate
```

Expected: FAIL with messages requiring `authored-svg` and `../../assets/diagrams/*.svg`, proving the current gate rejects the new desired behavior.

- [ ] **Step 2: Revert the temporary MDX change**

Restore the lesson to `.svg` and `authored-svg` before editing validator/component.

- [ ] **Step 3: Update `Figure.astro` type**

Change the provenance prop to:

```astro
provenance: "authored-svg" | "ai-generated-raster";
```

- [ ] **Step 4: Update validator constants and import gate**

In `site/scripts/validate-learning-site.mjs`, replace the SVG-only regex with PNG/WebP support for lesson figures:

```js
const allowedFigureAssetImport = /^\.\.\/\.\.\/assets\/diagrams\/[^/]+\.(?:png|webp)$/;
const requiredAiFigureProvenance = "ai-generated-raster";
```

Update checks so a lesson Figure requires `provenance="ai-generated-raster"` and error text says assets must come from `../../assets/diagrams/*.png` or `*.webp`.

- [ ] **Step 5: Add manifest coverage validation**

Add functions that read `src/assets/diagrams/ai-diagram-manifest.json`, parse JSON, and verify every imported PNG/WebP diagram has a manifest entry with:

```json
{
  "file": "learning-roadmap.png",
  "lesson": "start-here",
  "provenance": "ai-generated-raster",
  "claimStatus": "conceptual"
}
```

If the manifest is missing after PNG/WebP imports exist, emit:

```text
site/src/assets/diagrams/ai-diagram-manifest.json: missing AI diagram manifest
```

- [ ] **Step 6: Verify expected RED until assets/manifest are replaced**

Run:

```bash
npm --prefix site run validate
```

Expected at this intermediate point: current SVG lessons fail because validator now expects generated raster diagrams. Proceed to image replacement tasks.

---

### Task 2: Generate And Wire Lessons 1-4

**Files:**
- Create: `site/src/assets/diagrams/learning-roadmap.png`
- Create: `site/src/assets/diagrams/modeling-spectrum.png`
- Create: `site/src/assets/diagrams/matrix-grid-transform.png`
- Create: `site/src/assets/diagrams/affine-state-map.png`
- Modify: first four matching MDX lessons
- Modify/Create: `site/src/assets/diagrams/ai-diagram-manifest.json`
- Delete after PNG exists: four matching SVG files

- [ ] **Step 1: Generate `learning-roadmap.png`**

Prompt body:

```text
Create a polished scientific textbook diagram for an ABD/M-ABD learning website. Use a 16:9 landscape composition, clean warm off-white background, crisp vector-like arrows, short legible labels, precise formulas, and professional typography. Use orange arrows for transforms/forces/updates, purple solver blocks, blue evidence/boundary accents, and red only for forbidden-claim guardrails. Do not copy or imitate any paper figure. Do not show simulation screenshots or paper result plots. Do not imply a completed M-ABD solver or full paper reproduction. No watermark, logo, citation, author name, or decorative extra text.

Diagram content: a left-to-right learning roadmap with four large labeled stations: "Concept", "Formula", "Code", "Evidence". Connect them with arrows. Add a blue checkpoint labeled "Claim boundary" after Evidence. Include small icons: lightbulb, equation sheet, code brackets, archive record. Keep all labels exact and short.
```

- [ ] **Step 2: Generate `modeling-spectrum.png`**

Prompt body:

```text
Create a polished scientific textbook diagram for an ABD/M-ABD learning website. Use a 16:9 landscape composition, clean warm off-white background, crisp vector-like arrows, short legible labels, precise formulas, and professional typography. Use orange arrows for transforms/forces/updates, purple solver blocks, blue evidence/boundary accents, and red only for forbidden-claim guardrails. Do not copy or imitate any paper figure. Do not show simulation screenshots or paper result plots. Do not imply a completed M-ABD solver or full paper reproduction. No watermark, logo, citation, author name, or decorative extra text.

Diagram content: a modeling spectrum axis from left to right labeled "few state" to "many states". Show five clean icons labeled exactly: "Particle", "Rigid", "Affine", "Multi-affine", "FEM". Particle is a point, Rigid is a cube with rotate arrow, Affine is a sheared cube, Multi-affine is linked sheared blocks, FEM is a fine mesh cube. Add a subtle highlight around "Affine" as the middle representation.
```

- [ ] **Step 3: Generate `matrix-grid-transform.png`**

Prompt body:

```text
Create a polished scientific textbook diagram for an ABD/M-ABD learning website. Use a 16:9 landscape composition, clean warm off-white background, crisp vector-like arrows, short legible labels, precise formulas, and professional typography. Use orange arrows for transforms/forces/updates, purple solver blocks, blue evidence/boundary accents, and red only for forbidden-claim guardrails. Do not copy or imitate any paper figure. Do not show simulation screenshots or paper result plots. Do not imply a completed M-ABD solver or full paper reproduction. No watermark, logo, citation, author name, or decorative extra text.

Diagram content: left panel shows a square grid with basis arrows labeled "e1" and "e2". Center shows a matrix block labeled "A" with arrow. Right panel shows a sheared/scaled grid with transformed basis arrows labeled "A e1" and "A e2". Add formula "x' = A x" at the top. Keep labels exact.
```

- [ ] **Step 4: Generate `affine-state-map.png`**

Prompt body:

```text
Create a polished scientific textbook diagram for an ABD/M-ABD learning website. Use a 16:9 landscape composition, clean warm off-white background, crisp vector-like arrows, short legible labels, precise formulas, and professional typography. Use orange arrows for transforms/forces/updates, purple solver blocks, blue evidence/boundary accents, and red only for forbidden-claim guardrails. Do not copy or imitate any paper figure. Do not show simulation screenshots or paper result plots. Do not imply a completed M-ABD solver or full paper reproduction. No watermark, logo, citation, author name, or decorative extra text.

Diagram content: show a rest-space shape on the left labeled "x_rest". Show a 3x3 matrix block labeled "A" applying rotation, stretch, and shear, then an orange translation arrow labeled "t" to a world-space sheared shape labeled "x_world". Include formula exactly: "x_world = A x_rest + t". Add a small packing strip labeled "q in R^12 = [A, t]".
```

- [ ] **Step 5: Wire lessons 1-4**

Update these imports from `.svg` to `.png` and change provenance to `ai-generated-raster`:

```text
start-here.mdx -> learning-roadmap.png
why-affine-bodies.mdx -> modeling-spectrum.png
vectors-matrices-transforms.mdx -> matrix-grid-transform.png
affine-state.mdx -> affine-state-map.png
```

- [ ] **Step 6: Update manifest entries for lessons 1-4**

Create or extend `site/src/assets/diagrams/ai-diagram-manifest.json` with exact prompts and entries for the four generated files. Use `reviewNotes` initially as `"Generated and pending batch review."`.

- [ ] **Step 7: Delete replaced SVGs for lessons 1-4**

Delete:

```text
learning-roadmap.svg
modeling-spectrum.svg
matrix-grid-transform.svg
affine-state-map.svg
```

- [ ] **Step 8: Run validation and build**

Run:

```bash
npm --prefix site run validate
npm --prefix site run build
git diff --check
```

Expected: validation may still fail for lessons 5-12 until all are converted, but no failures should mention lessons 1-4. Build should pass if imports resolve.

---

### Task 3: Generate And Wire Lessons 5-8

**Files:**
- Create: `site/src/assets/diagrams/polar-decomposition.png`
- Create: `site/src/assets/diagrams/rigid-vs-affine-dof.png`
- Create: `site/src/assets/diagrams/jacobian-force-map.png`
- Create: `site/src/assets/diagrams/implicit-residual-loop.png`
- Modify: matching MDX lessons
- Modify: `site/src/assets/diagrams/ai-diagram-manifest.json`
- Delete after PNG exists: four matching SVG files

- [ ] **Step 1: Generate `polar-decomposition.png`**

Prompt body:

```text
Create a polished scientific textbook diagram for an ABD/M-ABD learning website. Use a 16:9 landscape composition, clean warm off-white background, crisp vector-like arrows, short legible labels, precise formulas, and professional typography. Use orange arrows for transforms/forces/updates, purple solver blocks, blue evidence/boundary accents, and red only for forbidden-claim guardrails. Do not copy or imitate any paper figure. Do not show simulation screenshots or paper result plots. Do not imply a completed M-ABD solver or full paper reproduction. No watermark, logo, citation, author name, or decorative extra text.

Diagram content: show an affine transform block labeled "A" splitting into two branches labeled "R" and "S". The R branch shows a pure rotated square/cube labeled "rotation". The S branch shows stretch/shear grid labeled "stretch + shear". Include formula exactly: "A = R S". Keep labels exact and short.
```

- [ ] **Step 2: Generate `rigid-vs-affine-dof.png`**

Prompt body:

```text
Create a polished scientific textbook diagram for an ABD/M-ABD learning website. Use a 16:9 landscape composition, clean warm off-white background, crisp vector-like arrows, short legible labels, precise formulas, and professional typography. Use orange arrows for transforms/forces/updates, purple solver blocks, blue evidence/boundary accents, and red only for forbidden-claim guardrails. Do not copy or imitate any paper figure. Do not show simulation screenshots or paper result plots. Do not imply a completed M-ABD solver or full paper reproduction. No watermark, logo, citation, author name, or decorative extra text.

Diagram content: split into two panels. Left panel labeled "Rigid: 6 DOF" with cube, three translation arrows, three rotation arcs. Right panel labeled "Affine: 12 numbers" with sheared cube, matrix block "A: 9" and vector "t: 3". Include small labels "translate", "rotate", "stretch", "shear".
```

- [ ] **Step 3: Generate `jacobian-force-map.png`**

Prompt body:

```text
Create a polished scientific textbook diagram for an ABD/M-ABD learning website. Use a 16:9 landscape composition, clean warm off-white background, crisp vector-like arrows, short legible labels, precise formulas, and professional typography. Use orange arrows for transforms/forces/updates, purple solver blocks, blue evidence/boundary accents, and red only for forbidden-claim guardrails. Do not copy or imitate any paper figure. Do not show simulation screenshots or paper result plots. Do not imply a completed M-ABD solver or full paper reproduction. No watermark, logo, citation, author name, or decorative extra text.

Diagram content: show generalized coordinates "q" as control knobs on the left, a Jacobian block "J" in the center, and a world point with force arrow "f" on the right. Include formulas exactly: "dx = J dq", "v = J qdot", "tau = J^T f". Show the reverse mapping from point force back to generalized force with an orange arrow labeled "virtual work".
```

- [ ] **Step 4: Generate `implicit-residual-loop.png`**

Prompt body:

```text
Create a polished scientific textbook diagram for an ABD/M-ABD learning website. Use a 16:9 landscape composition, clean warm off-white background, crisp vector-like arrows, short legible labels, precise formulas, and professional typography. Use orange arrows for transforms/forces/updates, purple solver blocks, blue evidence/boundary accents, and red only for forbidden-claim guardrails. Do not copy or imitate any paper figure. Do not show simulation screenshots or paper result plots. Do not imply a completed M-ABD solver or full paper reproduction. No watermark, logo, citation, author name, or decorative extra text.

Diagram content: show a loop with four nodes labeled exactly "guess q_next", "evaluate forces", "residual r(q_next)", "correction delta q". Arrows form a loop back to guess. Add final arrow to "accept step" when "|r| small". Use purple for residual/correction and orange for iteration arrows.
```

- [ ] **Step 5: Wire lessons 5-8, manifest, and delete SVGs**

Update imports/provenance for:

```text
svd-polar-rotation.mdx -> polar-decomposition.png
rigid-body-basics.mdx -> rigid-vs-affine-dof.png
generalized-coordinates-forces.mdx -> jacobian-force-map.png
implicit-time-stepping.mdx -> implicit-residual-loop.png
```

Add manifest entries and delete matching SVG files.

- [ ] **Step 6: Run validation and build**

Run:

```bash
npm --prefix site run validate
npm --prefix site run build
git diff --check
```

Expected: validation may still fail for lessons 9-12 until all are converted, but no failures should mention lessons 1-8. Build should pass if imports resolve.

---

### Task 4: Generate And Wire Lessons 9-12

**Files:**
- Create: `site/src/assets/diagrams/kkt-block-system.png`
- Create: `site/src/assets/diagrams/single-abd-pipeline.png`
- Create: `site/src/assets/diagrams/mabd-topology-solver-map.png`
- Create: `site/src/assets/diagrams/evidence-funnel.png`
- Modify: matching MDX lessons
- Modify: `site/src/assets/diagrams/ai-diagram-manifest.json`
- Delete after PNG exists: four matching SVG files

- [ ] **Step 1: Generate `kkt-block-system.png`**

Prompt body:

```text
Create a polished scientific textbook diagram for an ABD/M-ABD learning website. Use a 16:9 landscape composition, clean warm off-white background, crisp vector-like arrows, short legible labels, precise formulas, and professional typography. Use orange arrows for transforms/forces/updates, purple solver blocks, blue evidence/boundary accents, and red only for forbidden-claim guardrails. Do not copy or imitate any paper figure. Do not show simulation screenshots or paper result plots. Do not imply a completed M-ABD solver or full paper reproduction. No watermark, logo, citation, author name, or decorative extra text.

Diagram content: central KKT block matrix with exact labels "H", "G^T", "G", "0". Unknown vector labeled "delta q" and "lambda". Right-hand side labeled "-r" and "-C". Add side callouts "motion" near H and "constraints" near G. Make the matrix readable and precise.
```

- [ ] **Step 2: Generate `single-abd-pipeline.png`**

Prompt body:

```text
Create a polished scientific textbook diagram for an ABD/M-ABD learning website. Use a 16:9 landscape composition, clean warm off-white background, crisp vector-like arrows, short legible labels, precise formulas, and professional typography. Use orange arrows for transforms/forces/updates, purple solver blocks, blue evidence/boundary accents, and red only for forbidden-claim guardrails. Do not copy or imitate any paper figure. Do not show simulation screenshots or paper result plots. Do not imply a completed M-ABD solver or full paper reproduction. No watermark, logo, citation, author name, or decorative extra text.

Diagram content: pipeline with blocks labeled exactly "state q = [A,t]", "mass M", "material force", "dense CPU oracle", "scoped evidence". Show an affine block/cube above the pipeline. Add a small blue boundary label "conceptual only". Do not depict a completed production solver.
```

- [ ] **Step 3: Generate `mabd-topology-solver-map.png`**

Prompt body:

```text
Create a polished scientific textbook diagram for an ABD/M-ABD learning website. Use a 16:9 landscape composition, clean warm off-white background, crisp vector-like arrows, short legible labels, precise formulas, and professional typography. Use orange arrows for transforms/forces/updates, purple solver blocks, blue evidence/boundary accents, and red only for forbidden-claim guardrails. Do not copy or imitate any paper figure. Do not show simulation screenshots or paper result plots. Do not imply a completed M-ABD solver or full paper reproduction. No watermark, logo, citation, author name, or decorative extra text.

Diagram content: four topology sketches labeled exactly "chain", "tree", "loop", "graph". The loop must be a closed cycle of at least three bodies. The graph must show multiple connected bodies. Below them show a small block-sparse matrix pattern and arrow labeled "solver path". Add caption-like text inside image: "topology -> sparsity". Keep it conceptual.
```

- [ ] **Step 4: Generate `evidence-funnel.png`**

Prompt body:

```text
Create a polished scientific textbook diagram for an ABD/M-ABD learning website. Use a 16:9 landscape composition, clean warm off-white background, crisp vector-like arrows, short legible labels, precise formulas, and professional typography. Use orange arrows for transforms/forces/updates, purple solver blocks, blue evidence/boundary accents, and red only for forbidden-claim guardrails. Do not copy or imitate any paper figure. Do not show simulation screenshots or paper result plots. Do not imply a completed M-ABD solver or full paper reproduction. No watermark, logo, citation, author name, or decorative extra text.

Diagram content: evidence funnel from top to bottom with stages labeled exactly "claim map", "dated record", "test/report", "boundary gate", "allowed claim". On the side show a red blocked path labeled "forbidden claim" with an X. Use blue for valid evidence path and red only for forbidden path.
```

- [ ] **Step 5: Wire lessons 9-12, manifest, and delete SVGs**

Update imports/provenance for:

```text
newton-hessian-kkt.mdx -> kkt-block-system.png
single-body-abd.mdx -> single-abd-pipeline.png
multi-body-mabd.mdx -> mabd-topology-solver-map.png
repo-evidence-map.mdx -> evidence-funnel.png
```

Add manifest entries and delete matching SVG files.

- [ ] **Step 6: Run full site validation**

Run:

```bash
npm --prefix site run validate
npm --prefix site run build
git diff --check
```

Expected: all pass.

---

### Task 5: Review, Verify, Commit, Merge, Deploy

**Files:**
- Review all changed files.

- [ ] **Step 1: Run final verification**

Run:

```bash
npm --prefix site run validate
npm --prefix site run build
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
git diff --check
```

Expected: all pass.

- [ ] **Step 2: Dispatch final reviews**

Run review subagents for:

```text
1. Visual/content quality of the 12 generated diagrams.
2. Claim-boundary compliance for captions, prompts, metadata, and image labels.
3. Site/deploy readiness for imported raster assets.
```

Fix any Important or Critical findings, then re-run final verification.

- [ ] **Step 3: Commit implementation**

Inspect status, diff, and recent log. Stage only intended files and commit:

```bash
git add docs/superpowers/plans/2026-05-18-ai-learning-site-diagram-replacement.md \
  docs/superpowers/specs/2026-05-18-ai-learning-site-diagram-replacement-design.md \
  site/scripts/validate-learning-site.mjs \
  site/src/components/Figure.astro \
  site/src/content/lessons \
  site/src/assets/diagrams
git commit -m "feat: replace learning site diagrams with AI figures"
```

- [ ] **Step 4: Push, PR, merge, deploy**

Push branch, create PR, merge when checks/reviews are clear, wait for `Deploy Learning Site`, and smoke-test:

```bash
gh run list --workflow "Deploy Learning Site" --limit 5
```

Fetch these URLs after deploy:

```text
https://jandan138.github.io/mabd-newton/learn/
https://jandan138.github.io/mabd-newton/learn/start-here/
https://jandan138.github.io/mabd-newton/learn/repo-evidence-map/
```
