# ABD/M-ABD Learning Site Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a public Astro/MDX learning site that teaches ABD and M-ABD foundations with cards, tooltips, workflows, examples, and repository claim-boundary safeguards.

**Architecture:** Add an isolated `site/` Astro static site under the existing repository. Lessons live as MDX content collections, shared educational UI lives in small Astro components, and a Node validator checks route/content/claim-boundary constraints before build. The first milestone ships 12 complete lessons and a scalable path to 30+ lessons.

**Tech Stack:** Astro 6, MDX, TypeScript, hand-written CSS, Node 22, GitHub Pages Actions.

---

## File Structure

- Create: `site/package.json` with Astro scripts and dependencies.
- Create: `site/package-lock.json` by running `npm --prefix site install`.
- Create: `site/astro.config.mjs` with static output and `/mabd-newton` base path.
- Create: `site/tsconfig.json` extending Astro strict config.
- Create: `site/src/env.d.ts` for Astro type references.
- Create: `site/src/content.config.ts` defining the `lessons` content collection schema.
- Create: `site/src/data/lessons.ts` containing required lesson order, module names, and expansion slugs.
- Create: `site/src/data/glossary.ts` containing tooltip definitions.
- Create: `site/src/layouts/LearnLayout.astro` for shell, nav, banner, and footer.
- Create: `site/src/components/ConceptCard.astro`.
- Create: `site/src/components/ProblemCard.astro`.
- Create: `site/src/components/StepFlow.astro`.
- Create: `site/src/components/CompareGrid.astro`.
- Create: `site/src/components/PseudoCode.astro`.
- Create: `site/src/components/PitfallCard.astro`.
- Create: `site/src/components/RememberBox.astro`.
- Create: `site/src/components/Term.astro`.
- Create: `site/src/components/RepoEvidenceCard.astro`.
- Create: `site/src/pages/index.astro` redirecting to `learn/`.
- Create: `site/src/pages/learn/index.astro` for course home.
- Create: `site/src/pages/learn/[slug].astro` for lesson pages.
- Create: `site/src/pages/learn/glossary.astro`.
- Create: `site/src/pages/learn/roadmap.astro`.
- Create: `site/src/pages/learn/reproduction-map.astro`.
- Create: `site/src/content/lessons/start-here.mdx`.
- Create: `site/src/content/lessons/why-affine-bodies.mdx`.
- Create: `site/src/content/lessons/vectors-matrices-transforms.mdx`.
- Create: `site/src/content/lessons/affine-state.mdx`.
- Create: `site/src/content/lessons/svd-polar-rotation.mdx`.
- Create: `site/src/content/lessons/rigid-body-basics.mdx`.
- Create: `site/src/content/lessons/generalized-coordinates-forces.mdx`.
- Create: `site/src/content/lessons/implicit-time-stepping.mdx`.
- Create: `site/src/content/lessons/newton-hessian-kkt.mdx`.
- Create: `site/src/content/lessons/single-body-abd.mdx`.
- Create: `site/src/content/lessons/multi-body-mabd.mdx`.
- Create: `site/src/content/lessons/repo-evidence-map.mdx`.
- Create: `site/src/styles/learn.css`.
- Create: `site/scripts/validate-learning-site.mjs`.
- Create: `site/README.md`.
- Create: `.github/workflows/deploy-learning-site.yml`.

Do not commit unless the user explicitly requests commits. If a step below says
"commit checkpoint", treat it as a local review point and skip the actual
`git commit` command unless commit permission is explicit.

## Task 1: Bootstrap Astro Site

**Files:**
- Create: `site/package.json`
- Create: `site/astro.config.mjs`
- Create: `site/tsconfig.json`
- Create: `site/src/env.d.ts`
- Create: `site/src/content.config.ts`

- [ ] **Step 1: Create `site/package.json`**

```json
{
  "name": "mabd-newton-learning-site",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "astro dev --host 0.0.0.0",
    "build": "astro build",
    "preview": "astro preview --host 0.0.0.0",
    "validate": "node scripts/validate-learning-site.mjs"
  },
  "dependencies": {
    "@astrojs/mdx": "^5.0.6",
    "astro": "^6.3.3"
  }
}
```

- [ ] **Step 2: Create `site/astro.config.mjs`**

```js
import { defineConfig } from "astro/config";
import mdx from "@astrojs/mdx";

export default defineConfig({
  output: "static",
  integrations: [mdx()],
  site: "https://jandan138.github.io",
  base: "/mabd-newton",
});
```

- [ ] **Step 3: Create TypeScript config and env file**

`site/tsconfig.json`:

```json
{
  "extends": "astro/tsconfigs/strict"
}
```

`site/src/env.d.ts`:

```ts
/// <reference types="astro/client" />
```

- [ ] **Step 4: Create `site/src/content.config.ts`**

```ts
import { defineCollection, z } from "astro:content";

const lessons = defineCollection({
  type: "content",
  schema: z.object({
    title: z.string(),
    description: z.string(),
    module: z.string(),
    order: z.number().int().positive(),
    status: z.enum(["complete", "planned"]),
    claimStatus: z.enum(["conceptual", "passed", "incomplete", "not_verified", "unsupported"]),
    repoEvidence: z.array(z.string()).default([]),
  }),
});

export const collections = { lessons };
```

- [ ] **Step 5: Install dependencies**

Run: `npm --prefix site install`

Expected: `site/package-lock.json` is created and npm exits with code 0.

- [ ] **Step 6: Run early build check**

Run: `npm --prefix site run build`

Expected: build fails because no pages exist yet, or passes with no routes depending on Astro behavior. If it fails only due to missing pages, continue.

- [ ] **Step 7: Commit checkpoint if explicitly authorized**

Review: `git status --short`

Do not run `git commit` unless commit permission is explicit.

## Task 2: Add Lesson Order, Glossary, And Validator

**Files:**
- Create: `site/src/data/lessons.ts`
- Create: `site/src/data/glossary.ts`
- Create: `site/scripts/validate-learning-site.mjs`

- [ ] **Step 1: Create `site/src/data/lessons.ts`**

```ts
export interface LessonMeta {
  slug: string;
  title: string;
  module: string;
  order: number;
}

export const requiredLessons: LessonMeta[] = [
  { slug: "start-here", title: "先从这里开始", module: "Orientation", order: 1 },
  { slug: "why-affine-bodies", title: "为什么需要仿射体", module: "Orientation", order: 2 },
  { slug: "vectors-matrices-transforms", title: "向量、矩阵与坐标变换", module: "Math", order: 3 },
  { slug: "affine-state", title: "仿射状态：A 和 t", module: "ABD Foundations", order: 4 },
  { slug: "svd-polar-rotation", title: "SVD、Polar Decomposition 与旋转提取", module: "Math", order: 5 },
  { slug: "rigid-body-basics", title: "刚体动力学基础", module: "Physics", order: 6 },
  { slug: "generalized-coordinates-forces", title: "广义坐标、Jacobian 与力映射", module: "Simulation", order: 7 },
  { slug: "implicit-time-stepping", title: "隐式时间积分", module: "Numerics", order: 8 },
  { slug: "newton-hessian-kkt", title: "Newton、Hessian 与 KKT", module: "Numerics", order: 9 },
  { slug: "single-body-abd", title: "单体 ABD 核心思想", module: "ABD", order: 10 },
  { slug: "multi-body-mabd", title: "M-ABD：多体、关节与拓扑求解", module: "M-ABD", order: 11 },
  { slug: "repo-evidence-map", title: "如何阅读本仓库的证据", module: "Reproduction", order: 12 },
];

export const futureLessons = [
  "affine-deformation-modes",
  "coordinate-packing",
  "positive-definite-solves",
  "corotated-elasticity",
  "finite-difference-oracles",
  "dense-kkt-derivation",
  "residual-corrected-rhs",
  "ball-joint-worked-example",
  "hinge-joint-worked-example",
  "universal-joint-worked-example",
  "prismatic-joint-worked-example",
  "joint-limit-clamps",
  "chain-block-tridiagonal",
  "tree-abd-aba-intuition",
  "loop-schur-complement",
  "graph-gauss-seidel",
  "contact-force-mapping",
  "affine-actuation",
  "spinning-box-diagnostics",
  "rbd-baseline-caveats",
  "experiment-matrices",
  "asset-provenance",
  "adding-verified-claims",
  "adding-experiment-lanes",
  "implementation-bugs",
  "symbol-glossary",
  "further-reading",
];
```

- [ ] **Step 2: Create `site/src/data/glossary.ts`**

```ts
export const glossary = {
  ABD: "Affine Body Dynamics：用仿射变换表示近刚体/可变形体的动力学方法。",
  "M-ABD": "Multi-Affine-Body Dynamics：把 ABD 扩展到多体、关节和拓扑求解的框架。",
  affine: "仿射变换：线性变换加平移，常写作 x = A xbar + t。",
  DOF: "Degree of Freedom，自由度；描述系统状态所需的独立数字数量。",
  SVD: "Singular Value Decomposition，奇异值分解；把矩阵拆成两个旋转/正交因子和一个缩放因子。",
  "polar decomposition": "极分解；把变形矩阵拆成旋转部分和对称拉伸部分。",
  KKT: "Karush-Kuhn-Tucker 条件；带约束优化和约束动力学中的块线性系统形式。",
  Jacobian: "Jacobian 矩阵；描述一个量对另一个量的一阶变化关系。",
  Hessian: "Hessian 矩阵；二阶导数矩阵，常表示局部曲率或刚度。",
  "implicit Euler": "隐式欧拉；用下一时刻状态计算力和速度的时间积分方法，通常需要解方程。",
  "co-rotational": "共旋转方法；先把整体旋转分离出去，再在线性化坐标中处理弹性变形。",
  provenance: "来源记录；说明数据、代码、论文材料或实验结果来自哪里以及如何验证。",
};

export type GlossaryTerm = keyof typeof glossary;
```

- [ ] **Step 3: Create `site/scripts/validate-learning-site.mjs`**

```js
import fs from "node:fs";
import path from "node:path";

const root = process.cwd();
const requiredLessons = [
  "start-here",
  "why-affine-bodies",
  "vectors-matrices-transforms",
  "affine-state",
  "svd-polar-rotation",
  "rigid-body-basics",
  "generalized-coordinates-forces",
  "implicit-time-stepping",
  "newton-hessian-kkt",
  "single-body-abd",
  "multi-body-mabd",
  "repo-evidence-map",
];

const requiredBanner = "not evidence of a completed full M-ABD implementation or full paper reproduction";
const forbiddenBasePaths = ["/physics-primitive-agent", "https://jandan138.github.io/physics-primitive-agent"];
const forbiddenClaims = [
  "M-ABD is implemented",
  "implemented M-ABD",
  "paper-faithful solver",
  "reproduces the paper",
  "Newton supports affine-body dynamics",
  "matches paper results",
  "baseline comparison passed",
];

function walk(dir) {
  if (!fs.existsSync(dir)) return [];
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  return entries.flatMap((entry) => {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) return walk(fullPath);
    return [fullPath];
  });
}

function read(relativePath) {
  return fs.readFileSync(path.join(root, relativePath), "utf8");
}

const issues = [];

for (const slug of requiredLessons) {
  const lessonPath = path.join(root, "src/content/lessons", `${slug}.mdx`);
  if (!fs.existsSync(lessonPath)) {
    issues.push(`missing required lesson: ${slug}`);
  }
}

const config = read("astro.config.mjs");
if (!config.includes('base: "/mabd-newton"')) {
  issues.push("astro.config.mjs must use base: /mabd-newton");
}

const layout = read("src/layouts/LearnLayout.astro");
if (!layout.includes(requiredBanner)) {
  issues.push("LearnLayout.astro missing claim-boundary banner");
}

const checkedFiles = walk(path.join(root, "src")).filter((file) => /\.(astro|mdx|ts)$/.test(file));
for (const file of checkedFiles) {
  const relative = path.relative(root, file);
  const text = fs.readFileSync(file, "utf8");
  for (const forbidden of forbiddenBasePaths) {
    if (text.includes(forbidden)) {
      issues.push(`${relative}: hardcoded wrong deployment base ${forbidden}`);
    }
  }
  for (const claim of forbiddenClaims) {
    if (text.includes(claim) && !text.includes("Avoid")) {
      issues.push(`${relative}: forbidden unsupported claim phrase ${claim}`);
    }
  }
  if (relative.endsWith(".mdx")) {
    for (const key of ["title:", "description:", "module:", "order:", "status:", "claimStatus:"]) {
      if (!text.includes(key)) issues.push(`${relative}: missing frontmatter key ${key}`);
    }
    for (const marker of ["<ProblemCard", "<ConceptCard", "<RememberBox"]) {
      if (!text.includes(marker)) issues.push(`${relative}: missing learning component ${marker}`);
    }
  }
}

if (issues.length) {
  for (const issue of issues) console.error(issue);
  process.exit(1);
}

console.log("learning site validation passed");
```

- [ ] **Step 4: Run validator and expect missing layout/lesson failures**

Run: `npm --prefix site run validate`

Expected: FAIL with missing required lessons and missing `LearnLayout.astro`. Continue because later tasks add them.

- [ ] **Step 5: Commit checkpoint if explicitly authorized**

Review: `git status --short`

Do not run `git commit` unless commit permission is explicit.

## Task 3: Build Shared Layout, Components, And Styles

**Files:**
- Create: `site/src/layouts/LearnLayout.astro`
- Create: `site/src/components/*.astro`
- Create: `site/src/styles/learn.css`

- [ ] **Step 1: Create `site/src/layouts/LearnLayout.astro`**

Implement a responsive shell with side navigation, mobile-safe wrapping, and this exact claim banner text:

```text
This site teaches concepts from affine-body dynamics and tracks a Newton-first reproduction effort. It is not evidence of a completed full M-ABD implementation or full paper reproduction.
```

The layout must import `../styles/learn.css`, use `import.meta.env.BASE_URL` for links, and expose `title`, `description`, `currentSlug`, and `lessons` props.

- [ ] **Step 2: Create educational card components**

Each component should be small and slot-based:

```astro
---
interface Props {
  title: string;
  icon?: string;
}
const { title, icon = "*" } = Astro.props;
---

<section class="concept-card">
  <h3><span aria-hidden="true">{icon}</span>{title}</h3>
  <slot />
</section>
```

Use this structure for `ConceptCard`, `ProblemCard`, `PitfallCard`, and `RememberBox`, changing class names and default icons.

- [ ] **Step 3: Create `StepFlow.astro` and `CompareGrid.astro`**

`StepFlow` should render a titled ordered-card container through slots. `CompareGrid` should render a grid container through slots. Keep data handling in MDX; do not invent complex props.

- [ ] **Step 4: Create `PseudoCode.astro`**

Props: `title: string`. Render a `<figure>` with `<figcaption>` and a slotted `<pre>`-style body. Use CSS to preserve whitespace and horizontal scroll.

- [ ] **Step 5: Create `Term.astro`**

Props: `name: string`, `definition: string`. Render:

```astro
<abbr class="term" title={definition}><slot />{Astro.slots.has("default") ? null : name}</abbr>
```

If this inline expression is awkward in Astro, use a simpler two-branch render while keeping the output as `<abbr>`.

- [ ] **Step 6: Create `RepoEvidenceCard.astro`**

Props: `title: string`, `status: string`, `href?: string`. Render a card that says evidence links are records or claim-map references, not broad reproduction claims.

- [ ] **Step 7: Create `site/src/styles/learn.css`**

CSS requirements:

- Warm light background, high-contrast text.
- Sticky desktop nav and non-sticky mobile nav.
- Card styles for concept/problem/pitfall/remember/repo evidence.
- `.step-flow` as responsive timeline-like cards.
- `.compare-grid` as auto-fit cards.
- `.term` as dotted underline tooltip.
- `pre` and pseudocode blocks with horizontal scroll.
- `@media (max-width: 820px)` single-column shell.

- [ ] **Step 8: Run partial validation**

Run: `npm --prefix site run validate`

Expected: FAIL only on missing lessons/pages/frontmatter until routes and lessons are added.

## Task 4: Add Routes And Course Pages

**Files:**
- Create: `site/src/pages/index.astro`
- Create: `site/src/pages/learn/index.astro`
- Create: `site/src/pages/learn/[slug].astro`
- Create: `site/src/pages/learn/glossary.astro`
- Create: `site/src/pages/learn/roadmap.astro`
- Create: `site/src/pages/learn/reproduction-map.astro`

- [ ] **Step 1: Create root redirect page**

`site/src/pages/index.astro` should use a meta refresh and normal link to `learn/`, with the link built from `import.meta.env.BASE_URL`.

- [ ] **Step 2: Create lesson dynamic route**

`site/src/pages/learn/[slug].astro` should:

- import `getCollection` from `astro:content`;
- implement `getStaticPaths()` from all complete lesson entries;
- sort navigation by `data.order`;
- call `await lesson.render()`;
- pass lessons and current slug into `LearnLayout`;
- render frontmatter metadata and the MDX `Content`.

- [ ] **Step 3: Create course home**

`site/src/pages/learn/index.astro` should show:

- hero section: "ABD/M-ABD 基础知识补充教程";
- one-sentence problem statement;
- module cards for Math, Physics, Numerics, ABD, M-ABD, Reproduction;
- lesson cards linking to all 12 lessons;
- links to glossary, roadmap, and reproduction map.

- [ ] **Step 4: Create glossary page**

Render `glossary` terms from `site/src/data/glossary.ts` in cards. Keep the page educational, not a raw dictionary.

- [ ] **Step 5: Create roadmap page**

Provide three paths:

- "最快读懂论文": lessons 1, 2, 4, 5, 8, 9, 10, 11.
- "补齐完整基础": all 12 first-batch lessons.
- "参与仓库复现": lessons 1, 7, 8, 9, 10, 11, 12 plus records/docs.

- [ ] **Step 6: Create reproduction map page**

Explain that method oracles, experiment lanes, reports, and claim statuses are different evidence layers. Link to `docs/reference/claim-boundaries.md`, `docs/reference/paper-claims.yaml`, and `docs/records/` as repository paths in text.

- [ ] **Step 7: Run route build check**

Run: `npm --prefix site run build`

Expected: FAIL only because lesson MDX files are not added yet, or PASS if route code handles no lessons. Continue.

## Task 5: Add First Six Lessons

**Files:**
- Create: `site/src/content/lessons/start-here.mdx`
- Create: `site/src/content/lessons/why-affine-bodies.mdx`
- Create: `site/src/content/lessons/vectors-matrices-transforms.mdx`
- Create: `site/src/content/lessons/affine-state.mdx`
- Create: `site/src/content/lessons/svd-polar-rotation.mdx`
- Create: `site/src/content/lessons/rigid-body-basics.mdx`

- [ ] **Step 1: Use the shared MDX import block**

Every lesson should import the same components:

```mdx
import ConceptCard from "../../components/ConceptCard.astro";
import ProblemCard from "../../components/ProblemCard.astro";
import StepFlow from "../../components/StepFlow.astro";
import CompareGrid from "../../components/CompareGrid.astro";
import PseudoCode from "../../components/PseudoCode.astro";
import PitfallCard from "../../components/PitfallCard.astro";
import RememberBox from "../../components/RememberBox.astro";
import RepoEvidenceCard from "../../components/RepoEvidenceCard.astro";
```

- [ ] **Step 2: Write `start-here.mdx`**

Frontmatter:

```yaml
---
title: "先从这里开始"
description: "这门课如何把编程经验连接到 ABD/M-ABD 论文和本仓库复现。"
module: "Orientation"
order: 1
status: "complete"
claimStatus: "conceptual"
repoEvidence: []
---
```

Required content sections:

- ProblemCard: "它解决的问题：把 ABD/M-ABD 需要的数学、物理和数值方法拆成可学习的工程概念。"
- ConceptCard for "读论文不是背公式" with analogy "先学操作系统再读内核代码".
- ConceptCard for "概念、公式、代码、证据四层".
- StepFlow with steps: mental model, math object, pseudocode, repository evidence.
- PitfallCard explaining the site is not proof of full paper reproduction.
- RememberBox with three bullets: learn foundations, map to ABD, respect claim records.

- [ ] **Step 3: Write `why-affine-bodies.mdx`**

Must compare particles, rigid bodies, FEM, ABD, and M-ABD. Include a cube analogy:

- RBD: cube can move and rotate, cannot stretch.
- FEM: cube is many small tetrahedra, accurate but heavier.
- ABD: cube is one object with a 3x3 matrix that can rotate, stretch, and shear.
- M-ABD: many affine bodies connected by constraints.

Include pseudocode showing `x_world = A @ x_rest + t`.

- [ ] **Step 4: Write `vectors-matrices-transforms.mdx`**

Must explain vectors as arrows/numbers, matrices as machines that transform arrows, basis columns, transpose/inverse intuition, and why 3x3 matrices appear everywhere in ABD. Include a 2D matrix example before 3D.

- [ ] **Step 5: Write `affine-state.mdx`**

Must explain `A`, `t`, `q in R12`, coordinate packing, and how one affine body moves rest points. Include pseudocode:

```python
def affine_point(A, t, x_rest):
    return A @ x_rest + t

def pack_q(A, t):
    return [A[0,0], A[1,0], A[2,0], A[0,1], A[1,1], A[2,1], A[0,2], A[1,2], A[2,2], t[0], t[1], t[2]]
```

- [ ] **Step 6: Write `svd-polar-rotation.mdx`**

Must explain why a deformed matrix contains rotation plus stretch/shear, why ABD needs rotation extraction, SVD intuition, and polar decomposition as "find the nearest pure rotation". Include a PitfallCard that SVD is not magic compression here; it is geometry separation.

- [ ] **Step 7: Write `rigid-body-basics.mdx`**

Must explain 6 DOF, translation, rotation, angular velocity, inertia tensor, momentum, and why rotations make rigid-body simulation nonlinear. Include a CompareGrid for rotation matrix/quaternion/affine matrix.

- [ ] **Step 8: Run validation**

Run: `npm --prefix site run validate`

Expected: FAIL only for the remaining six missing lessons if routes/components are correct.

## Task 6: Add Last Six Lessons

**Files:**
- Create: `site/src/content/lessons/generalized-coordinates-forces.mdx`
- Create: `site/src/content/lessons/implicit-time-stepping.mdx`
- Create: `site/src/content/lessons/newton-hessian-kkt.mdx`
- Create: `site/src/content/lessons/single-body-abd.mdx`
- Create: `site/src/content/lessons/multi-body-mabd.mdx`
- Create: `site/src/content/lessons/repo-evidence-map.mdx`

- [ ] **Step 1: Write `generalized-coordinates-forces.mdx`**

Must explain `q`, `qd`, generalized forces, Jacobian, virtual work, and `J^T f`. Use analogy: physical force is a hand pushing a point; generalized force is how that push changes the knobs controlling the body.

- [ ] **Step 2: Write `implicit-time-stepping.mdx`**

Must compare explicit Euler and implicit Euler using a stiff spring analogy. Include pseudocode for explicit update and implicit residual solve. Explain why large time steps need solving equations.

- [ ] **Step 3: Write `newton-hessian-kkt.mdx`**

Must explain residuals, Jacobians, Hessians, Newton iterations, constraints, Lagrange multipliers, and KKT block matrices. Use analogy: KKT is solving motion and constraint forces in one negotiation table.

- [ ] **Step 4: Write `single-body-abd.mdx`**

Must explain single-body ABD solve from affine state, mass, stiffness, co-rotated force, polar/no-polar modes, and the idea of a dense CPU oracle. Include a RepoEvidenceCard linking to Phase 1, Phase 4, Phase 5, Phase 25, and Phase 26 records by repository path.

- [ ] **Step 5: Write `multi-body-mabd.mdx`**

Must explain control-point joints, ball/hinge/universal/prismatic constraints, KKT dual variables, chain/tree/loop/graph topology cases, and why topology solvers matter. Include a PitfallCard that current graph Gauss-Seidel is an inferred reconstruction where recorded.

- [ ] **Step 6: Write `repo-evidence-map.mdx`**

Must explain claim boundaries, method claims vs experiment claims, `docs/reference/paper-claims.yaml`, `docs/records/`, and why incomplete reports are honest progress. Include a CompareGrid for `conceptual`, `passed`, `incomplete`, and `intended`.

- [ ] **Step 7: Run validation and build**

Run: `npm --prefix site run validate`

Expected: `learning site validation passed`.

Run: `npm --prefix site run build`

Expected: Astro build succeeds and writes `site/dist`.

## Task 7: Add README And GitHub Pages Workflow

**Files:**
- Create: `site/README.md`
- Create: `.github/workflows/deploy-learning-site.yml`
- Modify: `.gitignore` if needed to ignore `site/node_modules`, `site/.astro`, and `site/dist`.

- [ ] **Step 1: Create `site/README.md`**

Include:

- site purpose;
- tech stack;
- directory contract;
- generated/local-only files;
- claim-boundary rules;
- local commands;
- visual QA checklist;
- deployment URL `https://jandan138.github.io/mabd-newton/learn/`.

- [ ] **Step 2: Create workflow**

`.github/workflows/deploy-learning-site.yml` should mirror the referenced project but use:

- name `Deploy Learning Site`;
- trigger paths `.github/workflows/deploy-learning-site.yml` and `site/**`;
- Node 22;
- `cache-dependency-path: site/package-lock.json`;
- working directory `site`;
- upload path `site/dist`.

- [ ] **Step 3: Update `.gitignore` only if needed**

Add these lines if absent:

```gitignore
site/node_modules/
site/.astro/
site/dist/
```

- [ ] **Step 4: Run repository checks**

Run: `npm --prefix site run validate`

Expected: `learning site validation passed`.

Run: `npm --prefix site run build`

Expected: Astro build succeeds.

Run: `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py`

Expected: docs/provenance validation passed.

Run: `git diff --check`

Expected: no output.

## Task 8: Agent Reviews And Final Hardening

**Files:**
- Modify any `site/**`, `.github/workflows/deploy-learning-site.yml`, `.gitignore`, or docs files only if review finds issues.

- [ ] **Step 1: Dispatch curriculum review agent**

Ask an agent to read the 12 lessons and report missing prerequisites, unclear analogies, or lesson-order problems. Expected output: concise findings with file references.

- [ ] **Step 2: Dispatch claim-boundary review agent**

Ask an agent to search the site for unsupported implementation, reproduction, baseline, or Newton-support claims. Expected output: findings with exact phrases and suggested safer wording.

- [ ] **Step 3: Dispatch site architecture review agent**

Ask an agent to inspect Astro routes, base path, validator, build commands, and GitHub Pages workflow. Expected output: deployment risks and concrete fixes.

- [ ] **Step 4: Apply review fixes**

Use `apply_patch` for manual edits. Do not rewrite unrelated files. Keep changes minimal.

- [ ] **Step 5: Run final verification**

Run:

```bash
npm --prefix site run validate
npm --prefix site run build
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
```

Expected:

- site validation passes;
- Astro build succeeds;
- docs/provenance validation passes;
- whitespace check has no output.

- [ ] **Step 6: Report final status**

Summarize created site, lesson count, commands run, review findings fixed, and any remaining risks. Do not claim deployment happened unless the workflow has actually run on GitHub Pages.

## Self-Review Notes

- Spec coverage: the plan covers Astro setup, MDX lessons, components, glossary,
  roadmap, reproduction map, validator, README, workflow, and claim-boundary
  safeguards.
- Placeholder scan: no unresolved placeholder markers or unnamed future
  implementation steps are used as required work. Future 30+ lesson topics are
  intentionally listed as expansion scope, not first-pass required files.
- Type consistency: frontmatter keys match the content schema and validator.
- Commit handling: plan records commit checkpoints but explicitly disables actual
  commits unless the user separately authorizes them.
