import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from dopemux.pm.reads import pm_get_priority_queue

from ..clients import mcp_client
from ..config import settings
from ..models import Task, TaskPriority, TaskStatus


logger = logging.getLogger(__name__)


def _utc_now_z() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class TaskIntegrationService:
    """Core task integration adapter to canonical backends."""

    def __init__(self):
        self.mcp_manager = mcp_client

    async def parse_prd_to_tasks(self, prd_content: str, project_id: str) -> List[Task]:
        """
        Parse PRD using Task-Master-AI and route directly to canonical PM backend.
        No local DB storage.
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
        """Sync tasks to Leantime for project management tracking."""
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
        Route request to canonical workflow authority to get next actionable tasks.
        """
        try:
            result = await pm_get_priority_queue(project_id)
            task_records = result.queue_items[:limit]
            actionable_tasks = [
                Task(
                    id=str(record.get("id")),
                    title=record.get("title") or record.get("headline", ""),
                    description=record.get("description", ""),
                    status=TaskStatus.PLANNED,
                    priority=TaskPriority.MEDIUM,
                    project_id=project_id,
                )
                for record in task_records
            ]

            logger.info(f"📋 Found {len(actionable_tasks)} actionable tasks for project {project_id} via adapter")
            return actionable_tasks

        except Exception as e:
            logger.error(f"❌ Failed to get actionable tasks: {e}")
            return []

    async def update_task_status(
        self,
        task_id: str,
        new_status: TaskStatus,
        assigned_to: str = None,
        project_id: str = "default",
    ) -> Dict[str, Any]:
        """
        Route task status update to canonical backend.
        """
        logger.info(f"🔄 Routing task {task_id} status update to {new_status.value} via adapter")

        try:
            await self.mcp_manager.initialize()
            assigned_part = assigned_to or "unassigned"
            idempotency_key = f"bridge-trans-{project_id}-{task_id}-{new_status.value}-{assigned_part}"
            transition_url = f"{settings.task_orchestrator_url}/api/projects/{project_id}/workflow/transition"
            transition_payload = {
                "workflow_id": task_id,
                "transition": new_status.value,
                "actor": settings.instance_name,
                "idempotency_key": idempotency_key,
            }

            async with self.mcp_manager.session.post(transition_url, json=transition_payload) as response:
                if response.status >= 400:
                    detail = await response.text()
                    raise RuntimeError(
                        f"Task Orchestrator rejected workflow transition for {task_id}: "
                        f"{response.status} {detail}"
                    )

                transition_result = await response.json()
                legality_result = transition_result.get("legality_result", "unavailable")
                if legality_result != "allowed":
                    raise RuntimeError(
                        f"Task Orchestrator returned non-authoritative transition result "
                        f"for {task_id}: {legality_result}"
                    )

            # Step 2: Mirror to Leantime (PM Record Authority)
            await self.mcp_manager.call_tool(
                "leantime-bridge",
                "update_ticket",
                {
                    "ticket_id": task_id,
                    "status": new_status.value,
                    "assigned_to": assigned_to,
                    "idempotency_key": idempotency_key,
                }
            )

            response = {
                "success": True,
                "task_id": task_id,
                "new_status": new_status.value,
                "legality_result": "allowed",
                "instance": settings.instance_name,
                "project_id": project_id,
                "timestamp": _utc_now_z(),
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
