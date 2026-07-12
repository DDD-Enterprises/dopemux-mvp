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
    targets = [
        "src",
        "services",
        "shared",
        "plugins",
        "tools",
        "scripts",
        "tests",
        "docker/mcp-servers-source",
        "docker/mcp-servers",
        "components",
    ]
    plan = deps.plan_repo_scan_phase(
        cwd=deps.repo_root,
        collector_factory=deps.collector_cls,
        merge_scan_excludes=deps.merge_scan_excludes,
        repo_scan_excludes=deps.repo_scan_excludes,
        base_excludes=[".git", "node_modules", "venv", ".venv", "docs", "test-results"],
        targets=targets,
    )
    deps.run_phase_inner(
        "C",
        dirs,
        cfg,
        plan.collector,
        plan.targets,
        ui=ui,
        selected_step_ids=deps.selected_execution_step_ids_for_phase(cfg, "C"),
    )
