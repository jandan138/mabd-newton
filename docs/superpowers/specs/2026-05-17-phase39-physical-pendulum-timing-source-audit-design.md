# Phase 39 Physical Pendulum Timing Source Audit Design

Date: 2026-05-17

## Purpose

Phase 39 removes a false physical-pendulum blocker without expanding the paper
claim. The physical-pendulum paper source lines
`/tmp/mabd-paper/source/sections/experiment.tex:77-91` describe angle tracking,
joint-force waveform behavior, phase drift, horizontal release, zero initial
velocity, gravity, and an elliptic-integral reference. They do not state a
runtime timing or performance claim for this experiment.

Current Phase 38 reports still list `paper_timing_missing` as a
physical-pendulum blocker. That is too broad for this specific claim and makes
the report imply a missing paper value that the cited source lines do not
contain.

## Scope

In scope:

- Add machine-checkable source-audit evidence that physical-pendulum source
  lines 77-91 do not contain a runtime timing claim.
- Remove `paper_timing_missing` from physical-pendulum MABD, RBD, and
  comparison report blockers.
- Keep `timing_distribution.scope = not_timed`; this phase does not benchmark
  runtime.
- Keep `joint_force_waveform_agreement_missing`,
  `pendulum_geometry_unknown`, and
  `physical_pendulum_comparison_pass_gate_not_enabled` blockers.
- Keep `experiment.single_body.physical_pendulum` as `intended`.

Out of scope:

- Claiming paper timing has been reproduced.
- Changing spinning-box or multibody timing claims.
- Claiming physical-pendulum experiment pass.
- Resolving joint-force waveform agreement or paper-faithful geometry.

## Report Contract

Physical-pendulum reports will add:

```json
"paper_timing_source_audit": {
  "source_lines": ["/tmp/mabd-paper/source/sections/experiment.tex:77-91"],
  "status": "not_a_physical_pendulum_paper_metric",
  "finding": "No runtime timing or performance value is stated in the cited physical-pendulum source lines."
}
```

The comparison report will keep `missing_paper_metrics` as
`["joint_force_error:paper_waveform_agreement"]` and will remove only
`paper_timing_missing` from `blocking_reasons`.

## Claim Boundary

Phase 39 verifies a source-audit correction only. It does not verify runtime
performance, paper timing for other experiments, physical-pendulum geometry,
joint-force waveform agreement, rendered output, or any passed
`experiment.*` claim.

## Tests

- `tests.test_experiment_runner` checks freshly generated physical-pendulum
  MABD, RBD, and comparison reports do not include `paper_timing_missing` and
  do include `paper_timing_source_audit`.
- `tests.test_phase0_bootstrap` checks committed reports, record text, claim
  boundaries, and `scripts/validate_docs.py` enforce the new boundary.
