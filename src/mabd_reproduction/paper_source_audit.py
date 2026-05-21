"""Paper-source audits for M-ABD reproduction claim boundaries."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import re


DEFAULT_PAPER_SOURCE_ROOT = Path("/tmp/mabd-paper/source")
TEXT_SOURCE_SUFFIXES = frozenset((".bib", ".bst", ".cls", ".json", ".tex"))

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

PHYSICAL_PENDULUM_AUDITED_FILE_HASHES = {
    "sections/experiment.tex": (
        "c5927183fe4e3f1c1c1617e5b10b7e9006da6a9eac537e891cb1dac03d58dd0f"
    ),
    "images/simple_pendulum/simple_pendulum.pdf": (
        "4b198ace42ff08d32dc266f1eca710987a2b6335d75878ee01b60498fed945cf"
    ),
}

ROLLING_SPINNING_EXPLICIT_RBD_AUDITED_FILE_HASHES = {
    "sections/singleabd.tex": (
        "0f18165cba13d358a07c67a652e728170abecd7372b5ba905ff2b4a5950a3e8d"
    ),
    "sections/experiment.tex": (
        "c5927183fe4e3f1c1c1617e5b10b7e9006da6a9eac537e891cb1dac03d58dd0f"
    ),
}

ROLLING_SPINNING_IMPLICIT_RBD_AUDITED_FILE_HASHES = {
    "sections/singleabd.tex": (
        "0f18165cba13d358a07c67a652e728170abecd7372b5ba905ff2b4a5950a3e8d"
    ),
    "sections/experiment.tex": (
        "c5927183fe4e3f1c1c1617e5b10b7e9006da6a9eac537e891cb1dac03d58dd0f"
    ),
}

ROLLING_SPINNING_MABD_AUDITED_FILE_HASHES = {
    "sections/singleabd.tex": (
        "0f18165cba13d358a07c67a652e728170abecd7372b5ba905ff2b4a5950a3e8d"
    ),
    "sections/experiment.tex": (
        "c5927183fe4e3f1c1c1617e5b10b7e9006da6a9eac537e891cb1dac03d58dd0f"
    ),
}

ROLLING_SPINNING_EXPLICIT_RBD_REQUIRED_SOURCE_PARAMETERS = (
    "rolling_cylinder_geometry",
    "rolling_cylinder_mass_or_density",
    "rolling_cylinder_initial_state",
    "rolling_cylinder_contact_friction_model",
    "explicit_rbd_integrator_details",
    "explicit_rbd_collision_parameters",
)

ROLLING_SPINNING_IMPLICIT_RBD_REQUIRED_SOURCE_PARAMETERS = (
    "rolling_cylinder_geometry",
    "rolling_cylinder_mass_or_density",
    "rolling_cylinder_initial_state",
    "rolling_cylinder_contact_friction_model",
    "implicit_rbd_integrator_details",
    "implicit_rbd_collision_parameters",
)

ROLLING_SPINNING_MABD_REQUIRED_SOURCE_PARAMETERS = (
    "rolling_cylinder_geometry",
    "rolling_cylinder_mass_or_density",
    "rolling_cylinder_initial_state",
    "mabd_affine_body_discretization",
    "mabd_rolling_contact_friction_model",
    "mabd_collision_parameters",
)


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


@dataclass(frozen=True)
class PhysicalPendulumGeometrySourceAudit:
    source_root: str
    file_hashes: dict[str, str]
    source_tree_paths: tuple[str, ...]
    scanned_text_paths: tuple[str, ...]
    scanned_tex_paths: tuple[str, ...]
    positive_findings: dict[str, dict[str, object]]
    absence_findings: dict[str, dict[str, object]]
    figure_pdf: dict[str, object]
    missing_parameters: tuple[str, ...]
    blockers: tuple[str, ...]
    status: str

    def to_report(self) -> dict[str, object]:
        return {
            "source_root": self.source_root,
            "file_hashes": dict(self.file_hashes),
            "source_tree_paths": list(self.source_tree_paths),
            "scanned_text_paths": list(self.scanned_text_paths),
            "scanned_tex_paths": list(self.scanned_tex_paths),
            "positive_findings": dict(self.positive_findings),
            "absence_findings": dict(self.absence_findings),
            "figure_pdf": dict(self.figure_pdf),
            "missing_parameters": list(self.missing_parameters),
            "blockers": list(self.blockers),
            "status": self.status,
        }


@dataclass(frozen=True)
class RollingSpinningExplicitRBDSourceAudit:
    source_root: str
    file_hashes: dict[str, str]
    source_tree_paths: tuple[str, ...]
    scanned_text_paths: tuple[str, ...]
    scanned_tex_paths: tuple[str, ...]
    positive_findings: dict[str, dict[str, object]]
    absence_findings: dict[str, dict[str, object]]
    missing_parameters: tuple[str, ...]
    blockers: tuple[str, ...]
    status: str

    def to_report(self) -> dict[str, object]:
        return {
            "source_root": self.source_root,
            "file_hashes": dict(self.file_hashes),
            "source_tree_paths": list(self.source_tree_paths),
            "scanned_text_paths": list(self.scanned_text_paths),
            "scanned_tex_paths": list(self.scanned_tex_paths),
            "positive_findings": dict(self.positive_findings),
            "absence_findings": dict(self.absence_findings),
            "missing_parameters": list(self.missing_parameters),
            "blockers": list(self.blockers),
            "status": self.status,
        }


@dataclass(frozen=True)
class RollingSpinningImplicitRBDSourceAudit:
    source_root: str
    file_hashes: dict[str, str]
    source_tree_paths: tuple[str, ...]
    scanned_text_paths: tuple[str, ...]
    scanned_tex_paths: tuple[str, ...]
    positive_findings: dict[str, dict[str, object]]
    absence_findings: dict[str, dict[str, object]]
    missing_parameters: tuple[str, ...]
    blockers: tuple[str, ...]
    status: str

    def to_report(self) -> dict[str, object]:
        return {
            "source_root": self.source_root,
            "file_hashes": dict(self.file_hashes),
            "source_tree_paths": list(self.source_tree_paths),
            "scanned_text_paths": list(self.scanned_text_paths),
            "scanned_tex_paths": list(self.scanned_tex_paths),
            "positive_findings": dict(self.positive_findings),
            "absence_findings": dict(self.absence_findings),
            "missing_parameters": list(self.missing_parameters),
            "blockers": list(self.blockers),
            "status": self.status,
        }


@dataclass(frozen=True)
class RollingSpinningMABDSourceAudit:
    source_root: str
    file_hashes: dict[str, str]
    source_tree_paths: tuple[str, ...]
    scanned_text_paths: tuple[str, ...]
    scanned_tex_paths: tuple[str, ...]
    positive_findings: dict[str, dict[str, object]]
    absence_findings: dict[str, dict[str, object]]
    missing_parameters: tuple[str, ...]
    blockers: tuple[str, ...]
    status: str

    def to_report(self) -> dict[str, object]:
        return {
            "source_root": self.source_root,
            "file_hashes": dict(self.file_hashes),
            "source_tree_paths": list(self.source_tree_paths),
            "scanned_text_paths": list(self.scanned_text_paths),
            "scanned_tex_paths": list(self.scanned_tex_paths),
            "positive_findings": dict(self.positive_findings),
            "absence_findings": dict(self.absence_findings),
            "missing_parameters": list(self.missing_parameters),
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


def _discover_source_tree_paths(source_root: Path) -> tuple[str, ...]:
    return tuple(
        sorted(
            path.relative_to(source_root).as_posix()
            for path in source_root.rglob("*")
            if path.is_file()
        )
    )


def _discover_text_paths(source_tree_paths: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(
        path
        for path in source_tree_paths
        if Path(path).suffix.lower() in TEXT_SOURCE_SUFFIXES
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


def _read_text_asset(source_root: Path, relative_path: str) -> str:
    return (source_root / relative_path).read_bytes().decode("utf-8", errors="ignore")


def _scan_text_assets_for_patterns(
    source_root: Path,
    relative_paths: tuple[str, ...],
    patterns: tuple[str, ...],
) -> tuple[str, ...]:
    hits: list[str] = []
    for relative_path in relative_paths:
        lines = _read_text_asset(source_root, relative_path).splitlines()
        for line_number, line in enumerate(lines, start=1):
            uncommented = _strip_tex_comment(line).strip()
            if not uncommented:
                continue
            normalized = uncommented.lower()
            if any(pattern.lower() in normalized for pattern in patterns):
                hits.append(f"{relative_path}:{line_number}: {uncommented}")
    return tuple(hits)


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


def _required_file_hashes(
    source_root: Path,
    expected_hashes: dict[str, str],
) -> dict[str, str]:
    file_hashes: dict[str, str] = {}
    for relative_path in expected_hashes:
        path = source_root / relative_path
        if not path.exists():
            raise FileNotFoundError(f"required paper source file does not exist: {path}")
        file_hashes[relative_path] = file_sha256(path)
    return file_hashes


def _physical_pendulum_pdf_image_paths(figure_pdf: Path) -> tuple[str, ...]:
    text = figure_pdf.read_bytes().decode("latin-1", errors="ignore")
    paths: list[str] = []
    for match in re.finditer(
        r"<stRef:filePath>(?P<path>.*?)</stRef:filePath>",
        text,
        flags=re.DOTALL,
    ):
        candidate = match.group("path").strip()
        if "pendulum" in candidate.lower():
            paths.append(candidate)
    for match in re.finditer(
        r"%%(?:DocumentFiles:|\+)(?P<path>[^\r\n]*pendulum\d+\.png)",
        text,
        flags=re.IGNORECASE,
    ):
        paths.append(match.group("path").strip())
    if not paths:
        paths.extend(
            match.group(0)
            for match in re.finditer(r"pendulum\d+\.png", text, flags=re.IGNORECASE)
        )
    return tuple(dict.fromkeys(paths))


def _physical_pendulum_geometry_absence_findings(
    *,
    source_root: Path,
    source_tree_paths: tuple[str, ...],
    scanned_text_paths: tuple[str, ...],
    figure_image_paths: tuple[str, ...],
) -> dict[str, dict[str, object]]:
    query_terms = (
        "body geometry",
        "length scale",
        "mass distribution",
        "inertia tensor",
        "raw angle curve data",
        "raw joint force curve data",
        "physical pendulum mesh",
        "physical pendulum body",
        "physical pendulum length",
        "physical pendulum mass",
        "physical pendulum inertia",
        "pendulum15.png",
    )
    context_terms = (
        "physical pendulum",
        "fixed pivot",
        "horizontal configuration",
        "zero initial velocity",
        "joint force",
        "elliptic",
        "pendulum15.png",
    )
    context_hits = list(
        _scan_text_assets_for_patterns(source_root, scanned_text_paths, context_terms)
    )
    context_hits.extend(
        f"images/simple_pendulum/simple_pendulum.pdf:metadata: {path}"
        for path in figure_image_paths
    )
    candidate_hits = list(_scan_text_assets_for_patterns(source_root, scanned_text_paths, query_terms))
    candidate_hits.extend(
        f"images/simple_pendulum/simple_pendulum.pdf:metadata: {path}"
        for path in figure_image_paths
        if any(term.lower() in path.lower() for term in query_terms)
    )
    usable_parameter_disclosures = [
        hit
        for hit in candidate_hits
        if "physical pendulum" in hit.lower()
        and any(
            term in hit.lower()
            for term in ("body geometry", "length scale", "mass distribution", "inertia tensor")
        )
    ]
    return {
        "physical_pendulum_geometry_parameter_search": {
            "status": "no_paper_faithful_physical_pendulum_geometry_parameters_found",
            "query_terms": list(query_terms),
            "searched_source_path_count": len(source_tree_paths),
            "scanned_text_path_count": len(scanned_text_paths),
            "context_hits": context_hits[:64],
            "candidate_hits": candidate_hits[:64],
            "usable_parameter_disclosures": usable_parameter_disclosures,
        }
    }


def physical_pendulum_geometry_source_audit(
    source_root: Path = DEFAULT_PAPER_SOURCE_ROOT,
) -> PhysicalPendulumGeometrySourceAudit:
    source_root = Path(source_root)
    if not source_root.exists():
        raise FileNotFoundError(
            f"paper source root does not exist: {source_root}; "
            "extract the paper source to /tmp/mabd-paper/source before running this audit"
        )

    file_hashes = _required_file_hashes(source_root, PHYSICAL_PENDULUM_AUDITED_FILE_HASHES)
    source_tree_paths = _discover_source_tree_paths(source_root)
    scanned_text_paths = _discover_text_paths(source_tree_paths)
    scanned_tex_paths = _discover_tex_paths(source_root)
    figure_relative_path = "images/simple_pendulum/simple_pendulum.pdf"
    figure_image_paths = _physical_pendulum_pdf_image_paths(source_root / figure_relative_path)
    absence_findings = _physical_pendulum_geometry_absence_findings(
        source_root=source_root,
        source_tree_paths=source_tree_paths,
        scanned_text_paths=scanned_text_paths,
        figure_image_paths=figure_image_paths,
    )
    positive_findings = {
        finding.key: finding.to_report()
        for finding in (
            _line_window_finding(
                source_root=source_root,
                key="figure_pdf_included",
                relative_path="sections/experiment.tex",
                line_start=77,
                line_end=83,
                required_snippets=("images/simple_pendulum/simple_pendulum.pdf",),
            ),
            _line_window_finding(
                source_root=source_root,
                key="fixed_pivot",
                relative_path="sections/experiment.tex",
                line_start=77,
                line_end=91,
                required_snippets=("fixed pivot",),
            ),
            _line_window_finding(
                source_root=source_root,
                key="horizontal_release_zero_initial_velocity",
                relative_path="sections/experiment.tex",
                line_start=77,
                line_end=91,
                required_snippets=("horizontal configuration", "zero initial velocity"),
            ),
            _line_window_finding(
                source_root=source_root,
                key="gravity",
                relative_path="sections/experiment.tex",
                line_start=77,
                line_end=91,
                required_snippets=("under gravity",),
            ),
            _line_window_finding(
                source_root=source_root,
                key="elliptic_angle_reference",
                relative_path="sections/experiment.tex",
                line_start=77,
                line_end=91,
                required_snippets=("elliptic-integral", "\\theta(t)"),
            ),
            _line_window_finding(
                source_root=source_root,
                key="joint_force_magnitude_plot",
                relative_path="sections/experiment.tex",
                line_start=77,
                line_end=91,
                required_snippets=("magnitude of the joint force",),
            ),
            _line_window_finding(
                source_root=source_root,
                key="phase_drift",
                relative_path="sections/experiment.tex",
                line_start=77,
                line_end=91,
                required_snippets=("phase drift",),
            ),
            _line_window_finding(
                source_root=source_root,
                key="abd_rbd_comparison",
                relative_path="sections/experiment.tex",
                line_start=77,
                line_end=91,
                required_snippets=("ABD method", "implicit RBD baseline"),
            ),
        )
    }

    missing_parameters = (
        "body_geometry",
        "length_scale",
        "mass_distribution",
        "inertia_tensor",
        "raw_angle_curve_data",
        "raw_joint_force_curve_data",
        "abd_timestep_values",
        "rbd_timestep_values",
        "exact_abd_numeric_outputs",
        "exact_rbd_numeric_outputs",
    )
    usable_parameter_disclosures = absence_findings["physical_pendulum_geometry_parameter_search"][
        "usable_parameter_disclosures"
    ]
    blockers = (
        (
            "physical_pendulum_geometry_parameters_missing_from_public_source_assets",
            "raw_physical_pendulum_curve_data_missing_from_public_source_assets",
            "physical_pendulum_private_author_assets_not_audited",
        )
        if not usable_parameter_disclosures
        else (
            "physical_pendulum_geometry_parameter_disclosure_found",
            "physical_pendulum_manual_geometry_review_required",
        )
    )
    hash_mismatches = tuple(
        relative_path
        for relative_path, expected in PHYSICAL_PENDULUM_AUDITED_FILE_HASHES.items()
        if file_hashes[relative_path] != expected
    )
    missing_positive_evidence = tuple(
        key for key, finding in positive_findings.items() if not finding["present"]
    )
    if hash_mismatches:
        blockers = (*blockers, "paper_source_hash_mismatch")
    if missing_positive_evidence:
        blockers = (*blockers, "paper_source_required_snippet_missing")
    status = (
        "source_mentions_physical_pendulum_geometry_parameters_requiring_manual_review"
        if usable_parameter_disclosures
        else (
            "source_assets_found_geometry_parameters_missing"
            if not hash_mismatches and not missing_positive_evidence
            else "source_assets_changed_or_required_physical_pendulum_facts_missing"
        )
    )

    return PhysicalPendulumGeometrySourceAudit(
        source_root=str(source_root),
        file_hashes=file_hashes,
        source_tree_paths=source_tree_paths,
        scanned_text_paths=scanned_text_paths,
        scanned_tex_paths=scanned_tex_paths,
        positive_findings=positive_findings,
        absence_findings=absence_findings,
        figure_pdf={
            "path": figure_relative_path,
            "sha256": file_hashes[figure_relative_path],
            "embedded_image_paths": list(figure_image_paths),
        },
        missing_parameters=missing_parameters,
        blockers=blockers,
        status=status,
    )


def _rolling_spinning_explicit_rbd_absence_findings(
    *,
    source_root: Path,
    source_tree_paths: tuple[str, ...],
    scanned_text_paths: tuple[str, ...],
) -> dict[str, dict[str, object]]:
    query_terms = (
        "rolling cylinder geometry",
        "rolling cylinder radius",
        "rolling cylinder half height",
        "rolling cylinder density",
        "rolling cylinder mass",
        "rolling cylinder initial position",
        "rolling cylinder initial linear velocity",
        "rolling cylinder initial angular velocity",
        "rolling cylinder contact friction model",
        "rolling cylinder collision parameters",
        "no-slip",
        "explicit RBD integrator",
        "explicit Euler",
        "collision parameters",
        "ke kd kf mu",
    )
    context_terms = (
        "rolling cylinder",
        "explicit RBD",
        "implicit RBD",
        "single thread",
        "10K",
        "h = 0.01",
    )
    context_hits = list(
        _scan_text_assets_for_patterns(source_root, scanned_text_paths, context_terms)
    )
    candidate_hits = list(
        _scan_text_assets_for_patterns(source_root, scanned_text_paths, query_terms)
    )
    parameter_terms = (
        "geometry",
        "radius",
        "half height",
        "density",
        "mass",
        "initial position",
        "initial linear velocity",
        "initial angular velocity",
        "contact friction model",
        "collision parameters",
        "no-slip",
        "explicit rbd integrator",
        "explicit euler",
        "ke kd kf mu",
    )
    usable_parameter_disclosures = [
        hit
        for hit in candidate_hits
        if "rolling cylinder" in hit.lower()
        and any(term in hit.lower() for term in parameter_terms)
    ]
    return {
        "rolling_spinning_explicit_rbd_parameter_search": {
            "status": "no_paper_faithful_explicit_rbd_source_parameters_found",
            "query_terms": list(query_terms),
            "searched_source_path_count": len(source_tree_paths),
            "scanned_text_path_count": len(scanned_text_paths),
            "context_hits": context_hits[:64],
            "candidate_hits": candidate_hits[:64],
            "usable_parameter_disclosures": usable_parameter_disclosures[:64],
        }
    }


def _rolling_spinning_implicit_rbd_absence_findings(
    *,
    source_root: Path,
    source_tree_paths: tuple[str, ...],
    scanned_text_paths: tuple[str, ...],
) -> dict[str, dict[str, object]]:
    query_terms = (
        "rolling cylinder geometry",
        "rolling cylinder radius",
        "rolling cylinder half height",
        "rolling cylinder density",
        "rolling cylinder mass",
        "rolling cylinder initial position",
        "rolling cylinder initial linear velocity",
        "rolling cylinder initial angular velocity",
        "rolling cylinder contact friction model",
        "rolling cylinder collision parameters",
        "no-slip",
        "implicit RBD integrator",
        "implicit Euler",
        "backward Euler",
        "Newton iterations",
        "collision parameters",
        "ke kd kf mu",
    )
    context_terms = (
        "rolling cylinder",
        "explicit RBD",
        "implicit RBD",
        "single thread",
        "10K",
        "h = 0.01",
    )
    context_hits = list(
        _scan_text_assets_for_patterns(source_root, scanned_text_paths, context_terms)
    )
    candidate_hits = list(
        _scan_text_assets_for_patterns(source_root, scanned_text_paths, query_terms)
    )
    parameter_terms = (
        "geometry",
        "radius",
        "half height",
        "density",
        "mass",
        "initial position",
        "initial linear velocity",
        "initial angular velocity",
        "contact friction model",
        "collision parameters",
        "no-slip",
        "implicit rbd integrator",
        "implicit euler",
        "backward euler",
        "newton iterations",
        "ke kd kf mu",
    )
    usable_parameter_disclosures = [
        hit
        for hit in candidate_hits
        if "rolling cylinder" in hit.lower()
        and any(term in hit.lower() for term in parameter_terms)
    ]
    return {
        "rolling_spinning_implicit_rbd_parameter_search": {
            "status": "no_paper_faithful_implicit_rbd_source_parameters_found",
            "query_terms": list(query_terms),
            "searched_source_path_count": len(source_tree_paths),
            "scanned_text_path_count": len(scanned_text_paths),
            "context_hits": context_hits[:64],
            "candidate_hits": candidate_hits[:64],
            "usable_parameter_disclosures": usable_parameter_disclosures[:64],
        }
    }


def _rolling_spinning_mabd_absence_findings(
    *,
    source_root: Path,
    source_tree_paths: tuple[str, ...],
    scanned_text_paths: tuple[str, ...],
) -> dict[str, dict[str, object]]:
    query_terms = (
        "rolling cylinder geometry",
        "rolling cylinder radius",
        "rolling cylinder half height",
        "rolling cylinder density",
        "rolling cylinder mass",
        "rolling cylinder initial position",
        "rolling cylinder initial linear velocity",
        "rolling cylinder initial angular velocity",
        "M-ABD affine body discretization",
        "affine body discretization",
        "rest points",
        "point masses",
        "M-ABD rolling contact friction model",
        "affine no-slip contact constraints",
        "M-ABD collision parameters",
        "collision parameters",
        "ke kd kf mu",
    )
    context_terms = (
        "rolling cylinder",
        "ABD",
        "co-rotated",
        "single thread",
        "10K",
        "h = 0.01",
    )
    context_hits = list(
        _scan_text_assets_for_patterns(source_root, scanned_text_paths, context_terms)
    )
    candidate_hits = list(
        _scan_text_assets_for_patterns(source_root, scanned_text_paths, query_terms)
    )
    parameter_terms = (
        "geometry",
        "radius",
        "half height",
        "density",
        "mass",
        "initial position",
        "initial linear velocity",
        "initial angular velocity",
        "affine body discretization",
        "rest points",
        "point masses",
        "rolling contact friction model",
        "affine no-slip contact constraints",
        "collision parameters",
        "ke kd kf mu",
    )
    usable_parameter_disclosures = [
        hit
        for hit in candidate_hits
        if "rolling cylinder" in hit.lower()
        and any(term in hit.lower() for term in parameter_terms)
    ]
    return {
        "rolling_spinning_mabd_parameter_search": {
            "status": "no_paper_faithful_mabd_source_parameters_found",
            "query_terms": list(query_terms),
            "searched_source_path_count": len(source_tree_paths),
            "scanned_text_path_count": len(scanned_text_paths),
            "context_hits": context_hits[:64],
            "candidate_hits": candidate_hits[:64],
            "usable_parameter_disclosures": usable_parameter_disclosures[:64],
        }
    }


def rolling_spinning_explicit_rbd_source_audit(
    source_root: Path = DEFAULT_PAPER_SOURCE_ROOT,
) -> RollingSpinningExplicitRBDSourceAudit:
    source_root = Path(source_root)
    if not source_root.exists():
        raise FileNotFoundError(
            f"paper source root does not exist: {source_root}; "
            "extract the paper source to /tmp/mabd-paper/source before running this audit"
        )

    file_hashes = _required_file_hashes(
        source_root,
        ROLLING_SPINNING_EXPLICIT_RBD_AUDITED_FILE_HASHES,
    )
    source_tree_paths = _discover_source_tree_paths(source_root)
    scanned_text_paths = _discover_text_paths(source_tree_paths)
    scanned_tex_paths = _discover_tex_paths(source_root)
    absence_findings = _rolling_spinning_explicit_rbd_absence_findings(
        source_root=source_root,
        source_tree_paths=source_tree_paths,
        scanned_text_paths=scanned_text_paths,
    )
    positive_findings = {
        finding.key: finding.to_report()
        for finding in (
            _line_window_finding(
                source_root=source_root,
                key="rolling_cylinder_benchmark",
                relative_path="sections/singleabd.tex",
                line_start=162,
                line_end=172,
                required_snippets=("rolling cylinder",),
            ),
            _line_window_finding(
                source_root=source_root,
                key="rolling_cylinder_step_count",
                relative_path="sections/singleabd.tex",
                line_start=162,
                line_end=172,
                required_snippets=("10K",),
            ),
            _line_window_finding(
                source_root=source_root,
                key="rolling_cylinder_time_step",
                relative_path="sections/singleabd.tex",
                line_start=162,
                line_end=172,
                required_snippets=("h = 0.01~sec",),
            ),
            _line_window_finding(
                source_root=source_root,
                key="explicit_rbd_timing_context",
                relative_path="sections/singleabd.tex",
                line_start=162,
                line_end=172,
                required_snippets=("explicit RBD", "32~ms"),
            ),
            _line_window_finding(
                source_root=source_root,
                key="hardware_thread_context",
                relative_path="sections/singleabd.tex",
                line_start=162,
                line_end=172,
                required_snippets=("i7 CPU", "single thread"),
            ),
            _line_window_finding(
                source_root=source_root,
                key="single_body_cube_not_rolling_source_context",
                relative_path="sections/experiment.tex",
                line_start=48,
                line_end=55,
                required_snippets=("single cube", "implicit RBD baseline"),
            ),
        )
    }

    usable_parameter_disclosures = absence_findings[
        "rolling_spinning_explicit_rbd_parameter_search"
    ]["usable_parameter_disclosures"]
    missing_parameters = (
        ()
        if usable_parameter_disclosures
        else ROLLING_SPINNING_EXPLICIT_RBD_REQUIRED_SOURCE_PARAMETERS
    )
    blockers = (
        (
            "explicit_rbd_source_disclosure_found",
            "explicit_rbd_manual_source_review_required",
        )
        if usable_parameter_disclosures
        else (
            "rolling_cylinder_geometry_parameters_missing_from_public_source",
            "rolling_cylinder_initial_state_missing_from_public_source",
            "rolling_cylinder_contact_friction_model_missing_from_public_source",
            "paper_explicit_rbd_solver_details_missing_from_public_source",
            "paper_explicit_rbd_collision_parameters_missing_from_public_source",
        )
    )
    hash_mismatches = tuple(
        relative_path
        for relative_path, expected in ROLLING_SPINNING_EXPLICIT_RBD_AUDITED_FILE_HASHES.items()
        if file_hashes[relative_path] != expected
    )
    missing_positive_evidence = tuple(
        key for key, finding in positive_findings.items() if not finding["present"]
    )
    if hash_mismatches:
        blockers = (*blockers, "paper_source_hash_mismatch")
    if missing_positive_evidence:
        blockers = (*blockers, "paper_source_required_snippet_missing")
    status = (
        "explicit_rbd_source_mentions_require_manual_review"
        if usable_parameter_disclosures
        else (
            "explicit_rbd_source_requirements_incomplete"
            if not hash_mismatches and not missing_positive_evidence
            else "explicit_rbd_source_changed_or_required_facts_missing"
        )
    )

    return RollingSpinningExplicitRBDSourceAudit(
        source_root=str(source_root),
        file_hashes=file_hashes,
        source_tree_paths=source_tree_paths,
        scanned_text_paths=scanned_text_paths,
        scanned_tex_paths=scanned_tex_paths,
        positive_findings=positive_findings,
        absence_findings=absence_findings,
        missing_parameters=missing_parameters,
        blockers=blockers,
        status=status,
    )


def rolling_spinning_implicit_rbd_source_audit(
    source_root: Path = DEFAULT_PAPER_SOURCE_ROOT,
) -> RollingSpinningImplicitRBDSourceAudit:
    source_root = Path(source_root)
    if not source_root.exists():
        raise FileNotFoundError(
            f"paper source root does not exist: {source_root}; "
            "extract the paper source to /tmp/mabd-paper/source before running this audit"
        )

    file_hashes = _required_file_hashes(
        source_root,
        ROLLING_SPINNING_IMPLICIT_RBD_AUDITED_FILE_HASHES,
    )
    source_tree_paths = _discover_source_tree_paths(source_root)
    scanned_text_paths = _discover_text_paths(source_tree_paths)
    scanned_tex_paths = _discover_tex_paths(source_root)
    absence_findings = _rolling_spinning_implicit_rbd_absence_findings(
        source_root=source_root,
        source_tree_paths=source_tree_paths,
        scanned_text_paths=scanned_text_paths,
    )
    positive_findings = {
        finding.key: finding.to_report()
        for finding in (
            _line_window_finding(
                source_root=source_root,
                key="rolling_cylinder_benchmark",
                relative_path="sections/singleabd.tex",
                line_start=162,
                line_end=172,
                required_snippets=("rolling cylinder",),
            ),
            _line_window_finding(
                source_root=source_root,
                key="rolling_cylinder_step_count",
                relative_path="sections/singleabd.tex",
                line_start=162,
                line_end=172,
                required_snippets=("10K",),
            ),
            _line_window_finding(
                source_root=source_root,
                key="rolling_cylinder_time_step",
                relative_path="sections/singleabd.tex",
                line_start=162,
                line_end=172,
                required_snippets=("h = 0.01~sec",),
            ),
            _line_window_finding(
                source_root=source_root,
                key="implicit_rbd_timing_context",
                relative_path="sections/singleabd.tex",
                line_start=162,
                line_end=172,
                required_snippets=("implicit RBD", "44~ms"),
            ),
            _line_window_finding(
                source_root=source_root,
                key="hardware_thread_context",
                relative_path="sections/singleabd.tex",
                line_start=162,
                line_end=172,
                required_snippets=("i7 CPU", "single thread"),
            ),
            _line_window_finding(
                source_root=source_root,
                key="single_body_cube_not_rolling_source_context",
                relative_path="sections/experiment.tex",
                line_start=48,
                line_end=55,
                required_snippets=("single cube", "implicit RBD baseline"),
            ),
        )
    }

    usable_parameter_disclosures = absence_findings[
        "rolling_spinning_implicit_rbd_parameter_search"
    ]["usable_parameter_disclosures"]
    missing_parameters = (
        ()
        if usable_parameter_disclosures
        else ROLLING_SPINNING_IMPLICIT_RBD_REQUIRED_SOURCE_PARAMETERS
    )
    blockers = (
        (
            "implicit_rbd_source_disclosure_found",
            "implicit_rbd_manual_source_review_required",
        )
        if usable_parameter_disclosures
        else (
            "rolling_cylinder_geometry_parameters_missing_from_public_source",
            "rolling_cylinder_initial_state_missing_from_public_source",
            "rolling_cylinder_contact_friction_model_missing_from_public_source",
            "paper_implicit_rbd_solver_details_missing_from_public_source",
            "paper_implicit_rbd_collision_parameters_missing_from_public_source",
        )
    )
    hash_mismatches = tuple(
        relative_path
        for relative_path, expected in ROLLING_SPINNING_IMPLICIT_RBD_AUDITED_FILE_HASHES.items()
        if file_hashes[relative_path] != expected
    )
    missing_positive_evidence = tuple(
        key for key, finding in positive_findings.items() if not finding["present"]
    )
    if hash_mismatches:
        blockers = (*blockers, "paper_source_hash_mismatch")
    if missing_positive_evidence:
        blockers = (*blockers, "paper_source_required_snippet_missing")
    status = (
        "implicit_rbd_source_mentions_require_manual_review"
        if usable_parameter_disclosures
        else (
            "implicit_rbd_source_requirements_incomplete"
            if not hash_mismatches and not missing_positive_evidence
            else "implicit_rbd_source_changed_or_required_facts_missing"
        )
    )

    return RollingSpinningImplicitRBDSourceAudit(
        source_root=str(source_root),
        file_hashes=file_hashes,
        source_tree_paths=source_tree_paths,
        scanned_text_paths=scanned_text_paths,
        scanned_tex_paths=scanned_tex_paths,
        positive_findings=positive_findings,
        absence_findings=absence_findings,
        missing_parameters=missing_parameters,
        blockers=blockers,
        status=status,
    )


def rolling_spinning_mabd_source_audit(
    source_root: Path = DEFAULT_PAPER_SOURCE_ROOT,
) -> RollingSpinningMABDSourceAudit:
    source_root = Path(source_root)
    if not source_root.exists():
        raise FileNotFoundError(
            f"paper source root does not exist: {source_root}; "
            "extract the paper source to /tmp/mabd-paper/source before running this audit"
        )

    file_hashes = _required_file_hashes(
        source_root,
        ROLLING_SPINNING_MABD_AUDITED_FILE_HASHES,
    )
    source_tree_paths = _discover_source_tree_paths(source_root)
    scanned_text_paths = _discover_text_paths(source_tree_paths)
    scanned_tex_paths = _discover_tex_paths(source_root)
    absence_findings = _rolling_spinning_mabd_absence_findings(
        source_root=source_root,
        source_tree_paths=source_tree_paths,
        scanned_text_paths=scanned_text_paths,
    )
    positive_findings = {
        finding.key: finding.to_report()
        for finding in (
            _line_window_finding(
                source_root=source_root,
                key="rolling_cylinder_benchmark",
                relative_path="sections/singleabd.tex",
                line_start=162,
                line_end=172,
                required_snippets=("rolling cylinder",),
            ),
            _line_window_finding(
                source_root=source_root,
                key="rolling_cylinder_step_count",
                relative_path="sections/singleabd.tex",
                line_start=162,
                line_end=172,
                required_snippets=("10K",),
            ),
            _line_window_finding(
                source_root=source_root,
                key="rolling_cylinder_time_step",
                relative_path="sections/singleabd.tex",
                line_start=162,
                line_end=172,
                required_snippets=("h = 0.01~sec",),
            ),
            _line_window_finding(
                source_root=source_root,
                key="corotated_abd_timing_context",
                relative_path="sections/singleabd.tex",
                line_start=162,
                line_end=172,
                required_snippets=("co-rotated", "27~ms"),
            ),
            _line_window_finding(
                source_root=source_root,
                key="hardware_thread_context",
                relative_path="sections/singleabd.tex",
                line_start=162,
                line_end=172,
                required_snippets=("i7 CPU", "single thread"),
            ),
            _line_window_finding(
                source_root=source_root,
                key="single_body_cube_not_rolling_source_context",
                relative_path="sections/experiment.tex",
                line_start=48,
                line_end=55,
                required_snippets=("single cube", "implicit RBD baseline"),
            ),
        )
    }

    usable_parameter_disclosures = absence_findings[
        "rolling_spinning_mabd_parameter_search"
    ]["usable_parameter_disclosures"]
    missing_parameters = (
        ()
        if usable_parameter_disclosures
        else ROLLING_SPINNING_MABD_REQUIRED_SOURCE_PARAMETERS
    )
    blockers = (
        (
            "mabd_source_disclosure_found",
            "mabd_manual_source_review_required",
        )
        if usable_parameter_disclosures
        else (
            "rolling_cylinder_geometry_parameters_missing_from_public_source",
            "rolling_cylinder_initial_state_missing_from_public_source",
            "paper_mabd_affine_discretization_missing_from_public_source",
            "paper_mabd_rolling_contact_friction_missing_from_public_source",
            "paper_mabd_collision_parameters_missing_from_public_source",
        )
    )
    hash_mismatches = tuple(
        relative_path
        for relative_path, expected in ROLLING_SPINNING_MABD_AUDITED_FILE_HASHES.items()
        if file_hashes[relative_path] != expected
    )
    missing_positive_evidence = tuple(
        key for key, finding in positive_findings.items() if not finding["present"]
    )
    if hash_mismatches:
        blockers = (*blockers, "paper_source_hash_mismatch")
    if missing_positive_evidence:
        blockers = (*blockers, "paper_source_required_snippet_missing")
    status = (
        "mabd_source_mentions_require_manual_review"
        if usable_parameter_disclosures
        else (
            "mabd_source_requirements_incomplete"
            if not hash_mismatches and not missing_positive_evidence
            else "mabd_source_changed_or_required_facts_missing"
        )
    )

    return RollingSpinningMABDSourceAudit(
        source_root=str(source_root),
        file_hashes=file_hashes,
        source_tree_paths=source_tree_paths,
        scanned_text_paths=scanned_text_paths,
        scanned_tex_paths=scanned_tex_paths,
        positive_findings=positive_findings,
        absence_findings=absence_findings,
        missing_parameters=missing_parameters,
        blockers=blockers,
        status=status,
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
    "PHYSICAL_PENDULUM_AUDITED_FILE_HASHES",
    "PhysicalPendulumGeometrySourceAudit",
    "ROLLING_SPINNING_EXPLICIT_RBD_AUDITED_FILE_HASHES",
    "ROLLING_SPINNING_EXPLICIT_RBD_REQUIRED_SOURCE_PARAMETERS",
    "ROLLING_SPINNING_IMPLICIT_RBD_AUDITED_FILE_HASHES",
    "ROLLING_SPINNING_IMPLICIT_RBD_REQUIRED_SOURCE_PARAMETERS",
    "ROLLING_SPINNING_MABD_AUDITED_FILE_HASHES",
    "ROLLING_SPINNING_MABD_REQUIRED_SOURCE_PARAMETERS",
    "RollingSpinningExplicitRBDSourceAudit",
    "RollingSpinningImplicitRBDSourceAudit",
    "RollingSpinningMABDSourceAudit",
    "VelocitySemanticsSourceAudit",
    "file_sha256",
    "physical_pendulum_geometry_source_audit",
    "rolling_spinning_explicit_rbd_source_audit",
    "rolling_spinning_implicit_rbd_source_audit",
    "rolling_spinning_mabd_source_audit",
    "velocity_semantics_source_audit",
]
