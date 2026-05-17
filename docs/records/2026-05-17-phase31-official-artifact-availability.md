# Phase 31 Official Artifact Availability Record

## Status

passed

## Scope

Phase 31 records a dated public-source audit for official implementation code,
project page, and supplementary-video availability for
"M-ABD: Scalable, Efficient, and Robust Multi-Affine-Body Dynamics".

The audit status is
`official_project_and_video_found_implementation_code_coming_soon_as_of_2026-05-17`.

This is not proof of private author-code absence. It is also not proof of
unpublished implementation-code absence or a paper experiment pass.

## Config Path

- `configs/experiments/paper_experiment_matrix.yaml`
- `docs/reference/official-artifact-sources.yaml`

## Repository

- base commit: `6093ae4`
- worktree:
  `/cpfs/user/zhuzihou/dev/mabd-newton/.worktrees/phase31-official-artifact-availability-audit`
- branch: `phase31-official-artifact-availability-audit`

## Vendored Newton

- source commit: `96713fa965463b69c229a4d30582c733ff3526bb`
- source path: `vendor/newton`
- local patch status: Phase 31 does not modify vendored Newton.

## Paper Source

- arXiv ID: `2603.08079`
- arXiv version: `v2`
- paper source root used for TeX text audit: `/tmp/mabd-paper/source`
- TeX evidence: `sections/experiment.tex:38` mentions a supplementary video,
  but the audited TeX source tree does not contain a supplementary-video URL or
  author-owned implementation-code repository URL. The public first-author
  project page separately provides the supplementary-video URL.

## Environment

- interpreter:
  `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python`
- reference clone source:
  `/cpfs/user/zhuzihou/conda-managed/envs/physics-primitive-newton-py310`
- readiness status: `smoke_passed`
- mutates_reference_environment=false
- uses_reference_python=false
- uses_ambient_python=false

## External Source Audit

- audited_on_utc: `2026-05-17`
- status: `official_project_and_video_found_implementation_code_coming_soon_as_of_2026-05-17`
- manifest: `docs/reference/official-artifact-sources.yaml`

Audited public sources:

- `https://arxiv.org/abs/2603.08079`
  - browser evidence: arXiv page lists v2, authors, PDF, HTML, and TeX Source;
    no author-provided implementation-code URL was observed in the audited page
    text.
- `https://s2026.conference-schedule.org/presentation/?id=papers_116&sess=sess102`
  - browser evidence: SIGGRAPH 2026 page lists the presentation, session,
    authors, event type, time, and location; no implementation-code URL was
    observed in the audited page text.
- `https://www.minghaoguo.com/`
  - browser evidence: the page uses explicit `Code` and `Project Page` links
    for some other publications, while the M-ABD entry lists a PDF link and
    links the first author whose page provides the official project page.
- `https://minsuglly.github.io/content.json`
  - browser evidence: the first-author homepage data lists M-ABD with `Paper`
    and `Page` links, including `https://minsuglly.github.io/mabd/`.
- `https://minsuglly.github.io/mabd/`
  - browser evidence: the official project page lists arXiv, `Code (coming
    soon)`, Video, and BibTeX links. It embeds the supplementary video at
    `https://www.youtube-nocookie.com/embed/xnLCdUfq52w?rel=0` and does not
    provide a released implementation-code URL.
- `https://github.com/MINSUGLLY/mabd`
  - API evidence: the public first-author repository exists with GitHub Pages
    enabled, root contents `index.html` and `static`, and GitHub languages
    summary `HTML`; this is recorded as project-page source rather than solver
    implementation code.
- `https://yangzzzy.github.io/`
  - browser evidence: the M-ABD entry lists title, authors, and venue; no code
    or project-page link was observed near the entry.
- `https://api.github.com/search/repositories?q=%22M-ABD%22%20%22Scalable%20Efficient%20Robust%20Multi-Affine-Body%20Dynamics%22`
  - observed JSON summary: `total_count = 0`,
    `incomplete_results = false`.

Blockers recorded:

- `official_implementation_code_marked_coming_soon`
- `official_implementation_code_not_found_in_audited_public_sources`

No `experiment.*` claim is passed in this phase.

## Artifacts

- structured manifest: `docs/reference/official-artifact-sources.yaml`
- raw web pages: not committed
- generated reports: not committed
- paper PDF/TeX assets: not committed

## Verification Commands

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_official_artifact_audit
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_phase0_bootstrap
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest newton.tests.test_mabd_phase4_solver_step
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/env/readiness_check.py
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"
git diff --check
```
