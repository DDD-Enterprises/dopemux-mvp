"""ConPort backend adapter for PM-plane decision and progress integration."""

import logging
import os
from typing import Any, Dict, List, Optional
import httpx

logger = logging.getLogger(__name__)

class ConPortAdapter:
    """Adapter for communicating with the ConPort (Decision Graph) HTTP API."""

    def __init__(self, base_url: Optional[str] = None):
        # Default to PORT_BASE+16 (3016)
        self.base_url = (base_url or os.getenv("CONPORT_URL", "http://localhost:3016")).rstrip("/")

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
        if tag:
            params["tag"] = tag
        if text:
            params["text"] = text
            
        try:
            response = await self._request("GET", "/kg/decisions/search", params=params)
            response.raise_for_status()
            return response.json()
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
