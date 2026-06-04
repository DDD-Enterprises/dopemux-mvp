"""Do Not Touch panel - visual fail-closed refusal matrix."""

from __future__ import annotations

from textual.widgets import Static

from dopemux.orchestrator.ui.data_sources import get_do_not_touch_data
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
                border_style=STRUCTURAL_BORDER,
                header_style=f"bold {RITUAL_CYAN}"
            )

            # Show top 3 refusals
            for ref in refusals[:3]:
                table.add_row(
                    f"[bold {ERROR_RED}]{ref['capability_id']}[/]",
                    f"[bold {RITUAL_CYAN}]{ref['tier']}[/]",
                    f"[bold {ERROR_RED}]REFUSE[/]"
                )

            if len(refusals) > 3:
                table.add_row(
                    f"[bold {TEXT_SECONDARY}](+{len(refusals) - 3} more fail-closed policies)[/]",
                    "",
                    ""
                )
            elif not refusals:
                table.add_row(f"[bold {SERUM_MINT}]No prohibited capabilities in policy[/]", "", "")

            return styled_panel(
                table,
                title=f"{Glyphs.BLOCKED} REFUSAL MATRIX SANCTUARY",
                border_style=ERROR_RED,
            )
        except Exception as e:
            return styled_panel(
                f"[{ERROR_RED}]Error: {e}[/]",
                title="REFUSAL MATRIX SANCTUARY (FAILED)",
                border_style=ERROR_RED,
            )
