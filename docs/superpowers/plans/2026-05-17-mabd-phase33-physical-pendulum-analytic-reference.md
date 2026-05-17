# Phase 33 Physical Pendulum Analytic Reference Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a bounded analytic-reference lane for the paper physical-pendulum scene.

**Architecture:** Add a per-scene config loader, a small SciPy-backed analytic reference helper, and a report/runner lane that produces incomplete machine-checkable evidence. Keep the experiment claim intended and the geometry/dynamics blockers explicit.

**Tech Stack:** Python 3.10, NumPy, SciPy, PyYAML, `unittest`, existing `mabd-newton-py310` environment.

---

### Task 1: Add Failing Tests

**Files:**
- Create: `tests/test_physical_pendulum_reference.py`
- Modify: `tests/test_experiment_run_configs.py`
- Modify: `tests/test_experiment_runner.py`

- [ ] **Step 1: Add analytic-reference tests**

Test `physical_pendulum_angle_reference` for:

```python
kappa = np.sqrt(0.5)
omega = 2.0
K = scipy.special.ellipk(kappa * kappa)
times = np.array([0.0, K / omega, 2.0 * K / omega])
angles = physical_pendulum_angle_reference(times, kappa=kappa, omega_lin=omega)
np.testing.assert_allclose(angles, [0.0, np.pi / 2.0, np.pi], atol=1.0e-12)
```

Also test invalid `kappa`, `omega_lin`, and negative times.

- [ ] **Step 2: Add config tests**

Load `configs/experiments/single_body_physical_pendulum.yaml` and assert:

```python
config.claim_id == "experiment.single_body.physical_pendulum"
config.scene_id == "single_body_physical_pendulum"
config.baseline_lane == "analytic_reference"
config.report_status == EvidenceStatus.INCOMPLETE
config.asset_ids == ("physical_pendulum_procedural",)
config.reference.kappa == np.sqrt(0.5)
config.reference.release_angle_rad == np.pi / 2.0
config.reference.initial_angle_rad == 0.0
```

Validate the config against `paper_experiment_matrix.yaml`, and reject a config
whose report status is changed to `passed`.

- [ ] **Step 3: Add runner/CLI tests**

Test `run_physical_pendulum_analytic_reference(...)` writes a full-schema report
with `status=incomplete`, `baseline_lane=analytic_reference`,
`solver_mode=analytic_elliptic_reference`, and finite angle samples. Add a CLI
test for:

```bash
scripts/run_experiment.py --lane analytic_reference --config configs/experiments/single_body_physical_pendulum.yaml --output <tmp>/pendulum.json
```

- [ ] **Step 4: Verify RED**

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_physical_pendulum_reference tests.test_experiment_run_configs tests.test_experiment_runner
```

Expected: fail because the new config, loader, helper, runner, and CLI lane do
not exist yet.

### Task 2: Implement Config And Analytic Helper

**Files:**
- Create: `configs/experiments/single_body_physical_pendulum.yaml`
- Modify: `src/mabd_reproduction/experiment_configs.py`
- Create: `src/mabd_reproduction/physical_pendulum_reference.py`

- [ ] **Step 1: Add config dataclasses and loader**

Add `PhysicalPendulumReferenceConfig` and `PhysicalPendulumRunConfig` with
strict numeric validation. Add `load_physical_pendulum_config(path)`.

- [ ] **Step 2: Add matrix validation**

Add `validate_physical_pendulum_config_against_matrix(config, matrix)` mirroring
the spinning-box checks for claim id, scene id, source lines, paper values,
required lanes, asset ids, and output report.

- [ ] **Step 3: Add analytic reference helper**

Implement:

```python
def physical_pendulum_angle_reference(times, *, kappa: float, omega_lin: float) -> np.ndarray:
    parameter = kappa * kappa
    complete = special.ellipk(parameter)
    sn, _cn, _dn, _ph = special.ellipj(complete - omega_lin * time_arr, parameter)
    return np.pi / 2.0 - 2.0 * np.arcsin(kappa * sn)
```

- [ ] **Step 4: Verify GREEN for helper/config**

Run the RED command. Expected: helper/config tests pass; runner tests still fail
until Task 3.

### Task 3: Implement Report And Runner

**Files:**
- Create: `src/mabd_reproduction/physical_pendulum_reports.py`
- Modify: `src/mabd_reproduction/experiment_runner.py`
- Modify: `scripts/run_experiment.py`

- [ ] **Step 1: Add report writer**

Create `write_physical_pendulum_analytic_reference_report(...)` that samples the
analytic reference, computes finite summary fields, and writes a `ClaimReport`
with status `EvidenceStatus.INCOMPLETE`.

- [ ] **Step 2: Add runner function**

Add `run_physical_pendulum_analytic_reference(...)` with explicit output path
or safe output-root handling.

- [ ] **Step 3: Add CLI lane**

Extend `--lane` choices with `analytic_reference` and dispatch to the physical
pendulum runner only when the loaded config targets
`experiment.single_body.physical_pendulum`.

- [ ] **Step 4: Verify GREEN**

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_physical_pendulum_reference tests.test_experiment_run_configs tests.test_experiment_runner
```

Expected: all focused tests pass.

### Task 4: Update Claims, Records, And Validators

**Files:**
- Modify: `docs/reference/claim-boundaries.md`
- Create: `docs/records/2026-05-17-phase33-physical-pendulum-analytic-reference.md`
- Modify: `scripts/validate_docs.py`
- Modify: `tests/test_phase0_bootstrap.py`

- [ ] **Step 1: Add Phase33 boundary bullets**

Record that Phase33 verifies only the physical-pendulum analytic-reference
formula/config/report lane and does not verify M-ABD/RBD dynamics or pass the
experiment claim.

- [ ] **Step 2: Add dated record**

Record source lines, environment isolation, tests, runner lane, and claim impact.

- [ ] **Step 3: Extend validators**

Require the Phase33 spec, plan, record, config, boundary snippets, and no passed
`experiment.*` claims.

### Task 5: Verify, Review, Merge, Push

**Files:** all Phase33 files.

- [ ] **Step 1: Run focused gates**

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_physical_pendulum_reference tests.test_experiment_run_configs tests.test_experiment_runner tests.test_phase0_bootstrap
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
```

- [ ] **Step 2: Run full gates**

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/env/readiness_check.py
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"
git diff --check
```

- [ ] **Step 3: Request review, commit, merge, and push**

Request solver/report and docs/provenance review, fix any Important or Critical
feedback, commit, fast-forward merge to `main`, rerun main gates, push
`origin/main`, and remove the temporary worktree.
