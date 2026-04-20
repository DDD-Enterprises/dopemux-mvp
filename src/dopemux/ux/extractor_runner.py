from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from ..commands.extractor_commands import _run_extractor_runner as _run_extractor_runner_impl
from ..commands.extractor_commands import _run_repscan_runner as _run_repscan_runner_impl


def run_extractor_runner(
    *,
    args: List[str],
    pipeline_version: str = "v5",
    repo_root: Optional[Path] = None,
) -> None:
    _run_extractor_runner_impl(
        pipeline_version=pipeline_version,
        args=args,
        repo_root=repo_root,
    )


def run_repscan_runner(
    *,
    args: List[str],
    pipeline_version: str = "v5",
    repo_root: Optional[Path] = None,
) -> None:
    _run_repscan_runner_impl(args=args, repo_root=repo_root)
