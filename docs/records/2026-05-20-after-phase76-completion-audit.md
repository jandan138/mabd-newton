# After Phase 76 Completion Audit

## Status

not_complete_after_phase76

## Objective

The user objective is A+B full reproduction of "M-ABD: Scalable, Efficient,
and Robust Multi-Affine-Body Dynamics" in this repository, using a Newton-first
implementation path, isolated environments, auditable provenance, and no
unsupported claim inflation.

Concrete success criteria:

- A: implement the paper method in vendored Newton without reducing the
  algorithmic scope.
- B: reproduce the paper evidence, including required scenes, assets, baselines,
  metrics, and timing claims.
- Use Newton as the implementation substrate; local Newton patches are allowed.
- Keep the environment isolated from the reference project and ambient DSW
  Python.
- Keep every claim backed by records, manifests, configs, reports, and tests.

## Prompt-to-artifact checklist

| Requirement | Evidence inspected | Status |
| --- | --- | --- |
| Paper provenance is pinned | `docs/reference/paper-claims.yaml`, `docs/reference/reproduction-gap-audit.yaml` record arXiv v2 PDF and TeX checksums | passed |
| Newton-only primary implementation path | `vendor/newton/`, `vendor/newton/PROVENANCE.md`, `newton.solvers.SolverMABD`, Phase 1-76 records | partial |
| Environment isolation | `docs/reference/reproduction-gap-audit.yaml` records `canonical_python`, `reference_python`, `cloned_from_reference = true`, `mutates_reference_environment = false`, `uses_reference_python = false`, `uses_ambient_python = false` | passed |
| A: implement the paper method | `docs/reference/paper-claims.yaml` has 19 passed method claims | partial |
| B: reproduce the paper evidence | `docs/reference/reproduction-gap-audit.yaml` has `experiment_claims_passed = 0` and `remaining_experiment_claims = 15` | failed |
| Rolling/spinning M-ABD lane exists | `reports/experiment_matrix/single_body_rolling_spinning_mabd_newton.json` exists and is validated by Phase 76 | incomplete diagnostic |
| Rolling/spinning M-ABD is paper-faithful | Phase 76 report keeps `paper_faithful_mabd_collision_missing` and `paper_faithful_mabd_rolling_cylinder` blockers | failed |
| Rolling/spinning explicit RBD is paper-faithful | Phase 75 report keeps `newton_explicit_euler_not_paper_explicit_rbd_solver` and Phase 76 keeps `paper_faithful_explicit_rbd_baseline` | failed |
| Paper-comparable timing is reproduced | rolling/spinning reports keep `paper_comparable = false` and `paper_comparable_timing` missing | failed |
| Comparative baselines are recorded | gap audit marks comparative baseline adapters missing or incomplete for multiple claims | failed |
| Assets and scene sources are complete | gap audit marks assets, geometry, raw curves, motion plans, and marker sequences missing for several claims | failed |
| No unsupported pass claim is made | `docs/reference/claim-boundaries.md`, `scripts/validate_docs.py`, and all current reports keep `experiment.*` claims non-passing | passed |

## Current machine-readable state

- full_reproduction_complete = `false`
- experiment_claims_passed = `0`
- remaining_experiment_claims = `15`
- No `experiment.*` claim is passed.
- The current rolling/spinning M-ABD report is a Newton `SolverMABD`
  diagnostic, not a paper-faithful pass gate.

## Missing work

The objective is not achieved. The next pass-gate candidate should target
`experiment.single_body.rolling_spinning` because Phase 73-76 already created
the protocol, RBD development lanes, and M-ABD diagnostic lane. The remaining
gaps are explicit and bounded:

- paper-faithful M-ABD rolling-cylinder contact/friction evidence;
- paper-faithful explicit RBD baseline evidence;
- paper-comparable timing protocol and result.

The current `docs/reference/reproduction-gap-audit.yaml` therefore points to:

`phase77-rolling-spinning-paper-faithful-pass-gate`

Do not call `update_goal(status="complete")` while these blockers remain.
