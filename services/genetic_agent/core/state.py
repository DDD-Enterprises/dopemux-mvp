"""State management for the Genetic Coding Agent system."""

from enum import Enum
from typing import Dict, Any, Optional
from datetime import datetime


class AgentState(Enum):
    """Enumeration of possible agent states."""

    IDLE = "idle"
    ANALYZING = "analyzing"
    REPAIRING = "repairing"
    VALIDATING = "validating"
    GENERATING = "generating"
    LEARNING = "learning"
    ERROR = "error"


class DevelopmentMode(Enum):
    """Development modes for bluesky development tasks."""
    REPAIR = "repair"  # Traditional bug fixing
    IDEATION = "ideation"  # Feature brainstorming and research
    DESIGN = "design"  # Architecture and planning
    IMPLEMENTATION = "implementation"  # Code generation and prototyping
    INTEGRATION = "integration"  # Merging and dependency resolution
    TESTING = "testing"  # Validation and quality assurance
    DOCUMENTATION = "documentation"  # Generating docs and handoff materials


class TaskType(Enum):
    """Task types for mode detection."""
    BUG_FIX = "bug_fix"
    FEATURE_DEV = "feature_dev"
    ARCHITECTURE = "architecture"
    TESTING = "testing"
    DOCUMENTATION = "documentation"



class AgentStatus:
    """Current status of an agent instance."""

    def __init__(self):
        self.state: AgentState = AgentState.IDLE
        self.current_task: Optional[Dict[str, Any]] = None
        self.start_time: Optional[datetime] = None
        self.last_activity: datetime = datetime.now()
        self.error_message: Optional[str] = None

    def update_state(self, new_state: AgentState, task: Optional[Dict[str, Any]] = None):
        """Update the agent state and associated task."""
        self.state = new_state
        if task is not None:
            self.current_task = task
        if new_state == AgentState.ANALYZING:
            self.start_time = datetime.now()
        self.last_activity = datetime.now()
        self.error_message = None

    def set_error(self, error_message: str):
        """Set error state with message."""
        self.state = AgentState.ERROR
        self.error_message = error_message
        self.last_activity = datetime.now()

    def get_status_dict(self) -> Dict[str, Any]:
        """Get status as a dictionary for API responses."""
        return {
            "state": self.state.value,
            "current_task": self.current_task,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "last_activity": self.last_activity.isoformat(),
            "uptime_seconds": (datetime.now() - (self.start_time or self.last_activity)).seconds,
            "error_message": self.error_message
        }