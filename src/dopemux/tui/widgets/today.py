"""Today panel - operators daily planning matrix summary."""

from __future__ import annotations

from textual.widgets import Static

from dopemux.orchestrator.ui.data_sources import get_today_data
from dopemux.ui.theme import Glyphs, styled_panel, styled_table


class TodayPanel(Static):
    """Daily matrix telemetry panel."""

    def render(self) -> object:
        try:
            data = get_today_data()
            table = styled_table(
                "",
                "Metric",
                "Value",
                show_header=False,
                compact=True,
                border_style="#4A9E94",
                header_style="bold #7DFBF6"
            )
            table.add_row("[bold]Authority[/]", f"[#94FADB]{data.get('authority', 'N/A')}[/]")
            table.add_row("[bold]Total Panels[/]", f"[#7DFBF6]{len(data.get('panels', []))}[/]")
            table.add_row("[bold]Mode[/]", "[#94FADB]READ-ONLY[/] (Fail-Closed)")
            table.add_row("[bold]Will Write[/]", "[#FF8BD1]FALSE[/]")
            
            return styled_panel(
                table,
                title=f"{Glyphs.PENDING} OPERATOR DAILY MATRIX",
                border_style="#7DFBF6",
            )
        except Exception as e:
            return styled_panel(
                f"[#FF8BD1]Error: {e}[/]",
                title="OPERATOR DAILY MATRIX (FAILED)",
                border_style="red",
            )
