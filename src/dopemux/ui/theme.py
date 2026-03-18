"""Dopemux CLI Theme - Single source of truth for all CLI/TUI styling.

This module defines the neon mint palette, Rich Theme object, glyph constants,
status chips, and helper factories that every dopemux CLI command must use.

Usage:
    from dopemux.ui.theme import DOPEMUX_THEME, Glyphs, StatusChip, styled_table, styled_panel
    from dopemux.console import console  # already themed

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

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Color Constants
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# ── Mint / Cyan family (hero) ──
RITUAL_CYAN = "#7DFBF6"
SERUM_MINT = "#94FADB"
MINT_BRIGHT = "#B4FFEE"
MINT_DIM = "#4A9E94"

# ── Accent pops (magenta / violet) ──
GREMLIN_PINK = "#FF8BD1"
AFTERCARE_VIOLET = "#9B78FF"
VIOLET_DIM = "#6B4FBF"

# ── Warm tones (warnings only) ──
GILT_EDGE = "#F5F26D"
SAINT_GOLD = "#FFCF78"

# ── Surfaces ──
INK_BLACK = "#020617"
VOID_NAVY = "#041628"
VELVET_PLUM = "#1A0520"

# ── Text hierarchy ──
TEXT_PRIMARY = "#E2E8F0"
TEXT_SECONDARY = "#94A3B8"
TEXT_MUTED = "#64748B"
TEXT_DISABLED = "#475569"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Rich Theme
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DOPEMUX_THEME = Theme(
    {
        # ── Mint family (hero) ──
        "mint": f"bold {RITUAL_CYAN}",
        "mint.soft": SERUM_MINT,
        "mint.bright": f"bold {MINT_BRIGHT}",
        "mint.dim": MINT_DIM,
        # ── Accent pops ──
        "magenta": f"bold {GREMLIN_PINK}",
        "violet": AFTERCARE_VIOLET,
        "violet.dim": VIOLET_DIM,
        # ── Warm (warnings only) ──
        "gold": GILT_EDGE,
        "amber": SAINT_GOLD,
        # ── Text hierarchy ──
        "text": TEXT_PRIMARY,
        "text.dim": TEXT_SECONDARY,
        "text.muted": TEXT_MUTED,
        "text.disabled": TEXT_DISABLED,
        "text.emphasis": f"bold {SERUM_MINT}",
        # ── Headings ──
        "heading": f"bold {RITUAL_CYAN}",
        "subheading": f"bold {SERUM_MINT}",
        "label": TEXT_SECONDARY,
        # ── Status (semantic) ──
        "success": SERUM_MINT,
        "error": f"bold {GREMLIN_PINK}",
        "warning": GILT_EDGE,
        "info": RITUAL_CYAN,
        "debug": AFTERCARE_VIOLET,
        # ── Status chips ──
        "chip.live": f"bold {RITUAL_CYAN}",
        "chip.override": f"bold {GILT_EDGE}",
        "chip.blocker": f"bold {GREMLIN_PINK}",
        "chip.logged": SERUM_MINT,
        "chip.aftercare": AFTERCARE_VIOLET,
        "chip.edge": f"bold {RITUAL_CYAN}",
        # ── Tables ──
        "table.header": f"bold {RITUAL_CYAN}",
        "table.border": MINT_DIM,
        "table.row.alt": f"on {VOID_NAVY}",
        # ── Panels ──
        "panel.border": MINT_DIM,
        "panel.title": f"bold {SERUM_MINT}",
        # ── Progress ──
        "bar.complete": RITUAL_CYAN,
        "bar.remaining": VELVET_PLUM,
        "bar.pulse": GREMLIN_PINK,
        "spinner": RITUAL_CYAN,
        # ── Severity ──
        "severity.healthy": SERUM_MINT,
        "severity.warning": GILT_EDGE,
        "severity.critical": f"bold {GREMLIN_PINK}",
        "severity.unknown": TEXT_MUTED,
        # ── Rule lines ──
        "rule.line": MINT_DIM,
    }
)


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
    table = Table(
        title=show_title,
        box=box_style,
        title_style="table.header",
        border_style="table.border",
        header_style="table.header",
        padding=(0, 1) if not compact else (0, 0),
        **table_kwargs,
    )
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
    return Panel(
        content,
        title=f"[panel.title]{title}[/panel.title]" if title else None,
        border_style=border_style,
        box=ROUNDED,
        padding=(1, 2),
        **kwargs,
    )


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
