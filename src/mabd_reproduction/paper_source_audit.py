"""Paper-source audits for M-ABD reproduction claim boundaries."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path


DEFAULT_PAPER_SOURCE_ROOT = Path("/tmp/mabd-paper/source")

AUDITED_FILE_HASHES = {
    "sections/singleabd.tex": (
        "0f18165cba13d358a07c67a652e728170abecd7372b5ba905ff2b4a5950a3e8d"
    ),
    "sections/solver.tex": (
        "871dbd7ae7f5544b95c6c4dc0940cb6a0e73eca48415b1abed2e3599db90c97e"
    ),
    "sections/experiment.tex": (
        "c5927183fe4e3f1c1c1617e5b10b7e9006da6a9eac537e891cb1dac03d58dd0f"
    ),
    "images/cube/roll_cube.pdf": (
        "7669b062348324a3b0090cc9f44930655c83233a87f63389db9198b88f95ae80"
    ),
}


@dataclass(frozen=True)
class PaperSourceFinding:
    key: str
    present: bool
    path: str
    line_start: int | None
    line_end: int | None
    evidence_text: str

    def to_report(self) -> dict[str, object]:
        return {
            "key": self.key,
            "present": self.present,
            "path": self.path,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "evidence_text": self.evidence_text,
        }


@dataclass(frozen=True)
class VelocitySemanticsSourceAudit:
    source_root: str
    file_hashes: dict[str, str]
    scanned_tex_paths: tuple[str, ...]
    findings: tuple[PaperSourceFinding, ...]
    blockers: tuple[str, ...]
    status: str

    def to_report(self) -> dict[str, object]:
        return {
            "source_root": self.source_root,
            "file_hashes": dict(self.file_hashes),
            "scanned_tex_paths": list(self.scanned_tex_paths),
            "findings": [finding.to_report() for finding in self.findings],
            "blockers": list(self.blockers),
            "status": self.status,
        }


def file_sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _strip_tex_comment(line: str) -> str:
    escaped = False
    parts: list[str] = []
    for char in line:
        if char == "%" and not escaped:
            break
        parts.append(char)
        escaped = char == "\\" and not escaped
        if char != "\\":
            escaped = False
    return "".join(parts)


def _read_lines(source_root: Path, relative_path: str) -> list[str]:
    return (source_root / relative_path).read_text(encoding="utf-8").splitlines()


def _discover_tex_paths(source_root: Path) -> tuple[str, ...]:
    return tuple(
        sorted(path.relative_to(source_root).as_posix() for path in source_root.rglob("*.tex"))
    )


def _line_window_finding(
    *,
    source_root: Path,
    key: str,
    relative_path: str,
    line_start: int,
    line_end: int,
    required_snippets: tuple[str, ...],
) -> PaperSourceFinding:
    lines = _read_lines(source_root, relative_path)
    selected = lines[line_start - 1 : line_end]
    uncommented = "\n".join(_strip_tex_comment(line).strip() for line in selected)
    present = all(snippet in uncommented for snippet in required_snippets)
    return PaperSourceFinding(
        key=key,
        present=present,
        path=relative_path,
        line_start=line_start,
        line_end=line_end,
        evidence_text=uncommented if present else f"missing snippets: {required_snippets!r}",
    )


def _scan_uncommented_tex(
    source_root: Path,
    tex_paths: tuple[str, ...],
    patterns: tuple[str, ...],
) -> list[tuple[str, int, str, str]]:
    hits: list[tuple[str, int, str, str]] = []
    for relative_path in tex_paths:
        for line_number, line in enumerate(_read_lines(source_root, relative_path), start=1):
            uncommented = _strip_tex_comment(line).strip()
            if not uncommented:
                continue
            normalized = uncommented.lower()
            for pattern in patterns:
                if pattern.lower() in normalized:
                    hits.append((relative_path, line_number, pattern, uncommented))
    return hits


def _negative_scan_finding(
    *,
    source_root: Path,
    tex_paths: tuple[str, ...],
    key: str,
    patterns: tuple[str, ...],
) -> PaperSourceFinding:
    hits = _scan_uncommented_tex(source_root, tex_paths, patterns)
    if hits:
        evidence = "\n".join(f"{path}:{line_number}: {text}" for path, line_number, _, text in hits)
        return PaperSourceFinding(
            key=key,
            present=True,
            path=";".join(sorted({path for path, _, _, _ in hits})),
            line_start=min(line_number for _, line_number, _, _ in hits),
            line_end=max(line_number for _, line_number, _, _ in hits),
            evidence_text=evidence,
        )
    return PaperSourceFinding(
        key=key,
        present=False,
        path="uncommented TeX scan",
        line_start=None,
        line_end=None,
        evidence_text="no matching uncommented source line",
    )


def velocity_semantics_source_audit(
    source_root: Path = DEFAULT_PAPER_SOURCE_ROOT,
) -> VelocitySemanticsSourceAudit:
    source_root = Path(source_root)
    if not source_root.exists():
        raise FileNotFoundError(
            f"paper source root does not exist: {source_root}; "
            "extract the paper source to /tmp/mabd-paper/source before running this audit"
        )
    tex_paths = _discover_tex_paths(source_root)
    file_hashes = {
        relative_path: file_sha256(source_root / relative_path)
        for relative_path in AUDITED_FILE_HASHES
    }

    findings = (
        _line_window_finding(
            source_root=source_root,
            key="implicit_euler_inertia_potential",
            relative_path="sections/singleabd.tex",
            line_start=34,
            line_end=42,
            required_snippets=(
                "E_I(\\bm{x})",
                "implicit Euler",
                "h\\dot{\\bm{x}}^n",
            ),
        ),
        _line_window_finding(
            source_root=source_root,
            key="g_map_twist_velocity",
            relative_path="sections/solver.tex",
            line_start=219,
            line_end=229,
            required_snippets=(
                "spatial twist",
                "\\bm V^j = \\bm{G}\\dot{\\bm q}^j",
            ),
        ),
        _line_window_finding(
            source_root=source_root,
            key="wrench_map_generalized_force",
            relative_path="sections/solver.tex",
            line_start=238,
            line_end=241,
            required_snippets=(
                "G(\\bm A^j)^\\top",
                "\\frac{1}{h}\\bm M_{A}^j\\dot{\\bm q}^j",
            ),
        ),
        _line_window_finding(
            source_root=source_root,
            key="spinning_box_twist_initialization",
            relative_path="sections/experiment.tex",
            line_start=40,
            line_end=55,
            required_snippets=(
                "\\bm p_0=[100, 0, 0]",
                "\\bm L_0=[0, 100, 0]",
                "\\bm V_0",
                "map it to ABD generalized velocities",
            ),
        ),
        _negative_scan_finding(
            source_root=source_root,
            tex_paths=tex_paths,
            key="decoupled_velocity_semantics",
            patterns=(
                "decoupled velocity",
                "decouple velocity",
                "velocity semantics",
                "qd_next",
                "q_{n+1}-q_n",
                "stored velocity",
            ),
        ),
        _negative_scan_finding(
            source_root=source_root,
            tex_paths=tex_paths,
            key="alternative_momentum_extraction",
            patterns=(
                "momentum extraction",
                "extract momentum",
                "alternative momentum",
                "computed from q_{n+1}",
                "read momentum",
            ),
        ),
    )

    expected_hash_mismatches = tuple(
        relative_path
        for relative_path, expected in AUDITED_FILE_HASHES.items()
        if file_hashes[relative_path] != expected
    )
    missing_positive_evidence = tuple(finding.key for finding in findings[:4] if not finding.present)
    blockers: tuple[str, ...] = ()
    decoupled_finding = findings[4]
    alternative_momentum_finding = findings[5]
    if not decoupled_finding.present:
        blockers = (*blockers, "source_does_not_specify_decoupled_velocity_semantics")
    if not alternative_momentum_finding.present:
        blockers = (*blockers, "source_does_not_specify_alternative_momentum_extraction")
    if expected_hash_mismatches:
        blockers = (*blockers, "paper_source_hash_mismatch")
    if missing_positive_evidence:
        blockers = (*blockers, "paper_source_required_snippet_missing")
    status = (
        "source_mentions_velocity_semantics_requiring_manual_review"
        if decoupled_finding.present or alternative_momentum_finding.present
        else "source_does_not_prove_decoupled_velocity_semantics"
    )

    return VelocitySemanticsSourceAudit(
        source_root=str(source_root),
        file_hashes=file_hashes,
        scanned_tex_paths=tex_paths,
        findings=findings,
        blockers=blockers,
        status=status,
    )


__all__ = [
    "AUDITED_FILE_HASHES",
    "DEFAULT_PAPER_SOURCE_ROOT",
    "PaperSourceFinding",
    "VelocitySemanticsSourceAudit",
    "file_sha256",
    "velocity_semantics_source_audit",
]
