"""
Session Commands

The `dopemux status` diagnostic HUD. Aggregates attention metrics,
context state, task progress, and mobile/tmux bridge health into a
single rendered dashboard.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

import click

from ..adhd import AttentionMonitor, ContextManager, TaskDecomposer
from ..config import ConfigManager
from ..console import console
from ..pm.writes import PMWriteConfig
from ..ui.theme import styled_table

logger = logging.getLogger(__name__)


def _get_attention_emoji(state: Optional[str]) -> str:
    """Get emoji for attention state."""
    emoji_map = {
        "focused": "🎯",
        "scattered": "🌪️",
        "hyperfocus": "🔥",
        "normal": "😊",
        "distracted": "😵‍💫",
    }
    return emoji_map.get(state, "❓")


@click.command("status")
@click.option("--attention", "-a", is_flag=True, help="🧠 Cognitive Load: Show attention metrics and focus state.")
@click.option("--context", "-c", is_flag=True, help="🔬 Mental Model: Show active mental model and context density.")
@click.option("--tasks", "-t", is_flag=True, help="📊 Mission Progress: Show task completion and ritual velocity.")
@click.option("--mobile", "-m", is_flag=True, help="📱 Satellite Link: Show Happy mobile synchronization status.")
@click.pass_context
def status(ctx, attention: bool, context: bool, tasks: bool, mobile: bool):
    """
    📊 Diagnostic HUD: Show current session status and metrics

    Retrieves high-fidelity telemetry from the active cockpit session,
    detailing attention levels, mental model depth, and ritual progression.
    Displays attention state, context information, task progress, and
    ADHD accommodation effectiveness.
    """
    project_path = Path.cwd()

    if not (project_path / ".dopemux").exists():
        console.logger.info(
            "[error]No Dopemux project found in current directory[/error]"
        )
        sys.exit(1)

    if not any([attention, context, tasks, mobile]):
        attention = context = tasks = mobile = True

    if attention:
        monitor = AttentionMonitor(project_path)
        metrics = monitor.get_current_metrics()

        table = styled_table(
            "🧠 Attention Metrics",
            ("Metric", {"style": "mint"}),
            ("Value", {"style": "mint.soft"}),
            ("Status", {"style": "gold"}),
        )

        table.add_row(
            "Current State",
            metrics.get("attention_state", "unknown"),
            _get_attention_emoji(metrics.get("attention_state")),
        )
        table.add_row(
            "Session Duration", f"{metrics.get('session_duration', 0):.1f} min", "⏱️"
        )
        table.add_row("Focus Score", f"{metrics.get('focus_score', 0):.1%}", "🎯")
        table.add_row("Context Switches", str(metrics.get("context_switches", 0)), "🔄")

        console.logger.info(table)

    if context:
        context_manager = ContextManager(project_path)
        current_context = context_manager.get_current_context()

        table = styled_table(
            "📍 Context Information",
            ("Item", {"style": "mint"}),
            ("Value", {"style": "mint.soft"}),
        )

        table.add_row("Current Goal", current_context.get("current_goal", "Not set"))
        table.add_row("Open Files", str(len(current_context.get("open_files", []))))
        table.add_row("Last Save", current_context.get("last_save", "Never"))
        table.add_row("Git Branch", current_context.get("git_branch", "unknown"))

        console.logger.info(table)

    pm_config = None
    try:
        config_mgr = ConfigManager()
        pm_config = PMWriteConfig(
            leantime_client=getattr(config_mgr, "leantime_client", None),
            orchestrator_client=getattr(config_mgr, "orchestrator_client", None),
            conport_client=getattr(config_mgr, "conport_client", None),
            memory_client=getattr(config_mgr, "memory_client", None),
        )
    except Exception as e:
        logger.debug(f"Could not build PMWriteConfig for status command: {e}")

    if tasks:
        decomposer = TaskDecomposer(project_path, pm_config=pm_config)
        progress_info = decomposer.get_progress()

        if progress_info:
            table = styled_table(
                "📋 Task Progress",
                ("Task", {"style": "mint"}),
                ("Status", {"style": "mint.soft"}),
                ("Progress", {"style": "gold"}),
            )

            for task in progress_info.get("tasks", []):
                status_emoji = (
                    "✅" if task["completed"] else "🔄" if task["in_progress"] else "⏳"
                )
                table.add_row(
                    task["name"], status_emoji, f"{task.get('progress', 0):.0%}"
                )

            console.logger.info(table)
        else:
            console.logger.info("[warning]No active tasks found[/warning]")

    if mobile:
        from ..mobile.runtime import check_cli_health, list_mobile_panes
        from ..mobile.tmux_utils import TmuxError

        cfg_manager = ctx.obj.get("config_manager") if ctx.obj else ConfigManager()
        mobile_cfg = cfg_manager.get_mobile_config()

        happy_ok = check_cli_health("happy")
        claude_ok = check_cli_health("claude")

        try:
            panes = list_mobile_panes()
            tmux_error = None
        except TmuxError as exc:
            panes = []
            tmux_error = str(exc)
            logger.error(f"Error: {exc}")

        mobile_table = styled_table(
            "📱 Mobile Status",
            ("Check", {"style": "mint"}),
            ("Status", {"style": "mint.soft"}),
        )

        mobile_table.add_row(
            "Mobile Enabled", "✅ Enabled" if mobile_cfg.enabled else "❌ Disabled"
        )
        mobile_table.add_row(
            "Happy CLI", "✅ Healthy" if happy_ok else "❌ Unavailable"
        )
        mobile_table.add_row(
            "Claude CLI", "✅ Healthy" if claude_ok else "⚠️ Check setup"
        )

        if tmux_error:
            mobile_table.add_row("tmux", f"⚠️ {tmux_error}")
        else:
            mobile_table.add_row("Active Sessions", str(len(panes)))

        console.logger.info(mobile_table)

        if not tmux_error and panes:
            sessions_table = styled_table(
                "📱 Active Happy Sessions",
                ("Pane", {"style": "mint"}),
                ("Window", {"style": "mint.soft"}),
                ("Path", {"style": "text.dim"}),
            )

            for pane in panes:
                sessions_table.add_row(
                    pane.title or "(unnamed)",
                    pane.window or "?",
                    pane.path or "",
                )

            console.logger.info(sessions_table)
