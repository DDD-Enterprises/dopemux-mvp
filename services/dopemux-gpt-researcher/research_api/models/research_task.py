"""
Research Task State Machine - Core model for ADHD-optimized research

This module implements the state machine that enables:
- Pause/resume capability for context switching
- Progress tracking for transparency
- Session persistence via ConPort
- Checkpoint system for recovery
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    """Research task status states"""
    PLANNING = "planning"
    REVIEWING = "reviewing"
    EXECUTING = "executing"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class ResearchType(str, Enum):
    """Different types of research with specialized workflows"""
    FEATURE_RESEARCH = "feature_research"
    SYSTEM_ARCHITECTURE = "system_architecture"
    BUG_INVESTIGATION = "bug_investigation"
    TECHNOLOGY_EVALUATION = "technology_evaluation"
    DOCUMENTATION_RESEARCH = "documentation_research"
    COMPETITIVE_ANALYSIS = "competitive_analysis"


class ADHDConfiguration(BaseModel):
    """ADHD-specific settings for research experience"""
    pomodoro_enabled: bool = True
    work_duration_minutes: int = 25
    break_duration_minutes: int = 5
    max_concurrent_sources: int = 5
    progressive_disclosure: bool = True
    auto_save_interval_seconds: int = 30
    gentle_notifications: bool = True
    visual_progress_enabled: bool = True


class ResearchQuestion(BaseModel):
    """Individual research question within a plan"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    question: str
    priority: int = 1
    estimated_duration_minutes: int = 5
    status: TaskStatus = TaskStatus.PLANNING
    sources_found: int = 0
    confidence_score: float = 0.0


class ResearchResult(BaseModel):
    """Result from executing a research question"""
    question_id: str
    answer: str
    sources: List[Dict[str, Any]] = []
    confidence: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.now)
    search_engines_used: List[str] = []
    processing_time_seconds: float = 0.0


class SessionSnapshot(BaseModel):
    """Checkpoint for resuming interrupted sessions"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    task_id: UUID
    timestamp: datetime = Field(default_factory=datetime.now)
    current_question_index: int
    status: TaskStatus
    partial_results: Dict[str, Any] = {}
    context_data: Dict[str, Any] = {}
    recovery_instructions: str = ""


class ProjectContext(BaseModel):
    """Project-specific context for research enhancement"""
    workspace_path: str
    tech_stack: List[str] = []
    architecture_patterns: List[str] = []
    recent_decisions: List[Dict[str, Any]] = []
    uploaded_files: List[str] = []
    github_repo: Optional[str] = None
    documentation_links: List[str] = []


class ResearchTask(BaseModel):
    """
    Main research task model with ADHD optimizations

    This model supports:
    - State machine for pause/resume
    - Progress tracking for transparency
    - Context preservation for interruptions
    - Checkpoint system for recovery
    """

    # Core identifiers
    id: UUID = Field(default_factory=uuid4)
    user_id: str

    # Research definition
    initial_prompt: str
    enhanced_prompt: Optional[str] = None
    research_type: ResearchType

    # State management
    status: TaskStatus = TaskStatus.PLANNING
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Research plan and execution
    research_plan: List[ResearchQuestion] = []
    current_question_index: int = 0
    results: Dict[str, ResearchResult] = {}

    # ADHD features
    adhd_config: ADHDConfiguration = Field(default_factory=ADHDConfiguration)
    session_snapshots: List[SessionSnapshot] = []

    # Context and persistence
    project_context: Optional[ProjectContext] = None
    conport_links: List[str] = []  # Links to ConPort entries

    # Metadata
    total_processing_time: float = 0.0
    sources_discovered: int = 0
    confidence_score: float = 0.0
    metadata: Dict[str, Any] = {}  # Enhanced orchestration metadata

    def transition_to(self, new_status: TaskStatus) -> None:
        """Safe state transition with validation"""
        valid_transitions = {
            TaskStatus.PLANNING: [TaskStatus.REVIEWING, TaskStatus.FAILED],
            TaskStatus.REVIEWING: [TaskStatus.EXECUTING, TaskStatus.PLANNING, TaskStatus.FAILED],
            TaskStatus.EXECUTING: [TaskStatus.PAUSED, TaskStatus.COMPLETED, TaskStatus.FAILED],
            TaskStatus.PAUSED: [TaskStatus.EXECUTING, TaskStatus.FAILED],
            TaskStatus.COMPLETED: [],  # Terminal state
            TaskStatus.FAILED: [TaskStatus.PLANNING],  # Allow restart
        }

        if new_status not in valid_transitions[self.status]:
            raise ValueError(f"Invalid transition from {self.status} to {new_status}")

        self.status = new_status
        self.updated_at = datetime.now()

        # Set timestamps for key transitions
        if new_status == TaskStatus.EXECUTING and self.started_at is None:
            self.started_at = datetime.now()
        elif new_status == TaskStatus.COMPLETED:
            self.completed_at = datetime.now()

    def create_checkpoint(self, context_data: Dict[str, Any] = None) -> SessionSnapshot:
        """Create a checkpoint for recovery"""
        snapshot = SessionSnapshot(
            task_id=self.id,
            current_question_index=self.current_question_index,
            status=self.status,
            partial_results=dict(self.results),
            context_data=context_data or {},
            recovery_instructions=f"Resume from question {self.current_question_index + 1}"
        )

        self.session_snapshots.append(snapshot)
        return snapshot

    def get_current_question(self) -> Optional[ResearchQuestion]:
        """Get the currently active research question"""
        if self.current_question_index < len(self.research_plan):
            return self.research_plan[self.current_question_index]
        return None

    def advance_to_next_question(self) -> bool:
        """Move to next question, return True if more questions exist"""
        if self.current_question_index < len(self.research_plan) - 1:
            self.current_question_index += 1
            return True
        return False

    def calculate_progress(self) -> Dict[str, Any]:
        """Calculate research progress for UI display"""
        total_questions = len(self.research_plan)
        completed_questions = len(self.results)

        return {
            "total_questions": total_questions,
            "completed_questions": completed_questions,
            "current_question": self.current_question_index + 1,
            "progress_percentage": (completed_questions / total_questions * 100) if total_questions > 0 else 0,
            "estimated_remaining_minutes": sum(
                q.estimated_duration_minutes
                for q in self.research_plan[self.current_question_index:]
            ),
            "elapsed_time_minutes": (
                (datetime.now() - self.started_at).total_seconds() / 60
                if self.started_at else 0
            )
        }

    def should_suggest_break(self) -> bool:
        """Check if it's time for a Pomodoro break"""
        if not self.adhd_config.pomodoro_enabled or not self.started_at:
            return False

        elapsed_minutes = (datetime.now() - self.started_at).total_seconds() / 60
        work_duration = self.adhd_config.work_duration_minutes

        return elapsed_minutes >= work_duration and self.status == TaskStatus.EXECUTING

    def get_latest_snapshot(self) -> Optional[SessionSnapshot]:
        """Get the most recent checkpoint"""
        if self.session_snapshots:
            return max(self.session_snapshots, key=lambda s: s.timestamp)
        return None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: str
        }