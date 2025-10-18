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


# ============================================================================
# QUICK WIN B1: Decision Show Command (~1 hour)
# ============================================================================

async def get_decision_by_id(
    conn: asyncpg.Connection,
    workspace_id: str,
    decision_id: str
) -> Optional[dict]:
    """Fetch a single decision with full details."""

    query = """
    SELECT
        id,
        summary,
        rationale,
        decision_type,
        confidence_level,
        tags,
        created_at,
        updated_at
    FROM decisions
    WHERE workspace_id = $1
    AND CAST(id AS TEXT) LIKE $2 || '%'
    LIMIT 1
    """

    try:
        row = await conn.fetchrow(query, workspace_id, decision_id)
        return dict(row) if row else None
    except Exception as e:
        console.print(f"[red]❌ Query error: {e}[/red]")
        return None


@click.command("show")
@click.argument("decision_id")
@click.option("--workspace", "-w", help="Workspace path (default: current git root)")
def show_decision(decision_id: str, workspace: Optional[str]):
    """
    🔍 Show detailed decision information

    Quick Win B1: Detailed view of a single decision with full rationale,
    tags, timestamps, and metadata.

    \b
    Examples:
        dopemux decisions show c4b0b       # Partial ID match
        dopemux decisions show a6f86-...   # Full UUID
    """

    async def _show():
        workspace_id = workspace or get_workspace_id()

        conn = await get_conport_connection()
        if not conn:
            return

        try:
            decision = await get_decision_by_id(conn, workspace_id, decision_id)

            if not decision:
                console.print(f"\n[yellow]❌ Decision not found: {decision_id}[/yellow]")
                console.print("[dim]Tip: Use partial ID (first 5 chars) or full UUID[/dim]")
                return

            # Display decision in rich panel
            content = []
            content.append(f"[bold cyan]Summary:[/bold cyan]")
            content.append(f"{decision['summary']}\n")

            content.append(f"[bold cyan]Rationale:[/bold cyan]")
            content.append(f"{decision['rationale']}\n")

            content.append(f"[bold cyan]Metadata:[/bold cyan]")
            content.append(f"  Type: [yellow]{decision['decision_type']}[/yellow]")
            content.append(f"  Confidence: [yellow]{decision['confidence_level']}[/yellow]")
            content.append(f"  Created: [dim]{decision['created_at'].strftime('%Y-%m-%d %I:%M%p')}[/dim]")

            age_days = (datetime.now(decision['created_at'].tzinfo) - decision['created_at']).days
            content.append(f"  Age: [dim]{age_days} days[/dim]")

            if decision['tags']:
                tags_str = ", ".join(decision['tags'])
                content.append(f"  Tags: [cyan]{tags_str}[/cyan]")

            console.print(Panel(
                "\n".join(content),
                title=f"[bold]Decision {str(decision['id'])[:8]}[/bold]",
                border_style="cyan"
            ))

            # Future enhancements placeholder
            console.print("\n[dim]📊 Coming in Phase 1:[/dim]")
            console.print("[dim]  • Alternatives considered[/dim]")
            console.print("[dim]  • Success criteria[/dim]")
            console.print("[dim]  • Outcome status[/dim]")
            console.print("[dim]  • Related decisions (genealogy)[/dim]")

        finally:
            await conn.close()

    asyncio.run(_show())


# ============================================================================
# QUICK WIN B2: Decision List Command (~1.5 hours)
# ============================================================================

@click.command("list")
@click.option("--limit", "-n", default=20, help="Number of decisions to show (default: 20)")
@click.option("--type", "-t", help="Filter by decision type")
@click.option("--tag", help="Filter by tag")
@click.option("--workspace", "-w", help="Workspace path (default: current git root)")
def list_decisions(limit: int, type: Optional[str], tag: Optional[str], workspace: Optional[str]):
    """
    📋 List recent decisions with filtering

    Quick Win B2: Searchable decision list with type and tag filtering.

    \b
    Examples:
        dopemux decisions list                    # 20 most recent
        dopemux decisions list -n 50              # 50 most recent
        dopemux decisions list --type technical   # Technical decisions only
        dopemux decisions list --tag adhd         # ADHD-related decisions
    """

    async def _list():
        workspace_id = workspace or get_workspace_id()

        conn = await get_conport_connection()
        if not conn:
            return

        try:
            # Build query with optional filters
            query = """
            SELECT
                id,
                summary,
                decision_type,
                tags,
                created_at,
                EXTRACT(DAY FROM (NOW() - created_at)) as age_days
            FROM decisions
            WHERE workspace_id = $1
            """

            params = [workspace_id]
            param_count = 1

            if type:
                param_count += 1
                query += f" AND decision_type = ${param_count}"
                params.append(type)

            if tag:
                param_count += 1
                query += f" AND ${param_count} = ANY(tags)"
                params.append(tag)

            query += f" ORDER BY created_at DESC LIMIT {limit}"

            rows = await conn.fetch(query, *params)

            if not rows:
                console.print(f"\n[yellow]No decisions found.[/yellow]")
                if type or tag:
                    console.print("[dim]Try removing filters[/dim]")
                return

            # Display table
            title_parts = [f"📋 Recent Decisions ({len(rows)})"]
            if type:
                title_parts.append(f"Type: {type}")
            if tag:
                title_parts.append(f"Tag: {tag}")

            table = Table(title=" | ".join(title_parts), show_header=True)
            table.add_column("ID", style="cyan", width=8)
            table.add_column("Age", style="dim", width=8)
            table.add_column("Type", style="yellow", width=15)
            table.add_column("Summary", style="white")

            for row in rows:
                decision_id = str(row['id'])[:8]
                age_days = int(row['age_days'])
                age_str = f"{age_days}d ago"
                dec_type = row['decision_type']
                summary = row['summary'][:60] + "..." if len(row['summary']) > 60 else row['summary']

                table.add_row(decision_id, age_str, dec_type, summary)

            console.print(table)

            console.print(f"\n[dim]Tip: Use 'dopemux decisions show <ID>' for full details[/dim]")

        finally:
            await conn.close()

    asyncio.run(_list())


# ============================================================================
# QUICK WIN B3: Energy Analytics Command (~1 hour)
# ============================================================================

@click.command("analytics")
@click.option("--days", "-d", default=30, help="Days to analyze (default: 30)")
@click.option("--workspace", "-w", help="Workspace path (default: current git root)")
def energy_analytics(days: int, workspace: Optional[str]):
    """
    📊 Analyze energy patterns and correlations

    Quick Win B3: Simple energy pattern analysis showing:
    - Energy level distribution
    - Time-of-day patterns
    - Most productive times

    Foundation for Phase 4 decision-energy correlation.

    \b
    Examples:
        dopemux decisions energy analytics         # Last 30 days
        dopemux decisions energy analytics -d 90   # Last 90 days
    """

    async def _analytics():
        workspace_id = workspace or get_workspace_id()

        conn = await get_conport_connection()
        if not conn:
            return

        try:
            # Query all energy logs
            rows = await conn.fetch("""
                SELECT value, created_at
                FROM custom_data
                WHERE workspace_id = $1
                AND category = 'adhd_energy'
                AND created_at > NOW() - INTERVAL '1 day' * $2
                ORDER BY created_at ASC
            """, workspace_id, days)

            if len(rows) < 3:
                console.print(f"\n[yellow]Need at least 3 energy logs for pattern analysis.[/yellow]")
                console.print(f"[dim]Found: {len(rows)} entries[/dim]")
                console.print(f"[dim]Log more with: dopemux decisions energy log [low|medium|high][/dim]")
                return

            import json

            # Parse energy data
            energy_data = []
            for row in rows:
                value = row['value']
                if isinstance(value, str):
                    value = json.loads(value)
                energy_data.append({
                    "level": value.get('energy_level'),
                    "timestamp": row['created_at'],
                    "hour": row['created_at'].hour
                })

            # Calculate statistics
            total = len(energy_data)
            low_count = sum(1 for e in energy_data if e['level'] == 'low')
            medium_count = sum(1 for e in energy_data if e['level'] == 'medium')
            high_count = sum(1 for e in energy_data if e['level'] == 'high')

            # Time-of-day analysis
            hour_counts = {}
            for entry in energy_data:
                hour = entry['hour']
                if hour not in hour_counts:
                    hour_counts[hour] = {'low': 0, 'medium': 0, 'high': 0}
                hour_counts[hour][entry['level']] += 1

            # Find peak hours
            high_hours = [(h, counts['high']) for h, counts in hour_counts.items() if counts['high'] > 0]
            high_hours.sort(key=lambda x: x[1], reverse=True)

            # Display analytics
            console.print(Panel.fit(
                f"[bold cyan]⚡ Energy Analytics[/bold cyan]\n"
                f"Period: Last {days} days | Entries: {total}",
                border_style="cyan"
            ))

            # Distribution
            console.print("\n[bold]📊 Energy Distribution:[/bold]")
            console.print(f"  🔥 High:   {high_count:2d} ({high_count/total*100:.0f}%) {'█' * int(high_count/total*20)}")
            console.print(f"  ⚡ Medium: {medium_count:2d} ({medium_count/total*100:.0f}%) {'█' * int(medium_count/total*20)}")
            console.print(f"  🔋 Low:    {low_count:2d} ({low_count/total*100:.0f}%) {'█' * int(low_count/total*20)}")

            # Time patterns
            if high_hours:
                console.print("\n[bold]🌟 Peak Energy Times:[/bold]")
                for hour, count in high_hours[:3]:
                    time_str = f"{hour:02d}:00" if hour < 12 else f"{hour:02d}:00"
                    period = "AM" if hour < 12 else "PM"
                    display_hour = hour if hour <= 12 else hour - 12
                    console.print(f"  • {display_hour:2d}:00 {period} - {count} high energy entries")

            # ADHD recommendations
            console.print("\n[bold]💡 ADHD Recommendations:[/bold]")

            if high_count > 0:
                console.print(f"  ✅ Schedule complex decisions during high-energy times")
            else:
                console.print(f"  ⚠️  No high-energy entries - may need more data or energy management")

            if low_count > medium_count + high_count:
                console.print(f"  ⚠️  Lots of low-energy entries - consider breaks, sleep, exercise")

            console.print("\n[dim]📈 Phase 4 will add:[/dim]")
            console.print("[dim]  • Decision quality correlation with energy[/dim]")
            console.print("[dim]  • Predictive energy modeling[/dim]")
            console.print("[dim]  • Optimal scheduling recommendations[/dim]")

        finally:
            await conn.close()

    asyncio.run(_analytics())
