# Guided Learning Site Tutorial Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert the learning site from structured lecture notes into a guided tutorial where one rubber-block toy project, math bridges, and worked exercises carry readers through all 12 lessons.

**Architecture:** Add focused Astro tutorial components, enrich each lesson with a shared project step and worked exercise, add math bridges on steep lessons, then extend the validator after content exists so final validation enforces the new tutorial structure. Keep all content conceptual and claim-bounded.

**Tech Stack:** Astro, MDX, TypeScript-flavored Astro components, Node validation script, existing Markdown docs and Python provenance validator.

---

## File Structure

- Create `site/src/components/GuidedProjectStep.astro`: card wrapper for the shared rubber-block project step in each lesson.
- Create `site/src/components/MathBridge.astro`: card wrapper for small slope-reduction explanations in math-heavy lessons.
- Create `site/src/components/WorkedExercise.astro`: card wrapper for prompt, hint, worked solution, and reference answer blocks.
- Modify `site/src/styles/learn.css`: add card variants for the three new components and details spacing for worked answers.
- Modify all 12 `site/src/content/lessons/*.mdx`: add imports, a guided project step, math bridges where required, and worked exercises.
- Modify `site/src/pages/learn/index.astro`: tell readers the site now follows one toy project.
- Modify `site/src/pages/learn/roadmap.astro`: recommend the guided full path as the default tutorial route.
- Modify `site/scripts/validate-learning-site.mjs`: enforce the new tutorial structure after all lesson content exists.

## Shared Tutorial Object

All lesson additions should refer to the same object: a small soft rubber block / stamp with a few marked rest-space points. The object evolves through the lessons:

- It begins as an everyday deformable object.
- Marked points become vectors and coordinates.
- A matrix `A` and translation `t` move the points.
- `q = [A, t]` becomes the generalized state.
- A marked point gets velocity and force mappings through `J qd` and `J^T f`.
- A next-step guess becomes a residual problem.
- A pinned marked point becomes a KKT constraint.
- One block becomes scoped single-body ABD evidence.
- Several blocks become multi-body joint/topology intuition.
- The toy project is finally classified as conceptual, not proof of full reproduction.

## Task 1: Add Tutorial Components And Styles

**Files:**
- Create: `site/src/components/GuidedProjectStep.astro`
- Create: `site/src/components/MathBridge.astro`
- Create: `site/src/components/WorkedExercise.astro`
- Modify: `site/src/styles/learn.css`

- [ ] **Step 1: Add `GuidedProjectStep.astro`**

Create `site/src/components/GuidedProjectStep.astro` with:

```astro
---
interface Props {
  title?: string;
  step?: string;
}

const { title = "贯穿小项目", step = "本节推进" } = Astro.props;
---

<section class="tutorial-card tutorial-card--guided-project">
  <p class="tutorial-card__eyebrow">{step}</p>
  <h3>{title}</h3>
  <slot />
</section>
```

- [ ] **Step 2: Add `MathBridge.astro`**

Create `site/src/components/MathBridge.astro` with:

```astro
---
interface Props {
  title?: string;
}

const { title = "数学坡道" } = Astro.props;
---

<section class="tutorial-card tutorial-card--math-bridge">
  <h3>{title}</h3>
  <ol class="math-bridge-list">
    <slot />
  </ol>
</section>
```

- [ ] **Step 3: Add `WorkedExercise.astro`**

Create `site/src/components/WorkedExercise.astro` with:

```astro
---
interface Props {
  title?: string;
}

const { title = "带答案的练习" } = Astro.props;
---

<section class="tutorial-card tutorial-card--worked-exercise">
  <h3>{title}</h3>
  <div class="worked-exercise">
    <slot />
  </div>
</section>
```

- [ ] **Step 4: Extend tutorial card styles**

Append these styles after the current `.tutorial-card--practice` block in `site/src/styles/learn.css`:

```css
.tutorial-card__eyebrow {
  color: #8b3f1f;
  font-size: 0.78rem;
  font-weight: 900;
  letter-spacing: 0.08em;
  margin: 0 0 0.35rem;
  text-transform: uppercase;
}

.tutorial-card--guided-project {
  border-color: #e2b98a;
  background: #fff4df;
}

.tutorial-card--math-bridge {
  border-color: #b9cce5;
  background: #f4f8ff;
}

.tutorial-card--worked-exercise {
  border-color: #c8d7a4;
  background: #f7fbec;
}

.math-bridge-list {
  display: grid;
  gap: 0.55rem;
  margin: 0;
  padding-left: 1.3rem;
}

.worked-exercise details {
  border: 1px solid rgba(84, 112, 54, 0.18);
  border-radius: 0.85rem;
  background: rgba(255, 255, 255, 0.58);
  margin-top: 0.75rem;
  padding: 0.75rem 0.9rem;
}

.worked-exercise summary {
  cursor: pointer;
  font-weight: 800;
}
```

- [ ] **Step 5: Verify components compile**

Run: `npm --prefix site run build`

Expected: build succeeds and still reports 17 pages.

- [ ] **Step 6: Commit Task 1**

Run:

```bash
git add site/src/components/GuidedProjectStep.astro site/src/components/MathBridge.astro site/src/components/WorkedExercise.astro site/src/styles/learn.css
git commit -m "feat: add guided tutorial components"
```

## Task 2: Enrich Lessons 1-4

**Files:**
- Modify: `site/src/content/lessons/start-here.mdx`
- Modify: `site/src/content/lessons/why-affine-bodies.mdx`
- Modify: `site/src/content/lessons/vectors-matrices-transforms.mdx`
- Modify: `site/src/content/lessons/affine-state.mdx`

- [ ] **Step 1: Add imports to lessons 1-4**

Add these imports near the existing tutorial component imports in each file:

```mdx
import GuidedProjectStep from "../../components/GuidedProjectStep.astro";
import MathBridge from "../../components/MathBridge.astro";
import WorkedExercise from "../../components/WorkedExercise.astro";
```

If a lesson does not use `MathBridge`, do not import it. For Task 2, `vectors-matrices-transforms.mdx` and `affine-state.mdx` must use `MathBridge`; `start-here.mdx` and `why-affine-bodies.mdx` do not need it.

- [ ] **Step 2: Add guided project steps after `PrereqBox`**

Use these exact themes, written in polished Chinese:

- `start-here`: introduce a soft rubber stamp/block with three marked rest-space points; every lesson advances the same object.
- `why-affine-bodies`: decide why the block is not a particle, not rigid-only, and not a full FEM mesh for this tutorial.
- `vectors-matrices-transforms`: mark two basis arrows and one point on the stamp; use coordinates to track where they go.
- `affine-state`: turn the same stamp into `A` plus `t`, then pack those numbers into `q`.

- [ ] **Step 3: Add math bridges to lessons 3-4**

Place each `MathBridge` before the first major formula or pseudocode block that uses the new abstraction.

For `vectors-matrices-transforms.mdx`, include three `<li>` items:

```mdx
<li>先只看一个点：`[1, 0]` 被矩阵送到第一列。</li>
<li>再看两个基方向：第一列和第二列一起决定方格如何倾斜或拉伸。</li>
<li>最后把同一规则搬到 3D：三列分别控制局部 x、y、z 方向。</li>
```

For `affine-state.mdx`, include three `<li>` items:

```mdx
<li>先用 `A @ x_rest` 改变点在静止参考坐标中的方向和长度。</li>
<li>再用 `+ t` 把整个变形后的物体搬到世界位置。</li>
<li>最后把 `A` 的 9 个数和 `t` 的 3 个数排成求解器读得懂的 `q`。</li>
```

- [ ] **Step 4: Add worked exercises before `RememberBox`**

Place each `WorkedExercise` after the existing `PracticePrompt` and before `RememberBox`. Each must include one problem paragraph, one `<details>` hint, one `<details>` reference answer.

Use these exercise topics:

- `start-here`: write the four-layer reading checklist for the rubber stamp project.
- `why-affine-bodies`: choose particle/rigid/affine/FEM for a squashed rubber block and justify the choice.
- `vectors-matrices-transforms`: apply `[[1, 0.5], [0, 1]]` to `[1, 0]` and `[0, 1]`, then describe the sheared grid.
- `affine-state`: pack a diagonal `A = diag(2, 1, 1)` and `t = [3, 0, 0]` into `q`, then explain what happens to one rest point.

The reference answer must be explicit enough that a reader can compare their own work without guessing.

- [ ] **Step 5: Verify Task 2 content**

Run: `npm --prefix site run build`

Expected: build succeeds and reports 17 pages.

Run: `git diff --check`

Expected: no output.

- [ ] **Step 6: Review Task 2 with subagents**

Dispatch two reviewers:

- Structure reviewer: check imports, component placement, MDX syntax, and build risks for lessons 1-4.
- Tutorial reviewer: check whether the rubber-block flow and worked exercises make lessons 1-4 feel more tutorial-like.

Fix any `NEEDS_FIX` findings before continuing.

- [ ] **Step 7: Commit Task 2**

Run:

```bash
git add site/src/content/lessons/start-here.mdx site/src/content/lessons/why-affine-bodies.mdx site/src/content/lessons/vectors-matrices-transforms.mdx site/src/content/lessons/affine-state.mdx
git commit -m "feat: guide early learning site lessons"
```

## Task 3: Enrich Lessons 5-8

**Files:**
- Modify: `site/src/content/lessons/svd-polar-rotation.mdx`
- Modify: `site/src/content/lessons/rigid-body-basics.mdx`
- Modify: `site/src/content/lessons/generalized-coordinates-forces.mdx`
- Modify: `site/src/content/lessons/implicit-time-stepping.mdx`

- [ ] **Step 1: Add imports to lessons 5-8**

Add `GuidedProjectStep` and `WorkedExercise` imports to all four files. Add `MathBridge` imports to `svd-polar-rotation.mdx`, `generalized-coordinates-forces.mdx`, and `implicit-time-stepping.mdx`.

- [ ] **Step 2: Add guided project steps after `PrereqBox`**

Use these exact themes:

- `svd-polar-rotation`: the stamp is rotated and squashed; the lesson separates overall rotation from stretch/shear.
- `rigid-body-basics`: run the same stamp through a rigid-only version to show what 6 DOF cannot express.
- `generalized-coordinates-forces`: push one marked point and map that point force back to the stamp's generalized coordinates.
- `implicit-time-stepping`: guess the stamp's next state and ask whether inertia and forces balance there.

- [ ] **Step 3: Add math bridges to lessons 5, 7, and 8**

For `svd-polar-rotation.mdx`, include:

```mdx
<li>先承认 `A` 里混着旋转、拉伸和剪切，不能直接把所有变化都当作弹性形变。</li>
<li>再用 polar decomposition 抽出最像整体朝向的 `R`。</li>
<li>最后把剩下的部分看成材料真正需要响应的拉伸或剪切。</li>
```

For `generalized-coordinates-forces.mdx`, include:

```mdx
<li>先写点位置 `x(q)`：标记点的位置由 stamp 的状态旋钮决定。</li>
<li>再线性化得到 `dx = J dq`：旋钮小动一下，点跟着小动。</li>
<li>最后用虚功反向读力：点力通过 `J^T f` 变成广义力。</li>
```

For `implicit-time-stepping.mdx`, include:

```mdx
<li>显式方法问“现在的力会把物体推到哪里”。</li>
<li>隐式方法问“下一步猜测自己是否满足方程”。</li>
<li>residual 就是这个猜测还差多少，Newton 修正负责把差距变小。</li>
```

- [ ] **Step 4: Add worked exercises before `RememberBox`**

Use these exercise topics:

- `svd-polar-rotation`: classify two deformations as pure rotation versus shear/stretch and explain whether elastic response is needed.
- `rigid-body-basics`: compare rigid state variables against `q = [A, t]` for the stamp.
- `generalized-coordinates-forces`: given one marked point with force `f`, state the direction of `J qd` and `J^T f` and what each output means.
- `implicit-time-stepping`: write the four-step loop `guess -> residual -> correction -> accept` for the stamp.

Each answer must include a concrete reference answer, not only a general explanation.

- [ ] **Step 5: Verify Task 3 content**

Run: `npm --prefix site run build`

Expected: build succeeds and reports 17 pages.

Run: `git diff --check`

Expected: no output.

- [ ] **Step 6: Review Task 3 with subagents**

Dispatch two reviewers:

- Technical reviewer: polar, rigid DOF, Jacobian force mapping, and implicit stepping accuracy.
- Tutorial reviewer: whether the math bridges reduce jumps for readers with some simulation background.

Fix any `NEEDS_FIX` findings before continuing.

- [ ] **Step 7: Commit Task 3**

Run:

```bash
git add site/src/content/lessons/svd-polar-rotation.mdx site/src/content/lessons/rigid-body-basics.mdx site/src/content/lessons/generalized-coordinates-forces.mdx site/src/content/lessons/implicit-time-stepping.mdx
git commit -m "feat: guide math-heavy learning lessons"
```

## Task 4: Enrich Lessons 9-12 And Entry Pages

**Files:**
- Modify: `site/src/content/lessons/newton-hessian-kkt.mdx`
- Modify: `site/src/content/lessons/single-body-abd.mdx`
- Modify: `site/src/content/lessons/multi-body-mabd.mdx`
- Modify: `site/src/content/lessons/repo-evidence-map.mdx`
- Modify: `site/src/pages/learn/index.astro`
- Modify: `site/src/pages/learn/roadmap.astro`

- [ ] **Step 1: Add imports to lessons 9-12**

Add `GuidedProjectStep` and `WorkedExercise` imports to all four files. Add `MathBridge` imports to `newton-hessian-kkt.mdx`, `single-body-abd.mdx`, and `multi-body-mabd.mdx`.

- [ ] **Step 2: Add guided project steps after `PrereqBox`**

Use these exact themes:

- `newton-hessian-kkt`: pin one marked point on the stamp and solve motion correction together with the constraint variable.
- `single-body-abd`: connect the toy stamp to scoped CPU oracle records, while keeping the tutorial object conceptual.
- `multi-body-mabd`: connect multiple stamps by marked-point joints and inspect which body blocks each joint touches.
- `repo-evidence-map`: separate toy tutorial understanding from repository evidence claims.

- [ ] **Step 3: Add math bridges to lessons 9-11**

For `newton-hessian-kkt.mdx`, include:

```mdx
<li>先只有运动残差：`H dq = -r` 表示怎样修正下一步猜测。</li>
<li>加入约束后，`G dq` 描述这次修正会怎样改变被钉住的点。</li>
<li>KKT 把运动修正和约束变量放进同一个线性系统，避免先修正运动再破坏约束。</li>
```

For `single-body-abd.mdx`, include:

```mdx
<li>先把 toy stamp 的 `q=[A,t]` 当作一个小规模状态。</li>
<li>再看质量、材料力和 residual 如何组成单体参考问题。</li>
<li>最后只把记录中验证过的 CPU oracle 范围称为证据，不升级为完整求解器。</li>
```

For `multi-body-mabd.mdx`, include:

```mdx
<li>先复制多个 toy stamps，每个 stamp 都有自己的 `q` block。</li>
<li>再用 marked-point joint 连接两个 block，得到稀疏的约束行。</li>
<li>最后比较 chain、tree、loop、graph 对 block solve 的影响。</li>
```

- [ ] **Step 4: Add worked exercises before `RememberBox`**

Use these exercise topics:

- `newton-hessian-kkt`: label a two-row KKT block system for a pinned point and identify `H`, `G`, `dq`, `lambda`.
- `single-body-abd`: choose one repo evidence card and state exactly what it supports and what it does not support.
- `multi-body-mabd`: draw three stamps in a triangle loop and list which two body blocks each joint touches.
- `repo-evidence-map`: rewrite one unsafe claim into a bounded claim using records and claim boundaries.

Each reference answer must explicitly preserve claim boundaries.

- [ ] **Step 5: Update learning home page**

In `site/src/pages/learn/index.astro`, update the opening problem paragraph to mention that the course now follows one rubber-block toy project. Add a short section before `学习模块`:

```astro
  <section class="tutorial-card tutorial-card--guided-project">
    <p class="tutorial-card__eyebrow">Default tutorial track</p>
    <h2>贯穿小项目：一块带标记点的软橡胶印章</h2>
    <p>
      默认路线会反复回到同一个 toy stamp：先看它为什么需要仿射体表示，再把它写成矩阵、状态、力映射、隐式残差、KKT 约束和有边界的仓库证据。
    </p>
  </section>
```

- [ ] **Step 6: Update roadmap page**

In `site/src/pages/learn/roadmap.astro`, change the second path title from `补齐完整基础` to `默认教程路线：跟着 toy stamp 走完一遍`, and change its description to:

```ts
description: "推荐新读者按 12 节课顺序走完同一个 rubber-stamp 小项目，逐步跨过矩阵、Jacobian、隐式积分和 KKT。",
```

- [ ] **Step 7: Verify Task 4 content**

Run: `npm --prefix site run build`

Expected: build succeeds and reports 17 pages.

Run: `git diff --check`

Expected: no output.

- [ ] **Step 8: Review Task 4 with subagents**

Dispatch three reviewers:

- Technical reviewer: Newton/KKT, ABD oracle, multi-body topology correctness.
- Tutorial reviewer: whether lessons 9-12 complete the guided toy project.
- Claim-boundary reviewer: no unsupported solver, reproduction, baseline, or paper-matching claims.

Fix any `NEEDS_FIX` findings before continuing.

- [ ] **Step 9: Commit Task 4**

Run:

```bash
git add site/src/content/lessons/newton-hessian-kkt.mdx site/src/content/lessons/single-body-abd.mdx site/src/content/lessons/multi-body-mabd.mdx site/src/content/lessons/repo-evidence-map.mdx site/src/pages/learn/index.astro site/src/pages/learn/roadmap.astro
git commit -m "feat: complete guided tutorial lesson track"
```

## Task 5: Add Validator Gates And Final Verification

**Files:**
- Modify: `site/scripts/validate-learning-site.mjs`

- [ ] **Step 1: Add required guided components**

After `requiredTutorialComponents`, add:

```js
const requiredGuidedTutorialComponents = [
  {
    marker: "<GuidedProjectStep",
    importPattern: /^\s*import\s+GuidedProjectStep\s+from\s+["']\.\.\/\.\.\/components\/GuidedProjectStep\.astro["'];?\s*$/m,
    importName: "GuidedProjectStep",
  },
  {
    marker: "<WorkedExercise",
    importPattern: /^\s*import\s+WorkedExercise\s+from\s+["']\.\.\/\.\.\/components\/WorkedExercise\.astro["'];?\s*$/m,
    importName: "WorkedExercise",
  },
];

const mathBridgeRequiredLessonSlugs = new Set([
  "vectors-matrices-transforms",
  "affine-state",
  "svd-polar-rotation",
  "generalized-coordinates-forces",
  "implicit-time-stepping",
  "newton-hessian-kkt",
  "single-body-abd",
  "multi-body-mabd",
]);

const mathBridgeComponent = {
  marker: "<MathBridge",
  importPattern: /^\s*import\s+MathBridge\s+from\s+["']\.\.\/\.\.\/components\/MathBridge\.astro["'];?\s*$/m,
  importName: "MathBridge",
};
```

- [ ] **Step 2: Add a generic details counter**

After `checkpointDetailsCount`, add:

```js
function componentDetailsCount(text, componentName) {
  const cleaned = stripExamplesAndComments(text);
  const pattern = new RegExp(`^[ \\t]*<${componentName}\\b[\\s\\S]*?<\\/${componentName}>`, "gm");
  return [...cleaned.matchAll(pattern)]
    .reduce((count, component) => count + [...component[0].matchAll(/<details\b/g)].length, 0);
}
```

- [ ] **Step 3: Enforce new lesson requirements**

Inside the existing `if (relative.endsWith(".mdx"))` block, after the current `requiredTutorialComponents` checks, add:

```js
    for (const component of requiredGuidedTutorialComponents) {
      if (!component.importPattern.test(cleanedLessonText)) {
        issues.push(`${relative}: missing ${component.importName} component import`);
      }
      if (!cleanedLessonText.includes(component.marker)) {
        issues.push(`${relative}: missing guided tutorial component ${component.marker}`);
      }
    }
    if (componentDetailsCount(text, "WorkedExercise") < 2) {
      issues.push(`${relative}: WorkedExercise must include at least two <details> blocks`);
    }
    const lessonSlug = path.basename(file, ".mdx");
    if (mathBridgeRequiredLessonSlugs.has(lessonSlug)) {
      if (!mathBridgeComponent.importPattern.test(cleanedLessonText)) {
        issues.push(`${relative}: missing MathBridge component import`);
      }
      if (!cleanedLessonText.includes(mathBridgeComponent.marker)) {
        issues.push(`${relative}: missing required MathBridge component`);
      }
    }
```

- [ ] **Step 4: Run validator**

Run: `npm --prefix site run validate`

Expected: `learning site validation passed`.

- [ ] **Step 5: Run build and docs validation**

Run:

```bash
npm --prefix site run build
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
git diff --check
```

Expected:

- Astro build succeeds and reports 17 pages.
- Docs/provenance validation passes Phase 0-58 or later if `origin/main` has advanced.
- `git diff --check` prints no output.

- [ ] **Step 6: Final review with subagents**

Dispatch two final reviewers:

- Full tutorial reviewer: assess the 12-lesson track as a tutorial for simulation-aware beginners.
- Claim/deploy reviewer: check claim boundaries, validator gates, build/deploy risks, and accidental Phase record changes.

Fix any `NEEDS_FIX` findings before committing.

- [ ] **Step 7: Commit Task 5**

Run:

```bash
git add site/scripts/validate-learning-site.mjs
git commit -m "test: enforce guided tutorial structure"
```

## Task 6: Branch Verification, PR, Deploy, Smoke Test

**Files:**
- No new source files expected unless final review requires fixes.

- [ ] **Step 1: Run full final verification**

Run:

```bash
npm --prefix site run validate
npm --prefix site run build
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
git diff --check
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
```

Expected:

- Learning-site validation passes.
- Astro build succeeds and reports 17 pages.
- Docs/provenance validation passes current phases.
- Whitespace check prints no output.
- Unit tests pass.

- [ ] **Step 2: Rebase if needed**

Run:

```bash
git fetch origin
git rebase origin/main
```

If rebase changes the branch, rerun Step 1 before continuing.

- [ ] **Step 3: Inspect final PR diff**

Run:

```bash
git status --short
git diff --name-status origin/main...HEAD
git diff --stat origin/main...HEAD
```

Expected:

- Working tree clean.
- Diff contains only guided tutorial spec/plan, site components/styles/content/pages, and validator changes.
- No Phase records, claim-boundary docs, reports, source, or tests are deleted or downgraded.

- [ ] **Step 4: Push and create PR**

Run:

```bash
git push -u origin feature/learning-site-guided-tutorial
gh pr create --base main --head feature/learning-site-guided-tutorial --title "Make learning site a guided tutorial" --body "## Summary
- Add a continuous rubber-block toy project across the learning site.
- Add math bridges and worked exercises with hints and reference answers.
- Enforce guided tutorial structure in the learning-site validator.

## Test Plan
- npm --prefix site run validate
- npm --prefix site run build
- PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
- git diff --check
- PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests"
```

Use the one-shot GitHub proxy skill if GitHub transport fails.

- [ ] **Step 5: Merge and verify deploy**

After PR checks/review are clear, merge the PR. Then verify the latest `Deploy Learning Site` workflow run succeeds on `main`.

- [ ] **Step 6: Smoke-test deployed tutorial pages**

Smoke-test these URLs:

```bash
curl -fLsS -o /dev/null -w "%{http_code} %{size_download} %{url_effective}\n" "https://jandan138.github.io/mabd-newton/learn/"
curl -fLsS -o /dev/null -w "%{http_code} %{size_download} %{url_effective}\n" "https://jandan138.github.io/mabd-newton/learn/start-here/"
curl -fLsS -o /dev/null -w "%{http_code} %{size_download} %{url_effective}\n" "https://jandan138.github.io/mabd-newton/learn/generalized-coordinates-forces/"
curl -fLsS -o /dev/null -w "%{http_code} %{size_download} %{url_effective}\n" "https://jandan138.github.io/mabd-newton/learn/newton-hessian-kkt/"
curl -fLsS -o /dev/null -w "%{http_code} %{size_download} %{url_effective}\n" "https://jandan138.github.io/mabd-newton/learn/repo-evidence-map/"
```

Expected: each URL returns HTTP `200`.

Also check tutorial markers on at least three pages:

```bash
curl -fLsS "https://jandan138.github.io/mabd-newton/learn/start-here/" | rg -o "贯穿小项目|数学坡道|带答案的练习"
curl -fLsS "https://jandan138.github.io/mabd-newton/learn/generalized-coordinates-forces/" | rg -o "贯穿小项目|数学坡道|带答案的练习"
curl -fLsS "https://jandan138.github.io/mabd-newton/learn/newton-hessian-kkt/" | rg -o "贯穿小项目|数学坡道|带答案的练习"
```

Expected: marker output confirms deployed pages contain the guided tutorial additions.
