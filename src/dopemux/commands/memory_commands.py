"""
Memory Commands
"""

import os
import sys
import subprocess
import time
from pathlib import Path
from subprocess import CalledProcessError
from typing import Optional, Dict, List, Sequence

import click
import yaml
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from ..console import console

@click.group()
def memory():
    """🧠 Memory capture and global rollup operations."""
    pass


@memory.group()
def rollup():
    """📊 Global rollup index operations."""
    pass


@rollup.command()
@click.option(
    "--projects-file",
    type=click.Path(exists=True, path_type=Path),
    help="File containing list of project roots (newline or JSON)",
)
@click.option(
    "--index-path",
    type=click.Path(path_type=Path),
    help="Global index path (default: ~/.dopemux/global_index.sqlite)",
)
def build(projects_file: Optional[Path], index_path: Optional[Path]):
    """Build global rollup index from project ledgers (read-only)."""
    from dopemux.memory.global_rollup import (
        GlobalRollupIndexer,
        resolve_rollup_projects,
        GlobalRollupError,
    )

    try:
        roots = resolve_rollup_projects(projects_file=projects_file)
        console.logger.info(f"[cyan]Resolved {len(roots)} project(s)[/cyan]")

        indexer = GlobalRollupIndexer(index_path=index_path)
        result = indexer.build(roots)

        console.logger.info(f"[green]✓[/green] Projects registered: {result['projects_registered']}")
        console.logger.info(f"[green]✓[/green] Pointers indexed: {result['pointers_upserted']}")
        console.logger.info(f"[green]✓[/green] Index: {result['index_path']}")

    except GlobalRollupError as e:
        console.logger.error(f"[red]✗ Rollup error:[/red] {e}")
        raise click.Abort()


@rollup.command()
@click.option(
    "--index-path",
    type=click.Path(path_type=Path),
    help="Global index path (default: ~/.dopemux/global_index.sqlite)",
)
def list(index_path: Optional[Path]):
    """List registered projects in global rollup index."""
    from dopemux.memory.global_rollup import GlobalRollupIndexer
    from rich.table import Table

    indexer = GlobalRollupIndexer(index_path=index_path)

    projects = indexer.list_projects()

    if not projects:
        console.logger.info("[yellow]No projects registered in global index[/yellow]")
        return

    table = Table(title="Registered Projects")
    table.add_column("Project ID", style="cyan")
    table.add_column("Repo Root", style="green")
    table.add_column("Last Seen", style="yellow")

    for proj in projects:
        table.add_row(
            proj["project_id"],
            proj["repo_root"],
            proj["last_seen_at"],
        )

    console.logger.info(table)


@rollup.command()
@click.argument("query")
@click.option(
    "--limit",
    type=int,
    default=10,
    help="Max results (default: 10, max: 100)",
)
@click.option(
    "--index-path",
    type=click.Path(path_type=Path),
    help="Global index path (default: ~/.dopemux/global_index.sqlite)",
)
def search(query: str, limit: int, index_path: Optional[Path]):
    """Search global rollup index for promoted work log entries."""
    from dopemux.memory.global_rollup import GlobalRollupIndexer
    from rich.table import Table

    indexer = GlobalRollupIndexer(index_path=index_path)

    results = indexer.search(query, limit=limit)

    if not results:
        console.logger.info(f"[yellow]No results for: {query}[/yellow]")
        return

    table = Table(title=f"Search Results: {query}")
    table.add_column("Timestamp", style="cyan")
    table.add_column("Type", style="yellow")
    table.add_column("Summary", style="green")
    table.add_column("Project", style="blue", overflow="fold")

    for row in results:
        table.add_row(
            row["ts_utc"],
            row["event_type"],
            row["summary"][:80] + ("..." if len(row["summary"]) > 80 else ""),
            row["project_id"][-40:],  # Last 40 chars of path
        )

    console.logger.info(table)
    console.logger.info(f"\n[dim]Showing {len(results)} of up to {limit} results[/dim]")


@memory.group()
def capture():
    """📥 Capture CLI tool events (Copilot, Codex, etc.)"""
    pass


@capture.command()
@click.option(
    "--event",
    type=str,
    required=True,
    help="Event JSON string (required)",
)
@click.option(
    "--mode",
    type=click.Choice(["plugin", "cli", "mcp", "auto"]),
    default="auto",
    help="Capture mode (default: auto)",
)
@click.option(
    "--quiet",
    is_flag=True,
    help="Suppress output (for hook usage)",
)
@click.option(
    "--repo-root",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Project repository root (default: auto-detect)",
)
@click.option(
    "--lane",
    type=str,
    default=None,
    help="Lane identifier for policy enforcement (e.g., agent:primary)",
)
def emit(event: str, mode: str, quiet: bool, repo_root: Optional[Path], lane: Optional[str]):
    """
    Emit a capture event to Chronicle.

    Writes event to per-project Chronicle ledger with content-addressed
    deduplication. Designed for hook and adapter usage.

    Examples:

        dopemux memory capture emit --event '{"event_type":"file.written","payload":{"path":"src/app.py"}}'

        dopemux memory capture emit --mode plugin --quiet --event '{"event_type":"task.completed","payload":{"task":"T-001"}}'
    """
    from dopemux.memory.capture_client import emit_capture_event, CaptureError
    import json

    try:
        # Parse event JSON
        try:
            event_data = json.loads(event)
        except json.JSONDecodeError as e:
            if not quiet:
                console.logger.error(f"[red]✗ Invalid JSON:[/red] {e}")
            raise click.Abort()

        # Validate event structure
        if not isinstance(event_data, dict):
            if not quiet:
                console.logger.error("[red]✗ Event must be a JSON object[/red]")
            raise click.Abort()

        if "event_type" not in event_data:
            if not quiet:
                console.logger.error("[red]✗ Event must have 'event_type' field[/red]")
            raise click.Abort()

        # Emit to Chronicle
        result = emit_capture_event(
            event_data,
            mode=mode,
            repo_root=repo_root,
            emit_event_bus=False,  # Don't emit to event bus for manual captures
            lane=lane,
        )

        # Output result
        if not quiet:
            if result.inserted:
                console.logger.info(f"[green]✓[/green] Event captured: {result.event_id[:16]}...")
                console.logger.info(f"  Event type: {event_data.get('event_type')}")
                console.logger.info(f"  Mode: {mode}")
            else:
                console.logger.info(f"[yellow]✓[/yellow] Event already exists (deduplicated): {result.event_id[:16]}...")

        # Exit code 0 on success
        sys.exit(0)

    except CaptureError as e:
        if not quiet:
            console.logger.error(f"[red]✗ Capture error:[/red] {e}")
        sys.exit(1)
    except Exception as e:
        if not quiet:
            console.logger.error(f"[red]✗ Unexpected error:[/red] {e}")
        sys.exit(1)


@capture.command()
@click.argument("session_id")
@click.option(
    "--since",
    type=str,
    default=None,
    help="Only ingest events after this ISO timestamp",
)
@click.option(
    "--repo-root",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Project repository root (default: auto-detect)",
)
def copilot(session_id: str, since: Optional[str], repo_root: Optional[Path]):
    """
    Ingest Copilot CLI session transcript into Chronicle.

    Parses JSONL events from ~/.copilot/session-state/{SESSION_ID}/events.jsonl
    and emits to Chronicle via content-addressed deduplication.

    Examples:

        dopemux memory capture copilot 550e8400-e29b-41d4-a716-446655440000

        dopemux memory capture copilot SESSION_ID --since 2025-02-12T10:30:00Z

        dopemux memory capture copilot SESSION_ID --repo-root /path/to/project
    """
    from dopemux.memory.adapters import CopilotCaptureAdapter
    from datetime import datetime

    try:
        # Parse since timestamp if provided
        since_dt = None
        if since:
            try:
                since_dt = datetime.fromisoformat(since.rstrip("Z"))
            except ValueError as e:
                console.logger.error(f"[red]✗ Invalid timestamp format:[/red] {e}")
                console.logger.info("[dim]Expected ISO 8601 format: 2025-02-12T10:30:00Z[/dim]")
                raise click.Abort()

        # Initialize adapter
        adapter = CopilotCaptureAdapter(repo_root=repo_root)

        # Ingest session
        console.logger.info(f"[cyan]📥 Ingesting Copilot session: {session_id}[/cyan]")
        if since:
            console.logger.info(f"[dim]Filtering events after: {since}[/dim]")

        stats = adapter.ingest_session(session_id, since=since_dt)

        # Display results
        console.logger.info(f"\n[green]✓[/green] Ingestion complete:")
        console.logger.info(f"  Total events parsed: {stats['total']}")
        console.logger.info(f"  Successfully inserted: {stats['inserted']}")
        console.logger.info(f"  Deduplicated (already exist): {stats['deduplicated']}")
        console.logger.info(f"  Skipped (unmapped types): {stats['skipped']}")

        if stats["inserted"] == 0 and stats["total"] > 0:
            console.logger.info("\n[yellow]💡 All events already ingested (idempotent)[/yellow]")

    except FileNotFoundError as e:
        console.logger.error(f"[red]✗ Session not found:[/red] {e}")
        console.logger.info("[dim]Use 'dopemux memory capture copilot-list' to see available sessions[/dim]")
        raise click.Abort()
    except Exception as e:
        console.logger.error(f"[red]✗ Ingestion failed:[/red] {e}")
        raise click.Abort()


@capture.command("copilot-list")
@click.option(
    "--limit",
    type=int,
    default=20,
    help="Max sessions to display (default: 20)",
)
def copilot_list(limit: int):
    """
    List available Copilot CLI sessions.

    Shows sessions from ~/.copilot/session-state/ with event counts and timestamps.

    Examples:

        dopemux memory capture copilot-list

        dopemux memory capture copilot-list --limit 50
    """
    from dopemux.memory.adapters import CopilotCaptureAdapter
    from rich.table import Table

    adapter = CopilotCaptureAdapter()
    sessions = adapter.list_sessions()

    if not sessions:
        console.logger.info("[yellow]No Copilot sessions found in ~/.copilot/session-state/[/yellow]")
        return

    # Limit results
    display_sessions = sessions[:limit]

    table = Table(title=f"Available Copilot Sessions (showing {len(display_sessions)} of {len(sessions)})")
    table.add_column("Session ID", style="cyan", width=36)
    table.add_column("Events", style="green", justify="right")
    table.add_column("Started", style="yellow")

    for session in display_sessions:
        table.add_row(
            session["session_id"],
            str(session["event_count"]),
            session.get("start_timestamp") or "unknown",
        )

    console.logger.info(table)

    if len(sessions) > limit:
        console.logger.info(f"\n[dim]💡 Showing {limit} of {len(sessions)} sessions. Use --limit to see more.[/dim]")


# ============================================================================
# 🚀 EASY LAUNCH SHORTCUTS - Quick commands for common workflows
# ============================================================================
