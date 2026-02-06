"""Bridge adapter for context-switch-tracker domain service."""

import os
from typing import Any, Dict

import aiohttp


class ContextSwitchBridgeAdapter:
    """Sends context-switch events to DopeconBridge."""

    def __init__(self, workspace_id: str, base_url: str | None = None):
        self.workspace_id = workspace_id
        self.base_url = base_url or os.getenv("DOPECON_BRIDGE_URL", "http://localhost:3016")

    async def emit_event(self, event_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        payload = {
            "stream": "dopemux:events",
            "event_type": event_type,
            "data": data,
            "source": "context-switch-tracker",
        }
        try:
            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(f"{self.base_url}/events", json=payload) as response:
                    return {
                        "success": response.status in (200, 201),
                        "status": response.status,
                    }
        except Exception as exc:
            return {"success": False, "error": str(exc)}
