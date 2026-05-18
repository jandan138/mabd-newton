# Learning Site Course Depth Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the ABD/M-ABD learning site feel like a real tutorial by adding objectives, prerequisites, checkpoints, and practice exercises to every lesson.

**Architecture:** Add four static Astro teaching components and extend the existing learning-site validator to require them in every lesson. Enrich all 12 existing MDX lessons in batches while preserving the current figures, evidence cards, claim boundaries, routes, and static Astro deployment model.

**Tech Stack:** Astro components, MDX lesson content, Node validation script, existing CSS in `site/src/styles/learn.css`.

---

## File Map

- Create `site/src/components/LearningGoals.astro`: presentational goal panel.
- Create `site/src/components/PrereqBox.astro`: presentational prerequisite panel.
- Create `site/src/components/CheckpointQuiz.astro`: static self-check panel using slotted `<details>`.
- Create `site/src/components/PracticePrompt.astro`: practice exercise panel.
- Modify `site/src/styles/learn.css`: shared card styles for tutorial components and details/summary.
- Modify `site/scripts/validate-learning-site.mjs`: require tutorial imports/usages and at least two checkpoint `<details>` per lesson.
- Modify all `site/src/content/lessons/*.mdx`: add imports and tutorial content blocks.

---

## Shared Lesson Requirements

Every lesson must include this import block addition:

```mdx
import LearningGoals from "../../components/LearningGoals.astro";
import PrereqBox from "../../components/PrereqBox.astro";
import CheckpointQuiz from "../../components/CheckpointQuiz.astro";
import PracticePrompt from "../../components/PracticePrompt.astro";
```

Every lesson must include this structure after the existing `<Figure ... />`:

```mdx
<LearningGoals>
  <li><strong>Goal 1:</strong> ...</li>
  <li><strong>Goal 2:</strong> ...</li>
  <li><strong>Goal 3:</strong> ...</li>
</LearningGoals>

<PrereqBox>
  <li>...</li>
  <li>...</li>
</PrereqBox>
```

Every lesson must include one checkpoint with at least two `<details>` items:

```mdx
<CheckpointQuiz>
  <details>
    <summary>Question text?</summary>
    <p>Answer text.</p>
  </details>
  <details>
    <summary>Question text?</summary>
    <p>Answer text.</p>
  </details>
</CheckpointQuiz>
```

Every lesson must include one practice block before the final `RememberBox`:

```mdx
<PracticePrompt title="动手练习">
写出一个 small, concrete task the learner can complete without large simulation runs.
</PracticePrompt>
```

---

### Task 1: Tutorial Components And Validator Gates

**Files:**
- Create: `site/src/components/LearningGoals.astro`
- Create: `site/src/components/PrereqBox.astro`
- Create: `site/src/components/CheckpointQuiz.astro`
- Create: `site/src/components/PracticePrompt.astro`
- Modify: `site/src/styles/learn.css`
- Modify: `site/scripts/validate-learning-site.mjs`

- [ ] **Step 1: Add validator constants first**

In `site/scripts/validate-learning-site.mjs`, add these constants near existing required component constants:

```js
const requiredTutorialComponents = [
  {
    marker: "<LearningGoals",
    importPattern: /^\s*import\s+LearningGoals\s+from\s+["']\.\.\/\.\.\/components\/LearningGoals\.astro["'];?\s*$/m,
    importName: "LearningGoals",
  },
  {
    marker: "<PrereqBox",
    importPattern: /^\s*import\s+PrereqBox\s+from\s+["']\.\.\/\.\.\/components\/PrereqBox\.astro["'];?\s*$/m,
    importName: "PrereqBox",
  },
  {
    marker: "<CheckpointQuiz",
    importPattern: /^\s*import\s+CheckpointQuiz\s+from\s+["']\.\.\/\.\.\/components\/CheckpointQuiz\.astro["'];?\s*$/m,
    importName: "CheckpointQuiz",
  },
  {
    marker: "<PracticePrompt",
    importPattern: /^\s*import\s+PracticePrompt\s+from\s+["']\.\.\/\.\.\/components\/PracticePrompt\.astro["'];?\s*$/m,
    importName: "PracticePrompt",
  },
];
```

- [ ] **Step 2: Add real-MDX checkpoint helper**

Add this helper near `figureCalls`:

```js
function checkpointDetailsCount(text) {
  const cleaned = stripExamplesAndComments(text);
  const checkpoint = cleaned.match(/^[ \t]*<CheckpointQuiz\b[\s\S]*?<\/CheckpointQuiz>/m);
  if (!checkpoint) return 0;
  return [...checkpoint[0].matchAll(/<details\b/g)].length;
}
```

- [ ] **Step 3: Enforce tutorial imports/usages in MDX validation**

Inside the existing `if (relative.endsWith(".mdx"))` block, after required learning component checks, add:

```js
const cleanedLessonText = stripExamplesAndComments(text);
for (const component of requiredTutorialComponents) {
  if (!component.importPattern.test(text)) {
    issues.push(`${relative}: missing ${component.importName} component import`);
  }
  if (!cleanedLessonText.includes(component.marker)) {
    issues.push(`${relative}: missing tutorial component ${component.marker}`);
  }
}
if (checkpointDetailsCount(text) < 2) {
  issues.push(`${relative}: CheckpointQuiz must include at least two <details> questions`);
}
```

- [ ] **Step 4: Run validation to verify RED**

Run:

```bash
npm --prefix site run validate
```

Expected: FAIL for every lesson missing the four tutorial imports/usages and checkpoint details. This proves the gate catches current shallow pages.

- [ ] **Step 5: Create `LearningGoals.astro`**

```astro
---
interface Props {
  title?: string;
}

const { title = "学完你应该能" } = Astro.props;
---

<section class="tutorial-card tutorial-card--goals">
  <h3>{title}</h3>
  <ul>
    <slot />
  </ul>
</section>
```

- [ ] **Step 6: Create `PrereqBox.astro`**

```astro
---
interface Props {
  title?: string;
}

const { title = "开始前确认" } = Astro.props;
---

<section class="tutorial-card tutorial-card--prereq">
  <h3>{title}</h3>
  <ul>
    <slot />
  </ul>
</section>
```

- [ ] **Step 7: Create `CheckpointQuiz.astro`**

```astro
---
interface Props {
  title?: string;
}

const { title = "检查理解" } = Astro.props;
---

<section class="tutorial-card tutorial-card--checkpoint">
  <h3>{title}</h3>
  <div class="checkpoint-list">
    <slot />
  </div>
</section>
```

- [ ] **Step 8: Create `PracticePrompt.astro`**

```astro
---
interface Props {
  title?: string;
}

const { title = "动手练习" } = Astro.props;
---

<section class="tutorial-card tutorial-card--practice">
  <h3>{title}</h3>
  <slot />
</section>
```

- [ ] **Step 9: Add CSS**

Append before `.learn-footer`:

```css
.tutorial-card {
  border: 1px solid #ead5bc;
  border-radius: 1.1rem;
  background: #fffaf3;
  box-shadow: 0 0.8rem 2rem rgba(73, 42, 23, 0.07);
  padding: 1rem;
}

.tutorial-card h3 {
  margin: 0 0 0.55rem;
  color: #2a1910;
  line-height: 1.2;
}

.tutorial-card ul {
  margin: 0;
  padding-left: 1.2rem;
}

.tutorial-card--goals {
  border-color: #c9d9ee;
  background: #f6fbff;
}

.tutorial-card--prereq {
  border-color: #dfcfef;
  background: #fbf7ff;
}

.tutorial-card--checkpoint {
  border-color: #d9c49d;
  background: #fff8e8;
}

.tutorial-card--practice {
  border-color: #b9d4b0;
  background: #f4fbef;
}

.checkpoint-list {
  display: grid;
  gap: 0.75rem;
}

.checkpoint-list details {
  border: 1px solid rgba(107, 64, 40, 0.18);
  border-radius: 0.85rem;
  background: rgba(255, 255, 255, 0.55);
  padding: 0.75rem 0.9rem;
}

.checkpoint-list summary {
  cursor: pointer;
  font-weight: 800;
}
```

- [ ] **Step 10: Verify build remains possible**

Run:

```bash
npm --prefix site run build
git diff --check
```

Expected: build passes because new components compile; diff check passes. `npm --prefix site run validate` still fails until lessons are enriched.

---

### Task 2: Enrich Lessons 1-4

**Files:**
- Modify: `site/src/content/lessons/start-here.mdx`
- Modify: `site/src/content/lessons/why-affine-bodies.mdx`
- Modify: `site/src/content/lessons/vectors-matrices-transforms.mdx`
- Modify: `site/src/content/lessons/affine-state.mdx`

- [ ] **Step 1: Add imports to each lesson**

Add the shared four tutorial imports after the existing component imports and before asset imports.

- [ ] **Step 2: Add goals/prereqs after each figure**

Use these lesson-specific contents:

```text
start-here goals: 说出这门课的四层阅读法; 判断一段文字是概念解释还是证据声明; 选择下一节应该补的基础。
start-here prereqs: 会读基础代码; 知道矩阵是数字表; 接受仓库声明必须看记录。

why-affine-bodies goals: 区分粒子/刚体/仿射体/FEM; 解释 ABD 的中间建模位置; 判断什么时候少量自由度有用。
why-affine-bodies prereqs: 理解位置和形状; 见过矩阵乘法; 读过 start-here。

vectors-matrices-transforms goals: 把向量看成箭头和数组; 用基向量解释矩阵列; 把坐标变换映射到程序数据流。
vectors-matrices-transforms prereqs: 会读二维坐标; 知道数组索引; 可以接受几何和代码是同一对象两种视角。

affine-state goals: 解释 A 和 t 的角色; 把 x_world = A x_rest + t 拆成程序步骤; 说明 q in R12 为什么适合求解。
affine-state prereqs: 已读矩阵变换课; 知道 3x3 矩阵和 3D 向量; 记得教程不是实现证据。
```

- [ ] **Step 3: Add checkpoints and practice**

Add one `CheckpointQuiz` with two questions and one `PracticePrompt` before each final `RememberBox`.

Use these question/exercise themes:

```text
start-here: Q1 为什么概念页不是复现证据? Q2 四层阅读法缺哪层时不能升级声明? Practice: 选一个后续课标题，写出概念/公式/代码/证据四个问题。
why-affine-bodies: Q1 ABD 为什么不是 FEM? Q2 刚体和仿射体多出的自由度是什么? Practice: 给一个软橡胶块场景，判断粒子/刚体/仿射体/FEM 哪个最合适并说明原因。
vectors-matrices-transforms: Q1 矩阵列为什么像基向量? Q2 x' = A x 在代码里需要哪些输入? Practice: 手写一个 2x2 剪切矩阵作用到两个点的结果。
affine-state: Q1 t 能表达剪切吗? Q2 A 和 t 为什么能打包成 12 个数? Practice: 用伪代码写 pack(A,t) 和 apply(A,t,x_rest)。
```

- [ ] **Step 4: Run partial validation**

Run:

```bash
npm --prefix site run validate
npm --prefix site run build
git diff --check
```

Expected: validation still fails for lessons 5-12 missing tutorial components, but not for lessons 1-4. Build and diff check pass.

---

### Task 3: Enrich Lessons 5-8

**Files:**
- Modify: `site/src/content/lessons/svd-polar-rotation.mdx`
- Modify: `site/src/content/lessons/rigid-body-basics.mdx`
- Modify: `site/src/content/lessons/generalized-coordinates-forces.mdx`
- Modify: `site/src/content/lessons/implicit-time-stepping.mdx`

- [ ] **Step 1: Add imports and top tutorial blocks**

Use these contents:

```text
svd-polar-rotation goals: 说明为什么要提取旋转; 区分 R 和 S; 判断整体旋转不应算作弹性拉伸。
svd-polar-rotation prereqs: 已读 affine-state; 知道矩阵可旋转也可拉伸; 接受本课是数学工具解释。

rigid-body-basics goals: 解释 6 DOF; 区分角速度和位置速度; 说出刚体参照对 ABD 的作用。
rigid-body-basics prereqs: 知道位置/速度; 见过旋转概念; 已读 affine-state 更好。

generalized-coordinates-forces goals: 解释 q/qd 和点速度关系; 使用 J^T f 说出广义力来源; 用虚功检查方向。
generalized-coordinates-forces prereqs: 已读矩阵变换和刚体基础; 知道力是向量; 能接受 Jacobian 是局部线性映射。

implicit-time-stepping goals: 区分显式和隐式更新; 解释残差循环; 说明硬系统为什么偏好隐式方法。
implicit-time-stepping prereqs: 知道速度/位置更新; 读过 generalized forces 更好; 知道求解器会反复修正猜测。
```

- [ ] **Step 2: Add checkpoints and practice**

Use these question/exercise themes:

```text
svd-polar-rotation: Q1 纯旋转为什么不该产生弹性力? Q2 A = R S 中 S 表示什么? Practice: 画一个旋转正方形和一个剪切正方形，标出哪个需要弹性响应。
rigid-body-basics: Q1 为什么 3D 刚体不是 9 DOF 旋转? Q2 ABD 相比刚体多表达了什么? Practice: 列出一个刚体状态和一个仿射体状态需要存的变量。
generalized-coordinates-forces: Q1 J qd 和 J^T f 方向为什么相反? Q2 为什么点力不能直接加到 q 上? Practice: 写两行伪代码表示 point_velocity = J @ qd 和 generalized_force = J.T @ f。
implicit-time-stepping: Q1 隐式方法为什么要在 q_next 上算力? Q2 residual 小意味着什么? Practice: 写出一个 guess/evaluate/solve/update 的四步循环。
```

- [ ] **Step 3: Run partial validation**

Run:

```bash
npm --prefix site run validate
npm --prefix site run build
git diff --check
```

Expected: validation still fails for lessons 9-12 only. Build and diff check pass.

---

### Task 4: Enrich Lessons 9-12

**Files:**
- Modify: `site/src/content/lessons/newton-hessian-kkt.mdx`
- Modify: `site/src/content/lessons/single-body-abd.mdx`
- Modify: `site/src/content/lessons/multi-body-mabd.mdx`
- Modify: `site/src/content/lessons/repo-evidence-map.mdx`

- [ ] **Step 1: Add imports and top tutorial blocks**

Use these contents:

```text
newton-hessian-kkt goals: 把 residual/Jacobian/Hessian/KKT 连成求解链; 解释 lambda 的约束含义; 读懂 KKT 块矩阵中每个块的角色。
newton-hessian-kkt prereqs: 已读 implicit-time-stepping; 知道矩阵乘法; 知道约束 C(q)=0 是规则。

single-body-abd goals: 说明单体 ABD 状态和材料响应; 区分 CPU oracle 和完整求解器; 读记录时找出 scoped evidence。
single-body-abd prereqs: 已读 affine-state、polar、KKT; 理解 q in R12; 尊重记录边界。

multi-body-mabd goals: 区分 body 数量、joint 约束和 topology 三类难点; 解释 G 和 lambda 在多体中的作用; 判断 chain/tree/loop/graph 对稀疏结构的影响。
multi-body-mabd prereqs: 已读 single-body ABD 和 KKT; 知道控制点关节; 理解教程不等于完整 M-ABD solver 证据。

repo-evidence-map goals: 区分 conceptual/passed/incomplete/intended; 按 claim map 和 records 查证一个说法; 避免把学习页升级成复现结论。
repo-evidence-map prereqs: 已读 start-here; 知道仓库有 docs/reference 和 docs/records; 接受 incomplete 是诚实边界。
```

- [ ] **Step 2: Add checkpoints and practice**

Use these question/exercise themes:

```text
newton-hessian-kkt: Q1 为什么 KKT 要同时求 dq 和 lambda? Q2 H 和 G 分别来自哪里? Practice: 给一个二行 KKT 块矩阵，标出运动方程和约束方程。
single-body-abd: Q1 CPU oracle 能证明什么、不能证明什么? Q2 q=[A,t] 中材料力主要看哪部分形变? Practice: 找一个本页 RepoEvidenceCard，写出它支持的范围和不支持的范围。
multi-body-mabd: Q1 loop 为什么不能只沿 tree 走一遍? Q2 G 的稀疏结构表示什么? Practice: 画三个体成三角闭环，列出每条 joint 会触碰哪些 body block。
repo-evidence-map: Q1 没有 records 时 claimStatus 应如何读? Q2 passed 是否等于完整论文复现? Practice: 打开 claim-boundaries，摘录一条 forbidden claim 并改写成安全说法。
```

- [ ] **Step 3: Run full site validation**

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
1. Tutorial-depth/content quality across all 12 lessons.
2. Claim-boundary compliance for new goals, checkpoints, exercises, and validator text.
3. Site/deploy readiness for new components and CSS.
```

Fix Important or Critical findings, then re-run final verification.

- [ ] **Step 3: Commit implementation**

Inspect status, diff, and recent log. Stage only intended files and commit:

```bash
git add docs/superpowers/plans/2026-05-18-learning-site-course-depth.md \
  docs/superpowers/specs/2026-05-18-learning-site-course-depth-design.md \
  site/scripts/validate-learning-site.mjs \
  site/src/components \
  site/src/content/lessons \
  site/src/styles/learn.css
git commit -m "feat: deepen learning site lessons"
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
https://jandan138.github.io/mabd-newton/learn/newton-hessian-kkt/
https://jandan138.github.io/mabd-newton/learn/repo-evidence-map/
```
