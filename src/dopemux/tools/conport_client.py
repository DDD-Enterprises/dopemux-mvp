#!/usr/bin/env python3
"""
ConPort Direct HTTP Client Tools
ADHD-optimized context preservation through direct API access
"""

import asyncio
import aiohttp
import json
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)

class ConPortClient:
    """
    Direct HTTP client for ConPort API - bypasses MCP transport issues
    Provides immediate, reliable access to ADHD context preservation features
    """

    def __init__(self, base_url: str = "http://localhost:3004"):
        self.base_url = base_url
        self.session: Optional[aiohttp.ClientSession] = None

    async def _ensure_session(self):
        """Ensure aiohttp session exists"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()

    async def health_check(self) -> Dict[str, Any]:
        """Check ConPort server health"""
        await self._ensure_session()
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {"status": "unhealthy", "error": f"HTTP {response.status}"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def get_active_context(self, workspace_id: str) -> Dict[str, Any]:
        """
        Get active context for workspace - critical for ADHD developers
        Returns current work context, session info, and focus state
        """
        await self._ensure_session()
        try:
            async with self.session.get(f"{self.base_url}/api/context/{workspace_id}") as response:
                if response.status == 200:
                    context = await response.json()
                    logger.info(f"Retrieved context for {workspace_id}: {context.get('active_context', 'N/A')}")
                    return context
                else:
                    return {"error": f"HTTP {response.status}"}
        except Exception as e:
            logger.error(f"Failed to get context: {e}")
            return {"error": str(e)}

    async def update_active_context(self, workspace_id: str, context_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update active context - preserve development state for ADHD continuity
        """
        await self._ensure_session()
        try:
            async with self.session.post(
                f"{self.base_url}/api/context/{workspace_id}",
                json=context_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"Updated context for {workspace_id}")
                    return result
                else:
                    return {"error": f"HTTP {response.status}"}
        except Exception as e:
            logger.error(f"Failed to update context: {e}")
            return {"error": str(e)}

    async def log_decision(self, workspace_id: str, summary: str, rationale: str,
                          alternatives: List[str] = None) -> Dict[str, Any]:
        """
        Log important decision with rationale - crucial for ADHD memory support
        """
        await self._ensure_session()
        decision_data = {
            "workspace_id": workspace_id,
            "summary": summary,
            "rationale": rationale,
            "alternatives": alternatives or []
        }

        try:
            async with self.session.post(
                f"{self.base_url}/api/decisions",
                json=decision_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"Logged decision: {summary}")
                    return result
                else:
                    return {"error": f"HTTP {response.status}"}
        except Exception as e:
            logger.error(f"Failed to log decision: {e}")
            return {"error": str(e)}

    async def get_decisions(self, workspace_id: str) -> Dict[str, Any]:
        """Get decision history for workspace"""
        await self._ensure_session()
        try:
            async with self.session.get(
                f"{self.base_url}/api/decisions",
                params={"workspace_id": workspace_id}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"Retrieved {len(result.get('decisions', []))} decisions for {workspace_id}")
                    return result
                else:
                    return {"error": f"HTTP {response.status}"}
        except Exception as e:
            logger.error(f"Failed to get decisions: {e}")
            return {"error": str(e)}

    async def log_progress(self, workspace_id: str, status: str, description: str,
                          percentage: int = 0) -> Dict[str, Any]:
        """
        Log progress on current work - visual feedback for ADHD motivation
        """
        await self._ensure_session()
        progress_data = {
            "workspace_id": workspace_id,
            "status": status,
            "description": description,
            "percentage": percentage
        }

        try:
            async with self.session.post(
                f"{self.base_url}/api/progress",
                json=progress_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"Logged progress: {description} ({status})")
                    return result
                else:
                    return {"error": f"HTTP {response.status}"}
        except Exception as e:
            logger.error(f"Failed to log progress: {e}")
            return {"error": str(e)}

    async def get_progress(self, status_filter: Optional[str] = None) -> Dict[str, Any]:
        """Get current progress items"""
        await self._ensure_session()
        params = {}
        if status_filter:
            params["status_filter"] = status_filter

        try:
            async with self.session.get(f"{self.base_url}/api/progress", params=params) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"Retrieved progress items (filter: {status_filter})")
                    return result
                else:
                    return {"error": f"HTTP {response.status}"}
        except Exception as e:
            logger.error(f"Failed to get progress: {e}")
            return {"error": str(e)}

    async def close(self):
        """Close the HTTP session"""
        if self.session and not self.session.closed:
            await self.session.close()

# ADHD-Friendly Convenience Functions
async def get_current_context(workspace_id: str = "/Users/hue/code/dopemux-mvp") -> Dict[str, Any]:
    """Quick function to get current development context"""
    client = ConPortClient()
    try:
        result = await client.get_active_context(workspace_id)
        return result
    finally:
        await client.close()

async def save_decision(summary: str, rationale: str, alternatives: List[str] = None,
                       workspace_id: str = "/Users/hue/code/dopemux-mvp") -> Dict[str, Any]:
    """Quick function to save important decisions"""
    client = ConPortClient()
    try:
        result = await client.log_decision(workspace_id, summary, rationale, alternatives)
        return result
    finally:
        await client.close()

async def update_progress(description: str, status: str = "IN_PROGRESS", percentage: int = 0,
                         workspace_id: str = "/Users/hue/code/dopemux-mvp") -> Dict[str, Any]:
    """Quick function to update work progress"""
    client = ConPortClient()
    try:
        result = await client.log_progress(workspace_id, status, description, percentage)
        return result
    finally:
        await client.close()

if __name__ == "__main__":
    # Test the client
    async def test_client():
        client = ConPortClient()

        # Test health
        health = await client.health_check()
        print(f"Health: {health}")

        # Test context
        context = await client.get_active_context("/Users/hue/code/dopemux-mvp")
        print(f"Context: {context}")

        # Test decision logging
        decision = await client.log_decision(
            "/Users/hue/code/dopemux-mvp",
            "Implement hybrid ConPort architecture",
            "Provides immediate reliability while maintaining future MCP compatibility",
            ["Direct integration", "MCP-only approach", "Separate service"]
        )
        print(f"Decision: {decision}")

        await client.close()

    asyncio.run(test_client())