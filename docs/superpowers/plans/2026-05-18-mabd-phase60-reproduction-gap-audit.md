# Phase 60 Reproduction Gap Audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a machine-checkable audit that proves the current repository has not completed the full paper reproduction and lists every remaining experiment gap.

**Architecture:** Store the audit in `docs/reference/reproduction-gap-audit.yaml`, cite it from a dated record, and validate it against the paper claim manifest, experiment matrix, committed reports, and claim boundaries. Keep the audit strictly non-passing for all `experiment.*` claims.

**Tech Stack:** Python 3.10, `unittest`, PyYAML, existing `mabd_reproduction.reporting` report loader, vendored Newton on `PYTHONPATH=src:vendor/newton`.

---

### Task 1: Add Regression Test

**Files:**
- Modify: `tests/test_phase0_bootstrap.py`

- [ ] **Step 1: Write the failing test**

Add `test_phase60_reproduction_gap_audit_is_bounded` to
`Phase0BootstrapTests`. The test must require Phase 60 claim-boundary bullets,
load `docs/reference/reproduction-gap-audit.yaml`, compare all remaining
experiment claim IDs to `paper-claims.yaml` and the experiment matrix, verify
matching blocking reasons/output paths, and check existing committed reports
remain non-passing.

- [ ] **Step 2: Verify red**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_phase0_bootstrap.Phase0BootstrapTests.test_phase60_reproduction_gap_audit_is_bounded
```

Expected: FAIL with a missing Phase 60 claim-boundary bullet.

### Task 2: Add Audit Artifacts

**Files:**
- Create: `docs/reference/reproduction-gap-audit.yaml`
- Create: `docs/superpowers/specs/2026-05-18-phase60-reproduction-gap-audit-design.md`
- Create: `docs/superpowers/plans/2026-05-18-mabd-phase60-reproduction-gap-audit.md`
- Create: `docs/records/2026-05-18-phase60-reproduction-gap-audit.md`
- Modify: `docs/reference/claim-boundaries.md`

- [ ] **Step 1: Create the structured audit**

Add a YAML file with `schema_version: 1`, `audit_id:
phase60_reproduction_gap_audit`, the isolated environment paths, global status
counts, completion gates, all 15 remaining experiment claims, matrix blocking
reasons, matrix output report paths, committed report statuses/hashes, and
`phase61-spinning-box-contact-mabd-lane` as the next recommended phase.

- [ ] **Step 2: Add dated record and boundaries**

Add the Phase 60 record with status
`passed_for_reproduction_gap_audit`, cite the YAML path, list
`remaining_experiment_claims: 15`, `experiment_claims_passed: 0`, and
`full_reproduction_complete: false`, and state that no `experiment.*` claim is
passed. Add matching Phase 60 bullets to `claim-boundaries.md`.

- [ ] **Step 3: Verify focused test green**

Run the Task 1 test again.

Expected: PASS.

### Task 3: Add Validator Coverage

**Files:**
- Modify: `scripts/validate_docs.py`

- [ ] **Step 1: Register Phase 60 paths**

Add the YAML, record, spec, and plan to `REQUIRED_PATHS`. Add Phase 60
placeholder strings to the stale-placeholder guard until the final commit is
backfilled.

- [ ] **Step 2: Implement `validate_phase60_record()`**

Read the record, audit YAML, boundaries, paper claims, matrix, and reports.
Verify the audit covers exactly every non-passed `experiment.*` claim, reports
matching claim/matrix status and blocking reasons, records existing report
hashes accurately, keeps all experiment reports non-passing, preserves the
environment non-pollution flags, and contains no forbidden overclaim wording.

- [ ] **Step 3: Wire validator**

Call `validate_phase60_record()` from `main()` after Phase 59 and update the
success message to Phase 60.

- [ ] **Step 4: Run validator**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
```

Expected: PASS and print Phase 0-60 validation passed.

### Task 4: Backfill Commit And Verify

**Files:**
- Modify: `docs/reference/reproduction-gap-audit.yaml`
- Modify: `docs/records/2026-05-18-phase60-reproduction-gap-audit.md`

- [ ] **Step 1: Commit initial Phase 60 changes**

Run:

```bash
git add docs/reference/reproduction-gap-audit.yaml docs/reference/claim-boundaries.md docs/records/2026-05-18-phase60-reproduction-gap-audit.md docs/superpowers/specs/2026-05-18-phase60-reproduction-gap-audit-design.md docs/superpowers/plans/2026-05-18-mabd-phase60-reproduction-gap-audit.md scripts/validate_docs.py tests/test_phase0_bootstrap.py
git commit -m "Record Phase60 reproduction gap audit"
```

- [ ] **Step 2: Backfill commit hash and amend**

Replace `TO_BE_BACKFILLED_PHASE60` with the commit hash from Step 1, then run:

```bash
git add docs/reference/reproduction-gap-audit.yaml docs/records/2026-05-18-phase60-reproduction-gap-audit.md
git commit --amend --no-edit
```

- [ ] **Step 3: Final verification**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"
git diff --check
```

Expected: all commands exit 0, Newton imports from `vendor/newton`, and the
worktree is clean except for the committed branch being ahead of `main`.
