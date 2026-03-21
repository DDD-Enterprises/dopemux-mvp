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
from typing import Any, Dict, List, Optional, Tuple, Union

try:
    import readchar
except ImportError:  # pragma: no cover - exercised in integration environments without optional TUI deps
    readchar = None
from rich.align import Align
from rich.console import Console, Group
from rich.layout import Layout
from rich.live import Live
from rich.spinner import Spinner
from rich.style import Style
from rich.text import Text

from ..claude.instruction_manager import InstructionManager
from ..roles.catalog import ROLE_CATALOG, RoleSpec
from ..ui.theme import (
    Glyphs,
    INK_BLACK,
    SERUM_MINT,
    StatusChip,
    styled_panel,
    styled_table,
)
from ..ui.voice import VoiceEngine, VoiceMode

console = Console()
VOICE = VoiceEngine(mode=VoiceMode.UI_STRICT, is_scattered=True)

DOPEMUX_HEADER_TEXT = Text.from_markup(
    f"""
[magenta]
  {Glyphs.BRAND_MARK}
  ,-----.                        ,-----.
  |  .--. | ,--.--. ,---.  ,---. |  .--. | ,---.  ,---. ,--.--.
  |  '--' | |  .--'| .-. || .-. :|  '--' |(  .-' | .-. ||  .--'
  |  | --'  |  |   ' '-' '' '-' '|  | --' .-'  `)' '-' '|  |
  `--'      `--'    `---'  `---' `--'      `----'  `---' `--'
[/]
[subheading]Dopamine-driven multiplexing for superintelligent agents.[/subheading]
[text.dim]{StatusChip.LIVE.render("Pick a role. Boot clean. Keep the next step visible.")}[/text.dim]
""",
    justify="center",
)

# --- State Management ---
class LauncherState(Enum):
    ROLE_SELECTION = auto()
    BOOT_SEQUENCE = auto()


class BootStepStatus(Enum):
    PENDING = ("[text.dim]●[/text.dim]", "text.dim")
    LOADING = (Spinner("dots", style="spinner"), "warning")
    SUCCESS = ("[success]✓[/success]", "success")
    FAILURE = ("[error]✗[/error]", "error")

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
            Text.from_markup(StatusChip.LIVE.render("Cockpit initializing."))
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
            self.add_log(
                StatusChip.EDGE.render(f"Dynamic persona scan slipped: {e}"),
                style="warning",
            )
            
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

    def _build_role_selection_panel(self) -> Any:
        """Builds the renderable for the role selection screen."""
        table = styled_table(
            "Role Deck",
            ("Key", {"no_wrap": True, "style": "magenta", "width": 20}),
            ("Label", {"no_wrap": True, "style": "subheading"}),
            ("Description", {"style": "text.dim"}),
            box=None,
            expand=True,
            show_header=False,
            padding=(0, 1),
        )

        # Handle scrolling
        max_rows = 15
        start_idx = max(0, self.selected_index - max_rows // 2)
        end_idx = min(len(self.roles), start_idx + max_rows)
        
        if len(self.roles) > max_rows and end_idx == len(self.roles):
            start_idx = len(self.roles) - max_rows

        for i in range(start_idx, end_idx):
            key, role = self.roles[i]
            style = Style(bgcolor=SERUM_MINT, color=INK_BLACK) if i == self.selected_index else Style()
            selector = "▶ " if i == self.selected_index else "  "
            table.add_row(
                f"{selector}{key}",
                role.label,
                role.description,
                style=style,
            )

        return styled_panel(
            table,
            title=StatusChip.LIVE.render("Select agent role"),
            border_style="info",
            expand=True,
        )

    def _build_boot_sequence_panel(self) -> Any:
        """Builds the renderable for the boot sequence screen."""
        boot_layout = Layout()
        boot_layout.split_row(
            Layout(self._build_boot_steps_table(), name="steps", ratio=1),
            Layout(self._build_boot_log_panel(), name="logs", ratio=2),
        )
        
        role_key, role_spec = self.roles[self.selected_index]
        title = StatusChip.LIVE.render(f"Booting {role_spec.label} ({role_key})")
        return styled_panel(boot_layout, title=title, border_style="info")

    def _build_boot_steps_table(self) -> Any:
        """Creates the table showing the status of each boot step."""
        table = styled_table(
            "Boot Steps",
            ("Icon", {"width": 3}),
            "Step",
            box=None,
            expand=True,
            show_header=False,
            padding=(0, 1),
        )

        for step in self.boot_steps:
            renderable = step.status.icon
            table.add_row(renderable, Text(step.name, style=step.status.style))
        return table

    def _build_boot_log_panel(self) -> Any:
        """Creates the panel for displaying real-time log messages."""
        # Display the last 15 log messages to prevent overflow
        log_text = Text("\n").join(self._boot_log_messages[-15:])
        return styled_panel(
            Align.bottom(log_text),
            title=StatusChip.LOGGED.render("Boot log"),
            border_style="panel.border",
            expand=True,
        )

    def _build_footer(self) -> Text:
        """Builds the footer with instructions."""
        if self.state == LauncherState.ROLE_SELECTION:
            return Text.from_markup(
                "[text.dim]Use ↑/↓ to navigate, Enter to select, Ctrl+C to quit[/text.dim]",
                justify="center",
            )
        return Text.from_markup(StatusChip.LOGGED.render("Boot sequence in progress..."), justify="center")

    def _refresh_live_view(self):
        """Updates the Live display with the new layout."""
        self.live.update(self._generate_layout(), refresh=True)

    # --- Public API for state transitions and updates ---
    def run_role_selection(self) -> Optional[str]:
        """
        Runs the interactive loop for role selection.
        Returns the selected role key or None if the user quits.
        """
        if readchar is None:
            raise RuntimeError("readchar is required for interactive role selection")
        try:
            while True:
                key = readchar.readkey()
                if key in (readchar.key.CTRL_C, "q"):
                    raise KeyboardInterrupt

                if self.state == LauncherState.ROLE_SELECTION:
                    if key == readchar.key.UP:
                        self.selected_index = (self.selected_index - 1) % len(self.roles)
                    elif key == readchar.key.DOWN:
                        self.selected_index = (self.selected_index + 1) % len(self.roles)
                    elif key in (readchar.key.ENTER, readchar.key.CR):
                        self.state = LauncherState.BOOT_SEQUENCE
                        self._refresh_live_view()
                        return self.roles[self.selected_index][0]
                    self._refresh_live_view()
        except KeyboardInterrupt:
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
                    chip = StatusChip.LOGGED if status == BootStepStatus.SUCCESS else StatusChip.BLOCKER
                    self.add_log(chip.render(f"{step_name}: {status.name.capitalize()}"), style=status.style)
                break
        self._refresh_live_view()

    def add_log(self, message: str, style: str = "text.dim"):
        """Adds a message to the boot log view."""
        self._boot_log_messages.append(
            Text.from_markup(f"[text.dim][{time.strftime('%H:%M:%S')}][/text.dim] {message}")
        )
        if self.state == LauncherState.BOOT_SEQUENCE:
            self._refresh_live_view()

    def finish(self, success: bool = True, final_message: str = "Setup complete."):
        """Stops the Live display with a final message."""
        if success:
            success_message = final_message if final_message != "Setup complete." else VOICE.get_aftercare()
            footer_text = Text.from_markup(StatusChip.AFTERCARE.render(success_message), justify="center")
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
    if readchar is None:
        console.print(StatusChip.BLOCKER.render("Missing dependency: readchar"))
        console.print(StatusChip.LIVE.render("Fix: pip install readchar"))
        return None, None
        
    wizard = LauncherWizard(console)
    try:
        wizard.live.start()
        role_key = wizard.run_role_selection()
        if role_key:
            return role_key, wizard
        else:
            wizard.live.stop()
            console.print(StatusChip.EDGE.render("Role selection cancelled."))
            return None, None
    except Exception as e:
        if wizard.live.is_started:
            wizard.live.stop()
        console.print(StatusChip.BLOCKER.render(f"Unexpected launcher error: {e}"))
        return None, None
