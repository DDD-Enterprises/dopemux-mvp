"""
Decisions Commands

BETA-CLI-01: list / show / query / review / update-outcome subcommands
were absent.  This module now implements them against the ConPort HTTP
API (localhost:${CONPORT_MCP_PORT:-3005}).
"""

import os
from typing import Optional

import click

from ..console import console
from ..ui.theme import styled_panel, styled_table, error_panel, Glyphs, StatusChip

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _conport_url() -> str:
    port = os.environ.get("CONPORT_MCP_PORT", "3005")
    return f"http://localhost:{port}"


def _workspace_id() -> str:
    return os.environ.get(
        "DOPEMUX_WORKSPACE_ID",
        os.environ.get("TASK_ORCHESTRATOR_PROJECT_ROOT", os.getcwd()),
    )


def _get_decisions(workspace_id: str) -> list:
    """Fetch all decisions from ConPort. Returns [] on error."""
    try:
        import requests
        r = requests.get(
            f"{_conport_url()}/api/decisions",
            params={"workspace_id": workspace_id},
            timeout=10,
        )
        r.raise_for_status()
        return r.json().get("decisions", [])
    except Exception as exc:
        console.logger.warning(f"[yellow]ConPort unavailable: {exc}[/yellow]")
        return []


def _print_decision_table(decisions: list) -> None:
    if not decisions:
        console.logger.info("[text.dim]No decisions found.[/text.dim]")
        return
    table = styled_table(
        "Decisions",
        columns=["ID", "Summary", "Date"],
        show_lines=True,
    )
    for d in decisions:
        table.add_row(
            str(d.get("id", "—")),
            d.get("summary", "")[:80],
            str(d.get("created_at", d.get("timestamp", "—")))[:19],
        )
    console.print(table)


# ---------------------------------------------------------------------------
# decisions group
# ---------------------------------------------------------------------------

@click.group()
def decisions():
    """
    📊 Decision Governance: Track and analyze cockpit conclusions

    Orchestrates the logging and analysis of ritual decisions within the
    persistent knowledge graph. Synchronizes ADHD-optimized visualizations
    with review workflows to ensure high-fidelity cognitive alignment.
    """
    pass


# ---------------------------------------------------------------------------
# decisions list
# ---------------------------------------------------------------------------

@decisions.command("list")
@click.option("--workspace", "-w", default=None, help="Workspace ID (defaults to DOPEMUX_WORKSPACE_ID or cwd)")
@click.option("--limit", "-n", default=20, show_default=True, help="Max decisions to show")
def decisions_list(workspace: Optional[str], limit: int):
    """List recent decisions from ConPort."""
    wid = workspace or _workspace_id()
    items = _get_decisions(wid)
    _print_decision_table(items[:limit])


# ---------------------------------------------------------------------------
# decisions show
# ---------------------------------------------------------------------------

@decisions.command("show")
@click.argument("decision_id", type=int)
@click.option("--workspace", "-w", default=None)
def decisions_show(decision_id: int, workspace: Optional[str]):
    """Show full detail for a single decision by ID."""
    wid = workspace or _workspace_id()
    items = _get_decisions(wid)
    match = next((d for d in items if d.get("id") == decision_id), None)
    if not match:
        console.logger.error(f"[red]Decision {decision_id} not found.[/red]")
        raise SystemExit(1)
    panel = styled_panel(
        "\n".join([
            f"[bold]Summary:[/bold]    {match.get('summary', '—')}",
            f"[bold]Rationale:[/bold]  {match.get('rationale', '—')}",
            f"[bold]Alternatives:[/bold] {', '.join(match.get('alternatives', [])) or '—'}",
            f"[bold]Date:[/bold]       {match.get('created_at', match.get('timestamp', '—'))}",
            f"[bold]Tags:[/bold]       {', '.join(match.get('tags', [])) or '—'}",
        ]),
        title=f"Decision #{decision_id}",
    )
    console.print(panel)


# ---------------------------------------------------------------------------
# decisions query
# ---------------------------------------------------------------------------

@decisions.command("query")
@click.argument("term")
@click.option("--workspace", "-w", default=None)
@click.option("--limit", "-n", default=20, show_default=True)
def decisions_query(term: str, workspace: Optional[str], limit: int):
    """Search decisions whose summary or rationale contains TERM."""
    wid = workspace or _workspace_id()
    items = _get_decisions(wid)
    term_lower = term.lower()
    matches = [
        d for d in items
        if term_lower in d.get("summary", "").lower()
        or term_lower in d.get("rationale", "").lower()
    ]
    if not matches:
        console.logger.info(f"[text.dim]No decisions matching {term!r}.[/text.dim]")
        return
    _print_decision_table(matches[:limit])


# ---------------------------------------------------------------------------
# decisions review  (add a review note to an existing decision)
# ---------------------------------------------------------------------------

@decisions.command("review")
@click.argument("decision_id", type=int)
@click.option("--note", "-m", required=True, help="Review note to attach")
@click.option("--workspace", "-w", default=None)
def decisions_review(decision_id: int, note: str, workspace: Optional[str]):
    """
    Attach a review note to a decision by logging a linked follow-up entry.

    ConPort does not support in-place mutation, so review notes are stored as
    a new decision whose summary references the original ID.
    """
    wid = workspace or _workspace_id()
    try:
        import requests
        r = requests.post(
            f"{_conport_url()}/api/decisions",
            json={
                "workspace_id": wid,
                "summary": f"[Review of #{decision_id}] {note}",
                "rationale": f"Follow-up review note for decision #{decision_id}.",
                "alternatives": [],
            },
            timeout=10,
        )
        r.raise_for_status()
        result = r.json()
        new_id = result.get("id", "?")
        console.logger.info(f"[green]Review note logged as decision #{new_id}.[/green]")
    except Exception as exc:
        console.logger.error(f"[red]Failed to log review: {exc}[/red]")
        raise SystemExit(1)


# ---------------------------------------------------------------------------
# decisions update-outcome
# ---------------------------------------------------------------------------

@decisions.command("update-outcome")
@click.argument("decision_id", type=int)
@click.option("--outcome", "-o", required=True, help="Outcome description (what actually happened)")
@click.option("--workspace", "-w", default=None)
def decisions_update_outcome(decision_id: int, outcome: str, workspace: Optional[str]):
    """
    Record the real-world outcome of a decision.

    Logged as a new ConPort entry linked to the original decision ID so the
    history is append-only and auditable.
    """
    wid = workspace or _workspace_id()
    try:
        import requests
        r = requests.post(
            f"{_conport_url()}/api/decisions",
            json={
                "workspace_id": wid,
                "summary": f"[Outcome of #{decision_id}] {outcome}",
                "rationale": f"Real-world outcome recorded for decision #{decision_id}.",
                "alternatives": [],
            },
            timeout=10,
        )
        r.raise_for_status()
        result = r.json()
        new_id = result.get("id", "?")
        console.logger.info(
            f"[green]Outcome logged as decision #{new_id} (linked to #{decision_id}).[/green]"
        )
    except Exception as exc:
        console.logger.error(f"[red]Failed to log outcome: {exc}[/red]")
        raise SystemExit(1)


# ---------------------------------------------------------------------------
# Existing sub-groups (kept unchanged)
# ---------------------------------------------------------------------------

@decisions.group()
def energy():
    """
    ⚡ Vitality Telemetry: Track ritual energy levels

    Synchronizes ADHD-optimized energy tracking rituals. Monitors cognitive
    vitality patterns throughout the temporal cycle to optimize
    decision-making timing and ritual efficiency.
    """
    pass


@decisions.group()
def patterns():
    """
    🔍 Cognitive Synthesis: Pattern detection and learning

    Engages the pattern detection engine to synthesize insights from
    decision history. Automatically clusters ritual tags, identifies
    sequential chains, and correlates energy telemetry with ritual quality.
    """
    pass


# ============================================================================
# Development Mode Commands (Contributor Support)
# ============================================================================
