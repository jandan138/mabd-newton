# Phase 31 Official Artifact Availability Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make official M-ABD artifact availability a dated, bounded,
machine-checkable record.

**Architecture:** Store public-source audit facts in a YAML manifest, summarize
them in a dated record, and validate the claim boundaries through unit tests and
`scripts/validate_docs.py`. No web pages, paper assets, generated reports, or
Newton source changes are committed.

**Tech Stack:** Python 3.10 `unittest`, PyYAML, Markdown records, YAML manifest,
existing isolated `mabd-newton-py310` environment.

---

### Task 1: Add Failing Manifest Tests

**Files:**
- Create: `tests/test_official_artifact_audit.py`
- Modify: `tests/test_phase0_bootstrap.py`

- [x] **Step 1: Write tests that require `docs/reference/official-artifact-sources.yaml`**

The tests must assert:

- audit id `phase31-official-artifact-availability`;
- audit date `2026-05-17`;
- status `official_project_and_video_found_implementation_code_coming_soon_as_of_2026-05-17`;
- official sources for arXiv, SIGGRAPH schedule, Minghao Guo page,
  first-author homepage data, first-author project page, first-author
  `MINSUGLLY/mabd` GitHub Pages repository, Yin Yang page, and TeX source tree;
- public repository-index search coverage for GitHub, explicitly marked
  `official: false`;
- non-absolute absence language;
- official supplementary-video URL is recorded from the project page;
- implementation code is recorded as `Code (coming soon)`.

- [x] **Step 2: Run tests and verify RED**

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_official_artifact_audit
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_phase0_bootstrap.Phase0BootstrapTests.test_phase31_official_artifact_audit_is_bounded tests.test_phase0_bootstrap.Phase0BootstrapTests.test_phase31_record_has_required_evidence_fields tests.test_phase0_bootstrap.Phase0BootstrapTests.test_docs_validator_accepts_phase0_contract
```

Expected: fail because the Phase 31 manifest, record, and validator output do
not exist yet.

### Task 2: Add Manifest, Record, And Claim Boundaries

**Files:**
- Create: `docs/reference/official-artifact-sources.yaml`
- Create: `docs/records/2026-05-17-phase31-official-artifact-availability.md`
- Modify: `docs/reference/claim-boundaries.md`

- [x] **Step 1: Add structured manifest**

The manifest records audited URLs and the scoped status. It must use
`official_project_and_video_found_implementation_code_coming_soon_as_of_2026-05-17`,
not absolute implementation-code absence language.

- [x] **Step 2: Add dated record**

The record lists repository base commit, environment, source URLs, first-author
project-page/video facts, GitHub repository search result, blockers, artifacts,
and verification commands.

- [x] **Step 3: Add claim-boundary bullets**

Add Phase 31 current, verified, and non-claim bullets plus a forbidden claim
that Phase 31 project-page/video availability or `Code (coming soon)` status
proves private or unpublished implementation-code absence.

### Task 3: Extend Validator

**Files:**
- Modify: `scripts/validate_docs.py`
- Modify: `tests/test_phase0_bootstrap.py`

- [x] **Step 1: Require Phase 31 paths**

Add the manifest, record, spec, and plan to `REQUIRED_PATHS`.

- [x] **Step 2: Validate the Phase 31 record and manifest**

Add `validate_phase31_record()` to require source URLs, scoped status,
blockers, non-pollution evidence, no stale placeholders, and no `experiment.*`
claim pass.

- [x] **Step 3: Update final validator message**

Change the success line from `/30` to `/31`.

### Task 4: Verify And Commit

**Files:** all Phase 31 files.

- [x] **Step 1: Run focused tests**

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_official_artifact_audit
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_phase0_bootstrap
```

- [x] **Step 2: Run full gates**

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest newton.tests.test_mabd_phase4_solver_step
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/env/readiness_check.py
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"
git diff --check
```

- [ ] **Step 3: Commit, merge, and push**

Commit Phase 31, merge to `main`, rerun gates on `main`, push to `origin/main`,
then remove the worktree.
