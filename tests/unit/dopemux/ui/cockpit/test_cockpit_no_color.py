from dopemux.ui.cockpit.render import render_cockpit


def test_no_color_semantics_have_no_ansi_sequences(monkeypatch) -> None:
    monkeypatch.setenv("NO_COLOR", "1")
    output = render_cockpit(120, 40)
    assert "\x1b[" not in output
    assert "[LIVE]" in output
    assert "authority:" in output
    assert "SRC=" in output
    assert "dopecon-bridge" in output
    assert "adapter/proxy o" in output
