"""
TaskMaster DopeconBridge Adapter

Task management via DopeconBridge for:
- Task creation and tracking
- Task orchestration
- Cross-plane task sync
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime, timezone
import sys
import logging
import httpx

# Add shared modules
SHARED_DIR = Path(__file__).parent.parent / "shared"
sys.path.insert(0, str(SHARED_DIR))

from dopecon_bridge_client import (
    AsyncDopeconBridgeClient,
    DopeconBridgeConfig,
)

from dopemux.pm.models import PMTask, PMTaskStatus, PMTransitionRequest, content_hash_task_id, PMLinkedIDUpdateRequest
from dopemux.pm.store import InMemoryPMTaskStore
from dopemux.pm.writes import PMWriteConfig, pm_update_work_item, pm_transition_work_item, pm_log_progress
from dopemux.pm.mapping import TASKMASTER_TO_CANONICAL
from dopemux.pm.adapters.orchestrator import SyncTaskOrchestratorAdapter

class SyncBridgeAdapterClientStub:
    """Base stub for synchronous bridge clients."""
    def __init__(self, config: DopeconBridgeConfig):
        self.config = config
        self.client = httpx.Client(
            base_url=config.base_url,
            headers={"X-API-Token": config.token} if config.token else {},
            timeout=config.timeout or 10.0
        )

class SyncLeantimeBridgeClient(SyncBridgeAdapterClientStub):
    """Synchronous Leantime bridge client."""
    def update_task(self, task_id: str, updates: Dict[str, Any], idempotency_key: str):
        payload = {"updates": updates, "idempotency_key": idempotency_key}
        resp = self.client.post(f"/pm/leantime/tasks/{task_id}", json=payload)
        resp.raise_for_status()

    def update_status(self, task_id: str, new_status: str, idempotency_key: str):
        payload = {"status": new_status, "idempotency_key": idempotency_key}
        resp = self.client.post(f"/pm/leantime/tasks/{task_id}/status", json=payload)
        resp.raise_for_status()

class SyncOrchestratorBridgeClient(SyncBridgeAdapterClientStub):
    """Synchronous Orchestrator bridge client."""
    def __init__(self, config: DopeconBridgeConfig, project_id: Optional[str] = None):
        super().__init__(config)
        self.project_id = project_id
        self.task_orchestrator = SyncTaskOrchestratorAdapter()

    def transition(self, task_id: str, new_status: PMTaskStatus, reason: str, expected_version: int, idempotency_key: str):
        return self.task_orchestrator.transition(
            task_id=task_id,
            new_status=new_status,
            reason=reason,
            expected_version=expected_version,
            idempotency_key=idempotency_key
        )

class SyncConportBridgeClient(SyncBridgeAdapterClientStub):
    def record_progress(self, task_id: str, progress_notes: str, is_decision: bool, idempotency_key: str):
        payload = {
            "description": progress_notes,
            "status": "DONE" if is_decision else "IN_PROGRESS",
            "metadata": {"taskmaster_task": True, "idempotency_key": idempotency_key, "task_id": task_id}
        }
        resp = self.client.post("/kg/progress", json=payload)
        resp.raise_for_status()

class SyncMemoryBridgeClient(SyncBridgeAdapterClientStub):
    def append_chronicle(self, task_id: str, progress_notes: str, is_decision: bool, idempotency_key: str):
        payload = {
            "source": "cognitive",
            "operation": "memory.append_chronicle",
            "data": {
                "task_id": task_id,
                "progress_notes": progress_notes,
                "is_decision": is_decision,
                "idempotency_key": idempotency_key
            },
            "requester": "taskmaster"
        }
        resp = self.client.post("/route/pm", json=payload)
        resp.raise_for_status()


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
        self.pm_store = InMemoryPMTaskStore()
        
        # Configure PM writes using the synchronous blocking clients
        self.pm_config = PMWriteConfig(
            leantime_client=SyncLeantimeBridgeClient(config),
            orchestrator_client=SyncOrchestratorBridgeClient(config, project_id=workspace_id),
            conport_client=SyncConportBridgeClient(config),
            memory_client=SyncMemoryBridgeClient(config)
        )
        logger.info(f"✅ TaskMaster DopeconBridge adapter initialized (workspace: {workspace_id})")
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
        # Clean up HTTPX sync clients
        self.pm_config.leantime_client.client.close()
        self.pm_config.orchestrator_client.client.close()
        self.pm_config.orchestrator_client.task_orchestrator.close()
        self.pm_config.conport_client.client.close()
        self.pm_config.memory_client.client.close()
    
    async def create_task(
        self,
        title: str,
        description: str,
        priority: int = 3,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create task via DopeconBridge and PM Task Store"""
        try:
            task_id = content_hash_task_id("taskmaster", None, title, description)
            
            pm_task = PMTask(
                task_id=task_id,
                title=title,
                description=description,
                status=PMTaskStatus.TODO,
                source="taskmaster",
                created_at_utc=datetime.now(timezone.utc),
                updated_at_utc=datetime.now(timezone.utc),
            )
            pm_task = self.pm_store.create(pm_task)
            
            # Canonical progress logging
            idempotency_key = f"create-{task_id}-{pm_task.version}"
            pm_log_progress(
                config=self.pm_config,
                task_id=task_id,
                progress_notes=f"Task created: {title}\nDescription: {description}",
                idempotency_key=idempotency_key,
                is_decision=True
            )
            
            # Publish event
            await self.client.publish_event(
                event_type="taskmaster.task.created",
                data={
                    "task_id": task_id,
                    "title": title,
                    "priority": priority,
                    "workspace_id": self.workspace_id,
                    "source": "taskmaster",
                    "idempotency_key": idempotency_key
                },
                source="taskmaster",
            )
            
            logger.info(f"Created task: {title} (priority: {priority})")
            
            return {
                "canonical_id": pm_task.task_id,
                "canonical_version": pm_task.version,
                "title": title,
                "priority": priority,
                "status": "TODO"
            }
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
        """Update task status idempotently via Canonical Store"""
        try:
            task = self.pm_store.get(task_id)
            if not task:
                logger.error(f"Task {task_id} not found in store")
                return False

            canonical_status = TASKMASTER_TO_CANONICAL.get(new_status, PMTaskStatus.TODO)
            idempotency_key = f"status-{task_id}-{canonical_status.value}-{task.version}"
            
            try:
                task = self.pm_store.transition(
                    task_id=task_id,
                    req=PMTransitionRequest(
                        idempotency_key=idempotency_key,
                        expected_version=task.version,
                        new_status=canonical_status,
                        ts_utc=datetime.now(timezone.utc),
                        source="taskmaster",
                    )
                )
            except Exception as e:
                logger.error(f"Store transition failed: {e}")
                return False
                
            # Perform canonical PM-plane write synchronously and fail closed
            pm_transition_work_item(
                config=self.pm_config,
                task_id=task_id,
                new_status=canonical_status,
                reason=f"Status update to {new_status} via taskmaster",
                idempotency_key=idempotency_key,
                expected_version=task.version - 1  # Before the transition was recorded
            )
                
            await self.client.publish_event(
                event_type="taskmaster.task.status_updated",
                data={
                    "task_id": task_id,
                    "new_status": new_status,
                    "canonical_status": canonical_status.value,
                    "canonical_version": task.version,
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                    "workspace_id": self.workspace_id,
                    "source": "taskmaster",
                    "idempotency_key": idempotency_key
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
        """Sync task to PM plane using canonical writes"""
        try:
            pm_task = self.pm_store.get(task_id)
            if not pm_task:
                logger.error(f"Task {task_id} not found in store")
                return False
                
            # Fetch actual remote canonical ID properly via route_pm
            response = await self.client.route_pm(
                operation="taskmaster.sync_task",
                data={
                    "task_id": pm_task.task_id,
                    "title": pm_task.title,
                    "description": pm_task.description,
                    "priority": 3,
                    "status": pm_task.status.value,
                },
                requester="taskmaster",
            )
            
            if response.success:
                pm_task_id = response.data.get("pm_task_id")
                
                # Update linked IDs canonically
                try:
                    idempotency_key = f"sync-{task_id}-{pm_task_id}"
                    self.pm_store.update_linked_ids(
                        task_id=task_id,
                        req=PMLinkedIDUpdateRequest(
                            idempotency_key=idempotency_key,
                            expected_version=pm_task.version,
                            linked_ids={"leantime": pm_task_id},
                            ts_utc=datetime.now(timezone.utc),
                            source="taskmaster",
                        )
                    )
                except Exception as e:
                    logger.error(f"Failed to update linked IDs: {e}")
                    return False
                
                # Use pm_update_work_item to record the sync passively
                try:
                    pm_update_work_item(
                        config=self.pm_config,
                        task_id=task_id,
                        updates={"linked_ids": {"leantime": pm_task_id}},
                        idempotency_key=idempotency_key
                    )
                except Exception as e:
                    logger.error(f"Failed canonical sync to PM plane: {e}")
                    return False
                
                logger.info(f"Synced task {task_id} to PM plane (canonical_id: {pm_task_id})")
                return True
            else:
                logger.error(f"Failed to route taskmaster.sync_task: {response.error}")
                return False
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
            task = self.pm_store.get(task_id)
            if not task:
                logger.error(f"Task {task_id} not found in store")
                return False
                
            idempotency_key = f"assign-{task_id}-{assignee}-{datetime.now(timezone.utc).timestamp()}"
            
            pm_update_work_item(
                config=self.pm_config,
                task_id=task_id,
                updates={"assignee": assignee},
                idempotency_key=idempotency_key
            )
            
            await self.client.publish_event(
                event_type="taskmaster.task.assigned",
                data={
                    "task_id": task_id,
                    "assignee": assignee,
                    "assigned_at": datetime.now(timezone.utc).isoformat(),
                    "workspace_id": self.workspace_id,
                    "source": "taskmaster",
                    "idempotency_key": idempotency_key
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
            task = self.pm_store.get(task_id)
            if not task:
                logger.error(f"Task {task_id} not found in store")
                return False
                
            idempotency_key = f"comment-{task_id}-{author}-{datetime.now(timezone.utc).timestamp()}"
            
            pm_log_progress(
                config=self.pm_config,
                task_id=task_id,
                progress_notes=f"[{author}]: {comment}",
                idempotency_key=idempotency_key,
                is_decision=False
            )
            
            await self.client.save_custom_data(
                workspace_id=self.workspace_id,
                category="task_comments",
                key=f"{task_id}_{datetime.now(timezone.utc).isoformat()}",
                value={
                    "task_id": task_id,
                    "comment": comment,
                    "author": author,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                },
            )
            
            await self.client.publish_event(
                event_type="taskmaster.task.commented",
                data={
                    "task_id": task_id,
                    "author": author,
                    "workspace_id": self.workspace_id,
                    "source": "taskmaster",
                    "idempotency_key": idempotency_key
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
            success = await self.update_task_status(task_id, "DONE")
            if not success:
                return False
            
            if completion_notes:
                idempotency_key = f"complete-notes-{task_id}-{datetime.now(timezone.utc).timestamp()}"
                pm_log_progress(
                    config=self.pm_config,
                    task_id=task_id,
                    progress_notes=f"Completion notes: {completion_notes}",
                    idempotency_key=idempotency_key,
                    is_decision=True
                )
            
            # Publish event
            await self.client.publish_event(
                event_type="taskmaster.task.completed",
                data={
                    "task_id": task_id,
                    "workspace_id": self.workspace_id,
                    "source": "taskmaster"
                },
                source="taskmaster",
            )
            
            logger.info(f"Completed task: {task_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to complete task: {e}")
            return False
