"""
Rich-based Progress Display for Dopemux ADHD UX

Provides visual feedback for long-running operations with:
- Complexity-based progress bars
- ADHD-friendly color schemes
- Time remaining estimates
- Status indicators without overwhelming details

Integrates with ADHD workflow manager for cognitive load awareness.
"""

import time

import logging

logger = logging.getLogger(__name__)

from typing import Optional, Dict, Any
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeRemainingColumn
from rich.text import Text
from rich.table import Table

from ..console import console


class ProgressDisplay:
    """
    ADHD-optimized progress display using Rich library.

    Provides clear, non-overwhelming visual feedback for operations
    while respecting cognitive load and attention span.
    """

    def __init__(self):
        self.console = console
        self.current_progress: Optional[Progress] = None

    def show_operation_start(self, operation_name: str, total_steps: Optional[int] = None, complexity: float = 0.5):
        """
        Show operation start with appropriate visual feedback.

        Args:
            operation_name: Name of the operation
            total_steps: Total steps if known (for progress bar)
            complexity: Cognitive complexity (0.0-1.0) to determine detail level
        """
        # Choose display style based on complexity
        if complexity > 0.7:
            # High complexity - minimal feedback to avoid overwhelm
            self._show_minimal_start(operation_name)
        elif total_steps and total_steps > 1:
            # Multi-step operation - progress bar
            self._show_progress_bar(operation_name, total_steps)
        else:
            # Simple operation - spinner
            self._show_spinner_start(operation_name)

    def update_progress(self, current_step: int, message: str = "", complexity: float = 0.5):
        """
        Update progress display.

        Args:
            current_step: Current step number
            message: Status message
            complexity: Current cognitive load
        """
        if self.current_progress:
            # Update progress bar if active
            task = next(iter(self.current_progress.tasks))
            self.current_progress.update(task, completed=current_step, description=message)

    def show_operation_complete(self, operation_name: str, duration: float, success: bool = True, results: Optional[Dict[str, Any]] = None):
        """
        Show operation completion with summary.

        Args:
            operation_name: Name of completed operation
            duration: Time taken in seconds
            success: Whether operation succeeded
            results: Optional results to display
        """
        # Clear any active progress
        if self.current_progress:
            self.current_progress.stop()
            self.current_progress = None

        # Show completion panel
        status_icon = "✅" if success else "❌"
        status_color = "green" if success else "red"

        panel_content = f"{status_icon} {operation_name} completed in {duration:.1f}s"

        if results:
            # Add key results for low complexity operations
            if len(results) <= 3:  # Don't overwhelm
                result_lines = [f"  {k}: {v}" for k, v in results.items()]
                panel_content += "\n" + "\n".join(result_lines)

        panel = Panel(
            panel_content,
            title=f"Operation Complete",
            border_style=status_color,
            padding=(1, 2)
        )

        self.console.log(panel)

    def show_error(self, operation_name: str, error: str, complexity: float = 0.5):
        """
        Show error with appropriate detail level.

        Args:
            operation_name: Operation that failed
            error: Error message
            complexity: Current cognitive load
        """
        # Clear progress
        if self.current_progress:
            self.current_progress.stop()
            self.current_progress = None

        # Show error with detail based on complexity
        if complexity > 0.7:
            # High complexity - minimal error info
            self.console.log(f"[red]❌ {operation_name} failed[/red]")
        else:
            # Provide helpful error details
            panel = Panel(
                f"Error: {error}\n\nTry checking logs or restarting the operation.",
                title=f"{operation_name} Failed",
                border_style="red",
                padding=(1, 2)
            )
            self.console.log(panel)

    def show_adhd_friendly_status(self, status_info: Dict[str, Any]):
        """
        Show status in ADHD-friendly format with progressive disclosure.

        Args:
            status_info: Status information to display
        """
        # Create a compact status table
        table = Table(show_header=False, box=None, padding=(0, 2))

        # Only show 3-4 key items to avoid overwhelm
        key_items = [
            ("Status", status_info.get("status", "Unknown")),
            ("Load", f"{status_info.get('cognitive_load', 0.5):.1f}"),
            ("Tasks", status_info.get("active_tasks", 0)),
        ]

        if "break_needed" in status_info and status_info["break_needed"]:
            key_items.append(("Break", "Recommended"))

        for label, value in key_items:
            table.add_row(f"[bold]{label}:[/bold]", str(value))

        panel = Panel(
            table,
            title="System Status",
            border_style="blue",
            padding=(1, 2)
        )

        self.console.log(panel)

    def _show_minimal_start(self, operation_name: str):
        """Show minimal start indicator for high-complexity operations."""
        self.console.log(f"[dim]⏳ Starting {operation_name}...[/dim]")

    def _show_spinner_start(self, operation_name: str):
        """Show spinner for simple operations."""
        with self.console.status(f"[bold green]Working on {operation_name}...[/bold green]") as status:
            # Spinner is handled by the context manager
            pass

    def _show_progress_bar(self, operation_name: str, total_steps: int):
        """Show progress bar for multi-step operations."""
        self.current_progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(complete_style="green", finished_style="green"),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
            console=self.console,
            refresh_per_second=2  # Gentle refresh rate
        )

        self.current_progress.start()
        task = self.current_progress.add_task(
            f"Processing {operation_name}...",
            total=total_steps
        )


# Convenience functions for common Dopemux operations
def show_mcp_operation_progress(operation_name: str, complexity: float = 0.5):
    """Show progress for MCP operations."""
    display = ProgressDisplay()
    display.show_operation_start(operation_name, complexity=complexity)


def complete_mcp_operation(operation_name: str, duration: float, results: Optional[Dict[str, Any]] = None):
    """Complete MCP operation display."""
    display = ProgressDisplay()
    display.show_operation_complete(operation_name, duration, results=results)


def show_hook_status(hook_info: Dict[str, Any]):
    """Show hook system status."""
    display = ProgressDisplay()
    display.show_adhd_friendly_status(hook_info)