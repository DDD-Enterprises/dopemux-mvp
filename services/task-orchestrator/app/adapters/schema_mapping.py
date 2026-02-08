"""
Schema Mapping Utilities - Architecture 3.0 Component 2

Reusable utilities for ADHD metadata encoding, description formatting,
and dependency mapping between ConPort and Task-Orchestrator.

Created: 2025-10-19 (Task 2.4)
Specification: docs/implementation-plans/conport-event-schema-design.md
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

# Import from parent directory
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from task_orchestrator.models import OrchestrationTask, TaskStatus

logger = logging.getLogger(__name__)


# ============================================================================
# ADHD Tag Encoding (Queryable Metadata)
# ============================================================================

def encode_energy_tag(energy: str) -> str:
    """
    Encode energy level as standardized tag.

    Args:
        energy: "low", "medium", or "high"

    Returns:
        Tag string: "energy-{level}"
    """
    return f"energy-{energy.lower()}"


def encode_complexity_tag(complexity: float) -> str:
    """
    Encode complexity score (0.0-1.0) as integer tag (0-10).

    Args:
        complexity: Float 0.0-1.0

    Returns:
        Tag string: "complexity-{0-10}"
    """
    complexity_int = int(complexity * 10)
    complexity_int = max(0, min(10, complexity_int))  # Clamp to [0, 10]
    return f"complexity-{complexity_int}"


def encode_priority_tag(priority: int) -> str:
    """
    Encode priority (1-5) as tag.

    Args:
        priority: Integer 1-5

    Returns:
        Tag string: "priority-{1-5}"
    """
    priority = max(1, min(5, priority))  # Clamp to [1, 5]
    return f"priority-{priority}"


def encode_agent_tag(agent_type: str) -> str:
    """
    Encode agent assignment as tag.

    Args:
        agent_type: Agent type value (e.g., "zen", "serena")

    Returns:
        Tag string: "agent-{type}"
    """
    return f"agent-{agent_type.lower()}"


def encode_all_adhd_tags(task: OrchestrationTask) -> List[str]:
    """
    Encode all ADHD metadata from OrchestrationTask as tags.

    Args:
        task: OrchestrationTask with ADHD metadata

    Returns:
        List of standardized ADHD tags
    """
    tags = [
        "task-orchestrator",  # Source system
        encode_energy_tag(task.energy_required),
        encode_complexity_tag(task.complexity_score),
        encode_priority_tag(task.priority)
    ]

    # Optional: Add agent tag if assigned
    if task.assigned_agent:
        tags.append(encode_agent_tag(task.assigned_agent.value))

    # Optional: Add leantime sync tag
    if task.leantime_id:
        tags.append("leantime-synced")

    return tags


# ============================================================================
# ADHD Tag Decoding (Parse from Tags)
# ============================================================================

def decode_energy_tag(tag: str) -> Optional[str]:
    """
    Decode energy tag to energy level.

    Args:
        tag: Tag string

    Returns:
        Energy level ("low", "medium", "high") or None if not energy tag
    """
    if tag.startswith("energy-"):
        return tag.split("-", 1)[1]
    return None


def decode_complexity_tag(tag: str) -> Optional[float]:
    """
    Decode complexity tag (0-10) to score (0.0-1.0).

    Args:
        tag: Tag string

    Returns:
        Complexity float 0.0-1.0, or None if not complexity tag
    """
    if tag.startswith("complexity-"):
        try:
            complexity_int = int(tag.split("-")[1])
            return complexity_int / 10.0
        except (ValueError, IndexError):
            return None
    return None


def decode_priority_tag(tag: str) -> Optional[int]:
    """
    Decode priority tag to priority value.

    Args:
        tag: Tag string

    Returns:
        Priority integer 1-5, or None if not priority tag
    """
    if tag.startswith("priority-"):
        try:
            return int(tag.split("-")[1])
        except (ValueError, IndexError):
            return None
    return None


def decode_agent_tag(tag: str) -> Optional[str]:
    """
    Decode agent assignment tag.

    Args:
        tag: Tag string

    Returns:
        Agent type string or None if not agent tag
    """
    if tag.startswith("agent-"):
        return tag.split("-", 1)[1]
    return None


def decode_all_adhd_tags(tags: List[str]) -> Dict[str, Any]:
    """
    Decode all ADHD metadata from tag list.

    Args:
        tags: List of tags from ConPort progress_entry

    Returns:
        Dict with decoded ADHD metadata (uses defaults for missing tags)
    """
    adhd_metadata = {
        "energy_required": "medium",  # default
        "complexity_score": 0.5,      # default
        "priority": 3,                # default
        "assigned_agent": None,       # default
        "is_leantime_synced": False   # default
    }

    for tag in tags:
        # Try each decoder
        energy = decode_energy_tag(tag)
        if energy:
            adhd_metadata["energy_required"] = energy

        complexity = decode_complexity_tag(tag)
        if complexity is not None:
            adhd_metadata["complexity_score"] = complexity

        priority = decode_priority_tag(tag)
        if priority is not None:
            adhd_metadata["priority"] = priority

        agent = decode_agent_tag(tag)
        if agent:
            adhd_metadata["assigned_agent"] = agent

        # Check for leantime sync
        if tag == "leantime-synced":
            adhd_metadata["is_leantime_synced"] = True

    return adhd_metadata


# ============================================================================
# Description Formatting (Display Metadata)
# ============================================================================

def build_task_description(
    title: str,
    description: str,
    estimated_minutes: int,
    complexity_score: float,
    energy_required: str
) -> str:
    """
    Build rich task description with embedded metadata.

    Format: "Title | Description | Duration: Xm | Complexity: Y.Z | Energy: {level}"

    Args:
        title: Task title
        description: Task description
        estimated_minutes: Duration estimate
        complexity_score: Complexity 0.0-1.0
        energy_required: Energy level

    Returns:
        Formatted description string
    """
    parts = [
        title,
        description if description else "",
        f"Duration: {estimated_minutes}m",
        f"Complexity: {complexity_score}",
        f"Energy: {energy_required}"
    ]
    return " | ".join(p for p in parts if p)


def parse_task_description(description: str) -> Dict[str, Any]:
    """
    Parse task description to extract embedded metadata.

    Args:
        description: Formatted description string

    Returns:
        Dict with parsed fields (title, description, duration, complexity, energy)
    """
    parts = description.split(" | ")

    parsed = {
        "title": parts[0] if len(parts) > 0 else "Unknown Task",
        "description": parts[1] if len(parts) > 1 else "",
        "estimated_minutes": 25,      # default
        "complexity_score": 0.5,      # default
        "energy_required": "medium"   # default
    }

    # Parse metadata from remaining parts
    for part in parts[2:]:
        if part.startswith("Duration: "):
            try:
                parsed["estimated_minutes"] = int(part.replace("Duration: ", "").replace("m", ""))
            except ValueError:
                pass  # Keep default

        elif part.startswith("Complexity: "):
            try:
                parsed["complexity_score"] = float(part.replace("Complexity: ", ""))
            except ValueError:
                pass  # Keep default

        elif part.startswith("Energy: "):
            parsed["energy_required"] = part.replace("Energy: ", "")

    return parsed


# ============================================================================
# Status Mapping
# ============================================================================

# Status mapping constants
TASK_STATUS_TO_CONPORT_STATUS = {
    TaskStatus.PENDING: "TODO",
    TaskStatus.IN_PROGRESS: "IN_PROGRESS",
    TaskStatus.COMPLETED: "DONE",
    TaskStatus.BLOCKED: "BLOCKED",
    TaskStatus.NEEDS_BREAK: "IN_PROGRESS",      # Lossy: ConPort doesn't have NEEDS_BREAK
    TaskStatus.CONTEXT_SWITCH: "IN_PROGRESS",   # Lossy: Treated as in-progress
    TaskStatus.PAUSED: "BLOCKED"                # Lossy: Paused = temporarily blocked
}

CONPORT_STATUS_TO_TASK_STATUS = {
    "TODO": TaskStatus.PENDING,
    "IN_PROGRESS": TaskStatus.IN_PROGRESS,
    "DONE": TaskStatus.COMPLETED,
    "BLOCKED": TaskStatus.BLOCKED
}


def map_task_status_to_conport(status: TaskStatus) -> str:
    """Map TaskStatus enum to ConPort status string."""
    return TASK_STATUS_TO_CONPORT_STATUS.get(status, "TODO")


def map_conport_status_to_task(status: str) -> TaskStatus:
    """Map ConPort status string to TaskStatus enum."""
    return CONPORT_STATUS_TO_TASK_STATUS.get(status, TaskStatus.PENDING)


# ============================================================================
# Dependency Mapping
# ============================================================================

def extract_conport_id_from_task_id(task_id: str) -> Optional[int]:
    """
    Extract ConPort progress_entry ID from OrchestrationTask ID.

    Handles format: "conport-{id}" → {id}

    Args:
        task_id: OrchestrationTask.id (may be "conport-123" or custom format)

    Returns:
        ConPort progress_entry ID or None if not in expected format
    """
    if task_id.startswith("conport-"):
        try:
            return int(task_id.split("-", 1)[1])
        except (ValueError, IndexError):
            logger.warning(f"Invalid conport task_id format: {task_id}")
            return None
    return None


def build_dependency_links(
    task: OrchestrationTask,
    all_tasks: List[OrchestrationTask]
) -> List[Dict[str, Any]]:
    """
    Build ConPort link_conport_items calls for task dependencies.

    Args:
        task: OrchestrationTask with dependencies populated
        all_tasks: All available OrchestrationTask objects (for ID lookup)

    Returns:
        List of link specs ready for ConPort link_conport_items() calls
    """
    if not hasattr(task, 'conport_id') or task.conport_id is None:
        logger.warning(f"Task {task.id} has no conport_id, cannot build dependency links")
        return []

    link_specs = []

    for dependency_id in task.dependencies:
        # Find the dependency task
        dep_task = next((t for t in all_tasks if t.id == dependency_id), None)

        if not dep_task:
            logger.warning(f"Dependency task not found: {dependency_id}")
            continue

        if not hasattr(dep_task, 'conport_id') or dep_task.conport_id is None:
            logger.warning(f"Dependency task {dependency_id} has no conport_id")
            continue

        # Build link spec
        link_spec = {
            "source_item_id": task.conport_id,
            "target_item_id": dep_task.conport_id,
            "relationship_type": "depends_on",
            "description": f"Task {task.id} depends on {dependency_id}"
        }
        link_specs.append(link_spec)

    return link_specs


# ============================================================================
# Query Helpers
# ============================================================================

def build_adhd_query_tags(
    min_energy: Optional[str] = None,
    max_complexity: Optional[float] = None,
    min_priority: Optional[int] = None
) -> List[str]:
    """
    Build tag list for querying ConPort with ADHD filters.

    Example: Find all low-energy, low-complexity tasks:
        tags = build_adhd_query_tags(min_energy="low", max_complexity=0.4)
        # Returns: ["energy-low", "complexity-0", "complexity-1", "complexity-2", "complexity-3", "complexity-4"]

    Args:
        min_energy: Minimum energy level filter
        max_complexity: Maximum complexity filter (0.0-1.0)
        min_priority: Minimum priority filter

    Returns:
        List of tags for ConPort query
    """
    query_tags = ["task-orchestrator"]  # Always filter to task-orchestrator items

    # Energy filter
    if min_energy:
        query_tags.append(encode_energy_tag(min_energy))

    # Complexity filter (expand to range for max)
    if max_complexity is not None:
        max_complexity_int = int(max_complexity * 10)
        for i in range(0, max_complexity_int + 1):
            query_tags.append(f"complexity-{i}")

    # Priority filter (expand to range for min)
    if min_priority is not None:
        for i in range(min_priority, 6):  # 1-5, so 6 is upper bound
            query_tags.append(f"priority-{i}")

    return query_tags


def filter_tasks_by_adhd_criteria(
    tasks: List[OrchestrationTask],
    energy_level: Optional[str] = None,
    max_complexity: Optional[float] = None,
    min_priority: Optional[int] = None
) -> List[OrchestrationTask]:
    """
    Filter OrchestrationTask list by ADHD criteria.

    Useful for client-side filtering when ConPort query limitations exist.

    Args:
        tasks: List of OrchestrationTask objects
        energy_level: Filter to specific energy level
        max_complexity: Filter to complexity <= threshold
        min_priority: Filter to priority >= threshold

    Returns:
        Filtered task list
    """
    filtered = tasks

    if energy_level:
        filtered = [t for t in filtered if t.energy_required == energy_level]

    if max_complexity is not None:
        filtered = [t for t in filtered if t.complexity_score <= max_complexity]

    if min_priority is not None:
        filtered = [t for t in filtered if t.priority >= min_priority]

    return filtered


# ============================================================================
# Validation Utilities
# ============================================================================

def validate_adhd_metadata(task: OrchestrationTask) -> Tuple[bool, List[str]]:
    """
    Validate OrchestrationTask ADHD metadata.

    Args:
        task: OrchestrationTask to validate

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []

    # Validate energy level
    if task.energy_required not in ["low", "medium", "high"]:
        errors.append(f"Invalid energy_required: {task.energy_required} (must be low/medium/high)")

    # Validate complexity score
    if not (0.0 <= task.complexity_score <= 1.0):
        errors.append(f"Invalid complexity_score: {task.complexity_score} (must be 0.0-1.0)")

    # Validate priority
    if not (1 <= task.priority <= 5):
        errors.append(f"Invalid priority: {task.priority} (must be 1-5)")

    # Validate cognitive load matches complexity
    if hasattr(task, 'cognitive_load') and task.cognitive_load != task.complexity_score:
        errors.append(f"cognitive_load ({task.cognitive_load}) should equal complexity_score ({task.complexity_score})")

    # Validate estimated minutes is reasonable
    if task.estimated_minutes < 1:
        errors.append(f"Invalid estimated_minutes: {task.estimated_minutes} (must be >= 1)")

    is_valid = len(errors) == 0
    return is_valid, errors


def validate_conport_progress_data(progress_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate ConPort progress_entry data before sending.

    Args:
        progress_data: Dict ready for mcp__conport__log_progress()

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []

    # Required fields
    required_fields = ["workspace_id", "status", "description", "tags"]
    for field in required_fields:
        if field not in progress_data:
            errors.append(f"Missing required field: {field}")

    # Validate workspace_id is absolute path
    if "workspace_id" in progress_data:
        if not progress_data["workspace_id"].startswith("/"):
            errors.append(f"workspace_id must be absolute path, got: {progress_data['workspace_id']}")

    # Validate status
    if "status" in progress_data:
        valid_statuses = ["TODO", "IN_PROGRESS", "DONE", "BLOCKED"]
        if progress_data["status"] not in valid_statuses:
            errors.append(f"Invalid status: {progress_data['status']} (must be one of {valid_statuses})")

    # Validate tags is list
    if "tags" in progress_data:
        if not isinstance(progress_data["tags"], list):
            errors.append(f"tags must be list, got: {type(progress_data['tags'])}")
        elif len(progress_data["tags"]) == 0:
            errors.append("tags list is empty (should include at least 'task-orchestrator')")

    # Validate description is not empty
    if "description" in progress_data:
        if not progress_data["description"] or len(progress_data["description"].strip()) == 0:
            errors.append("description cannot be empty")

    is_valid = len(errors) == 0
    return is_valid, errors


# ============================================================================
# Batch Mapping Utilities
# ============================================================================

def batch_encode_tasks_to_progress(
    tasks: List[OrchestrationTask],
    workspace_id: str
) -> List[Optional[Dict[str, Any]]]:
    """
    Batch transform OrchestrationTask list to ConPort progress_entry format.

    Uses safe transformation (returns None for invalid tasks).

    Args:
        tasks: List of OrchestrationTask objects
        workspace_id: Workspace ID for all tasks

    Returns:
        List of progress_entry dicts (None for failed transformations)
    """
    # Import here to avoid circular dependency
    from .conport_adapter import safe_orchestration_task_to_conport_progress

    progress_list = []
    for task in tasks:
        progress_data = safe_orchestration_task_to_conport_progress(task, workspace_id)
        progress_list.append(progress_data)

    successful = sum(1 for p in progress_list if p is not None)
    logger.info(f"✅ Batch encoded {successful}/{len(tasks)} tasks")

    return progress_list


def batch_decode_progress_to_tasks(
    progress_entries: List[Dict[str, Any]]
) -> List[Optional[OrchestrationTask]]:
    """
    Batch transform ConPort progress_entry list to OrchestrationTask format.

    Uses safe transformation (returns None for invalid entries).

    Args:
        progress_entries: List of ConPort progress_entry dicts

    Returns:
        List of OrchestrationTask objects (None for failed transformations)
    """
    # Import here to avoid circular dependency
    from .conport_adapter import safe_conport_progress_to_orchestration_task

    tasks = []
    for progress in progress_entries:
        task = safe_conport_progress_to_orchestration_task(progress)
        tasks.append(task)

    successful = sum(1 for t in tasks if t is not None)
    logger.info(f"✅ Batch decoded {successful}/{len(progress_entries)} progress entries")

    return tasks


# ============================================================================
# ConPort Query Builders
# ============================================================================

def build_get_ready_tasks_query() -> Dict[str, Any]:
    """
    Build query parameters for ConPort to get all ready-to-start tasks.

    Ready tasks: status=TODO, no dependencies (or all dependencies DONE)

    Returns:
        Query parameters dict
    """
    return {
        "status_filter": "TODO",
        "tags_filter": ["task-orchestrator"]
    }


def build_get_high_energy_tasks_query() -> Dict[str, Any]:
    """
    Build query for high-energy tasks (for when developer has focus time).

    Returns:
        Query parameters dict
    """
    return {
        "status_filter": "TODO",
        "tags_filter": ["task-orchestrator", "energy-high"]
    }


def build_get_low_complexity_tasks_query() -> Dict[str, Any]:
    """
    Build query for low-complexity tasks (complexity <= 0.4).

    Good for scattered attention or end-of-day work.

    Returns:
        Query parameters dict
    """
    low_complexity_tags = ["task-orchestrator"]
    # Add all complexity tags 0-4 (0.0-0.4)
    for i in range(0, 5):
        low_complexity_tags.append(f"complexity-{i}")

    return {
        "status_filter": "TODO",
        "tags_filter": low_complexity_tags
    }
