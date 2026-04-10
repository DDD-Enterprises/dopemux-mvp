from __future__ import annotations

import sys
from pathlib import Path


SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from benchmarking.cli.benchmark_hardening_smoke import run_hardening_smoke


def test_change_summary_reports_state_blocker_and_governance_deltas(tmp_path: Path) -> None:
    payload = run_hardening_smoke(root=tmp_path / "benchmarks", proof_dir=tmp_path / "proof")
    summary = payload["sample_change_summary"]
    assert "recommendation_state_change" in summary
    assert "blocker_delta" in summary
    assert "governance_state_change" in summary
    assert summary["recommendation_state_change"]["changed"] is True
    assert summary["claims"]
