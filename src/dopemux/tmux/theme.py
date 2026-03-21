"""Shared tmux palette helpers backed by the Dopemux UI theme."""

from __future__ import annotations

from ..ui.theme import (
    AFTERCARE_VIOLET,
    GILT_EDGE,
    GREMLIN_PINK,
    INK_BLACK,
    MINT_DIM,
    RITUAL_CYAN,
    SAINT_GOLD,
    SERUM_MINT,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    VELVET_PLUM,
    VOID_NAVY,
)

TMUX_ACCENT = RITUAL_CYAN
TMUX_SUCCESS = SERUM_MINT
TMUX_WARNING = GILT_EDGE
TMUX_ALERT = GREMLIN_PINK
TMUX_AFTERCARE = AFTERCARE_VIOLET
TMUX_GOLD = SAINT_GOLD
TMUX_BACKGROUND = INK_BLACK
TMUX_SURFACE = VOID_NAVY
TMUX_PANEL = VELVET_PLUM
TMUX_BORDER = MINT_DIM
TMUX_FOREGROUND = TEXT_PRIMARY
TMUX_MUTED = TEXT_SECONDARY
TMUX_TITLE_BG = VOID_NAVY
TMUX_TITLE_FG = TEXT_PRIMARY


def tmux_style(*, fg: str | None = None, bg: str | None = None, bold: bool = False) -> str:
    """Return a tmux style string built from canonical brand colors."""
    parts: list[str] = []
    if fg:
        parts.append(f"fg={fg}")
    if bg:
        parts.append(f"bg={bg}")
    if bold:
        parts.append("bold")
    return ",".join(parts)


def tmux_segment(text: str, *, fg: str | None = None, bg: str | None = None, bold: bool = False) -> str:
    """Wrap a tmux status segment with style markers."""
    style = tmux_style(fg=fg, bg=bg, bold=bold)
    if not style:
        return text
    return f"#[{style}]{text}"


def _pane_styles(neon: bool) -> dict[str, str]:
    if neon:
        return {
            "monitor:worktree": tmux_style(fg=TMUX_BACKGROUND, bg=TMUX_SUCCESS),
            "monitor:logs": tmux_style(fg=TMUX_BACKGROUND, bg=TMUX_WARNING),
            "monitor:metrics": tmux_style(fg=TMUX_BACKGROUND, bg=TMUX_ALERT),
            "monitor:attention": tmux_style(fg=TMUX_BACKGROUND, bg=TMUX_ALERT),
            "monitor:adhd": tmux_style(fg=TMUX_BACKGROUND, bg=TMUX_SUCCESS),
            "monitor:system": tmux_style(fg=TMUX_BACKGROUND, bg=TMUX_WARNING),
            "monitor:pm-hierarchy": tmux_style(fg=TMUX_BACKGROUND, bg=TMUX_ALERT),
            "monitor:task-detail": tmux_style(fg=TMUX_BACKGROUND, bg=TMUX_AFTERCARE),
            "monitor": tmux_style(fg=TMUX_BACKGROUND, bg=TMUX_ACCENT),
            "metrics:bar": tmux_style(fg=TMUX_ACCENT, bg=TMUX_BACKGROUND),
            "orchestrator:control": tmux_style(fg=TMUX_ACCENT, bg=TMUX_SURFACE),
            "sandbox:shell": tmux_style(fg=TMUX_ALERT, bg=TMUX_PANEL),
            "agent:primary": tmux_style(fg=TMUX_SUCCESS, bg=TMUX_SURFACE),
            "agent:secondary": tmux_style(fg=TMUX_BACKGROUND, bg=TMUX_GOLD),
        }
    return {
        "monitor:worktree": tmux_style(fg=TMUX_SUCCESS, bg=TMUX_SURFACE),
        "monitor:logs": tmux_style(fg=TMUX_ACCENT, bg=TMUX_SURFACE),
        "monitor:metrics": tmux_style(fg=TMUX_WARNING, bg=TMUX_SURFACE),
        "monitor:attention": tmux_style(fg=TMUX_WARNING, bg=TMUX_SURFACE),
        "monitor:adhd": tmux_style(fg=TMUX_SUCCESS, bg=TMUX_SURFACE),
        "monitor:system": tmux_style(fg=TMUX_ACCENT, bg=TMUX_SURFACE),
        "monitor:pm-hierarchy": tmux_style(fg=TMUX_WARNING, bg=TMUX_SURFACE),
        "monitor:task-detail": tmux_style(fg=TMUX_AFTERCARE, bg=TMUX_SURFACE),
        "monitor": tmux_style(fg=TMUX_FOREGROUND, bg=TMUX_SURFACE),
        "metrics:bar": tmux_style(fg=TMUX_ACCENT, bg=TMUX_BACKGROUND),
        "orchestrator:control": tmux_style(fg=TMUX_FOREGROUND, bg=TMUX_PANEL),
        "sandbox:shell": tmux_style(fg=TMUX_AFTERCARE, bg=TMUX_PANEL),
        "agent:primary": tmux_style(fg=TMUX_SUCCESS, bg=TMUX_SURFACE),
        "agent:secondary": tmux_style(fg=TMUX_GOLD, bg=TMUX_PANEL),
    }


def _pane_border_styles(neon: bool) -> dict[str, str]:
    background = TMUX_BACKGROUND if neon else TMUX_PANEL
    return {
        "monitor:worktree": tmux_style(fg=TMUX_SUCCESS, bg=background),
        "monitor:logs": tmux_style(fg=TMUX_ACCENT, bg=background),
        "monitor:metrics": tmux_style(fg=TMUX_WARNING, bg=background),
        "monitor:attention": tmux_style(fg=TMUX_WARNING, bg=background),
        "monitor:adhd": tmux_style(fg=TMUX_SUCCESS, bg=background),
        "monitor:system": tmux_style(fg=TMUX_ACCENT, bg=background),
        "monitor:pm-hierarchy": tmux_style(fg=TMUX_WARNING, bg=background),
        "monitor:task-detail": tmux_style(fg=TMUX_AFTERCARE, bg=background),
        "monitor": tmux_style(fg=TMUX_BORDER, bg=background),
        "metrics:bar": tmux_style(fg=TMUX_ACCENT, bg=background),
        "orchestrator:control": tmux_style(fg=TMUX_ACCENT if neon else TMUX_FOREGROUND, bg=TMUX_BACKGROUND),
        "sandbox:shell": tmux_style(fg=TMUX_ALERT, bg=TMUX_BACKGROUND),
        "agent:primary": tmux_style(fg=TMUX_SUCCESS, bg=TMUX_BACKGROUND),
        "agent:secondary": tmux_style(fg=TMUX_GOLD, bg=TMUX_BACKGROUND),
    }


def _status_left(neon: bool) -> str:
    label_bg = TMUX_ACCENT
    label_fg = TMUX_BACKGROUND if neon else TMUX_SURFACE
    return (
        f"{tmux_segment(' ◆ Ø ◆ ', fg=label_fg, bg=label_bg, bold=True)}"
        f"{tmux_segment(' dopemux ', fg=TMUX_BACKGROUND, bg=TMUX_SUCCESS, bold=True)} "
        f"{tmux_segment('#H', fg=TMUX_SUCCESS)} #[default]"
    )


def _status_right(neon: bool) -> str:
    return (
        f"{tmux_segment('#{{@dopemux_mobile_indicator:-📱 idle}}', fg=TMUX_SUCCESS)} #[default]"
        f"{tmux_segment('#(./scripts/ccr_model_tracker.sh 2>/dev/null || echo \"🤖\")', fg=TMUX_GOLD if neon else TMUX_AFTERCARE)} #[default]"
        f"{tmux_segment('  %R', fg=TMUX_AFTERCARE)} "
        f"{tmux_segment('%a %b %d', fg=TMUX_ACCENT)} "
        f"{tmux_segment('#{{window_index}}:#{{window_name}}', fg=TMUX_FOREGROUND if neon else TMUX_MUTED)} "
        f"{tmux_segment('#{{pane_index}}:#{{pane_title}}', fg=TMUX_WARNING)}"
    )


def build_tmux_theme(name: str = "muted") -> dict[str, dict[str, str] | str]:
    """Build a tmux theme preset from the shared Dopemux palette."""
    neon = name == "neon"
    background = TMUX_BACKGROUND if neon else TMUX_SURFACE
    foreground = TMUX_FOREGROUND
    warning = TMUX_GOLD if neon else TMUX_WARNING
    return {
        "pane_styles": _pane_styles(neon),
        "pane_border_styles": _pane_border_styles(neon),
        "status_style": tmux_style(fg=foreground, bg=background),
        "status_left": _status_left(neon),
        "status_right": _status_right(neon),
        "status_palette": {
            "accent": TMUX_ACCENT,
            "background": background,
            "foreground": foreground,
            "warning": warning,
            "success": TMUX_SUCCESS,
            "info": TMUX_ACCENT,
            "alert": TMUX_ALERT,
        },
    }


THEME_PRESETS = {
    "muted": build_tmux_theme("muted"),
    "neon": build_tmux_theme("neon"),
}
