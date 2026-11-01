"""B03: streamable-HTTP handshake, bearer on every request, 401/403 stop."""

from __future__ import annotations

import logging
from pathlib import Path

import pytest

from dopemux.mcp import http_stdio_bridge as bridge

from .conftest import SESSION_ID, call_msg, init_msg, initialized_msg, list_msg

ARGV_MEMORY = ["--server", "dope-memory", "--principal", "runner:codex"]


def test_should_post_to_slash_mcp_with_both_accept_types(repo, fake_server, tokens, run_bridge):
    run_bridge(ARGV_MEMORY, [init_msg(1)])

    [req] = fake_server.requests
    assert req.path == "/mcp"
    assert req.headers["accept"] == "application/json, text/event-stream"
    assert req.headers["content-type"] == "application/json"


def test_should_parse_an_sse_framed_initialize_response(repo, fake_server, tokens, run_bridge):
    fake_server.sse_responses = True

    result = run_bridge(ARGV_MEMORY, [init_msg(1)])

    assert result.code == 0
    [reply] = result.lines()
    assert reply["id"] == 1
    assert reply["result"]["serverInfo"]["name"] == "fake"


def test_should_parse_a_plain_json_response(repo, fake_server, tokens, run_bridge):
    fake_server.sse_responses = False

    result = run_bridge(ARGV_MEMORY, [init_msg(1), list_msg(2)])

    replies = result.lines()
    assert [r["id"] for r in replies] == [1, 2]
    assert replies[1]["result"]["tools"]


def test_should_echo_the_session_id_on_later_requests(repo, fake_server, tokens, run_bridge):
    run_bridge(ARGV_MEMORY, [init_msg(1), initialized_msg(), list_msg(2)])

    first, second, third = fake_server.requests
    assert "mcp-session-id" not in first.headers
    assert second.headers["mcp-session-id"] == SESSION_ID
    assert third.headers["mcp-session-id"] == SESSION_ID


def test_should_print_nothing_for_notifications_initialized(repo, fake_server, tokens, run_bridge):
    result = run_bridge(ARGV_MEMORY, [init_msg(1), initialized_msg()])

    assert result.code == 0
    assert [r["id"] for r in result.lines()] == [1]  # one line: the initialize reply
    assert fake_server.bodies("notifications/initialized")


def test_should_send_the_bearer_token_on_every_request(repo, fake_server, fake_token, tokens, run_bridge):
    run_bridge(
        ARGV_MEMORY,
        [init_msg(1), initialized_msg(), list_msg(2), call_msg(3, "memory_store", {"text": "x"})],
    )

    assert len(fake_server.requests) >= 4
    for req in fake_server.requests:
        assert req.headers["authorization"] == f"Bearer {fake_token}"


def test_should_never_send_a_request_without_authorization(repo, fake_server, tokens, run_bridge):
    run_bridge(ARGV_MEMORY, [init_msg(1), list_msg(2)])

    assert all("authorization" in r.headers for r in fake_server.requests)


def test_should_not_leak_the_token_to_stdout_stderr_or_logs(
    repo, fake_server, fake_token, tokens, run_bridge, caplog
):
    caplog.set_level(logging.DEBUG)

    result = run_bridge(
        ARGV_MEMORY,
        [init_msg(1), initialized_msg(), list_msg(2), call_msg(3, "memory_store", {"text": "x"})],
    )

    assert fake_token not in result.stdout
    assert fake_token not in result.stderr
    assert fake_token not in caplog.text


def test_should_reinitialize_once_when_the_session_has_expired(repo, fake_server, tokens, run_bridge, monkeypatch):
    # Expire the server session just before the third message reaches it.
    original = bridge._StreamableClient.send
    state = {"count": 0}

    def _send(self, message):
        state["count"] += 1
        if state["count"] == 3:
            fake_server.expire_sessions()
        return original(self, message)

    monkeypatch.setattr(bridge._StreamableClient, "send", _send)

    result = run_bridge(ARGV_MEMORY, [init_msg(1), initialized_msg(), list_msg(2)])

    assert result.code == 0
    replies = result.lines()
    assert [r["id"] for r in replies] == [1, 2]  # re-initialization never reaches the client
    assert len(fake_server.bodies("initialize")) == 2
    assert len(fake_server.bodies("notifications/initialized")) == 2
    assert len(fake_server.bodies("tools/list")) == 2  # the expired attempt and the retry


def test_should_return_a_jsonrpc_error_when_the_session_is_gone_and_no_initialize_was_seen(
    repo, fake_server, tokens, run_bridge
):
    result = run_bridge(ARGV_MEMORY, [list_msg(2)])

    [reply] = result.lines()
    assert reply["id"] == 2
    assert reply["error"]["code"] == bridge.SERVER_ERROR_CODE
    assert result.code == 0


@pytest.mark.parametrize("status", [401, 403])
def test_should_stop_on_401_or_403_with_a_clear_stderr_line(
    repo, fake_server, fake_token, tokens, run_bridge, status
):
    fake_server.auth_status = status

    result = run_bridge(ARGV_MEMORY, [init_msg(1), list_msg(2)])

    assert result.code == bridge.EXIT_AUTH
    assert str(status) in result.stderr
    assert "runner:codex" in result.stderr
    [reply] = result.lines()  # the failed request gets an error; the second is never sent
    assert reply["id"] == 1
    assert reply["error"]["code"] == bridge.SERVER_ERROR_CODE
    assert len(fake_server.requests) == 1
    assert fake_token not in result.stdout + result.stderr


def test_should_stop_when_the_server_rejects_the_token(repo, fake_server, tokens, run_bridge, monkeypatch):
    monkeypatch.setattr(bridge, "get_token", lambda principal: "fake-wrong-token-0000000000")

    result = run_bridge(ARGV_MEMORY, [init_msg(1), list_msg(2)])

    assert result.code == bridge.EXIT_AUTH
    assert len(fake_server.requests) == 1
    assert "wrong-token" not in result.stdout + result.stderr


def test_should_report_a_connection_error_as_a_jsonrpc_error(tmp_path: Path, monkeypatch, tokens, run_bridge):
    root = tmp_path / "r"
    root.mkdir()
    (root / ".git").mkdir()
    (root / ".envrc.dopemux-mcp").write_text("DOPE_MEMORY_PORT=1\n")  # nothing listens on port 1
    monkeypatch.chdir(root)

    result = run_bridge(ARGV_MEMORY, [init_msg(4)])

    [reply] = result.lines()
    assert reply["id"] == 4
    assert reply["error"]["message"] == "Bridge transport error"


def test_should_report_parse_errors_without_contacting_the_server(repo, fake_server, tokens, monkeypatch, capsys):
    import io

    monkeypatch.setattr("sys.stdin", io.StringIO("not json\n[1]\n"))

    code = bridge.main(ARGV_MEMORY)

    out = capsys.readouterr().out.splitlines()
    assert code == 0
    assert '"code":-32700' in out[0]
    assert '"code":-32600' in out[1]
    assert fake_server.requests == []


def test_should_not_follow_redirects_or_use_proxies():
    handler = bridge._NoRedirect()

    assert handler.redirect_request(None, None, 302, "Found", {}, "http://elsewhere/") is None
