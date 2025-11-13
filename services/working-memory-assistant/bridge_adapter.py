"""
Working Memory Assistant DopeconBridge Adapter

Working memory management via DopeconBridge for:
- Memory state tracking
- Context preservation
- Memory capacity monitoring
- Cognitive load management
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime
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


class WorkingMemoryBridgeAdapter:
    """DopeconBridge adapter for Working Memory Assistant service"""
    
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
        logger.info(f"✅ Working Memory Assistant DopeconBridge adapter initialized (workspace: {workspace_id})")
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def save_memory_state(
        self,
        state_type: str,
        content: Dict[str, Any],
        priority: int = 5,
    ) -> bool:
        """Save working memory state"""
        try:
            state_id = f"memory_{state_type}_{datetime.utcnow().isoformat()}"
            
            await self.client.save_custom_data(
                workspace_id=self.workspace_id,
                category="working_memory",
                key=state_id,
                value={
                    "state_id": state_id,
                    "type": state_type,
                    "content": content,
                    "priority": priority,
                    "created_at": datetime.utcnow().isoformat(),
                },
            )
            
            await self.client.publish_event(
                event_type="memory.state.saved",
                data={
                    "state_type": state_type,
                    "priority": priority,
                    "workspace_id": self.workspace_id,
                },
                source="working-memory-assistant",
            )
            
            logger.info(f"Saved memory state: {state_type} (priority {priority})")
            return True
        except Exception as e:
            logger.error(f"Failed to save memory state: {e}")
            return False
    
    async def get_memory_state(
        self,
        state_type: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Get working memory states"""
        try:
            results = await self.client.get_custom_data(
                workspace_id=self.workspace_id,
                category="working_memory",
                limit=limit,
            )
            
            states = [r.get("value", {}) for r in results]
            
            # Filter by type if specified
            if state_type:
                states = [s for s in states if s.get("type") == state_type]
            
            # Sort by priority
            states.sort(key=lambda x: x.get("priority", 0), reverse=True)
            
            return states
        except Exception as e:
            logger.error(f"Failed to get memory state: {e}")
            return []
    
    async def log_cognitive_load(
        self,
        load_level: float,
        active_tasks: int,
        context_switches: int,
    ) -> bool:
        """Log current cognitive load"""
        try:
            await self.client.publish_event(
                event_type="memory.cognitive_load.updated",
                data={
                    "load_level": load_level,
                    "active_tasks": active_tasks,
                    "context_switches": context_switches,
                    "timestamp": datetime.utcnow().isoformat(),
                    "workspace_id": self.workspace_id,
                },
                source="working-memory-assistant",
            )
            
            logger.debug(f"Logged cognitive load: {load_level:.2f} ({active_tasks} tasks)")
            return True
        except Exception as e:
            logger.error(f"Failed to log cognitive load: {e}")
            return False
    
    async def preserve_context(
        self,
        context_name: str,
        context_data: Dict[str, Any],
    ) -> bool:
        """Preserve context for later restoration"""
        try:
            context_id = f"context_{context_name}_{datetime.utcnow().isoformat()}"
            
            await self.client.save_custom_data(
                workspace_id=self.workspace_id,
                category="preserved_contexts",
                key=context_id,
                value={
                    "context_id": context_id,
                    "name": context_name,
                    "data": context_data,
                    "preserved_at": datetime.utcnow().isoformat(),
                },
            )
            
            logger.info(f"Preserved context: {context_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to preserve context: {e}")
            return False
    
    async def restore_context(
        self,
        context_name: str,
    ) -> Optional[Dict[str, Any]]:
        """Restore a previously preserved context"""
        try:
            results = await self.client.get_custom_data(
                workspace_id=self.workspace_id,
                category="preserved_contexts",
                limit=50,
            )
            
            # Find most recent matching context
            for r in results:
                ctx = r.get("value", {})
                if ctx.get("name") == context_name:
                    logger.info(f"Restored context: {context_name}")
                    return ctx.get("data", {})
            
            logger.warning(f"Context not found: {context_name}")
            return None
        except Exception as e:
            logger.error(f"Failed to restore context: {e}")
            return None
    
    async def monitor_memory_capacity(
        self,
    ) -> Dict[str, Any]:
        """Monitor working memory capacity usage"""
        try:
            states = await self.get_memory_state(limit=100)
            
            total_items = len(states)
            high_priority = len([s for s in states if s.get("priority", 0) >= 7])
            
            # Simplified capacity calculation
            capacity_percentage = min(100, (total_items / 7) * 100)  # Miller's 7±2 rule
            
            capacity = {
                "total_items": total_items,
                "high_priority_items": high_priority,
                "capacity_used_percent": capacity_percentage,
                "status": "overloaded" if capacity_percentage > 100 else "normal",
                "recommendation": self._get_capacity_recommendation(capacity_percentage),
            }
            
            logger.info(f"Memory capacity: {capacity_percentage:.1f}% ({total_items} items)")
            return capacity
        except Exception as e:
            logger.error(f"Failed to monitor memory capacity: {e}")
            return {}
    
    def _get_capacity_recommendation(self, capacity_percent: float) -> str:
        """Get recommendation based on capacity usage"""
        if capacity_percent < 50:
            return "Memory capacity healthy - good space for new information"
        elif capacity_percent < 80:
            return "Memory capacity moderate - consider offloading low-priority items"
        elif capacity_percent < 100:
            return "Memory capacity high - offload or consolidate items recommended"
        else:
            return "Memory capacity exceeded - immediate offloading required"
