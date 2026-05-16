"""Shared report status contracts for M-ABD reproduction evidence."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class EvidenceStatus(str, Enum):
    """Allowed machine-readable reproduction statuses."""

    PASSED = "passed"
    FAILED = "failed"
    INCOMPLETE = "incomplete"
    NOT_VERIFIED = "not_verified"
    UNSUPPORTED = "unsupported"
    QUALITATIVE_RECONSTRUCTION = "qualitative_reconstruction"


@dataclass(frozen=True)
class ClaimReport:
    """Minimal report record shared by future runners and validators."""

    claim_id: str
    scene_id: str
    solver_mode: str
    backend: str
    baseline_lane: str
    expected: dict[str, Any]
    observed: dict[str, Any]
    threshold: dict[str, Any]
    unit: str
    status: EvidenceStatus
    failure_reason: str
    source_commit: str
    vendored_newton_commit: str
    paper_source_version: str


REQUIRED_REPORT_KEYS = frozenset(ClaimReport.__dataclass_fields__)
