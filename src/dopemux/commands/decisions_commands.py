#!/usr/bin/env python3
"""
Dopemux Decision Management Commands

Quick Win implementations:
1. Decision review command - Interactive review workflow for overdue decisions
2. Decision stats command - Aggregate statistics with Rich charts
3. Energy logging command - Simple ADHD energy tracking

These commands provide immediate value while laying groundwork for
full ConPort enhancement roadmap (Phase 1-5).
"""

import asyncio
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Tuple

import asyncpg
import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.text import Text

console = Console()


# ============================================================================
# Database Connection Helpers
# ============================================================================

async def get_conport_connection():
    """Get async connection to ConPort PostgreSQL database."""
    database_url = os.getenv(
        "CONPORT_DATABASE_URL",
        "postgresql://dopemux_age:dopemux_age_dev_password@localhost:5455/dopemux_knowledge_graph"
    )
    try:
        conn = await asyncpg.connect(database_url)
        return conn
    except Exception as e:
        console.print(f"[red]❌ Failed to connect to ConPort database: {e}[/red]")
        console.print("[dim]Make sure mcp-conport container is running (docker ps | grep conport)[/dim]")
        console.print(f"[dim]Database: localhost:5455/dopemux_knowledge_graph[/dim]")
        return None


def get_workspace_id() -> str:
    """
    Get current workspace ID matching ConPort format.

    ConPort stores workspace_id as basename (e.g., 'dopemux-mvp'),
    not full path (e.g., '/Users/hue/code/dopemux-mvp').
    """
    try:
        import subprocess
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True
        )
        full_path = result.stdout.strip()
        # Return basename to match ConPort format
        return Path(full_path).name
    except Exception:
        return Path(os.getcwd()).name


# ============================================================================
# QUICK WIN 1: Decision Review Command (~2 hours)
# ============================================================================

async def get_decisions_needing_review(
    conn: asyncpg.Connection,
    workspace_id: str,
    overdue_only: bool = False
) -> List[Tuple]:
    """
    Query decisions that need review.

    Criteria:
    - >30 days old with no outcome status
    - or specifically marked for review
    - or low confidence (<0.6) - when confidence field exists
    """
    # Use parameterized interval
    days_threshold = 90 if overdue_only else 30

    query = """
    SELECT
        id,
        summary,
        created_at,
        tags,
        EXTRACT(DAY FROM (NOW() - created_at)) as age_days
    FROM decisions
    WHERE workspace_id = $1
    AND (
        -- Decisions older than threshold with no review
        (created_at < NOW() - INTERVAL '1 day' * $2)
        OR
        -- Tagged for review (when tags field exists)
        (tags IS NOT NULL AND tags @> ARRAY['needs-review'])
    )
    ORDER BY created_at ASC
    LIMIT 20;
    """

    try:
        rows = await conn.fetch(query, workspace_id, days_threshold)
        return rows
    except Exception as e:
        console.print(f"[yellow]⚠️  Query error (this is expected if ConPort hasn't been enhanced yet): {e}[/yellow]")
        return []


@click.command("review")
@click.option("--overdue", is_flag=True, help="Show only overdue decisions (>90 days)")
@click.option("--interactive", "-i", is_flag=True, help="Interactive review mode")
@click.option("--workspace", "-w", help="Workspace path (default: current git root)")
def review_decisions(overdue: bool, interactive: bool, workspace: Optional[str]):
    """
    🔔 Review decisions pending review

    Quick Win #1: Simple review workflow for decisions older than 30 days.
    Shows decisions needing attention and optionally prompts for updates.

    \b
    Examples:
        dopemux decisions review              # Show all pending reviews
        dopemux decisions review --overdue    # Show only >90 days old
        dopemux decisions review -i           # Interactive mode
    """

    async def _review():
        workspace_id = workspace or get_workspace_id()

        console.print(Panel.fit(
            f"[bold cyan]🔔 Decision Review[/bold cyan]\n"
            f"Workspace: [dim]{workspace_id}[/dim]",
            border_style="cyan"
        ))

        conn = await get_conport_connection()
        if not conn:
            return

        try:
            # Get decisions needing review
            decisions = await get_decisions_needing_review(conn, workspace_id, overdue)

            if not decisions:
                console.print("\n[green]✅ No decisions need review! All caught up.[/green]")
                console.print("[dim]Tip: Decisions are flagged for review after 30 days.[/dim]")
                return

            # Display table
            table = Table(title=f"\n📋 Decisions Pending Review ({len(decisions)})", show_header=True)
            table.add_column("ID", style="cyan", width=6)
            table.add_column("Age", style="yellow", width=8)
            table.add_column("Summary", style="white")
            table.add_column("Tags", style="dim", width=20)

            for decision in decisions:
                decision_id = str(decision['id'])
                age_days = int(decision['age_days'])
                summary = decision['summary'][:60] + "..." if len(decision['summary']) > 60 else decision['summary']
                tags = ", ".join(decision['tags'] or [])[:18] if decision['tags'] else ""

                # Color code by age
                if age_days > 90:
                    age_str = f"[red]{age_days}d[/red]"
                    icon = "⚠️ "
                elif age_days > 60:
                    age_str = f"[yellow]{age_days}d[/yellow]"
                    icon = "⏰ "
                else:
                    age_str = f"{age_days}d"
                    icon = "📅 "

                table.add_row(
                    decision_id,
                    icon + age_str,
                    summary,
                    tags
                )

            console.print(table)

            # Recommendations
            console.print("\n[bold]💡 Review Recommendations:[/bold]")
            console.print("  • Check if implementation is complete")
            console.print("  • Update outcome status (successful/failed/mixed)")
            console.print("  • Add lessons learned")
            console.print("  • Schedule follow-up if needed")

            if interactive:
                console.print("\n[dim]Interactive mode coming in Phase 1 implementation...[/dim]")
                console.print("[dim]For now, use ConPort MCP tools directly via Claude Code[/dim]")

        finally:
            await conn.close()

    asyncio.run(_review())


# ============================================================================
# QUICK WIN 2: Decision Stats Command (~3 hours)
# ============================================================================

async def get_decision_statistics(
    conn: asyncpg.Connection,
    workspace_id: str,
    since_days: int = 30
) -> dict:
    """Gather decision statistics for the workspace."""

    since_date = datetime.now() - timedelta(days=since_days)

    # Total decisions
    total = await conn.fetchval(
        "SELECT COUNT(*) FROM decisions WHERE workspace_id = $1 AND created_at > $2",
        workspace_id, since_date
    )

    # Decisions by tag (top 10)
    tag_counts = await conn.fetch("""
        SELECT unnest(tags) as tag, COUNT(*) as count
        FROM decisions
        WHERE workspace_id = $1 AND created_at > $2 AND tags IS NOT NULL
        GROUP BY tag
        ORDER BY count DESC
        LIMIT 10
    """, workspace_id, since_date)

    # Recent decisions (last 7 days)
    recent = await conn.fetchval(
        "SELECT COUNT(*) FROM decisions WHERE workspace_id = $1 AND created_at > NOW() - INTERVAL '7 days'",
        workspace_id
    )

    return {
        "total": total,
        "since_days": since_days,
        "recent_7d": recent,
        "tag_counts": [(row['tag'], row['count']) for row in tag_counts],
        "workspace_id": workspace_id
    }


@click.command("stats")
@click.option("--since", "-s", default=30, help="Days to look back (default: 30)")
@click.option("--workspace", "-w", help="Workspace path (default: current git root)")
def decision_stats(since: int, workspace: Optional[str]):
    """
    📈 Show decision statistics with charts

    Quick Win #2: Aggregate statistics showing decision patterns,
    tag distribution, and activity over time.

    \b
    Examples:
        dopemux decisions stats              # Last 30 days
        dopemux decisions stats --since 90   # Last 90 days
    """

    async def _stats():
        workspace_id = workspace or get_workspace_id()

        console.print(Panel.fit(
            f"[bold cyan]📈 Decision Statistics[/bold cyan]\n"
            f"Workspace: [dim]{workspace_id}[/dim]",
            border_style="cyan"
        ))

        conn = await get_conport_connection()
        if not conn:
            return

        try:
            stats = await get_decision_statistics(conn, workspace_id, since)

            if stats["total"] == 0:
                console.print(f"\n[yellow]No decisions found in the last {since} days.[/yellow]")
                console.print("[dim]Start logging decisions with ConPort MCP![/dim]")
                return

            # Summary stats
            console.print(f"\n[bold]📊 Summary (Last {since} Days)[/bold]")
            console.print(f"  Total Decisions: [cyan]{stats['total']}[/cyan]")
            console.print(f"  Recent (7d):     [green]{stats['recent_7d']}[/green]")
            console.print(f"  Daily Average:   [dim]{stats['total'] / since:.1f}[/dim]")

            # Tag distribution
            if stats["tag_counts"]:
                console.print(f"\n[bold]🏷️  Top Tags[/bold]")

                table = Table(show_header=True, box=None)
                table.add_column("Tag", style="cyan")
                table.add_column("Count", style="yellow", justify="right")
                table.add_column("Bar", style="blue")

                max_count = max(count for _, count in stats["tag_counts"])

                for tag, count in stats["tag_counts"]:
                    bar_width = int((count / max_count) * 20)
                    bar = "█" * bar_width
                    table.add_row(tag, str(count), bar)

                console.print(table)

            # ADHD Insights placeholder
            console.print(f"\n[bold]🧠 ADHD Insights[/bold]")
            console.print("  [dim]• Pattern detection coming in Phase 3[/dim]")
            console.print("  [dim]• Energy correlation analysis coming in Phase 4[/dim]")
            console.print("  [dim]• Success prediction coming in Phase 3[/dim]")

            console.print(f"\n[dim]Full stats dashboard coming in Phase 2 (Enhanced CLI)[/dim]")

        finally:
            await conn.close()

    asyncio.run(_stats())


# ============================================================================
# QUICK WIN 3: Energy Logging Command (~2 hours)
# ============================================================================

async def log_energy_level(
    conn: asyncpg.Connection,
    workspace_id: str,
    energy_level: str,
    context: Optional[str] = None
):
    """Log current energy level to ConPort (foundation for Phase 4 dashboard)."""
    import json

    # For now, store as custom_data until Phase 1 adds adhd_metrics table
    value_dict = {
        "energy_level": energy_level,
        "context": context,
        "timestamp": datetime.now().isoformat()
    }

    await conn.execute("""
        INSERT INTO custom_data (workspace_id, category, key, value, created_at)
        VALUES ($1, 'adhd_energy', $2, $3::jsonb, NOW())
    """, workspace_id, datetime.now().isoformat(), json.dumps(value_dict))


@click.command("energy")
@click.argument("level", type=click.Choice(["low", "medium", "high"], case_sensitive=False))
@click.option("--context", "-c", help="Optional context note")
@click.option("--workspace", "-w", help="Workspace path (default: current git root)")
def log_energy(level: str, context: Optional[str], workspace: Optional[str]):
    """
    ⚡ Log current energy level

    Quick Win #3: Simple energy tracking for ADHD dashboard foundation.
    Track your energy levels to correlate with decision quality later.

    \b
    Examples:
        dopemux energy high                    # Log high energy
        dopemux energy low -c "after lunch"    # With context
    """

    async def _log():
        workspace_id = workspace or get_workspace_id()

        # Energy emoji mapping
        emojis = {"low": "🔋", "medium": "⚡", "high": "🔥"}
        emoji = emojis.get(level.lower(), "⚡")

        conn = await get_conport_connection()
        if not conn:
            return

        try:
            await log_energy_level(conn, workspace_id, level.lower(), context)

            console.print(f"\n{emoji} [bold]Energy logged:[/bold] [cyan]{level.upper()}[/cyan]")
            if context:
                console.print(f"   Context: [dim]{context}[/dim]")
            console.print(f"   Time: [dim]{datetime.now().strftime('%I:%M %p')}[/dim]")

            console.print("\n[dim]💡 Tip: Log energy regularly to discover your peak productivity times[/dim]")
            console.print("[dim]   Phase 4 will add energy correlation with decision quality[/dim]")

        finally:
            await conn.close()

    asyncio.run(_log())


# ============================================================================
# Energy Status Command (Bonus!)
# ============================================================================

@click.command("status")
@click.option("--days", "-d", default=7, help="Days to show (default: 7)")
@click.option("--workspace", "-w", help="Workspace path (default: current git root)")
def energy_status(days: int, workspace: Optional[str]):
    """
    📊 Show energy level history

    View recent energy logs to understand your patterns.
    """

    async def _status():
        workspace_id = workspace or get_workspace_id()

        conn = await get_conport_connection()
        if not conn:
            return

        try:
            # Query recent energy logs
            rows = await conn.fetch("""
                SELECT key, value, created_at
                FROM custom_data
                WHERE workspace_id = $1
                AND category = 'adhd_energy'
                AND created_at > NOW() - INTERVAL '1 day' * $2
                ORDER BY created_at DESC
                LIMIT 50
            """, workspace_id, days)

            if not rows:
                console.print(f"\n[yellow]No energy logs found in the last {days} days.[/yellow]")
                console.print("[dim]Start logging with: dopemux energy [low|medium|high][/dim]")
                return

            console.print(f"\n[bold]⚡ Energy History (Last {days} Days)[/bold]\n")

            for row in rows:
                import json
                # Parse JSON value if it's a string
                value = row['value']
                if isinstance(value, str):
                    value = json.loads(value)

                energy = value.get('energy_level', 'unknown')
                ctx = value.get('context', '')
                timestamp = row['created_at']

                emoji_map = {"low": "🔋", "medium": "⚡", "high": "🔥"}
                emoji = emoji_map.get(energy, "⚡")

                color_map = {"low": "red", "medium": "yellow", "high": "green"}
                color = color_map.get(energy, "white")

                time_str = timestamp.strftime("%m/%d %I:%M%p")
                console.print(f"{emoji} [{color}]{energy.upper():6}[/{color}]  {time_str}  {ctx}")

            console.print(f"\n[dim]Logged {len(rows)} energy entries[/dim]")

        finally:
            await conn.close()

    asyncio.run(_status())
