from __future__ import annotations

from typing import Any


def build_portfolio_view(
    benchmark_run_id: str,
    profile_fit_rows: list[dict[str, Any]],
    archetype_rollups: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "benchmark_run_id": benchmark_run_id,
        "view_type": "portfolio_matrix",
        "profiles": profile_fit_rows,
        "archetypes": archetype_rollups,
        "ranking_present": False,
        "notes": [
            "Portfolio view is a matrix-style skeleton.",
            "No universal best-model leaderboard is produced in M3.",
        ],
    }
