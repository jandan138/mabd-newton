# Phase 17 Spinning-Box M-ABD Paper Metrics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add paper-facing linear and angular momentum diagnostics to the M-ABD single-body spinning-box development lane while keeping the experiment claim incomplete.

**Architecture:** Put paper-value parsing and rigid cube momentum helpers in a small shared module so the M-ABD lane and RBD development baseline use the same cube mass, inertia, `p0`, and `L0` interpretation. The M-ABD report will initialize its configured `initial_qd` from the paper spatial twist via Newton's existing M-ABD rigid embedding, record final momentum errors via the existing twist map, and remain `incomplete`.

**Tech Stack:** Python 3.10, NumPy, PyYAML, `unittest`, vendored Newton M-ABD CPU oracle, canonical `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python`.

---

## Completion Audit

Objective: "完全实现 推进到底 using superpowers" means this repository is not done until the Newton-only M-ABD method and every paper evidence claim are implemented, run, and recorded without overclaiming.

Current evidence after Phase 16:

- `docs/reference/paper-claims.yaml`: 18 claims are `passed`, 15 `experiment.*` claims remain `intended`.
- `configs/experiments/paper_experiment_matrix.yaml`: 5 experiments are `planned`, 5 are `blocked_by_baselines`, and 5 are `blocked_by_assets`.
- `experiment.single_body.spinning_box` remains `blocked_by_baselines` with blockers `rbd_implicit_baseline_report_incomplete` and `spinning_box_comparison_report_incomplete`.
- `docs/reference/claim-boundaries.md` explicitly says Phase 16 does not verify the paper spinning-box experiment or any passed `experiment.*` claim.

Phase 17 is not the full objective. It removes one concrete weakness in the nearest lane: the M-ABD spinning-box report currently lacks the paper comparison metrics `linear_momentum_error` and `angular_momentum_error`, so the comparison protocol reports M-ABD metric-missing blockers.

## File Structure

- Create: `src/mabd_reproduction/spinning_box_physics.py`
  - Owns parsing of spinning-box paper physical values.
  - Computes cube mass, isotropic inertia, target spatial twist, ABD generalized velocity, and M-ABD momentum diagnostics.
- Modify: `src/mabd_reproduction/rigid_baselines.py`
  - Reuse shared paper-value parsing/properties.
  - Preserve public `spinning_box_rbd_properties(config)` behavior.
- Modify: `src/mabd_reproduction/single_body_reports.py`
  - Use paper-mapped `initial_qd` for configured spinning-box runs.
  - Add paper-facing momentum metrics to `observed` and thresholds.
- Modify: `configs/experiments/single_body_spinning_box.yaml`
  - Replace synthetic `initial_qd` with `rigid_embedding_E(I) @ [omega0, v0]` from paper `p0/L0`.
  - Add thresholds for `linear_momentum_error` and `angular_momentum_error`.
- Modify tests:
  - `tests/test_experiment_run_configs.py`
  - `tests/test_single_body_report_lane.py`
  - `tests/test_spinning_box_comparison.py`
  - `tests/test_rigid_baselines.py`
  - `tests/test_phase0_bootstrap.py`
- Modify docs:
  - `docs/reference/claim-boundaries.md`
  - `docs/records/2026-05-17-phase17-spinning-box-mabd-paper-metrics.md`
  - `scripts/validate_docs.py`

## Task 1: Shared Spinning-Box Physics Helpers

**Files:**
- Create: `src/mabd_reproduction/spinning_box_physics.py`
- Modify: `tests/test_rigid_baselines.py`
- Modify: `src/mabd_reproduction/rigid_baselines.py`

- [ ] **Step 1: Write failing shared-helper tests**

Add this test to `tests/test_rigid_baselines.py`:

```python
    def test_shared_spinning_box_physics_maps_paper_momenta_to_abd_velocity(self) -> None:
        from newton.solvers import mabd

        from mabd_reproduction.experiment_configs import load_spinning_box_config
        from mabd_reproduction.spinning_box_physics import (
            abd_generalized_velocity_from_paper_momenta,
            spinning_box_physical_properties,
        )

        config = load_spinning_box_config(ROOT / "configs/experiments/single_body_spinning_box.yaml")
        properties = spinning_box_physical_properties(config)
        qd = abd_generalized_velocity_from_paper_momenta(config)

        self.assertEqual(qd.shape, (12,))
        np.testing.assert_allclose(properties.mass_kg, 1.0)
        np.testing.assert_allclose(properties.inertia_diag_kg_m2, [1.0 / 600.0] * 3)
        np.testing.assert_allclose(properties.linear_velocity_m_s, [100.0, 0.0, 0.0])
        np.testing.assert_allclose(properties.angular_velocity_rad_s, [0.0, 60000.0, 0.0])
        np.testing.assert_allclose(
            mabd.twist_map_G(np.eye(3)) @ qd,
            [0.0, 60000.0, 0.0, 100.0, 0.0, 0.0],
            atol=1.0e-12,
        )
```

- [ ] **Step 2: Run test to verify RED**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_rigid_baselines
```

Expected: fail with `ModuleNotFoundError: No module named 'mabd_reproduction.spinning_box_physics'`.

- [ ] **Step 3: Implement shared module**

Create `src/mabd_reproduction/spinning_box_physics.py`:

```python
"""Shared paper-value physics helpers for the single-body spinning-box scene."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Any

import numpy as np
from newton.solvers import mabd

from .experiment_configs import SpinningBoxRunConfig


@dataclass(frozen=True)
class SpinningBoxPhysicalProperties:
    cube_size_m: float
    density_kg_m3: float
    mass_kg: float
    inertia_diag_kg_m2: np.ndarray
    linear_momentum_kg_m_s: np.ndarray
    angular_momentum_kg_m2_s: np.ndarray
    linear_velocity_m_s: np.ndarray
    angular_velocity_rad_s: np.ndarray


@dataclass(frozen=True)
class SpinningBoxMABDMomentumDiagnostics:
    spatial_twist: np.ndarray
    linear_momentum_kg_m_s: np.ndarray
    angular_momentum_kg_m2_s: np.ndarray
    linear_momentum_error: float
    angular_momentum_error: float


def _paper_float(value: Any, name: str, *, positive: bool = False) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{name} must be numeric")
    if isinstance(value, int | float):
        result = float(value)
    elif isinstance(value, str) and value:
        try:
            result = float(value.split()[0])
        except ValueError as exc:
            raise ValueError(f"{name} must start with a numeric value") from exc
    else:
        raise ValueError(f"{name} must be numeric")
    if not isfinite(result):
        raise ValueError(f"{name} must be finite")
    if positive and result <= 0.0:
        raise ValueError(f"{name} must be positive")
    return result


def _paper_vector(value: Any, name: str) -> np.ndarray:
    vector = np.asarray(value, dtype=float)
    if vector.shape != (3,):
        raise ValueError(f"{name} must contain 3 numeric values")
    if not np.all(np.isfinite(vector)):
        raise ValueError(f"{name} must contain 3 finite numeric values")
    return vector


def spinning_box_physical_properties(config: SpinningBoxRunConfig) -> SpinningBoxPhysicalProperties:
    cube_size_m = _paper_float(config.paper_values.get("cube_size_m"), "cube_size_m", positive=True)
    density_kg_m3 = _paper_float(config.paper_values.get("density"), "density", positive=True)
    mass_kg = density_kg_m3 * cube_size_m**3
    inertia_diag = np.full(3, (1.0 / 6.0) * mass_kg * cube_size_m**2, dtype=float)
    linear_momentum = _paper_vector(config.paper_values.get("p0"), "p0")
    angular_momentum = _paper_vector(config.paper_values.get("L0"), "L0")
    return SpinningBoxPhysicalProperties(
        cube_size_m=cube_size_m,
        density_kg_m3=density_kg_m3,
        mass_kg=mass_kg,
        inertia_diag_kg_m2=inertia_diag,
        linear_momentum_kg_m_s=linear_momentum,
        angular_momentum_kg_m2_s=angular_momentum,
        linear_velocity_m_s=linear_momentum / mass_kg,
        angular_velocity_rad_s=angular_momentum / inertia_diag,
    )


def paper_spatial_twist_from_momenta(config: SpinningBoxRunConfig) -> np.ndarray:
    properties = spinning_box_physical_properties(config)
    return np.concatenate([properties.angular_velocity_rad_s, properties.linear_velocity_m_s])


def abd_generalized_velocity_from_paper_momenta(
    config: SpinningBoxRunConfig,
    A: np.ndarray | None = None,
) -> np.ndarray:
    A_arr = np.eye(3) if A is None else np.asarray(A, dtype=float)
    return mabd.rigid_embedding_E(A_arr) @ paper_spatial_twist_from_momenta(config)


def mabd_momentum_diagnostics(
    config: SpinningBoxRunConfig,
    q: np.ndarray,
    qd: np.ndarray,
) -> SpinningBoxMABDMomentumDiagnostics:
    properties = spinning_box_physical_properties(config)
    A, _t = mabd.unpack_q(q)
    spatial_twist = mabd.twist_map_G(A) @ np.asarray(qd, dtype=float)
    linear_momentum = properties.mass_kg * spatial_twist[3:6]
    angular_momentum = properties.inertia_diag_kg_m2 * spatial_twist[0:3]
    return SpinningBoxMABDMomentumDiagnostics(
        spatial_twist=spatial_twist,
        linear_momentum_kg_m_s=linear_momentum,
        angular_momentum_kg_m2_s=angular_momentum,
        linear_momentum_error=float(np.linalg.norm(linear_momentum - properties.linear_momentum_kg_m_s)),
        angular_momentum_error=float(np.linalg.norm(angular_momentum - properties.angular_momentum_kg_m2_s)),
    )


__all__ = [
    "SpinningBoxMABDMomentumDiagnostics",
    "SpinningBoxPhysicalProperties",
    "abd_generalized_velocity_from_paper_momenta",
    "mabd_momentum_diagnostics",
    "paper_spatial_twist_from_momenta",
    "spinning_box_physical_properties",
]
```

- [ ] **Step 4: Reuse shared properties in RBD baseline**

Modify `src/mabd_reproduction/rigid_baselines.py`:

- Delete local `_paper_float` and `_paper_vector`.
- Import shared dataclass/function:

```python
from .spinning_box_physics import (
    SpinningBoxPhysicalProperties,
    spinning_box_physical_properties,
)
```

- Replace the `SpinningBoxRBDProperties` dataclass with an alias:

```python
SpinningBoxRBDProperties = SpinningBoxPhysicalProperties
```

- Replace `spinning_box_rbd_properties(...)` body with:

```python
def spinning_box_rbd_properties(config: SpinningBoxRunConfig) -> SpinningBoxRBDProperties:
    return spinning_box_physical_properties(config)
```

- Remove unused imports `isfinite` and `Any`.

- [ ] **Step 5: Run Task 1 GREEN checks**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_rigid_baselines
/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check src/mabd_reproduction/spinning_box_physics.py src/mabd_reproduction/rigid_baselines.py tests/test_rigid_baselines.py
git diff --check
```

Expected: tests pass, ruff clean, diff check clean.

- [ ] **Step 6: Commit Task 1**

```bash
git add src/mabd_reproduction/spinning_box_physics.py src/mabd_reproduction/rigid_baselines.py tests/test_rigid_baselines.py
git commit -m "feat: share spinning-box paper physics helpers"
```

## Task 2: M-ABD Lane Paper Momentum Metrics

**Files:**
- Modify: `configs/experiments/single_body_spinning_box.yaml`
- Modify: `tests/test_experiment_run_configs.py`
- Modify: `tests/test_single_body_report_lane.py`
- Modify: `src/mabd_reproduction/single_body_reports.py`

- [ ] **Step 1: Write failing config and report tests**

Add assertions to `tests/test_experiment_run_configs.py::test_spinning_box_config_is_machine_checkable`:

```python
        from newton.solvers import mabd

        from mabd_reproduction.spinning_box_physics import (
            abd_generalized_velocity_from_paper_momenta,
            spinning_box_physical_properties,
        )

        properties = spinning_box_physical_properties(config)
        np.testing.assert_allclose(
            config.initial_qd,
            abd_generalized_velocity_from_paper_momenta(config),
            atol=1.0e-12,
        )
        np.testing.assert_allclose(
            mabd.twist_map_G(np.eye(3)) @ config.initial_qd,
            [0.0, 60000.0, 0.0, 100.0, 0.0, 0.0],
            atol=1.0e-12,
        )
        np.testing.assert_allclose(properties.linear_momentum_kg_m_s, [100.0, 0.0, 0.0])
        np.testing.assert_allclose(properties.angular_momentum_kg_m2_s, [0.0, 100.0, 0.0])
        self.assertIn("linear_momentum_error", config.thresholds)
        self.assertIn("angular_momentum_error", config.thresholds)
```

Add assertions to `tests/test_single_body_report_lane.py::test_spinning_box_report_uses_run_config`:

```python
        self.assertIn("linear_momentum_error", loaded.observed)
        self.assertIn("angular_momentum_error", loaded.observed)
        self.assertIn("final_linear_momentum_kg_m_s", loaded.observed)
        self.assertIn("final_angular_momentum_kg_m2_s", loaded.observed)
        self.assertIn("paper_spatial_twist", loaded.observed)
        self.assertLessEqual(
            loaded.observed["linear_momentum_error"],
            loaded.threshold["linear_momentum_error"],
        )
        self.assertLessEqual(
            loaded.observed["angular_momentum_error"],
            loaded.threshold["angular_momentum_error"],
        )
```

- [ ] **Step 2: Run tests to verify RED**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_run_configs tests.test_single_body_report_lane
```

Expected: fail because config still has synthetic `initial_qd` and the report lacks momentum metrics.

- [ ] **Step 3: Update spinning-box config**

Replace `simulation.initial_qd` in `configs/experiments/single_body_spinning_box.yaml` with:

```yaml
  initial_qd:
    - 0.0
    - 0.0
    - -60000.0
    - 0.0
    - 0.0
    - 0.0
    - 60000.0
    - 0.0
    - 0.0
    - 100.0
    - 0.0
    - 0.0
```

Add thresholds under `report.thresholds`:

```yaml
    linear_momentum_error: 1.0e-9
    angular_momentum_error: 1.0e-9
```

- [ ] **Step 4: Add M-ABD diagnostics to report implementation**

Modify `src/mabd_reproduction/single_body_reports.py`:

- Import helpers:

```python
from .spinning_box_physics import (
    abd_generalized_velocity_from_paper_momenta,
    mabd_momentum_diagnostics,
)
```

- For configured runs, validate the config uses the paper-mapped velocity:

```python
    if config is not None:
        expected_qd = abd_generalized_velocity_from_paper_momenta(config)
        if not np.allclose(qd, expected_qd, rtol=0.0, atol=1.0e-12):
            raise ValueError("single_body_spinning_box initial_qd must map paper p0/L0 to ABD velocity")
```

- Before the time loop, compute:

```python
    initial_diagnostics = mabd_momentum_diagnostics(config, q, qd) if config is not None else None
```

- After the time loop, compute:

```python
    final_diagnostics = mabd_momentum_diagnostics(config, q, qd) if config is not None else None
```

- Build `observed` before constructing `ClaimReport`:

```python
    observed = {
        "step_count": step_count,
        "time_step_s": dt,
        "energy_drift": energy_drift,
        "generalized_momentum_delta_norm": momentum_delta,
    }
    if initial_diagnostics is not None and final_diagnostics is not None:
        observed.update(
            {
                "paper_spatial_twist": initial_diagnostics.spatial_twist.tolist(),
                "final_spatial_twist": final_diagnostics.spatial_twist.tolist(),
                "final_linear_momentum_kg_m_s": final_diagnostics.linear_momentum_kg_m_s.tolist(),
                "final_angular_momentum_kg_m2_s": final_diagnostics.angular_momentum_kg_m2_s.tolist(),
                "linear_momentum_error": final_diagnostics.linear_momentum_error,
                "angular_momentum_error": final_diagnostics.angular_momentum_error,
            }
        )
```

- Pass `observed=observed` into `ClaimReport`.

- [ ] **Step 5: Run Task 2 GREEN checks**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_run_configs tests.test_single_body_report_lane
/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check src/mabd_reproduction/single_body_reports.py tests/test_experiment_run_configs.py tests/test_single_body_report_lane.py
git diff --check
```

Expected: tests pass, ruff clean, diff check clean.

- [ ] **Step 6: Commit Task 2**

```bash
git add configs/experiments/single_body_spinning_box.yaml src/mabd_reproduction/single_body_reports.py tests/test_experiment_run_configs.py tests/test_single_body_report_lane.py
git commit -m "feat: record spinning-box M-ABD paper momentum metrics"
```

## Task 3: Comparison Protocol Uses M-ABD Metrics

**Files:**
- Modify: `tests/test_spinning_box_comparison.py`
- Modify: `tests/test_experiment_runner.py`

- [ ] **Step 1: Write failing comparison assertions**

Modify `tests/test_spinning_box_comparison.py::test_write_spinning_box_comparison_report_records_incomplete_protocol`:

- Replace the two M-ABD missing-metric assertions with:

```python
        self.assertNotIn("mabd_newton:linear_momentum_error", loaded.observed["missing_required_metrics"])
        self.assertNotIn("mabd_newton:angular_momentum_error", loaded.observed["missing_required_metrics"])
        self.assertNotIn("mabd_newton:energy_drift", loaded.observed["missing_required_metrics"])
        self.assertEqual(
            loaded.observed["lane_metrics"]["mabd_newton"]["linear_momentum_error"],
            0.0,
        )
        self.assertEqual(
            loaded.observed["lane_metrics"]["mabd_newton"]["angular_momentum_error"],
            0.0,
        )
```

Add an equivalent assertion to `tests/test_experiment_runner.py::test_run_spinning_box_comparison_writes_explicit_output_report`:

```python
        self.assertNotIn("mabd_newton:linear_momentum_error", loaded.observed["missing_required_metrics"])
        self.assertNotIn("mabd_newton:angular_momentum_error", loaded.observed["missing_required_metrics"])
```

- [ ] **Step 2: Run tests to verify RED if Task 2 is not implemented**

Run before Task 2 GREEN if executing independently:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_spinning_box_comparison tests.test_experiment_runner
```

Expected before Task 2: fail because M-ABD report metrics are missing. Expected after Task 2: pass.

- [ ] **Step 3: Run Task 3 GREEN checks**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_spinning_box_comparison tests.test_experiment_runner
/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check tests/test_spinning_box_comparison.py tests/test_experiment_runner.py
git diff --check
```

Expected: tests pass, ruff clean, diff check clean.

- [ ] **Step 4: Commit Task 3**

```bash
git add tests/test_spinning_box_comparison.py tests/test_experiment_runner.py
git commit -m "test: assert comparison consumes M-ABD paper metrics"
```

## Task 4: Phase 17 Docs, Bounds, And Record

**Files:**
- Modify: `docs/reference/claim-boundaries.md`
- Modify: `scripts/validate_docs.py`
- Modify: `tests/test_phase0_bootstrap.py`
- Create: `docs/records/2026-05-17-phase17-spinning-box-mabd-paper-metrics.md`

- [ ] **Step 1: Write failing docs tests**

Add to `tests/test_phase0_bootstrap.py`:

```python
    def test_phase17_spinning_box_mabd_paper_metrics_are_bounded(self) -> None:
        text = (ROOT / "docs/reference/claim-boundaries.md").read_text()
        normalized_text = " ".join(text.split())

        self.assertIn("Phase 17 verifies paper-value momentum metric reporting", text)
        self.assertIn("M-ABD spinning-box development lane", normalized_text)
        self.assertIn("paper p0/L0", normalized_text)
        self.assertIn("Phase 17 does not verify the paper spinning-box experiment", text)
        self.assertIn("paper-faithful implicit RBD baseline", normalized_text)
        self.assertIn("paper timing", normalized_text)
        self.assertIn("any passed `experiment.*` claim", normalized_text)

    def test_phase17_record_has_required_evidence_fields(self) -> None:
        text = (
            ROOT / "docs/records/2026-05-17-phase17-spinning-box-mabd-paper-metrics.md"
        ).read_text()

        for snippet in (
            "## Status",
            "passed",
            "## Config Path",
            "configs/experiments/single_body_spinning_box.yaml",
            "## Repository",
            "plan commit:",
            "implementation commits:",
            "## Paper Source",
            "experiment.tex:40-55",
            "## Environment",
            "mabd-newton-py310",
            "## Metrics And Thresholds",
            "paper_spatial_twist",
            "linear_momentum_error",
            "angular_momentum_error",
            "spinning_box_comparison_report_incomplete",
            "## Artifacts",
            "`src/mabd_reproduction/spinning_box_physics.py`",
            "`write_spinning_box_development_report`",
            "No `experiment.*` claim is passed in this phase.",
        ):
            self.assertIn(snippet, text)
```

Update `test_docs_validator_accepts_phase0_contract` expected string to include `/17`.

- [ ] **Step 2: Run docs tests to verify RED**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_phase0_bootstrap
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
```

Expected: fail because Phase 17 boundaries and record are missing.

- [ ] **Step 3: Update claim boundaries**

Add a Phase 17 Current bullet:

```markdown
- This repository contains Phase 17 paper-value momentum metric reporting for
  the M-ABD single-body spinning-box development lane after the Phase 17 record
  is created.
```

Add Verified bullets:

```markdown
- Phase 17 verifies paper-value momentum metric reporting for the M-ABD
  spinning-box development lane: paper `p0/L0` parsing, ABD generalized
  velocity initialization via the rigid embedding map, final spatial twist
  extraction via the paper twist map, and `linear_momentum_error` /
  `angular_momentum_error` fields consumed by the comparison protocol.
- Phase 17 does not verify the paper spinning-box experiment,
  paper-faithful implicit RBD baseline, paper-faithful affine collision, paper
  timing, rendered output, paper trajectory agreement, generated report
  artifacts as committed evidence, or any passed `experiment.*` claim.
```

- [ ] **Step 4: Update docs validator**

In `scripts/validate_docs.py`:

- Add the Phase 17 record path to `REQUIRED_PATHS`.
- Extend `validate_claim_boundaries()` with Phase 17 required and forbidden snippets.
- Add `validate_phase17_record()` requiring the snippets from the test plus:
  - `spinning_box_physics.py`
  - `abd_generalized_velocity_from_paper_momenta`
  - `mabd_momentum_diagnostics`
  - `linear_momentum_error <= 1.0e-9`
  - `angular_momentum_error <= 1.0e-9`
- Call `validate_phase17_record()` from `main()`.
- Update final print to:

```python
print("Phase 0/1/2/3/4/5/6/7/8/9/10/11/12/13/14/15/16/17 docs/provenance validation passed")
```

- [ ] **Step 5: Create Phase 17 record**

Create `docs/records/2026-05-17-phase17-spinning-box-mabd-paper-metrics.md` with:

- status `passed`
- config path
- base commit `12be437`
- plan commit placeholder to fill after committing this plan
- implementation commits placeholder to fill after Task 1-3 commits
- paper source checksums from earlier records
- environment paths
- metrics: paper `p0/L0`, `paper_spatial_twist`, `linear_momentum_error`, `angular_momentum_error`, thresholds `1.0e-9`
- artifact list
- explicit no-pass claim impact

- [ ] **Step 6: Run Task 4 GREEN checks**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_phase0_bootstrap
/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check scripts/validate_docs.py tests/test_phase0_bootstrap.py
git diff --check
```

Expected: docs validator passes through Phase 17, tests pass, ruff clean, diff check clean.

- [ ] **Step 7: Commit Task 4**

```bash
git add docs/reference/claim-boundaries.md scripts/validate_docs.py tests/test_phase0_bootstrap.py docs/records/2026-05-17-phase17-spinning-box-mabd-paper-metrics.md
git commit -m "docs: record Phase 17 M-ABD paper momentum metrics"
```

## Task 5: Final Verification, Review, Merge, Push

**Files:**
- Modify: `docs/records/2026-05-17-phase17-spinning-box-mabd-paper-metrics.md`

- [ ] **Step 1: Run full verification**

Run:

```bash
/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_rigid_baselines tests.test_single_body_report_lane tests.test_spinning_box_comparison tests.test_experiment_runner tests.test_experiment_run_configs tests.test_phase0_bootstrap
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"
git diff --check
```

Expected: all commands pass; full public test count increases from 138.

- [ ] **Step 2: Request independent review**

Request two review agents:

- claim/spec review: Phase 17 boundaries, no `experiment.*` pass, docs validator coverage.
- code review: physical helper correctness, M-ABD report diagnostics, comparison metric behavior, no RBD overclaim.

- [ ] **Step 3: Apply valid findings**

If reviewers find critical or important issues, fix them with TDD where code changes are needed, rerun focused checks, and commit.

- [ ] **Step 4: Update Phase 17 record final verification**

Replace placeholders with concrete plan/implementation/review commits and verification counts. Commit:

```bash
git add docs/records/2026-05-17-phase17-spinning-box-mabd-paper-metrics.md
git commit -m "docs: add Phase 17 verification evidence"
```

- [ ] **Step 5: Re-run final verification**

Run the full verification command list from Step 1 again.

- [ ] **Step 6: Merge and push**

From `/cpfs/user/zhuzihou/dev/mabd-newton`:

```bash
git merge --ff-only phase17-spinning-box-mabd-paper-metrics
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
GIT_SSH_COMMAND='ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=accept-new' git push git@github.com:jandan138/mabd-newton.git main
GIT_SSH_COMMAND='ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=accept-new' git fetch git@github.com:jandan138/mabd-newton.git main:refs/remotes/origin/main
git worktree remove /cpfs/user/zhuzihou/dev/mabd-newton/.worktrees/phase17-spinning-box-mabd-paper-metrics
git branch -d phase17-spinning-box-mabd-paper-metrics
```

Expected: main and origin/main point at the Phase 17 final commit.
