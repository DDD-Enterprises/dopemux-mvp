"""Generate Cockpit pixel parity proof artifacts."""

from __future__ import annotations

import argparse
import asyncio
from dataclasses import asdict
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from typing import Any

from PIL import Image, ImageStat

from dopemux.ui.cockpit.app import CockpitApp
from dopemux.ui.cockpit.render_modes import render_cockpit


PACKET_ID = "TP-DMX-COCKPIT-PIXEL-PARITY-PROOF-001"
CLASSIFICATIONS: tuple[str, ...] = (
    "MATCH",
    "ACCEPTABLE_DELTA",
    "DESIGN_DRIFT",
    "RUNTIME_BUG",
    "SPEC_AMBIGUITY",
    "UNKNOWN",
)
COCKPIT_REFERENCE_MODES: tuple[str, ...] = (
    "pm",
    "implementer",
    "overview",
    "services",
    "events",
)


@dataclass(frozen=True)
class ReferenceImageClassification:
    path: str
    width: int
    height: int
    mode: str
    mean_luminance: float
    category: str
    classification: str
    pixel_certainty: str
    rationale: str


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def classify_reference_image(path: Path) -> ReferenceImageClassification:
    with Image.open(path) as image:
        rgb = image.convert("RGB")
        stat = ImageStat.Stat(rgb)
        mean_luminance = sum(stat.mean) / 3
        width, height = image.size
        mode = image.mode

    if mean_luminance >= 180:
        category = "non_runtime_setup_form_reference"
        classification = "SPEC_AMBIGUITY"
        rationale = (
            "Uploaded PNG is bright and visually distinct from the dark Cockpit runtime "
            "reference set; treat as reference-set ambiguity, not runtime failure."
        )
    else:
        category = "dark_cockpit_reference"
        classification = "DESIGN_DRIFT"
        rationale = (
            "Uploaded PNG is a dark Cockpit/RTE-style reference. Current runtime export "
            "is the merged five-mode static continuation surface, so exact pixel parity "
            "is not proven and visual drift must be reported rather than fixed here."
        )

    return ReferenceImageClassification(
        path=str(path),
        width=width,
        height=height,
        mode=mode,
        mean_luminance=round(mean_luminance, 2),
        category=category,
        classification=classification,
        pixel_certainty="UNKNOWN",
        rationale=rationale,
    )


async def _export_svg(mode: str, *, cols: int, rows: int) -> str:
    app = CockpitApp(mode=mode, cols=cols, rows=rows)
    async with app.run_test(size=(cols, rows)) as pilot:
        await pilot.pause()
        return app.export_screenshot()


def _write_runtime_artifacts(output_dir: Path) -> list[dict[str, Any]]:
    render_dir = output_dir / "runtime-renders"
    screenshot_dir = output_dir / "runtime-screenshots"
    render_dir.mkdir(parents=True, exist_ok=True)
    screenshot_dir.mkdir(parents=True, exist_ok=True)

    artifacts: list[dict[str, Any]] = []
    for mode in COCKPIT_REFERENCE_MODES:
        text_path = render_dir / f"{mode}.txt"
        svg_path = screenshot_dir / f"{mode}.svg"
        text = render_cockpit(mode, cols=120, rows=40, plain=True)
        text_path.write_text(text + "\n", encoding="utf-8")
        svg = asyncio.run(_export_svg(mode, cols=120, rows=40))
        svg_path.write_text(svg, encoding="utf-8")
        record: dict[str, Any] = {
            "mode": mode,
            "text_path": str(text_path),
            "text_sha256": _sha256(text_path),
            "svg_path": str(svg_path),
            "svg_sha256": _sha256(svg_path),
            "classification": "UNKNOWN",
            "classification_reason": (
                "Runtime artifact was generated for proof comparison, but uploaded PNG "
                "viewport/font/source equivalence is not established in this packet."
            ),
        }
        raster_path = _rasterize_svg(svg_path)
        if raster_path is None:
            record["raster_png_path"] = None
            record["rasterization"] = "UNKNOWN"
            record["rasterization_reason"] = "rsvg-convert unavailable or failed"
        else:
            with Image.open(raster_path) as image:
                record["raster_png_path"] = str(raster_path)
                record["raster_png_sha256"] = _sha256(raster_path)
                record["raster_png_size"] = [image.size[0], image.size[1]]
                record["rasterization"] = "OBSERVED"
        artifacts.append(record)
    return artifacts


def _rasterize_svg(svg_path: Path) -> Path | None:
    converter = shutil.which("rsvg-convert")
    if converter is None:
        return None
    png_path = svg_path.with_suffix(".png")
    result = subprocess.run(
        [converter, str(svg_path), "-o", str(png_path)],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode != 0 or not png_path.is_file():
        return None
    return png_path


def _write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Cockpit Pixel Parity Report",
        "",
        f"Packet: `{PACKET_ID}`",
        "",
        "## Verdict",
        "",
        report["verdict"],
        "",
        "## Reference Classifications",
        "",
        "| Reference | Size | Luminance | Classification | Pixel Certainty |",
        "| --- | ---: | ---: | --- | --- |",
    ]
    for item in report["reference_images"]:
        lines.append(
            "| "
            + Path(item["path"]).name
            + f" | {item['width']}x{item['height']} | {item['mean_luminance']} | "
            + f"{item['classification']} | {item['pixel_certainty']} |"
        )
    lines.extend(
        [
            "",
            "## Runtime Artifacts",
            "",
            "| Mode | Text | SVG | Rasterization |",
            "| --- | --- | --- | --- |",
        ]
    )
    for item in report["runtime_artifacts"]:
        lines.append(
            f"| {item['mode']} | `{item['text_path']}` | `{item['svg_path']}` | "
            f"{item['rasterization']} |"
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "This report does not authorize design changes, token changes, live integration, "
            "or READY_FOR_CLAUDE_DESIGN claims.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def generate_pixel_parity_report(*, upload_dir: Path, output_dir: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    reference_images = [
        classify_reference_image(path)
        for path in sorted(upload_dir.glob("*.png"))
    ]
    runtime_artifacts = _write_runtime_artifacts(output_dir)

    report = {
        "packet_id": PACKET_ID,
        "status": "CONTINUATION_PROOF",
        "classification_vocab": list(CLASSIFICATIONS),
        "runtime_modes": list(COCKPIT_REFERENCE_MODES),
        "upload_dir": str(upload_dir),
        "reference_images": [asdict(item) for item in reference_images],
        "runtime_artifacts": runtime_artifacts,
        "verdict": (
            "DESIGN_DRIFT observed for dark uploaded Cockpit/RTE references; "
            "SPEC_AMBIGUITY observed for the setup-form reference; true pixel "
            "MATCH is UNKNOWN because viewport/font/source equivalence is not proven."
        ),
        "boundaries": {
            "runtime_changes_authorized": False,
            "design_fixes_authorized": False,
            "token_doctrine_changes_authorized": False,
            "live_integration_claimed": False,
            "ready_for_claude_design_claimed": False,
        },
    }
    json_path = output_dir / "PIXEL_PARITY_REPORT.json"
    md_path = output_dir / "PIXEL_PARITY_REPORT.md"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _write_markdown(report, md_path)
    return report


def write_pixel_parity_report(*, upload_dir: Path, output_dir: Path) -> dict[str, Any]:
    return generate_pixel_parity_report(upload_dir=upload_dir, output_dir=output_dir)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--upload-dir",
        type=Path,
        default=Path("docs/03-reference/Dopemux Cockpit TUI Design System/uploads"),
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    write_pixel_parity_report(upload_dir=args.upload_dir, output_dir=args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
