"""Do Not Touch panel - visual fail-closed refusal matrix."""

from __future__ import annotations

from textual.widgets import Static

from dopemux.orchestrator.ui.data_sources import get_do_not_touch_data
from dopemux.ui.theme import Glyphs, styled_panel, styled_table


class DoNotTouchPanel(Static):
    """Refusal matrix panel."""

    def render(self) -> object:
        try:
            data = get_do_not_touch_data()
            refusals = data.get("refusals", [])
            
            table = styled_table(
                "",
                "Prohibited Capability",
                "Tier",
                "Decision",
                show_header=True,
                compact=True,
                border_style="#4A9E94",
                header_style="bold #7DFBF6"
            )
            
            # Show top 3 refusals
            for ref in refusals[:3]:
                table.add_row(
                    f"[bold #FF8BD1]{ref['capability_id']}[/]",
                    f"[bold #7DFBF6]{ref['tier']}[/]",
                    "[bold #FF8BD1]REFUSE[/]"
                )
                
            if len(refusals) > 3:
                table.add_row(
                    f"[bold #94A3B8](+{len(refusals) - 3} more fail-closed policies)[/]",
                    "",
                    ""
                )
            elif not refusals:
                table.add_row("[bold #94FADB]No prohibited capabilities in policy[/]", "", "")
                
            return styled_panel(
                table,
                title=f"{Glyphs.BLOCKED} REFUSAL MATRIX SANCTUARY",
                border_style="#FF8BD1",
            )
        except Exception as e:
            return styled_panel(
                f"[#FF8BD1]Error: {e}[/]",
                title="REFUSAL MATRIX SANCTUARY (FAILED)",
                border_style="red",
            )
