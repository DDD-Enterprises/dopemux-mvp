from dopemux.ui.splash import DOPEMUX_STARTUP_BANNER, render_startup_banner
from dopemux.ui.theme import Glyphs, RenderMode, set_render_mode


def test_render_startup_banner_plain_mode_emits_plain_banner_text() -> None:
    banner = render_startup_banner(RenderMode.PLAIN)

    assert banner.plain == DOPEMUX_STARTUP_BANNER.rstrip("\n")


def test_render_startup_banner_rich_mode_preserves_banner_text() -> None:
    banner = render_startup_banner(RenderMode.RICH)

    assert banner.plain == DOPEMUX_STARTUP_BANNER.rstrip("\n")
    assert "[ deterministic core ]" in banner.plain
    assert "[ memory mesh ]" in banner.plain
    assert "[ operator ]" in banner.plain


def test_glyphs_use_ascii_fallback_in_plain_mode() -> None:
    set_render_mode(RenderMode.PLAIN)

    public_glyphs = [
        value
        for name, value in vars(Glyphs).items()
        if name.isupper() and isinstance(value, str)
    ]

    try:
        assert Glyphs.SUCCESS != "\uf058"
        assert Glyphs.SUCCESS == "OK"
        assert all(value.isascii() for value in public_glyphs)
    finally:
        set_render_mode(RenderMode.RICH)
