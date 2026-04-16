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
