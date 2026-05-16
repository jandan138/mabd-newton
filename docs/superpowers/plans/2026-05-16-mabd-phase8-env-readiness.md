# Phase 8 Environment Readiness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the cloned M-ABD Newton Python environment machine-checkable without mutating the reference project environment, ambient DSW Python, or vendored Newton source.

**Architecture:** Add a small `mabd_reproduction.environment` module and `scripts/env/readiness_check.py` CLI modeled on the useful parts of `physics-primitive-agent`: explicit environment roots, import provenance, package/version checks, output writability, and JSON reports. The checker is diagnostic evidence only; it must not install packages and must not mark any method or experiment claim as passed.

**Tech Stack:** Python 3.10 standard library, PyYAML only through existing validators, vendored Newton import via `PYTHONPATH`, `unittest`, ruff, docs/provenance validator.

---

### Task 1: RED Tests For Environment Contract And Readiness Report

**Files:**
- Create: `tests/test_environment_readiness.py`

- [ ] **Step 1: Add tests for environment contract defaults**

Create `tests/test_environment_readiness.py` with:

```python
from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from mabd_reproduction.environment import (
    MABD_ENV_ROOT,
    MABD_PYTHON,
    REFERENCE_ENV_ROOT,
    EnvironmentReadinessError,
    build_readiness_report,
    write_readiness_report,
)


ROOT = Path(__file__).resolve().parents[1]


class EnvironmentReadinessTests(unittest.TestCase):
    def test_contract_uses_cloned_mabd_environment(self) -> None:
        self.assertEqual(
            MABD_ENV_ROOT,
            Path("/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310"),
        )
        self.assertEqual(MABD_PYTHON, MABD_ENV_ROOT / "bin/python")
        self.assertEqual(
            REFERENCE_ENV_ROOT,
            Path("/cpfs/user/zhuzihou/conda-managed/envs/physics-primitive-newton-py310"),
        )
        self.assertNotEqual(MABD_ENV_ROOT, REFERENCE_ENV_ROOT)

    def test_readiness_report_proves_imports_and_non_pollution(self) -> None:
        report = build_readiness_report(
            project_root=ROOT,
            env_root=MABD_ENV_ROOT,
            reference_env_root=REFERENCE_ENV_ROOT,
            python_executable=MABD_PYTHON,
            required_packages=("yaml", "warp"),
        )

        self.assertEqual(report["status"], "smoke_passed")
        self.assertEqual(report["environment"]["role"], "mabd-newton-clone")
        self.assertTrue(report["environment"]["python"].endswith("/bin/python"))
        self.assertEqual(report["reference_environment"]["role"], "reference-source")
        self.assertFalse(report["non_pollution"]["uses_ambient_python"])
        self.assertFalse(report["non_pollution"]["uses_reference_python"])
        self.assertIn("vendor/newton/newton/__init__.py", report["imports"]["newton"]["path"])
        self.assertEqual(report["packages"]["yaml"]["status"], "present")
        self.assertEqual(report["packages"]["warp"]["status"], "present")

    def test_write_readiness_report_creates_parent_directory(self) -> None:
        report = {"status": "smoke_passed", "value": 1}
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "nested/readiness.json"

            write_readiness_report(report, output)

            self.assertTrue(output.exists())
            self.assertEqual(json.loads(output.read_text(encoding="utf-8")), report)

    def test_readiness_rejects_ambient_python_path(self) -> None:
        ambient = Path("/usr/bin/python3")
        if not ambient.exists():
            self.skipTest("ambient python path is not present on this machine")

        with self.assertRaises(EnvironmentReadinessError):
            build_readiness_report(
                project_root=ROOT,
                env_root=MABD_ENV_ROOT,
                reference_env_root=REFERENCE_ENV_ROOT,
                python_executable=ambient,
                required_packages=("yaml",),
            )

    def test_readiness_rejects_reference_python_path(self) -> None:
        reference_python = REFERENCE_ENV_ROOT / "bin/python"
        if not reference_python.exists():
            self.skipTest("reference python path is not present on this machine")

        with self.assertRaises(EnvironmentReadinessError):
            build_readiness_report(
                project_root=ROOT,
                env_root=MABD_ENV_ROOT,
                reference_env_root=REFERENCE_ENV_ROOT,
                python_executable=reference_python,
                required_packages=("yaml",),
            )


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify RED**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_environment_readiness
```

Expected: fail because `mabd_reproduction.environment` is missing.

### Task 2: Implement Pure Environment Readiness Helpers

**Files:**
- Create: `src/mabd_reproduction/environment.py`
- Modify: `src/mabd_reproduction/__init__.py`

- [ ] **Step 1: Add constants and dataclass-free JSON helpers**

Create `src/mabd_reproduction/environment.py` with public constants:

```python
MABD_ENV_ROOT = Path("/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310")
MABD_PYTHON = MABD_ENV_ROOT / "bin/python"
REFERENCE_ENV_ROOT = Path("/cpfs/user/zhuzihou/conda-managed/envs/physics-primitive-newton-py310")
REFERENCE_PYTHON = REFERENCE_ENV_ROOT / "bin/python"
AMBIENT_PYTHON_PREFIXES = (Path("/usr/bin"), Path("/isaac-sim"))
```

Add `EnvironmentReadinessError(RuntimeError)`.

- [ ] **Step 2: Add subprocess probes**

Implement private helpers:

```python
def _run_probe(python_executable: Path, code: str, *, project_root: Path) -> dict[str, object]:
    ...

def _probe_module(python_executable: Path, module_name: str, *, project_root: Path) -> dict[str, object]:
    ...

def _probe_package_version(python_executable: Path, module_name: str, *, project_root: Path) -> dict[str, object]:
    ...
```

The subprocess environment must set `PYTHONPATH` to `<project_root>/src:<project_root>/vendor/newton`. Do not call pip, conda, or install commands.

- [ ] **Step 3: Add `build_readiness_report`**

Implement:

```python
def build_readiness_report(
    *,
    project_root: Path = ROOT,
    env_root: Path = MABD_ENV_ROOT,
    reference_env_root: Path = REFERENCE_ENV_ROOT,
    python_executable: Path = MABD_PYTHON,
    required_packages: Sequence[str] = ("yaml", "warp"),
) -> dict[str, object]:
    ...
```

Required behavior:

- reject a missing `python_executable`
- reject a `python_executable` outside `env_root`
- reject `python_executable == reference_env_root / "bin/python"`
- reject known ambient prefixes such as `/usr/bin`
- probe `newton` and require its path to contain `vendor/newton/newton/__init__.py`
- probe each `required_packages` and mark `present` with version/path or `missing`
- compute final status `smoke_passed` only when every required package is present and Newton import is vendored
- include `environment`, `reference_environment`, `non_pollution`, `imports`, `packages`, and `commands` mappings

- [ ] **Step 4: Add report writer and exports**

Implement:

```python
def write_readiness_report(report: Mapping[str, object], output_path: Path) -> None:
    ...
```

Export `environment` from `src/mabd_reproduction/__init__.py` only if the existing package pattern needs it.

- [ ] **Step 5: Run focused GREEN**

Run:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_environment_readiness
```

Expected: pass.

### Task 3: Add Readiness CLI And Documentation Gate

**Files:**
- Create: `scripts/env/readiness_check.py`
- Modify: `docs/operations/environment.md`
- Modify: `docs/reference/claim-boundaries.md`
- Modify: `scripts/validate_docs.py`
- Modify: `tests/test_phase0_bootstrap.py`
- Create: `docs/records/2026-05-16-phase8-environment-readiness.md`

- [ ] **Step 1: Add CLI**

Create `scripts/env/readiness_check.py`:

```python
#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from mabd_reproduction.environment import (
    EnvironmentReadinessError,
    build_readiness_report,
    write_readiness_report,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check the isolated M-ABD Newton environment.")
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        report = build_readiness_report()
    except EnvironmentReadinessError as exc:
        report = {"status": "configuration_error", "failure_reason": str(exc)}
        print(json.dumps(report, indent=2, sort_keys=True))
        if args.output is not None:
            write_readiness_report(report, args.output)
        return 2
    print(json.dumps(report, indent=2, sort_keys=True))
    if args.output is not None:
        write_readiness_report(report, args.output)
    return 0 if report["status"] == "smoke_passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Update environment docs**

Add a "Machine-Checkable Readiness" section showing:

```bash
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python \
  scripts/env/readiness_check.py --output reports/generated/environment-readiness/local/readiness.json
```

State that generated readiness JSON is not committed and that `smoke_passed` is environment evidence only.

- [ ] **Step 3: Update boundaries**

Add Phase 8 current/verified entries:

- verifies the cloned environment contract, vendored Newton import, required packages, and non-pollution guards through readiness checks
- does not verify solver behavior, scene dynamics, timing, baselines, or paper experiments

- [ ] **Step 4: Update validator and bootstrap tests**

Require:

- `scripts/env/readiness_check.py`
- `tests/test_environment_readiness.py`
- Phase 8 record
- environment docs mention `readiness_check.py`, `smoke_passed`, `reports/generated/environment-readiness/local/readiness.json`
- claim boundaries contain Phase 8 boundary text
- validator output becomes `Phase 0/1/2/3/4/5/6/7/8 docs/provenance validation passed`

- [ ] **Step 5: Create Phase 8 record**

Record:

- base commit `e13529d`
- reference env path `/cpfs/user/zhuzihou/conda-managed/envs/physics-primitive-newton-py310`
- cloned env path `/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310`
- the readiness command and focused tests
- status is environment `smoke_passed` only, no method or experiment claim passed
- implementation commit marker `IMPLEMENTATION_COMMIT_PENDING`

### Task 4: Verification, Review, Commit, Merge

**Files:**
- All Phase 8 files.

- [ ] **Step 1: Run full Phase 8 verification**

Run:

```bash
/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m ruff check src/mabd_reproduction/environment.py scripts/env/readiness_check.py tests/test_environment_readiness.py tests/test_phase0_bootstrap.py scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/env/readiness_check.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python scripts/validate_docs.py
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest tests.test_environment_readiness tests.test_phase0_bootstrap
PYTHONPATH=src:vendor/newton /cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310/bin/python -m unittest discover -s tests
git diff --check
```

Expected: all exit 0.

- [ ] **Step 2: Commit implementation**

Run:

```bash
git add docs/operations/environment.md docs/records/2026-05-16-phase8-environment-readiness.md docs/reference/claim-boundaries.md docs/superpowers/plans/2026-05-16-mabd-phase8-env-readiness.md scripts/env/readiness_check.py scripts/validate_docs.py src/mabd_reproduction/environment.py tests/test_environment_readiness.py tests/test_phase0_bootstrap.py
git commit -m "feat: add Phase 8 environment readiness"
```

- [ ] **Step 3: Backfill record commit hash**

Replace `IMPLEMENTATION_COMMIT_PENDING` with the implementation commit hash, rerun docs validation, and commit:

```bash
git add docs/records/2026-05-16-phase8-environment-readiness.md
git commit -m "docs: record Phase 8 implementation commit"
```

- [ ] **Step 4: Review and merge**

Request independent review focused on false-positive readiness, accidental environment mutation, and claim boundary drift. Fix issues, rerun Step 1, fast-forward merge to `main`, verify again on `main`, push to `origin/main`, then remove the worktree and branch.
