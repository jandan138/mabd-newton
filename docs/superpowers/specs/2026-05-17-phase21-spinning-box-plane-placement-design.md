# Phase 21 Spinning-Box Plane Placement Design

## Scope

Phase 21 fixes the configured single-body spinning-box initial pose so the
paper-sized cube rests on the configured frictionless plane instead of starting
with its center on the plane. With side length `0.1 m`, plane normal
`[0, 1, 0]`, and plane offset `0`, the configured translation must be
`t_y = 0.05 m`.

This phase is a scene-configuration and diagnostic consistency correction. It
does not implement collision detection, continuous collision detection,
friction, an implicit contact solve, gravity, paper-faithful affine collision,
paper-faithful implicit RBD, rendered trajectory agreement, timing, or any
passed `experiment.*` claim.

## Design

Keep the existing M-ABD development lane and report status unchanged. Update
`configs/experiments/single_body_spinning_box.yaml` so `initial_q` packs the
identity affine transform with translation `[0, 0.05, 0]`. Add validation that
the configured plane is the expected horizontal plane and that the initial cube
corner signed distances are nonnegative with minimum distance `0`.

The report will continue to record contact diagnostics at
`initial_configured_q_qd`. After this phase those diagnostics should show:

- `contact_min_signed_distance_m = 0.0`
- `contact_max_penetration_m = 0.0`
- `contact_active_count = 0`
- `contact_total_normal_force_n = [0.0, 0.0, 0.0]`
- `contact_total_generalized_force = [0.0] * 12`

The previous penetrated initial state is not preserved as a supported mode.
Penalty-force integration will remain out of scope until the scene starts from
a non-penetrating configuration and a bounded contact stepping design is
recorded.

## Claim Boundaries

Phase 21 verifies only config/report consistency for the procedural
spinning-box resting pose. It does not prove the paper spinning-box experiment,
baseline comparison, contact solve, collision pipeline, or timing result. The
single-body M-ABD report and comparison report remain `incomplete`.
