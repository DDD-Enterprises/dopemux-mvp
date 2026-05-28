"""Risks panel - elevated security capability risks (TX, TU, T6)."""

from __future__ import annotations

from textual.widgets import Static

from dopemux.orchestrator.ui.data_sources import get_risks_data
from dopemux.ui.theme import Glyphs, styled_panel, styled_table


class RisksPanel(Static):
    """Elevated security risks panel."""

    def render(self) -> object:
        try:
            risks = get_risks_data()
            table = styled_table(
                "",
                "Risk Capability",
                "Tier",
                "Mode",
                show_header=True,
                compact=True,
                border_style="#4A9E94",
                header_style="bold #7DFBF6"
            )
            
            # Show top 3 risks
            for risk in risks[:3]:
                table.add_row(
                    f"[bold #FF8BD1]{risk['capability_id']}[/]",
                    f"[bold #FFCF78]{risk['tier']}[/]",
                    f"[bold #F5F26D]{risk['mode'].upper()}[/]"
                )
                
            if len(risks) > 3:
                table.add_row(
                    f"[bold #94A3B8](+{len(risks) - 3} more open risks)[/]",
                    "",
                    ""
                )
            elif not risks:
                table.add_row("[bold #94FADB]No elevated risks found[/]", "", "")
                
            return styled_panel(
                table,
                title=f"{Glyphs.WARNING} OPEN SECURITY RISKS",
                border_style="#FFCF78",
            )
        except Exception as e:
            return styled_panel(
                f"[#FF8BD1]Error: {e}[/]",
                title="OPEN SECURITY RISKS (FAILED)",
                border_style="red",
            )
