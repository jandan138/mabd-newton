# Phase59 T-Handle Figure Agreement Diagnostics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add bounded T-handle digitized figure curve-error diagnostics to the comparison report without enabling a pass gate.

**Architecture:** Extend T-handle lane reports with per-sample relative energy loss, add comparison-report helpers that interpolate Phase58 color-family curves on a normalized figure-time axis, then record all-color-family and best-color-family diagnostics for RK4 and M-ABD lanes. Claim boundaries and validators are updated so the new evidence is machine-checkable but still incomplete.

**Tech Stack:** Python 3.10, existing `ClaimReport` JSON schema, existing T-handle report writers, `unittest`, vendored Newton import isolation.

---

### Task 1: RED Tests For Lane Energy-Loss Samples

**Files:**
- Modify: `tests/test_t_handle_reference.py`
- Modify: `tests/test_t_handle_comparison_reports.py`

- [ ] **Step 1: Add failing report sample assertions**

Extend the T-handle report tests to assert both lane reports expose finite
`relative_energy_loss` values in each angular velocity sample:

```python
samples = loaded.observed["angular_velocity_samples"]
self.assertTrue(all("relative_energy_loss" in sample for sample in samples))
self.assertAlmostEqual(samples[0]["relative_energy_loss"], 0.0)
self.assertTrue(all(isfinite(sample["relative_energy_loss"]) for sample in samples))
```

- [ ] **Step 2: Run RED**

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_t_handle_reference tests.test_t_handle_comparison_reports
```

Expected: fail because the sample rows do not yet include
`relative_energy_loss`.

### Task 2: GREEN Lane Energy-Loss Samples

**Files:**
- Modify: `src/mabd_reproduction/t_handle_reports.py`
- Test: `tests/test_t_handle_reference.py`
- Test: `tests/test_t_handle_comparison_reports.py`

- [ ] **Step 1: Add RK4 sample energy loss**

For RK4 report sample rows, compute:

```python
energy = 0.5 * np.dot(inertia, omega * omega)
relative_energy_loss = (energy_initial - energy) / energy_initial
```

Add `energy` and `relative_energy_loss` to each sample row.

- [ ] **Step 2: Add M-ABD sample energy loss**

For M-ABD report sample rows, compute:

```python
relative_energy_loss = (rollout.energy_initial - sample.energy) / rollout.energy_initial
```

Add `relative_energy_loss` to each sample row.

- [ ] **Step 3: Run GREEN**

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_t_handle_reference tests.test_t_handle_comparison_reports
```

Expected: pass.

### Task 3: RED Tests For Figure Agreement Diagnostics

**Files:**
- Modify: `tests/test_t_handle_comparison_reports.py`

- [ ] **Step 1: Add figure-agreement assertions**

In `test_t_handle_comparison_consumes_valid_figure_curve_report`, assert:

```python
diagnostics = loaded.observed["digitized_figure_curve_agreement_diagnostics"]
self.assertTrue(loaded.observed["digitized_figure_curve_agreement_available"])
self.assertFalse(loaded.observed["digitized_figure_curve_agreement_passed"])
for metric in ("intermediate_axis_angular_velocity_waveform", "energy_loss"):
    for lane in ("rbd_rk4_reference", "mabd_newton"):
        entry = diagnostics[metric][lane]
        self.assertEqual(entry["status"], "diagnostic_available_not_pass_gate")
        self.assertEqual(entry["time_normalization"]["figure_time_range"], [0.0, 100.0])
        self.assertEqual(entry["time_normalization"]["mapping"], "lane_time_s / diagnostic_duration_s * 100")
        self.assertIn(entry["best_color_family"], {"blue", "orange", "green"})
        self.assertGreater(entry["matched_sample_count"], 0)
        self.assertTrue(isfinite(entry["best_rmse"]))
        self.assertTrue(isfinite(entry["best_max_abs_error"]))
        self.assertEqual(
            entry["time_normalization"]["claim_status"],
            "normalized_figure_time_not_paper_raw_time",
        )
        self.assertEqual(
            entry["best_color_family_claim_status"],
            "numeric_best_fit_not_legend_identity",
        )
        self.assertEqual(
            entry["agreement_claim_status"],
            "diagnostic_only_not_curve_agreement",
        )
        self.assertEqual(set(entry["all_color_family_errors"]), {"blue", "orange", "green"})
```

Also assert the waveform and energy paper metric statuses mention diagnostic
availability, not agreement pass.

- [ ] **Step 2: Run RED**

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_t_handle_comparison_reports
```

Expected: fail because the diagnostics are absent.

### Task 4: GREEN Figure Agreement Diagnostics

**Files:**
- Modify: `src/mabd_reproduction/comparison_reports.py`
- Test: `tests/test_t_handle_comparison_reports.py`

- [ ] **Step 1: Add interpolation helpers**

Implement helpers that validate finite lane samples, normalize time, interpolate
digitized figure color-family samples, and return per-color error statistics.

- [ ] **Step 2: Add comparison observed fields**

When a valid figure report is present, populate:

- `digitized_figure_curve_agreement_available`
- `digitized_figure_curve_agreement_passed = false`
- `digitized_figure_curve_agreement_diagnostics`

Keep `t_handle_digitized_figure_curve_agreement_not_passed`.
Also keep `sample_grid_flip_delta_unavailable` whenever the sample-grid flip
diagnostic remains unavailable.

- [ ] **Step 3: Update metric statuses**

Use statuses:

- `paper_figure_digitized_color_family_error_diagnostic_available_not_agreement`
- `paper_figure_digitized_energy_loss_error_diagnostic_available_not_agreement`

- [ ] **Step 4: Run GREEN**

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_t_handle_comparison_reports
```

Expected: pass.

### Task 5: Records, Validator, And Artifacts

**Files:**
- Modify: `docs/reference/claim-boundaries.md`
- Create: `docs/records/2026-05-18-phase59-t-handle-figure-agreement-diagnostics.md`
- Modify: `scripts/validate_docs.py`
- Modify: `tests/test_phase0_bootstrap.py`
- Modify: `reports/experiment_matrix/single_body_t_handle_rk4_reference.json`
- Modify: `reports/experiment_matrix/single_body_t_handle_mabd_newton.json`
- Modify: `reports/experiment_matrix/single_body_t_handle_comparison.json`

- [ ] **Step 1: Regenerate reports**

Run the T-handle lanes with current source and vendored Newton commits:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/run_experiment.py --lane t_handle_rk4_reference --config configs/experiments/single_body_t_handle.yaml --matrix configs/experiments/paper_experiment_matrix.yaml --source-commit <commit> --vendored-newton-commit <newton-commit>
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/run_experiment.py --lane t_handle_mabd_newton --config configs/experiments/single_body_t_handle.yaml --matrix configs/experiments/paper_experiment_matrix.yaml --source-commit <commit> --vendored-newton-commit <newton-commit>
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/run_experiment.py --lane t_handle_comparison --config configs/experiments/single_body_t_handle.yaml --matrix configs/experiments/paper_experiment_matrix.yaml --rbd-report reports/experiment_matrix/single_body_t_handle_rk4_reference.json --mabd-report reports/experiment_matrix/single_body_t_handle_mabd_newton.json --figure-report reports/experiment_matrix/single_body_t_handle_figure_curves.json --source-commit <commit> --vendored-newton-commit <newton-commit>
```

- [ ] **Step 2: Add Phase59 validator checks**

Validate that committed reports contain finite figure-agreement diagnostics,
retain incomplete status, retain `sample_grid_flip_delta_unavailable`, retain
all required blockers, and persist the normalized-time / best-color-family
disclaimers:

- `normalized_figure_time_not_paper_raw_time`
- `numeric_best_fit_not_legend_identity`
- `diagnostic_only_not_curve_agreement`

Add durable Phase59 boundary bullets to `docs/reference/claim-boundaries.md`
with the same shape as Phase58:

- This repository contains Phase59 T-handle digitized-figure agreement
  diagnostic evidence.
- Phase59 verifies normalized-time numeric error diagnostics against digitized
  color-family curves.
- Phase59 does not verify raw curve agreement, legend-entry identity, paper raw
  time alignment, energy-loss agreement, timing, rendered output, pass gates,
  full reproduction, or any passed `experiment.*` claim.
- Phase59 evidence must not be described as any of the forbidden claims above.

Create the dated Phase59 record with command, config path, repo commit,
vendored Newton source commit, paper source version, environment, backend, seed
status, metrics, thresholds, raw artifacts, report hashes, retained blockers,
and incomplete status.

- [ ] **Step 3: Run focused docs/tests**

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_t_handle_reference tests.test_t_handle_comparison_reports tests.test_phase0_bootstrap
```

Expected: pass.

### Task 6: Final Verification

**Files:**
- All modified files

- [ ] **Step 1: Run full gates**

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"
/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .
git diff --check
```

Expected: all pass.
