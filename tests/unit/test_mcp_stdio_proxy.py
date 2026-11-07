"""Unit tests for the `dopemux mcp launch` stdio proxy (Task 3c, D2).

Both sides run on in-memory SDK streams: a runner `ClientSession` talks to the
proxy's stdio side, and the proxy's backend `ClientSession` talks to a fake
lowlevel `Server`. No network except the refused-port probe.
"""

from __future__ import annotations

import socket
import time
from contextlib import asynccontextmanager
from typing import Any, Dict, List

import anyio
import pytest
from mcp import ClientSession, types
from mcp.server.lowlevel import Server
from mcp.server.lowlevel.helper_types import ReadResourceContents
from mcp.shared.exceptions import McpError
from mcp.shared.memory import create_client_server_memory_streams
from mcp.shared.message import SessionMessage

from dopemux.mcp import stdio_proxy
from dopemux.mcp.stdio_proxy import BackendSpec

SPEC = BackendSpec(url="http://127.0.0.1:9/mcp", transport="http", name="fake")
RESOURCE_URI = "memo://note"


def _fake_backend() -> Server:
    server: Server = Server("fake-backend")

    @server.list_tools()
    async def _list_tools() -> List[types.Tool]:
        return [
            types.Tool(
                name=name,
                description=name,
                inputSchema={
                    "type": "object",
                    "properties": {"text": {"type": "string"}},
                },
            )
            for name in ("echo", "notify", "sample", "elicit", "roots")
        ]

    @server.call_tool()
    async def _call_tool(
        name: str, arguments: Dict[str, Any]
    ) -> List[types.TextContent]:
        session = server.request_context.session
        if name == "echo":
            return [types.TextContent(type="text", text=str(arguments.get("text", "")))]
        if name == "notify":
            await session.send_tool_list_changed()
            return [types.TextContent(type="text", text="sent")]
        try:
            if name == "sample":
                await session.create_message(
                    [
                        types.SamplingMessage(
                            role="user",
                            content=types.TextContent(type="text", text="hi"),
                        )
                    ],
                    max_tokens=5,
                )
            elif name == "elicit":
                await session.elicit_form(
                    "name?", {"type": "object", "properties": {"n": {"type": "string"}}}
                )
            else:
                await session.list_roots()
        except McpError as exc:
            return [
                types.TextContent(
                    type="text", text=f"{exc.error.code}:{exc.error.message}"
                )
            ]
        return [types.TextContent(type="text", text="answered")]

    @server.list_resources()
    async def _list_resources() -> List[types.Resource]:
        return [types.Resource(uri=RESOURCE_URI, name="note", mimeType="text/plain")]

    @server.read_resource()
    async def _read_resource(uri: Any) -> List[ReadResourceContents]:
        return [
            ReadResourceContents(content="hello from backend", mime_type="text/plain")
        ]

    return server


def _factory(server: Server):
    """A `session_factory` serving `server` over in-memory streams."""

    @asynccontextmanager
    async def factory(**client_kwargs: Any):
        async with create_client_server_memory_streams() as (
            client_streams,
            server_streams,
        ):
            async with anyio.create_task_group() as tg:
                options = server.create_initialization_options()
                tg.start_soon(
                    lambda: server.run(server_streams[0], server_streams[1], options)
                )
                async with ClientSession(
                    client_streams[0], client_streams[1], **client_kwargs
                ) as session:
                    yield session
                tg.cancel_scope.cancel()

    return factory


@asynccontextmanager
async def _runner_via_proxy(server: Server, *, message_handler=None):
    """Yield (runner session, exit-code box) with the proxy in between."""
    box: Dict[str, int] = {}
    async with create_client_server_memory_streams() as (client_streams, proxy_streams):
        async with anyio.create_task_group() as tg:

            async def _serve() -> None:
                box["code"] = await stdio_proxy.serve(
                    SPEC,
                    proxy_streams[0],
                    proxy_streams[1],
                    session_factory=_factory(server),
                )

            tg.start_soon(_serve)
            async with ClientSession(
                client_streams[0], client_streams[1], message_handler=message_handler
            ) as runner:
                with anyio.fail_after(5):
                    await runner.initialize()
                yield runner, box
            # The runner closing its streams is stdin EOF for the proxy.
            await client_streams[1].aclose()
            with anyio.fail_after(5):
                while "code" not in box:
                    await anyio.sleep(0.01)


async def test_proxy_lists_and_calls_backend_tools():
    async with _runner_via_proxy(_fake_backend()) as (runner, box):
        with anyio.fail_after(5):
            tools = await runner.list_tools()
            result = await runner.call_tool("echo", {"text": "hi"})
            resources = await runner.list_resources()
            read = await runner.read_resource(RESOURCE_URI)
    assert [t.name for t in tools.tools] == [
        "echo",
        "notify",
        "sample",
        "elicit",
        "roots",
    ]
    assert result.isError is False
    assert result.content[0].text == "hi"
    assert [str(r.uri) for r in resources.resources] == [RESOURCE_URI]
    assert read.contents[0].text == "hello from backend"
    assert box["code"] == 0


async def test_proxy_forwards_tool_list_changed():
    seen: List[Any] = []
    changed = anyio.Event()

    async def handler(message: Any) -> None:
        if isinstance(message, types.ServerNotification) and isinstance(
            message.root, types.ToolListChangedNotification
        ):
            seen.append(message.root)
            changed.set()

    async with _runner_via_proxy(_fake_backend(), message_handler=handler) as (
        runner,
        _box,
    ):
        with anyio.fail_after(5):
            await runner.list_tools()
            result = await runner.call_tool("notify", {})
            await changed.wait()
    assert result.content[0].text == "sent"
    assert len(seen) == 1


@pytest.mark.parametrize("tool", ["sample", "elicit", "roots"])
async def test_proxy_answers_backend_sampling_with_error(tool: str):
    async with _runner_via_proxy(_fake_backend()) as (runner, _box):
        with anyio.fail_after(5):  # a pending backend request would hang here
            result = await runner.call_tool(tool, {})
    assert result.content[0].text == "-32601:not supported by dopemux proxy"


async def test_proxy_exits_one_when_backend_cannot_connect_after_one_retry():
    attempts: List[int] = []

    @asynccontextmanager
    async def broken(**_kwargs: Any):
        attempts.append(1)
        raise OSError("connection refused")
        yield  # pragma: no cover

    async with create_client_server_memory_streams() as (
        _client_streams,
        proxy_streams,
    ):
        with anyio.fail_after(5):
            code = await stdio_proxy.serve(
                SPEC, proxy_streams[0], proxy_streams[1], session_factory=broken
            )
    assert code == 1
    assert len(attempts) == 2


def _closed_port() -> int:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


@pytest.mark.parametrize("transport,path", [("sse", "/sse"), ("http", "/mcp")])
def test_probe_backend_false_on_refused_port(transport: str, path: str):
    backend = BackendSpec(
        url=f"http://127.0.0.1:{_closed_port()}{path}",
        transport=transport,
        name="refused",
    )
    started = time.monotonic()
    assert stdio_proxy.probe_backend(backend, timeout_s=1.0) is False
    assert time.monotonic() - started < 1.5


# --- backend drop, resend, no-response (fix round 1, finding A) --------------


class _Backend:
    """A fake backend whose sessions the test can break from the outside."""

    def __init__(self, *plan: str) -> None:
        # per session: "ok" | "refuse" | "dead_read" | "terminated" | "terminated_echo"
        self.plan = list(plan)
        self.sessions: List[Dict[str, Any]] = []
        self.calls: List[str] = []
        self.called = anyio.Event()
        self.server = self._server()
        #: While ``time.monotonic()`` is below this, every connect is refused.
        self.down_until = 0.0
        self.refused = 0

    def _server(self) -> Server:
        server: Server = Server("breakable-backend")

        @server.list_tools()
        async def _list_tools() -> List[types.Tool]:
            return [
                types.Tool(name=n, description=n, inputSchema={"type": "object"})
                for n in ("echo", "block")
            ]

        @server.call_tool()
        async def _call_tool(
            name: str, arguments: Dict[str, Any]
        ) -> List[types.TextContent]:
            self.calls.append(name)
            self.called.set()
            if name == "block":
                await anyio.Event().wait()  # never answers
            return [types.TextContent(type="text", text=f"ok:{len(self.sessions)}")]

        return server

    def factory(self):
        @asynccontextmanager
        async def factory(**client_kwargs: Any):
            if time.monotonic() < self.down_until:
                self.refused += 1
                raise OSError("connection refused (backend restarting)")
            mode = self.plan.pop(0) if self.plan else "ok"
            if mode == "refuse":
                self.sessions.append({"mode": mode})
                raise OSError("connection refused")
            async with create_client_server_memory_streams() as (
                client_streams,
                server_streams,
            ):
                async with anyio.create_task_group() as tg:
                    options = self.server.create_initialization_options()
                    tg.start_soon(
                        lambda: self.server.run(
                            server_streams[0], server_streams[1], options
                        )
                    )
                    if mode == "dead_read":
                        await server_streams[1].aclose()  # nothing can ever be answered
                    write: Any = client_streams[1]
                    if mode.startswith("terminated"):
                        write, outbound = anyio.create_memory_object_stream(0)
                        tg.start_soon(
                            self._terminate,
                            mode,
                            outbound,
                            client_streams[1],
                            server_streams[1].clone(),
                        )
                    self.sessions.append(
                        {
                            "mode": mode,
                            "client": client_streams,
                            "server": server_streams,
                        }
                    )
                    async with ClientSession(
                        client_streams[0], write, **client_kwargs
                    ) as session:
                        yield session
                    tg.cancel_scope.cancel()

        return factory

    @staticmethod
    async def _terminate(
        mode: str, outbound: Any, to_server: Any, to_client: Any
    ) -> None:
        """The streamable HTTP transport after a backend restart (SDK 1.29).

        Every POST on the old session gets HTTP 404 and the transport answers that
        request with ``JSONRPCError(32600, "Session terminated")``; the server never
        sees it. ``terminated_echo`` does that only to ``echo`` tool calls.
        """
        async with outbound, to_client:
            async for message in outbound:
                root = message.message.root
                if (
                    isinstance(root, types.JSONRPCRequest)
                    and root.method != "initialize"
                    and (
                        mode == "terminated"
                        or (root.params or {}).get("name") == "echo"
                    )
                ):
                    error = types.ErrorData(code=32600, message="Session terminated")
                    reply = types.JSONRPCError(jsonrpc="2.0", id=root.id, error=error)
                    await to_client.send(SessionMessage(types.JSONRPCMessage(reply)))
                else:
                    await to_server.send(message)


@asynccontextmanager
async def _runner_via(backend: _Backend, *, reconnect_guard=None):
    box: Dict[str, int] = {}
    async with create_client_server_memory_streams() as (client_streams, proxy_streams):
        async with anyio.create_task_group() as tg:

            async def _serve() -> None:
                box["code"] = await stdio_proxy.serve(
                    SPEC,
                    proxy_streams[0],
                    proxy_streams[1],
                    session_factory=backend.factory(),
                    reconnect_guard=reconnect_guard,
                )

            tg.start_soon(_serve)
            async with ClientSession(client_streams[0], client_streams[1]) as runner:
                with anyio.fail_after(5):
                    await runner.initialize()
                yield runner, box
            await client_streams[1].aclose()
            tg.cancel_scope.cancel()


async def test_proxy_resends_unwritten_request_on_reconnected_session():
    backend = _Backend()
    async with _runner_via(backend) as (runner, _box):
        with anyio.fail_after(5):
            await runner.list_tools()
        await backend.sessions[0]["client"][
            1
        ].aclose()  # the next write fails: never written
        with anyio.fail_after(5):
            result = await runner.call_tool("echo", {})
    assert result.content[0].text == "ok:2"
    assert backend.calls == ["echo"]
    assert len(backend.sessions) == 2


async def test_proxy_reconnects_when_backend_read_side_ended_while_idle():
    backend = _Backend()
    async with _runner_via(backend) as (runner, _box):
        with anyio.fail_after(5):
            await runner.list_tools()
        # An SSE backend restart: the transport closes only the read side.
        await backend.sessions[0]["server"][1].aclose()
        with anyio.fail_after(
            5
        ):  # used to hang: the request was written, never answered
            result = await runner.call_tool("echo", {})
    assert result.content[0].text == "ok:2"
    assert backend.calls == ["echo"]
    assert len(backend.sessions) == 2


async def test_proxy_fails_in_flight_request_without_replay():
    backend = _Backend()
    outcome: Dict[str, Any] = {}
    async with _runner_via(backend) as (runner, _box):

        async def _call() -> None:
            try:
                outcome["result"] = await runner.call_tool("block", {})
            except McpError as exc:
                outcome["error"] = exc.error

        with anyio.fail_after(5):
            async with anyio.create_task_group() as tg:
                tg.start_soon(_call)
                await backend.called.wait()
                await backend.sessions[0]["server"][1].aclose()  # drops mid-request
    assert "result" not in outcome
    assert outcome["error"].code == types.CONNECTION_CLOSED
    assert "not retried" in outcome["error"].message
    assert backend.calls == ["block"]  # never replayed


async def test_proxy_fails_fast_and_exits_one_when_reconnect_cannot_answer(monkeypatch):
    monkeypatch.setattr(stdio_proxy, "INITIALIZE_TIMEOUT_S", 0.3)
    # A failed reconnect attempt is retried with backoff for RECONNECT_WAIT_S (I3);
    # this test is about the reconnect giving up, so the wait is shorter than a retry.
    monkeypatch.setattr(stdio_proxy, "RECONNECT_WAIT_S", 0.2)
    backend = _Backend("ok", "dead_read")
    async with _runner_via(backend) as (runner, box):
        with anyio.fail_after(5):
            await runner.list_tools()
        await backend.sessions[0]["server"][1].aclose()
        with anyio.fail_after(5):
            with pytest.raises(McpError) as info:
                await runner.call_tool("echo", {})
            while "code" not in box:
                await anyio.sleep(0.01)
    assert info.value.error.code == types.CONNECTION_CLOSED
    assert box["code"] == 1
    assert backend.calls == []


async def test_proxy_bounds_a_request_with_a_read_timeout(monkeypatch):
    monkeypatch.setattr(stdio_proxy, "REQUEST_TIMEOUT_S", 0.3)
    backend = _Backend()
    async with _runner_via(backend) as (runner, _box):
        with anyio.fail_after(5):
            with pytest.raises(McpError) as info:
                await runner.call_tool("block", {})
            again = await runner.call_tool(
                "echo", {}
            )  # a slow tool does not end the session
    assert "Timed out" in info.value.error.message
    assert again.content[0].text == "ok:1"
    assert len(backend.sessions) == 1


# --- Streamable HTTP "Session terminated" (fix round 2) ---------------------


async def test_proxy_reconnects_and_resends_after_streamable_session_terminated():
    backend = _Backend("terminated", "ok")
    async with _runner_via(backend) as (runner, box):
        with anyio.fail_after(5):
            result = await runner.call_tool("echo", {})
        assert "code" not in box  # still serving the runner
    assert result.content[0].text == "ok:2"
    assert backend.calls == ["echo"]  # the backend executed it exactly once
    assert len(backend.sessions) == 2


async def test_proxy_does_not_loop_when_fresh_session_is_also_terminated():
    backend = _Backend("terminated", "terminated")
    async with _runner_via(backend) as (runner, box):
        with anyio.fail_after(5):
            with pytest.raises(McpError) as info:
                await runner.call_tool("echo", {})
            while "code" not in box:  # the reconnect dropped too: exit 1
                await anyio.sleep(0.01)
    assert info.value.error.code == 32600
    assert info.value.error.message == "Session terminated"
    assert len(backend.sessions) == 2
    assert backend.calls == []
    assert box["code"] == 1


async def test_proxy_in_flight_other_requests_survive_a_session_terminated_reconnect():
    backend = _Backend("terminated_echo", "ok")
    outcome: Dict[str, Any] = {}
    async with _runner_via(backend) as (runner, _box):

        async def _block() -> None:
            try:
                outcome["result"] = await runner.call_tool("block", {})
            except McpError as exc:
                outcome["error"] = exc.error

        with anyio.fail_after(5):  # a replayed "block" would never answer
            async with anyio.create_task_group() as tg:
                tg.start_soon(_block)
                await backend.called.wait()  # accepted by session 1
                echo = await runner.call_tool("echo", {})
    assert echo.content[0].text == "ok:2"
    assert backend.calls == ["block", "echo"]  # "block" ran once, never replayed
    assert "result" not in outcome
    assert outcome["error"].code == types.CONNECTION_CLOSED
    assert "not retried" in outcome["error"].message


# --- reconnect guard (final review C1) ---------------------------------------
# Port of the reviewer's scratch probe `to_reconnect_probe.py`: switch-project
# stopped project A's orchestrator (its session answers "Session terminated")
# and project B's now listens on the same URL. Without a guard the proxy resent
# A's runner request to B ("served by project B").


def _owner_server(owner: str, calls: List[str]) -> Server:
    server: Server = Server(f"jar-{owner}")

    @server.list_tools()
    async def _list_tools() -> List[types.Tool]:
        return [
            types.Tool(name="whoami", description="x", inputSchema={"type": "object"})
        ]

    @server.call_tool()
    async def _call_tool(
        name: str, arguments: Dict[str, Any]
    ) -> List[types.TextContent]:
        calls.append(owner)
        return [types.TextContent(type="text", text=f"served by project {owner}")]

    return server


def _switched_owner_factory(calls: List[str], connects: List[str]):
    plan = ["A-terminated", "B"]

    @asynccontextmanager
    async def factory(**client_kwargs: Any):
        mode = plan.pop(0)
        connects.append(mode)
        server = _owner_server("A" if mode.startswith("A") else "B", calls)
        async with create_client_server_memory_streams() as (
            client_streams,
            server_streams,
        ):
            async with anyio.create_task_group() as tg:
                options = server.create_initialization_options()
                tg.start_soon(
                    lambda: server.run(server_streams[0], server_streams[1], options)
                )
                write: Any = client_streams[1]
                if mode == "A-terminated":
                    write, outbound = anyio.create_memory_object_stream(0)
                    tg.start_soon(
                        _Backend._terminate,
                        "terminated",
                        outbound,
                        client_streams[1],
                        server_streams[1].clone(),
                    )
                async with ClientSession(
                    client_streams[0], write, **client_kwargs
                ) as session:
                    yield session
                tg.cancel_scope.cancel()

    return factory


async def test_reconnect_guard_refusal_reaches_the_runner_and_nothing_is_resent(capsys):
    calls: List[str] = []
    connects: List[str] = []
    guard_calls: List[int] = []

    def guard() -> None:
        guard_calls.append(1)
        raise stdio_proxy.ProxyRefused(
            "TASK_ORCHESTRATOR_START_BLOCKED_WRONG_PROJECT",
            "/code/b; run dopemux mcp switch-project here to take it over",
        )

    box: Dict[str, int] = {}
    async with create_client_server_memory_streams() as (client_streams, proxy_streams):
        async with anyio.create_task_group() as tg:

            async def _serve() -> None:
                box["code"] = await stdio_proxy.serve(
                    SPEC,
                    proxy_streams[0],
                    proxy_streams[1],
                    session_factory=_switched_owner_factory(calls, connects),
                    reconnect_guard=guard,
                )

            tg.start_soon(_serve)
            async with ClientSession(client_streams[0], client_streams[1]) as runner:
                with anyio.fail_after(5):
                    await runner.initialize()
                    with pytest.raises(McpError) as info:
                        await runner.call_tool("whoami", {})
                    while "code" not in box:
                        await anyio.sleep(0.01)
            tg.cancel_scope.cancel()
    assert info.value.error.code == -32000
    assert info.value.error.message == (
        "TASK_ORCHESTRATOR_START_BLOCKED_WRONG_PROJECT: "
        "/code/b; run dopemux mcp switch-project here to take it over"
    )
    assert calls == []  # project B never received A's request
    assert connects == ["A-terminated"]  # the guard ran before any reconnect
    assert guard_calls == [1]
    assert box["code"] == 1
    err = capsys.readouterr().err
    assert (
        "TASK_ORCHESTRATOR_START_BLOCKED_WRONG_PROJECT: /code/b; "
        "run dopemux mcp switch-project here to take it over"
    ) in err


async def test_reconnect_guard_passing_keeps_the_resend():
    backend = _Backend("terminated_echo", "ok")
    guard_calls: List[int] = []
    async with _runner_via(backend, reconnect_guard=lambda: guard_calls.append(1)) as (
        runner,
        box,
    ):
        with anyio.fail_after(5):
            tools = await runner.list_tools()  # the first session: no guard
            assert guard_calls == []
            result = await runner.call_tool("echo", {})
        assert "code" not in box
    assert [t.name for t in tools.tools] == ["echo", "block"]
    assert result.content[0].text == "ok:2"
    assert backend.calls == ["echo"]
    assert guard_calls == [1]


async def test_reconnect_guard_unexpected_exception_is_a_refusal():
    backend = _Backend("terminated", "ok")

    def broken_guard() -> None:
        raise RuntimeError("docker inspect blew up")

    async with _runner_via(backend, reconnect_guard=broken_guard) as (runner, box):
        with anyio.fail_after(5):
            with pytest.raises(McpError) as info:
                await runner.call_tool("echo", {})
            while "code" not in box:
                await anyio.sleep(0.01)
    assert info.value.error.code == -32000
    assert info.value.error.message.startswith("LAUNCH_RECONNECT_GUARD_FAILED: ")
    assert "docker inspect blew up" in info.value.error.message
    assert backend.calls == []
    assert len(backend.sessions) == 1  # never reconnected
    assert box["code"] == 1


# --- reconnect backoff and the per-window budget (final review I3) ------------


async def test_reconnect_backs_off_until_a_briefly_down_backend_answers():
    backend = _Backend()
    async with _runner_via(backend) as (runner, box):
        with anyio.fail_after(5):
            await runner.list_tools()
        backend.down_until = time.monotonic() + 0.6
        await backend.sessions[0]["client"][1].aclose()  # the next write fails
        with anyio.fail_after(5):
            result = await runner.call_tool("echo", {})
        assert "code" not in box
    assert result.content[0].text == "ok:2"
    assert backend.refused >= 2  # retried, with backoff, while it was down
    assert backend.calls == ["echo"]


async def test_two_drops_inside_one_window_end_the_proxy():
    backend = _Backend()
    async with _runner_via(backend) as (runner, box):
        with anyio.fail_after(5):
            await runner.list_tools()
        await backend.sessions[0]["client"][1].aclose()
        with anyio.fail_after(5):
            first = await runner.call_tool("echo", {})
        await backend.sessions[1]["client"][1].aclose()
        with anyio.fail_after(5):
            with pytest.raises(McpError) as info:
                await runner.call_tool("echo", {})
            while "code" not in box:
                await anyio.sleep(0.01)
    assert first.content[0].text == "ok:2"
    assert info.value.error.code == types.CONNECTION_CLOSED
    assert len(backend.sessions) == 2
    assert box["code"] == 1


async def test_two_drops_in_separate_windows_both_heal(monkeypatch):
    monkeypatch.setattr(stdio_proxy, "RECONNECT_WINDOW_S", 0.3)
    backend = _Backend()
    async with _runner_via(backend) as (runner, box):
        with anyio.fail_after(5):
            await runner.list_tools()
        await backend.sessions[0]["client"][1].aclose()
        with anyio.fail_after(5):
            first = await runner.call_tool("echo", {})
        await anyio.sleep(0.4)  # the next drop falls in a new window
        await backend.sessions[1]["client"][1].aclose()
        with anyio.fail_after(5):
            second = await runner.call_tool("echo", {})
        assert "code" not in box
    assert first.content[0].text == "ok:2"
    assert second.content[0].text == "ok:3"
    assert backend.calls == ["echo", "echo"]


# --- a termination signal inside an event loop ends it at a safe point --------------


@pytest.fixture
def fresh_deferred_exit(monkeypatch):
    """A private deferred-exit slot, so a failure here never leaks into other tests."""
    monkeypatch.setattr(stdio_proxy, "_deferred_exit", {})


def test_defer_exit_outside_an_event_loop_declines(fresh_deferred_exit):
    assert stdio_proxy.defer_exit_in_event_loop(143) is False


def test_a_signal_deferred_into_a_probe_ends_it_with_system_exit(
    monkeypatch, fresh_deferred_exit
):
    @asynccontextmanager
    async def hanging_session(backend: Any, **_kwargs: Any):
        # what the launcher's SIGTERM handler does when it fires inside the loop
        assert stdio_proxy.defer_exit_in_event_loop(143) is True
        await anyio.sleep_forever()
        yield  # pragma: no cover

    monkeypatch.setattr(stdio_proxy, "_sdk_session", hanging_session)
    started = time.monotonic()
    with pytest.raises(SystemExit) as info:
        stdio_proxy.probe_backend(SPEC, timeout_s=30.0)
    assert info.value.code == 143
    assert time.monotonic() - started < 5  # cancelled at once, not after the timeout
