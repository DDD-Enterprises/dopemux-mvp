"""
Dopemux Orchestrator TUI - Fully Interactive Multi-AI Coordination

Main entry point for the Textual-based TUI that provides:
- Multi-instance AI development in a single pane
- Full keyboard/mouse interaction
- Visual progress indicators
- ADHD-optimized design with energy adaptation

Architecture:
- Layer 3: Interactive TUI (this file)
- Layer 2: Command Router & State Manager
- Layer 1: Tmux Control (TmuxLayoutManager)
"""

import asyncio
import os
from datetime import datetime
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Static, Input, ProgressBar, Label
from textual.binding import Binding
from textual.reactive import reactive
from textual import events
from typing import Optional

# Import our tmux layout manager
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from orchestrator.tmux.layout_manager import TmuxLayoutManager, EnergyLevel


class AIOutputPane(Static):
    """
    Widget displaying output from a single AI (Claude, Gemini, or Grok).

    Features:
    - Scrollable output
    - Color-coded status (green=ready, yellow=busy, red=error)
    - AI-specific styling
    - Auto-scroll on new content
    """

    DEFAULT_CSS = """
    AIOutputPane {
        border: solid $primary;
        height: 1fr;
        padding: 1;
        overflow-y: auto;
    }

    AIOutputPane.active {
        border: solid $accent;
    }

    AIOutputPane.busy {
        border: solid yellow;
    }

    AIOutputPane.error {
        border: solid red;
    }
    """

    ai_name: reactive[str] = reactive("AI")
    status: reactive[str] = reactive("ready")
    output_lines: reactive[list] = reactive(lambda: [])

    def __init__(self, ai_name: str, **kwargs):
        super().__init__(**kwargs)
        self.ai_name = ai_name
        self.id = f"pane_{ai_name.lower()}"

    def compose(self) -> ComposeResult:
        """Build the pane UI."""
        yield Label(f"[bold]{self.ai_name}[/bold]", id="ai_label")
        yield Static("Ready to receive commands...", id="output", classes="output")

    def add_output(self, text: str) -> None:
        """Add new output line to the pane."""
        self.output_lines.append(f"{datetime.now().strftime('%H:%M:%S')} | {text}")
        output_widget = self.query_one("#output", Static)
        output_widget.update("\n".join(self.output_lines[-100:]))  # Keep last 100 lines
        output_widget.scroll_end(animate=False)

    def set_status(self, status: str) -> None:
        """Update pane status (ready/busy/error)."""
        self.status = status
        self.remove_class("active", "busy", "error")
        if status == "busy":
            self.add_class("busy")
        elif status == "error":
            self.add_class("error")

    def set_active(self, active: bool) -> None:
        """Highlight pane as active target for commands."""
        if active:
            self.add_class("active")
        else:
            self.remove_class("active")


class ProgressTrackerPane(Static):
    """
    Widget displaying visual progress indicators.

    ADHD-Optimized Features:
    - Overall session progress bar
    - Per-task progress indicators
    - Break reminder countdown
    - Task completion celebrations
    """

    DEFAULT_CSS = """
    ProgressTrackerPane {
        border: solid $primary;
        height: 1fr;
        padding: 1;
        width: 25%;
    }
    """

    session_progress: reactive[int] = reactive(0)
    tasks_done: reactive[int] = reactive(0)
    tasks_total: reactive[int] = reactive(0)
    break_timer_seconds: reactive[int] = reactive(25 * 60)  # 25 minutes

    def compose(self) -> ComposeResult:
        """Build the progress tracker UI."""
        yield Label("[bold]Progress Tracker[/bold]")
        yield Label("Session Progress:", id="session_label")
        yield ProgressBar(total=100, show_eta=False, id="session_progress")
        yield Label("", id="tasks_label")
        yield Label("Break in: 25:00", id="break_timer")

    def update_session_progress(self, percent: int) -> None:
        """Update overall session progress."""
        self.session_progress = min(100, max(0, percent))
        progress_bar = self.query_one("#session_progress", ProgressBar)
        progress_bar.update(progress=self.session_progress)

    def update_tasks(self, done: int, total: int) -> None:
        """Update task completion counters."""
        self.tasks_done = done
        self.tasks_total = total
        tasks_label = self.query_one("#tasks_label", Label)
        tasks_label.update(f"Tasks: {done}/{total} ✅")

    def update_break_timer(self, seconds_remaining: int) -> None:
        """Update break reminder countdown."""
        self.break_timer_seconds = seconds_remaining
        minutes = seconds_remaining // 60
        seconds = seconds_remaining % 60
        timer_label = self.query_one("#break_timer", Label)

        # Color-code based on time remaining
        if seconds_remaining < 300:  # < 5 minutes
            timer_label.update(f"[red]Break in: {minutes}:{seconds:02d}[/red]")
        elif seconds_remaining < 600:  # < 10 minutes
            timer_label.update(f"[yellow]Break in: {minutes}:{seconds:02d}[/yellow]")
        else:
            timer_label.update(f"Break in: {minutes}:{seconds:02d}")


class StatusInfoPane(Static):
    """
    Widget displaying system status information.

    Shows:
    - Current energy level (from ADHD Engine)
    - Session duration
    - Active AI count
    - Keyboard shortcuts reminder
    """

    DEFAULT_CSS = """
    StatusInfoPane {
        border: solid $primary;
        height: 1fr;
        padding: 1;
        width: 25%;
    }
    """

    energy_level: reactive[str] = reactive("medium")
    session_duration: reactive[int] = reactive(0)
    active_ais: reactive[int] = reactive(0)

    def compose(self) -> ComposeResult:
        """Build the status info UI."""
        yield Label("[bold]Status Info[/bold]")
        yield Label("Energy: 🟡 MEDIUM", id="energy_label")
        yield Label("Session: 0m", id="session_label")
        yield Label("Active AIs: 0/3", id="ai_count_label")
        yield Label("\nShortcuts:", id="shortcuts_header")
        yield Label("? - Help", id="help_shortcut")
        yield Label("q - Quit", id="quit_shortcut")

    def update_energy(self, energy: str) -> None:
        """Update energy level display."""
        self.energy_level = energy
        energy_label = self.query_one("#energy_label", Label)

        # Map energy to emoji and color
        energy_map = {
            EnergyLevel.VERY_LOW.value: ("🔴", "LOW", "red"),
            EnergyLevel.LOW.value: ("🔴", "LOW", "red"),
            EnergyLevel.MEDIUM.value: ("🟡", "MEDIUM", "yellow"),
            EnergyLevel.HIGH.value: ("🟢", "HIGH", "green"),
            EnergyLevel.HYPERFOCUS.value: ("🟢", "HYPERFOCUS", "green")
        }

        emoji, text, color = energy_map.get(energy, ("🟡", "MEDIUM", "yellow"))
        energy_label.update(f"Energy: {emoji} [{color}]{text}[/{color}]")

    def update_session_duration(self, minutes: int) -> None:
        """Update session duration."""
        self.session_duration = minutes
        session_label = self.query_one("#session_label", Label)
        session_label.update(f"Session: {minutes}m")

    def update_active_ais(self, count: int) -> None:
        """Update active AI counter."""
        self.active_ais = count
        ai_label = self.query_one("#ai_count_label", Label)
        ai_label.update(f"Active AIs: {count}/3")


class CommandInput(Input):
    """
    Enhanced input widget for sending commands to AIs.

    Features:
    - @claude, @gemini, @grok targeting
    - @all for parallel execution
    - Command history navigation
    - Auto-completion hints
    """

    DEFAULT_CSS = """
    CommandInput {
        dock: bottom;
        height: 3;
        border: solid $accent;
    }
    """

    def __init__(self, **kwargs):
        super().__init__(
            placeholder="Command: @claude analyze auth.py | @all run tests | ?=help",
            **kwargs
        )
        self.command_history: list[str] = []
        self.history_index: int = -1


class DopemuxOrchestratorTUI(App):
    """
    Main Dopemux Orchestrator TUI Application.

    Provides fully interactive multi-AI coordination with:
    - 4-pane layout (3 AI outputs + progress + status)
    - Keyboard shortcuts for all operations
    - Visual progress indicators
    - ADHD-optimized design
    """

    TITLE = "Dopemux Orchestrator TUI"
    SUB_TITLE = "Multi-AI Coordination • ADHD-Optimized"

    CSS = """
    Screen {
        layout: grid;
        grid-size: 5 2;
        grid-rows: 1fr 3;
    }

    #main_container {
        column-span: 5;
        layout: horizontal;
    }

    #ai_panes {
        width: 3fr;
        layout: horizontal;
    }

    #info_panes {
        width: 2fr;
        layout: vertical;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("?", "help", "Help", show=True),
        Binding("ctrl+1", "focus_claude", "Claude", show=False),
        Binding("ctrl+2", "focus_gemini", "Gemini", show=False),
        Binding("ctrl+3", "focus_grok", "Grok", show=False),
        Binding("ctrl+r", "refresh_energy", "Refresh Energy", show=False),
    ]

    # Reactive state
    current_target: reactive[str] = reactive("claude")
    energy_level: reactive[str] = reactive("medium")
    session_start: datetime = datetime.now()

    def __init__(self, workspace_id: str = None, **kwargs):
        super().__init__(**kwargs)
        self.workspace_id = workspace_id or os.getcwd()
        self.layout_manager: Optional[TmuxLayoutManager] = None

    def compose(self) -> ComposeResult:
        """Build the main UI layout."""
        yield Header()

        with Container(id="main_container"):
            # Left side: 3 AI output panes
            with Horizontal(id="ai_panes"):
                yield AIOutputPane("Claude")
                yield AIOutputPane("Gemini")
                yield AIOutputPane("Grok")

            # Right side: Progress + Status
            with Vertical(id="info_panes"):
                yield ProgressTrackerPane()
                yield StatusInfoPane()

        yield CommandInput(id="command_input")
        yield Footer()

    def on_mount(self) -> None:
        """Initialize the application after mounting."""
        # Set initial focus to command input
        self.query_one("#command_input", CommandInput).focus()

        # Highlight Claude as default target
        self.query_one("#pane_claude", AIOutputPane).set_active(True)

        # Start background tasks
        self.set_timer(1, self.update_session_timer)
        self.set_timer(5, self.check_energy_level)
        self.set_timer(1, self.update_break_countdown)

        # Log startup
        self.query_one("#pane_claude", AIOutputPane).add_output("Dopemux Orchestrator TUI initialized ✅")
        self.query_one("#pane_gemini", AIOutputPane).add_output("Ready for commands")
        self.query_one("#pane_grok", AIOutputPane).add_output("Ready for commands")

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle command submission."""
        command = event.value.strip()
        if not command:
            return

        # Clear input
        event.input.value = ""

        # Parse target AI(s) from @mentions
        if command.startswith("@"):
            parts = command.split(maxsplit=1)
            if len(parts) == 2:
                target, actual_command = parts
                target = target[1:]  # Remove @

                if target == "all":
                    # Send to all AIs
                    await self.execute_command_parallel(actual_command)
                elif target in ["claude", "gemini", "grok"]:
                    # Send to specific AI
                    await self.execute_command(target, actual_command)
                else:
                    self.query_one("#pane_claude", AIOutputPane).add_output(f"❌ Unknown target: @{target}")
            else:
                self.query_one("#pane_claude", AIOutputPane).add_output("❌ Command format: @target command")
        else:
            # No @mention, use current target
            await self.execute_command(self.current_target, command)

    async def execute_command(self, ai: str, command: str) -> None:
        """Execute command on specific AI."""
        pane = self.query_one(f"#pane_{ai}", AIOutputPane)
        pane.add_output(f"📤 {command}")
        pane.set_status("busy")

        try:
            # TODO: Route to actual AI CLI (claude, gemini-cli, grok-cli)
            # For now, simulate with placeholder
            await asyncio.sleep(0.5)
            pane.add_output(f"✅ Command received (simulation)")
            pane.set_status("ready")
        except Exception as e:
            pane.add_output(f"❌ Error: {e}")
            pane.set_status("error")

    async def execute_command_parallel(self, command: str) -> None:
        """Execute command on all AIs in parallel."""
        tasks = [
            self.execute_command("claude", command),
            self.execute_command("gemini", command),
            self.execute_command("grok", command)
        ]
        await asyncio.gather(*tasks)

    def update_session_timer(self) -> None:
        """Update session duration display."""
        elapsed = datetime.now() - self.session_start
        minutes = int(elapsed.total_seconds() / 60)
        self.query_one(StatusInfoPane).update_session_duration(minutes)

    def check_energy_level(self) -> None:
        """Check ADHD Engine energy level and update UI."""
        # TODO: Query actual ADHD Engine
        # For now, keep current energy
        self.query_one(StatusInfoPane).update_energy(self.energy_level)

    def update_break_countdown(self) -> None:
        """Update break reminder countdown."""
        # TODO: Track actual work time and calculate remaining
        # For now, show static 25 min
        self.query_one(ProgressTrackerPane).update_break_timer(25 * 60)

    # Action handlers
    def action_focus_claude(self) -> None:
        """Focus Claude pane as command target."""
        self.set_active_pane("claude")

    def action_focus_gemini(self) -> None:
        """Focus Gemini pane as command target."""
        self.set_active_pane("gemini")

    def action_focus_grok(self) -> None:
        """Focus Grok pane as command target."""
        self.set_active_pane("grok")

    def set_active_pane(self, ai: str) -> None:
        """Set the active AI pane for command targeting."""
        # Deactivate all
        for pane_ai in ["claude", "gemini", "grok"]:
            self.query_one(f"#pane_{pane_ai}", AIOutputPane).set_active(False)

        # Activate target
        self.query_one(f"#pane_{ai}", AIOutputPane).set_active(True)
        self.current_target = ai

    def action_help(self) -> None:
        """Show help screen."""
        # TODO: Create help modal
        self.query_one("#pane_claude", AIOutputPane).add_output("""
📖 Keyboard Shortcuts:
  @claude <cmd> - Send to Claude
  @gemini <cmd> - Send to Gemini
  @grok <cmd> - Send to Grok
  @all <cmd> - Send to all AIs
  Ctrl+1/2/3 - Focus pane
  ? - This help
  q - Quit
        """.strip())

    def action_refresh_energy(self) -> None:
        """Manually refresh energy level from ADHD Engine."""
        self.check_energy_level()
        self.query_one("#pane_claude", AIOutputPane).add_output("🔄 Energy level refreshed")


def run_orchestrator_tui(workspace_id: str = None):
    """Launch the Dopemux Orchestrator TUI."""
    app = DopemuxOrchestratorTUI(workspace_id=workspace_id)
    app.run()


if __name__ == "__main__":
    run_orchestrator_tui()
