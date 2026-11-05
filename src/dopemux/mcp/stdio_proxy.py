"""Stdio MCP proxy for ``dopemux mcp launch`` (design D2), on the official ``mcp`` SDK.

The runner talks MCP over this process's stdin/stdout; the proxy holds one
client session to the worktree's sidecar (SSE for conport, streamable HTTP for
dope-memory and task-orchestrator) and forwards every request verbatim.

Rules:

* Requests from the backend that need the runner (sampling, elicitation,
  roots) are answered at once with ``-32601 not supported by dopemux proxy``,
  never left pending.
* The backend's ``tools/list_changed`` is forwarded to the runner.
* A backend session is dead once its write side fails or its read side has
  ended (an SSE backend restart closes only the read side; the SDK answers
  nothing written after that). The liveness check runs immediately before each
  send, so a request is never written to a session known to be dead: it is sent
  once on the reconnected session. A request in flight when its session drops
  gets an error at once and is never replayed (its effect is unknown).
* A Streamable HTTP backend restart invalidates the session: each POST on it
  gets HTTP 404, which the SDK answers with ``32600 "Session terminated"``. The
  backend never processed that request, so the session is dropped and the
  request is sent once on the reconnected (freshly initialized) session; a
  second "Session terminated" is returned to the runner, never retried again.
* Every forwarded request is bounded by ``REQUEST_TIMEOUT_S`` and every backend
  ``initialize`` by ``INITIALIZE_TIMEOUT_S``; a timeout is an error for that
  request only, not a dead session.
* Exit 0 when stdin closes; exit 1 once the backend session has dropped and the
  single reconnect has failed or dropped too (runner requests still waiting get
  their error first).
* Nothing but MCP frames ever reaches stdout.

``serve(backend, read_stream, write_stream, *, session_factory=None)`` is the
stream-level core; ``session_factory(**client_kwargs)`` must return an async
context manager yielding an entered, not yet initialized ``ClientSession``
constructed with exactly those keyword arguments (the proxy's sampling,
elicitation and roots callbacks and its message handler).
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
import threading
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import timedelta
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
#: Upper bound on one forwarded request (slow tools included).
REQUEST_TIMEOUT_S = 300.0
#: Upper bound on a backend ``initialize`` (first connect and the reconnect).
INITIALIZE_TIMEOUT_S = 10.0
#: How long a failed proxy waits for runner requests to receive their errors.
DRAIN_S = 1.0

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


#: What SDK 1.29's streamable HTTP client answers when a POST on its session gets
#: HTTP 404 (``streamable_http.py``, ``_send_session_terminated_error``).
SESSION_TERMINATED_CODE = 32600
SESSION_TERMINATED_MESSAGE = "Session terminated"


def _session_terminated(error: types.ErrorData) -> bool:
    """True when the backend rejected the request unprocessed: its session is gone.

    Code and text must both match. The code alone is not enough: a backend's
    own error with that code may come from a request it did process, which must
    never be replayed. If the SDK rewords the message, this degrades to passing
    the error to the runner (the behaviour before), never to a duplicate call.
    """
    return error.code == SESSION_TERMINATED_CODE and SESSION_TERMINATED_MESSAGE in (
        error.message or ""
    )


def _can_receive(session: ClientSession) -> bool:
    """False once nothing can ever arrive on ``session``'s read stream.

    The SDK only answers requests that are pending when its read stream ends;
    one sent afterwards waits forever. SDK transports and in-memory streams are
    anyio memory streams, whose sender count drops to 0 when the transport
    closes its read side. Anything else is assumed alive (the request timeout
    still bounds it).
    """
    stream = getattr(session, "_read_stream", None)
    statistics = getattr(stream, "statistics", None)
    if statistics is None:
        return True
    try:
        return statistics().open_send_streams > 0
    except Exception:  # noqa: BLE001 - unknown stream type: assume alive
        return True


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
        #: Runner requests currently inside ``forward``.
        self.active = 0

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
            session: Optional[ClientSession] = None
            try:
                async with self._factory(**self.client_kwargs()) as session:
                    with anyio.fail_after(INITIALIZE_TIMEOUT_S):
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
                self._end_session(session)
            if attempt < MAX_BACKEND_SESSIONS:
                _say(f"backend {self.backend.name} session ended; reconnecting once")
        _say(f"backend {self.backend.name} unavailable; run /mcp reconnect after fixing it")
        self.failed.set()
        self._connected.set()  # wake waiters so they see the failure
        if not started:
            task_status.started(None)

    def _detach(self, session: Optional[ClientSession]) -> None:
        """Stop handing out ``session``; waiters block until the reconnect."""
        if session is not None and session is self.session:
            self.session = None
            if self._connected.is_set():
                self._connected = anyio.Event()

    def _end_session(self, ended: Optional[ClientSession]) -> None:
        self._detach(ended)
        for scope, owner in list(self._inflight.items()):
            if owner is ended:
                scope.cancel()

    def _drop(self, session: ClientSession) -> None:
        """Mark ``session`` dead now, and let ``run`` close it and reconnect."""
        if session is self.session:
            self._detach(session)
            self._dropped.set()

    def _unavailable(self) -> McpError:
        return _connection_lost(f"dopemux proxy: backend {self.backend.name} unavailable")

    async def _live_session(self) -> ClientSession:
        """A session that can still answer, waiting out at most one reconnect.

        Returns without awaiting after the final check, so the caller's
        ``send_request`` registers its response stream before anything else runs.
        """
        with anyio.move_on_after(RECONNECT_WAIT_S):
            while not self.failed.is_set():
                session = self.session
                if session is None:
                    await self._connected.wait()
                elif _can_receive(session):
                    return session
                else:
                    self._drop(session)  # read side ended: nothing sent there is answered
        raise self._unavailable()

    async def forward(self, request: Any, result_type: type) -> Any:
        # The runner's frame validated with its `jsonrpc`/`id` kept as extras;
        # rebuild from method and params so the backend frame gets its own.
        request = type(request)(method=request.method, params=request.params)
        for attempt in range(1, MAX_BACKEND_SESSIONS + 1):
            session = await self._live_session()
            with anyio.CancelScope() as scope:
                self._inflight[scope] = session
                try:
                    return await session.send_request(
                        types.ClientRequest(request),
                        result_type,
                        request_read_timeout_seconds=timedelta(seconds=REQUEST_TIMEOUT_S),
                    )
                except McpError as exc:
                    if _session_terminated(exc.error):
                        # Streamable HTTP restart: unprocessed, so resend once on
                        # the reconnected session; a second one is the result.
                        self._drop(session)
                        if attempt == MAX_BACKEND_SESSIONS:
                            raise
                        continue
                    if exc.error.code != types.CONNECTION_CLOSED:
                        raise  # the backend's own error, or this request's timeout
                    self._drop(session)
                except (anyio.ClosedResourceError, anyio.BrokenResourceError):
                    self._drop(session)  # never written: safe to send on the next session
                    continue
                finally:
                    self._inflight.pop(scope, None)
            raise _connection_lost(
                f"dopemux proxy: backend {self.backend.name} dropped during the request; "
                "not retried"
            )
        raise self._unavailable()


def _build_server(link: _BackendLink, init: types.InitializeResult) -> Server:
    server: Server = Server(
        name=link.backend.name,
        version=init.serverInfo.version,
        instructions=init.instructions,
    )

    def handler_for(result_type: type) -> Callable[[Any], Any]:
        async def handler(request: Any) -> types.ServerResult:
            link.downstream = server.request_context.session
            link.active += 1
            try:
                return types.ServerResult(await link.forward(request, result_type))
            finally:
                link.active -= 1

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
            # Waiting runner requests fail with "unavailable"; let those errors go
            # out before the server stops.
            with anyio.move_on_after(DRAIN_S):
                while link.active:
                    await anyio.sleep(0.01)
                await anyio.sleep(0.05)
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
