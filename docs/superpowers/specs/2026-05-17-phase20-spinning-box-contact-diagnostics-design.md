# Phase 20 Spinning-Box Contact Diagnostics Design

## Scope

Phase 20 adds machine-checkable contact diagnostics for the single-body
spinning-box M-ABD development lane. The paper scene is a cube moving on a
frictionless surface, while the current lane is still a zero-force free-body
oracle. This phase introduces the procedural cube corner set and aggregates the
existing M-ABD point-plane normal penalty oracle over those corners.

This is contact-force assembly evidence only. It does not implement paper-
faithful affine collision detection, continuous collision detection, friction,
implicit contact solve, rigid-body contact matching, rendered trajectory
agreement, timing, or any passed `experiment.*` claim.

## Design

Use the existing paper cube parameters in
`configs/experiments/single_body_spinning_box.yaml` to derive eight centered
cube corners at side length `cube_size_m`. Add a `contact_surface` block to the
config with a normalized plane, normal penalty stiffness, and damping. The
default initial state remains unchanged so previous momentum and energy
diagnostics remain comparable; contact diagnostics are recorded as a separate
snapshot, not used to mutate the Phase 18/19 integration evidence.

`src/mabd_reproduction/spinning_box_physics.py` will expose:

- `spinning_box_cube_corners(config) -> np.ndarray`
- `spinning_box_contact_diagnostics(config, q, qd) -> SpinningBoxContactDiagnostics`

The diagnostics include active contact count, minimum signed distance, maximum
penetration depth, total normal force vector, total generalized force vector,
and per-corner signed distances. The implementation reuses
`newton.solvers.mabd.evaluate_point_plane_penalty_contact` for every corner and
sums `generalized_force` by virtual work.

`src/mabd_reproduction/experiment_configs.py` will parse and validate the
optional `contact_surface` block. `src/mabd_reproduction/single_body_reports.py`
will include contact diagnostics in the generated M-ABD lane report when a
configured spinning-box run is supplied.

## Claim Boundaries

The report status remains `incomplete`. The comparison report remains blocked
by incomplete lane reports and non-paper-faithful RBD/contact lanes. Phase 20
only proves that the reproduction can derive paper-sized cube contact points
and assemble affine generalized normal penalty force diagnostics without
mutating the isolated environment or vendored Newton outside the existing M-ABD
oracle module.

