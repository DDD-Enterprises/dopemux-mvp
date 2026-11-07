"""B01 / B05: envrc discovery reads only what it needs and fails closed."""

from __future__ import annotations

import logging
import os
from pathlib import Path

import pytest

from dopemux.mcp import http_stdio_bridge as bridge

from .conftest import call_msg, init_msg

ARGV_MEMORY = ["--server", "dope-memory", "--principal", "runner:codex"]
ARGV_CONPORT = ["--server", "conport", "--principal", "runner:codex"]


def test_should_find_envrc_in_the_working_directory(repo: Path):
    found = bridge.discover_profile("dope-memory", repo)

    assert found.envrc_path == repo / ".envrc.dopemux-mcp"
    assert found.base_url.startswith("http://127.0.0.1:")
    assert found.base_url.endswith(str(found.port))


def test_should_walk_up_from_a_subdirectory_to_the_nearest_envrc(repo: Path):
    deep = repo / "src" / "pkg"
    deep.mkdir(parents=True)

    found = bridge.discover_profile("conport", deep)

    assert found.envrc_path == repo / ".envrc.dopemux-mcp"


def test_should_use_the_port_key_of_the_selected_server(tmp_path: Path):
    root = tmp_path / "r"
    root.mkdir()
    (root / ".git").mkdir()
    (root / ".envrc.dopemux-mcp").write_text("DOPE_MEMORY_PORT=3054\nCONPORT_MCP_PORT=3007\n")

    assert bridge.discover_profile("dope-memory", root).port == 3054
    assert bridge.discover_profile("conport", root).port == 3007


def test_should_use_each_servers_own_id_keys(repo: Path):
    memory = bridge.discover_profile("dope-memory", repo)
    conport = bridge.discover_profile("conport", repo)

    assert dict(memory.ids) == {"workspace_id": "wt-memory-ws", "instance_id": "wt-memory-inst"}
    assert dict(conport.ids) == {"workspace_id": "/abs/conport/ws", "instance_id": "wt-conport-inst"}


def test_should_fail_closed_when_no_envrc_exists(tmp_path: Path):
    root = tmp_path / "bare"
    root.mkdir()
    (root / ".git").mkdir()

    with pytest.raises(bridge.BridgeStartupError) as err:
        bridge.discover_profile("dope-memory", root)

    assert "dopemux mcp init" in str(err.value)


def test_should_not_cross_into_another_checkouts_envrc(tmp_path: Path):
    """A worktree under <main>/.worktrees/ has its own .git file and no envrc."""
    main = tmp_path / "main"
    main.mkdir()
    (main / ".git").mkdir()
    (main / ".envrc.dopemux-mcp").write_text("DOPE_MEMORY_PORT=3054\n")
    worktree = main / ".worktrees" / "feature"
    sub = worktree / "src"
    sub.mkdir(parents=True)
    (worktree / ".git").write_text("gitdir: /elsewhere\n")

    with pytest.raises(bridge.BridgeStartupError) as err:
        bridge.discover_profile("dope-memory", sub)

    assert "dopemux mcp init" in str(err.value)


@pytest.mark.parametrize("line", ["", "DOPE_MEMORY_PORT=", "DOPE_MEMORY_PORT=abc", "DOPE_MEMORY_PORT=70000"])
def test_should_fail_closed_on_a_missing_or_invalid_port(tmp_path: Path, line: str):
    root = tmp_path / "r"
    root.mkdir()
    (root / ".git").mkdir()
    (root / ".envrc.dopemux-mcp").write_text(f"{line}\nCONPORT_MCP_PORT=3007\n")

    with pytest.raises(bridge.BridgeStartupError) as err:
        bridge.discover_profile("dope-memory", root)

    assert "DOPE_MEMORY_PORT" in str(err.value)


def test_should_not_stop_at_the_first_envrc_that_lacks_the_port(tmp_path: Path):
    """Nearest file wins; a missing port there never falls through to an outer file."""
    outer = tmp_path / "outer"
    inner = outer / "inner"
    inner.mkdir(parents=True)
    (outer / ".envrc.dopemux-mcp").write_text("DOPE_MEMORY_PORT=3054\n")
    (inner / ".envrc.dopemux-mcp").write_text("CONPORT_MCP_PORT=3007\n")

    with pytest.raises(bridge.BridgeStartupError):
        bridge.discover_profile("dope-memory", inner)


def test_should_never_keep_or_expose_the_database_password(repo: Path, fake_password: str, monkeypatch):
    before = dict(os.environ)

    found = bridge.discover_profile("dope-memory", repo)

    assert fake_password not in repr(found)
    assert fake_password not in repr(vars(found))
    assert dict(os.environ) == before
    assert not any("PASSWORD" in key or "DATABASE_URL" in key for key in os.environ if key not in before)


def test_should_keep_only_the_selected_servers_keys(repo: Path):
    found = bridge.discover_profile("conport", repo)

    assert set(found.ids) <= {"workspace_id", "instance_id"}
    assert "wt-memory-ws" not in repr(found)


def test_should_not_let_the_password_reach_output_or_logs(
    repo: Path, fake_password: str, fake_server, tokens, run_bridge, caplog
):
    caplog.set_level(logging.DEBUG)

    result = run_bridge(ARGV_MEMORY, [init_msg(1), call_msg(2, "memory_store", {"text": "hi"})])

    assert result.code == 0
    assert fake_password not in result.stdout
    assert fake_password not in result.stderr
    assert fake_password not in caplog.text


def test_should_not_let_the_password_reach_output_on_a_failed_start(
    tmp_path: Path, fake_password: str, run_bridge, tokens, monkeypatch, caplog
):
    root = tmp_path / "r"
    root.mkdir()
    (root / ".git").mkdir()
    (root / ".envrc.dopemux-mcp").write_text(f"POSTGRES_PASSWORD={fake_password}\n")
    monkeypatch.chdir(root)
    caplog.set_level(logging.DEBUG)

    result = run_bridge(ARGV_MEMORY, [init_msg(1)])

    assert result.code != 0
    assert fake_password not in result.stdout + result.stderr + caplog.text


# --- B05: fail-closed startup (stderr message + JSON-RPC error, never an unauthenticated request) ---


def test_should_answer_with_a_jsonrpc_error_when_the_envrc_is_missing(
    tmp_path: Path, monkeypatch, run_bridge, tokens, fake_server
):
    root = tmp_path / "bare"
    root.mkdir()
    (root / ".git").mkdir()
    monkeypatch.chdir(root)

    result = run_bridge(ARGV_MEMORY, [init_msg(7)])

    assert result.code == bridge.EXIT_STARTUP
    assert "dopemux mcp init" in result.stderr
    [reply] = result.lines()
    assert reply["id"] == 7
    assert reply["error"]["code"] == bridge.SERVER_ERROR_CODE
    assert "dopemux mcp init" in reply["error"]["message"]
    assert fake_server.requests == []
    assert tokens == []  # the keychain is not touched when there is nothing to talk to


def test_should_answer_with_a_jsonrpc_error_when_the_port_is_missing(
    tmp_path: Path, monkeypatch, run_bridge, tokens, fake_server
):
    root = tmp_path / "r"
    root.mkdir()
    (root / ".git").mkdir()
    (root / ".envrc.dopemux-mcp").write_text("CONPORT_MCP_PORT=3007\n")
    monkeypatch.chdir(root)

    result = run_bridge(ARGV_MEMORY, [init_msg(3)])

    assert result.code == bridge.EXIT_STARTUP
    assert "DOPE_MEMORY_PORT" in result.stderr
    assert result.lines()[0]["id"] == 3
    assert fake_server.requests == []


def test_should_send_nothing_to_stdout_for_a_notification_before_the_error(
    tmp_path: Path, monkeypatch, run_bridge, tokens
):
    root = tmp_path / "bare"
    root.mkdir()
    (root / ".git").mkdir()
    monkeypatch.chdir(root)

    result = run_bridge(
        ARGV_MEMORY,
        [{"jsonrpc": "2.0", "method": "notifications/initialized"}, init_msg(1)],
    )

    [reply] = result.lines()
    assert reply["id"] == 1


def test_should_exit_nonzero_with_a_stderr_message_when_stdin_closes_first(
    tmp_path: Path, monkeypatch, run_bridge, tokens
):
    root = tmp_path / "bare"
    root.mkdir()
    (root / ".git").mkdir()
    monkeypatch.chdir(root)

    result = run_bridge(ARGV_MEMORY, [])

    assert result.code == bridge.EXIT_STARTUP
    assert result.stdout == ""
    assert "dopemux mcp init" in result.stderr


def test_should_fail_closed_when_the_keychain_has_no_token(repo: Path, fake_server, run_bridge, monkeypatch):
    from dopemux.auth import TokenNotFoundError

    def _missing(principal: str) -> str:
        raise TokenNotFoundError(f"no keychain item for {principal}")

    monkeypatch.setattr(bridge, "get_token", _missing)

    result = run_bridge(ARGV_MEMORY, [init_msg(5)])

    assert result.code == bridge.EXIT_STARTUP
    assert "runner:codex" in result.stderr
    reply = result.lines()[0]
    assert reply["id"] == 5 and reply["error"]["code"] == bridge.SERVER_ERROR_CODE
    assert fake_server.requests == []


def test_should_fail_closed_when_the_keychain_is_locked(repo: Path, fake_server, run_bridge, monkeypatch):
    from dopemux.auth import KeychainError

    def _locked(principal: str) -> str:
        raise KeychainError("keychain locked")

    monkeypatch.setattr(bridge, "get_token", _locked)

    result = run_bridge(ARGV_MEMORY, [init_msg(5)])

    assert result.code == bridge.EXIT_STARTUP
    assert "keychain locked" in result.stderr
    assert fake_server.requests == []


def test_should_fail_closed_on_an_invalid_principal(repo: Path, fake_server, run_bridge, monkeypatch):
    from dopemux.auth import keychain

    def _no_keychain(*args, **kwargs):
        raise AssertionError("the keychain must not be reached for an invalid principal")

    monkeypatch.setattr(keychain, "_run", _no_keychain)

    result = run_bridge(["--server", "dope-memory", "--principal", "not-a-principal"], [init_msg(5)])

    assert result.code == bridge.EXIT_STARTUP
    assert fake_server.requests == []
    assert result.lines()[0]["error"]["code"] == bridge.SERVER_ERROR_CODE


def test_should_refuse_an_empty_token(repo: Path, fake_server, run_bridge, monkeypatch):
    monkeypatch.setattr(bridge, "get_token", lambda principal: "")

    result = run_bridge(ARGV_MEMORY, [init_msg(5)])

    assert result.code == bridge.EXIT_STARTUP
    assert fake_server.requests == []


def test_should_ask_the_helper_for_the_named_principal_only(repo: Path, fake_server, tokens, run_bridge):
    run_bridge(ARGV_CONPORT, [init_msg(1)])

    assert tokens == ["runner:codex"]
