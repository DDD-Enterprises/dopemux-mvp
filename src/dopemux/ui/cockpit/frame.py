"""Width-locked Cockpit frame and rule primitives.

This module is intentionally primitive-level only. It supplies the grid geometry
that later mode builders can consume without replacing the deterministic render
model in :mod:`dopemux.ui.cockpit.render`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .render import TOO_SMALL_MESSAGE, viewport_supported


SUPPORTED_FRAME_SIZES: tuple[tuple[int, int], ...] = (
    (120, 40),
    (100, 32),
    (80, 24),
)


@dataclass(frozen=True)
class FrameLayout:
    """Character-grid coordinates for the approved Cockpit shell."""

    cols: int
    rows: int
    left_divider_col: int
    right_divider_col: int
    inspector_split_row: int
    center_split_row: int
    body_rule_row: int
    command_row: int
    status_rule_row: int
    status_row: int
    bottom_row: int

    @property
    def left_column(self) -> range:
        return range(1, self.left_divider_col)

    @property
    def center_column(self) -> range:
        return range(self.left_divider_col + 1, self.right_divider_col)

    @property
    def inspector_column(self) -> range:
        return range(self.right_divider_col + 1, self.cols - 1)

    @property
    def protected_rows(self) -> tuple[int, ...]:
        return (0, self.body_rule_row, self.status_rule_row, self.bottom_row)

    @property
    def divider_cols(self) -> tuple[int, int]:
        return (self.left_divider_col, self.right_divider_col)


FRAME_LAYOUTS: dict[tuple[int, int], FrameLayout] = {
    (120, 40): FrameLayout(
        cols=120,
        rows=40,
        left_divider_col=25,
        right_divider_col=84,
        inspector_split_row=22,
        center_split_row=25,
        body_rule_row=35,
        command_row=36,
        status_rule_row=37,
        status_row=38,
        bottom_row=39,
    ),
    (100, 32): FrameLayout(
        cols=100,
        rows=32,
        left_divider_col=21,
        right_divider_col=70,
        inspector_split_row=17,
        center_split_row=19,
        body_rule_row=27,
        command_row=28,
        status_rule_row=29,
        status_row=30,
        bottom_row=31,
    ),
    (80, 24): FrameLayout(
        cols=80,
        rows=24,
        left_divider_col=17,
        right_divider_col=56,
        inspector_split_row=11,
        center_split_row=13,
        body_rule_row=19,
        command_row=20,
        status_rule_row=21,
        status_row=22,
        bottom_row=23,
    ),
}


class FrameDrawError(ValueError):
    """Raised when a draw operation would violate protected frame geometry."""


class FrameBuffer:
    """Mutable grid with immutable protected border, divider, and rule cells."""

    def __init__(self, layout: FrameLayout) -> None:
        self.layout = layout
        self._cells = [[" " for _ in range(layout.cols)] for _ in range(layout.rows)]
        self._protected: set[tuple[int, int]] = set()
        self._draw_shell()

    def lines(self) -> tuple[str, ...]:
        return tuple("".join(row) for row in self._cells)

    def put_text(self, row: int, col: int, text: str) -> None:
        if not isinstance(row, int) or not isinstance(col, int):
            raise FrameDrawError("frame coordinates must be whole character cells")
        if row < 0 or row >= self.layout.rows:
            raise FrameDrawError("row outside frame")
        if col < 0 or col + len(text) > self.layout.cols:
            raise FrameDrawError("text outside frame")
        for offset, char in enumerate(text):
            target = (row, col + offset)
            if target in self._protected:
                raise FrameDrawError("cannot draw over protected frame cell")
            self._cells[row][col + offset] = char

    def _draw_shell(self) -> None:
        layout = self.layout
        self._draw_full_rule(0, left="┏", fill="━", divider="┯", right="┓")
        for row in range(1, layout.bottom_row):
            self._protect(row, 0, "┃")
            self._protect(row, layout.cols - 1, "┃")
            self._protect(row, layout.left_divider_col, "│")
            self._protect(row, layout.right_divider_col, "│")
        self._draw_body_rule()
        self._draw_full_rule(layout.status_rule_row, left="┠", fill="─", divider="┼", right="┨")
        self._draw_full_rule(layout.bottom_row, left="┗", fill="━", divider="┷", right="┛")

    def _draw_body_rule(self) -> None:
        layout = self.layout
        row = layout.body_rule_row
        for col in range(layout.cols):
            char = "─"
            if col == 0:
                char = "┠"
            elif col == layout.left_divider_col:
                char = "┴"
            elif col == layout.right_divider_col:
                char = "┤"
            elif col == layout.cols - 1:
                char = "┨"
            self._protect(row, col, char)

    def _draw_full_rule(self, row: int, *, left: str, fill: str, divider: str, right: str) -> None:
        layout = self.layout
        for col in range(layout.cols):
            char = fill
            if col == 0:
                char = left
            elif col in layout.divider_cols:
                char = divider
            elif col == layout.cols - 1:
                char = right
            self._protect(row, col, char)

    def _protect(self, row: int, col: int, char: str) -> None:
        self._cells[row][col] = char
        self._protected.add((row, col))


def frame_layout_for_viewport(cols: int, rows: int) -> FrameLayout | None:
    """Return the approved layout for a supported viewport, else ``None``."""
    if not viewport_supported(cols, rows):
        return None
    if (cols, rows) in FRAME_LAYOUTS:
        return FRAME_LAYOUTS[(cols, rows)]
    supported = sorted(FRAME_LAYOUTS.values(), key=lambda item: item.cols)
    for layout in supported:
        if cols <= layout.cols and rows <= layout.rows:
            return layout
    return FRAME_LAYOUTS[(120, 40)]


def render_frame_shell(cols: int, rows: int) -> str:
    """Render only the Cockpit frame shell for the nearest approved viewport."""
    layout = frame_layout_for_viewport(cols, rows)
    if layout is None:
        return TOO_SMALL_MESSAGE
    return "\n".join(FrameBuffer(layout).lines()) + "\n"


def protected_cells(layout: FrameLayout) -> frozenset[tuple[int, int]]:
    """Expose protected frame cells for tests and downstream validators."""
    return frozenset(FrameBuffer(layout)._protected)


def iter_frame_lines(cols: int, rows: int) -> Iterable[str]:
    """Yield frame shell lines for supported viewports."""
    return iter(render_frame_shell(cols, rows).splitlines())
