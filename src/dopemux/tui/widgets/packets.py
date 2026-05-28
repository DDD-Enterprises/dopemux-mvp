"""Packets panel - task packet validation matrices."""

from __future__ import annotations

from textual.widgets import Static

from dopemux.orchestrator.ui.data_sources import get_packets_data
from dopemux.ui.theme import Glyphs, styled_panel, styled_table


class PacketsPanel(Static):
    """Task validation panel."""

    def render(self) -> object:
        try:
            packets = get_packets_data()
            table = styled_table(
                "",
                "Packet File",
                "Validation",
                show_header=True,
                compact=True,
                border_style="#4A9E94",
                header_style="bold #7DFBF6"
            )
            
            # Show top 3 task packets
            for pkt in packets[:3]:
                status_color = "#94FADB" if pkt["valid"] else "#FF8BD1"
                status_label = "PASS" if pkt["valid"] else "FAIL"
                table.add_row(
                    f"[bold]{pkt['name']}[/]",
                    f"[{status_color}]{status_label}[/]"
                )
                
            if len(packets) > 3:
                table.add_row(
                    f"[bold #94A3B8](+{len(packets) - 3} more task packets)[/]",
                    ""
                )
            elif not packets:
                table.add_row("[bold #94A3B8]No task packets found[/]", "")
                
            return styled_panel(
                table,
                title=f"{Glyphs.PACKAGE} UNBLOCKED TASK PACKETS",
                border_style="#9B78FF",
            )
        except Exception as e:
            return styled_panel(
                f"[#FF8BD1]Error: {e}[/]",
                title="UNBLOCKED TASK PACKETS (FAILED)",
                border_style="red",
            )
