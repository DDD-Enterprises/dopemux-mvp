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
                inputSchema={"type": "object", "properties": {"text": {"type": "string"}}},
            )
            for name in ("echo", "notify", "sample", "elicit", "roots")
        ]

    @server.call_tool()
    async def _call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
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
                            role="user", content=types.TextContent(type="text", text="hi")
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
            return [types.TextContent(type="text", text=f"{exc.error.code}:{exc.error.message}")]
        return [types.TextContent(type="text", text="answered")]

    @server.list_resources()
    async def _list_resources() -> List[types.Resource]:
        return [types.Resource(uri=RESOURCE_URI, name="note", mimeType="text/plain")]

    @server.read_resource()
    async def _read_resource(uri: Any) -> List[ReadResourceContents]:
        return [ReadResourceContents(content="hello from backend", mime_type="text/plain")]

    return server


def _factory(server: Server):
    """A `session_factory` serving `server` over in-memory streams."""

    @asynccontextmanager
    async def factory(**client_kwargs: Any):
        async with create_client_server_memory_streams() as (client_streams, server_streams):
            async with anyio.create_task_group() as tg:
                options = server.create_initialization_options()
                tg.start_soon(lambda: server.run(server_streams[0], server_streams[1], options))
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
                    SPEC, proxy_streams[0], proxy_streams[1], session_factory=_factory(server)
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
    assert [t.name for t in tools.tools] == ["echo", "notify", "sample", "elicit", "roots"]
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

    async with _runner_via_proxy(_fake_backend(), message_handler=handler) as (runner, _box):
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

    async with create_client_server_memory_streams() as (_client_streams, proxy_streams):
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
        url=f"http://127.0.0.1:{_closed_port()}{path}", transport=transport, name="refused"
    )
    started = time.monotonic()
    assert stdio_proxy.probe_backend(backend, timeout_s=1.0) is False
    assert time.monotonic() - started < 1.5
