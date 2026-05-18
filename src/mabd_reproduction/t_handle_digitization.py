"""Digitize T-handle color-family curves from the recorded paper figure."""

from __future__ import annotations

import hashlib
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image

from .experiment_configs import THandleRunConfig
from .reporting import ClaimReport, EvidenceStatus, write_claim_report


T_HANDLE_FIGURE_PDF = Path("/tmp/mabd-paper/source/images/T-handle/T-handle.pdf")
T_HANDLE_FIGURE_PDF_SHA256 = (
    "5ae6464fd7e7e6fd471ad56e67cdbead6014736cb731a232ce29d80630a72c1c"
)
RENDER_DPI = 300
EXPECTED_RENDERED_SIZE_PX = (3861, 1541)
ANGULAR_VELOCITY_BOX_PX = (326, 410, 1858, 1260)
ENERGY_LOSS_BOX_PX = (2204, 410, 3788, 1262)
COLOR_FAMILIES_RGB = {
    "blue": (56, 112, 168),
    "orange": (200, 72, 32),
    "green": (32, 72, 48),
}
RGB_DISTANCE_THRESHOLD = 45.0
MIN_SAMPLE_COVERAGE = 0.80


@dataclass(frozen=True)
class THandleDigitizedCurve:
    metric: str
    color_family: str
    unit: str
    axis_range: tuple[float, float]
    plot_box_px: tuple[int, int, int, int]
    extraction_success: bool
    sample_coverage: float
    curve_identity_status: str
    samples: tuple[dict[str, float], ...]


@dataclass(frozen=True)
class THandleFigureCurves:
    source_pdf_path: str
    source_pdf_sha256: str
    render_command: tuple[str, ...]
    renderer_version: str
    render_dpi: int
    rendered_size_px: tuple[int, int]
    sample_count: int
    figure_curve_scope: str
    angular_velocity_curves: dict[str, THandleDigitizedCurve]
    energy_loss_curves: dict[str, THandleDigitizedCurve]


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
    color_family: str,
    rgb: tuple[int, int, int],
    unit: str,
    plot_box_px: tuple[int, int, int, int],
    axis_range: tuple[float, float],
    sample_count: int,
) -> THandleDigitizedCurve:
    left, top, right, bottom = plot_box_px
    crop = image_array[top : bottom + 1, left : right + 1, :]
    mask = _color_mask(crop, rgb, threshold=RGB_DISTANCE_THRESHOLD)
    width = right - left
    times = np.linspace(0.0, 100.0, sample_count)
    raw_values: list[float | None] = []
    matched = 0

    for time_s in times:
        x_local = int(round((float(time_s) / 100.0) * width))
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
    return THandleDigitizedCurve(
        metric=metric,
        color_family=color_family,
        unit=unit,
        axis_range=axis_range,
        plot_box_px=plot_box_px,
        extraction_success=extraction_success,
        sample_coverage=float(coverage),
        curve_identity_status="color_family_not_legend_entry",
        samples=samples,
    )


def _digitize_color_families(
    image_array: np.ndarray,
    *,
    metric: str,
    unit: str,
    plot_box_px: tuple[int, int, int, int],
    axis_range: tuple[float, float],
    sample_count: int,
) -> dict[str, THandleDigitizedCurve]:
    return {
        color_family: _digitize_curve(
            image_array,
            metric=metric,
            color_family=color_family,
            rgb=rgb,
            unit=unit,
            plot_box_px=plot_box_px,
            axis_range=axis_range,
            sample_count=sample_count,
        )
        for color_family, rgb in COLOR_FAMILIES_RGB.items()
    }


def digitize_t_handle_figure_curves(
    pdf_path: str | Path = T_HANDLE_FIGURE_PDF,
    *,
    sample_count: int = 101,
) -> THandleFigureCurves:
    """Return calibrated color-family samples from the T-handle paper figure."""

    if sample_count < 2:
        raise ValueError("sample_count must be at least 2")
    source_pdf = Path(pdf_path)
    source_hash = _sha256_file(source_pdf)
    if source_hash != T_HANDLE_FIGURE_PDF_SHA256:
        raise ValueError(f"unexpected T-handle figure sha256: {source_hash}")
    renderer_version = _pdftocairo_version()
    with tempfile.TemporaryDirectory() as tmpdir:
        image, command = _render_pdf(source_pdf, Path(tmpdir) / "t_handle")
        if image.size != EXPECTED_RENDERED_SIZE_PX:
            raise ValueError(f"unexpected rendered size: {image.size}")
        image_array = np.asarray(image)
        angular_velocity_curves = _digitize_color_families(
            image_array,
            metric="omega_intermediate_rad_s",
            unit="rad/s",
            plot_box_px=ANGULAR_VELOCITY_BOX_PX,
            axis_range=(-2.0, 6.0),
            sample_count=sample_count,
        )
        energy_loss_curves = _digitize_color_families(
            image_array,
            metric="relative_energy_loss",
            unit="ratio",
            plot_box_px=ENERGY_LOSS_BOX_PX,
            axis_range=(0.0, 0.25),
            sample_count=sample_count,
        )

    return THandleFigureCurves(
        source_pdf_path=source_pdf.as_posix(),
        source_pdf_sha256=source_hash,
        render_command=command,
        renderer_version=renderer_version,
        render_dpi=RENDER_DPI,
        rendered_size_px=EXPECTED_RENDERED_SIZE_PX,
        sample_count=sample_count,
        figure_curve_scope="color_family_digitization_only",
        angular_velocity_curves=angular_velocity_curves,
        energy_loss_curves=energy_loss_curves,
    )


def _curve_to_report_mapping(curve: THandleDigitizedCurve) -> dict[str, object]:
    return {
        "metric": curve.metric,
        "color_family": curve.color_family,
        "unit": curve.unit,
        "axis_range": list(curve.axis_range),
        "plot_box_px": list(curve.plot_box_px),
        "extraction_success": curve.extraction_success,
        "sample_coverage": curve.sample_coverage,
        "curve_identity_status": curve.curve_identity_status,
        "samples": [dict(sample) for sample in curve.samples],
    }


def _curves_to_report_mapping(
    curves: dict[str, THandleDigitizedCurve],
) -> dict[str, dict[str, object]]:
    return {
        color_family: _curve_to_report_mapping(curve)
        for color_family, curve in curves.items()
    }


def write_t_handle_figure_curve_report(
    path: str | Path,
    *,
    config: THandleRunConfig,
    source_commit: str,
    vendored_newton_commit: str,
    paper_source_version: str = "2603.08079v2",
    sample_count: int = 101,
) -> ClaimReport:
    curves = digitize_t_handle_figure_curves(sample_count=sample_count)
    reference_available = all(
        curve.extraction_success
        for curve in (
            *curves.angular_velocity_curves.values(),
            *curves.energy_loss_curves.values(),
        )
    )
    limitations = [
        "not_authors_raw_data",
        "no_solid_dashed_line_style_split",
        "no_curve_identity_claim",
        "no_curve_agreement_gate",
        "no_runtime_timing_evidence",
    ]
    observed = {
        "lane_status": (
            "figure_color_families_digitized"
            if reference_available
            else "figure_color_family_digitization_incomplete"
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
        "figure_curve_scope": curves.figure_curve_scope,
        "angular_velocity_curves": _curves_to_report_mapping(curves.angular_velocity_curves),
        "energy_loss_curves": _curves_to_report_mapping(curves.energy_loss_curves),
        "limitations": limitations,
        "blocking_reasons": [
            "raw_t_handle_reference_curve_data_missing",
            "t_handle_digitized_figure_curve_agreement_not_passed",
            "t_handle_comparison_report_incomplete",
            "t_handle_timing_evidence_missing",
        ],
    }
    report = ClaimReport(
        claim_id=config.claim_id,
        scene_id=config.scene_id,
        asset_hashes={"t_handle_pdf": T_HANDLE_FIGURE_PDF_SHA256},
        solver_mode="t_handle_paper_figure_digitization",
        backend="pdftocairo_pillow",
        baseline_lane="paper_figure_digitization",
        expected={
            "source_lines": list(config.source_lines),
            "paper_values": config.paper_values,
            "figure_pdf_sha256": T_HANDLE_FIGURE_PDF_SHA256,
            "renderer_version": "pdftocairo 22.02.0",
            "rendered_size_px": list(EXPECTED_RENDERED_SIZE_PX),
            "digitized_source_scope": "paper_figure_color_families_only",
            "known_source_gaps": [
                "raw_t_handle_reference_curve_data_missing",
                "exact_t_handle_geometry_unknown",
                "no_solid_dashed_line_style_split",
                "no_curve_identity_claim",
            ],
            "limitations": limitations,
            "full_experiment_claim_passed": False,
        },
        observed=observed,
        threshold={
            "min_sample_coverage": MIN_SAMPLE_COVERAGE,
            "rgb_distance_threshold": RGB_DISTANCE_THRESHOLD,
        },
        unit="digitized_curve_samples",
        status=EvidenceStatus.INCOMPLETE,
        failure_reason=(
            "T-handle paper figure color-family samples were digitized, but authors' "
            "raw curve data, solid/dashed line separation, curve identity, curve "
            "agreement, timing evidence, and the comparison pass gate remain missing"
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
    "COLOR_FAMILIES_RGB",
    "ENERGY_LOSS_BOX_PX",
    "EXPECTED_RENDERED_SIZE_PX",
    "MIN_SAMPLE_COVERAGE",
    "RENDER_DPI",
    "RGB_DISTANCE_THRESHOLD",
    "T_HANDLE_FIGURE_PDF",
    "T_HANDLE_FIGURE_PDF_SHA256",
    "THandleDigitizedCurve",
    "THandleFigureCurves",
    "digitize_t_handle_figure_curves",
    "write_t_handle_figure_curve_report",
]
