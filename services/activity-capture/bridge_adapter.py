"""
Activity Capture DopeconBridge Adapter

Activity tracking via DopeconBridge for:
- Window activity tracking
- Application usage
- Time tracking
- Activity analytics
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


class ActivityCaptureBridgeAdapter:
    """DopeconBridge adapter for Activity Capture service"""
    
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
        logger.info(f"✅ Activity Capture DopeconBridge adapter initialized (workspace: {workspace_id})")
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def log_window_activity(
        self,
        window_title: str,
        application: str,
        duration_seconds: float,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Log window activity"""
        try:
            activity_id = f"activity_{datetime.utcnow().isoformat()}"
            
            await self.client.save_custom_data(
                workspace_id=self.workspace_id,
                category="window_activities",
                key=activity_id,
                value={
                    "activity_id": activity_id,
                    "window_title": window_title,
                    "application": application,
                    "duration": duration_seconds,
                    "metadata": metadata or {},
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )
            
            # Publish activity event
            await self.client.publish_event(
                event_type="activity.window.captured",
                data={
                    "application": application,
                    "duration": duration_seconds,
                    "workspace_id": self.workspace_id,
                },
                source="activity-capture",
            )
            
            logger.debug(f"Logged window activity: {application} ({duration_seconds}s)")
            return True
        except Exception as e:
            logger.error(f"Failed to log window activity: {e}")
            return False
    
    async def log_application_usage(
        self,
        application: str,
        total_time_seconds: float,
        session_count: int,
    ) -> bool:
        """Log application usage summary"""
        try:
            await self.client.save_custom_data(
                workspace_id=self.workspace_id,
                category="app_usage",
                key=f"{application}_{datetime.utcnow().date().isoformat()}",
                value={
                    "application": application,
                    "total_time": total_time_seconds,
                    "session_count": session_count,
                    "date": datetime.utcnow().date().isoformat(),
                    "updated_at": datetime.utcnow().isoformat(),
                },
            )
            
            logger.info(f"Logged app usage: {application} ({total_time_seconds}s, {session_count} sessions)")
            return True
        except Exception as e:
            logger.error(f"Failed to log application usage: {e}")
            return False
    
    async def get_daily_activity(
        self,
        date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get activity for a specific date"""
        try:
            if not date:
                date = datetime.utcnow().date().isoformat()
            
            results = await self.client.get_custom_data(
                workspace_id=self.workspace_id,
                category="window_activities",
                limit=1000,
            )
            
            # Filter by date
            daily_activities = [
                r.get("value", {})
                for r in results
                if r.get("value", {}).get("timestamp", "").startswith(date)
            ]
            
            return daily_activities
        except Exception as e:
            logger.error(f"Failed to get daily activity: {e}")
            return []
    
    async def get_application_stats(
        self,
        application: str,
        days: int = 7,
    ) -> Dict[str, Any]:
        """Get application usage statistics"""
        try:
            results = await self.client.get_custom_data(
                workspace_id=self.workspace_id,
                category="app_usage",
                limit=days * 10,  # Get more than needed
            )
            
            # Filter for this application
            app_data = [
                r.get("value", {})
                for r in results
                if r.get("value", {}).get("application") == application
            ][:days]
            
            if not app_data:
                return {
                    "application": application,
                    "total_time": 0,
                    "average_time": 0,
                    "days_tracked": 0,
                }
            
            total_time = sum(d.get("total_time", 0) for d in app_data)
            
            return {
                "application": application,
                "total_time": total_time,
                "average_time": total_time / len(app_data) if app_data else 0,
                "days_tracked": len(app_data),
                "data": app_data,
            }
        except Exception as e:
            logger.error(f"Failed to get application stats: {e}")
            return {}
    
    async def start_activity_session(
        self,
        session_id: str,
        session_type: str = "work",
    ) -> bool:
        """Start an activity tracking session"""
        try:
            await self.client.save_custom_data(
                workspace_id=self.workspace_id,
                category="activity_sessions",
                key=session_id,
                value={
                    "session_id": session_id,
                    "type": session_type,
                    "started_at": datetime.utcnow().isoformat(),
                    "status": "active",
                },
            )
            
            await self.client.publish_event(
                event_type="activity.session.started",
                data={
                    "session_id": session_id,
                    "type": session_type,
                    "workspace_id": self.workspace_id,
                },
                source="activity-capture",
            )
            
            logger.info(f"Started activity session: {session_id} ({session_type})")
            return True
        except Exception as e:
            logger.error(f"Failed to start activity session: {e}")
            return False
    
    async def end_activity_session(
        self,
        session_id: str,
        summary: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """End an activity tracking session"""
        try:
            await self.client.publish_event(
                event_type="activity.session.ended",
                data={
                    "session_id": session_id,
                    "ended_at": datetime.utcnow().isoformat(),
                    "summary": summary or {},
                    "workspace_id": self.workspace_id,
                },
                source="activity-capture",
            )
            
            logger.info(f"Ended activity session: {session_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to end activity session: {e}")
            return False
    
    async def log_idle_time(
        self,
        idle_duration_seconds: float,
    ) -> bool:
        """Log idle time"""
        try:
            await self.client.publish_event(
                event_type="activity.idle.detected",
                data={
                    "duration": idle_duration_seconds,
                    "timestamp": datetime.utcnow().isoformat(),
                    "workspace_id": self.workspace_id,
                },
                source="activity-capture",
            )
            
            logger.debug(f"Logged idle time: {idle_duration_seconds}s")
            return True
        except Exception as e:
            logger.error(f"Failed to log idle time: {e}")
            return False
