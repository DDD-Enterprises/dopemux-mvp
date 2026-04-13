from __future__ import annotations

from pathlib import Path
from typing import Any

from ..storage.hashing import stable_json_dumps
from ..storage.paths import run_paths


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(stable_json_dumps(payload) + "\n", encoding="utf-8")


def write_route_identity_admissibility(
    benchmark_run_id: str,
    payload: dict[str, Any],
    root: Path | None = None,
) -> None:
    run = run_paths(benchmark_run_id, root)
    _write_json(run.recommendations_dir / "ROUTE_IDENTITY_ADMISSIBILITY.json", payload)
    if payload.get("campaign_state") == "invalidated":
        _write_json(
            run.governance_dir / "CAMPAIGN_INVALIDATION.json",
            {
                "benchmark_run_id": benchmark_run_id,
                "campaign_state": "invalidated",
                "reason_codes": payload.get("admissibility_blocker_codes", []),
                "source_artifact": "recommendations/ROUTE_IDENTITY_ADMISSIBILITY.json",
            },
        )
