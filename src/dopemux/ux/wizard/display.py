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
from dopemux.ui.theme import Glyphs, styled_panel, styled_table

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
WIZARD_VERSION = "2.0.0"


# ── Welcome / branded header ───────────────────────────────────────────────

def render_welcome_panel(state: WizardState) -> None:
    """Display the branded wizard header with repo metadata."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    repo_name = state.repo_root.name

    branch_line = f"Branch: [bold]{state.git_branch or '(unknown)'}[/bold]"
    if state.git_clean:
        branch_line += "  •  [success]Clean working tree[/success]"
    else:
        branch_line += "  •  [warning]Dirty working tree[/warning]"

    body = (
        f"\n"
        f"  Repository: [mint]{repo_name}[/mint]\n"
        f"  {branch_line}\n"
        f"  Time: {now}\n"
        f"\n"
        f"  This wizard will guide you through:\n"
        f"  [text.muted]1.[/text.muted] 🔬  Corpus analysis — what's in your repo\n"
        f"  [text.muted]2.[/text.muted] 💊  Cost planning — choose your budget\n"
        f"  [text.muted]3.[/text.muted] ⚡  Extraction — build your truth map\n"
    )

    console.print(
        styled_panel(
            body,
            title=f"🔬  DOPEMUX DOCUMENTATION AUDIT WIZARD  v{WIZARD_VERSION}",
            padding=(0, 2),
        )
    )


# ── Stage transitions ──────────────────────────────────────────────────────

def render_stage_header(stage_num: int, title: str, icon: str) -> None:
    """Print a visual separator when entering a new stage."""
    console.print()
    console.rule(f"[heading]  Stage {stage_num}  •  {icon}  {title}  [/heading]", style="rule.line")
    console.print()


def render_stage_complete(stage_num: int, title: str, result: StageResult) -> None:
    """Show stage completion status with duration."""
    if result.status == StageStatus.COMPLETED:
        icon = Glyphs.SUCCESS
        style = "success"
        label = "Complete"
    elif result.status == StageStatus.SKIPPED:
        icon = Glyphs.SKIPPED
        style = "warning"
        label = "Skipped"
    elif result.status == StageStatus.FAILED:
        icon = Glyphs.ERROR
        style = "error"
        label = "Failed"
    else:
        icon = Glyphs.PENDING
        style = "text.muted"
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
    table.add_column("Detail", style="text.dim")

    for label, passed, detail in checks:
        icon = f"[success]{Glyphs.SUCCESS}[/success]" if passed else f"[warning]{Glyphs.WARNING}[/warning]"
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

    table = styled_table(
        f"{Glyphs.DATABASE} Corpus Breakdown",
        ("Class", {"min_width": 12}),
        ("Files", {"justify": "right", "min_width": 6}),
        ("Size", {"justify": "right", "min_width": 8}),
        ("Coverage", {"min_width": 24}),
    )

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
    table = styled_table(
        f"{Glyphs.WRENCH} Select Routing Policy",
        ("Policy", {"min_width": 18}),
        ("Est. Cost", {"justify": "right", "min_width": 10}),
        ("Keys", {"justify": "center", "min_width": 6}),
        ("Description", {"min_width": 24}),
    )

    for p in policies:
        name = p["name"]
        prefix = f"{Glyphs.PROMPT} " if name == selected else "  "
        emoji = p.get("emoji", "💊")
        low = p.get("low_cost", 0)
        high = p.get("high_cost", 0)
        cost_str = f"~${low:.0f}–${high:.0f}"
        keys_ok = p.get("keys_ok", True)
        keys_str = f"[success]{Glyphs.SUCCESS} {p.get('keys_status', '')}[/success]" if keys_ok else f"[error]{Glyphs.ERROR} {p.get('keys_status', '')}[/error]"

        style = "bold" if name == selected else ""
        table.add_row(
            f"{prefix}{emoji} [{style}]{p.get('label', name)}[/{style}]",
            cost_str,
            keys_str,
            f"[text.dim]{p.get('desc', '')}[/text.dim]",
        )

    corpus_mb = corpus_size / (1024 * 1024)
    table.caption = f"[text.dim]Estimates based on {corpus_mb:.1f} MB corpus, 14 phases[/text.dim]"
    console.print(table)


# ── Phase preview ──────────────────────────────────────────────────────────

def render_phase_table(file_counts: Dict[str, int]) -> None:
    """Display per-phase file count and estimated partitions."""
    table = styled_table(
        f"{Glyphs.CODE} Extraction Phase Map",
        ("Phase", {"min_width": 4, "justify": "center"}),
        ("Name", {"min_width": 22}),
        ("Files", {"justify": "right", "min_width": 6}),
        ("Est. Partitions", {"justify": "right", "min_width": 14}),
    )

    for phase_key in PHASES:
        info = PHASE_INFO[phase_key]
        count = file_counts.get(phase_key, 0)
        partitions = max(1, math.ceil(count / 50)) if count > 0 else 0
        count_str = f"{count:,}" if count > 0 else "[text.muted]—[/text.muted]"
        part_str = str(partitions) if partitions > 0 else "[text.muted]meta[/text.muted]"
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
        styled_panel(
            f"[text.dim]{content}[/text.dim]",
            title=f"{Glyphs.INFO}  {title}",
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
            lines.append(f"  [success]  {Glyphs.SUCCESS} Completed:[/success]   {completed}")
        if skipped:
            lines.append(f"  [warning]  {Glyphs.SKIPPED} Skipped:[/warning]    {skipped}")
        if failed:
            lines.append(f"  [error]  {Glyphs.ERROR} Failed:[/error]     {failed}")
    else:
        lines.append(f"  [text.muted]No phases executed (preview mode)[/text.muted]")

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
    title_icon = Glyphs.SUCCESS if completed > 0 and failed == 0 else Glyphs.INFO

    console.print(
        styled_panel(
            f"\n{body}\n",
            title=f"{title_icon}  Wizard Summary",
            padding=(0, 2),
        )
    )


# ── Batch plan table ──────────────────────────────────────────────────────

def render_batch_plan_table(batch_plan: Dict[str, Any]) -> None:
    """Show batch breakdown per Grok pass — batch count, tokens, authority classes."""
    passes = batch_plan.get("passes", {})
    if not passes:
        return

    table = styled_table(
        f"{Glyphs.WRENCH} Prescan Batch Plan",
        ("Pass", {"min_width": 12}),
        ("Batches", {"justify": "right", "min_width": 8}),
        ("Est. Tokens", {"justify": "right", "min_width": 12}),
        ("Files", {"justify": "right", "min_width": 8}),
    )

    total_batches = 0
    total_tokens = 0
    total_files = 0

    for pass_id, plan_data in passes.items():
        batches = plan_data.get("batches", [])
        n_batches = len(batches)
        est_tokens = plan_data.get("total_estimated_tokens", 0)
        n_files = plan_data.get("total_files", 0)

        total_batches += n_batches
        total_tokens += est_tokens
        total_files += n_files

        tok_str = f"{est_tokens / 1_000_000:.1f}M" if est_tokens > 0 else "—"
        table.add_row(pass_id, str(n_batches), tok_str, str(n_files))

    table.add_section()
    total_tok_str = f"{total_tokens / 1_000_000:.1f}M" if total_tokens > 0 else "—"
    table.add_row("[bold]Total[/bold]", f"[bold]{total_batches}[/bold]", f"[bold]{total_tok_str}[/bold]", f"[bold]{total_files}[/bold]")

    # Oversized files warning
    oversized = batch_plan.get("oversized_files", [])
    if oversized:
        table.caption = f"[warning]⚠ {len(oversized)} file(s) too large for LLM batches (see oversized_manifest.json)[/warning]"

    console.print(table)


# ── Archaeology table ─────────────────────────────────────────────────────

def render_archaeology_table(report: Dict[str, Any]) -> None:
    """Feature archaeology results with status + recommendation columns."""
    features = report.get("discovered_features", [])
    if not features:
        console.print("  [text.dim]No historical features discovered.[/text.dim]")
        return

    table = styled_table(
        f"{Glyphs.DATABASE} Feature Archaeology",
        ("Feature", {"min_width": 24}),
        ("Status", {"min_width": 12}),
        ("Files", {"justify": "right", "min_width": 6}),
        ("Recommendation", {"min_width": 16}),
    )

    STATUS_STYLES = {
        "completed": ("success", Glyphs.SUCCESS),
        "abandoned": ("text.dim", "⚪"),
        "partial": ("warning", "🟡"),
        "documented_only": ("violet", "🔵"),
    }

    for feat in features[:20]:
        status = feat.get("status", "unknown")
        style, icon = STATUS_STYLES.get(status, ("text.dim", "❓"))
        n_files = len(feat.get("source_paths", []))
        rec = feat.get("recommendation", "—")
        table.add_row(
            feat.get("name", "Unknown"),
            f"[{style}]{icon} {status}[/{style}]",
            str(n_files),
            rec,
        )

    summary = report.get("summary", {})
    total = summary.get("total_discovered", len(features))
    worth = summary.get("worth_restoring", 0)
    table.caption = f"[text.dim]{total} features discovered, {worth} worth restoring[/text.dim]"
    console.print(table)


# ── Code intelligence summary ─────────────────────────────────────────────

def render_hotspot_table(hotspots: List[Dict[str, Any]]) -> None:
    """Display top hotspot files by churn × complexity."""
    if not hotspots:
        return

    table = styled_table(
        f"{Glyphs.WARNING} Complexity Hotspots",
        ("File", {"min_width": 30}),
        ("Churn", {"justify": "right", "min_width": 6}),
        ("Complexity", {"justify": "right", "min_width": 10}),
        ("Score", {"justify": "right", "min_width": 6}),
        ("Contributors", {"justify": "right", "min_width": 12}),
    )

    for h in hotspots:
        score = h.get("hotspot_score", 0)
        style = "error" if score >= 0.8 else "warning" if score >= 0.5 else ""
        table.add_row(
            h.get("rel_path", ""),
            f"{h.get('churn_score', 0):.2f}",
            f"{h.get('complexity_score', 0):.2f}",
            f"[{style}]{score:.2f}[/{style}]" if style else f"{score:.2f}",
            str(h.get("contributors", 0)),
        )

    console.print(table)


def render_orphan_summary(total: int, high_confidence: int) -> None:
    """Show dead code candidate counts."""
    if total == 0:
        console.print(f"  {Glyphs.SUCCESS}  No dead code candidates detected")
        return

    console.print(
        f"  {Glyphs.INFO}  {total} dead code candidates found, "
        f"{high_confidence} high-confidence (advisory only — will be deprioritized)"
    )


def render_hub_table(hubs: List[Dict[str, Any]]) -> None:
    """Display architectural hub files by in-degree."""
    if not hubs:
        return

    table = styled_table(
        f"{Glyphs.CODE} Architectural Hub Files",
        ("File", {"min_width": 30}),
        ("In-Degree", {"justify": "right", "min_width": 10}),
        ("Out-Degree", {"justify": "right", "min_width": 10}),
        ("PageRank", {"justify": "right", "min_width": 8}),
    )

    for h in hubs:
        table.add_row(
            h.get("rel_path", ""),
            str(h.get("in_degree", 0)),
            str(h.get("out_degree", 0)),
            f"{h.get('pagerank', 0):.4f}",
        )

    console.print(table)


def render_processing_order_preview(order: List[Dict[str, Any]], top_n: int = 10) -> None:
    """Show files that will be extracted first (highest priority)."""
    if not order:
        return

    table = styled_table(
        f"{Glyphs.ARROW_RIGHT} Extraction Priority (Top {top_n})",
        ("Rank", {"justify": "center", "min_width": 4}),
        ("File", {"min_width": 30}),
        ("Score", {"justify": "right", "min_width": 6}),
        ("PageRank", {"justify": "right", "min_width": 8}),
        ("Proximity", {"justify": "right", "min_width": 8}),
        ("Hotspot", {"justify": "right", "min_width": 8}),
    )

    for i, entry in enumerate(order[:top_n], 1):
        table.add_row(
            str(i),
            entry.get("rel_path", ""),
            f"{entry.get('score', 0):.3f}",
            f"{entry.get('pagerank', 0):.3f}",
            f"{entry.get('proximity', 0):.3f}",
            f"{entry.get('hotspot', 0):.3f}",
        )

    console.print(table)


def render_test_coverage_summary(mapped: int, total: int) -> None:
    """Show test file mapping coverage."""
    if total == 0:
        return

    pct = (mapped / total * 100) if total > 0 else 0
    bar = _bar(mapped / total if total > 0 else 0, width=20)
    style = "success" if pct >= 60 else "warning" if pct >= 30 else "error"
    console.print(
        f"  [{style}]{bar}[/{style}]  {mapped}/{total} source files have mapped tests ({pct:.0f}%)"
    )


def render_code_intel_summary(code_intel: Dict[str, Any]) -> None:
    """Combined code intelligence display: hotspots, orphans, hubs, coverage."""
    summary = code_intel.get("summary", {})

    # Summary line
    console.print(
        f"\n  [bold]Code Intelligence:[/bold]  "
        f"{summary.get('total_code_files', 0)} code files  •  "
        f"{summary.get('entry_points', 0)} entry points  •  "
        f"avg complexity {summary.get('avg_complexity', 0):.2f}"
    )
    console.print()

    # Hotspots
    hotspots = code_intel.get("hotspots", [])
    hot_count = summary.get("hotspots", 0)
    if hot_count > 0:
        render_hotspot_table(hotspots[:10])
        console.print()

    # Dead code
    orphans = code_intel.get("orphans", [])
    high_conf = sum(1 for o in orphans if o.get("confidence", 0) >= 0.7)
    render_orphan_summary(len(orphans), high_conf)
    console.print()

    # Hub files
    hubs = code_intel.get("hub_files", [])
    if hubs:
        render_hub_table(hubs[:5])
        console.print()

    # Test coverage
    test_mappings = code_intel.get("test_mappings", [])
    mapped = sum(1 for t in test_mappings if t.get("test_path"))
    total = len(test_mappings)
    if total > 0:
        render_test_coverage_summary(mapped, total)
        console.print()

    # Processing order
    order = code_intel.get("processing_order", [])
    if order:
        render_processing_order_preview(order, top_n=10)


def render_phase_intelligence_brief(
    phase_key: str, state: "WizardState",
) -> None:
    """Per-phase prescan intelligence: files, skips, compression hints, estimates."""
    router = state.intelligence_router
    if not router:
        return

    skip_count = state.phase_skip_counts.get(phase_key, 0)
    partition_count = state.phase_partition_counts.get(phase_key, 0)
    token_estimate = state.phase_token_estimates.get(phase_key, 0)

    parts = []
    if partition_count > 0:
        parts.append(f"{partition_count} partitions")
    if skip_count > 0:
        parts.append(f"[warning]{skip_count} files skipped by prescan[/warning]")
    if token_estimate > 0:
        parts.append(f"~{token_estimate / 1_000_000:.1f}M tokens est.")

    if parts:
        console.print(f"  [text.dim]Intelligence: {' • '.join(parts)}[/text.dim]")


def render_extraction_phase_progress(
    phase_key: str, partition_num: int, total: int,
) -> None:
    """Per-partition progress within a phase."""
    bar = _bar(partition_num / total if total > 0 else 0, width=20)
    console.print(
        f"  [mint]{bar}[/mint] {partition_num}/{total} partitions", end="\r"
    )


def render_token_budget_bar(used: int, budget: int) -> None:
    """Visual token usage bar: [████████░░░░] 1.2M / 1.5M tokens."""
    frac = min(used / budget, 1.0) if budget > 0 else 0
    bar = _bar(frac, width=20)
    style = "success" if frac < 0.75 else "warning" if frac < 0.9 else "error"
    console.print(
        f"  [{style}]{bar}[/{style}] {used / 1_000_000:.1f}M / {budget / 1_000_000:.1f}M tokens"
    )


def render_savings_report(estimated: Dict[str, Any], actual: Dict[str, Any]) -> None:
    """Compare estimated vs actual token savings from prescan intelligence."""
    est_pct = estimated.get("estimated_reduction_pct", 0)
    est_skipped = estimated.get("skipped_files_count", 0)
    act_pct = actual.get("estimated_reduction_pct", 0) if actual else 0

    console.print(f"\n  [bold]Prescan Savings:[/bold]")
    console.print(f"    Files skipped: {est_skipped}")
    console.print(f"    Estimated reduction: {est_pct:.1f}%")
    if actual:
        console.print(f"    Actual reduction: {act_pct:.1f}%")


# ── Summary / completion ───────────────────────────────────────────────────

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
        console.print(f"\n[heading]{Glyphs.ARROW_RIGHT} Next Steps:[/heading]")
        for i, step in enumerate(steps, 1):
            console.print(f"  {i}. {step}")
        console.print()
