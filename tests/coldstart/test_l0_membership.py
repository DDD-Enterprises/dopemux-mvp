from __future__ import annotations

import json
import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = REPO_ROOT / "templates/plugin/l0_membership.json"

EXPECTED_ITEMS = {
    *(f".claude/commands/dx/{name}.md" for name in [
        "backlinks",
        "block",
        "blocked",
        "cancel",
        "complete",
        "complete-tree",
        "context",
        "depends",
        "implement",
        "next",
        "note",
        "notes",
        "preview",
        "reopen",
        "resume",
        "search",
        "start",
        "tree",
    ]),
    *(f".claude/hooks/{name}" for name in [
        "check_energy.sh",
        "dcp_denylist_nudge.py",
        "dcp_surface_guard.py",
        "log_progress.sh",
        "mcp_health_probe.py",
        "orchestrator_enforcement.py",
        "orchestrator_post_edit_nudge.py",
        "orchestrator_session_start.py",
        "orchestrator_subagent_protocol.py",
        "prompt_analyzer.py",
        "proof_tracking_guard.py",
        "save_context.sh",
        "session_lifecycle.py",
        "track_file_edit.sh",
    ]),
    ".claude/commands/implement.md",
    ".claude/commands/plan.md",
    ".claude/commands/plan-slice.md",
    ".claude/commands/plan-tasks.md",
    ".claude/commands/research.md",
    ".claude/commands/research-deep.md",
    ".claude/commands/research-quick.md",
    ".claude/commands/research-report.md",
}

FLEET_PATTERNS = {
    "mcp_tool": re.compile(r"mcp__[A-Za-z0-9_-]+__", re.I),
    "slash_mcp": re.compile(r"/mcp\s+\S+", re.I),
    "task_orchestrator_mcp": re.compile(r"mcp__task[-_]orchestrator__", re.I),
    "conport_mcp": re.compile(r"mcp__conport__", re.I),
    "localhost": re.compile(r"localhost|127\.0\.0\.1"),
    "docker": re.compile(r"\bdocker\b", re.I),
    "requests_localhost": re.compile(r"requests\.get\([^\n]*localhost", re.I),
    "socket_connect": re.compile(r"socket\.(?:create_connection|connect)\("),
}


def load_manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text())


def test_manifest_exists_and_covers_all_keeper_surfaces() -> None:
    manifest = load_manifest()

    assert manifest["version"] == "1.0"
    assert manifest["generated"]

    items = manifest["items"]
    paths = {item["path"] for item in items}

    assert paths == EXPECTED_ITEMS
    assert len(items) == len(EXPECTED_ITEMS)

    for item in items:
        source_path = REPO_ROOT / item["path"]
        assert source_path.exists(), item["path"]
        assert item["tier"] in {"L0", "L0.5"}
        assert item["type"] in {"skill", "hook"}
        assert item["evidence"], item["path"]
        assert all(entry.strip() for entry in item["evidence"])


def test_l0_items_have_no_direct_fleet_coupling_patterns() -> None:
    manifest = load_manifest()

    for item in manifest["items"]:
        if item["tier"] != "L0":
            continue

        text = (REPO_ROOT / item["path"]).read_text(errors="replace")
        hits = {
            name: pattern.pattern
            for name, pattern in FLEET_PATTERNS.items()
            if pattern.search(text)
        }
        assert hits == {}, f"{item['path']} is L0 but has fleet patterns: {hits}"


def test_l0_5_items_record_specific_fleet_dependencies() -> None:
    manifest = load_manifest()

    for item in manifest["items"]:
        if item["tier"] == "L0.5":
            assert item["fleet_deps"], item["path"]
