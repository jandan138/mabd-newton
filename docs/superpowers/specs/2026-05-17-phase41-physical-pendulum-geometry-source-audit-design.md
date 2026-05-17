# Phase 41 Physical Pendulum Geometry Source Audit Design

Date: 2026-05-17

## Purpose

Phase 41 audits whether the paper PDF/TeX source assets disclose enough
physical-pendulum geometry to remove `pendulum_geometry_unknown`. Phase 40 added
scalar joint-force diagnostics, but a paper-faithful joint-force claim still
requires the exact pendulum geometry or an explicit source finding that the
public paper assets do not provide it.

## Scope

In scope:

- Scan the local arXiv v2 TeX source tree at `/tmp/mabd-paper/source`.
- Record a full local source-tree inventory and the text/TeX paths scanned for
  the absence check.
- Hash the physical-pendulum TeX section and figure PDF.
- Record positive source facts from `sections/experiment.tex:77-91`.
- Record `images/simple_pendulum/simple_pendulum.pdf` availability and embedded
  image provenance paths visible in the PDF metadata.
- Search scanned source text for physical-pendulum geometry/data disclosure
  terms, and switch to manual-review status if usable length, mass, inertia,
  geometry, or raw-curve disclosures are found.
- Record missing scene parameters: mesh/body geometry, body length scale, mass
  distribution, inertia tensor, timestep list, raw angle curve data, raw
  joint-force curve data, and exact ABD/RBD numeric outputs.
- Keep `pendulum_geometry_unknown` and all `experiment.*` claims unchanged.

Out of scope:

- Guessing the pendulum geometry from the plotted PDF.
- Extracting or tracing plot curves from rasterized figure content.
- Claiming paper-faithful physical-pendulum geometry.
- Passing the physical-pendulum experiment.

## Audit Contract

Add `physical_pendulum_geometry_source_audit()` returning a dataclass report
with:

- `status = "source_assets_found_geometry_parameters_missing"`
- `source_root`
- `file_hashes`
- `source_tree_paths`
- `scanned_text_paths`
- `scanned_tex_paths`
- `positive_findings`
- `absence_findings`
- `figure_pdf`
- `missing_parameters`
- `blockers`

The audit must fail loudly if the source root or required files are missing.
It must not hardcode absence: a source tree containing usable physical-pendulum
geometry/data disclosure terms must return manual-review status and must not
emit the public-source geometry-missing blocker.
The report is evidence about public paper assets only. It must not be used to
replace missing method or experiment evidence.

## Claim Boundary

Phase 41 verifies that the paper source assets found locally do not disclose the
physical-pendulum geometry parameters required for a paper-faithful geometry
claim. It does not prove private author assets are absent, does not pass the
physical-pendulum experiment, and does not remove `pendulum_geometry_unknown`.

## Tests

- `tests.test_physical_pendulum_source_audit` verifies the audit status,
  positive paper-source findings, figure PDF hash, source-tree inventory,
  searched text/TeX paths, absence-search behavior, embedded image metadata
  paths, missing geometry parameters, blockers, required-file failures, and the
  manual-review branch for fixture source trees that disclose geometry data.
- `tests.test_phase0_bootstrap` and `scripts/validate_docs.py` verify the
  Phase41 record, claim boundaries, and non-overclaim constraints.
