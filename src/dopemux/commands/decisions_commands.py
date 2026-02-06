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

import logging

logger = logging.getLogger(__name__)

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
        console.log(f"[red]❌ Failed to connect to ConPort database: {e}[/red]")
        console.log("[dim]Make sure mcp-conport container is running (docker ps | grep conport)[/dim]")
        console.log(f"[dim]Database: localhost:5455/dopemux_knowledge_graph[/dim]")
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
    except Exception as e:
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
        console.log(f"[yellow]⚠️  Query error (this is expected if ConPort hasn't been enhanced yet): {e}[/yellow]")
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
                console.log("\n[green]✅ No decisions need review! All caught up.[/green]")
                console.log("[dim]Tip: Decisions are flagged for review after 30 days.[/dim]")
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

            console.log(table)

            # Recommendations
            console.log("\n[bold]💡 Review Recommendations:[/bold]")
            console.log("  • Check if implementation is complete")
            console.log("  • Update outcome status (successful/failed/mixed)")
            console.log("  • Add lessons learned")
            console.log("  • Schedule follow-up if needed")

            if interactive:
                console.log("\n[dim]Interactive mode coming in Phase 1 implementation...[/dim]")
                console.log("[dim]For now, use ConPort MCP tools directly via Claude Code[/dim]")

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
            since_date = datetime.now() - timedelta(days=since)
            decision_rows = await conn.fetch(
                """
                SELECT created_at, tags, outcome_status, confidence_level, decision_type
                FROM decisions
                WHERE workspace_id = $1 AND created_at > $2
                """,
                workspace_id,
                since_date,
            )
            decisions = [dict(row) for row in decision_rows]

            if stats["total"] == 0:
                console.log(f"\n[yellow]No decisions found in the last {since} days.[/yellow]")
                console.log("[dim]Start logging decisions with ConPort MCP![/dim]")
                return

            # Summary stats
            console.log(f"\n[bold]📊 Summary (Last {since} Days)[/bold]")
            console.log(f"  Total Decisions: [cyan]{stats['total']}[/cyan]")
            console.log(f"  Recent (7d):     [green]{stats['recent_7d']}[/green]")
            console.log(f"  Daily Average:   [dim]{stats['total'] / since:.1f}[/dim]")

            # Tag distribution
            if stats["tag_counts"]:
                console.log(f"\n[bold]🏷️  Top Tags[/bold]")

                table = Table(show_header=True, box=None)
                table.add_column("Tag", style="cyan")
                table.add_column("Count", style="yellow", justify="right")
                table.add_column("Bar", style="blue")

                max_count = max(count for _, count in stats["tag_counts"])

                for tag, count in stats["tag_counts"]:
                    bar_width = int((count / max_count) * 20)
                    bar = "█" * bar_width
                    table.add_row(tag, str(count), bar)

                console.log(table)

            # Enhanced ADHD Insights - analyze decision patterns for ADHD optimization
            console.log(f"\n[bold]🧠 ADHD Decision Insights[/bold]")

            # Success Rate & Quality Analysis
            successful_decisions = sum(1 for d in decisions if d.get('outcome_status') == 'successful')
            failed_decisions = sum(1 for d in decisions if d.get('outcome_status') == 'failed')
            mixed_decisions = sum(1 for d in decisions if d.get('outcome_status') == 'mixed')
            total_with_outcome = successful_decisions + failed_decisions + mixed_decisions

            if total_with_outcome > 0:
                success_rate = (successful_decisions / total_with_outcome) * 100
                console.log(f"  ✅ Success Rate: {success_rate:.1f}% ({successful_decisions}/{total_with_outcome} completed)")

                if failed_decisions > 0:
                    console.log(f"  ⚠️  Failure Rate: {(failed_decisions/total_with_outcome)*100:.1f}% - Consider reviewing decision process")
                if mixed_decisions > 0:
                    console.log(f"  ⚖️  Mixed Outcomes: {(mixed_decisions/total_with_outcome)*100:.1f}% - Partial wins need follow-up")
            else:
                console.log(f"  ⏳ No outcomes tracked yet - start logging decision results!")

            # Decision Velocity & ADHD Task Chunking
            recent_decisions = [d for d in decisions if d['created_at'] > since_date]
            if recent_decisions:
                daily_rate = len(recent_decisions) / since
                console.log(f"  📈 Decision Velocity: {daily_rate:.1f} decisions/day")

                if daily_rate > 3:
                    console.log(f"  ⚡ High velocity! Consider ADHD-friendly breaks every 25 minutes")
                elif daily_rate < 0.5:
                    console.log(f"  🐌 Low velocity - may indicate decision paralysis or overload")

            # Confidence Level Analysis (ADHD decision quality)
            confidence_levels = {}
            for d in decisions:
                conf = d.get('confidence_level', 'unknown')
                confidence_levels[conf] = confidence_levels.get(conf, 0) + 1

            if len(confidence_levels) > 1:
                high_conf = confidence_levels.get('high', 0)
                low_conf = confidence_levels.get('low', 0)
                total_conf = sum(confidence_levels.values())

                if total_conf > 0:
                    console.log(f"  🎯 Confidence Distribution:")
                    console.log(f"     High: {high_conf/total_conf*100:.0f}% | Low: {low_conf/total_conf*100:.0f}%")

                    if low_conf > high_conf:
                        console.log(f"     ⚠️  Many low-confidence decisions - may indicate rushed choices")
                    if high_conf > low_conf * 2:
                        console.log(f"     ✅ Strong confidence pattern - good decision hygiene!")

            # Decision Type Analysis (ADHD executive function support)
            decision_types = {}
            for d in decisions:
                dec_type = d.get('decision_type', 'UNKNOWN')
                decision_types[dec_type] = decision_types.get(dec_type, 0) + 1

            if decision_types:
                most_common = max(decision_types.items(), key=lambda x: x[1])
                diversity = len(decision_types)

                console.log(f"  🏗️  Decision Portfolio: {diversity} types, most common: {most_common[0]} ({most_common[1]}x)")

                if diversity < 3:
                    console.log(f"     ⚠️  Low decision diversity - consider broadening decision scope")
                elif diversity > 5:
                    console.log(f"     🎭 Complex portfolio - may benefit from decision categorization")

            # Time Pressure Analysis (ADHD temporal awareness)
            urgent_decisions = [d for d in decisions if (datetime.now() - d['created_at']).days < 1]
            if urgent_decisions:
                urgent_rate = len(urgent_decisions) / len(decisions) * 100
                console.log(f"  ⏰ Time Pressure: {urgent_rate:.0f}% decisions made same-day")

                if urgent_rate > 50:
                    console.log(f"     🚨 High urgency pattern - consider implementing decision buffers")
                elif urgent_rate < 10:
                    console.log(f"     🧘 Low urgency - good for thoughtful decision-making")

            # Tag Pattern Analysis (ADHD categorization support)
            all_tags = []
            for d in decisions:
                all_tags.extend(d.get('tags', []))

            if all_tags:
                from collections import Counter
                tag_counts = Counter(all_tags)
                unique_tags = len(tag_counts)
                most_used = tag_counts.most_common(1)[0] if tag_counts else ("none", 0)

                console.log(f"  🏷️  Tagging: {unique_tags} unique tags, most used: '{most_used[0]}' ({most_used[1]}x)")

                if unique_tags < 5:
                    console.log(f"     💭 Consider more granular tagging for better organization")
                elif unique_tags > 15:
                    console.log(f"     🗂️  Rich tagging system - excellent for decision retrieval!")

            # ADHD-Specific Recommendations
            console.log(f"\n[bold]💡 ADHD Optimization Recommendations:[/bold]")

            recommendations = []

            # Success rate recommendations
            if total_with_outcome > 0 and success_rate < 60:
                recommendations.append("📈 Decision quality review needed - consider implementing decision checklists")

            # Velocity recommendations
            if recent_decisions and daily_rate > 5:
                recommendations.append("⚡ High decision load - implement 25-minute focus sessions with breaks")

            # Confidence recommendations
            if confidence_levels.get('low', 0) > confidence_levels.get('high', 0):
                recommendations.append("🎯 Build confidence through small wins - start with low-risk decisions")

            # Diversity recommendations
            if len(decision_types) < 3:
                recommendations.append("🎭 Expand decision variety - include technical, process, and strategic decisions")

            # Time pressure recommendations
            if urgent_decisions and len(urgent_decisions) > len(decisions) * 0.7:
                recommendations.append("⏰ Reduce decision urgency - implement decision review buffers")

            if not recommendations:
                recommendations.append("✅ Decision patterns look healthy - keep up the good work!")

            for rec in recommendations[:3]:  # Limit to 3 for ADHD focus
                console.log(f"  • {rec}")

            console.log(f"\n[dim]🧠 Enhanced ADHD insights available in Phase 3 (ML-powered patterns)[/dim]")

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

            console.log(f"\n{emoji} [bold]Energy logged:[/bold] [cyan]{level.upper()}[/cyan]")
            if context:
                console.log(f"   Context: [dim]{context}[/dim]")
            console.log(f"   Time: [dim]{datetime.now().strftime('%I:%M %p')}[/dim]")

            console.log("\n[dim]💡 Tip: Log energy regularly to discover your peak productivity times[/dim]")
            console.log("[dim]   Phase 4 will add energy correlation with decision quality[/dim]")

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
                console.log(f"\n[yellow]No energy logs found in the last {days} days.[/yellow]")
                console.log("[dim]Start logging with: dopemux energy [low|medium|high][/dim]")
                return

            console.log(f"\n[bold]⚡ Energy History (Last {days} Days)[/bold]\n")

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
                console.log(f"{emoji} [{color}]{energy.upper():6}[/{color}]  {time_str}  {ctx}")

            console.log(f"\n[dim]Logged {len(rows)} energy entries[/dim]")

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
        console.log(f"[red]❌ Query error: {e}[/red]")
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
                console.log(f"\n[yellow]❌ Decision not found: {decision_id}[/yellow]")
                console.log("[dim]Tip: Use partial ID (first 5 chars) or full UUID[/dim]")
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
            console.log("\n[dim]📊 Coming in Phase 1:[/dim]")
            console.log("[dim]  • Alternatives considered[/dim]")
            console.log("[dim]  • Success criteria[/dim]")
            console.log("[dim]  • Outcome status[/dim]")
            console.log("[dim]  • Related decisions (genealogy)[/dim]")

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
                console.log(f"\n[yellow]No decisions found.[/yellow]")
                if type or tag:
                    console.log("[dim]Try removing filters[/dim]")
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

            console.log(table)

            console.log(f"\n[dim]Tip: Use 'dopemux decisions show <ID>' for full details[/dim]")

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
                console.log(f"\n[yellow]Need at least 3 energy logs for pattern analysis.[/yellow]")
                console.log(f"[dim]Found: {len(rows)} entries[/dim]")
                console.log(f"[dim]Log more with: dopemux decisions energy log [low|medium|high][/dim]")
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
            console.log("\n[bold]📊 Energy Distribution:[/bold]")
            console.log(f"  🔥 High:   {high_count:2d} ({high_count/total*100:.0f}%) {'█' * int(high_count/total*20)}")
            console.log(f"  ⚡ Medium: {medium_count:2d} ({medium_count/total*100:.0f}%) {'█' * int(medium_count/total*20)}")
            console.log(f"  🔋 Low:    {low_count:2d} ({low_count/total*100:.0f}%) {'█' * int(low_count/total*20)}")

            # Time patterns
            if high_hours:
                console.log("\n[bold]🌟 Peak Energy Times:[/bold]")
                for hour, count in high_hours[:3]:
                    time_str = f"{hour:02d}:00" if hour < 12 else f"{hour:02d}:00"
                    period = "AM" if hour < 12 else "PM"
                    display_hour = hour if hour <= 12 else hour - 12
                    console.log(f"  • {display_hour:2d}:00 {period} - {count} high energy entries")

            # ADHD recommendations
            console.log("\n[bold]💡 ADHD Recommendations:[/bold]")

            if high_count > 0:
                console.log(f"  ✅ Schedule complex decisions during high-energy times")
            else:
                console.log(f"  ⚠️  No high-energy entries - may need more data or energy management")

            if low_count > medium_count + high_count:
                console.log(f"  ⚠️  Lots of low-energy entries - consider breaks, sleep, exercise")

            console.log("\n[dim]📈 Phase 4 will add:[/dim]")
            console.log("[dim]  • Decision quality correlation with energy[/dim]")
            console.log("[dim]  • Predictive energy modeling[/dim]")
            console.log("[dim]  • Optimal scheduling recommendations[/dim]")

        finally:
            await conn.close()

    asyncio.run(_analytics())


# ============================================================================
# PHASE 3: Semantic Search Command (~1.5 hours)
# ============================================================================

@click.command("search")
@click.argument("query")
@click.option("--top-k", "-k", default=5, help="Number of results to return (default: 5)")
@click.option("--type", "-t", help="Filter by item type (decision, progress_entry, system_pattern)")
@click.option("--tag", help="Filter by tag")
@click.option("--workspace", "-w", help="Workspace path")
def semantic_search_cmd(query: str, top_k: int, type: Optional[str], tag: Optional[str], workspace: Optional[str]):
    """
    🔍 Semantic search ConPort knowledge graph

    Phase 3 feature: Discover knowledge by meaning, not keywords.
    Uses vector embeddings to find relevant content through understanding.
    Perfect for exploring complex relationships and ADHD-friendly discovery.

    \b
    Examples:
        dopemux decisions search "ADHD optimization patterns"     # Find related insights
        dopemux decisions search "performance bottlenecks" -k 10  # More results
        dopemux decisions search "genetic agent" --type decision  # Filter by type
        dopemux decisions search "mcp" --tag integration          # Filter by tag
    """

    async def _search():
        from ..tools.conport_client import semantic_search

        workspace_id = workspace or get_workspace_id()

        console.print(Panel.fit(
            f"[bold cyan]🔍 Semantic Search[/bold cyan]\n"
            f"Query: [yellow]{query}[/yellow] | Workspace: [dim]{workspace_id}[/dim]",
            border_style="cyan"
        ))

        try:
            # Prepare filters
            filter_item_types = [type] if type else None
            filter_tags_include_any = [tag] if tag else None

            # Execute semantic search
            result = await semantic_search(
                query=query,
                top_k=top_k,
                workspace_id=workspace_id,
                filter_item_types=filter_item_types,
                filter_tags_include_any=filter_tags_include_any
            )

            if "error" in result:
                console.log(f"\n[red]❌ Search failed: {result['error']}[/red]")
                console.log("[dim]Make sure ConPort server is running (check http://localhost:3004)[/dim]")
                return

            results = result.get("result", [])
            if not results:
                console.log(f"\n[yellow]No results found for: {query}[/yellow]")
                console.log("[dim]Try a different query or check your filters[/dim]")
                return

            # Display results
            console.log(f"\n[bold]🎯 Found {len(results)} semantic matches:[/bold]\n")

            for i, item in enumerate(results, 1):
                # Extract item details
                item_type = item.get("metadata", {}).get("conport_item_type", "unknown")
                item_id = item.get("metadata", {}).get("conport_item_id", "unknown")
                distance = item.get("distance", 0)
                score = 1 - distance  # Convert distance to similarity score

                # Get content preview
                content = item.get("document", {}).get("content", "")
                if len(content) > 150:
                    content = content[:147] + "..."

                # Type-specific icons and colors
                type_config = {
                    "decision": ("🧠", "cyan"),
                    "progress_entry": ("📋", "green"),
                    "system_pattern": ("🔄", "yellow"),
                    "unknown": ("❓", "dim")
                }
                icon, color = type_config.get(item_type, type_config["unknown"])

                console.log(f"[bold {color}]{i}. {icon} {item_type.upper()}[/bold {color}] (ID: {item_id})")
                console.log(f"   [dim]Similarity: {score:.3f}[/dim]")
                console.log(f"   [white]{content}[/white]")
                console.log()

            # ADHD-friendly tips
            console.log("[bold]💡 Semantic Search Tips:[/bold]")
            console.log("  • Uses meaning, not keywords - try natural language")
            console.log("  • Results are ranked by relevance to your intent")
            console.log("  • Filter with --type or --tag for focused results")
            console.log("  • Great for discovering connections you didn't know existed")

        except Exception as e:
            console.log(f"\n[red]❌ Search error: {e}[/red]")
            console.log("[dim]Check ConPort server connectivity[/dim]")

    asyncio.run(_search())


# ============================================================================
# PHASE 2: Decision Graph Visualization (~2 hours)
# ============================================================================

async def get_decision_relationships(
    conn: asyncpg.Connection,
    workspace_id: str,
    decision_id: str,
    max_depth: int = 3
) -> dict:
    """
    Fetch decision genealogy (ancestors and descendants).

    Returns structure with decision details and relationships.
    """
    # First, get the target decision
    target_decision = await get_decision_by_id(conn, workspace_id, decision_id)

    if not target_decision:
        return None

    # Get ancestors (decisions this one builds upon)
    ancestors_query = """
    WITH RECURSIVE ancestry AS (
        -- Base case: start with target decision
        SELECT
            dr.source_decision_id as decision_id,
            dr.relationship_type,
            1 as depth
        FROM ag_catalog.decision_relationships dr
        WHERE dr.target_decision_id = $1

        UNION

        -- Recursive case: find ancestors of ancestors
        SELECT
            dr.source_decision_id,
            dr.relationship_type,
            a.depth + 1
        FROM ag_catalog.decision_relationships dr
        JOIN ancestry a ON dr.target_decision_id = a.decision_id
        WHERE a.depth < $2
    )
    SELECT DISTINCT
        a.decision_id,
        a.relationship_type,
        a.depth,
        d.summary,
        d.decision_type,
        d.created_at
    FROM ancestry a
    JOIN decisions d ON d.id = a.decision_id
    WHERE d.workspace_id = $3
    ORDER BY a.depth, d.created_at
    """

    # Get descendants (decisions that build upon this one)
    descendants_query = """
    WITH RECURSIVE descendants AS (
        -- Base case: start with target decision
        SELECT
            dr.target_decision_id as decision_id,
            dr.relationship_type,
            1 as depth
        FROM ag_catalog.decision_relationships dr
        WHERE dr.source_decision_id = $1

        UNION

        -- Recursive case: find descendants of descendants
        SELECT
            dr.target_decision_id,
            dr.relationship_type,
            d.depth + 1
        FROM ag_catalog.decision_relationships dr
        JOIN descendants d ON dr.source_decision_id = d.decision_id
        WHERE d.depth < $2
    )
    SELECT DISTINCT
        d.decision_id,
        d.relationship_type,
        d.depth,
        dec.summary,
        dec.decision_type,
        dec.created_at
    FROM descendants d
    JOIN decisions dec ON dec.id = d.decision_id
    WHERE dec.workspace_id = $3
    ORDER BY d.depth, dec.created_at
    """

    try:
        ancestors = await conn.fetch(ancestors_query, target_decision['id'], max_depth, workspace_id)
        descendants = await conn.fetch(descendants_query, target_decision['id'], max_depth, workspace_id)

        return {
            "target": target_decision,
            "ancestors": [dict(row) for row in ancestors],
            "descendants": [dict(row) for row in descendants]
        }
    except Exception as e:
        # Graceful fallback if relationships table doesn't exist yet
        console.log(f"[yellow]⚠️  Relationships query failed (tables may be in different schema): {e}[/yellow]")
        return {
            "target": target_decision,
            "ancestors": [],
            "descendants": []
        }


def render_decision_tree(graph_data: dict) -> str:
    """
    Render ASCII decision genealogy tree.

    Format:
                    #140: Parent Decision
                        ↓ builds_upon
              ┌─────→ #143: Sibling A ←─────┐
              │         ↓ extends           │
    #144 ← #145: Target Decision   #146 → implements
              │         (YOU ARE HERE)      │
              └──────────────→ #147: Child
    """
    lines = []
    target = graph_data["target"]
    ancestors = graph_data["ancestors"]
    descendants = graph_data["descendants"]

    # Build tree representation
    if ancestors:
        lines.append("\n[bold]🌳 Decision Genealogy:[/bold]")
        lines.append(f"   Target: #{str(target['id'])[:8]} - {target['summary'][:50]}\n")

        # Show ancestors (what this builds upon)
        lines.append("[dim]Ancestors (builds upon):[/dim]")
        for anc in ancestors[:5]:  # Limit to 5 for ADHD
            indent = "  " * anc['depth']
            rel = anc['relationship_type']
            lines.append(f"{indent}↑ {rel:12} #{str(anc['decision_id'])[:8]} - {anc['summary'][:40]}")

    # Show target decision
    lines.append(f"\n[bold cyan]→ TARGET: #{str(target['id'])[:8]}[/bold cyan]")
    lines.append(f"  {target['summary']}")
    lines.append(f"  [dim]({target['decision_type']}, {target['created_at'].strftime('%Y-%m-%d')})[/dim]")

    # Show descendants (what builds on this)
    if descendants:
        lines.append("\n[dim]Descendants (extend this decision):[/dim]")
        for desc in descendants[:5]:  # Limit to 5 for ADHD
            indent = "  " * desc['depth']
            rel = desc['relationship_type']
            lines.append(f"{indent}↓ {rel:12} #{str(desc['decision_id'])[:8]} - {desc['summary'][:40]}")

    if not ancestors and not descendants:
        lines.append("\n[dim]No related decisions found (orphan decision)[/dim]")
        lines.append("[dim]Link decisions using ConPort MCP: link_conport_items()[/dim]")

    return "\n".join(lines)


@click.command("graph")
@click.argument("decision_id")
@click.option("--depth", "-d", default=3, help="Relationship depth to traverse (default: 3)")
@click.option("--workspace", "-w", help="Workspace path (default: current git root)")
def graph_decision(decision_id: str, depth: int, workspace: Optional[str]):
    """
    🌳 Show decision genealogy graph

    Phase 2 feature: Visualize decision relationships (ancestors/descendants)
    showing how decisions build upon each other.

    \b
    Examples:
        dopemux decisions graph c4b0b        # Show genealogy
        dopemux decisions graph a6f86 -d 5   # Deeper traversal
    """

    async def _graph():
        workspace_id = workspace or get_workspace_id()

        conn = await get_conport_connection()
        if not conn:
            return

        try:
            graph_data = await get_decision_relationships(conn, workspace_id, decision_id, depth)

            if not graph_data:
                console.log(f"\n[yellow]❌ Decision not found: {decision_id}[/yellow]")
                return

            # Render tree
            tree = render_decision_tree(graph_data)

            console.print(Panel(
                tree,
                title=f"[bold]Decision Genealogy (depth={depth})[/bold]",
                border_style="cyan"
            ))

            # Stats
            anc_count = len(graph_data["ancestors"])
            desc_count = len(graph_data["descendants"])

            if anc_count > 0 or desc_count > 0:
                console.log(f"\n[bold]📊 Graph Stats:[/bold]")
                console.log(f"  Ancestors: {anc_count}")
                console.log(f"  Descendants: {desc_count}")
                console.log(f"  Total related: {anc_count + desc_count}")

        finally:
            await conn.close()

    asyncio.run(_graph())


# ============================================================================
# PHASE 2: Interactive Review Mode (~1.5 hours)
# ============================================================================

async def update_decision_outcome(
    conn: asyncpg.Connection,
    decision_id: str,
    outcome_status: str,
    outcome_notes: Optional[str] = None
):
    """Update decision outcome after review."""

    await conn.execute("""
        UPDATE decisions
        SET
            outcome_status = $1,
            outcome_notes = $2,
            outcome_date = NOW(),
            updated_at = NOW()
        WHERE CAST(id AS TEXT) LIKE $3 || '%'
    """, outcome_status, outcome_notes, decision_id)


@click.command("update-outcome")
@click.argument("decision_id")
@click.argument("outcome", type=click.Choice(["successful", "failed", "mixed", "abandoned"]))
@click.option("--notes", "-n", help="Outcome notes/description")
@click.option("--workspace", "-w", help="Workspace path")
def update_outcome(decision_id: str, outcome: str, notes: Optional[str], workspace: Optional[str]):
    """
    ✏️  Update decision outcome after review

    Phase 2 feature: Mark decision as successful/failed/mixed/abandoned
    with optional notes about what actually happened.

    \b
    Examples:
        dopemux decisions update-outcome c4b0b successful
        dopemux decisions update-outcome a6f86 failed -n "Performance issues"
        dopemux decisions update-outcome 960ea mixed -n "Partially implemented"
    """

    async def _update():
        workspace_id = workspace or get_workspace_id()

        conn = await get_conport_connection()
        if not conn:
            return

        try:
            # Verify decision exists first
            decision = await get_decision_by_id(conn, workspace_id, decision_id)

            if not decision:
                console.log(f"\n[yellow]❌ Decision not found: {decision_id}[/yellow]")
                return

            # Update outcome
            await update_decision_outcome(conn, decision_id, outcome, notes)

            # Confirm
            emoji_map = {
                "successful": "✅",
                "failed": "❌",
                "mixed": "⚖️",
                "abandoned": "🚫"
            }
            emoji = emoji_map.get(outcome, "📝")

            console.log(f"\n{emoji} [bold]Outcome updated:[/bold] {outcome.upper()}")
            console.log(f"   Decision: [cyan]{decision['summary'][:60]}[/cyan]")
            if notes:
                console.log(f"   Notes: [dim]{notes}[/dim]")
            console.log(f"   [dim]Updated: {datetime.now().strftime('%Y-%m-%d %I:%M%p')}[/dim]")

        finally:
            await conn.close()

    asyncio.run(_update())


# ============================================================================
# PHASE 2: Enhanced Stats with Confidence Distribution (~1 hour)
# ============================================================================

@click.command("stats-enhanced")
@click.option("--since", "-s", default=30, help="Days to look back (default: 30)")
@click.option("--workspace", "-w", help="Workspace path")
def enhanced_stats(since: int, workspace: Optional[str]):
    """
    📈 Enhanced decision statistics with confidence distribution

    Phase 2 feature: Extended stats showing:
    - Confidence level distribution
    - Outcome status breakdown
    - Decision type distribution
    - Review status summary

    \b
    Examples:
        dopemux decisions stats-enhanced
        dopemux decisions stats-enhanced --since 90
    """

    async def _enhanced():
        workspace_id = workspace or get_workspace_id()

        conn = await get_conport_connection()
        if not conn:
            return

        try:
            since_date = datetime.now() - timedelta(days=since)

            # Get comprehensive stats
            total = await conn.fetchval(
                "SELECT COUNT(*) FROM decisions WHERE workspace_id = $1 AND created_at > $2",
                workspace_id, since_date
            )

            if total == 0:
                console.log(f"\n[yellow]No decisions found in the last {since} days.[/yellow]")
                return

            # Confidence distribution
            confidence_dist = await conn.fetch("""
                SELECT confidence_level, COUNT(*) as count
                FROM decisions
                WHERE workspace_id = $1 AND created_at > $2
                GROUP BY confidence_level
                ORDER BY
                    CASE confidence_level
                        WHEN 'high' THEN 1
                        WHEN 'medium' THEN 2
                        WHEN 'low' THEN 3
                        ELSE 4
                    END
            """, workspace_id, since_date)

            # Outcome distribution
            outcome_dist = await conn.fetch("""
                SELECT outcome_status, COUNT(*) as count
                FROM decisions
                WHERE workspace_id = $1 AND created_at > $2
                GROUP BY outcome_status
            """, workspace_id, since_date)

            # Type distribution
            type_dist = await conn.fetch("""
                SELECT decision_type, COUNT(*) as count
                FROM decisions
                WHERE workspace_id = $1 AND created_at > $2
                GROUP BY decision_type
                ORDER BY count DESC
                LIMIT 5
            """, workspace_id, since_date)

            # Display enhanced stats
            console.print(Panel.fit(
                f"[bold cyan]📈 Enhanced Decision Statistics[/bold cyan]\n"
                f"Period: Last {since} days | Total: {total} decisions",
                border_style="cyan"
            ))

            # Confidence distribution
            if confidence_dist:
                console.log("\n[bold]🎯 Confidence Distribution:[/bold]")
                for row in confidence_dist:
                    level = row['confidence_level'] or 'unset'
                    count = row['count']
                    pct = count / total * 100
                    bar = "█" * int(pct / 5)

                    emoji = {"high": "🔥", "medium": "⚡", "low": "🔋"}.get(level, "❓")
                    console.log(f"  {emoji} {level:8} {count:3d} ({pct:4.0f}%) {bar}")

            # Outcome distribution
            if any(row['outcome_status'] for row in outcome_dist):
                console.log("\n[bold]📊 Outcome Status:[/bold]")
                for row in outcome_dist:
                    status = row['outcome_status'] or 'pending'
                    count = row['count']
                    pct = count / total * 100
                    bar = "█" * int(pct / 5)

                    emoji_map = {
                        "successful": "✅",
                        "failed": "❌",
                        "mixed": "⚖️",
                        "abandoned": "🚫",
                        "pending": "⏳"
                    }
                    emoji = emoji_map.get(status, "❓")
                    console.log(f"  {emoji} {status:10} {count:3d} ({pct:4.0f}%) {bar}")

            # Type distribution
            console.log("\n[bold]🏷️  Decision Types:[/bold]")
            for row in type_dist:
                dec_type = row['decision_type']
                count = row['count']
                pct = count / total * 100
                bar = "█" * int(pct / 5)
                console.log(f"  • {dec_type:15} {count:3d} ({pct:4.0f}%) {bar}")

            # ADHD insights
            console.log("\n[bold]🧠 ADHD Insights:[/bold]")

            # Calculate review needs
            review_count = await conn.fetchval("""
                SELECT COUNT(*)
                FROM decisions
                WHERE workspace_id = $1
                AND created_at < NOW() - INTERVAL '30 days'
                AND (outcome_status IS NULL OR outcome_status = 'pending')
            """, workspace_id)

            if review_count > 0:
                console.log(f"  ⚠️  {review_count} decisions need review (>30 days old)")
            else:
                console.log(f"  ✅ All decisions reviewed or recent")

            # Confidence insights
            low_conf = sum(row['count'] for row in confidence_dist if row['confidence_level'] == 'low')
            if low_conf > 0:
                console.log(f"  ⚠️  {low_conf} low-confidence decisions may need revisiting")

            console.log(f"\n[dim]Full ADHD insights coming in Phase 3 (pattern learning)[/dim]")

        finally:
            await conn.close()

    asyncio.run(_enhanced())


# ============================================================================
# PHASE 2: Query Language for Flexible Filtering (~1.5 hours)
# ============================================================================

@click.command("query")
@click.argument("filter_expression")
@click.option("--limit", "-n", default=20, help="Max results (default: 20)")
@click.option("--workspace", "-w", help="Workspace path")
def query_decisions(filter_expression: str, limit: int, workspace: Optional[str]):
    """
    🔍 Query decisions with flexible filter expressions

    Phase 2 feature: SQL-like query language for complex filtering.

    \b
    Filter expressions:
        age > 30                           # Decisions older than 30 days
        confidence = low                   # Low confidence only
        type = architectural               # Architectural decisions
        outcome = pending                  # Pending outcomes
        tag contains mcp                   # Tag matching
        age > 60 AND confidence = low      # Combined filters

    \b
    Examples:
        dopemux decisions query "age > 90"
        dopemux decisions query "type = architectural AND outcome = successful"
        dopemux decisions query "confidence = low" -n 10
    """

    async def _query():
        workspace_id = workspace or get_workspace_id()

        conn = await get_conport_connection()
        if not conn:
            return

        try:
            # Parse filter expression into SQL WHERE clause
            # Simple parser for demonstration (full parser in Phase 2 complete)
            where_clause = "workspace_id = $1"
            params = [workspace_id]
            param_count = 1

            # Parse simple expressions
            if "age >" in filter_expression:
                import re
                match = re.search(r'age\s*>\s*(\d+)', filter_expression)
                if match:
                    days = int(match.group(1))
                    param_count += 1
                    where_clause += f" AND created_at < NOW() - INTERVAL '1 day' * ${param_count}"
                    params.append(days)

            if "type =" in filter_expression:
                import re
                match = re.search(r'type\s*=\s*(\w+)', filter_expression)
                if match:
                    dec_type = match.group(1)
                    param_count += 1
                    where_clause += f" AND decision_type = ${param_count}"
                    params.append(dec_type)

            if "confidence =" in filter_expression:
                import re
                match = re.search(r'confidence\s*=\s*(\w+)', filter_expression)
                if match:
                    conf = match.group(1)
                    param_count += 1
                    where_clause += f" AND confidence_level = ${param_count}"
                    params.append(conf)

            if "outcome =" in filter_expression:
                import re
                match = re.search(r'outcome\s*=\s*(\w+)', filter_expression)
                if match:
                    outcome = match.group(1)
                    param_count += 1
                    where_clause += f" AND outcome_status = ${param_count}"
                    params.append(outcome)

            # Execute query
            query = f"""
                SELECT
                    id, summary, decision_type, confidence_level,
                    outcome_status, created_at,
                    EXTRACT(DAY FROM (NOW() - created_at)) as age_days
                FROM decisions
                WHERE {where_clause}
                ORDER BY created_at DESC
                LIMIT {limit}
            """

            rows = await conn.fetch(query, *params)

            if not rows:
                console.log(f"\n[yellow]No decisions match: {filter_expression}[/yellow]")
                return

            # Display results
            table = Table(title=f"📋 Query Results ({len(rows)}) - {filter_expression}", show_header=True)
            table.add_column("ID", style="cyan", width=8)
            table.add_column("Age", style="dim", width=8)
            table.add_column("Type", style="yellow", width=12)
            table.add_column("Conf", style="green", width=8)
            table.add_column("Summary", style="white")

            for row in rows:
                decision_id = str(row['id'])[:8]
                age_days = int(row['age_days'])
                dec_type = row['decision_type'][:10]
                conf = (row['confidence_level'] or 'N/A')[:6]
                summary = row['summary'][:45] + "..." if len(row['summary']) > 45 else row['summary']

                table.add_row(decision_id, f"{age_days}d", dec_type, conf, summary)

            console.log(table)
            console.log(f"\n[dim]Tip: Use 'dopemux decisions show <ID>' for details[/dim]")

        finally:
            await conn.close()

    asyncio.run(_query())


# ============================================================================
# PHASE 3 SPRINT 1: Tag Pattern Detection (~2 hours)
# ============================================================================

async def detect_tag_clusters(
    conn: asyncpg.Connection,
    workspace_id: str,
    min_support: int = 2
) -> list:
    """
    Detect frequently co-occurring tag patterns using Apriori algorithm.

    Returns tag clusters with occurrence counts, success rates, and recommendations.
    """
    # Fetch all decisions with tags
    decisions = await conn.fetch("""
        SELECT id, tags, outcome_status, confidence_level, decision_type
        FROM decisions
        WHERE workspace_id = $1
        AND tags IS NOT NULL
        AND array_length(tags, 1) > 0
    """, workspace_id)

    if len(decisions) < min_support:
        return []

    # Count tag frequencies (single tags)
    from collections import Counter
    tag_counts = Counter()
    tag_pairs = Counter()

    for decision in decisions:
        tags = set(decision['tags'])

        # Count individual tags
        for tag in tags:
            tag_counts[tag] += 1

        # Count tag pairs
        tags_list = sorted(tags)
        for i, tag1 in enumerate(tags_list):
            for tag2 in tags_list[i+1:]:
                pair = (tag1, tag2)
                tag_pairs[pair] += 1

    # Filter by min_support
    frequent_tags = {tag: count for tag, count in tag_counts.items()
                     if count >= min_support}

    frequent_pairs = {pair: count for pair, count in tag_pairs.items()
                      if count >= min_support}

    # Calculate association metrics
    clusters = []

    for (tag1, tag2), count in frequent_pairs.items():
        # Confidence: P(tag2 | tag1)
        confidence = count / tag_counts[tag1]

        # Lift: How much more likely is tag2 given tag1?
        lift = confidence / (tag_counts[tag2] / len(decisions))

        # Success rate for this cluster
        cluster_decisions = [d for d in decisions
                             if tag1 in d['tags'] and tag2 in d['tags']]

        successful = sum(1 for d in cluster_decisions
                        if d['outcome_status'] == 'successful')
        total_with_outcome = sum(1 for d in cluster_decisions
                                if d['outcome_status'] is not None)

        success_rate = successful / total_with_outcome if total_with_outcome > 0 else None

        clusters.append({
            "tags": [tag1, tag2],
            "occurrence_count": count,
            "confidence": confidence,
            "lift": lift,
            "success_rate": success_rate,
            "sample_size": len(cluster_decisions),
            "decisions_with_outcome": total_with_outcome
        })

    # Sort by occurrence count (most frequent first)
    clusters.sort(key=lambda x: x['occurrence_count'], reverse=True)

    return clusters[:10]  # ADHD limit: top 10


async def store_pattern(
    conn: asyncpg.Connection,
    workspace_id: str,
    pattern_type: str,
    pattern_signature: dict,
    stats: dict
):
    """Store or update a detected pattern."""
    import json

    await conn.execute("""
        INSERT INTO decision_patterns (
            workspace_id,
            pattern_type,
            pattern_signature,
            pattern_name,
            occurrence_count,
            success_count,
            pattern_confidence,
            recommendations,
            last_seen
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW())
        ON CONFLICT (workspace_id, pattern_type, pattern_signature)
        DO UPDATE SET
            occurrence_count = EXCLUDED.occurrence_count,
            success_count = EXCLUDED.success_count,
            pattern_confidence = EXCLUDED.pattern_confidence,
            last_seen = NOW(),
            updated_at = NOW()
    """,
        workspace_id,
        pattern_type,
        json.dumps(pattern_signature),
        stats.get('pattern_name'),
        stats.get('occurrence_count'),
        stats.get('success_count'),
        stats.get('pattern_confidence'),
        json.dumps(stats.get('recommendations', []))
    )


@click.command("tags")
@click.option("--min-support", "-m", default=2, help="Minimum occurrences for pattern (default: 2)")
@click.option("--workspace", "-w", help="Workspace path")
@click.option("--save", "-s", is_flag=True, help="Save detected patterns to database")
def pattern_tags(min_support: int, workspace: Optional[str], save: bool):
    """
    🔍 Detect and display tag clustering patterns

    Phase 3 Sprint 1: Auto-detect frequently co-occurring tags and
    provide recommendations for new decisions.

    \b
    Examples:
        dopemux decisions patterns tags                  # Show tag clusters
        dopemux decisions patterns tags --min-support 3  # Require 3+ occurrences
        dopemux decisions patterns tags --save           # Save to database
    """

    async def _detect():
        workspace_id = workspace or get_workspace_id()

        conn = await get_conport_connection()
        if not conn:
            return

        try:
            clusters = await detect_tag_clusters(conn, workspace_id, min_support)

            if not clusters:
                console.log(f"\n[yellow]No tag patterns found with min_support={min_support}.[/yellow]")
                console.log("[dim]Try lowering --min-support or add more tagged decisions[/dim]")
                return

            # Display patterns
            console.print(Panel.fit(
                f"[bold cyan]🔍 Tag Pattern Analysis[/bold cyan]\n"
                f"Workspace: {workspace_id} | Min Support: {min_support}",
                border_style="cyan"
            ))

            console.log(f"\n[bold]📊 Detected {len(clusters)} Tag Clusters:[/bold]\n")

            for i, cluster in enumerate(clusters, 1):
                tags = " + ".join(cluster['tags'])
                count = cluster['occurrence_count']
                conf = cluster['confidence']
                lift = cluster['lift']

                # Visual indicators
                if lift > 2.0:
                    indicator = "🔥 Strong"
                elif lift > 1.5:
                    indicator = "⚡ Moderate"
                else:
                    indicator = "💡 Weak"

                console.log(f"[bold cyan]{i}. {tags}[/bold cyan] {indicator}")
                console.log(f"   Occurrences: {count}")
                console.log(f"   Confidence: {conf:.0%} (when you use '{cluster['tags'][0]}', {conf:.0%} chance you also use '{cluster['tags'][1]}')")
                console.log(f"   Lift: {lift:.2f}x (tags appear together {lift:.1f}x more than random)")

                if cluster['success_rate'] is not None:
                    sr = cluster['success_rate']
                    console.log(f"   Success rate: {sr:.0%} ({cluster['decisions_with_outcome']}/{cluster['sample_size']} decisions completed)")
                else:
                    console.log(f"   Success rate: N/A (no outcomes tracked yet)")

                console.log()

            # Save patterns if requested
            if save:
                console.log("[bold]💾 Saving patterns to database...[/bold]")
                saved = 0

                for cluster in clusters:
                    pattern_sig = {"tags": cluster['tags']}
                    stats = {
                        "pattern_name": " + ".join(cluster['tags']),
                        "occurrence_count": cluster['occurrence_count'],
                        "success_count": int(cluster['success_rate'] * cluster['decisions_with_outcome'])
                                        if cluster['success_rate'] else 0,
                        "pattern_confidence": cluster['confidence'],
                        "recommendations": [
                            f"When using '{cluster['tags'][0]}', consider also tagging with '{cluster['tags'][1]}' ({cluster['confidence']:.0%} co-occurrence)"
                        ]
                    }

                    await store_pattern(conn, workspace_id, 'tag_cluster', pattern_sig, stats)
                    saved += 1

                console.log(f"✅ Saved {saved} patterns to decision_patterns table")

            # Recommendations
            console.log("[bold]💡 Recommendations:[/bold]")

            if clusters:
                top_cluster = clusters[0]
                console.log(f"  • Most common pattern: '{' + '.join(top_cluster['tags'])}' ({top_cluster['occurrence_count']} occurrences)")
                console.log(f"  • When tagging decisions, consider these frequent combinations")

                # Suggest tags for next decision
                console.log(f"\n[dim]Next time you tag a decision with '{clusters[0]['tags'][0]}', the system can suggest '{clusters[0]['tags'][1]}'[/dim]")

        finally:
            await conn.close()

    asyncio.run(_detect())
