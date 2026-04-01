"""Dopemux CLI Theme - Single source of truth for all CLI/TUI styling.

This module defines the neon mint palette, Rich Theme object, glyph constants,
status chips, and helper factories that every dopemux CLI command must use.

Usage:
from rich.console import Console
    from dopemux.ui.theme import DOPEMUX_THEME, Glyphs, StatusChip, styled_table, styled_panel

    console = Console(theme=DOPEMUX_THEME)
    console.print(f"{Glyphs.SUCCESS} All checks passed", style="success")
    console.print(StatusChip.LIVE.render("Pipeline running"))
"""

from __future__ import annotations

import enum
import os
from typing import Any

from datetime import datetime, timezone

from rich.box import ROUNDED, SIMPLE
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.theme import Theme


def get_active_theme_name() -> str:
    """Return the name of the active theme from environment or default.

    This function is intentionally kept free of config imports and heavy logic
    to avoid import-time cycles. Higher-level code (CLI/config) should
    initialize and propagate the theme as needed.
    """
    env_theme = os.environ.get("DOPEMUX_THEME")
    if env_theme:
        return env_theme.lower()

    # Fallback default theme when no environment override is set.
    return "pastel-neon-dreams"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Dynamic Color Palette (Legacy / Compatibility)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# These are maintained for modules like tmux/theme.py that import them directly.
# They are now dynamic properties that reflect the active theme.

_PALETTES = {
    "mint-mojo": {
        "cyan": "#7DFBF6", "mint": "#94FADB", "pink": "#FF8BD1", "violet": "#9B78FF", 
        "gold": "#F5F26D", "black": "#020617", "navy": "#041628", "grey": "#94A3B8"
    },
    "pastel-neon-dreamscape": {
        "cyan": "#00FFFF", "mint": "#66FF66", "pink": "#FF00FF", "violet": "#FF66FF",
        "gold": "#FFFF00", "black": "#000000", "navy": "#080808", "grey": "#A9A9A9"
    },
    "pastel-neon-dreams": {
        "cyan": "#00FFFF", "mint": "#7FFFD4", "pink": "#FF69B4", "violet": "#FFB2FF",
        "gold": "#FFFFE0", "black": "#000000", "navy": "#080808", "grey": "#A9A9A9"
    }
}

_active_palette = _PALETTES.get(get_active_theme_name(), _PALETTES["pastel-neon-dreams"])

RITUAL_CYAN = _active_palette["cyan"]
SERUM_MINT = _active_palette["mint"]
MINT_BRIGHT = _active_palette["cyan"]
MINT_DIM = _active_palette["grey"]
GREMLIN_PINK = _active_palette["pink"]
AFTERCARE_VIOLET = _active_palette["violet"]
VIOLET_DIM = "#800080"
GILT_EDGE = _active_palette["gold"]
SAINT_GOLD = "#FFCF78"
INK_BLACK = _active_palette["black"]
VOID_NAVY = _active_palette["navy"]
VELVET_PLUM = "#1A001A"
TEXT_PRIMARY = "#E5E5E5"
TEXT_SECONDARY = _active_palette["grey"]

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Theme Definitions & Multi-Theme Engine
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def build_theme(name: str) -> Theme:
    """Construct a Rich Theme object for the specified palette."""
    if name == "mint-mojo":
        return Theme({
            "mint": "bold #7DFBF6",
            "mint.soft": "#94FADB",
            "mint.bright": "bold #B4FFEE",
            "mint.dim": "#4A9E94",
            "magenta": "bold #FF8BD1",
            "violet": "#9B78FF",
            "violet.dim": "#6B4FBF",
            "text": "#E2E8F0",
            "text.dim": "#94A3B8",
            "text.muted": "#64748B",
            "text.disabled": "#475569",
            "text.emphasis": "bold #94FADB",
            "heading": "bold #7DFBF6",
            "subheading": "bold #94FADB",
            "label": "#94A3B8",
            "success": "#94FADB",
            "error": "bold #FF8BD1",
            "warning": "#F5F26D",
            "gold": "#F5F26D",
            "amber": "#FFCF78",
            "info": "#7DFBF6",
            "debug": "#9B78FF",
            "hazard": "#F5F26D",
            "gilt.edge": "#F5F26D",
            "chip.live": "bold #7DFBF6",
            "chip.override": "bold #F5F26D",
            "chip.blocker": "bold #FF8BD1",
            "chip.logged": "#94FADB",
            "chip.aftercare": "#9B78FF",
            "chip.edge": "bold #7DFBF6",
            "table.header": "bold #7DFBF6",
            "table.border": "#4A9E94",
            "table.row.alt": "on #041628",
            "panel.border": "#4A9E94",
            "panel.title": "bold #94FADB",
            "bar.complete": "#7DFBF6",
            "bar.remaining": "#1A0520",
            "bar.pulse": "#FF8BD1",
            "spinner": "#7DFBF6",
            "severity.healthy": "#94FADB",
            "severity.warning": "#F5F26D",
            "severity.critical": "bold #FF8BD1",
            "severity.unknown": "#64748B",
            "rule.line": "#4A9E94",
            "surface.black": "#020617",
            "surface.navy": "#041628",
            "surface.plum": "#1A0520",
            "bg.black": "on #020617",
            "bg.navy": "on #041628",
            "row.active": "bold #94FADB on #041628",
        })
    elif name == "pastel-neon-dreamscape":
        # New Theme: Pastel Neon Dreamscape on Black
        # Colors: #00FFFF, #FF00FF, #FFFF00, #00FF00, #66FFFF, #FF66FF, #FFFF66, #66FF66, #333333, #000000
        return Theme({
            "mint": "bold #00FFFF",
            "mint.soft": "#66FFFF",
            "mint.bright": "bold #00FFFF",
            "mint.dim": "#A9A9A9",
            "magenta": "bold #FF00FF",
            "violet": "#FF66FF",
            "violet.dim": "#800080",
            "text": "#E5E5E5",
            "text.dim": "#A9A9A9",
            "text.muted": "#A9A9A9",
            "text.disabled": "#333333",
            "text.emphasis": "bold #FFFFFF",
            "heading": "bold #00FFFF",
            "subheading": "bold #66FF66",
            "label": "#A9A9A9",
            "success": "#00FF00",
            "success.soft": "#66FF66",
            "error": "bold #FF00FF",
            "warning": "#FFFF00",
            "gold": "#FFFF00",
            "amber": "#FFCF78",
            "warning.soft": "#FFFF66",
            "info": "#66FFFF",
            "debug": "#FF66FF",
            "hazard": "#FFFF00",
            "gilt.edge": "#FFFF00",
            "chip.live": "bold #00FFFF",
            "chip.override": "bold #FFFF00",
            "chip.blocker": "bold #FF00FF",
            "chip.logged": "#66FF66",
            "chip.aftercare": "#FF66FF",
            "chip.edge": "bold #66FFFF",
            "table.header": "bold #00FFFF",
            "table.border": "#333333",
            "table.row.alt": "on #080808",
            "panel.border": "#00FFFF",
            "panel.title": "bold #66FFFF",
            "bar.complete": "#00FFFF",
            "bar.remaining": "#333333",
            "bar.pulse": "#FF00FF",
            "spinner": "#00FFFF",
            "severity.healthy": "#00FF00",
            "severity.warning": "#FFFF00",
            "severity.critical": "bold #FF00FF",
            "severity.unknown": "#333333",
            "rule.line": "#333333",
            "surface.black": "#000000",
            "surface.navy": "#080808",
            "surface.plum": "#1A001A",
            "bg.black": "on #000000",
            "bg.navy": "on #080808",
            "row.active": "bold #FFFFFF on #080808",
        })
    else:
        # Default: Pastel Neon Dreams (Current product theme)
        return Theme({
            "mint": "bold #00FFFF",
            "mint.soft": "#7FFFD4",
            "mint.bright": "bold #B2FFFF",
            "mint.dim": "#A9A9A9",
            "magenta": "bold #FF00FF",
            "violet": "#FFB2FF",
            "violet.dim": "#800080",
            "gremlin.pink": "#FF00FF",
            "text": "#E5E5E5",
            "text.dim": "#A9A9A9",
            "text.muted": "#A9A9A9",
            "text.disabled": "#4D4D4D",
            "text.emphasis": "bold #FFFFFF",
            "heading": "bold #00FFFF",
            "subheading": "bold #7FFFD4",
            "label": "#A9A9A9",
            "success": "#7FFFD4",
            "error": "bold #FF69B4",
            "warning": "#FFFFE0",
            "gold": "#FFFFE0",
            "amber": "#FFCF78",
            "info": "#B2FFFF",
            "debug": "#FFB2FF",
            "hazard": "#FFFFE0",
            "gilt.edge": "#FFFFE0",
            "chip.live": "bold #00FFFF",
            "chip.override": "bold #FFFFE0",
            "chip.blocker": "bold #FF69B4",
            "chip.logged": "#7FFFD4",
            "chip.aftercare": "#FFB2FF",
            "chip.edge": "bold #B2FFFF",
            "table.header": "bold #00FFFF",
            "table.border": "#A9A9A9",
            "table.row.alt": "on #080808",
            "panel.border": "#00FFFF",
            "panel.title": "bold #B2FFFF",
            "bar.complete": "#00FFFF",
            "bar.remaining": "#080808",
            "bar.pulse": "#FF00FF",
            "spinner": "#00FFFF",
            "severity.healthy": "#7FFFD4",
            "severity.warning": "#FFFFE0",
            "severity.critical": "bold #FF69B4",
            "severity.unknown": "#4D4D4D",
            "rule.line": "#A9A9A9",
            "surface.black": "#000000",
            "surface.navy": "#080808",
            "surface.plum": "#1A001A",
            "bg.black": "on #000000",
            "bg.navy": "on #080808",
            "row.active": "bold #FFFFFF on #080808",
        })

DOPEMUX_THEME = build_theme(get_active_theme_name())


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Glyphs
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class Glyphs:
    """Nerd Font glyphs for status indicators and UI elements.

    Primary set assumes JetBrains Mono Nerd Font.
    Fallback chars provided for graceful degradation.
    """

    # ── Status ──
    SUCCESS = "\uf058"  # nf-fa-check_circle
    ERROR = "\uf057"  # nf-fa-times_circle
    WARNING = "\uf06a"  # nf-fa-exclamation_circle
    INFO = "\uf05a"  # nf-fa-info_circle
    RUNNING = "\uf04b"  # nf-fa-play
    PENDING = "\uf017"  # nf-fa-clock_o
    BLOCKED = "\uf05e"  # nf-fa-ban
    SKIPPED = "\uf050"  # nf-fa-forward
    FIRE = "\uf06d"  # nf-fa-fire
    GOLD = "\uf091"  # nf-fa-trophy

    # ── Dev ──
    GIT = "\ue725"  # nf-dev-git_branch
    CODE = "\uf121"  # nf-fa-code
    PACKAGE = "\uf487"  # nf-oct-package
    BUG = "\uf188"  # nf-fa-bug
    WRENCH = "\uf0ad"  # nf-fa-wrench

    # ── System ──
    DOCKER = "\uf308"  # nf-linux-docker
    SERVER = "\uf233"  # nf-fa-server
    DATABASE = "\uf1c0"  # nf-fa-database

    # ── Navigation ──
    ARROW_RIGHT = "\uf054"  # nf-fa-chevron_right
    ARROW_DOWN = "\uf078"  # nf-fa-chevron_down
    PROMPT = "\u276f"  # ❯

    # ── Brand ──
    BRAND_MARK = "━━━◆ \u00d8 ◆━━━"  # ━━━◆ Ø ◆━━━
    SECTION_RULE = "───"

    # ── Fallback map (glyph -> ascii) ──
    _FALLBACK = {
        SUCCESS: "\u2713",  # ✓
        ERROR: "\u2717",  # ✗
        WARNING: "!",
        INFO: "i",
        RUNNING: "\u25b6",  # ▶
        PENDING: "~",
        BLOCKED: "#",
        SKIPPED: "-",
        FIRE: "^",
        GOLD: "*",
        GIT: "Y",
        CODE: "<>",
        PACKAGE: "[]",
        BUG: "*",
        WRENCH: "%",
        ARROW_RIGHT: ">",
        ARROW_DOWN: "v",
        PROMPT: ">",
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Status Chips
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class StatusChip(enum.Enum):
    """Brand status chips with associated Rich styles.

    Usage:
        console.print(StatusChip.LIVE.render("Pipeline active"))
        console.print(StatusChip.BLOCKER.render("Missing API key"))
    """

    LIVE = ("LIVE", "chip.live")
    BLOCKER = ("BLOCKER", "chip.blocker")
    OVERRIDE = ("OVERRIDE", "chip.override")
    LOGGED = ("LOGGED", "chip.logged")
    AFTERCARE = ("AFTERCARE", "chip.aftercare")
    EDGE = ("EDGE", "chip.edge")

    def __init__(self, label: str, style: str) -> None:
        self.label = label
        self.style_name = style

    def render(self, message: str = "") -> str:
        """Return Rich markup string for this chip + optional message.

        Example: ``StatusChip.LIVE.render("Running")``
        produces ``"[chip.live]\\[LIVE][/chip.live] Running"``
        """
        chip = f"[{self.style_name}]\\[{self.label}][/{self.style_name}]"
        if message:
            return f"{chip} {message}"
        return chip


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Render Mode
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class RenderMode(enum.Enum):
    """Output rendering modes."""

    RICH = "rich"  # Full themed output (default)
    PLAIN = "plain"  # NO_COLOR - strip all styles
    COMPACT = "compact"  # Reduced spacing, inline status
    AUDIT = "audit"  # Structured text with timestamps


def _detect_render_mode() -> RenderMode:
    """Detect render mode from environment."""
    if os.environ.get("NO_COLOR"):
        return RenderMode.PLAIN
    mode = os.environ.get("DOPEMUX_RENDER_MODE", "rich").lower()
    try:
        return RenderMode(mode)
    except ValueError:
        return RenderMode.RICH


_cached_render_mode: RenderMode | None = None


def get_render_mode() -> RenderMode:
    """Return the current render mode (cached after first call).

    Reads from ``DOPEMUX_RENDER_MODE`` env var or ``NO_COLOR``.
    CLI flags set the env var before this is called.
    """
    global _cached_render_mode
    if _cached_render_mode is None:
        _cached_render_mode = _detect_render_mode()
    return _cached_render_mode


def set_render_mode(mode: RenderMode) -> None:
    """Explicitly set the render mode (used by CLI flags)."""
    global _cached_render_mode
    _cached_render_mode = mode
    os.environ["DOPEMUX_RENDER_MODE"] = mode.value


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Console Factory
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

MAX_WIDTH = 120


def create_console(**kwargs: Any) -> Console:
    """Create a Rich Console pre-loaded with the dopemux theme.

    Respects ``NO_COLOR`` and ``DOPEMUX_RENDER_MODE`` env vars.

    Returns:
        A :class:`rich.console.Console` configured with :data:`DOPEMUX_THEME`.
    """
    mode = _detect_render_mode()
    no_color = mode == RenderMode.PLAIN
    return Console(
        theme=DOPEMUX_THEME,
        width=min(kwargs.pop("width", 9999), MAX_WIDTH),
        no_color=no_color,
        **kwargs,
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Component Helpers
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def styled_table(
    title: str,
    *columns: str | tuple[str, dict[str, Any]],
    compact: bool = False,
    **table_kwargs: Any,
) -> Table:
    """Create a branded Rich Table with dopemux styling.

    Args:
        title: Table title (rendered with ``table.header`` style).
        *columns: Column names, or ``(name, kwargs)`` tuples for
            :meth:`Table.add_column`.
        compact: If ``True``, use ``SIMPLE`` box and tighter padding.
        **table_kwargs: Forwarded to :class:`rich.table.Table`.

    Returns:
        A pre-styled :class:`rich.table.Table`.

    Example::

        t = styled_table(
            f"{Glyphs.PACKAGE} Dependencies",
            "Name",
            ("Version", {"justify": "right"}),
            ("Status", {"justify": "center"}),
        )
        t.add_row("rich", "13.9", "[success]installed[/]")
    """
    mode = get_render_mode()
    if mode == RenderMode.COMPACT:
        compact = True
    box_style = SIMPLE if compact else ROUNDED
    show_title = title if mode != RenderMode.COMPACT else None
    
    # Set defaults in table_kwargs if not provided
    table_kwargs.setdefault("title", show_title)
    table_kwargs.setdefault("box", box_style)
    table_kwargs.setdefault("title_style", "table.header")
    table_kwargs.setdefault("border_style", "table.border")
    table_kwargs.setdefault("header_style", "table.header")
    table_kwargs.setdefault("padding", (0, 1) if not compact else (0, 0))
    
    table = Table(**table_kwargs)
    if mode == RenderMode.AUDIT:
        table.add_column("Timestamp", style="text.dim", no_wrap=True)
    for col in columns:
        if isinstance(col, tuple):
            name, col_kwargs = col
            table.add_column(name, **col_kwargs)
        else:
            table.add_column(col)
    if mode == RenderMode.AUDIT:
        # Monkey-patch add_row to prepend timestamp
        _orig_add_row = table.add_row

        def _audit_add_row(*args: Any, **kwargs: Any) -> None:
            ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            _orig_add_row(ts, *args, **kwargs)

        table.add_row = _audit_add_row  # type: ignore[assignment]
    return table


def styled_panel(
    content: Any,
    title: str = "",
    border_style: str = "panel.border",
    **kwargs: Any,
) -> Panel:
    """Create a branded Rich Panel with dopemux styling.

    Args:
        content: Panel body (renderable or string).
        title: Panel title (rendered with ``panel.title`` style).
        border_style: Rich style name for the border.
        **kwargs: Forwarded to :class:`rich.panel.Panel`.

    Returns:
        A pre-styled :class:`rich.panel.Panel`.

    Example::

        styled_panel(
            "[error]Connection refused[/]\\n\\n"
            "[text.dim]Why:[/] Database not running\\n"
            "[text.dim]Fix:[/] Run [mint]docker compose up db[/]",
            title="Connection Error",
            border_style="error",
        )
    """
    mode = get_render_mode()
    if mode == RenderMode.COMPACT:
        # No border — return content as a simple Text renderable
        header = f"[panel.title]{title}[/panel.title]\n" if title else ""
        return Text.from_markup(f"{header}{content}" if isinstance(content, str) else header)
    if mode == RenderMode.AUDIT:
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        plain_title = title or "Panel"
        # Strip Rich markup for audit log line
        header = f"[{ts}] {plain_title}: "
        return Text.from_markup(f"{header}{content}" if isinstance(content, str) else header)
    kwargs.setdefault("title", f"[panel.title]{title}[/panel.title]" if title else None)
    kwargs.setdefault("border_style", border_style)
    kwargs.setdefault("box", ROUNDED)
    kwargs.setdefault("padding", (1, 2))
    
    return Panel(content, **kwargs)


def error_panel(problem: str, why: str, fix: str, title: str = "Error") -> Panel:
    """Create a 3-part error panel (Problem / Why / Fix).

    Args:
        problem: What went wrong.
        why: Why it happened.
        fix: Actionable fix step.
        title: Panel title.

    Returns:
        A :class:`rich.panel.Panel` styled with ``error`` border.
    """
    body = (
        f"[error]{Glyphs.ERROR} {problem}[/error]\n\n"
        f"[text.dim]Why:[/text.dim] {why}\n"
        f"[text.dim]Fix:[/text.dim] [mint]{fix}[/mint]"
    )
    return styled_panel(body, title=f"{Glyphs.ERROR} {title}", border_style="error")


def styled_gauge(
    value: float,
    width: int = 10,
    complete_style: str = "bar.complete",
    remaining_style: str = "bar.remaining",
) -> str:
    """Create a branded progress gauge with dopemux styling.

    Args:
        value: Float between 0.0 and 1.0.
        width: Total width in characters.
        complete_style: Rich style for the completed portion.
        remaining_style: Rich style for the remaining portion.

    Returns:
        Rich markup string for the gauge (e.g., "[mint]████[/][grey]░░░░░░[/]").
    """
    safe_value = max(0.0, min(1.0, value))
    filled_len = int(safe_value * width)
    remaining_len = width - filled_len

    filled = "█" * filled_len
    remaining = "░" * remaining_len

    return f"[{complete_style}]{filled}[/][{remaining_style}]{remaining}[/]"
