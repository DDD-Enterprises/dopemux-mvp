"""W07 B01/B02/B05: the real Codex gate, released servers and the stdio-route entries.

No test here reads the keychain, starts a server or opens a socket: the gate's
two seams (`fleet_catalog._fetch_health`, `fleet_catalog.get_token`) are
monkeypatched, and every file lives under pytest's tmp_path.
"""

from __future__ import annotations

import json
import tomllib
from pathlib import Path
from typing import Any, Dict

import pytest
from click.testing import CliRunner

from dopemux.auth import KeychainError, TokenNotFoundError
from dopemux.commands import mcp_commands
from dopemux.mcp import fleet_catalog, http_stdio_bridge

REPO_ROOT = Path(__file__).resolve().parents[3]
FAKE_TOKEN = "fake-token-for-w07-tests-only-0123456789"  # generated for tests; not a real secret

GOOD_MEMORY: Dict[str, Any] = {"auth_mode": "enforce", "identity_required_writes": True}
GOOD_CONPORT: Dict[str, Any] = {
    "auth_mode": "enforce",
    "identity_required_writes": True,
    "auth_principal_column": "ok",
}
MEMORY_PORT = 43120
CONPORT_PORT = 43104


# --------------------------------------------------------------------------
# fixtures
# --------------------------------------------------------------------------


@pytest.fixture()
def checkout(tmp_path: Path) -> Path:
    root = tmp_path / "checkout"
    root.mkdir()
    (root / ".git").mkdir()
    (root / ".envrc.dopemux-mcp").write_text(
        f"export DOPE_MEMORY_PORT={MEMORY_PORT}\n"
        f"export CONPORT_HTTP_PORT={CONPORT_PORT}\n"
        "export POSTGRES_PASSWORD=fake-password-must-never-be-read\n"
    )
    return root


@pytest.fixture()
def seams(monkeypatch):
    """Healthy servers and a present token; tests overwrite pieces of `state`."""
    state: Dict[str, Any] = {
        "health": {MEMORY_PORT: dict(GOOD_MEMORY), CONPORT_PORT: dict(GOOD_CONPORT)},
        "token": FAKE_TOKEN,
        "probed_ports": [],
        "token_principals": [],
    }

    def fake_fetch(port: int) -> Dict[str, Any]:
        state["probed_ports"].append(port)
        value = state["health"][port]
        if isinstance(value, Exception):
            raise value
        return value

    def fake_get_token(principal: str) -> str:
        state["token_principals"].append(principal)
        if isinstance(state["token"], Exception):
            raise state["token"]
        return state["token"]

    monkeypatch.setattr(mcp_commands, "_fetch_health", fake_fetch)
    monkeypatch.setattr(mcp_commands, "get_token", fake_get_token)
    return state


def _real_catalog() -> Dict[str, Any]:
    return fleet_catalog.load_root_catalog(REPO_ROOT)


# --------------------------------------------------------------------------
# gate: each check failing alone, all passing
# --------------------------------------------------------------------------


def test_should_hold_when_both_servers_enforce_and_the_token_exists(checkout, seams):
    gate = mcp_commands.evaluate_codex_memory_gate(checkout)

    assert gate.ok is True
    assert gate.failures == ()
    assert sorted(seams["probed_ports"]) == sorted([MEMORY_PORT, CONPORT_PORT])
    assert seams["token_principals"] == ["runner:codex"]


def test_should_never_carry_the_token_in_the_result(checkout, seams):
    gate = mcp_commands.evaluate_codex_memory_gate(checkout)

    assert FAKE_TOKEN not in repr(gate)
    assert "fake-password-must-never-be-read" not in repr(gate)


@pytest.mark.parametrize(
    "server_port, key, value, needle",
    [
        (MEMORY_PORT, "auth_mode", "off", "dope-memory"),
        (MEMORY_PORT, "auth_mode", "enforced", "dope-memory"),
        (MEMORY_PORT, "auth_mode", None, "dope-memory"),
        (MEMORY_PORT, "identity_required_writes", False, "dope-memory"),
        (MEMORY_PORT, "identity_required_writes", "true", "dope-memory"),
        (CONPORT_PORT, "auth_mode", "off", "conport"),
        (CONPORT_PORT, "identity_required_writes", False, "conport"),
        (CONPORT_PORT, "auth_principal_column", "missing", "conport"),
        (CONPORT_PORT, "auth_principal_column", "partial", "conport"),
    ],
)
def test_should_fail_when_one_health_field_is_wrong(checkout, seams, server_port, key, value, needle):
    seams["health"][server_port][key] = value

    gate = mcp_commands.evaluate_codex_memory_gate(checkout)

    assert gate.ok is False
    assert len(gate.failures) == 1
    assert needle in gate.failures[0]
    assert key in gate.failures[0]


def test_should_name_the_new_accepted_modes_when_auth_mode_is_off(checkout, seams):
    seams["health"][MEMORY_PORT]["auth_mode"] = "off"

    gate = mcp_commands.evaluate_codex_memory_gate(checkout)

    assert gate.ok is False
    assert "auth_mode is 'off', expected 'log' or 'enforce'" in gate.failures[0]


@pytest.mark.parametrize("mode", ["log", "enforce"])
@pytest.mark.parametrize("port", [MEMORY_PORT, CONPORT_PORT])
def test_should_hold_for_either_accepted_mode_on_either_server(checkout, seams, port, mode):
    seams["health"][port]["auth_mode"] = mode

    gate = mcp_commands.evaluate_codex_memory_gate(checkout)

    assert gate.ok is True
    assert gate.failures == ()


def test_should_still_require_identity_required_writes_in_log_mode(checkout, seams):
    seams["health"][MEMORY_PORT].update(auth_mode="log", identity_required_writes=False)

    gate = mcp_commands.evaluate_codex_memory_gate(checkout)

    assert gate.ok is False
    assert "identity_required_writes" in gate.failures[0]


def test_should_still_require_the_conport_principal_column_in_log_mode(checkout, seams):
    seams["health"][CONPORT_PORT].update(auth_mode="log", auth_principal_column="missing")

    gate = mcp_commands.evaluate_codex_memory_gate(checkout)

    assert gate.ok is False
    assert "auth_principal_column" in gate.failures[0]


def test_should_still_require_the_runner_token_in_log_mode(checkout, seams):
    seams["health"][MEMORY_PORT]["auth_mode"] = "log"
    seams["health"][CONPORT_PORT]["auth_mode"] = "log"
    seams["token"] = TokenNotFoundError("no item")

    gate = mcp_commands.evaluate_codex_memory_gate(checkout)

    assert gate.ok is False
    assert len(gate.failures) == 1
    assert "gate check 2" in gate.failures[0]


def test_should_report_which_servers_are_in_log_mode(checkout, seams):
    seams["health"][CONPORT_PORT]["auth_mode"] = "log"

    gate = mcp_commands.evaluate_codex_memory_gate(checkout)

    assert gate.log_mode_servers == ("conport",)
    seams["health"][CONPORT_PORT]["auth_mode"] = "enforce"
    assert mcp_commands.evaluate_codex_memory_gate(checkout).log_mode_servers == ()


def test_should_fail_when_a_required_health_field_is_absent(checkout, seams):
    del seams["health"][MEMORY_PORT]["identity_required_writes"]

    gate = mcp_commands.evaluate_codex_memory_gate(checkout)

    assert gate.ok is False
    assert "identity_required_writes" in gate.failures[0]


def test_should_not_require_a_principal_column_field_from_dope_memory(checkout, seams):
    assert "auth_principal_column" not in seams["health"][MEMORY_PORT]

    assert mcp_commands.evaluate_codex_memory_gate(checkout).ok is True


def test_should_fail_when_a_health_endpoint_is_unreachable(checkout, seams):
    seams["health"][CONPORT_PORT] = mcp_commands._HealthProbeError("connection refused")

    gate = mcp_commands.evaluate_codex_memory_gate(checkout)

    assert gate.ok is False
    assert "conport" in gate.failures[0]
    assert "connection refused" in gate.failures[0]


def test_should_fail_closed_without_an_envrc(tmp_path, seams):
    bare = tmp_path / "bare"
    bare.mkdir()
    (bare / ".git").mkdir()

    gate = mcp_commands.evaluate_codex_memory_gate(bare)

    assert gate.ok is False
    assert any("dope-memory" in f for f in gate.failures)
    assert any("conport" in f for f in gate.failures)
    assert any("dopemux mcp init" in f for f in gate.failures)
    assert seams["probed_ports"] == []


def test_should_fail_when_the_envrc_lacks_one_port(checkout, seams):
    (checkout / ".envrc.dopemux-mcp").write_text(f"export DOPE_MEMORY_PORT={MEMORY_PORT}\n")

    gate = mcp_commands.evaluate_codex_memory_gate(checkout)

    assert gate.ok is False
    assert len(gate.failures) == 1
    assert "CONPORT_HTTP_PORT" in gate.failures[0]


def test_should_fail_when_no_token_exists_for_the_runner(checkout, seams):
    seams["token"] = TokenNotFoundError("no item")

    gate = mcp_commands.evaluate_codex_memory_gate(checkout)

    assert gate.ok is False
    assert len(gate.failures) == 1
    assert "runner:codex" in gate.failures[0]
    assert "TokenNotFoundError" in gate.failures[0]
    assert "dopemux auth issue runner:codex" in gate.failures[0]


def test_should_fail_and_name_any_other_auth_error(checkout, seams):
    seams["token"] = KeychainError("keychain locked")

    gate = mcp_commands.evaluate_codex_memory_gate(checkout)

    assert gate.ok is False
    assert "KeychainError" in gate.failures[0]


def test_should_report_every_failed_check_together(checkout, seams):
    seams["health"][MEMORY_PORT]["auth_mode"] = "off"
    seams["health"][CONPORT_PORT]["auth_principal_column"] = "missing"
    seams["token"] = TokenNotFoundError("no item")

    gate = mcp_commands.evaluate_codex_memory_gate(checkout)

    assert len(gate.failures) == 3


# --------------------------------------------------------------------------
# generate: write vs preview, --allow-sequenced
# --------------------------------------------------------------------------


@pytest.fixture()
def generate_env(tmp_path, monkeypatch, seams):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    (repo / ".envrc.dopemux-mcp").write_text(
        f"export DOPE_MEMORY_PORT={MEMORY_PORT}\nexport CONPORT_HTTP_PORT={CONPORT_PORT}\n"
    )
    monkeypatch.setattr(mcp_commands, "get_repo_root", lambda fallback_cwd=False, **_kw: str(repo))
    out = tmp_path / "out"
    return repo, out


def _invoke(out: Path, *extra: str):
    # The real catalog declares profiles, so the in-repo agent targets (and with
    # them .codex/config.toml) are only produced in agent-matrix mode.
    return CliRunner().invoke(
        mcp_commands.mcp_generate_cmd,
        ["--agent-matrix", "--apply", "--output-dir", str(out), *extra],
    )


def test_should_write_the_codex_config_when_the_gate_holds(generate_env):
    repo, out = generate_env

    result = _invoke(out)

    assert result.exit_code == 0, result.output
    text = (repo / ".codex" / "config.toml").read_text()
    servers = tomllib.loads(text)["mcp_servers"]
    assert set(servers) == {"conport", "dope-memory"}


LOG_NOTICE_NEEDLES = (
    "log mode",
    "runner:codex",
    "without a token",
    "unverified",
    "until enforce",
)


def test_should_print_the_log_mode_notice_once_when_a_server_is_in_log_mode(generate_env, seams):
    repo, out = generate_env
    seams["health"][MEMORY_PORT]["auth_mode"] = "log"

    result = _invoke(out)

    assert result.exit_code == 0, result.output
    assert (repo / ".codex" / "config.toml").is_file()
    notice_lines = [line for line in result.output.splitlines() if "log mode" in line]
    assert len(notice_lines) == 1
    for needle in LOG_NOTICE_NEEDLES:
        assert needle in " ".join(result.output.split())
    assert "dope-memory" in notice_lines[0]


def test_should_print_one_notice_naming_both_servers_when_both_are_in_log_mode(generate_env, seams):
    _repo, out = generate_env
    seams["health"][MEMORY_PORT]["auth_mode"] = "log"
    seams["health"][CONPORT_PORT]["auth_mode"] = "log"

    result = _invoke(out)

    assert result.exit_code == 0, result.output
    assert sum("log mode" in line for line in result.output.splitlines()) == 1
    assert "conport" in result.output and "dope-memory" in result.output


def test_should_print_the_notice_for_a_mixed_log_and_enforce_pair(generate_env, seams):
    repo, out = generate_env
    seams["health"][CONPORT_PORT]["auth_mode"] = "log"

    result = _invoke(out)

    assert result.exit_code == 0, result.output
    assert (repo / ".codex" / "config.toml").is_file()
    assert sum("log mode" in line for line in result.output.splitlines()) == 1


def test_should_print_no_log_notice_when_both_servers_enforce(generate_env):
    repo, out = generate_env

    result = _invoke(out)

    assert result.exit_code == 0, result.output
    assert (repo / ".codex" / "config.toml").is_file()
    assert "log mode" not in result.output
    assert "unverified" not in result.output


def test_should_print_no_log_notice_when_the_gate_fails(generate_env, seams):
    _repo, out = generate_env
    seams["health"][MEMORY_PORT]["auth_mode"] = "log"
    seams["token"] = TokenNotFoundError("none")

    result = _invoke(out)

    assert "Refused to write .codex/config.toml" in result.output
    assert "Memory servers in log mode" not in result.output


def test_should_keep_unreleased_servers_out_of_the_written_file(generate_env):
    repo, out = generate_env

    _invoke(out)

    written = (repo / ".codex" / "config.toml").read_text()
    for name in ("task-orchestrator", "serena", "dope-context", "gpt-researcher", "pal-stdio"):
        assert f'"{name}"' not in written


def test_should_still_preview_unreleased_servers_without_writing_them(generate_env):
    repo, out = generate_env

    _invoke(out)

    preview = tomllib.loads((out / "codex" / "config.toml").read_text())["mcp_servers"]
    assert {"conport", "dope-memory", "pal-stdio"} <= set(preview)
    assert "task-orchestrator" not in preview


@pytest.mark.parametrize(
    "break_it, needle",
    [
        (lambda s: s["health"][MEMORY_PORT].update(auth_mode="off"), "dope-memory"),
        (lambda s: s["health"][CONPORT_PORT].update(identity_required_writes=False), "conport"),
        (lambda s: s["health"][CONPORT_PORT].update(auth_principal_column="missing"), "auth_principal_column"),
        (lambda s: s.update(token=TokenNotFoundError("none")), "runner:codex"),
    ],
)
def test_should_write_only_the_preview_and_name_the_failed_check(generate_env, seams, break_it, needle):
    repo, out = generate_env
    break_it(seams)

    result = _invoke(out)

    assert result.exit_code == 0, result.output
    assert not (repo / ".codex" / "config.toml").exists()
    assert (out / "codex" / "config.toml").is_file()
    assert needle in result.output
    assert "Refused to write .codex/config.toml" in result.output


def test_should_not_touch_an_existing_codex_config_when_the_gate_fails(generate_env, seams):
    repo, out = generate_env
    (repo / ".codex").mkdir()
    (repo / ".codex" / "config.toml").write_text('model = "x"\n')
    seams["health"][MEMORY_PORT]["auth_mode"] = "off"

    _invoke(out)

    assert (repo / ".codex" / "config.toml").read_text() == 'model = "x"\n'


def test_should_preserve_user_keys_when_the_gate_holds(generate_env):
    repo, out = generate_env
    (repo / ".codex").mkdir()
    (repo / ".codex" / "config.toml").write_text('model = "x"\n\n[agents]\nmax_threads = 4\n')

    result = _invoke(out)

    assert result.exit_code == 0, result.output
    parsed = tomllib.loads((repo / ".codex" / "config.toml").read_text())
    assert parsed["model"] == "x"
    assert parsed["agents"]["max_threads"] == 4
    assert set(parsed["mcp_servers"]) == {"conport", "dope-memory"}


def test_should_reject_allow_sequenced_and_name_the_new_gate(generate_env, seams):
    repo, out = generate_env

    result = _invoke(out, "--allow-sequenced")

    assert result.exit_code != 0
    assert "--allow-sequenced" in result.output
    assert "auth_mode" in result.output
    assert "'log' or 'enforce'" in " ".join(result.output.split())
    assert "runner:codex" in result.output
    assert not (repo / ".codex" / "config.toml").exists()
    assert not out.exists()
    assert seams["probed_ports"] == []
    assert seams["token_principals"] == []


def test_should_reject_allow_sequenced_even_when_the_gate_would_hold(generate_env):
    repo, out = generate_env

    result = _invoke(out, "--allow-sequenced")

    assert result.exit_code != 0
    assert not (repo / ".codex" / "config.toml").exists()


def test_should_not_probe_or_read_the_keychain_on_a_dry_run(generate_env, seams):
    _repo, out = generate_env

    result = CliRunner().invoke(
        mcp_commands.mcp_generate_cmd, ["--agent-matrix", "--output-dir", str(out)]
    )

    assert result.exit_code == 0, result.output
    assert "Dry-run only" in result.output
    assert seams["probed_ports"] == []
    assert seams["token_principals"] == []


def test_should_list_the_memory_gate_in_generate_help():
    result = CliRunner().invoke(mcp_commands.mcp_generate_cmd, ["--help"])

    assert result.exit_code == 0
    assert "--allow-sequenced" in result.output
    assert "removed" in result.output.lower()


# --------------------------------------------------------------------------
# rendered entries
# --------------------------------------------------------------------------

BRIDGE_ARGS = ["-m", "dopemux.mcp.http_stdio_bridge"]


def test_should_render_the_codex_entries_through_the_stdio_route():
    region = fleet_catalog.render_codex_managed_region(_real_catalog(), released_only=True)
    body = "\n".join(
        line for line in region.splitlines() if not line.startswith("#")
    )
    servers = tomllib.loads(body)["mcp_servers"]

    assert servers == {
        "conport": {
            "command": "python",
            "args": [*BRIDGE_ARGS, "--server", "conport", "--principal", "runner:codex"],
        },
        "dope-memory": {
            "command": "python",
            "args": [*BRIDGE_ARGS, "--server", "dope-memory", "--principal", "runner:codex"],
        },
    }


def test_should_render_no_cwd_env_or_token_in_the_codex_entries():
    region = fleet_catalog.render_codex_managed_region(_real_catalog(), released_only=True)

    assert "cwd" not in region
    assert "env" not in region
    assert "token" not in region.lower().replace("--principal", "")


def test_should_render_the_codex_bridge_entries_despite_the_per_worktree_scope():
    catalog = _real_catalog()
    assert catalog["servers"]["conport"]["scope"] == "per-worktree"
    assert catalog["servers"]["dope-memory"]["scope"] == "per-worktree"

    lines = fleet_catalog._codex_server_lines(catalog)

    assert '[mcp_servers."conport"]' in lines
    assert '[mcp_servers."dope-memory"]' in lines


def test_should_keep_the_per_worktree_skip_for_other_servers():
    catalog = _real_catalog()
    assert catalog["servers"]["task-orchestrator"]["scope"] == "per-worktree"

    for released_only in (False, True):
        lines = fleet_catalog._codex_server_lines(catalog, released_only=released_only)
        assert '[mcp_servers."task-orchestrator"]' not in lines


def test_should_skip_a_per_worktree_server_that_is_not_a_memory_server():
    catalog = {
        "version": 1,
        "defaults": {"per_worktree": []},
        "servers": {
            "other-local": {
                "scope": "per-worktree",
                "transport": "http",
                "url_template": "http://localhost:1/mcp",
                "agents": {"codex": "full"},
            }
        },
    }

    assert fleet_catalog._codex_server_lines(catalog) == []


def test_should_not_render_a_bridge_entry_for_a_server_closed_to_codex():
    catalog = _real_catalog()
    catalog["servers"]["dope-memory"]["agents"]["codex"] = "none"

    lines = fleet_catalog._codex_server_lines(catalog)

    assert '[mcp_servers."dope-memory"]' not in lines
    assert '[mcp_servers."conport"]' in lines


def test_should_keep_the_default_claude_code_rendering_on_direct_http():
    """AMENDMENT_02: Claude Code stays on direct HTTP/SSE in 2A; the tracked .mcp.json still matches."""
    catalog = _real_catalog()
    local = mcp_commands._build_local_mcp_json(["conport", "dope-memory"], catalog)["mcpServers"]

    assert local["conport"]["type"] == "sse"
    assert local["conport"]["url"] == "http://localhost:${CONPORT_MCP_PORT:-3005}/sse"
    assert local["dope-memory"]["type"] == "http"
    assert local["dope-memory"]["url"] == "http://localhost:${DOPE_MEMORY_PORT:-3020}/mcp"
    for entry in local.values():
        assert "command" not in entry
        assert "runner:claude" not in json.dumps(entry)

    committed = json.loads((REPO_ROOT / ".mcp.json").read_text(encoding="utf-8"))
    expected = mcp_commands._build_local_mcp_json(list(catalog["defaults"]["per_worktree"]), catalog)
    assert committed == expected


def test_should_render_the_claude_code_bridge_entry_through_its_own_function():
    catalog = _real_catalog()

    for name in ("conport", "dope-memory"):
        entry = mcp_commands._render_claude_memory_bridge_entry(name, catalog["servers"][name])
        assert entry["type"] == "stdio"
        assert entry["command"] == "python"
        assert entry["args"] == [*BRIDGE_ARGS, "--server", name, "--principal", "runner:claude"]
        assert entry["description"] == catalog["servers"][name]["description"]
        assert "url" not in entry
        assert "env" not in entry


def test_should_refuse_a_claude_code_bridge_entry_for_a_server_without_a_bridge_profile():
    import click

    catalog = _real_catalog()

    with pytest.raises(click.ClickException, match="no stdio bridge profile"):
        mcp_commands._render_claude_memory_bridge_entry(
            "task-orchestrator", catalog["servers"]["task-orchestrator"]
        )


def test_should_not_wire_the_claude_code_bridge_function_into_any_default_path():
    import inspect

    for fn in (
        mcp_commands._render_local_entry,
        mcp_commands._build_local_mcp_json,
        mcp_commands._ensure_fast_problems,
        mcp_commands.mcp_init_cmd.callback,
        mcp_commands.mcp_add_cmd.callback,
    ):
        assert "_render_claude_memory_bridge_entry" not in inspect.getsource(fn)


def test_should_leave_the_task_orchestrator_entry_unchanged():
    local = mcp_commands._build_local_mcp_json(["task-orchestrator"], _real_catalog())["mcpServers"]

    assert local["task-orchestrator"]["type"] == "http"
    assert local["task-orchestrator"]["url"].startswith("http://127.0.0.1:")


def test_should_render_entries_the_real_bridge_parser_accepts():
    parser = http_stdio_bridge.build_parser()
    servers = _real_catalog()["servers"]
    local = {
        name: mcp_commands._render_claude_memory_bridge_entry(name, servers[name])
        for name in ("conport", "dope-memory")
    }

    for name, entry in local.items():
        parsed = parser.parse_args(entry["args"][len(BRIDGE_ARGS):])
        assert parsed.server == name
        assert parsed.principal == "runner:claude"


def test_should_cover_exactly_the_servers_the_bridge_has_profiles_for():
    assert set(mcp_commands.MEMORY_BRIDGE_SERVERS) == set(http_stdio_bridge.PROFILES)


def test_should_use_the_interpreter_the_legacy_bridge_mode_uses():
    from dopemux.config.manager import ConfigManager
    from dopemux.mcp.registry import MCPServerDefinition
    from unittest.mock import Mock

    server = MCPServerDefinition(
        name="http-server",
        transport="http",
        docker={"service": "s", "compose_file": "compose.yml", "port": 8888},
    )
    registry = Mock()
    registry.get_server.return_value = server
    legacy = ConfigManager()._generate_server_config(
        registry, "http-server", "docker", docker_compose_bin="docker compose"
    )

    catalog = _real_catalog()
    claude_entry = mcp_commands._render_claude_memory_bridge_entry("conport", catalog["servers"]["conport"])
    codex_command, _args = mcp_commands._memory_bridge_command("conport", "runner:codex")

    assert claude_entry["command"] == legacy["command"]
    assert codex_command == legacy["command"]


# --------------------------------------------------------------------------
# ensure drift detection follows the new defaults
# --------------------------------------------------------------------------


def _ensure_problems(repo: Path, catalog: Dict[str, Any]):
    return mcp_commands._ensure_fast_problems(catalog, repo, repo)


def test_should_accept_an_mcp_json_rendered_from_the_new_defaults(tmp_path):
    catalog = _real_catalog()
    repo = tmp_path / "r"
    repo.mkdir()
    rendered = mcp_commands._build_local_mcp_json(list(catalog["defaults"]["per_worktree"]), catalog)
    import json

    (repo / mcp_commands.PROJECT_MCP_FILENAME).write_text(json.dumps(rendered))

    problems = _ensure_problems(repo, catalog)

    assert not any("does not match catalog defaults" in p for p in problems)


def test_should_flag_a_bridge_entry_in_mcp_json_as_drift_while_it_is_not_the_default(tmp_path):
    catalog = _real_catalog()
    repo = tmp_path / "r"
    repo.mkdir()
    rendered = mcp_commands._build_local_mcp_json(list(catalog["defaults"]["per_worktree"]), catalog)
    rendered["mcpServers"]["conport"] = mcp_commands._render_claude_memory_bridge_entry(
        "conport", catalog["servers"]["conport"]
    )
    import json

    (repo / mcp_commands.PROJECT_MCP_FILENAME).write_text(json.dumps(rendered))

    problems = _ensure_problems(repo, catalog)

    assert any("does not match catalog defaults" in p for p in problems)


# --------------------------------------------------------------------------
# parity gate and merge defaults
# --------------------------------------------------------------------------


def test_should_pass_parity_for_a_region_written_with_released_only(tmp_path, monkeypatch):
    catalog = _real_catalog()
    repo = tmp_path / "r"
    (repo / ".codex").mkdir(parents=True)
    merged = fleet_catalog.merge_codex_config_toml(None, catalog, released_only=True)
    (repo / ".codex" / "config.toml").write_text(merged)
    monkeypatch.setattr(fleet_catalog, "load_root_catalog", lambda _root: catalog)

    assert fleet_catalog.validate_codex_config_toml_parity(repo) == []


def test_should_flag_a_region_that_carries_unreleased_servers(tmp_path, monkeypatch):
    catalog = _real_catalog()
    repo = tmp_path / "r"
    (repo / ".codex").mkdir(parents=True)
    merged = fleet_catalog.merge_codex_config_toml(None, catalog)  # default: every renderable row
    assert '"pal-stdio"' in merged
    (repo / ".codex" / "config.toml").write_text(merged)
    monkeypatch.setattr(fleet_catalog, "load_root_catalog", lambda _root: catalog)

    errors = fleet_catalog.validate_codex_config_toml_parity(repo)

    assert errors and "does not match" in errors[0]


# --------------------------------------------------------------------------
# catalog
# --------------------------------------------------------------------------


def test_should_keep_the_two_catalogs_byte_identical():
    root = (REPO_ROOT / "mcp_catalog.yaml").read_bytes()
    bundled = (REPO_ROOT / "src" / "dopemux" / "mcp" / "default_catalog.yaml").read_bytes()

    assert root == bundled


def test_should_release_only_the_memory_servers_to_codex_in_the_catalog():
    servers = _real_catalog()["servers"]

    released = {n for n, s in servers.items() if isinstance(s.get("agents"), dict) and s["agents"].get("codex") == "full"}
    sequenced = {
        n for n, s in servers.items() if isinstance(s.get("agents"), dict) and s["agents"].get("codex") == "full-sequenced"
    }

    assert released == {"conport", "dope-memory"}
    assert sequenced == {"task-orchestrator", "serena", "dope-context", "gpt-researcher", "pal-stdio"}


def test_should_say_log_or_enforce_in_the_help_text_and_the_preview_header():
    help_text = " ".join(
        CliRunner().invoke(mcp_commands.mcp_generate_cmd, ["--help"]).output.split()
    )
    header = " ".join(fleet_catalog.render_codex_config_fragment(_real_catalog()).replace("# ", "").split())

    assert "auth_mode log or enforce" in help_text
    assert "auth_mode log or enforce" in header
    assert "enforce and identity" not in help_text
    assert "auth_mode enforce" not in header


def test_should_not_name_the_removed_orchestrator_setting_in_generator_code_or_output():
    for relative in ("src/dopemux/mcp/fleet_catalog.py", "src/dopemux/commands/mcp_commands.py"):
        assert "actor_authentication" not in (REPO_ROOT / relative).read_text(encoding="utf-8")
    assert "actor_authentication" not in fleet_catalog.render_codex_config_fragment(_real_catalog())
    assert "allow-sequenced" not in fleet_catalog.render_codex_managed_region(_real_catalog(), released_only=True)
