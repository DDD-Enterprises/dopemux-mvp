"""Authority panel - capability classifications and writer policies."""

from __future__ import annotations

from textual.widgets import Static

from dopemux.orchestrator.ui.data_sources import get_authority_data
from dopemux.ui.theme import (
    ERROR_RED,
    Glyphs,
    RITUAL_CYAN,
    SERUM_MINT,
    STRUCTURAL_BORDER,
    TEXT_SECONDARY,
    styled_panel,
    styled_table,
)


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
                border_style=STRUCTURAL_BORDER,
                header_style=f"bold {RITUAL_CYAN}"
            )

            # Show top 3 capabilities
            for cap in caps[:3]:
                status_color = SERUM_MINT if cap["allowed"] else ERROR_RED
                status_label = "YES" if cap["allowed"] else "NO"
                table.add_row(
                    f"[bold {RITUAL_CYAN}]{cap['capability_id']}[/]",
                    f"[{TEXT_SECONDARY}]{cap['tier']}[/]",
                    f"[{status_color}]{status_label}[/]"
                )

            if len(caps) > 3:
                table.add_row(
                    f"[bold {TEXT_SECONDARY}](+{len(caps) - 3} more capability rules)[/]",
                    "",
                    ""
                )

            return styled_panel(
                table,
                title=f"{Glyphs.INFO} INTEGRATION AUTHORITY",
                border_style=RITUAL_CYAN,
            )
        except Exception as e:
            return styled_panel(
                f"[{ERROR_RED}]Error: {e}[/]",
                title="INTEGRATION AUTHORITY (FAILED)",
                border_style=ERROR_RED,
            )
