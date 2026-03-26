"""
DØPEMÜX Boot Sequence and Splash Screens
"""
import time
from rich.live import Live
from rich.console import Group
from rich.text import Text
from rich.panel import Panel
from .theme import Glyphs

DOPEMUX_ASCII = """
[mint]
██████╗  [ritual.cyan]Ø[/ritual.cyan] ██████╗ ███████╗[violet]███╗   ███╗[/violet]██╗   ██╗██╗  ██╗
██╔══██╗   ██╔══██╗██╔════╝[violet]████╗ ████║[/violet]██║   ██║╚██╗██╔╝
██║  ██║   ██████╔╝█████╗  [violet]██╔████╔██║[/violet]██║   ██║ ╚███╔╝ 
██║  ██║   ██╔═══╝ ██╔══╝  [violet]██║╚██╔╝██║[/violet]██║   ██║ ██╔██╗ 
██████╔╝   ██║     ███████╗[violet]██║ ╚═╝ ██║[/violet]╚██████╔╝██╔╝ ██╗
╚═════╝    ╚═╝     ╚══════╝[violet]╚═╝     ╚═╝[/violet] ╚═════╝ ╚═╝  ╚═╝
[/mint]
"""

def boot_sequence():
    """
    Displays a cinematic boot sequence simulating neural link mounting.
    """
    messages = [
        ("Initializing flight-deck telemetry...", "OK", "mint"),
        ("Mounting neural context...", "ACTIVE", "ritual.cyan"),
        ("Synchronizing MCP tool boundaries...", "OK", "mint"),
        ("Calibrating cognitive sensors...", "ENGAGED", "gilt.edge"),
    ]
    
    with Live(Text("", justify="center"), refresh_per_second=15, transient=True) as live:
        current_text = Text.from_markup(DOPEMUX_ASCII)
        live.update(current_text)
        time.sleep(0.4)
        
        for msg, status, color in messages:
            current_text.append("\n")
            current_text.append(f"{Glyphs.SUCCESS} {msg} ", style="text.dim")
            live.update(current_text)
            time.sleep(0.3)
            current_text.append(f"[{status}]", style=f"bold {color}")
            live.update(current_text)
            time.sleep(0.1)
            
        time.sleep(0.5)
