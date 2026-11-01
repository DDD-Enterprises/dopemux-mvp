"""B04 id filling (schema-driven, never overriding) and the unchanged --base-url mode."""

from __future__ import annotations

import io
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Dict

import pytest

from dopemux.mcp import http_stdio_bridge as bridge

from .conftest import CONPORT_TOOLS, call_msg, init_msg, initialized_msg, list_msg

ARGV_MEMORY = ["--server", "dope-memory", "--principal", "runner:codex"]
ARGV_CONPORT = ["--server", "conport", "--principal", "runner:codex"]


def _echoed_args(result, msg_id: int) -> Any:
    reply = next(r for r in result.lines() if r.get("id") == msg_id)
    return json.loads(reply["result"]["content"][0]["text"])


def _handshake():
    return [init_msg(1), initialized_msg(), list_msg(2)]


def test_should_fill_dope_memory_ids_from_its_own_keys(repo, fake_server, tokens, run_bridge):
    result = run_bridge(ARGV_MEMORY, _handshake() + [call_msg(3, "memory_store", {"text": "hi"})])

    assert _echoed_args(result, 3) == {
        "text": "hi",
        "workspace_id": "wt-memory-ws",
        "instance_id": "wt-memory-inst",
    }


def test_should_fill_conport_ids_from_its_own_keys(repo, fake_server, tokens, run_bridge):
    fake_server.tools = CONPORT_TOOLS

    result = run_bridge(ARGV_CONPORT, _handshake() + [call_msg(3, "update_context", {"patch": {"a": 1}})])

    assert _echoed_args(result, 3) == {
        "patch": {"a": 1},
        "workspace_id": "/abs/conport/ws",
        "instance_id": "wt-conport-inst",
    }


def test_should_fill_only_the_ids_the_tool_schema_declares(repo, fake_server, tokens, run_bridge):
    fake_server.tools = CONPORT_TOOLS

    result = run_bridge(
        ARGV_CONPORT,
        _handshake()
        + [
            call_msg(3, "save_custom_data", {"category": "c"}),  # workspace_id only
            call_msg(4, "fork_instance", {"target_instance": "t"}),  # workspace_id + required target
        ],
    )

    assert _echoed_args(result, 3) == {"category": "c", "workspace_id": "/abs/conport/ws"}
    assert _echoed_args(result, 4) == {"target_instance": "t", "workspace_id": "/abs/conport/ws"}


def test_should_leave_a_tool_without_id_parameters_untouched(repo, fake_server, tokens, run_bridge):
    result = run_bridge(ARGV_MEMORY, _handshake() + [call_msg(3, "memory_search", {"query": "q"})])

    assert _echoed_args(result, 3) == {"query": "q"}


@pytest.mark.parametrize("supplied", ["caller-ws", "", None])
def test_should_never_override_a_caller_supplied_value(repo, fake_server, tokens, run_bridge, supplied):
    result = run_bridge(
        ARGV_MEMORY,
        _handshake() + [call_msg(3, "memory_store", {"text": "hi", "workspace_id": supplied})],
    )

    echoed = _echoed_args(result, 3)
    assert echoed["workspace_id"] == supplied
    assert echoed["instance_id"] == "wt-memory-inst"  # the omitted one is still filled


def test_should_create_the_arguments_object_when_the_caller_omitted_it(repo, fake_server, tokens, run_bridge):
    result = run_bridge(ARGV_MEMORY, _handshake() + [call_msg(3, "memory_store", omit_arguments=True)])

    assert _echoed_args(result, 3) == {"workspace_id": "wt-memory-ws", "instance_id": "wt-memory-inst"}


def test_should_learn_schemas_from_the_server_not_from_a_built_in_list(repo, fake_server, tokens, run_bridge):
    fake_server.tools = [
        {
            "name": "brand_new_tool",
            "inputSchema": {"type": "object", "properties": {"instance_id": {"type": "string"}}},
        }
    ]

    result = run_bridge(ARGV_MEMORY, _handshake() + [call_msg(3, "brand_new_tool", {})])

    assert _echoed_args(result, 3) == {"instance_id": "wt-memory-inst"}


def test_should_fetch_the_tool_list_itself_when_the_client_never_asked(repo, fake_server, tokens, run_bridge):
    result = run_bridge(
        ARGV_MEMORY,
        [init_msg(1), initialized_msg(), call_msg(3, "memory_store", {"text": "hi"})],
    )

    assert _echoed_args(result, 3)["workspace_id"] == "wt-memory-ws"
    assert len(fake_server.bodies("tools/list")) == 1
    assert [r["id"] for r in result.lines()] == [1, 3]  # the internal listing is never printed


def test_should_follow_pagination_when_it_fetches_the_tool_list(repo, fake_server, tokens, run_bridge):
    fake_server.page_tools = True  # memory_store is on page 1, memory_search on page 2
    fake_server.tools = list(reversed(fake_server.tools))

    result = run_bridge(
        ARGV_MEMORY,
        [init_msg(1), initialized_msg(), call_msg(3, "memory_store", {"text": "hi"})],
    )

    assert _echoed_args(result, 3)["instance_id"] == "wt-memory-inst"
    assert len(fake_server.bodies("tools/list")) == 2


def test_should_not_fill_an_id_the_envrc_does_not_define(tmp_path, monkeypatch, fake_server, tokens, run_bridge):
    root = tmp_path / "r"
    root.mkdir()
    (root / ".git").mkdir()
    (root / ".envrc.dopemux-mcp").write_text(
        f"DOPE_MEMORY_PORT={fake_server.port}\nDOPE_MEMORY_WORKSPACE_ID=only-ws\n"
    )
    monkeypatch.chdir(root)

    result = run_bridge(ARGV_MEMORY, _handshake() + [call_msg(3, "memory_store", {"text": "hi"})])

    assert _echoed_args(result, 3) == {"text": "hi", "workspace_id": "only-ws"}


def test_should_ignore_the_other_servers_id_keys(tmp_path, monkeypatch, fake_server, tokens, run_bridge):
    root = tmp_path / "r"
    root.mkdir()
    (root / ".git").mkdir()
    (root / ".envrc.dopemux-mcp").write_text(
        f"DOPE_MEMORY_PORT={fake_server.port}\nDOPEMUX_WORKSPACE_ID=conport-ws\nDOPEMUX_INSTANCE_ID=conport-inst\n"
    )
    monkeypatch.chdir(root)

    result = run_bridge(ARGV_MEMORY, _handshake() + [call_msg(3, "memory_store", {"text": "hi"})])

    assert _echoed_args(result, 3) == {"text": "hi"}


def test_should_not_touch_requests_other_than_tools_call(repo, fake_server, tokens, run_bridge):
    run_bridge(ARGV_MEMORY, _handshake())

    [listing] = fake_server.bodies("tools/list")
    assert "params" not in listing


# --- tools/list shown to the client: filled ids are no longer required ---

REQUIRED_TOOLS = [
    {
        "name": "write_thing",
        "description": "keeps this exact text",
        "inputSchema": {
            "type": "object",
            "properties": {
                "workspace_id": {"type": "string"},
                "instance_id": {"type": "string"},
                "text": {"type": "string"},
            },
            "required": ["workspace_id", "text", "instance_id"],
        },
        "annotations": {"readOnlyHint": False},
    },
    {
        "name": "no_ids",
        "inputSchema": {"type": "object", "properties": {"q": {"type": "string"}}, "required": ["q"]},
    },
    {
        "name": "ids_only_required",
        "inputSchema": {
            "type": "object",
            "properties": {"workspace_id": {"type": "string"}},
            "required": ["workspace_id"],
        },
    },
]


def _forwarded_tools(result, msg_id: int = 2):
    reply = next(r for r in result.lines() if r.get("id") == msg_id)
    return {t["name"]: t for t in reply["result"]["tools"]}


def test_should_drop_filled_ids_from_required_in_the_forwarded_tool_list(repo, fake_server, tokens, run_bridge):
    fake_server.tools = REQUIRED_TOOLS

    tools = _forwarded_tools(run_bridge(ARGV_MEMORY, _handshake()))

    assert tools["write_thing"]["inputSchema"]["required"] == ["text"]
    assert "required" not in tools["ids_only_required"]["inputSchema"]


def test_should_keep_properties_and_every_other_field_of_the_forwarded_tool(repo, fake_server, tokens, run_bridge):
    fake_server.tools = REQUIRED_TOOLS

    tools = _forwarded_tools(run_bridge(ARGV_MEMORY, _handshake()))

    original = REQUIRED_TOOLS[0]
    sent = tools["write_thing"]
    assert sent["inputSchema"]["properties"] == original["inputSchema"]["properties"]
    assert sent["inputSchema"]["type"] == "object"
    assert {k: v for k, v in sent.items() if k != "inputSchema"} == {
        k: v for k, v in original.items() if k != "inputSchema"
    }
    assert tools["ids_only_required"]["inputSchema"]["properties"] == {"workspace_id": {"type": "string"}}


def test_should_leave_a_tool_without_ids_unchanged_in_the_forwarded_list(repo, fake_server, tokens, run_bridge):
    fake_server.tools = REQUIRED_TOOLS

    tools = _forwarded_tools(run_bridge(ARGV_MEMORY, _handshake()))

    assert tools["no_ids"] == REQUIRED_TOOLS[1]


def test_should_keep_required_for_an_id_the_envrc_does_not_define(tmp_path, monkeypatch, fake_server, tokens, run_bridge):
    root = tmp_path / "r"
    root.mkdir()
    (root / ".git").mkdir()
    (root / ".envrc.dopemux-mcp").write_text(
        f"DOPE_MEMORY_PORT={fake_server.port}\nDOPE_MEMORY_WORKSPACE_ID=only-ws\n"
    )
    monkeypatch.chdir(root)
    fake_server.tools = REQUIRED_TOOLS

    tools = _forwarded_tools(run_bridge(ARGV_MEMORY, _handshake()))

    assert tools["write_thing"]["inputSchema"]["required"] == ["text", "instance_id"]
    assert tools["ids_only_required"]["inputSchema"].get("required") is None


def test_should_still_fill_after_hiding_required(repo, fake_server, tokens, run_bridge):
    """The learned schema keeps the ids, so omitted ids are still filled."""
    fake_server.tools = REQUIRED_TOOLS

    result = run_bridge(ARGV_MEMORY, _handshake() + [call_msg(3, "write_thing", {"text": "hi"})])

    assert _echoed_args(result, 3) == {
        "text": "hi",
        "workspace_id": "wt-memory-ws",
        "instance_id": "wt-memory-inst",
    }


def test_should_not_hide_required_in_the_bridges_own_tool_listing(repo, fake_server, tokens, run_bridge):
    fake_server.tools = REQUIRED_TOOLS

    result = run_bridge(
        ARGV_MEMORY, [init_msg(1), initialized_msg(), call_msg(3, "write_thing", {"text": "hi"})]
    )

    assert [r["id"] for r in result.lines()] == [1, 3]  # internal listing is never printed
    assert _echoed_args(result, 3)["workspace_id"] == "wt-memory-ws"


def test_should_fill_and_be_accepted_when_the_model_omits_a_required_id(repo, fake_server, tokens, run_bridge):
    """End to end: list, see no required ids, call without them, server receives them."""
    fake_server.tools = REQUIRED_TOOLS

    result = run_bridge(ARGV_MEMORY, _handshake() + [call_msg(3, "write_thing", {"text": "hi"})])

    assert "workspace_id" not in _forwarded_tools(result)["write_thing"]["inputSchema"]["required"]
    [call] = fake_server.bodies("tools/call")
    assert call["params"]["arguments"]["workspace_id"] == "wt-memory-ws"
    assert call["params"]["arguments"]["instance_id"] == "wt-memory-inst"
    reply = next(r for r in result.lines() if r.get("id") == 3)
    assert "error" not in reply


# --- compatibility: the --base-url mode ---


class _PlainJsonRpc(BaseHTTPRequestHandler):
    seen: list = []

    def log_message(self, *args: Any) -> None:
        return

    def do_POST(self) -> None:  # noqa: N802
        raw = self.rfile.read(int(self.headers.get("Content-Length") or 0))
        _PlainJsonRpc.seen.append({"headers": dict(self.headers), "path": self.path, "body": json.loads(raw)})
        reply = json.dumps({"jsonrpc": "2.0", "id": json.loads(raw).get("id"), "result": {"ok": True}}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(reply)))
        self.end_headers()
        self.wfile.write(reply)


@pytest.fixture
def plain_server():
    _PlainJsonRpc.seen = []
    httpd = HTTPServer(("127.0.0.1", 0), _PlainJsonRpc)
    thread = threading.Thread(target=httpd.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{httpd.server_address[1]}"
    httpd.shutdown()
    httpd.server_close()
    thread.join(timeout=5)


def test_should_keep_base_url_mode_unchanged(plain_server, monkeypatch, capsys, tokens):
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(init_msg(1)) + "\n"))

    code = bridge.main(["--base-url", plain_server])

    out = capsys.readouterr()
    assert code == 0
    assert json.loads(out.out) == {"jsonrpc": "2.0", "id": 1, "result": {"ok": True}}
    [seen] = _PlainJsonRpc.seen
    assert seen["path"] == "/mcp"
    assert seen["headers"]["Accept"] == "application/json"
    assert not any(k.lower() in {"authorization", "mcp-session-id"} for k in seen["headers"])
    assert tokens == []  # the keychain is never consulted in --base-url mode


def test_should_keep_base_url_transport_error_shape(monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(init_msg(9)) + "\n"))

    code = bridge.main(["--base-url", "http://127.0.0.1:1"])

    reply = json.loads(capsys.readouterr().out)
    assert code == 0
    assert reply["id"] == 9
    assert reply["error"]["code"] == bridge.SERVER_ERROR_CODE
    assert reply["error"]["message"] == "Bridge transport error"
    assert "detail" in reply["error"]["data"]


def test_should_still_render_the_config_generator_command(tmp_path):
    """The only in-repo caller renders `--base-url`; its argv must still parse."""
    parser = bridge.build_parser()

    args = parser.parse_args(["--base-url", "http://localhost:3004", "--timeout", "5"])

    assert args.base_url == "http://localhost:3004" and args.server is None and args.timeout == 5


@pytest.mark.parametrize(
    "argv",
    [
        [],
        ["--server", "dope-memory"],  # no principal
        ["--principal", "runner:codex"],  # no server
        ["--base-url", "http://x", "--server", "dope-memory", "--principal", "runner:codex"],
        ["--server", "orchestrator", "--principal", "runner:codex"],  # not a Wave 2A profile
    ],
)
def test_should_reject_invalid_argument_combinations(argv, capsys):
    with pytest.raises(SystemExit) as exit_info:
        bridge.main(argv)

    assert exit_info.value.code == 2
