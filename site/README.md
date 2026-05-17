# M-ABD Learning Site

This directory contains the public learning site for ABD and M-ABD concepts in this repository. The site teaches mathematical and simulation background, links concepts back to repository evidence, and keeps all reproduction claims inside the documented project boundaries.

Deployment URL: <https://jandan138.github.io/mabd-newton/learn/>

## Tech Stack

- Astro 6 static output
- MDX lessons
- TypeScript content configuration
- Hand-written CSS
- Node 22 and npm
- GitHub Pages Actions deployment

## Directory Contract

- `src/pages/` owns public routes under `/learn/`.
- `src/content/lessons/` owns lesson MDX files.
- `src/content.config.ts` defines lesson frontmatter requirements.
- `src/data/lessons.ts` defines required lesson order and future expansion slugs.
- `src/data/glossary.ts` defines tooltip terms used by lesson content.
- `src/components/` owns reusable educational UI only.
- `src/layouts/` owns page shells and shared navigation.
- `src/styles/` owns site CSS.
- `scripts/validate-learning-site.mjs` checks route, content, and claim-boundary constraints before build.

## Generated And Local-Only Files

The following files and directories are generated or local-only and must not be committed:

- `site/node_modules/`
- `site/.astro/`
- `site/dist/`

The committed dependency lockfile is `site/package-lock.json`.

## Claim-Boundary Rules

- Do not claim M-ABD is implemented until `SolverMABD` code and method records exist.
- Do not claim full paper reproduction until every required paper claim is passed or explicitly incomplete.
- Do not claim unmodified Newton supports affine-body dynamics.
- Do not claim rigid `body_q` proxy collision is paper-faithful affine collision.
- Do not claim comparative baselines without installed, run, and recorded adapters.
- Prefer links to evidence records and documented claim status over broad implementation claims.

## Local Commands

Run commands from the repository root:

```bash
npm --prefix site install
npm --prefix site run validate
npm --prefix site run build
npm --prefix site run dev
npm --prefix site run preview
```

Repository documentation validation:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
```

## Visual QA Checklist

- Course home loads at `/mabd-newton/learn/` and links to all required lessons.
- Lesson pages render MDX components, navigation, and evidence callouts correctly.
- Glossary, roadmap, and reproduction map routes work from the deployed base path.
- Desktop layout is readable without horizontal scrolling.
- Mobile layout keeps cards, navigation, code blocks, and tables usable.
- Claim-boundary banner and footer language remain visible and accurate.
- Build output has no broken asset paths under the `/mabd-newton` base path.
