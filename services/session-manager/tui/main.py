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

import logging

import asyncio
import os
from datetime import datetime
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Static, Input, ProgressBar, Label
from textual.binding import Binding
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual import events
from typing import Optional

logger = logging.getLogger(__name__)

# Import our tmux layout manager
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from orchestrator.tmux.layout_manager import TmuxLayoutManager, EnergyLevel

# Import command router for AI CLI execution
from .command_router import get_command_router

# Import TUI State Manager (coordinates all state: progress, breaks, energy, history)
from .state_manager import get_state_manager
from .conport_tracker import get_progress_tracker


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

    async def on_key(self, event: events.Key) -> None:
        """Handle key events for history navigation."""
        # Get state manager from parent app
        app = self.app
        if not hasattr(app, 'state_manager'):
            return

        # Up arrow: Previous command
        if event.key == "up":
            prev_command = app.state_manager.get_history_navigation("up")
            if prev_command:
                # Remove @mention prefix if present (user can re-add)
                if prev_command.startswith("@"):
                    parts = prev_command.split(maxsplit=1)
                    if len(parts) == 2:
                        self.value = prev_command  # Keep full @mention format
                    else:
                        self.value = prev_command
                else:
                    self.value = prev_command
                event.stop()
                event.prevent_default()

        # Down arrow: Next command
        elif event.key == "down":
            next_command = app.state_manager.get_history_navigation("down")
            if next_command is not None:  # Empty string is valid (new command)
                self.value = next_command
                event.stop()
                event.prevent_default()


class HelpModal(ModalScreen[None]):
    """Keyboard shortcuts modal for the orchestrator TUI."""

    DEFAULT_CSS = """
    #help_modal {
        align: center middle;
        width: 72;
        height: 18;
        border: heavy $accent;
        background: $surface;
        padding: 1 2;
    }

    #help_modal_text {
        content-align: left top;
    }
    """

    BINDINGS = [
        Binding("escape", "dismiss_modal", "Close", show=False),
        Binding("q", "dismiss_modal", "Close", show=False),
        Binding("enter", "dismiss_modal", "Close", show=False),
    ]

    HELP_TEXT = """
[bold]Keyboard Shortcuts[/bold]

@claude <cmd>  Send command to Claude
@gemini <cmd>  Send command to Gemini
@grok <cmd>    Send command to Grok
@all <cmd>     Send command to all AIs

Ctrl+1/2/3     Focus Claude/Gemini/Grok pane
Ctrl+R         Refresh energy state
?              Open this help
q              Quit

Press [bold]Esc[/bold], [bold]Enter[/bold], or [bold]q[/bold] to close.
""".strip()

    def compose(self) -> ComposeResult:
        yield Container(
            Static(self.HELP_TEXT, id="help_modal_text"),
            id="help_modal",
        )

    def action_dismiss_modal(self) -> None:
        self.dismiss(None)


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
    SUB_TITLE = "Multi-AI Coordination • ADHD-Optimized • Full State Management"

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
        # Set workspace_id first (needed by other initializers)
        self.workspace_id = workspace_id or os.getcwd()
        self.layout_manager: Optional[TmuxLayoutManager] = None
        self.command_router = get_command_router()
        
        # Initialize TUI State Manager (coordinates progress, breaks, energy, history)
        self.state_manager = get_state_manager(self.workspace_id)
        
        # Progress tracker (depends on workspace_id)
        self.progress_tracker = get_progress_tracker(self.workspace_id)
        
        # Default active AI target
        self.current_target = "claude"

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

        # Initialize TUI State Manager (coordinates all: progress, breaks, energy, history)
        asyncio.create_task(self._initialize_state_manager())

        # Start background tasks
        self.set_timer(1, self.update_session_timer)
        self.set_timer(5, self.check_energy_level)
        self.set_timer(1, self.update_break_countdown)
        self.set_timer(2, self.update_progress_display)  # Update progress every 2 seconds

        # Log startup and CLI status
        self.query_one("#pane_claude", AIOutputPane).add_output("Dopemux Orchestrator TUI initialized ✅")
        self.query_one("#pane_claude", AIOutputPane).add_output("📊 ConPort progress tracking enabled")

        # Show CLI availability status
        cli_status = self.command_router.get_cli_status_report()
        for line in cli_status.split('\n'):
            self.query_one("#pane_claude", AIOutputPane).add_output(line)

        # Initialize other panes
        self.query_one("#pane_gemini", AIOutputPane).add_output("Ready for commands")
        self.query_one("#pane_grok", AIOutputPane).add_output("Ready for commands")

        # Update active AI count
        available_count = len(self.command_router.get_available_ais())
        self.query_one(StatusInfoPane).update_active_ais(available_count)


    async def _initialize_state_manager(self):
        """Initialize TUI State Manager and show results."""
        result = await self.state_manager.initialize()

        if result.get('warnings'):
            for warning in result['warnings']:
                self.query_one("#pane_claude", AIOutputPane).add_output(f"⚠️  {warning}")
        else:
            successful = result.get('successful_managers', 0)
            total = result.get('total_managers', 0)
            self.query_one("#pane_claude", AIOutputPane).add_output(
                f"✅ All state managers initialized ({successful}/{total})"
            )
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
        """Execute command on specific AI via CommandRouter with ConPort progress tracking."""
        pane = self.query_one(f"#pane_{ai}", AIOutputPane)
        pane.add_output(f"📤 {command}")
        pane.set_status("busy")

        # Check if CLI is available
        if not self.command_router.is_available(ai):
            pane.add_output(f"❌ {ai} CLI not available. Install it first.")
            pane.set_status("error")
            return

        # Coordinate command start (progress, history, break activity)
        await self.state_manager.on_command_start(ai, command)

        # Define callbacks for streaming output
        def on_output(line: str):
            """Handle stdout from AI CLI."""
            pane.add_output(line)

        def on_error(line: str):
            """Handle stderr/errors from AI CLI."""
            pane.add_output(f"⚠️ {line}")

        try:
            # Execute command via router with streaming callbacks
            return_code, final_output = await self.command_router.execute_command(
                ai=ai,
                command=command,
                output_callback=on_output,
                error_callback=on_error,
                timeout=300  # 5 minute timeout
            )

            # Show completion status and update ConPort
            if return_code == 0:
                pane.add_output(f"✅ Command completed successfully")
                pane.set_status("ready")
                complete_result = await self.state_manager.on_command_complete(ai, return_code)
                # Check for break suggestions
                if complete_result.get('break_suggested'):
                    pane.add_output(complete_result.get('break_message', '☕ Break recommended!'))
            else:
                pane.add_output(f"❌ Command failed (exit code: {return_code})")
                pane.set_status("error")
                await self.state_manager.on_command_complete(ai, return_code, f"Exit code: {return_code}")

        except asyncio.TimeoutError:
            pane.add_output("⏰ Command timed out after 5 minutes")
            pane.set_status("error")
            await self.state_manager.on_command_complete(ai, -1, "Timeout after 5 minutes")
        except ValueError as e:
            pane.add_output(f"❌ {e}")
            pane.set_status("error")
            await self.state_manager.on_command_complete(ai, -1, str(e))
        except Exception as e:
            pane.add_output(f"❌ Unexpected error: {e}")
            pane.set_status("error")
            await self.state_manager.on_command_complete(ai, -1, str(e))

            logger.error(f"Error: {e}")
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
        """Check energy level via state manager and update UI."""
        # get_ui_state() refreshes energy; keep this timer for explicit updates.
        self.update_progress_display()

    def update_break_countdown(self) -> None:
        """Update break reminder countdown."""
        async def _update():
            try:
                ui_state = await self.state_manager.get_ui_state()
                break_state = ui_state.get("break", {})
                if break_state and not break_state.get("error"):
                    elapsed_seconds = int(break_state.get("elapsed_seconds", 0))
                    work_duration_minutes = int(
                        getattr(self.state_manager.breaks, "work_duration_minutes", 25)
                    )
                    remaining_seconds = max(0, (work_duration_minutes * 60) - elapsed_seconds)
                    self.query_one(ProgressTrackerPane).update_break_timer(remaining_seconds)
            except Exception as exc:
                logger.debug("Failed to update break countdown: %s", exc)

        asyncio.create_task(_update())

    def update_progress_display(self) -> None:
        """Update all UI elements from TUI State Manager (single optimized call)."""
        async def _update():
            # Single call gets all state (progress, break, energy, history)
            ui_state = await self.state_manager.get_ui_state()

            # Update progress pane
            progress = ui_state.get('progress', {})
            total_commands = progress.get('completed_commands', 0) + progress.get('active_commands', 0)
            self.query_one(ProgressTrackerPane).update_tasks(
                done=progress.get('completed_commands', 0),
                total=max(total_commands, 1)
            )

            if total_commands > 0:
                progress_percent = int((progress.get('completed_commands', 0) / total_commands) * 100)
                self.query_one(ProgressTrackerPane).update_session_progress(progress_percent)

            # Update break timer from break manager (Day 9)
            break_state = ui_state.get('break', {})
            if break_state and not break_state.get('error'):
                elapsed_seconds = break_state.get('elapsed_seconds', 0)
                break_suggested = break_state.get('break_suggested', False)
                break_mandatory = break_state.get('break_mandatory', False)
                work_duration_minutes = int(
                    getattr(self.state_manager.breaks, "work_duration_minutes", 25)
                )
                remaining_seconds = max(0, (work_duration_minutes * 60) - int(elapsed_seconds))
                
                # Update break timer display
                self.query_one(ProgressTrackerPane).update_break_timer(remaining_seconds)
                
                # Day 9: Show break notification if needed
                if break_suggested and not hasattr(self, '_break_notified'):
                    self._break_notified = True
                    self.query_one("#pane_claude", AIOutputPane).add_output(
                        f"☕ Break suggested! You've been working for {break_state.get('elapsed_minutes', 0)} minutes"
                    )
                elif break_mandatory:
                    self.query_one("#pane_claude", AIOutputPane).add_output(
                        f"🛑 Break STRONGLY suggested! {break_state.get('elapsed_minutes', 0)} min elapsed (research-backed: breaks improve ADHD focus)"
                    )

            # Update energy level and apply UI adaptations (Day 10)
            energy_state = ui_state.get('energy', {})
            if energy_state and not energy_state.get('error'):
                energy_level = energy_state.get('level', 'medium')
                ui_adaptations = energy_state.get('ui_adaptations', {})
                
                # Update energy display
                self.query_one(StatusInfoPane).update_energy(energy_level)
                
                # Day 10: Apply energy-based UI color adaptation
                color_intensity = ui_adaptations.get('color_intensity', 1.0)
                for ai_name in ["claude", "gemini", "grok"]:
                    try:
                        pane = self.query_one(f"#pane_{ai_name}", AIOutputPane)
                        # Apply ADHD-optimized color feedback
                        border_color = self._get_energy_border_color(energy_level, color_intensity)
                        pane.styles.border = ("solid", border_color)
                    except Exception as e:
                        logger.warning(f"Could not apply energy color to {ai_name}: {e}")

        # Run async update
        asyncio.create_task(_update())

    def _get_energy_border_color(self, energy_level: str, intensity: float) -> str:
        """
        Get border color based on energy level (ADHD visual feedback).
        
        Day 10: Energy-aware UI adaptation
        Colors:
        - very_low/low: Dim blue (calming, suggests rest)
        - medium: Green (neutral, balanced)
        - high: Bright green (energized)
        - hyperfocus: Yellow (caution, take breaks!)
        """
        colors = {
            "very_low": "#4080ff" if intensity > 0.7 else "#305080",  # Dim blue
            "low": "#60a0ff" if intensity > 0.7 else "#406080",       # Light blue
            "medium": "#40ff40" if intensity > 0.7 else "#308030",    # Green
            "high": "#60ff60",                                         # Bright green
            "hyperfocus": "#ffff40"                                    # Yellow warning
        }
        return colors.get(energy_level, "#40ff40")  # Default: green

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
        self.push_screen(HelpModal())

    def action_refresh_energy(self) -> None:
        """Manually refresh energy level from ADHD Engine."""
        self.check_energy_level()
        self.query_one("#pane_claude", AIOutputPane).add_output("🔄 Energy level refreshed")

    async def action_quit(self) -> None:
        """Clean up and quit the application."""
        # Finalize all managers via state manager
        await self.state_manager.close()
        await super().action_quit()


def run_orchestrator_tui(workspace_id: str = None):
    """Launch the Dopemux Orchestrator TUI."""
    app = DopemuxOrchestratorTUI(workspace_id=workspace_id)
    app.run()


if __name__ == "__main__":
    run_orchestrator_tui()
