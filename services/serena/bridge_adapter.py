"""
Serena v2 DopeconBridge Adapter

Replaces direct PostgreSQL/AGE database access with DopeconBridge client usage.
Provides the same interface as ConPortDBClient but uses the bridge as backend.
"""

import logging
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List

# Add shared modules to path
SHARED_DIR = Path(__file__).parent.parent.parent / "shared"
if str(SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(SHARED_DIR))

from dopecon_bridge_client import (
    AsyncDopeconBridgeClient,
    DopeconBridgeConfig,
)

logger = logging.getLogger(__name__)


class SerenaBridgeAdapter:
    """
    DopeconBridge adapter for Serena v2.
    
    Replaces ConPortDBClient's direct database access with bridge calls.
    Provides the same API surface for gradual migration.
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 5455,
        database: str = "dopemux_knowledge_graph",
        user: str = "dopemux_age",
        password: Optional[str] = None,
        workspace_id: Optional[str] = None,
    ):
        """
        Initialize Serena bridge adapter.
        
        Note: host/port/database/user/password are kept for API compatibility
        but are not used - all access goes through DopeconBridge.

        Args:
            host: Ignored (kept for compatibility)
            port: Ignored (kept for compatibility)
            database: Ignored (kept for compatibility)
            user: Ignored (kept for compatibility)
            password: Ignored (kept for compatibility)
            workspace_id: Workspace identifier (defaults from env)
        """
        self.workspace_id = workspace_id or os.getenv(
            "WORKSPACE_ROOT",
            str(Path.cwd())
        )
        
        # Initialize DopeconBridge client
        config = DopeconBridgeConfig.from_env()
        self.client = AsyncDopeconBridgeClient(config=config)
        
        # Compatibility attributes
        self._pool = None
        
        logger.info(
            f"✅ Serena DopeconBridge adapter initialized "
            f"(workspace: {self.workspace_id})"
        )
        logger.warning(
            "Direct database parameters (host/port/database/user) are ignored. "
            "All access goes through DopeconBridge."
        )

    async def connect(self):
        """Establish connection (compatibility method, no-op for bridge)."""
        logger.debug("Connect called (no-op for bridge adapter)")

    async def disconnect(self):
        """Close connection (compatibility method)."""
        await self.client.aclose()
        logger.debug("Bridge adapter closed")

    async def get_active_context(
        self,
        workspace_id: str = None,
        session_id: str = None,
    ) -> Optional[Dict]:
        """
        Get active context via DopeconBridge.
        
        Args:
            workspace_id: Workspace identifier (optional, uses configured)
            session_id: Optional session ID
            
        Returns:
            Active context dict or None
        """
        workspace = workspace_id or self.workspace_id
        
        try:
            # Use bridge to get recent decisions (proxy for context)
            decisions = await self.client.recent_decisions(
                workspace_id=workspace,
                limit=1,
            )
            
            if decisions.count > 0 and decisions.items:
                # Return in old format for compatibility
                decision = decisions.items[0]
                return {
                    "summary": decision.get("summary", ""),
                    "rationale": decision.get("rationale", ""),
                    "content": decision.get("implementation_details", ""),
                    "tags": decision.get("tags", []),
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get active context via bridge: {e}")
            return None

    async def search_decisions(
        self,
        query: str,
        workspace_id: str = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Search decisions via DopeconBridge.
        
        Args:
            query: Search query
            workspace_id: Optional workspace filter
            limit: Maximum results
            
        Returns:
            List of decision dicts
        """
        workspace = workspace_id or self.workspace_id
        
        try:
            results = await self.client.search_decisions(
                query=query,
                workspace_id=workspace,
                limit=limit,
            )
            return results.items
        except Exception as e:
            logger.error(f"Failed to search decisions via bridge: {e}")
            return []

    async def get_recent_decisions(
        self,
        workspace_id: str = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Get recent decisions via DopeconBridge.
        
        Args:
            workspace_id: Optional workspace filter
            limit: Maximum results
            
        Returns:
            List of decision dicts
        """
        workspace = workspace_id or self.workspace_id
        
        try:
            results = await self.client.recent_decisions(
                workspace_id=workspace,
                limit=limit,
            )
            return results.items
        except Exception as e:
            logger.error(f"Failed to get recent decisions via bridge: {e}")
            return []

    async def get_related_decisions(
        self,
        decision_id: str,
        k: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Get related decisions via DopeconBridge.
        
        Args:
            decision_id: Decision to find relations for
            k: Number of related decisions
            
        Returns:
            List of related decision dicts
        """
        try:
            results = await self.client.related_decisions(
                decision_id=decision_id,
                k=k,
            )
            return results.items
        except Exception as e:
            logger.error(f"Failed to get related decisions via bridge: {e}")
            return []

    async def semantic_search(
        self,
        query: str,
        workspace_id: str = None,
        k: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Semantic search via DopeconBridge.
        
        Args:
            query: Search text
            workspace_id: Optional workspace filter
            k: Number of results
            
        Returns:
            List of semantically related decisions
        """
        workspace = workspace_id or self.workspace_id
        
        try:
            results = await self.client.related_text(
                query=query,
                workspace_id=workspace,
                k=k,
            )
            return results.items
        except Exception as e:
            logger.error(f"Failed semantic search via bridge: {e}")
            return []

    async def create_decision(
        self,
        summary: str,
        rationale: str,
        implementation_details: str = None,
        tags: List[str] = None,
        workspace_id: str = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Create a decision via DopeconBridge.
        
        Args:
            summary: Decision summary
            rationale: Decision rationale
            implementation_details: Optional implementation details
            tags: Optional tags list
            workspace_id: Optional workspace override
            
        Returns:
            Created decision dict or None
        """
        workspace = workspace_id or self.workspace_id
        
        try:
            result = await self.client.create_decision(
                summary=summary,
                rationale=rationale,
                implementation_details=implementation_details,
                tags=tags or [],
                workspace_id=workspace,
            )
            return dict(result)
        except Exception as e:
            logger.error(f"Failed to create decision via bridge: {e}")
            return None

    async def save_navigation_state(
        self,
        state_data: Dict[str, Any],
        workspace_id: str = None,
    ) -> bool:
        """
        Save Serena navigation state via DopeconBridge custom data.
        
        Args:
            state_data: Navigation state to save
            workspace_id: Optional workspace override
            
        Returns:
            True if successful
        """
        workspace = workspace_id or self.workspace_id
        
        try:
            success = await self.client.save_custom_data(
                workspace_id=workspace,
                category="serena_navigation",
                key="latest_state",
                value=state_data,
            )
            return success
        except Exception as e:
            logger.error(f"Failed to save navigation state via bridge: {e}")
            return False

    async def get_navigation_state(
        self,
        workspace_id: str = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Get Serena navigation state via DopeconBridge custom data.
        
        Args:
            workspace_id: Optional workspace override
            
        Returns:
            Navigation state dict or None
        """
        workspace = workspace_id or self.workspace_id
        
        try:
            results = await self.client.get_custom_data(
                workspace_id=workspace,
                category="serena_navigation",
                key="latest_state",
                limit=1,
            )
            if results:
                return results[0].get("value", {})
            return None
        except Exception as e:
            logger.error(f"Failed to get navigation state via bridge: {e}")
            return None
