from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from mabd_reproduction.environment_clone import EnvironmentCloneError, build_clone_plan


ROOT = Path(__file__).resolve().parents[1]


class EnvironmentCloneTests(unittest.TestCase):
    def test_missing_target_builds_conda_clone_plan(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            reference = base / "physics-primitive-newton-py310"
            target = base / "mabd-newton-py310"
            conda = base / "miniforge3/bin/conda"
            reference.mkdir()

            plan = build_clone_plan(
                reference_env=reference,
                target_env=target,
                conda_executable=conda,
                sync_existing=False,
            )

        self.assertEqual(plan["status"], "ready_to_clone")
        self.assertEqual(
            plan["commands"],
            [[str(conda), "create", "-y", "-p", str(target), "--clone", str(reference)]],
        )
        self.assertFalse(plan["non_pollution"]["mutates_reference_environment"])
        self.assertFalse(plan["non_pollution"]["uses_reference_python"])
        self.assertFalse(plan["non_pollution"]["uses_ambient_python"])

    def test_existing_target_refuses_default_overwrite_or_sync(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            reference = base / "physics-primitive-newton-py310"
            target = base / "mabd-newton-py310"
            reference.mkdir()
            target.mkdir()

            plan = build_clone_plan(reference_env=reference, target_env=target)

        self.assertEqual(plan["status"], "target_exists")
        self.assertEqual(plan["commands"], [])
        self.assertFalse(plan["can_execute"])
        self.assertIn("--sync-existing", plan["operator_action"])

    def test_existing_target_sync_requires_explicit_flag(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            reference = base / "physics-primitive-newton-py310"
            target = base / "mabd-newton-py310"
            reference.mkdir()
            target.mkdir()

            plan = build_clone_plan(
                reference_env=reference,
                target_env=target,
                sync_existing=True,
            )

        self.assertEqual(plan["status"], "ready_to_sync_existing")
        self.assertEqual(plan["commands"], [["rsync", "-a", "--delete", f"{reference}/", f"{target}/"]])
        self.assertTrue(plan["can_execute"])

    def test_rejects_reference_target_aliasing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            reference = Path(temp_dir) / "env"
            reference.mkdir()

            with self.assertRaises(EnvironmentCloneError):
                build_clone_plan(reference_env=reference, target_env=reference)

    def test_rejects_nested_reference_and_target_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            reference = base / "reference"
            target = reference / "target"
            reference.mkdir()

            with self.assertRaises(EnvironmentCloneError):
                build_clone_plan(reference_env=reference, target_env=target)

            parent_target = base / "parent-target"
            nested_reference = parent_target / "reference"
            nested_reference.mkdir(parents=True)

            with self.assertRaises(EnvironmentCloneError):
                build_clone_plan(reference_env=nested_reference, target_env=parent_target)

    def test_cli_dry_run_emits_clone_json_without_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            reference = base / "physics-primitive-newton-py310"
            target = base / "mabd-newton-py310"
            conda = base / "miniforge3/bin/conda"
            reference.mkdir()

            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/env/clone_from_reference.py",
                    "--reference-env",
                    str(reference),
                    "--target-env",
                    str(target),
                    "--conda",
                    str(conda),
                    "--dry-run",
                ],
                cwd=ROOT,
                env={**os.environ, "PYTHONPATH": f"{ROOT / 'src'}:{ROOT / 'vendor/newton'}"},
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "ready_to_clone")
        self.assertFalse(payload["executed"])
        self.assertFalse(payload["non_pollution"]["mutates_reference_environment"])

    def test_cli_refuses_existing_target_without_sync(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            reference = base / "physics-primitive-newton-py310"
            target = base / "mabd-newton-py310"
            reference.mkdir()
            target.mkdir()

            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/env/clone_from_reference.py",
                    "--reference-env",
                    str(reference),
                    "--target-env",
                    str(target),
                    "--dry-run",
                ],
                cwd=ROOT,
                env={**os.environ, "PYTHONPATH": f"{ROOT / 'src'}:{ROOT / 'vendor/newton'}"},
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

        self.assertEqual(result.returncode, 2)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "target_exists")
        self.assertFalse(payload["can_execute"])


if __name__ == "__main__":
    unittest.main()
