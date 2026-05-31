"""Frame and rule primitive tests for TP-DMX-COCKPIT-P2-FRAME-RULE-001."""

from __future__ import annotations

import pytest

from dopemux.ui.cockpit.frame import (
    FRAME_LAYOUTS,
    SUPPORTED_FRAME_SIZES,
    FrameBuffer,
    FrameDrawError,
    frame_layout_for_viewport,
    protected_cells,
    render_frame_shell,
)
from dopemux.ui.cockpit.render import TOO_SMALL_MESSAGE


def test_supported_frame_layouts_match_design_grid_coordinates():
    expected = {
        (120, 40): (25, 84, 22, 25, 35, 36, 37, 38, 39),
        (100, 32): (21, 70, 17, 19, 27, 28, 29, 30, 31),
        (80, 24): (17, 56, 11, 13, 19, 20, 21, 22, 23),
    }
    assert set(FRAME_LAYOUTS) == set(SUPPORTED_FRAME_SIZES) == set(expected)
    for size, coords in expected.items():
        layout = FRAME_LAYOUTS[size]
        assert (
            layout.left_divider_col,
            layout.right_divider_col,
            layout.inspector_split_row,
            layout.center_split_row,
            layout.body_rule_row,
            layout.command_row,
            layout.status_rule_row,
            layout.status_row,
            layout.bottom_row,
        ) == coords


@pytest.mark.parametrize("cols,rows", SUPPORTED_FRAME_SIZES)
def test_frame_shell_is_width_locked_and_height_locked(cols: int, rows: int):
    lines = render_frame_shell(cols, rows).splitlines()
    assert len(lines) == rows
    assert {len(line) for line in lines} == {cols}
    assert lines[0].startswith("┏")
    assert lines[0].endswith("┓")
    assert lines[-1].startswith("┗")
    assert lines[-1].endswith("┛")


@pytest.mark.parametrize("cols,rows", SUPPORTED_FRAME_SIZES)
def test_frame_shell_has_three_columns_and_protected_rules(cols: int, rows: int):
    layout = FRAME_LAYOUTS[(cols, rows)]
    lines = render_frame_shell(cols, rows).splitlines()

    for row in range(1, layout.bottom_row):
        assert lines[row][0] in {"┃", "┠"}
        assert lines[row][layout.left_divider_col] in {"│", "┴", "┯", "┷", "┼"}
        assert lines[row][layout.right_divider_col] in {"│", "┤", "┯", "┷", "┼"}
        assert lines[row][cols - 1] in {"┃", "┨"}

    assert lines[layout.body_rule_row][0] == "┠"
    assert lines[layout.body_rule_row][layout.left_divider_col] == "┴"
    assert lines[layout.body_rule_row][layout.right_divider_col] == "┤"
    assert lines[layout.status_rule_row][layout.left_divider_col] == "┼"
    assert lines[layout.status_rule_row][layout.right_divider_col] == "┼"


def test_below_minimum_viewport_returns_single_blocker_panel():
    assert render_frame_shell(79, 24) == TOO_SMALL_MESSAGE
    assert render_frame_shell(80, 23) == TOO_SMALL_MESSAGE
    assert render_frame_shell(40, 10) == TOO_SMALL_MESSAGE


def test_frame_layout_selects_nearest_approved_grid_without_new_layout_tree():
    assert frame_layout_for_viewport(120, 40) == FRAME_LAYOUTS[(120, 40)]
    assert frame_layout_for_viewport(101, 33) == FRAME_LAYOUTS[(120, 40)]
    assert frame_layout_for_viewport(90, 30) == FRAME_LAYOUTS[(100, 32)]
    assert frame_layout_for_viewport(80, 24) == FRAME_LAYOUTS[(80, 24)]
    assert frame_layout_for_viewport(140, 50) == FRAME_LAYOUTS[(120, 40)]
    assert frame_layout_for_viewport(79, 24) is None


def test_frame_buffer_refuses_writes_to_protected_cells_and_subcell_coordinates():
    layout = FRAME_LAYOUTS[(80, 24)]
    frame = FrameBuffer(layout)
    cells = protected_cells(layout)
    assert (0, 0) in cells
    assert (layout.body_rule_row, layout.left_divider_col) in cells

    with pytest.raises(FrameDrawError, match="protected"):
        frame.put_text(0, 0, "x")
    with pytest.raises(FrameDrawError, match="whole character cells"):
        frame.put_text(1.5, 1, "x")  # type: ignore[arg-type]
    with pytest.raises(FrameDrawError, match="outside frame"):
        frame.put_text(1, layout.cols, "x")


def test_frame_buffer_allows_content_inside_column_cells():
    layout = FRAME_LAYOUTS[(80, 24)]
    frame = FrameBuffer(layout)
    frame.put_text(1, 1, "PM")
    frame.put_text(1, layout.left_divider_col + 1, "center")
    frame.put_text(1, layout.right_divider_col + 1, "inspector")
    line = frame.lines()[1]
    assert "PM" in line
    assert "center" in line
    assert "inspector" in line
