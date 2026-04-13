from dopemux.ui.splash import DOPEMUX_STARTUP_BANNER, render_startup_banner
from dopemux.ui.theme import RenderMode


def test_render_startup_banner_plain_mode_emits_plain_banner_text() -> None:
    banner = render_startup_banner(RenderMode.PLAIN)

    assert banner.plain == DOPEMUX_STARTUP_BANNER.rstrip("\n")


def test_render_startup_banner_rich_mode_preserves_banner_text() -> None:
    banner = render_startup_banner(RenderMode.RICH)

    assert banner.plain == DOPEMUX_STARTUP_BANNER.rstrip("\n")
    assert "[ deterministic core ]" in banner.plain
    assert "[ memory mesh ]" in banner.plain
    assert "[ operator ]" in banner.plain
