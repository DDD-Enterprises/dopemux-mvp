from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Sequence


@dataclass(frozen=True)
class PhaseRunnerDeps:
    repo_root: Path
    repo_scan_excludes: Sequence[str]
    collector_cls: Any
    merge_scan_excludes: Callable[[list[str], list[str]], list[str]]
    run_phase_inner: Callable[..., None]
    selected_execution_step_ids_for_phase: Callable[[Any, str], Optional[list[str]]]
    collect_phase_artifacts: Callable[[Dict[str, Path], Sequence[str], Sequence[str]], list[Dict[str, Any]]]
