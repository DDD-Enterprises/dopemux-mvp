from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum

class PlaneType(str, Enum):
    PROJECT_MANAGEMENT = "pm"
    COGNITIVE = "cognitive"
    INTEGRATION = "integration"

class CoordinationEventType(str, Enum):
    TASK_CREATED = "task_created"
    TASK_UPDATED = "task_updated"
    TASK_COMPLETED = "task_completed"
    DECISION_MADE = "decision_made"
    PROGRESS_UPDATED = "progress_updated"
    CONFLICT_DETECTED = "conflict_detected"
    BREAK_RECOMMENDED = "break_recommended"
    CONTEXT_SWITCH = "context_switch"
    HEALTH_CHECK = "health_check"
    SYNC_COMPLETED = "sync_completed"

class ConflictResolutionStrategy(str, Enum):
    PM_WINS = "pm_wins"
    COGNITIVE_WINS = "cognitive_wins"
    MERGE_INTELLIGENT = "merge_intelligent"
    ASK_USER = "ask_user"
    LAST_MODIFIED = "last_modified"
    CONSENSUS = "consensus"

class CoordinationOperationRequest(BaseModel):
    operation: str
    source_plane: str
    data: Dict[str, Any]
    priority: int = 5

class CoordinationOperationResponse(BaseModel):
    success: bool
    operation_id: Optional[str] = None
    result: Dict[str, Any]
    timestamp: datetime

class PlaneHealthResponse(BaseModel):
    plane: str
    status: str
    last_check: datetime
    services: Dict[str, str]
    issues: List[str] = []
    metrics: Dict[str, Any] = {}

class CoordinationMetricsResponse(BaseModel):
    events_processed: int
    conflicts_detected: int
    conflicts_resolved: int
    sync_operations: int
    health_checks: int
    timestamp: datetime

class EmitEventRequest(BaseModel):
    event_type: str
    source_plane: str
    target_plane: str
    entity_type: str
    entity_id: str
    data: Dict[str, Any]
    priority: int = 5

class ConflictResolutionRequest(BaseModel):
    resolution_strategy: str
    resolved_value: Optional[Any] = None

class HealthResponse(BaseModel):
    service: str
    status: str
    ts: str
    dependencies: Dict[str, str]
