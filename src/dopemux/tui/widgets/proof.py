"""Proof panel - proof bundle validation matrices."""

from __future__ import annotations

from textual.widgets import Static

from dopemux.orchestrator.ui.data_sources import get_proof_data
from dopemux.ui.theme import Glyphs, styled_panel, styled_table


class ProofPanel(Static):
    """Proof attestation panel."""

    def render(self) -> object:
        try:
            proofs = get_proof_data()
            table = styled_table(
                "",
                "Proof Path",
                "Validation",
                show_header=True,
                compact=True,
                border_style="#4A9E94",
                header_style="bold #7DFBF6"
            )
            
            # Show top 3 proof bundles
            for proof in proofs[:3]:
                status_color = "#94FADB" if proof["valid"] else "#FF8BD1"
                status_label = "PASS" if proof["valid"] else "FAIL"
                table.add_row(
                    f"[bold]{proof['path']}[/]",
                    f"[{status_color}]{status_label}[/]"
                )
                
            if len(proofs) > 3:
                table.add_row(
                    f"[bold #94A3B8](+{len(proofs) - 3} more proof bundles)[/]",
                    ""
                )
            elif not proofs:
                table.add_row("[bold #94A3B8]No proof bundles found[/]", "")
                
            return styled_panel(
                table,
                title=f"{Glyphs.WRENCH} PROOF ATTESTATION MATRIX",
                border_style="#94FADB",
            )
        except Exception as e:
            return styled_panel(
                f"[#FF8BD1]Error: {e}[/]",
                title="PROOF ATTESTATION MATRIX (FAILED)",
                border_style="red",
            )
