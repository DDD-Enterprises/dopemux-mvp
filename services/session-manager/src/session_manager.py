"""
Session Manager - Step 7 of Phase 1
Session restoration with gentle ADHD re-orientation

Enables instant recovery after interruptions with context summary.
Research shows ADHD users need explicit "where you left off" guidance.

Complexity: 0.45 (Medium)
Effort: 4 focus blocks (100 minutes)
"""

from typing import Optional

import logging

logger = logging.getLogger(__name__)

from datetime import datetime, timedelta
from checkpoint_manager import CheckpointManager, Checkpoint
from rich.console import Console
from rich.panel import Panel
from rich.table import Table


class SessionManager:
    """
    Manage session lifecycle with ADHD-optimized restoration.

    Features:
    - Detect if resuming previous session
    - Show gentle re-orientation summary
    - Restore agents, mode, context
    - Provide clear next steps
    """

    def __init__(
        self,
        workspace_id: str,
        session_id: str,
        checkpoint_manager: CheckpointManager,
    ):
        """
        Initialize session manager.

        Args:
            workspace_id: ConPort workspace
            session_id: Session identifier
            checkpoint_manager: For loading checkpoints
        """
        self.workspace_id = workspace_id
        self.session_id = session_id
        self.checkpoint_mgr = checkpoint_manager
        self.console = Console()

    def start_session(self, force_new: bool = False) -> Optional[Checkpoint]:
        """
        Start session with optional resume.

        Args:
            force_new: Force new session (don't try to resume)

        Returns:
            Previous checkpoint if resumed, None if new session

        ADHD Benefits:
        - Eliminates "what was I doing?" anxiety
        - Provides explicit next steps
        - Reduces activation energy to resume work
        """
        if force_new:
            self._show_new_session_welcome()
            return None

        # Try to load checkpoint
        checkpoint = self.checkpoint_mgr.load_latest_checkpoint()

        if not checkpoint:
            self._show_new_session_welcome()
            return None

        # Show resume prompt
        should_resume = self._show_resume_prompt(checkpoint)

        if should_resume:
            self._restore_from_checkpoint(checkpoint)
            return checkpoint
        else:
            self._show_new_session_welcome()
            return None

    def _show_new_session_welcome(self):
        """Display welcome message for new session."""
        self.console.print(
            Panel(
                "[bold green]👋 Welcome to Dopemux Multi-AI Orchestrator![/bold green]\n\n"
                "Starting fresh session.\n\n"
                "[dim]Commands:[/dim]\n"
                "  • /mode research|plan|implement\n"
                "  • /agent claude|gemini|grok\n"
                "  • /help for full command list\n\n"
                "[dim]ADHD Features Active:[/dim]\n"
                "  • Auto-save every 30s 💾\n"
                "  • Break reminders at 25/50/90 min ⏱️\n"
                "  • Energy-aware task suggestions 🎯",
                title="Dopemux Orchestrator",
                border_style="green",
            )
        )

    def _show_resume_prompt(self, checkpoint: Checkpoint) -> bool:
        """
        Show gentle resume prompt with context.

        Args:
            checkpoint: Previous checkpoint

        Returns:
            True if user wants to resume
        """
        # Calculate time since last session
        time_ago = datetime.now() - checkpoint.last_activity
        time_ago_str = self._format_time_ago(time_ago)

        # Build summary panel
        summary_lines = []
        summary_lines.append(f"[bold]Last session:[/bold] {time_ago_str}")
        summary_lines.append(f"[bold]Mode:[/bold] {checkpoint.mode.upper()}")
        summary_lines.append(f"[bold]Energy:[/bold] {checkpoint.energy_level}")
        summary_lines.append(
            f"[bold]Duration:[/bold] {checkpoint.session_duration_seconds // 60} minutes"
        )

        # Show what they were doing
        summary_lines.append("\n[bold cyan]YOU WERE:[/bold cyan]")

        if checkpoint.open_files:
            summary_lines.append(f"  • Editing: {checkpoint.open_files[0]}")

        if checkpoint.chat_history:
            last_msg = checkpoint.chat_history[-1]
            content = last_msg.get("content", "")[:60]
            summary_lines.append(f"  • Working on: {content}...")

        if checkpoint.active_agents:
            agents_str = ", ".join(a["name"] for a in checkpoint.active_agents)
            summary_lines.append(f"  • Using: {agents_str}")

        # Show next action
        summary_lines.append("\n[bold yellow]RECOMMENDED:[/bold yellow]")
        summary_lines.append("  Continue where you left off")

        # Display panel
        self.console.print(
            Panel(
                "\n".join(summary_lines),
                title="[bold]👋 Welcome Back![/bold]",
                border_style="cyan",
            )
        )

        # Prompt for action
        self.console.logger.info("\n[bold]What would you like to do?[/bold]")
        self.console.logger.info("  [green][r][/green] Resume last session")
        self.console.logger.info("  [yellow][n][/yellow] Start new session")
        self.console.logger.info("  [cyan][d][/cyan] Show more details first")

        choice = input("\nYour choice [r/n/d]: ").strip().lower()

        if choice == "d":
            self._show_detailed_checkpoint(checkpoint)
            choice = input("\nResume session? [r/n]: ").strip().lower()

        return choice == "r"

    def _show_detailed_checkpoint(self, checkpoint: Checkpoint):
        """Show detailed checkpoint information."""
        table = Table(title="Checkpoint Details", show_header=True)
        table.add_column("Attribute", style="cyan")
        table.add_column("Value", style="white")

        table.add_row("Session ID", checkpoint.session_id)
        table.add_row("Timestamp", checkpoint.timestamp.strftime("%Y-%m-%d %H:%M:%S"))
        table.add_row("Mode", checkpoint.mode)
        table.add_row("Energy", checkpoint.energy_level)
        table.add_row("Active Agents", str(len(checkpoint.active_agents)))
        table.add_row("Chat Messages", str(len(checkpoint.chat_history)))
        table.add_row("Open Files", str(len(checkpoint.open_files)))
        table.add_row("Pending Tasks", str(len(checkpoint.pending_tasks)))
        table.add_row(
            "Session Duration", f"{checkpoint.session_duration_seconds // 60} minutes"
        )

        self.console.logger.info(table)

        # Show recent chat history
        if checkpoint.chat_history:
            self.console.logger.info("\n[bold]Recent Conversation:[/bold]")
            for msg in checkpoint.chat_history[-5:]:
                role = msg.get("role", "unknown")
                content = msg.get("content", "")[:80]
                self.console.logger.info(f"  [{role}]: {content}")

    def _restore_from_checkpoint(self, checkpoint: Checkpoint):
        """
        Restore session from checkpoint.

        Args:
            checkpoint: Checkpoint to restore from
        """
        self.console.logger.info("\n[green]🔄 Restoring session...[/green]")

        # Restore state to checkpoint manager
        self.checkpoint_mgr.current_mode = checkpoint.mode
        self.checkpoint_mgr.current_energy = checkpoint.energy_level
        self.checkpoint_mgr.active_agents = checkpoint.active_agents
        self.checkpoint_mgr.chat_history = checkpoint.chat_history
        self.checkpoint_mgr.open_files = checkpoint.open_files
        self.checkpoint_mgr.cursor_positions = checkpoint.cursor_positions
        self.checkpoint_mgr.pending_tasks = checkpoint.pending_tasks

        self.console.logger.info("✅ Session state restored")
        self.console.logger.info(f"✅ Mode: {checkpoint.mode}")
        self.console.logger.info(f"✅ Energy: {checkpoint.energy_level}")

        # Show next action
        self.console.print(
            f"\n[bold green]Ready to continue![/bold green] You can pick up right where you left off.\n"
        )

    def _format_time_ago(self, delta: timedelta) -> str:
        """Format time delta in human-readable form."""
        seconds = int(delta.total_seconds())

        if seconds < 60:
            return f"{seconds} seconds ago"
        elif seconds < 3600:
            return f"{seconds // 60} minutes ago"
        elif seconds < 86400:
            hours = seconds // 3600
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        else:
            days = seconds // 86400
            return f"{days} day{'s' if days > 1 else ''} ago"


if __name__ == "__main__":
    """Test session manager."""

    logger.info("Testing Session Manager:")
    logger.info("=" * 60)

    from checkpoint_manager import CheckpointManager

    # Create checkpoint manager with existing checkpoint
    checkpoint_mgr = CheckpointManager(
        workspace_id="/Users/hue/code/ui-build",
        session_id="test-session-123",
    )

    # Update state
    checkpoint_mgr.update_state(
        mode="implement",
        energy="medium",
        agents=[{"name": "grok", "status": "running"}],
        message={"role": "user", "content": "Implement JWT token generation"},
    )

    # Save
    checkpoint_mgr.save_checkpoint(verbose=True)

    # Create session manager
    session_mgr = SessionManager(
        workspace_id="/Users/hue/code/ui-build",
        session_id="test-session-123",
        checkpoint_manager=checkpoint_mgr,
    )

    # Start session (should offer to resume)
    logger.info("\nAttempting to resume session...")
    # checkpoint = session_mgr.start_session()  # Interactive - commented out for test

    logger.info("\n✅ Session manager test complete")
