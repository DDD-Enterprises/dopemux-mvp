from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional


def s_int_base_root(repo_root: Path, out_root: Optional[Path] = None) -> Path:
    if out_root is not None:
        return out_root.resolve()
    return (repo_root / "proof" / "s_int").resolve()


def s_int_run_root(repo_root: Path, run_id: str, out_root: Optional[Path] = None) -> Path:
    return s_int_base_root(repo_root, out_root=out_root) / str(run_id).strip()


def ensure_s_int_dirs(repo_root: Path, run_id: str, out_root: Optional[Path] = None) -> Dict[str, Path]:
    root = s_int_run_root(repo_root, run_id, out_root=out_root)
    raw = root / "raw"
    root.mkdir(parents=True, exist_ok=True)
    raw.mkdir(parents=True, exist_ok=True)
    return {
        "root": root,
        "raw": raw,
        "input": root / "S_INT_INPUT.json",
        "machine_summary": root / "S_INT_MACHINE_SUMMARY.json",
        "summary_md": root / "S_INT_SUMMARY.md",
        "checklist_md": root / "S_INT_CHECKLIST.md",
        "fail_closed_md": root / "S_INT_FAIL_CLOSED.md",
    }
