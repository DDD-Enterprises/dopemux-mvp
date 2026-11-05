"""Stdio MCP proxy for ``dopemux mcp launch`` (design D2), on the official ``mcp`` SDK.

The runner talks MCP over this process's stdin/stdout; the proxy holds one
client session to the worktree's sidecar (SSE for conport, streamable HTTP for
dope-memory and task-orchestrator) and forwards every request verbatim.

Rules:

* Requests from the backend that need the runner (sampling, elicitation,
  roots) are answered at once with ``-32601 not supported by dopemux proxy``,
  never left pending.
* The backend's ``tools/list_changed`` is forwarded to the runner.
* A request that was never written to a dead backend session is sent once on
  the reconnected session; a request in flight when the session drops gets an
  error and is never replayed (its effect is unknown).
* Exit 0 when stdin closes; exit 1 once the backend session has dropped and the
  single reconnect has failed or dropped too.
* Nothing but MCP frames ever reaches stdout.
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
import threading
from contextlib import asynccontextmanager
from dataclasses import dataclass
from functools import partial
from typing import Any, AsyncContextManager, AsyncIterator, Callable, Dict, Literal, Optional

import anyio
from mcp import ClientSession, types
from mcp.server.lowlevel.server import NotificationOptions, Server
from mcp.server.session import ServerSession
from mcp.server.stdio import stdio_server
from mcp.shared.exceptions import McpError

__all__ = ["BackendSpec", "probe_backend", "run_proxy", "serve"]

NOT_SUPPORTED_MESSAGE = "not supported by dopemux proxy"
#: The first backend session plus one reconnect.
MAX_BACKEND_SESSIONS = 2
#: How long a runner request waits for a reconnecting backend.
RECONNECT_WAIT_S = 10.0

SessionFactory = Callable[..., AsyncContextManager[ClientSession]]

# Every runner request the proxy serves, with the result type the backend returns.
_FORWARDED: Dict[type, type] = {
    types.ListToolsRequest: types.ListToolsResult,
    types.CallToolRequest: types.CallToolResult,
    types.ListResourcesRequest: types.ListResourcesResult,
    types.ListResourceTemplatesRequest: types.ListResourceTemplatesResult,
    types.ReadResourceRequest: types.ReadResourceResult,
    types.ListPromptsRequest: types.ListPromptsResult,
    types.GetPromptRequest: types.GetPromptResult,
    types.SetLevelRequest: types.EmptyResult,
}


@dataclass(frozen=True)
class BackendSpec:
    """Where the sidecar listens and how to speak to it."""

    url: str
    transport: Literal["sse", "http"]
    name: str


def _say(message: str) -> None:
    print(f"dopemux mcp launch: {message}", file=sys.stderr, flush=True)


def _not_supported() -> types.ErrorData:
    return types.ErrorData(code=types.METHOD_NOT_FOUND, message=NOT_SUPPORTED_MESSAGE)


async def _refuse_sampling(context: Any, params: Any) -> types.ErrorData:
    return _not_supported()


async def _refuse_elicitation(context: Any, params: Any) -> types.ErrorData:
    return _not_supported()


async def _refuse_roots(context: Any) -> types.ErrorData:
    return _not_supported()


def _connection_lost(detail: str) -> McpError:
    return McpError(types.ErrorData(code=types.CONNECTION_CLOSED, message=detail))


@asynccontextmanager
async def _sdk_session(
    backend: BackendSpec, **client_kwargs: Any
) -> AsyncIterator[ClientSession]:
    """An entered, not yet initialized SDK client session to ``backend``."""
    if backend.transport == "sse":
        from mcp.client.sse import sse_client

        async with sse_client(backend.url) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream, **client_kwargs) as session:
                yield session
    elif backend.transport == "http":
        from mcp.client.streamable_http import streamable_http_client

        async with streamable_http_client(backend.url) as (read_stream, write_stream, _sid):
            async with ClientSession(read_stream, write_stream, **client_kwargs) as session:
                yield session
    else:
        raise ValueError(f"unsupported backend transport: {backend.transport!r}")


class _BackendLink:
    """The backend client session, its single reconnect, and in-flight requests."""

    def __init__(self, backend: BackendSpec, factory: SessionFactory) -> None:
        self.backend = backend
        self._factory = factory
        self.session: Optional[ClientSession] = None
        self.downstream: Optional[ServerSession] = None
        self.failed = anyio.Event()
        self._connected = anyio.Event()
        self._dropped = anyio.Event()
        self._inflight: Dict[anyio.CancelScope, ClientSession] = {}

    def client_kwargs(self) -> Dict[str, Any]:
        return {
            "sampling_callback": _refuse_sampling,
            "elicitation_callback": _refuse_elicitation,
            "list_roots_callback": _refuse_roots,
            "message_handler": self._on_backend_message,
        }

    async def _on_backend_message(self, message: Any) -> None:
        if not (
            isinstance(message, types.ServerNotification)
            and isinstance(message.root, types.ToolListChangedNotification)
        ):
            return
        if self.downstream is None:
            return  # the runner has not listed tools yet; it will get a fresh list
        try:
            await self.downstream.send_tool_list_changed()
        except (anyio.ClosedResourceError, anyio.BrokenResourceError):
            pass

    async def run(self, *, task_status: Any = anyio.TASK_STATUS_IGNORED) -> None:
        """Hold backend sessions; report the first ``InitializeResult`` (or None)."""
        started = False
        for attempt in range(1, MAX_BACKEND_SESSIONS + 1):
            self._dropped = anyio.Event()
            try:
                async with self._factory(**self.client_kwargs()) as session:
                    init = await session.initialize()
                    self.session = session
                    self._connected.set()
                    if not started:
                        started = True
                        task_status.started(init)
                    await self._dropped.wait()
            except Exception as exc:  # noqa: BLE001 - any transport failure ends the session
                _say(f"backend {self.backend.name} at {self.backend.url}: {exc!r}")
            finally:
                self._end_session()
            if attempt < MAX_BACKEND_SESSIONS:
                _say(f"backend {self.backend.name} session ended; reconnecting once")
        _say(f"backend {self.backend.name} unavailable; run /mcp reconnect after fixing it")
        self.failed.set()
        self._connected.set()  # wake waiters so they see the failure
        if not started:
            task_status.started(None)

    def _end_session(self) -> None:
        ended = self.session
        self.session = None
        if self._connected.is_set():
            self._connected = anyio.Event()
        for scope, owner in list(self._inflight.items()):
            if owner is ended:
                scope.cancel()

    def _drop(self, session: ClientSession) -> None:
        if session is self.session:
            self._dropped.set()

    async def _current(self) -> ClientSession:
        with anyio.move_on_after(RECONNECT_WAIT_S):
            while self.session is None and not self.failed.is_set():
                await self._connected.wait()
        if self.session is None:
            raise _connection_lost(f"dopemux proxy: backend {self.backend.name} unavailable")
        return self.session

    async def forward(self, request: Any, result_type: type) -> Any:
        # The runner's frame validated with its `jsonrpc`/`id` kept as extras;
        # rebuild from method and params so the backend frame gets its own.
        request = type(request)(method=request.method, params=request.params)
        for _ in range(2):
            session = await self._current()
            with anyio.CancelScope() as scope:
                self._inflight[scope] = session
                try:
                    return await session.send_request(types.ClientRequest(request), result_type)
                except McpError as exc:
                    if exc.error.code == types.CONNECTION_CLOSED:
                        self._drop(session)
                    raise
                except (anyio.ClosedResourceError, anyio.BrokenResourceError):
                    self._drop(session)  # never written: safe to send on the next session
                    continue
                finally:
                    self._inflight.pop(scope, None)
            raise _connection_lost(
                f"dopemux proxy: backend {self.backend.name} dropped during the request; "
                "not retried"
            )
        raise _connection_lost(f"dopemux proxy: backend {self.backend.name} unavailable")


def _build_server(link: _BackendLink, init: types.InitializeResult) -> Server:
    server: Server = Server(
        name=link.backend.name,
        version=init.serverInfo.version,
        instructions=init.instructions,
    )

    def handler_for(result_type: type) -> Callable[[Any], Any]:
        async def handler(request: Any) -> types.ServerResult:
            link.downstream = server.request_context.session
            return types.ServerResult(await link.forward(request, result_type))

        return handler

    # Raw handlers keep the forward lossless: the SDK decorators would re-validate
    # tool input and re-shape results the backend already produced.
    for request_type, result_type in _FORWARDED.items():
        server.request_handlers[request_type] = handler_for(result_type)
    return server


async def serve(
    backend: BackendSpec,
    read_stream: Any,
    write_stream: Any,
    *,
    session_factory: Optional[SessionFactory] = None,
) -> int:
    """Serve MCP on ``read_stream``/``write_stream``, forwarding to ``backend``.

    ``session_factory(**client_kwargs)`` yields an entered, uninitialized
    ``ClientSession`` built with the given kwargs (the proxy's callbacks); the
    default connects to ``backend.url`` with the SDK transport. Returns 0 when
    the read side closes, 1 when the backend is gone after one reconnect.
    """
    link = _BackendLink(backend, session_factory or partial(_sdk_session, backend))
    exit_code = 1
    async with anyio.create_task_group() as tg:
        init = await tg.start(link.run)
        if init is None:
            tg.cancel_scope.cancel()
            return 1
        server = _build_server(link, init)
        options = server.create_initialization_options(NotificationOptions(tools_changed=True))

        async def serve_runner() -> None:
            nonlocal exit_code
            await server.run(read_stream, write_stream, options)
            exit_code = 0
            tg.cancel_scope.cancel()

        async def watch_backend() -> None:
            nonlocal exit_code
            await link.failed.wait()
            exit_code = 1
            tg.cancel_scope.cancel()

        tg.start_soon(serve_runner)
        tg.start_soon(watch_backend)
    return exit_code


class _DaemonStdin:
    """Line source for ``stdio_server(stdin=...)`` read by a daemon thread.

    The SDK's default reader blocks a non-daemon worker thread in
    ``readline()``, so a proxy whose backend is gone could not exit until the
    runner wrote again. This reader is a daemon thread on the raw descriptor
    (``os.read``, not ``sys.stdin.buffer``, whose lock interpreter shutdown
    needs), so it never holds the process open.
    """

    def __init__(self, fd: Optional[int] = None) -> None:
        self._fd = fd if fd is not None else sys.stdin.fileno()

    def __aiter__(self) -> AsyncIterator[str]:
        return self._lines()

    async def _lines(self) -> AsyncIterator[str]:
        loop = asyncio.get_running_loop()
        queue: "asyncio.Queue[Optional[str]]" = asyncio.Queue()

        def put(item: Optional[str]) -> None:
            try:
                loop.call_soon_threadsafe(queue.put_nowait, item)
            except RuntimeError:  # loop already closed
                pass

        def pump() -> None:
            pending = b""
            try:
                while chunk := os.read(self._fd, 65536):
                    pending += chunk
                    while b"\n" in pending:
                        line, pending = pending.split(b"\n", 1)
                        put(line.decode("utf-8", errors="replace") + "\n")
                if pending:
                    put(pending.decode("utf-8", errors="replace"))
            except OSError:
                pass
            finally:
                put(None)

        threading.Thread(target=pump, name="dopemux-mcp-launch-stdin", daemon=True).start()
        while True:
            line = await queue.get()
            if line is None:
                return
            yield line


def _route_logging_to_stderr() -> None:
    """stdout carries MCP frames only: move every non-file log handler to stderr."""
    root = logging.getLogger()
    for handler in list(root.handlers):
        if not isinstance(handler, logging.FileHandler):
            root.removeHandler(handler)
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setFormatter(logging.Formatter("%(levelname)s %(name)s: %(message)s"))
    root.addHandler(stderr_handler)
    root.setLevel(logging.WARNING)


def run_proxy(
    backend: BackendSpec, *, session_factory: Optional[SessionFactory] = None
) -> int:
    """Serve the runner over this process's stdio until stdin closes."""
    _route_logging_to_stderr()

    async def _main() -> int:
        exit_code = 1
        with anyio.CancelScope() as scope:
            stdin: Any = _DaemonStdin()  # duck-types the anyio.AsyncFile it reads lines from
            async with stdio_server(stdin=stdin) as (read_stream, write_stream):
                exit_code = await serve(
                    backend, read_stream, write_stream, session_factory=session_factory
                )
                scope.cancel()  # stop the stdio reader/writer tasks
        return exit_code

    return anyio.run(_main)


def probe_backend(backend: BackendSpec, *, timeout_s: float = 1.0) -> bool:
    """True when an SDK ``initialize`` against ``backend`` succeeds within ``timeout_s``."""

    async def _probe() -> bool:
        with anyio.fail_after(timeout_s):
            async with _sdk_session(backend) as session:
                await session.initialize()
        return True

    try:
        return anyio.run(_probe)
    except (KeyboardInterrupt, SystemExit):
        raise
    except BaseException:  # noqa: BLE001 - refused, timed out, protocol error: all "not ready"
        return False
