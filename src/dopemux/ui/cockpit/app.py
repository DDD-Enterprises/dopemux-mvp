"""Textual shell for static Dopemux Cockpit mode surfaces."""

from __future__ import annotations

from typing import Any

from .render import TOO_SMALL_MESSAGE, TOP_LEVEL_MODES, viewport_supported
from .render_modes import MODE_TITLES, normalize_mode, render_cockpit

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
    """Top-level mode bar."""
    def __init__(self, active: str = "PM") -> None:
        if Static is None:
            raise RuntimeError("[BLOCKER] textual unavailable for interactive cockpit")
        super().__init__(id="cockpit-mode-bar")
        self._active = active

    def set_active(self, active: str) -> None:
        self._active = active
        self.refresh()

    def render(self) -> str:
        return " | ".join(
            f"[ {mode} ]" if mode == self._active else f"  {mode}  "
            for mode in TOP_LEVEL_MODES
        )


class CockpitModeScreen(Static if Static is not None else object):
    """Static mode render widget."""
    def __init__(self, *, mode: str, cols: int, rows: int) -> None:
        if Static is None:
            raise RuntimeError("[BLOCKER] textual unavailable for interactive cockpit")
        super().__init__(id="cockpit-mode-screen")
        self._mode = normalize_mode(mode)
        self._cols, self._rows = cols, rows

    def set_mode(self, mode: str) -> None:
        self._mode = normalize_mode(mode)
        self.refresh()

    def render(self) -> str:
        return render_cockpit(self._mode, cols=self._cols, rows=self._rows)


class CockpitApp(App):
    """Dopemux Cockpit Textual shell."""
    TITLE = "Dopemux Cockpit"
    SUB_TITLE = "STATIC DEMO  NO WRITES"
    BINDINGS = [
        ("1", "select_mode('pm')", "PM"),
        ("2", "select_mode('implementer')", "Implementer"),
        ("3", "select_mode('overview')", "Overview"),
        ("4", "select_mode('services')", "Services"),
        ("5", "select_mode('events')", "Events"),
        ("q", "quit", "Quit"),
    ]

    def __init__(self, *, mode: str = "pm", cols: int = 120, rows: int = 40) -> None:
        if _TEXTUAL_IMPORT_ERROR is not None:
            raise RuntimeError("[BLOCKER] textual unavailable for interactive cockpit")
        super().__init__()
        self._mode = normalize_mode(mode)
        self._cols, self._rows = cols, rows
        self.title = f"Dopemux Cockpit  mode={MODE_TITLES[self._mode]}"

    def compose(self) -> ComposeResult:
        assert Header is not None and Static is not None
        assert Footer is not None and Vertical is not None
        yield Header()
        if not viewport_supported(self._cols, self._rows):
            yield Static(TOO_SMALL_MESSAGE, id="cockpit-too-small")
            yield Footer()
            return
        with Vertical():
            yield CockpitModeBar(active=MODE_TITLES[self._mode])
            yield CockpitModeScreen(mode=self._mode, cols=self._cols, rows=self._rows)
        yield Footer()

    def action_select_mode(self, mode: str) -> None:
        self._mode = normalize_mode(mode)
        self.title = f"Dopemux Cockpit  mode={MODE_TITLES[self._mode]}"
        self.query_one("#cockpit-mode-bar", CockpitModeBar).set_active(
            MODE_TITLES[self._mode]
        )
        self.query_one("#cockpit-mode-screen", CockpitModeScreen).set_mode(self._mode)


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
    normalized_mode = normalize_mode(mode)
    cols, rows = size

    if plain or audit:
        return render_cockpit(normalized_mode, cols=cols, rows=rows, plain=True)
    if not viewport_supported(cols, rows):
        return TOO_SMALL_MESSAGE
    app = CockpitApp(mode=normalized_mode, cols=cols, rows=rows)
    app.run()
    return None
