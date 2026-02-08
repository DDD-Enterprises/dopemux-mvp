"""WebSocket progress streamer for research task updates."""

import asyncio
from collections import defaultdict
from typing import Any, Dict, List, Optional, Set
from uuid import UUID


class WebSocketProgressStreamer:
    """
    Lightweight in-process progress streamer.

    The main FastAPI app handles direct socket lifecycle; this class provides
    a shared interface for orchestrator progress emissions.
    """

    def __init__(self):
        self.running = False
        self._subscribers: Dict[str, Set[Any]] = defaultdict(set)
        self._event_history: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def start_server(self) -> None:
        self.running = True

    async def stop_server(self) -> None:
        self.running = False
        async with self._lock:
            self._subscribers.clear()

    async def subscribe(self, task_id: UUID | str, websocket: Any) -> None:
        async with self._lock:
            self._subscribers[str(task_id)].add(websocket)

    async def unsubscribe(self, task_id: UUID | str, websocket: Any) -> None:
        async with self._lock:
            subscribers = self._subscribers.get(str(task_id))
            if subscribers and websocket in subscribers:
                subscribers.remove(websocket)

    async def emit_progress(self, task_id: UUID | str, payload: Dict[str, Any]) -> None:
        task_key = str(task_id)
        self._event_history[task_key].append(payload)

        subscribers = list(self._subscribers.get(task_key, set()))
        for websocket in subscribers:
            try:
                await websocket.send_json(payload)
            except Exception:
                await self.unsubscribe(task_key, websocket)

    def get_recent_events(self, task_id: UUID | str, limit: int = 20) -> List[Dict[str, Any]]:
        events = self._event_history.get(str(task_id), [])
        return events[-limit:]
