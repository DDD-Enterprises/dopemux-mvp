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
from dopemux.ui.progress import branded_progress
from dopemux.ui.progress import branded_progress
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..console import console
from ..ui.theme import styled_panel, styled_table, error_panel, Glyphs, StatusChip

@click.group()
def memory():
    """
    🧠 Cognitive Core: Memory capture and global DAEMON rollup operations

    Orchestrates the persistent memory systems of the DØPEMÜX cockpit. 
    This system synchronizes per-project ledgers into a global rollup index, 
    enabling cross-workspace semantic search and high-fidelity telemetry 
    harvesting from ritual toolsets.
    """
    pass


@memory.group()
def rollup():
    """
    📊 Global Synthesis: Sync and query global daemon rollup index

    Manages the centralized synchronization of distributed project ledgers. 
    The rollup subsystem aggregates work-log entries and telemetry signals 
    into a unified SQLite index for global HUD visibility.
    """
    pass


@rollup.command()
@click.option(
    "--projects-file",
    type=click.Path(exists=True, path_type=Path),
    help="🔬 Manifest Coordinate: Path to the ritual projects manifest (newline-separated or JSON).",
)
@click.option(
    "--index-path",
    type=click.Path(path_type=Path),
    help="📜 Index Anchor: Override the default global SQLite index path (~/.dopemux/global_index.sqlite).",
)
def build(projects_file: Optional[Path], index_path: Optional[Path]):
    """
    ⚙️ Synchronize Ledgers: Build global rollup index from project state

    Performs a deep-tissue synchronization ritual, aggregating individual 
    project ledgers into the global DAEMON rollup index.
    """
    from dopemux.memory.global_rollup import (
        GlobalRollupIndexer,
        resolve_rollup_projects,
        GlobalRollupError,
    )

    try:
        roots = resolve_rollup_projects(projects_file=projects_file)
        console.logger.info(f"[info]Resolved {len(roots)} project(s)[/info]")

        indexer = GlobalRollupIndexer(index_path=index_path)
        result = indexer.build(roots)

        console.logger.info(f"[success]✓[/success] Projects registered: {result['projects_registered']}")
        console.logger.info(f"[success]✓[/success] Pointers indexed: {result['pointers_upserted']}")
        console.logger.info(f"[success]✓[/success] Index: {result['index_path']}")

    except GlobalRollupError as e:
        console.logger.error(f"[error]✗ Rollup error:[/error] {e}")
        raise click.Abort()


@rollup.command()
@click.option(
    "--index-path",
    type=click.Path(path_type=Path),
    help="📜 Index Anchor: Override the default global SQLite index path (~/.dopemux/global_index.sqlite).",
)
def list(index_path: Optional[Path]):
    """
    📋 Catalog Workspaces: List all active projects in the global rollup

    Displays the full index of registered project ledgers, detailing 
    their absolute repository coordinates and last-seen telemetry.
    """
    from dopemux.memory.global_rollup import GlobalRollupIndexer

    indexer = GlobalRollupIndexer(index_path=index_path)

    projects = indexer.list_projects()

    if not projects:
        console.logger.info("[warning]No projects registered in global index[/warning]")
        return

    table = styled_table(
        "Registered Projects",
        ("Project ID", {"style": "info"}),
        ("Repo Root", {"style": "success"}),
        ("Last Seen", {"style": "warning"}),
    )

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
    help="📊 Telemetry Limit: Maximum ritual results to render in the HUD (default: 10).",
)
@click.option(
    "--index-path",
    type=click.Path(path_type=Path),
    help="📜 Index Anchor: Override the default global SQLite index path (~/.dopemux/global_index.sqlite).",
)
def search(query: str, limit: int, index_path: Optional[Path]):
    """
    🔍 Semantic Search: Query global rollup for promoted work log entries

    Performs a cross-workspace search ritual across all synchronized 
    project ledgers to retrieve high-fidelity work-log telemetry.
    """
    from dopemux.memory.global_rollup import GlobalRollupIndexer

    indexer = GlobalRollupIndexer(index_path=index_path)

    results = indexer.search(query, limit=limit)

    if not results:
        console.logger.info(f"[warning]No results for: {query}[/warning]")
        return

    table = styled_table(
        f"Search Results: {query}",
        ("Timestamp", {"style": "info"}),
        ("Type", {"style": "warning"}),
        ("Summary", {"style": "success"}),
        ("Project", {"style": "info", "overflow": "fold"}),
    )

    for row in results:
        table.add_row(
            row["ts_utc"],
            row["event_type"],
            row["summary"][:80] + ("..." if len(row["summary"]) > 80 else ""),
            row["project_id"][-40:],  # Last 40 chars of path
        )

    console.logger.info(table)
    console.logger.info(f"\n[text.dim]Showing {len(results)} of up to {limit} results[/text.dim]")


@memory.group()
def capture():
    """
    📥 Telemetry Ingestion: Capture ritual tool signals (Copilot, Codex, etc.)

    Engages the ingestion adapters for external ritual tools. This subsystem 
    captures raw telemetry signals and converts them into content-addressed 
    events for storage in the per-project Chronicle ledger.
    """
    pass


@capture.command()
@click.option(
    "--event",
    type=str,
    required=True,
    help="📊 Signal Payload: Event JSON string for ingestion.",
)
@click.option(
    "--mode",
    type=click.Choice(["plugin", "cli", "mcp", "auto"]),
    default="auto",
    help="🧪 Capture Aesthetic: Mode for signal ingestion (default: auto).",
)
@click.option(
    "--quiet",
    is_flag=True,
    help="🔇 Silence HUD: Suppress telemetry output during the ritual.",
)
@click.option(
    "--repo-root",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="🔬 Repository Coordinate: Project root for ledger synchronization.",
)
@click.option(
    "--lane",
    type=str,
    default=None,
    help="🛣️  Ritual Lane: Identifier for policy enforcement (e.g., agent:primary).",
)
def emit(event: str, mode: str, quiet: bool, repo_root: Optional[Path], lane: Optional[str]):
    """
    ⚡ Pulse Chronicle: Emit a capture event to the project ledger

    Writes a single telemetry signal to the per-project Chronicle ledger 
    using deterministic, content-addressed deduplication.
    """
    from dopemux.memory.capture_client import emit_capture_event, CaptureError
    import json

    try:
        # Parse event JSON
        try:
            event_data = json.loads(event)
        except json.JSONDecodeError as e:
            if not quiet:
                console.logger.error(f"[error]✗ Invalid JSON:[/error] {e}")
            raise click.Abort()

        # Validate event structure
        if not isinstance(event_data, dict):
            if not quiet:
                console.logger.error("[error]✗ Event must be a JSON object[/error]")
            raise click.Abort()

        if "event_type" not in event_data:
            if not quiet:
                console.logger.error("[error]✗ Event must have 'event_type' field[/error]")
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
                console.logger.info(f"[success]✓[/success] Event captured: {result.event_id[:16]}...")
                console.logger.info(f"  Event type: {event_data.get('event_type')}")
                console.logger.info(f"  Mode: {mode}")
            else:
                console.logger.info(f"[warning]✓[/warning] Event already exists (deduplicated): {result.event_id[:16]}...")

        # Exit code 0 on success
        sys.exit(0)

    except CaptureError as e:
        if not quiet:
            console.logger.error(f"[error]✗ Capture error:[/error] {e}")
        sys.exit(1)
    except Exception as e:
        if not quiet:
            console.logger.error(f"[error]✗ Unexpected error:[/error] {e}")
        sys.exit(1)


@capture.command()
@click.argument("session_id")
@click.option(
    "--since",
    type=str,
    default=None,
    help="⏳ Temporal Gate: Only ingest signals after this ISO timestamp.",
)
@click.option(
    "--repo-root",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="🔬 Repository Coordinate: Project root for ledger synchronization.",
)
def copilot(session_id: str, since: Optional[str], repo_root: Optional[Path]):
    """
    🤖 Copilot Synchronization: Ingest CLI session signals into Chronicle

    Synchronizes the Copilot CLI session transcript into the per-project 
    ledger via high-fidelity, content-addressed ingestion.
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
                console.logger.error(f"[error]✗ Invalid timestamp format:[/error] {e}")
                console.logger.info("[text.dim]Expected ISO 8601 format: 2025-02-12T10:30:00Z[/text.dim]")
                raise click.Abort()

        # Initialize adapter
        adapter = CopilotCaptureAdapter(repo_root=repo_root)

        # Ingest session
        console.logger.info(f"[info]📥 Ingesting Copilot session: {session_id}[/info]")
        if since:
            console.logger.info(f"[text.dim]Filtering events after: {since}[/text.dim]")

        stats = adapter.ingest_session(session_id, since=since_dt)

        # Display results
        console.logger.info(f"\n[success]✓[/success] Ingestion complete:")
        console.logger.info(f"  Total events parsed: {stats['total']}")
        console.logger.info(f"  Successfully inserted: {stats['inserted']}")
        console.logger.info(f"  Deduplicated (already exist): {stats['deduplicated']}")
        console.logger.info(f"  Skipped (unmapped types): {stats['skipped']}")

        if stats["inserted"] == 0 and stats["total"] > 0:
            console.logger.info("\n[warning]💡 All events already ingested (idempotent)[/warning]")

    except FileNotFoundError as e:
        console.logger.error(f"[error]✗ Session not found:[/error] {e}")
        console.logger.info("[text.dim]Use 'dopemux memory capture copilot-list' to see available sessions[/text.dim]")
        raise click.Abort()
    except Exception as e:
        console.logger.error(f"[error]✗ Ingestion failed:[/error] {e}")
        raise click.Abort()


@capture.command("copilot-list")
@click.option(
    "--limit",
    type=int,
    default=20,
    help="📊 Session Limit: Maximum session identifiers to display (default: 20).",
)
def copilot_list(limit: int):
    """
    📋 Catalog Sessions: List available Copilot CLI ritual sessions

    Displays the index of identified Copilot ritual sessions from the local 
    file system, including signal counts and temporal coordinates.
    """
    from dopemux.memory.adapters import CopilotCaptureAdapter

    adapter = CopilotCaptureAdapter()
    sessions = adapter.list_sessions()

    if not sessions:
        console.logger.info("[warning]No Copilot sessions found in ~/.copilot/session-state/[/warning]")
        return

    # Limit results
    display_sessions = sessions[:limit]

    table = styled_table(
        f"Available Copilot Sessions (showing {len(display_sessions)} of {len(sessions)})",
        ("Session ID", {"style": "info", "width": 36}),
        ("Events", {"style": "success", "justify": "right"}),
        ("Started", {"style": "warning"}),
    )

    for session in display_sessions:
        table.add_row(
            session["session_id"],
            str(session["event_count"]),
            session.get("start_timestamp") or "unknown",
        )

    console.logger.info(table)

    if len(sessions) > limit:
        console.logger.info(f"\n[text.dim]💡 Showing {limit} of {len(sessions)} sessions. Use --limit to see more.[/text.dim]")


# ============================================================================
# 🚀 EASY LAUNCH SHORTCUTS - Quick commands for common workflows
# ============================================================================
