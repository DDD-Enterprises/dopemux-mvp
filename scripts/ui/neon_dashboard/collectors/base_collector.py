"""Base collector utilities for polling external services."""

from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

try:  # pragma: no cover - optional dependency
    import aiohttp
except ImportError:  # pragma: no cover - fallback when aiohttp missing
    aiohttp = None  # type: ignore

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class CacheEntry:
    value: Any
    expires_at: float


class BaseCollector:
    """Shared helper for all network/data collectors."""

    cache_ttl: float = 10.0
    http_timeout: float = 2.0

    def __init__(self, *, cache_ttl: Optional[float] = None, timeout: Optional[float] = None):
        self.cache_ttl = cache_ttl if cache_ttl is not None else self.cache_ttl
        self.http_timeout = timeout if timeout is not None else self.http_timeout
        self._cache: Dict[str, CacheEntry] = {}
        self._session: Optional["aiohttp.ClientSession"] = None  # type: ignore[name-defined]
        self._lock = asyncio.Lock()
        self._failure_log: Dict[str, float] = {}
        self._failure_cooldown = 30.0  # seconds between repeated warnings

    async def close(self) -> None:
        if self._session is not None and not self._session.closed:  # type: ignore[attr-defined]
            await self._session.close()  # type: ignore[call-arg]
        self._session = None

    async def _get_session(self) -> Optional["aiohttp.ClientSession"]:  # type: ignore[name-defined]
        if aiohttp is None:
            return None
        if self._session is None or self._session.closed:  # type: ignore[attr-defined]
            timeout = aiohttp.ClientTimeout(total=self.http_timeout)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    def _cache_get(self, key: str) -> Any:
        entry = self._cache.get(key)
        if entry and entry.expires_at > time.time():
            return entry.value
        if key in self._cache:
            del self._cache[key]
        return None

    def _cache_set(self, key: str, value: Any) -> None:
        self._cache[key] = CacheEntry(value=value, expires_at=time.time() + self.cache_ttl)

    async def _http_json(self, url: str) -> Any:
        session = await self._get_session()
        if session is None:
            logger.debug("aiohttp not installed; skipping request to %s", url)
            return None
        try:
            async with session.get(url) as resp:
                if resp.status >= 400:
                    self._log_warning(url, "Request failed %s -> %s", url, resp.status)
                    return None
                text = await resp.text()
                if not text.strip():
                    return None
                try:
                    result = json.loads(text)
                except json.JSONDecodeError:
                    logger.exception("Invalid JSON from %s", url)
                    return None
                self._reset_failure_log(url)
                return result
        except asyncio.TimeoutError:
            self._log_warning(url, "Timeout fetching %s", url)
        except Exception as exc:  # pragma: no cover - resilience
            if aiohttp is not None and isinstance(exc, aiohttp.ClientError):
                self._log_warning(url, "HTTP error fetching %s: %s", url, exc)
            elif isinstance(exc, OSError):
                self._log_warning(url, "OS error fetching %s: %s", url, exc)
            else:
                logger.exception("Unexpected error fetching %s", url)
        return None

    async def fetch(self) -> Any:
        """Subclasses implement actual fetch logic."""
        raise NotImplementedError

    async def get(self, cache_key: str = "default") -> Any:
        """Fetch data with in-memory caching."""
        cached = self._cache_get(cache_key)
        if cached is not None:
            return cached

        async with self._lock:
            cached = self._cache_get(cache_key)
            if cached is not None:
                return cached
            value = await self.fetch()
            self._cache_set(cache_key, value)
            return value

    def _log_warning(self, key: str, message: str, *fmt_args: object) -> None:
        """Emit throttled warning logs so dashboards aren't flooded."""
        now = time.time()
        last = self._failure_log.get(key, 0.0)
        if now - last >= self._failure_cooldown:
            logger.warning(message, *fmt_args, exc_info=False)
            self._failure_log[key] = now

    def _reset_failure_log(self, key: str) -> None:
        """Clear cooldown for a successful fetch."""
        if key in self._failure_log:
            del self._failure_log[key]
