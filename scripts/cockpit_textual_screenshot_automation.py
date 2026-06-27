"""Generate repeatable Cockpit Textual screenshot proof artifacts."""

from __future__ import annotations

import argparse
import asyncio
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
from typing import Any, Sequence

from PIL import Image, ImageStat

from dopemux.ui.cockpit.app import CockpitApp
from dopemux.ui.cockpit.render import viewport_supported
from dopemux.ui.cockpit.render_modes import (
    SUPPORTED_COCKPIT_MODES,
    normalize_mode,
    render_cockpit,
)


PACKET_ID = "TP-DMX-COCKPIT-TEXTUAL-SCREENSHOT-AUTOMATION-001"
DEFAULT_VIEWPORTS: tuple[tuple[int, int], ...] = ((120, 40), (100, 32), (80, 24))
DEFAULT_MODES: tuple[str, ...] = SUPPORTED_COCKPIT_MODES


@dataclass(frozen=True)
class ScreenshotArtifact:
    mode: str
    viewport: dict[str, int]
    text_path: str
    text_sha256: str
    svg_path: str
    svg_sha256: str
    raw_svg_sha256: str
    normalized_svg_sha256: str
    capture_status: str
    capture_reason: str
    raster_png_path: str | None
    raster_png_sha256: str | None
    raster_png_size: list[int] | None
    raster_png_mean_luminance: float | None
    raster_png_nonblank: bool | None
    rasterization: str
    rasterization_reason: str


def normalize_svg_for_hash(svg: str) -> str:
    """Normalize generated Textual IDs that are not meaningful screenshot content."""
    normalized = re.sub(r"terminal-[0-9]+", "terminal-ID", svg)
    return re.sub(r"clip-[0-9]+", "clip-ID", normalized)


def _sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _artifact_text(content: str) -> str:
    """Make generated proof text compatible with git diff whitespace gates."""
    return "\n".join(line.rstrip() for line in content.splitlines()).rstrip("\n") + "\n"


def _parse_viewport(raw: str) -> tuple[int, int]:
    try:
        cols_raw, rows_raw = raw.lower().split("x", maxsplit=1)
        cols = int(cols_raw)
        rows = int(rows_raw)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"viewport must use COLSxROWS syntax, got {raw!r}"
        ) from exc
    if not viewport_supported(cols, rows):
        raise argparse.ArgumentTypeError(
            f"unsupported cockpit viewport {cols}x{rows}; minimum is 80x24"
        )
    return cols, rows


def _validate_viewports(viewports: Sequence[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    validated: list[tuple[int, int]] = []
    for cols, rows in viewports:
        if not viewport_supported(cols, rows):
            raise ValueError(f"unsupported cockpit viewport: {cols}x{rows}")
        validated.append((cols, rows))
    if not validated:
        raise ValueError("at least one viewport is required")
    return tuple(validated)


async def _export_svg(mode: str, *, cols: int, rows: int) -> str:
    app = CockpitApp(mode=mode, cols=cols, rows=rows)
    async with app.run_test(size=(cols, rows)) as pilot:
        await pilot.pause()
        return app.export_screenshot()


def _rasterize_svg(svg_path: Path, png_path: Path) -> dict[str, Any]:
    png_path.unlink(missing_ok=True)
    converter = shutil.which("rsvg-convert")
    if converter is None:
        return _raster_unknown("rsvg-convert unavailable")

    result = subprocess.run(
        [converter, str(svg_path), "-o", str(png_path)],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode != 0 or not png_path.is_file():
        reason = result.stderr.strip()[:500] or f"rsvg-convert exited {result.returncode}"
        return _raster_unknown(reason)

    with Image.open(png_path) as image:
        rgb = image.convert("RGB")
        gray = image.convert("L")
        stat = ImageStat.Stat(rgb)
        mean_luminance = sum(stat.mean) / 3
        extrema = gray.getextrema()
        return {
            "raster_png_path": str(png_path),
            "raster_png_sha256": _sha256_path(png_path),
            "raster_png_size": [image.size[0], image.size[1]],
            "raster_png_mean_luminance": round(mean_luminance, 2),
            "raster_png_nonblank": bool(extrema[0] != extrema[1]),
            "rasterization": "OBSERVED",
            "rasterization_reason": "rsvg-convert produced a PNG artifact",
        }


def _raster_unknown(reason: str) -> dict[str, Any]:
    return {
        "raster_png_path": None,
        "raster_png_sha256": None,
        "raster_png_size": None,
        "raster_png_mean_luminance": None,
        "raster_png_nonblank": None,
        "rasterization": "UNKNOWN",
        "rasterization_reason": reason,
    }


def _write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Cockpit Textual Screenshot Automation Report",
        "",
        f"Packet: `{PACKET_ID}`",
        "",
        "## Verdict",
        "",
        report["verdict"],
        "",
        "## Screenshots",
        "",
        "| Mode | Viewport | SVG | Rasterization |",
        "| --- | ---: | --- | --- |",
    ]
    for item in report["screenshots"]:
        viewport = item["viewport"]
        lines.append(
            f"| {item['mode']} | {viewport['cols']}x{viewport['rows']} | "
            f"`{item['svg_path']}` | {item['rasterization']} |"
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "This report proves repeatable current-runtime Textual screenshot capture "
            "only. It does not authorize design changes, token changes, pixel parity "
            "claims, live integration, PM writes, or READY_FOR_CLAUDE_DESIGN claims.",
            "",
        ]
    )
    path.write_text(_artifact_text("\n".join(lines)), encoding="utf-8")


def generate_textual_screenshot_report(
    *,
    output_dir: Path,
    modes: Sequence[str] = DEFAULT_MODES,
    viewports: Sequence[tuple[int, int]] = DEFAULT_VIEWPORTS,
) -> dict[str, Any]:
    """Generate text, SVG, optional raster, and manifest artifacts."""
    output_dir.mkdir(parents=True, exist_ok=True)
    text_dir = output_dir / "runtime-renders"
    svg_dir = output_dir / "textual-screenshots"
    png_dir = output_dir / "raster-screenshots"
    for artifact_dir in (text_dir, svg_dir, png_dir):
        if artifact_dir.is_dir():
            shutil.rmtree(artifact_dir)
        artifact_dir.mkdir(parents=True, exist_ok=True)

    normalized_modes = tuple(normalize_mode(mode) for mode in modes)
    if not normalized_modes:
        raise ValueError("at least one mode is required")
    validated_viewports = _validate_viewports(viewports)

    screenshots: list[dict[str, Any]] = []
    for cols, rows in validated_viewports:
        for mode in normalized_modes:
            stem = f"{mode}-{cols}x{rows}"
            text_path = text_dir / f"{stem}.txt"
            svg_path = svg_dir / f"{stem}.svg"
            png_path = png_dir / f"{stem}.png"

            text = _artifact_text(render_cockpit(mode, cols=cols, rows=rows, plain=True))
            text_path.write_text(text, encoding="utf-8")
            svg = _artifact_text(asyncio.run(_export_svg(mode, cols=cols, rows=rows)))
            svg_path.write_text(svg, encoding="utf-8")
            normalized_svg_sha256 = _sha256_text(normalize_svg_for_hash(svg))
            raster = _rasterize_svg(svg_path, png_path)

            screenshots.append(
                asdict(
                    ScreenshotArtifact(
                        mode=mode,
                        viewport={"cols": cols, "rows": rows},
                        text_path=str(text_path),
                        text_sha256=_sha256_path(text_path),
                        svg_path=str(svg_path),
                        svg_sha256=normalized_svg_sha256,
                        raw_svg_sha256=_sha256_path(svg_path),
                        normalized_svg_sha256=normalized_svg_sha256,
                        capture_status="PASS",
                        capture_reason=(
                            "Textual run_test export_screenshot returned SVG"
                        ),
                        raster_png_path=raster["raster_png_path"],
                        raster_png_sha256=raster["raster_png_sha256"],
                        raster_png_size=raster["raster_png_size"],
                        raster_png_mean_luminance=raster["raster_png_mean_luminance"],
                        raster_png_nonblank=raster["raster_png_nonblank"],
                        rasterization=raster["rasterization"],
                        rasterization_reason=raster["rasterization_reason"],
                    )
                )
            )

    report: dict[str, Any] = {
        "packet_id": PACKET_ID,
        "status": "CONTINUATION_PROOF",
        "purpose": (
            "Repeatable Cockpit Textual screenshot automation for the current "
            "merged five-mode runtime continuation."
        ),
        "modes": list(normalized_modes),
        "viewports": [
            {"cols": cols, "rows": rows}
            for cols, rows in validated_viewports
        ],
        "screenshot_count": len(screenshots),
        "screenshots": screenshots,
        "verdict": (
            "PASS: current Cockpit Textual runtime screenshots were generated "
            "for the requested modes and viewports. Pixel parity, design "
            "approval, token doctrine, and live integration remain outside "
            "this packet."
        ),
        "boundaries": {
            "runtime_changes_authorized": False,
            "design_fixes_authorized": False,
            "token_doctrine_changes_authorized": False,
            "pixel_parity_claimed": False,
            "live_integration_claimed": False,
            "ready_for_claude_design_claimed": False,
        },
        "unknowns": [
            "Cross-platform terminal font/raster equivalence is not proven.",
            "Uploaded PNG pixel parity is not evaluated by this packet.",
            "Live service, PM, ConPort, and dope-memory integration are not exercised.",
            "Raster PNG proof is UNKNOWN when rsvg-convert is unavailable.",
        ],
    }

    json_path = output_dir / "TEXTUAL_SCREENSHOT_AUTOMATION_REPORT.json"
    md_path = output_dir / "TEXTUAL_SCREENSHOT_AUTOMATION_REPORT.md"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _write_markdown(report, md_path)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--mode",
        action="append",
        choices=SUPPORTED_COCKPIT_MODES,
        dest="modes",
        help="Cockpit mode to capture. May be repeated. Defaults to all modes.",
    )
    parser.add_argument(
        "--viewport",
        action="append",
        type=_parse_viewport,
        dest="viewports",
        help="Viewport in COLSxROWS form. May be repeated.",
    )
    args = parser.parse_args()
    report = generate_textual_screenshot_report(
        output_dir=args.output,
        modes=tuple(args.modes) if args.modes else DEFAULT_MODES,
        viewports=tuple(args.viewports) if args.viewports else DEFAULT_VIEWPORTS,
    )
    sys.stderr.write(
        f"wrote {report['screenshot_count']} screenshot records to {args.output}\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
