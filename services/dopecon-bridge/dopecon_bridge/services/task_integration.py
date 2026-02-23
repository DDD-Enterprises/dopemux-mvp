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
from ..core import cache_manager, db_manager
from ..models import Task, TaskPriority, TaskRecord, TaskStatus


logger = logging.getLogger(__name__)


class TaskIntegrationService:
    """Core task integration with multi-instance shared state."""

    def __init__(self):
        self.db_manager = db_manager
        self.cache_manager = cache_manager
        self.mcp_manager = mcp_client

    async def parse_prd_to_tasks(self, prd_content: str, project_id: str) -> List[Task]:
        """
        Parse PRD using Task-Master-AI and create shared task structure.
        ADHD-friendly: Clear progress indicators and manageable chunks.
        """
        logger.info(f"🔍 Parsing PRD for project {project_id} (instance: {settings.instance_name})")

        try:
            # Step 1: Use Task-Master-AI to parse PRD
            prd_result = await self.mcp_manager.call_tool(
                "task-master-ai",
                "parse_prd",
                {"content": prd_content, "project_id": project_id}
            )

            # Step 2: Convert to unified task format and store in shared database
            tasks = []
            async with await self.db_manager.get_session() as session:
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

                    # Store in shared database
                    task_record = TaskRecord(**asdict(task))
                    session.add(task_record)
                    tasks.append(task)

                await session.commit()

            # Step 3: Use Task-Orchestrator to analyze dependencies
            await self._analyze_task_dependencies(tasks)

            # Step 4: Create tasks in Leantime for tracking
            await self._sync_tasks_to_leantime(tasks)

            # Step 5: Cache results for fast access
            cache_client = await self.cache_manager.get_client()
            await cache_client.setex(
                f"project:{project_id}:tasks",
                3600,  # 1 hour cache
                json.dumps([asdict(task) for task in tasks], default=str)
            )

            logger.info(f"✅ Successfully processed {len(tasks)} tasks from PRD")
            return tasks

        except Exception as e:
            logger.error(f"❌ PRD parsing failed: {e}")
            raise

    async def _analyze_task_dependencies(self, tasks: List[Task]):
        """Use Task-Orchestrator to analyze and set dependencies."""
        try:
            task_descriptions = [
                {"id": t.id, "title": t.title, "description": t.description}
                for t in tasks
            ]

            dependency_result = await self.mcp_manager.call_tool(
                "task-orchestrator",
                "analyze_dependencies",
                {"tasks": task_descriptions}
            )

            dependencies = dependency_result.get("dependencies", [])
            if not dependencies:
                return

            # Map for efficient lookup
            task_map = {t.id: t for t in tasks}
            update_params = []
            now = datetime.utcnow()

            for dep in dependencies:
                task_id = dep.get("task_id")
                depends_on = dep.get("depends_on", [])

                # Collect for bulk update
                update_params.append({
                    "b_id": task_id,
                    "b_dependencies": depends_on,
                    "b_updated_at": now
                })

                # Update in-memory objects
                if task_id in task_map:
                    task_map[task_id].dependencies = depends_on

            # Perform bulk update in shared database
            async with await self.db_manager.get_session() as session:
                await session.execute(
                    TaskRecord.__table__.update()
                    .where(TaskRecord.id == bindparam("b_id"))
                    .values(
                        dependencies=bindparam("b_dependencies"),
                        updated_at=bindparam("b_updated_at")
                    ),
                    update_params
                )
                await session.commit()

        except Exception as e:
            logger.warning(f"⚠️ Dependency analysis failed: {e}")

    async def _sync_tasks_to_leantime(self, tasks: List[Task]):
        """Sync tasks to Leantime for project management tracking."""
        if not tasks:
            return

        try:
            # Step 1: Prepare parallel tool calls
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

            # Step 2: Execute in parallel to avoid N+1 sequential waits
            results = await asyncio.gather(*coros, return_exceptions=True)

            update_params = []
            now = datetime.utcnow()
            for task, leantime_result in zip(tasks, results):
                if isinstance(leantime_result, Exception):
                    logger.error(f"❌ Failed to sync task {task.id} to Leantime: {leantime_result}")
                    continue

                if leantime_result and "id" in leantime_result:
                    task.tags.append(f"leantime_id:{leantime_result['id']}")
                    update_params.append({
                        "b_id": task.id,
                        "b_tags": task.tags,
                        "b_updated_at": now
                    })

            # Step 3: Perform bulk update for all successful syncs
            if update_params:
                async with await self.db_manager.get_session() as session:
                    await session.execute(
                        TaskRecord.__table__.update()
                        .where(TaskRecord.id == bindparam("b_id"))
                        .values(
                            tags=bindparam("b_tags"),
                            updated_at=bindparam("b_updated_at")
                        ),
                        update_params
                    )
                    await session.commit()

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
        Get next actionable tasks for ADHD-friendly workflow.
        Checks shared database for cross-instance task coordination.
        """
        try:
            cache_client = await self.cache_manager.get_client()
            cache_key = f"project:{project_id}:actionable_tasks"
            cached_result = await cache_client.get(cache_key)

            if cached_result:
                logger.debug("📋 Returning cached actionable tasks")
                task_dicts = json.loads(cached_result)
                return [
                    Task(
                        id=t["id"],
                        title=t["title"],
                        description=t["description"],
                        status=TaskStatus(t["status"]),
                        priority=TaskPriority(t["priority"]),
                        instance_id=t.get("instance_id", "default"),
                        project_id=t.get("project_id"),
                        dependencies=t.get("dependencies", []),
                        tags=t.get("tags", [])
                    )
                    for t in task_dicts
                ]

            # Query database for actionable tasks (no blocking dependencies)
            async with await self.db_manager.get_session() as session:
                from sqlalchemy import text
                
                result = await session.execute(
                    text("""
                    SELECT t.* FROM tasks t
                    WHERE t.project_id = :project_id
                    AND t.status = 'planned'
                    AND (
                        t.dependencies IS NULL
                        OR t.dependencies = '[]'::json
                    )
                    ORDER BY
                        CASE t.priority
                            WHEN 'critical' THEN 1
                            WHEN 'high' THEN 2
                            WHEN 'medium' THEN 3
                            WHEN 'low' THEN 4
                        END,
                        t.created_at
                    LIMIT :limit
                    """),
                    {"project_id": project_id, "limit": limit}
                )

                task_records = result.fetchall()
                actionable_tasks = [
                    Task(
                        id=record.id,
                        title=record.title,
                        description=record.description or "",
                        status=TaskStatus(record.status),
                        priority=TaskPriority(record.priority),
                        instance_id=record.instance_id,
                        project_id=record.project_id,
                        dependencies=record.dependencies or [],
                        tags=record.tags or [],
                        assigned_to=record.assigned_to,
                        estimated_hours=record.estimated_hours
                    )
                    for record in task_records
                ]

                # Cache result for 5 minutes
                await cache_client.setex(
                    cache_key,
                    300,
                    json.dumps([asdict(task) for task in actionable_tasks], default=str)
                )

                logger.info(f"📋 Found {len(actionable_tasks)} actionable tasks for project {project_id}")
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
        Update task status across all systems with dependency resolution.
        ADHD-friendly: Clear progress feedback and automatic next-action suggestions.
        """
        logger.info(f"🔄 Updating task {task_id} to status {new_status.value}")

        try:
            async with await self.db_manager.get_session() as session:
                result = await session.execute(
                    TaskRecord.__table__.select().where(TaskRecord.id == task_id)
                )
                task_record = result.fetchone()

                if not task_record:
                    raise ValueError(f"Task {task_id} not found")

                old_status = task_record.status

                update_data = {
                    "status": new_status.value,
                    "updated_at": datetime.utcnow()
                }
                if assigned_to:
                    update_data["assigned_to"] = assigned_to

                await session.execute(
                    TaskRecord.__table__.update()
                    .where(TaskRecord.id == task_id)
                    .values(**update_data)
                )
                await session.commit()

                # Invalidate cache
                cache_client = await self.cache_manager.get_client()
                await cache_client.delete(f"project:{task_record.project_id}:actionable_tasks")

                # Get next suggested actions for ADHD accommodation
                next_actions = await self.get_next_actionable_tasks(task_record.project_id, 3)

                response = {
                    "success": True,
                    "task_id": task_id,
                    "old_status": old_status,
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
