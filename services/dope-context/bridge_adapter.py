"""
Dope Context DopeconBridge Adapter

Manages context via DopeconBridge for:
- Active context tracking
- Context switching
- Multi-workspace context
- Context history
"""

from typing import Dict, Any, Optional, List
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


class DopeContextBridgeAdapter:
    """DopeconBridge adapter for Dope Context service"""
    
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
        logger.info(f"✅ Dope Context DopeconBridge adapter initialized (workspace: {workspace_id})")
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def set_active_context(
        self,
        context_id: str,
        context_data: Dict[str, Any],
    ) -> bool:
        """Set active context via DopeconBridge custom data"""
        try:
            success = await self.client.save_custom_data(
                workspace_id=self.workspace_id,
                category="active_context",
                key=context_id,
                value={
                    **context_data,
                    "activated_at": datetime.utcnow().isoformat(),
                    "context_id": context_id,
                },
            )
            
            if success:
                await self.client.publish_event(
                    event_type="context.activated",
                    data={
                        "context_id": context_id,
                        "workspace_id": self.workspace_id,
                    },
                    source="dope-context",
                )
            
            logger.info(f"Set active context: {context_id}")
            return success
        except Exception as e:
            logger.error(f"Failed to set active context: {e}")
            return False
    
    async def get_active_context(
        self,
        context_id: str = "default",
    ) -> Optional[Dict[str, Any]]:
        """Get active context"""
        try:
            results = await self.client.get_custom_data(
                workspace_id=self.workspace_id,
                category="active_context",
                key=context_id,
                limit=1,
            )
            if results:
                return results[0].get("value", {})
            return None
        except Exception as e:
            logger.error(f"Failed to get active context: {e}")
            return None
    
    async def log_context_switch(
        self,
        from_context: str,
        to_context: str,
        reason: str,
    ) -> bool:
        """Log context switch event"""
        try:
            # Save switch record
            await self.client.save_custom_data(
                workspace_id=self.workspace_id,
                category="context_switches",
                key=f"switch_{datetime.utcnow().isoformat()}",
                value={
                    "from": from_context,
                    "to": to_context,
                    "reason": reason,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )
            
            # Publish event
            await self.client.publish_event(
                event_type="context.switched",
                data={
                    "from": from_context,
                    "to": to_context,
                    "reason": reason,
                    "workspace_id": self.workspace_id,
                },
                source="dope-context",
            )
            
            logger.info(f"Context switch: {from_context} → {to_context} ({reason})")
            return True
        except Exception as e:
            logger.error(f"Failed to log context switch: {e}")
            return False
    
    async def get_context_history(
        self,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """Get context switch history"""
        try:
            results = await self.client.get_custom_data(
                workspace_id=self.workspace_id,
                category="context_switches",
                limit=limit,
            )
            return [r.get("value", {}) for r in results]
        except Exception as e:
            logger.error(f"Failed to get context history: {e}")
            return []
    
    async def save_context_snapshot(
        self,
        snapshot_id: str,
        snapshot_data: Dict[str, Any],
    ) -> bool:
        """Save a context snapshot for recovery"""
        try:
            success = await self.client.save_custom_data(
                workspace_id=self.workspace_id,
                category="context_snapshots",
                key=snapshot_id,
                value={
                    **snapshot_data,
                    "snapshot_id": snapshot_id,
                    "created_at": datetime.utcnow().isoformat(),
                },
            )
            
            if success:
                await self.client.publish_event(
                    event_type="context.snapshot.saved",
                    data={
                        "snapshot_id": snapshot_id,
                        "workspace_id": self.workspace_id,
                    },
                    source="dope-context",
                )
            
            return success
        except Exception as e:
            logger.error(f"Failed to save context snapshot: {e}")
            return False
    
    async def restore_context_snapshot(
        self,
        snapshot_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Restore a context snapshot"""
        try:
            results = await self.client.get_custom_data(
                workspace_id=self.workspace_id,
                category="context_snapshots",
                key=snapshot_id,
                limit=1,
            )
            
            if results:
                snapshot_data = results[0].get("value", {})
                
                await self.client.publish_event(
                    event_type="context.snapshot.restored",
                    data={
                        "snapshot_id": snapshot_id,
                        "workspace_id": self.workspace_id,
                    },
                    source="dope-context",
                )
                
                logger.info(f"Restored context snapshot: {snapshot_id}")
                return snapshot_data
            
            return None
        except Exception as e:
            logger.error(f"Failed to restore context snapshot: {e}")
            return None
    
    async def track_context_metric(
        self,
        metric_name: str,
        metric_value: float,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Track a context-related metric"""
        try:
            await self.client.publish_event(
                event_type="context.metric",
                data={
                    "metric_name": metric_name,
                    "metric_value": metric_value,
                    "metadata": metadata or {},
                    "workspace_id": self.workspace_id,
                    "timestamp": datetime.utcnow().isoformat(),
                },
                source="dope-context",
            )
            return True
        except Exception as e:
            logger.error(f"Failed to track context metric: {e}")
            return False
