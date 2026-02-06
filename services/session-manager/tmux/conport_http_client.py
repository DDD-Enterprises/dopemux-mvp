"""Minimal ConPort HTTP client shim for tmux layout persistence."""

import aiohttp
import os
from typing import Any, Dict


class ConPortHTTPClient:
    """Lightweight client used by tmux layout manager."""

    def __init__(self, workspace_id: str):
        self.workspace_id = workspace_id
        self.base_url = os.getenv("DOPECON_BRIDGE_URL", "http://localhost:3016")

    async def log_custom_data(self, category: str, key: str, value: Any) -> Dict[str, Any]:
        payload = {
            "workspace_id": self.workspace_id,
            "category": category,
            "key": key,
            "value": value,
        }

        try:
            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(f"{self.base_url}/api/custom-data", json=payload) as response:
                    return {
                        "success": response.status in (200, 201),
                        "status": response.status,
                    }
        except Exception as exc:
            return {"success": False, "error": str(exc)}
