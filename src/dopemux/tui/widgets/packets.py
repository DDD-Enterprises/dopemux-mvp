"""Packets panel - task packet validation matrices."""

from __future__ import annotations

from textual.widgets import Static

from dopemux.orchestrator.ui.data_sources import get_packets_data
from dopemux.ui.theme import (
    AFTERCARE_VIOLET,
    ERROR_RED,
    Glyphs,
    RITUAL_CYAN,
    SERUM_MINT,
    STRUCTURAL_BORDER,
    TEXT_SECONDARY,
    styled_panel,
    styled_table,
)


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
                border_style=STRUCTURAL_BORDER,
                header_style=f"bold {RITUAL_CYAN}"
            )

            # Show top 3 task packets
            for pkt in packets[:3]:
                status_color = SERUM_MINT if pkt["valid"] else ERROR_RED
                status_label = "PASS" if pkt["valid"] else "FAIL"
                table.add_row(
                    f"[bold {RITUAL_CYAN}]{pkt['name']}[/]",
                    f"[{status_color}]{status_label}[/]"
                )

            if len(packets) > 3:
                table.add_row(
                    f"[bold {TEXT_SECONDARY}](+{len(packets) - 3} more task packets)[/]",
                    ""
                )
            elif not packets:
                table.add_row(f"[bold {TEXT_SECONDARY}]No task packets found[/]", "")

            return styled_panel(
                table,
                title=f"{Glyphs.PACKAGE} UNBLOCKED TASK PACKETS",
                border_style=AFTERCARE_VIOLET,
            )
        except Exception as e:
            return styled_panel(
                f"[{ERROR_RED}]Error: {e}[/]",
                title="UNBLOCKED TASK PACKETS (FAILED)",
                border_style=ERROR_RED,
            )
