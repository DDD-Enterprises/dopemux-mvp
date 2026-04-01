from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional


def fl_int_base_root(run_root: Path, out_root: Optional[Path] = None) -> Path:
    if out_root is not None:
        return out_root.resolve()
    return (run_root.resolve() / "postprocess" / "fl_int_v1").resolve()


def ensure_fl_int_dirs(run_root: Path, out_root: Optional[Path] = None) -> Dict[str, Path]:
    root = fl_int_base_root(run_root, out_root=out_root)
    raw = root / "raw"
    root.mkdir(parents=True, exist_ok=True)
    raw.mkdir(parents=True, exist_ok=True)
    return {
        "root": root,
        "raw": raw,
        "input": root / "FL_INT_INPUT.json",
        "machine_summary": root / "FL_INT_MACHINE_SUMMARY.json",
        "summary_md": root / "FL_INT_SUMMARY.md",
        "checklist_md": root / "FL_INT_CHECKLIST.md",
        "fail_closed_md": root / "FL_INT_FAIL_CLOSED.md",
    }
