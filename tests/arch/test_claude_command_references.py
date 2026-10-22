"""Drift gate for ``.claude/commands/**/*.md`` references.

Pure file reads only. Each check takes the commands directory (and the repo
root where repo state is needed) and returns a list of violation strings, so
the same helpers can be pointed at synthetic or historical command trees.

Checks:
1. ``mcp__<server>__<tool>`` names a tool in ``mcp_tool_surfaces.json``
   when the server has a captured (live/seed, non-empty) tool list.
   ``mcp__<server>__*`` is a server reference only (no tool check).
2. Every referenced MCP server (wildcards included) is known to the surfaces
   snapshot, the MCP catalog or ``.mcp.json``; referenced servers with no
   captured tool list must equal ``UNVERIFIED_SERVERS``.
3. ``model:`` frontmatter values are in ``ALLOWED_COMMAND_MODELS``.
4. ``scripts/<path>.py|.sh`` mentions exist in the repo.
"""

import json
import re
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
COMMANDS_DIR = REPO_ROOT / ".claude" / "commands"

# Servers referenced by commands that have no captured tool list, so their tool
# names cannot be verified. A new unverifiable server must be added here
# deliberately; a server that gains a captured list must be removed.
UNVERIFIED_SERVERS = frozenset({"pal", "gpt-researcher"})

ALLOWED_COMMAND_MODELS = frozenset(
    {
        "claude-opus-5-5",
        "claude-sonnet-5-5",
        "claude-haiku-5-5",
        "opus",
        "sonnet",
        "haiku",
        "inherit",
    }
)

_CAPTURED_SOURCES = frozenset({"live", "seed"})
# Tool token: a bare ``*`` (server wildcard) or a full name with optional
# hyphenated parts, so ``get_context-foo`` is not truncated to ``get_context``.
_MCP_TOOL = r"(\*|[A-Za-z0-9_]+(?:-[A-Za-z0-9_]+)*)"
_MCP_REF = re.compile(r"mcp__([A-Za-z0-9-]+)__" + _MCP_TOOL)
# NOTE: the ``/mcp <server> <tool>`` prose form is intentionally unchecked.
# zen.md and zen-continue.md currently reference a nonexistent ``zen`` server
# (follow-up packet); a prose scan would flag them.
# Repo-root ``scripts/`` paths, optionally ``./scripts/`` (not nested).
_SCRIPT_PATH = r"scripts/[A-Za-z0-9_./-]+\.(?:py|sh)\b"
_SCRIPT_REF = re.compile(r"(?<![\w/.-])(?:\./)?" + _SCRIPT_PATH)
_MODEL_LINE = re.compile(r"^model:\s*(.*?)\s*$")


def _command_files(commands_dir: Path) -> list[Path]:
    return sorted(Path(commands_dir).rglob("*.md"))


def _mcp_refs(commands_dir: Path):
    """Yield (location, server, tool) for every mcp__server__tool mention."""
    for path in _command_files(commands_dir):
        rel = path.relative_to(commands_dir)
        text = path.read_text(encoding="utf-8")
        for lineno, line in enumerate(text.splitlines(), start=1):
            for match in _MCP_REF.finditer(line):
                yield f"{rel}:{lineno}", match.group(1), match.group(2)


def _surface_servers(repo_root: Path) -> dict:
    data = json.loads((Path(repo_root) / "mcp_tool_surfaces.json").read_text())
    return data["servers"]


def _captured_tools(repo_root: Path) -> dict[str, set[str]]:
    """Map server -> tool names for servers with a live/seed non-empty list."""
    captured = {}
    for name, server in _surface_servers(repo_root).items():
        tools = server.get("tools") or {}
        if server.get("source") in _CAPTURED_SOURCES and tools:
            captured[name] = set(tools)
    return captured


def _known_servers(repo_root: Path) -> set[str]:
    repo_root = Path(repo_root)
    known = set(_surface_servers(repo_root))
    catalog = yaml.safe_load((repo_root / "mcp_catalog.yaml").read_text())
    known |= set(catalog.get("servers") or {})
    mcp_json = json.loads((repo_root / ".mcp.json").read_text())
    known |= set(mcp_json.get("mcpServers") or {})
    return known


def check_mcp_tool_refs(commands_dir: Path, repo_root: Path) -> list[str]:
    captured = _captured_tools(repo_root)
    violations = []
    for location, server, tool in _mcp_refs(commands_dir):
        if tool == "*":  # server wildcard: checked by check_mcp_servers only
            continue
        if server in captured and tool not in captured[server]:
            violations.append(
                f"{location}: mcp__{server}__{tool} is not a {server} tool"
            )
    return violations


def check_mcp_servers(
    commands_dir: Path,
    repo_root: Path,
    unverified: frozenset[str] = UNVERIFIED_SERVERS,
) -> list[str]:
    known = _known_servers(repo_root)
    captured = _captured_tools(repo_root)
    violations = []
    referenced = set()
    for location, server, _tool in _mcp_refs(commands_dir):
        referenced.add(server)
        if server not in known:
            violations.append(f"{location}: unknown MCP server '{server}'")
    actual = {s for s in referenced if s in known and s not in captured}
    for server in sorted(actual - set(unverified)):
        violations.append(
            f"server '{server}' lacks a captured tool list: UNVERIFIED_SERVERS"
        )
    for server in sorted(set(unverified) - actual):
        violations.append(
            f"UNVERIFIED_SERVERS entry '{server}' is not referenced "
            "or is now verifiable"
        )
    return violations


def _frontmatter_lines(text: str):
    """Yield (lineno, line) of the leading ``---`` frontmatter block."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return
    for lineno, line in enumerate(lines[1:], start=2):
        if line.strip() == "---":
            return
        yield lineno, line


def check_model_pins(commands_dir: Path) -> list[str]:
    violations = []
    for path in _command_files(commands_dir):
        rel = path.relative_to(commands_dir)
        text = path.read_text(encoding="utf-8")
        for lineno, line in _frontmatter_lines(text):
            match = _MODEL_LINE.match(line)
            if not match:
                continue
            value = match.group(1).strip("\"'")
            if value not in ALLOWED_COMMAND_MODELS:
                msg = f"{rel}:{lineno}: model '{value}' is not allowed"
                violations.append(msg)
    return violations


def check_script_refs(commands_dir: Path, repo_root: Path) -> list[str]:
    violations = []
    for path in _command_files(commands_dir):
        rel = path.relative_to(commands_dir)
        text = path.read_text(encoding="utf-8")
        for lineno, line in enumerate(text.splitlines(), start=1):
            for match in _SCRIPT_REF.finditer(line):
                if not (Path(repo_root) / match.group(0)).is_file():
                    violations.append(
                        f"{rel}:{lineno}: {match.group(0)} does not exist"
                    )
    return violations


def _write_command(
    commands_dir: Path,
    body: str,
    model: str = "inherit",
) -> None:
    commands_dir.mkdir(parents=True, exist_ok=True)
    (commands_dir / "sample.md").write_text(
        f"---\nmodel: {model}\n---\n{body}\n", encoding="utf-8"
    )


# --- Real repo gate -------------------------------------------------------


def test_should_name_only_captured_tools_when_commands_reference_mcp_tools():
    assert check_mcp_tool_refs(COMMANDS_DIR, REPO_ROOT) == []


def test_should_reference_only_known_servers_when_commands_name_servers():
    assert check_mcp_servers(COMMANDS_DIR, REPO_ROOT) == []


def test_should_pin_only_allowed_models_when_commands_declare_model():
    assert check_model_pins(COMMANDS_DIR) == []


def test_should_reference_existing_scripts_when_commands_mention_scripts():
    assert check_script_refs(COMMANDS_DIR, REPO_ROOT) == []


# --- Negative controls ----------------------------------------------------


def test_should_report_violation_when_tool_name_is_not_captured(tmp_path):
    _write_command(tmp_path, "Use `mcp__conport__no_such_tool` here.")

    violations = check_mcp_tool_refs(tmp_path, REPO_ROOT)

    assert len(violations) == 1
    assert "mcp__conport__no_such_tool" in violations[0]


def test_should_report_violation_when_server_is_unknown(tmp_path):
    _write_command(tmp_path, "Use `mcp__no-such-server__do_thing` here.")

    violations = check_mcp_servers(tmp_path, REPO_ROOT)

    assert any("unknown MCP server 'no-such-server'" in v for v in violations)


def test_should_report_violation_when_unverified_server_unlisted(tmp_path):
    _write_command(tmp_path, "Use `mcp__pal__thinkdeep` here.")

    violations = check_mcp_servers(tmp_path, REPO_ROOT, unverified=frozenset())

    assert any("'pal'" in v and "UNVERIFIED_SERVERS" in v for v in violations)


def test_should_report_violation_when_unverified_entry_is_stale(tmp_path):
    _write_command(tmp_path, "Use `mcp__conport__get_context` here.")

    stale = frozenset({"pal"})

    violations = check_mcp_servers(tmp_path, REPO_ROOT, unverified=stale)

    assert any("UNVERIFIED_SERVERS entry 'pal'" in v for v in violations)


def test_should_report_violation_when_model_pin_is_stale(tmp_path):
    _write_command(tmp_path, "No refs.", model='"claude-sonnet-4-20250514"')

    violations = check_model_pins(tmp_path)

    assert len(violations) == 1
    assert "claude-sonnet-4-20250514" in violations[0]


def test_should_report_violation_when_script_does_not_exist(tmp_path):
    _write_command(tmp_path, "Run `scripts/definitely_missing_script.py` now.")

    violations = check_script_refs(tmp_path, REPO_ROOT)

    assert len(violations) == 1
    assert "scripts/definitely_missing_script.py" in violations[0]


def test_should_report_nothing_when_synthetic_command_is_valid(tmp_path):
    _write_command(
        tmp_path,
        "Use `mcp__conport__get_context` and run `scripts/proof_bundle.sh`.",
        model="opus",
    )

    assert check_mcp_tool_refs(tmp_path, REPO_ROOT) == []
    assert check_model_pins(tmp_path) == []
    assert check_script_refs(tmp_path, REPO_ROOT) == []


# --- AUDIT-01 negative controls (F2, F3) -----------------------------------


def test_should_report_violation_when_tool_token_has_hyphen_suffix(tmp_path):
    _write_command(tmp_path, "Use `mcp__conport__get_context-foo` here.")

    violations = check_mcp_tool_refs(tmp_path, REPO_ROOT)

    assert len(violations) == 1
    assert "mcp__conport__get_context-foo" in violations[0]


def test_should_report_violation_when_wildcard_server_is_unknown(tmp_path):
    _write_command(tmp_path, "Use `mcp__no-such-server__*` here.")

    violations = check_mcp_servers(tmp_path, REPO_ROOT)

    assert any("unknown MCP server 'no-such-server'" in v for v in violations)


def test_should_accept_wildcard_when_server_is_known_and_captured(tmp_path):
    _write_command(tmp_path, "Use `mcp__conport__*` here.")

    assert check_mcp_tool_refs(tmp_path, REPO_ROOT) == []
    violations = check_mcp_servers(tmp_path, REPO_ROOT, unverified=frozenset())
    assert violations == []


def test_should_require_unverified_listing_when_wildcard_server_uncaptured(
    tmp_path,
):
    _write_command(tmp_path, "Use `mcp__pal__*` here.")

    violations = check_mcp_servers(tmp_path, REPO_ROOT, unverified=frozenset())

    assert any("'pal'" in v and "UNVERIFIED_SERVERS" in v for v in violations)


def test_should_report_violation_when_dot_slash_script_is_missing(tmp_path):
    _write_command(tmp_path, "Run `./scripts/set-profile.sh` now.")

    violations = check_script_refs(tmp_path, REPO_ROOT)

    assert len(violations) == 1
    assert "scripts/set-profile.sh" in violations[0]


def test_should_report_violation_when_bare_script_path_is_missing(tmp_path):
    _write_command(tmp_path, "Run python scripts/x.py now.")

    violations = check_script_refs(tmp_path, REPO_ROOT)

    assert len(violations) == 1
    assert "scripts/x.py" in violations[0]


def test_should_ignore_nested_scripts_dir_when_not_repo_root_scripts(tmp_path):
    _write_command(tmp_path, "See foo/scripts/x.py and xscripts/a.py.")

    assert check_script_refs(tmp_path, REPO_ROOT) == []
