# Learning Site Executable Tutorial Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the learning site feel executable by adding hand-calculation examples, a cumulative toy-solver trace, misconception repair cards, and three chapter recaps.

**Architecture:** Add four focused Astro card components and style variants, enrich lessons in three content batches, then extend the existing learning-site validator to prevent regressions. Keep every addition conceptual and claim-bounded; the toy-solver trace is tutorial pseudocode, not repository implementation evidence.

**Tech Stack:** Astro, MDX, CSS, Node validation script, Python docs/provenance validator, unittest.

**TDD/Validation Strategy:** Treat `site/scripts/validate-learning-site.mjs` as the executable regression test for tutorial structure. When adding the validator gates, first observe the gate fail with a controlled missing required marker, then restore/complete the content and verify the gate passes; do not commit any temporary red-state mutation.

---

## File Structure

- Create `site/src/components/HandCalc.astro`: hand-calculation card for concrete numeric examples.
- Create `site/src/components/ToySolverStep.astro`: cumulative soft-rubber-stamp toy-solver trace card.
- Create `site/src/components/MisconceptionRepair.astro`: misconception correction card.
- Create `site/src/components/ChapterRecap.astro`: checkpoint recap card.
- Modify `site/src/styles/learn.css`: add four card variants and compact list/table styling.
- Modify all 12 lessons in `site/src/content/lessons/*.mdx`: add toy-solver and misconception cards; add hand-calcs and recaps to required lessons.
- Modify `site/scripts/validate-learning-site.mjs`: enforce the new executable tutorial structure.

## Required Lesson Coverage

Every lesson:
- `ToySolverStep`
- `MisconceptionRepair`

Hand calculation lessons:
- `vectors-matrices-transforms`
- `affine-state`
- `svd-polar-rotation`
- `generalized-coordinates-forces`
- `implicit-time-stepping`
- `newton-hessian-kkt`
- `single-body-abd`
- `multi-body-mabd`

Chapter recap lessons:
- `affine-state`
- `implicit-time-stepping`
- `repo-evidence-map`

## Task 1: Add Executable Tutorial Components And Styles

**Files:**
- Create: `site/src/components/HandCalc.astro`
- Create: `site/src/components/ToySolverStep.astro`
- Create: `site/src/components/MisconceptionRepair.astro`
- Create: `site/src/components/ChapterRecap.astro`
- Modify: `site/src/styles/learn.css`

- [ ] **Step 1: Create `HandCalc.astro`**

Create `site/src/components/HandCalc.astro` with:

```astro
---
interface Props {
  title?: string;
}

const { title = "手算小算例" } = Astro.props;
---

<section class="tutorial-card tutorial-card--hand-calc">
  <h3>{title}</h3>
  <div class="tutorial-card__body hand-calc">
    <slot />
  </div>
</section>
```

- [ ] **Step 2: Create `ToySolverStep.astro`**

Create `site/src/components/ToySolverStep.astro` with:

```astro
---
interface Props {
  title?: string;
  step?: string;
}

const { title = "最小玩具求解器", step = "新增一行" } = Astro.props;
---

<section class="tutorial-card tutorial-card--toy-solver">
  <p class="tutorial-card__eyebrow">{step}</p>
  <h3>{title}</h3>
  <slot />
</section>
```

- [ ] **Step 3: Create `MisconceptionRepair.astro`**

Create `site/src/components/MisconceptionRepair.astro` with:

```astro
---
interface Props {
  title?: string;
}

const { title = "常见误解纠正" } = Astro.props;
---

<section class="tutorial-card tutorial-card--misconception">
  <h3>{title}</h3>
  <slot />
</section>
```

- [ ] **Step 4: Create `ChapterRecap.astro`**

Create `site/src/components/ChapterRecap.astro` with:

```astro
---
interface Props {
  title?: string;
}

const { title = "阶段复盘" } = Astro.props;
---

<section class="tutorial-card tutorial-card--chapter-recap">
  <h3>{title}</h3>
  <slot />
</section>
```

- [ ] **Step 5: Add CSS variants**

Append this CSS after the existing `.tutorial-card--worked-exercise` block in `site/src/styles/learn.css`:

```css
.tutorial-card--hand-calc {
  border-color: #e3c27f;
  background: #fff8e6;
}

.tutorial-card--toy-solver {
  border-color: #b5d0d5;
  background: #f1fbfc;
}

.tutorial-card--misconception {
  border-color: #e5b4a5;
  background: #fff4f0;
}

.tutorial-card--chapter-recap {
  border-color: #c7c0ec;
  background: #f8f6ff;
}

.tutorial-card__body > :first-child,
.tutorial-card--toy-solver > :first-child,
.tutorial-card--misconception > :first-child,
.tutorial-card--chapter-recap > :first-child {
  margin-top: 0;
}

.hand-calc table {
  border-collapse: collapse;
  font-size: 0.94rem;
  margin: 0.75rem 0;
  width: 100%;
}

.hand-calc th,
.hand-calc td {
  border: 1px solid rgba(107, 64, 40, 0.18);
  padding: 0.45rem 0.55rem;
  text-align: left;
  vertical-align: top;
}
```

- [ ] **Step 6: Verify and commit Task 1**

Run:

```bash
npm --prefix site run build
git diff --check
```

Expected:
- Build succeeds and reports 17 pages.
- `git diff --check` prints no output.

Commit:

```bash
git add site/src/components/HandCalc.astro site/src/components/ToySolverStep.astro site/src/components/MisconceptionRepair.astro site/src/components/ChapterRecap.astro site/src/styles/learn.css
git commit -m "feat: add executable tutorial components"
```

## Task 2: Enrich Lessons 1-4

**Files:**
- Modify: `site/src/content/lessons/start-here.mdx`
- Modify: `site/src/content/lessons/why-affine-bodies.mdx`
- Modify: `site/src/content/lessons/vectors-matrices-transforms.mdx`
- Modify: `site/src/content/lessons/affine-state.mdx`

- [ ] **Step 1: Add imports**

Add these imports to all four files:

```mdx
import ToySolverStep from "../../components/ToySolverStep.astro";
import MisconceptionRepair from "../../components/MisconceptionRepair.astro";
```

Add this import only to `vectors-matrices-transforms.mdx` and `affine-state.mdx`:

```mdx
import HandCalc from "../../components/HandCalc.astro";
```

Add this import only to `affine-state.mdx`:

```mdx
import ChapterRecap from "../../components/ChapterRecap.astro";
```

- [ ] **Step 2: Add `ToySolverStep` after `GuidedProjectStep`**

Use these themes:

- `start-here`: define the conceptual toy object and three marked rest points `p0`, `px`, `py`.
- `why-affine-bodies`: choose `model = affine_body` for the soft rubber stamp, while marking particle/RBD/FEM as comparison models.
- `vectors-matrices-transforms`: store marked points and basis arrows as arrays.
- `affine-state`: store `A`, `t`, and `q = pack(A, t)`.

Each `ToySolverStep` must include a short fenced pseudocode block.

- [ ] **Step 3: Add `HandCalc` to lessons 3-4**

Add `HandCalc` after `MathBridge` and before the first existing pseudocode block.

For `vectors-matrices-transforms.mdx`, use this calculation:

```mdx
<HandCalc title="手算小算例：剪切矩阵把基箭头送到哪里">
  <p>给定 `A = [[1, 0.5], [0, 1]]`。</p>
  <table>
    <thead><tr><th>输入</th><th>计算</th><th>结果</th><th>解释</th></tr></thead>
    <tbody>
      <tr><td>`e_x = [1, 0]`</td><td>`A @ e_x`</td><td>`[1, 0]`</td><td>x 方向不变。</td></tr>
      <tr><td>`e_y = [0, 1]`</td><td>`A @ e_y`</td><td>`[0.5, 1]`</td><td>y 方向向右偏，方格被剪切。</td></tr>
    </tbody>
  </table>
</HandCalc>
```

For `affine-state.mdx`, use this calculation:

```mdx
<HandCalc title="手算小算例：先乘 A，再加 t">
  <p>给定 `A = diag(2, 1, 1)`、`t = [3, 0, 0]`、`x_rest = [1, 0, 0]`。</p>
  <ol>
    <li>`A @ x_rest = [2, 0, 0]`。</li>
    <li>`x_world = [2, 0, 0] + [3, 0, 0] = [5, 0, 0]`。</li>
    <li>`q = [2, 0, 0, 0, 1, 0, 0, 0, 1, 3, 0, 0]`。</li>
  </ol>
  <p>这个点先被 x 方向拉伸，再被整体平移。</p>
</HandCalc>
```

- [ ] **Step 4: Add `MisconceptionRepair` before `RememberBox`**

Place it after `WorkedExercise` and before `RememberBox` in all four files. Use these misconceptions:

- `start-here`: “教程页讲了这个概念，所以仓库已经证明它” is wrong.
- `why-affine-bodies`: “ABD 就是低分辨率 FEM” is wrong.
- `vectors-matrices-transforms`: “矩阵只是数字表，列没有几何含义” is wrong.
- `affine-state`: “`q` 的 12 个数字是 12 个互不相关的旋钮” is wrong.

Each card must include four short labels in Chinese: `误解`、`为什么容易这样想`、`正确读法`、`下一步检查`.

- [ ] **Step 5: Add `ChapterRecap` to `affine-state.mdx`**

Place `ChapterRecap` after `MisconceptionRepair` and before `RememberBox` in `affine-state.mdx`. It must include:

- `现在能做`: map rest points using `A @ x_rest + t`, pack `q`.
- `还不能做`: forces, time stepping, constraints, evidence claims.
- `下一段`: polar, rigid-body comparison, Jacobian force mapping, implicit stepping.

- [ ] **Step 6: Verify, review, and commit Task 2**

Run:

```bash
npm --prefix site run build
git diff --check
```

Expected:
- Build succeeds and reports 17 pages.
- `git diff --check` prints no output.

Review with subagents:
- Structure reviewer for imports, placements, and MDX syntax.
- Tutorial reviewer for hand calculation clarity and first recap usefulness.

Commit:

```bash
git add site/src/content/lessons/start-here.mdx site/src/content/lessons/why-affine-bodies.mdx site/src/content/lessons/vectors-matrices-transforms.mdx site/src/content/lessons/affine-state.mdx
git commit -m "feat: make early lessons more executable"
```

## Task 3: Enrich Lessons 5-8

**Files:**
- Modify: `site/src/content/lessons/svd-polar-rotation.mdx`
- Modify: `site/src/content/lessons/rigid-body-basics.mdx`
- Modify: `site/src/content/lessons/generalized-coordinates-forces.mdx`
- Modify: `site/src/content/lessons/implicit-time-stepping.mdx`

- [ ] **Step 1: Add imports**

Add these imports to all four files:

```mdx
import ToySolverStep from "../../components/ToySolverStep.astro";
import MisconceptionRepair from "../../components/MisconceptionRepair.astro";
```

Add this import to `svd-polar-rotation.mdx`, `generalized-coordinates-forces.mdx`, and `implicit-time-stepping.mdx`:

```mdx
import HandCalc from "../../components/HandCalc.astro";
```

Add this import only to `implicit-time-stepping.mdx`:

```mdx
import ChapterRecap from "../../components/ChapterRecap.astro";
```

- [ ] **Step 2: Add `ToySolverStep` after `GuidedProjectStep`**

Use these themes:

- `svd-polar-rotation`: add `R_like = extract_rotation_like_part(A)` as conceptual pseudocode, not implementation evidence.
- `rigid-body-basics`: add a rigid-only branch `rigid_state = (position, orientation)` to compare against affine `q`.
- `generalized-coordinates-forces`: add `J = jacobian(point_position, q)`, `point_velocity = J @ qd`, `tau = J.T @ f`.
- `implicit-time-stepping`: add `residual = next_state_guess - update_rule(next_state_guess)` as conceptual implicit solve trace.

Each `ToySolverStep` must include a fenced pseudocode block.

- [ ] **Step 3: Add `HandCalc` to lessons 5, 7, and 8**

For `svd-polar-rotation.mdx`, add after `MathBridge`:

```mdx
<HandCalc title="手算小算例：先分类，再谈 polar">
  <p>比较两个二维矩阵：`A1 = [[0, -1], [1, 0]]` 和 `A2 = [[1, 0.5], [0, 1]]`。</p>
  <ul>
    <li>`A1` 保持单位长度和直角，只改变朝向；它像纯旋转。</li>
    <li>`A2` 把 `e_y` 送到 `[0.5, 1]`，直角被剪斜；它包含剪切。</li>
  </ul>
  <p>本课只建立分类直觉，不要求手算完整 SVD。</p>
</HandCalc>
```

For `generalized-coordinates-forces.mdx`, add after `MathBridge`:

```mdx
<HandCalc title="手算小算例：一个小 Jacobian 的两个方向">
  <p>给定 `J = [[1, 0], [0, 2]]`、`qd = [3, 1]`、`f = [2, 1]`。</p>
  <ol>
    <li>`J @ qd = [3, 2]`，这是标记点速度。</li>
    <li>`J.T @ f = [2, 2]`，这是广义力。</li>
  </ol>
  <p>同一个 `J` 一边把旋钮速度推到点速度，另一边把点力拉回旋钮力。</p>
</HandCalc>
```

For `implicit-time-stepping.mdx`, add after `MathBridge`:

```mdx
<HandCalc title="手算小算例：一个标量 residual">
  <p>用极简位置更新 `r = x_next - x_now - h * v_next`。给定 `x_now = 0`、`h = 0.1`、候选 `v_next = 1.5`、候选 `x_next = 0.10`。</p>
  <ol>
    <li>`h * v_next = 0.15`。</li>
    <li>`r = 0.10 - 0 - 0.15 = -0.05`。</li>
  </ol>
  <p>残差不是零，说明这个下一步猜测还不自洽。</p>
</HandCalc>
```

- [ ] **Step 4: Add `MisconceptionRepair` before `RememberBox`**

Place it after `WorkedExercise` and before `RememberBox` in all four files. Use these misconceptions:

- `svd-polar-rotation`: “只要 `A` 变了，就一定是材料被拉伸” is wrong.
- `rigid-body-basics`: “旋转矩阵有 9 个数，所以刚体旋转是 9 DOF” is wrong.
- `generalized-coordinates-forces`: “`J^T f` 是为了形状凑得上随便转置” is wrong.
- `implicit-time-stepping`: “residual 很小说明整个物理模型都正确” is wrong.

Each card must include `误解`、`为什么容易这样想`、`正确读法`、`下一步检查`.

- [ ] **Step 5: Add `ChapterRecap` to `implicit-time-stepping.mdx`**

Place `ChapterRecap` after `MisconceptionRepair` and before `RememberBox`. It must include:

- `现在能做`: state representation, point force mapping, residual checking.
- `还不能做`: constrained KKT solve, multi-body topology, evidence classification.
- `下一段`: KKT, single-body ABD evidence, multi-body M-ABD, repo evidence map.

- [ ] **Step 6: Verify, review, and commit Task 3**

Run:

```bash
npm --prefix site run build
git diff --check
```

Expected:
- Build succeeds and reports 17 pages.
- `git diff --check` prints no output.

Review with subagents:
- Technical reviewer for polar, rigid DOF, Jacobian mapping, and implicit residual accuracy.
- Tutorial reviewer for concrete hand-calculation usefulness.

Commit:

```bash
git add site/src/content/lessons/svd-polar-rotation.mdx site/src/content/lessons/rigid-body-basics.mdx site/src/content/lessons/generalized-coordinates-forces.mdx site/src/content/lessons/implicit-time-stepping.mdx
git commit -m "feat: make math lessons more executable"
```

## Task 4: Enrich Lessons 9-12

**Files:**
- Modify: `site/src/content/lessons/newton-hessian-kkt.mdx`
- Modify: `site/src/content/lessons/single-body-abd.mdx`
- Modify: `site/src/content/lessons/multi-body-mabd.mdx`
- Modify: `site/src/content/lessons/repo-evidence-map.mdx`

- [ ] **Step 1: Add imports**

Add these imports to all four files:

```mdx
import ToySolverStep from "../../components/ToySolverStep.astro";
import MisconceptionRepair from "../../components/MisconceptionRepair.astro";
```

Add this import to `newton-hessian-kkt.mdx`, `single-body-abd.mdx`, and `multi-body-mabd.mdx`:

```mdx
import HandCalc from "../../components/HandCalc.astro";
```

Add this import only to `repo-evidence-map.mdx`:

```mdx
import ChapterRecap from "../../components/ChapterRecap.astro";
```

- [ ] **Step 2: Add `ToySolverStep` after `GuidedProjectStep`**

Use these themes:

- `newton-hessian-kkt`: add a pinned-point constraint row and solve `dq` with `lambda` in the same conceptual block system.
- `single-body-abd`: connect the single soft rubber stamp trace to scoped CPU oracle evidence.
- `multi-body-mabd`: expand from one `q` block to `q1`, `q2`, `q3` blocks and joint rows.
- `repo-evidence-map`: classify every toy-solver trace line as conceptual unless a dated record supports a bounded claim.

Each `ToySolverStep` must include a fenced pseudocode block.

- [ ] **Step 3: Add `HandCalc` to lessons 9, 10, and 11**

For `newton-hessian-kkt.mdx`, add after `MathBridge`:

```mdx
<HandCalc title="手算小算例：一个 2x2 KKT 玩具系统">
  <p>给定 `[2 1; 1 0][dq; lambda] = [4; -1]`。</p>
  <ol>
    <li>第二行给出 `dq = -1`。</li>
    <li>代回第一行：`2 * (-1) + lambda = 4`，所以 `lambda = 6`。</li>
  </ol>
  <p>这里的 `lambda` 是对偶变量；它的物理解释依赖约束写法和尺度。</p>
</HandCalc>
```

For `single-body-abd.mdx`, add after `MathBridge`:

```mdx
<HandCalc title="手算小算例：单体状态和残差大小">
  <p>一块印章有 `q=[A,t]`，所以状态和 residual 都按 12 个分量记账。</p>
  <table>
    <thead><tr><th>部分</th><th>数字个数</th><th>教程含义</th></tr></thead>
    <tbody>
      <tr><td>`A`</td><td>9</td><td>旋转、拉伸、剪切的整体线性部分。</td></tr>
      <tr><td>`t`</td><td>3</td><td>整体平移。</td></tr>
      <tr><td>`residual`</td><td>12</td><td>每个状态分量还差多少才满足一步方程。</td></tr>
    </tbody>
  </table>
  <p>这只是单体教程记账，不证明完整求解器存在。</p>
</HandCalc>
```

For `multi-body-mabd.mdx`, add after `MathBridge`:

```mdx
<HandCalc title="手算小算例：三块印章的稀疏触碰表">
  <table>
    <thead><tr><th>关节</th><th>触碰的物体块</th><th>不触碰</th></tr></thead>
    <tbody>
      <tr><td>`J12`</td><td>`B1`, `B2`</td><td>`B3`</td></tr>
      <tr><td>`J23`</td><td>`B2`, `B3`</td><td>`B1`</td></tr>
      <tr><td>`J31`</td><td>`B3`, `B1`</td><td>`B2`</td></tr>
    </tbody>
  </table>
  <p>这张表解释 `G` 的稀疏块位置，不声称完整拓扑求解器已经完成。</p>
</HandCalc>
```

- [ ] **Step 4: Add `MisconceptionRepair` before `RememberBox`**

Place it after `WorkedExercise` and before `RememberBox` in all four files. Use these misconceptions:

- `newton-hessian-kkt`: “`lambda` 就是可以直接比较大小的约束力” is wrong.
- `single-body-abd`: “CPU oracle 通过就等于完整 M-ABD 求解器完成” is wrong.
- `multi-body-mabd`: “三体闭环只要沿树走一遍就够” is wrong.
- `repo-evidence-map`: “教程小项目能跑通概念，所以仓库主张也能升级” is wrong.

Each card must include `误解`、`为什么容易这样想`、`正确读法`、`下一步检查`.

- [ ] **Step 5: Add `ChapterRecap` to `repo-evidence-map.mdx`**

Place `ChapterRecap` after `MisconceptionRepair` and before `RememberBox`. It must include:

- `现在能做`: explain the soft-rubber-stamp toy trace from points through KKT and evidence classification.
- `还不能做`: claim full M-ABD implementation, full paper reproduction, baselines, paper-matching, or paper-faithful collision.
- `下一步`: only records/tests/reports can upgrade claims.

- [ ] **Step 6: Verify, review, and commit Task 4**

Run:

```bash
npm --prefix site run build
git diff --check
```

Expected:
- Build succeeds and reports 17 pages.
- `git diff --check` prints no output.

Review with subagents:
- Technical reviewer for KKT dual variable wording, single-body ABD scope, and multi-body sparsity.
- Claim-boundary reviewer for lessons 10-12.
- Tutorial reviewer for final recap quality.

Commit:

```bash
git add site/src/content/lessons/newton-hessian-kkt.mdx site/src/content/lessons/single-body-abd.mdx site/src/content/lessons/multi-body-mabd.mdx site/src/content/lessons/repo-evidence-map.mdx
git commit -m "feat: make solver lessons more executable"
```

## Task 5: Add Validator Gates

**Files:**
- Modify: `site/scripts/validate-learning-site.mjs`

- [ ] **Step 1: Add executable tutorial constants**

After `mathBridgeComponent`, add:

```js
const requiredExecutableTutorialComponents = [
  {
    marker: "<ToySolverStep",
    importPattern: /^\s*import\s+ToySolverStep\s+from\s+["']\.\.\/\.\.\/components\/ToySolverStep\.astro["'];?\s*$/m,
    importName: "ToySolverStep",
  },
  {
    marker: "<MisconceptionRepair",
    importPattern: /^\s*import\s+MisconceptionRepair\s+from\s+["']\.\.\/\.\.\/components\/MisconceptionRepair\.astro["'];?\s*$/m,
    importName: "MisconceptionRepair",
  },
];

const handCalcRequiredLessonSlugs = new Set([
  "vectors-matrices-transforms",
  "affine-state",
  "svd-polar-rotation",
  "generalized-coordinates-forces",
  "implicit-time-stepping",
  "newton-hessian-kkt",
  "single-body-abd",
  "multi-body-mabd",
]);

const handCalcComponent = {
  marker: "<HandCalc",
  importPattern: /^\s*import\s+HandCalc\s+from\s+["']\.\.\/\.\.\/components\/HandCalc\.astro["'];?\s*$/m,
  importName: "HandCalc",
};

const chapterRecapRequiredLessonSlugs = new Set([
  "affine-state",
  "implicit-time-stepping",
  "repo-evidence-map",
]);

const chapterRecapComponent = {
  marker: "<ChapterRecap",
  importPattern: /^\s*import\s+ChapterRecap\s+from\s+["']\.\.\/\.\.\/components\/ChapterRecap\.astro["'];?\s*$/m,
  importName: "ChapterRecap",
};
```

- [ ] **Step 2: Enforce executable tutorial components**

Inside the existing `if (relative.endsWith(".mdx"))` block, after the MathBridge requirement block, add:

```js
    for (const component of requiredExecutableTutorialComponents) {
      if (!component.importPattern.test(cleanedLessonText)) {
        issues.push(`${relative}: missing ${component.importName} component import`);
      }
      if (!cleanedLessonText.includes(component.marker)) {
        issues.push(`${relative}: missing executable tutorial component ${component.marker}`);
      }
    }
    if (handCalcRequiredLessonSlugs.has(lessonSlug)) {
      if (!handCalcComponent.importPattern.test(cleanedLessonText)) {
        issues.push(`${relative}: missing HandCalc component import`);
      }
      if (!cleanedLessonText.includes(handCalcComponent.marker)) {
        issues.push(`${relative}: missing required HandCalc component`);
      }
    }
    if (chapterRecapRequiredLessonSlugs.has(lessonSlug)) {
      if (!chapterRecapComponent.importPattern.test(cleanedLessonText)) {
        issues.push(`${relative}: missing ChapterRecap component import`);
      }
      if (!cleanedLessonText.includes(chapterRecapComponent.marker)) {
        issues.push(`${relative}: missing required ChapterRecap component`);
      }
    }
```

- [ ] **Step 3: Verify and commit Task 5**

Before the green verification, confirm the new validator can fail: temporarily rename one required marker in a lesson, run `npm --prefix site run validate`, and expect the relevant missing-component issue. Restore that temporary marker before running the commands below.

Run:

```bash
npm --prefix site run validate
npm --prefix site run build
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
git diff --check
```

Expected:
- Learning site validation passes.
- Build succeeds and reports 17 pages.
- Docs/provenance validation passes current phases.
- `git diff --check` prints no output.

Review with subagents:
- Validator spec reviewer.
- Claim/deploy reviewer.

Commit:

```bash
git add site/scripts/validate-learning-site.mjs
git commit -m "test: enforce executable tutorial structure"
```

## Task 6: Final Verification, PR, Merge, Deploy

**Files:**
- No new planned source files.

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
- Site validation passes.
- Build succeeds and reports 17 pages.
- Docs/provenance validation passes current phases.
- Whitespace check prints no output.
- Unit tests pass.

- [ ] **Step 2: Rebase and rerun verification if main advanced**

Run:

```bash
git fetch origin
git rebase origin/main
```

If rebase changes commits, rerun Step 1.

- [ ] **Step 3: Inspect final diff**

Run:

```bash
git status --short
git diff --name-status origin/main...HEAD
git diff --stat origin/main...HEAD
```

Expected:
- Worktree clean.
- Diff contains only executable tutorial spec/plan, site components/styles/content, and site validator changes.
- No docs records, claim-boundary files, reports, source, or tests are deleted/downgraded.

- [ ] **Step 4: Push and create PR**

Run:

```bash
git push -u origin feature/learning-site-executable-tutorial
gh pr create --base main --head feature/learning-site-executable-tutorial --title "Make learning site more executable" --body "## Summary
- Add hand-calculation examples, misconception repair cards, toy-solver trace cards, and chapter recaps.
- Enrich the guided soft-rubber-stamp tutorial with concrete calculations and cumulative pseudocode.
- Enforce executable tutorial structure in the learning-site validator.

## Test Plan
- npm --prefix site run validate
- npm --prefix site run build
- PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
- git diff --check
- PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests"
```

Use the one-shot GitHub proxy environment if GitHub transport fails.

- [ ] **Step 5: Merge and verify deploy**

Check PR merge status, merge when clean, then wait for the `Deploy Learning Site` workflow on `main` to complete successfully.

- [ ] **Step 6: Smoke-test deployed pages**

Run HTTP smoke tests for:

```bash
https://jandan138.github.io/mabd-newton/learn/
https://jandan138.github.io/mabd-newton/learn/affine-state/
https://jandan138.github.io/mabd-newton/learn/generalized-coordinates-forces/
https://jandan138.github.io/mabd-newton/learn/newton-hessian-kkt/
https://jandan138.github.io/mabd-newton/learn/repo-evidence-map/
```

Expected: each returns HTTP `200`.

Check deployed markers:

```bash
curl -fLsS "https://jandan138.github.io/mabd-newton/learn/affine-state/" | rg -o "手算小算例|最小玩具求解器|常见误解纠正|阶段复盘"
curl -fLsS "https://jandan138.github.io/mabd-newton/learn/generalized-coordinates-forces/" | rg -o "手算小算例|最小玩具求解器|常见误解纠正"
curl -fLsS "https://jandan138.github.io/mabd-newton/learn/repo-evidence-map/" | rg -o "最小玩具求解器|常见误解纠正|阶段复盘"
```

Expected: marker output confirms executable tutorial additions are deployed.
