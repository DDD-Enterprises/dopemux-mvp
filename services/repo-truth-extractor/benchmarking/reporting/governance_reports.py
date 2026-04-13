from __future__ import annotations

from pathlib import Path
from typing import Any

from ..storage.hashing import stable_json_dumps
from ..storage.paths import run_paths


class GovernanceReportWriter:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root

    def _write_json(self, path: Path, payload: dict[str, Any] | list[dict[str, Any]]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(stable_json_dumps(payload) + "\n", encoding="utf-8")

    def write_packets(
        self,
        benchmark_run_id: str,
        recommendations: list[dict[str, Any]],
        packets: list[dict[str, Any]],
        decisions: list[dict[str, Any]],
        profile_fit_rows: list[dict[str, Any]],
        portfolio_view: dict[str, Any],
    ) -> None:
        run = run_paths(benchmark_run_id, self.root)
        self._write_json(run.governance_dir / "PROMOTION_RECOMMENDATIONS.json", recommendations)
        self._write_json(run.governance_dir / "GOVERNANCE_DECISIONS.json", decisions)
        for packet in packets:
            self._write_json(
                run.governance_dir / f"GOVERNANCE_PACKET__{packet['recommendation_id']}.json",
                packet,
            )
        for row in profile_fit_rows:
            self._write_json(run.rollups_dir / f"PROFILE_FIT__{row['profile_id']}.json", row)
        self._write_json(run.rollups_dir / "PORTFOLIO_VIEW.json", portfolio_view)
