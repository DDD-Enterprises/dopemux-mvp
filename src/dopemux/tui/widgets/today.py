"""Today panel - operators daily planning matrix summary."""

from __future__ import annotations

from textual.widgets import Static

from dopemux.orchestrator.ui.data_sources import get_panel_data
from dopemux.ui.theme import (
    ERROR_RED,
    Glyphs,
    RITUAL_CYAN,
    SERUM_MINT,
    STRUCTURAL_BORDER,
    styled_panel,
    styled_table,
)


class TodayPanel(Static):
    """Daily matrix telemetry panel."""

    def render(self) -> object:
        try:
            data = get_panel_data("today")
            table = styled_table(
                "",
                "Metric",
                "Value",
                show_header=False,
                compact=True,
                border_style=STRUCTURAL_BORDER,
                header_style=f"bold {RITUAL_CYAN}"
            )
            table.add_row("[bold]Authority[/]", f"[{SERUM_MINT}]{data.get('authority', 'N/A')}[/]")
            table.add_row("[bold]Total Panels[/]", f"[{RITUAL_CYAN}]{len(data.get('panels', []))}[/]")
            table.add_row("[bold]Mode[/]", f"[{SERUM_MINT}]READ-ONLY[/] (Fail-Closed)")
            table.add_row("[bold]Will Write[/]", f"[{ERROR_RED}]FALSE[/]")

            return styled_panel(
                table,
                title=f"{Glyphs.PENDING} OPERATOR DAILY MATRIX",
                border_style=RITUAL_CYAN,
            )
        except Exception as e:
            return styled_panel(
                f"[{ERROR_RED}]Error: {e}[/]",
                title="OPERATOR DAILY MATRIX (FAILED)",
                border_style=ERROR_RED,
            )
