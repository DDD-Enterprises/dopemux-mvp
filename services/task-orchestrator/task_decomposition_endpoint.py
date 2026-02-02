"""
Task Decomposition API Endpoint for Task Orchestrator

Handles decomposition requests from ADHD Engine.
Calls Pal planner, persists to ConPort, syncs to Leantime.
"""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DecompositionRequest(BaseModel):
    """Request to decompose a task."""
    task_id: str = Field(..., description="Task ID to decompose")
    adhd_context: Dict[str, Any] = Field(
        ...,
        description="Current ADHD state (energy, attention, cognitive_load)"
    )
    method: str = Field(
        default="pal",
        description="Decomposition method: 'pal' (AI) or 'pattern' (rule-based)"
    )
    max_subtasks: int = Field(
        default=7,
        ge=3,
        le=10,
        description="Maximum number of subtasks to generate"
    )
    target_duration_minutes: int = Field(
        default=15,
        ge=5,
        le=30,
        description="Target duration per subtask in minutes"
    )
    timestamp: Optional[str] = Field(
        default=None,
        description="Request timestamp"
    )


class DecompositionResponse(BaseModel):
    """Response from task decomposition."""
    parent_task_id: str
    subtask_ids: List[str]
    subtasks: List[Dict[str, Any]]
    total_estimated_minutes: int
    break_points: List[str] = Field(default_factory=list)
    schedule: Optional[Dict[str, Any]] = None
    method: str
    leantime_synced: bool = False
    conport_persisted: bool = False
    timestamp: str


async def handle_decomposition_request(
    request: DecompositionRequest,
    task_coordinator,  # TaskCoordinator instance
    pal_client,  # TaskOrchestratorPALClient instance
    leantime_client,  # LeantimeClient instance
    conport_adapter,  # ConPortEventAdapter instance (via DopeconBridge)
    workspace_id: str
) -> DecompositionResponse:
    """
    Handle task decomposition request from ADHD Engine.
    
    Flow:
    1. Get task from internal storage
    2. Call Pal planner for AI decomposition (or use pattern fallback)
    3. Convert to OrchestrationTask objects
    4. Persist to ConPort (parent BLOCKED, subtasks TODO, DECOMPOSED_INTO links)
    5. Sync to Leantime (create child tickets)
    6. Schedule based on ADHD state
    7. Return structured breakdown
    
    Args:
        request: Decomposition request from ADHD Engine
        task_coordinator: TaskCoordinator instance
        pal_client: Pal planner client
        leantime_client: Leantime API client
        conport_adapter: ConPort adapter for persistence
        workspace_id: Current workspace ID
    
    Returns:
        Decomposition response with subtasks and metadata
    
    Raises:
        ValueError: If task not found or decomposition fails
        RuntimeError: If Pal planner or ConPort unavailable
    """
    logger.info(
        f"Decomposition request for task {request.task_id} "
        f"via {request.method} method"
    )
    
    # 1. Get original task
    task = await task_coordinator.get_task(request.task_id)
    if not task:
        raise ValueError(f"Task {request.task_id} not found in Task Orchestrator")
    
    # 2. Call Pal planner for AI decomposition
    if request.method == "pal":
        logger.info(f"Calling Pal planner for task {request.task_id}")
        try:
            pal_breakdown = await pal_client.plan_task_breakdown(
                complex_task={
                    'id': task.id,
                    'description': task.description,
                    'complexity': getattr(task, 'complexity_score', 0.5),
                    'estimated_minutes': task.estimated_minutes
                },
                context=request.adhd_context
            )
        except Exception as e:
            logger.error(f"Pal planner failed: {e}, falling back to pattern method")
            # Fallback to pattern-based (ADHD Engine would provide this)
            # For now, generate simple breakdown
            pal_breakdown = {
                'subtasks': [
                    {
                        'name': f"Subtask {i+1}",
                        'description': f"Part {i+1} of {task.description}",
                        'duration_minutes': request.target_duration_minutes,
                        'dependencies': [],
                        'adhd_accommodations': []
                    }
                    for i in range(min(request.max_subtasks, 5))
                ],
                'execution_order': [f"subtask{i+1}" for i in range(5)],
                'total_duration': request.target_duration_minutes * 5,
                'break_points': ["after subtask2", "after subtask4"],
                'progress_checkpoints': [],
                'confidence': 0.5
            }
    else:
        # Pattern-based fallback (simple split)
        logger.info(f"Using pattern-based decomposition for task {request.task_id}")
        estimated_total = task.estimated_minutes
        num_subtasks = min(
            request.max_subtasks,
            max(3, estimated_total // request.target_duration_minutes)
        )
        
        pal_breakdown = {
            'subtasks': [
                {
                    'name': f"Part {i+1}",
                    'description': f"Part {i+1} of {task.description}",
                    'duration_minutes': estimated_total // num_subtasks,
                    'dependencies': [f"subtask{i}"] if i > 0 else [],
                    'adhd_accommodations': ["15min chunks", "clear goal"]
                }
                for i in range(num_subtasks)
            ],
            'execution_order': [f"subtask{i+1}" for i in range(num_subtasks)],
            'total_duration': estimated_total,
            'break_points': [
                f"after subtask{i+1}"
                for i in range(0, num_subtasks, 2)
            ],
            'progress_checkpoints': [],
            'confidence': 0.7
        }
    
    # 3. Convert to OrchestrationTask objects
    from task_orchestrator.models import OrchestrationTask, TaskStatus
    
    subtasks = []
    for idx, subtask_data in enumerate(pal_breakdown.get('subtasks', [])):
        subtask = OrchestrationTask(
            id=f"{task.id}_sub_{idx+1}",
            description=subtask_data['description'],
            complexity_score=subtask_data.get('complexity_score', 0.3),
            estimated_minutes=subtask_data['duration_minutes'],
            dependencies=subtask_data.get('dependencies', []),
            status=TaskStatus.PENDING,
            parent_task_id=task.id,
            order=idx,
            energy_required=_map_duration_to_energy(subtask_data['duration_minutes'])
        )
        subtasks.append(subtask)
    
    subtask_ids = [st.id for st in subtasks]
    
    logger.info(f"Created {len(subtasks)} subtasks for task {request.task_id}")
    
    # 4. Persist to ConPort
    conport_persisted = False
    try:
        logger.info(f"Persisting decomposition to ConPort for task {request.task_id}")
        
        # Update parent task status to BLOCKED
        await conport_adapter.update_progress_entry(
            entry_id=task.id,
            status="BLOCKED",
            metadata={
                'decomposed': True,
                'decomposition_method': request.method,
                'original_estimate': task.estimated_minutes,
                'num_subtasks': len(subtasks),
                'timestamp': datetime.now().isoformat()
            }
        )
        
        # Create subtask progress entries
        for subtask in subtasks:
            subtask_entry = await conport_adapter.create_progress_entry(
                workspace_id=workspace_id,
                description=subtask.description,
                status="TODO",
                metadata={
                    'parent_task_id': task.id,
                    'order': subtask.order,
                    'estimated_minutes': subtask.estimated_minutes,
                    'energy_required': subtask.energy_required,
                    'dependencies': subtask.dependencies
                }
            )
            
            # Link to parent (DECOMPOSED_INTO relationship)
            await conport_adapter.link_items(
                source_item_type="progress_entry",
                source_item_id=task.id,
                target_item_type="progress_entry",
                target_item_id=subtask_entry['id'],
                relationship_type="DECOMPOSED_INTO"
            )
        
        conport_persisted = True
        logger.info(f"Decomposition persisted to ConPort successfully")
    
    except Exception as e:
        logger.error(f"Failed to persist decomposition to ConPort: {e}")
        # Continue anyway - persistence is important but not critical for initial UX
    
    # 5. Sync to Leantime (create child tickets)
    leantime_synced = False
    if hasattr(task, 'leantime_id') and task.leantime_id and leantime_client:
        try:
            logger.info(f"Syncing decomposition to Leantime for task {request.task_id}")
            
            for subtask in subtasks:
                leantime_ticket = await leantime_client.create_ticket(
                    project_id=getattr(task, 'project_id', None),
                    headline=subtask.description,
                    planHours=subtask.estimated_minutes / 60.0,
                    parent_id=task.leantime_id,
                    tags=["decomposed", f"order:{subtask.order}"]
                )
                
                # Store Leantime ID for future sync
                subtask.leantime_id = leantime_ticket.get('id')
                logger.debug(f"Created Leantime ticket {subtask.leantime_id} for subtask {subtask.id}")
            
            # Update parent ticket metadata
            await leantime_client.update_ticket(
                ticket_id=task.leantime_id,
                tags=["decomposed", f"subtasks:{len(subtasks)}"],
                metadata={"decomposition_method": request.method}
            )
            
            leantime_synced = True
            logger.info(f"Decomposition synced to Leantime successfully")
        
        except Exception as e:
            logger.error(f"Failed to sync decomposition to Leantime: {e}")
            # Continue anyway - Leantime sync is optional
    else:
        logger.debug(f"Task {request.task_id} has no Leantime ID, skipping sync")
    
    # 6. Schedule based on ADHD state
    schedule = None
    try:
        schedule = await task_coordinator.schedule_subtasks(
            subtasks,
            request.adhd_context
        )
        logger.info(f"Generated ADHD-aware schedule for subtasks")
    except Exception as e:
        logger.warning(f"Failed to generate schedule: {e}")
    
    # 7. Return structured breakdown
    response = DecompositionResponse(
        parent_task_id=task.id,
        subtask_ids=subtask_ids,
        subtasks=[_subtask_to_dict(st) for st in subtasks],
        total_estimated_minutes=sum(st.estimated_minutes for st in subtasks),
        break_points=pal_breakdown.get('break_points', []),
        schedule=schedule,
        method=request.method,
        leantime_synced=leantime_synced,
        conport_persisted=conport_persisted,
        timestamp=datetime.now().isoformat()
    )
    
    logger.info(
        f"Decomposition complete for task {request.task_id}: "
        f"{len(subtasks)} subtasks, {response.total_estimated_minutes}min total"
    )
    
    return response


def _map_duration_to_energy(duration_minutes: int) -> str:
    """Map subtask duration to energy requirement."""
    if duration_minutes <= 10:
        return "low"
    elif duration_minutes <= 20:
        return "medium"
    else:
        return "high"


def _subtask_to_dict(subtask) -> Dict[str, Any]:
    """Convert OrchestrationTask to dict for API response."""
    return {
        "id": subtask.id,
        "description": subtask.description,
        "estimated_minutes": subtask.estimated_minutes,
        "energy_required": getattr(subtask, 'energy_required', 'medium'),
        "order": getattr(subtask, 'order', 0),
        "dependencies": subtask.dependencies if hasattr(subtask, 'dependencies') else [],
        "status": subtask.status.value if hasattr(subtask.status, 'value') else str(subtask.status),
        "parent_task_id": getattr(subtask, 'parent_task_id', None),
        "leantime_id": getattr(subtask, 'leantime_id', None)
    }
