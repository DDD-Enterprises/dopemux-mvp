"""Visual output tools - return formatted text for Claude to display in terminal.

All functions return plain strings with Unicode box-drawing characters and
strategic emoji for gorgeous, terminal-safe output.
"""

from typing import Any, Dict, List


def format_session_banner(session_data: Dict[str, Any]) -> str:
    """Generate a session start banner."""
    energy = session_data.get("energy_level", "medium")
    energy_bar = {"high": "████████", "medium": "█████░░░", "low": "███░░░░░"}
    icons = {"high": "⚡", "medium": "🔋", "low": "🪫"}

    task = session_data.get("task", "General")[:38]
    est = session_data.get("estimated_minutes", 25)
    break_at = session_data.get("break_at", "??:??")
    icon = icons.get(energy, "❓")
    bar = energy_bar.get(energy, "░░░░░░░░")

    return (
        f"\n┌──────────────────────────────────────────────┐\n"
        f"│  🎯 Focus Session Started                    │\n"
        f"│                                              │\n"
        f"│  Task: {task:<38} │\n"
        f"│  Energy: {icon} {bar}  {energy.upper():<8}   │\n"
        f"│  Timer:  ⏱️  {est} min{' ' * max(0, 26 - len(str(est)))}│\n"
        f"│  Break:  ☕ at {break_at}{' ' * max(0, 24 - len(str(break_at)))}│\n"
        f"│                                              │\n"
        f"│  💡 Tip: Type /break when you need a pause   │\n"
        f"└──────────────────────────────────────────────┘"
    )


def format_workflow_status(status: Dict[str, Any]) -> str:
    """Generate workflow status dashboard."""
    session = status.get("session", {})
    adhd = status.get("adhd_state", {})
    tasks = status.get("active_tasks", [])
    decisions = status.get("recent_decisions", [])

    elapsed = session.get("elapsed_minutes", 0)
    total = session.get("estimated_minutes", 25)
    pct = min(100, int(elapsed / max(total, 1) * 100))
    filled = pct // 5
    bar = "█" * filled + "░" * (20 - filled)

    energy = adhd.get("energy_level", "?")
    attention = adhd.get("attention", "?")

    lines: List[str] = [
        "┌─── 📊 Workflow Status ───────────────────────┐",
        f"│  Session: [{bar}] {pct:>3}% ({elapsed}/{total}m) │",
        f"│  Energy:  {energy:<8} Focus: {attention:<10}│",
        "├─── Active Tasks ──────────────────────────────┤",
    ]

    for t in tasks[:3]:
        icon = "🔄" if t.get("status") == "IN_PROGRESS" else "⏳"
        title = t.get("title", "Untitled")[:40]
        lines.append(f"│  {icon} {title:<40} │")

    if not tasks:
        lines.append("│  (no active tasks)                           │")

    if decisions:
        lines.append("├─── Recent Decisions ──────────────────────────┤")
        for d in decisions[:2]:
            summary = d.get("summary", "")[:40]
            lines.append(f"│  📝 {summary:<40} │")

    lines.append("└──────────────────────────────────────────────┘")
    return "\n".join(lines)


def format_break_reminder(adhd_state: Dict[str, Any]) -> str:
    """Gentle break reminder with progress celebration."""
    mins = adhd_state.get("session_minutes", 0)
    return (
        f"\n╔══════════════════════════════════════════════╗\n"
        f"║  ☕ Break Time!                               ║\n"
        f"║                                              ║\n"
        f"║  You've been focused for {mins} minutes.       ║\n"
        f"║  Great work! 🎉                               ║\n"
        f"║                                              ║\n"
        f"║  Suggestions:                                ║\n"
        f"║  • 🚶 Stand up and stretch (2 min)           ║\n"
        f"║  • 💧 Grab water                              ║\n"
        f"║  • 👀 Look at something 20ft away (20 sec)   ║\n"
        f"║                                              ║\n"
        f"║  Type /resume when ready                     ║\n"
        f"╚══════════════════════════════════════════════╝"
    )


def format_task_decomposition(decomposition: Dict[str, Any]) -> str:
    """Render task decomposition as a visual tree."""
    parent = decomposition.get("parent_task", "Task")
    subtasks = decomposition.get("subtasks", [])
    total_min = decomposition.get("total_estimated_minutes", 0)

    lines: List[str] = [
        f"🌳 {parent}",
        f"   Total: ~{total_min} min | {len(subtasks)} subtasks",
        "",
    ]

    for i, st in enumerate(subtasks):
        is_last = i == len(subtasks) - 1
        prefix = "└──" if is_last else "├──"
        energy_icon = {"low": "🟢", "medium": "🟡", "high": "🔴"}.get(
            st.get("energy", "medium"), "⚪"
        )
        title = st.get("title", "Subtask")
        est = st.get("estimated_minutes", 10)
        cog = st.get("cognitive_load", 0.5)

        lines.append(f"   {prefix} {energy_icon} {title}")
        connector = "   " if is_last else "│  "
        lines.append(f"   {connector}    ⏱️ {est}m | 🧠 {cog:.1f}")

        if st.get("break_after"):
            lines.append(f"   {connector}    ☕ Break recommended after")

    return "\n".join(lines)


def format_context_switch(from_task: str, to_task: str, reorientation_min: int) -> str:
    """Render context switch notification."""
    return (
        f"\n┌─── 🔄 Context Switch ─────────────────────────┐\n"
        f"│  From: {from_task[:38]:<38} │\n"
        f"│  To:   {to_task[:38]:<38} │\n"
        f"│  Est. reorientation: ~{reorientation_min} min{' ' * max(0, 18 - len(str(reorientation_min)))}│\n"
        f"│                                              │\n"
        f"│  💾 Previous context saved automatically      │\n"
        f"└──────────────────────────────────────────────┘"
    )


def format_risk_assessment(assessment: Dict[str, Any]) -> str:
    """Render risk assessment result."""
    risk_level = assessment.get("risk_level", "unknown")
    risk_score = assessment.get("risk_score", 0.0)
    factors = assessment.get("risk_factors", [])

    risk_icons = {"low": "🟢", "medium": "🟡", "high": "🔴", "critical": "🚨"}
    icon = risk_icons.get(risk_level, "⚪")

    pct = int(risk_score * 100)
    filled = pct // 5
    bar = "█" * filled + "░" * (20 - filled)

    lines: List[str] = [
        "┌─── ⚠️ Risk Assessment ────────────────────────┐",
        f"│  Risk: {icon} {risk_level.upper():<8} [{bar}] {pct}%  │",
        "├──────────────────────────────────────────────┤",
    ]

    for f in factors[:4]:
        factor_text = f[:42] if isinstance(f, str) else str(f)[:42]
        lines.append(f"│  • {factor_text:<42}│")

    if not factors:
        lines.append("│  No specific risk factors identified.        │")

    lines.append("└──────────────────────────────────────────────┘")
    return "\n".join(lines)
