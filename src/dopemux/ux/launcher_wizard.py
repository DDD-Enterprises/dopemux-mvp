"""
Dopemux Cockpit Launcher Wizard

A highly visual, interactive terminal UI for selecting a role and monitoring
the boot sequence of Dopemux services.
"""
import sys
import time
import subprocess
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import List, Optional, Tuple

from rich.align import Align
from rich.console import Console, Group
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.spinner import Spinner
from rich.table import Table
from rich.text import Text

from ..console import console as shared_console
from ..claude.instruction_manager import InstructionManager
from ..roles.catalog import ROLE_CATALOG, RoleSpec
from ..ui.theme import StatusChip
from .interactive_prompts import InteractivePrompts

DOPEMUX_HEADER_TEXT = Text.from_markup(
    """
[magenta]
  ,-----.                        ,-----.
  |  .--. | ,--.--. ,---.  ,---. |  .--. | ,---.  ,---. ,--.--.
  |  '--' | |  .--'| .-. || .-. :|  '--' |(  .-' | .-. ||  .--'
  |  | --'  |  |   ' '-' '' '-' '|  | --' .-'  `)' '-' '|  |
  `--'      `--'    `---'  `---' `--'      `----'  `---' `--'
[/]
[mint.soft]Dopamine-driven multiplexing for superintelligent agents.[/]
""",
    justify="center",
)

# --- State Management ---
class LauncherState(Enum):
    ROLE_SELECTION = auto()
    BOOT_SEQUENCE = auto()


class BootStepStatus(Enum):
    PENDING = ("[text.dim]●[/]", "text.dim")
    LOADING = (Spinner("dots", style="warning"), "warning")
    SUCCESS = ("[success]✓[/]", "success")
    FAILURE = ("[error]✗[/]", "error")

    def __init__(self, icon, style):
        self.icon = icon
        self.style = style


@dataclass
class BootStep:
    name: str
    status: BootStepStatus = BootStepStatus.PENDING
    message: str = ""


# --- Core Wizard Class ---
class LauncherWizard:
    """Manages the state and rendering of the launcher UI."""

    def __init__(self, console: Console):
        self.console = console
        self.state = LauncherState.ROLE_SELECTION
        self.roles: List[Tuple[str, RoleSpec]] = self._load_all_roles()
        self.selected_index = 0
        self.error_message: Optional[str] = None

        self.boot_steps = [
            BootStep("Configuring Worktree"),
            BootStep("Booting MCP Services"),
            BootStep("Connecting to Docker"),
            BootStep("Starting Activity Monitor"),
        ]
        self._boot_log_messages: List[Text] = [
            Text.from_markup(StatusChip.LIVE.render("Launcher initializing."))
        ]
        self.live = Live(
            self._generate_layout(),
            console=self.console,
            screen=True,
            auto_refresh=False,
        )

    def _load_all_roles(self) -> List[Tuple[str, RoleSpec]]:
        """Loads static roles and dynamic personas, combining them into one list."""
        all_roles = list(ROLE_CATALOG.items())

        try:
            im = InstructionManager(Path.cwd())
            dynamic_personas = im.list_personas()
            for persona_key in dynamic_personas:
                # Add only if not already in catalog
                if persona_key not in ROLE_CATALOG:
                    spec = RoleSpec(
                        key=persona_key,
                        label=persona_key.replace("_", " ").replace("-", " ").title(),
                        description=f"Dynamic Persona (.claude/personas/{persona_key}.agent.md)",
                        attention_state="focused",
                        required_servers=["conport"],
                        optional_servers=["pal", "serena"],
                        metamcp_namespace=f"dopemux-{persona_key}",
                        profile_name=persona_key,
                    )
                    all_roles.append((persona_key, spec))
        except Exception as e:
            self.add_log(f"Warning: Could not load dynamic personas: {e}", style="warning")
            
        return all_roles

    def _generate_layout(self) -> Layout:
        """Creates the `rich` Layout based on the current wizard state."""
        layout = Layout()
        layout.split(
            Layout(DOPEMUX_HEADER_TEXT, name="header", size=8),
            Layout(name="main"),
            Layout(self._build_footer(), name="footer", size=3),
        )

        if self.state == LauncherState.ROLE_SELECTION:
            layout["main"].update(self._build_role_selection_panel())
        elif self.state == LauncherState.BOOT_SEQUENCE:
            layout["main"].update(self._build_boot_sequence_panel())
        
        return layout

    def _build_role_selection_panel(self) -> Panel:
        """Builds the renderable for the role selection screen."""
        table = Table(
            box=None, expand=True, show_header=False, padding=(0, 1)
        )
        table.add_column("Key", no_wrap=True, style="magenta", width=20)
        table.add_column("Label", no_wrap=True, style="mint.soft")
        table.add_column("Description", style="dim")

        # Handle scrolling
        max_rows = 15
        start_idx = max(0, self.selected_index - max_rows // 2)
        end_idx = min(len(self.roles), start_idx + max_rows)
        
        if len(self.roles) > max_rows and end_idx == len(self.roles):
            start_idx = len(self.roles) - max_rows

        for i in range(start_idx, end_idx):
            key, role = self.roles[i]
            style = "row.active" if i == self.selected_index else ""
            selector = "▶ " if i == self.selected_index else "  "
            table.add_row(
                f"{selector}{key}",
                role.label,
                role.description,
                style=style,
            )

        return Panel(
            table,
            title=f"[panel.title]{StatusChip.LIVE.render('Select agent role')}[/panel.title]",
            border_style="info",
            expand=True,
        )

    def _build_boot_sequence_panel(self) -> Panel:
        """Builds the renderable for the boot sequence screen."""
        boot_layout = Layout()
        boot_layout.split_row(
            Layout(self._build_boot_steps_table(), name="steps", ratio=1),
            Layout(self._build_boot_log_panel(), name="logs", ratio=2),
        )
        
        role_key, role_spec = self.roles[self.selected_index]
        title = (
            f"[panel.title]{StatusChip.LIVE.render('Booting')} "
            f"[mint.soft]{role_spec.label}[/mint.soft] [text.dim]({role_key})[/text.dim][/panel.title]"
        )
        return Panel(boot_layout, title=title, border_style="info")

    def _build_boot_steps_table(self) -> Table:
        """Creates the table showing the status of each boot step."""
        table = Table(box=None, expand=True, show_header=False)
        table.add_column("Icon", width=3)
        table.add_column("Step")

        for step in self.boot_steps:
            renderable = step.status.icon
            table.add_row(renderable, Text(step.name, style=step.status.style))
        return table

    def _build_boot_log_panel(self) -> Panel:
        """Creates the panel for displaying real-time log messages."""
        # Display the last 15 log messages to prevent overflow
        log_text = Text("\n").join(self._boot_log_messages[-15:])
        return Panel(
            Align.bottom(log_text),
            title="[panel.title]Logs[/panel.title]",
            border_style="table.border",
            expand=True,
        )

    def _build_footer(self) -> Text:
        """Builds the footer with instructions."""
        if self.state == LauncherState.ROLE_SELECTION:
            return Text.from_markup(
                StatusChip.LOGGED.render("Select a role from the prompt to continue, or cancel to quit."),
                justify="center",
            )
        return Text.from_markup(
            StatusChip.LIVE.render("Boot sequence in progress."),
            justify="center",
        )

    def _refresh_live_view(self):
        """Updates the Live display with the new layout."""
        self.live.update(self._generate_layout(), refresh=True)

    # --- Public API for state transitions and updates ---
    def run_role_selection(self) -> Optional[str]:
        """
        Runs the progressive interactive role selection prompt.
        Returns the selected role key or None if the user quits.
        """
        attention_complexity = {
            "scattered": 0.1,
            "focused": 0.3,
            "variable": 0.6,
            "hyperfocused": 0.7,
        }
        actions = [
            {
                "name": key,
                "description": f"{role.label} - {role.description}",
                "complexity": attention_complexity.get(role.attention_state, 0.5),
            }
            for key, role in self.roles
        ]

        selected_role = InteractivePrompts().ask_action_selection(
            actions,
            "Select agent role",
        )
        if not selected_role:
            return None

        for idx, (key, _role) in enumerate(self.roles):
            if key == selected_role:
                self.selected_index = idx
                self.state = LauncherState.BOOT_SEQUENCE
                return key

        self.error_message = f"Unknown selected role: {selected_role}"
        return None

    def update_boot_step(self, step_name: str, status: BootStepStatus, message: str = ""):
        """
        Finds a boot step by name and updates its status and message.
        Refreshes the view afterwards.
        """
        for step in self.boot_steps:
            if step.name == step_name:
                step.status = status
                step.message = message
                if status != BootStepStatus.LOADING:
                    self.add_log(f"[{status.style}]{step_name}: {status.name.capitalize()}[/]")
                break
        self._refresh_live_view()

    def add_log(self, message: str, style: str = "dim"):
        """Adds a message to the boot log view."""
        self._boot_log_messages.append(
            Text.from_markup(f"[{style}][{time.strftime('%H:%M:%S')}] {message}[/{style}]")
        )
        if self.state == LauncherState.BOOT_SEQUENCE:
            self._refresh_live_view()

    def finish(self, success: bool = True, final_message: str = "Setup complete."):
        """Stops the Live display with a final message."""
        if success:
            footer_text = Text.from_markup(StatusChip.LOGGED.render(final_message), justify="center")
        else:
            footer_text = Text.from_markup(StatusChip.BLOCKER.render(final_message), justify="center")
        
        self.live.update(self._generate_layout(), refresh=True)
        time.sleep(1.5) # Allow user to see the final state
        self.live.stop()
        self.console.print(footer_text)


def start_wizard() -> Optional[Tuple[str, LauncherWizard]]:
    """
    Initializes and runs the Dopemux Launcher Wizard.

    This function handles the initial role selection phase. If a role is
    selected, it returns the role's key and the wizard instance, which
    can then be used to display the boot sequence.

    Returns:
        A tuple of (role_key, wizard_instance) if a role is selected.
        (None, None) if the user quits.
    """
    wizard = LauncherWizard(shared_console)
    try:
        role_key = wizard.run_role_selection()
        if role_key:
            wizard.live.start()
            wizard._refresh_live_view()
            return role_key, wizard
        else:
            if wizard.live.is_started:
                wizard.live.stop()
            shared_console.print("[text.dim]Role selection cancelled.[/]")
            return None, None
    except Exception as e:
        if wizard.live.is_started:
            wizard.live.stop()
        shared_console.print(StatusChip.BLOCKER.render(f"Unexpected launcher error: {e}"), style="error")
        return None, None
