# Phase 31 Official Artifact Availability Design

## Goal

Record a dated, machine-checkable public-source audit for official M-ABD
implementation code, project page, and supplementary-video availability without
claiming that private or unpublished implementation artifacts do not exist.

## Inputs

- arXiv page and TeX source for `2603.08079` v2.
- SIGGRAPH 2026 schedule page for `papers_116`, session `sess102`.
- Public author pages that list M-ABD, including first-author page data and
  project page links.
- Public repository-index searches.

## Design

Add `docs/reference/official-artifact-sources.yaml` as the structured source
manifest. The manifest stores the audit date, scoped status, audited URLs,
observations, first-author project-page and video facts, repository-search
result, blockers, and explicit non-claims.

Add a dated record under `docs/records/` and extend claim boundaries. The
record is evidence for artifact availability only. It records that the
official project page and supplementary video were found, while implementation
code is marked `Code (coming soon)`. It does not pass any `experiment.*`
claim, does not modify vendored Newton, and does not prove that private author
code or unpublished implementation material is absent.

## Validation

- Unit tests load the manifest and require official-source coverage, scoped
  availability/coming-soon language, the official project page, the video URL,
  and the implementation-code blocker.
- `scripts/validate_docs.py` requires the Phase 31 record, manifest, claim
  boundary text, and no overclaiming.
- Existing experiment claim statuses remain unchanged.
