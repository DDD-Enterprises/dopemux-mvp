"""Async helper utilities shared across genetic-agent components."""

from __future__ import annotations

from typing import Any, Awaitable, Callable
import asyncio


class AsyncClientMixin:
    """
    Minimal mixin to provide common lifecycle helpers for async clients.

    Historically this mixin hosted shared locking/cleanup helpers. The new
    implementation keeps the public surface so existing imports continue to
    work without pulling in extra dependencies.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)  # type: ignore[misc]
        self._async_lock = asyncio.Lock()

    async def _run_with_lock(self, coro_factory: Callable[[], Awaitable[Any]]) -> Any:
        """
        Run the provided coroutine factory under an async lock.

        Useful when subclasses share a single network client that should only
        process one request at a time (e.g., constrained MCP endpoints).
        """
        async with self._async_lock:
            return await coro_factory()

    async def aclose(self) -> None:
        """Close the underlying httpx client if the subclass defines _client."""
        client = getattr(self, "_client", None)
        close = getattr(client, "aclose", None)
        if callable(close):
            await close()
