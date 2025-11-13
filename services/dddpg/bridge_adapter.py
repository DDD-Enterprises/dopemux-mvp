"""
DDDPG (Dope Decision Graph) DopeconBridge Adapter

Replaces direct storage access with DopeconBridge client usage.
All decision graph operations flow through DopeconBridge.
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
import sys
import logging

# Add shared modules
SHARED_DIR = Path(__file__).parent.parent / "shared"
sys.path.insert(0, str(SHARED_DIR))

from dopecon_bridge_client import (
    AsyncDopeconBridgeClient,
    DopeconBridgeConfig,
)

logger = logging.getLogger(__name__)


class DDDPGBridgeAdapter:
    """
    DopeconBridge adapter for Dope Decision Graph.
    
    Provides decision graph operations via DopeconBridge:
    - Decision creation and querying
    - Graph traversal and navigation
    - Context-aware decision retrieval
    - Semantic search
    """
    
    def __init__(
        self,
        workspace_id: str,
        base_url: str = None,
        token: str = None,
    ):
        self.workspace_id = workspace_id
        
        config = DopeconBridgeConfig.from_env()
        if base_url:
            config = DopeconBridgeConfig(
                base_url=base_url,
                token=token or config.token,
                source_plane="cognitive_plane",
                timeout=config.timeout,
            )
        
        self.client = AsyncDopeconBridgeClient(config=config)
        logger.info(f"✅ DDDPG DopeconBridge adapter initialized (workspace: {workspace_id})")
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def create_decision(
        self,
        summary: str,
        rationale: str,
        implementation_details: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Create decision via DopeconBridge"""
        try:
            result = await self.client.create_decision(
                summary=summary,
                rationale=rationale,
                implementation_details=implementation_details,
                tags=tags or [],
                workspace_id=self.workspace_id,
            )
            
            logger.info(f"Created decision via DopeconBridge: {result.get('id')}")
            return result
        except Exception as e:
            logger.error(f"Failed to create decision via DopeconBridge: {e}")
            raise
    
    async def get_recent_decisions(
        self,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Get recent decisions via DopeconBridge"""
        try:
            results = await self.client.recent_decisions(
                workspace_id=self.workspace_id,
                limit=limit,
            )
            return results.items if hasattr(results, 'items') else results
        except Exception as e:
            logger.error(f"Failed to get recent decisions: {e}")
            return []
    
    async def search_decisions(
        self,
        query: str,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """Search decisions via DopeconBridge"""
        try:
            results = await self.client.search_decisions(
                query=query,
                workspace_id=self.workspace_id,
                limit=limit,
            )
            return results.items if hasattr(results, 'items') else results
        except Exception as e:
            logger.error(f"Failed to search decisions: {e}")
            return []
    
    async def get_related_decisions(
        self,
        decision_id: str,
        k: int = 10,
    ) -> List[Dict[str, Any]]:
        """Get related decisions via graph traversal"""
        try:
            results = await self.client.related_decisions(
                decision_id=decision_id,
                k=k,
            )
            return results.items if hasattr(results, 'items') else results
        except Exception as e:
            logger.error(f"Failed to get related decisions: {e}")
            return []
    
    async def semantic_search(
        self,
        query: str,
        k: int = 10,
    ) -> List[Dict[str, Any]]:
        """Semantic search via DopeconBridge"""
        try:
            results = await self.client.related_text(
                query=query,
                workspace_id=self.workspace_id,
                k=k,
            )
            return results.items if hasattr(results, 'items') else results
        except Exception as e:
            logger.error(f"Failed to perform semantic search: {e}")
            return []
    
    async def save_graph_state(
        self,
        state_data: Dict[str, Any],
    ) -> bool:
        """Save graph navigation state"""
        try:
            success = await self.client.save_custom_data(
                workspace_id=self.workspace_id,
                category="dddpg_graph_state",
                key="latest_navigation",
                value=state_data,
            )
            
            if success:
                await self.client.publish_event(
                    event_type="dddpg.graph_state.saved",
                    data={"workspace_id": self.workspace_id},
                    source="dddpg",
                )
            
            return success
        except Exception as e:
            logger.error(f"Failed to save graph state: {e}")
            return False
    
    async def get_graph_state(self) -> Optional[Dict[str, Any]]:
        """Get graph navigation state"""
        try:
            results = await self.client.get_custom_data(
                workspace_id=self.workspace_id,
                category="dddpg_graph_state",
                key="latest_navigation",
                limit=1,
            )
            if results:
                return results[0].get("value", {})
            return None
        except Exception as e:
            logger.error(f"Failed to get graph state: {e}")
            return None
    
    async def publish_graph_event(
        self,
        event_type: str,
        data: Dict[str, Any],
    ) -> bool:
        """Publish a DDDPG graph event"""
        try:
            await self.client.publish_event(
                event_type=f"dddpg.{event_type}",
                data={**data, "workspace_id": self.workspace_id},
                source="dddpg",
            )
            return True
        except Exception as e:
            logger.error(f"Failed to publish graph event: {e}")
            return False
