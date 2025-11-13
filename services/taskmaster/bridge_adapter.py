"""
TaskMaster DopeconBridge Adapter

Task management via DopeconBridge for:
- Task creation and tracking
- Task orchestration
- Cross-plane task sync
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


class TaskMasterBridgeAdapter:
    """DopeconBridge adapter for TaskMaster service"""
    
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
        logger.info(f"✅ TaskMaster DopeconBridge adapter initialized (workspace: {workspace_id})")
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def create_task(
        self,
        title: str,
        description: str,
        priority: int = 3,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create task via DopeconBridge"""
        try:
            result = await self.client.create_progress_entry(
                description=f"{title}: {description}",
                status="TODO",
                metadata={
                    "taskmaster_task": True,
                    "priority": priority,
                    "tags": tags or [],
                    "title": title,
                    **(metadata or {}),
                },
                workspace_id=self.workspace_id,
            )
            
            # Publish event
            await self.client.publish_event(
                event_type="taskmaster.task.created",
                data={
                    "task_id": result.get("id"),
                    "title": title,
                    "priority": priority,
                    "workspace_id": self.workspace_id,
                },
                source="taskmaster",
            )
            
            logger.info(f"Created task: {title} (priority: {priority})")
            return result
        except Exception as e:
            logger.error(f"Failed to create task: {e}")
            return {}
    
    async def get_tasks(
        self,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Get tasks via DopeconBridge"""
        try:
            entries = await self.client.get_progress_entries(
                workspace_id=self.workspace_id,
                limit=limit,
                status=status,
            )
            
            # Filter for TaskMaster tasks
            taskmaster_tasks = [
                entry for entry in entries
                if entry.get("metadata", {}).get("taskmaster_task", False)
            ]
            
            return taskmaster_tasks
        except Exception as e:
            logger.error(f"Failed to get tasks: {e}")
            return []
    
    async def update_task_status(
        self,
        task_id: str,
        new_status: str,
    ) -> bool:
        """Update task status"""
        try:
            # Create a new progress entry with updated status
            # (In real implementation, would update existing entry)
            await self.client.publish_event(
                event_type="taskmaster.task.status_updated",
                data={
                    "task_id": task_id,
                    "new_status": new_status,
                    "updated_at": datetime.utcnow().isoformat(),
                    "workspace_id": self.workspace_id,
                },
                source="taskmaster",
            )
            
            logger.info(f"Updated task {task_id} status: {new_status}")
            return True
        except Exception as e:
            logger.error(f"Failed to update task status: {e}")
            return False
    
    async def sync_to_pm_plane(
        self,
        task_id: str,
    ) -> bool:
        """Sync task to PM plane (Leantime/etc)"""
        try:
            # Get task details
            tasks = await self.get_tasks()
            task = next((t for t in tasks if t.get("id") == task_id), None)
            
            if not task:
                logger.error(f"Task {task_id} not found")
                return False
            
            # Route to PM plane
            response = await self.client.route_pm(
                operation="taskmaster.sync_task",
                data={
                    "task_id": task_id,
                    "title": task.get("metadata", {}).get("title", "Untitled"),
                    "description": task.get("description", ""),
                    "priority": task.get("metadata", {}).get("priority", 3),
                    "status": task.get("status", "TODO"),
                },
                requester="taskmaster",
            )
            
            if response.success:
                # Save sync record
                await self.client.save_custom_data(
                    workspace_id=self.workspace_id,
                    category="taskmaster_pm_sync",
                    key=task_id,
                    value={
                        "task_id": task_id,
                        "pm_task_id": response.data.get("pm_task_id"),
                        "synced_at": datetime.utcnow().isoformat(),
                    },
                )
                
                logger.info(f"Synced task {task_id} to PM plane")
            
            return response.success
        except Exception as e:
            logger.error(f"Failed to sync task to PM plane: {e}")
            return False
    
    async def assign_task(
        self,
        task_id: str,
        assignee: str,
    ) -> bool:
        """Assign task to a user"""
        try:
            await self.client.publish_event(
                event_type="taskmaster.task.assigned",
                data={
                    "task_id": task_id,
                    "assignee": assignee,
                    "assigned_at": datetime.utcnow().isoformat(),
                    "workspace_id": self.workspace_id,
                },
                source="taskmaster",
            )
            
            logger.info(f"Assigned task {task_id} to {assignee}")
            return True
        except Exception as e:
            logger.error(f"Failed to assign task: {e}")
            return False
    
    async def add_task_comment(
        self,
        task_id: str,
        comment: str,
        author: str,
    ) -> bool:
        """Add comment to task"""
        try:
            await self.client.save_custom_data(
                workspace_id=self.workspace_id,
                category="task_comments",
                key=f"{task_id}_{datetime.utcnow().isoformat()}",
                value={
                    "task_id": task_id,
                    "comment": comment,
                    "author": author,
                    "created_at": datetime.utcnow().isoformat(),
                },
            )
            
            await self.client.publish_event(
                event_type="taskmaster.task.commented",
                data={
                    "task_id": task_id,
                    "author": author,
                    "workspace_id": self.workspace_id,
                },
                source="taskmaster",
            )
            
            logger.info(f"Added comment to task {task_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to add task comment: {e}")
            return False
    
    async def get_task_comments(
        self,
        task_id: str,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Get comments for a task"""
        try:
            results = await self.client.get_custom_data(
                workspace_id=self.workspace_id,
                category="task_comments",
                limit=limit,
            )
            
            # Filter for this task
            task_comments = [
                r.get("value", {})
                for r in results
                if r.get("value", {}).get("task_id") == task_id
            ]
            
            return task_comments
        except Exception as e:
            logger.error(f"Failed to get task comments: {e}")
            return []
    
    async def complete_task(
        self,
        task_id: str,
        completion_notes: Optional[str] = None,
    ) -> bool:
        """Mark task as completed"""
        try:
            # Update status
            await self.update_task_status(task_id, "DONE")
            
            # Save completion data
            await self.client.save_custom_data(
                workspace_id=self.workspace_id,
                category="task_completions",
                key=task_id,
                value={
                    "task_id": task_id,
                    "completed_at": datetime.utcnow().isoformat(),
                    "notes": completion_notes,
                },
            )
            
            # Publish event
            await self.client.publish_event(
                event_type="taskmaster.task.completed",
                data={
                    "task_id": task_id,
                    "workspace_id": self.workspace_id,
                },
                source="taskmaster",
            )
            
            logger.info(f"Completed task: {task_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to complete task: {e}")
            return False
