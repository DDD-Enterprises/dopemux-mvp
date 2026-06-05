from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "brand_lint.py"


def _load_brand_lint_module():
    spec = importlib.util.spec_from_file_location("brand_lint_module", SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_brand_lint_passes_on_current_repo_state() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH)],
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).resolve().parents[2]),
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "0 errors, 0 warnings" in result.stdout


def test_brand_lint_helpers_catch_merge_markers_and_raw_hex(tmp_path: Path) -> None:
    module = _load_brand_lint_module()

    doc = tmp_path / "brand.md"
    doc.write_text("<<<<<<< HEAD\nconflict\n=======\nother\n>>>>>>> branch\n", encoding="utf-8")
    py_file = tmp_path / "ui.py"
    py_file.write_text('PANEL = "#ff00ff"\n', encoding="utf-8")

    merge_errors = module._iter_merge_marker_violations(doc)
    palette_errors = module._iter_palette_violations(py_file)

    assert merge_errors
    assert "merge conflict markers detected" in merge_errors[0]
    assert palette_errors
    assert "#ff00ff" in palette_errors[0]


def test_is_red_family_rejects_magenta_pink_and_admits_red() -> None:
    module = _load_brand_lint_module()

    # Magenta (300), pink (330), and just-outside-band hues must be rejected so a
    # danger-slot regression to those colors is caught by the gate.
    for hue in (300.0, 330.0, 339.0, 16.0):
        assert module._is_red_family(hue) is False, hue

    # The shipped danger reds (mint-mojo 346, dreamscape 344, dreams 349) and the
    # band boundaries must be admitted.
    for hue in (340.0, 344.0, 346.0, 349.0, 0.0, 15.0):
        assert module._is_red_family(hue) is True, hue

    # Out-of-range hues are rejected, not wrapped (strict contract predicate).
    for hue in (-1.0, 360.0, 400.0):
        assert module._is_red_family(hue) is False, hue


def test_danger_style_keys_are_the_expected_contract() -> None:
    module = _load_brand_lint_module()

    # Drift guard: the enforced danger slots must match the documented contract.
    assert module.DANGER_STYLE_KEYS == ("error", "chip.blocker", "severity.critical")


def test_theme_danger_slots_resolve_to_red_family() -> None:
    module = _load_brand_lint_module()

    # Every theme's error / chip.blocker / severity.critical slot must resolve to
    # a red-family hue in the live build_theme() output.
    assert module._iter_theme_danger_hue_violations() == []
