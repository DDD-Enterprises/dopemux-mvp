from __future__ import annotations

import sys
from pathlib import Path


SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from benchmarking.cli.benchmark_reporting_smoke import run_reporting_smoke


def test_explainability_chain_resolves_to_rollup_delta_attempt_and_bundle(tmp_path: Path) -> None:
    payload = run_reporting_smoke(root=tmp_path / "benchmarks", proof_dir=tmp_path / "proof")
    detail = payload["sample_candidate_detail"]
    chain = detail["explanation_chain"]["chain"]
    node_types = [item["node_type"] for item in chain]
    assert "recommendation_state" in node_types
    assert "rollup_case_set" in node_types
    assert "control_deltas" in node_types
    assert "benchmark_case_attempt" in node_types
    assert "evidence_bundle" in node_types
    claims = detail["explanation_chain"]["claims"]
    evidence_classes = {item["evidence_class"] for item in claims}
    assert "BENCHMARK_DERIVED" in evidence_classes
    assert "GOVERNANCE_DERIVED" in evidence_classes
    assert "METADATA_ONLY" in evidence_classes
