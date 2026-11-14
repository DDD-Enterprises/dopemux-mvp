"""Drift gate for ``.claude/commands/**/*.md`` references.

Pure file reads only. Each check takes the commands directory (and the repo
root where repo state is needed) and returns a list of violation strings, so
the same helpers can be pointed at synthetic or historical command trees.

Checks:
1. ``mcp__<server>__<tool>`` and ``/mcp <server> <tool>`` name a tool in
   ``mcp_tool_surfaces.json`` when the server has a captured (live/seed,
   non-empty) tool list.
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
UNVERIFIED_SERVERS = frozenset({"pal-stdio", "gpt-researcher"})

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
# Tool token: any run of name characters (or a bare ``*`` server wildcard) up
# to a non-name character, so malformed tokens such as ``get_context--bad`` or
# ``*bad`` are captured whole and reported instead of truncating to a valid
# prefix. Server names may contain single underscores (``MCP_DOCKER``); the
# ``__`` separator ends the lazy server group.
_MCP_TOOL = r"([A-Za-z0-9_*-]+)"
_MCP_SERVER = r"([A-Za-z0-9-]+(?:_[A-Za-z0-9-]+)*?)"
_MCP_REF = re.compile(r"mcp__" + _MCP_SERVER + r"__" + _MCP_TOOL)
# Prose form ``/mcp <server> <tool>``.
_MCP_PROSE_REF = re.compile(
    r"(?<![\w/])/mcp\s+([A-Za-z0-9_-]+)\s+([A-Za-z0-9_*-]+)"
)
# Repo-root ``scripts/`` paths, optionally ``./scripts/`` (not nested).
_SCRIPT_PATH = r"scripts/[A-Za-z0-9_./-]+\.(?:py|sh)\b"
_SCRIPT_REF = re.compile(r"(?<![\w/.-])(?:\./)?" + _SCRIPT_PATH)
_MODEL_LINE = re.compile(r"^model:\s*(.*?)\s*$")


def _command_files(commands_dir: Path) -> list[Path]:
    return sorted(Path(commands_dir).rglob("*.md"))


def _mcp_refs(commands_dir: Path):
    """Yield (location, server, tool) for mcp__s__t or /mcp s t mentions."""
    for path in _command_files(commands_dir):
        rel = path.relative_to(commands_dir)
        text = path.read_text(encoding="utf-8")
        for lineno, line in enumerate(text.splitlines(), start=1):
            for pattern in (_MCP_REF, _MCP_PROSE_REF):
                for match in pattern.finditer(line):
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


# ConPort's SSE `update_context` posts `context_data` as the request body, and
# `_update_context` stores only the fields it reads. Any other key is dropped
# while the call still reports success, so payload keys are checked against
# the server source.
_CONPORT_DIR = REPO_ROOT / "docker" / "mcp-servers-source" / "conport"
_CONTEXT_PAYLOAD = re.compile(r'\bcontext_data"?\s*[:=]\s*(?=\{)')
_PAYLOAD_TOKEN = re.compile(r'[{}]|"(\w+)"\s*:')
_WORKSPACE_ROOT = "$(git rev-parse --show-toplevel)"

# ConPort's schema rejects any other progress status. The window holds the
# arguments that follow a tool name in a command file.
_PROGRESS_CALL = re.compile(r"mcp__conport__(?:log|update|get)_progress")
_STATUS_ARG = re.compile(r'"?\bstatus"?\s*[:=]\s*"([A-Z][A-Z_]*)"')
_PROGRESS_CALL_WINDOW = 300

# Custom-data records one command saves and others read: (category, key,
# {command file: calls}). A save and a read that disagree on workspace,
# category or key fail silently, so both sides are pinned to one call shape.
_SHARED_RECORDS = (
    (
        "research",
        "last_research",
        {"research-deep.md": 1, "research-report.md": 1},
    ),
    (
        "dx_session",
        "last_session",
        {"dx/implement.md": 2, "dx/context.md": 1, "dx/next.md": 1},
    ),
)


def _update_context_fields() -> frozenset[str]:
    source = (_CONPORT_DIR / "enhanced_server.py").read_text(encoding="utf-8")
    body = source.split("async def _update_context(", 1)[1]
    body = body.split("\n    async def ", 1)[0]
    return frozenset(re.findall(r"data\.get\('(\w+)'\)", body))


def _progress_statuses() -> frozenset[str]:
    schema = (_CONPORT_DIR / "schema.sql").read_text(encoding="utf-8")
    table = schema.split("CREATE TABLE progress_entries", 1)[1]
    values = re.search(r"CHECK \(status IN \(([^)]*)\)\)", table).group(1)
    return frozenset(re.findall(r"'(\w+)'", values))


def _payload_keys(text: str) -> list[str]:
    """Top-level keys of the JSON-like object that opens `text`."""
    keys, depth = [], 0
    for token in _PAYLOAD_TOKEN.finditer(text):
        if token.group(0) == "{":
            depth += 1
        elif token.group(0) == "}":
            depth -= 1
            if depth == 0:
                break
        elif depth == 1:
            keys.append(token.group(1))
    return keys


def check_context_payloads(commands_dir: Path) -> list[str]:
    supported = _update_context_fields()
    violations = []
    for path in _command_files(commands_dir):
        rel = path.relative_to(commands_dir)
        text = path.read_text(encoding="utf-8")
        for payload in _CONTEXT_PAYLOAD.finditer(text):
            lineno = text.count("\n", 0, payload.start()) + 1
            for key in _payload_keys(text[payload.end():]):
                if key not in supported:
                    violations.append(
                        f"{rel}:{lineno}: update_context drops {key}"
                    )
    return violations


def check_progress_statuses(commands_dir: Path) -> list[str]:
    allowed = _progress_statuses()
    violations = set()
    for path in _command_files(commands_dir):
        rel = path.relative_to(commands_dir)
        text = path.read_text(encoding="utf-8")
        for call in _PROGRESS_CALL.finditer(text):
            start = call.end()
            args = text[start:start + _PROGRESS_CALL_WINDOW]
            for status in _STATUS_ARG.finditer(args):
                if status.group(1) not in allowed:
                    lineno = text.count("\n", 0, start + status.start()) + 1
                    violations.add(
                        f"{rel}:{lineno}: schema.sql rejects progress "
                        f"status {status.group(1)}"
                    )
    return sorted(violations)


def check_shared_records(
    commands_dir: Path, records=_SHARED_RECORDS
) -> list[str]:
    violations = []
    for category, key, files in records:
        call = re.compile(
            rf'workspace_id[:=]\s*"{re.escape(_WORKSPACE_ROOT)}",?\s*'
            rf'category[:=]\s*"{category}",?\s*key[:=]\s*"{key}"'
        )
        for name, expected in files.items():
            text = (Path(commands_dir) / name).read_text(encoding="utf-8")
            found = len(call.findall(text))
            if found != expected:
                violations.append(
                    f"{name}: expected {expected} {category}/{key} "
                    f"call(s), found {found}"
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


def test_should_send_only_stored_fields_when_commands_update_context():
    assert "active_context" in _update_context_fields()
    assert check_context_payloads(COMMANDS_DIR) == []


def test_should_use_schema_statuses_when_commands_call_progress_tools():
    assert "PLANNED" in _progress_statuses()
    assert check_progress_statuses(COMMANDS_DIR) == []


def test_should_share_one_record_when_commands_save_and_read_session_data():
    assert check_shared_records(COMMANDS_DIR) == []


# --- Negative controls ----------------------------------------------------


def test_should_accept_stored_field_when_command_sends_context_data(tmp_path):
    commands = tmp_path / "commands"
    _write_command(commands, 'context_data={"active_context": "focus"}')

    assert check_context_payloads(commands) == []


def test_should_report_violation_when_context_data_key_is_unstored(tmp_path):
    commands = tmp_path / "commands"
    _write_command(commands, 'context_data={"last_research": {"id": "x"}}')

    violations = check_context_payloads(commands)

    assert violations == ["sample.md:4: update_context drops last_research"]


def test_should_report_violation_when_status_is_not_in_schema(tmp_path):
    commands = tmp_path / "commands"
    _write_command(commands, 'mcp__conport__log_progress\n  "status": "TODO"')

    violations = check_progress_statuses(commands)

    assert violations == [
        "sample.md:5: schema.sql rejects progress status TODO"
    ]


def test_should_ignore_status_when_no_progress_tool_is_named(tmp_path):
    commands = tmp_path / "commands"
    _write_command(commands, '"status": "NOT_RUN"')

    assert check_progress_statuses(commands) == []


def test_should_report_violation_when_reader_uses_another_key(tmp_path):
    commands = tmp_path / "commands"
    commands.mkdir()
    workspace = f'workspace_id="{_WORKSPACE_ROOT}"'
    (commands / "writer.md").write_text(
        f'{workspace},\n  category="research",\n  key="last_research"\n',
        encoding="utf-8",
    )
    (commands / "reader.md").write_text(
        f'{workspace},\n  category="research",\n  key="latest_research"\n',
        encoding="utf-8",
    )
    records = (
        ("research", "last_research", {"writer.md": 1, "reader.md": 1}),
    )

    violations = check_shared_records(commands, records)

    assert violations == [
        "reader.md: expected 1 research/last_research call(s), found 0"
    ]


def test_should_report_violation_when_writer_uses_a_fixed_workspace(tmp_path):
    commands = tmp_path / "commands"
    commands.mkdir()
    (commands / "writer.md").write_text(
        'workspace_id: "/fixed/path"\n'
        '  category: "dx_session"\n'
        '  key: "last_session"\n',
        encoding="utf-8",
    )
    records = (("dx_session", "last_session", {"writer.md": 1}),)

    violations = check_shared_records(commands, records)

    assert violations == [
        "writer.md: expected 1 dx_session/last_session call(s), found 0"
    ]


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
    _write_command(tmp_path, "Use `mcp__pal-stdio__thinkdeep` here.")

    violations = check_mcp_servers(tmp_path, REPO_ROOT, unverified=frozenset())

    assert any(
        "'pal-stdio'" in v and "UNVERIFIED_SERVERS" in v for v in violations
    )


def test_should_report_violation_when_unverified_entry_is_stale(tmp_path):
    _write_command(tmp_path, "Use `mcp__conport__get_context` here.")

    stale = frozenset({"pal-stdio"})

    violations = check_mcp_servers(tmp_path, REPO_ROOT, unverified=stale)

    assert any("UNVERIFIED_SERVERS entry 'pal-stdio'" in v for v in violations)


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
    _write_command(tmp_path, "Use `mcp__pal-stdio__*` here.")

    violations = check_mcp_servers(tmp_path, REPO_ROOT, unverified=frozenset())

    assert any(
        "'pal-stdio'" in v and "UNVERIFIED_SERVERS" in v for v in violations
    )


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


# --- Prose scan and regex-edge negative controls (follow-up W08) -----------


def test_should_report_violation_when_prose_tool_is_not_captured(tmp_path):
    _write_command(tmp_path, "Call: /mcp conport no_such_tool {}")

    violations = check_mcp_tool_refs(tmp_path, REPO_ROOT)

    assert len(violations) == 1
    assert "mcp__conport__no_such_tool" in violations[0]


def test_should_report_violation_when_prose_server_is_unknown(tmp_path):
    _write_command(tmp_path, "Call: /mcp zen execute_workflow {}")

    violations = check_mcp_servers(tmp_path, REPO_ROOT)

    assert any("unknown MCP server 'zen'" in v for v in violations)


def test_should_accept_prose_reference_when_tool_is_captured(tmp_path):
    _write_command(tmp_path, "Call: /mcp conport get_context {}")

    assert check_mcp_tool_refs(tmp_path, REPO_ROOT) == []
    assert check_mcp_servers(tmp_path, REPO_ROOT, frozenset()) == []


def test_should_ignore_slash_mcp_when_embedded_in_a_path(tmp_path):
    _write_command(tmp_path, "See docs/mcp zen thing and a/mcp zen x.")

    assert list(_mcp_refs(tmp_path)) == []


def test_should_report_violation_when_tool_token_is_malformed(tmp_path):
    _write_command(tmp_path, "Use `mcp__conport__get_context--bad` here.")

    violations = check_mcp_tool_refs(tmp_path, REPO_ROOT)

    assert len(violations) == 1
    assert "get_context--bad" in violations[0]


def test_should_report_violation_when_wildcard_has_trailing_garbage(tmp_path):
    _write_command(tmp_path, "Use `mcp__conport__*bad` here.")

    violations = check_mcp_tool_refs(tmp_path, REPO_ROOT)

    assert len(violations) == 1


def test_should_parse_server_name_when_it_contains_an_underscore(tmp_path):
    _write_command(tmp_path, "Use `mcp__MCP_DOCKER__some_tool` here.")

    servers = {s for _loc, s, _t in _mcp_refs(tmp_path)}

    assert servers == {"MCP_DOCKER"}
