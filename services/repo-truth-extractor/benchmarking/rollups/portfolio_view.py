from __future__ import annotations

from typing import Any


def build_portfolio_view(
    benchmark_run_id: str,
    profile_fit_rows: list[dict[str, Any]],
    archetype_rollups: list[dict[str, Any]],
) -> dict[str, Any]:
    benchmark_modes = sorted(
        {
            str(mode)
            for payload in profile_fit_rows + archetype_rollups
            for mode in payload.get("benchmark_modes", [])
        }
    )
    return {
        "benchmark_run_id": benchmark_run_id,
        "view_type": "portfolio_matrix",
        "benchmark_modes": benchmark_modes,
        "lane_isolation_preserved": len(benchmark_modes) <= 1,
        "profiles": profile_fit_rows,
        "archetypes": archetype_rollups,
        "ranking_present": False,
        "notes": [
            "Portfolio view is a matrix-style skeleton.",
            "No universal best-model leaderboard is produced in M3.",
            "This view is runtime-route scoped and must not collapse direct_model evidence into route-profile truth.",
        ],
    }
