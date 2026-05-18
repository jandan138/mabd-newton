"""Digitize spinning-box color-family curves from the recorded paper figure."""

from __future__ import annotations

import hashlib
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image

from .experiment_configs import SpinningBoxRunConfig
from .reporting import ClaimReport, EvidenceStatus, write_claim_report


SPINNING_BOX_FIGURE_PDF = Path("/tmp/mabd-paper/source/images/cube/roll_cube.pdf")
SPINNING_BOX_FIGURE_PDF_SHA256 = (
    "7669b062348324a3b0090cc9f44930655c83233a87f63389db9198b88f95ae80"
)
RENDER_DPI = 300
EXPECTED_RENDERED_SIZE_PX = (3570, 2187)
ANGULAR_MOMENTUM_BOX_PX = (394, 1139, 1751, 1956)
LINEAR_MOMENTUM_BOX_PX = (2142, 1139, 3528, 1956)
COLOR_FAMILIES_RGB = {
    "blue": (56, 112, 168),
    "orange": (200, 72, 32),
    "green": (32, 72, 48),
    "gray": (176, 160, 144),
    "brown": (160, 144, 128),
}
RGB_DISTANCE_THRESHOLD = 55.0
MIN_SAMPLE_COVERAGE = 0.80
TIME_AXIS_RANGE_S = (0.0, 10.0)
MOMENTUM_AXIS_RANGE = (95.0, 100.0)
FIGURE_CURVE_SCOPE = "paper_roll_cube_color_family_digitization"
COLOR_ASSIGNMENT_POLICY = "nearest_color_family_within_threshold"
CURVE_IDENTITY_STATUS = "color_family_not_legend_entry"
CURVE_AGREEMENT_STATUS = "not_evaluated"
BLOCKING_REASONS = [
    "spinning_box_figure_curve_agreement_not_evaluated",
    "spinning_box_reference_legend_identity_not_evaluated",
    "spinning_box_line_style_split_not_evaluated",
    "mabd_newton_report_incomplete",
    "spinning_box_comparison_pass_gate_not_enabled",
]


@dataclass(frozen=True)
class SpinningBoxDigitizedCurve:
    metric: str
    color_family: str
    unit: str
    axis_range: tuple[float, float]
    plot_box_px: tuple[int, int, int, int]
    extraction_success: bool
    sample_coverage: float
    matched_sample_count: int
    interpolated_sample_count: int
    longest_missing_run: int
    source_pixel_count: int
    curve_identity_status: str
    samples: tuple[dict[str, float], ...]


@dataclass(frozen=True)
class SpinningBoxFigureCurves:
    source_pdf_path: str
    source_pdf_sha256: str
    render_command: tuple[str, ...]
    renderer_version: str
    render_dpi: int
    rendered_size_px: tuple[int, int]
    rendered_image_sha256: str
    sample_count: int
    figure_curve_scope: str
    color_family_curve_available: bool
    paper_reference_legend_identity_available: bool
    color_assignment_policy: str
    curve_identity_status: str
    curve_agreement_status: str
    angular_momentum_curves: dict[str, SpinningBoxDigitizedCurve]
    linear_momentum_curves: dict[str, SpinningBoxDigitizedCurve]


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


def _render_pdf(pdf_path: Path, output_prefix: Path) -> tuple[Image.Image, tuple[str, ...], str]:
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
    png_path = output_prefix.with_suffix(".png")
    rendered_hash = _sha256_file(png_path)
    image = Image.open(png_path).convert("RGB")
    recorded_command = (*command[:-1], "temporary_output_prefix")
    return image, recorded_command, rendered_hash


def _color_family_masks(crop: np.ndarray) -> dict[str, np.ndarray]:
    names = tuple(COLOR_FAMILIES_RGB)
    centers = np.asarray([COLOR_FAMILIES_RGB[name] for name in names], dtype=np.int32)
    delta = crop.astype(np.int32)[:, :, None, :] - centers[None, None, :, :]
    distance = np.sqrt(np.sum(delta * delta, axis=3))
    nearest = np.argmin(distance, axis=2)
    nearest_distance = np.min(distance, axis=2)
    return {
        name: (nearest == index) & (nearest_distance <= RGB_DISTANCE_THRESHOLD)
        for index, name in enumerate(names)
    }


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


def _longest_missing_run(values: list[float | None]) -> int:
    longest = 0
    current = 0
    for value in values:
        if value is None:
            current += 1
            longest = max(longest, current)
        else:
            current = 0
    return longest


def _digitize_curve(
    mask: np.ndarray,
    *,
    metric: str,
    color_family: str,
    unit: str,
    plot_box_px: tuple[int, int, int, int],
    axis_range: tuple[float, float],
    sample_count: int,
) -> SpinningBoxDigitizedCurve:
    left, top, right, bottom = plot_box_px
    width = right - left
    times = np.linspace(TIME_AXIS_RANGE_S[0], TIME_AXIS_RANGE_S[1], sample_count)
    raw_values: list[float | None] = []
    matched = 0

    for time_s in times:
        x_local = int(round((float(time_s) / TIME_AXIS_RANGE_S[1]) * width))
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
    interpolated_sample_count = sum(value is None for value in raw_values)
    longest_missing_run = _longest_missing_run(raw_values)
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
    return SpinningBoxDigitizedCurve(
        metric=metric,
        color_family=color_family,
        unit=unit,
        axis_range=axis_range,
        plot_box_px=plot_box_px,
        extraction_success=extraction_success,
        sample_coverage=float(coverage),
        matched_sample_count=matched,
        interpolated_sample_count=interpolated_sample_count,
        longest_missing_run=longest_missing_run,
        source_pixel_count=int(np.count_nonzero(mask)),
        curve_identity_status=CURVE_IDENTITY_STATUS,
        samples=samples,
    )


def _digitize_color_families(
    image_array: np.ndarray,
    *,
    metric: str,
    unit: str,
    plot_box_px: tuple[int, int, int, int],
    sample_count: int,
) -> dict[str, SpinningBoxDigitizedCurve]:
    left, top, right, bottom = plot_box_px
    crop = image_array[top : bottom + 1, left : right + 1, :]
    masks = _color_family_masks(crop)
    return {
        color_family: _digitize_curve(
            masks[color_family],
            metric=metric,
            color_family=color_family,
            unit=unit,
            plot_box_px=plot_box_px,
            axis_range=MOMENTUM_AXIS_RANGE,
            sample_count=sample_count,
        )
        for color_family in COLOR_FAMILIES_RGB
    }


def digitize_spinning_box_figure_curves(
    pdf_path: str | Path = SPINNING_BOX_FIGURE_PDF,
    *,
    sample_count: int = 101,
) -> SpinningBoxFigureCurves:
    """Return calibrated color-family samples from the spinning-box paper figure."""

    if sample_count < 2:
        raise ValueError("sample_count must be at least 2")
    source_pdf = Path(pdf_path)
    source_hash = _sha256_file(source_pdf)
    if source_hash != SPINNING_BOX_FIGURE_PDF_SHA256:
        raise ValueError(f"unexpected spinning-box figure sha256: {source_hash}")
    renderer_version = _pdftocairo_version()
    with tempfile.TemporaryDirectory() as tmpdir:
        image, command, rendered_image_sha256 = _render_pdf(
            source_pdf,
            Path(tmpdir) / "roll_cube",
        )
        if image.size != EXPECTED_RENDERED_SIZE_PX:
            raise ValueError(f"unexpected rendered size: {image.size}")
        image_array = np.asarray(image)
        angular_momentum_curves = _digitize_color_families(
            image_array,
            metric="angular_momentum",
            unit="paper_plot_units",
            plot_box_px=ANGULAR_MOMENTUM_BOX_PX,
            sample_count=sample_count,
        )
        linear_momentum_curves = _digitize_color_families(
            image_array,
            metric="linear_momentum",
            unit="paper_plot_units",
            plot_box_px=LINEAR_MOMENTUM_BOX_PX,
            sample_count=sample_count,
        )

    color_family_curve_available = all(
        curve.extraction_success
        for curve in (*angular_momentum_curves.values(), *linear_momentum_curves.values())
    )
    return SpinningBoxFigureCurves(
        source_pdf_path=source_pdf.as_posix(),
        source_pdf_sha256=source_hash,
        render_command=command,
        renderer_version=renderer_version,
        render_dpi=RENDER_DPI,
        rendered_size_px=EXPECTED_RENDERED_SIZE_PX,
        rendered_image_sha256=rendered_image_sha256,
        sample_count=sample_count,
        figure_curve_scope=FIGURE_CURVE_SCOPE,
        color_family_curve_available=color_family_curve_available,
        paper_reference_legend_identity_available=False,
        color_assignment_policy=COLOR_ASSIGNMENT_POLICY,
        curve_identity_status=CURVE_IDENTITY_STATUS,
        curve_agreement_status=CURVE_AGREEMENT_STATUS,
        angular_momentum_curves=angular_momentum_curves,
        linear_momentum_curves=linear_momentum_curves,
    )


def _curve_to_report_mapping(curve: SpinningBoxDigitizedCurve) -> dict[str, object]:
    return {
        "metric": curve.metric,
        "color_family": curve.color_family,
        "unit": curve.unit,
        "axis_range": list(curve.axis_range),
        "plot_box_px": list(curve.plot_box_px),
        "extraction_success": curve.extraction_success,
        "sample_coverage": curve.sample_coverage,
        "matched_sample_count": curve.matched_sample_count,
        "interpolated_sample_count": curve.interpolated_sample_count,
        "longest_missing_run": curve.longest_missing_run,
        "source_pixel_count": curve.source_pixel_count,
        "curve_identity_status": curve.curve_identity_status,
        "samples": [dict(sample) for sample in curve.samples],
    }


def _curves_to_report_mapping(
    curves: dict[str, SpinningBoxDigitizedCurve],
) -> dict[str, dict[str, object]]:
    return {
        color_family: _curve_to_report_mapping(curve)
        for color_family, curve in curves.items()
    }


def write_spinning_box_figure_curve_report(
    path: str | Path,
    *,
    config: SpinningBoxRunConfig,
    source_commit: str,
    vendored_newton_commit: str,
    paper_source_version: str = "2603.08079v2",
    sample_count: int = 101,
) -> ClaimReport:
    curves = digitize_spinning_box_figure_curves(sample_count=sample_count)
    expected = {
        "source_lines": list(config.source_lines),
        "paper_values": config.paper_values,
        "figure_pdf_sha256": SPINNING_BOX_FIGURE_PDF_SHA256,
        "renderer_version": "pdftocairo 22.02.0",
        "rendered_size_px": list(EXPECTED_RENDERED_SIZE_PX),
        "digitized_source_scope": FIGURE_CURVE_SCOPE,
        "known_source_gaps": [
            "not_authors_raw_data",
            "no_curve_identity_claim",
            "no_curve_agreement_gate",
            "no_runtime_timing_evidence",
        ],
        "full_experiment_claim_passed": False,
    }
    observed = {
        "lane_status": (
            "figure_color_families_digitized"
            if curves.color_family_curve_available
            else "figure_color_family_digitization_incomplete"
        ),
        "full_experiment_claim_passed": False,
        "figure_curve_scope": curves.figure_curve_scope,
        "source_pdf_path": curves.source_pdf_path,
        "source_pdf_sha256": curves.source_pdf_sha256,
        "render_command": list(curves.render_command),
        "renderer_version": curves.renderer_version,
        "render_dpi": curves.render_dpi,
        "rendered_size_px": list(curves.rendered_size_px),
        "rendered_image_sha256": curves.rendered_image_sha256,
        "sample_count": curves.sample_count,
        "color_family_curve_available": curves.color_family_curve_available,
        "paper_reference_legend_identity_available": (
            curves.paper_reference_legend_identity_available
        ),
        "color_assignment_policy": curves.color_assignment_policy,
        "curve_identity_status": curves.curve_identity_status,
        "curve_agreement_status": curves.curve_agreement_status,
        "angular_momentum_curves": _curves_to_report_mapping(curves.angular_momentum_curves),
        "linear_momentum_curves": _curves_to_report_mapping(curves.linear_momentum_curves),
        "blocking_reasons": list(BLOCKING_REASONS),
    }
    report = ClaimReport(
        claim_id=config.claim_id,
        scene_id=config.scene_id,
        asset_hashes={"spinning_box_roll_cube_pdf": SPINNING_BOX_FIGURE_PDF_SHA256},
        solver_mode="spinning_box_paper_figure_curve_digitization",
        backend="paper_pdf_digitization",
        baseline_lane="paper_figure_digitization",
        expected=expected,
        observed=observed,
        threshold={
            "min_sample_coverage": MIN_SAMPLE_COVERAGE,
            "rgb_distance_threshold": RGB_DISTANCE_THRESHOLD,
        },
        unit="digitized_curve_samples",
        status=EvidenceStatus.INCOMPLETE,
        failure_reason=(
            "Spinning-box paper figure color-family samples were digitized, but curve "
            "identity, curve agreement, solver agreement, timing evidence, and the "
            "comparison pass gate remain missing"
        ),
        timing_distribution={"status": "not_measured", "paper_comparable": False},
        raw_outputs={"figure_samples": "compact_numeric_samples_only"},
        plot_paths={},
        source_commit=source_commit,
        vendored_newton_commit=vendored_newton_commit,
        paper_source_version=paper_source_version,
    )
    write_claim_report(report, path)
    return report


__all__ = [
    "ANGULAR_MOMENTUM_BOX_PX",
    "BLOCKING_REASONS",
    "COLOR_ASSIGNMENT_POLICY",
    "COLOR_FAMILIES_RGB",
    "CURVE_AGREEMENT_STATUS",
    "CURVE_IDENTITY_STATUS",
    "EXPECTED_RENDERED_SIZE_PX",
    "FIGURE_CURVE_SCOPE",
    "LINEAR_MOMENTUM_BOX_PX",
    "MIN_SAMPLE_COVERAGE",
    "MOMENTUM_AXIS_RANGE",
    "RENDER_DPI",
    "RGB_DISTANCE_THRESHOLD",
    "SPINNING_BOX_FIGURE_PDF",
    "SPINNING_BOX_FIGURE_PDF_SHA256",
    "SpinningBoxDigitizedCurve",
    "SpinningBoxFigureCurves",
    "digitize_spinning_box_figure_curves",
    "write_spinning_box_figure_curve_report",
]
