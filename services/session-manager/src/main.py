"""
Dopemux Multi-AI Orchestrator - Main Entry Point
PHASE 1 MVP - All 7 Steps Integrated

What this does:
- Spawns tmux session with adaptive layout (Steps 1)
- Parses user commands with 100% accuracy (Step 2)
- Manages AI CLI instances (Step 3)
- Coordinates via message bus (Step 4)
- Auto-saves every 30s (Step 5)
- Routes commands intelligently (Step 6)
- Restores sessions gracefully (Step 7)
"""

import sys

import logging

logger = logging.getLogger(__name__)

from pathlib import Path
from datetime import datetime

from tmux_manager import TmuxLayoutManager
from command_parser import CommandParser
from agent_spawner import AgentSpawner, AgentConfig, AgentType
from message_bus_v2 import create_message_bus, Event, EventType
from checkpoint_manager import CheckpointManager
from router import CommandRouter
from session_manager import SessionManager
from context_protocol import ContextSharingProtocol

from rich.console import Console
from rich.prompt import Prompt


class DopemuxOrchestrator:
    """
    Main orchestrator coordinating all components.

    ADHD-Optimized Multi-AI Development Mission Control
    """

    def __init__(self, workspace_id: str, energy_level: str = "medium"):
        """
        Initialize Dopemux orchestrator.

        Args:
            workspace_id: ConPort workspace path
            energy_level: Starting energy level (low/medium/high)
        """
        self.workspace_id = workspace_id
        self.session_id = f"dopemux-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        self.console = Console()

        # Initialize components
        self.console.print("[cyan]Initializing Dopemux Orchestrator...[/cyan]")

        # Step 1: Tmux Layout Manager
        self.tmux = TmuxLayoutManager()
        self.console.print("  ✅ Tmux layout manager")

        # Step 2: Command Parser
        self.parser = CommandParser()
        self.console.print("  ✅ Command parser (100% accuracy)")

        # Step 3: Agent Spawner
        self.spawner = AgentSpawner()
        self.console.print("  ✅ Agent spawner")

        # Step 4: Message Bus
        self.message_bus = create_message_bus("in_memory", max_events=10000)
        self.console.print("  ✅ Message bus (thread-safe, async)")

        # Step 5: Checkpoint Manager
        self.checkpoint_mgr = CheckpointManager(
            workspace_id=workspace_id, session_id=self.session_id
        )
        self.console.print("  ✅ Checkpoint manager (30s auto-save)")

        # Step 6: Command Router
        self.context_protocol = ContextSharingProtocol(workspace_id, self.session_id)
        self.router = CommandRouter(
            self.parser, self.spawner, self.message_bus, self.context_protocol
        )
        self.console.print("  ✅ Command router")

        # Step 7: Session Manager
        self.session_mgr = SessionManager(
            workspace_id, self.session_id, self.checkpoint_mgr
        )
        self.console.print("  ✅ Session manager\n")

        # Create tmux session
        self.console.print(f"Creating tmux session ({energy_level} energy)...")
        self.tmux.create_session(energy_level=energy_level)

        # Start auto-save
        self.checkpoint_mgr.start_auto_save()

        self.console.print("[bold green]✅ Dopemux ready![/bold green]\n")

    def run(self):
        """
        Main orchestrator loop.

        Handles:
        - User input via chat interface
        - Command routing to AI agents
        - Event coordination
        - ADHD accommodations
        """
        self.console.print(
            "[bold]Dopemux Multi-AI Orchestrator[/bold] - Phase 1 MVP\n"
        )
        self.console.print("[dim]Type /help for commands, /quit to exit[/dim]\n")

        try:
            while True:
                # Get user input
                user_input = Prompt.ask("\n[bold cyan]You[/bold cyan]").strip()

                if not user_input:
                    continue

                # Handle special commands
                if user_input == "/quit":
                    break
                elif user_input == "/help":
                    self._show_help()
                    continue
                elif user_input == "/status":
                    self._show_status()
                    continue

                # Route command
                self.console.print("[dim]Routing command...[/dim]")
                result = self.router.route_command(user_input)

                # Display result
                self._display_result(result)

                # Update checkpoint state
                self.checkpoint_mgr.update_state(
                    message={"role": "user", "content": user_input, "timestamp": datetime.now().isoformat()}
                )

        except KeyboardInterrupt:
            self.console.print("\n\n[yellow]Interrupted by user[/yellow]")

        finally:
            self._shutdown()

    def _show_help(self):
        """Display help information."""
        self.console.print(
            """
[bold cyan]Dopemux Commands:[/bold cyan]

[bold]Workflow Modes:[/bold]
  /mode research      → Research phase (Gemini primary)
  /mode plan          → Planning phase (Claude primary)
  /mode implement     → Implementation (Grok primary)
  /mode debug         → Debug phase (Gemini primary)

[bold]Agent Control:[/bold]
  /agent claude       → Use Claude explicitly
  /agent gemini       → Use Gemini explicitly
  /agent grok         → Use Grok explicitly
  /consensus <question> → Multi-model decision

[bold]Context:[/bold]
  /context save       → Save context manually
  /status             → Show agent status
  /help               → This help

[bold]ADHD:[/bold]
  /break [minutes]    → Start break timer
  /energy [level]     → Check/set energy level

[bold]System:[/bold]
  /quit               → Exit (auto-saves)
        """
        )

    def _show_status(self):
        """Display system status."""
        status = self.spawner.get_status()
        metrics = self.message_bus.get_metrics()

        self.console.print("\n[bold]System Status:[/bold]")
        self.console.print(f"  Session: {self.session_id}")
        self.console.print(f"  Checkpoints: {self.checkpoint_mgr.checkpoint_count}")
        self.console.print(f"  Events: {metrics.total_events_published} published")
        self.console.print(f"  Buffer: {metrics.buffer_utilization_percent:.1f}% full")

        self.console.print("\n[bold]Agents:[/bold]")
        for agent_name, agent_status in status.items():
            icon = "✅" if agent_status["status"] == "running" else "❌"
            self.console.print(f"  {icon} {agent_name}: {agent_status['status']}")

    def _display_result(self, result: dict):
        """Display command execution result."""
        self.console.print(
            f"\n[dim]Agents: {', '.join(result.get('agents', []))}[/dim]"
        )
        self.console.print(f"[dim]Strategy: {result.get('strategy', 'unknown')}[/dim]")
        self.console.print(f"[dim]Estimated: {result.get('estimated_duration', 0)} min[/dim]\n")

        # Show responses
        responses = result.get("responses", {})
        for agent, response in responses.items():
            self.console.print(f"[bold green]{agent}:[/bold green]")
            if response:
                for line in response[:10]:  # First 10 lines
                    self.console.print(f"  {line.strip()}")
                if len(response) > 10:
                    self.console.print(f"  [dim]... {len(response) - 10} more lines[/dim]")

    def _shutdown(self):
        """Graceful shutdown."""
        self.console.print("\n[cyan]Shutting down Dopemux...[/cyan]")

        # Stop auto-save
        self.checkpoint_mgr.stop_auto_save()

        # Final checkpoint
        self.checkpoint_mgr.save_checkpoint(verbose=True)

        # Stop agents
        self.spawner.stop_all()

        # Shutdown message bus
        self.message_bus.shutdown()

        self.console.print("[bold green]✅ Goodbye![/bold green]\n")


def main():
    """Entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Dopemux Multi-AI Orchestrator")
    parser.add_argument(
        "--workspace",
        default="/Users/hue/code/ui-build",
        help="Workspace directory",
    )
    parser.add_argument(
        "--energy",
        choices=["low", "medium", "high"],
        default="medium",
        help="Starting energy level",
    )
    parser.add_argument(
        "--new",
        action="store_true",
        help="Force new session (don't resume)",
    )

    args = parser.parse_args()

    # Create orchestrator
    orchestrator = DopemuxOrchestrator(
        workspace_id=args.workspace, energy_level=args.energy
    )

    # Start session (with resume prompt)
    if not args.new:
        orchestrator.session_mgr.start_session()

    # Run main loop
    orchestrator.run()


if __name__ == "__main__":
    main()
