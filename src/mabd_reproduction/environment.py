"""Machine-checkable readiness contract for the isolated M-ABD environment."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
MABD_ENV_ROOT = Path("/cpfs/user/zhuzihou/conda-managed/envs/mabd-newton-py310")
MABD_PYTHON = MABD_ENV_ROOT / "bin/python"
REFERENCE_ENV_ROOT = Path("/cpfs/user/zhuzihou/conda-managed/envs/physics-primitive-newton-py310")
REFERENCE_PYTHON = REFERENCE_ENV_ROOT / "bin/python"
AMBIENT_PYTHON_PREFIXES = (Path("/usr/bin"), Path("/isaac-sim"))


class EnvironmentReadinessError(RuntimeError):
    """Raised when the configured readiness interpreter violates isolation rules."""


def _as_resolved(path: Path) -> Path:
    return path.expanduser().resolve(strict=False)


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _json_from_stdout(stdout: str) -> dict[str, Any]:
    for line in reversed(stdout.splitlines()):
        line = line.strip()
        if line.startswith("{") and line.endswith("}"):
            data = json.loads(line)
            if isinstance(data, dict):
                return data
    return {"status": "probe_error", "failure_reason": "probe did not emit JSON"}


def _probe_env(project_root: Path) -> dict[str, str]:
    return {
        **os.environ,
        "PYTHONPATH": f"{project_root / 'src'}:{project_root / 'vendor/newton'}",
    }


def _run_probe(python_executable: Path, code: str, *, project_root: Path) -> dict[str, Any]:
    result = subprocess.run(
        [str(python_executable), "-c", code],
        cwd=project_root,
        env=_probe_env(project_root),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        return {
            "status": "probe_error",
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
    data = _json_from_stdout(result.stdout)
    data.setdefault("stderr", result.stderr)
    return data


def _probe_module(python_executable: Path, module_name: str, *, project_root: Path) -> dict[str, Any]:
    code = f"""
import importlib
import json

module_name = {module_name!r}
try:
    module = importlib.import_module(module_name)
except Exception as exc:
    print(json.dumps({{"status": "missing", "module": module_name, "error": str(exc)}}, sort_keys=True))
else:
    print(json.dumps({{
        "status": "present",
        "module": module_name,
        "path": str(getattr(module, "__file__", "")),
        "version": str(getattr(module, "__version__", "")),
    }}, sort_keys=True))
"""
    return _run_probe(python_executable, code, project_root=project_root)


def _probe_package_version(python_executable: Path, module_name: str, *, project_root: Path) -> dict[str, Any]:
    return _probe_module(python_executable, module_name, project_root=project_root)


def _validate_python_choice(
    *,
    env_root: Path,
    reference_env_root: Path,
    python_executable: Path,
    current_python: Path,
) -> tuple[Path, Path, Path, Path]:
    env_root_resolved = _as_resolved(env_root)
    reference_root_resolved = _as_resolved(reference_env_root)
    python_resolved = _as_resolved(python_executable)
    current_python_resolved = _as_resolved(current_python)

    if not python_executable.exists():
        raise EnvironmentReadinessError(f"python executable does not exist: {python_executable}")
    if not _is_relative_to(python_resolved, env_root_resolved):
        raise EnvironmentReadinessError(
            f"python executable must live under M-ABD env root {env_root}: {python_executable}"
        )
    if _is_relative_to(python_resolved, reference_root_resolved):
        raise EnvironmentReadinessError(
            f"python executable must not use reference env root {reference_env_root}: {python_executable}"
        )
    for prefix in AMBIENT_PYTHON_PREFIXES:
        if _is_relative_to(python_resolved, _as_resolved(prefix)):
            raise EnvironmentReadinessError(
                f"python executable must not use ambient Python prefix {prefix}: {python_executable}"
            )
    if not current_python.exists():
        raise EnvironmentReadinessError(f"current Python executable does not exist: {current_python}")
    if not _is_relative_to(current_python_resolved, env_root_resolved):
        raise EnvironmentReadinessError(
            f"current Python must live under M-ABD env root {env_root}: {current_python}"
        )
    if _is_relative_to(current_python_resolved, reference_root_resolved):
        raise EnvironmentReadinessError(
            f"current Python must not use reference env root {reference_env_root}: {current_python}"
        )
    for prefix in AMBIENT_PYTHON_PREFIXES:
        if _is_relative_to(current_python_resolved, _as_resolved(prefix)):
            raise EnvironmentReadinessError(
                f"current Python must not use ambient Python prefix {prefix}: {current_python}"
            )
    if current_python_resolved != python_resolved:
        raise EnvironmentReadinessError(
            f"current Python must match probe Python: {current_python} != {python_executable}"
        )
    return env_root_resolved, reference_root_resolved, python_resolved, current_python_resolved


def _classify_package_path(package: Mapping[str, Any], *, env_root: Path, project_root: Path) -> dict[str, Any]:
    classified = dict(package)
    if package.get("status") != "present":
        classified["from_environment"] = False
        return classified

    package_path = _as_resolved(Path(str(package.get("path", ""))))
    from_environment = _is_relative_to(package_path, env_root)
    classified["from_environment"] = from_environment
    if from_environment:
        return classified

    if _is_relative_to(package_path, project_root):
        classified["status"] = "shadowed"
    else:
        classified["status"] = "outside_environment"
    return classified


def build_readiness_report(
    *,
    project_root: Path = ROOT,
    env_root: Path = MABD_ENV_ROOT,
    reference_env_root: Path = REFERENCE_ENV_ROOT,
    python_executable: Path = MABD_PYTHON,
    current_python: Path | None = None,
    required_packages: Sequence[str] = ("yaml", "warp"),
) -> dict[str, Any]:
    """Build a diagnostic readiness report without installing or mutating dependencies."""

    project_root = _as_resolved(project_root)
    current_python = Path(sys.executable) if current_python is None else current_python
    env_root_resolved, reference_root_resolved, python_resolved, current_python_resolved = _validate_python_choice(
        env_root=env_root,
        reference_env_root=reference_env_root,
        python_executable=python_executable,
        current_python=current_python,
    )

    newton_probe = _probe_module(python_executable, "newton", project_root=project_root)
    packages = {
        module_name: _classify_package_path(
            _probe_package_version(python_executable, module_name, project_root=project_root),
            env_root=env_root_resolved,
            project_root=project_root,
        )
        for module_name in required_packages
    }
    newton_path = str(newton_probe.get("path", "")).replace("\\", "/")
    vendored_newton = "vendor/newton/newton/__init__.py" in newton_path
    packages_present = all(
        package.get("status") == "present" and package.get("from_environment") is True
        for package in packages.values()
    )
    status = "smoke_passed" if vendored_newton and packages_present else "dependency_gap"

    return {
        "status": status,
        "environment": {
            "role": "mabd-newton-clone",
            "root": str(env_root),
            "root_realpath": str(env_root_resolved),
            "python": str(python_executable),
            "python_realpath": str(python_resolved),
            "current_python": str(current_python),
            "current_python_realpath": str(current_python_resolved),
        },
        "reference_environment": {
            "role": "reference-source",
            "root": str(reference_env_root),
            "root_realpath": str(reference_root_resolved),
            "python": str(reference_env_root / "bin/python"),
        },
        "non_pollution": {
            "uses_ambient_python": any(
                _is_relative_to(python_resolved, _as_resolved(prefix)) for prefix in AMBIENT_PYTHON_PREFIXES
            ),
            "uses_ambient_current_python": any(
                _is_relative_to(current_python_resolved, _as_resolved(prefix)) for prefix in AMBIENT_PYTHON_PREFIXES
            ),
            "uses_reference_python": _is_relative_to(python_resolved, reference_root_resolved),
            "uses_reference_current_python": _is_relative_to(current_python_resolved, reference_root_resolved),
            "installs_packages": False,
            "mutates_reference_environment": False,
        },
        "imports": {
            "newton": {
                **newton_probe,
                "vendored": vendored_newton,
            }
        },
        "packages": packages,
        "commands": {
            "readiness": (
                "PYTHONPATH=src:vendor/newton "
                f"{python_executable} scripts/env/readiness_check.py"
            ),
            "docs": (
                "PYTHONPATH=src:vendor/newton "
                f"{python_executable} scripts/validate_docs.py"
            ),
            "tests": (
                "PYTHONPATH=src:vendor/newton "
                f"{python_executable} -m unittest discover -s tests"
            ),
        },
    }


def write_readiness_report(report: Mapping[str, object], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


__all__ = [
    "AMBIENT_PYTHON_PREFIXES",
    "MABD_ENV_ROOT",
    "MABD_PYTHON",
    "REFERENCE_ENV_ROOT",
    "REFERENCE_PYTHON",
    "EnvironmentReadinessError",
    "build_readiness_report",
    "write_readiness_report",
]
