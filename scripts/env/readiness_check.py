#!/usr/bin/env python3
"""Check the isolated M-ABD Newton runtime without mutating environments."""

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
    parser.add_argument("--output", type=Path, help="Optional JSON report path.")
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
