# Phase 30 Velocity Semantics Source Audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add machine-checkable evidence for what the paper source does and does not specify about spinning-box velocity and momentum semantics.

**Architecture:** Add a focused Python source-audit helper that reads local paper source files, validates checksums and snippets, scans uncommented TeX for alternative semantics, then wire the result into docs/record validation without modifying solver behavior.

**Tech Stack:** Python 3.10, unittest, pathlib/hashlib, existing isolated `mabd-newton-py310` environment, local paper source under `/tmp/mabd-paper/source`.

---

### Task 1: Source Audit Helper

**Files:**
- Create: `src/mabd_reproduction/paper_source_audit.py`
- Create: `tests/test_paper_source_audit.py`

- [ ] **Step 1: Write failing audit tests**

Create `tests/test_paper_source_audit.py` with assertions for the audit status,
file checksums, positive source findings, and absent decoupled semantics.

- [ ] **Step 2: Run focused test and verify RED**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_paper_source_audit
```

Expected: fails because `mabd_reproduction.paper_source_audit` does not exist.

- [ ] **Step 3: Implement the helper**

Add immutable dataclasses for source findings and an audit result. Implement
`velocity_semantics_source_audit(...)` so it hashes the audited files, validates
required snippets in uncommented TeX lines, scans for missing alternative
semantics, and returns
`source_does_not_prove_decoupled_velocity_semantics`.

- [ ] **Step 4: Run focused test and verify GREEN**

Run the same focused unittest command. Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/mabd_reproduction/paper_source_audit.py tests/test_paper_source_audit.py
git commit -m "feat: add velocity semantics source audit"
```

### Task 2: Claim Boundary And Record Gates

**Files:**
- Modify: `docs/reference/claim-boundaries.md`
- Add: `docs/records/2026-05-17-phase30-velocity-semantics-source-audit.md`
- Modify: `scripts/validate_docs.py`
- Modify: `tests/test_phase0_bootstrap.py`

- [ ] **Step 1: Write failing bootstrap/validator assertions**

Add tests requiring Phase 30 claim-boundary bullets, the Phase 30 record, the
audit status, and `/30` validator output.

- [ ] **Step 2: Run focused tests and verify RED**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_phase0_bootstrap
```

Expected: fails because Phase 30 docs and validator entries are missing.

- [ ] **Step 3: Add docs and validator checks**

Update claim boundaries, add the dated record, import and call the audit helper
from `scripts/validate_docs.py`, and keep all experiment claims unpassed.

- [ ] **Step 4: Run focused tests and verify GREEN**

Run the same bootstrap unittest command. Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add docs/reference/claim-boundaries.md docs/records/2026-05-17-phase30-velocity-semantics-source-audit.md scripts/validate_docs.py tests/test_phase0_bootstrap.py
git commit -m "docs: record Phase 30 velocity semantics audit"
```

### Task 3: Full Verification And Integration

**Files:**
- Verify all touched files and standard gates.

- [ ] **Step 1: Run standard gates**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest newton.tests.test_mabd_phase4_solver_step
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/env/readiness_check.py
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"
git diff --check
```

- [ ] **Step 2: Merge and push**

Fast-forward `main`, rerun standard gates on `main`, push to `origin/main`, and
remove the temporary worktree.
