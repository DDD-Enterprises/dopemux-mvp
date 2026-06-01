"""PR readiness queue panel."""

from __future__ import annotations

from textual.widgets import Static

from dopemux.orchestrator.ui.data_sources import get_pr_queue_data
from dopemux.ui.theme import Glyphs, styled_panel, styled_table


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
                border_style="#4A9E94",
                header_style="bold #7DFBF6"
            )
            
            # Show top 3 PRs
            for pr in entries[:3]:
                state_color = "#94FADB" if pr.get("is_ready", False) else "#FFCF78"
                table.add_row(
                    f"[bold #7DFBF6]#{pr.get('number', 'N/A')}[/]",
                    f"[{state_color}]{pr.get('readiness', 'STALE')}[/]",
                    f"[bold #94A3B8]{pr.get('age', 'unknown')}[/]"
                )
                
            if len(entries) > 3:
                table.add_row(
                    f"[bold #94A3B8](+{len(entries) - 3} more PRs in queue)[/]",
                    "",
                    ""
                )
            elif not entries:
                table.add_row("[bold #94A3B8]No pull requests in queue[/]", "", "")
                
            return styled_panel(
                table,
                title=f"{Glyphs.GIT} PR READINESS GRIDS",
                border_style="#F5F26D",
            )
        except Exception as e:
            return styled_panel(
                f"[#FF8BD1]Error: {e}[/]",
                title="PR READINESS GRIDS (FAILED)",
                border_style="red",
            )
