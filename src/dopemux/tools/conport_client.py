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

    def __init__(self, base_url: str = "http://localhost:3005"):
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
            logger.error(f"ConPort health check failed: {e}")
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

    async def semantic_search(self, workspace_id: str, query: str, top_k: int = 5,
                           filter_item_types: Optional[List[str]] = None,
                           filter_tags_include_any: Optional[List[str]] = None,
                           filter_tags_include_all: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Perform ConPort search using compatibility-safe endpoint routing.

        Preferred path is `/api/adhd/semantic-search` (current). Falls back to
        `/api/semantic-search` for older server variants.
        """
        await self._ensure_session()

        payload = {
            "workspace_id": workspace_id,
            "query_text": query,
            "top_k": top_k
        }

        # Add optional filters
        if filter_item_types:
            payload["filter_item_types"] = filter_item_types
        if filter_tags_include_any:
            payload["filter_tags_include_any"] = filter_tags_include_any
        if filter_tags_include_all:
            payload["filter_tags_include_all"] = filter_tags_include_all

        endpoints = ["/api/adhd/semantic-search", "/api/semantic-search"]
        last_error: Optional[str] = None

        try:
            for idx, endpoint in enumerate(endpoints):
                async with self.session.post(
                    f"{self.base_url}{endpoint}",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        if isinstance(result, dict):
                            results = result.get("results")
                            if isinstance(results, list):
                                result_count = len(results)
                            else:
                                legacy = result.get("result")
                                result_count = len(legacy) if isinstance(legacy, list) else 0

                            if result.get("deprecated"):
                                logger.warning(
                                    "ConPort search endpoint returned deprecated mode (%s): %s",
                                    result.get("search_mode"),
                                    result.get("deprecation_notice", "no notice provided"),
                                )

                            result["_endpoint_used"] = endpoint
                            logger.info(
                                "ConPort search found %s results for '%s' via %s",
                                result_count,
                                query,
                                endpoint,
                            )
                        return result

                    error_text = await response.text()
                    last_error = f"HTTP {response.status}: {error_text}"
                    should_fallback = idx == 0 and response.status in (404, 405)
                    if not should_fallback:
                        return {"error": last_error, "endpoint": endpoint}

            return {"error": last_error or "All semantic search endpoints failed"}
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
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

async def semantic_search(query: str, top_k: int = 5, workspace_id: str = "/Users/hue/code/dopemux-mvp",
                         filter_item_types: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Quick semantic search function - discover knowledge by meaning

    Finds relevant content using vector embeddings, not just keywords.
    Perfect for exploring complex relationships and ADHD-friendly discovery.
    """
    client = ConPortClient()
    try:
        result = await client.semantic_search(
            workspace_id=workspace_id,
            query=query,
            top_k=top_k,
            filter_item_types=filter_item_types
        )
        return result
    finally:
        await client.close()

if __name__ == "__main__":
    # Test the client
    async def test_client():
        client = ConPortClient()

        # Test health
        health = await client.health_check()
        logger.info(f"Health: {health}")

        # Test context
        context = await client.get_active_context("/Users/hue/code/dopemux-mvp")
        logger.info(f"Context: {context}")

        # Test decision logging
        decision = await client.log_decision(
            "/Users/hue/code/dopemux-mvp",
            "Implement hybrid ConPort architecture",
            "Provides immediate reliability while maintaining future MCP compatibility",
            ["Direct integration", "MCP-only approach", "Separate service"]
        )
        logger.info(f"Decision: {decision}")

        # Test semantic search
        search_results = await client.semantic_search(
            workspace_id="/Users/hue/code/dopemux-mvp",
            query="ADHD optimization",
            top_k=3
        )
        logger.info(f"Semantic search: {search_results}")

        await client.close()

    asyncio.run(test_client())
