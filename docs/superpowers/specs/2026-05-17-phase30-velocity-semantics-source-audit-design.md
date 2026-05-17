# Phase 30 Velocity Semantics Source Audit Design

Date: 2026-05-17

## Decision

Phase 30 records a machine-checkable audit of the M-ABD paper source for the
single-body spinning-box velocity and momentum semantics.

Phase 29 proved that, under the current finite-difference velocity relation
`qd_next=(q_next-q_n)/h`, the paper spinning-box angular momentum cannot be
represented by an orthogonal affine update at the paper step sizes. Phase 30
therefore checks the paper TeX and figure source before changing Newton solver
semantics. The result is an evidence boundary: the paper source supports
implicit-Euler inertia potential, `G(A)` twist mapping, and `G(A)^T` wrench
mapping, but does not provide an explicit decoupled velocity update or
alternative momentum extraction rule for the spinning-box plot.

## Source Basis

Paper source files audited by this phase:

- `/tmp/mabd-paper/source/sections/singleabd.tex:34-42`: variational inertia
  potential and implicit Euler example.
- `/tmp/mabd-paper/source/sections/solver.tex:219-241`: `G(A)` maps ABD
  velocity to spatial twist, and `G(A)^T` maps spatial wrench to affine force.
- `/tmp/mabd-paper/source/sections/experiment.tex:40-55`: spinning-box
  initial momenta, initialization through target spatial twist, and momentum
  comparison text.
- `/tmp/mabd-paper/source/images/cube/roll_cube.pdf`: plotted h values and
  momentum axes for the spinning-box figure.

## Scope

Phase 30 adds a small source-audit helper and repository gates:

- compute SHA256 checksums for the audited TeX/PDF source files;
- verify the required source snippets are present in uncommented TeX lines;
- scan uncommented TeX for explicit decoupled velocity or alternative momentum
  extraction terms;
- report the audit status as
  `source_does_not_prove_decoupled_velocity_semantics`;
- record this status in claim boundaries and a dated record;
- keep all `experiment.*` claims unpassed.

## Non-Goals

Phase 30 does not:

- modify vendored Newton;
- change `SolverMABD.step()` semantics;
- decouple stored velocity from finite-difference position updates;
- add a new M-ABD lane pass;
- pass `experiment.single_body.spinning_box`;
- prove that the paper authors did not use private implementation details not
  present in the source archive;
- vendor raw paper PDF, TeX, figures, logs, or generated reports;
- update any `experiment.*` status in `paper-claims.yaml` to `passed`.

## Exit Criteria

The phase is complete when:

- unit tests cover the source-audit helper and its checksums/findings;
- claim-boundary tests require Phase 30 current/verified/non-claim bullets;
- docs validation requires the Phase 30 record and audit status;
- all standard repo gates pass;
- the branch is merged to `main` and pushed.

The next implementation phase may then choose either a reconstruction path with
explicitly documented non-paper semantics, or continue searching for external
author code/assets that define the missing velocity semantics.
