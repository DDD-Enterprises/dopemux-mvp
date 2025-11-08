"""Simple async in-memory Redis replacement used for tests and fallbacks."""
from __future__ import annotations

from collections import defaultdict
import fnmatch
from typing import Any, Dict, List, Optional


class InMemoryRedis:
    """Minimal subset of Redis commands implemented in memory."""

    def __init__(self) -> None:
        self._store: Dict[str, Any] = {}
        self._lists: defaultdict[str, List[Any]] = defaultdict(list)

    async def ping(self) -> bool:
        return True

    async def close(self) -> bool:
        return True

    async def flushdb(self) -> None:
        self._store.clear()
        self._lists.clear()

    async def set(self, key: str, value: Any) -> bool:
        self._store[key] = value
        return True

    async def setex(self, key: str, ttl: int, value: Any) -> bool:
        # TTL ignored; kept for API compatibility
        return await self.set(key, value)

    async def get(self, key: str) -> Optional[Any]:
        return self._store.get(key)

    async def delete(self, key: str) -> int:
        existed = 1 if key in self._store or key in self._lists else 0
        self._store.pop(key, None)
        self._lists.pop(key, None)
        return existed

    async def keys(self, pattern: str = "*") -> List[str]:
        keys = set(self._store.keys()) | set(self._lists.keys())
        return [k for k in keys if fnmatch.fnmatch(k, pattern)]

    async def lpush(self, key: str, value: Any) -> int:
        lst = self._lists[key]
        lst.insert(0, value)
        return len(lst)

    async def lrange(self, key: str, start: int, end: int) -> List[Any]:
        lst = self._lists.get(key, [])
        if not lst:
            return []
        if end == -1:
            end = len(lst) - 1
        return lst[start : end + 1]

    async def ltrim(self, key: str, start: int, end: int) -> bool:
        lst = self._lists.get(key, [])
        if not lst:
            return True
        if end == -1:
            end = len(lst) - 1
        self._lists[key] = lst[start : end + 1]
        return True
