# Phase 72 Spinning-Box Figure Momentum Endpoint Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Correct the spinning-box digitized figure diagnostic to compare paper endpoint momentum values against lane endpoint momentum magnitudes instead of momentum error fields.

**Architecture:** Keep the existing comparison report schema and diagnostic-only status. Add a small endpoint-value resolver in `comparison_reports.py` that derives linear and angular momentum magnitudes from available lane report fields, then use it in `_spinning_box_figure_metric_diagnostic`.

**Tech Stack:** Python 3.10, `unittest`, existing `ClaimReport` JSON artifacts.

---

### Task 1: Red Test For Endpoint Momentum Sources

**Files:**
- Modify: `tests/test_spinning_box_comparison.py`

- [ ] **Step 1: Write the failing test expectation**

Change `test_spinning_box_comparison_consumes_valid_figure_curve_report` so the
linear M-ABD diagnostic expects endpoint momentum source and magnitude:

```python
self.assertEqual(linear_mabd["lane_value_source"], "final_linear_momentum_norm")
self.assertGreater(linear_mabd["lane_value"], 99.0)
self.assertLess(linear_mabd["lane_value"], 101.0)
self.assertLess(linear_mabd["best_abs_error"], 5.0)
```

Also assert the angular M-ABD and RBD diagnostics use endpoint momentum
sources:

```python
angular_mabd = diagnostics["angular_momentum"]["mabd_newton"]
self.assertEqual(angular_mabd["lane_value_source"], "final_angular_momentum_norm")
self.assertGreater(angular_mabd["lane_value"], 99.0)
self.assertLess(angular_mabd["lane_value"], 101.0)
self.assertLess(angular_mabd["best_abs_error"], 5.0)

linear_rbd = diagnostics["linear_momentum"]["rbd_implicit_baseline"]
self.assertEqual(linear_rbd["lane_value_source"], "final_linear_momentum_norm")
self.assertGreater(linear_rbd["lane_value"], 99.0)
self.assertLess(linear_rbd["lane_value"], 101.0)

angular_rbd = diagnostics["angular_momentum"]["rbd_implicit_baseline"]
self.assertEqual(angular_rbd["lane_value_source"], "final_angular_momentum_norm")
self.assertGreater(angular_rbd["lane_value"], 99.0)
self.assertLess(angular_rbd["lane_value"], 101.0)
```

- [ ] **Step 2: Run the red test**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_spinning_box_comparison.SpinningBoxComparisonTests.test_spinning_box_comparison_consumes_valid_figure_curve_report
```

Expected: FAIL because `lane_value_source` is still
`linear_momentum_error` / `angular_momentum_error`.

### Task 2: Implement Endpoint Momentum Resolver

**Files:**
- Modify: `src/mabd_reproduction/comparison_reports.py`

- [ ] **Step 1: Add vector norm helpers**

Add helpers near `_finite_vector3`:

```python
def _vector3_norm(value: Any) -> float | None:
    vector = _finite_vector3(value)
    if vector is None:
        return None
    result = sqrt(sum(component * component for component in vector))
    return result if isfinite(result) else None
```

- [ ] **Step 2: Add spinning-box endpoint source resolver**

Add:

```python
def _spinning_box_lane_endpoint_momentum_value(
    report: ClaimReport,
    *,
    metric: str,
) -> tuple[float | None, str]:
    if metric == "linear_momentum":
        value = _vector3_norm(report.observed.get("final_linear_momentum_kg_m_s"))
        if value is not None:
            return value, "final_linear_momentum_norm"
        mass = _finite_scalar(report.observed.get("mass_kg"))
        velocity = _finite_vector3(report.observed.get("linear_velocity_m_s"))
        if mass is not None and velocity is not None:
            momentum = [mass * component for component in velocity]
            value = sqrt(sum(component * component for component in momentum))
            return (value if isfinite(value) else None), "final_linear_momentum_norm"
        return None, "final_linear_momentum_norm"
    if metric == "angular_momentum":
        value = _vector3_norm(report.observed.get("final_angular_momentum_kg_m2_s"))
        if value is not None:
            return value, "final_angular_momentum_norm"
        inertia = _finite_vector3(report.observed.get("inertia_diag_kg_m2"))
        angular_velocity = _finite_vector3(report.observed.get("angular_velocity_rad_s"))
        if inertia is not None and angular_velocity is not None:
            momentum = [
                inertia_component * omega_component
                for inertia_component, omega_component in zip(inertia, angular_velocity, strict=True)
            ]
            value = sqrt(sum(component * component for component in momentum))
            return (value if isfinite(value) else None), "final_angular_momentum_norm"
        return None, "final_angular_momentum_norm"
    raise ValueError(f"unsupported spinning-box figure metric: {metric}")
```

- [ ] **Step 3: Use the resolver in `_spinning_box_figure_metric_diagnostic`**

Replace:

```python
lane_metric = metric_config["lane_metric"]
lane_value = _finite_scalar(report.observed.get(lane_metric))
```

with:

```python
lane_value, lane_metric = _spinning_box_lane_endpoint_momentum_value(
    report,
    metric=metric,
)
```

Keep the existing `lane_value_source` output key, now populated with the endpoint
source label.

- [ ] **Step 4: Run the green test**

Run the same unittest command from Task 1. Expected: PASS.

### Task 3: Regenerate Report And Evidence

**Files:**
- Modify: `reports/experiment_matrix/single_body_spinning_box_comparison.json`
- Modify: `docs/reference/claim-boundaries.md`
- Modify: `scripts/validate_docs.py`
- Modify: `tests/test_phase0_bootstrap.py`
- Create: `docs/records/2026-05-20-phase72-spinning-box-figure-momentum-endpoint.md`

- [ ] **Step 1: Regenerate comparison report**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/run_experiment.py --lane spinning_box_comparison --config configs/experiments/single_body_spinning_box.yaml --matrix configs/experiments/paper_experiment_matrix.yaml --mabd-report reports/experiment_matrix/single_body_spinning_box.json --rbd-report reports/experiment_matrix/single_body_spinning_box_rbd_baseline.json --figure-report reports/experiment_matrix/single_body_spinning_box_figure_curves.json --output reports/experiment_matrix/single_body_spinning_box_comparison.json --source-commit TO_BE_BACKFILLED_PHASE72 --vendored-newton-commit 96713fa965463b69c229a4d30582c733ff3526bb
```

Expected summary JSON reports `status = incomplete`.

- [ ] **Step 2: Add docs boundaries and validator**

Add Phase 72 claim-boundary bullets and a validator requiring:

```python
"final_linear_momentum_norm"
"final_angular_momentum_norm"
"digitized_figure_curve_agreement_passed = false"
"spinning_box_digitized_figure_curve_agreement_not_passed"
"No `experiment.*` claim is passed."
```

- [ ] **Step 3: Write Phase 72 record**

Record source commit, report SHA256, Python path, environment non-pollution,
metrics before/after source fix, verification commands, and claim impact.

- [ ] **Step 4: Run focused verification**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_spinning_box_comparison tests.test_experiment_runner tests.test_phase0_bootstrap
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
git diff --check
```

Expected: all pass, no whitespace errors.
