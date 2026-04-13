from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from extractor.phases.base import PhaseRunnerDeps


def run_phase(
    deps: PhaseRunnerDeps,
    dirs: Dict[str, Path],
    cfg: Any,
    ui: Optional[Any] = None,
) -> None:
    excludes = [
        ".git",
        "node_modules",
        "venv",
        ".venv",
        "tests",
        "docs",
        "extraction",
        "reports",
        "tmp",
        "_audit_out",
        "SYSTEM_ARCHIVE",
        "*.zip",
    ]
    collector = deps.collector_cls(
        deps.repo_root,
        deps.merge_scan_excludes(excludes, list(deps.repo_scan_excludes)),
    )
    targets = [
        ".claude",
        ".dopemux",
        ".githooks",
        ".github",
        ".taskx",
        "config",
        "scripts",
        "tools",
        "compose",
        "docker",
        "AGENTS.md",
        "README.md",
        "QUICK_START.md",
        "INSTALL.md",
        "CHANGELOG.md",
        "pyproject.toml",
        "dopemux.toml",
        "compose.yml",
        "compose.yml",
        "Makefile",
        ".claude.json",
        ".taskxroot",
        ".vibe",
        "src/dopemux/hooks",
        "src/dopemux/claude",
        "src/dopemux/claude_tools",
        "src/dopemux/commands",
        "src/dopemux/mcp",
        "src/dopemux/cli.py",
        "src/dopemux/__main__.py",
        "src/dopemux/routing_cli.py",
        "src/dopemux/profile_commands.py",
        "src/dopemux/dev_commands.py",
        "src/dopemux/worktree_commands.py",
        "src/dopemux/events",
        "src/dopemux/event_bus.py",
        "services/copilot_transcript_ingester",
        "services/dopecon-bridge",
        "mcp-proxy-config.copilot.yaml",
        "mcp-proxy-config.json",
    ]
    deps.run_phase_inner(
        "A",
        dirs,
        cfg,
        collector,
        targets,
        ui=ui,
        selected_step_ids=deps.selected_execution_step_ids_for_phase(cfg, "A"),
    )
