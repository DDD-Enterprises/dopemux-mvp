"""Dope-Memory backend adapter for PM-plane chronicle integration."""

import logging
import os
from typing import Any, Dict, List, Optional
import httpx

logger = logging.getLogger(__name__)

class DopeMemoryAdapter:
    """Adapter for communicating with the dope-memory HTTP API."""

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (base_url or os.getenv("DOPE_MEMORY_URL", "http://localhost:3020")).rstrip("/")

    async def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        """Helper to make an HTTP request."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.request(method, f"{self.base_url}{path}", **kwargs)
            return response

    async def search_chronicle(
        self,
        workspace_id: str,
        session_id: Optional[str] = None,
        category: Optional[str] = None,
        entry_type: Optional[str] = None,
        workflow_phase: Optional[str] = None,
        tags_any: Optional[List[str]] = None,
        time_range: str = "week",
        top_k: int = 3,
        cursor: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Call the memory_search endpoint."""
        payload = {
            "workspace_id": workspace_id,
            "session_id": session_id,
            "category": category,
            "entry_type": entry_type,
            "workflow_phase": workflow_phase,
            "tags_any": tags_any,
            "time_range": time_range,
            "top_k": top_k,
            "cursor": cursor,
        }
        payload = {k: v for k, v in payload.items() if v is not None}
        
        try:
            response = await self._request("POST", "/tools/memory_search", json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to search dope-memory chronicle: {e}")
            raise

    async def append_chronicle(
        self,
        workspace_id: str,
        entry_type: str,
        summary: str,
        category: str,
        details: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        links: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Call the memory_store endpoint to append a record."""
        payload = {
            "workspace_id": workspace_id,
            "entry_type": entry_type,
            "category": category,
            "summary": summary,
            "details": details,
            "tags": tags,
            "links": links,
            "idempotency_key": idempotency_key,
        }
        
        payload = {k: v for k, v in payload.items() if v is not None}

        try:
            response = await self._request("POST", "/tools/memory_store", json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to append to dope-memory chronicle: {e}")
            raise

    async def correct_chronicle(
        self,
        workspace_id: str,
        entry_id: str,
        correction_type: str,
        corrected_summary: Optional[str] = None,
        corrected_tags: Optional[List[str]] = None,
        idempotency_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Call the memory_correct endpoint to correct/supersede a record."""
        payload = {
            "workspace_id": workspace_id,
            "entry_id": entry_id,
            "correction_type": correction_type,
            "corrected_summary": corrected_summary,
            "corrected_tags": corrected_tags,
            "idempotency_key": idempotency_key,
        }
        payload = {k: v for k, v in payload.items() if v is not None}

        try:
            response = await self._request("POST", "/tools/memory_correct", json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            # Re-raise so callers can catch HTTPError to do a fallback
            logger.error(f"Failed to correct dope-memory chronicle: {e}")
            raise
