"""
Task Legacy Commands

Deprecated `dopemux task` command retained for backwards compatibility.
Replaced by SuperClaude /dx: commands; this stub prints a migration
banner and delegates to the legacy TaskDecomposer so existing scripts
still round-trip through the PM plane backfill.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

import click

from ..adhd import TaskDecomposer
from ..config import ConfigManager
from ..console import console
from ..pm.writes import PMWriteConfig
from ..ui.theme import Glyphs, styled_table

logger = logging.getLogger(__name__)


@click.command("task")
@click.argument("description", required=False)
@click.option("--duration", "-d", type=int, default=25, help="⏱️ Ritual Duration: Session length in minutes (default: 25).")
@click.option(
    "--priority", "-p", type=click.Choice(["low", "medium", "high"]), default="medium", help="📊 Mission Priority: Calibration level for the task (default: medium)."
)
@click.option("--list", "-l", "list_tasks", is_flag=True, help="📋 Catalog Missions: List current active ritual tasks.")
@click.pass_context
def task(
    ctx, description: Optional[str], duration: int, priority: str, list_tasks: bool
):
    """
    📋 Legacy Ritual: Manage tasks (DEPRECATED - Use SuperClaude /dx: commands)

    This command has been replaced by:
    - /dx:implement - Start ADHD-optimized implementation session
    - /dx:session start/end/break - Session management
    - /dx:load - Load tasks from ConPort
    - /dx:stats - View ADHD metrics and progress

    For backwards compatibility, this command remains but delegates
    to the TaskDecomposer tracking (now synced to the canonical PM plane).
    See: docs/90-adr/ADR-XXXX-path-c-migration.md
    """
    console.logger.info("[warning]" + "=" * 60 + "[/warning]")
    console.logger.info("[error]⚠️  DEPRECATED COMMAND[/error]")
    console.logger.info("[warning]" + "=" * 60 + "[/warning]")
    console.logger.info()
    console.logger.info(
        "The 'dopemux task' command has been replaced by SuperClaude /dx: commands:"
    )
    console.logger.info()
    console.logger.info(
        "  [info]/dx:implement[/info] - Start ADHD-optimized implementation session"
    )
    console.logger.info("  [info]/dx:session start[/info] - Begin work session")
    console.logger.info("  [info]/dx:load[/info] - Load tasks from ConPort")
    console.logger.info("  [info]/dx:stats[/info] - View ADHD metrics and progress")
    console.logger.info()
    console.logger.info("Migration completed: October 2025")
    console.logger.info("See: [info]docs/90-adr/ADR-XXXX-path-c-migration.md[/info]")
    console.logger.info()
    console.logger.info("[warning]" + "=" * 60 + "[/warning]")

    project_path = Path.cwd()
    if not (project_path / ".dopemux").exists():
        console.logger.info(
            "[error]No Dopemux project found in current directory[/error]"
        )
        sys.exit(1)

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
        logger.debug(f"Could not build PMWriteConfig for task command: {e}")

    decomposer = TaskDecomposer(project_path, pm_config=pm_config)

    decomposer.backfill_to_pm_plane()

    if list_tasks:
        tasks = decomposer.list_tasks()
        if not tasks:
            console.logger.info("[warning]No tasks found[/warning]")
            return

        table = styled_table(
            f"{Glyphs.INFO} Current Tasks",
            ("Task", {"style": "mint"}),
            ("Priority", {"style": "gold"}),
            ("Duration", {"style": "mint.soft"}),
            ("Status", {"style": "violet"}),
        )

        for task_item in tasks:
            status = (
                "✅ Complete"
                if task_item.get("status") == "completed"
                else (
                    "🔄 In Progress"
                    if task_item.get("status") == "in_progress"
                    else "⏳ Pending"
                )
            )
            table.add_row(
                task_item["description"],
                task_item["priority"],
                f"{task_item['estimated_duration']}m",
                status,
            )

        console.logger.info(table)
        return

    if not description:
        console.logger.info(
            "[error]Description required when not listing tasks[/error]"
        )
        console.logger.info("Use 'dopemux task --list' to list current tasks")
        sys.exit(1)

    task_id = decomposer.add_task(
        description=description, duration=duration, priority=priority
    )

    console.logger.info(f"[success]✅ Task added: {description}[/success]")
    console.logger.info(f"[info]🆔 ID: {task_id}[/info]")
    console.logger.info(f"[warning]⏱️ Duration: {duration} minutes[/warning]")
    console.logger.info(f"[info]🎯 Priority: {priority}[/info]")
