# Phase 29 Spinning-Box Kinematic Feasibility Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add machine-checkable evidence that the paper spinning-box momenta require affine stretch under the standard `qd_next = (q_next - q_n) / h` update if `A_next` is kept near orthogonal.

**Architecture:** Add a small physics helper in `spinning_box_physics.py`, wire its per-step-size output into the Phase 28 paper-horizon diagnostic report, then update docs/records/validator gates. The report remains incomplete and still has no M-ABD `lane_gate_status`.

**Tech Stack:** Python 3.10, NumPy, PyYAML, unittest, vendored Newton M-ABD helpers, existing isolated `mabd-newton-py310` environment.

---

### Task 1: Physics Helper And Unit Evidence

**Files:**
- Modify: `src/mabd_reproduction/spinning_box_physics.py`
- Modify: `tests/test_rigid_baselines.py`

- [ ] **Step 1: Write the failing helper test**

Add this test to `tests/test_rigid_baselines.py` after `test_shared_spinning_box_physics_maps_paper_momenta_to_abd_velocity`:

```python
    def test_spinning_box_kinematic_feasibility_bounds_paper_momentum(self) -> None:
        from mabd_reproduction.spinning_box_physics import (
            spinning_box_kinematic_feasibility,
        )

        config = load_spinning_box_config(CONFIG_PATH)

        coarse = spinning_box_kinematic_feasibility(config, 0.01)
        fine = spinning_box_kinematic_feasibility(config, 0.001)

        self.assertEqual(
            coarse.status,
            "paper_momentum_requires_affine_stretch_under_q_delta_over_h",
        )
        self.assertEqual(
            fine.status,
            "paper_momentum_requires_affine_stretch_under_q_delta_over_h",
        )
        self.assertAlmostEqual(coarse.paper_angular_speed_rad_s, 60000.0)
        self.assertAlmostEqual(coarse.orthogonal_update_angular_speed_bound_rad_s, 100.0)
        self.assertAlmostEqual(fine.orthogonal_update_angular_speed_bound_rad_s, 1000.0)
        self.assertAlmostEqual(coarse.paper_angular_momentum_norm_kg_m2_s, 100.0)
        self.assertAlmostEqual(
            coarse.orthogonal_update_angular_momentum_bound_kg_m2_s,
            1.0 / 6.0,
        )
        self.assertAlmostEqual(
            fine.orthogonal_update_angular_momentum_bound_kg_m2_s,
            10.0 / 6.0,
        )
        self.assertAlmostEqual(coarse.required_speed_to_bound_ratio, 600.0)
        self.assertAlmostEqual(fine.required_speed_to_bound_ratio, 60.0)
        self.assertTrue(coarse.requires_affine_stretch)
        self.assertTrue(fine.requires_affine_stretch)
        self.assertEqual(
            coarse.to_report()["velocity_update_relation"],
            "qd_next=(q_next-q_n)/h",
        )
```

- [ ] **Step 2: Run the focused test and verify RED**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_rigid_baselines
```

Expected: fails with import error for `spinning_box_kinematic_feasibility`.

- [ ] **Step 3: Implement the helper**

In `src/mabd_reproduction/spinning_box_physics.py`, add a dataclass after `SpinningBoxContactDiagnostics`:

```python
@dataclass(frozen=True)
class SpinningBoxKinematicFeasibility:
    time_step_s: float
    paper_angular_speed_rad_s: float
    orthogonal_update_angular_speed_bound_rad_s: float
    paper_angular_momentum_norm_kg_m2_s: float
    orthogonal_update_angular_momentum_bound_kg_m2_s: float
    required_speed_to_bound_ratio: float
    requires_affine_stretch: bool
    velocity_update_relation: str
    status: str

    def to_report(self) -> dict[str, object]:
        return {
            "time_step_s": self.time_step_s,
            "paper_angular_speed_rad_s": self.paper_angular_speed_rad_s,
            "orthogonal_update_angular_speed_bound_rad_s": (
                self.orthogonal_update_angular_speed_bound_rad_s
            ),
            "paper_angular_momentum_norm_kg_m2_s": (
                self.paper_angular_momentum_norm_kg_m2_s
            ),
            "orthogonal_update_angular_momentum_bound_kg_m2_s": (
                self.orthogonal_update_angular_momentum_bound_kg_m2_s
            ),
            "required_speed_to_bound_ratio": self.required_speed_to_bound_ratio,
            "requires_affine_stretch": self.requires_affine_stretch,
            "velocity_update_relation": self.velocity_update_relation,
            "status": self.status,
        }
```

Add this helper before `__all__`:

```python
def spinning_box_kinematic_feasibility(
    config: SpinningBoxRunConfig,
    time_step_s: float,
) -> SpinningBoxKinematicFeasibility:
    dt = float(time_step_s)
    if dt <= 0.0:
        raise ValueError("time_step_s must be positive")
    properties = spinning_box_physical_properties(config)
    angular_speed = properties.angular_velocity_rad_s
    angular_momentum = properties.angular_momentum_kg_m2_s
    paper_speed_norm = float(np.linalg.norm(angular_speed))
    paper_momentum_norm = float(np.linalg.norm(angular_momentum))
    speed_bound = 1.0 / dt
    inertia_bound = float(np.max(properties.inertia_diag_kg_m2))
    momentum_bound = inertia_bound * speed_bound
    ratio = paper_speed_norm / speed_bound
    requires_stretch = bool(paper_momentum_norm > momentum_bound * (1.0 + 1.0e-12))
    status = (
        "paper_momentum_requires_affine_stretch_under_q_delta_over_h"
        if requires_stretch
        else "orthogonal_update_can_represent_paper_momentum"
    )
    return SpinningBoxKinematicFeasibility(
        time_step_s=dt,
        paper_angular_speed_rad_s=paper_speed_norm,
        orthogonal_update_angular_speed_bound_rad_s=speed_bound,
        paper_angular_momentum_norm_kg_m2_s=paper_momentum_norm,
        orthogonal_update_angular_momentum_bound_kg_m2_s=momentum_bound,
        required_speed_to_bound_ratio=ratio,
        requires_affine_stretch=requires_stretch,
        velocity_update_relation="qd_next=(q_next-q_n)/h",
        status=status,
    )
```

Add `"SpinningBoxKinematicFeasibility"` and `"spinning_box_kinematic_feasibility"` to `__all__`.

- [ ] **Step 4: Run focused tests and verify GREEN**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_rigid_baselines
```

Expected: all `tests.test_rigid_baselines` tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/mabd_reproduction/spinning_box_physics.py tests/test_rigid_baselines.py
git commit -m "feat: add spinning-box kinematic feasibility helper"
```

### Task 2: Report Wiring

**Files:**
- Modify: `src/mabd_reproduction/single_body_reports.py`
- Modify: `tests/test_single_body_report_lane.py`

- [ ] **Step 1: Write failing report assertions**

In `test_spinning_box_paper_horizon_report_records_development_gap`, add:

```python
        self.assertEqual(
            loaded.observed["mabd_kinematic_feasibility_status"],
            "paper_momentum_requires_affine_stretch_under_q_delta_over_h",
        )
```

Inside the loop over `paper_horizon_results`, add:

```python
            self.assertIn("kinematic_feasibility", entry)
            feasibility = entry["kinematic_feasibility"]
            self.assertEqual(
                feasibility["status"],
                "paper_momentum_requires_affine_stretch_under_q_delta_over_h",
            )
            self.assertTrue(feasibility["requires_affine_stretch"])
            self.assertEqual(
                feasibility["velocity_update_relation"],
                "qd_next=(q_next-q_n)/h",
            )
            if entry["time_step_s"] == 0.01:
                self.assertAlmostEqual(feasibility["required_speed_to_bound_ratio"], 600.0)
            if entry["time_step_s"] == 0.001:
                self.assertAlmostEqual(feasibility["required_speed_to_bound_ratio"], 60.0)
```

- [ ] **Step 2: Run focused report test and verify RED**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_single_body_report_lane
```

Expected: fails because report lacks `mabd_kinematic_feasibility_status` and per-step `kinematic_feasibility`.

- [ ] **Step 3: Wire helper into report**

In `src/mabd_reproduction/single_body_reports.py`, import `spinning_box_kinematic_feasibility`.

In `_run_spinning_box_paper_horizon_step_size(...)`, compute:

```python
    feasibility = spinning_box_kinematic_feasibility(config, time_step_s)
```

Add to `summary`:

```python
        "kinematic_feasibility": feasibility.to_report(),
```

In `write_spinning_box_paper_horizon_report(...)`, compute statuses:

```python
    feasibility_statuses = sorted(
        {
            str(result["kinematic_feasibility"]["status"])
            for result in results
        }
    )
```

Add to `observed`:

```python
        "mabd_kinematic_feasibility_status": (
            feasibility_statuses[0]
            if len(feasibility_statuses) == 1
            else "mixed_kinematic_feasibility_statuses"
        ),
        "mabd_kinematic_feasibility_statuses": feasibility_statuses,
```

Append `"mabd_kinematic_feasibility_blocker_recorded"` to the diagnostic blocking reasons when any feasibility status is `paper_momentum_requires_affine_stretch_under_q_delta_over_h`.

- [ ] **Step 4: Run focused report tests and verify GREEN**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_single_body_report_lane
```

Expected: all report lane tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/mabd_reproduction/single_body_reports.py tests/test_single_body_report_lane.py
git commit -m "feat: record spinning-box MABD feasibility diagnostics"
```

### Task 3: Docs, Validator, And Record

**Files:**
- Modify: `docs/reference/claim-boundaries.md`
- Create: `docs/records/2026-05-17-phase29-spinning-box-kinematic-feasibility.md`
- Modify: `scripts/validate_docs.py`
- Modify: `tests/test_phase0_bootstrap.py`

- [ ] **Step 1: Write docs validator tests first**

Add tests in `tests/test_phase0_bootstrap.py` mirroring Phase 28 patterns:

- require claim-boundary bullets for `This repository contains Phase 29`, `Phase 29 verifies`, and `Phase 29 does not verify`;
- require the Phase 29 record file;
- require snippets `paper_momentum_requires_affine_stretch_under_q_delta_over_h`, `qd_next=(q_next-q_n)/h`, `No experiment.* claim is passed`, and the standard final command list.

- [ ] **Step 2: Run docs tests and verify RED**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_phase0_bootstrap
```

Expected: fails on missing Phase 29 docs/record/validator requirements.

- [ ] **Step 3: Update docs and validator**

Update `docs/reference/claim-boundaries.md`:

- Current: Phase 29 kinematic feasibility diagnostics exist for spinning-box M-ABD paper horizon.
- Verified: helper and report fields compute the orthogonal finite-difference angular-speed/momentum bounds and record the feasibility blocker.
- Non-claims: no M-ABD lane pass, no spinning-box experiment pass, no comparison pass, no projection-based solver evidence.

Create `docs/records/2026-05-17-phase29-spinning-box-kinematic-feasibility.md` with:

- status `passed`;
- config paths;
- branch/worktree/base/design/plan/implementation/docs commit placeholders;
- paper source lines;
- environment clone details;
- metrics: target angular speed `60000`, bounds `100` and `1000`, ratios `600` and `60`, status string;
- TDD RED/GREEN output snippets;
- final verification commands;
- explicit claim impact.

Update `scripts/validate_docs.py`:

- add the record path to `REQUIRED_PATHS`;
- add Phase 29 claim-boundary snippet checks;
- add `validate_phase29_record()`;
- require no `experiment.*` claim is passed;
- require spinning-box matrix still has `mabd_newton_report_incomplete` and `spinning_box_comparison_report_incomplete`;
- call `validate_phase29_record()` from `main()`;
- update final message to include `/29`.

- [ ] **Step 4: Run docs tests and validator GREEN**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_phase0_bootstrap
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
```

Expected: Phase 0-29 docs/provenance validation passes.

- [ ] **Step 5: Commit**

```bash
git add docs/reference/claim-boundaries.md docs/records/2026-05-17-phase29-spinning-box-kinematic-feasibility.md scripts/validate_docs.py tests/test_phase0_bootstrap.py
git commit -m "docs: record Phase 29 spinning-box feasibility"
```

### Task 4: Final Verification And Merge

**Files:**
- No planned source edits.

- [ ] **Step 1: Run full gates**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest newton.tests.test_mabd_phase4_solver_step
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/env/readiness_check.py
git diff --check
```

Expected: all commands exit 0; `newton.__file__` points under this worktree's `vendor/newton`.

- [ ] **Step 2: Use finishing-a-development-branch**

Fast-forward merge to `main`, rerun the final gates on `main`, push `origin main`, and remove the worktree after successful verification.

## Plan Self-Review

- Spec coverage: The tasks cover helper, report wiring, claim boundaries, record, docs validator, tests, and final gates.
- Placeholder scan: The plan contains no TBD/TODO placeholders.
- Type consistency: The helper dataclass, `to_report()`, report fields, and tests use consistent names.
- Claim boundary: No task changes `paper-claims.yaml` experiment statuses or creates an M-ABD lane pass gate.
