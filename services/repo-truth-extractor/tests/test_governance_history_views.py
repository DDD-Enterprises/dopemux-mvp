from __future__ import annotations

import sys
from pathlib import Path


SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from benchmarking.cli.benchmark_reporting_smoke import run_reporting_smoke


def test_governance_history_distinguishes_current_and_historical_decisions(tmp_path: Path) -> None:
    payload = run_reporting_smoke(root=tmp_path / "benchmarks", proof_dir=tmp_path / "proof")
    history = payload["sample_governance_history"]
    assert history["current_effective_decision"] is not None
    assert len(history["decision_history"]) >= 2
    current_id = history["current_effective_decision"]["decision_id"]
    assert all(item["decision_id"] != current_id for item in history["historical_decisions"])
