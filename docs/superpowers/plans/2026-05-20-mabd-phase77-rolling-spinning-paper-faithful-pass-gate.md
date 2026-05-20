# Phase 77 Rolling/Spinning Material Preflight Plan

## Goal

Add a fail-closed finite-stiffness M-ABD material preflight lane for the
rolling-cylinder experiment without passing the paper claim.

## Tasks

1. Add config RED/GREEN tests for `mabd_material_preflight`.
   - Check the separate report path.
   - Check paper material values.
   - Check `zero_stiffness_diagnostic = false`.
   - Keep `mabd_newton` backward compatible with its zero-stiffness diagnostic.

2. Add report runner RED/GREEN tests.
   - Add `run_rolling_spinning_mabd_material_preflight`.
   - Add CLI lane `rolling_spinning_mabd_material_preflight`.
   - Assert the report is `incomplete` and records finite material values.

3. Generate the material preflight report.
   - Use the project-owned cloned environment.
   - Record source and vendored Newton commits.
   - Do not overwrite Phase 73-76 reports.

4. Update claim-boundary evidence.
   - Add a Phase 77 record.
   - Add report and record checks to `scripts/validate_docs.py`.
   - Keep `docs/reference/reproduction-gap-audit.yaml` fail-closed.

5. Verify.
   - Run targeted config and runner tests.
   - Run docs validator.
   - Run full unittest discovery before final push.
   - Run `git diff --check`.
