"""
ConPort Client for WMA Integration

Client wrapper for ConPort MCP tools to provide semantic context enrichment.
"""

import asyncio

import logging

logger = logging.getLogger(__name__)

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

# Import ConPort MCP tools (these would be available in the Dopemux environment)
try:
    from mcp__conport__get_decisions import get_decisions
    from mcp__conport__get_progress import get_progress
    from mcp__conport__get_system_patterns import get_system_patterns
    from mcp__conport__link_conport_items import link_conport_items
    from mcp__conport__get_linked_items import get_linked_items
    from mcp__conport__semantic_search_conport import semantic_search_conport
except ImportError:
    # Fallback for development/testing
    logger.info("ConPort MCP tools not available, using mock implementations")

    async def get_decisions(workspace_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        return [{
            "id": 1,
            "summary": "Implement predictive context restoration",
            "rationale": "Improve interrupt recovery using TF-IDF and KNN",
            "created_at": datetime.now().isoformat(),
            "tags": ["adhd", "predictive"]
        }, {
            "id": 2,
            "summary": "Add ADHD-optimized suggestions",
            "rationale": "Reduce cognitive load with personalized recommendations",
            "created_at": (datetime.now() - timedelta(hours=2)).isoformat(),
            "tags": ["adhd", "ux"]
        }]

    async def get_progress(workspace_id: str, status_filter: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        progress_items = [{
            "id": 1,
            "description": "Implement TF-IDF vectorization",
            "status": "DONE",
            "created_at": datetime.now().isoformat()
        }, {
            "id": 2,
            "description": "Add KNN pattern matching",
            "status": "DONE",
            "created_at": (datetime.now() - timedelta(hours=1)).isoformat()
        }, {
            "id": 3,
            "description": "Integrate with WMA service",
            "status": "IN_PROGRESS",
            "created_at": (datetime.now() - timedelta(minutes=30)).isoformat()
        }]

        if status_filter:
            progress_items = [p for p in progress_items if p["status"] == status_filter]

        return progress_items[:limit]

    async def get_system_patterns(workspace_id: str, limit: int = 10, tags_filter_include_any: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        patterns = [{
            "id": 1,
            "name": "ADHD 25-minute focus sessions",
            "description": "Use Pomodoro-style sessions with energy matching",
            "created_at": datetime.now().isoformat(),
            "tags": ["adhd", "session-management"]
        }, {
            "id": 2,
            "name": "Predictive context restoration",
            "description": "TF-IDF and KNN for intelligent recovery",
            "created_at": (datetime.now() - timedelta(hours=3)).isoformat(),
            "tags": ["adhd", "predictive"]
        }]

        if tags_filter_include_any:
            patterns = [p for p in patterns if any(tag in p["tags"] for tag in tags_filter_include_any)]

        return patterns[:limit]

    async def link_conport_items(**kwargs) -> None:
        pass

    async def get_linked_items(**kwargs) -> List[Dict[str, Any]]:
        return []

    async def semantic_search_conport(**kwargs) -> List[Dict[str, Any]]:
        return []

class ConPortClient:
    """Client for interacting with ConPort knowledge graph"""

    def __init__(self, workspace_id: str):
        self.workspace_id = workspace_id

    async def get_decisions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent decisions from ConPort"""
        try:
            result = await get_decisions(
                workspace_id=self.workspace_id,
                limit=limit
            )
            return result.get('decisions', []) if isinstance(result, dict) else result
        except Exception as e:
            logger.error(f"Failed to get decisions: {e}")
            return []

    async def get_progress(self, status_filter: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Get progress entries from ConPort"""
        try:
            result = await get_progress(
                workspace_id=self.workspace_id,
                status_filter=status_filter,
                limit=limit
            )
            return result.get('progress_entries', []) if isinstance(result, dict) else result
        except Exception as e:
            logger.error(f"Failed to get progress: {e}")
            return []

    async def get_system_patterns(self, limit: int = 10, tags_filter_include_any: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Get system patterns from ConPort"""
        try:
            result = await get_system_patterns(
                workspace_id=self.workspace_id,
                limit=limit,
                tags_filter_include_any=tags_filter_include_any
            )
            return result.get('patterns', []) if isinstance(result, dict) else result
        except Exception as e:
            logger.error(f"Failed to get patterns: {e}")
            return []

    async def link_conport_items(self, source_item_type: str, source_item_id: str,
                                target_item_type: str, target_item_id: str,
                                relationship_type: str, description: Optional[str] = None) -> None:
        """Link WMA items to ConPort items"""
        try:
            await link_conport_items(
                workspace_id=self.workspace_id,
                source_item_type=source_item_type,
                source_item_id=source_item_id,
                target_item_type=target_item_type,
                target_item_id=target_item_id,
                relationship_type=relationship_type,
                description=description
            )
        except Exception as e:
            logger.error(f"Failed to link items: {e}")

    async def get_linked_items(self, item_type: str, item_id: str) -> List[Dict[str, Any]]:
        """Get items linked to a specific item"""
        try:
            result = await get_linked_items(
                workspace_id=self.workspace_id,
                item_type=item_type,
                item_id=item_id
            )
            return result.get('linked_items', []) if isinstance(result, dict) else result
        except Exception as e:
            logger.error(f"Failed to get linked items: {e}")
            return []

    async def semantic_search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Perform semantic search across ConPort data"""
        try:
            result = await semantic_search_conport(
                workspace_id=self.workspace_id,
                query_text=query,
                top_k=top_k
            )
            return result.get('results', []) if isinstance(result, dict) else result
        except Exception as e:
            logger.error(f"Failed to perform semantic search: {e}")
            return []

async def test_conport_client():
    """Test ConPort client functionality"""
    client = ConPortClient(workspace_id="test_workspace")

    # Test getting decisions
    decisions = await client.get_decisions(limit=5)
    logger.info(f"Decisions: {len(decisions)}")

    # Test getting progress
    progress = await client.get_progress(status_filter="IN_PROGRESS", limit=5)
    logger.info(f"Progress: {len(progress)}")

    # Test getting patterns
    patterns = await client.get_system_patterns(limit=5)
    logger.info(f"Patterns: {len(patterns)}")

if __name__ == "__main__":
    asyncio.run(test_conport_client())
