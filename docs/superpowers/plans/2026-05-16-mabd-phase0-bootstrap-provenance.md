# M-ABD Phase 0 Bootstrap And Provenance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the Phase 0 repository gate for the Newton-first M-ABD reproduction: provenance, claim boundaries, vendored Newton import isolation, docs validation, and the minimal Python package/test skeleton.

**Architecture:** Keep Phase 0 narrow and auditable. The root package owns reproduction metadata and validation helpers, `scripts/validate_docs.py` enforces source/claim/provenance contracts, and `vendor/newton/` is a direct copy of the local Newton tree with a provenance record before any M-ABD solver edits. Solver code begins only after this gate is clean.

**Tech Stack:** Python 3.10+, standard-library `unittest`, `PyYAML`, setuptools, vendored Newton source, shell verification commands.

---

## Phase Boundary

This plan implements only Phase 0 from `docs/superpowers/specs/2026-05-16-mabd-newton-only-full-reproduction-design.md`.

Phase 0 exit criteria:

- Root license exists before implementation code.
- Newton is copied into `vendor/newton/` without its `.git` directory.
- `vendor/newton/PROVENANCE.md` records source URL, commit, dirty status, copy date, copy command, license inventory, patch policy, and import-isolation command.
- Claim boundary source of truth exists at `docs/reference/claim-boundaries.md`.
- Source claim manifest exists at `docs/reference/paper-claims.yaml`.
- Documentation/metadata validator exists and passes.
- Minimal Python package exists for future report/schema code.
- Unit tests validate the bootstrap contracts.
- A dated Phase 0 record exists under `docs/records/`.
- All Phase 0 commands pass and the result is committed before Phase 1.

## File Structure

- Create `AGENTS.md`: repo-local operating rules, claim boundaries, artifact policy, and canonical commands.
- Create `.gitignore`: ignore Python caches, generated reports/artifacts, and local virtual environments while keeping manifests and vendored source trackable.
- Create `LICENSE.md`: root Apache-2.0 license aligned with vendored Newton.
- Create `pyproject.toml`: installable package metadata and dev dependencies.
- Create `src/mabd_reproduction/__init__.py`: package version and public package marker.
- Create `src/mabd_reproduction/reporting.py`: small dataclass/status contract used by tests and future reports.
- Create `scripts/validate_docs.py`: repository validator for Phase 0 docs, claim manifest, provenance, and import isolation.
- Create `docs/operations/environment.md`: local validation environment contract that avoids mutating shared interpreters.
- Create `tests/test_phase0_bootstrap.py`: unit tests for validator, report statuses, YAML manifest, and vendored Newton import resolution.
- Create `docs/reference/claim-boundaries.md`: current/intended/verified claim source of truth.
- Create `docs/reference/paper-claims.yaml`: claim traceability manifest seeded from the paper source review.
- Create `docs/records/README.md`: record contract.
- Create `docs/records/2026-05-16-phase0-bootstrap-provenance.md`: Phase 0 evidence record.
- Create `reports/README.md`: generated report policy.
- Create `assets/manifests/README.md`: asset manifest policy.
- Create `configs/experiments/README.md`: experiment config contract.
- Create `vendor/newton/`: copied local Newton source.
- Create `vendor/newton/PROVENANCE.md`: vendored Newton provenance.

## Task 1: Add Project Governance Files

**Files:**

- Create: `AGENTS.md`
- Create: `.gitignore`
- Create: `LICENSE.md`
- Create: `pyproject.toml`
- Create: `src/mabd_reproduction/__init__.py`
- Create: `src/mabd_reproduction/reporting.py`

- [ ] **Step 1: Write root project files**

Create `AGENTS.md` with:

```markdown
# Agent Rules

## Project Context

This repository is a Newton-first reproduction of "M-ABD: Scalable, Efficient,
and Robust Multi-Affine-Body Dynamics". The current repository claim is
bootstrap/provenance until method and experiment records prove more.

## Priority Order

1. Preserve the claim boundaries in `docs/reference/claim-boundaries.md`.
2. Keep Newton source provenance and local patches auditable.
3. Keep reproduction configs, manifests, records, and reports machine-checkable.
4. Prefer small tested gates over broad unverified solver changes.

## Claim Boundary Rules

- Do not claim M-ABD is implemented until `SolverMABD` code and method records exist.
- Do not claim full paper reproduction until every required paper claim is passed or explicitly incomplete.
- Do not claim unmodified Newton supports affine-body dynamics.
- Do not claim rigid `body_q` proxy collision is paper-faithful affine collision.
- Do not claim comparative baselines without installed, run, and recorded adapters.

## Source And Documentation Rules

- Durable design lives under `docs/superpowers/specs/`.
- Executable implementation plans live under `docs/superpowers/plans/`.
- Source claim boundaries live in `docs/reference/claim-boundaries.md`.
- Paper claim mappings live in `docs/reference/paper-claims.yaml`.
- Dated evidence records live under `docs/records/`.

## Artifact Policy

- Do not commit generated videos, large raw logs, simulation run directories, or raw paper assets.
- Commit small configs, manifests, tests, source code, and Markdown records.
- Paper PDF/TeX checksums may be recorded; do not vendor paper files unless a manifest proves license compatibility.

## Commands

- Canonical Python: `/cpfs/user/zhuzihou/conda-managed/envs/physics-primitive-newton-py310/bin/python`
- Do not install into the ambient DSW Python or mutate the shared Newton environment during routine validation.
- Validate docs and provenance: `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/physics-primitive-newton-py310/bin/python scripts/validate_docs.py`
- Run tests: `PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/physics-primitive-newton-py310/bin/python -m unittest discover -s tests`
- Check vendored Newton import: `PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/physics-primitive-newton-py310/bin/python -c "import newton; print(newton.__file__)"`
- Whitespace check: `git diff --check`
```

Create `.gitignore` with:

```gitignore
.worktrees/
__pycache__/
*.py[cod]
*.egg-info/
.pytest_cache/
.ruff_cache/
.mypy_cache/
.coverage
htmlcov/
.venv/
venv/
build/
dist/
reports/generated/
reports/raw/
docs/records/generated/
assets/raw/
*.usd
*.usda
*.usdc
*.mp4
*.mov
*.avi
*.log
```

Create `LICENSE.md` by copying `/cpfs/user/zhuzihou/dev/newton/LICENSE.md`.

Create `pyproject.toml` with:

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "mabd-newton"
version = "0.1.0"
description = "Newton-first reproduction scaffold for Multi-Affine-Body Dynamics"
requires-python = ">=3.10"
dependencies = [
    "PyYAML>=6.0",
]

[project.optional-dependencies]
dev = [
    "ruff>=0.4",
]
newton = [
    "warp-lang>=1.13.0",
]

[tool.setuptools.package-dir]
"" = "src"

[tool.setuptools.packages.find]
where = ["src"]

[tool.ruff]
target-version = "py310"
line-length = 100
```

Create `src/mabd_reproduction/__init__.py` with:

```python
"""Reproduction helpers for the Newton-first M-ABD implementation."""

__all__ = ["__version__"]

__version__ = "0.1.0"
```

Create `src/mabd_reproduction/reporting.py` with:

```python
"""Shared report status contracts for M-ABD reproduction evidence."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class EvidenceStatus(StrEnum):
    """Allowed machine-readable reproduction statuses."""

    PASSED = "passed"
    FAILED = "failed"
    INCOMPLETE = "incomplete"
    NOT_VERIFIED = "not_verified"
    UNSUPPORTED = "unsupported"
    QUALITATIVE_RECONSTRUCTION = "qualitative_reconstruction"


@dataclass(frozen=True)
class ClaimReport:
    """Minimal report record shared by future runners and validators."""

    claim_id: str
    scene_id: str
    solver_mode: str
    backend: str
    baseline_lane: str
    expected: dict[str, Any]
    observed: dict[str, Any]
    threshold: dict[str, Any]
    unit: str
    status: EvidenceStatus
    failure_reason: str
    source_commit: str
    vendored_newton_commit: str
    paper_source_version: str


REQUIRED_REPORT_KEYS = frozenset(ClaimReport.__dataclass_fields__)
```

- [ ] **Step 2: Run formatting-neutral checks**

Run:

```bash
MABD_PYTHON=/cpfs/user/zhuzihou/conda-managed/envs/physics-primitive-newton-py310/bin/python
"$MABD_PYTHON" -m py_compile src/mabd_reproduction/__init__.py src/mabd_reproduction/reporting.py
git diff --check
```

Expected: both commands exit with status `0`.

- [ ] **Step 3: Commit governance package**

Run:

```bash
git add AGENTS.md .gitignore LICENSE.md pyproject.toml src/mabd_reproduction
git commit -m "chore: add M-ABD repo bootstrap package"
```

Expected: commit succeeds.

## Task 2: Add Claim Boundary And Paper Claim Manifest

**Files:**

- Create: `docs/reference/claim-boundaries.md`
- Create: `docs/reference/paper-claims.yaml`
- Create: `docs/records/README.md`
- Create: `reports/README.md`
- Create: `assets/manifests/README.md`
- Create: `configs/experiments/README.md`
- Create: `docs/operations/environment.md`

- [ ] **Step 1: Write claim-boundary source of truth**

Create `docs/reference/claim-boundaries.md` with:

```markdown
# Claim Boundaries

## Current

- This repository contains a reviewed Newton-first design for reproducing
  "M-ABD: Scalable, Efficient, and Robust Multi-Affine-Body Dynamics".
- This repository contains Phase 0 provenance, manifests, validation scripts,
  and bootstrap tests after the Phase 0 record is created.

## Intended

- Vendor Newton and implement a paper-faithful `newton.solvers.SolverMABD`.
- Reproduce the paper method with affine state, equality joint constraints,
  topology solvers, contact/reporting lanes, and dense oracles.
- Reproduce paper evidence through configs, asset manifests, metrics, reports,
  and baseline lanes where required.

## Verified

- No method-level M-ABD result is verified at Phase 0.
- No experiment, timing, or comparative baseline result is verified at Phase 0.

## Forbidden Claims

- Unmodified Newton already supports M-ABD.
- Existing Newton rigid-body solvers are equivalent to the M-ABD method.
- A rigid `body_q` proxy is paper-faithful affine collision.
- The project implements generic inequality-constrained M-ABD KKT.
- Comparative baselines are reproduced before their adapters, configs, raw logs,
  and reports exist.
- CPU timings are paper-comparable without matching benchmark protocol and
  recorded hardware/threading conditions.

## Evidence Record Requirements

Each verified claim needs a dated record with the command, config path, repo
commit, vendored Newton source commit, paper source version, environment,
backend, seed, metrics, thresholds, raw artifacts, and status.
```

- [ ] **Step 2: Write paper claim manifest**

Create `docs/reference/paper-claims.yaml` with:

```yaml
paper:
  title: "M-ABD: Scalable, Efficient, and Robust Multi-Affine-Body Dynamics"
  arxiv_id: "2603.08079"
  arxiv_version: "v2"
  siggraph_url: "https://s2026.conference-schedule.org/presentation/?id=papers_116&sess=sess102"
  pdf_url: "https://arxiv.org/pdf/2603.08079"
  tex_source_url: "https://arxiv.org/e-print/2603.08079"
  pdf_sha256: "a594e79093673c60fc59ad14f9b71f29a8f7f8e7b1c3d9c73efe6f5814cc6ec0"
  tex_source_sha256: "73ec398956c606dec2f8f40f0d38b9d5370e11b27830775e1b3765fe0efc563f"
  local_pdf: "/tmp/mabd-paper/mabd.pdf"
  local_tex_source: "/tmp/mabd-paper/source"
manifest_version: 1
status_vocabulary:
  - intended
  - passed
  - failed
  - incomplete
  - not_verified
  - unsupported
  - qualitative_reconstruction
claims:
  - claim_id: method.single_body.affine_kinematics
    source_path: "/tmp/mabd-paper/source/sections/singleabd.tex"
    source_line: "ABD kinematics and affine state definition"
    expected_value: "x_i = A xbar_i + t with q in R12"
    unit: "equation"
    conflict_note: "none"
    reproduction_status: intended
  - claim_id: method.single_body.corotated_stiffness
    source_path: "/tmp/mabd-paper/source/sections/singleabd.tex"
    source_line: "rest generalized stiffness and co-rotated force assembly"
    expected_value: "H_A_bar = M_A / h^2 + K_A_bar and volume-weighted Jbar^T f"
    unit: "equation"
    conflict_note: "none"
    reproduction_status: intended
  - claim_id: method.single_body.no_polar_mode
    source_path: "/tmp/mabd-paper/source/sections/singleabd.tex"
    source_line: "polar and no-polar normalized block variants"
    expected_value: "polar and no-polar rotation handling supported"
    unit: "algorithm"
    conflict_note: "none"
    reproduction_status: intended
  - claim_id: method.single_body.twist_wrench_maps
    source_path: "/tmp/mabd-paper/source/sections/singleabd.tex"
    source_line: "G(A), E(A), and virtual-work force mapping"
    expected_value: "G(A)E(A)=I and spatial wrench maps to affine generalized force"
    unit: "identity"
    conflict_note: "none"
    reproduction_status: intended
  - claim_id: method.joints.ball
    source_path: "/tmp/mabd-paper/source/sections_a/multiabd.tex"
    source_line: "ball joint control point constraints"
    expected_value: "rank 3 ball joint constraint"
    unit: "rank"
    conflict_note: "none"
    reproduction_status: intended
  - claim_id: method.joints.hinge
    source_path: "/tmp/mabd-paper/source/sections_a/multiabd.tex"
    source_line: "hinge joint control point constraints"
    expected_value: "rank 5 hinge joint constraint"
    unit: "rank"
    conflict_note: "none"
    reproduction_status: intended
  - claim_id: method.joints.universal
    source_path: "/tmp/mabd-paper/source/sections_a/multiabd.tex"
    source_line: "universal joint equation"
    expected_value: "rank 4 universal joint constraint"
    unit: "rank"
    conflict_note: "paper figure caption appears inconsistent with equation; reproduction follows equation"
    reproduction_status: intended
  - claim_id: method.joints.prismatic
    source_path: "/tmp/mabd-paper/source/sections_a/multiabd.tex"
    source_line: "prismatic joint control point constraints"
    expected_value: "rank 5 prismatic joint constraint"
    unit: "rank"
    conflict_note: "none"
    reproduction_status: intended
  - claim_id: method.kkt.residual_corrected_rhs
    source_path: "/tmp/mabd-paper/source/sections/solver.tex"
    source_line: "dual KKT lower RHS and footnote correction"
    expected_value: "support paper-simplified zero RHS and residual-corrected -C(q_n)"
    unit: "equation"
    conflict_note: "paper display and correction footnote differ"
    reproduction_status: intended
  - claim_id: experiment.single_body.rolling_spinning
    source_path: "/tmp/mabd-paper/source/sections/experiment.tex"
    source_line: "single-body ABD vs RBD rolling and spinning tests"
    expected_value: "rolling/spinning timing and behavior metrics"
    unit: "scene"
    conflict_note: "full comparative evidence requires baseline lanes"
    reproduction_status: intended
  - claim_id: experiment.single_body.spinning_box
    source_path: "/tmp/mabd-paper/source/sections/experiment.tex"
    source_line: "spinning box diagnostics"
    expected_value: "momentum and energy diagnostics"
    unit: "scene"
    conflict_note: "none"
    reproduction_status: intended
  - claim_id: experiment.single_body.t_handle
    source_path: "/tmp/mabd-paper/source/sections/experiment.tex"
    source_line: "T-handle intermediate-axis instability"
    expected_value: "flip timing and angular-velocity waveform"
    unit: "scene"
    conflict_note: "none"
    reproduction_status: intended
  - claim_id: experiment.single_body.heavy_top
    source_path: "/tmp/mabd-paper/source/sections/experiment.tex"
    source_line: "heavy top"
    expected_value: "precession and nutation curve"
    unit: "scene"
    conflict_note: "none"
    reproduction_status: intended
  - claim_id: experiment.single_body.physical_pendulum
    source_path: "/tmp/mabd-paper/source/sections/experiment.tex"
    source_line: "physical pendulum"
    expected_value: "angle and joint-force comparison to analytic reference"
    unit: "scene"
    conflict_note: "none"
    reproduction_status: intended
  - claim_id: experiment.joints.heavy_end_chain
    source_path: "/tmp/mabd-paper/source/sections/experiment.tex"
    source_line: "heavy-end chain robustness"
    expected_value: "stable constrained chain under heavy end load"
    unit: "scene"
    conflict_note: "none"
    reproduction_status: intended
  - claim_id: experiment.joints.ball_joint_nets
    source_path: "/tmp/mabd-paper/source/sections/experiment.tex"
    source_line: "hanging ball-joint nets and scaling"
    expected_value: "20x20, 50x50, and 100x100 net scaling"
    unit: "scene"
    conflict_note: "assets and exact parameters must be sourced or reconstructed"
    reproduction_status: intended
  - claim_id: experiment.joints.pulley
    source_path: "/tmp/mabd-paper/source/sections/experiment.tex"
    source_line: "pulley and huge pulley"
    expected_value: "pulley and huge pulley stress tests"
    unit: "scene"
    conflict_note: "none"
    reproduction_status: intended
  - claim_id: experiment.hierarchy.trees
    source_path: "/tmp/mabd-paper/source/sections/experiment.tex"
    source_line: "willow and pear tree tests"
    expected_value: "hierarchical tree tests"
    unit: "scene"
    conflict_note: "scene asset availability must be proven by manifest"
    reproduction_status: intended
  - claim_id: experiment.cloak
    source_path: "/tmp/mabd-paper/source/sections/experiment.tex"
    source_line: "net cloak scene"
    expected_value: "net cloak dynamics"
    unit: "scene"
    conflict_note: "asset availability must be proven by manifest"
    reproduction_status: intended
  - claim_id: experiment.armadillo_coupling
    source_path: "/tmp/mabd-paper/source/sections/experiment.tex"
    source_line: "armadillo coupling scene"
    expected_value: "coupled armadillo simulation"
    unit: "scene"
    conflict_note: "asset availability must be proven by manifest"
    reproduction_status: intended
  - claim_id: experiment.ragdoll_on_net
    source_path: "/tmp/mabd-paper/source/sections/experiment.tex"
    source_line: "ragdoll-on-net scene and Table 1 timing"
    expected_value: "ragdoll-on-net dynamics and timing"
    unit: "scene"
    conflict_note: "Table 1 and experiment text report different ragdoll timings; separate timing claims required in Phase 4/5"
    reproduction_status: intended
  - claim_id: experiment.mixed_joints.falling
    source_path: "/tmp/mabd-paper/source/sections/experiment.tex"
    source_line: "falling mixed joints"
    expected_value: "ball, universal, hinge, and prismatic pairs"
    unit: "scene"
    conflict_note: "none"
    reproduction_status: intended
  - claim_id: experiment.robot.franka
    source_path: "/tmp/mabd-paper/source/sections/experiment.tex"
    source_line: "Franka pick-and-place"
    expected_value: "robot-like actuation mapping and pick-place scene"
    unit: "scene"
    conflict_note: "requires tested actuation mapping before verification"
    reproduction_status: intended
  - claim_id: experiment.protein_chain
    source_path: "/tmp/mabd-paper/source/sections/experiment.tex"
    source_line: "protein chain reconstruction"
    expected_value: "protein chain reconstruction scene"
    unit: "scene"
    conflict_note: "asset/source availability must be proven by manifest"
    reproduction_status: intended
```

- [ ] **Step 3: Write artifact directory README files**

Create `docs/records/README.md` with:

```markdown
# Verification Records

Dated records are the durable evidence trail for this reproduction.

Each record must include:

- date
- status
- command
- config path
- repository commit
- vendored Newton source commit and patch status
- paper source version and checksums
- backend and environment
- random seed when applicable
- metrics, thresholds, artifact paths, and claim impact
```

Create `reports/README.md` with:

```markdown
# Reports

Generated tables, plots, JSON summaries, and raw time series belong under this
directory. Commit small summary files only when they are part of a dated record.
Large generated outputs belong in ignored subdirectories such as
`reports/generated/` or `reports/raw/`.
```

Create `assets/manifests/README.md` with:

```markdown
# Asset Manifests

Each paper or reconstructed asset needs a manifest with source URI or local path,
license, checksum, geometry counts or skeleton counts, reconstruction script and
seed when procedural, status, and whether it can support full paper evidence.
Raw asset files are not committed unless their license and size are acceptable.
```

Create `configs/experiments/README.md` with:

```markdown
# Experiment Configs

Each experiment config must list claim IDs, geometry, asset manifest, materials,
joints, initial state, forces, actuation, contact, duration, time-step grid,
solver budget, backend, random seed, metrics, paper claims, and output paths.
Paper-missing values must be represented as `unknown_in_source` or
`not_applicable`.
```

- [ ] **Step 4: Write environment contract**

Create `docs/operations/environment.md` with:

```markdown
# Environment Contract

## Canonical Local Runtime

Use the already-created Newton Python environment from the reference project:

```text
/cpfs/user/zhuzihou/conda-managed/envs/physics-primitive-newton-py310
```

Canonical interpreter:

```text
/cpfs/user/zhuzihou/conda-managed/envs/physics-primitive-newton-py310/bin/python
```

This environment already contains Newton runtime dependencies such as
`warp-lang==1.13.0`, `PyYAML`, and the importer stack validated by
`physics-primitive-agent`.

## Non-Pollution Rule

Routine validation in this repository must not install packages into the ambient
Isaac/DSW Python, the shared reference Newton environment, or the local vendored
Newton tree.

Use `PYTHONPATH` to point at this repository's source and vendored Newton copy
instead of running `pip install -e .` during normal validation.

## Commands

```bash
MABD_PYTHON=/cpfs/user/zhuzihou/conda-managed/envs/physics-primitive-newton-py310/bin/python
PYTHONPATH=src:vendor/newton "$MABD_PYTHON" scripts/validate_docs.py
PYTHONPATH=src:vendor/newton "$MABD_PYTHON" -m unittest discover -s tests
PYTHONPATH=vendor/newton "$MABD_PYTHON" -c "import newton; print(newton.__file__)"
```

The import check must print a path under this repository's `vendor/newton`
directory. If it imports `/cpfs/user/zhuzihou/dev/newton`, the `PYTHONPATH` is
wrong for this repo.

## Dependency Changes

Dependency installation is an explicit environment-maintenance action, not part
of Phase 0 validation. If a future phase needs dependency mutation, record the
interpreter path, command, indexes, package versions, and reason in
`docs/records/` before using the mutated environment for evidence.
```

- [ ] **Step 5: Validate YAML syntax**

Run:

```bash
MABD_PYTHON=/cpfs/user/zhuzihou/conda-managed/envs/physics-primitive-newton-py310/bin/python
"$MABD_PYTHON" - <<'PY'
from pathlib import Path
import yaml
data = yaml.safe_load(Path("docs/reference/paper-claims.yaml").read_text())
assert data["paper"]["arxiv_id"] == "2603.08079"
assert len(data["claims"]) >= 20
assert {c["reproduction_status"] for c in data["claims"]} == {"intended"}
print("paper claim manifest ok")
PY
```

Expected output contains:

```text
paper claim manifest ok
```

- [ ] **Step 6: Commit reference docs**

Run:

```bash
git add docs/reference docs/records/README.md docs/operations/environment.md reports/README.md assets/manifests/README.md configs/experiments/README.md
git commit -m "docs: add M-ABD claim and artifact manifests"
```

Expected: commit succeeds.

## Task 3: Vendor Newton With Provenance

**Files:**

- Create/modify tree: `vendor/newton/`
- Create: `vendor/newton/PROVENANCE.md`

- [ ] **Step 1: Copy local Newton source**

Run:

```bash
mkdir -p vendor
rsync -a --delete \
  --exclude .git \
  --exclude __pycache__ \
  --exclude .pytest_cache \
  --exclude .mypy_cache \
  --exclude .ruff_cache \
  /cpfs/user/zhuzihou/dev/newton/ vendor/newton/
```

Expected: `vendor/newton/newton/solvers.py` and `vendor/newton/LICENSE.md` exist, and `vendor/newton/.git` does not exist.

- [ ] **Step 2: Write provenance**

Create `vendor/newton/PROVENANCE.md` with:

```markdown
# Vendored Newton Provenance

## Source

- Upstream URL: `https://github.com/newton-physics/newton.git`
- Local source path: `/cpfs/user/zhuzihou/dev/newton`
- Source commit: `96713fa965463b69c229a4d30582c733ff3526bb`
- Source status at copy time: clean on `main` against `origin/main`
- Copy date: `2026-05-16`
- Copy command:

```bash
rsync -a --delete \
  --exclude .git \
  --exclude __pycache__ \
  --exclude .pytest_cache \
  --exclude .mypy_cache \
  --exclude .ruff_cache \
  /cpfs/user/zhuzihou/dev/newton/ vendor/newton/
```

## License Inventory

- `vendor/newton/LICENSE.md`: Newton Apache-2.0 license.
- `vendor/newton/newton/licenses/CC-BY-4.0.txt`: Creative Commons Attribution 4.0 license text.
- `vendor/newton/newton/licenses/unittest-parallel-LICENSE.txt`: unittest-parallel license text.
- `vendor/newton/newton/licenses/viser_and_inter-font-family.txt`: viser and Inter font family license notices.

## Local Patch Policy

All M-ABD changes must be made inside this repository. Modified vendored Newton
files must keep upstream notices intact and include prominent modification
notes where required by Apache-2.0. Every solver-facing patch needs tests under
`vendor/newton/newton/tests/` or root `tests/`, plus a dated record when it
changes reproduction evidence.

## Import Isolation Check

Run:

```bash
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/physics-primitive-newton-py310/bin/python -c "import newton; print(newton.__file__)"
```

Expected output path begins with this repository and contains:

```text
vendor/newton/newton/__init__.py
```
```

- [ ] **Step 3: Verify vendored copy and import isolation**

Run:

```bash
test -f vendor/newton/newton/solvers.py
test -f vendor/newton/LICENSE.md
test ! -d vendor/newton/.git
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/physics-primitive-newton-py310/bin/python -c "import newton; print(newton.__file__)"
```

Expected: tests exit `0`; import path contains `vendor/newton/newton/__init__.py`.

- [ ] **Step 4: Commit vendored Newton**

Run:

```bash
git add vendor/newton
git commit -m "chore: vendor Newton source for M-ABD"
```

Expected: commit succeeds.

## Task 4: Add Phase 0 Validator And Tests

**Files:**

- Create: `scripts/validate_docs.py`
- Create: `tests/test_phase0_bootstrap.py`

- [ ] **Step 1: Write failing unit tests**

Create `tests/test_phase0_bootstrap.py` with:

```python
from __future__ import annotations

import subprocess
import sys
import unittest
import os
from pathlib import Path

import yaml

from mabd_reproduction.reporting import EvidenceStatus, REQUIRED_REPORT_KEYS


ROOT = Path(__file__).resolve().parents[1]


class Phase0BootstrapTests(unittest.TestCase):
    def test_report_status_vocabulary_matches_spec(self) -> None:
        self.assertEqual(
            {status.value for status in EvidenceStatus},
            {
                "passed",
                "failed",
                "incomplete",
                "not_verified",
                "unsupported",
                "qualitative_reconstruction",
            },
        )
        self.assertIn("claim_id", REQUIRED_REPORT_KEYS)
        self.assertIn("vendored_newton_commit", REQUIRED_REPORT_KEYS)

    def test_claim_manifest_has_required_source_material(self) -> None:
        data = yaml.safe_load((ROOT / "docs/reference/paper-claims.yaml").read_text())
        self.assertEqual(data["paper"]["arxiv_id"], "2603.08079")
        self.assertEqual(data["paper"]["arxiv_version"], "v2")
        self.assertGreaterEqual(len(data["claims"]), 20)
        claim_ids = {claim["claim_id"] for claim in data["claims"]}
        self.assertIn("method.joints.universal", claim_ids)
        self.assertIn("experiment.ragdoll_on_net", claim_ids)
        universal = next(c for c in data["claims"] if c["claim_id"] == "method.joints.universal")
        self.assertIn("inconsistent", universal["conflict_note"])

    def test_claim_boundaries_refuse_method_claims_at_phase0(self) -> None:
        text = (ROOT / "docs/reference/claim-boundaries.md").read_text()
        self.assertIn("## Current", text)
        self.assertIn("## Intended", text)
        self.assertIn("## Verified", text)
        self.assertIn("No method-level M-ABD result is verified at Phase 0.", text)

    def test_vendored_newton_import_resolves_inside_repo(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "import newton; print(newton.__file__)",
            ],
            cwd=ROOT,
            env={**os.environ, "PYTHONPATH": str(ROOT / "vendor/newton")},
            text=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.assertIn("vendor/newton/newton/__init__.py", result.stdout.replace("\\", "/"))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests and verify the validator is missing**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/physics-primitive-newton-py310/bin/python -m unittest discover -s tests
test ! -f scripts/validate_docs.py
```

Expected: unit tests pass if earlier tasks are complete; the second command exits `0`, proving the validator still needs implementation.

- [ ] **Step 3: Implement validator**

Create `scripts/validate_docs.py` with:

```python
#!/usr/bin/env python3
"""Validate Phase 0 documentation, provenance, and claim manifests."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_PATHS = (
    "AGENTS.md",
    "LICENSE.md",
    "pyproject.toml",
    "docs/reference/claim-boundaries.md",
    "docs/reference/paper-claims.yaml",
    "docs/records/README.md",
    "reports/README.md",
    "assets/manifests/README.md",
    "configs/experiments/README.md",
    "vendor/newton/PROVENANCE.md",
    "vendor/newton/LICENSE.md",
    "vendor/newton/newton/solvers.py",
)
STATUS_VALUES = {
    "intended",
    "passed",
    "failed",
    "incomplete",
    "not_verified",
    "unsupported",
    "qualitative_reconstruction",
}


def fail(message: str) -> None:
    raise SystemExit(f"validate_docs.py: {message}")


def read_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        fail(f"{path} must contain a YAML mapping")
    return data


def require_paths() -> None:
    missing = [path for path in REQUIRED_PATHS if not (ROOT / path).exists()]
    if missing:
        fail("missing required paths: " + ", ".join(missing))
    if (ROOT / "vendor/newton/.git").exists():
        fail("vendor/newton must not contain an embedded .git directory")


def validate_claim_boundaries() -> None:
    text = (ROOT / "docs/reference/claim-boundaries.md").read_text(encoding="utf-8")
    for heading in ("## Current", "## Intended", "## Verified", "## Forbidden Claims"):
        if heading not in text:
            fail(f"claim-boundaries.md missing {heading}")
    if "No method-level M-ABD result is verified at Phase 0." not in text:
        fail("claim-boundaries.md must explicitly deny Phase 0 method verification")


def validate_paper_claims() -> None:
    data = read_yaml(ROOT / "docs/reference/paper-claims.yaml")
    paper = data.get("paper")
    claims = data.get("claims")
    if not isinstance(paper, dict):
        fail("paper-claims.yaml missing paper mapping")
    if paper.get("arxiv_id") != "2603.08079":
        fail("paper-claims.yaml arxiv_id must be 2603.08079")
    if paper.get("arxiv_version") != "v2":
        fail("paper-claims.yaml arxiv_version must be v2")
    if not isinstance(claims, list) or len(claims) < 20:
        fail("paper-claims.yaml must contain at least 20 seeded claims")

    seen: set[str] = set()
    required_fields = {
        "claim_id",
        "source_path",
        "source_line",
        "expected_value",
        "unit",
        "conflict_note",
        "reproduction_status",
    }
    for claim in claims:
        if not isinstance(claim, dict):
            fail("each paper claim must be a mapping")
        missing = sorted(required_fields - set(claim))
        if missing:
            fail(f"{claim.get('claim_id', '<unknown>')} missing fields: {', '.join(missing)}")
        claim_id = str(claim["claim_id"])
        if claim_id in seen:
            fail(f"duplicate claim_id {claim_id}")
        seen.add(claim_id)
        status = str(claim["reproduction_status"])
        if status not in STATUS_VALUES:
            fail(f"{claim_id} has invalid reproduction_status {status}")

    for claim_id in (
        "method.single_body.affine_kinematics",
        "method.joints.universal",
        "method.kkt.residual_corrected_rhs",
        "experiment.ragdoll_on_net",
        "experiment.robot.franka",
        "experiment.protein_chain",
    ):
        if claim_id not in seen:
            fail(f"paper-claims.yaml missing required claim {claim_id}")


def validate_provenance() -> None:
    text = (ROOT / "vendor/newton/PROVENANCE.md").read_text(encoding="utf-8")
    required_snippets = (
        "https://github.com/newton-physics/newton.git",
        "96713fa965463b69c229a4d30582c733ff3526bb",
        "rsync -a --delete",
        "vendor/newton/newton/__init__.py",
        "Local Patch Policy",
    )
    for snippet in required_snippets:
        if snippet not in text:
            fail(f"PROVENANCE.md missing {snippet}")


def validate_newton_import() -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "vendor/newton")
    result = subprocess.run(
        [sys.executable, "-c", "import newton; print(newton.__file__)"],
        cwd=ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        fail("vendored newton import failed: " + result.stderr.strip())
    if "vendor/newton/newton/__init__.py" not in result.stdout.replace("\\", "/"):
        fail("import newton did not resolve to vendor/newton: " + result.stdout.strip())


def main() -> int:
    require_paths()
    validate_claim_boundaries()
    validate_paper_claims()
    validate_provenance()
    validate_newton_import()
    print("Phase 0 docs/provenance validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run validator and tests**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/physics-primitive-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/physics-primitive-newton-py310/bin/python -m unittest discover -s tests
```

Expected output contains:

```text
Phase 0 docs/provenance validation passed
OK
```

- [ ] **Step 5: Commit validator and tests**

Run:

```bash
git add scripts/validate_docs.py tests/test_phase0_bootstrap.py
git commit -m "test: validate Phase 0 M-ABD bootstrap"
```

Expected: commit succeeds.

## Task 5: Add Phase 0 Evidence Record

**Files:**

- Create: `docs/records/2026-05-16-phase0-bootstrap-provenance.md`

- [ ] **Step 1: Run final Phase 0 verification commands**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/physics-primitive-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/physics-primitive-newton-py310/bin/python -m unittest discover -s tests
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/physics-primitive-newton-py310/bin/python -c "import newton; print(newton.__file__)"
git diff --check
git status --short --branch
```

Expected:

- Validator prints `Phase 0 docs/provenance validation passed`.
- Unit tests end with `OK`.
- Newton import path contains `vendor/newton/newton/__init__.py`.
- `git diff --check` exits `0`.
- `git status --short --branch` shows only the uncommitted Phase 0 record, if all previous commits were made.

- [ ] **Step 2: Write the evidence record**

Create `docs/records/2026-05-16-phase0-bootstrap-provenance.md` with:

```markdown
# 2026-05-16 Phase 0 Bootstrap And Provenance

## Date

2026-05-16

## Status

Complete for Phase 0 bootstrap. This record does not verify any M-ABD method,
scene, timing, or comparative baseline claim.

## Commands

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/physics-primitive-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/physics-primitive-newton-py310/bin/python -m unittest discover -s tests
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/physics-primitive-newton-py310/bin/python -c "import newton; print(newton.__file__)"
git diff --check
git status --short --branch
```

## Expected Results

- Documentation/provenance validator passes.
- Unit tests pass.
- `import newton` resolves inside `vendor/newton`.
- Whitespace check passes.
- Working tree is clean after this record is committed.

## Source Versions

- Paper: arXiv `2603.08079v2`
- Paper PDF sha256: `a594e79093673c60fc59ad14f9b71f29a8f7f8e7b1c3d9c73efe6f5814cc6ec0`
- Paper TeX source sha256: `73ec398956c606dec2f8f40f0d38b9d5370e11b27830775e1b3765fe0efc563f`
- Vendored Newton source commit: `96713fa965463b69c229a4d30582c733ff3526bb`
- Vendored Newton copy status: copied from clean local source without `.git`

## Artifacts

- Claim boundaries: `docs/reference/claim-boundaries.md`
- Paper claim manifest: `docs/reference/paper-claims.yaml`
- Vendored Newton provenance: `vendor/newton/PROVENANCE.md`
- Validator: `scripts/validate_docs.py`
- Tests: `tests/test_phase0_bootstrap.py`

## Claim Impact

- Current claim expands from reviewed design only to reviewed design plus
  Phase 0 bootstrap/provenance infrastructure.
- No solver, scene, baseline, contact, timing, or full-reproduction claim is
  verified by this record.

## Next Phase

Phase 1 starts single-body ABD implementation with dense CPU oracles, affine
state tests, co-rotated stiffness, polar/no-polar modes, and invariants.
```

- [ ] **Step 3: Run final verification after record creation**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/physics-primitive-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/physics-primitive-newton-py310/bin/python -m unittest discover -s tests
git diff --check
```

Expected: all commands exit with status `0`.

- [ ] **Step 4: Commit Phase 0 record**

Run:

```bash
git add docs/records/2026-05-16-phase0-bootstrap-provenance.md
git commit -m "docs: record Phase 0 M-ABD bootstrap"
```

Expected: commit succeeds.

## Task 6: Phase 0 Completion Gate

**Files:**

- Modify: none unless verification exposes a failure.

- [ ] **Step 1: Run completion gate**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/physics-primitive-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/physics-primitive-newton-py310/bin/python -m unittest discover -s tests
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/physics-primitive-newton-py310/bin/python -c "import newton; print(newton.__file__)"
git diff --check
git status --short --branch
git log --oneline -5
```

Expected:

- Validator prints `Phase 0 docs/provenance validation passed`.
- Unit tests end with `OK`.
- Newton import path contains `vendor/newton/newton/__init__.py`.
- `git diff --check` exits `0`.
- `git status --short --branch` shows no uncommitted files.
- Recent log includes commits for repo bootstrap package, claim/artifact manifests, vendored Newton, validator/tests, and Phase 0 record.

- [ ] **Step 2: Attempt remote push**

Run:

```bash
git push -u origin main
```

Expected if network is available: push succeeds. If the environment reports `Proxy CONNECT aborted`, record the push failure in the final status and leave local commits intact.

## Self-Review

Spec coverage for Phase 0:

- License/provenance: Task 1 and Task 3.
- Vendored Newton import isolation: Task 3, Task 4, and Task 6.
- Docs validator: Task 4.
- Claim-boundary doc: Task 2.
- Source manifests: Task 2.
- Initial bootstrap files listed in the spec: Tasks 1 through 4.
- Records and commands before next phase: Task 5 and Task 6.

Intentional gaps beyond Phase 0:

- `SolverMABD`, affine state, dense oracles, joints, KKT solvers, scene runners,
  baseline adapters, and performance evidence are Phase 1 through Phase 5 work.
- Phase 0 must not mark any of those claims as verified.

Placeholder scan:

- The plan contains no unresolved-marker text, no open implementation
  placeholders, and no generic test steps without concrete test code.

Type consistency:

- `EvidenceStatus`, `ClaimReport`, and `REQUIRED_REPORT_KEYS` are defined before tests import them.
- The validator and tests both use the same status vocabulary and claim manifest path.
