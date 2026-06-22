"""Tests for the Cockpit pixel parity proof generator."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from scripts.cockpit_pixel_parity_proof import (
    CLASSIFICATIONS,
    COCKPIT_REFERENCE_MODES,
    classify_reference_image,
    generate_pixel_parity_report,
)


def _write_png(path: Path, color: tuple[int, int, int]) -> None:
    Image.new("RGB", (8, 8), color).save(path)


def test_reference_classification_separates_dark_cockpit_from_setup_form(
    tmp_path: Path,
) -> None:
    dark = tmp_path / "dark-cockpit.png"
    bright = tmp_path / "setup-form.png"
    _write_png(dark, (10, 20, 30))
    _write_png(bright, (245, 245, 242))

    dark_result = classify_reference_image(dark)
    bright_result = classify_reference_image(bright)

    assert dark_result.category == "dark_cockpit_reference"
    assert dark_result.classification == "DESIGN_DRIFT"
    assert dark_result.pixel_certainty == "UNKNOWN"
    assert bright_result.category == "non_runtime_setup_form_reference"
    assert bright_result.classification == "SPEC_AMBIGUITY"
    assert bright_result.pixel_certainty == "UNKNOWN"


def test_generate_report_emits_required_classifications_and_runtime_artifacts(
    tmp_path: Path,
) -> None:
    uploads = tmp_path / "uploads"
    output = tmp_path / "proof"
    uploads.mkdir()
    _write_png(uploads / "dark-a.png", (10, 20, 30))
    _write_png(uploads / "bright-a.png", (245, 245, 242))

    report = generate_pixel_parity_report(upload_dir=uploads, output_dir=output)

    assert set(CLASSIFICATIONS) == {
        "MATCH",
        "ACCEPTABLE_DELTA",
        "DESIGN_DRIFT",
        "RUNTIME_BUG",
        "SPEC_AMBIGUITY",
        "UNKNOWN",
    }
    assert report["packet_id"] == "TP-DMX-COCKPIT-PIXEL-PARITY-PROOF-001"
    assert report["runtime_modes"] == list(COCKPIT_REFERENCE_MODES)
    assert {item["classification"] for item in report["reference_images"]} == {
        "DESIGN_DRIFT",
        "SPEC_AMBIGUITY",
    }
    assert all(item["pixel_certainty"] == "UNKNOWN" for item in report["reference_images"])
    assert (output / "PIXEL_PARITY_REPORT.json").is_file()
    assert (output / "PIXEL_PARITY_REPORT.md").is_file()
    for mode in COCKPIT_REFERENCE_MODES:
        assert (output / "runtime-renders" / f"{mode}.txt").is_file()
        assert (output / "runtime-screenshots" / f"{mode}.svg").is_file()
