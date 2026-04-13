from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _item(row_id: str, path: str, line_range: list[int], **extra: Any) -> dict[str, Any]:
    base = {"id": row_id, "path": path, "line_range": line_range}
    base.update(extra)
    return base


def build_fl_int_run_root(base: Path) -> Path:
    run_root = base / "runs" / "fl_int_case"
    phase_dirs = {
        "D": "D_docs_pipeline",
        "C": "C_code_surfaces",
        "R": "R_arbitration",
        "X": "X_feature_index",
    }
    for phase_dir in phase_dirs.values():
        (run_root / phase_dir / "norm").mkdir(parents=True, exist_ok=True)
    write_json(
        run_root / phase_dirs["D"] / "norm" / "DOC_CONTRACT_CLAIMS.json",
        {
            "schema": "DOC_CONTRACT_CLAIMS@v1",
            "items": [
                _item(
                    "doc_claim_pm",
                    "docs/pm-plane.md",
                    [10, 12],
                    name="PM plane preserved",
                    evidence=[
                        {
                            "path": "docs/pm-plane.md",
                            "line_range": [10, 12],
                            "excerpt": "PM plane governs planning surfaces.",
                        }
                    ],
                )
            ],
        },
    )
    write_json(
        run_root / phase_dirs["C"] / "norm" / "COGNITIVE_FEATURES_SURFACE.json",
        {
            "schema": "COGNITIVE_FEATURES_SURFACE@v1",
            "items": [
                _item(
                    "code_feature_pm",
                    "services/task-orchestrator/server.py",
                    [30, 35],
                    component="task-orchestrator",
                    evidence=[
                        {
                            "path": "services/task-orchestrator/server.py",
                            "line_range": [30, 35],
                            "excerpt": "publish planning updates into PM plane",
                        }
                    ],
                )
            ],
        },
    )
    (run_root / phase_dirs["R"] / "norm" / "CONFLICT_LEDGER.md").write_text(
        "# Conflict Ledger\n\n- contradiction FL-1 remains unresolved.\n",
        encoding="utf-8",
    )
    write_json(
        run_root / phase_dirs["X"] / "norm" / "FEATURE_SURFACE.json",
        {
            "schema": "FEATURE_SURFACE@v1",
            "items": [
                _item(
                    "x_feature_pm",
                    "services/task-orchestrator/server.py",
                    [30, 35],
                    component="task-orchestrator",
                    symbol="sync_to_pm_plane",
                    evidence=[
                        {
                            "path": "services/task-orchestrator/server.py",
                            "line_range": [30, 35],
                            "excerpt": "sync_to_pm_plane",
                        }
                    ],
                )
            ],
        },
    )
    return run_root

