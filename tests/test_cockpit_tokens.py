from __future__ import annotations

from dopemux.ui.cockpit.tokens import validate_rendered_text
from dopemux.voice import Surface


def test_validate_rendered_text_requires_ui_closer() -> None:
    result = validate_rendered_text(
        "label: Focus\nmessage: Evidence row updated.\naction: Review",
        surface=Surface.UI,
    )

    assert not result.ok
    assert any(item.code == "MISSING_CLOSER" for item in result.violations)
