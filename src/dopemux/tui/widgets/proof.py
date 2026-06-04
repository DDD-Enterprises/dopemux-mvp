"""Proof panel - proof bundle validation matrices."""

from __future__ import annotations

from textual.widgets import Static

from dopemux.orchestrator.ui.data_sources import get_proof_data
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
                border_style=STRUCTURAL_BORDER,
                header_style=f"bold {RITUAL_CYAN}"
            )

            # Show top 3 proof bundles
            for proof in proofs[:3]:
                status_color = SERUM_MINT if proof["valid"] else ERROR_RED
                status_label = "PASS" if proof["valid"] else "FAIL"
                table.add_row(
                    f"[bold {RITUAL_CYAN}]{proof['path']}[/]",
                    f"[{status_color}]{status_label}[/]"
                )

            if len(proofs) > 3:
                table.add_row(
                    f"[bold {TEXT_SECONDARY}](+{len(proofs) - 3} more proof bundles)[/]",
                    ""
                )
            elif not proofs:
                table.add_row(f"[bold {TEXT_SECONDARY}]No proof bundles found[/]", "")

            return styled_panel(
                table,
                title=f"{Glyphs.WRENCH} PROOF ATTESTATION MATRIX",
                border_style=SERUM_MINT,
            )
        except Exception as e:
            return styled_panel(
                f"[{ERROR_RED}]Error: {e}[/]",
                title="PROOF ATTESTATION MATRIX (FAILED)",
                border_style=ERROR_RED,
            )
