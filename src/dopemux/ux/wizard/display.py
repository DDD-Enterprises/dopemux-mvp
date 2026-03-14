"""Rich display helpers for the extraction wizard.

All rendering is centralised here so stage modules stay logic-focused.
"""

from __future__ import annotations

import math
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from rich.box import ROUNDED, SIMPLE_HEAVY, HEAVY
from rich.columns import Columns
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from dopemux.console import console

from .stages import (
    AUTHORITY_CLASSES,
    PHASE_INFO,
    PHASES,
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

        style = "bold" if name == selected else ""
        table.add_row(
            f"{prefix}{emoji} [{style}]{p.get('label', name)}[/{style}]",
            cost_str,
            keys_str,
            f"[dim]{p.get('desc', '')}[/dim]",
        )

    corpus_mb = corpus_size / (1024 * 1024)
    table.caption = f"[dim]Estimates based on {corpus_mb:.1f} MB corpus, 14 phases[/dim]"
    console.print(table)


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


# ── Intelligence report ───────────────────────────────────────────────────

_LIFECYCLE_META: Dict[str, Tuple[str, str]] = {
    "fresh":   ("🌱", "bright_green"),
    "active":  ("🔥", "green"),
    "stale":   ("🌤", "yellow"),
    "frozen":  ("🧊", "blue"),
    "unknown": ("❓", "dim"),
}

_SAVINGS_THRESHOLDS = [
    (50, "bold green", "🚀 MAJOR SAVINGS"),
    (25, "green",      "💚 GOOD SAVINGS"),
    (10, "yellow",     "💛 MODERATE"),
    (0,  "dim",        "—  MINIMAL"),
]


def _health_gauge(score: int) -> Text:
    """Render a coloured health score bar in a Text object."""
    if score >= 75:
        bar_color, label = "bright_green", "HEALTHY"
    elif score >= 50:
        bar_color, label = "yellow", "FAIR"
    else:
        bar_color, label = "red", "NEEDS ATTENTION"

    filled = round(score / 5)           # 0-20 blocks
    empty  = 20 - filled
    bar = "█" * filled + "░" * empty
    t = Text()
    t.append("  ")
    t.append(bar, style=bar_color)
    t.append(f"  {score}/100  ", style="bold " + bar_color)
    t.append(label, style="bold " + bar_color)
    return t


def _fmt(n: int, warn_above: int = 0, good_below: int = 0) -> str:
    """Format a number with optional colour."""
    if warn_above and n > warn_above:
        return f"[bold yellow]{n:,}[/bold yellow]"
    if good_below and n < good_below:
        return f"[green]{n:,}[/green]"
    return f"[bold]{n:,}[/bold]"


def render_intelligence_report(intel: Dict[str, Any]) -> None:
    """
    Render the full prescan_intelligence.json as a rich terminal display.

    Sections:
      1. Header panel with corpus health gauge
      2. Side-by-side: Corpus Profile | Planned Features
      3. Lifecycle distribution bar chart
      4. Extraction hints (savings & routing)
      5. Co-change groups (if any)
    """
    summary = intel.get("corpus_summary", {})
    lifecycle = intel.get("lifecycle_distribution", {})
    planned = intel.get("planned_features", {})
    hints = intel.get("extraction_hints", {})
    dup_groups = intel.get("duplicate_groups", {})
    co_groups = intel.get("co_change_groups", [])

    health = summary.get("corpus_health_score", 0)
    total_files = summary.get("included_files", 0)
    ghost_count = summary.get("ghost_files", 0)
    git_branch = intel.get("git_branch", "?")
    git_sha = (intel.get("git_sha") or "?")[:10]
    chain_count = intel.get("version_chain_count", 0)
    compress_n = intel.get("compression_potential_files", 0)
    skip_n = len(hints.get("skip_duplicates", []))
    dup_n = sum(len(v) - 1 for v in dup_groups.values())
    hichurn_n = len(hints.get("high_churn_files", []))

    adr_n = len(planned.get("proposed_adrs", []))
    stub_n = len(planned.get("stub_files", []))
    todo_n = len(planned.get("todo_files", []))
    draft_n = len(planned.get("draft_docs", []))

    # ── 1. Header panel ────────────────────────────────────────────────────
    gen_ts = intel.get("generated_at", "")[:19].replace("T", "  ")
    header_lines = [
        "",
        _health_gauge(health),
        Text(f"\n  Git: {git_sha}  •  Branch: {git_branch}  •  Generated: {gen_ts}", style="dim"),
        Text(""),
    ]
    header_body = Text.assemble(*[
        item if isinstance(item, Text) else Text(item)
        for item in header_lines
    ])

    console.print()
    console.print(
        Panel(
            header_body,
            title="[bold white]🧠  PRE-EXTRACTION INTELLIGENCE REPORT[/bold white]",
            border_style="bright_cyan",
            box=HEAVY,
            padding=(0, 2),
        )
    )

    # ── 2. Side-by-side: Corpus Profile | Planned Features ─────────────────
    # Left panel — corpus profile
    left = Table(box=None, show_header=False, padding=(0, 1), expand=True)
    left.add_column("Label", style="dim", min_width=24)
    left.add_column("Value", justify="right")

    left.add_row("Total included files",    _fmt(total_files))
    left.add_row("Ghost files (👻 recovered)", _fmt(ghost_count))
    left.add_row("Redundant files (dupes)",  _fmt(dup_n, warn_above=50))
    left.add_row("Skip candidates",          _fmt(skip_n, warn_above=100))
    left.add_row("Version chains",           _fmt(chain_count))
    left.add_row("Compressible version files", _fmt(compress_n))
    left.add_row("High-churn files (> 1/mo)", _fmt(hichurn_n))
    left.add_row("Co-change groups",         _fmt(len(co_groups)))

    corpus_panel = Panel(
        left,
        title="[bold cyan]📦 Corpus Profile[/bold cyan]",
        border_style="cyan",
        box=ROUNDED,
        padding=(0, 1),
    )

    # Right panel — planned features
    right = Table(box=None, show_header=False, padding=(0, 1), expand=True)
    right.add_column("Label", style="dim", min_width=22)
    right.add_column("Value", justify="right")

    def _feat_fmt(n: int, icon: str) -> str:
        color = "magenta" if n > 0 else "dim"
        return f"[{color}]{icon}  {n:,}[/{color}]"

    right.add_row("Proposed ADRs",         _feat_fmt(adr_n,   "📋"))
    right.add_row("Stub implementations", _feat_fmt(stub_n,  "🔧"))
    right.add_row("Files with TODOs",     _feat_fmt(todo_n,  "📌"))
    right.add_row("Draft / proposed docs", _feat_fmt(draft_n, "📝"))

    total_planned = adr_n + stub_n + draft_n
    right.add_section()
    feat_color = "magenta" if total_planned > 0 else "dim"
    right.add_row(
        "[bold]Total planned work items[/bold]",
        f"[bold {feat_color}]{total_planned:,}[/bold {feat_color}]",
    )

    planned_panel = Panel(
        right,
        title="[bold magenta]🗺  Planned Features[/bold magenta]",
        border_style="magenta",
        box=ROUNDED,
        padding=(0, 1),
    )

    console.print(Columns([corpus_panel, planned_panel], equal=True, expand=True))

    # ── 3. Lifecycle bar chart ──────────────────────────────────────────────
    if lifecycle:
        lc_table = Table(
            box=ROUNDED,
            border_style="dim cyan",
            title="[bold]📅  File Lifecycle Distribution[/bold]",
            padding=(0, 1),
        )
        lc_table.add_column("Stage",   min_width=10)
        lc_table.add_column("Bar",     min_width=28)
        lc_table.add_column("Files",   justify="right", min_width=6)
        lc_table.add_column("%",       justify="right", min_width=5)

        lc_total = sum(lifecycle.values()) or 1
        for stage, count in sorted(
            lifecycle.items(),
            key=lambda x: ["fresh", "active", "stale", "frozen", "unknown"].index(x[0])
            if x[0] in ["fresh", "active", "stale", "frozen", "unknown"]
            else 99,
        ):
            icon, color = _LIFECYCLE_META.get(stage, ("•", "white"))
            frac = count / lc_total
            bar_filled = round(frac * 26)
            bar = f"[{color}]" + "█" * bar_filled + "[/]" + "[dim]" + "░" * (26 - bar_filled) + "[/dim]"
            pct = f"{frac * 100:.0f}%"
            lc_table.add_row(
                f"{icon}  [{color}]{stage}[/{color}]",
                bar,
                f"{count:,}",
                f"[dim]{pct}[/dim]",
            )

        console.print(lc_table)

    # ── 4. Extraction hints ─────────────────────────────────────────────────
    if skip_n or compress_n or ghost_count or total_planned or hichurn_n:
        token_reduction_est = min(
            int((skip_n / max(total_files, 1)) * 100 * 0.6
                + (compress_n / max(total_files, 1)) * 100 * 0.3),
            65,
        )
        for threshold, color, label in _SAVINGS_THRESHOLDS:
            if token_reduction_est >= threshold:
                savings_color, savings_label = color, label
                break

        hints_lines: list[str] = []
        if skip_n:
            hints_lines.append(
                f"  [bold yellow]💰 {skip_n:,} files SKIPPED[/bold yellow]"
                f" [dim](exact duplicates — zero extraction cost)[/dim]"
            )
        if compress_n:
            hints_lines.append(
                f"  [bold cyan]🗜  {compress_n:,} files COMPRESSED[/bold cyan]"
                f" [dim](version chains → evolution summaries)[/dim]"
            )
        if ghost_count:
            hints_lines.append(
                f"  [dim]👻 {ghost_count} ghost files[/dim]"
                f" [dim](deleted content — run Grok DISCOVER pass to assess)[/dim]"
            )
        if total_planned:
            hints_lines.append(
                f"  [bold magenta]📋 {total_planned} planned features[/bold magenta]"
                f" [dim]→ Phase X + T priority routing[/dim]"
            )
        if hichurn_n:
            hints_lines.append(
                f"  [bold]🔥 {hichurn_n} high-churn files[/bold]"
                f" [dim]→ premium model routing recommended[/dim]"
            )

        hints_lines.append("")
        hints_lines.append(
            f"  Estimated token reduction: "
            f"[bold {savings_color}]{token_reduction_est}%  {savings_label}[/bold {savings_color}]"
        )

        console.print(
            Panel(
                "\n".join(hints_lines),
                title="[bold green]💡  Extraction Hints[/bold green]",
                border_style="green",
                box=ROUNDED,
                padding=(0, 1),
            )
        )

    # ── 5. Co-change groups ─────────────────────────────────────────────────
    if co_groups:
        cg_table = Table(
            box=ROUNDED,
            border_style="dim",
            title=(
                "[bold]🔗  Top Co-Change Groups "
                "[dim](files that always move together)[/dim][/bold]"
            ),
            padding=(0, 1),
            show_lines=True,
        )
        cg_table.add_column("Commits", justify="right", min_width=7)
        cg_table.add_column("Files in Group", min_width=48)

        for group in co_groups[:6]:
            files_txt = "\n".join(
                f"[dim cyan]{f}[/dim cyan]"
                for f in sorted(group["files"])[:4]
            )
            if len(group["files"]) > 4:
                files_txt += f"\n[dim]  … +{len(group['files']) - 4} more[/dim]"
            cg_table.add_row(
                f"[bold]{group['commit_count']}[/bold]",
                files_txt,
            )

        console.print(cg_table)

    # ── 6. Code Intelligence ────────────────────────────────────────────────
    code_intel = intel.get("code_intelligence", {})
    if code_intel:
        code_tbl = Table(box=None, show_header=False, padding=(0, 1), expand=True)
        code_tbl.add_column("Metric", style="dim", min_width=28)
        code_tbl.add_column("Value", justify="right")

        code_tbl.add_row("Python files analysed", _fmt(code_intel.get("total_python_files", 0)))
        code_tbl.add_row("Entry points (CLI/API/main)", _fmt(code_intel.get("entry_point_count", 0)))
        code_tbl.add_row("Orphan files (dead code)", _fmt(code_intel.get("orphan_count", 0), warn_above=10))
        code_tbl.add_row("Hub files (≥5 importers)", _fmt(code_intel.get("hub_count", 0)))
        code_tbl.add_row("Circular imports detected", _fmt(code_intel.get("circular_count", len(code_intel.get("circular_imports", []))), warn_above=1))

        cov_ratio = code_intel.get("test_coverage_ratio", 0)
        cov_pct = int(cov_ratio * 100)
        cov_color = "green" if cov_pct >= 60 else ("yellow" if cov_pct >= 30 else "red")
        code_tbl.add_row("Test coverage (by file)", f"[{cov_color}]{cov_pct}%[/{cov_color}]")

        avg_doc = code_intel.get("avg_docstring_coverage", 0)
        dc = "green" if avg_doc >= 0.6 else ("yellow" if avg_doc >= 0.3 else "red")
        code_tbl.add_row("Avg docstring coverage", f"[{dc}]{avg_doc:.0%}[/{dc}]")

        # Top hubs
        hub_lines: list[str] = []
        for h in code_intel.get("hub_files", [])[:5]:
            hub_lines.append(f"  [cyan]{h['path']}[/cyan] [dim]← {h['imported_by']} importers[/dim]")

        # Top complexity hotspots
        hot_lines: list[str] = []
        for h in code_intel.get("complexity_hotspots", [])[:5]:
            cx_val = h.get("score", h.get("complexity", 0))
            hc = "red" if cx_val > 0.7 else "yellow"
            hot_lines.append(f"  [{hc}]{h['path']}[/{hc}] [dim](score: {cx_val:.2f})[/dim]")

        body_parts = [code_tbl]
        if hub_lines:
            body_parts.append(Text(""))
            body_parts.append(Text("🔗 Top Import Hubs", style="bold"))
            for ln in hub_lines:
                body_parts.append(Text.from_markup(ln))
        if hot_lines:
            body_parts.append(Text(""))
            body_parts.append(Text("🔥 Complexity Hotspots", style="bold"))
            for ln in hot_lines:
                body_parts.append(Text.from_markup(ln))

        from rich.console import Group as RichGroup

        console.print(
            Panel(
                RichGroup(*body_parts),
                title="[bold blue]💻 Code Intelligence[/bold blue]",
                border_style="blue",
                box=ROUNDED,
                padding=(0, 1),
            )
        )

    # ── 7. Architecture Intelligence ────────────────────────────────────────
    arch_data = intel.get("architecture", {})
    if arch_data:
        arch_tbl = Table(box=None, show_header=False, padding=(0, 1), expand=True)
        arch_tbl.add_column("Metric", style="dim", min_width=28)
        arch_tbl.add_column("Value", justify="right")

        arch_tbl.add_row("Services (compose + registry)", _fmt(arch_data.get("service_count", 0)))
        arch_tbl.add_row("API endpoints detected", _fmt(arch_data.get("api_endpoint_count", 0)))
        arch_tbl.add_row("Event publish/subscribe flows", _fmt(arch_data.get("event_flow_count", 0)))
        arch_tbl.add_row("Files mapped to services", _fmt(arch_data.get("mapped_file_count", arch_data.get("file_service_map_count", 0))))

        # Service-port table
        svc_list = arch_data.get("services", [])
        if svc_list and isinstance(svc_list, list):
            svc_tbl = Table(
                box=ROUNDED,
                border_style="dim",
                padding=(0, 1),
                show_lines=False,
            )
            svc_tbl.add_column("Service", style="bold cyan", min_width=24)
            svc_tbl.add_column("Ports", justify="right", min_width=12)
            svc_tbl.add_column("Files", justify="right", min_width=6)

            partitions = arch_data.get("service_partitions", {})
            for svc_item in sorted(svc_list, key=lambda s: s.get("name", ""))[:15]:
                svc_name = svc_item.get("name", "?")
                raw_ports = svc_item.get("ports", [])
                ports = ", ".join(str(p).split(":")[-1] for p in raw_ports) or "—"
                file_count = len(partitions.get(svc_name, []))
                svc_tbl.add_row(svc_name, ports, str(file_count))

        # Event flows
        event_lines: list[str] = []
        for ef in arch_data.get("event_flows", [])[:5]:
            event_lines.append(
                f"  [magenta]{ef.get('type', '?')}[/magenta] "
                f"[dim]in {ef.get('file', '?')}:{ef.get('line', '?')}[/dim]"
            )

        from rich.console import Group as RichGroup

        parts = [arch_tbl]
        if svc_list:
            parts.append(Text(""))
            parts.append(svc_tbl)
        if event_lines:
            parts.append(Text(""))
            parts.append(Text("⚡ Event Flows (sample)", style="bold"))
            for ln in event_lines:
                parts.append(Text.from_markup(ln))

        console.print(
            Panel(
                RichGroup(*parts),
                title="[bold green]🏗️  Architecture Intelligence[/bold green]",
                border_style="green",
                box=ROUNDED,
                padding=(0, 1),
            )
        )

    # ── 8. Feature Intelligence ─────────────────────────────────────────────
    feat_data = intel.get("features", {})
    if feat_data:
        feat_tbl = Table(box=None, show_header=False, padding=(0, 1), expand=True)
        feat_tbl.add_column("Metric", style="dim", min_width=28)
        feat_tbl.add_column("Value", justify="right")

        feat_tbl.add_row("Feature flags (ENABLE_*/FEATURE_*)", _fmt(feat_data.get("feature_flag_count", 0)))
        feat_tbl.add_row("CLI commands (click)", _fmt(feat_data.get("cli_command_count", 0)))
        feat_tbl.add_row("MCP tools registered", _fmt(feat_data.get("mcp_tool_count", 0)))
        feat_tbl.add_row("MCP servers identified", _fmt(feat_data.get("mcp_server_count", 0)))

        avg_comp = feat_data.get("avg_completeness", 0)
        comp_color = "green" if avg_comp >= 0.7 else ("yellow" if avg_comp >= 0.4 else "red")
        feat_tbl.add_row(
            "Avg feature completeness",
            f"[{comp_color}]{avg_comp:.0%}[/{comp_color}]",
        )

        # Feature flags table
        flags = feat_data.get("feature_flags", [])
        if flags:
            flag_tbl = Table(
                box=ROUNDED,
                border_style="dim",
                padding=(0, 1),
                show_lines=False,
            )
            flag_tbl.add_column("Flag", style="bold yellow", min_width=30)
            flag_tbl.add_column("Default", justify="center", min_width=8)
            flag_tbl.add_column("Files", justify="right", min_width=5)

            for fl in flags[:12]:
                name = fl.get("name", "?")
                default = fl.get("default", "?")
                files = fl.get("file_count", len(fl.get("files", [])))
                flag_tbl.add_row(name, str(default), str(files))

        # CLI tree
        cli_cmds = feat_data.get("cli_commands", [])
        cli_lines: list[str] = []
        for cmd in cli_cmds[:8]:
            indent = "  " * cmd.get("depth", 0)
            kind = cmd.get("kind", "command")
            icon = "📂" if kind == "group" else "▸"
            cli_lines.append(
                f"  {indent}{icon} [bold]{cmd.get('name', '?')}[/bold] "
                f"[dim]{cmd.get('file', '')}[/dim]"
            )

        # MCP servers
        mcp_servers = feat_data.get("mcp_servers", [])
        mcp_lines: list[str] = []
        for srv in mcp_servers[:8]:
            tool_n = srv.get("tool_count", 0)
            mcp_lines.append(
                f"  [cyan]{srv.get('name', '?')}[/cyan] "
                f"[dim]({tool_n} tools)[/dim]"
            )

        from rich.console import Group as RichGroup

        parts = [feat_tbl]
        if flags:
            parts.append(Text(""))
            parts.append(flag_tbl)
        if cli_lines:
            parts.append(Text(""))
            parts.append(Text("🖥  CLI Command Tree", style="bold"))
            for ln in cli_lines:
                parts.append(Text.from_markup(ln))
        if mcp_lines:
            parts.append(Text(""))
            parts.append(Text("🔌 MCP Servers", style="bold"))
            for ln in mcp_lines:
                parts.append(Text.from_markup(ln))

        console.print(
            Panel(
                RichGroup(*parts),
                title="[bold yellow]🎯 Feature Intelligence[/bold yellow]",
                border_style="yellow",
                box=ROUNDED,
                padding=(0, 1),
            )
        )

    console.print()
