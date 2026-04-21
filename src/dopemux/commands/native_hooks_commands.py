"""
Native Hooks Commands

Registers DØPEMÜX synchronization hooks in Claude Code settings so CLI
activity shows up in cockpit telemetry.
"""

import json
import logging
from pathlib import Path

import click

from ..console import console

logger = logging.getLogger(__name__)


@click.group()
def native_hooks():
    """
    🔗 Protocol Synchronization: Manage Claude Code internal hooks

    Orchestrates the registration and management of high-fidelity internal
    hooks. These rituals ensure that Claude Code activity is seamlessly
    synchronized with the DØPEMÜX cockpit telemetry.
    """
    pass


@native_hooks.command("register")
@click.option(
    "--global",
    "is_global",
    is_flag=True,
    help="🌐 Global Calibration: Register ritual hooks in the global configuration ledger.",
)
def native_hooks_register(is_global: bool):
    """
    ⚡ Synchronize Protocol: Register DØPEMÜX hooks in Claude settings

    Automates the injection of ritual hook coordinates into the Claude
    Code configuration ledger, enabling real-time signal detection.
    """
    hook_script = Path(__file__).resolve().parent.parent / "claude" / "native_hooks.py"
    cmd = f"python3 {hook_script}"

    hooks_config = {
        "hooks": {
            "command": [
                {
                    "events": [
                        "SessionStart",
                        "UserPromptSubmit",
                        "PreToolUse",
                        "PermissionRequest",
                        "PostToolUse",
                        "PostToolUseFailure",
                        "Stop",
                        "SubagentStop",
                        "PreCompact",
                        "SessionEnd",
                    ],
                    "command": cmd,
                }
            ]
        }
    }

    if is_global:
        settings_path = Path.home() / ".claude" / "settings.json"
    else:
        settings_path = Path.cwd() / ".claude" / "settings.json"

    existing = {}
    if settings_path.exists():
        try:
            existing = json.loads(settings_path.read_text())
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Failed to load or read native hooks settings: {e}")

    if "hooks" not in existing:
        existing["hooks"] = {}
    if "command" not in existing["hooks"]:
        existing["hooks"]["command"] = []

    already_registered = any(
        h.get("command") == cmd for h in existing["hooks"]["command"]
    )

    if not already_registered:
        existing["hooks"]["command"].insert(0, hooks_config["hooks"]["command"][0])
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        settings_path.write_text(json.dumps(existing, indent=2))
        console.print(
            f"[success]✓ Registered Dopemux native hooks in {settings_path}[/success]"
        )
    else:
        console.print(
            f"[info]Dopemux native hooks already registered in {settings_path}[/info]"
        )
