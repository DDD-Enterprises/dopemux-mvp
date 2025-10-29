"""
DDDPG - Dope Data & Decisions Graph Portal
Core data models - PRODUCTION READY with multi-instance support
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class DecisionStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"


class DecisionType(str, Enum):
    ARCHITECTURE = "architecture"
    IMPLEMENTATION = "implementation"
    TOOLING = "tooling"
    PROCESS = "process"
    REFACTOR = "refactor"
    ADHD = "adhd"
    OTHER = "other"


class DecisionVisibility(str, Enum):
    """Multi-instance visibility control"""
    PRIVATE = "private"    # Only this instance
    SHARED = "shared"      # All instances in workspace
    GLOBAL = "global"      # All workspaces


class RelationshipType(str, Enum):
    """Typed graph relationships"""
    SUPERSEDES = "supersedes"
    IMPLEMENTS = "implements"
    RELATES_TO = "relates_to"
    CONTRADICTS = "contradicts"
    REQUIRES = "requires"
    SUGGESTS = "suggests"


class Decision(BaseModel):
    """
    Core decision model - ADHD-optimized with multi-instance support
    
    Multi-Instance:
    - workspace_id: Main workspace root (e.g., /dopemux-mvp)
    - instance_id: Specific instance (e.g., "A", "feature-auth")
    - visibility: Who can see this decision
    
    Graph:
    - related_decisions: Connected decision IDs
    - relationships stored separately in DecisionRelationship
    
    ADHD:
    - cognitive_load: Complexity rating 1-5
    - agent_metadata: Flexible extensions for agents
    """
    
    # Identity
    id: Optional[int] = None
    
    # Core content
    summary: str = Field(..., max_length=200, description="One-sentence summary")
    rationale: Optional[str] = Field(None, max_length=1000, description="Why this decision")
    implementation_details: Optional[str] = None
    
    # Classification
    status: DecisionStatus = DecisionStatus.ACTIVE
    decision_type: Optional[DecisionType] = None
    tags: List[str] = Field(default_factory=list)
    
    # Multi-instance support (CRITICAL!)
    workspace_id: str = Field(..., description="Main workspace root path")
    instance_id: str = Field(default="A", description="Instance identifier (A, B, feature-auth, etc)")
    visibility: DecisionVisibility = DecisionVisibility.SHARED
    
    # Multi-tenancy (optional auth mode)
    user_id: Optional[str] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
    # Graph relationships
    related_decisions: List[int] = Field(default_factory=list, description="Related decision IDs")
    code_references: List[str] = Field(default_factory=list, description="File paths mentioned")
    
    # ADHD optimization
    cognitive_load: Optional[int] = Field(None, ge=1, le=5, description="Complexity 1-5")
    
    # Agent extensions (flexible!)
    agent_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Agent-specific data (serena, task-orchestrator, zen, etc)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "summary": "Use DDDPG for all context management",
                "rationale": "One unified system beats 3 fragmented ones",
                "workspace_id": "/Users/hue/code/dopemux-mvp",
                "instance_id": "A",
                "visibility": "shared",
                "tags": ["architecture", "dddpg"],
                "decision_type": "architecture",
                "cognitive_load": 4,
                "agent_metadata": {
                    "serena": {"hover_count": 0},
                    "task_orchestrator": {"status": "DONE", "priority": 5}
                }
            }
        }


class DecisionRelationship(BaseModel):
    """
    Typed graph relationship between decisions
    Stored as edges in PostgreSQL AGE
    """
    
    from_decision_id: int = Field(..., description="Source decision")
    to_decision_id: int = Field(..., description="Target decision")
    relationship_type: RelationshipType
    
    # Relationship metadata
    weight: float = Field(1.0, ge=0.0, le=1.0, description="Strength of relationship")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = Field(None, description="User or agent ID")
    
    # Flexible metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_schema_extra = {
            "example": {
                "from_decision_id": 10,
                "to_decision_id": 5,
                "relationship_type": "implements",
                "weight": 0.9,
                "created_by": "task-orchestrator"
            }
        }


class WorkSession(BaseModel):
    """
    ADHD-optimized work session tracking
    Tracks focus, context, and break needs
    """
    
    # Identity
    session_id: str = Field(..., description="Unique session ID")
    
    # Multi-instance context
    workspace_id: str
    instance_id: str = Field(default="A")
    
    # Session state
    started_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None
    
    # ADHD tracking
    focus_level: Optional[int] = Field(None, ge=1, le=5, description="Current focus 1-5")
    break_needed: bool = False
    context_preserved: bool = True
    
    # Active context
    current_file: Optional[str] = None
    current_decisions: List[int] = Field(default_factory=list)
    
    # Session metadata
    total_decisions_created: int = 0
    total_decisions_viewed: int = 0
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "session_20251029_014900",
                "workspace_id": "/Users/hue/code/dopemux-mvp",
                "instance_id": "A",
                "focus_level": 4,
                "current_file": "services/dddpg/core/models.py",
                "current_decisions": [1, 2, 3]
            }
        }


class DecisionGraph(BaseModel):
    """
    Graph query result containing nodes and edges
    Used for graph traversal queries
    """
    
    nodes: List[Decision] = Field(default_factory=list)
    edges: List[DecisionRelationship] = Field(default_factory=list)
    
    # Query metadata
    query_type: str = Field(..., description="overview, exploration, deep")
    depth: int = Field(1, ge=1, le=3)
    total_nodes: int = 0
    execution_time_ms: Optional[float] = None


# Export all models
__all__ = [
    "Decision",
    "DecisionStatus",
    "DecisionType",
    "DecisionVisibility",
    "DecisionRelationship",
    "RelationshipType",
    "WorkSession",
    "DecisionGraph",
]
