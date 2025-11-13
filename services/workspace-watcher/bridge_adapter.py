"""
Workspace Watcher DopeconBridge Adapter

File system monitoring via DopeconBridge for:
- File change detection
- Project activity tracking
- Workspace state monitoring
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


class WorkspaceWatcherBridgeAdapter:
    """DopeconBridge adapter for Workspace Watcher service"""
    
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
        logger.info(f"✅ Workspace Watcher DopeconBridge adapter initialized (workspace: {workspace_id})")
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def log_file_change(
        self,
        file_path: str,
        change_type: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Log file system change"""
        try:
            await self.client.publish_event(
                event_type=f"workspace.file.{change_type}",
                data={
                    "file_path": file_path,
                    "change_type": change_type,
                    "metadata": metadata or {},
                    "timestamp": datetime.utcnow().isoformat(),
                    "workspace_id": self.workspace_id,
                },
                source="workspace-watcher",
            )
            
            logger.debug(f"Logged file change: {change_type} {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to log file change: {e}")
            return False
    
    async def save_workspace_snapshot(
        self,
        snapshot_data: Dict[str, Any],
    ) -> bool:
        """Save workspace state snapshot"""
        try:
            snapshot_id = f"snapshot_{datetime.utcnow().isoformat()}"
            
            success = await self.client.save_custom_data(
                workspace_id=self.workspace_id,
                category="workspace_snapshots",
                key=snapshot_id,
                value={
                    "snapshot_id": snapshot_id,
                    "data": snapshot_data,
                    "created_at": datetime.utcnow().isoformat(),
                },
            )
            
            logger.info(f"Saved workspace snapshot: {snapshot_id}")
            return success
        except Exception as e:
            logger.error(f"Failed to save workspace snapshot: {e}")
            return False
    
    async def get_file_history(
        self,
        file_path: str,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Get change history for a file"""
        try:
            # Query events for this file
            history = await self.client.get_event_history(
                stream="dopemux:events",
                count=limit,
            )
            
            # Filter for this file
            file_events = [
                event for event in history.events
                if event.get("data", {}).get("file_path") == file_path
            ]
            
            return file_events
        except Exception as e:
            logger.error(f"Failed to get file history: {e}")
            return []
    
    async def track_project_activity(
        self,
        project_path: str,
        activity_summary: Dict[str, Any],
    ) -> bool:
        """Track project-level activity"""
        try:
            await self.client.save_custom_data(
                workspace_id=self.workspace_id,
                category="project_activity",
                key=f"{Path(project_path).name}_{datetime.utcnow().date().isoformat()}",
                value={
                    "project_path": project_path,
                    "summary": activity_summary,
                    "date": datetime.utcnow().date().isoformat(),
                    "updated_at": datetime.utcnow().isoformat(),
                },
            )
            
            logger.info(f"Tracked project activity: {project_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to track project activity: {e}")
            return False
