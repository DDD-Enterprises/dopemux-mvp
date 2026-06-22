"""Regression: `dopemux dashboard` crashed with
``MissingStyle: Failed to get style 'warning'``.

Dashboard widgets render rich Panels/markup using dopemux *theme* style names
(``warning``, ``text.dim``, ``label``, ``mint`` …). Textual renders widgets via
``app.console`` (see textual.visual.render_strips), which did not have
``DOPEMUX_THEME`` registered — so the first themed render raised MissingStyle.
"""

import pytest
from rich.console import Console
from rich.errors import MissingStyle

from dopemux.ui.dashboard import DopemuxDashboard


def test_warning_is_unknown_to_a_plain_console():
    """Confirms the failure mode: 'warning' is a dopemux theme name, not a base style."""
    with pytest.raises(MissingStyle):
        Console().get_style("warning")


async def test_dashboard_registers_dopemux_theme_on_console():
    """After mount, the app console must resolve dopemux theme style names."""
    app = DopemuxDashboard()
    async with app.run_test():
        for name in ("warning", "text.dim", "label"):
            # Raises MissingStyle if the theme was not registered.
            assert app.console.get_style(name) is not None
