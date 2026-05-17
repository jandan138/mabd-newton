# Phase 18 Spinning-Box MABD Physical Mass Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the spinning-box M-ABD lane's synthetic identity mass diagonal with the paper cube's physical affine mass diagonal and record bounded energy diagnostics.

**Architecture:** The physical mass derivation lives beside the Phase 17 paper-momentum helpers in `spinning_box_physics.py`. The YAML config stores the derived 12-vector so experiment reports remain manifest-driven, while tests and docs validation ensure the manifest matches the paper-derived helper.

**Tech Stack:** Python 3.10, NumPy, PyYAML, `unittest`, vendored Newton M-ABD affine helpers, Markdown/YAML provenance records.

---

## File Structure

- Modify `src/mabd_reproduction/spinning_box_physics.py`: add a paper-derived `spinning_box_mabd_mass_diagonal` helper.
- Modify `configs/experiments/single_body_spinning_box.yaml`: replace identity `mass_diagonal` with nine `1/1200` affine entries and three `1.0` translation entries.
- Modify `src/mabd_reproduction/single_body_reports.py`: emit physical mass diagonal and initial/final/relative kinetic energy diagnostics.
- Modify `tests/test_experiment_run_configs.py`: assert the config mass diagonal and physical energy match paper-derived values.
- Modify `tests/test_single_body_report_lane.py`: assert generated M-ABD reports expose physical mass/energy diagnostics.
- Modify `tests/test_phase0_bootstrap.py`: assert Phase 18 boundary and record snippets are present.
- Modify `docs/reference/claim-boundaries.md`: add bounded Phase 18 evidence and non-claims.
- Modify `scripts/validate_docs.py`: require Phase 18 record, boundary language, and config physical mass diagonal.
- Create `docs/records/2026-05-17-phase18-spinning-box-mabd-physical-mass.md`: dated evidence record.

---

### Task 1: Plan And Spec Commit

**Files:**
- Create: `docs/superpowers/specs/2026-05-17-phase18-spinning-box-mabd-physical-mass-design.md`
- Create: `docs/superpowers/plans/2026-05-17-mabd-phase18-spinning-box-mabd-physical-mass.md`

- [ ] **Step 1: Check plan/spec files exist**

Run:

```bash
test -f docs/superpowers/specs/2026-05-17-phase18-spinning-box-mabd-physical-mass-design.md
test -f docs/superpowers/plans/2026-05-17-mabd-phase18-spinning-box-mabd-physical-mass.md
```

Expected: both commands exit `0`.

- [ ] **Step 2: Commit docs-only planning artifacts**

Run:

```bash
git add docs/superpowers/specs/2026-05-17-phase18-spinning-box-mabd-physical-mass-design.md docs/superpowers/plans/2026-05-17-mabd-phase18-spinning-box-mabd-physical-mass.md
git commit -m "docs: plan Phase 18 spinning-box physical mass"
```

Expected: commit succeeds and touches only the two planning files.

---

### Task 2: Add Paper-Derived Mass-Diagonal Tests

**Files:**
- Modify: `tests/test_experiment_run_configs.py`
- Modify: `tests/test_single_body_report_lane.py`

- [ ] **Step 1: Add failing config assertions**

In `tests/test_experiment_run_configs.py`, import `spinning_box_mabd_mass_diagonal` and add these assertions in `test_spinning_box_config_is_machine_checkable` after `properties = spinning_box_physical_properties(config)`:

```python
        expected_mass_diagonal = spinning_box_mabd_mass_diagonal(config)
        np.testing.assert_allclose(
            expected_mass_diagonal,
            [1.0 / 1200.0] * 9 + [1.0, 1.0, 1.0],
            rtol=0.0,
            atol=1.0e-15,
        )
        np.testing.assert_allclose(config.mass_diagonal, expected_mass_diagonal, atol=1.0e-15)
        self.assertAlmostEqual(float(0.5 * config.initial_qd @ np.diag(config.mass_diagonal) @ config.initial_qd), 3005000.0)
```

Expected initial failure before implementation: import fails because `spinning_box_mabd_mass_diagonal` does not exist, or config comparison fails because the YAML still uses identity mass.

- [ ] **Step 2: Add failing report assertions**

In `tests/test_single_body_report_lane.py`, add these assertions to `test_spinning_box_report_uses_run_config` after the existing angular momentum error assertion:

```python
        self.assertEqual(loaded.observed["mass_diagonal_source"], "paper_uniform_centered_cube_continuous")
        self.assertEqual(len(loaded.observed["mabd_mass_diagonal"]), 12)
        self.assertAlmostEqual(loaded.observed["mass_kg"], 1.0)
        self.assertAlmostEqual(loaded.observed["initial_energy_j"], 3005000.0)
        self.assertAlmostEqual(loaded.observed["final_energy_j"], 3005000.0)
        self.assertLessEqual(loaded.observed["relative_energy_drift"], 1.0e-15)
```

Expected initial failure before implementation: report observed keys are missing.

- [ ] **Step 3: Run focused tests and verify RED**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_run_configs tests.test_single_body_report_lane
```

Expected: FAIL for the missing helper and/or missing report diagnostics.

---

### Task 3: Implement Physical Mass Helper And Report Diagnostics

**Files:**
- Modify: `src/mabd_reproduction/spinning_box_physics.py`
- Modify: `src/mabd_reproduction/single_body_reports.py`
- Modify: `configs/experiments/single_body_spinning_box.yaml`

- [ ] **Step 1: Add `spinning_box_mabd_mass_diagonal`**

In `src/mabd_reproduction/spinning_box_physics.py`, add:

```python
def spinning_box_mabd_mass_diagonal(config: SpinningBoxRunConfig) -> np.ndarray:
    properties = spinning_box_physical_properties(config)
    affine_second_moment = properties.mass_kg * properties.cube_size_m**2 / 12.0
    return np.concatenate(
        [
            np.full(9, affine_second_moment, dtype=float),
            np.full(3, properties.mass_kg, dtype=float),
        ]
    )
```

Also export it in `__all__`.

- [ ] **Step 2: Update the YAML mass diagonal**

In `configs/experiments/single_body_spinning_box.yaml`, set:

```yaml
  mass_diagonal:
    - 0.0008333333333333334
    - 0.0008333333333333334
    - 0.0008333333333333334
    - 0.0008333333333333334
    - 0.0008333333333333334
    - 0.0008333333333333334
    - 0.0008333333333333334
    - 0.0008333333333333334
    - 0.0008333333333333334
    - 1.0
    - 1.0
    - 1.0
```

- [ ] **Step 3: Emit mass and energy report diagnostics**

In `src/mabd_reproduction/single_body_reports.py`, import `spinning_box_mabd_mass_diagonal` and include these observed fields when `config is not None`:

```python
        properties = spinning_box_physical_properties(config)
        observed.update(
            {
                "mass_kg": properties.mass_kg,
                "mabd_mass_diagonal": mass_matrix.diagonal().tolist(),
                "mass_diagonal_source": "paper_uniform_centered_cube_continuous",
                "initial_energy_j": initial_energy,
                "final_energy_j": final_energy,
                "relative_energy_drift": 0.0
                if initial_energy == 0.0
                else energy_drift / abs(initial_energy),
            }
        )
```

Use a local `final_energy = _kinetic_energy(qd, mass_matrix)` to avoid recomputing with inconsistent names. Keep the existing absolute `energy_drift`.

- [ ] **Step 4: Run focused tests and verify GREEN**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_experiment_run_configs tests.test_single_body_report_lane
```

Expected: both focused test modules pass.

- [ ] **Step 5: Commit implementation**

Run:

```bash
git add src/mabd_reproduction/spinning_box_physics.py src/mabd_reproduction/single_body_reports.py configs/experiments/single_body_spinning_box.yaml tests/test_experiment_run_configs.py tests/test_single_body_report_lane.py
git commit -m "feat: use paper physical mass for spinning-box MABD lane"
```

Expected: commit succeeds.

---

### Task 4: Add Phase 18 Provenance Gates

**Files:**
- Modify: `docs/reference/claim-boundaries.md`
- Modify: `scripts/validate_docs.py`
- Modify: `tests/test_phase0_bootstrap.py`
- Create: `docs/records/2026-05-17-phase18-spinning-box-mabd-physical-mass.md`

- [ ] **Step 1: Add failing docs tests**

In `tests/test_phase0_bootstrap.py`, add tests requiring:

```python
    def test_phase18_spinning_box_mabd_physical_mass_is_bounded(self) -> None:
        text = (ROOT / "docs/reference/claim-boundaries.md").read_text()
        normalized_text = " ".join(text.split())

        self.assertIn("Phase 18 verifies physical affine mass-diagonal reporting", text)
        self.assertIn("paper uniform centered cube", normalized_text)
        self.assertIn("m*s^2/12", normalized_text)
        self.assertIn("relative_energy_drift", text)
        self.assertIn("Phase 18 does not verify the paper spinning-box experiment", text)
        self.assertIn("paper-faithful implicit RBD baseline", text)
        self.assertIn("any passed `experiment.*` claim", text)

    def test_phase18_record_has_required_evidence_fields(self) -> None:
        text = (
            ROOT / "docs/records/2026-05-17-phase18-spinning-box-mabd-physical-mass.md"
        ).read_text()

        for snippet in (
            "## Status\n\npassed",
            "## Config Path",
            "configs/experiments/single_body_spinning_box.yaml",
            "## Repository",
            "plan commit:",
            "implementation commit:",
            "## Vendored Newton",
            "96713fa965463b69c229a4d30582c733ff3526bb",
            "## Paper Source",
            "PDF SHA256:",
            "TeX source SHA256:",
            "experiment.tex:40-55",
            "## Environment",
            "mabd-newton-py310",
            "physics-primitive-newton-py310",
            "## Metrics And Thresholds",
            "mass_diagonal = [1/1200] * 9 + [1.0] * 3",
            "initial_energy_j = 3005000.0",
            "relative_energy_drift",
            "## Artifacts",
            "`spinning_box_mabd_mass_diagonal`",
            "generated reports: not committed",
            "No `experiment.*` claim is passed in this phase.",
        ):
            self.assertIn(snippet, text)
```

Expected initial failure before docs implementation: boundary snippet and record are missing.

- [ ] **Step 2: Run docs tests and verify RED**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_phase0_bootstrap
```

Expected: FAIL because Phase 18 docs and record are not present yet.

- [ ] **Step 3: Update docs validator**

In `scripts/validate_docs.py`:

- update the docstring and final print string to include `/18`
- add `docs/records/2026-05-17-phase18-spinning-box-mabd-physical-mass.md` to `REQUIRED_PATHS`
- add Phase 18 boundary snippet checks to `validate_claim_boundaries`
- add `validate_phase18_record()`
- call `validate_phase18_record()` from `main()`
- in `validate_phase13_config`, assert `config.mass_diagonal` matches `spinning_box_mabd_mass_diagonal(config)`

Expected validator failure before record text is added: Phase 18 record missing required fields.

- [ ] **Step 4: Add boundary and record text**

Update `docs/reference/claim-boundaries.md` with Phase 18 current/verified/non-claim bullets. Create `docs/records/2026-05-17-phase18-spinning-box-mabd-physical-mass.md` with sections matching previous records and including the plan/implementation commit hashes.

- [ ] **Step 5: Run docs tests and validator**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_phase0_bootstrap
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
```

Expected: both pass.

- [ ] **Step 6: Commit docs/provenance**

Run:

```bash
git add docs/reference/claim-boundaries.md docs/records/2026-05-17-phase18-spinning-box-mabd-physical-mass.md scripts/validate_docs.py tests/test_phase0_bootstrap.py
git commit -m "docs: record Phase 18 spinning-box physical mass evidence"
```

Expected: commit succeeds.

---

### Task 5: Full Verification, Review, Merge, Push

**Files:**
- No planned file edits unless review finds a concrete issue.

- [ ] **Step 1: Run full gates**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check .
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
PYTHONPATH=vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -c "import newton; print(newton.__file__)"
git diff --check
```

Expected: ruff passes, validator prints Phase 0 through Phase 18 passed, unittest reports all tests OK, import resolves to the worktree `vendor/newton`, and `git diff --check` has no output.

- [ ] **Step 2: Request multi-angle review**

Dispatch two reviewers:

- claim/spec reviewer: verify Phase 18 does not overclaim and docs/validator match AGENTS.md boundaries
- code/physics reviewer: verify mass diagonal derivation, q packing order, report metrics, and tests

Expected: no high-severity findings, or fixes are committed and gates rerun.

- [ ] **Step 3: Merge and push**

Run:

```bash
git checkout main
git merge --ff-only phase18-spinning-box-mabd-physical-mass
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
git diff --check
git push origin main
```

Expected: merge is fast-forward, main gates pass, and push succeeds.
