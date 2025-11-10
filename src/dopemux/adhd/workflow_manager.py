"""
ADHD Workflow Manager for Dopemux

Provides ADHD-optimized workflow management with:
- Cognitive load monitoring and automatic adjustments
- 25-minute focus session tracking with break suggestions
- Progressive disclosure of information
- Context preservation across interruptions
- Integration with ADHD Engine services

Core Features:
- Real-time cognitive load assessment
- Automatic break recommendations
- Session state management
- Visual feedback optimization
- Interrupt recovery support
"""

import asyncio
import time
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
import logging

from ..ux.progress_display import ProgressDisplay
from ..ux.interactive_prompts import InteractivePrompts

logger = logging.getLogger(__name__)


class ADHDWorkflowManager:
    """
    Manages ADHD-optimized development workflows.

    Coordinates between ADHD Engine services, user interactions,
    and Dopemux operations to maintain optimal cognitive flow.
    """

    def __init__(self):
        self.session_start_time = None
        self.last_break_time = None
        self.cognitive_load_history = []
        self.current_focus_level = "medium"
        self.session_duration_minutes = 25  # ADHD-optimized focus period
        self.break_duration_minutes = 5

        # Initialize UI components
        self.progress_display = ProgressDisplay()
        self.interactive_prompts = InteractivePrompts()

        # ADHD Engine integration (will be initialized if available)
        self.adhd_engine_client = None

    def start_session(self, task_description: str = "") -> Dict[str, Any]:
        """
        Start an ADHD-optimized work session.

        Args:
            task_description: Description of the current task

        Returns:
            Session initialization data
        """
        self.session_start_time = datetime.now()
        self.cognitive_load_history = []
        self.current_focus_level = "medium"

        session_data = {
            "session_id": f"session_{int(time.time())}",
            "start_time": self.session_start_time.isoformat(),
            "task_description": task_description,
            "focus_level": self.current_focus_level,
            "target_duration": self.session_duration_minutes,
            "break_duration": self.break_duration_minutes
        }

        logger.info(f"Started ADHD session: {session_data['session_id']}")
        return session_data

    def end_session(self) -> Dict[str, Any]:
        """
        End the current work session.

        Returns:
            Session summary data
        """
        if not self.session_start_time:
            return {"error": "No active session"}

        end_time = datetime.now()
        duration = (end_time - self.session_start_time).total_seconds() / 60

        session_summary = {
            "session_id": f"session_{int(self.session_start_time.timestamp())}",
            "start_time": self.session_start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_minutes": round(duration, 1),
            "cognitive_load_avg": self._calculate_avg_cognitive_load(),
            "breaks_taken": 1 if self.last_break_time else 0,
            "focus_level_final": self.current_focus_level
        }

        # Reset session state
        self.session_start_time = None
        self.last_break_time = None

        logger.info(f"Ended ADHD session: {session_summary['duration_minutes']}min")
        return session_summary

    def check_break_needed(self) -> Tuple[bool, str]:
        """
        Check if a break is needed based on session timing and cognitive load.

        Returns:
            Tuple of (break_needed, reason)
        """
        if not self.session_start_time:
            return False, "No active session"

        elapsed_minutes = (datetime.now() - self.session_start_time).total_seconds() / 60

        # Time-based break check
        if elapsed_minutes >= self.session_duration_minutes:
            return True, f"Session duration reached ({elapsed_minutes:.1f}min)"

        # Cognitive load check
        avg_load = self._calculate_avg_cognitive_load()
        if avg_load > 0.8:
            return True, f"High cognitive load ({avg_load:.1f})"

        # Recent break check (prevent too frequent breaks)
        if self.last_break_time:
            time_since_break = (datetime.now() - self.last_break_time).total_seconds() / 60
            if time_since_break < 20:  # Minimum 20min between breaks
                return False, "Recent break taken"

        return False, "No break needed"

    def suggest_break(self) -> Dict[str, Any]:
        """
        Generate a break suggestion with timing and activities.

        Returns:
            Break suggestion data
        """
        break_needed, reason = self.check_break_needed()

        if not break_needed:
            return {
                "suggested": False,
                "reason": reason
            }

        # Generate break activities based on cognitive load
        activities = self._generate_break_activities()

        return {
            "suggested": True,
            "reason": reason,
            "duration_minutes": self.break_duration_minutes,
            "activities": activities,
            "urgency": "high" if reason.startswith("High cognitive") else "medium"
        }

    def update_cognitive_load(self, load_level: float, context: str = "") -> None:
        """
        Update the current cognitive load level.

        Args:
            load_level: Float 0.0-1.0 (0=low, 1=high cognitive load)
            context: Optional context about the load measurement
        """
        timestamp = datetime.now()

        self.cognitive_load_history.append({
            "timestamp": timestamp,
            "load": load_level,
            "context": context
        })

        # Update focus level based on load
        if load_level < 0.3:
            self.current_focus_level = "low"
        elif load_level < 0.7:
            self.current_focus_level = "medium"
        else:
            self.current_focus_level = "high"

        # Keep only last 50 measurements (about 25 minutes at 30s intervals)
        if len(self.cognitive_load_history) > 50:
            self.cognitive_load_history = self.cognitive_load_history[-50:]

        logger.debug(f"Cognitive load updated: {load_level:.2f} ({self.current_focus_level})")

    def take_break(self) -> Dict[str, Any]:
        """
        Record that a break was taken.

        Returns:
            Break completion data
        """
        self.last_break_time = datetime.now()

        return {
            "break_taken": True,
            "timestamp": self.last_break_time.isoformat(),
            "duration_minutes": self.break_duration_minutes,
            "next_session_start": (self.last_break_time + timedelta(minutes=self.break_duration_minutes)).isoformat()
        }

    def get_progressive_info(self, full_info: Dict[str, Any], user_expertise: str = "intermediate") -> Dict[str, Any]:
        """
        Apply progressive disclosure to information based on user context.

        Args:
            full_info: Complete information dictionary
            user_expertise: User expertise level ("beginner", "intermediate", "expert")

        Returns:
            Filtered information appropriate for user level
        """
        if user_expertise == "beginner":
            # Show minimal essential info
            essential_keys = ["status", "message", "next_action"]
            return {k: v for k, v in full_info.items() if k in essential_keys}

        elif user_expertise == "intermediate":
            # Show moderate detail, hide advanced options
            hide_keys = ["debug_info", "internal_metrics", "raw_data"]
            return {k: v for k, v in full_info.items() if k not in hide_keys}

        else:  # expert
            # Show everything
            return full_info

    def get_context_snapshot(self) -> Dict[str, Any]:
        """
        Get a complete context snapshot for interrupt recovery.

        Returns:
            Current session state for restoration
        """
        return {
            "session_active": self.session_start_time is not None,
            "session_start": self.session_start_time.isoformat() if self.session_start_time else None,
            "last_break": self.last_break_time.isoformat() if self.last_break_time else None,
            "current_focus_level": self.current_focus_level,
            "cognitive_load_recent": self._calculate_avg_cognitive_load(),
            "session_duration_minutes": self.session_duration_minutes,
            "cognitive_load_history_count": len(self.cognitive_load_history)
        }

    def restore_context(self, snapshot: Dict[str, Any]) -> bool:
        """
        Restore session context from a snapshot.

        Args:
            snapshot: Context snapshot from get_context_snapshot()

        Returns:
            Success status
        """
        try:
            if snapshot.get("session_active"):
                self.session_start_time = datetime.fromisoformat(snapshot["session_start"])
                if snapshot.get("last_break"):
                    self.last_break_time = datetime.fromisoformat(snapshot["last_break"])
                self.current_focus_level = snapshot.get("current_focus_level", "medium")

            logger.info("Context restored successfully")
            return True
        except Exception as e:
            logger.error(f"Context restoration failed: {e}")
            return False

    def _calculate_avg_cognitive_load(self, window_minutes: int = 10) -> float:
        """Calculate average cognitive load over recent window."""
        if not self.cognitive_load_history:
            return 0.5  # Default medium load

        # Get measurements within time window
        cutoff_time = datetime.now() - timedelta(minutes=window_minutes)
        recent_loads = [
            entry["load"] for entry in self.cognitive_load_history
            if entry["timestamp"] > cutoff_time
        ]

        return sum(recent_loads) / len(recent_loads) if recent_loads else 0.5

    def _generate_break_activities(self) -> List[str]:
        """Generate appropriate break activities based on cognitive load."""
        avg_load = self._calculate_avg_cognitive_load()

        if avg_load > 0.8:
            # High cognitive load - suggest calming activities
            return [
                "Take a 2-minute breathing exercise",
                "Step away from screen and look at something 20+ feet away",
                "Do gentle neck and shoulder stretches",
                "Drink water and have a healthy snack"
            ]
        elif avg_load > 0.6:
            # Medium cognitive load - suggest light activities
            return [
                "Stand up and walk around for 2 minutes",
                "Do some simple desk stretches",
                "Listen to 1 minute of calming music",
                "Practice the 4-7-8 breathing technique"
            ]
        else:
            # Lower cognitive load - suggest engagement activities
            return [
                "Take a short walk outside if possible",
                "Do some light physical activity",
                "Listen to an interesting podcast segment",
                "Have a conversation with a colleague"
            ]


# Global instance for easy access
adhd_workflow = ADHDWorkflowManager()


# Convenience functions
def start_adhd_session(task_description: str = "") -> Dict[str, Any]:
    """Start an ADHD-optimized work session."""
    return adhd_workflow.start_session(task_description)


def end_adhd_session() -> Dict[str, Any]:
    """End the current ADHD work session."""
    return adhd_workflow.end_session()


def check_break_recommendation() -> Dict[str, Any]:
    """Check if a break is recommended."""
    return adhd_workflow.suggest_break()


def update_cognitive_load(load: float, context: str = "") -> None:
    """Update cognitive load level."""
    adhd_workflow.update_cognitive_load(load, context)


def get_context_snapshot() -> Dict[str, Any]:
    """Get current context for preservation."""
    return adhd_workflow.get_context_snapshot()


def restore_context(snapshot: Dict[str, Any]) -> bool:
    """Restore context from snapshot."""
    return adhd_workflow.restore_context(snapshot)