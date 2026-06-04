"""Risks panel - elevated security capability risks (TX, TU, T6)."""

from __future__ import annotations

from textual.widgets import Static

from dopemux.orchestrator.ui.data_sources import get_risks_data
from dopemux.ui.theme import (
    ERROR_RED,
    GILT_EDGE,
    Glyphs,
    RITUAL_CYAN,
    SAINT_GOLD,
    SERUM_MINT,
    STRUCTURAL_BORDER,
    TEXT_SECONDARY,
    styled_panel,
    styled_table,
)


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
                border_style=STRUCTURAL_BORDER,
                header_style=f"bold {RITUAL_CYAN}"
            )

            # Show top 3 risks
            for risk in risks[:3]:
                table.add_row(
                    f"[bold {ERROR_RED}]{risk['capability_id']}[/]",
                    f"[bold {SAINT_GOLD}]{risk['tier']}[/]",
                    f"[bold {GILT_EDGE}]{risk['mode'].upper()}[/]"
                )

            if len(risks) > 3:
                table.add_row(
                    f"[bold {TEXT_SECONDARY}](+{len(risks) - 3} more open risks)[/]",
                    "",
                    ""
                )
            elif not risks:
                table.add_row(f"[bold {SERUM_MINT}]No elevated risks found[/]", "", "")

            return styled_panel(
                table,
                title=f"{Glyphs.WARNING} OPEN SECURITY RISKS",
                border_style=SAINT_GOLD,
            )
        except Exception as e:
            return styled_panel(
                f"[{ERROR_RED}]Error: {e}[/]",
                title="OPEN SECURITY RISKS (FAILED)",
                border_style=ERROR_RED,
            )
