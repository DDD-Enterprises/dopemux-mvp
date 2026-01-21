"""
ADHD-Optimized Progress Tracking

Visual progress tracking with clear milestones, time estimates,
and encouraging feedback designed for neurodivergent users.
"""

import time

import logging

logger = logging.getLogger(__name__)

from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Dict, Any

from rich.console import Console
from rich.progress import (
    Progress, TaskID, BarColumn, TextColumn, TimeElapsedColumn,
    TimeRemainingColumn, SpinnerColumn
)
from rich.panel import Panel
from rich.text import Text


class UpdateState(Enum):
    """Current state of the update process."""
    INITIALIZING = "initializing"
    DISCOVERING = "discovering"
    BACKING_UP = "backing_up"
    UPDATING = "updating"
    ORCHESTRATING = "orchestrating"
    VALIDATING = "validating"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class PhaseProgress:
    """Progress tracking for individual phases."""
    name: str
    description: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    current_step: str = ""
    progress_percentage: float = 0.0
    estimated_duration: Optional[timedelta] = None

    @property
    def is_active(self) -> bool:
        return self.started_at is not None and self.completed_at is None

    @property
    def is_completed(self) -> bool:
        return self.completed_at is not None

    @property
    def duration(self) -> Optional[timedelta]:
        if self.started_at:
            end_time = self.completed_at or datetime.now()
            return end_time - self.started_at
        return None


class ProgressTracker:
    """
    ADHD-optimized progress tracker with visual feedback.

    Features:
    - Clear visual progress bars with time estimates
    - Milestone celebrations
    - Interrupt-friendly checkpointing
    - Encouraging messages and tips
    """

    def __init__(self, console: Console):
        self.console = console
        self.update_start_time: Optional[datetime] = None
        self.current_state = UpdateState.INITIALIZING
        self.phases: Dict[str, PhaseProgress] = {}
        self.main_progress: Optional[Progress] = None
        self.encouragement_messages = [
            "💡 Tip: Feel free to take a break - I'll save your progress!",
            "🎯 Great progress! You're doing awesome!",
            "☕ Perfect time for a coffee break if you need one",
            "🧠 Update running smoothly - ADHD optimizations working!",
            "⭐ Almost there! The finish line is in sight!",
        ]
        self.encouragement_index = 0

    @contextmanager
    def start_update(self, update_name: str):
        """Start tracking an update with ADHD-friendly progress display."""
        self.update_start_time = datetime.now()
        self.current_state = UpdateState.DISCOVERING

        # Create rich progress display
        self.main_progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=self.console,
            expand=True
        )

        with self.main_progress:
            # Create main task
            main_task = self.main_progress.add_task(
                f"🚀 {update_name}",
                total=100
            )

            # Show welcome message
            self._show_welcome_message(update_name)

            try:
                yield main_task
            finally:
                self._show_completion_summary()

    def start_phase(self, main_task: TaskID, phase_name: str,
                   phase_number: int, total_phases: int) -> None:
        """Start a new phase with progress tracking."""
        # Calculate phase progress for main task
        phase_progress = (phase_number - 1) / total_phases * 100
        self.main_progress.update(main_task, completed=phase_progress)

        # Create phase progress tracker
        phase_key = phase_name.lower()
        self.phases[phase_key] = PhaseProgress(
            name=phase_name,
            description=f"Phase {phase_number}/{total_phases}",
            started_at=datetime.now(),
            estimated_duration=timedelta(minutes=3)  # Default estimate
        )

        # Show phase start message
        self._show_phase_start(phase_name, phase_number, total_phases)

    def complete_phase(self, phase_name: str) -> None:
        """Mark a phase as completed with celebration."""
        phase_key = phase_name.lower()
        if phase_key in self.phases:
            self.phases[phase_key].completed_at = datetime.now()
            self.phases[phase_key].progress_percentage = 100.0

        self._show_phase_completion(phase_name)

    def update_phase_progress(self, phase_name: str,
                             step_description: str,
                             percentage: float = None) -> None:
        """Update progress within a phase."""
        phase_key = phase_name.lower()
        if phase_key in self.phases:
            self.phases[phase_key].current_step = step_description
            if percentage is not None:
                self.phases[phase_key].progress_percentage = percentage

        # Show step update
        self.console.print(f"[dim]  → {step_description}...[/dim]")

    def show_checkpoint_saved(self, checkpoint_name: str) -> None:
        """Show that a checkpoint was saved."""
        self.console.print(f"[green]💾 Checkpoint saved: {checkpoint_name}[/green]")

    def show_encouragement(self) -> None:
        """Show an encouraging message for ADHD users."""
        message = self.encouragement_messages[self.encouragement_index]
        self.encouragement_index = (self.encouragement_index + 1) % len(self.encouragement_messages)

        panel = Panel(
            Text(message, style="cyan"),
            title="💝 ADHD Support",
            border_style="cyan"
        )
        self.console.print(panel)

    def show_time_estimate(self, estimated_minutes: int) -> None:
        """Show time estimate in ADHD-friendly format."""
        if estimated_minutes <= 5:
            time_desc = "⚡ Just a few minutes"
        elif estimated_minutes <= 15:
            time_desc = f"☕ About {estimated_minutes} minutes (perfect for a coffee break)"
        elif estimated_minutes <= 30:
            time_desc = f"🍽️ About {estimated_minutes} minutes (good time for lunch)"
        else:
            time_desc = f"📚 About {estimated_minutes} minutes (maybe read a chapter?)"

        self.console.print(f"[dim]⏱️ {time_desc}[/dim]")

    def show_interrupt_recovery(self, last_checkpoint: str, time_ago: str) -> None:
        """Show friendly interrupt recovery message."""
        panel = Panel(
            f"Welcome back! 👋\\n\\n"
            f"Last checkpoint: {last_checkpoint}\\n"
            f"Time since interruption: {time_ago}\\n\\n"
            f"I've saved your progress - let's pick up where we left off!",
            title="🔄 Resuming Update",
            border_style="green"
        )
        self.console.print(panel)

    def _show_welcome_message(self, update_name: str) -> None:
        """Show ADHD-friendly welcome message."""
        welcome_text = (
            f"Starting {update_name}! 🚀\\n\\n"
            "✨ ADHD Optimizations Active:\\n"
            "  • Visual progress tracking\\n"
            "  • Automatic checkpointing every 30 seconds\\n"
            "  • Interrupt-safe with resume capability\\n"
            "  • Clear next steps and time estimates\\n\\n"
            "Feel free to step away - I'll keep track of everything!"
        )

        panel = Panel(
            welcome_text,
            title="🧠 Dopemux Update Manager",
            border_style="bright_blue"
        )
        self.console.print(panel)

    def _show_phase_start(self, phase_name: str, phase_number: int, total_phases: int) -> None:
        """Show phase start with progress indicator."""
        # Create visual progress indicator
        filled_blocks = "█" * (phase_number - 1)
        current_block = "▓"
        empty_blocks = "░" * (total_phases - phase_number)
        progress_bar = f"[{filled_blocks}{current_block}{empty_blocks}]"

        self.console.print(f"\\n[bold cyan]Phase {phase_number}/{total_phases}: {phase_name}[/bold cyan]")
        self.console.print(f"[dim]{progress_bar} {phase_number}/{total_phases} phases complete[/dim]")

    def _show_phase_completion(self, phase_name: str) -> None:
        """Show phase completion with mini celebration."""
        self.console.print(f"[green]✅ {phase_name} completed![/green]")

        # Show encouragement periodically
        if len([p for p in self.phases.values() if p.is_completed]) % 2 == 0:
            self.show_encouragement()

    def _show_completion_summary(self) -> None:
        """Show final completion summary."""
        if self.update_start_time:
            duration = datetime.now() - self.update_start_time
            duration_str = f"{duration.total_seconds():.1f} seconds"

            completed_phases = [p for p in self.phases.values() if p.is_completed]
            success_rate = len(completed_phases) / len(self.phases) * 100 if self.phases else 100

            summary = (
                f"Duration: {duration_str}\\n"
                f"Phases completed: {len(completed_phases)}/{len(self.phases)}\\n"
                f"Success rate: {success_rate:.0f}%"
            )

            if success_rate == 100:
                panel = Panel(
                    f"🎉 Update completed successfully! 🎉\\n\\n{summary}",
                    title="✅ Success",
                    border_style="green"
                )
            else:
                panel = Panel(
                    f"⚠️ Update completed with issues\\n\\n{summary}",
                    title="⚠️ Partial Success",
                    border_style="yellow"
                )

            self.console.print(panel)