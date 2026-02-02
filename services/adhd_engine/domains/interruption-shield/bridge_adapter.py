"""
Interruption Shield DopeconBridge Adapter

Focus protection via DopeconBridge for:
- Interruption detection and logging
- Focus session management
- Distraction tracking
"""

from typing import Dict, Any, Optional
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


class InterruptionShieldBridgeAdapter:
    """DopeconBridge adapter for Interruption Shield service"""
    
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
        logger.info(f"✅ Interruption Shield DopeconBridge adapter initialized (workspace: {workspace_id})")
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def log_interruption(
        self,
        interruption_type: str,
        source: str,
        severity: str = "medium",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Log an interruption event"""
        try:
            interruption_id = f"interrupt_{datetime.utcnow().isoformat()}"
            
            await self.client.save_custom_data(
                workspace_id=self.workspace_id,
                category="interruptions",
                key=interruption_id,
                value={
                    "interruption_id": interruption_id,
                    "type": interruption_type,
                    "source": source,
                    "severity": severity,
                    "metadata": metadata or {},
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )
            
            await self.client.publish_event(
                event_type="shield.interruption.detected",
                data={
                    "type": interruption_type,
                    "source": source,
                    "severity": severity,
                    "workspace_id": self.workspace_id,
                },
                source="interruption-shield",
            )
            
            logger.warning(f"Logged interruption: {interruption_type} from {source} ({severity})")
            return True
        except Exception as e:
            logger.error(f"Failed to log interruption: {e}")
            return False
    
    async def start_focus_session(
        self,
        session_id: str,
        duration_minutes: int,
        focus_goal: Optional[str] = None,
    ) -> bool:
        """Start a focus session"""
        try:
            await self.client.save_custom_data(
                workspace_id=self.workspace_id,
                category="focus_sessions",
                key=session_id,
                value={
                    "session_id": session_id,
                    "duration_minutes": duration_minutes,
                    "focus_goal": focus_goal,
                    "started_at": datetime.utcnow().isoformat(),
                    "status": "active",
                },
            )
            
            await self.client.publish_event(
                event_type="shield.focus.started",
                data={
                    "session_id": session_id,
                    "duration": duration_minutes,
                    "workspace_id": self.workspace_id,
                },
                source="interruption-shield",
            )
            
            logger.info(f"Started focus session: {session_id} ({duration_minutes}min)")
            return True
        except Exception as e:
            logger.error(f"Failed to start focus session: {e}")
            return False
    
    async def end_focus_session(
        self,
        session_id: str,
        interruption_count: int,
        completion_percentage: float,
    ) -> bool:
        """End a focus session"""
        try:
            await self.client.publish_event(
                event_type="shield.focus.ended",
                data={
                    "session_id": session_id,
                    "interruptions": interruption_count,
                    "completion": completion_percentage,
                    "ended_at": datetime.utcnow().isoformat(),
                    "workspace_id": self.workspace_id,
                },
                source="interruption-shield",
            )
            
            logger.info(f"Ended focus session: {session_id} ({completion_percentage}% complete, {interruption_count} interruptions)")
            return True
        except Exception as e:
            logger.error(f"Failed to end focus session: {e}")
            return False
