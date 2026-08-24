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
    plan = deps.plan_repo_scan_phase(
        cwd=deps.repo_root,
        collector_factory=deps.collector_cls,
        merge_scan_excludes=deps.merge_scan_excludes,
        repo_scan_excludes=deps.repo_scan_excludes,
        base_excludes=[".git"],
        targets=["docs"],
    )
    deps.run_phase_inner(
        "D",
        dirs,
        cfg,
        plan.collector,
        plan.targets,
        ui=ui,
        selected_step_ids=deps.selected_execution_step_ids_for_phase(cfg, "D"),
    )
