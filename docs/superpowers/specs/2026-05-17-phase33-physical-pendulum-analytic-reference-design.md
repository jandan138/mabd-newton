# Phase 33 Physical Pendulum Analytic Reference Design

## Goal

Add a machine-checkable analytic-reference lane for
`experiment.single_body.physical_pendulum`. This phase records the paper's
elliptic-integral angle reference as executable evidence, but it does not pass
the physical-pendulum experiment.

## Paper Source

- `/tmp/mabd-paper/source/sections/experiment.tex:77-91`
- The paper states that the physical pendulum starts from a horizontal
  configuration with zero initial velocity under gravity.
- The paper's analytic angle reference is
  `theta(t)=pi/2 - 2 asin(kappa * sn(K(kappa) - omega_lin * t, kappa))`.

## Design

Create `configs/experiments/single_body_physical_pendulum.yaml` with the paper
claim id, scene id, source lines, asset id, normalized procedural reference
parameters, report status `incomplete`, and output report path. The config must
match `paper_experiment_matrix.yaml`, reject passed experiment status, and keep
the existing `pendulum_geometry_unknown` blocker.

Add `mabd_reproduction.physical_pendulum_reference` for the analytic reference
only. It will evaluate the paper equation using SciPy's elliptic functions,
treating the paper's `kappa` as modulus and passing `kappa**2` to SciPy's
parameterized `ellipk`/`ellipj` APIs. The helper returns deterministic finite
angle samples and validates `0 < kappa < 1`, positive `omega_lin`, and
nonnegative finite sample times.

Add an `analytic_reference` runner lane that writes a full-schema `ClaimReport`
for `experiment.single_body.physical_pendulum`. The report remains
`incomplete`; its `observed` payload records angle samples, period estimate,
and the lane status. Its `failure_reason` must cite missing M-ABD/RBD dynamics,
joint-force comparison, and unspecified paper geometry.

## Boundaries

- This phase does not simulate a Newton M-ABD physical pendulum.
- This phase does not run an RBD baseline.
- This phase does not compute joint-force waveform agreement.
- This phase does not remove the `pendulum_geometry_unknown` blocker.
- This phase does not change any `experiment.*` claim to `passed`.

## Validation

- Unit tests cover the analytic equation at deterministic reference points.
- Config tests cover matrix alignment, safe status handling, and sample fields.
- Runner tests cover full-schema report writing and CLI dispatch.
- Docs validators and bootstrap tests enforce Phase33 claim boundaries and
  forbid treating the analytic-reference lane as a passed experiment.
