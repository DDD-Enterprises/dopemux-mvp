"""
Decisions Commands

BETA-CLI-01: list / show / query / review / update-outcome subcommands
were absent.  This module now implements them against the ConPort HTTP
API (localhost:${CONPORT_HTTP_PORT:-3004} or CONPORT_URL).
"""

import os
import sys
from typing import Any, Optional

import click
import requests

from ..console import console
from ..ui.theme import styled_panel, styled_table

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

DEFAULT_DECISION_LOOKUP_LIMIT = 1000
WORKSPACE_HELP = "Workspace ID (defaults to DOPEMUX_WORKSPACE_ID or cwd)"


def _conport_url() -> str:
    if url := os.environ.get("CONPORT_URL"):
        return url.rstrip("/")
    port = os.environ.get("CONPORT_HTTP_PORT", "3004")
    return f"http://localhost:{port}"


def _workspace_id() -> str:
    return os.environ.get(
        "DOPEMUX_WORKSPACE_ID",
        os.environ.get("TASK_ORCHESTRATOR_PROJECT_ROOT", os.getcwd()),
    )


def _get_decisions(workspace_id: str, limit: int = 20) -> list[dict[str, Any]]:
    """Fetch all decisions from ConPort. Returns [] on error."""
    try:
        r = requests.get(
            f"{_conport_url()}/api/decisions",
            params={"workspace_id": workspace_id, "limit": limit},
            timeout=10,
        )
        r.raise_for_status()
        return r.json().get("decisions", [])
    except (requests.ConnectionError, requests.Timeout) as exc:
        console.logger.warning(f"[yellow]ConPort unavailable: {exc}[/yellow]")
        return []
    except requests.HTTPError as exc:
        response = exc.response
        status = response.status_code if response is not None else "unknown"
        console.logger.warning(f"[yellow]ConPort rejected decisions request: HTTP {status}[/yellow]")
        return []
    except requests.RequestException as exc:
        console.logger.warning(f"[yellow]ConPort request failed: {exc}[/yellow]")
        return []


def _find_decision(decisions: list[dict[str, Any]], decision_id: str) -> dict[str, Any] | None:
    return next((d for d in decisions if str(d.get("id")) == decision_id), None)


def _created_decision_id(result: dict[str, Any]) -> str:
    decision = result.get("decision")
    if isinstance(decision, dict):
        return str(decision.get("id", "?"))
    return str(result.get("id", "?"))


def _print_decision_table(decisions: list[dict[str, Any]]) -> None:
    if not decisions:
        console.logger.info("[text.dim]No decisions found.[/text.dim]")
        return
    table = styled_table(
        "Decisions",
        "ID",
        "Summary",
        "Date",
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
@click.option("--workspace", "-w", default=None, help=WORKSPACE_HELP)
@click.option("--limit", "-n", default=20, show_default=True, help="Max decisions to show")
def decisions_list(workspace: Optional[str], limit: int):
    """List recent decisions from ConPort."""
    wid = workspace or _workspace_id()
    items = _get_decisions(wid, limit=limit)
    _print_decision_table(items[:limit])


# ---------------------------------------------------------------------------
# decisions show
# ---------------------------------------------------------------------------

@decisions.command("show")
@click.argument("decision_id")
@click.option("--workspace", "-w", default=None, help=WORKSPACE_HELP)
def decisions_show(decision_id: str, workspace: Optional[str]):
    """Show full detail for a single decision by ID."""
    wid = workspace or _workspace_id()
    items = _get_decisions(wid, limit=DEFAULT_DECISION_LOOKUP_LIMIT)
    match = _find_decision(items, decision_id)
    if not match:
        console.logger.error(f"[red]Decision {decision_id} not found.[/red]")
        sys.exit(1)
    panel = styled_panel(
        "\n".join([
            f"[bold]Summary:[/bold]    {match.get('summary', '—')}",
            f"[bold]Rationale:[/bold]  {match.get('rationale', '—')}",
            f"[bold]Alternatives:[/bold] {', '.join(match.get('alternatives', [])) or '—'}",
            f"[bold]Date:[/bold]       {match.get('created_at', match.get('timestamp', '—'))}",
            f"[bold]Tags:[/bold]       {', '.join(match.get('tags', [])) or '—'}",
        ]),
        title=f"Decision {decision_id}",
    )
    console.print(panel)


# ---------------------------------------------------------------------------
# decisions query
# ---------------------------------------------------------------------------

@decisions.command("query")
@click.argument("term")
@click.option("--workspace", "-w", default=None, help=WORKSPACE_HELP)
@click.option("--limit", "-n", default=20, show_default=True, help="Max matching decisions to show")
def decisions_query(term: str, workspace: Optional[str], limit: int):
    """Search decisions whose summary or rationale contains TERM."""
    wid = workspace or _workspace_id()
    items = _get_decisions(wid, limit=max(limit, DEFAULT_DECISION_LOOKUP_LIMIT))
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
@click.argument("decision_id")
@click.option("--note", "-m", required=True, help="Review note to attach")
@click.option("--workspace", "-w", default=None, help=WORKSPACE_HELP)
def decisions_review(decision_id: str, note: str, workspace: Optional[str]):
    """
    Attach a review note to a decision by logging a referencing follow-up entry.

    ConPort does not support in-place mutation, so review notes are stored as
    a new decision whose summary references the original ID.
    """
    wid = workspace or _workspace_id()
    if not _find_decision(_get_decisions(wid, limit=DEFAULT_DECISION_LOOKUP_LIMIT), decision_id):
        console.logger.error(f"[red]Decision {decision_id} not found; review not logged.[/red]")
        sys.exit(1)
    try:
        r = requests.post(
            f"{_conport_url()}/api/decisions",
            json={
                "workspace_id": wid,
                "summary": f"[Review of {decision_id}] {note}",
                "rationale": f"Follow-up review note for decision {decision_id}.",
                "alternatives": [],
            },
            timeout=10,
        )
        r.raise_for_status()
        result = r.json()
        new_id = _created_decision_id(result)
        console.logger.info(f"[green]Review note logged as decision #{new_id}.[/green]")
    except requests.RequestException as exc:
        console.logger.error(f"[red]Failed to log review: {exc}[/red]")
        sys.exit(1)


# ---------------------------------------------------------------------------
# decisions update-outcome
# ---------------------------------------------------------------------------

@decisions.command("update-outcome")
@click.argument("decision_id")
@click.option("--outcome", "-o", required=True, help="Outcome description (what actually happened)")
@click.option("--workspace", "-w", default=None, help=WORKSPACE_HELP)
def decisions_update_outcome(decision_id: str, outcome: str, workspace: Optional[str]):
    """
    Record the real-world outcome of a decision.

    Logged as a new ConPort entry referencing the original decision ID so the
    history is append-only and auditable.
    """
    wid = workspace or _workspace_id()
    if not _find_decision(_get_decisions(wid, limit=DEFAULT_DECISION_LOOKUP_LIMIT), decision_id):
        console.logger.error(f"[red]Decision {decision_id} not found; outcome not logged.[/red]")
        sys.exit(1)
    try:
        r = requests.post(
            f"{_conport_url()}/api/decisions",
            json={
                "workspace_id": wid,
                "summary": f"[Outcome of {decision_id}] {outcome}",
                "rationale": f"Real-world outcome recorded for decision {decision_id}.",
                "alternatives": [],
            },
            timeout=10,
        )
        r.raise_for_status()
        result = r.json()
        new_id = _created_decision_id(result)
        console.logger.info(
            f"[green]Outcome logged as decision #{new_id} (references {decision_id}).[/green]"
        )
    except requests.RequestException as exc:
        console.logger.error(f"[red]Failed to log outcome: {exc}[/red]")
        sys.exit(1)


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
