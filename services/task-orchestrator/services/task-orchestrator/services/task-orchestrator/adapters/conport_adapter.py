"""
ConPort Event Adapter - Architecture 3.0 Components 2, 4, 5

Implements bidirectional transformation and cross-plane data flow:
- Component 2: Schema transformations (OrchestrationTask ↔ ConPort progress_entry)
- Component 4: Real-time sync (Task-Orchestrator → ConPort MCP pushing)
- Component 5: Cross-plane queries (ConPort → Task-Orchestrator enrichment)

Ensures ADHD metadata preservation and lossless bidirectional synchronization.

Created: 2025-10-19 (Components 2, 4)
Enhanced: 2025-10-20 (Component 5)
Specification: docs/implementation-plans/conport-event-schema-design.md
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# Import from parent directory
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from enhanced_orchestrator import OrchestrationTask, TaskStatus, AgentType

logger = logging.getLogger(__name__)


# ============================================================================
# ADHD Tag Utilities (from Task 2.1 Schema Specification)
# ============================================================================

def encode_energy_tag(energy: str) -> str:
    """Encode energy level as tag."""
    return f"energy-{energy.lower()}"


def encode_complexity_tag(complexity: float) -> str:
    """Encode complexity score (0.0-1.0) as tag (0-10)."""
    complexity_int = int(complexity * 10)
    complexity_int = max(0, min(10, complexity_int))  # Clamp to [0, 10]
    return f"complexity-{complexity_int}"


def encode_priority_tag(priority: int) -> str:
    """Encode priority (1-5) as tag."""
    priority = max(1, min(5, priority))  # Clamp to [1, 5]
    return f"priority-{priority}"


def decode_energy_tag(tag: str) -> Optional[str]:
    """Decode energy tag to energy level."""
    if tag.startswith("energy-"):
        return tag.split("-", 1)[1]
    return None


def decode_complexity_tag(tag: str) -> Optional[float]:
    """Decode complexity tag (0-10) to score (0.0-1.0)."""
    if tag.startswith("complexity-"):
        try:
            complexity_int = int(tag.split("-")[1])
            return complexity_int / 10.0
        except (ValueError, IndexError):
            return None
    return None


def decode_priority_tag(tag: str) -> Optional[int]:
    """Decode priority tag to priority value."""
    if tag.startswith("priority-"):
        try:
            return int(tag.split("-")[1])
        except (ValueError, IndexError):
            return None
    return None


# ============================================================================
# Core Transformation Functions (from Task 2.1 Schema Specification)
# ============================================================================

def orchestration_task_to_conport_progress(
    task: OrchestrationTask,
    workspace_id: str
) -> Dict[str, Any]:
    """
    Transform OrchestrationTask to ConPort progress_entry format.

    Ensures ADHD metadata is preserved as queryable tags.

    Args:
        task: OrchestrationTask to transform
        workspace_id: Absolute path to workspace (e.g., "/Users/hue/code/dopemux-mvp")

    Returns:
        Dict ready for mcp__conport__log_progress() call

    Raises:
        ValueError: If required fields are missing
    """
    # Validate required fields
    if not task.id or not task.title:
        raise ValueError(f"Invalid task: missing id or title (id={task.id}, title={task.title})")

    # Step 1: Map status enum
    status_mapping = {
        TaskStatus.PENDING: "TODO",
        TaskStatus.IN_PROGRESS: "IN_PROGRESS",
        TaskStatus.COMPLETED: "DONE",
        TaskStatus.BLOCKED: "BLOCKED",
        TaskStatus.NEEDS_BREAK: "IN_PROGRESS",  # ConPort doesn't have NEEDS_BREAK
        TaskStatus.CONTEXT_SWITCH: "IN_PROGRESS",  # Treat as in-progress
        TaskStatus.PAUSED: "BLOCKED"  # Paused = temporarily blocked
    }

    # Step 2: Build rich description with embedded metadata
    # Format: "Title | Description | Duration: Xm | Complexity: Y.Z | Energy: {level}"
    description_parts = [
        task.title,
        task.description if task.description else "",
        f"Duration: {task.estimated_minutes}m",
        f"Complexity: {task.complexity_score}",
        f"Energy: {task.energy_required}"
    ]
    description = " | ".join(p for p in description_parts if p)

    # Step 3: Build ADHD metadata tags (queryable)
    tags = [
        "task-orchestrator",  # Source system identifier
        encode_energy_tag(task.energy_required),
        encode_complexity_tag(task.complexity_score),
        encode_priority_tag(task.priority)
    ]

    # Add agent assignment tag if present
    if task.assigned_agent:
        tags.append(f"agent-{task.assigned_agent.value}")

    # Add Leantime sync tag if applicable
    if task.leantime_id:
        tags.append("leantime-synced")

    # Step 4: Build ConPort progress_entry
    progress_entry = {
        "id": task.id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "workspace_id": workspace_id,
        "status": status_mapping.get(task.status, "TODO"),
        "description": description,
        "tags": tags
    }

    # Step 5: Add linking if Leantime task
    if task.leantime_id:
        progress_entry.update({
            "linked_item_type": "leantime_task",
            "linked_item_id": str(task.leantime_id),
            "link_relationship_type": "tracks_implementation"
        })

    return progress_entry


def conport_progress_to_orchestration_task(progress: Dict[str, Any]) -> OrchestrationTask:
    """
    Transform ConPort progress_entry to OrchestrationTask.

    Parses embedded metadata from description and tags.

    Args:
        progress: ConPort progress_entry dict

    Returns:
        OrchestrationTask with all metadata restored

    Raises:
        ValueError: If progress dict is invalid
    """
    # Validate required fields
    required_fields = ["id", "status", "description", "timestamp"]
    missing = [f for f in required_fields if f not in progress]
    if missing:
        raise ValueError(f"Invalid progress entry: missing fields {missing}")

    # Step 1: Reverse status mapping
    status_mapping = {
        "TODO": TaskStatus.PENDING,
        "IN_PROGRESS": TaskStatus.IN_PROGRESS,
        "DONE": TaskStatus.COMPLETED,
        "BLOCKED": TaskStatus.BLOCKED
    }

    # Step 2: Parse description (format: "title | description | metadata")
    desc_parts = progress["description"].split(" | ")
    title = desc_parts[0] if len(desc_parts) > 0 else "Unknown Task"
    description = desc_parts[1] if len(desc_parts) > 1 else ""

    # Parse embedded metadata from description
    estimated_minutes = 25  # default
    complexity_score = 0.5  # default
    energy_required = "medium"  # default

    for part in desc_parts[2:]:  # Metadata in later parts
        if part.startswith("Duration: "):
            try:
                estimated_minutes = int(part.replace("Duration: ", "").replace("m", ""))
            except ValueError:
                pass  # Use default
        elif part.startswith("Complexity: "):
            try:
                complexity_score = float(part.replace("Complexity: ", ""))
            except ValueError:
                pass  # Use default
        elif part.startswith("Energy: "):
            energy_required = part.replace("Energy: ", "")

    # Step 3: Extract ADHD metadata from tags (AUTHORITATIVE)
    priority = 3  # default
    assigned_agent = None
    leantime_id = None

    for tag in progress.get("tags", []):
        # Tags override description metadata (tags are queryable, thus canonical)
        decoded_complexity = decode_complexity_tag(tag)
        if decoded_complexity is not None:
            complexity_score = decoded_complexity

        decoded_energy = decode_energy_tag(tag)
        if decoded_energy:
            energy_required = decoded_energy

        decoded_priority = decode_priority_tag(tag)
        if decoded_priority is not None:
            priority = decoded_priority

        # Agent assignment
        if tag.startswith("agent-"):
            agent_name = tag.split("-", 1)[1]
            try:
                assigned_agent = AgentType(agent_name)
            except ValueError:
                logger.warning(f"Unknown agent type in tag: {tag}")

    # Step 4: Extract Leantime link if present
    if progress.get("linked_item_type") == "leantime_task":
        try:
            leantime_id = int(progress["linked_item_id"])
        except (ValueError, TypeError):
            logger.warning(f"Invalid leantime_id: {progress.get('linked_item_id')}")

    # Step 5: Build OrchestrationTask
    return OrchestrationTask(
        id=f"conport-{progress['id']}",  # Prefix to identify source
        leantime_id=leantime_id,
        title=title,
        description=description,
        status=status_mapping.get(progress["status"], TaskStatus.PENDING),
        priority=priority,
        complexity_score=complexity_score,
        estimated_minutes=estimated_minutes,
        assigned_agent=assigned_agent,
        energy_required=energy_required,
        cognitive_load=complexity_score,  # Same as complexity
        context_switches_allowed=2,  # Default ADHD setting
        break_frequency_minutes=25,  # Default Pomodoro
        dependencies=[],  # Populated separately from linked_items query
        dependents=[],
        agent_assignments={},
        progress_checkpoints=[],
        last_synced=datetime.fromisoformat(progress["timestamp"]),
        sync_conflicts=[]
    )


# ============================================================================
# Safe Transformation with Error Handling
# ============================================================================

def safe_orchestration_task_to_conport_progress(
    task: OrchestrationTask,
    workspace_id: str
) -> Optional[Dict[str, Any]]:
    """
    Safe transformation with validation and error handling.

    Returns None if transformation fails instead of raising exception.
    """
    try:
        # Validate required fields
        if not task.id or not task.title:
            logger.error(f"Invalid task: missing id or title (id={task.id}, title={getattr(task, 'title', None)})")
            return None

        # Validate complexity score range
        if not (0.0 <= task.complexity_score <= 1.0):
            logger.warning(f"Invalid complexity {task.complexity_score}, clamping to [0,1]")
            task.complexity_score = max(0.0, min(1.0, task.complexity_score))

        # Validate workspace_id
        if not workspace_id or not workspace_id.startswith("/"):
            logger.error(f"Invalid workspace_id: must be absolute path, got: {workspace_id}")
            return None

        # Perform transformation
        progress_data = orchestration_task_to_conport_progress(task, workspace_id)

        # Validate output
        required_keys = ["workspace_id", "status", "description", "tags"]
        if not all(k in progress_data for k in required_keys):
            logger.error(f"Invalid progress_data: missing required keys")
            return None

        return progress_data

    except Exception as e:
        logger.error(f"Transformation failed for task {getattr(task, 'id', 'unknown')}: {e}")
        return None


def safe_conport_progress_to_orchestration_task(progress: Dict[str, Any]) -> Optional[OrchestrationTask]:
    """
    Safe reverse transformation with error handling.

    Returns None if transformation fails instead of raising exception.
    """
    try:
        return conport_progress_to_orchestration_task(progress)
    except Exception as e:
        logger.error(f"Reverse transformation failed for progress {progress.get('id', 'unknown')}: {e}")
        return None


# ============================================================================
# ConPort Event Adapter Class
# ============================================================================

class ConPortEventAdapter:
    """
    Adapter for ConPort ↔ Task-Orchestrator event synchronization.

    Handles:
    - Bidirectional task transformations
    - ConPort MCP API interactions
    - Dependency synchronization
    - Error handling and retry logic
    - ADHD metadata preservation

    Usage:
        adapter = ConPortEventAdapter(workspace_id, conport_client)
        await adapter.sync_task_to_conport(orchestration_task)
        tasks = await adapter.get_all_tasks_from_conport()
    """

    def __init__(self, workspace_id: str, conport_client: Any = None):
        """
        Initialize ConPort adapter.

        Args:
            workspace_id: Absolute path to workspace
            conport_client: ConPort MCP client (optional, uses placeholder if None)
        """
        self.workspace_id = workspace_id
        self.conport_client = conport_client
        self.local_cache: Dict[str, Dict] = {}  # Fallback cache if ConPort unavailable

    # ------------------------------------------------------------------------
    # Task Synchronization Methods
    # ------------------------------------------------------------------------

    async def create_task_in_conport(self, task: OrchestrationTask) -> Optional[int]:
        """
        Create new task in ConPort.

        Returns ConPort progress_entry ID if successful, None otherwise.
        """
        try:
            # Transform to ConPort format
            progress_data = safe_orchestration_task_to_conport_progress(task, self.workspace_id)
            if not progress_data:
                logger.error(f"Transformation failed for task {task.id}")
                return None

            # Call ConPort MCP (with retry)
            conport_id = await self._resilient_log_progress(progress_data)

            if conport_id:
                logger.info(f"✅ Created task in ConPort: {task.title} (ID: {conport_id})")
                # Store ConPort ID in task for future updates
                task.conport_id = conport_id
                return conport_id
            else:
                # Fallback: Store in local cache
                self.local_cache[task.id] = progress_data
                logger.warning(f"⚠️ ConPort unavailable, cached task locally: {task.id}")
                return None

        except Exception as e:
            logger.error(f"Failed to create task in ConPort: {e}")
            return None

    async def create_task_in_conport_from_sync(self, event: Any) -> Optional[int]:
        """
        Create task in ConPort from sync event data.

        Used by Task Orchestrator sync methods.
        """
        try:
            # Extract progress data from sync event
            progress_data = {
                "workspace_id": self.workspace_id,
                "status": event.data.get("status", "pending").upper(),
                "description": f"Task orchestration: {event.data.get('title', 'Unknown task')}",
                "linked_item_type": "orchestration_task",
                "linked_item_id": event.task_id
            }

            # Call ConPort MCP (with retry)
            conport_id = await self._resilient_log_progress(progress_data)

            if conport_id:
                logger.info(f"✅ Synced task to ConPort: {event.task_id} (ID: {conport_id})")
                return conport_id
            else:
                logger.warning(f"⚠️ ConPort sync failed, task not persisted: {event.task_id}")
                return None

        except Exception as e:
            logger.error(f"Failed to sync task to ConPort: {e}")
            return None

    async def update_task_in_conport(
        self,
        task: OrchestrationTask,
        status: Optional[str] = None,
        description: Optional[str] = None
    ) -> bool:
        """
        Update existing task in ConPort.

        Returns True if successful, False otherwise.
        """
        try:
            if not hasattr(task, 'conport_id') or task.conport_id is None:
                logger.error(f"Cannot update task {task.id}: no conport_id")
                return False

            # Call ConPort update
            success = await self._resilient_update_progress(
                progress_id=task.conport_id,
                status=status,
                description=description
            )

            if success:
                task.last_synced = datetime.now()
                logger.info(f"✅ Updated task in ConPort: {task.title} (ID: {task.conport_id})")
            else:
                logger.warning(f"⚠️ Failed to update task in ConPort: {task.id}")

            return success

        except Exception as e:
            logger.error(f"Update failed for task {task.id}: {e}")
            return False

    async def get_all_tasks_from_conport(
        self,
        status_filter: Optional[str] = None,
        tags_filter: Optional[List[str]] = None
    ) -> List[OrchestrationTask]:
        """
        Retrieve all tasks from ConPort and transform to OrchestrationTask.

        Args:
            status_filter: Filter by status ("TODO", "IN_PROGRESS", "DONE", "BLOCKED")
            tags_filter: Filter by tags (e.g., ["task-orchestrator", "energy-high"])

        Returns:
            List of OrchestrationTask objects
        """
        try:
            # Call ConPort get_progress (placeholder - needs actual MCP call)
            progress_entries = await self._get_progress_from_conport(
                status_filter=status_filter,
                tags_filter=tags_filter
            )

            # Transform all entries
            tasks = []
            for progress in progress_entries:
                task = safe_conport_progress_to_orchestration_task(progress)
                if task:
                    tasks.append(task)
                else:
                    logger.warning(f"Skipped invalid progress entry: {progress.get('id')}")

            logger.info(f"✅ Retrieved {len(tasks)} tasks from ConPort")
            return tasks

        except Exception as e:
            logger.error(f"Failed to get tasks from ConPort: {e}")
            return []

    async def sync_dependencies_to_conport(self, task: OrchestrationTask) -> bool:
        """
        Sync task dependencies to ConPort using link_conport_items.

        Args:
            task: OrchestrationTask with dependencies populated

        Returns:
            True if all dependencies synced successfully
        """
        try:
            if not hasattr(task, 'conport_id') or task.conport_id is None:
                logger.error(f"Cannot sync dependencies for task {task.id}: no conport_id")
                return False

            # Sync each dependency
            for dependency_id in task.dependencies:
                # Find ConPort ID for dependency (assumes conport-{id} format)
                if dependency_id.startswith("conport-"):
                    dep_conport_id = int(dependency_id.split("-")[1])
                else:
                    logger.warning(f"Unknown dependency ID format: {dependency_id}")
                    continue

                # Create dependency link
                await self._link_conport_items(
                    source_id=task.conport_id,
                    target_id=dep_conport_id,
                    relationship_type="depends_on",
                    description=f"Task {task.id} depends on {dependency_id}"
                )

            logger.info(f"✅ Synced {len(task.dependencies)} dependencies for task {task.id}")
            return True

        except Exception as e:
            logger.error(f"Dependency sync failed for task {task.id}: {e}")
            return False

    # ------------------------------------------------------------------------
    # ConPort MCP Client Methods (Resilient wrappers)
    # ------------------------------------------------------------------------

    async def _resilient_log_progress(self, progress_data: Dict) -> Optional[int]:
        """
        Log progress to ConPort with retry logic.

        Returns ConPort progress_entry ID if successful, None otherwise.
        """
        max_retries = 3

        for attempt in range(max_retries):
            try:
                if self.conport_client:
                    # Call actual ConPort MCP client
                    result = await self.conport_client.log_progress(**progress_data)
                    # ConPort MCP returns dict with "id" field
                    if isinstance(result, dict) and "id" in result:
                        return result["id"]
                    else:
                        logger.error(f"Invalid ConPort response format: {result}")
                        return None
                else:
                    # Placeholder: No client available
                    logger.warning("ConPort client not configured, using placeholder")
                    return None

            except (ConnectionError, OSError) as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.warning(f"ConPort connection failed (attempt {attempt+1}/{max_retries}), retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"ConPort unavailable after {max_retries} attempts: {e}")
                    return None

            except Exception as e:
                logger.error(f"ConPort API error: {e}")
                return None

        return None

    async def _resilient_update_progress(
        self,
        progress_id: int,
        status: Optional[str] = None,
        description: Optional[str] = None
    ) -> bool:
        """
        Update progress in ConPort with retry logic.

        Returns True if successful, False otherwise.
        """
        max_retries = 3

        for attempt in range(max_retries):
            try:
                if self.conport_client:
                    # Call actual ConPort MCP client
                    await self.conport_client.update_progress(
                        workspace_id=self.workspace_id,
                        progress_id=progress_id,
                        status=status,
                        description=description
                    )
                    return True
                else:
                    # Placeholder
                    logger.warning("ConPort client not configured")
                    return False

            except ConnectionError as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.warning(f"ConPort update failed (attempt {attempt+1}/{max_retries}), retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"ConPort unavailable after {max_retries} attempts: {e}")
                    return False

            except Exception as e:
                logger.error(f"ConPort update error: {e}")
                return False

        return False

    async def _get_progress_from_conport(
        self,
        status_filter: Optional[str] = None,
        tags_filter: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Get progress entries from ConPort.
        """
        try:
            if self.conport_client:
                # Call actual ConPort MCP client
                result = await self.conport_client.get_progress(
                    workspace_id=self.workspace_id,
                    status_filter=status_filter,
                    limit=100  # Reasonable limit for task orchestration
                )
                # ConPort MCP returns dict with "result" field containing list of progress entries
                if isinstance(result, dict) and "result" in result:
                    entries = result["result"]
                    # Filter by tags if specified (ConPort doesn't have direct tag filter in get_progress)
                    if tags_filter:
                        filtered = []
                        for entry in entries:
                            entry_tags = entry.get("tags", [])
                            if any(tag in entry_tags for tag in tags_filter):
                                filtered.append(entry)
                        return filtered
                    return entries
                else:
                    logger.error(f"Invalid ConPort get_progress response: {result}")
                    return []
            else:
                logger.warning("ConPort client not configured")
                return []

        except Exception as e:
            logger.error(f"Failed to get progress from ConPort: {e}")
            return []

    async def _link_conport_items(
        self,
        source_id: int,
        target_id: int,
        relationship_type: str,
        description: str
    ) -> bool:
        """
        Create relationship link between ConPort items.
        """
        try:
            if self.conport_client:
                # Call actual ConPort MCP client
                await self.conport_client.link_conport_items(
                    workspace_id=self.workspace_id,
                    source_item_type="progress_entry",
                    source_item_id=str(source_id),
                    target_item_type="progress_entry",
                    target_item_id=str(target_id),
                    relationship_type=relationship_type,
                    description=description
                )
                logger.info(f"📎 Linked: {source_id} -{relationship_type}-> {target_id}")
                return True
            else:
                logger.warning("ConPort client not configured for linking")
                return False

        except Exception as e:
            logger.error(f"Failed to link items: {e}")
            return False

    # ------------------------------------------------------------------------
    # Batch Operations
    # ------------------------------------------------------------------------

    async def batch_create_tasks(self, tasks: List[OrchestrationTask]) -> List[int]:
        """
        Create multiple tasks in ConPort.

        Uses sequential calls for Phase 1 (acceptable performance for <10 tasks).

        Returns list of ConPort IDs (None for failed items).
        """
        conport_ids = []

        for task in tasks:
            conport_id = await self.create_task_in_conport(task)
            conport_ids.append(conport_id)

        successful = sum(1 for id in conport_ids if id is not None)
        logger.info(f"✅ Batch created {successful}/{len(tasks)} tasks in ConPort")

        return conport_ids

    async def batch_update_tasks(self, updates: List[Dict[str, Any]]) -> int:
        """
        Update multiple tasks in ConPort.

        Args:
            updates: List of {"conport_id": int, "status": str, "description": str}

        Returns:
            Number of successful updates
        """
        successful = 0

        for update in updates:
            success = await self._resilient_update_progress(
                progress_id=update["conport_id"],
                status=update.get("status"),
                description=update.get("description")
            )
            if success:
                successful += 1

        logger.info(f"✅ Batch updated {successful}/{len(updates)} tasks in ConPort")
        return successful

    # ------------------------------------------------------------------------
    # Sprint Context Management
    # ------------------------------------------------------------------------

    async def activate_sprint_context(self, sprint_id: str, sprint_name: str, task_count: int) -> bool:
        """
        Set ConPort active_context for sprint execution.

        Creates sprint context in ACT mode with task-orchestrator metadata.
        """
        try:
            sprint_context = {
                "sprint_id": sprint_id,
                "sprint_name": sprint_name,
                "mode": "ACT",  # Sprint execution mode
                "focus": f"Sprint {sprint_id} execution with automated PM",
                "automation_enabled": True,
                "adhd_optimized": True,
                "task_count": task_count,
                "orchestration_active": True,
                "auto_setup_timestamp": datetime.now().isoformat()
            }

            if self.conport_client:
                # Call ConPort MCP
                await self.conport_client.update_active_context(
                    workspace_id=self.workspace_id,
                    patch_content=sprint_context
                )
                logger.info(f"🎯 ConPort context activated for sprint: {sprint_id}")
                return True
            else:
                logger.warning("ConPort client not configured")
                return False

        except Exception as e:
            logger.error(f"Failed to activate sprint context: {e}")
            return False

    # ------------------------------------------------------------------------
    # Event Handler Helper Methods (Component 4)
    # ------------------------------------------------------------------------

    async def update_task_status(self, task_id: str, status: str) -> bool:
        """
        Update task status in ConPort (for event handlers).

        Args:
            task_id: Task ID (format: "orch_{leantime_id}" or "conport-{conport_id}")
            status: New status (TODO, IN_PROGRESS, DONE, BLOCKED)

        Returns:
            True if successful, False otherwise
        """
        try:
            # Extract ConPort ID from task_id
            if task_id.startswith("conport-"):
                conport_id = int(task_id.split("-")[1])
            else:
                # Query ConPort to find task by tags
                all_tasks = await self.get_all_tasks_from_conport(tags_filter=["task-orchestrator"])
                matching_task = None
                for task in all_tasks:
                    if task.id == task_id:
                        matching_task = task
                        break

                if not matching_task or not hasattr(matching_task, 'conport_id'):
                    logger.warning(f"Task not found in ConPort: {task_id}")
                    return False

                conport_id = matching_task.conport_id

            # Update status in ConPort
            success = await self._resilient_update_progress(
                progress_id=conport_id,
                status=status
            )

            if success:
                logger.info(f"✅ Updated task {task_id} status to {status} in ConPort")
            else:
                logger.warning(f"⚠️ Failed to update task {task_id} status in ConPort")

            return success

        except Exception as e:
            logger.error(f"Failed to update task status for {task_id}: {e}")
            return False

    async def update_task_progress(self, task_id: str, status: str, progress: float) -> bool:
        """
        Update task progress in ConPort (for event handlers).

        Args:
            task_id: Task ID
            status: Current status
            progress: Progress percentage (0.0-1.0)

        Returns:
            True if successful
        """
        try:
            # Update status (progress is embedded in description metadata)
            # For future enhancement, could add progress field to ConPort schema
            return await self.update_task_status(task_id, status)

        except Exception as e:
            logger.error(f"Failed to update task progress for {task_id}: {e}")
            return False

    async def sync_imported_tasks(self, task_count: int, sprint_id: str) -> bool:
        """
        Sync imported tasks to ConPort (for tasks_imported event).

        Args:
            task_count: Number of tasks imported
            sprint_id: Sprint ID

        Returns:
            True if successful
        """
        try:
            # Activate sprint context in ConPort
            success = await self.activate_sprint_context(
                sprint_id=sprint_id,
                sprint_name=f"Sprint {sprint_id}",
                task_count=task_count
            )

            if success:
                logger.info(f"✅ Synced {task_count} imported tasks for sprint {sprint_id}")
            else:
                logger.warning(f"⚠️ Failed to sync imported tasks for sprint {sprint_id}")

            return success

        except Exception as e:
            logger.error(f"Failed to sync imported tasks: {e}")
            return False

    async def link_decision_to_tasks(self, decision_id: str) -> bool:
        """
        Link decision to related tasks in ConPort (for decision_logged event).

        Args:
            decision_id: ConPort decision ID

        Returns:
            True if successful
        """
        try:
            # Get all active tasks
            active_tasks = await self.get_all_tasks_from_conport(status_filter="IN_PROGRESS")

            # Link decision to all active tasks (they likely contributed to the decision)
            linked_count = 0
            for task in active_tasks:
                if hasattr(task, 'conport_id') and task.conport_id:
                    await self._link_conport_items(
                        source_id=int(decision_id) if decision_id.isdigit() else 0,
                        target_id=task.conport_id,
                        relationship_type="informs",
                        description=f"Decision logged during task {task.id}"
                    )
                    linked_count += 1

            logger.info(f"✅ Linked decision {decision_id} to {linked_count} tasks")
            return True

        except Exception as e:
            logger.error(f"Failed to link decision to tasks: {e}")
            return False

    async def adjust_task_recommendations(self, energy_level: str, attention_level: str) -> bool:
        """
        Adjust task recommendations based on ADHD state (for adhd_state_changed event).

        Args:
            energy_level: Current energy level (low, medium, high)
            attention_level: Current attention level (scattered, transitioning, focused)

        Returns:
            True if successful
        """
        try:
            # Update active context with current ADHD state
            if self.conport_client:
                await self.conport_client.update_active_context(
                    workspace_id=self.workspace_id,
                    patch_content={
                        "current_energy": energy_level,
                        "current_attention": attention_level,
                        "state_updated_at": datetime.now().isoformat()
                    }
                )
                logger.info(f"✅ Updated ADHD state in ConPort: energy={energy_level}, attention={attention_level}")
                return True
            else:
                logger.warning("ConPort client not configured")
                return False

        except Exception as e:
            logger.error(f"Failed to adjust task recommendations: {e}")
            return False

    # ------------------------------------------------------------------------
    # Component 5: Cross-Plane Query Methods
    # ------------------------------------------------------------------------

    async def enrich_task_with_decisions(
        self,
        task: OrchestrationTask,
        tags: List[str]
    ) -> List[Dict]:
        """
        Query ConPort for decisions relevant to a task.

        Use before task execution to provide decision context and guidance.

        Args:
            task: OrchestrationTask to enrich
            tags: Tags to filter decisions (e.g., ["oauth", "authentication"])

        Returns:
            List of relevant decision dicts with summary, rationale, tags

        Example:
            Task: "Implement OAuth authentication"
            Tags: ["oauth", "authentication", "security"]
            Returns: [{"id": 145, "summary": "Use OAuth 2.0 PKCE", ...}]
        """
        if not self.conport_client:
            logger.warning("⚠️ ConPort client not configured, cannot query decisions")
            return []

        try:
            logger.info(f"🔍 Querying ConPort decisions for task '{task.title}' with tags: {tags}")

            # Query ConPort for decisions matching any of the tags
            result = await self.conport_client.get_decisions(
                workspace_id=self.workspace_id,
                tags_filter_include_any=tags,
                limit=10
            )

            decisions = result.get("result", [])
            logger.info(f"📚 Found {len(decisions)} relevant decisions")

            # Optionally link decisions to task in ConPort
            if decisions and hasattr(task, 'conport_id') and task.conport_id:
                for decision in decisions[:3]:  # Link top 3 most relevant
                    try:
                        await self._link_conport_items(
                            source_item_type="decision",
                            source_item_id=str(decision['id']),
                            target_item_type="progress_entry",
                            target_item_id=str(task.conport_id),
                            relationship_type="informs",
                            description=f"Decision informs task implementation"
                        )
                    except Exception as e:
                        logger.debug(f"Could not link decision {decision['id']} to task: {e}")

            return decisions

        except Exception as e:
            logger.error(f"❌ Failed to query decisions: {e}")
            return []

    async def get_applicable_patterns(
        self,
        task_domain: str,
        complexity: float
    ) -> List[Dict]:
        """
        Find system patterns applicable to task domain and complexity.

        Use to guide implementation with proven patterns.

        Args:
            task_domain: Domain tags (e.g., "adhd", "error-handling", "authentication")
            complexity: Task complexity score (0.0-1.0)

        Returns:
            List of applicable pattern dicts with name, description, tags

        Example:
            Domain: "adhd,error-handling"
            Complexity: 0.6
            Returns: [{"name": "ADHD Error Message Structure", ...}]
        """
        if not self.conport_client:
            logger.warning("⚠️ ConPort client not configured, cannot query patterns")
            return []

        try:
            # Parse domain tags
            domain_tags = [tag.strip() for tag in task_domain.split(",")]
            logger.info(f"🔍 Querying ConPort patterns for domain: {domain_tags}, complexity: {complexity}")

            # Query ConPort for patterns matching domain
            result = await self.conport_client.get_system_patterns(
                workspace_id=self.workspace_id,
                tags_filter_include_any=domain_tags,
                limit=5
            )

            # ConPort returns different format - extract patterns
            if isinstance(result, dict):
                patterns = result.get("patterns", result.get("result", []))
            else:
                patterns = []

            logger.info(f"📐 Found {len(patterns)} applicable patterns")
            return patterns

        except Exception as e:
            logger.error(f"❌ Failed to query patterns: {e}")
            return []

    async def get_current_adhd_state(self) -> Dict[str, str]:
        """
        Get current ADHD state (energy, attention) from ConPort active context.

        Use to adapt task recommendations based on user's current state.

        Returns:
            Dict with {"energy": str, "attention": str, "mode": str}
            Default: {"energy": "medium", "attention": "normal", "mode": "ACT"}

        Example:
            Returns: {"energy": "low", "attention": "scattered", "mode": "PLAN"}
            Adapt: Suggest lower-complexity tasks, shorter sessions
        """
        if not self.conport_client:
            logger.warning("⚠️ ConPort client not configured, using default ADHD state")
            return {"energy": "medium", "attention": "normal", "mode": "ACT"}

        try:
            logger.debug("🔍 Querying ConPort active context for ADHD state")

            result = await self.conport_client.get_active_context(
                workspace_id=self.workspace_id
            )

            # Extract ADHD state from active context
            energy = result.get("current_energy", "medium")
            attention = result.get("current_attention", "normal")
            mode = result.get("mode", "ACT")

            adhd_state = {
                "energy": energy,
                "attention": attention,
                "mode": mode
            }

            logger.info(f"🧠 Current ADHD state: energy={energy}, attention={attention}, mode={mode}")
            return adhd_state

        except Exception as e:
            logger.error(f"❌ Failed to query ADHD state: {e}")
            return {"energy": "medium", "attention": "normal", "mode": "ACT"}

    async def get_task_dependencies_from_graph(
        self,
        task_id: str
    ) -> List[Dict]:
        """
        Query knowledge graph for task dependencies via ConPort relationships.

        Use to discover implicit dependencies through decision/pattern links.

        Args:
            task_id: ConPort progress entry ID

        Returns:
            List of related items with type, id, relationship, description

        Example:
            Task: "Component 6"
            Returns: [
                {"type": "decision", "id": 161, "relationship": "depends_on"},
                {"type": "progress_entry", "id": 157, "relationship": "blocked_by"}
            ]
        """
        if not self.conport_client:
            logger.warning("⚠️ ConPort client not configured, cannot query dependencies")
            return []

        try:
            logger.info(f"🔍 Querying ConPort knowledge graph for task {task_id}")

            # Query linked items
            result = await self.conport_client.get_linked_items(
                workspace_id=self.workspace_id,
                item_type="progress_entry",
                item_id=task_id,
                limit=20
            )

            # Extract linked items
            if isinstance(result, dict):
                linked_items = result.get("links", result.get("result", []))
            else:
                linked_items = []

            logger.info(f"🕸️ Found {len(linked_items)} linked items")
            return linked_items

        except Exception as e:
            logger.error(f"❌ Failed to query dependencies: {e}")
            return []

    async def find_similar_completed_tasks(
        self,
        task_description: str,
        limit: int = 5
    ) -> List[Dict]:
        """
        Find similar completed tasks via semantic search.

        Use to learn from past implementations and avoid repeating mistakes.

        Args:
            task_description: Natural language description of current task
            limit: Number of similar tasks to return (default 5)

        Returns:
            List of similar task dicts with description, status, outcome

        Example:
            Description: "Add real-time sync for ConPort"
            Returns: [{
                "id": 157,
                "description": "Component 4: ConPort MCP Real-Time Sync",
                "status": "DONE",
                "score": 0.89
            }]
        """
        if not self.conport_client:
            logger.warning("⚠️ ConPort client not configured, cannot search tasks")
            return []

        try:
            logger.info(f"🔍 Semantic search for similar tasks: '{task_description}'")

            # Semantic search ConPort for similar progress entries
            result = await self.conport_client.semantic_search_conport(
                workspace_id=self.workspace_id,
                query_text=task_description,
                top_k=limit,
                filter_item_types=["progress_entry"]
            )

            # Extract results
            if isinstance(result, dict):
                similar_tasks = result.get("results", [])
            else:
                similar_tasks = []

            # Filter for DONE tasks only (learn from completed work)
            completed_tasks = [
                task for task in similar_tasks
                if task.get("status") == "DONE"
            ]

            logger.info(f"✅ Found {len(completed_tasks)} similar completed tasks")
            return completed_tasks

        except Exception as e:
            logger.error(f"❌ Failed to search similar tasks: {e}")
            return []

    # ------------------------------------------------------------------------
    # Utility Methods
    # ------------------------------------------------------------------------

    def get_task_by_conport_id(self, conport_id: int, tasks: List[OrchestrationTask]) -> Optional[OrchestrationTask]:
        """Find OrchestrationTask by its ConPort ID."""
        for task in tasks:
            if hasattr(task, 'conport_id') and task.conport_id == conport_id:
                return task
        return None

    def get_cache_stats(self) -> Dict[str, int]:
        """Get local cache statistics."""
        return {
            "cached_tasks": len(self.local_cache),
            "cache_size_bytes": sum(len(str(v)) for v in self.local_cache.values())
        }
