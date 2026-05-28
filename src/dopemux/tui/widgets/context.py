"""Context panel - context source freshness tracking."""

from __future__ import annotations

from textual.widgets import Static

from dopemux.orchestrator.ui.data_sources import get_context_data
from dopemux.ui.theme import Glyphs, styled_panel, styled_table


class ContextPanel(Static):
    """Context telemetry panel."""

    def render(self) -> object:
        try:
            data = get_context_data()
            table = styled_table(
                "",
                "Source",
                "Telemetry Status",
                show_header=True,
                compact=True,
                border_style="#4A9E94",
                header_style="bold #7DFBF6"
            )
            
            for source, meta in data.items():
                if isinstance(meta, dict):
                    fresh = meta.get("fresh", True)
                    status_color = "#94FADB" if fresh else "#FF8BD1"
                    status_label = "FRESH" if fresh else "STALE"
                    table.add_row(
                        f"[bold #7DFBF6]{source}[/]",
                        f"[{status_color}]{Glyphs.SUCCESS if fresh else Glyphs.ERROR} {status_label}[/]"
                    )
                
            return styled_panel(
                table,
                title=f"{Glyphs.SERVER} CONTEXT FRESHNESS TELEMETRY",
                border_style="#4A9E94",
            )
        except Exception as e:
            return styled_panel(
                f"[#FF8BD1]Error: {e}[/]",
                title="CONTEXT FRESHNESS TELEMETRY (FAILED)",
                border_style="red",
            )
