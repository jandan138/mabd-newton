# Phase 77 Rolling/Spinning Paper-Faithful Pass Gate Design

## Scope

Phase 77 adds a fail-closed rolling-cylinder M-ABD material preflight lane for
`experiment.single_body.rolling_spinning`.

The lane exists because the Phase 76 `mabd_newton` diagnostic deliberately ran
with zero stiffness to isolate static-plane contact plumbing. That diagnostic is
not paper-faithful M-ABD. Phase 77 moves one step closer to the paper setup by
using the paper single-body material values recorded in the LaTeX source:

- `young_modulus_pa = 1.0e9`
- `poisson_ratio = 0.3`
- `density_kg_m3 = 1000.0`

## Claim Boundary

This phase must remain incomplete. It does not pass
`experiment.single_body.rolling_spinning` and does not claim full paper
reproduction.

The new report must keep these blockers visible:

- `mabd_material_preflight_incomplete`
- `paper_faithful_mabd_collision_missing`
- `paper_faithful_explicit_rbd_baseline_missing`
- `paper_faithful_implicit_rbd_baseline_missing`
- `paper_comparable_timing_missing`

## Config Contract

`configs/experiments/single_body_rolling_spinning.yaml` gets a separate
`mabd_material_preflight` section with its own report path:

```text
reports/experiment_matrix/single_body_rolling_spinning_mabd_material_preflight.json
```

The section must be matrix-validated as fail-closed:

- relative JSON report under `reports/experiment_matrix`
- report path distinct from protocol, RBD, and Phase 76 M-ABD reports
- `young_modulus_pa > 0`
- `poisson_ratio in (-1, 0.5)`
- `zero_stiffness_diagnostic = false`

## Runtime Contract

`SolverMABD` construction must consume the config material values instead of
hardcoded zero stiffness. The old `mabd_newton` lane keeps its default zero
stiffness behavior through loader defaults; the new preflight lane supplies the
finite material values explicitly.

## Environment Contract

Use the existing cloned project environment:

```text
/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python
```

The reference environment
`/cpfs/user/zhuzihou/conda-managed/envs/physics-primitive-newton-py310` is source
only. This phase must not mutate it or the ambient DSW Python.
