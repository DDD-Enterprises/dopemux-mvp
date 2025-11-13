"""
Session Intelligence DopeconBridge Adapter

Session analytics via DopeconBridge for:
- Session pattern detection
- Productivity analysis
- Session optimization
- Intelligence gathering
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime, timedelta
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


class SessionIntelligenceBridgeAdapter:
    """DopeconBridge adapter for Session Intelligence service"""
    
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
        logger.info(f"✅ Session Intelligence DopeconBridge adapter initialized (workspace: {workspace_id})")
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def start_session_tracking(
        self,
        session_id: str,
        session_type: str,
        initial_context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Start tracking a work session"""
        try:
            await self.client.save_custom_data(
                workspace_id=self.workspace_id,
                category="session_tracking",
                key=session_id,
                value={
                    "session_id": session_id,
                    "type": session_type,
                    "started_at": datetime.utcnow().isoformat(),
                    "initial_context": initial_context or {},
                    "status": "active",
                },
            )
            
            await self.client.publish_event(
                event_type="session.started",
                data={
                    "session_id": session_id,
                    "type": session_type,
                    "workspace_id": self.workspace_id,
                },
                source="session-intelligence",
            )
            
            logger.info(f"Started session tracking: {session_id} ({session_type})")
            return True
        except Exception as e:
            logger.error(f"Failed to start session tracking: {e}")
            return False
    
    async def end_session_tracking(
        self,
        session_id: str,
        session_summary: Dict[str, Any],
    ) -> bool:
        """End session tracking and record summary"""
        try:
            await self.client.publish_event(
                event_type="session.ended",
                data={
                    "session_id": session_id,
                    "ended_at": datetime.utcnow().isoformat(),
                    "summary": session_summary,
                    "workspace_id": self.workspace_id,
                },
                source="session-intelligence",
            )
            
            # Save summary as custom data
            await self.client.save_custom_data(
                workspace_id=self.workspace_id,
                category="session_summaries",
                key=session_id,
                value={
                    "session_id": session_id,
                    "summary": session_summary,
                    "ended_at": datetime.utcnow().isoformat(),
                },
            )
            
            logger.info(f"Ended session tracking: {session_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to end session tracking: {e}")
            return False
    
    async def analyze_session_patterns(
        self,
        days: int = 7,
    ) -> Dict[str, Any]:
        """Analyze patterns across recent sessions"""
        try:
            results = await self.client.get_custom_data(
                workspace_id=self.workspace_id,
                category="session_summaries",
                limit=days * 10,
            )
            
            sessions = [r.get("value", {}) for r in results]
            
            if not sessions:
                return {"pattern": "insufficient_data"}
            
            total_sessions = len(sessions)
            avg_duration = sum(
                s.get("summary", {}).get("duration", 0)
                for s in sessions
            ) / total_sessions if total_sessions > 0 else 0
            
            patterns = {
                "total_sessions": total_sessions,
                "average_duration": avg_duration,
                "analysis_period_days": days,
            }
            
            logger.info(f"Session patterns: {total_sessions} sessions, avg {avg_duration:.1f}min")
            return patterns
        except Exception as e:
            logger.error(f"Failed to analyze session patterns: {e}")
            return {}
