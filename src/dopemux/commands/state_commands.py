"""
State Commands

`dopemux save` (currently exposed as `backup`) and `dopemux restore`
for session context snapshotting. The ContextManager persists the
active cockpit state to disk and reconstructs it on demand.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

import click

from ..adhd import ContextManager
from ..console import console
from ..ui.progress import branded_progress
from ..ui.theme import Glyphs, styled_table

logger = logging.getLogger(__name__)


@click.command("save")
@click.option("--message", "-m", help="💾 Context Note: Add a descriptive label to the archive.")
@click.option("--force", "-f", is_flag=True, help="⚡ Force Extraction: Overwrite existing temporal coordinates.")
@click.pass_context
def save(ctx, message: Optional[str], force: bool):
    """
    💾 Archive Context: Save current development mental model

    Captures the active state of the flight-deck, including open artifacts,
    cursor coordinates, and cognitive decisions. Stores this snapshot in
    the ritual ledger for future temporal restoration.
    """
    project_path = Path.cwd()

    if not (project_path / ".dopemux").exists():
        console.logger.info(
            "[error]No Dopemux project found in current directory[/error]"
        )
        sys.exit(1)

    with branded_progress(console=console) as progress:
        task = progress.add_task("Saving context...", total=None)

        context_manager = ContextManager(project_path)
        session_id = context_manager.save_context(message=message, force=force)

        progress.update(task, description="Context saved!", completed=True)

    console.logger.info(
        f"[success]✅ Context saved (session: {session_id[:8]})[/success]"
    )
    if message:
        console.logger.info(f"[text.dim]Note: {message}[/text.dim]")


@click.command("restore")
@click.option("--session", "-s", help="🧪 Temporal Coordinate: Specific session ID to restore.")
@click.option(
    "--list", "-l", "list_sessions", is_flag=True, help="📋 Catalog Archives: List all available saved sessions."
)
@click.pass_context
def restore(ctx, session: Optional[str], list_sessions: bool):
    """
    🔄 Temporal Restoration: Reconstruct past development mental model

    Restores files, cursor coordinates, and cognitive state from a previously
    archived session, synchronizing the cockpit with past coordinates.
    """
    project_path = Path.cwd()

    if not (project_path / ".dopemux").exists():
        console.logger.info(
            "[error]No Dopemux project found in current directory[/error]"
        )
        sys.exit(1)

    context_manager = ContextManager(project_path)

    if list_sessions:
        sessions = context_manager.list_sessions()
        if not sessions:
            console.logger.info("[warning]No saved sessions found[/warning]")
            return

        table = styled_table(
            "Available Sessions",
            ("ID", {"style": "mint"}),
            ("Timestamp", {"style": "mint.soft"}),
            ("Goal", {"style": "gold"}),
            ("Files", {"justify": "right", "style": "violet"}),
        )

        for s in sessions:
            table.add_row(
                s["id"],
                s["timestamp"],
                s.get("current_goal", "No goal set")[:50],
                str(len(s.get("open_files", []))),
            )

        console.logger.info(table)
        for s in sessions:
            console.logger.info(
                f"- {s['id']} :: {s.get('current_goal', 'No goal set')}"
            )
        return

    with branded_progress(console=console) as progress:
        task = progress.add_task("Restoring context...", total=None)

        if session:
            context = context_manager.restore_session(session)
        else:
            context = context_manager.restore_latest()

        progress.update(task, description="Context restored!", completed=True)

    if context:
        console.print(
            f"[success]{Glyphs.SUCCESS} Restored session from {context.get('timestamp', 'unknown')}[/success]"
        )
        console.print(
            f"[info]🎯 Goal: {context.get('current_goal', 'No goal set')}[/info]"
        )
        console.print(
            f"[text.dim]📁 Files: {len(context.get('open_files', []))} files restored[/text.dim]"
        )
    else:
        console.logger.info(f"[error]{Glyphs.ERROR} No context found to restore[/error]")
