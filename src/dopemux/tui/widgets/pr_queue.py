"""PR readiness queue panel."""

from __future__ import annotations

from textual.widgets import Static

from dopemux.orchestrator.ui.data_sources import get_pr_queue_data
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


class PRQueuePanel(Static):
    """PR classification queue panel."""

    def render(self) -> object:
        try:
            data = get_pr_queue_data()
            entries = data.get("entries", [])
            
            table = styled_table(
                "",
                "PR",
                "State",
                "Age",
                show_header=True,
                compact=True,
                border_style=STRUCTURAL_BORDER,
                header_style=f"bold {RITUAL_CYAN}"
            )

            # Show top 3 PRs
            for pr in entries[:3]:
                state_color = SERUM_MINT if pr.get("is_ready", False) else SAINT_GOLD
                table.add_row(
                    f"[bold {RITUAL_CYAN}]#{pr.get('number', 'N/A')}[/]",
                    f"[{state_color}]{pr.get('readiness', 'STALE')}[/]",
                    f"[bold {TEXT_SECONDARY}]{pr.get('age', 'unknown')}[/]"
                )

            if len(entries) > 3:
                table.add_row(
                    f"[bold {TEXT_SECONDARY}](+{len(entries) - 3} more PRs in queue)[/]",
                    "",
                    ""
                )
            elif not entries:
                table.add_row(f"[bold {TEXT_SECONDARY}]No pull requests in queue[/]", "", "")

            return styled_panel(
                table,
                title=f"{Glyphs.GIT} PR READINESS GRIDS",
                border_style=GILT_EDGE,
            )
        except Exception as e:
            return styled_panel(
                f"[{ERROR_RED}]Error: {e}[/]",
                title="PR READINESS GRIDS (FAILED)",
                border_style=ERROR_RED,
            )
