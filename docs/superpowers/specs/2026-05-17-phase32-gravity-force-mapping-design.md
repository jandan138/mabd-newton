# Phase 32 Gravity Force Mapping Design

## Goal

Add a Newton-first M-ABD CPU oracle path for uniform gravity forces. This is
method evidence for generalized force assembly only; it does not pass heavy-top,
physical-pendulum, contact, timing, or experiment claims.

## Inputs

- Passed-method paper source lines:
  - `/tmp/mabd-paper/source/sections/singleabd.tex:23-26` for the affine point
    coordinate Jacobian.
  - `/tmp/mabd-paper/source/sections/singleabd.tex:42` for external force in
    the implicit-Euler state prediction.
  - `/tmp/mabd-paper/source/sections/singleabd.tex:55-58` for projection into
    ABD coordinates.
  - `/tmp/mabd-paper/source/sections/solver.tex:238-242` for virtual-work
    external wrench mapping to affine generalized force.
- Non-claim experiment motivation:
  - `/tmp/mabd-paper/source/sections/experiment.tex:67-75` for heavy top under
    gravity.
  - `/tmp/mabd-paper/source/sections/experiment.tex:80-91` for physical
    pendulum under gravity.
- Additional non-claim background:
  - `/tmp/mabd-paper/source/sections/singleabd.tex:104-109` for virtual-work
    mapping of aggregated spatial forces into affine generalized forces.
- Existing `SingleBodyABDPrecompute.rest_points` and `masses`.
- Existing CPU oracle `MABDCPUOracleConfig` and `solve_cpu_oracle_step`.

## Design

Add `gravity_generalized_force(rest_points, masses, gravity)` in the vendored
M-ABD affine math module. The helper sums each point mass force `m_i g` through
the existing affine point Jacobian `J_i^T`, producing a 12-vector generalized
force. This keeps gravity independent of mesh resolution and uses the same
virtual-work mapping as point forces.

Extend `MABDCPUOracleConfig` with optional `gravity`. During each CPU oracle
step, gravity force is assembled per body from that body's precompute points
and masses, then added before actuation forces. `gravity=None` remains the
default and preserves existing behavior.

## Boundaries

- This is a CPU oracle feature, not a Warp/GPU production solver path.
- This does not implement contact, collision detection, friction, or implicit
  contact.
- This does not pass any `experiment.*` claim.
- Heavy-top and physical-pendulum scenes still need scene geometry, joints,
  analytic/RK4 references, and report gates.

## Validation

- Unit tests verify the gravity helper against explicit `J_i^T m_i g`
  assembly.
- CPU oracle step tests verify gravity contributes to `q`, `qd`, and `dq`.
- Validation rejects malformed gravity vectors.
- Docs validator and bootstrap tests enforce the Phase 32 claim boundaries and
  record evidence.
