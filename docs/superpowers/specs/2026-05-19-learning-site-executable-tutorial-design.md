# Learning Site Executable Tutorial Design

## Context

The learning site now has a coherent 12-lesson guided path around one soft rubber stamp with marked points. It includes learning goals, prerequisites, a guided project step, math bridges, checkpoint questions, practice prompts, and worked exercises.

The next weakness is that the tutorial still often reads as explanation plus answer, not as something the reader can actively compute or assemble. The user approved strengthening four areas:

- Hand-calculation examples.
- A minimal ABD toy-solver line.
- Common misconception correction.
- Chapter-level recaps.

The user did not request the repository code-reading layer in this pass, so repo code navigation is out of scope.

## Goal

Make the guided learning site feel executable: readers should repeatedly plug in concrete numbers, update a cumulative toy-solver pseudocode trace, catch common RBD/FEM/solver misconceptions, and pause at three recap checkpoints to see what the soft-rubber-stamp project can and cannot do yet.

## Audience

The audience remains simulation-aware beginners: readers who know basic programming and some physical simulation ideas, but who are new to ABD/M-ABD and need concrete steps from familiar physics concepts to affine-body math.

## Non-Goals

- Do not add a real executable solver or claim a solver implementation exists.
- Do not claim the toy-solver trace is production code, evidence, or paper reproduction.
- Do not add repository source-code navigation in this pass.
- Do not weaken claim-boundary, AI-diagram, deployment, or provenance validation.

## Tutorial Additions

### Hand Calculation

Add a `HandCalc.astro` component for small numeric examples. It should make each numeric step inspectable:

- Given values.
- Operation.
- Result.
- Short interpretation.

This component should appear in the lessons where numeric concrete examples matter most:

- `vectors-matrices-transforms`: multiply a shear matrix by basis vectors.
- `affine-state`: compute `A @ x_rest + t` and pack `q`.
- `svd-polar-rotation`: classify a pure rotation-like case versus a shear/stretch case using simple matrix intuition, not full SVD arithmetic.
- `generalized-coordinates-forces`: use a tiny Jacobian to map `qd` to point velocity and `f` to generalized force.
- `implicit-time-stepping`: compute a scalar residual from a guessed next value.
- `newton-hessian-kkt`: write and label a small 2x2 or block KKT system.
- `single-body-abd`: compute what part of `q` and residual belongs to a single soft-rubber-stamp state, while keeping evidence scoped.
- `multi-body-mabd`: list a tiny sparse block incidence table for three stamps in a loop.

The validator should require `HandCalc` for those eight lessons.

### Toy Solver Trace

Add a `ToySolverStep.astro` component. It is not executable code; it is a cumulative pseudocode trace that tells the reader which line of the minimal toy solver was just added.

Every lesson should have one `ToySolverStep` so the full sequence becomes:

1. Define the soft rubber stamp and marked points.
2. Choose an affine-body representation.
3. Represent points and basis vectors as arrays.
4. Store `A`, `t`, and packed `q`.
5. Separate rotation-like motion from stretch/shear intuition.
6. Compare with rigid-only state.
7. Map point velocity and point force through `J` and `J^T`.
8. Form a residual for an implicit step.
9. Add a pinned-point KKT constraint.
10. Connect the single-body trace to scoped CPU oracle evidence.
11. Extend the trace to multiple stamp blocks and joint rows.
12. Classify the trace as conceptual tutorial material, not reproduction evidence.

The validator should require `ToySolverStep` in every lesson.

### Misconception Repair

Add a `MisconceptionRepair.astro` component. Each lesson should contain one misconception framed as:

- Mistaken mental model.
- Why it is tempting.
- Correct reading.
- What to check next.

Examples:

- `A` is not just a rotation matrix.
- `q` is not 12 unrelated sliders.
- `J^T f` is not a random transpose trick.
- A small residual is not proof that the model is physically complete.
- `lambda` is a dual variable, not automatically a directly comparable force magnitude.
- A tutorial toy trace is not solver evidence.

The validator should require `MisconceptionRepair` in every lesson.

### Chapter Recap

Add a `ChapterRecap.astro` component for lessons 4, 8, and 12. These are the natural checkpoints:

- Lesson 4: representation checkpoint. The reader can map points with `A` and `t`, but no force or time stepping exists yet.
- Lesson 8: dynamics checkpoint. The reader has state, force mapping, and residual intuition, but not constraints or evidence classification yet.
- Lesson 12: evidence checkpoint. The reader can tell which parts are tutorial concepts and which parts need records.

Each recap should answer:

- What the toy stamp can do now.
- What it still cannot do.
- Which next lesson or evidence layer fills the gap.

The validator should require `ChapterRecap` only for `affine-state`, `implicit-time-stepping`, and `repo-evidence-map`.

## Component Styling

Use the current tutorial card visual system. Add these variants:

- `.tutorial-card--hand-calc`
- `.tutorial-card--toy-solver`
- `.tutorial-card--misconception`
- `.tutorial-card--chapter-recap`

Do not introduce a new visual language. The site already uses warm paper-like cards; these components should remain compact and readable on mobile.

## Validator Design

Extend `site/scripts/validate-learning-site.mjs` using the existing marker-based pattern:

- Every lesson must import and use `ToySolverStep`.
- Every lesson must import and use `MisconceptionRepair`.
- The eight numeric/math lessons must import and use `HandCalc`.
- Lessons 4, 8, and 12 must import and use `ChapterRecap`.
- Checks must run on `stripExamplesAndComments(text)` so fenced examples and comments cannot satisfy requirements.

Existing validator checks must remain intact.

## Content Strategy

The content should be added in batches:

1. Components, styles, and validator scaffolding.
2. Lessons 1-4: representation and first recap.
3. Lessons 5-8: math/dynamics and second recap.
4. Lessons 9-12: KKT/evidence and final recap.
5. Final validator enforcement and reviews.

Every batch needs two reviews:

- Spec/structure review: imports, placement, validator compatibility, build risks.
- Tutorial review: whether the new blocks make the lesson more executable and beginner-guided.

Claim-boundary review is required for lessons 9-12 and final review.

## Success Criteria

- A reader can follow a cumulative minimal toy-solver trace across all 12 lessons.
- The key math-heavy lessons include concrete numeric or table-based hand examples.
- Every lesson explicitly repairs one likely misconception.
- Lessons 4, 8, and 12 give clear recap checkpoints.
- The tutorial remains claim-bounded: no full M-ABD solver, full paper reproduction, baseline, paper-matching, or collision-fidelity claim is introduced.
- `npm --prefix site run validate`, `npm --prefix site run build`, docs validation, `git diff --check`, and final unit tests pass before merge.
