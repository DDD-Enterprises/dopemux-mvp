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
    final_items = deps.collect_phase_artifacts(dirs, ["R", "X", "T"], ["raw", "norm", "qa"])
    deps.run_phase_inner(
        "Z",
        dirs,
        cfg,
        None,
        None,
        precollected_items=final_items,
        ui=ui,
        selected_step_ids=deps.selected_execution_step_ids_for_phase(cfg, "Z"),
    )
