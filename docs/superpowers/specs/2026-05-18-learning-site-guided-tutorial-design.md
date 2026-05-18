# Learning Site Guided Tutorial Design

## Context

The deployed learning site now has 12 structured lessons with goals, prerequisites, checkpoint questions, and practice prompts. User feedback is that the target audience is right, but the content still feels like structured lecture notes rather than a real tutorial. The main gaps are:

- Lessons do not share one continuous example, so readers must rebuild context on every page.
- The slope from matrices to Jacobians, implicit stepping, and KKT is too steep even for readers with some simulation background.
- Exercises ask useful questions, but they do not provide hints, worked steps, or reference answers.

## Audience

Primary readers have some programming and physical simulation background. They may know rigid bodies, particles, or FEM at a high level, but they are new to ABD/M-ABD and need a guided bridge from familiar simulation objects to affine-body state, force mapping, implicit solves, and evidence boundaries.

## Goal

Turn the learning site from a concept sequence into a guided tutorial track where a reader follows one toy affine body project through all 12 lessons, crosses math-heavy transitions in small steps, and can check every exercise against hints and reference answers.

## Non-Goals

- Do not claim the toy project is a production solver or paper reproduction.
- Do not add executable simulation code unless a later plan explicitly scopes and verifies it.
- Do not create or vendor paper assets.
- Do not weaken existing claim-boundary, AI diagram, or provenance validation.

## Recommended Approach

Use the already approved direction: combine a continuous guided tutorial track with worked exercises.

The tutorial object is a small soft rubber block / stamp. It starts as a visual object, then becomes points, vectors, `A`, `t`, `q`, point Jacobians, residuals, KKT blocks, single-body ABD evidence, multi-body joints, and finally a claim/evidence reading exercise. The same object appears in every lesson so readers always know what problem the formulas are serving.

## Content Architecture

### Guided Project Step

Add a new component `GuidedProjectStep.astro` and require one instance in every lesson. It should answer:

- What part of the rubber-block toy project is being built in this lesson?
- What state or equation did we have before this lesson?
- What new capability does this lesson add?

The component is conceptual only. It should not imply the repository implements a full tutorial solver.

### Math Bridge

Add a new component `MathBridge.astro` for lessons with steep transitions. It should contain short numbered bridges that translate one formula into smaller questions. Required initial lessons:

- `vectors-matrices-transforms`: coordinates to matrix columns.
- `affine-state`: matrix columns plus translation to packed `q`.
- `svd-polar-rotation`: `A` to rotation/stretch separation.
- `generalized-coordinates-forces`: point position to `J qd` and `J^T f`.
- `implicit-time-stepping`: explicit update to residual solve.
- `newton-hessian-kkt`: residual solve to constrained block system.
- `single-body-abd`: local formulas to scoped CPU oracle evidence.
- `multi-body-mabd`: one-body block to multi-body block topology.

Other lessons may use it if it improves flow, but the validator only needs to enforce the required set.

### Worked Exercise

Add a new component `WorkedExercise.astro` and require one instance in every lesson. Each worked exercise must include:

- A concrete task tied to the rubber-block project.
- A `<details>` hint block.
- A `<details>` worked-solution block.
- A short reference answer or checklist.

Existing `PracticePrompt` can remain as the lightweight prompt. `WorkedExercise` turns it into a tutorial by showing how to solve it.

## Lesson Map

1. `start-here`: introduce the rubber-block project and explain that every lesson advances the same object through concept, formula, pseudocode, and evidence layers.
2. `why-affine-bodies`: choose why a block needs more than rigid motion but less than FEM detail.
3. `vectors-matrices-transforms`: track two or three marked points and transform them with a simple matrix.
4. `affine-state`: package the block as `A` and `t`, then as `q in R12`.
5. `svd-polar-rotation`: split a tilted/deformed block into rotation-like and stretch-like parts.
6. `rigid-body-basics`: compare the same block under rigid 6-DOF motion versus affine motion.
7. `generalized-coordinates-forces`: attach a force to one marked point and map it back to generalized force.
8. `implicit-time-stepping`: advance the block by asking whether the next state satisfies a residual.
9. `newton-hessian-kkt`: constrain one marked point and show how KKT couples motion correction with constraint variables.
10. `single-body-abd`: connect the toy single block to scoped single-body ABD records without upgrading the claim.
11. `multi-body-mabd`: connect two or three toy blocks by control-point joints and identify touched matrix blocks.
12. `repo-evidence-map`: classify which parts of the tutorial are conceptual and which repository records support bounded claims.

## Validator Design

Extend `site/scripts/validate-learning-site.mjs` without weakening existing checks.

New gates:

- Every lesson imports and uses `GuidedProjectStep`.
- Every lesson imports and uses `WorkedExercise`.
- Every `WorkedExercise` contains at least two `<details>` blocks after comments/examples are stripped.
- Required math-heavy lessons import and use `MathBridge`.
- The new checks must use the same `stripExamplesAndComments()` pattern so examples and comments cannot satisfy validation.

Do not make the validator parse full MDX semantics. Marker-based validation is sufficient and consistent with the existing site validator.

## Styling

Extend `site/src/styles/learn.css` with small cards that match the existing warm paper-like theme:

- `.tutorial-card--guided-project` for the shared toy-project step.
- `.tutorial-card--math-bridge` for slope-reduction explanations.
- `.tutorial-card--worked-exercise` for hints and worked answers.

Use the existing card system rather than introducing a new visual language.

## Review Strategy

Use subagents after each content batch:

- Structure review: component imports/usages, validator expectations, build risks.
- Tutorial-quality review: whether the section feels like a guided tutorial and reduces math jumps.
- Claim-boundary review: no unsupported implementation or reproduction claims.

Content should be implemented in batches:

- Components and validator gates.
- Lessons 1-4.
- Lessons 5-8.
- Lessons 9-12.
- Homepage/roadmap polish if needed.

## Verification

Run the following before completion:

- `npm --prefix site run validate`
- `npm --prefix site run build`
- `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py`
- `git diff --check`
- Full unit tests if site/content edits interact with repository validation expectations.

## Success Criteria

- A reader can name the same toy object and describe how it evolves through all 12 lessons.
- Every math-heavy transition has an explicit bridge from prior intuition to the new formula.
- Every lesson contains a worked exercise with hint and reference solution.
- Existing claim boundaries are preserved.
- Site validation, docs validation, build, and whitespace checks pass.
