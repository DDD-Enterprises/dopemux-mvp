"""
Dopemux Launch Wizard.

Provides a high-flair, interactive UI for selecting AI roles and configuring
Dopemux sessions with ADHD-optimized visual feedback.
"""

import os
import sys
from pathlib import Path
from typing import List, Optional, Tuple

from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.layout import Layout

from ..roles.catalog import ROLE_CATALOG, RoleSpec
from ..ui.theme import Glyphs, SERUM_MINT, GREMLIN_PINK, RITUAL_CYAN

console = Console()

class LaunchWizard:
    """
    Interactive terminal wizard for Dopemux session startup.
    
    Features:
    - Keyboard-driven role selection.
    - Real-time details and explanation preview.
    - ADHD-friendly high-contrast styling.
    """
    
    def __init__(self):
        self.roles = list(ROLE_CATALOG.values())
        self.selected_index = 0
        self.aborted = False
        
    def _get_layout(self) -> Layout:
        """Build the responsive wizard layout."""
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=3)
        )
        layout["main"].split_row(
            Layout(name="list", ratio=1),
            Layout(name="details", ratio=2)
        )
        return layout

    def _render_header(self) -> Panel:
        """Render the wizard header."""
        return Panel(
            Text.assemble(
                (f"{Glyphs.BRAND_MARK} ", f"bold {SERUM_MINT}"),
                ("Dopemux Launch Cockpit ", f"bold {RITUAL_CYAN}"),
                (f"{Glyphs.WRENCH}", "text.dim")
            ),
            border_style=RITUAL_CYAN,
            padding=(0, 2)
        )

    def _render_role_list(self) -> Panel:
        """Render the selectable list of roles."""
        table = Table.grid(expand=True)
        table.add_column()
        
        for i, role in enumerate(self.roles):
            style = f"bold {SERUM_MINT}" if i == self.selected_index else "text.dim"
            prefix = f"{Glyphs.ARROW_RIGHT} " if i == self.selected_index else "  "
            table.add_row(Text(f"{prefix}{role.label}", style=style))
            
        return Panel(table, title="[mint]Select Role[/]", border_style=SERUM_MINT)

    def _render_details(self) -> Panel:
        """Render detailed information for the currently highlighted role."""
        role = self.roles[self.selected_index]
        
        content = Group(
            Text(f"\n{role.description}\n", style="text"),
            Text.assemble(("Attention State: ", "bold"), (role.attention_state.upper(), f"bold {GREMLIN_PINK}"), "\n"),
            Text("\nRequired MCP Servers:", style="bold"),
            *[Text(f" • {s}", style="text.dim") for s in (role.required_servers or ["conport"])],
            Text("\nOptional Extras:", style="bold"),
            *[Text(f" • {s}", style="text.dim") for s in (role.optional_servers or ["none"])]
        )
        
        return Panel(
            content, 
            title=f"[{SERUM_MINT}]Role Analysis: {role.label}[/]", 
            border_style=RITUAL_CYAN,
            padding=(1, 2)
        )

    def _render_footer(self) -> Text:
        """Render the navigation footer."""
        return Text.assemble(
            ("\n ↑/↓ ", f"bold {SERUM_MINT}"), ("Move", "text.dim"),
            ("   ENTER ", f"bold {SERUM_MINT}"), ("Select Role", "text.dim"),
            ("   ESC/Q ", f"bold {GREMLIN_PINK}"), ("Cancel", "text.dim")
        )

    def run(self) -> Optional[str]:
        """Run the interactive wizard loop."""
        try:
            import readchar
        except ImportError:
            console.print("[error]Missing dependency: 'readchar'[/error]")
            console.print("[info]Fix: pip install readchar[/info]")
            return None
        
        layout = self._get_layout()
        
        with Live(layout, console=console, screen=True, auto_refresh=True):
            while True:
                # Update layout components
                layout["header"].update(self._render_header())
                layout["list"].update(self._render_role_list())
                layout["details"].update(self._render_details())
                layout["footer"].update(self._render_footer())
                
                # Handle input
                key = readchar.readkey()
                
                if key == readchar.key.UP:
                    self.selected_index = (self.selected_index - 1) % len(self.roles)
                elif key == readchar.key.DOWN:
                    self.selected_index = (self.selected_index + 1) % len(self.roles)
                elif key in (readchar.key.ENTER, readchar.key.CR):
                    return self.roles[self.selected_index].key
                elif key in (readchar.key.ESC, 'q', 'Q'):
                    self.aborted = True
                    return None

def start_wizard() -> Optional[str]:
    """Helper to run the wizard and handle result."""
    try:
        wizard = LaunchWizard()
        return wizard.run()
    except Exception as e:
        console.print(f"[error]Wizard failed: {e}[/error]")
        return None
