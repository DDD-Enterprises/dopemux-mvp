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


def test_read_command_nonorch_allowlist_present_and_writefree(manifest):
    """The fail-closed allowlist must exist and contain no obvious mutating tool."""
    allow = manifest.get("read_command_nonorch_allowlist", {}).get("tools")
    assert isinstance(allow, list) and allow, "manifest missing read_command_nonorch_allowlist.tools"
    forbidden = {"Write", "Edit", "MultiEdit", "NotebookEdit"}
    assert not (set(allow) & forbidden), f"allowlist must not contain repo-write tools: {set(allow) & forbidden}"
    # No ConPort/dope-context *write* tool should be allowlisted (only read helpers).
    for t in allow:
        assert not any(
            t.startswith(p) for p in ("mcp__conport__log", "mcp__conport__update",
                                      "mcp__conport__delete", "mcp__dope-context__index")
        ), f"allowlist must not contain a bridge/memory write tool: {t}"


def test_committed_read_commands_obey_nonorch_allowlist(validator, manifest):
    """Every committed read command's non-orchestrator tools are within the allowlist."""
    allow = set(manifest["read_command_nonorch_allowlist"]["tools"])
    for name in manifest["read_surface"]:
        path = DX_DIR / f"{name}.md"
        nonorch = validator.nonorch_tools(validator.parse_frontmatter_allowed_tools(path))
        assert nonorch.issubset(allow), \
            f"{name} read command lists non-orchestrator tool(s) outside the allowlist: {nonorch - allow}"


def test_validator_bites_when_read_command_gains_a_nonorch_write_tool(validator, tmp_path):
    """A read command gaining a repo/bridge write (e.g. Write) must fail condition (g)."""
    (tmp_path / ".taskorchestrator").mkdir()
    shutil.copy(MANIFEST, tmp_path / ".taskorchestrator" / "surface_manifest.json")
    dx = tmp_path / ".claude" / "commands" / "dx"
    dx.mkdir(parents=True)
    for p in DX_DIR.glob("*.md"):
        shutil.copy(p, dx / p.name)

    assert validator.run_validation(tmp_path)[0] == []  # untampered passes

    # Inject a repo-write tool into a read command (tree).
    tree = dx / "tree.md"
    tree.write_text(tree.read_text().replace('"Bash", "Read",', '"Bash", "Read", "Write",', 1))
    failures, _ = validator.run_validation(tmp_path)
    assert any("Write" in f and "tree" in f for f in failures), \
        f"validator failed to catch a read command gaining a non-orchestrator write tool; failures={failures}"

    # And a bridge write (ConPort log) must also be caught.
    shutil.copy(DX_DIR / "tree.md", tree)  # restore clean
    tree.write_text(
        tree.read_text().replace('"Bash", "Read",', '"Bash", "Read", "mcp__conport__log_decision",', 1)
    )
    failures, _ = validator.run_validation(tmp_path)
    assert any("mcp__conport__log_decision" in f and "tree" in f for f in failures), \
        f"validator failed to catch a read command gaining a ConPort write tool; failures={failures}"
