# Phase 35 Physical Pendulum RBD Baseline Design

## Objective

Add a Newton-only physical-pendulum `rbd_implicit_baseline` diagnostic lane for
`experiment.single_body.physical_pendulum`.

This phase advances the paper-reproduction matrix by producing a
machine-checkable RBD baseline report for the same configured physical-pendulum
scene used by the Phase 33 analytic reference and Phase 34 M-ABD diagnostic.
It does not pass the full paper experiment. The required `mabd_newton` lane,
paper-faithful pendulum geometry, joint-force waveform agreement, rendered
figure, and paper timing remain incomplete.

## Current Evidence Gap

The current `main` state has:

- `experiment.single_body.physical_pendulum` still at `intended`.
- `required_missing_lanes` in
  `configs/experiments/single_body_physical_pendulum.yaml` still listing
  `mabd_newton` and `rbd_implicit_baseline`.
- a committed Phase 34 M-ABD diagnostic report that records
  `rbd_implicit_baseline` as missing.
- no physical-pendulum RBD baseline report artifact.

Phase 35 closes only the last item for current configs. Historical Phase 34
records remain historical evidence from their source commit.

## Approach Options

### Option A: Scalar Implicit RBD Pendulum Diagnostic

Implement a deterministic scalar rigid-pendulum implicit-Euler rollout in NumPy.
Use the same angle convention as the analytic reference and Phase 34 M-ABD
diagnostic: angle is `0` at horizontal release and positive downward. At each
step solve

```text
theta_next - theta - h * (omega + h * g / L * cos(theta_next)) = 0
omega_next = (theta_next - theta) / h
```

with Newton iterations. Compute compact angle samples, phase/angle error against
the elliptic reference, and a diagnostic pivot joint-force magnitude from the
point-mass rigid pendulum kinematics.

This is the recommended path because it directly targets the paper's physical
pendulum text, is deterministic, and stays isolated from external engines.

### Option B: Newton `SolverSemiImplicit` Rigid Body With Joint Proxy

Build a Newton rigid body and approximate the fixed pivot with a local proxy
constraint. This would exercise more Newton runtime surface, but the repository
does not currently have a paper-faithful rigid joint adapter for this scene.
It risks confusing proxy behavior with a verified RBD baseline.

### Option C: Leave RBD Missing And Start Another Scene

Start another experiment claim without closing the existing physical-pendulum
baseline gap. This increases breadth but does not improve the already active
physical-pendulum evidence chain.

## Selected Design

Use Option A.

Phase 35 introduces a small focused module,
`src/mabd_reproduction/physical_pendulum_rbd.py`, with:

- `PhysicalPendulumRBDSample`
- `PhysicalPendulumRBDRollout`
- `roll_out_physical_pendulum_rbd_baseline(config)`

The rollout consumes a new `rbd_baseline` block in
`single_body_physical_pendulum.yaml`. The block records:

- time step, step count, and sample count
- length, mass, gravity, initial angle, and initial angular velocity
- Newton iteration cap and residual tolerance
- output report path
- thresholds for angle error, phase drift, implicit residual, and length
  constraint error

The report writer lives in `physical_pendulum_reports.py` and emits a
`ClaimReport` with:

- `baseline_lane = rbd_implicit_baseline`
- `solver_mode = physical_pendulum_scalar_implicit_rbd_development`
- `backend = cpu_numpy_newton_only`
- `status = incomplete`
- `observed.lane_status = development_diagnostic_generated`
- compact samples with angle, angular velocity, reference angle, angle error,
  implicit residual, length error, and joint-force magnitude
- `observed.required_missing_lanes = ["mabd_newton"]`
- explicit non-claim limitations for paper geometry, joint-force waveform
  agreement, rendered output, and timing

The current config-level `required_missing_lanes` becomes only
`["mabd_newton"]`. This means the current configuration now has an executable
RBD baseline diagnostic, but the paper claim still remains not passed.

## Validation

Tests must prove:

- config parsing rejects malformed `rbd_baseline` fields
- the RBD rollout has finite compact samples and bounded implicit residual
- the generated report is schema-valid, incomplete, and uses the required lane
  id without claiming a full experiment pass
- CLI dispatch for `--lane rbd_implicit_baseline` chooses the physical-pendulum
  runner when the config claim id is
  `experiment.single_body.physical_pendulum`
- docs/provenance validators require the Phase 35 record and report artifact

## Claim Boundaries

Allowed Phase 35 claims:

- a Newton-only physical-pendulum RBD implicit baseline diagnostic exists
- the current physical-pendulum config no longer lists `rbd_implicit_baseline`
  as a missing lane
- the generated RBD report is machine-checkable and incomplete

Forbidden Phase 35 claims:

- the physical-pendulum paper experiment is passed
- the RBD diagnostic is a paper-faithful implicit RBD baseline for all paper
  purposes
- the diagnostic joint-force magnitude is waveform agreement with the paper
- paper geometry, rendering, or timing is verified
- any `experiment.*` paper claim is passed
