from pathlib import Path
import sys

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from services.serena.dopecode.transform.write_layer import WriteLayer


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_validate_boundary_rejects_workspace_escape_and_prefix_collisions(tmp_path: Path):
    workspace = tmp_path / "workspace"
    sibling = tmp_path / "workspace2"
    workspace.mkdir()
    sibling.mkdir()

    layer = WriteLayer(workspace, "ws-test")

    with pytest.raises(ValueError):
        layer._validate_boundary("../escape.txt")

    with pytest.raises(ValueError):
        layer._validate_boundary("../workspace2/evil.txt")


def test_apply_patch_applies_supported_unified_diff(tmp_path: Path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    target = workspace / "pkg" / "module.py"
    _write(target, "alpha = 1\nbeta = 2\ngamma = 3\n")

    layer = WriteLayer(workspace, "ws-test")
    diff_text = """--- a/pkg/module.py\n+++ b/pkg/module.py\n@@ -1,3 +1,3 @@\n alpha = 1\n-beta = 2\n+beta = 20\n gamma = 3\n"""

    result = layer.apply_patch("pkg/module.py", diff_text)

    assert result["status"] == "applied"
    assert result["approval_receipt"]["execution_mode"] == "direct"
    assert target.read_text(encoding="utf-8") == "alpha = 1\nbeta = 20\ngamma = 3\n"


def test_apply_patch_rejects_malformed_diff_and_leaves_file_unchanged(tmp_path: Path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    target = workspace / "pkg" / "module.py"
    original = "alpha = 1\nbeta = 2\n"
    _write(target, original)

    layer = WriteLayer(workspace, "ws-test")
    malformed = """--- a/pkg/module.py\n+++ b/pkg/module.py\n@@ -1,2 +1,2 @@\n alpha = 1\n-beta = 2\n+beta = 20\n+extra = 3\n"""

    with pytest.raises(ValueError):
        layer.apply_patch("pkg/module.py", malformed)

    assert target.read_text(encoding="utf-8") == original


def test_batch_apply_patch_preserves_deterministic_order_and_reports_partial_failure(tmp_path: Path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    _write(workspace / "b.py", "value = 2\n")
    _write(workspace / "a.py", "value = 1\n")

    layer = WriteLayer(workspace, "ws-test")
    operations = [
        {
            "path": "b.py",
            "diff": "--- a/b.py\n+++ b/b.py\n@@ -1,1 +1,1 @@\n-value = 2\n+value = 20\n",
        },
        {
            "path": "a.py",
            "diff": "--- a/a.py\n+++ b/a.py\n@@ -1,1 +1,1 @@\n-value = 1\n+value = 10\n+extra = 2\n",
        },
    ]

    preview = layer.batch_apply_patch(operations, preview=True)
    assert preview["ordered_files"] == ["a.py", "b.py"]
    assert preview["approval_receipt"]["execution_mode"] == "preview_required"
    assert workspace.joinpath("a.py").read_text(encoding="utf-8") == "value = 1\n"
    assert workspace.joinpath("b.py").read_text(encoding="utf-8") == "value = 2\n"

    result = layer.batch_apply_patch(operations, preview=False)
    assert result["status"] == "partial_failure"
    assert result["approval_receipt"]["execution_mode"] == "approval_required"
    assert result["applied_count"] == 1
    assert result["failed_count"] == 1
    assert workspace.joinpath("b.py").read_text(encoding="utf-8") == "value = 20\n"
    assert workspace.joinpath("a.py").read_text(encoding="utf-8") == "value = 1\n"
