from dopemux.ui.cockpit.frame import LAYOUTS, FrameBuffer, draw_static_grid


def test_supported_frame_dimensions_are_exact() -> None:
    for layout in LAYOUTS.values():
        frame = FrameBuffer(layout.width, layout.height, layout)
        rendered = frame.render()
        lines = rendered.splitlines()
        assert len(lines) == layout.height
        assert all(len(line) == layout.width for line in lines)


def test_normal_writes_do_not_overwrite_protected_cells() -> None:
    layout = LAYOUTS["80x24"]
    frame = FrameBuffer(layout.width, layout.height, layout)
    draw_static_grid(frame, layout)
    before = frame.render().splitlines()
    frame.write(0, 0, "blocked")
    frame.write(5, layout.left_divider, "blocked")
    frame.write(layout.body_rule, 2, "blocked")
    after = frame.render().splitlines()
    assert after[0] == before[0]
    assert after[5][layout.left_divider] == before[5][layout.left_divider]
    assert after[layout.body_rule] == before[layout.body_rule]


def test_hard_clipping_has_no_ellipsis_or_wrapping() -> None:
    frame = FrameBuffer(10, 3)
    frame.write(1, 7, "abcdef")
    lines = frame.render().splitlines()
    assert lines[1] == "       abc"
    assert lines[2] == "          "
    assert "..." not in frame.render()
    assert "…" not in frame.render()
