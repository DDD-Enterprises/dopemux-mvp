"""
Leantime-TaskMaster Synchronization Manager for Dopemux

This module manages bidirectional synchronization between Leantime and Task-Master AI,
handling data consistency, conflict resolution, and ADHD-optimized workflow coordination.
"""

import asyncio
import hashlib
import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.config import Config
from core.exceptions import DopemuxIntegrationError, SyncError
from core.monitoring import MetricsCollector
from utils.adhd_optimizations import ADHDTaskOptimizer

from .leantime_bridge import (
    LeantimeMCPClient,
    LeantimeProject,
    LeantimeTask,
    TaskPriority,
    TaskStatus,
)
from .taskmaster_bridge import TaskMasterMCPClient, TaskMasterTask

logger = logging.getLogger(__name__)


class SyncDirection(Enum):
    """Synchronization direction options."""

    LEANTIME_TO_TASKMASTER = "leantime_to_taskmaster"
    TASKMASTER_TO_LEANTIME = "taskmaster_to_leantime"
    BIDIRECTIONAL = "bidirectional"


class ConflictResolution(Enum):
    """Conflict resolution strategies."""

    LEANTIME_WINS = "leantime_wins"
    TASKMASTER_WINS = "taskmaster_wins"
    MANUAL_REVIEW = "manual_review"
    MERGE_INTELLIGENT = "merge_intelligent"
    LATEST_TIMESTAMP = "latest_timestamp"


@dataclass
class SyncResult:
    """Result of a synchronization operation."""

    success: bool
    synced_tasks: int
    created_tasks: int
    updated_tasks: int
    conflicts: int
    errors: List[str]
    sync_duration: float
    timestamp: datetime

    def to_dict(self) -> Dict[str, Any]:
        return {**asdict(self), "timestamp": self.timestamp.isoformat()}


@dataclass
class TaskMapping:
    """Mapping between Leantime and TaskMaster tasks."""

    leantime_id: Optional[int]
    taskmaster_id: Optional[str]
    sync_hash: str
    last_sync: datetime
    conflict_count: int = 0
    sync_direction: SyncDirection = SyncDirection.BIDIRECTIONAL

    def generate_hash(
        self,
        leantime_task: Optional[LeantimeTask] = None,
        taskmaster_task: Optional[TaskMasterTask] = None,
    ) -> str:
        """Generate hash for conflict detection."""
        data = {}
        if leantime_task:
            data["leantime"] = {
                "headline": leantime_task.headline,
                "description": leantime_task.description,
                "status": leantime_task.status.value,
                "priority": leantime_task.priority.value,
                "updated_at": (
                    leantime_task.updated_at.isoformat()
                    if leantime_task.updated_at
                    else None
                ),
            }
        if taskmaster_task:
            data["taskmaster"] = {
                "title": taskmaster_task.title,
                "description": taskmaster_task.description,
                "status": taskmaster_task.status,
                "priority": taskmaster_task.priority,
                "updated_at": (
                    taskmaster_task.updated_at.isoformat()
                    if taskmaster_task.updated_at
                    else None
                ),
            }

        return hashlib.md5(json.dumps(data, sort_keys=True).encode()).hexdigest()


class LeantimeTaskMasterSyncManager:
    """
    Manages synchronization between Leantime and Task-Master AI.

    Provides bidirectional sync, conflict resolution, and ADHD-optimized
    workflow coordination between the two systems.
    """

    def __init__(self, config: Config):
        self.config = config
        self.metrics = MetricsCollector()
        self.adhd_optimizer = ADHDTaskOptimizer()

        # Sync configuration
        self.sync_interval = config.get("sync.interval", 300)  # 5 minutes default
        self.conflict_resolution = ConflictResolution(
            config.get("sync.conflict_resolution", "merge_intelligent")
        )
        self.max_retries = config.get("sync.max_retries", 3)
        self.batch_size = config.get("sync.batch_size", 50)

        # Task mappings and state
        self.task_mappings: Dict[str, TaskMapping] = {}
        self.sync_running = False
        self.last_sync: Optional[datetime] = None

        # Clients (will be injected)
        self.leantime_client: Optional[LeantimeMCPClient] = None
        self.taskmaster_client: Optional[TaskMasterMCPClient] = None

    async def initialize(
        self, leantime_client: LeantimeMCPClient, taskmaster_client: TaskMasterMCPClient
    ) -> bool:
        """
        Initialize sync manager with MCP clients.

        Args:
            leantime_client: Connected Leantime MCP client
            taskmaster_client: Connected TaskMaster MCP client

        Returns:
            True if initialization successful
        """
        self.leantime_client = leantime_client
        self.taskmaster_client = taskmaster_client

        try:
            # Load existing task mappings
            await self._load_task_mappings()

            # Verify client connections
            leantime_health = await self.leantime_client.health_check()
            taskmaster_health = await self.taskmaster_client.health_check()

            if not (
                leantime_health.get("connected") and taskmaster_health.get("connected")
            ):
                raise DopemuxIntegrationError("One or more clients not connected")

            logger.info("Sync manager initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize sync manager: {e}")
            return False

    async def start_sync_loop(self):
        """Start the continuous synchronization loop."""
        if self.sync_running:
            logger.warning("Sync loop already running")
            return

        self.sync_running = True
        logger.info(f"Starting sync loop with {self.sync_interval}s interval")

        try:
            while self.sync_running:
                try:
                    await self.sync_all()
                except Exception as e:
                    logger.error(f"Error in sync loop: {e}")
                    self.metrics.record_sync_error("sync_loop", str(e))

                await asyncio.sleep(self.sync_interval)

        finally:
            self.sync_running = False
            logger.info("Sync loop stopped")

    async def stop_sync_loop(self):
        """Stop the synchronization loop."""
        self.sync_running = False
        logger.info("Stopping sync loop...")

    async def sync_all(self) -> SyncResult:
        """
        Perform full bidirectional synchronization.

        Returns:
            Synchronization result summary
        """
        start_time = datetime.now()
        sync_result = SyncResult(
            success=True,
            synced_tasks=0,
            created_tasks=0,
            updated_tasks=0,
            conflicts=0,
            errors=[],
            sync_duration=0.0,
            timestamp=start_time,
        )

        try:
            logger.info("Starting full synchronization")

            # Get all tasks from both systems
            leantime_tasks = await self.leantime_client.get_tasks()
            taskmaster_tasks = await self.taskmaster_client.get_tasks()

            logger.info(
                f"Found {len(leantime_tasks)} Leantime tasks, {len(taskmaster_tasks)} TaskMaster tasks"
            )

            # Sync from Leantime to TaskMaster
            lt_to_tm_result = await self._sync_leantime_to_taskmaster(
                leantime_tasks, taskmaster_tasks
            )
            sync_result.created_tasks += lt_to_tm_result.created_tasks
            sync_result.updated_tasks += lt_to_tm_result.updated_tasks
            sync_result.conflicts += lt_to_tm_result.conflicts
            sync_result.errors.extend(lt_to_tm_result.errors)

            # Sync from TaskMaster to Leantime
            tm_to_lt_result = await self._sync_taskmaster_to_leantime(
                taskmaster_tasks, leantime_tasks
            )
            sync_result.created_tasks += tm_to_lt_result.created_tasks
            sync_result.updated_tasks += tm_to_lt_result.updated_tasks
            sync_result.conflicts += tm_to_lt_result.conflicts
            sync_result.errors.extend(tm_to_lt_result.errors)

            sync_result.synced_tasks = (
                sync_result.created_tasks + sync_result.updated_tasks
            )
            self.last_sync = start_time

            # Save updated mappings
            await self._save_task_mappings()

            logger.info(
                f"Sync completed: {sync_result.synced_tasks} tasks synced, {sync_result.conflicts} conflicts"
            )

        except Exception as e:
            logger.error(f"Sync failed: {e}")
            sync_result.success = False
            sync_result.errors.append(str(e))
            self.metrics.record_sync_error("full_sync", str(e))

        finally:
            sync_result.sync_duration = (datetime.now() - start_time).total_seconds()

        # Record metrics
        self.metrics.record_sync_operation(sync_result)

        return sync_result

    async def _sync_leantime_to_taskmaster(
        self, leantime_tasks: List[LeantimeTask], taskmaster_tasks: List[TaskMasterTask]
    ) -> SyncResult:
        """Sync tasks from Leantime to TaskMaster."""
        result = SyncResult(
            success=True,
            synced_tasks=0,
            created_tasks=0,
            updated_tasks=0,
            conflicts=0,
            errors=[],
            sync_duration=0.0,
            timestamp=datetime.now(),
        )

        # Create mapping of TaskMaster tasks by ID for quick lookup
        tm_tasks_by_id = {task.id: task for task in taskmaster_tasks}

        for lt_task in leantime_tasks:
            try:
                # Find corresponding TaskMaster task
                mapping_key = f"lt_{lt_task.id}"
                mapping = self.task_mappings.get(mapping_key)

                if mapping and mapping.taskmaster_id:
                    # Update existing TaskMaster task
                    tm_task = tm_tasks_by_id.get(mapping.taskmaster_id)
                    if tm_task:
                        if await self._should_sync_to_taskmaster(
                            lt_task, tm_task, mapping
                        ):
                            await self._update_taskmaster_task(
                                lt_task, tm_task, mapping
                            )
                            result.updated_tasks += 1
                    else:
                        # TaskMaster task was deleted, create new one
                        await self._create_taskmaster_task(lt_task, mapping_key)
                        result.created_tasks += 1
                else:
                    # Create new TaskMaster task
                    await self._create_taskmaster_task(lt_task, mapping_key)
                    result.created_tasks += 1

            except Exception as e:
                logger.error(f"Error syncing Leantime task {lt_task.id}: {e}")
                result.errors.append(f"Task {lt_task.id}: {e}")

        return result

    async def _sync_taskmaster_to_leantime(
        self, taskmaster_tasks: List[TaskMasterTask], leantime_tasks: List[LeantimeTask]
    ) -> SyncResult:
        """Sync tasks from TaskMaster to Leantime."""
        result = SyncResult(
            success=True,
            synced_tasks=0,
            created_tasks=0,
            updated_tasks=0,
            conflicts=0,
            errors=[],
            sync_duration=0.0,
            timestamp=datetime.now(),
        )

        # Create mapping of Leantime tasks by ID for quick lookup
        lt_tasks_by_id = {task.id: task for task in leantime_tasks if task.id}

        for tm_task in taskmaster_tasks:
            try:
                # Find corresponding Leantime task
                mapping_key = f"tm_{tm_task.id}"
                mapping = self.task_mappings.get(mapping_key)

                if mapping and mapping.leantime_id:
                    # Update existing Leantime task
                    lt_task = lt_tasks_by_id.get(mapping.leantime_id)
                    if lt_task:
                        if await self._should_sync_to_leantime(
                            tm_task, lt_task, mapping
                        ):
                            await self._update_leantime_task(tm_task, lt_task, mapping)
                            result.updated_tasks += 1
                    else:
                        # Leantime task was deleted, create new one
                        await self._create_leantime_task(tm_task, mapping_key)
                        result.created_tasks += 1
                else:
                    # Create new Leantime task
                    await self._create_leantime_task(tm_task, mapping_key)
                    result.created_tasks += 1

            except Exception as e:
                logger.error(f"Error syncing TaskMaster task {tm_task.id}: {e}")
                result.errors.append(f"Task {tm_task.id}: {e}")

        return result

    async def _should_sync_to_taskmaster(
        self, lt_task: LeantimeTask, tm_task: TaskMasterTask, mapping: TaskMapping
    ) -> bool:
        """Determine if Leantime task should be synced to TaskMaster."""
        # Generate current hash for conflict detection
        current_hash = mapping.generate_hash(
            leantime_task=lt_task, taskmaster_task=tm_task
        )

        if current_hash == mapping.sync_hash:
            return False  # No changes detected

        # Check for conflicts
        if self._has_conflict(lt_task, tm_task, mapping):
            await self._handle_conflict(lt_task, tm_task, mapping)
            return False

        return True

    async def _should_sync_to_leantime(
        self, tm_task: TaskMasterTask, lt_task: LeantimeTask, mapping: TaskMapping
    ) -> bool:
        """Determine if TaskMaster task should be synced to Leantime."""
        # Generate current hash for conflict detection
        current_hash = mapping.generate_hash(
            leantime_task=lt_task, taskmaster_task=tm_task
        )

        if current_hash == mapping.sync_hash:
            return False  # No changes detected

        # Check for conflicts
        if self._has_conflict(lt_task, tm_task, mapping):
            await self._handle_conflict(lt_task, tm_task, mapping)
            return False

        return True

    def _has_conflict(
        self, lt_task: LeantimeTask, tm_task: TaskMasterTask, mapping: TaskMapping
    ) -> bool:
        """Check if there's a conflict between Leantime and TaskMaster tasks."""
        # Simple conflict detection based on timestamps and changes
        lt_updated = lt_task.updated_at or lt_task.created_at or datetime.min
        tm_updated = tm_task.updated_at or tm_task.created_at or datetime.min

        # If both have been updated since last sync, it's a conflict
        return (
            lt_updated > mapping.last_sync
            and tm_updated > mapping.last_sync
            and abs((lt_updated - tm_updated).total_seconds()) < 300
        )  # Within 5 minutes

    async def _handle_conflict(
        self, lt_task: LeantimeTask, tm_task: TaskMasterTask, mapping: TaskMapping
    ):
        """Handle synchronization conflicts based on resolution strategy."""
        mapping.conflict_count += 1

        if self.conflict_resolution == ConflictResolution.LEANTIME_WINS:
            await self._update_taskmaster_task(lt_task, tm_task, mapping)
        elif self.conflict_resolution == ConflictResolution.TASKMASTER_WINS:
            await self._update_leantime_task(tm_task, lt_task, mapping)
        elif self.conflict_resolution == ConflictResolution.LATEST_TIMESTAMP:
            lt_updated = lt_task.updated_at or lt_task.created_at or datetime.min
            tm_updated = tm_task.updated_at or tm_task.created_at or datetime.min

            if lt_updated > tm_updated:
                await self._update_taskmaster_task(lt_task, tm_task, mapping)
            else:
                await self._update_leantime_task(tm_task, lt_task, mapping)
        elif self.conflict_resolution == ConflictResolution.MERGE_INTELLIGENT:
            await self._intelligent_merge(lt_task, tm_task, mapping)
        else:  # MANUAL_REVIEW
            logger.warning(
                f"Manual review required for conflict: LT:{lt_task.id} <-> TM:{tm_task.id}"
            )
            # Store conflict for manual resolution
            await self._store_conflict_for_review(lt_task, tm_task, mapping)

    async def _intelligent_merge(
        self, lt_task: LeantimeTask, tm_task: TaskMasterTask, mapping: TaskMapping
    ):
        """Perform intelligent merge of conflicting tasks."""
        # Merge logic: prefer the most recently updated content for each field
        lt_updated = lt_task.updated_at or lt_task.created_at or datetime.min
        tm_updated = tm_task.updated_at or tm_task.created_at or datetime.min

        # Create merged versions
        if lt_updated > tm_updated:
            # Update TaskMaster with Leantime data, preserve AI analysis
            merged_tm = TaskMasterTask(
                id=tm_task.id,
                title=lt_task.headline,
                description=lt_task.description,
                status=self._map_status_to_taskmaster(lt_task.status),
                priority=int(lt_task.priority.value),
                complexity_score=tm_task.complexity_score,  # Preserve AI analysis
                estimated_hours=tm_task.estimated_hours,
                dependencies=tm_task.dependencies,
                subtasks=tm_task.subtasks,
                tags=tm_task.tags,
                ai_analysis=tm_task.ai_analysis,
            )
            await self._apply_taskmaster_update(merged_tm)
        else:
            # Update Leantime with TaskMaster data, preserve Leantime metadata
            merged_lt = LeantimeTask(
                id=lt_task.id,
                headline=tm_task.title,
                description=tm_task.description,
                project_id=lt_task.project_id,
                user_id=lt_task.user_id,
                status=self._map_status_to_leantime(tm_task.status),
                priority=TaskPriority(str(min(tm_task.priority, 4))),
                story_points=tm_task.estimated_hours,
                sprint=lt_task.sprint,
                milestone_id=lt_task.milestone_id,
                dependencies=lt_task.dependencies,
                tags=lt_task.tags,
            )
            await self._apply_leantime_update(merged_lt)

        # Update mapping
        mapping.sync_hash = mapping.generate_hash(
            leantime_task=lt_task, taskmaster_task=tm_task
        )
        mapping.last_sync = datetime.now()

    async def _create_taskmaster_task(self, lt_task: LeantimeTask, mapping_key: str):
        """Create new TaskMaster task from Leantime task."""
        # Convert Leantime task to TaskMaster format
        tm_task = TaskMasterTask(
            id=f"lt_{lt_task.id}_{datetime.now().timestamp()}",
            title=lt_task.headline,
            description=lt_task.description,
            status=self._map_status_to_taskmaster(lt_task.status),
            priority=int(lt_task.priority.value),
        )

        # Apply ADHD optimizations
        tm_task = await self.adhd_optimizer.optimize_taskmaster_task(tm_task)

        # Note: TaskMaster doesn't have direct task creation API,
        # so we'd need to add it to the tasks.json file
        await self._add_task_to_taskmaster_file(tm_task)

        # Create mapping
        self.task_mappings[mapping_key] = TaskMapping(
            leantime_id=lt_task.id,
            taskmaster_id=tm_task.id,
            sync_hash=mapping_key,  # Initial hash
            last_sync=datetime.now(),
        )

    async def _create_leantime_task(self, tm_task: TaskMasterTask, mapping_key: str):
        """Create new Leantime task from TaskMaster task."""
        # Convert TaskMaster task to Leantime format
        lt_task = LeantimeTask(
            headline=tm_task.title,
            description=tm_task.description,
            project_id=self.config.get("sync.default_project_id", 1),
            status=self._map_status_to_leantime(tm_task.status),
            priority=TaskPriority(str(min(tm_task.priority, 4))),
            story_points=(
                int(tm_task.estimated_hours) if tm_task.estimated_hours else None
            ),
        )

        # Apply ADHD optimizations
        lt_task = await self.adhd_optimizer.optimize_task(lt_task)

        # Create in Leantime
        created_task = await self.leantime_client.create_task(lt_task)

        if created_task:
            # Create mapping
            self.task_mappings[mapping_key] = TaskMapping(
                leantime_id=created_task.id,
                taskmaster_id=tm_task.id,
                sync_hash=mapping_key,  # Initial hash
                last_sync=datetime.now(),
            )

    async def _update_taskmaster_task(
        self, lt_task: LeantimeTask, tm_task: TaskMasterTask, mapping: TaskMapping
    ):
        """Update TaskMaster task with Leantime data."""
        # Update TaskMaster task fields
        tm_task.title = lt_task.headline
        tm_task.description = lt_task.description
        tm_task.status = self._map_status_to_taskmaster(lt_task.status)
        tm_task.priority = int(lt_task.priority.value)

        await self._apply_taskmaster_update(tm_task)

        # Update mapping
        mapping.sync_hash = mapping.generate_hash(
            leantime_task=lt_task, taskmaster_task=tm_task
        )
        mapping.last_sync = datetime.now()

    async def _update_leantime_task(
        self, tm_task: TaskMasterTask, lt_task: LeantimeTask, mapping: TaskMapping
    ):
        """Update Leantime task with TaskMaster data."""
        # Update Leantime task fields
        lt_task.headline = tm_task.title
        lt_task.description = tm_task.description
        lt_task.status = self._map_status_to_leantime(tm_task.status)
        lt_task.priority = TaskPriority(str(min(tm_task.priority, 4)))

        await self._apply_leantime_update(lt_task)

        # Update mapping
        mapping.sync_hash = mapping.generate_hash(
            leantime_task=lt_task, taskmaster_task=tm_task
        )
        mapping.last_sync = datetime.now()

    def _map_status_to_taskmaster(self, leantime_status: TaskStatus) -> str:
        """Map Leantime status to TaskMaster status."""
        status_map = {
            TaskStatus.PENDING: "pending",
            TaskStatus.IN_PROGRESS: "in_progress",
            TaskStatus.COMPLETED: "done",
            TaskStatus.BLOCKED: "deferred",
            TaskStatus.DEFERRED: "deferred",
            TaskStatus.CANCELLED: "cancelled",
            TaskStatus.NEEDS_BREAK: "pending",
            TaskStatus.CONTEXT_SWITCH: "pending",
        }
        return status_map.get(leantime_status, "pending")

    def _map_status_to_leantime(self, taskmaster_status: str) -> TaskStatus:
        """Map TaskMaster status to Leantime status."""
        status_map = {
            "pending": TaskStatus.PENDING,
            "in_progress": TaskStatus.IN_PROGRESS,
            "done": TaskStatus.COMPLETED,
            "deferred": TaskStatus.DEFERRED,
            "cancelled": TaskStatus.CANCELLED,
        }
        return status_map.get(taskmaster_status, TaskStatus.PENDING)

    async def _apply_taskmaster_update(self, tm_task: TaskMasterTask):
        """Apply update to TaskMaster task."""
        # Since TaskMaster API doesn't have direct update, we'd modify the file
        await self._update_task_in_taskmaster_file(tm_task)

    async def _apply_leantime_update(self, lt_task: LeantimeTask):
        """Apply update to Leantime task."""
        await self.leantime_client.update_task(lt_task)

    async def _add_task_to_taskmaster_file(self, tm_task: TaskMasterTask):
        """Add task to TaskMaster tasks.json file."""
        # This would require direct file manipulation
        # Implementation depends on TaskMaster's file structure

    async def _update_task_in_taskmaster_file(self, tm_task: TaskMasterTask):
        """Update task in TaskMaster tasks.json file."""
        # This would require direct file manipulation
        # Implementation depends on TaskMaster's file structure

    async def _store_conflict_for_review(
        self, lt_task: LeantimeTask, tm_task: TaskMasterTask, mapping: TaskMapping
    ):
        """Store conflict information for manual review."""
        conflict_data = {
            "leantime_task": asdict(lt_task),
            "taskmaster_task": asdict(tm_task),
            "mapping": asdict(mapping),
            "timestamp": datetime.now().isoformat(),
        }

        # Store to conflicts file or database
        conflicts_file = Path(self.config.get("sync.conflicts_file", "conflicts.json"))
        conflicts = []

        if conflicts_file.exists():
            with open(conflicts_file, "r") as f:
                conflicts = json.load(f)

        conflicts.append(conflict_data)

        with open(conflicts_file, "w") as f:
            json.dump(conflicts, f, indent=2, default=str)

    async def _load_task_mappings(self):
        """Load task mappings from persistent storage."""
        mappings_file = Path(
            self.config.get("sync.mappings_file", "task_mappings.json")
        )

        if mappings_file.exists():
            try:
                with open(mappings_file, "r") as f:
                    data = json.load(f)

                for key, mapping_data in data.items():
                    self.task_mappings[key] = TaskMapping(
                        leantime_id=mapping_data.get("leantime_id"),
                        taskmaster_id=mapping_data.get("taskmaster_id"),
                        sync_hash=mapping_data.get("sync_hash", ""),
                        last_sync=datetime.fromisoformat(
                            mapping_data.get("last_sync", datetime.now().isoformat())
                        ),
                        conflict_count=mapping_data.get("conflict_count", 0),
                        sync_direction=SyncDirection(
                            mapping_data.get("sync_direction", "bidirectional")
                        ),
                    )

                logger.info(f"Loaded {len(self.task_mappings)} task mappings")

            except Exception as e:
                logger.error(f"Failed to load task mappings: {e}")

    async def _save_task_mappings(self):
        """Save task mappings to persistent storage."""
        mappings_file = Path(
            self.config.get("sync.mappings_file", "task_mappings.json")
        )

        try:
            data = {}
            for key, mapping in self.task_mappings.items():
                data[key] = {
                    "leantime_id": mapping.leantime_id,
                    "taskmaster_id": mapping.taskmaster_id,
                    "sync_hash": mapping.sync_hash,
                    "last_sync": mapping.last_sync.isoformat(),
                    "conflict_count": mapping.conflict_count,
                    "sync_direction": mapping.sync_direction.value,
                }

            with open(mappings_file, "w") as f:
                json.dump(data, f, indent=2)

            logger.debug(f"Saved {len(self.task_mappings)} task mappings")

        except Exception as e:
            logger.error(f"Failed to save task mappings: {e}")

    # Public API Methods

    async def sync_project_from_prd(
        self,
        prd_content: str,
        project_name: str,
        leantime_project_id: Optional[int] = None,
    ) -> SyncResult:
        """
        Create project and tasks from PRD using TaskMaster AI analysis.

        Args:
            prd_content: Product Requirements Document content
            project_name: Name for the project
            leantime_project_id: Optional existing Leantime project ID

        Returns:
            Sync result with task creation details
        """
        start_time = datetime.now()
        result = SyncResult(
            success=True,
            synced_tasks=0,
            created_tasks=0,
            updated_tasks=0,
            conflicts=0,
            errors=[],
            sync_duration=0.0,
            timestamp=start_time,
        )

        try:
            # Parse PRD with TaskMaster AI
            prd_analysis = await self.taskmaster_client.parse_prd(
                prd_content, project_name
            )

            # Create or get Leantime project
            if leantime_project_id:
                project = await self.leantime_client.get_project(leantime_project_id)
            else:
                project = await self.leantime_client.create_project(
                    LeantimeProject(
                        name=project_name, description=f"Generated from PRD analysis"
                    )
                )

            if not project:
                raise SyncError("Failed to create or get Leantime project")

            # Create Leantime tasks from PRD analysis
            for tm_task in prd_analysis.tasks:
                try:
                    # Convert to Leantime task
                    lt_task = LeantimeTask(
                        headline=tm_task.title,
                        description=tm_task.description,
                        project_id=project.id,
                        status=self._map_status_to_leantime(tm_task.status),
                        priority=TaskPriority(str(min(tm_task.priority, 4))),
                        story_points=(
                            int(tm_task.estimated_hours)
                            if tm_task.estimated_hours
                            else None
                        ),
                    )

                    # Apply ADHD optimizations
                    lt_task = await self.adhd_optimizer.optimize_task(lt_task)

                    # Create in Leantime
                    created_task = await self.leantime_client.create_task(lt_task)

                    if created_task:
                        # Create mapping
                        mapping_key = f"prd_{tm_task.id}"
                        self.task_mappings[mapping_key] = TaskMapping(
                            leantime_id=created_task.id,
                            taskmaster_id=tm_task.id,
                            sync_hash=mapping_key,
                            last_sync=datetime.now(),
                        )
                        result.created_tasks += 1

                except Exception as e:
                    logger.error(f"Failed to create task '{tm_task.title}': {e}")
                    result.errors.append(f"Task '{tm_task.title}': {e}")

            result.synced_tasks = result.created_tasks
            await self._save_task_mappings()

            logger.info(
                f"PRD sync completed: {result.created_tasks} tasks created from {len(prd_analysis.tasks)} analyzed"
            )

        except Exception as e:
            logger.error(f"PRD sync failed: {e}")
            result.success = False
            result.errors.append(str(e))

        finally:
            result.sync_duration = (datetime.now() - start_time).total_seconds()

        return result

    async def get_sync_status(self) -> Dict[str, Any]:
        """Get current synchronization status."""
        leantime_health = (
            await self.leantime_client.health_check()
            if self.leantime_client
            else {"status": "not_connected"}
        )
        taskmaster_health = (
            await self.taskmaster_client.health_check()
            if self.taskmaster_client
            else {"status": "not_connected"}
        )

        return {
            "sync_running": self.sync_running,
            "last_sync": self.last_sync.isoformat() if self.last_sync else None,
            "sync_interval": self.sync_interval,
            "conflict_resolution": self.conflict_resolution.value,
            "task_mappings_count": len(self.task_mappings),
            "leantime_status": leantime_health,
            "taskmaster_status": taskmaster_health,
            "total_conflicts": sum(
                mapping.conflict_count for mapping in self.task_mappings.values()
            ),
        }


# Factory function for easy instantiation
def create_sync_manager(config: Config) -> LeantimeTaskMasterSyncManager:
    """
    Factory function to create sync manager.

    Args:
        config: Dopemux configuration

    Returns:
        Configured sync manager
    """
    return LeantimeTaskMasterSyncManager(config)
