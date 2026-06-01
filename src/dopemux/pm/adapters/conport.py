"""ConPort backend adapter for PM-plane decision and progress integration."""

import asyncio
import logging
import os
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import httpx
from filelock import FileLock

logger = logging.getLogger(__name__)

class ConPortAdapter:
    """Adapter for communicating with the ConPort (Decision Graph) HTTP API."""

    def __init__(self, base_url: Optional[str] = None):
        # ConPort HTTP service is exposed on 3004 by default.
        self.base_url = (base_url or os.getenv("CONPORT_URL", "http://localhost:3004")).rstrip("/")

    async def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        """Helper to make an HTTP request."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.request(method, f"{self.base_url}{path}", **kwargs)
            return response

    async def save_custom_data(
        self,
        workspace_id: str,
        category: str,
        key: str,
        value: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Call the kg/custom_data endpoint to save metadata/progress."""
        payload = {
            "workspace_id": workspace_id,
            "category": category,
            "key": key,
            "value": value
        }
        try:
            # Note: Bridge routes /kg/custom_data to ConPort
            response = await self._request("POST", "/kg/custom_data", json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to save custom data to ConPort: {e}")
            raise

    async def get_custom_data(
        self,
        workspace_id: str,
        category: str,
        key: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Retrieve custom data from ConPort."""
        params = {
            "workspace_id": workspace_id,
            "category": category,
            "limit": limit
        }
        if key:
            params["key"] = key
            
        try:
            response = await self._request("GET", "/kg/custom_data", params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get custom data from ConPort: {e}")
            raise
            
    async def search_decisions(self, tag: Optional[str] = None, text: Optional[str] = None, limit: int = 5) -> Dict[str, Any]:
        """Search decisions in the knowledge graph."""
        params = {"limit": limit}
            
        try:
            response = await self._request("GET", "/api/decisions", params=params)
            response.raise_for_status()
            payload = response.json()
            decisions = payload.get("decisions", [])
            if tag:
                decisions = [
                    item for item in decisions
                    if tag in [str(entry) for entry in item.get("tags", [])]
                ]
            if text:
                lowered = text.lower()
                decisions = [
                    item for item in decisions
                    if lowered in str(item.get("summary", "")).lower()
                    or lowered in str(item.get("rationale", "")).lower()
                ]
            return {
                **payload,
                "decisions": decisions[:limit],
                "count": len(decisions[:limit]),
            }
        except Exception as e:
            logger.error(f"Failed to search decisions in ConPort: {e}")
            raise

    async def health(self) -> bool:
        """Check health of conport."""
        try:
            # /kg/health is the health endpoint for the bridge/KG
            response = await self._request("GET", "/kg/health")
            return response.status_code == 200
        except Exception:
            return False

    async def record_progress(
        self,
        task_id: str,
        progress_notes: str,
        is_decision: bool,
        idempotency_key: Optional[str] = None,
        timeout: int = 5,
    ) -> Dict[str, Any]:
        """Record progress/decision canonical write, protected by a file lock and logged to a local journal."""
        # Define XDG journal and lock files
        xdg_share = os.path.expanduser("~/.local/share/dopemux")
        os.makedirs(xdg_share, exist_ok=True)
        filepath = os.path.join(xdg_share, "progress_log.json")
        lock_path = filepath + ".lock"

        entry = {
            "task_id": task_id,
            "progress_notes": progress_notes,
            "is_decision": is_decision,
            "idempotency_key": idempotency_key,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        # 1. Canonical HTTP post to ConPort API
        payload = {
            "workspace_id": "default",
            "category": "decision" if is_decision else "progress",
            "key": task_id,
            "value": {
                "description": progress_notes,
                "is_decision": is_decision,
                "idempotency_key": idempotency_key
            }
        }
        response = await self._request("POST", "/kg/custom_data", json=payload)
        response.raise_for_status()

        # 2. Persist progress receipt only after ConPort accepts it
        await asyncio.to_thread(self._write_journal_sync, filepath, lock_path, entry, timeout)

        return response.json()

    def _write_journal_sync(self, filepath: str, lock_path: str, entry: Dict[str, Any], timeout: int):
        """Synchronously acquire FileLock and append to the journal file."""
        with FileLock(lock_path, timeout=timeout):
            existing = []
            if os.path.exists(filepath):
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        existing = json.load(f)
                except Exception:
                    existing = []

            existing.append(entry)

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(existing, f, indent=2, sort_keys=True)
