# Learning Site Course Depth Design

Date: 2026-05-18

## Decision

Turn the ABD/M-ABD learning site from a set of polished concept pages into a more
tutorial-like course. Keep the current visuals and lesson order, but add reusable
learning structure to every lesson: objectives, prerequisites, a guided checkpoint,
and a short practice exercise.

The preferred approach is a shallow site-architecture change plus a broad content
pass. This avoids inventing a full LMS while still making each page feel like a
lesson that teaches, checks understanding, and gives the reader something to do.

## Alternatives Considered

1. **Structured lesson depth pass, recommended.** Add lesson scaffolding and enrich
   all 12 pages. This is small, reviewable, and immediately improves tutorial feel.
2. **Interactive course system.** Add progress state, quizzes, search, and client
   interactivity. This is heavier and unnecessary before the content itself is deep.
3. **Long-form textbook rewrite.** Rewrite each lesson as a chapter. This could be
   strong later, but it is too large for one safe pass and harder to validate.

## Goals

- Make every lesson read like a tutorial, not a short explainer.
- Give the learner explicit outcomes before the main text.
- Surface prerequisites so readers can route themselves through the sequence.
- Add one self-check and one practice exercise per lesson.
- Keep claim boundaries visible: tutorial material is conceptual unless tied to
  scoped repository evidence.
- Keep the site static, fast, and deployable through the existing Astro/GitHub Pages
  workflow.

## Non-Goals

- Do not add user accounts, progress persistence, client-side quiz state, or an LMS.
- Do not add new paper claims or solver implementation claims.
- Do not add more generated images in this pass.
- Do not rewrite solver, experiment, or report code.
- Do not turn conceptual pages into evidence records.

## Content Model

Every lesson should include these tutorial blocks:

- `LearningGoals`: three concrete outcomes starting with action verbs such as
  "辨认", "解释", "把 ... 映射到 ...", "检查".
- `PrereqBox`: two to four prerequisites or route hints. These can mention earlier
  lessons or basic programming/math knowledge.
- `CheckpointQuiz`: two questions with hidden answers. Questions should test the
  exact lesson idea, not trivia. Answers should be concise and reinforce boundaries.
- `PracticePrompt`: one small exercise the reader can do without running large
  simulations. Exercises may be paper-and-pencil, pseudocode, or repository-reading
  tasks.

Technical lessons may also add a compact formula/code bridge using existing
`PseudoCode`, `StepFlow`, or `CompareGrid` components where the current content is
too abstract.

## Component Design

Add four small Astro components under `site/src/components/`:

- `LearningGoals.astro`: titled panel with slotted list content.
- `PrereqBox.astro`: prerequisite/route panel with slotted list content.
- `CheckpointQuiz.astro`: panel that accepts slotted `<details>` items, allowing
  static answer reveal without JavaScript.
- `PracticePrompt.astro`: exercise panel with a `title` prop and slotted body.

These components should be presentational only. They should not own lesson data,
fetch state, or introduce JavaScript.

## Placement Rules

For each lesson MDX:

1. Keep `ProblemCard` first.
2. Keep the existing `Figure` immediately after `ProblemCard`.
3. Add `LearningGoals` and `PrereqBox` immediately after the figure.
4. Keep existing explanatory sections and cards.
5. Add `CheckpointQuiz` after the main conceptual explanation and before final
   evidence/reminder sections where possible.
6. Add `PracticePrompt` near the end, before `RememberBox`.

This preserves the current scan order: problem, visual, outcomes, prerequisites,
explanation, check, practice, evidence, memory.

## Validation Rules

Extend `site/scripts/validate-learning-site.mjs` so every lesson requires:

- `import LearningGoals from "../../components/LearningGoals.astro"`
- `import PrereqBox from "../../components/PrereqBox.astro"`
- `import CheckpointQuiz from "../../components/CheckpointQuiz.astro"`
- `import PracticePrompt from "../../components/PracticePrompt.astro"`
- At least one `<LearningGoals>`, `<PrereqBox>`, `<CheckpointQuiz>`, and
  `<PracticePrompt>` in real MDX, ignoring fenced code and comments.
- At least two `<details>` items inside each lesson's checkpoint area.

Keep existing figure, claim-boundary, route, and asset checks intact.

## Claim Boundary Rules

- Checkpoint answers and exercises must not say M-ABD is complete.
- Evidence-reading exercises may point to claim maps or records, but must describe
  them as scoped evidence.
- Lessons may explain formulas and solver concepts, but must not upgrade tutorial
  explanations into implementation claims.
- Captions and repository evidence cards remain the source of claim-status cues.

## Review Process

Use subagent-driven development in two batches:

1. Components and validator gates.
2. Lesson content enrichment across all 12 lessons.

After each batch, run a spec-compliance review and a content/claim-boundary review.
If reviewers find shallow exercises, vague goals, or overclaims, revise before
continuing.

## Verification

Required checks after implementation:

- `npm --prefix site run validate`
- `npm --prefix site run build`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py`
- `git diff --check`
- Public URL smoke test after merge and deploy.
