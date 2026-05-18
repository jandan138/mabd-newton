# Phase 60 Reproduction Gap Audit Design

## Goal

Phase 60 adds a durable, machine-checkable audit for the current distance to
the requested A+B full reproduction of the M-ABD paper. It does not implement a
new solver path or pass any paper experiment; it records the remaining gaps so
future phases cannot accidentally overclaim completion.

## Scope

The audit covers every `experiment.*` claim in
`docs/reference/paper-claims.yaml`, the matching entries in
`configs/experiments/paper_experiment_matrix.yaml`, committed compact reports
under `reports/experiment_matrix/`, and the isolated Newton environment
contract. The audit is a reference YAML file plus a dated evidence record,
claim-boundary bullets, validator checks, and unit coverage.

## Architecture

- `docs/reference/reproduction-gap-audit.yaml` is the structured source of
  truth for the Phase 60 audit. It records global pass counts, environment
  isolation flags, completion gates, every remaining experiment claim, matrix
  blockers, committed report status, report hashes, and the next recommended
  technical phase.
- `docs/records/2026-05-18-phase60-reproduction-gap-audit.md` records the
  dated evidence and verification commands.
- `scripts/validate_docs.py` validates the YAML against the paper claim
  manifest, experiment matrix, committed reports, claim boundaries, and
  forbidden overclaim text.
- `tests/test_phase0_bootstrap.py` keeps a focused regression test for the
  audit boundary and the all-remaining-claim coverage contract.

## Data Flow

The validator reads `paper-claims.yaml` and selects all `experiment.*` claims
whose status is not `passed`. It then reads the experiment matrix and verifies
that `reproduction-gap-audit.yaml` has exactly the same claim IDs, status
values, blocking reasons, and matrix output report paths. For report paths that
exist, it loads the committed claim report and verifies the audit records the
same status and hash; for missing matrix output reports, it requires the audit
to say `committed_report_status: missing`.

## Claim Boundaries

Phase 60 may verify only the audit itself. It must not claim a passed paper
experiment, a solver/contact fix, a comparative baseline result, a timing
result, or a full paper reproduction. The audit must explicitly keep
`full_reproduction_complete = false` and `experiment_claims_passed = 0`.

## Next Technical Slice

The audit recommends `phase61-spinning-box-contact-mabd-lane` because the
spinning-box claim already has explicit paper values, an RBD lane gate, and
committed M-ABD/comparison diagnostics. It remains blocked by the incomplete
M-ABD lane and comparison report, so the next work should focus on the
Newton-only contact/MABD gap before any pass gate is considered.

## Testing

The new unit test must fail before the audit artifacts exist, then pass after
the YAML, record, claim boundaries, and validator are added. Final validation
requires the canonical isolated Python:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_phase0_bootstrap.Phase0BootstrapTests.test_phase60_reproduction_gap_audit_is_bounded
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
```
