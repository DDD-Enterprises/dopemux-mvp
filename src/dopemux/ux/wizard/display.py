"""Rich display helpers for the extraction wizard.

All rendering is centralised here so stage modules stay logic-focused.
"""

from __future__ import annotations

import math
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from rich.box import ROUNDED, SIMPLE_HEAVY
from rich.columns import Columns
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from dopemux.console import console

from .stages import (
    AUTHORITY_CLASSES,
    PHASE_INFO,
    PHASES,
    PROVIDER_COLORS,
    StageResult,
    StageStatus,
    WizardState,
)

# ── Version tag ─────────────────────────────────────────────────────────────
WIZARD_VERSION = "1.0.0"


# ── Welcome / branded header ───────────────────────────────────────────────

def render_welcome_panel(state: WizardState) -> None:
    """Display the branded wizard header with repo metadata."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    repo_name = state.repo_root.name

    branch_line = f"Branch: [bold]{state.git_branch or '(unknown)'}[/bold]"
    if state.git_clean:
        branch_line += "  •  [green]Clean working tree[/green]"
    else:
        branch_line += "  •  [yellow]Dirty working tree[/yellow]"

    body = (
        f"\n"
        f"  Repository: [bold cyan]{repo_name}[/bold cyan]\n"
        f"  {branch_line}\n"
        f"  Time: {now}\n"
        f"\n"
        f"  This wizard will guide you through:\n"
        f"  [dim]1.[/dim] 📊  Corpus analysis — what's in your repo\n"
        f"  [dim]2.[/dim] 💰  Cost planning — choose your budget\n"
        f"  [dim]3.[/dim] 🚀  Extraction — build your truth map\n"
    )

    console.print(
        Panel(
            body,
            title=f"[bold white]🔬  DOPEMUX DOCUMENTATION AUDIT WIZARD  v{WIZARD_VERSION}[/bold white]",
            border_style="bright_cyan",
            box=ROUNDED,
            padding=(0, 2),
        )
    )


# ── Stage transitions ──────────────────────────────────────────────────────

def render_stage_header(stage_num: int, title: str, icon: str) -> None:
    """Print a visual separator when entering a new stage."""
    console.print()
    console.rule(f"[bold bright_cyan]  Stage {stage_num}  •  {icon}  {title}  [/bold bright_cyan]")
    console.print()


def render_stage_complete(stage_num: int, title: str, result: StageResult) -> None:
    """Show stage completion status with duration."""
    if result.status == StageStatus.COMPLETED:
        icon = "✅"
        style = "bold green"
        label = "Complete"
    elif result.status == StageStatus.SKIPPED:
        icon = "⏭️"
        style = "bold yellow"
        label = "Skipped"
    elif result.status == StageStatus.FAILED:
        icon = "❌"
        style = "bold red"
        label = "Failed"
    else:
        icon = "⏳"
        style = "dim"
        label = result.status.value

    duration_str = f" ({result.duration:.1f}s)" if result.duration > 0 else ""
    msg = f"  {result.message}" if result.message else ""
    console.print(
        f"\n  {icon}  [{style}]Stage {stage_num} — {title}: {label}{duration_str}[/{style}]{msg}\n"
    )


# ── Health check grid ──────────────────────────────────────────────────────

def render_health_check(checks: List[Tuple[str, bool, str]]) -> None:
    """Render a list of (label, passed, detail) health checks."""
    table = Table(box=SIMPLE_HEAVY, show_header=False, padding=(0, 2))
    table.add_column("Status", width=4)
    table.add_column("Check", min_width=20)
    table.add_column("Detail", style="dim")

    for label, passed, detail in checks:
        icon = "[green]✓[/green]" if passed else "[yellow]⚠[/yellow]"
        table.add_row(icon, label, detail)

    console.print(table)


# ── Corpus breakdown ───────────────────────────────────────────────────────

def _bar(fraction: float, width: int = 20) -> str:
    """Produce a text progress bar: ████░░░░."""
    filled = round(fraction * width)
    return "█" * filled + "░" * (width - filled)


def render_corpus_table(stats: Dict[str, Any]) -> None:
    """Display authority class breakdown from corpus_stats.json."""
    by_class: Dict[str, Dict[str, int]] = stats.get("by_class", {})
    total_count = stats.get("included_count", 1) or 1
    total_size = stats.get("total_included_size", 0)

    table = Table(
        title="[bold]Corpus Breakdown[/bold]",
        box=ROUNDED,
        border_style="bright_cyan",
        padding=(0, 1),
    )
    table.add_column("Class", min_width=12)
    table.add_column("Files", justify="right", min_width=6)
    table.add_column("Size", justify="right", min_width=8)
    table.add_column("Coverage", min_width=24)

    for cls_name in ["canonical", "historical", "operational", "audit", "template", "generated"]:
        cls_data = by_class.get(cls_name, {"count": 0, "total_size": 0})
        count = cls_data.get("count", 0)
        size = cls_data.get("total_size", 0)
        frac = count / total_count if total_count else 0
        meta = AUTHORITY_CLASSES.get(cls_name, {})
        icon = meta.get("icon", "⬜")
        color = meta.get("color", "white")

        size_mb = f"{size / (1024 * 1024):.1f}MB"
        pct = f"{frac * 100:.0f}%"
        bar = _bar(frac)

        table.add_row(
            f"{icon} [{color}]{cls_name}[/{color}]",
            f"{count:,}",
            size_mb,
            f"[{color}]{bar}[/{color}] {pct}",
        )

    total_mb = f"{total_size / (1024 * 1024):.1f} MB"
    table.add_section()
    table.add_row("[bold]Total[/bold]", f"[bold]{total_count:,}[/bold]", f"[bold]{total_mb}[/bold]", "")

    console.print(table)


# ── Cost profile comparison ────────────────────────────────────────────────

def render_cost_table(
    policies: List[Dict[str, Any]],
    corpus_size: int,
    selected: Optional[str] = None,
) -> None:
    """Display routing policy comparison table.

    Each entry in *policies* must have:
        name, label, emoji, desc, low_cost, high_cost, keys_status (str like '3/3')
    """
    table = Table(
        title="[bold]Select Routing Policy[/bold]",
        box=ROUNDED,
        border_style="bright_cyan",
        padding=(0, 1),
    )
    table.add_column("Policy", min_width=18)
    table.add_column("Est. Cost", justify="right", min_width=10)
    table.add_column("Keys", justify="center", min_width=6)
    table.add_column("Description", min_width=24)

    for p in policies:
        name = p["name"]
        prefix = "❯ " if name == selected else "  "
        emoji = p.get("emoji", "💛")
        low = p.get("low_cost", 0)
        high = p.get("high_cost", 0)
        cost_str = f"~${low:.0f}–${high:.0f}"
        keys_ok = p.get("keys_ok", True)
        keys_str = f"[green]✓ {p.get('keys_status', '')}[/green]" if keys_ok else f"[red]✗ {p.get('keys_status', '')}[/red]"

        label = p.get("label", name)
        if name == selected:
            policy_cell = f"{prefix}{emoji} [bold]{label}[/bold]"
        else:
            policy_cell = f"{prefix}{emoji} {label}"
        table.add_row(
            policy_cell,
            cost_str,
            keys_str,
            f"[dim]{p.get('desc', '')}[/dim]",
        )

    corpus_mb = corpus_size / (1024 * 1024)
    table.caption = f"[dim]Estimates based on {corpus_mb:.1f} MB corpus, 14 phases[/dim]"
    console.print(table)


def render_policy_detail(policy: Dict[str, Any], *, index: int, total: int) -> None:
    """Display the currently highlighted routing profile in detail."""
    title = f"[bold white]Profile {index + 1}/{total} • {policy.get('emoji', '💛')} {policy.get('label', policy.get('name', '?'))}[/bold white]"
    low = policy.get("low_cost", 0)
    high = policy.get("high_cost", 0)
    keys_detail = policy.get("keys_detail", {})
    tier_routes = policy.get("tier_routes", {})

    lines = [
        f"[bold]Policy:[/bold] {policy.get('name', '?')}",
        f"[bold]Estimated cost:[/bold] ~${low:.0f}–${high:.0f}",
        f"[bold]What it does:[/bold] {policy.get('desc', '')}",
        "",
        "[bold]Required keys:[/bold]",
    ]

    for env_var, is_set in keys_detail.items():
        status = "[green]set[/green]" if is_set else "[red]missing[/red]"
        lines.append(f"  • {env_var}: {status}")

    lines.extend(["", "[bold]Tier routing:[/bold]"])
    for tier in ("bulk", "extract", "synthesis", "qa"):
        routes = tier_routes.get(tier, [])
        pretty_routes = ", ".join(
            f"{provider}/{model_id}" for provider, model_id, _env_var in routes
        ) or "none"
        lines.append(f"  • {tier}: {pretty_routes}")

    console.print(
        Panel(
            "\n".join(lines),
            title=title,
            border_style="bright_cyan",
            box=ROUNDED,
            padding=(1, 2),
        )
    )


# ── Phase preview ──────────────────────────────────────────────────────────

def render_phase_table(file_counts: Dict[str, int]) -> None:
    """Display per-phase file count and estimated partitions."""
    table = Table(
        title="[bold]Extraction Phase Map[/bold]",
        box=ROUNDED,
        border_style="bright_cyan",
        padding=(0, 1),
    )
    table.add_column("Phase", min_width=4, justify="center")
    table.add_column("Name", min_width=22)
    table.add_column("Files", justify="right", min_width=6)
    table.add_column("Est. Partitions", justify="right", min_width=14)

    for phase_key in PHASES:
        info = PHASE_INFO[phase_key]
        count = file_counts.get(phase_key, 0)
        partitions = max(1, math.ceil(count / 50)) if count > 0 else 0
        count_str = f"{count:,}" if count > 0 else "[dim]—[/dim]"
        part_str = str(partitions) if partitions > 0 else "[dim]meta[/dim]"
        table.add_row(
            f"[bold]{phase_key}[/bold]",
            f"{info['icon']}  {info['name']}",
            count_str,
            part_str,
        )

    total_files = sum(file_counts.values())
    total_parts = sum(max(1, math.ceil(c / 50)) for c in file_counts.values() if c > 0)
    table.add_section()
    table.add_row("[bold]Σ[/bold]", "", f"[bold]{total_files:,}[/bold]", f"[bold]{total_parts}[/bold]")

    console.print(table)


# ── Educational panels ─────────────────────────────────────────────────────

def render_educational_panel(title: str, content: str) -> None:
    """Show an educational info panel with dim explanatory text."""
    console.print(
        Panel(
            f"[dim]{content}[/dim]",
            title=f"[bold bright_cyan]ℹ️  {title}[/bold bright_cyan]",
            border_style="dim cyan",
            box=ROUNDED,
            padding=(1, 2),
        )
    )


# ── Summary / completion ───────────────────────────────────────────────────

def render_summary_panel(state: WizardState) -> None:
    """Display the final wizard completion summary."""
    completed = sum(1 for r in state.phase_results.values() if r.status == StageStatus.COMPLETED)
    skipped = sum(1 for r in state.phase_results.values() if r.status == StageStatus.SKIPPED)
    failed = sum(1 for r in state.phase_results.values() if r.status == StageStatus.FAILED)
    total = len(state.phase_results)

    lines = [
        f"  [bold]Run ID:[/bold]          {state.run_id}",
        f"  [bold]Policy:[/bold]          {state.selected_policy}",
        f"  [bold]Workers:[/bold]         {state.workers}",
        f"  [bold]Overrides:[/bold]       {len(state.provider_key_overrides)} provider key override(s)",
        "",
    ]

    if total > 0:
        lines.append(f"  [bold]Phases:[/bold]          {total} total")
        if completed:
            lines.append(f"  [green]  ✓ Completed:[/green]   {completed}")
        if skipped:
            lines.append(f"  [yellow]  ⏭ Skipped:[/yellow]    {skipped}")
        if failed:
            lines.append(f"  [red]  ✗ Failed:[/red]     {failed}")
    else:
        lines.append("  [dim]No phases executed (preview mode)[/dim]")

    if state.corpus_stats:
        corpus_mb = state.corpus_total_size / (1024 * 1024)
        lines.extend([
            "",
            f"  [bold]Corpus:[/bold]          {state.corpus_included_count:,} files, {corpus_mb:.1f} MB",
        ])

    if state.execute_mode and state.run_id:
        run_dir = state.repo_root / "extraction" / "repo-truth-extractor" / "v5" / "runs" / state.run_id
        lines.extend([
            "",
            f"  [bold]Artifacts:[/bold]       {run_dir}",
        ])

    body = "\n".join(lines)
    title_icon = "🏆" if completed > 0 and failed == 0 else "📋"

    console.print(
        Panel(
            f"\n{body}\n",
            title=f"[bold white]{title_icon}  Wizard Summary[/bold white]",
            border_style="bright_cyan",
            box=ROUNDED,
            padding=(0, 2),
        )
    )


def render_next_steps(state: WizardState) -> None:
    """Show recommended next steps after wizard completion."""
    steps = []
    if not state.execute_mode:
        steps.append("Run with [bold]--execute[/bold] to perform actual extraction")
    if state.phase_results:
        completed = [k for k, v in state.phase_results.items() if v.status == StageStatus.COMPLETED]
        if completed:
            steps.append(f"Review extraction artifacts in [bold]extraction/repo-truth-extractor/v5/runs/{state.run_id}/[/bold]")
    if not state.promptset_ready:
        steps.append("Generate promptset with [bold]dopemux extractor init --interactive[/bold]")

    if steps:
        console.print("\n[bold bright_cyan]Next Steps:[/bold bright_cyan]")
        for i, step in enumerate(steps, 1):
            console.print(f"  {i}. {step}")
        console.print()
