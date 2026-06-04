"""Context panel - context source freshness tracking."""

from __future__ import annotations

from textual.widgets import Static

from dopemux.orchestrator.ui.data_sources import get_context_data
from dopemux.ui.theme import (
    ERROR_RED,
    Glyphs,
    RITUAL_CYAN,
    SERUM_MINT,
    STRUCTURAL_BORDER,
    styled_panel,
    styled_table,
)


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
                border_style=STRUCTURAL_BORDER,
                header_style=f"bold {RITUAL_CYAN}"
            )

            for source, meta in data.items():
                if isinstance(meta, dict):
                    fresh = meta.get("fresh", True)
                    status_color = SERUM_MINT if fresh else ERROR_RED
                    status_label = "FRESH" if fresh else "STALE"
                    table.add_row(
                        f"[bold {RITUAL_CYAN}]{source}[/]",
                        f"[{status_color}]{Glyphs.SUCCESS if fresh else Glyphs.ERROR} {status_label}[/]"
                    )

            return styled_panel(
                table,
                title=f"{Glyphs.SERVER} CONTEXT FRESHNESS TELEMETRY",
                border_style=RITUAL_CYAN,
            )
        except Exception as e:
            return styled_panel(
                f"[{ERROR_RED}]Error: {e}[/]",
                title="CONTEXT FRESHNESS TELEMETRY (FAILED)",
                border_style=ERROR_RED,
            )
