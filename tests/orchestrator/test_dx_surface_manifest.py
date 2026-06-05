"""Tests for the task-orchestrator /dx: read-surface manifest + validator.

Covers TP-DMX-ORCH-CS-P1: the surface manifest is an independent authority and the
validator (scripts/validate_dx_surface.py) enforces that the committed /dx: command
surface conforms to it — in particular that no `read`-class command can call a write tool.
"""
from __future__ import annotations

import importlib.util
import json
import shutil
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "validate_dx_surface.py"
MANIFEST = REPO_ROOT / ".taskorchestrator" / "surface_manifest.json"
DX_DIR = REPO_ROOT / ".claude" / "commands" / "dx"


def _load_validator():
    spec = importlib.util.spec_from_file_location("validate_dx_surface", SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def validator():
    return _load_validator()


@pytest.fixture(scope="module")
def manifest():
    return json.loads(MANIFEST.read_text())


def test_manifest_is_valid_json_with_required_shape(manifest):
    for key in ("tools", "read_only_tools", "commands", "read_surface", "boundary"):
        assert key in manifest, f"manifest missing top-level key: {key}"
    assert len(manifest["tools"]) == 14, "expected the live v3 surface (14 tools)"
    assert set(manifest["read_only_tools"]).issubset(manifest["tools"])


def test_read_only_tools_are_classified_safe_read_only(manifest):
    for tool in manifest["read_only_tools"]:
        assert manifest["tools"][tool]["classification"] == "safe_read_only"


def test_manifest_internal_consistency(manifest):
    read_class = {n for n, s in manifest["commands"].items() if s.get("surface_class") == "read"}
    assert read_class == set(manifest["read_surface"])


def test_validator_passes_against_committed_surface(validator):
    failures, _ = validator.run_validation(REPO_ROOT)
    assert failures == [], "committed /dx surface must conform to the manifest:\n" + "\n".join(failures)


def test_every_read_command_uses_only_read_only_tools(validator, manifest):
    read_only = set(manifest["read_only_tools"])
    for name in manifest["read_surface"]:
        path = DX_DIR / f"{name}.md"
        tools = validator.orchestrator_tools(validator.parse_frontmatter_allowed_tools(path))
        assert tools, f"{name}: expected at least one orchestrator tool"
        assert tools.issubset(read_only), f"{name} read command lists non-read tool(s): {tools - read_only}"


def test_every_command_file_is_catalogued(manifest):
    files = {p.stem for p in DX_DIR.glob("*.md")}
    catalogued = set(manifest["commands"])
    assert files == catalogued, f"uncatalogued or stale: {files ^ catalogued}"


def test_validator_bites_when_read_command_gains_a_write_tool(validator, tmp_path):
    """Tampering a read command with a write tool must produce a non-empty failure list."""
    # Build a minimal tmp root mirroring the layout the validator scans.
    (tmp_path / ".taskorchestrator").mkdir()
    shutil.copy(MANIFEST, tmp_path / ".taskorchestrator" / "surface_manifest.json")
    dx = tmp_path / ".claude" / "commands" / "dx"
    dx.mkdir(parents=True)
    for p in DX_DIR.glob("*.md"):
        shutil.copy(p, dx / p.name)

    # Sanity: untampered copy passes.
    assert validator.run_validation(tmp_path)[0] == []

    # Inject a write tool into a read command (tree → advance_item).
    tree = dx / "tree.md"
    tree.write_text(
        tree.read_text().replace(
            '"mcp__task-orchestrator__query_items"',
            '"mcp__task-orchestrator__query_items",\n  "mcp__task-orchestrator__advance_item"',
            1,
        )
    )
    failures, _ = validator.run_validation(tmp_path)
    assert any("advance_item" in f and "tree" in f for f in failures), \
        f"validator failed to catch a read command gaining a write tool; failures={failures}"
