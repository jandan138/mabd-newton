from __future__ import annotations

import json
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
