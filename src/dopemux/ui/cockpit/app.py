"""Textual shell for the Dopemux Cockpit PM slice.

The deterministic render is in :mod:`render`. This module is a thin
Textual surface over it: a top-level mode bar, a PM screen body, and a
chrome footer. It performs no live writes and no PM mutations.
"""

from __future__ import annotations

from typing import Any

from .render import (
    TOO_SMALL_MESSAGE,
    TOP_LEVEL_MODES,
    render_pm,
    viewport_supported,
)

try:
    from textual.app import App, ComposeResult
    from textual.containers import Vertical
    from textual.widgets import Footer, Header, Static
except ModuleNotFoundError as exc:
    App = object
    ComposeResult = Any
    Vertical = None
    Footer = None
    Header = None
    Static = None
    _TEXTUAL_IMPORT_ERROR: ModuleNotFoundError | None = exc
else:
    _TEXTUAL_IMPORT_ERROR = None


class CockpitModeBar(Static if Static is not None else object):
    """Top-level mode bar (PM, Implementer, Overview, Services, Events)."""

    def __init__(self, active: str = "PM") -> None:
        if Static is None:
            raise RuntimeError("[BLOCKER] textual unavailable for interactive cockpit")
        super().__init__(id="cockpit-mode-bar")
        self._active = active

    def render(self) -> str:
        cells: list[str] = []
        for mode in TOP_LEVEL_MODES:
            if mode == self._active:
                cells.append(f"[ {mode} ]")
            else:
                cells.append(f"  {mode}  ")
        return " | ".join(cells)


class CockpitPMScreen(Static if Static is not None else object):
    """Static PM render. Reuses the deterministic render module."""

    def __init__(self, *, cols: int, rows: int) -> None:
        if Static is None:
            raise RuntimeError("[BLOCKER] textual unavailable for interactive cockpit")
        super().__init__(id="cockpit-pm-screen")
        self._cols = cols
        self._rows = rows

    def render(self) -> str:
        return render_pm(cols=self._cols, rows=self._rows)


class CockpitApp(App):
    """Dopemux Cockpit Textual shell (PM slice)."""

    TITLE = "Dopemux Cockpit  mode=PM"
    SUB_TITLE = "STATIC DEMO  NO WRITES"

    BINDINGS = [
        ("q", "quit", "Quit"),
    ]

    def __init__(self, *, cols: int = 120, rows: int = 40) -> None:
        if _TEXTUAL_IMPORT_ERROR is not None:
            raise RuntimeError("[BLOCKER] textual unavailable for interactive cockpit")
        super().__init__()
        self._cols = cols
        self._rows = rows

    def compose(self) -> ComposeResult:
        assert Header is not None
        assert Static is not None
        assert Footer is not None
        assert Vertical is not None
        yield Header()
        if not viewport_supported(self._cols, self._rows):
            yield Static(TOO_SMALL_MESSAGE, id="cockpit-too-small")
            yield Footer()
            return
        with Vertical():
            yield CockpitModeBar(active="PM")
            yield CockpitPMScreen(cols=self._cols, rows=self._rows)
        yield Footer()


def run_cockpit(
    *,
    mode: str = "pm",
    size: tuple[int, int] = (120, 40),
    plain: bool = False,
    audit: bool = False,
) -> str | None:
    """Entry point used by the ``dopemux cockpit`` CLI command.

    Plain / audit modes print the deterministic render and return the text
    so the CLI can stream it. Interactive mode launches the Textual shell.
    """
    if mode != "pm":
        raise ValueError(f"unsupported cockpit mode: {mode!r}")

    cols, rows = size

    if plain or audit:
        return render_pm(cols=cols, rows=rows, plain=True)

    if not viewport_supported(cols, rows):
        return TOO_SMALL_MESSAGE

    app = CockpitApp(cols=cols, rows=rows)
    app.run()
    return None
