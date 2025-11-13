"""
Leantime DopeconBridge Adapter

PM Plane integration for Leantime via DopeconBridge.

Features:
- Task synchronization (PM ↔ Cognitive)
- Project updates
- Sprint planning
- Resource allocation
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


class LeantimeBridgeAdapter:
    """
    DopeconBridge adapter for Leantime PM plane integration.
    
    Features:
    - Task synchronization (PM ↔ Cognitive)
    - Project updates
    - Sprint planning
    - Resource allocation
    """
    
    def __init__(
        self,
        workspace_id: str,
        base_url: str = None,
        token: str = None,
    ):
        self.workspace_id = workspace_id
        
        # Use PM plane for Leantime
        config = DopeconBridgeConfig.from_env()
        if base_url:
            config = DopeconBridgeConfig(
                base_url=base_url,
                token=token or config.token,
                source_plane="pm_plane",  # PM plane for Leantime
                timeout=config.timeout,
            )
        else:
            config.source_plane = "pm_plane"
        
        self.client = AsyncDopeconBridgeClient(config=config)
        logger.info(f"✅ Leantime DopeconBridge adapter initialized (PM plane, workspace: {workspace_id})")
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def sync_task_to_leantime(
        self,
        task_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Sync cognitive task to PM plane (Leantime)"""
        try:
            response = await self.client.route_pm(
                operation="leantime.create_task",
                data=task_data,
                requester="cognitive-task-sync",
            )
            
            if response.success:
                logger.info(f"Synced task to Leantime: {task_data.get('title')}")
                return response.data
            else:
                logger.error(f"Failed to sync task to Leantime: {response.error}")
                return {}
        except Exception as e:
            logger.error(f"Failed to sync task to Leantime: {e}")
            return {}
    
    async def get_leantime_tasks(
        self,
        project_id: str,
    ) -> List[Dict[str, Any]]:
        """Get tasks from Leantime via DopeconBridge"""
        try:
            response = await self.client.route_pm(
                operation="leantime.get_tasks",
                data={"project_id": project_id},
                requester="cognitive-query",
            )
            
            if response.success:
                return response.data.get("tasks", [])
            return []
        except Exception as e:
            logger.error(f"Failed to get Leantime tasks: {e}")
            return []
    
    async def update_sprint_status(
        self,
        sprint_id: str,
        status: str,
        completion: float,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Update sprint status in Leantime"""
        try:
            response = await self.client.route_pm(
                operation="leantime.update_sprint",
                data={
                    "sprint_id": sprint_id,
                    "status": status,
                    "completion": completion,
                    "metadata": metadata or {},
                    "updated_at": datetime.utcnow().isoformat(),
                },
                requester="sprint-tracker",
            )
            
            if response.success:
                # Publish event
                await self.client.publish_event(
                    event_type="leantime.sprint.updated",
                    data={
                        "sprint_id": sprint_id,
                        "status": status,
                        "completion": completion,
                    },
                    source="leantime-adapter",
                )
                logger.info(f"Updated sprint {sprint_id}: {status} ({completion}%)")
            
            return response.success
        except Exception as e:
            logger.error(f"Failed to update sprint status: {e}")
            return False
    
    async def create_project(
        self,
        project_name: str,
        project_details: Dict[str, Any],
    ) -> Optional[str]:
        """Create project in Leantime"""
        try:
            response = await self.client.route_pm(
                operation="leantime.create_project",
                data={
                    "name": project_name,
                    "details": project_details,
                },
                requester="project-manager",
            )
            
            if response.success:
                project_id = response.data.get("project_id")
                logger.info(f"Created project in Leantime: {project_name} (ID: {project_id})")
                return project_id
            return None
        except Exception as e:
            logger.error(f"Failed to create project: {e}")
            return None
    
    async def get_project_status(
        self,
        project_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Get project status from Leantime"""
        try:
            response = await self.client.route_pm(
                operation="leantime.get_project_status",
                data={"project_id": project_id},
                requester="status-query",
            )
            
            if response.success:
                return response.data
            return None
        except Exception as e:
            logger.error(f"Failed to get project status: {e}")
            return None
    
    async def allocate_resource(
        self,
        resource_type: str,
        resource_id: str,
        allocation_data: Dict[str, Any],
    ) -> bool:
        """Allocate resource in Leantime"""
        try:
            response = await self.client.route_pm(
                operation="leantime.allocate_resource",
                data={
                    "resource_type": resource_type,
                    "resource_id": resource_id,
                    "allocation": allocation_data,
                },
                requester="resource-manager",
            )
            
            if response.success:
                await self.client.publish_event(
                    event_type="leantime.resource.allocated",
                    data={
                        "resource_type": resource_type,
                        "resource_id": resource_id,
                    },
                    source="leantime-adapter",
                )
                logger.info(f"Allocated resource: {resource_type}:{resource_id}")
            
            return response.success
        except Exception as e:
            logger.error(f"Failed to allocate resource: {e}")
            return False
    
    async def sync_from_cognitive(
        self,
        cognitive_task_id: str,
        cognitive_task_data: Dict[str, Any],
    ) -> Optional[str]:
        """
        Sync a task from cognitive plane to Leantime.
        Returns Leantime task ID if successful.
        """
        try:
            # Create corresponding task in Leantime
            response = await self.sync_task_to_leantime({
                "title": cognitive_task_data.get("title", "Untitled Task"),
                "description": cognitive_task_data.get("description", ""),
                "priority": cognitive_task_data.get("priority", 3),
                "cognitive_task_id": cognitive_task_id,
                "metadata": cognitive_task_data.get("metadata", {}),
            })
            
            if response:
                leantime_task_id = response.get("task_id")
                
                # Save mapping
                await self.client.save_custom_data(
                    workspace_id=self.workspace_id,
                    category="task_mappings",
                    key=f"cognitive_{cognitive_task_id}",
                    value={
                        "cognitive_id": cognitive_task_id,
                        "leantime_id": leantime_task_id,
                        "synced_at": datetime.utcnow().isoformat(),
                    },
                )
                
                logger.info(f"Synced cognitive task {cognitive_task_id} → Leantime task {leantime_task_id}")
                return leantime_task_id
            
            return None
        except Exception as e:
            logger.error(f"Failed to sync from cognitive plane: {e}")
            return None
    
    async def get_task_mapping(
        self,
        cognitive_task_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Get the Leantime task ID for a cognitive task"""
        try:
            results = await self.client.get_custom_data(
                workspace_id=self.workspace_id,
                category="task_mappings",
                key=f"cognitive_{cognitive_task_id}",
                limit=1,
            )
            if results:
                return results[0].get("value", {})
            return None
        except Exception as e:
            logger.error(f"Failed to get task mapping: {e}")
            return None
