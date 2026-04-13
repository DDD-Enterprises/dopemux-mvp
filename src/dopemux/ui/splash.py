"""
Dopemux boot sequence and startup banner rendering.
"""

from __future__ import annotations

import time

from rich.live import Live
from rich.text import Text

from .theme import Glyphs, RenderMode, get_render_mode

DOPEMUX_STARTUP_BANNER = """\
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   ██████╗  ██████╗ ██████╗ ███████╗███╗   ███╗██╗   ██╗██╗  ██╗             ║
║   ██╔══██╗██╔═══██╗██╔══██╗██╔════╝████╗ ████║██║   ██║╚██╗██╔╝             ║
║   ██║  ██║██║   ██║██████╔╝█████╗  ██╔████╔██║██║   ██║ ╚███╔╝              ║
║   ██║  ██║██║   ██║██╔═══╝ ██╔══╝  ██║╚██╔╝██║██║   ██║ ██╔██╗              ║
║   ██████╔╝╚██████╔╝██║     ███████╗██║ ╚═╝ ██║╚██████╔╝██╔╝ ██╗             ║
║   ╚═════╝  ╚═════╝ ╚═╝     ╚══════╝╚═╝     ╚═╝ ╚═════╝ ╚═╝  ╚═╝             ║
║        ║             ║                                ║                     ║
║        '             '                                '                     ║
║                                                                              ║
║         [ deterministic core ]   [ memory mesh ]   [ operator ]            ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""


def _banner_markup() -> str:
    """Return Rich markup for the branded startup banner."""
    frame = "#00ffff"
    logo = [
        "#00ffff",
        "#00f0ff",
        "#00e1ff",
        "#00d2ff",
        "#5aaaff",
        "#8c82ff",
        "#b478ff",
    ]
    drip_bar = "#78b4ff"
    drip_tick = "#b478ff"
    tag_core = "#ff50dc"
    tag_mesh = "#b478ff"
    tag_operator = "#00ffff"

    return "\n".join(
        [
            f"[{frame}]╔══════════════════════════════════════════════════════════════════════════════╗[/]",
            f"[{frame}]║[/]                                                                              [{frame}]║[/]",
            (
                f"[{frame}]║   [/]"
                f"[{logo[0]}]██████╗[/][{logo[1]}]  ██████╗[/][{logo[2]}] ██████╗[/]"
                f"[{logo[3]}] ███████╗[/][{logo[4]}]███╗   ███╗[/][{logo[5]}]██╗   ██╗[/]"
                f"[{logo[6]}]██╗  ██╗[/]"
                f"[{frame}]             ║[/]"
            ),
            (
                f"[{frame}]║   [/]"
                f"[{logo[0]}]██╔══██╗[/][{logo[1]}]██╔═══██╗[/][{logo[2]}]██╔══██╗[/]"
                f"[{logo[3]}]██╔════╝[/][{logo[4]}]████╗ ████║[/][{logo[5]}]██║   ██║[/]"
                f"[{logo[6]}]╚██╗██╔╝[/]"
                f"[{frame}]             ║[/]"
            ),
            (
                f"[{frame}]║   [/]"
                f"[{logo[0]}]██║  ██║[/][{logo[1]}]██║   ██║[/][{logo[2]}]██████╔╝[/]"
                f"[{logo[3]}]█████╗  [/][{logo[4]}]██╔████╔██║[/][{logo[5]}]██║   ██║[/]"
                f"[{logo[6]}] ╚███╔╝[/]"
                f"[{frame}]              ║[/]"
            ),
            (
                f"[{frame}]║   [/]"
                f"[{logo[0]}]██║  ██║[/][{logo[1]}]██║   ██║[/][{logo[2]}]██╔═══╝ [/]"
                f"[{logo[3]}]██╔══╝  [/][{logo[4]}]██║╚██╔╝██║[/][{logo[5]}]██║   ██║[/]"
                f"[{logo[6]}] ██╔██╗[/]"
                f"[{frame}]              ║[/]"
            ),
            (
                f"[{frame}]║   [/]"
                f"[{logo[0]}]██████╔╝[/][{logo[1]}]╚██████╔╝[/][{logo[2]}]██║     [/]"
                f"[{logo[3]}]███████╗[/][{logo[4]}]██║ ╚═╝ ██║[/][{logo[5]}]╚██████╔╝[/]"
                f"[{logo[6]}]██╔╝ ██╗[/]"
                f"[{frame}]             ║[/]"
            ),
            (
                f"[{frame}]║   [/]"
                f"[{logo[0]}]╚═════╝ [/][{logo[1]}] ╚═════╝ [/][{logo[2]}]╚═╝     [/]"
                f"[{logo[3]}]╚══════╝[/][{logo[4]}]╚═╝     ╚═╝[/][{logo[5]}] ╚═════╝ [/]"
                f"[{logo[6]}]╚═╝  ╚═╝[/]"
                f"[{frame}]             ║[/]"
            ),
            f"[{frame}]║        [/{frame}][{drip_bar}]║[/][{frame}]             [{drip_bar}]║[/][{frame}]                                [{drip_bar}]║[/][{frame}]                     ║[/]",
            f"[{frame}]║        [/{frame}][{drip_tick}]'[/][{frame}]             [{drip_tick}]'[/][{frame}]                                [{drip_tick}]'[/][{frame}]                     ║[/]",
            f"[{frame}]║[/]                                                                              [{frame}]║[/]",
            (
                f"[{frame}]║         [/]"
                f"[{tag_core}][ deterministic core ][/]"
                f"[{frame}]   [/]"
                f"[{tag_mesh}][ memory mesh ][/]"
                f"[{frame}]   [/]"
                f"[{tag_operator}][ operator ][/]"
                f"[{frame}]            ║[/]"
            ),
            f"[{frame}]║[/]                                                                              [{frame}]║[/]",
            f"[{frame}]╚══════════════════════════════════════════════════════════════════════════════╝[/]",
        ]
    )


def render_startup_banner(mode: RenderMode | None = None) -> Text:
    """Render the startup banner for the active render mode."""
    active_mode = mode or get_render_mode()
    if active_mode == RenderMode.PLAIN:
        return Text(DOPEMUX_STARTUP_BANNER.rstrip("\n"))
    return Text.from_markup(_banner_markup())


def boot_sequence() -> None:
    """Display the startup banner and boot-status sequence."""
    messages = [
        ("Initializing flight-deck telemetry...", "OK", "mint"),
        ("Mounting memory mesh...", "ACTIVE", "violet"),
        ("Synchronizing deterministic core...", "OK", "magenta"),
        ("Confirming operator surface...", "READY", "info"),
    ]

    with Live(Text("", justify="center"), refresh_per_second=15, transient=True) as live:
        current_text = render_startup_banner()
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
