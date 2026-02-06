"""Core research task models used by the ADHD-optimized research service."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    """Lifecycle state for research tasks and sub-steps."""

    PLANNING = "planning"
    REVIEWING = "reviewing"
    EXECUTING = "executing"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class ResearchType(str, Enum):
    """Supported research task categories."""

    FEATURE_RESEARCH = "feature_research"
    BUG_INVESTIGATION = "bug_investigation"
    TECHNOLOGY_EVALUATION = "technology_evaluation"
    SYSTEM_ARCHITECTURE = "system_architecture"
    DOCUMENTATION_RESEARCH = "documentation_research"
    COMPETITIVE_ANALYSIS = "competitive_analysis"
    QUICK_LOOKUP = "quick_lookup"


class ADHDConfiguration(BaseModel):
    """ADHD-oriented execution controls."""

    pomodoro_enabled: bool = True
    work_duration_minutes: int = 25
    break_duration_minutes: int = 5
    max_concurrent_sources: int = 5
    progressive_disclosure: bool = True
    auto_save_interval_seconds: int = 30
    gentle_notifications: bool = True
    visual_progress_enabled: bool = True


class ProjectContext(BaseModel):
    """Optional project context injected into research prompts."""

    workspace_path: str = ""
    tech_stack: List[str] = Field(default_factory=list)
    architecture_patterns: List[str] = Field(default_factory=list)
    current_focus: str = ""


class ResearchQuestion(BaseModel):
    """Single planned question in a research workflow."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    question: str
    priority: int = 1
    estimated_duration_minutes: int = 5
    status: TaskStatus = TaskStatus.PLANNING
    sources_found: int = 0
    confidence_score: float = 0.0


class ResearchResult(BaseModel):
    """Result payload for a completed research question."""

    question_id: str
    answer: str
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    confidence: float = 0.0
    search_engines_used: List[str] = Field(default_factory=list)
    processing_time_seconds: float = 0.0
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SessionSnapshot(BaseModel):
    """Checkpoint for pause/resume recovery."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    task_id: UUID
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    current_question_index: int = 0
    status: TaskStatus = TaskStatus.PAUSED
    partial_results: Dict[str, Any] = Field(default_factory=dict)
    context_data: Dict[str, Any] = Field(default_factory=dict)
    recovery_instructions: str = ""


class ResearchTask(BaseModel):
    """Top-level task entity for orchestrated research execution."""

    id: UUID = Field(default_factory=uuid4)
    user_id: str
    initial_prompt: str
    enhanced_prompt: Optional[str] = None
    research_type: ResearchType = ResearchType.FEATURE_RESEARCH
    adhd_config: ADHDConfiguration = Field(default_factory=ADHDConfiguration)
    project_context: Optional[ProjectContext] = None

    status: TaskStatus = TaskStatus.PLANNING
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    research_plan: List[ResearchQuestion] = Field(default_factory=list)
    results: Dict[str, ResearchResult] = Field(default_factory=dict)
    current_question_index: int = 0
    checkpoints: List[SessionSnapshot] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    total_processing_time: float = 0.0
    sources_discovered: int = 0
    confidence_score: float = 0.0

    def transition_to(self, new_status: TaskStatus) -> None:
        """Transition task status and update timestamp."""
        self.status = new_status
        self.updated_at = datetime.now(timezone.utc)

    def calculate_progress(self) -> Dict[str, Any]:
        """Compute progress metrics for UI and API responses."""
        total_questions = len(self.research_plan)
        completed_questions = sum(
            1 for question in self.research_plan if question.status == TaskStatus.COMPLETED
        )

        progress_percentage = (
            (completed_questions / total_questions) * 100 if total_questions else 0.0
        )

        remaining = [
            question
            for question in self.research_plan
            if question.status not in {TaskStatus.COMPLETED, TaskStatus.FAILED}
        ]
        estimated_remaining = sum(q.estimated_duration_minutes for q in remaining)
        elapsed_minutes = (
            datetime.now(timezone.utc) - self.created_at
        ).total_seconds() / 60.0

        return {
            "progress_percentage": progress_percentage,
            "total_questions": total_questions,
            "completed_questions": completed_questions,
            "current_question": self.current_question_index,
            "estimated_remaining_minutes": estimated_remaining,
            "elapsed_time_minutes": int(elapsed_minutes),
        }

    def create_checkpoint(self, context_data: Dict[str, Any]) -> SessionSnapshot:
        """Create and store a recoverable task checkpoint."""
        snapshot = SessionSnapshot(
            task_id=self.id,
            current_question_index=self.current_question_index,
            status=self.status,
            partial_results={key: value.model_dump() for key, value in self.results.items()},
            context_data=context_data,
            recovery_instructions=(
                f"Resume from question index {self.current_question_index} "
                f"with status '{self.status.value}'."
            ),
        )
        self.checkpoints.append(snapshot)
        self.updated_at = datetime.now(timezone.utc)
        return snapshot

    def get_latest_snapshot(self) -> Optional[SessionSnapshot]:
        """Return latest checkpoint if available."""
        return self.checkpoints[-1] if self.checkpoints else None

    def should_suggest_break(self) -> bool:
        """Whether the current session exceeds configured focus duration."""
        elapsed_minutes = (
            datetime.now(timezone.utc) - self.created_at
        ).total_seconds() / 60.0
        return elapsed_minutes >= self.adhd_config.work_duration_minutes
