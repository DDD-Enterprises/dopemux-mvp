"""
DopeconBridge Services - Task Integration Service

Core business logic for task management, PRD parsing, and cross-system sync.
Extracted from main.py lines 662-1318.
"""

import asyncio
import json
import logging
import uuid
from dataclasses import asdict
from datetime import datetime
from typing import Any, Dict, List

from sqlalchemy import bindparam

from ..clients import mcp_client
from ..config import settings
from ..models import Task, TaskPriority, TaskStatus


logger = logging.getLogger(__name__)


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
                        "projectId": int(task.project_id) if task.project_id else 1,
                        "headline": task.title,
                        "description": task.description,
                        "priority": self._map_priority_to_leantime(task.priority),
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

    def _map_priority_to_leantime(self, priority: TaskPriority) -> str:
        """Map unified priority to Leantime priority format."""
        mapping = {
            TaskPriority.LOW: "1",
            TaskPriority.MEDIUM: "2",
            TaskPriority.HIGH: "3",
            TaskPriority.CRITICAL: "4"
        }
        return mapping.get(priority, "2")

    async def get_next_actionable_tasks(self, project_id: str, limit: int = 5) -> List[Task]:
        """
        Route request to canonical PM backend to get next actionable tasks.
        """
        try:
            # Query canonical backend for actionable tasks
            result = await self.mcp_manager.call_tool(
                "leantime-bridge",
                "search_tickets",
                {"project_id": project_id, "status": "planned", "limit": limit}
            )

            task_records = result.get("tickets", [])
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

    async def update_task_status(
        self,
        task_id: str,
        new_status: TaskStatus,
        assigned_to: str = None
    ) -> Dict[str, Any]:
        """
        Route task status update to canonical backend.
        """
        logger.info(f"🔄 Routing task {task_id} status update to {new_status.value} via adapter")

        try:
            # Map unified status to canonical Leantime status logic or similar
            # Assuming task_id is a Leantime ID here.
            await self.mcp_manager.call_tool(
                "leantime-bridge",
                "update_ticket",
                {"ticket_id": task_id, "status": new_status.value, "assigned_to": assigned_to}
            )

            # We need the project ID to get next actionable tasks. 
            # We can fetch the ticket details from leantime-bridge to get it.
            try:
                ticket = await self.mcp_manager.call_tool(
                    "leantime-bridge",
                    "get_ticket",
                    {"ticket_id": task_id}
                )
                project_id = str(ticket.get("projectId", "1"))
            except Exception as get_err:
                logger.warning(f"⚠️ Failed to get ticket details for {task_id}, defaulting project to 1: {get_err}")
                project_id = "1"

            # Get next suggested actions for ADHD accommodation
            # using canonical backend
            next_actions = await self.get_next_actionable_tasks(project_id, 3)

            response = {
                "success": True,
                "task_id": task_id,
                "new_status": new_status.value,
                "instance": settings.instance_name,
                "timestamp": datetime.utcnow().isoformat(),
                "suggested_next_actions": [
                    {"id": t.id, "title": t.title, "priority": t.priority.value}
                    for t in next_actions
                ]
            }

            if new_status == TaskStatus.COMPLETED:
                logger.info(f"✅ Task {task_id} completed!")

            return response

        except Exception as e:
            logger.error(f"❌ Task status update failed: {e}")
            raise


# Global service instance
task_service = TaskIntegrationService()
