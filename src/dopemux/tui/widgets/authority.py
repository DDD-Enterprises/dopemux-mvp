"""Authority panel - capability classifications and writer policies."""

from __future__ import annotations

from textual.widgets import Static

from dopemux.orchestrator.ui.data_sources import get_authority_data
from dopemux.ui.theme import Glyphs, styled_panel, styled_table


class AuthorityPanel(Static):
    """Capabilities authorization panel."""

    def render(self) -> object:
        try:
            data = get_authority_data()
            caps = data.get("capabilities", [])
            
            table = styled_table(
                "",
                "Capability ID",
                "Tier",
                "Allowed",
                show_header=True,
                compact=True,
                border_style="#4A9E94",
                header_style="bold #7DFBF6"
            )
            
            # Show top 3 capabilities
            for cap in caps[:3]:
                status_color = "#94FADB" if cap["allowed"] else "#FF8BD1"
                status_label = "YES" if cap["allowed"] else "NO"
                table.add_row(
                    f"[bold]{cap['capability_id']}[/]",
                    f"[#7DFBF6]{cap['tier']}[/]",
                    f"[{status_color}]{status_label}[/]"
                )
                
            if len(caps) > 3:
                table.add_row(
                    f"[bold #94A3B8](+{len(caps) - 3} more capability rules)[/]",
                    "",
                    ""
                )
                
            return styled_panel(
                table,
                title=f"{Glyphs.INFO} INTEGRATION AUTHORITY",
                border_style="#7DFBF6",
            )
        except Exception as e:
            return styled_panel(
                f"[#FF8BD1]Error: {e}[/]",
                title="INTEGRATION AUTHORITY (FAILED)",
                border_style="red",
            )
