#!/usr/bin/env python3
"""Clone or refresh the isolated M-ABD Newton environment."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from mabd_reproduction.environment import MABD_ENV_ROOT, REFERENCE_ENV_ROOT
from mabd_reproduction.environment_clone import (
    DEFAULT_CONDA,
    EnvironmentCloneError,
    build_clone_plan,
    execute_clone_plan,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Clone the project M-ABD Newton environment.")
    parser.add_argument("--reference-env", type=Path, default=REFERENCE_ENV_ROOT)
    parser.add_argument("--target-env", type=Path, default=MABD_ENV_ROOT)
    parser.add_argument("--conda", type=Path, default=DEFAULT_CONDA)
    parser.add_argument("--sync-existing", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--output", type=Path, help="Optional JSON plan/report path.")
    return parser.parse_args()


def _write_json(payload: dict[str, object], output_path: Path | None) -> None:
    if output_path is None:
        return
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    try:
        plan = build_clone_plan(
            reference_env=args.reference_env,
            target_env=args.target_env,
            conda_executable=args.conda,
            sync_existing=args.sync_existing,
        )
    except EnvironmentCloneError as exc:
        payload = {"status": "configuration_error", "failure_reason": str(exc), "executed": False}
        print(json.dumps(payload, indent=2, sort_keys=True))
        _write_json(payload, args.output)
        return 2

    if args.dry_run:
        payload = {**plan, "executed": False}
    else:
        payload = execute_clone_plan(plan)

    print(json.dumps(payload, indent=2, sort_keys=True))
    _write_json(payload, args.output)
    if payload.get("status") in {"ready_to_clone", "ready_to_sync_existing", "clone_completed", "sync_completed"}:
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
