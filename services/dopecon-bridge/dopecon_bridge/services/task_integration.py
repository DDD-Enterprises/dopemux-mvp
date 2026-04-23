import asyncio
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from dopemux.pm.adapters.orchestrator import SyncTaskOrchestratorAdapter
from dopemux.pm.models import PMTaskStatus
from dopemux.pm.writes import PMWriteConfig, pm_transition_work_item

from ..clients import mcp_client
from ..config import settings
from ..models import Task, TaskPriority, TaskStatus


logger = logging.getLogger(__name__)

TASK_STATUS_TO_PM_STATUS = {
    TaskStatus.PLANNED: PMTaskStatus.TODO,
    TaskStatus.IN_PROGRESS: PMTaskStatus.IN_PROGRESS,
    TaskStatus.BLOCKED: PMTaskStatus.BLOCKED,
    TaskStatus.COMPLETED: PMTaskStatus.DONE,
}


def _utc_now_z() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class TaskIntegrationService:
    """Core task integration adapter to canonical backends.
    
    This service serves as a bridge between the frontend/API and the 
    authoritative PM Plane. It has been refactored to remove local 
    state (shadow authority) and instead delegate all operations to 
    the PM Plane pillars (Task Orchestrator, ConPort, and Leantime).
    """

    def __init__(self):
        """Initialize the adapter with an MCP client manager."""
        self.mcp_manager = mcp_client

    async def parse_prd_to_tasks(self, prd_content: str, project_id: str) -> List[Task]:
        """
        Parse a PRD document into structured tasks using Task-Master-AI.
        
        This method utilizes the `task-master-ai` MCP tool to perform semantic 
        decomposition of requirement text into structured task objects, 
        associating them with the specified project.

        Args:
            prd_content: The raw text of the PRD.
            project_id: The project identifier.

        Returns:
            A list of initialized Task objects.
        """
        logger.info(f"🔍 Parsing PRD for project {project_id} via adapter (instance: {settings.instance_name})")

        try:
            # Step 1: Use Task-Master-AI to parse PRD
            prd_result = await self.mcp_manager.call_tool(
                "task-master-ai",
                "parse_prd",
                {"content": prd_content, "project_id": project_id}
            )

            tasks = []
            for task_data in prd_result.get("tasks", []):
                task = Task(
                    id=str(uuid.uuid4()),
                    title=task_data.get("title", ""),
                    description=task_data.get("description", ""),
                    status=TaskStatus.PLANNED,
                    priority=TaskPriority(task_data.get("priority", "medium")),
                    project_id=project_id,
                    instance_id=settings.instance_name,
                    tags=task_data.get("tags", [])
                )
                tasks.append(task)

            # Step 2: Directly route tasks to Leantime for tracking
            await self._sync_tasks_to_leantime(tasks)

            logger.info(f"✅ Successfully processed {len(tasks)} tasks from PRD")
            return tasks

        except Exception as e:
            logger.error(f"❌ PRD parsing failed: {e}")
            raise

    async def _sync_tasks_to_leantime(self, tasks: List[Task]):
        """Sync tasks to Leantime for project management tracking.
        
        Args:
            tasks: List of Task objects to synchronize.
        """
        if not tasks:
            return

        try:
            coros = [
                self.mcp_manager.call_tool(
                    "leantime-bridge",
                    "create_ticket",
                    {
                        "projectId": int(task.project_id) if task.project_id.isdigit() else 1,
                        "headline": task.title,
                        "description": task.description,
                        "priority": "3",
                        "type": "task"
                    }
                )
                for task in tasks
            ]

            results = await asyncio.gather(*coros, return_exceptions=True)

            for task, leantime_result in zip(tasks, results):
                if isinstance(leantime_result, Exception):
                    logger.error(f"❌ Failed to sync task {task.id} to Leantime: {leantime_result}")
                    continue

                if leantime_result and "id" in leantime_result:
                    task.tags.append(f"leantime_id:{leantime_result['id']}")

        except Exception as e:
            logger.warning(f"⚠️ Leantime sync failed: {e}")

    async def get_next_actionable_tasks(self, project_id: str, limit: int = 5) -> List[Task]:
        """
        Retrieve next actionable tasks by delegating to the leantime-bridge authority.
        
        Args:
            project_id: The project identifier.
            limit: Maximum number of tasks to return.

        Returns:
            A list of Task objects from the mirror authority.
        """
        try:
            # Query canonical backend for actionable tasks
            result = await self.mcp_manager.call_tool(
                "leantime-bridge",
                "list_tickets",
                {"projectId": int(project_id) if project_id.isdigit() else 1, "status": "planned"}
            )

            task_records = result if isinstance(result, list) else result.get("tickets", [])
            actionable_tasks = [
                Task(
                    id=str(record.get("id")),
                    title=record.get("headline", ""),
                    description=record.get("description", ""),
                    status=TaskStatus.PLANNED,
                    priority=TaskPriority.MEDIUM,
                    project_id=project_id,
                )
                for record in task_records
            ][:limit]

            logger.info(f"📋 Found {len(actionable_tasks)} actionable tasks for project {project_id} via adapter")
            return actionable_tasks

        except Exception as e:
            logger.error(f"❌ Failed to get actionable tasks: {e}")
            return []

    async def get_priority_queue(self, project_id: str) -> Dict[str, Any]:
        """Retrieve the canonical workflow queue from task-orchestrator via HTTP."""
        fail_closed = {
            "project_id": project_id,
            "linked_ids": {},
            "legality_result": "unavailable",
            "blockers": [],
            "next_action": None,
            "queue_items": [],
        }

        try:
            await self.mcp_manager.initialize()
            url = f"{settings.task_orchestrator_url}/api/projects/{project_id}/workflow/queue"
            async with self.mcp_manager.session.get(url) as response:
                if response.status != 200:
                    logger.warning(
                        "⚠️ Task Orchestrator queue read returned %s for %s",
                        response.status,
                        project_id,
                    )
                    return fail_closed

                payload = await response.json()
                payload.setdefault("project_id", project_id)
                payload.setdefault("linked_ids", {})
                payload.setdefault("legality_result", "unavailable")
                payload.setdefault("blockers", [])
                payload.setdefault("next_action", None)
                payload.setdefault("queue_items", [])
                return payload

        except Exception as e:
            logger.error(f"❌ Failed to get priority queue: {e}")
            return fail_closed

    async def update_task_status(
        self,
        task_id: str,
        new_status: TaskStatus,
        assigned_to: str = None,
        project_id: str = "default",
    ) -> Dict[str, Any]:
        """
        Update a task's status across all authorities.
        
        This method performs a dual-update:
        1. Executes a workflow transition via the PM Plane's 
           authoritative `pm_transition_work_item` tool.
        2. Updates the task in Leantime (the mirror authority) via 
           the `leantime-bridge`.

        Args:
            task_id: The ID of the task to update.
            new_status: The target status.
            assigned_to: Optional assignee update.

        Returns:
            A dictionary containing the success status and updated task data.
        """
        logger.info(f"🔄 Routing task {task_id} status update to {new_status.value} via adapter")

        if assigned_to is not None:
            raise ValueError(
                "assigned_to is not supported on the workflow transition path. "
                "Phase 1 requires metadata changes to be dispatched separately to Leantime."
            )

        try:
            target_status = TASK_STATUS_TO_PM_STATUS.get(new_status)
            if target_status is None:
                raise ValueError(f"Unsupported task status for PM workflow transition: {new_status.value}")

            orchestrator_client = SyncTaskOrchestratorAdapter(base_url=settings.task_orchestrator_url)
            try:
                pm_config = PMWriteConfig(
                    leantime_client=None,
                    orchestrator_client=orchestrator_client,
                    conport_client=None,
                    memory_client=None,
                    project_id=project_id,
                )
                pm_transition_work_item(
                    config=pm_config,
                    task_id=task_id,
                    new_status=target_status,
                    reason="bridge task status update",
                    idempotency_key=f"bridge-status:{project_id}:{task_id}:{new_status.value}",
                    expected_version=1,
                )
            finally:
                orchestrator_client.close()

            response = {
                "success": True,
                "task_id": task_id,
                "new_status": new_status.value,
                "instance": settings.instance_name,
                "timestamp": datetime.utcnow().isoformat(),
            }

            if new_status == TaskStatus.COMPLETED:
                logger.info(f"✅ Task {task_id} completed!")

            return response

        except Exception as e:
            logger.error(f"❌ Task status update failed: {e}")
            raise

    async def get_priority_queue(self, project_id: str) -> Dict[str, Any]:
        """Return the canonical project workflow queue via the PM-plane read layer."""
        result = await pm_get_priority_queue(project_id)
        return result.model_dump()


task_service = TaskIntegrationService()
