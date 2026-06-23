"""Tests for Cockpit Textual screenshot automation proof generation."""

from __future__ import annotations

from pathlib import Path

import scripts.cockpit_textual_screenshot_automation as automation
from scripts.cockpit_textual_screenshot_automation import (
    DEFAULT_VIEWPORTS,
    generate_textual_screenshot_report,
    normalize_svg_for_hash,
)


def test_normalize_svg_for_hash_removes_generated_textual_ids() -> None:
    svg_a = '<svg class="terminal-123"><clipPath id="clip-456"></clipPath></svg>'
    svg_b = '<svg class="terminal-789"><clipPath id="clip-101"></clipPath></svg>'

    assert normalize_svg_for_hash(svg_a) == normalize_svg_for_hash(svg_b)


def test_generate_report_emits_mode_viewport_screenshot_manifest(
    tmp_path: Path,
) -> None:
    report = generate_textual_screenshot_report(
        output_dir=tmp_path,
        modes=("pm", "services"),
        viewports=((80, 24), (100, 32)),
    )

    assert report["packet_id"] == "TP-DMX-COCKPIT-TEXTUAL-SCREENSHOT-AUTOMATION-001"
    assert report["status"] == "CONTINUATION_PROOF"
    assert report["modes"] == ["pm", "services"]
    assert report["viewports"] == [
        {"cols": 80, "rows": 24},
        {"cols": 100, "rows": 32},
    ]
    assert report["boundaries"] == {
        "runtime_changes_authorized": False,
        "design_fixes_authorized": False,
        "token_doctrine_changes_authorized": False,
        "pixel_parity_claimed": False,
        "live_integration_claimed": False,
        "ready_for_claude_design_claimed": False,
    }
    assert len(report["screenshots"]) == 4

    for item in report["screenshots"]:
        assert item["capture_status"] == "PASS"
        assert item["mode"] in {"pm", "services"}
        assert item["viewport"]["cols"] in {80, 100}
        assert item["viewport"]["rows"] in {24, 32}
        assert len(item["text_sha256"]) == 64
        assert len(item["svg_sha256"]) == 64
        assert len(item["raw_svg_sha256"]) == 64
        assert len(item["normalized_svg_sha256"]) == 64
        assert item["svg_sha256"] == item["normalized_svg_sha256"]
        assert Path(item["text_path"]).is_file()
        svg_path = Path(item["svg_path"])
        assert svg_path.is_file()
        assert "<svg" in svg_path.read_text(encoding="utf-8")

    assert (tmp_path / "TEXTUAL_SCREENSHOT_AUTOMATION_REPORT.json").is_file()
    assert (tmp_path / "TEXTUAL_SCREENSHOT_AUTOMATION_REPORT.md").is_file()


def test_default_viewports_cover_reference_and_minimum_sizes() -> None:
    assert DEFAULT_VIEWPORTS == ((120, 40), (100, 32), (80, 24))


def test_generator_removes_stale_rasters_when_converter_is_unavailable(
    tmp_path: Path,
    monkeypatch,
) -> None:
    stale_png = tmp_path / "raster-screenshots" / "pm-80x24.png"
    stale_png.parent.mkdir(parents=True)
    stale_png.write_bytes(b"stale")
    monkeypatch.setattr(automation.shutil, "which", lambda _name: None)

    report = generate_textual_screenshot_report(
        output_dir=tmp_path,
        modes=("pm",),
        viewports=((80, 24),),
    )

    assert not stale_png.exists()
    assert report["screenshots"][0]["raster_png_path"] is None
    assert report["screenshots"][0]["rasterization"] == "UNKNOWN"
