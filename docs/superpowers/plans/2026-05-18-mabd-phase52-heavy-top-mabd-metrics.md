# Phase52 Heavy-Top MABD Metrics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add MABD-derived heavy-top precession velocity and energy drift diagnostics, then consume them in the heavy-top comparison report without overclaiming experiment completion.

**Architecture:** Extend the existing heavy-top MABD rollout dataclasses and report writer in place. The comparison report will derive paper metric statuses from the presence of finite MABD diagnostic fields while retaining paper-source and pass-gate blockers.

**Tech Stack:** Python 3.10, NumPy, vendored Newton, `unittest`, YAML/JSON evidence files.

---

### Task 1: RED Tests For MABD Rollout Metrics

**Files:**
- Modify: `tests/test_heavy_top_mabd.py`
- Test: `tests/test_heavy_top_mabd.py`

- [ ] **Step 1: Write the failing test**

Add assertions to `test_model_derived_heavy_top_lane_generates_bounded_diagnostics`:

```python
self.assertTrue(np.isfinite(rollout.energy_initial))
self.assertTrue(np.isfinite(rollout.energy_final))
self.assertTrue(np.isfinite(rollout.relative_energy_drift))
self.assertGreater(rollout.energy_initial, 0.0)
self.assertTrue(
    np.all(
        np.isfinite(
            [sample.precession_velocity_rad_s for sample in rollout.samples]
        )
    )
)
self.assertAlmostEqual(
    max(abs(sample.precession_velocity_rad_s) for sample in rollout.samples),
    rollout.max_abs_precession_velocity_rad_s,
)
```

Add deterministic helper tests:

```python
def test_sampled_precession_velocity_stencil_handles_unwrapped_crossing():
    raw_precession = np.asarray([3.0, -3.0, -2.5], dtype=float)
    unwrapped_precession = np.unwrap(raw_precession)
    sample_times = np.asarray([0.0, 1.0, 3.0], dtype=float)
    velocities = _sampled_precession_velocities_rad_s(unwrapped_precession, sample_times)
    expected = np.asarray(
        [
            (unwrapped_precession[1] - unwrapped_precession[0]) / 1.0,
            (unwrapped_precession[2] - unwrapped_precession[0]) / 3.0,
            (unwrapped_precession[2] - unwrapped_precession[1]) / 2.0,
        ],
        dtype=float,
    )
    np.testing.assert_allclose(velocities, expected, rtol=0.0, atol=1.0e-15)


def test_point_mass_energy_fixture_matches_hand_calculation():
    rest_points_m = np.asarray([[0.0, 1.0, 0.0], [0.0, 3.0, 0.0]], dtype=float)
    point_masses_kg = np.asarray([2.0, 3.0], dtype=float)
    gravity_m_s2 = np.asarray([0.0, -10.0, 0.0], dtype=float)
    q = mabd.pack_q(np.eye(3), np.zeros(3, dtype=float))
    qd = mabd.pack_q(np.zeros((3, 3), dtype=float), np.asarray([0.0, 2.0, 0.0]))
    assert _point_mass_energy(
        q,
        qd,
        rest_points_m=rest_points_m,
        point_masses_kg=point_masses_kg,
        gravity_m_s2=gravity_m_s2,
    ) == 120.0
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_heavy_top_mabd
```

Expected: FAIL because `HeavyTopMABDRollout.energy_initial` and `HeavyTopMABDSample.precession_velocity_rad_s` do not exist.

### Task 2: GREEN Implementation For Rollout Metrics

**Files:**
- Modify: `src/mabd_reproduction/heavy_top_mabd.py`
- Test: `tests/test_heavy_top_mabd.py`

- [ ] **Step 1: Add metric fields and helpers**

Add `precession_velocity_rad_s` to `HeavyTopMABDSample`. Add `energy_initial`, `energy_final`, and `relative_energy_drift` to `HeavyTopMABDRollout`.

Add helpers:

```python
def _point_mass_energy(
    q: np.ndarray,
    qd: np.ndarray,
    *,
    rest_points_m: np.ndarray,
    point_masses_kg: np.ndarray,
    gravity_m_s2: np.ndarray,
) -> float:
    points = mabd.affine_points(q, rest_points_m)
    velocities = mabd.affine_points(qd, rest_points_m)
    kinetic = 0.5 * float(np.sum(point_masses_kg * np.sum(velocities * velocities, axis=1)))
    potential = -float(np.sum(point_masses_kg * (points @ gravity_m_s2)))
    return kinetic + potential
```

and a sampled velocity helper using unwrapped precession angles.

- [ ] **Step 2: Populate metrics in the rollout**

Compute initial energy before the loop, update final energy after the loop, and assign precession velocities to sampled rows after sample collection.

- [ ] **Step 3: Run test to verify it passes**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_heavy_top_mabd
```

Expected: PASS.

### Task 3: RED Tests For Reports And Comparison Consumption

**Files:**
- Modify: `tests/test_heavy_top_comparison_reports.py`
- Test: `tests/test_heavy_top_comparison_reports.py`

- [ ] **Step 1: Write failing assertions**

In `test_heavy_top_comparison_report_records_bounded_protocol`, update expected missing paper metrics to:

```python
self.assertEqual(
    loaded.observed["missing_paper_metrics"],
    ["nutation_angle_error:paper_reference_curve_missing"],
)
self.assertIsNotNone(loaded.observed["lane_metrics"]["mabd_newton"]["energy_drift"])
self.assertEqual(
    loaded.observed["paper_metric_statuses"]["precession_velocity_error"]["status"],
    "diagnostic_available",
)
self.assertEqual(
    loaded.observed["paper_metric_statuses"]["energy_drift"]["status"],
    "diagnostic_available",
)
```

Also assert the MABD lane report samples contain `precession_velocity_rad_s`.

Retain claim-boundary assertions:

```python
self.assertEqual(loaded.status, EvidenceStatus.INCOMPLETE)
self.assertEqual(mabd_loaded.status, EvidenceStatus.INCOMPLETE)
self.assertFalse(loaded.observed["full_experiment_claim_passed"])
self.assertFalse(mabd_loaded.observed["full_experiment_claim_passed"])
for blocker in (
    "exact_heavy_top_inertia_unknown",
    "exact_heavy_top_geometry_unknown",
    "raw_heavy_top_reference_curve_data_missing",
    "mabd_newton_report_incomplete",
    "heavy_top_comparison_report_incomplete",
    "heavy_top_timing_evidence_missing",
    "heavy_top_comparison_pass_gate_not_enabled",
):
    self.assertIn(blocker, loaded.observed["blocking_reasons"])
```

Add a negative comparison test that deletes one sample row's `precession_velocity_rad_s`; expected `missing_paper_metrics` must then include `precession_velocity_error:mabd_precession_velocity_samples_missing`.

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_heavy_top_comparison_reports
```

Expected: FAIL because report rows and comparison statuses still mark MABD metrics missing.

### Task 4: GREEN Implementation For Reports And Comparison

**Files:**
- Modify: `src/mabd_reproduction/heavy_top_reports.py`
- Modify: `src/mabd_reproduction/comparison_reports.py`
- Test: `tests/test_heavy_top_comparison_reports.py`

- [ ] **Step 1: Emit MABD metric fields**

Include rollout energy fields in `write_heavy_top_mabd_newton_report.observed`. Include `precession_velocity_rad_s` in `_mabd_sample_rows`.

- [ ] **Step 2: Consume metrics in comparison**

Update `_heavy_top_metric_snapshot` so `mabd_newton.energy_drift` reads `observed["relative_energy_drift"]`. In `write_heavy_top_comparison_report`, compute missing MABD metrics from finite fields:

```python
mabd_precession_available = _heavy_top_mabd_precession_velocity_available(mabd_report)
mabd_energy_available = _finite_scalar(mabd_report.observed.get("relative_energy_drift")) is not None
```

Only retain missing entries for unavailable MABD fields. Always retain `nutation_angle_error:paper_reference_curve_missing`.

- [ ] **Step 3: Run comparison tests**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_heavy_top_comparison_reports
```

Expected: PASS.

### Task 5: Regenerate Reports And Documentation

**Files:**
- Modify: `reports/experiment_matrix/single_body_heavy_top_mabd_newton.json`
- Modify: `reports/experiment_matrix/single_body_heavy_top_comparison.json`
- Modify: `reports/experiment_matrix/single_body_heavy_top_rk4_reference.json` only if source commit provenance must be aligned
- Modify: `docs/reference/claim-boundaries.md`
- Modify: `scripts/validate_docs.py`
- Create: `docs/records/2026-05-18-phase52-heavy-top-mabd-metrics.md`

- [ ] **Step 1: Regenerate heavy-top reports**

Run the existing CLI lanes with the current source commit. Source-commit backfill is mandatory for the generated reports and record; do not leave branch-local placeholders in committed evidence.

- [ ] **Step 2: Record claim boundaries**

Add a Phase52 section stating that MABD diagnostic precession velocity and energy drift are available, while heavy-top remains incomplete.

Add a Phase52 “does not verify” paragraph and Forbidden Claims entry matching the Phase49-51 heavy-top style. It must explicitly say Phase52 does not verify a passed heavy-top experiment, paper-faithful geometry/inertia, raw curve agreement, comparison pass gate, timing evidence, rendered output, generated video, or full paper reproduction.

- [ ] **Step 3: Add a Phase52 validator**

Extend `scripts/validate_docs.py` required paths and add checks for the new metrics, hashes, record text, and no overclaiming.

### Task 6: Final Verification And Integration

**Files:**
- All modified files

- [ ] **Step 1: Run full verification**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"
/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .
git diff --check
```

Expected: all commands pass.

- [ ] **Step 2: Commit, merge to `main`, push, and remove the worktree**

Use non-interactive git commands and do not touch unrelated worktrees or the root feature branch.
