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
    safe_read_only = {
        name for name, spec in manifest["tools"].items() if spec.get("classification") == "safe_read_only"
    }
    assert set(manifest["read_only_tools"]) == safe_read_only


def test_manifest_internal_consistency(manifest):
    read_class = {n for n, s in manifest["commands"].items() if s.get("surface_class") == "read"}
    assert read_class == set(manifest["read_surface"])
    safe_read_only = {
        name for name, spec in manifest["tools"].items() if spec.get("classification") == "safe_read_only"
    }
    assert set(manifest["read_only_tools"]) == safe_read_only


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


def test_validator_bites_when_read_only_tools_gain_a_write_tool(validator, tmp_path):
    """A write-class tool in read_only_tools must fail the internal manifest consistency check."""
    (tmp_path / ".taskorchestrator").mkdir()
    shutil.copy(MANIFEST, tmp_path / ".taskorchestrator" / "surface_manifest.json")
    dx = tmp_path / ".claude" / "commands" / "dx"
    dx.mkdir(parents=True)
    for p in DX_DIR.glob("*.md"):
        shutil.copy(p, dx / p.name)

    assert validator.run_validation(tmp_path)[0] == []

    manifest_path = tmp_path / ".taskorchestrator" / "surface_manifest.json"
    manifest_data = json.loads(manifest_path.read_text())
    manifest_data["read_only_tools"].append("advance_item")
    manifest_path.write_text(json.dumps(manifest_data, indent=2))

    failures, _ = validator.run_validation(tmp_path)
    assert any("read_only_tools" in f and "advance_item" in f for f in failures), \
        f"validator failed to catch a write-class tool in read_only_tools; failures={failures}"


def test_read_command_nonorch_allowlist_present_and_writefree(manifest):
    """The fail-closed allowlist must exist, exclude bare Bash, and scope Bash to read-only cmds."""
    cfg = manifest.get("read_command_nonorch_allowlist", {})
    allow = cfg.get("tools")
    assert isinstance(allow, list) and allow, "manifest missing read_command_nonorch_allowlist.tools"
    forbidden = {"Write", "Edit", "MultiEdit", "NotebookEdit", "Bash"}
    assert not (set(allow) & forbidden), \
        f"plain-tool allowlist must not contain repo-write or bare Bash: {set(allow) & forbidden}"
    # No ConPort/dope-context *write* tool should be allowlisted (only read helpers).
    for t in allow:
        assert not any(
            t.startswith(p) for p in ("mcp__conport__log", "mcp__conport__update",
                                      "mcp__conport__delete", "mcp__dope-context__index")
        ), f"allowlist must not contain a bridge/memory write tool: {t}"
    # Scoped-Bash commands must be read-only (no commit/rm/push/branch/etc.).
    bash_cmds = cfg.get("bash_allowed_commands", [])
    assert isinstance(bash_cmds, list) and bash_cmds, "missing bash_allowed_commands"
    mutating = {"git commit", "git push", "git branch", "git checkout", "git reset",
                "git merge", "git rebase", "rm", "touch", "mv", "cp", "git add"}
    assert not (set(bash_cmds) & mutating), \
        f"bash_allowed_commands must be read-only: {set(bash_cmds) & mutating}"


def test_committed_read_commands_obey_nonorch_allowlist(validator, manifest):
    """Every committed read command's non-orchestrator tools must pass the read-command rule."""
    cfg = manifest["read_command_nonorch_allowlist"]
    allow = set(cfg["tools"])
    bash_cmds = cfg["bash_allowed_commands"]
    for name in manifest["read_surface"]:
        path = DX_DIR / f"{name}.md"
        nonorch = validator.nonorch_tools(validator.parse_frontmatter_allowed_tools(path))
        for t in nonorch:
            reason = validator.read_command_nonorch_violation(t, allow, bash_cmds)
            assert reason is None, f"{name}: {t} disallowed in read command: {reason}"


def test_read_command_nonorch_violation_helper(validator, manifest):
    """Unit-cover the read-command tool classifier directly."""
    cfg = manifest["read_command_nonorch_allowlist"]
    allow = set(cfg["tools"])
    bash_cmds = cfg["bash_allowed_commands"]
    f = validator.read_command_nonorch_violation
    # Allowed.
    assert f("Read", allow, bash_cmds) is None
    assert f("Bash(git rev-parse:*)", allow, bash_cmds) is None
    # Rejected.
    assert f("Bash", allow, bash_cmds) is not None          # bare/unscoped
    assert f("Bash(git commit:*)", allow, bash_cmds) is not None
    assert f("Bash(rm:*)", allow, bash_cmds) is not None
    assert f("Write", allow, bash_cmds) is not None
    assert f("mcp__conport__log_decision", allow, bash_cmds) is not None


def test_validator_bites_when_read_command_gains_a_nonorch_write_tool(validator, tmp_path):
    """A read command gaining a repo/bridge write or unsafe Bash must fail condition (g)."""
    (tmp_path / ".taskorchestrator").mkdir()
    shutil.copy(MANIFEST, tmp_path / ".taskorchestrator" / "surface_manifest.json")
    dx = tmp_path / ".claude" / "commands" / "dx"
    dx.mkdir(parents=True)
    for p in DX_DIR.glob("*.md"):
        shutil.copy(p, dx / p.name)

    assert validator.run_validation(tmp_path)[0] == []  # untampered passes

    def tamper_and_check(replacement, needle):
        shutil.copy(DX_DIR / "tree.md", dx / "tree.md")  # restore clean
        tree = dx / "tree.md"
        tree.write_text(tree.read_text().replace('"Bash(git rev-parse:*)", "Read",',
                                                 f'"Bash(git rev-parse:*)", "Read", {replacement},', 1))
        failures, _ = validator.run_validation(tmp_path)
        assert any(needle in f and "tree" in f for f in failures), \
            f"validator missed {replacement} in a read command; failures={failures}"

    tamper_and_check('"Write"', "Write")                                   # repo write
    tamper_and_check('"mcp__conport__log_decision"', "mcp__conport__log_decision")  # bridge write

    # Bare unscoped Bash must also be rejected (regression for the scoped-Bash hardening).
    shutil.copy(DX_DIR / "tree.md", dx / "tree.md")
    tree = dx / "tree.md"
    tree.write_text(tree.read_text().replace('"Bash(git rev-parse:*)"', '"Bash"', 1))
    failures, _ = validator.run_validation(tmp_path)
    assert any("Bash" in f and "tree" in f for f in failures), \
        f"validator failed to reject bare Bash in a read command; failures={failures}"

    # A scoped but mutating Bash command must be rejected.
    shutil.copy(DX_DIR / "tree.md", dx / "tree.md")
    tree = dx / "tree.md"
    tree.write_text(tree.read_text().replace('"Bash(git rev-parse:*)"', '"Bash(git commit:*)"', 1))
    failures, _ = validator.run_validation(tmp_path)
    assert any("git commit" in f and "tree" in f for f in failures), \
        f"validator failed to reject a mutating scoped Bash in a read command; failures={failures}"
