"""Digitize heavy-top reference-family curves from the recorded paper figure."""

from __future__ import annotations

import hashlib
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image

from .experiment_configs import HeavyTopRunConfig
from .reporting import ClaimReport, EvidenceStatus, write_claim_report


HEAVY_TOP_FIGURE_PDF = Path("/tmp/mabd-paper/source/images/spinning_top/spinning_top.pdf")
HEAVY_TOP_FIGURE_PDF_SHA256 = (
    "c8f5e206415b9feb3578ee32aa3b7284e2695bdd84eeb0200f3b4aa01cf3422d"
)
RENDER_DPI = 300
EXPECTED_RENDERED_SIZE_PX = (3179, 1924)
PRECESSION_BOX_PX = (1508, 72, 3154, 672)
NUTATION_BOX_PX = (1508, 1010, 3154, 1710)
REFERENCE_RGB = (32, 72, 48)
BLUE_RGB = (56, 112, 168)
ORANGE_RGB = (200, 72, 32)
RGB_DISTANCE_THRESHOLD = 70.0
MIN_SAMPLE_COVERAGE = 0.80


@dataclass(frozen=True)
class HeavyTopDigitizedCurve:
    metric: str
    unit: str
    axis_range: tuple[float, float]
    plot_box_px: tuple[int, int, int, int]
    extraction_success: bool
    sample_coverage: float
    samples: tuple[dict[str, float], ...]


@dataclass(frozen=True)
class HeavyTopFigureCurves:
    source_pdf_path: str
    source_pdf_sha256: str
    render_command: tuple[str, ...]
    renderer_version: str
    render_dpi: int
    rendered_size_px: tuple[int, int]
    sample_count: int
    reference_precession: HeavyTopDigitizedCurve
    reference_nutation: HeavyTopDigitizedCurve
    non_reference_curve_status: str
    non_reference_color_counts: dict[str, int]


def _sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _pdftocairo_version() -> str:
    result = subprocess.run(
        ["pdftocairo", "-v"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    text = (result.stderr or result.stdout).splitlines()[0].strip()
    return text.replace(" version ", " ", 1)


def _render_pdf(pdf_path: Path, output_prefix: Path) -> tuple[Image.Image, tuple[str, ...]]:
    command = (
        "pdftocairo",
        "-png",
        "-singlefile",
        "-r",
        str(RENDER_DPI),
        str(pdf_path),
        str(output_prefix),
    )
    subprocess.run(
        list(command),
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    image = Image.open(output_prefix.with_suffix(".png")).convert("RGB")
    return image, command


def _color_mask(crop: np.ndarray, rgb: tuple[int, int, int], *, threshold: float) -> np.ndarray:
    delta = crop.astype(np.int32) - np.asarray(rgb, dtype=np.int32)
    distance = np.sqrt(np.sum(delta * delta, axis=2))
    return distance <= threshold


def _axis_value_from_pixel(
    *,
    y_abs: float,
    plot_box_px: tuple[int, int, int, int],
    axis_range: tuple[float, float],
) -> float:
    _left, top, _right, bottom = plot_box_px
    axis_min, axis_max = axis_range
    fraction = (bottom - y_abs) / (bottom - top)
    return float(axis_min + fraction * (axis_max - axis_min))


def _fill_missing(values: list[float | None]) -> list[float]:
    xs = np.asarray([index for index, value in enumerate(values) if value is not None], dtype=float)
    ys = np.asarray([float(value) for value in values if value is not None], dtype=float)
    if len(xs) == 0:
        return [float("nan") for _ in values]
    if len(xs) == 1:
        return [float(ys[0]) for _ in values]
    interpolated = np.interp(np.arange(len(values), dtype=float), xs, ys)
    return [float(value) for value in interpolated]


def _digitize_curve(
    image_array: np.ndarray,
    *,
    metric: str,
    unit: str,
    plot_box_px: tuple[int, int, int, int],
    axis_range: tuple[float, float],
    sample_count: int,
) -> HeavyTopDigitizedCurve:
    left, top, right, bottom = plot_box_px
    crop = image_array[top : bottom + 1, left : right + 1, :]
    mask = _color_mask(crop, REFERENCE_RGB, threshold=RGB_DISTANCE_THRESHOLD)
    width = right - left
    times = np.linspace(0.0, 10.0, sample_count)
    raw_values: list[float | None] = []
    matched = 0

    for time_s in times:
        x_local = int(round((float(time_s) / 10.0) * width))
        y_pixels: np.ndarray | None = None
        for half_width in (3, 6, 10, 15):
            x0 = max(0, x_local - half_width)
            x1 = min(mask.shape[1] - 1, x_local + half_width)
            ys, _xs = np.nonzero(mask[:, x0 : x1 + 1])
            if len(ys) > 0:
                y_pixels = ys
                break
        if y_pixels is None:
            raw_values.append(None)
            continue
        matched += 1
        y_abs = top + float(np.median(y_pixels))
        raw_values.append(
            _axis_value_from_pixel(
                y_abs=y_abs,
                plot_box_px=plot_box_px,
                axis_range=axis_range,
            )
        )

    coverage = matched / float(sample_count)
    filled_values = _fill_missing(raw_values)
    axis_min, axis_max = axis_range
    samples = tuple(
        {
            "time_s": float(time_s),
            "value": min(axis_max, max(axis_min, float(value))),
        }
        for time_s, value in zip(times, filled_values, strict=True)
    )
    extraction_success = coverage >= MIN_SAMPLE_COVERAGE and all(
        np.isfinite(sample["value"]) for sample in samples
    )
    return HeavyTopDigitizedCurve(
        metric=metric,
        unit=unit,
        axis_range=axis_range,
        plot_box_px=plot_box_px,
        extraction_success=extraction_success,
        sample_coverage=float(coverage),
        samples=samples,
    )


def _non_reference_counts(image_array: np.ndarray) -> dict[str, int]:
    boxes = (PRECESSION_BOX_PX, NUTATION_BOX_PX)
    counts = {"blue": 0, "orange": 0}
    for left, top, right, bottom in boxes:
        crop = image_array[top : bottom + 1, left : right + 1, :]
        counts["blue"] += int(np.count_nonzero(_color_mask(crop, BLUE_RGB, threshold=90.0)))
        counts["orange"] += int(np.count_nonzero(_color_mask(crop, ORANGE_RGB, threshold=90.0)))
    return counts


def digitize_heavy_top_reference_curves(
    pdf_path: str | Path = HEAVY_TOP_FIGURE_PDF,
    *,
    sample_count: int = 101,
) -> HeavyTopFigureCurves:
    """Return calibrated green reference-family samples from the paper figure."""

    if sample_count < 2:
        raise ValueError("sample_count must be at least 2")
    source_pdf = Path(pdf_path)
    source_hash = _sha256_file(source_pdf)
    if source_hash != HEAVY_TOP_FIGURE_PDF_SHA256:
        raise ValueError(f"unexpected heavy-top figure sha256: {source_hash}")
    renderer_version = _pdftocairo_version()
    with tempfile.TemporaryDirectory() as tmpdir:
        image, command = _render_pdf(source_pdf, Path(tmpdir) / "spinning_top")
        if image.size != EXPECTED_RENDERED_SIZE_PX:
            raise ValueError(f"unexpected rendered size: {image.size}")
        image_array = np.asarray(image)
        precession = _digitize_curve(
            image_array,
            metric="precession_velocity_rad_s",
            unit="rad/s",
            plot_box_px=PRECESSION_BOX_PX,
            axis_range=(0.0, 8.0),
            sample_count=sample_count,
        )
        nutation = _digitize_curve(
            image_array,
            metric="nutation_angle_deg",
            unit="deg",
            plot_box_px=NUTATION_BOX_PX,
            axis_range=(5.0, 30.0),
            sample_count=sample_count,
        )
        counts = _non_reference_counts(image_array)

    return HeavyTopFigureCurves(
        source_pdf_path=source_pdf.as_posix(),
        source_pdf_sha256=source_hash,
        render_command=command,
        renderer_version=renderer_version,
        render_dpi=RENDER_DPI,
        rendered_size_px=EXPECTED_RENDERED_SIZE_PX,
        sample_count=sample_count,
        reference_precession=precession,
        reference_nutation=nutation,
        non_reference_curve_status="color_family_counts_only",
        non_reference_color_counts=counts,
    )


def _curve_to_report_mapping(curve: HeavyTopDigitizedCurve) -> dict[str, object]:
    return {
        "metric": curve.metric,
        "unit": curve.unit,
        "axis_range": list(curve.axis_range),
        "plot_box_px": list(curve.plot_box_px),
        "extraction_success": curve.extraction_success,
        "sample_coverage": curve.sample_coverage,
        "samples": [dict(sample) for sample in curve.samples],
    }


def write_heavy_top_figure_curve_report(
    path: str | Path,
    *,
    config: HeavyTopRunConfig,
    source_commit: str,
    vendored_newton_commit: str,
    paper_source_version: str = "2603.08079v2",
    sample_count: int = 101,
) -> ClaimReport:
    curves = digitize_heavy_top_reference_curves(sample_count=sample_count)
    reference_available = (
        curves.reference_precession.extraction_success
        and curves.reference_nutation.extraction_success
    )
    limitations = [
        "not_authors_raw_data",
        "no_blue_orange_line_style_split",
        "no_curve_agreement_gate",
        "no_runtime_timing_evidence",
    ]
    observed = {
        "lane_status": (
            "reference_curves_digitized"
            if reference_available
            else "reference_curve_digitization_incomplete"
        ),
        "full_experiment_claim_passed": False,
        "reference_curve_available": reference_available,
        "source_pdf_path": curves.source_pdf_path,
        "source_pdf_sha256": curves.source_pdf_sha256,
        "render_command": list(curves.render_command),
        "renderer_version": curves.renderer_version,
        "render_dpi": curves.render_dpi,
        "rendered_size_px": list(curves.rendered_size_px),
        "sample_count": curves.sample_count,
        "reference_curves": {
            "reference_precession": _curve_to_report_mapping(curves.reference_precession),
            "reference_nutation": _curve_to_report_mapping(curves.reference_nutation),
        },
        "non_reference_curve_status": curves.non_reference_curve_status,
        "non_reference_color_counts": dict(curves.non_reference_color_counts),
        "limitations": limitations,
        "blocking_reasons": [
            "raw_heavy_top_reference_curve_data_missing",
            "heavy_top_digitized_figure_curve_agreement_not_passed",
            "heavy_top_comparison_report_incomplete",
            "heavy_top_timing_evidence_missing",
            "heavy_top_comparison_pass_gate_not_enabled",
        ],
    }
    report = ClaimReport(
        claim_id=config.claim_id,
        scene_id=config.scene_id,
        asset_hashes={"spinning_top_pdf": HEAVY_TOP_FIGURE_PDF_SHA256},
        solver_mode="heavy_top_paper_figure_digitization",
        backend="pdftocairo_pillow",
        baseline_lane="paper_figure_digitization",
        expected={
            "source_lines": list(config.source_lines),
            "paper_values": config.paper_values,
            "figure_pdf_sha256": HEAVY_TOP_FIGURE_PDF_SHA256,
            "renderer_version": "pdftocairo 22.02.0",
            "rendered_size_px": list(EXPECTED_RENDERED_SIZE_PX),
            "digitized_source_scope": "paper_figure_reference_family_only",
            "known_source_gaps": [
                "raw_heavy_top_reference_curve_data_missing",
                "exact_heavy_top_inertia_unknown",
                "exact_heavy_top_geometry_unknown",
            ],
            "limitations": limitations,
            "full_experiment_claim_passed": False,
        },
        observed=observed,
        threshold={"min_sample_coverage": MIN_SAMPLE_COVERAGE},
        unit="digitized_curve_samples",
        status=EvidenceStatus.INCOMPLETE,
        failure_reason=(
            "heavy-top paper figure reference-family samples were digitized, but "
            "authors' raw curve data, curve agreement, paper-faithful geometry/inertia, "
            "timing evidence, and the comparison pass gate remain missing"
        ),
        timing_distribution={"status": "not_measured", "paper_comparable": False},
        raw_outputs={"reference_samples": "compact_numeric_samples_only"},
        plot_paths={},
        source_commit=source_commit,
        vendored_newton_commit=vendored_newton_commit,
        paper_source_version=paper_source_version,
    )
    write_claim_report(report, path)
    return report


__all__ = [
    "EXPECTED_RENDERED_SIZE_PX",
    "HEAVY_TOP_FIGURE_PDF",
    "HEAVY_TOP_FIGURE_PDF_SHA256",
    "HeavyTopDigitizedCurve",
    "HeavyTopFigureCurves",
    "RENDER_DPI",
    "digitize_heavy_top_reference_curves",
    "write_heavy_top_figure_curve_report",
]
