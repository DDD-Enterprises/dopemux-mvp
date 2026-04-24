"""Fixed-size framebuffer with protected borders and hard clipping."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Layout:
    width: int
    height: int
    left_divider: int
    right_divider: int
    inspector_split: int
    center_split: int
    body_rule: int
    command_row: int
    status_rule: int
    status_row: int
    bottom_row: int
    gutter_col: int

    @property
    def protected_columns(self) -> frozenset[int]:
        return frozenset({0, self.left_divider, self.right_divider, self.width - 1})

    @property
    def protected_rows(self) -> frozenset[int]:
        return frozenset({0, 2, 4, self.body_rule, self.status_rule, self.bottom_row})


LAYOUTS: dict[str, Layout] = {
    "120x40": Layout(120, 40, 25, 84, 22, 25, 35, 36, 37, 38, 39, 26),
    "100x32": Layout(100, 32, 21, 70, 17, 19, 27, 28, 29, 30, 31, 22),
    "80x24": Layout(80, 24, 17, 56, 11, 13, 19, 20, 21, 22, 23, 18),
}
SUPPORTED_SIZES = tuple(LAYOUTS)


class FrameBuffer:
    """Mutable character grid that refuses normal writes into protected cells."""

    def __init__(self, width: int, height: int, layout: Layout | None = None) -> None:
        self.width = width
        self.height = height
        self.layout = layout
        self._cells = [[" " for _ in range(width)] for _ in range(height)]

    def is_protected(self, row: int, col: int) -> bool:
        if self.layout is None:
            return False
        return row in self.layout.protected_rows or col in self.layout.protected_columns

    def set_cell(self, row: int, col: int, char: str, *, force: bool = False) -> None:
        if row < 0 or row >= self.height or col < 0 or col >= self.width:
            return
        if not force and self.is_protected(row, col):
            return
        self._cells[row][col] = char[0] if char else " "

    def write(self, row: int, col: int, text: str, *, force: bool = False) -> None:
        if row < 0 or row >= self.height or col >= self.width:
            return
        for offset, char in enumerate(text):
            target_col = col + offset
            if target_col >= self.width:
                break
            self.set_cell(row, target_col, char, force=force)

    def render(self) -> str:
        return "\n".join("".join(row) for row in self._cells)


def draw_static_grid(frame: FrameBuffer, layout: Layout) -> None:
    """Draw the fixed cockpit grid before content writes."""

    last_col = layout.width - 1
    for col in range(layout.width):
        frame.set_cell(0, col, "━", force=True)
        frame.set_cell(layout.bottom_row, col, "━", force=True)
    frame.set_cell(0, 0, "┏", force=True)
    frame.set_cell(0, last_col, "┓", force=True)
    frame.set_cell(layout.bottom_row, 0, "┗", force=True)
    frame.set_cell(layout.bottom_row, last_col, "┛", force=True)

    for row in range(1, layout.bottom_row):
        frame.set_cell(row, 0, "┃", force=True)
        frame.set_cell(row, last_col, "┃", force=True)
        frame.set_cell(row, layout.left_divider, "│", force=True)
        frame.set_cell(row, layout.right_divider, "│", force=True)

    for row in layout.protected_rows:
        if row in {0, layout.bottom_row}:
            continue
        for col in range(1, last_col):
            frame.set_cell(row, col, "─", force=True)
        frame.set_cell(row, 0, "┠", force=True)
        frame.set_cell(row, last_col, "┨", force=True)
        junction = "┬" if row in {2, 4} else "┴"
        frame.set_cell(row, layout.left_divider, junction, force=True)
        frame.set_cell(row, layout.right_divider, junction, force=True)

    for split_row, start_col, end_col in (
        (layout.inspector_split, layout.right_divider + 1, last_col),
        (layout.center_split, layout.left_divider + 1, layout.right_divider),
    ):
        for col in range(start_col, end_col):
            frame.set_cell(split_row, col, "─", force=True)
        frame.set_cell(split_row, layout.right_divider, "├", force=True)
        frame.set_cell(split_row, last_col, "┤", force=True)
