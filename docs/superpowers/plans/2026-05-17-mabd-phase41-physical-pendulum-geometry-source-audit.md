# Phase 41 Physical Pendulum Geometry Source Audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a machine-checkable audit showing that the public paper source assets contain the physical-pendulum figure and caption facts but do not disclose paper-faithful geometry parameters.

**Architecture:** Extend the existing paper-source audit module with a focused physical-pendulum geometry audit. The audit records positive source facts, hashes the source files, extracts visible PDF metadata image paths, and keeps missing geometry parameters as blockers. Docs and validators enforce that this is an absence/availability audit only.

**Review correction:** The absence claim must be backed by a machine-checkable
full source-tree inventory and negative scan. The audit must return manual-review
status if a fixture source tree discloses usable physical-pendulum geometry or
raw curve data.

**Tech Stack:** Python 3.10, `unittest`, local arXiv TeX/PDF assets, Markdown records, `scripts/validate_docs.py`.

---

## File Map

- Modify `src/mabd_reproduction/paper_source_audit.py`: add physical-pendulum geometry audit dataclasses and helper.
- Add `tests/test_physical_pendulum_source_audit.py`: unit tests for the audit.
- Modify `tests/test_phase0_bootstrap.py`: Phase41 boundary, record, and validator tests.
- Modify `scripts/validate_docs.py`: require Phase41 files and validate audit output.
- Modify `docs/reference/claim-boundaries.md`: add Phase41 bounded claim text.
- Add `docs/records/2026-05-17-phase41-physical-pendulum-geometry-source-audit.md`.

## Task 1: RED Audit Tests

- [ ] **Step 1: Add failing unit tests**

Create `tests/test_physical_pendulum_source_audit.py` with:

```python
from __future__ import annotations

import unittest
from pathlib import Path

from mabd_reproduction.paper_source_audit import (
    physical_pendulum_geometry_source_audit,
)


class PhysicalPendulumSourceAuditTests(unittest.TestCase):
    def test_audit_records_figure_source_and_missing_geometry(self) -> None:
        audit = physical_pendulum_geometry_source_audit()
        report = audit.to_report()

        self.assertEqual(audit.status, "source_assets_found_geometry_parameters_missing")
        self.assertEqual(
            audit.figure_pdf["path"],
            "images/simple_pendulum/simple_pendulum.pdf",
        )
        self.assertEqual(
            audit.file_hashes["sections/experiment.tex"],
            "c5927183fe4e3f1c1c1617e5b10b7e9006da6a9eac537e891cb1dac03d58dd0f",
        )
        self.assertEqual(
            audit.file_hashes["images/simple_pendulum/simple_pendulum.pdf"],
            "4b198ace42ff08d32dc266f1eca710987a2b6335d75878ee01b60498fed945cf",
        )
        self.assertIn("fixed_pivot", audit.positive_findings)
        self.assertIn("horizontal_release_zero_initial_velocity", audit.positive_findings)
        self.assertIn("elliptic_angle_reference", audit.positive_findings)
        self.assertIn("joint_force_magnitude_plot", audit.positive_findings)
        self.assertIn("body_geometry", audit.missing_parameters)
        self.assertIn("mass_distribution", audit.missing_parameters)
        self.assertIn("inertia_tensor", audit.missing_parameters)
        self.assertIn("raw_joint_force_curve_data", audit.missing_parameters)
        self.assertIn(
            "physical_pendulum_geometry_parameters_missing_from_public_source_assets",
            audit.blockers,
        )
        self.assertIn("pendulum15.png", "\n".join(audit.figure_pdf["embedded_image_paths"]))
        self.assertEqual(report["status"], audit.status)

    def test_audit_inventories_and_searches_source_tree(self) -> None:
        audit = physical_pendulum_geometry_source_audit()
        report = audit.to_report()

        self.assertIn("sections_a/multiabd.tex", audit.scanned_tex_paths)
        self.assertIn("ref.bib", audit.scanned_text_paths)
        self.assertIn("images/simple_pendulum/simple_pendulum.pdf", audit.source_tree_paths)
        self.assertGreaterEqual(len(audit.source_tree_paths), 30)

        absence = audit.absence_findings["physical_pendulum_geometry_parameter_search"]
        self.assertEqual(
            absence["status"],
            "no_paper_faithful_physical_pendulum_geometry_parameters_found",
        )
        self.assertEqual(absence["searched_source_path_count"], len(audit.source_tree_paths))
        self.assertEqual(absence["usable_parameter_disclosures"], [])
        self.assertIn("source_tree_paths", report)
        self.assertIn("absence_findings", report)

    def test_geometry_disclosure_triggers_manual_review_instead_of_absence_blocker(self) -> None:
        ...

    def test_audit_requires_experiment_tex_and_figure_pdf(self) -> None:
        ...

    def test_audit_requires_source_root(self) -> None:
        missing = Path("/tmp/mabd-paper/source-does-not-exist")
        with self.assertRaisesRegex(FileNotFoundError, "paper source root does not exist"):
            physical_pendulum_geometry_source_audit(missing)
```

- [ ] **Step 2: Run RED**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_physical_pendulum_source_audit
```

Expected: fail with missing `physical_pendulum_geometry_source_audit`.

## Task 2: Implement Audit Helper

- [ ] **Step 1: Add dataclass and helper**

In `src/mabd_reproduction/paper_source_audit.py`, add:

```python
@dataclass(frozen=True)
class PhysicalPendulumGeometrySourceAudit:
    source_root: str
    file_hashes: dict[str, str]
    positive_findings: dict[str, dict[str, object]]
    figure_pdf: dict[str, object]
    missing_parameters: tuple[str, ...]
    blockers: tuple[str, ...]
    status: str

    def to_report(self) -> dict[str, object]:
        return {
            "source_root": self.source_root,
            "file_hashes": dict(self.file_hashes),
            "positive_findings": dict(self.positive_findings),
            "figure_pdf": dict(self.figure_pdf),
            "missing_parameters": list(self.missing_parameters),
            "blockers": list(self.blockers),
            "status": self.status,
        }
```

Add `physical_pendulum_geometry_source_audit(...)` that reads the full source
tree inventory, scans text/TeX source files, verifies the caption/source snippets
on lines 77-91, hashes `sections/experiment.tex` and
`images/simple_pendulum/simple_pendulum.pdf`, extracts PDF metadata path strings
containing `pendulum`, and returns status
`source_assets_found_geometry_parameters_missing` only when no usable
physical-pendulum geometry/data disclosure is found. If usable disclosure terms
are found in a fixture source tree, return
`source_mentions_physical_pendulum_geometry_parameters_requiring_manual_review`
and omit the public-source geometry-missing blocker.

- [ ] **Step 2: Run GREEN**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_physical_pendulum_source_audit
```

Expected: pass.

## Task 3: Docs And Validator

- [ ] **Step 1: Add Phase41 bootstrap tests**

In `tests/test_phase0_bootstrap.py`, add tests requiring Phase41 claim-boundary
text, record text, and a validator rejection when the audit status is changed
to `geometry_reconstructed`.

- [ ] **Step 2: Extend `scripts/validate_docs.py`**

Require the Phase41 spec, plan, and record paths. Import
`physical_pendulum_geometry_source_audit`, call it in `validate_phase41_record`,
and enforce:

- status `source_assets_found_geometry_parameters_missing`
- positive finding `fixed_pivot`
- full `source_tree_paths`, `scanned_text_paths`, and `scanned_tex_paths`
- `images/simple_pendulum/simple_pendulum.pdf` hash
- absence finding status
  `no_paper_faithful_physical_pendulum_geometry_parameters_found`
- missing parameter `body_geometry`
- blocker `physical_pendulum_geometry_parameters_missing_from_public_source_assets`
- `experiment.single_body.physical_pendulum` remains `intended`
- no `experiment.*` claim is `passed`
- all current physical-pendulum reports remain `incomplete`
- all current physical-pendulum reports retain `pendulum_geometry_unknown`
- comparison keeps `missing_paper_metrics =
  ["joint_force_error:paper_geometry_unknown"]`

- [ ] **Step 3: Update claim boundaries**

Add Phase41 current, verified, non-claim, and forbidden-claim bullets.

## Task 4: Record, Verify, Commit

- [ ] **Step 1: Add Phase41 record**

Create `docs/records/2026-05-17-phase41-physical-pendulum-geometry-source-audit.md`
with the implementation commit, audited file hashes, status, blockers, and
verification commands.

- [ ] **Step 2: Run focused gates**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_physical_pendulum_source_audit tests.test_phase0_bootstrap
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
git diff --check
```

Expected: all pass.

- [ ] **Step 3: Commit**

```bash
git add src/mabd_reproduction/paper_source_audit.py tests/test_physical_pendulum_source_audit.py tests/test_phase0_bootstrap.py scripts/validate_docs.py docs/reference/claim-boundaries.md docs/records/2026-05-17-phase41-physical-pendulum-geometry-source-audit.md docs/superpowers/specs/2026-05-17-phase41-physical-pendulum-geometry-source-audit-design.md docs/superpowers/plans/2026-05-17-mabd-phase41-physical-pendulum-geometry-source-audit.md
git commit -m "Audit physical pendulum geometry source assets"
```
