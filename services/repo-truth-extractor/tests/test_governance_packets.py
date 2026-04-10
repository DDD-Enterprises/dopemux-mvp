from __future__ import annotations

import sys
from pathlib import Path


SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from benchmarking.cli.benchmark_governance_smoke import run_governance_smoke


def test_governance_packets_include_evidence_refs_and_required_action(tmp_path: Path) -> None:
    proof_dir = tmp_path / "proof"
    payload = run_governance_smoke(root=tmp_path / "benchmarks", proof_dir=proof_dir)
    packet = payload["sample_governance_packet"]
    recommendation = payload["sample_recommendation"]
    assert recommendation["recommendation_state"] == "recommended_for_review"
    assert packet["evidence_bundle_ids"]
    assert packet["required_action"]
    assert packet["control_delta_summary"]["delta_count"] >= 1
    assert (proof_dir / "sample_governance_packet.json").exists()
